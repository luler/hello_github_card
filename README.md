# GitHub 仓库卡片生成器

一个基于 FastAPI 和 Pillow 的 GitHub 仓库卡片生成工具，支持 Web 界面和 API 调用。

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

**POST** `/api/generate`

```json
{
  "repo_url": "https://github.com/luler/hello_github_card"
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
