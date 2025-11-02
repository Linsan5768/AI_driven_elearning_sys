# Docker 中的 Ollama 设置指南

## ✅ 已完成的配置

Docker 中的 Ollama 服务已经启用并配置完成：

1. ✅ `docker-compose.yml` - Ollama 服务已启用
2. ✅ `frontend/nginx.conf` - 添加了 Ollama 代理（`/ollama`）
3. ✅ `backend/app.py` - 更新为使用 Docker 网络中的 `ollama:11434`
4. ✅ `frontend/src/config/apiConfig.ts` - 支持环境变量和生产环境代理
5. ✅ 前端组件已更新为使用代理或环境变量

## 🚀 快速开始

### 1. 启动所有服务（包括 Ollama）

```bash
# 构建并启动所有容器
docker-compose up -d --build

# 查看所有服务状态
docker-compose ps
```

你应该看到三个服务：
- `magic-academy-backend`
- `magic-academy-frontend`
- `magic-academy-ollama` ✅

### 2. 等待 Ollama 启动

Ollama 首次启动可能需要 10-30 秒：

```bash
# 查看 Ollama 日志
docker logs -f magic-academy-ollama

# 当看到 "Ollama is running" 或类似消息时，表示已启动
```

### 3. 拉取所需模型

```bash
# 进入 Ollama 容器
docker exec -it magic-academy-ollama sh

# 在容器内拉取模型
ollama pull qwen2.5:7b
ollama pull llama2

# 验证模型已下载
ollama list

# 退出容器
exit
```

或者直接从宿主机执行：

```bash
# 从宿主机执行（需要端口映射）
docker exec magic-academy-ollama ollama pull qwen2.5:7b
docker exec magic-academy-ollama ollama pull llama2
docker exec magic-academy-ollama ollama list
```

### 4. 验证配置

```bash
# 测试 Ollama API（通过端口映射）
curl http://localhost:11434/api/tags

# 测试 Ollama API（通过 Nginx 代理）
curl http://localhost/ollama/api/tags

# 测试后端访问 Ollama（从后端容器内）
docker exec magic-academy-backend curl http://ollama:11434/api/tags
```

## 📝 工作原理

### Docker 网络架构

```
Browser → Frontend (Nginx) → /ollama → Ollama Container
                                    ↓
                           Backend → ollama:11434 (Docker network)
```

### URL 配置说明

1. **前端（浏览器）**:
   - 开发环境: `http://127.0.0.1:11434`
   - 生产环境（Docker）: `/ollama`（通过 Nginx 代理）

2. **后端（容器内）**:
   - 使用 Docker 服务名: `http://ollama:11434`

3. **环境变量覆盖**:
   - 可通过 `VITE_OLLAMA_URL` 自定义 URL

## 🔧 配置选项

### 方案 A: 使用 Nginx 代理（当前配置，推荐）

优点：
- ✅ 无需暴露端口到宿主机
- ✅ 统一的前端入口
- ✅ 更好的安全性

访问方式：
- 前端: `http://localhost/ollama/api/...`
- 后端: `http://ollama:11434/api/...`

### 方案 B: 直接端口映射（如需外部访问）

如果你想从宿主机直接访问 Ollama：

```yaml
# docker-compose.yml 中已包含端口映射
ports:
  - "11434:11434"  # 已启用
```

访问方式：
- 前端: `http://localhost/ollama/api/...`（通过代理）
- 宿主机: `http://localhost:11434/api/...`（直接访问）

## 🐛 故障排查

### Ollama 容器无法启动

```bash
# 检查日志
docker logs magic-academy-ollama

# 检查资源使用
docker stats magic-academy-ollama

# 重启 Ollama
docker-compose restart ollama
```

### 模型下载失败

```bash
# 检查网络连接
docker exec magic-academy-ollama ping -c 3 8.8.8.8

# 手动拉取模型（带详细输出）
docker exec -it magic-academy-ollama ollama pull qwen2.5:7b --verbose
```

### 前端无法访问 Ollama

```bash
# 测试代理是否工作
curl http://localhost/ollama/api/tags

# 检查 Nginx 配置
docker exec magic-academy-frontend cat /etc/nginx/conf.d/default.conf

# 检查 Nginx 日志
docker logs magic-academy-frontend
```

### 后端无法访问 Ollama

```bash
# 测试后端到 Ollama 的连接
docker exec magic-academy-backend curl http://ollama:11434/api/tags

# 检查网络连接
docker exec magic-academy-backend ping -c 3 ollama
```

## 📊 监控 Ollama

### 查看模型列表

```bash
docker exec magic-academy-ollama ollama list
```

### 查看运行状态

```bash
# 查看容器资源使用
docker stats magic-academy-ollama

# 查看 API 请求日志
docker logs magic-academy-ollama | grep -i "generate"
```

## 💾 数据持久化

Ollama 模型存储在 Docker volume `ollama_data` 中：

```bash
# 查看 volume
docker volume ls | grep ollama

# 备份模型数据（可选）
docker run --rm -v ollama_data:/data -v $(pwd):/backup alpine tar czf /backup/ollama-backup.tar.gz /data

# 恢复模型数据（可选）
docker run --rm -v ollama_data:/data -v $(pwd):/backup alpine tar xzf /backup/ollama-backup.tar.gz -C /data
```

## 🔄 更新模型

```bash
# 拉取最新版本的模型
docker exec magic-academy-ollama ollama pull qwen2.5:7b

# 查看可用模型版本
docker exec magic-academy-ollama ollama show qwen2.5:7b
```

## 📝 环境变量（可选）

如果需要自定义配置，可以创建 `.env` 文件：

```env
# .env
VITE_OLLAMA_URL=/ollama  # 或 http://your-custom-url:11434
```

然后在 `docker-compose.yml` 中引用：

```yaml
frontend:
  build:
    args:
      - VITE_OLLAMA_URL=${VITE_OLLAMA_URL:-/ollama}
```

## ✅ 验证清单

完成后，确认：

- [ ] Ollama 容器正在运行: `docker ps | grep ollama`
- [ ] 模型已下载: `docker exec magic-academy-ollama ollama list`
- [ ] 前端代理工作: `curl http://localhost/ollama/api/tags`
- [ ] 后端可以访问: `docker exec magic-academy-backend curl http://ollama:11434/api/tags`
- [ ] 应用功能正常: 在浏览器中测试 LLM 功能

## 🎯 总结

现在你的 Magic Academy 应用已经完全容器化，包括 Ollama LLM 服务：

1. ✅ Ollama 运行在 Docker 容器中
2. ✅ 模型数据持久化存储
3. ✅ 前端通过 Nginx 代理访问
4. ✅ 后端直接通过 Docker 网络访问
5. ✅ 支持开发和生产环境自动切换

所有服务都可以通过 `docker-compose up -d` 一键启动！

