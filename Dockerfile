# 使用官方 ARM Python 运行时作为父镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 将当前目录内容复制到容器的 /app 中
COPY . /app

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 让端口 8001 可供此容器外的环境使用
EXPOSE 8001

# 运行 app.py，使用环境变量 PORT（Render 会自动设置）
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8001}