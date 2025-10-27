// API密钥配置
// 注意：在生产环境中，这些密钥应该通过环境变量管理

export const API_KEYS = {
  // Claude API密钥 (从 https://console.anthropic.com/ 获取)
  CLAUDE_API_KEY: 'your_claude_api_key_here',
  
  // OpenAI API密钥 (可选)
  OPENAI_API_KEY: 'your_openai_api_key_here',
  
  // Google AI API密钥 (可选)
  GOOGLE_AI_API_KEY: 'your_google_ai_api_key_here',
  
  // Hugging Face API密钥 (可选)
  HUGGINGFACE_API_KEY: 'your_huggingface_api_key_here'
}

// 模型配置
export const MODEL_CONFIG = {
  // 本地模型 (无需API密钥)
  LOCAL_MODELS: {
    'qwen2.5': 'qwen2.5:7b',
    'deepseek-r1': 'deepseek-r1:8b',
    'mistral': 'mistral',
    'llama2': 'llama2'
  },
  
  // 联网模型 (需要API密钥)
  CLOUD_MODELS: {
    'claude-3.5': 'claude-3-5-sonnet-20241022',
    'gpt-4o': 'gpt-4o',
    'gemini-1.5': 'gemini-1.5-pro'
  }
}

// 检查API密钥是否配置
export const checkAPIKey = (model: string): boolean => {
  switch (model) {
    case 'claude-3.5':
      return API_KEYS.CLAUDE_API_KEY !== 'your_claude_api_key_here'
    case 'gpt-4o':
      return API_KEYS.OPENAI_API_KEY !== 'your_openai_api_key_here'
    case 'gemini-1.5':
      return API_KEYS.GOOGLE_AI_API_KEY !== 'your_google_ai_api_key_here'
    default:
      return true // 本地模型不需要API密钥
  }
}


