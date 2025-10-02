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

### 方式一：Docker 部署（推荐）

```bash
# 使用 Docker Compose 一键启动
docker-compose up -d

# 访问服务
# Web 界面: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

详细说明请查看 [DOCKER.md](DOCKER.md)

### 方式二：本地运行

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 启动服务

```bash
python api.py
```

#### 3. 访问服务

- **Web 界面**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

### 方式三：命令行使用

```bash
python
>>> from main import GitHubRepoCard
>>> generator = GitHubRepoCard("https://github.com/python/cpython")
>>> generator.fetch_repo_data()
>>> generator.create_card("output.png")
```

## 🔌 API 使用

### 生成卡片

**POST** `/api/generate`

请求体：
```json
{
  "repo_url": "https://github.com/owner/repo"
}
```

响应：
```json
{
  "success": true,
  "message": "卡片生成成功",
  "data": {
    "owner": "owner",
    "repo_name": "repo",
    "image_url": "/images/owner_repo_20240101_120000.png",
    "filename": "owner_repo_20240101_120000.png",
    "repo_info": {
      "description": "仓库描述",
      "stars": 1000,
      "forks": 200,
      "issues": 50,
      "contributors": 30
    }
  }
}
```

### 健康检查

**GET** `/api/health`

响应：
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00"
}
```

## 📁 项目结构

```
hello_github_card/
├── main.py                 # 核心卡片生成逻辑
├── api.py                  # FastAPI 服务
├── requirements.txt        # Python 依赖
├── Dockerfile             # Docker 镜像构建文件
├── docker-compose.yml     # Docker Compose 配置
├── .dockerignore          # Docker 忽略文件
├── README.md              # 项目文档
├── DOCKER.md              # Docker 部署文档
├── USAGE.md               # 详细使用指南
├── static/                # 静态文件
│   └── index.html         # Web 前端页面
├── images/                # 生成的卡片图片
└── test_*.py             # 测试文件
```

## 🎨 卡片样式

- **尺寸**: 900x450 像素
- **背景**: #f6f8fa 浅灰色
- **头像**: 右上角圆形头像
- **标题**: 作者名（灰色）+ 仓库名（黑色加粗）
- **描述**: 最多 3 行，自动换行
- **统计**: Contributors、Issues、Forks、Stars
- **底部**: 彩色装饰条

## 🌐 支持的 URL 格式

- `https://github.com/owner/repo`
- `github.com/owner/repo`
- `owner/repo`

## 📝 注意事项

1. 图片文件名会自动清理特殊字符
2. 同一仓库的旧图片会自动删除
3. 支持 Windows、macOS、Linux 系统字体
4. Emoji 自动使用系统 Emoji 字体渲染
5. Docker 部署时已包含所需字体

## 🛠️ 技术栈

- **后端**: FastAPI, Uvicorn
- **图像处理**: Pillow
- **前端**: 原生 HTML/CSS/JavaScript
- **API**: GitHub REST API v3
- **部署**: Docker, Docker Compose

## 📚 文档

- [使用指南](USAGE.md) - 详细的使用说明
- [Docker 部署](DOCKER.md) - Docker 部署完整指南
- [API 文档](http://localhost:8000/docs) - 在线 API 文档（需先启动服务）

## 📄 License

MIT License

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

