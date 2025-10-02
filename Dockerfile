# 使用官方 Python 基础镜像
FROM python:3.11-slim

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 设置工作目录
WORKDIR /app

# 安装系统依赖（字体支持）
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    fontconfig \
    && fc-cache -f -v \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 验证字体安装
RUN fc-list | grep -i emoji || echo "Warning: Emoji fonts not found"

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY main.py api.py ./
COPY static/ ./static/

# 创建 images 目录
RUN mkdir -p images

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/health')"

# 运行 FastAPI 服务器
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]