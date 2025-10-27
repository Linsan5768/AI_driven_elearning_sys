// 测试Ollama API题目生成功能
const testOllama = async () => {
  const prompt = `你是一个专业的计算机科学教师。请基于以下课程资料，生成一道高质量的选择题。

课程主题：计算机网络基础
课程资料：
- OSI七层模型：应用层、表示层、会话层、传输层、网络层、数据链路层、物理层
- TCP/IP协议栈：应用层、传输层、网络层、网络接口层
- IP地址分类：A类、B类、C类、D类、E类
- 子网掩码和CIDR表示法

要求：
1. 生成一个基于课程资料的具体问题
2. 提供4个选项（A、B、C、D），其中只有一个是正确答案
3. 正确答案应该是选项的索引（0、1、2或3）
4. 提供详细的解释说明

请严格按照以下JSON格式返回，不要添加任何其他内容：
{
  "question": "问题内容",
  "options": ["选项A", "选项B", "选项C", "选项D"],
  "correctAnswer": 0,
  "explanation": "详细解释说明"
}

注意：correctAnswer必须是数字0、1、2或3，对应选项的索引位置。`

  try {
    console.log('发送提示词到Ollama...')
    const response = await fetch('http://localhost:11434/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'mistral',
        prompt: prompt,
        stream: false,
        options: {
          temperature: 0.7,
          top_p: 0.9
        }
      })
    })

    if (response.ok) {
      const data = await response.json()
      console.log('Ollama响应:', data.response)
      
      // 尝试解析JSON
      try {
        const cleanResponse = data.response.trim()
        const jsonMatch = cleanResponse.match(/\{[\s\S]*\}/)
        if (jsonMatch) {
          const questionData = JSON.parse(jsonMatch[0])
          console.log('成功解析题目:', questionData)
          console.log('问题:', questionData.question)
          console.log('选项:', questionData.options)
          console.log('正确答案:', questionData.correctAnswer)
          console.log('解释:', questionData.explanation)
        } else {
          console.log('未找到JSON格式')
        }
      } catch (parseError) {
        console.error('JSON解析失败:', parseError)
      }
    } else {
      console.error('API调用失败:', response.status)
    }
  } catch (error) {
    console.error('请求失败:', error)
  }
}

testOllama()


