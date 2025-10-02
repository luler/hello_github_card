# -*- coding: utf-8 -*-
"""
GitHub 仓库卡片生成 API 服务
提供 Web 接口和静态页面服务
"""

import re
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
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


def get_image_filename(owner: str, repo_name: str) -> str:
    """
    生成图片文件名

    :param owner: 仓库所有者
    :param repo_name: 仓库名称
    :return: 文件名
    """
    # 生成基础文件名: owner_repo_timestamp.png
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{owner}_{repo_name}_{timestamp}"

    # 清理文件名
    clean_name = sanitize_filename(base_name)

    return f"{clean_name}.png"


def cleanup_old_images(owner: str, repo_name: str):
    """
    清理同一仓库的旧图片，只保留最新的一张

    :param owner: 仓库所有者
    :param repo_name: 仓库名称
    """
    # 查找所有该仓库的图片
    pattern = f"{sanitize_filename(owner)}_{sanitize_filename(repo_name)}_*.png"

    existing_files = list(IMAGES_DIR.glob(pattern))

    # 按修改时间排序
    existing_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    # 删除除了最新的之外的所有文件
    for old_file in existing_files[1:]:
        try:
            old_file.unlink()
            print(f"已删除旧图片: {old_file.name}")
        except Exception as e:
            print(f"删除旧图片失败 {old_file.name}: {e}")


@app.get("/")
async def read_root():
    """返回首页 HTML"""
    html_file = STATIC_DIR / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    else:
        return {"message": "GitHub Card Generator API", "docs": "/docs"}


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

        # 生成文件名
        filename = get_image_filename(owner, repo_name)
        output_path = IMAGES_DIR / filename

        # 生成卡片
        result = generator.create_card(str(output_path))

        if not result:
            raise HTTPException(
                status_code=500,
                detail="生成卡片失败"
            )

        # 清理旧图片
        cleanup_old_images(owner, repo_name)

        # 返回结果
        return JSONResponse({
            "success": True,
            "message": "卡片生成成功",
            "data": {
                "owner": owner,
                "repo_name": repo_name,
                "image_url": f"/images/{filename}",
                "filename": filename,
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
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
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
