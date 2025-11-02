# Docker代码镜像化状态报告

## 当前状态总结

### ✅ 已完全镜像化的部分（可安全删除本地代码）

#### 1. 前端代码 (`frontend/`)
- ✅ **所有源代码**：`frontend/src/` - 构建时COPY到镜像
- ✅ **构建产物**：`frontend/dist/` - 已打包到Nginx镜像
- ✅ **依赖**：`frontend/node_modules/` - 构建时安装到镜像
- ✅ **配置文件**：`vite.config.ts`, `tsconfig.json`等 - 构建时COPY到镜像

**结论**：删除 `frontend/src/`, `frontend/node_modules/`, `frontend/dist/` **完全安全**

#### 2. 后端源代码 (`backend/app.py`)
- ✅ **主应用代码**：`backend/app.py` - 构建时COPY到镜像
- ✅ **Python虚拟环境**：`backend/venv/` - 不需要，容器内有独立Python环境
- ✅ **依赖**：在容器内通过`requirements.txt`安装

**结论**：删除 `backend/app.py` **完全安全**（但需要保留用于重新构建）

---

### ⚠️ 当前使用本地目录挂载的部分（需要迁移）

#### 1. 上传文件目录 (`backend/uploads/`)
- ❌ **当前状态**：使用bind mount，挂载本地目录 `./backend/uploads`
- ⚠️ **如果删除本地代码**：所有上传的文件会丢失
- ✅ **已更新配置**：`docker-compose.yml`已改为使用named volume `backend_uploads`

#### 2. 课程文件目录 (`backend/courses/`)
- ❌ **当前状态**：使用bind mount，挂载本地目录 `./backend/courses`
- ⚠️ **如果删除本地代码**：所有生成的课程会丢失
- ✅ **已更新配置**：`docker-compose.yml`已改为使用named volume `backend_courses`

---

## 迁移步骤（使数据完全独立于本地代码）

### 快速迁移（推荐）

```bash
cd /Users/lin/Uni/2025S2/ELEC5620/demo

# 运行迁移脚本
./migrate-to-volumes.sh

# 重新启动容器
docker-compose up -d

# 验证数据
docker-compose exec backend ls -la /app/uploads
docker-compose exec backend ls -la /app/courses
```

### 手动迁移

```bash
# 1. 停止容器
docker-compose down

# 2. 备份数据（可选但推荐）
tar -czf backend_data_backup_$(date +%Y%m%d).tar.gz backend/uploads/ backend/courses/

# 3. 创建volumes（docker-compose会自动创建，但可以手动创建）
docker volume create demo_backend_uploads
docker volume create demo_backend_courses

# 4. 迁移数据
docker run --rm \
  -v $(pwd)/backend/uploads:/source:ro \
  -v demo_backend_uploads:/destination \
  alpine sh -c "cp -r /source/. /destination/"

docker run --rm \
  -v $(pwd)/backend/courses:/source:ro \
  -v demo_backend_courses:/destination \
  alpine sh -c "cp -r /source/. /destination/"

# 5. 启动容器
docker-compose up -d
```

---

## 迁移后验证

### 1. 检查容器状态
```bash
docker-compose ps
# 所有容器应显示 "Up" 状态
```

### 2. 检查数据在volume中
```bash
# 查看uploads volume
docker run --rm -v demo_backend_uploads:/data alpine ls -la /data

# 查看courses volume
docker run --rm -v demo_backend_courses:/data alpine ls -la /data
```

### 3. 检查容器内数据
```bash
# 进入backend容器
docker-compose exec backend bash

# 在容器内查看
ls -la /app/uploads
ls -la /app/courses
exit
```

### 4. 测试功能
```bash
# 测试API
curl http://localhost:8001/api/game-state

# 测试前端
curl http://localhost
```

---

## 删除本地代码前的最终检查清单

### ✅ 确认以下内容：

- [ ] 已完成数据迁移到named volumes
- [ ] 容器正常运行：`docker-compose ps`
- [ ] 数据在volume中：`docker volume inspect demo_backend_uploads`
- [ ] API正常工作：`curl http://localhost:8001/api/game-state`
- [ ] 前端正常显示：访问 `http://localhost`
- [ ] 可以上传新文件（测试）
- [ ] 可以生成新课程（测试）
- [ ] 已备份重要数据（可选但推荐）

### ✅ 可以安全删除的本地文件和目录：

```bash
# 前端（完全镜像化）
rm -rf frontend/src/
rm -rf frontend/node_modules/
rm -rf frontend/dist/

# 后端（已镜像化）
# ⚠️ 注意：不要删除app.py，因为需要用它重新构建镜像
# 如果确定不再需要重新构建，可以删除：
# rm backend/app.py

# 虚拟环境（不需要）
rm -rf backend/venv/

# 数据目录（迁移到volume后）
# ⚠️ 只在确认数据已在volume中后删除：
# rm -rf backend/uploads/
# rm -rf backend/courses/
```

### ⚠️ 必须保留的文件：

```bash
# Docker配置文件（必需）
docker-compose.yml          # Docker Compose配置
backend/Dockerfile          # 后端镜像构建文件
frontend/Dockerfile         # 前端镜像构建文件
frontend/nginx.conf         # Nginx配置

# 依赖文件（重新构建时需要）
backend/requirements.txt    # Python依赖
frontend/package.json       # Node依赖
frontend/package-lock.json  # Node依赖锁定

# 源代码（如果要重新构建镜像）
backend/app.py              # 后端源代码（保留用于重新构建）
frontend/src/               # 前端源代码（保留用于重新构建）

# CI/CD配置（如果有）
Jenkinsfile                 # Jenkins pipeline配置
```

---

## 重新构建镜像（如果需要）

如果修改了代码并需要重新构建镜像：

```bash
# 停止容器
docker-compose down

# 重新构建并启动
docker-compose up -d --build

# 或者只重新构建特定服务
docker-compose build backend
docker-compose build frontend
docker-compose up -d
```

---

## 数据恢复（如果需要）

如果误删了本地数据，可以从volume恢复：

```bash
# 恢复uploads
docker run --rm \
  -v demo_backend_uploads:/source \
  -v $(pwd)/backend:/destination \
  alpine sh -c "cp -r /source/. /destination/uploads/"

# 恢复courses
docker run --rm \
  -v demo_backend_courses:/source \
  -v $(pwd)/backend:/destination \
  alpine sh -c "cp -r /source/. /destination/courses/"
```

---

## 备份Volumes

定期备份named volumes：

```bash
# 备份uploads volume
docker run --rm \
  -v demo_backend_uploads:/data:ro \
  -v $(pwd):/backup \
  alpine tar czf /backup/uploads_backup_$(date +%Y%m%d).tar.gz -C /data .

# 备份courses volume
docker run --rm \
  -v demo_backend_courses:/data:ro \
  -v $(pwd):/backup \
  alpine tar czf /backup/courses_backup_$(date +%Y%m%d).tar.gz -C /data .
```

---

## 常见问题

### Q: 删除本地代码后，如何修改代码？
A: 需要重新克隆代码库，修改后重新构建镜像：`docker-compose build && docker-compose up -d`

### Q: 如何查看volume中存储了多少数据？
A: `docker system df -v` 或 `docker volume inspect demo_backend_uploads`

### Q: 如何清理不再需要的volumes？
A: `docker volume rm demo_backend_uploads demo_backend_courses`（⚠️ 会删除所有数据）

### Q: 如何在不同的Docker主机间迁移volumes？
A: 使用`docker volume export/import`或备份tar文件

---

## 总结

### 当前配置状态：
- ✅ **前端代码**：已完全镜像化
- ✅ **后端代码**：已完全镜像化
- ⚠️ **数据目录**：已配置为named volumes，但**需要运行迁移脚本**将现有数据迁移到volumes

### 迁移后的状态：
- ✅ 所有代码在Docker镜像中
- ✅ 所有数据在Docker volumes中
- ✅ 删除本地代码**完全安全**（但建议保留源代码用于重新构建）

### 推荐操作：
1. 运行 `./migrate-to-volumes.sh` 迁移数据
2. 验证功能正常
3. 备份重要数据
4. 删除本地代码（但保留源代码和配置文件用于重新构建）

---

*最后更新：2025年11月*

