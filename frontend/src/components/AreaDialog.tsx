import React, { useState, useEffect, useRef } from 'react'
import styled from '@emotion/styled'
import { motion, AnimatePresence } from 'framer-motion'
import { COURSE_MATERIALS } from '../config/courseMaterials'
import type { Question } from '../config/courseMaterials'
import { API_KEYS, checkAPIKey } from '../config/apiKeys'
import axios from 'axios'
import BattleScene from './BattleScene'

// Add CSS animation styles
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
const AvatarCircle = styled.div<{ side: 'left' | 'right'; src: string }>`
  position: fixed;
  top: 50%;
  ${props => props.side === 'left' ? 'left: 12%;' : 'right: 12%;'}
  transform: translateY(-50%);
  width: 384px; /* 3x */
  height: 384px; /* 3x */
  pointer-events: none; /* do not block dialog */
  z-index: 1000;

  &::after {
    content: '';
    position: absolute;
    inset: 0;
    background-image: url(${props => props.src});
    background-size: contain;
    background-repeat: no-repeat;
    background-position: center;
    image-rendering: pixelated;
  }
`

// Inject global styles
if (typeof document !== 'undefined') {
  const style = document.createElement('style')
  style.textContent = globalStyles
  document.head.appendChild(style)
}

// Load MathJax v3 once for TeX rendering (\\( ... \\), \\[ ... \\])
if (typeof window !== 'undefined' && !(window as any)._mathjaxLoaded) {
  ;(window as any).MathJax = {
    tex: {
      inlineMath: [['\\(', '\\)'], ['$', '$']],
      displayMath: [['\\[', '\\]'], ['$$', '$$']]
    },
    options: {
      skipHtmlTags: ['script','noscript','style','textarea','pre','code']
    }
  }
  const script = document.createElement('script')
  script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'
  script.async = true
  script.onload = () => { (window as any)._mathjaxLoaded = true }
  document.head.appendChild(script)
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
  height: 12px;
  background: #333;
  border-radius: 6px;
  margin-bottom: 12px;
  overflow: hidden;
  position: relative;
`

const ProgressFill = styled.div<{ $progress: number }>`
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #66BB6A);
  width: ${props => props.$progress}%;
  transition: width 0.3s ease;
`

const ProgressLabel = styled.div`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 12px;
  color: #ddd;
  pointer-events: none;
`

// 使用配置文件中的课程资料

const AreaDialog: React.FC<AreaDialogProps> = ({ isOpen, onClose, areaId, onComplete }) => {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isUserTyping, setIsUserTyping] = useState(false)
  const typingTimerRef = useRef<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [taskProgress, setTaskProgress] = useState(0)
  const [isTestMode, setIsTestMode] = useState(false)
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null)

  const [learnedKnowledgePoints, setLearnedKnowledgePoints] = useState<Set<number>>(new Set())
  const [knowledgePointsList, setKnowledgePointsList] = useState<string[]>([])
  const [showThinking, setShowThinking] = useState(true)  // 永久开启思考显示
  const [thinkingContent, setThinkingContent] = useState<string>('')
  const [testQuestions, setTestQuestions] = useState<Question[]>([])

  const [correctAnswers, setCorrectAnswers] = useState(0)
  const [selectedModel, setSelectedModel] = useState<string>('qwen2.5')
  const chatContainerRef = useRef<HTMLDivElement>(null)

  // Re-typeset math whenever messages update
  useEffect(() => {
    const mj = (window as any).MathJax
    if (mj && chatContainerRef.current) {
      mj.typesetPromise ? mj.typesetPromise([chatContainerRef.current]) : mj.typeset?.()
    }
  }, [messages])

  // Learned knowledge points (IDs)
  const [courseData, setCourseData] = useState<any>(null)
  
  // Battle scene state control
  const [showBattleScene, setShowBattleScene] = useState(false)
  const totalKnowledgePoints = courseData?.knowledgePointCount || 0
  const learningProgress = (learnedKnowledgePoints.size / totalKnowledgePoints) * 100

  // Fetch dynamic course data from backend API
  useEffect(() => {
    const fetchCourseData = async () => {
      try {
        console.log(`📚 Fetching course data: ${areaId}`)
        const response = await axios.get(`http://127.0.0.1:8001/api/course-library/${areaId}`)
        if (response.data) {
          setCourseData(response.data)
          console.log(`✅ Successfully loaded course: ${response.data.subject}`, response.data)
        }
      } catch (error) {
        console.log(`⚠️ API fetch failed, trying static data: ${areaId}`)
        // If API call fails, use static data as fallback
        const defaultData = COURSE_MATERIALS[areaId as keyof typeof COURSE_MATERIALS]
        if (defaultData) {
          setCourseData(defaultData)
          console.log(`📖 Using static course data`)
        }
      }
    }
    
    if (areaId) {
      fetchCourseData()
    }
  }, [areaId])

  useEffect(() => {
    if (isOpen && areaId && courseData) {
      // Clear previous session UI immediately to avoid showing stale records
      setMessages([])
      setThinkingContent('')
      setIsTestMode(false)
      setSelectedAnswer(null)
      initializeDialog()
    }
  }, [isOpen, areaId, courseData])

  const initializeDialog = async () => {
    setIsLoading(true)
    // Prevent showing previous records while loading new content
    setMessages([])
    
    try {
      // Fetch learned points from backend
      let restoredLearnedPoints: number[] = []
      const gameStateResponse = await axios.get('http://127.0.0.1:8001/api/game-state')
      if (gameStateResponse.data && gameStateResponse.data.areas[areaId]) {
        const areaData = gameStateResponse.data.areas[areaId]
        restoredLearnedPoints = areaData.learnedPoints || []
        // Restore learned points
        setLearnedKnowledgePoints(new Set(restoredLearnedPoints))
        console.log(`📚 Restored learning progress: ${areaId} - Learned ${restoredLearnedPoints.length} knowledge points`, restoredLearnedPoints)
      }
      
      // Let LLM generate knowledge points list
      const listPrompt = `You are a professor at the Magic Academy teaching ${courseData?.subject || 'Course'}. Generate a knowledge points list based strictly on the course materials. Always answer in English only.

【Course Materials】:
${courseData?.materials.join('\n') || 'Fundamental Knowledge'}

【Task】: Based on the above course materials, generate ${totalKnowledgePoints} knowledge point titles

【Requirements】:
1. Titles must be based on the provided course materials
2. Use professional and accurate computer science terminology, suitable for university level
3. Arrange from easy to difficult by learning difficulty
4. Each title should not exceed 8 words
5. Strictly follow the output format

【Output Format】 (strictly follow this format):
1. [Knowledge Point Title 1]
2. [Knowledge Point Title 2]
3. [Knowledge Point Title 3]
4. [Knowledge Point Title 4]
5. [Knowledge Point Title 5]

Please only output the above format without any additional content.`

      const response = await callRealLLMAPI(listPrompt, selectedModel)
      
      // Parse knowledge points list
      const lines = response.split('\n').filter(line => line.trim())
      const points = lines.map(line => {
        const match = line.match(/\d+\.\s*(.+)/)
        return match ? match[1].trim() : line.trim()
      }).filter(point => point.length > 0)
      
      setKnowledgePointsList(points)

      const currentProgress = Math.round((restoredLearnedPoints.length / totalKnowledgePoints) * 100)
      const progressMessage = restoredLearnedPoints.length > 0 
        ? `\n\n📊 **Learning Progress Restored:** ${restoredLearnedPoints.length}/${totalKnowledgePoints} (${currentProgress}%)\n✅ You previously learned: ${restoredLearnedPoints.map(p => `Point ${p}`).join(', ')}` 
        : ''

      const welcomeMessage: Message = {
        id: '1',
        role: 'assistant',
        content: `🔮 **Welcome to ${courseData?.subject || areaId} Magic Hall!**

Young apprentice, I am a professor at the Magic Academy, and I will guide you to master this knowledge.

**📚 Course Information:**
• **Difficulty Level:** ${courseData?.difficulty === 'easy' ? 'Beginner' : courseData?.difficulty === 'medium' ? 'Intermediate' : 'Advanced'}
• **Subject Category:** ${courseData?.category || 'Computer Science'}
• **Knowledge Points:** ${totalKnowledgePoints} points${progressMessage}

📚 **Knowledge Points in This Area:**

${points.map((point, index) => `${index + 1}. ${point}`).join('\n')}

💡 **How to Use:**
• Enter a number (1-${totalKnowledgePoints}) to learn the corresponding knowledge point
• After learning 20% of the knowledge points, you can take the test
• You can also chat with me directly, and I will answer your questions based on the course content

Please enter a number to learn a knowledge point, or ask me a question directly!`,
        timestamp: new Date()
      }
      
      setMessages([welcomeMessage])
      setTaskProgress(currentProgress)
      setIsTestMode(false)

      setSelectedAnswer(null)

      // Don't clear restored learning progress!
      // setLearnedKnowledgePoints(new Set())
      setTestQuestions([])

      setCorrectAnswers(0)
    } catch (error) {
      console.error('Initialization failed:', error)
      // Use default knowledge points list
      const defaultPoints = Array.from({ length: totalKnowledgePoints }, (_, i) => `Knowledge Point ${i + 1}`)
      setKnowledgePointsList(defaultPoints)
      
      // Use the current learnedKnowledgePoints state instead of restoredLearnedPoints
      const learnedPointsArray = Array.from(learnedKnowledgePoints)
      const currentProgress = Math.round((learnedPointsArray.length / totalKnowledgePoints) * 100)
      const progressMessage = learnedPointsArray.length > 0 
        ? `\n\n📊 **Learning Progress Restored:** ${learnedPointsArray.length}/${totalKnowledgePoints} (${currentProgress}%)\n✅ You previously learned: ${learnedPointsArray.map((p: number) => `Point ${p}`).join(', ')}` 
        : ''
      
      const welcomeMessage: Message = {
        id: '1',
        role: 'assistant',
        content: `🔮 **Welcome to ${courseData?.subject || areaId} Magic Hall!**

Young apprentice, I am a professor at the Magic Academy, and I will guide you to master this knowledge.

**📚 Course Information:**
• **Difficulty Level:** ${courseData?.difficulty === 'easy' ? 'Beginner' : courseData?.difficulty === 'medium' ? 'Intermediate' : 'Advanced'}
• **Subject Category:** ${courseData?.category || 'Computer Science'}
• **Knowledge Points:** ${totalKnowledgePoints} points${progressMessage}

📚 **Knowledge Points in This Area:**

${defaultPoints.map((point, index) => `${index + 1}. ${point}`).join('\n')}

💡 **How to Use:**
• Enter a number (1-${totalKnowledgePoints}) to learn the corresponding knowledge point
• After learning 20% of the knowledge points, you can take the test
• You can also chat with me directly, and I will answer your questions based on the course content

Please enter a number to learn a knowledge point, or ask me a question directly!`,
        timestamp: new Date()
      }
      setMessages([welcomeMessage])
      setTaskProgress(currentProgress)
      setIsTestMode(false)

      setSelectedAnswer(null)

      // Don't clear restored learning progress!
      // setLearnedKnowledgePoints(new Set())
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
        // Handle test answer
        await handleTestAnswer(userInput)
      } else if (userInput.toLowerCase() === 'test' || userInput.toLowerCase() === '测试') {
        // Start test
        await startTest()
      } else {
        // Normal chat - based on current area knowledge points
        await handleChatMessage(userInput)
      }
    } catch (error) {
      console.error('Failed to process message:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `❌ **Error Occurred**

Sorry, an error occurred while processing your message. Please try again later.`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const learnKnowledgePoint = async (pointNumber: number) => {
    const pointTitle = knowledgePointsList[pointNumber - 1] || `Knowledge Point ${pointNumber}`
    
    // Let LLM generate knowledge point content
    // Only get current knowledge point materials, don't include other points
    const currentPointMaterial = courseData?.materials[pointNumber - 1] || 'Fundamental Knowledge'
    
    const contentPrompt = `You are a professor at the Magic Academy teaching ${courseData?.subject || 'Course'}, instructing a young apprentice on the knowledge point "${pointTitle}". Always answer in English only and format headings in bold (Markdown).

【Current Lesson Materials】:
${currentPointMaterial}

【Important Notice】:
Only explain this ONE knowledge point, do not involve other knowledge points!

【Teaching Requirements】:
1. Strictly base your explanation on the provided materials; do not invent facts
2. Explain only this knowledge point; do not mention other points
3. Use precise yet friendly terminology; keep it accessible
4. Blend subtle Magic Academy flavor (mentor voice, light metaphors) while maintaining rigor
5. Include 1 concrete, real-world example (code/math when relevant)
6. End with 1 short "Try it" prompt for the apprentice
7. Keep within 150 words, concise and vivid

【Recommended Structure】 (use bold labels):
• **Essence**: one-sentence plain definition
• **Magic Analogy**: a brief, imaginative comparison (one sentence)
• **Example**: a clear, minimal example
• **Key Spell**: a distilled rule/formula/checklist (one line)
• **Try it**: one mini task (one line)

【Output Requirements】:
Write a single paragraph or short bullet list following the structure. No titles or prefixes.`

    const content = await callRealLLMAPI(contentPrompt, selectedModel)
    
    // Update learned knowledge points
    const newLearnedPoints = new Set([...learnedKnowledgePoints, pointNumber])
    setLearnedKnowledgePoints(newLearnedPoints)
    
    // Call backend API to update learning progress
    try {
      await axios.post(`http://127.0.0.1:8001/api/update-learning-progress/${areaId}`, {
        learnedPoints: Array.from(newLearnedPoints)
      })
    } catch (error) {
      console.error('Failed to update learning progress:', error)
    }
    
    const learnMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: `📖 **Knowledge Point ${pointNumber}: ${pointTitle}**

${content}

---

✅ **Learning Complete!**
• Current Learning Progress: ${newLearnedPoints.size}/${totalKnowledgePoints} (${Math.round((newLearnedPoints.size / totalKnowledgePoints) * 100)}%)

${newLearnedPoints.size / totalKnowledgePoints >= 0.2 ? '🎉 **Congratulations!** You have completed 20% of the knowledge points and can now take the test!' : '💡 Continue learning other knowledge points!'}`,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, learnMessage])
    setTaskProgress(Math.min(90, (newLearnedPoints.size / totalKnowledgePoints) * 100))
    setThinkingContent('')
  }

  const handleTestAnswer = async (userInput: string) => {
    const answerString = userInput.trim().toUpperCase()
    
    // 检查是否是批量答案（长度等于题目数量）
    const questionCount = testQuestions.length
    if (answerString.length === questionCount && questionCount > 0) {
      // 批量处理答案
      const userAnswers = answerString.split('')
      const answerNumbers: number[] = []
      
      // 验证每个答案都是ABCD
      for (let i = 0; i < questionCount; i++) {
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
          const exampleAnswer = Array(questionCount).fill('A').join('')
          const errorMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: `❌ **Input Error**

Please enter a ${questionCount}-letter answer combination, each letter must be A, B, C, or D.
Example: ${exampleAnswer}`,
            timestamp: new Date()
          }
          setMessages(prev => [...prev, errorMessage])
          return
        }
        answerNumbers.push(answerNumber)
      }
      
      // Calculate correct answer count
      let correctCount = 0
      const results: { question: Question, userAnswer: number, isCorrect: boolean }[] = []
      
      for (let i = 0; i < questionCount; i++) {
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
      
      // Display detailed results
      const detailedResults = results.map((result, index) => {
        const { question, userAnswer, isCorrect } = result
        return `**Question ${index + 1}:** ${isCorrect ? '✅ Correct' : '❌ Wrong'}
Question: ${question.question}
Your Answer: ${['A', 'B', 'C', 'D'][userAnswer]}. ${question.options[userAnswer]}
Correct Answer: ${['A', 'B', 'C', 'D'][question.correctAnswer]}. ${question.options[question.correctAnswer]}
Explanation: ${question.explanation}`
      }).join('\n\n')
      
      const finalScore = (correctCount / questionCount) * 100
      
      const resultMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `📊 **Test Results Details**

${detailedResults}

**📋 Summary:**
Correct Answers: ${correctCount}/${questionCount}
Accuracy: ${finalScore.toFixed(1)}%`,
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, resultMessage])
      
      // Check if test is passed (accuracy >= 80%)
      const passThreshold = 80  // Requires 80% accuracy
      if (finalScore >= passThreshold) {
        setTaskProgress(100)
        const completeMessage: Message = {
          id: (Date.now() + 2).toString(),
          role: 'assistant',
          content: `🎉 **Test Passed! Congratulations!**

✅ You answered ${correctCount}/${questionCount} questions correctly with an accuracy of ${finalScore.toFixed(1)}%!
🌟 You have reached the 80% passing standard!

Click the "Complete Task" button to continue exploring the next Magic Hall.`,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, completeMessage])
        setIsTestMode(false)
        
        // Call completion callback
        setTimeout(() => {
          onComplete()
        }, 1000)
      } else {
        const failMessage: Message = {
          id: (Date.now() + 2).toString(),
          role: 'assistant',
          content: `😔 **Test Failed**

❌ Your accuracy is ${finalScore.toFixed(1)}%, you need to reach 80% to pass.
It is recommended to review the knowledge points and take the test again.

📊 Need to answer correctly: ${Math.ceil(questionCount * 0.8)}/${questionCount} questions

Please continue learning the related knowledge points, or restart the test.`,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, failMessage])
        setIsTestMode(false)
      }
      
      return
    }
    
    // If not batch answer, show error message
    const exampleAnswer = Array(questionCount).fill('A').join('')
    const errorMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: `❌ **Input Format Error**

Please enter a ${questionCount}-letter answer combination, for example: ${exampleAnswer}
(Enter the corresponding A/B/C/D letter for each question in order)`,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, errorMessage])
  }

  const generateFallbackQuestion = (questionNum: number, pointTitle: string, pointContent: string): Question => {
    // Extract key information from knowledge point content to generate simple question
    console.log(`🔄 Generating fallback question ${questionNum} - ${pointTitle}`)
    
    return {
      id: `q${questionNum}`,
      question: `Regarding "${pointTitle}", which description is most accurate?`,
      options: [
        'This is an important concept mentioned in the course',
        'This is not within the scope of this course',
        'This is an outdated technology',
        'This is only theoretical knowledge with no practical application'
      ],
      correctAnswer: 0,
      explanation: `According to the course content, ${pointTitle} is an important knowledge point in this course.`
    }
  }

  const startTest = async () => {
    if (!courseData || learnedKnowledgePoints.size < Math.ceil(totalKnowledgePoints * 0.2)) {
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `⚠️ **Cannot Start Test**

You need to complete 20% of the knowledge points before taking the test.

**Current Progress:** ${learnedKnowledgePoints.size}/${totalKnowledgePoints} (${Math.round((learnedKnowledgePoints.size / totalKnowledgePoints) * 100)}%)

Please continue learning more knowledge points!`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
      return
    }

    // Open battle scene instead of in-dialog test
    setShowBattleScene(true)
  }

  const handleBattleComplete = async (passed: boolean, score: number) => {
    // Close battle scene
    setShowBattleScene(false)

    if (passed) {
      // Mark area as completed
      try {
        await fetch(`http://127.0.0.1:8001/api/complete-area/${areaId}`, {
          method: 'POST'
        })

        const successMessage: Message = {
      id: Date.now().toString(),
      role: 'assistant',
          content: `🎉 **Battle Victory!**

Congratulations! You achieved ${score.toFixed(1)}% accuracy in the magic battle!

✨ The professor recognizes your mastery of the magic!
✨ The next area has been unlocked!

You may now proceed to the next Magic Hall or review what you've learned here.`,
      timestamp: new Date()
    }
        setMessages(prev => [...prev, successMessage])
        
        // Call the onComplete callback to notify parent component
        onComplete()
      } catch (error) {
        console.error('Failed to complete area:', error)
      }
    } else {
      const failMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `💔 **Battle Result**

You achieved ${score.toFixed(1)}% accuracy, but you need at least 80% to proceed.

📚 Don't be discouraged! Review the knowledge points and try again.
💪 You can retake the test after reviewing the materials.`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, failMessage])
    }
  }

  const generateAllQuestions = async () => {
    // Only generate questions for learned knowledge points
    const learnedPoints = Array.from(learnedKnowledgePoints)
    const totalQuestions = learnedPoints.length  // Generate questions based on learned points

    if (totalQuestions === 0) {
      const errorMessage: Message = {
      id: Date.now().toString(),
      role: 'assistant',
        content: `⚠️ **Cannot Generate Test**\n\nYou haven't learned any knowledge points yet. Please study first before taking the test.`,
      timestamp: new Date()
    }
      setMessages(prev => [...prev, errorMessage])
      setIsTestMode(false)
      return
    }
    
    // Display progress message (progress bar style)
    const progressMessage: Message = {
      id: 'progress-msg',
      role: 'assistant',
      content: `⏳ **Generating test questions...**\n\n${'▓'.repeat(0)}${'░'.repeat(totalQuestions)} 0/${totalQuestions}`,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, progressMessage])

    // Generate questions
    const questions: Question[] = []
    
    console.log(`🎯 Generating test questions - Learned ${totalQuestions} knowledge points, will generate ${totalQuestions} questions`)
    
    // Only generate questions for learned points, ensure no duplication
    for (let i = 0; i < totalQuestions; i++) {
      // Get learned knowledge point (in learning order)
      const pointNumber = learnedPoints[i]
      const pointTitle = knowledgePointsList[pointNumber - 1] || `Knowledge Point ${pointNumber}`
      const pointContent = courseData?.materials[pointNumber - 1] || ''
      
      console.log(`📝 Question ${i + 1}/${totalQuestions} - Knowledge Point ${pointNumber}: ${pointTitle}`)
      
      // 更新进度条
      const completed = i
      const remaining = totalQuestions - completed
      const progressBar = '▓'.repeat(completed) + '░'.repeat(remaining)
      setMessages(prev => prev.map(msg => 
        msg.id === 'progress-msg' 
          ? { ...msg, content: `⏳ **Generating test questions...**\n\n${progressBar} ${completed}/${totalQuestions}` }
          : msg
      ))
      
      // Use LLM to generate questions based on actual course content (disable thinking display)
      const questionPrompt = `You are a professor at the Magic Academy teaching ${courseData?.subject || 'Course'}, designing test questions for apprentices. Always answer in English only.

【Knowledge Point to Test】:
${pointContent}

【Important Requirements】:
1. Question must be a concise problem, no more than 30 words
2. Do not directly copy the knowledge point content as the question
3. Extract a key concept from the knowledge point to ask about
4. 4 options should be short and clear, each no more than 20 words
5. Only one correct answer, the other 3 should be misleading but clearly wrong

【Question Angle Examples】:
Knowledge Point: Python is an interpreted language, created by Guido van Rossum in 1991, emphasizes code readability...

Can ask from different angles:
- Concept Understanding: What type of programming language is Python?
- Historical Background: Who created Python?
- Design Philosophy: What does Python's design philosophy emphasize?
- Application Scenarios: What fields is Python suitable for?
- Syntax Features: How does Python organize code blocks?

【Wrong Example】 (directly copying):
Question: Python is an interpreted language, created by Guido van Rossum in 1991... ❌

【Correct Examples】 (extracting questions):
Question: What type of programming language is Python? ✅
Question: How does Python organize code blocks? ✅
Question: What fields is Python primarily applied to? ✅

【Output Format】 (strictly follow this format):
Question: [A concise question, no more than 30 words]
A. [Option A, no more than 20 words]
B. [Option B, no more than 20 words]
C. [Option C, no more than 20 words]
D. [Option D, no more than 20 words]
Answer: [A/B/C/D]
Explanation: [Brief explanation of why this answer is correct, no more than 50 words]

Please only output the above format without any additional content.`

      try {
        // Disable thinking display during question generation, only show progress bar
        const response = await callRealLLMAPI(questionPrompt, selectedModel, true)
        console.log(`📥 LLM Response (Question ${i + 1}/${totalQuestions}):`, response)
        
        // Parse LLM response
        const questionMatch = response.match(/Question[：:]\s*(.+?)(?=\n[A-D]\.)/si)
        const optionAMatch = response.match(/A\.\s*(.+?)(?=\n[B-D]\.|$)/s)
        const optionBMatch = response.match(/B\.\s*(.+?)(?=\n[C-D]\.|$)/s)
        const optionCMatch = response.match(/C\.\s*(.+?)(?=\n[D]\.|$)/s)
        const optionDMatch = response.match(/D\.\s*(.+?)(?=\n(?:Answer|答案)|$)/si)
        const answerMatch = response.match(/(?:Answer|答案)[：:]\s*([A-D])/i)
        const explanationMatch = response.match(/(?:Explanation|解析)[：:]\s*(.+?)$/si)
        
        if (questionMatch && optionAMatch && optionBMatch && optionCMatch && optionDMatch && answerMatch && explanationMatch) {
          const answerLetter = answerMatch[1].toUpperCase()
          const correctAnswerIndex = answerLetter.charCodeAt(0) - 'A'.charCodeAt(0)
          
          const question: Question = {
          id: `q${i + 1}`,
            question: questionMatch[1].trim(),
            options: [
              optionAMatch[1].trim(),
              optionBMatch[1].trim(),
              optionCMatch[1].trim(),
              optionDMatch[1].trim()
            ],
            correctAnswer: correctAnswerIndex,
            explanation: explanationMatch[1].trim()
          }
          
          console.log(`✅ Question ${i + 1} generated successfully:`, question)
          questions.push(question)
      } else {
          console.warn(`⚠️ Question ${i + 1} parsing failed, using fallback question`)
          // Use fallback question
          questions.push(generateFallbackQuestion(i + 1, pointTitle, pointContent))
        }
      } catch (error) {
        console.error(`❌ Question ${i + 1} generation failed:`, error)
        // Use fallback question
        questions.push(generateFallbackQuestion(i + 1, pointTitle, pointContent))
      }
    }
    
    // Set generated questions
    setTestQuestions(questions)

    // Display completion progress
    const progressBar = '▓'.repeat(totalQuestions)
    setMessages(prev => prev.map(msg => 
      msg.id === 'progress-msg' 
        ? { ...msg, content: `✅ **Questions Generated!**\n\n${progressBar} ${totalQuestions}/${totalQuestions}` }
        : msg
    ))
    
    // Wait 0.5 seconds then remove progress message and display questions
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // Remove progress message
    setMessages(prev => prev.filter(msg => msg.id !== 'progress-msg'))
    
    // Display all questions
    const answerFormat = Array(totalQuestions).fill('A').join('')  // Generate example of corresponding length
    const learnedPointsStr = learnedPoints.join(', ')
    const allQuestionsMessage: Message = {
      id: Date.now().toString(),
      role: 'assistant',
      content: `📝 **Test Questions (Total: ${totalQuestions})**

Based on your learned knowledge points: ${learnedPointsStr}

${questions.map((q, index) => `**Question ${index + 1}:**
${q.question}

A. ${q.options[0]}
B. ${q.options[1]}
C. ${q.options[2]}
D. ${q.options[3]}`).join('\n\n')}

**📋 How to Answer:**
Please submit all your answers at once, format: ${answerFormat}
(For example: Enter ${totalQuestions} letters in order corresponding to each question)`,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, allQuestionsMessage])
  }

  const generateNextQuestion = async (retryCount = 0) => {
    // Max 2 retries to avoid excessive retrying
    if (retryCount >= 2) {
      console.error('Question generation failed, using fallback question')
      
      // Generate fallback question based on knowledge points
      const learnedPoints = Array.from(learnedKnowledgePoints)
      const randomPointNumber = learnedPoints[Math.floor(Math.random() * learnedPoints.length)]
      const pointTitle = knowledgePointsList[randomPointNumber - 1] || `Knowledge Point ${randomPointNumber}`
      const pointContent = courseData?.materials[randomPointNumber - 1] || ''
      
      // Use fallback question generation function
      const defaultQuestion: Question = generateFallbackQuestion(
        getCurrentQuestionNumber(), 
        pointTitle, 
        pointContent
      )
      
      
      setSelectedAnswer(null)


      const testMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `📝 **Question ${getCurrentQuestionNumber()}**

**Question:**
${defaultQuestion.question}

**Options:**
A. ${defaultQuestion.options[0]}
B. ${defaultQuestion.options[1]}
C. ${defaultQuestion.options[2]}
D. ${defaultQuestion.options[3]}

Please select the correct answer (reply A, B, C, or D):`,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, testMessage])
      setThinkingContent('')
      return
    }

    // Randomly select a learned knowledge point
    const learnedPoints = Array.from(learnedKnowledgePoints)
    const randomPointNumber = learnedPoints[Math.floor(Math.random() * learnedPoints.length)]
    const pointTitle = knowledgePointsList[randomPointNumber - 1] || `Knowledge Point ${randomPointNumber}`

    // Display thinking process
    if (showThinking) {
      setThinkingContent(`🎯 Generating test question for knowledge point "${pointTitle}"...\n🔍 Analyzing knowledge point content...\n❓ Designing question and options...\n📝 Generating correct answer and explanation...`)
    }

    // Let LLM generate multiple choice question
    const questionPrompt = `You are a professor at the Magic Academy, designing a technical test question about "${pointTitle}" for magic apprentices. Always answer in English only.

【Course Materials】:
${courseData?.materials.join('\n') || 'Fundamental Knowledge'}

【Question Requirements】:
1. Question must be strictly based on course material content
2. Use professional computer science terminology, suitable for university level
3. Only 1 correct answer among 4 options
4. If it's a math question, carefully calculate to ensure the answer is correct
5. Options cannot be duplicated, must have appropriate misleading elements

【Special Requirements for Math Questions】:
- Question cannot directly give away or hint at the answer
- Options should only contain expressions, not equals signs and results
- Ensure only one correct answer
- Other options must be wrong answers, cannot be correct

【Quality Check】:
- Math questions: Check calculation results and option uniqueness three times
- General knowledge questions: Ensure logical coherence
- Explanation must be consistent with the correct answer

【JSON Format】 (Strictly output in this format, do not add any other content):
{
  "question": "Question content (concise and clear)",
  "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
  "correctAnswer": 0,
  "explanation": "Brief explanation (consistent with correct answer)"
}

【Math Question Example】 (Reference format):
{
  "question": "Which expression equals 6?",
  "options": ["2×3", "1×5", "3×2", "2×4"],
  "correctAnswer": 0,
  "explanation": "2×3=6, other expressions do not equal 6"
}

【Important Reminders】:
- correctAnswer is a number: 0=first option, 1=second option, 2=third option, 3=fourth option
- Only output JSON, do not add any other text, explanations or descriptions
- Ensure all punctuation is correct
- Do not add line breaks, keep JSON format intact`

    const response = await callRealLLMAPI(questionPrompt, selectedModel)
    
    try {
      // Parse JSON - Increase fault tolerance
      const cleanResponse = response.trim()
      console.log('LLM raw response:', cleanResponse)
      
      // Try multiple JSON extraction methods
      let jsonMatch = cleanResponse.match(/\{[\s\S]*\}/)
      if (!jsonMatch) {
        // If complete JSON not found, try to find JSON start
        const startIndex = cleanResponse.indexOf('{')
        if (startIndex !== -1) {
          const partialJson = cleanResponse.substring(startIndex)
          // Try to complete JSON
          if (!partialJson.includes('}')) {
            // If missing closing bracket, try to complete
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
    const chatPrompt = `You are a professor at the Magic Academy teaching ${courseData?.subject || 'Course'}, guiding a curious magic apprentice. Answer the apprentice's question strictly based on the course materials. Always answer in English only.

【Course Materials】:
${courseData?.materials.join('\n') || 'Fundamental Knowledge'}

【Apprentice Question】: ${userInput}

【Answer Requirements】:
1. Base your answer only on the provided course materials
2. Use professional yet clear terminology appropriate for university-level learners
3. You may incorporate subtle Magic Academy flavor, but keep it rigorous
4. Be accurate and specific; avoid vague statements
5. If the question is out of scope, say: "This question is beyond the scope of this course, young apprentice."
6. Keep it concise within 150 words
7. Use concrete examples when helpful

【Output Format】:
Answer directly without any prefix or suffix.`

    const response = await callRealLLMAPI(chatPrompt, selectedModel)
    
    const chatMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: response,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, chatMessage])
  }

  const callRealLLMAPI = async (userInput: string, model: string = 'qwen2.5', skipThinking: boolean = false): Promise<string> => {
    try {
      switch (model) {
        case 'claude-3.5':
          // 检查API密钥是否配置
          if (!checkAPIKey('claude-3.5')) {
            console.warn('Claude API密钥未配置，回退到本地模型')
            return await callLocalModel(userInput, 'qwen2.5', skipThinking)
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
            return await callLocalModel(userInput, 'qwen2.5', skipThinking)
          }
          break

        case 'qwen2.5':
        case 'ollama-llama2':
          return await callLocalModel(userInput, model, skipThinking)
          break

        default:
          return await callLocalModel(userInput, 'qwen2.5', skipThinking)
      }
    } catch (error) {
      console.error('API调用失败:', error)
      // 回退到本地模型
      return await callLocalModel(userInput, 'qwen2.5')
    }
  }

  const callLocalModel = async (userInput: string, model: string = 'qwen2.5', skipThinking: boolean = false): Promise<string> => {
    const ollamaModel = model === 'qwen2.5' ? 'qwen2.5:7b' : 'llama2'
    
    // Start streaming thinking content (hidden during question generation)
    if (showThinking && !skipThinking) {
      setThinkingContent('🤔 Thinking...\n')
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
                
                // 实时更新思考过程（出题时不显示）
                if (showThinking && !skipThinking) {
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
    
    const modelResponses = responses[model as keyof typeof responses] || responses['ollama-llama2']
    return modelResponses[Math.floor(Math.random() * modelResponses.length)]
  }

  const getCurrentQuestionNumber = () => {
    // 计算当前是第几题（基于测试开始后的用户回答数量）
    const testStartIndex = messages.findIndex(msg => msg.content.includes('Starting Test!'))
    if (testStartIndex === -1) return 1
    
    const testMessages = messages.slice(testStartIndex)
    const userAnswers = testMessages.filter(msg => msg.role === 'user' && ['A', 'B', 'C', 'D'].includes(msg.content.trim().toUpperCase()))
    
    return userAnswers.length + 1
  }

  const getErrorAnalysis = () => {
    return `You answered ${5 - correctAnswers} questions wrong. It is recommended to re-study the relevant knowledge points, especially those you got wrong.`
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
    <>
      {/* Battle Scene - renders on top of everything */}
      {showBattleScene && (
        <BattleScene
          areaId={areaId}
          courseData={courseData}
          learnedKnowledgePoints={learnedKnowledgePoints}
          modelType={selectedModel}
          onClose={() => setShowBattleScene(false)}
          onBattleComplete={handleBattleComplete}
        />
      )}

    <AnimatePresence>
      {isOpen && (
        <DialogOverlay
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
            {/* Avatars on both sides of dialog */}
            <AvatarCircle
              side="left"
              src={isUserTyping 
                ? '/character/A_young_wizard_student_is_holding_a_magic_wand._breathing-idle_south-east.gif'
                : '/character/wizard_idle.gif'}
            />
            <AvatarCircle
              side="right"
              src={isLoading 
                ? '/character/A_old_wizard_professor_is_holding_a_magic_wand_with_a_magic_hat._breathing-idle_south-west.gif'
                : '/character/A_old_wizard_professor_is_holding_a_magic_wand_with_a_magic_hat._breathing-idle_south.gif'}
            />
          <DialogContent
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
          >
            {!courseData ? (
              // 加载课程数据中
              <div style={{ 
                display: 'flex', 
                flexDirection: 'column',
                alignItems: 'center', 
                justifyContent: 'center',
                minHeight: '400px',
                color: 'white',
                gap: '16px'
              }}>
                <div style={{ fontSize: '48px' }}>📚</div>
                <div style={{ fontSize: '18px' }}>Loading course data...</div>
              </div>
            ) : (
              <>
            <DialogHeader>
                  <DialogTitle>{courseData.subject || areaId} Magic Hall</DialogTitle>
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
                  <option value="qwen2.5">🤖 Qwen2.5 (Local)</option>
                  <option value="claude-3.5">🌐 Claude 3.5 (Online)</option>
                  
                </select>
                {/* Removed Thinking Display indicator */}
                <CloseButton onClick={onClose}>×</CloseButton>
              </div>
            </DialogHeader>

            <ProgressBar>
              <ProgressFill $progress={learningProgress} />
              <ProgressLabel>
                Learning Progress: {learnedKnowledgePoints.size}/{totalKnowledgePoints} ({Math.round(learningProgress)}%)
              </ProgressLabel>
            </ProgressBar>

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
                        Thinking...
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
                          <span>AI Thinking Process</span>
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
                onChange={(e) => {
                  const v = e.target.value
                  setInputMessage(v)
                  if (typingTimerRef.current) clearTimeout(typingTimerRef.current)
                  setIsUserTyping(!!v)
                  typingTimerRef.current = setTimeout(() => setIsUserTyping(false), 1200)
                }}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder={isTestMode ? "Please enter A, B, C, or D for the answer..." : "Enter a number to learn a knowledge point, ask me a question directly, or enter 'test' to take the test..."}
                disabled={isLoading}
              />
              <SendButton
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isLoading}
              >
                Send
              </SendButton>
            </InputContainer>

            {/* 开始测试按钮：仅当学习进度≥20%时显示 */}
            {!isTestMode && totalKnowledgePoints > 0 && (learnedKnowledgePoints.size / totalKnowledgePoints) >= 0.2 && (
              <div style={{ marginTop: '16px', textAlign: 'center' }}>
                <SendButton
                  onClick={startTest}
                  style={{ background: '#FF9800' }}
                  disabled={isLoading}
                >
                  Start Magic Duel
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
                  🧪 Small Test Time
                </div>
                <div style={{ color: '#ffffff', fontSize: '14px' }}>
                  Answer the professor's questions to complete this Magic Hall!
                </div>
              </div>
            )}

            {taskProgress === 100 && selectedAnswer !== null && (
              <CompleteButton onClick={handleComplete}>
                🎓 Complete Learning
              </CompleteButton>
            )}
              </>
            )}
          </DialogContent>
        </DialogOverlay>
      )}
    </AnimatePresence>
    </>
  )
}

export default AreaDialog
