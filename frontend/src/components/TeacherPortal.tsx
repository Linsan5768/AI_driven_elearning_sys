import { useState, useRef, useEffect } from 'react'
import styled from '@emotion/styled'
import { motion } from 'framer-motion'
import axios from 'axios'

const PortalContainer = styled.div`
  width: 100vw;
  height: 100vh;
  /*background-image: url('/Teacherend_Homepage.png');*/
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  background-attachment: fixed;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`

const Header = styled.div`
  padding: 30px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-bottom: 2px solid rgba(255, 255, 255, 0.2);
  display: flex;
  justify-content: space-between;
  align-items: center;
`

const Title = styled.h1`
  color: white;
  margin: 0;
  font-size: 32px;
  display: flex;
  align-items: center;
  gap: 15px;
`

const SwitchButton = styled.button`
  padding: 12px 24px;
  background: rgba(255, 255, 255, 0.2);
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 25px;
  color: white;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s;
  
  &:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: translateY(-2px);
  }
`

const ContentArea = styled.div`
  flex: 1;
  padding: 40px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 30px;
`

const Card = styled(motion.div)`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  color: #111; /* force dark text for readability */
`

const UploadSection = styled.div`
  border: 3px dashed #667eea;
  border-radius: 15px;
  padding: 60px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: rgba(102, 126, 234, 0.05);
  
  &:hover {
    border-color: #764ba2;
    background: rgba(102, 126, 234, 0.1);
    transform: translateY(-5px);
  }
  
  &.dragging {
    border-color: #4CAF50;
    background: rgba(76, 175, 80, 0.1);
  }
`

const FileInput = styled.input`
  display: none;
`

const Button = styled.button<{ variant?: 'primary' | 'secondary' | 'danger' }>`
  padding: 14px 28px;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  
  ${props => props.variant === 'primary' && `
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
    }
  `}
  
  ${props => props.variant === 'secondary' && `
    background: #e0e0e0;
    color: #333;
    &:hover {
      background: #d0d0d0;
    }
  `}
  
  ${props => props.variant === 'danger' && `
    background: #f44336;
    color: white;
    &:hover {
      background: #d32f2f;
    }
  `}
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none !important;
  }
`

const ProgressTrack = styled.div`
  width: 100%;
  height: 12px;
  background: #e0e0e0;
  border-radius: 10px;
  overflow: hidden;
  margin: 14px 0 10px;
`

const ProgressFill = styled.div<{ progress: number }>`
  width: ${props => props.progress}%;
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transition: width 0.35s ease;
`

const ProgressMeta = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #333;
`

const CourseCard = styled(motion.div)`
  background: white;
  border-radius: 15px;
  padding: 25px;
  border: 2px solid #e0e0e0;
  transition: all 0.3s;
  
  &:hover {
    border-color: #667eea;
    box-shadow: 0 5px 20px rgba(102, 126, 234, 0.2);
  }
`

const KnowledgePointList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 20px;
`

const KnowledgePoint = styled.div`
  padding: 15px;
  background: #f5f5f5;
  border-radius: 10px;
  border-left: 4px solid #667eea;
  color: #333;
  line-height: 1.6;
`

interface CourseData {
  id: string
  subject: string
  materials: Array<string | {
    id?: string
    concept?: string
    topic?: string
    level?: string
    definition?: string
    facts?: Array<{ fact?: string; numbers?: string[]; source_quote?: string }>
  }>
  difficulty: 'easy' | 'medium' | 'hard'
  category: string
  fileName: string
  generatedAt: string
  thinking_trace?: string[]
  knowledge_structure?: {
    pipeline?: string[]
    concept_index?: Array<{
      concept: string
      topic: string
      level: string
      definition?: { text?: string; source_quotes?: string[] }
      examples?: Array<{ text?: string; source_quote?: string }>
      key_facts?: Array<{ fact?: string; numbers?: string[]; source_quote?: string }>
      relationships?: Array<{ type?: string; target_concept?: string; evidence_quote?: string }>
    }>
    topics?: Array<{
      topic: string
      levels?: {
        beginner?: string[]
        intermediate?: string[]
        advanced?: string[]
      }
    }>
  }
}

interface TeacherPortalProps {
  onSwitchToStudent: () => void
  onCourseApplied?: () => void
  onLogout: () => void
}

import { API_BASE_URL } from '../config/apiConfig'

interface ReportInfo {
  report_id: string
  student_id: string
  type: string
  subject: string
  title: string
  subtitle: string
  generated_at: string
  area_name: string
  accuracy: number
  total_questions: number
  filename: string
  pdf_filename: string | null
}

const TeacherPortal: React.FC<TeacherPortalProps> = ({ onSwitchToStudent, onCourseApplied, onLogout }) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [generatedCourse, setGeneratedCourse] = useState<CourseData | null>(null)
  const [courses, setCourses] = useState<CourseData[]>([])
  const [reports, setReports] = useState<ReportInfo[]>([])
  const [statusMessage, setStatusMessage] = useState('')
  const [processingStage, setProcessingStage] = useState('')
  const [showProcessingThinking, setShowProcessingThinking] = useState(false)
  const [thinkingSteps, setThinkingSteps] = useState<string[]>([])
  const [replaceExisting, setReplaceExisting] = useState(true) // Default: replace existing courses
  const [isDragging, setIsDragging] = useState(false)
  const [previewMode, setPreviewMode] = useState<'summary' | 'structure'>('structure')
  // History is always shown now, removed toggle
  
  const fileInputRef = useRef<HTMLInputElement>(null)

  const normalizeCourseData = (raw: any): CourseData => {
    const knowledgeStructure = raw?.knowledge_structure
    const conceptIndex = Array.isArray(knowledgeStructure?.concept_index)
      ? knowledgeStructure.concept_index
      : []

    const safeMaterials: Array<string | {
      id?: string
      concept?: string
      topic?: string
      level?: string
      definition?: string
      facts?: Array<{ fact?: string; numbers?: string[]; source_quote?: string }>
    }> = Array.isArray(raw?.materials)
      ? raw.materials.filter((m: any) => {
          if (typeof m === 'string') return m.trim().length > 0
          if (m && typeof m === 'object') return Boolean(m.concept || m.definition)
          return false
        })
      : []

    const fallbackFromConcepts: Array<string> = conceptIndex
      .map((c: any) => {
        const concept = typeof c?.concept === 'string' ? c.concept.trim() : ''
        const topic = typeof c?.topic === 'string' ? c.topic.trim() : 'General'
        if (!concept) return ''
        return `${topic}: ${concept}`
      })
      .filter((x: string) => x.length > 0)

    const materials = safeMaterials.length > 0 ? safeMaterials : fallbackFromConcepts

    const difficultyRaw = String(raw?.difficulty || 'medium').toLowerCase()
    const difficulty: 'easy' | 'medium' | 'hard' =
      difficultyRaw === 'easy' || difficultyRaw === 'hard' ? difficultyRaw : 'medium'

    return {
      id: String(raw?.id || `course_${Date.now()}`),
      subject: String(raw?.subject || 'Untitled Course'),
      materials,
      difficulty,
      category: String(raw?.category || 'General'),
      fileName: String(raw?.fileName || raw?.filename || 'unknown'),
      generatedAt: String(raw?.generatedAt || new Date().toISOString()),
      thinking_trace: Array.isArray(raw?.thinking_trace) ? raw.thinking_trace : undefined,
      knowledge_structure: knowledgeStructure
    }
  }

  const updateProcessing = (nextProgress: number, stage: string, thought?: string) => {
    const safeProgress = Math.max(0, Math.min(100, Math.round(nextProgress)))
    setProgress(safeProgress)
    setProcessingStage(stage)
    setStatusMessage(stage)
    if (thought) {
      setThinkingSteps(prev => [...prev, thought])
    }
  }

  // Load course history and reports
  useEffect(() => {
    loadCourses()
    loadReports()
  }, [])

  const loadReports = async () => {
    try {
      console.log(`🔍 Loading reports from: ${API_BASE_URL}/teacher/reports`)
      const response = await axios.get(`${API_BASE_URL}/teacher/reports`)
      console.log(`✅ Reports API response:`, response.data)
      if (response.data && response.data.reports) {
        setReports(response.data.reports)
        console.log(`📊 Loaded ${response.data.total} reports`)
      } else {
        console.warn('⚠️ No reports in response:', response.data)
      }
    } catch (error: any) {
      console.error('❌ Failed to load reports:', error)
      console.error('Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        url: error.config?.url
      })
      // Show error to user
      setStatusMessage(`⚠️ Failed to load reports: ${error.message}`)
    }
  }

  const handleDownloadReport = async (reportId: string, subject: string) => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/teacher/reports/${reportId}/download`,
        {
          responseType: 'blob',
          timeout: 30000
        }
      )

      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const subjectName = subject.replace(/\s+/g, '_')
      a.download = `${subjectName}_Report_${Date.now()}.pdf`
      document.body.appendChild(a)
      a.click()
      setTimeout(() => {
        if (document.body.contains(a)) {
          document.body.removeChild(a)
        }
        URL.revokeObjectURL(url)
      }, 200)
    } catch (err: any) {
      console.error('Failed to download report:', err)
      alert(err.response?.data?.error || 'Failed to download report')
    }
  }

  const loadCourses = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/courses`)
      if (response.data && response.data.courses) {
        const normalized = response.data.courses.map((c: any) => normalizeCourseData(c))
        setCourses(normalized)
        console.log(`📚 Loaded ${response.data.total} historical courses`)
      }
    } catch (error) {
      console.error('Failed to load course list:', error)
    }
  }

  const renderMaterialText = (m: any): string => {
    if (typeof m === 'string') return m
    if (!m || typeof m !== 'object') return String(m)
    const topic = m.topic ? `[${m.topic}] ` : ''
    const concept = m.concept || 'Unnamed concept'
    const definition = m.definition ? `: ${m.definition}` : ''
    return `${topic}${concept}${definition}`
  }

  const handleDeleteCourse = async (courseId: string) => {
    if (!confirm('Are you sure you want to delete this course?')) return
    
    try {
      await axios.delete(`${API_BASE_URL}/courses/${courseId}`)
      setStatusMessage('🗑️ Course deleted')
      loadCourses() // Refresh list
      setTimeout(() => setStatusMessage(''), 3000)
    } catch (error: any) {
      setStatusMessage(`❌ Delete failed: ${error.message}`)
    }
  }

  const handleFilesSelect = (files: FileList | File[]) => {
    const validTypes = ['application/pdf', 'text/plain', 'text/markdown']
    const validExtensions = ['.pdf', '.txt', '.md']
    const incoming = Array.from(files)
    const validFiles: File[] = []

    incoming.forEach(file => {
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
      if (validTypes.includes(file.type) || validExtensions.includes(fileExtension)) {
        validFiles.push(file)
      }
    })

    if (validFiles.length > 0) {
      // Replace current selection with new valid files
      setSelectedFiles(validFiles)
      if (validFiles.length === 1) {
        setStatusMessage(`File selected: ${validFiles[0].name}`)
      } else {
        setStatusMessage(`Selected ${validFiles.length} files`)
      }
    } else {
      setStatusMessage('⚠️ Please upload PDF, TXT or MD file')
    }
  }

  const handleFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (files && files.length > 0) {
      handleFilesSelect(files)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const files = e.dataTransfer.files
    if (files && files.length > 0) {
      handleFilesSelect(files)
    }
  }

  const handleUploadAndGenerate = async () => {
    if (selectedFiles.length === 0) {
      setStatusMessage('⚠️ Please select at least one file first')
      return
    }

    setIsProcessing(true)
    setThinkingSteps([])
    updateProcessing(5, '📄 Preparing uploaded files...', 'Input files validated and waiting for upload.')

    try {
      // 1. Upload all selected files and combine their text content
      let combinedTextContent = ''
      const sourceNames: string[] = []

      for (let index = 0; index < selectedFiles.length; index++) {
        const file = selectedFiles[index]
        const formData = new FormData()
        formData.append('file', file)

        const uploadProgress = 10 + Math.round((index / Math.max(selectedFiles.length, 1)) * 35)
        updateProcessing(
          uploadProgress,
          `📤 Uploading file ${index + 1}/${selectedFiles.length}...`,
          `Uploading ${file.name}`
        )

        const uploadResponse = await axios.post(`${API_BASE_URL}/upload-pdf`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        const { text_content } = uploadResponse.data
        sourceNames.push(file.name)
        setThinkingSteps(prev => [
          ...prev,
          `Extracted text from ${file.name} (${text_content?.length || 0} chars).`
        ])

        // Mark boundaries between different source files to give LLM more context
        combinedTextContent += `\n\n===== SOURCE FILE ${index + 1}: ${file.name} =====\n\n${text_content}`
      }
      
      updateProcessing(50, '🤖 Starting realtime extraction job...', 'Dispatching async generation task.')

      // 2. Start async generation job
      const startResponse = await axios.post(`${API_BASE_URL}/generate-course-async`, {
        text_content: combinedTextContent,
        file_name: sourceNames.join(' + ')
      })

      const jobId = startResponse.data?.job_id
      if (!jobId) {
        throw new Error('No job_id returned from async generation API')
      }

      // 3. Poll realtime progress from backend
      let courseResult: any = null
      let consumedThinkingCount = 0
      const maxPollRounds = 600 // ~10 minutes if interval is 1s

      for (let round = 0; round < maxPollRounds; round++) {
        const progressResponse = await axios.get(`${API_BASE_URL}/generate-course-progress/${jobId}`)
        const job = progressResponse.data

        const backendProgress = typeof job?.progress === 'number' ? Math.max(0, Math.min(100, job.progress)) : 0
        const mappedProgress = 50 + Math.round((backendProgress / 100) * 50)
        const stage = job?.stage || 'processing'
        const detail = job?.detail || 'Processing...'
        updateProcessing(mappedProgress, `🤖 ${stage}`, detail)

        if (Array.isArray(job?.thinking_trace) && job.thinking_trace.length > consumedThinkingCount) {
          const newSteps = job.thinking_trace.slice(consumedThinkingCount)
          consumedThinkingCount = job.thinking_trace.length
          setThinkingSteps(prev => [...prev, ...newSteps])
        }

        if (job?.status === 'completed') {
          courseResult = job?.result
          break
        }
        if (job?.status === 'failed') {
          throw new Error(job?.error || 'Async generation failed')
        }

        await new Promise(resolve => setTimeout(resolve, 1000))
      }

      if (!courseResult) {
        throw new Error('Generation timeout: no completed result returned')
      }

      const courseData = normalizeCourseData(courseResult)
      if (Array.isArray(courseData?.thinking_trace) && courseData.thinking_trace.length > 0) {
        setThinkingSteps(prev => [...prev, ...(courseData.thinking_trace || [])])
      }
      setGeneratedCourse(courseData)
      
      // Refresh course list (course saved to file)
      await loadCourses()
      
      updateProcessing(100, '✅ Course generated successfully!', 'Processing completed and result materialized.')
      
      // Reset selected files
      setSelectedFiles([])
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      
    } catch (error: any) {
      console.error('Error processing PDF:', error)
      updateProcessing(
        progress || 0,
        `❌ Processing failed: ${error.response?.data?.error || error.message}`,
        `Error: ${error.response?.data?.error || error.message}`
      )
    } finally {
      setIsProcessing(false)
    }
  }

  // handleDeleteCourse defined above

  const handleResetMap = async () => {
    if (!window.confirm('Are you sure you want to reset the game map? This will clear all course areas!')) {
      return
    }
    
    try {
      setStatusMessage('🔄 Resetting game map...')
      
      await axios.post(`${API_BASE_URL}/reset-game-map`)
      
      setStatusMessage('✅ Map reset! All course areas cleared')
      
      // Notify App to refresh game state
      if (onCourseApplied) {
        onCourseApplied()
      }
      
      setTimeout(() => setStatusMessage(''), 3000)
    } catch (error: any) {
      console.error('Reset map error:', error)
      setStatusMessage(`❌ Reset failed: ${error.response?.data?.error || error.message}`)
    }
  }

  const handleApplyToGame = async (course: CourseData) => {
    try {
      setStatusMessage(replaceExisting ? 
        '🎮 Replacing map courses...' : 
        '🎮 Adding course to game map...'
      )
      
      const response = await axios.post(`${API_BASE_URL}/apply-course-to-game`, {
        course_id: course.id,
        course_data: course,
        replace_existing: replaceExisting  // Pass replace flag
      })
      
      const mode = replaceExisting ? 'Replaced' : 'Added'
      setStatusMessage(`✅ Success! ${mode} "${course.subject}" to game map with ${response.data.chapter_count} areas`)
      
      // Notify App to refresh game state
      if (onCourseApplied) {
        onCourseApplied()
      }
      
      // Auto-switch to student view after 2 seconds
      setTimeout(() => {
        setStatusMessage('🎮 Redirecting to Student View...')
        setTimeout(() => {
          onSwitchToStudent()
        }, 500)
      }, 2000)
    } catch (error: any) {
      console.error('Apply course error:', error)
      setStatusMessage(`❌ Apply failed: ${error.response?.data?.error || error.message}`)
    }
  }

  return (
    <PortalContainer>
      <Header>
        <Title>
          Teacher Portal
        </Title>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <div
            style={{
              padding: '10px 20px',
              background: '#4CAF50',
              borderRadius: '8px',
              color: 'white',
              fontSize: '14px',
              fontWeight: '600'
            }}
          >
            📚 Course History ({courses.length})
          </div>
          <button
            onClick={handleResetMap}
            style={{
              padding: '10px 20px',
              background: '#ff6b6b',
              border: 'none',
              borderRadius: '8px',
              color: 'white',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.3s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = '#ee5a52'}
            onMouseLeave={(e) => e.currentTarget.style.background = '#ff6b6b'}
          >
            🔄 Reset Map
          </button>
        <SwitchButton onClick={onSwitchToStudent}>
          Switch to Student View
        </SwitchButton>
        <SwitchButton onClick={onLogout}>
          Back to Landing
        </SwitchButton>
        </div>
      </Header>

      <ContentArea>
        {/* PDF upload section */}
        <Card
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h2 style={{ margin: '0 0 20px 0', color: '#333' }}>📚 Upload Course Materials</h2>
          <div style={{ marginBottom: '14px', display: 'flex', justifyContent: 'flex-end' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#333', fontSize: '14px' }}>
              <input
                type="checkbox"
                checked={showProcessingThinking}
                onChange={(e) => setShowProcessingThinking(e.target.checked)}
              />
              Show model thinking process
            </label>
          </div>
          
          <UploadSection
            className={isDragging ? 'dragging' : ''}
            onClick={() => fileInputRef.current?.click()}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div style={{ fontSize: '60px', marginBottom: '20px' }}>
              {selectedFiles.length > 0
                ? (selectedFiles.every(f => f.name.toLowerCase().endsWith('.txt') || f.name.toLowerCase().endsWith('.md'))
                    ? '📝'
                    : '📄')
                : '📄'}
            </div>
            <h3 style={{ margin: '0 0 10px 0', color: '#667eea' }}>
              {selectedFiles.length === 0
                ? 'Click or Drag to Upload Course Files (you can select multiple)'
                : selectedFiles.length === 1
                  ? selectedFiles[0].name
                  : `${selectedFiles.length} files selected`}
            </h3>
            <p style={{ margin: 0, color: '#666' }}>
              Support PDF, TXT, MD formats • You can upload slides, transcripts and notes together • AI will analyze all selected files to generate detailed knowledge points
            </p>
          </UploadSection>
          
          <FileInput
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,.md,application/pdf,text/plain,text/markdown"
            multiple
            onChange={handleFileInputChange}
          />
          
          {selectedFiles.length > 0 && (
            <div style={{ marginTop: '20px', textAlign: 'center' }}>
              <Button
                variant="primary"
                onClick={handleUploadAndGenerate}
                disabled={isProcessing}
              >
                {isProcessing ? '🔄 Processing...' : '✨ Generate Course'}
              </Button>
            </div>
          )}
          
          {isProcessing && (
            <div>
              <ProgressTrack>
                <ProgressFill progress={progress} />
              </ProgressTrack>
              <ProgressMeta>
                <span>{processingStage || 'Processing...'}</span>
                <strong>{progress}%</strong>
              </ProgressMeta>
              {showProcessingThinking && thinkingSteps.length > 0 && (
                <div
                  style={{
                    marginTop: '12px',
                    maxHeight: '180px',
                    overflowY: 'auto',
                    background: '#f7f8ff',
                    border: '1px solid #d9ddff',
                    borderRadius: '10px',
                    padding: '10px 12px',
                    fontSize: '13px',
                    color: '#333'
                  }}
                >
                  {thinkingSteps.map((step, index) => (
                    <div key={index} style={{ marginBottom: '6px', lineHeight: 1.45 }}>
                      {index + 1}. {step}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          
          {!isProcessing && statusMessage && (
            <p style={{ 
              textAlign: 'center', 
              marginTop: '20px',
              color: statusMessage.includes('Success') ? '#4CAF50' : 
                     statusMessage.includes('failed') ? '#f44336' : '#667eea',
              fontWeight: 600
            }}>
              {statusMessage}
            </p>
          )}
        </Card>

        {/* Generated course preview */}
        {generatedCourse && (
          <Card
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 style={{ margin: 0, color: '#333' }}>✨ Generated Course Content</h2>
              <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
                <select
                  value={previewMode}
                  onChange={(e) => setPreviewMode(e.target.value as 'summary' | 'structure')}
                  style={{
                    padding: '10px 12px',
                    borderRadius: '10px',
                    border: '1px solid #ccc',
                    fontSize: '14px',
                    background: '#fff',
                    color: '#333'
                  }}
                >
                  <option value="structure">🧠 Structured Knowledge</option>
                  <option value="summary">📚 Legacy Materials</option>
                </select>
                <label style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '12px',
                  cursor: 'pointer',
                  padding: '14px 20px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  borderRadius: '12px',
                  transition: 'all 0.3s ease',
                  boxShadow: '0 4px 15px rgba(102, 126, 234, 0.3)',
                  border: '2px solid rgba(255, 255, 255, 0.2)'
                }}>
                  <div style={{
                    position: 'relative',
                    width: '24px',
                    height: '24px',
                    minWidth: '24px',
                    borderRadius: '6px',
                    background: replaceExisting ? '#4CAF50' : 'rgba(255, 255, 255, 0.3)',
                    border: '2px solid white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'all 0.3s ease'
                  }}>
                    <input
                      type="checkbox"
                      checked={replaceExisting}
                      onChange={(e) => setReplaceExisting(e.target.checked)}
                      style={{ 
                        position: 'absolute',
                        opacity: 0,
                        cursor: 'pointer',
                        width: '100%',
                        height: '100%',
                        margin: 0
                      }}
                    />
                    {replaceExisting && (
                      <span style={{ color: 'white', fontSize: '16px', fontWeight: 'bold' }}>✓</span>
                    )}
                  </div>
                  <span style={{ 
                    color: '#111', 
                    fontSize: '15px', 
                    fontWeight: '600',
                    textShadow: '0 2px 4px rgba(0, 0, 0, 0.2)'
                  }}>
                    {replaceExisting ? '🔄 Replace Existing Course' : '➕ Add to Existing Course'}
                  </span>
                </label>
                <Button
                  variant="primary"
                  onClick={() => handleApplyToGame(generatedCourse)}
                >
                  🎮 Apply to Game
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => setGeneratedCourse(null)}
                >
                  Close Preview
                </Button>
              </div>
            </div>
            
            <div style={{ marginTop: '25px' }}>
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: '1fr 1fr', 
                gap: '20px',
                marginBottom: '25px'
              }}>
                <div>
                  <strong style={{ color: '#667eea' }}>📖 Course Name:</strong>
                  <p style={{ margin: '5px 0', fontSize: '18px' }}>{generatedCourse.subject}</p>
                </div>
                <div>
                  <strong style={{ color: '#667eea' }}>📁 Source File:</strong>
                  <p style={{ margin: '5px 0', color: '#111' }}>{generatedCourse.fileName}</p>
                </div>
                <div>
                  <strong style={{ color: '#667eea' }}>⚡ Difficulty Level:</strong>
                  <p style={{ margin: '5px 0', color: '#111' }}>
                    {generatedCourse.difficulty === 'easy' ? 'Beginner ⭐' : 
                     generatedCourse.difficulty === 'medium' ? 'Intermediate ⭐⭐' : 
                     'Advanced ⭐⭐⭐'}
                  </p>
                </div>
                <div>
                  <strong style={{ color: '#667eea' }}>🏷️ Category:</strong>
                  <p style={{ margin: '5px 0', color: '#111' }}>{generatedCourse.category}</p>
                </div>
              </div>
              
              {previewMode === 'summary' || !generatedCourse.knowledge_structure?.concept_index?.length ? (
                <div>
                  <strong style={{ color: '#667eea', fontSize: '18px' }}>
                    📚 Knowledge Points ({generatedCourse.materials.length}):
                  </strong>
                  <KnowledgePointList>
                    {generatedCourse.materials.map((point, index) => (
                      <KnowledgePoint key={index}>
                        <strong>{index + 1}. </strong>{renderMaterialText(point)}
                      </KnowledgePoint>
                    ))}
                  </KnowledgePointList>
                </div>
              ) : (
                <div>
                  <strong style={{ color: '#667eea', fontSize: '18px' }}>
                    🧠 Structured Concepts ({generatedCourse.knowledge_structure.concept_index.length})
                  </strong>
                  <KnowledgePointList>
                    {generatedCourse.knowledge_structure.concept_index.map((concept, index) => (
                      <KnowledgePoint key={index}>
                        <div style={{ marginBottom: '8px' }}>
                          <strong>{index + 1}. {concept.concept}</strong>
                          <span style={{ marginLeft: '8px', color: '#555' }}>
                            [{concept.topic} • {concept.level}]
                          </span>
                        </div>

                        {concept.definition?.text && (
                          <div style={{ marginBottom: '8px' }}>
                            <strong>Definition:</strong> {concept.definition.text}
                          </div>
                        )}

                        {concept.examples && concept.examples.length > 0 && (
                          <div style={{ marginBottom: '8px' }}>
                            <strong>Examples:</strong>
                            <ul style={{ margin: '4px 0 0 18px' }}>
                              {concept.examples.map((ex, i) => (
                                <li key={i}>{ex.text || ex.source_quote || '-'}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {concept.key_facts && concept.key_facts.length > 0 && (
                          <div style={{ marginBottom: '8px' }}>
                            <strong>Key Facts:</strong>
                            <ul style={{ margin: '4px 0 0 18px' }}>
                              {concept.key_facts.map((fact, i) => (
                                <li key={i}>
                                  {fact.fact || '-'}
                                  {fact.numbers && fact.numbers.length > 0 ? ` (numbers: ${fact.numbers.join(', ')})` : ''}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {concept.relationships && concept.relationships.length > 0 && (
                          <div>
                            <strong>Relationships:</strong>
                            <ul style={{ margin: '4px 0 0 18px' }}>
                              {concept.relationships.map((rel, i) => (
                                <li key={i}>
                                  {rel.type || 'related-to'} → {rel.target_concept || 'N/A'}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </KnowledgePoint>
                    ))}
                  </KnowledgePointList>
                </div>
              )}
            </div>
          </Card>
        )}

        {/* Historical courses list */}
        {courses.length > 0 && (
          <Card
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <h2 style={{ margin: '0 0 25px 0', color: '#333' }}>
              📋 Course History ({courses.length})
            </h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              {courses.map((course) => (
                <CourseCard
                  key={course.id}
                  whileHover={{ scale: 1.02 }}
                  transition={{ duration: 0.2 }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                    <div style={{ flex: 1 }}>
                      <h3 style={{ margin: '0 0 10px 0', color: '#667eea' }}>
                        {course.subject}
                      </h3>
                      <div style={{ display: 'flex', gap: '20px', fontSize: '14px', color: '#111' }}>
                        <span>📁 {course.fileName}</span>
                        <span>📚 {(course.materials || []).length} Knowledge Points</span>
                        <span>🏷️ {course.category}</span>
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <Button
                        variant="primary"
                        onClick={() => handleApplyToGame(course)}
                      >
                        🎮 Apply
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={() => setGeneratedCourse(course)}
                      >
                        View
                      </Button>
                      <Button
                        variant="danger"
                        onClick={() => handleDeleteCourse(course.id)}
                      >
                        Delete
                      </Button>
                    </div>
                  </div>
                </CourseCard>
              ))}
            </div>
          </Card>
        )}

        {/* Student Reports Section */}
        {reports.length > 0 && (
          <Card
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            <h2 style={{ margin: '0 0 25px 0', color: '#333' }}>
              📊 Student Reports ({reports.length})
            </h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              {reports.map((report) => (
                <CourseCard
                  key={report.report_id}
                  whileHover={{ scale: 1.01 }}
                  transition={{ duration: 0.2 }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                    <div style={{ flex: 1 }}>
                      <h3 style={{ margin: '0 0 8px 0', color: '#667eea', fontSize: '18px' }}>
                        📖 {report.subject}
                      </h3>
                      <div style={{ marginBottom: '8px', fontSize: '16px', fontWeight: '600', color: '#333' }}>
                        {report.title}
                      </div>
                      <div style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>
                        {report.subtitle}
                      </div>
                      <div style={{ display: 'flex', gap: '20px', fontSize: '13px', color: '#111', flexWrap: 'wrap' }}>
                        <span>📅 {new Date(report.generated_at).toLocaleDateString()}</span>
                        <span>📚 {report.total_questions} Questions</span>
                        <span>🎯 {report.accuracy.toFixed(1)}% Accuracy</span>
                        <span>👤 Student: {report.student_id}</span>
                        <span>📝 Type: {report.type === 'subject_final' ? 'Subject Final' : report.type === 'module' ? 'Module' : report.type}</span>
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                      {report.pdf_filename && (
                        <Button
                          variant="primary"
                          onClick={() => handleDownloadReport(report.report_id, report.subject)}
                        >
                          📥 Download PDF
                        </Button>
                      )}
                    </div>
                  </div>
                </CourseCard>
              ))}
            </div>
          </Card>
        )}

        {reports.length === 0 && (
          <Card
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
              <div style={{ fontSize: '48px', marginBottom: '20px' }}>📊</div>
              <h3 style={{ margin: '0 0 10px 0', color: '#333' }}>No Reports Yet</h3>
              <p style={{ margin: 0 }}>Student reports will appear here after they complete course units and tests.</p>
            </div>
          </Card>
        )}
      </ContentArea>
    </PortalContainer>
  )
}

export default TeacherPortal
