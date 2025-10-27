import React, { useState, useEffect, useRef } from 'react'
import styled from '@emotion/styled'
import { motion, AnimatePresence } from 'framer-motion'
import { COURSE_MATERIALS } from '../config/courseMaterials'
import type { Question } from '../config/courseMaterials'
import { API_KEYS, checkAPIKey } from '../config/apiKeys'

// 添加CSS动画样式
const globalStyles = `
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
  
  @keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
  }
`

// 注入全局样式
if (typeof document !== 'undefined') {
  const style = document.createElement('style')
  style.textContent = globalStyles
  document.head.appendChild(style)
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface AreaDialogProps {
  isOpen: boolean
  onClose: () => void
  areaId: string
  onComplete: () => void
}

const DialogOverlay = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
`

const DialogContent = styled(motion.div)`
  background: #1a1a1a;
  border-radius: 16px;
  padding: 24px;
  width: 90%;
  max-width: 700px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
  border: 2px solid #333;
`

const DialogHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid #333;
`

const DialogTitle = styled.h2`
  color: #ffffff;
  margin: 0;
  font-size: 24px;
  font-weight: bold;
`

const CloseButton = styled.button`
  background: #ff4757;
  color: white;
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  
  &:hover {
    background: #ff3742;
    transform: scale(1.1);
  }
`

const ChatContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  margin-bottom: 20px;
  padding: 16px;
  background: #2a2a2a;
  border-radius: 12px;
  border: 1px solid #444;
  min-height: 300px;
  max-height: 400px;
`

const MessageBubble = styled.div<{ $isUser: boolean }>`
  margin-bottom: 16px;
  display: flex;
  justify-content: ${props => props.$isUser ? 'flex-end' : 'flex-start'};
`

const MessageContent = styled.div<{ $isUser: boolean }>`
  background: ${props => props.$isUser ? '#64B5F6' : '#444'};
  color: #ffffff;
  padding: 12px 16px;
  border-radius: 18px;
  max-width: 80%;
  word-wrap: break-word;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  
  ${props => props.$isUser ? `
    border-bottom-right-radius: 6px;
  ` : `
    border-bottom-left-radius: 6px;
  `}
`

const MessageTime = styled.div<{ $isUser: boolean }>`
  font-size: 11px;
  color: #888;
  margin-top: 4px;
  text-align: ${props => props.$isUser ? 'right' : 'left'};
`

const InputContainer = styled.div`
  display: flex;
  gap: 12px;
  align-items: flex-end;
`

const MessageInput = styled.textarea`
  flex: 1;
  background: #333;
  color: #ffffff;
  border: 1px solid #555;
  border-radius: 8px;
  padding: 12px;
  font-size: 14px;
  resize: none;
  min-height: 44px;
  max-height: 120px;
  font-family: inherit;
  
  &:focus {
    outline: none;
    border-color: #64B5F6;
    box-shadow: 0 0 0 2px rgba(100, 181, 246, 0.2);
  }
  
  &::placeholder {
    color: #888;
  }
`

const SendButton = styled.button`
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 20px;
  cursor: pointer;
  font-size: 14px;
  font-weight: bold;
  transition: all 0.2s ease;
  white-space: nowrap;
  
  &:hover {
    background: #45a049;
    transform: translateY(-1px);
  }
  
  &:disabled {
    background: #666;
    cursor: not-allowed;
    transform: none;
  }
`

const CompleteButton = styled.button`
  background: #FF9800;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  cursor: pointer;
  font-size: 16px;
  font-weight: bold;
  margin-top: 20px;
  transition: all 0.2s ease;
  
  &:hover {
    background: #F57C00;
    transform: translateY(-1px);
  }
`

const LoadingIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  color: #888;
  font-size: 14px;
`

const Spinner = styled.div`
  width: 16px;
  height: 16px;
  border: 2px solid #444;
  border-top: 2px solid #64B5F6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`

const ProgressBar = styled.div`
  width: 100%;
  height: 8px;
  background: #333;
  border-radius: 4px;
  margin-bottom: 20px;
  overflow: hidden;
`

const ProgressFill = styled.div<{ $progress: number }>`
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #66BB6A);
  width: ${props => props.$progress}%;
  transition: width 0.3s ease;
`

// 使用配置文件中的课程资料

const AreaDialog: React.FC<AreaDialogProps> = ({ isOpen, onClose, areaId, onComplete }) => {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [taskProgress, setTaskProgress] = useState(0)
  const [isTestMode, setIsTestMode] = useState(false)
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null)

  const [learnedKnowledgePoints, setLearnedKnowledgePoints] = useState<Set<number>>(new Set())
  const [knowledgePointsList, setKnowledgePointsList] = useState<string[]>([])
  const [showThinking, setShowThinking] = useState(false)
  const [thinkingContent, setThinkingContent] = useState<string>('')
  const [testQuestions, setTestQuestions] = useState<Question[]>([])

  const [correctAnswers, setCorrectAnswers] = useState(0)
  const [selectedModel, setSelectedModel] = useState<string>('qwen2.5')
  const chatContainerRef = useRef<HTMLDivElement>(null)

  const courseData = COURSE_MATERIALS[areaId as keyof typeof COURSE_MATERIALS]
  const totalKnowledgePoints = courseData?.knowledgePointCount || 0
  const learningProgress = (learnedKnowledgePoints.size / totalKnowledgePoints) * 100

  useEffect(() => {
    if (isOpen && areaId) {
      initializeDialog()
    }
  }, [isOpen, areaId])

  const initializeDialog = async () => {
    setIsLoading(true)
    
    try {
      // 让LLM生成知识点列表
      const listPrompt = `你是一位经验丰富的${courseData?.subject || '计算机科学'}教授。请严格按照课程资料生成知识点列表。

【课程资料】：
${courseData?.materials.join('\n') || '基础知识'}

【任务】：根据上述课程资料，生成${totalKnowledgePoints}个知识点标题

【要求】：
1. 标题必须基于提供的课程资料内容
2. 使用小学生能理解的简单词汇
3. 按照学习难度从易到难排列
4. 每个标题不超过8个字
5. 严格按照格式输出

【输出格式】（严格按此格式）：
1. [知识点标题1]
2. [知识点标题2]
3. [知识点标题3]
4. [知识点标题4]
5. [知识点标题5]

请只输出上述格式，不要添加任何其他内容。`

      const response = await callRealLLMAPI(listPrompt, selectedModel)
      
      // 解析知识点列表
      const lines = response.split('\n').filter(line => line.trim())
      const points = lines.map(line => {
        const match = line.match(/\d+\.\s*(.+)/)
        return match ? match[1].trim() : line.trim()
      }).filter(point => point.length > 0)
      
      setKnowledgePointsList(points)

      const welcomeMessage: Message = {
        id: '1',
        role: 'assistant',
        content: `🎓 **欢迎来到 ${courseData?.subject || areaId} 区域！**

我是你的AI导师，将帮助你深入理解这个计算机科学主题。

**📚 课程信息：**
• **难度等级：** ${courseData?.difficulty === 'easy' ? '初级' : courseData?.difficulty === 'medium' ? '中级' : '高级'}
• **学科分类：** ${courseData?.category || '计算机科学'}
• **知识点数量：** ${totalKnowledgePoints}个

�� **本区域的知识点列表：**

${points.map((point, index) => `${index + 1}. ${point}`).join('\n')}

💡 **使用方法：**
• 输入数字（1-${totalKnowledgePoints}）来学习对应知识点
• 学完20%的知识点后可以参加测试
• 也可以直接跟我聊天，我会基于课程内容回答你的问题

请输入数字学习知识点，或者直接问我问题！`,
        timestamp: new Date()
      }
      
      setMessages([welcomeMessage])
      setTaskProgress(0)
      setIsTestMode(false)

      setSelectedAnswer(null)

      setLearnedKnowledgePoints(new Set())
      setTestQuestions([])

      setCorrectAnswers(0)
    } catch (error) {
      console.error('初始化失败:', error)
      // 使用默认知识点列表
      const defaultPoints = Array.from({ length: totalKnowledgePoints }, (_, i) => `知识点${i + 1}`)
      setKnowledgePointsList(defaultPoints)
      
      const welcomeMessage: Message = {
        id: '1',
        role: 'assistant',
        content: `🎓 **欢迎来到 ${courseData?.subject || areaId} 区域！**

我是你的AI导师，将帮助你深入理解这个计算机科学主题。

**📚 课程信息：**
• **难度等级：** ${courseData?.difficulty === 'easy' ? '初级' : courseData?.difficulty === 'medium' ? '中级' : '高级'}
• **学科分类：** ${courseData?.category || '计算机科学'}
• **知识点数量：** ${totalKnowledgePoints}个

📚 **本区域的知识点列表：**

${defaultPoints.map((point, index) => `${index + 1}. ${point}`).join('\n')}

💡 **使用方法：**
• 输入数字（1-${totalKnowledgePoints}）来学习对应知识点
• 学完20%的知识点后可以参加测试
• 也可以直接跟我聊天，我会基于课程内容回答你的问题

请输入数字学习知识点，或者直接问我问题！`,
        timestamp: new Date()
      }
      setMessages([welcomeMessage])
      setTaskProgress(0)
      setIsTestMode(false)

      setSelectedAnswer(null)

      setLearnedKnowledgePoints(new Set())
      setTestQuestions([])

      setCorrectAnswers(0)
    } finally {
      setIsLoading(false)
      setThinkingContent('')
    }
  }

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const userInput = inputMessage.trim()
      const knowledgePointNumber = parseInt(userInput)
      
      if (!isNaN(knowledgePointNumber) && knowledgePointNumber >= 1 && knowledgePointNumber <= totalKnowledgePoints) {
        // 学习知识点
        await learnKnowledgePoint(knowledgePointNumber)
      } else if (isTestMode && testQuestions.length > 0) {
        // 处理测试答案
        await handleTestAnswer(userInput)
      } else if (userInput.toLowerCase() === '测试') {
        // 开始测试
        await startTest()
      } else {
        // 正常聊天 - 基于当前区域知识点
        await handleChatMessage(userInput)
      }
    } catch (error) {
      console.error('处理消息失败:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `❌ **出错了**

抱歉，处理你的消息时出现了错误。请稍后再试。`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const learnKnowledgePoint = async (pointNumber: number) => {
    const pointTitle = knowledgePointsList[pointNumber - 1] || `知识点${pointNumber}`
    
    // 让LLM生成知识点内容
    const contentPrompt = `你是专业的${courseData?.subject || '计算机科学'}教授，需要讲解知识点"${pointTitle}"。

【课程资料】：
${courseData?.materials.join('\n') || '基础知识'}

【教学要求】：
1. 严格基于课程资料内容，不能编造
2. 使用清晰易懂的术语，适合大学生理解
3. 包含1-2个具体例子帮助理解
4. 控制在100字以内，简洁明了
5. 可以适当使用专业术语，但要解释清楚

【教学格式】：
先解释概念，再举例说明，最后总结要点。

【输出要求】：
直接输出教学内容，不要添加标题或前缀。`

    const content = await callRealLLMAPI(contentPrompt, selectedModel)
    
    setLearnedKnowledgePoints(prev => new Set([...prev, pointNumber]))
    
    const learnMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: `📖 **知识点 ${pointNumber}：${pointTitle}**

${content}

---

✅ **学习完成！**
• 当前学习进度：${learnedKnowledgePoints.size + 1}/${totalKnowledgePoints} (${Math.round(((learnedKnowledgePoints.size + 1) / totalKnowledgePoints) * 100)}%)

${(learnedKnowledgePoints.size + 1) / totalKnowledgePoints >= 0.2 ? '🎉 **恭喜！** 你已经学完了20%的知识点，可以参加测试了！' : '💡 继续学习其他知识点吧！'}`,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, learnMessage])
    setTaskProgress(Math.min(90, ((learnedKnowledgePoints.size + 1) / totalKnowledgePoints) * 100))
    setThinkingContent('')
  }

  const handleTestAnswer = async (userInput: string) => {
    const answerString = userInput.trim().toUpperCase()
    
    // 检查是否是5个字母的批量答案
    if (answerString.length === 5 && testQuestions.length === 5) {
      // 批量处理答案
      const userAnswers = answerString.split('')
      const answerNumbers: number[] = []
      
      // 验证每个答案都是ABCD
      for (let i = 0; i < 5; i++) {
        const letter = userAnswers[i]
        let answerNumber = -1
        switch (letter) {
          case 'A': answerNumber = 0; break
          case 'B': answerNumber = 1; break
          case 'C': answerNumber = 2; break
          case 'D': answerNumber = 3; break
          default: answerNumber = -1
        }
        
        if (answerNumber === -1) {
          const errorMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: `❌ **输入错误**

请输入5个字母的答案组合，每个字母必须是A、B、C或D。
例如：ABCDA`,
            timestamp: new Date()
          }
          setMessages(prev => [...prev, errorMessage])
          return
        }
        answerNumbers.push(answerNumber)
      }
      
      // 计算正确答案数
      let correctCount = 0
      const results: { question: Question, userAnswer: number, isCorrect: boolean }[] = []
      
      for (let i = 0; i < 5; i++) {
        const question = testQuestions[i]
        const userAnswer = answerNumbers[i]
        const isCorrect = userAnswer === question.correctAnswer
        if (isCorrect) correctCount++
        
        results.push({
          question,
          userAnswer,
          isCorrect
        })
      }
      
      setCorrectAnswers(correctCount)
      
      // 显示详细结果
      const detailedResults = results.map((result, index) => {
        const { question, userAnswer, isCorrect } = result
        return `**第${index + 1}题：** ${isCorrect ? '✅ 正确' : '❌ 错误'}
题目：${question.question}
你的答案：${['A', 'B', 'C', 'D'][userAnswer]}. ${question.options[userAnswer]}
正确答案：${['A', 'B', 'C', 'D'][question.correctAnswer]}. ${question.options[question.correctAnswer]}
解释：${question.explanation}`
      }).join('\n\n')
      
      const finalScore = (correctCount / 5) * 100
      
      const resultMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `📊 **测试结果详情**

${detailedResults}

**📋 总结：**
正确题数：${correctCount}/5
正确率：${finalScore}%`,
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, resultMessage])
      
      // 判断是否通过测试
      if (finalScore >= 20) {
        setTaskProgress(100)
        const completeMessage: Message = {
          id: (Date.now() + 2).toString(),
          role: 'assistant',
          content: `🎉 **测试通过！恭喜你！**

✅ 你已经达到了20%的正确率，可以完成这个区域的学习了！

点击"完成任务"按钮继续下一个区域的探索。`,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, completeMessage])
        setIsTestMode(false)
        
        // 调用完成回调
        setTimeout(() => {
          onComplete()
        }, 1000)
      } else {
        const failMessage: Message = {
          id: (Date.now() + 2).toString(),
          role: 'assistant',
          content: `😔 **测试未通过**

❌ 你需要达到20%的正确率才能完成区域学习。
建议重新学习知识点后再次测试。

请继续学习相关知识点，或者重新开始测试。`,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, failMessage])
        setIsTestMode(false)
      }
      
      return
    }
    
    // 如果不是批量答案，显示错误信息
    const errorMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: `❌ **输入格式错误**

请输入5个字母的答案组合，例如：ABCDA
（第1题选A，第2题选B，第3题选C，第4题选D，第5题选A）`,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, errorMessage])
  }

  const startTest = async () => {
    if (!courseData || learnedKnowledgePoints.size < Math.ceil(totalKnowledgePoints * 0.2)) {
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `⚠️ **无法开始测试**

你需要先学完20%的知识点才能参加测试。

**当前进度：** ${learnedKnowledgePoints.size}/${totalKnowledgePoints} (${Math.round((learnedKnowledgePoints.size / totalKnowledgePoints) * 100)}%)

请继续学习更多知识点！`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
      return
    }

    // 开始测试，生成5个题目
    setIsTestMode(true)

    setSelectedAnswer(null)

    
    const testMessage: Message = {
      id: Date.now().toString(),
      role: 'assistant',
      content: `🧪 **开始测试！**

我将为你生成5道涵盖本区域知识点的题目。
每道题答完后会显示正确答案和解析。
答对1道题（20%）即可完成区域学习！

准备好了吗？让我开始生成题目...`,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, testMessage])
    
    // 一次性生成5道题目
    await generateAllQuestions()
  }

  const generateAllQuestions = async () => {
    // 显示思考过程
    if (showThinking) {
      setThinkingContent(`🎯 正在生成5道测试题目...\n🔍 分析所有学习过的知识点...\n❓ 设计综合性测试题目...\n📝 生成题目、选项和解析...`)
    }

    // 一次性生成5道题目
    const questions: Question[] = []
    const learnedPoints = Array.from(learnedKnowledgePoints)
    
    for (let i = 0; i < 5; i++) {
      // 为每道题随机选择一个知识点
      const randomPointNumber = learnedPoints[Math.floor(Math.random() * learnedPoints.length)]
      const pointTitle = knowledgePointsList[randomPointNumber - 1] || `知识点${randomPointNumber}`
      
      // 生成默认题目（跳过LLM验证，直接使用高质量默认题目）
      let question: Question
      if (pointTitle.includes('网络') || pointTitle.includes('协议') || pointTitle.includes('TCP') || pointTitle.includes('HTTP')) {
        question = {
          id: `q${i + 1}`,
          question: 'TCP协议相比UDP协议的主要优势是什么？',
          options: ['传输速度更快', '提供可靠的数据传输', '占用带宽更少', '支持广播传输'],
          correctAnswer: 1,
          explanation: 'TCP是面向连接的协议，提供可靠的数据传输服务，包括错误检测、重传机制等。'
        }
      } else if (pointTitle.includes('算法') || pointTitle.includes('数据结构') || pointTitle.includes('栈') || pointTitle.includes('队列')) {
        question = {
          id: `q${i + 1}`,
          question: '以下哪种数据结构遵循"后进先出"(LIFO)原则？',
          options: ['队列', '栈', '链表', '数组'],
          correctAnswer: 1,
          explanation: '栈是一种后进先出(LIFO)的数据结构，最后压入的元素最先弹出。'
        }
      } else if (pointTitle.includes('进程') || pointTitle.includes('线程') || pointTitle.includes('操作系统') || pointTitle.includes('死锁')) {
        question = {
          id: `q${i + 1}`,
          question: '死锁产生的必要条件不包括以下哪一项？',
          options: ['互斥条件', '占有等待', '可抢占', '循环等待'],
          correctAnswer: 2,
          explanation: '死锁的四个必要条件是：互斥、占有等待、非抢占、循环等待。可抢占不是死锁的必要条件。'
        }
      } else if (pointTitle.includes('数据库') || pointTitle.includes('SQL') || pointTitle.includes('事务') || pointTitle.includes('ACID')) {
        question = {
          id: `q${i + 1}`,
          question: '数据库事务的ACID特性中，"I"代表什么？',
          options: ['原子性(Atomicity)', '一致性(Consistency)', '隔离性(Isolation)', '持久性(Durability)'],
          correctAnswer: 2,
          explanation: 'ACID中的I代表隔离性(Isolation)，确保并发事务的执行不会相互干扰。'
        }
      } else {
        question = {
          id: `q${i + 1}`,
          question: '敏捷开发方法的核心思想是什么？',
          options: ['详细的文档规范', '严格的流程控制', '迭代开发和持续交付', '大型团队协作'],
          correctAnswer: 2,
          explanation: '敏捷开发强调迭代开发、持续交付、快速响应变化和团队协作。'
        }
      }
      
      questions.push(question)
    }
    
    // 设置生成的题目
    setTestQuestions(questions)


    
    // 显示所有题目
    const allQuestionsMessage: Message = {
      id: Date.now().toString(),
      role: 'assistant',
      content: `📝 **测试题目（共5题）**

${questions.map((q, index) => `**第${index + 1}题：**
${q.question}

A. ${q.options[0]}
B. ${q.options[1]}
C. ${q.options[2]}
D. ${q.options[3]}`).join('\n\n')}

**📋 答题方式：**
请一次性提交你的答案，格式如：ABCDA
（例如：如果你的答案是第1题选A，第2题选B，第3题选C，第4题选D，第5题选A，请输入"ABCDA"）`,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, allQuestionsMessage])
    setThinkingContent('')
  }

  const generateNextQuestion = async (retryCount = 0) => {
    // 最多重试2次，避免过度重试
    if (retryCount >= 2) {
      console.error('题目生成失败，使用高质量默认题目')
      
      // 根据知识点生成高质量的默认题目
      const learnedPoints = Array.from(learnedKnowledgePoints)
      const randomPointNumber = learnedPoints[Math.floor(Math.random() * learnedPoints.length)]
      const pointTitle = knowledgePointsList[randomPointNumber - 1] || `知识点${randomPointNumber}`
      
      // 生成不同类型的默认题目
      let defaultQuestion: Question
      if (pointTitle.includes('网络') || pointTitle.includes('协议')) {
        defaultQuestion = {
          id: Date.now().toString(),
          question: 'TCP协议的主要特点是什么？',
          options: ['无连接', '可靠传输', '不可靠传输', '广播通信'],
          correctAnswer: 1, // B. 可靠传输
          explanation: 'TCP是传输控制协议，提供可靠的数据传输服务。'
        }
      } else if (pointTitle.includes('算法') || pointTitle.includes('数据结构')) {
        defaultQuestion = {
          id: Date.now().toString(),
          question: '栈的数据结构特点是什么？',
          options: ['先进先出', '后进先出', '随机访问', '双向访问'],
          correctAnswer: 1, // B. 后进先出
          explanation: '栈是一种后进先出(LIFO)的数据结构。'
        }
      } else {
        defaultQuestion = {
          id: Date.now().toString(),
          question: `关于"${pointTitle}"，下列说法正确的是：`,
          options: ['选项A', '选项B', '选项C', '选项D'],
          correctAnswer: 0,
          explanation: '这是默认的解释。'
        }
      }
      
      
      setSelectedAnswer(null)


      const testMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `📝 **第${getCurrentQuestionNumber()}题**

**题目：**
${defaultQuestion.question}

**选项：**
A. ${defaultQuestion.options[0]}
B. ${defaultQuestion.options[1]}
C. ${defaultQuestion.options[2]}
D. ${defaultQuestion.options[3]}

请选择正确答案（回复A、B、C或D）：`,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, testMessage])
      setThinkingContent('')
      return
    }

    // 随机选择一个已学习的知识点
    const learnedPoints = Array.from(learnedKnowledgePoints)
    const randomPointNumber = learnedPoints[Math.floor(Math.random() * learnedPoints.length)]
    const pointTitle = knowledgePointsList[randomPointNumber - 1] || `知识点${randomPointNumber}`

    // 显示思考过程
    if (showThinking) {
      setThinkingContent(`🎯 正在为知识点"${pointTitle}"生成测试题目...\n🔍 分析知识点内容...\n❓ 设计题目和选项...\n📝 生成正确答案和解析...`)
    }

    // 让LLM生成选择题
    const questionPrompt = `你是经验丰富的计算机科学教授，需要为知识点"${pointTitle}"生成一道高质量选择题。

【课程资料】：
${courseData?.materials.join('\n') || '基础知识'}

【题目要求】：
1. 题目必须严格基于课程资料内容
2. 语言适合小学生理解
3. 4个选项中只有1个正确答案
4. 如果是数学题，必须仔细计算确保答案正确
5. 选项不能重复，要有适当迷惑性

【数学题特殊要求】：
- 题目中不能直接给出答案或暗示答案
- 选项只能包含算式，不能包含等号和结果
- 确保只有一个正确答案
- 其他选项必须是错误答案，不能是正确答案

【质量检查】：
- 数学题：请三次检查计算结果和选项唯一性
- 常识题：确保逻辑合理
- 解析必须与正确答案一致

【JSON格式】（严格按此格式输出，不要添加任何其他内容）：
{
  "question": "题目内容（简洁明了）",
  "options": ["选项1", "选项2", "选项3", "选项4"],
  "correctAnswer": 0,
  "explanation": "简短解析（与正确答案一致）"
}

【数学题示例】（参考格式）：
{
  "question": "下列哪个算式的结果是6？",
  "options": ["2×3", "1×5", "3×2", "2×4"],
  "correctAnswer": 0,
  "explanation": "2×3=6，其他算式的结果都不是6"
}

【重要提醒】：
- correctAnswer是数字：0=第一个选项，1=第二个选项，2=第三个选项，3=第四个选项
- 只输出JSON，不要添加任何其他文字、说明或解释
- 确保所有标点符号正确
- 不要换行，保持JSON格式完整`

    const response = await callRealLLMAPI(questionPrompt, selectedModel)
    
    try {
      // 解析JSON - 增加容错性
      const cleanResponse = response.trim()
      console.log('LLM原始响应:', cleanResponse)
      
      // 尝试多种JSON提取方式
      let jsonMatch = cleanResponse.match(/\{[\s\S]*\}/)
      if (!jsonMatch) {
        // 如果没找到完整JSON，尝试找到JSON开始
        const startIndex = cleanResponse.indexOf('{')
        if (startIndex !== -1) {
          const partialJson = cleanResponse.substring(startIndex)
          // 尝试补全JSON
          if (!partialJson.includes('}')) {
            // 如果缺少结束括号，尝试补全
            const completedJson = partialJson + '}'
            try {
              const testData = JSON.parse(completedJson)
              if (testData.question && testData.options) {
                jsonMatch = [completedJson]
              }
            } catch (e) {
              // 补全失败，继续尝试其他方法
            }
          } else {
            jsonMatch = [partialJson]
          }
        }
      }
      
      if (jsonMatch) {
        try {
          const questionData = JSON.parse(jsonMatch[0])
          console.log('解析的题目数据:', questionData)
          
          // 使用验证函数检查题目
          if (validateQuestion(questionData)) {
            
            setSelectedAnswer(null)
      

            const testMessage: Message = {
              id: Date.now().toString(),
              role: 'assistant',
              content: `📝 **第${getCurrentQuestionNumber()}题**

**题目：**
${questionData.question}

**选项：**
A. ${questionData.options[0]}
B. ${questionData.options[1]}
C. ${questionData.options[2]}
D. ${questionData.options[3]}

请选择正确答案（回复A、B、C或D）：`,
              timestamp: new Date()
            }

            setMessages(prev => [...prev, testMessage])
            setThinkingContent('')
            return
          } else {
            console.warn('生成的题目验证失败，重试中...', questionData)
            // 重试生成题目
            setTimeout(() => {
              generateNextQuestion(retryCount + 1)
            }, 1000)
            return
          }
        } catch (parseError) {
          console.error('JSON解析失败:', parseError, '尝试的JSON:', jsonMatch[0])
        }
      }
    } catch (error) {
      console.error('解析题目失败:', error)
    }

    // 如果LLM生成失败，重试
    setTimeout(() => {
      generateNextQuestion(retryCount + 1)
    }, 1000)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleComplete = () => {
    onComplete()
    onClose()
  }

  const handleChatMessage = async (userInput: string) => {
    const chatPrompt = `你是一位耐心的${courseData?.subject || '计算机科学'}教授。请基于课程资料准确回答学生问题。

【课程资料】：
${courseData?.materials.join('\n') || '基础知识'}

【学生问题】：${userInput}

【回答要求】：
1. 只能基于提供的课程资料回答
2. 使用小学生能理解的简单语言
3. 回答要准确、具体，避免模糊表述
4. 如果问题超出课程范围，请说"这个问题超出了我们当前的学习内容"
5. 回答要简洁，不超过100字
6. 可以用简单的例子帮助理解

【回答格式】：
直接回答问题，不要添加前缀或后缀。`

    const response = await callRealLLMAPI(chatPrompt, selectedModel)
    
    const chatMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: response,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, chatMessage])
  }

  const callRealLLMAPI = async (userInput: string, model: string = 'qwen2.5'): Promise<string> => {
    try {
      switch (model) {
        case 'claude-3.5':
          // 检查API密钥是否配置
          if (!checkAPIKey('claude-3.5')) {
            console.warn('Claude API密钥未配置，回退到本地模型')
            return await callLocalModel(userInput, 'qwen2.5')
          }
          
          // Claude 3.5 Sonnet API
          const claudeResponse = await fetch('https://api.anthropic.com/v1/messages', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'x-api-key': API_KEYS.CLAUDE_API_KEY,
              'anthropic-version': '2023-06-01'
            },
            body: JSON.stringify({
              model: 'claude-3-5-sonnet-20241022',
              max_tokens: 1000,
              messages: [
                {
                  role: 'user',
                  content: userInput
                }
              ]
            })
          })
          
          if (claudeResponse.ok) {
            const data = await claudeResponse.json()
            return data.content[0].text
          } else {
            console.error('Claude API调用失败:', claudeResponse.status)
            // 回退到本地模型
            return await callLocalModel(userInput)
          }
          break

        case 'qwen2.5':
        case 'deepseek-r1':
        case 'ollama-mistral':
        case 'ollama-llama2':
          return await callLocalModel(userInput, model)
          break

        default:
          return await callLocalModel(userInput, 'qwen2.5')
      }
    } catch (error) {
      console.error('API调用失败:', error)
      // 回退到本地模型
      return await callLocalModel(userInput, 'qwen2.5')
    }
  }

  const callLocalModel = async (userInput: string, model: string = 'qwen2.5'): Promise<string> => {
    const ollamaModel = model === 'qwen2.5' ? 'qwen2.5:7b' : 
                       model === 'deepseek-r1' ? 'deepseek-r1:8b' :
                       model.includes('mistral') ? 'mistral' : 'llama2'
    
    // 开始流式输出思考过程
    if (showThinking) {
      setThinkingContent('🤔 正在思考...\n')
    }
    
    const ollamaResponse = await fetch('http://localhost:11434/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: ollamaModel,
        prompt: userInput,
        stream: true,
        options: {
          temperature: 0.3,
          top_p: 0.8,
          top_k: 40,
          repeat_penalty: 1.1
        }
      })
    })
    
    if (ollamaResponse.ok) {
      const reader = ollamaResponse.body?.getReader()
      if (!reader) {
        throw new Error('无法读取响应流')
      }
      
      let fullResponse = ''
      const decoder = new TextDecoder()
      
      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          
          const chunk = decoder.decode(value)
          const lines = chunk.split('\n').filter(line => line.trim())
          
          for (const line of lines) {
            try {
              const data = JSON.parse(line)
              if (data.response) {
                fullResponse += data.response
                
                // 实时更新思考过程
                if (showThinking) {
                  setThinkingContent(prev => prev + data.response)
                }
              }
            } catch (e) {
              // 忽略非JSON行
            }
          }
        }
      } finally {
        reader.releaseLock()
      }
      
      return fullResponse
    } else {
      console.error('Ollama API调用失败:', ollamaResponse.status, ollamaResponse.statusText)
      return simulateLLMResponse(userInput, model)
    }
  }

  const simulateLLMResponse = async (userInput: string, model: string): Promise<string> => {
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000))
    
    const responses = {
      'ollama-mistral': [
        `作为Mistral 7B模型，我认为：${userInput} 这个话题很有趣。让我从技术角度来分析一下...`,
        `根据我的理解，${userInput} 涉及到几个关键概念。首先...`,
        `这是一个很有深度的问题。作为AI助手，我想分享一些见解：${userInput}...`
      ],
      'ollama-llama2': [
        `Llama2模型认为：${userInput} 是一个值得深入探讨的话题。`,
        `从我的角度来看，${userInput} 有以下几个层面...`,
        `这是一个很好的问题！让我用Llama2的视角来回答：${userInput}...`
      ],
      'huggingface': [
        `基于Hugging Face的开源模型，我对${userInput}的理解是...`,
        `这是一个复杂的话题。让我用开源AI的视角来分析：${userInput}...`,
        `作为开源AI助手，我认为${userInput}可以从以下角度考虑...`
      ],
      'openai-compatible': [
        `使用OpenAI兼容的API，我的回答是：${userInput} 这个问题...`,
        `基于兼容模型的训练，我认为${userInput}涉及到...`,
        `这是一个很好的问题！让我用兼容模型的视角来回答：${userInput}...`
      ]
    }
    
    const modelResponses = responses[model as keyof typeof responses] || responses['ollama-mistral']
    return modelResponses[Math.floor(Math.random() * modelResponses.length)]
  }

  const getCurrentQuestionNumber = () => {
    // 计算当前是第几题（基于测试开始后的用户回答数量）
    const testStartIndex = messages.findIndex(msg => msg.content.includes('开始测试！'))
    if (testStartIndex === -1) return 1
    
    const testMessages = messages.slice(testStartIndex)
    const userAnswers = testMessages.filter(msg => msg.role === 'user' && ['A', 'B', 'C', 'D'].includes(msg.content.trim().toUpperCase()))
    
    return userAnswers.length + 1
  }

  const getErrorAnalysis = () => {
    return `你答错了${5 - correctAnswers}道题。建议重新学习相关知识点，特别是那些你答错的题目内容。`
  }

  const validateQuestion = (questionData: any): boolean => {
    console.log('开始验证题目:', questionData)
    
    // 基本格式验证 - 放宽要求
    if (!questionData.question || !questionData.options || 
        !Array.isArray(questionData.options) || questionData.options.length !== 4) {
      console.warn('基本格式验证失败')
      return false
    }
    
    // 答案范围验证
    if (typeof questionData.correctAnswer !== 'number' || 
        questionData.correctAnswer < 0 || questionData.correctAnswer > 3) {
      console.warn('答案范围验证失败:', questionData.correctAnswer)
      return false
    }
    
    // 检查选项格式（不应该重复字母）
    const options = questionData.options
    for (let i = 0; i < options.length; i++) {
      const option = options[i]
      // 检查是否包含重复的字母标记
      if (option.includes(`(${String.fromCharCode(65 + i)})`) || 
          option.includes(`（${String.fromCharCode(65 + i)}）`) ||
          option.includes(`[${String.fromCharCode(65 + i)}]`) ||
          option.includes(`【${String.fromCharCode(65 + i)}】`)) {
        console.warn('选项包含重复字母标记:', option)
        return false
      }
      
      // 检查选项是否为空或太短 - 放宽要求
      if (!option.trim() || option.trim().length < 1) {
        console.warn('选项内容太短:', option)
        return false
      }
    }
    
    // 检查题目是否为空或太短 - 放宽要求
    if (!questionData.question.trim() || questionData.question.trim().length < 3) {
      console.warn('题目内容太短:', questionData.question)
      return false
    }
    
    // 检查数学题的答案一致性和唯一性
    const question = questionData.question.toLowerCase()
    const correctAnswer = questionData.correctAnswer
    
    if (question.includes('多少') || question.includes('等于') || question.includes('还剩') || 
        question.includes('+') || question.includes('-') || question.includes('×') || question.includes('乘') ||
        question.includes('颗') || question.includes('个') || question.includes('只')) {
      
      // 检查题目是否泄露答案
      if (question.includes('等于4') || question.includes('等于3') || question.includes('等于2') || 
          question.includes('等于1') || question.includes('等于5') || question.includes('等于6')) {
        console.warn('题目泄露答案:', question)
        return false
      }
      
      // 检查选项格式 - 数学题选项不能包含等号和结果
      for (let i = 0; i < options.length; i++) {
        const option = options[i]
        if (option.includes('=') || option.includes('＝')) {
          console.warn('数学题选项包含等号:', option)
          return false
        }
      }
      
      // 检查选项唯一性 - 确保只有一个正确答案
      const results = []
      for (let i = 0; i < options.length; i++) {
        const option = options[i]
        const numbers = option.match(/\d+/g)
        if (numbers && numbers.length >= 2) {
          const num1 = parseInt(numbers[0])
          const num2 = parseInt(numbers[1])
          
          let result = 0
          if (option.includes('×') || option.includes('乘')) {
            result = num1 * num2
          } else if (option.includes('+') || option.includes('加')) {
            result = num1 + num2
          } else if (option.includes('-') || option.includes('减')) {
            result = num1 - num2
          } else if (option.includes('÷') || option.includes('除')) {
            result = num1 / num2
          }
          results.push(result)
        }
      }
      
      // 检查是否有重复的结果
      const uniqueResults = new Set(results)
      if (uniqueResults.size !== results.length) {
        console.warn('数学题有多个正确答案:', results)
        return false
      }
      
      // 检查正确答案是否唯一
      const correctOption = options[correctAnswer]
      const correctNumbers = correctOption.match(/\d+/g)
      if (correctNumbers && correctNumbers.length >= 2) {
        const num1 = parseInt(correctNumbers[0])
        const num2 = parseInt(correctNumbers[1])
        
        let correctResult = 0
        if (correctOption.includes('×') || correctOption.includes('乘')) {
          correctResult = num1 * num2
        } else if (correctOption.includes('+') || correctOption.includes('加')) {
          correctResult = num1 + num2
        } else if (correctOption.includes('-') || correctOption.includes('减')) {
          correctResult = num1 - num2
        } else if (correctOption.includes('÷') || correctOption.includes('除')) {
          correctResult = num1 / num2
        }
        
        // 检查其他选项是否也是正确答案
        for (let i = 0; i < options.length; i++) {
          if (i === correctAnswer) continue
          
          const otherOption = options[i]
          const otherNumbers = otherOption.match(/\d+/g)
          if (otherNumbers && otherNumbers.length >= 2) {
            const num1 = parseInt(otherNumbers[0])
            const num2 = parseInt(otherNumbers[1])
            
            let otherResult = 0
            if (otherOption.includes('×') || otherOption.includes('乘')) {
              otherResult = num1 * num2
            } else if (otherOption.includes('+') || otherOption.includes('加')) {
              otherResult = num1 + num2
            } else if (otherOption.includes('-') || otherOption.includes('减')) {
              otherResult = num1 - num2
            } else if (otherOption.includes('÷') || otherOption.includes('除')) {
              otherResult = num1 / num2
            }
            
            if (otherResult === correctResult) {
              console.warn('数学题有多个正确答案:', { correctResult, otherResult, correctOption, otherOption })
              return false
            }
          }
        }
      }
    }
    
    // 检查选项是否有重复内容 - 只在完全相同时拒绝
    const optionSet = new Set(options.map((opt: string) => opt.trim().toLowerCase()))
    if (optionSet.size !== options.length) {
      console.warn('选项内容有重复:', options)
      return false
    }
    
    console.log('题目验证通过')
    return true
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <DialogOverlay
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <DialogContent
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
          >
            <DialogHeader>
              <DialogTitle>{areaId} 学习区域</DialogTitle>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  style={{
                    background: '#2a2a2a',
                    color: 'white',
                    border: '1px solid #444',
                    borderRadius: '6px',
                    padding: '6px 12px',
                    fontSize: '12px',
                    cursor: 'pointer'
                  }}
                >
                  <option value="qwen2.5">🤖 Qwen2.5 (本地)</option>
                  <option value="deepseek-r1">🧠 DeepSeek R1 (本地)</option>
                  <option value="claude-3.5">🌐 Claude 3.5 (联网)</option>
                  <option value="ollama-mistral">📚 Mistral (本地)</option>
                </select>
                <button
                  onClick={() => setShowThinking(!showThinking)}
                  style={{
                    background: showThinking ? '#4CAF50' : '#666',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '6px 12px',
                    fontSize: '12px',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                >
                  {showThinking ? '🧠 隐藏思考' : '🧠 显示思考'}
                </button>
                <CloseButton onClick={onClose}>×</CloseButton>
              </div>
            </DialogHeader>

            <ProgressBar>
              <ProgressFill $progress={learningProgress} />
            </ProgressBar>

            <div style={{ marginTop: '8px', fontSize: '12px', color: '#888' }}>
              学习进度：{learnedKnowledgePoints.size}/{totalKnowledgePoints} ({Math.round(learningProgress)}%)
              {learningProgress >= 40 && !isTestMode && (
                <div style={{ marginTop: '8px' }}>
                  <SendButton onClick={startTest} style={{ background: '#FF9800', fontSize: '12px', padding: '6px 12px' }}>
                    🧪 开始测试
                  </SendButton>
                </div>
              )}
            </div>

            <ChatContainer ref={chatContainerRef}>
              {messages.map((message) => (
                <MessageBubble key={message.id} $isUser={message.role === 'user'}>
                  <div>
                    <MessageContent $isUser={message.role === 'user'}>
                      <div style={{
                        whiteSpace: 'pre-wrap',
                        lineHeight: '1.6',
                        fontFamily: 'system-ui, -apple-system, sans-serif'
                      }}>
                        {message.content.split('\n').map((line, index) => {
                          // 处理粗体文本
                          if (line.includes('**')) {
                            const parts = line.split(/(\*\*.*?\*\*)/g)
                            return (
                              <div key={index} style={{ marginBottom: '4px' }}>
                                {parts.map((part, partIndex) => {
                                  if (part.startsWith('**') && part.endsWith('**')) {
                                    return (
                                      <span key={partIndex} style={{ 
                                        fontWeight: 'bold',
                                        color: message.role === 'user' ? '#fff' : '#4CAF50'
                                      }}>
                                        {part.slice(2, -2)}
                                      </span>
                                    )
                                  }
                                  return <span key={partIndex}>{part}</span>
                                })}
                              </div>
                            )
                          }
                          // 处理分隔线
                          if (line.trim() === '---') {
                            return (
                              <div key={index} style={{
                                borderTop: '1px solid #333',
                                margin: '8px 0',
                                opacity: 0.6
                              }}></div>
                            )
                          }
                          // 处理列表项
                          if (line.trim().startsWith('•')) {
                            return (
                              <div key={index} style={{ 
                                marginLeft: '16px',
                                marginBottom: '2px'
                              }}>
                                {line}
                              </div>
                            )
                          }
                          // 普通文本
                          return <div key={index}>{line}</div>
                        })}
                      </div>
                    </MessageContent>
                    <MessageTime $isUser={message.role === 'user'}>
                      {message.timestamp.toLocaleTimeString()}
                    </MessageTime>
                  </div>
                </MessageBubble>
              ))}
               
              {isLoading && (
                <MessageBubble $isUser={false}>
                  <div>
                    <MessageContent $isUser={false}>
                      <LoadingIndicator>
                        <Spinner />
                        正在思考中...
                      </LoadingIndicator>
                    </MessageContent>
                  </div>
                </MessageBubble>
              )}

              {/* 思考过程显示 */}
              {showThinking && thinkingContent && (
                <MessageBubble $isUser={false}>
                  <div>
                    <MessageContent $isUser={false}>
                      <div style={{ 
                        background: '#1a1a1a', 
                        padding: '16px', 
                        borderRadius: '12px',
                        border: '1px solid #333',
                        fontFamily: 'system-ui, -apple-system, sans-serif',
                        fontSize: '14px',
                        lineHeight: '1.6',
                        whiteSpace: 'pre-wrap',
                        color: '#e0e0e0',
                        position: 'relative'
                      }}>
                        <div style={{ 
                          color: '#4CAF50', 
                          fontWeight: '600', 
                          marginBottom: '12px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px'
                        }}>
                          <span style={{ fontSize: '16px' }}>🧠</span>
                          <span>AI思考过程</span>
                          <div style={{
                            width: '8px',
                            height: '8px',
                            background: '#4CAF50',
                            borderRadius: '50%',
                            animation: 'pulse 1.5s infinite'
                          }}></div>
                        </div>
                        <div style={{ 
                          borderLeft: '3px solid #4CAF50',
                          paddingLeft: '12px',
                          marginLeft: '4px'
                        }}>
                          {thinkingContent}
                          <span style={{ 
                            display: 'inline-block',
                            width: '2px',
                            height: '16px',
                            background: '#4CAF50',
                            animation: 'blink 1s infinite',
                            marginLeft: '2px'
                          }}></span>
                        </div>
                      </div>
                    </MessageContent>
                  </div>
                </MessageBubble>
              )}
            </ChatContainer>

            <InputContainer>
              <MessageInput
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder={isTestMode ? "请输入A、B、C或D选择答案..." : "输入数字学习知识点，或直接问我问题，或输入'测试'参加测试..."}
                disabled={isLoading}
              />
              <SendButton
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isLoading}
              >
                发送
              </SendButton>
            </InputContainer>

            {/* 开始测试按钮 */}
            {!isTestMode && messages.length >= 2 && (
              <div style={{ marginTop: '16px', textAlign: 'center' }}>
                <SendButton
                  onClick={startTest}
                  style={{ background: '#FF9800' }}
                  disabled={isLoading}
                >
                  🎯 开始小测试
                </SendButton>
              </div>
            )}

            {/* 测试模式提示 */}
            {isTestMode && (
              <div style={{ 
                marginTop: '16px', 
                padding: '12px', 
                background: '#2a2a2a', 
                borderRadius: '8px',
                border: '1px solid #FF9800',
                textAlign: 'center'
              }}>
                <div style={{ color: '#FF9800', fontWeight: 'bold', marginBottom: '8px' }}>
                  🧪 小测试时间
                </div>
                <div style={{ color: '#ffffff', fontSize: '14px' }}>
                  请回答小老师的问题。答对了就可以完成学习哦！
                </div>
              </div>
            )}

            {taskProgress === 100 && selectedAnswer !== null && (
              <CompleteButton onClick={handleComplete}>
                🎓 完成学习
              </CompleteButton>
            )}
          </DialogContent>
        </DialogOverlay>
      )}
    </AnimatePresence>
  )
}

export default AreaDialog
