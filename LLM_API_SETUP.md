# 🤖 LLM API 配置指南

## 📋 推荐的免费LLM API

### 1. 🏠 Ollama (最推荐)

**安装步骤：**
```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows - 下载安装包
# https://ollama.ai/download
```

**下载模型：**
```bash
# 下载 Llama2 7B (4GB)
ollama pull llama2

# 下载 Mistral 7B (4GB) 
ollama pull mistral

# 下载 Code Llama (4GB)
ollama pull codellama

# 下载更小的模型 (1.9GB)
ollama pull llama2:7b-chat-q4_0
```

**测试API：**
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama2",
  "prompt": "Why is the sky blue?",
  "stream": false
}'
```

### 2. 🤗 Hugging Face Inference API

**注册步骤：**
1. 访问 https://huggingface.co
2. 免费注册账号
3. 前往 Settings > Access Tokens
4. 创建新的 Token

**配置：**
```bash
# 在 frontend 目录创建 .env 文件
echo "REACT_APP_HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxxxxxxxxx" > .env
```

**免费额度：**
- 每月1000次API调用
- 多种预训练模型
- 无需信用卡

### 3. 💻 LM Studio (本地GUI)

**安装：**
1. 下载：https://lmstudio.ai
2. 安装并运行
3. 下载模型（推荐：Llama 2 7B Chat）
4. 启动本地服务器（端口1234）

**特点：**
- 图形化界面
- 本地运行，隐私安全
- OpenAI兼容API

### 4. 🌐 Together AI

**注册：**
1. 访问 https://api.together.xyz
2. 注册免费账号
3. 获取API密钥

**免费额度：**
- $25免费额度
- 多种开源模型
- 云端推理

## 🔧 项目配置

### 环境变量设置

在 `frontend` 目录创建 `.env` 文件：

```env
# Hugging Face API Key
REACT_APP_HUGGINGFACE_API_KEY=hf_your_token_here

# Together AI API Key (可选)
REACT_APP_TOGETHER_API_KEY=your_together_key_here

# 本地服务配置
REACT_APP_OLLAMA_HOST=http://localhost:11434
REACT_APP_LMSTUDIO_HOST=http://localhost:1234
```

### 推荐配置组合

**方案一：纯本地（最佳隐私）**
- Ollama + Mistral 7B
- 完全免费，无API限制
- 需要8GB RAM

**方案二：混合使用**
- Ollama (主要) + Hugging Face (备用)
- 本地优先，云端备份
- 平衡性能和可用性

**方案三：云端为主**
- Hugging Face + Together AI
- 无需本地资源
- 受API限制

## 🚀 快速开始

### 选择 Ollama (推荐)

```bash
# 1. 安装 Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. 下载模型
ollama pull mistral

# 3. 启动游戏
cd backend && python app.py
cd frontend && npm run dev

# 4. 选择 "Ollama - Mistral 7B" 模型
```

### 选择 Hugging Face

```bash
# 1. 注册并获取 API Key
# 2. 配置环境变量
echo "REACT_APP_HUGGINGFACE_API_KEY=hf_your_key" > frontend/.env

# 3. 启动游戏
cd backend && python app.py
cd frontend && npm run dev

# 4. 选择 "Hugging Face" 模型
```

## 📊 模型对比

| 模型 | 大小 | 速度 | 质量 | 成本 | 隐私 |
|------|------|------|------|------|------|
| Ollama Mistral | 4GB | 快 | 高 | 免费 | 完全 |
| Ollama Llama2 | 4GB | 快 | 高 | 免费 | 完全 |
| HuggingFace | 0 | 中 | 中 | 限额 | 一般 |
| Together AI | 0 | 快 | 高 | 限额 | 一般 |
| LM Studio | 4GB+ | 快 | 高 | 免费 | 完全 |

## 🛠️ 故障排除

### Ollama 连接失败
```bash
# 检查服务状态
ollama list

# 重启服务
ollama serve

# 测试连接
curl http://localhost:11434/api/version
```

### Hugging Face API 错误
- 检查API密钥是否正确
- 确认免费额度未用完
- 检查模型名称是否正确

### 跨域问题
如果遇到CORS错误，在开发环境中是正常的，生产环境需要配置代理。

## 💡 使用建议

1. **开发测试**：使用模拟响应
2. **本地demo**：使用Ollama
3. **在线演示**：使用Hugging Face
4. **生产环境**：根据需求选择合适的服务

现在你的游戏已经支持真实的LLM API了！🎉


