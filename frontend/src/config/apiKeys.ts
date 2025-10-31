// API key configuration
// Note: In production, these keys should be managed via environment variables

export const API_KEYS = {
  // Claude API key (get from https://console.anthropic.com/)
  CLAUDE_API_KEY: 'your_claude_api_key_here',
  
  // OpenAI API key (optional)
  OPENAI_API_KEY: 'your_openai_api_key_here',
  
  // Google AI API key (optional)
  GOOGLE_AI_API_KEY: 'your_google_ai_api_key_here',
  
  // Hugging Face API key (optional)
  HUGGINGFACE_API_KEY: 'your_huggingface_api_key_here'
}

// Model configuration
export const MODEL_CONFIG = {
  // Local models (no API key required)
  LOCAL_MODELS: {
    'qwen2.5': 'qwen2.5:7b',
    'deepseek-r1': 'deepseek-r1:8b',
    'mistral': 'mistral',
    'llama2': 'llama2'
  },
  
  // Online models (API key required)
  CLOUD_MODELS: {
    'claude-3.5': 'claude-3-5-sonnet-20241022',
    'gpt-4o': 'gpt-4o',
    'gemini-1.5': 'gemini-1.5-pro'
  }
}

// Check whether API key is configured
export const checkAPIKey = (model: string): boolean => {
  switch (model) {
    case 'claude-3.5':
      return API_KEYS.CLAUDE_API_KEY !== 'your_claude_api_key_here'
    case 'gpt-4o':
      return API_KEYS.OPENAI_API_KEY !== 'your_openai_api_key_here'
    case 'gemini-1.5':
      return API_KEYS.GOOGLE_AI_API_KEY !== 'your_google_ai_api_key_here'
    default:
      return true // Local models do not require an API key
  }
}


