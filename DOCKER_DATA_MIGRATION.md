# Docker数据持久化迁移指南

## 当前状态分析

### ✅ 已完全镜像化的部分
1. **前端代码** (`frontend/`)
   - 所有源代码在构建时COPY到Docker镜像
   - 构建产物（dist/）已打包到Nginx镜像
   - **删除本地代码完全安全**

2. **后端代码** (`backend/app.py`)
   - 源代码在构建时COPY到Docker镜像
   - **app.py删除本地代码完全安全**

### ⚠️ 使用本地目录挂载的部分（需要迁移）
1. **backend/uploads/** - 上传的文件
2. **backend/courses/** - 生成的课程JSON文件

这些目录使用bind mount，依赖本地文件系统。如果删除本地代码，这些数据会丢失。

---

## 迁移到Named Volumes（推荐方案）

### 步骤1：停止容器

```bash
cd /Users/lin/Uni/2025S2/ELEC5620/demo
docker-compose down
```

### 步骤2：备份现有数据（可选，但强烈推荐）

```bash
# 备份uploads目录
tar -czf backend_uploads_backup_$(date +%Y%m%d_%H%M%S).tar.gz backend/uploads/

# 备份courses目录
tar -czf backend_courses_backup_$(date +%Y%m%d_%H%M%S).tar.gz backend/courses/
```

### 步骤3：迁移数据到Named Volume

我已经更新了`docker-compose.yml`，将bind mount改为named volumes。现在需要迁移数据：

```bash
# 方法1：使用临时容器迁移（推荐）
# 1. 创建named volumes（docker-compose会自动创建，但我们可以先创建）
docker volume create demo_backend_uploads
docker volume create demo_backend_courses

# 2. 创建临时容器来复制数据
docker run --rm -v $(pwd)/backend/uploads:/source -v demo_backend_uploads:/destination alpine sh -c "cp -r /source/. /destination/"
docker run --rm -v $(pwd)/backend/courses:/source -v demo_backend_courses:/destination alpine sh -c "cp -r /source/. /destination/"

# 3. 更新docker-compose.yml中的volume名称（已更新）
# 确保volumes部分使用正确的名称：backend_uploads 和 backend_courses
```

### 步骤4：验证数据迁移

```bash
# 检查volume内容
docker run --rm -v demo_backend_uploads:/data alpine ls -la /data
docker run --rm -v demo_backend_courses:/data alpine ls -la /data
```

### 步骤5：重新启动容器

```bash
docker-compose up -d
```

### 步骤6：验证应用运行正常

```bash
# 检查容器状态
docker-compose ps

# 检查后端健康
curl http://localhost:8001/api/game-state

# 检查前端
curl http://localhost
```

---

## 迁移后验证清单

- [ ] 容器正常启动
- [ ] 后端API响应正常
- [ ] 前端页面正常显示
- [ ] 上传的文件仍然存在
- [ ] 生成的课程仍然存在
- [ ] 可以上传新文件
- [ ] 可以生成新课程

---

## 迁移后删除本地代码

**⚠️ 重要警告**：只有确认以下内容后，才能安全删除本地代码：

### 可以安全删除的目录/文件：
1. ✅ `frontend/src/` - 源代码（已镜像化）
2. ✅ `frontend/node_modules/` - 依赖（已镜像化）
3. ✅ `frontend/dist/` - 构建产物（已镜像化）
4. ✅ `backend/app.py` - 源代码（已镜像化）
5. ✅ `backend/venv/` - Python虚拟环境（已镜像化）
6. ✅ `backend/uploads/` - 上传文件（迁移到volume后）
7. ✅ `backend/courses/` - 课程文件（迁移到volume后）

### 必须保留的文件：
1. ⚠️ `docker-compose.yml` - Docker配置
2. ⚠️ `backend/Dockerfile` - 后端镜像构建文件
3. ⚠️ `frontend/Dockerfile` - 前端镜像构建文件
4. ⚠️ `frontend/nginx.conf` - Nginx配置
5. ⚠️ `backend/requirements.txt` - Python依赖
6. ⚠️ `Jenkinsfile` - CI/CD配置（如果有）

### 删除前最终检查：

```bash
# 1. 确认数据在volume中
docker volume inspect demo_backend_uploads
docker volume inspect demo_backend_courses

# 2. 确认应用运行正常
docker-compose ps
curl http://localhost:8001/api/game-state

# 3. 备份docker-compose.yml和Dockerfile
cp docker-compose.yml docker-compose.yml.backup
cp backend/Dockerfile backend/Dockerfile.backup
cp frontend/Dockerfile frontend/Dockerfile.backup
```

---

## 数据恢复（如果需要）

如果需要从named volume恢复数据到本地：

```bash
# 恢复uploads
docker run --rm -v demo_backend_uploads:/source -v $(pwd)/backend:/destination alpine sh -c "cp -r /source/. /destination/uploads/"

# 恢复courses
docker run --rm -v demo_backend_courses:/source -v $(pwd)/backend:/destination alpine sh -c "cp -r /source/. /destination/courses/"
```

---

## 访问Volume数据

### 查看volume中的数据：

```bash
# 查看uploads
docker run --rm -v demo_backend_uploads:/data alpine ls -la /data

# 查看courses
docker run --rm -v demo_backend_courses:/data alpine ls -la /data
```

### 在容器内访问：

```bash
# 进入backend容器
docker exec -it magic-academy-backend bash

# 在容器内查看
ls -la /app/uploads
ls -la /app/courses
```

---

## 注意事项

1. **首次迁移**：需要手动将数据从本地目录复制到named volume
2. **后续构建**：修改代码后需要重新构建镜像：`docker-compose build`
3. **数据备份**：定期备份named volumes（使用`docker volume`命令）
4. **开发模式**：如果需要在开发时看到代码变化，可以考虑保留bind mount，但生产环境应使用named volumes

---

## 快速迁移脚本

创建并运行以下脚本自动完成迁移：

```bash
#!/bin/bash
# migrate-to-volumes.sh

set -e

echo "🔄 Stopping containers..."
docker-compose down

echo "📦 Creating volumes..."
docker volume create demo_backend_uploads 2>/dev/null || true
docker volume create demo_backend_courses 2>/dev/null || true

echo "📋 Migrating uploads data..."
if [ -d "backend/uploads" ] && [ "$(ls -A backend/uploads)" ]; then
    docker run --rm -v $(pwd)/backend/uploads:/source -v demo_backend_uploads:/destination alpine sh -c "cp -r /source/. /destination/ && echo 'Uploads migrated'"
else
    echo "No uploads to migrate"
fi

echo "📋 Migrating courses data..."
if [ -d "backend/courses" ] && [ "$(ls -A backend/courses)" ]; then
    docker run --rm -v $(pwd)/backend/courses:/source -v demo_backend_courses:/destination alpine sh -c "cp -r /source/. /destination/ && echo 'Courses migrated'"
else
    echo "No courses to migrate"
fi

echo "✅ Migration complete!"
echo "📝 Update docker-compose.yml volume names if needed:"
echo "   - demo_backend_uploads -> backend_uploads"
echo "   - demo_backend_courses -> backend_courses"
echo ""
echo "🚀 Start containers with: docker-compose up -d"
```

---

*最后更新：2025年11月*

