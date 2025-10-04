# -*- coding: utf-8 -*-
"""
GitHub 仓库卡片生成 API 服务
提供 Web 接口和静态页面服务
"""

import asyncio
import re
from datetime import datetime, timedelta
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from main import GitHubRepoCard

# 创建 FastAPI 应用
app = FastAPI(
    title="GitHub Card Generator API",
    description="生成 GitHub 仓库卡片的 API 服务",
    version="1.0.0"
)

# 配置静态文件目录
IMAGES_DIR = Path("images")
STATIC_DIR = Path("static")

# 确保目录存在
IMAGES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# 挂载静态文件目录
app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 异步任务队列
regeneration_queue = asyncio.Queue()


class RepoRequest(BaseModel):
    """仓库请求模型"""
    repo_url: str

    class Config:
        json_schema_extra = {
            "example": {
                "repo_url": "https://github.com/python/cpython"
            }
        }


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不支持的特殊字符

    :param filename: 原始文件名
    :return: 清理后的文件名
    """
    # 移除或替换不支持的字符
    # Windows 文件名不支持: < > : " / \ | ? *
    # 保留字母、数字、下划线、连字符、点
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 移除多余的空格
    sanitized = re.sub(r'\s+', '_', sanitized)
    # 移除开头和结尾的点和空格
    sanitized = sanitized.strip('. ')
    return sanitized


def parse_repo_url(repo_url: str) -> tuple:
    """
    解析 GitHub 仓库 URL

    :param repo_url: GitHub 仓库 URL
    :return: (owner, repo_name) 元组
    """
    # 支持多种 URL 格式
    # https://github.com/owner/repo
    # github.com/owner/repo
    # owner/repo

    repo_url = repo_url.strip().rstrip('/')

    # 移除协议
    if '://' in repo_url:
        repo_url = repo_url.split('://', 1)[1]

    # 移除 github.com
    if repo_url.startswith('github.com/'):
        repo_url = repo_url[11:]

    # 分割 owner 和 repo
    parts = repo_url.split('/')
    if len(parts) >= 2:
        owner = parts[-2]
        repo = parts[-1]
        return owner, repo
    else:
        raise ValueError("无效的 GitHub 仓库 URL 格式")


def get_image_path(owner: str, repo_name: str) -> Path:
    """
    生成图片存储路径

    :param owner: 仓库所有者
    :param repo_name: 仓库名称
    :return: 图片路径（Path对象）
    """
    # 清理目录名和文件名
    clean_owner = sanitize_filename(owner)
    clean_repo = sanitize_filename(repo_name)

    # 创建目录结构: images/{owner}/
    owner_dir = IMAGES_DIR / clean_owner
    owner_dir.mkdir(parents=True, exist_ok=True)

    # 返回完整路径: images/{owner}/{repo_name}.png
    return owner_dir / f"{clean_repo}.png"


def is_card_outdated(image_path: Path, max_age_days: int = 1) -> bool:
    """
    检查卡片是否过期（超过指定天数）

    :param image_path: 图片路径
    :param max_age_days: 最大有效天数，默认1天
    :return: 是否过期
    """
    if not image_path.exists():
        return True

    # 获取文件修改时间
    mtime = datetime.fromtimestamp(image_path.stat().st_mtime)
    age = datetime.now() - mtime

    return age > timedelta(days=max_age_days)


async def regenerate_card_worker():
    """
    后台任务：处理卡片重新生成队列
    """
    while True:
        try:
            # 从队列获取任务
            owner, repo_name, image_path = await regeneration_queue.get()

            print(f"\n[后台任务] 重新生成卡片: {owner}/{repo_name}")

            # 生成卡片
            normalized_url = f"https://github.com/{owner}/{repo_name}"
            generator = GitHubRepoCard(normalized_url)

            if generator.fetch_repo_data():
                generator.create_card(str(image_path))
                print(f"[后台任务] 卡片重新生成完成: {owner}/{repo_name}")
            else:
                print(f"[后台任务] 获取仓库信息失败: {owner}/{repo_name}")

            # 标记任务完成
            regeneration_queue.task_done()

        except Exception as e:
            print(f"[后台任务] 重新生成卡片失败: {e}")
            regeneration_queue.task_done()


@app.on_event("startup")
async def startup_event():
    """应用启动时创建后台任务"""
    asyncio.create_task(regenerate_card_worker())


@app.get("/")
async def read_root():
    """返回首页 HTML"""
    html_file = STATIC_DIR / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    else:
        return {"message": "GitHub Card Generator API", "docs": "/docs"}


@app.get("/github/{owner}/{repo_name}")
async def direct_card(owner: str, repo_name: str, request: Request):
    """
    通过路径参数获取 GitHub 仓库卡片
    - 如果卡片不存在，自动生成
    - 如果卡片存在但超过1天，放入异步队列重新生成，同时返回旧卡片
    - 如果卡片存在且未过期，直接返回
    - 支持 ETag 验证，匹配时返回 304 Not Modified

    :param owner: 仓库所有者
    :param repo_name: 仓库名称
    :param request: 请求对象
    :return: 卡片图片文件或 304 响应
    """
    try:
        # 获取图片路径
        image_path = get_image_path(owner, repo_name)

        # 检查卡片是否存在
        if not image_path.exists():
            # 卡片不存在，立即生成
            print(f"\n[直接生成] 卡片不存在，立即生成: {owner}/{repo_name}")

            normalized_url = f"https://github.com/{owner}/{repo_name}"
            generator = GitHubRepoCard(normalized_url)

            if not generator.fetch_repo_data():
                raise HTTPException(
                    status_code=404,
                    detail="无法获取仓库信息，请检查仓库名称是否正确"
                )

            result = generator.create_card(str(image_path))
            if not result:
                raise HTTPException(
                    status_code=500,
                    detail="生成卡片失败"
                )

            print(f"[直接生成] 卡片生成成功: {owner}/{repo_name}")

        # 检查卡片是否过期
        elif is_card_outdated(image_path, max_age_days=1):
            # 卡片过期，放入队列异步重新生成
            print(f"\n[异步更新] 卡片已过期，加入重新生成队列: {owner}/{repo_name}")
            await regeneration_queue.put((owner, repo_name, image_path))
            print(f"[异步更新] 先返回旧卡片: {owner}/{repo_name}")

        else:
            # 卡片未过期，直接返回
            print(f"\n[缓存命中] 卡片未过期，直接返回: {owner}/{repo_name}")

        # 生成服务端 ETag
        server_etag = f'"{owner}/{repo_name}-{int(image_path.stat().st_mtime)}"'

        # 获取客户端 ETag
        client_etag = request.headers.get("if-none-match")

        # ETag 验证：如果匹配则返回 304 Not Modified
        if client_etag == server_etag:
            print(f"[304] ETag 匹配，返回 Not Modified: {owner}/{repo_name}")
            return Response(
                status_code=304,
                headers={
                    "Cache-Control": "public, max-age=86400, must-revalidate",
                    "ETag": server_etag,
                    "Last-Modified": datetime.fromtimestamp(
                        image_path.stat().st_mtime
                    ).strftime("%a, %d %b %Y %H:%M:%S GMT")
                }
            )

        # 返回图片文件，设置缓存头
        return FileResponse(
            image_path,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=86400, must-revalidate",  # 缓存1天，但需验证
                "ETag": server_etag,  # 使用文件修改时间作为ETag
                "Last-Modified": datetime.fromtimestamp(
                    image_path.stat().st_mtime
                ).strftime("%a, %d %b %Y %H:%M:%S GMT")
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[错误] 处理卡片请求失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"服务器错误: {str(e)}"
        )


@app.post("/api/generate")
async def generate_card(request: RepoRequest):
    """
    生成 GitHub 仓库卡片

    :param request: 仓库请求
    :return: 生成的图片信息
    """
    try:
        # 解析仓库 URL
        owner, repo_name = parse_repo_url(request.repo_url)

        # 标准化 URL
        normalized_url = f"https://github.com/{owner}/{repo_name}"

        print(f"\n{'=' * 60}")
        print(f"正在生成卡片: {owner}/{repo_name}")
        print(f"{'=' * 60}")

        # 创建卡片生成器
        generator = GitHubRepoCard(normalized_url)

        # 获取仓库数据
        if not generator.fetch_repo_data():
            raise HTTPException(
                status_code=404,
                detail="无法获取仓库信息，请检查仓库 URL 是否正确"
            )

        # 生成文件路径
        image_path = get_image_path(owner, repo_name)

        # 生成卡片
        result = generator.create_card(str(image_path))

        if not result:
            raise HTTPException(
                status_code=500,
                detail="生成卡片失败"
            )

        # 计算相对路径用于返回URL
        relative_path = image_path.relative_to(IMAGES_DIR)
        image_url = f"/images/{relative_path.as_posix()}"

        # 返回结果
        return JSONResponse({
            "success": True,
            "message": "卡片生成成功",
            "data": {
                "owner": owner,
                "repo_name": repo_name,
                "image_url": image_url,
                "filename": image_path.name,
                "repo_info": {
                    "description": generator.api_data.get("description", ""),
                    "stars": generator.api_data.get("stargazers_count", 0),
                    "forks": generator.api_data.get("forks_count", 0),
                    "issues": generator.api_data.get("open_issues_count", 0),
                    "contributors": generator.contributors_count
                }
            }
        })

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"服务器错误: {str(e)}"
        )


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy"
    }


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  GitHub Card Generator API Server")
    print("=" * 60)
    print(f"  访问地址: http://localhost:8000")
    print(f"  API 文档: http://localhost:8000/docs")
    print(f"  图片目录: {IMAGES_DIR.absolute()}")
    print("=" * 60 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
