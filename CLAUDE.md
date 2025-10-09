# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 Z.AI (chat.z.ai) 的逆向 API 代理服务，提供兼容 OpenAI 格式的聊天完成端点。该服务将 OpenAI API 格式的请求转换为 Z.AI 的内部 API 格式，处理身份验证、请求签名、图片上传和流式响应。

**支持的模型：**
- GLM-4.6 (标准版、搜索版、高级搜索版、无思考版)
- GLM-4.5V (视觉模型)
- GLM-4.5

## 开发命令

### 运行应用
```bash
# 安装依赖
pip install -r requirements.txt

# 运行开发服务器（带自动重载）
python main.py

# 或直接使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### 构建可执行文件
```bash
# 使用 PyInstaller 构建平台特定的可执行文件
python build.py

# 输出文件位于 dist/blackboxai2api
```

### Docker 操作
```bash
# 本地构建和运行
docker build -t blackboxai2api .
docker run -d --name blackboxai2api --restart always -p 8001:8001 -e APP_SECRET=你的密钥 blackboxai2api

# 多平台构建（ARM64）
docker buildx build --platform linux/arm64 -t bbapi-arm64 .
```

### 测试 API
```bash
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_SECRET" \
  -d '{"model":"glm-4.6","messages":[{"role":"user","content":"你好"}],"stream":false}'
```

## 架构设计

### 核心流程
1. **请求入口** (`api/routes.py`): FastAPI 路由处理 OpenAI 格式的请求
2. **身份验证**: 从 Authorization 头验证 Bearer token
3. **消息转换** (`api/chat_service.py`): 将 OpenAI 格式转换为 Z.AI 格式
4. **图片处理** (`api/image_uploader.py`): 上传 base64 或 URL 图片到 Z.AI CDN
5. **请求签名** (`api/signature_generator.py`): 为请求生成 HMAC-SHA256 签名
6. **代理到 Z.AI**: 使用正确的头部和签名转发请求到 chat.z.ai
7. **响应转换**: 将 Z.AI 的流式响应转换回 OpenAI 格式

### 核心组件

**api/app.py**
- FastAPI 应用工厂
- CORS 和中间件配置
- 全局异常处理器
- 健康检查端点

**api/routes.py**
- `/v1/chat/completions` - 主要聊天端点（POST）
- `/v1/models` - 列出可用模型（GET）
- 针对 ALLOWED_MODELS 进行模型验证
- 流式与非流式响应路由

**api/chat_service.py**
- `prepare_data()`: 构造 Z.AI 请求负载，包括模型映射、功能配置和签名
- `process_streaming_response()`: 处理 Z.AI 的 SSE 流，转换不同阶段（thinking/answer/other/done）
- `process_non_streaming_response()`: 累积完整响应并返回单个完成结果
- `convert_messages()`: 从 OpenAI 消息格式中提取文本和图片 URL
- `getfeatures()`: 配置特定模型的功能（网络搜索、思考、预览模式、MCP 服务器）

**api/signature_generator.py**
- 两阶段 HMAC-SHA256 签名过程
- 第一阶段：使用密钥 "junjie" 和时间桶值（n = timestamp / 5分钟）进行 HMAC
- 第二阶段：使用第一阶段结果对完整请求字符串进行 HMAC 签名
- 所有 Z.AI API 请求都需要此签名

**api/image_uploader.py**
- 在聊天请求前上传图片到 Z.AI 的文件服务
- 支持 base64 编码图片和外部 URL
- 返回用于 Z.AI 消息格式的文件 ID
- 使用 multipart/form-data 上传

**api/config.py**
- 使用 pydantic-settings 的集中配置管理
- 从 .env 文件加载环境变量
- `MODELS_MAPPING`: 将公开模型名称映射到 Z.AI 内部模型 ID
- `ALLOWED_MODELS`: API 公开的模型列表
- `PROXY_URL`: Z.AI 基础 URL（默认：https://chat.z.ai）
- Z.AI 请求所需的头部（User-Agent、X-FE-Version 等）

**api/models.py**
- 用于请求/响应验证的 Pydantic 模型
- `ChatRequest`: 兼容 OpenAI 的聊天完成请求
- `Message`: 支持字符串内容和多模态内容（文本 + 图片）

### Z.AI API 特性

**模型映射：**
- 公开名称（glm-4.6, glm-4.5V）映射到 Z.AI 内部模型 ID
- 示例："glm-4.6" → "GLM-4-6-API-V1"

**请求参数：**
- `requestId`、`timestamp`、`user_id` 作为查询参数
- `signature_timestamp` 和 `X-Signature` 头部用于认证
- `features` 对象控制搜索、思考、图片生成
- `mcp_servers` 数组启用高级搜索功能

**响应阶段：**
- `thinking`: 模型推理（转换为 delta 中的 reasoning_content）
- `answer`: 最终响应内容（转换为 delta 中的 content）
- `tool_call`: 工具使用（当前实现中已注释）
- `other`: 完成并带有使用统计
- `done`: 流结束标记

**特殊处理：**
- 从 thinking 阶段过滤掉 `<summary>` 和 `</summary>` 标签
- 从 answer 阶段过滤掉 `</details>` 标签
- 非流式模式完全忽略 thinking 阶段

### 环境配置

创建 `.env` 文件：
```
HOST=0.0.0.0
PORT=8001
DEBUG=False
WORKERS=1
LOG_LEVEL=INFO
PROXY_URL=https://chat.z.ai
```

身份验证要求用户在 `Authorization: Bearer TOKEN` 头部提供他们的 Z.AI 访问令牌。

## 重要说明

- 签名算法使用硬编码密钥（"junjie"）- 这是 Z.AI 客户端实现的一部分
- 时间戳至关重要：请求使用毫秒级 Unix 时间戳，签名需要时间桶计算
- X-FE-Version 头部是必需的，应与 Z.AI 当前的前端版本匹配
- 图片文件必须在发送聊天请求前上传到 Z.AI 的 CDN
- 模型功能（搜索、思考）根据模型变体按请求配置
