# GitHub 仓库卡片生成器

一个基于 FastAPI 和 Pillow 的 GitHub 仓库卡片生成工具，支持 Web 界面和 API 调用。

> 临时在线试用地址：https://cas.luler.top/?search=68de28ca84a3a

## ✨ 功能特性

- 🎨 生成精美的 GitHub 仓库信息卡片
- 📱 移动端完美兼容的 Web 界面
- 🚀 RESTful API 接口支持
- 🐳 Docker 一键部署
- 🖼️ 支持图片预览、放大查看和下载
- 😊 支持 Emoji 显示（彩色）
- 🌍 支持中英文混排
- 📊 显示仓库统计信息（Stars、Forks、Issues、Contributors）
- 🔄 自动清理旧图片，同一仓库只保留最新版本

## 📦 快速开始

### Docker 部署（推荐）

```bash
# 一键启动
docker-compose up -d

# 访问 http://localhost:8000
```

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python api.py

# 访问 http://localhost:8000
```

## 🔌 API 使用

### 方式一：直接获取卡片图片（推荐）

**GET** `/github/{owner}/{repo_name}`

直接返回卡片图片，支持智能缓存和自动更新：

```html
<!-- 在 HTML 中使用 -->
<img src="http://localhost:8000/github/luler/hello_github_card" alt="GitHub Card">

<!-- 在 Markdown 中使用 -->
![GitHub Card](http://localhost:8000/github/luler/hello_github_card)
```

**特性：**

- ✅ 卡片不存在时自动生成
- ✅ 卡片存在且未过期（24小时内）直接返回
- ✅ 卡片过期后异步更新，同时返回旧卡片（不阻塞请求）
- ✅ 支持浏览器缓存（Cache-Control: 24小时）
- ✅ 支持 ETag 验证（304 Not Modified，节省带宽）

**缓存机制：**

- **首次访问**：生成卡片并返回（200 OK）
- **24小时内**：直接使用浏览器缓存，不请求服务器
- **F5 刷新**：验证 ETag，未更新返回 304（仅传输响应头约 200 字节）
- **卡片过期**：后台异步更新，先返回旧版本

### 方式二：API 接口生成

**POST** `/api/generate`

- 请求：

```json
{
  "repo_url": "https://github.com/luler/hello_github_card"
}
```

- 正常返回示例：

```json
{
  "success": true,
  "message": "卡片生成成功",
  "data": {
    "owner": "luler",
    "repo_name": "hello_github_card",
    "image_url": "/images/luler/hello_github_card.png",
    "filename": "hello_github_card.png",
    "repo_info": {
      "description": "一个基于 FastAPI 和 Pillow 的 GitHub 仓库卡片生成工具，支持 Web 界面和 API 调用。",
      "stars": 0,
      "forks": 0,
      "issues": 0,
      "contributors": 1
    }
  }
}
```

- 错误返回示例：

```json
{
  "detail": "服务器错误: 404: 无法获取仓库信息，请检查仓库 URL 是否正确"
}
```

**GET** `/api/health` - 健康检查

详细文档：http://localhost:8000/docs

## 🎨 卡片样式

![](example.png)

- **尺寸**: 900x450 像素
- **背景**: 浅灰色 (#f6f8fa)
- **头像**: 右上角圆形头像
- **标题**: 作者名（灰色）+ 仓库名（黑色加粗）
- **描述**: 最多 3 行，自动换行，支持 Emoji
- **统计**: Contributors、Issues、Forks、Stars
- **底部**: 彩色装饰条

## 🛠️ 技术栈

- **后端**: FastAPI, Uvicorn
- **图像处理**: Pillow
- **前端**: HTML/CSS/JavaScript
- **API**: GitHub REST API v3
- **部署**: Docker, Docker Compose
