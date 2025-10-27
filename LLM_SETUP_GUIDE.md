# 🤖 LLM模型设置指南

## 🌐 联网模型设置

### 1. Claude 3.5 Sonnet (推荐)
**特点**：推理能力强，中文优秀，联网搜索，价格合理

**设置步骤**：
1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 注册账号并创建API密钥
3. 复制API密钥
4. 编辑 `frontend/src/config/apiKeys.ts`
5. 将 `your_claude_api_key_here` 替换为你的真实API密钥

```typescript
export const API_KEYS = {
  CLAUDE_API_KEY: 'sk-ant-api03-...', // 你的真实API密钥
  // ...
}
```

### 2. GPT-4o (OpenAI)
**特点**：OpenAI最新模型，多模态，联网能力强

**设置步骤**：
1. 访问 [OpenAI Platform](https://platform.openai.com/)
2. 创建API密钥
3. 编辑配置文件，添加 `OPENAI_API_KEY`

### 3. Gemini 1.5 Pro (Google)
**特点**：Google模型，联网能力强，价格便宜

**设置步骤**：
1. 访问 [Google AI Studio](https://aistudio.google.com/)
2. 获取API密钥
3. 编辑配置文件，添加 `GOOGLE_AI_API_KEY`

## 🏠 本地模型 (无需设置)

### 已安装的模型：
- **Qwen2.5:7b** - 中文支持好，推理能力强
- **DeepSeek R1:8b** - 数学和推理能力强
- **Mistral:7b** - 通用性能好

### 检查本地模型：
```bash
ollama list
```

### 下载新模型：
```bash
# 下载更多模型
ollama pull llama3.2:3b
ollama pull codellama:7b
ollama pull phi3:mini
```

## 🎯 模型选择建议

### 学习场景：
- **数学题** → DeepSeek R1 或 Claude 3.5
- **中文内容** → Qwen2.5 或 Claude 3.5
- **复杂推理** → Claude 3.5 或 GPT-4o
- **快速回答** → 本地模型 (无需网络)

### 性能对比：
| 模型 | 中文支持 | 数学能力 | 推理能力 | 联网 | 价格 |
|------|----------|----------|----------|------|------|
| Claude 3.5 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | 中等 |
| GPT-4o | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | 高 |
| Qwen2.5 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ | 免费 |
| DeepSeek R1 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | 免费 |

## 🔧 故障排除

### 联网模型不工作：
1. 检查API密钥是否正确配置
2. 确认网络连接正常
3. 检查API配额是否用完
4. 查看浏览器控制台错误信息

### 本地模型不工作：
1. 确认Ollama服务正在运行：`ollama serve`
2. 检查模型是否已下载：`ollama list`
3. 重启Ollama服务

### 性能优化：
1. **本地模型**：关闭其他程序释放内存
2. **联网模型**：选择地理位置较近的服务器
3. **通用优化**：降低temperature参数提高准确性

## 🚀 快速开始

1. **配置API密钥**（可选）
2. **启动服务器**：
   ```bash
   cd backend && python app.py
   cd frontend && npm run dev
   ```
3. **选择模型**：在对话框顶部选择想要的模型
4. **开始学习**：享受高质量的AI教学体验！

## 💡 使用技巧

- **思考模式**：开启思考模式观察AI推理过程
- **模型切换**：可以随时切换不同模型比较效果
- **离线使用**：本地模型支持完全离线使用
- **联网增强**：联网模型可以获取最新信息


