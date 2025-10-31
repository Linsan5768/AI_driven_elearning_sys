import { useState, useRef, useEffect } from 'react'
import styled from '@emotion/styled'
import { motion } from 'framer-motion'
import axios from 'axios'

const PortalContainer = styled.div`
  width: 100vw;
  height: 100vh;
  background-image: url('/game-background.png');
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

const ProgressBar = styled.div<{ progress: number }>`
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  margin: 20px 0;
  
  &::after {
    content: '';
    display: block;
    width: ${props => props.progress}%;
    height: 100%;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    transition: width 0.3s ease;
  }
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
  materials: string[]
  difficulty: 'easy' | 'medium' | 'hard'
  category: string
  fileName: string
  generatedAt: string
}

interface TeacherPortalProps {
  onSwitchToStudent: () => void
  onCourseApplied?: () => void
}

const API_BASE_URL = 'http://127.0.0.1:8001/api'

const TeacherPortal: React.FC<TeacherPortalProps> = ({ onSwitchToStudent, onCourseApplied }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [generatedCourse, setGeneratedCourse] = useState<CourseData | null>(null)
  const [courses, setCourses] = useState<CourseData[]>([])
  const [statusMessage, setStatusMessage] = useState('')
  const [replaceExisting, setReplaceExisting] = useState(true) // Default: replace existing courses
  const [isDragging, setIsDragging] = useState(false)
  const [showHistory, setShowHistory] = useState(true)
  
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Load course history
  useEffect(() => {
    loadCourses()
  }, [])

  const loadCourses = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/courses`)
      if (response.data && response.data.courses) {
        setCourses(response.data.courses)
        console.log(`📚 Loaded ${response.data.total} historical courses`)
      }
    } catch (error) {
      console.error('Failed to load course list:', error)
    }
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

  const handleFileSelect = (file: File) => {
    const validTypes = ['application/pdf', 'text/plain', 'text/markdown']
    const validExtensions = ['.pdf', '.txt', '.md']
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
    
    if (validTypes.includes(file.type) || validExtensions.includes(fileExtension)) {
      setSelectedFile(file)
      setStatusMessage(`File selected: ${file.name}`)
    } else {
      setStatusMessage('⚠️ Please upload PDF, TXT or MD file')
    }
  }

  const handleFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      handleFileSelect(file)
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
    
    const file = e.dataTransfer.files[0]
    if (file) {
      handleFileSelect(file)
    }
  }

  const handleUploadAndGenerate = async () => {
    if (!selectedFile) {
      setStatusMessage('⚠️ Please select a file first')
      return
    }

    setIsProcessing(true)
    setProgress(0)
    setStatusMessage('📄 Reading file...')

    try {
      // 1. Upload file
      const formData = new FormData()
      formData.append('file', selectedFile)
      
      setProgress(20)
      setStatusMessage('📤 Uploading file to server...')
      
      const uploadResponse = await axios.post(`${API_BASE_URL}/upload-pdf`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      const { file_path, text_content } = uploadResponse.data
      
      setProgress(40)
      setStatusMessage('🤖 AI Professor analyzing course content...')
      
      // 2. Let AI analyze content and generate knowledge points
      const generateResponse = await axios.post(`${API_BASE_URL}/generate-course`, {
        text_content,
        file_name: selectedFile.name
      })
      
      setProgress(80)
      setStatusMessage('✨ Organizing knowledge points...')
      
      const courseData = generateResponse.data
      setGeneratedCourse(courseData)
      
      // Refresh course list (course saved to file)
      await loadCourses()
      
      setProgress(100)
      setStatusMessage('✅ Course generated successfully!')
      
      // Reset selected file
      setSelectedFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      
    } catch (error: any) {
      console.error('Error processing PDF:', error)
      setStatusMessage(`❌ Processing failed: ${error.response?.data?.error || error.message}`)
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
          🧙‍♂️ Computer Magic Academy - Teacher Portal
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
            Switch to Student View 🎓
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
          
          <UploadSection
            className={isDragging ? 'dragging' : ''}
            onClick={() => fileInputRef.current?.click()}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div style={{ fontSize: '60px', marginBottom: '20px' }}>
              {selectedFile ? (selectedFile.name.endsWith('.txt') || selectedFile.name.endsWith('.md') ? '📝' : '📄') : '📄'}
            </div>
            <h3 style={{ margin: '0 0 10px 0', color: '#667eea' }}>
              {selectedFile ? selectedFile.name : 'Click or Drag to Upload Course File'}
            </h3>
            <p style={{ margin: 0, color: '#666' }}>
              Support PDF, TXT, MD formats • AI will analyze and generate detailed knowledge points
            </p>
          </UploadSection>
          
          <FileInput
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,.md,application/pdf,text/plain,text/markdown"
            onChange={handleFileInputChange}
          />
          
          {selectedFile && (
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
              <ProgressBar progress={progress} />
              <p style={{ textAlign: 'center', color: '#667eea', fontWeight: 600 }}>
                {statusMessage}
              </p>
            </div>
          )}
          
          {!isProcessing && statusMessage && (
            <p style={{ 
              textAlign: 'center', 
              marginTop: '20px',
              color: statusMessage.includes('Success') || statusMessage.includes('成功') ? '#4CAF50' : 
                     statusMessage.includes('failed') || statusMessage.includes('失败') ? '#f44336' : '#667eea',
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
              
              <div>
                <strong style={{ color: '#667eea', fontSize: '18px' }}>
                  📚 Knowledge Points ({generatedCourse.materials.length}):
                </strong>
                <KnowledgePointList>
                  {generatedCourse.materials.map((point, index) => (
                    <KnowledgePoint key={index}>
                      <strong>{index + 1}. </strong>{point}
                    </KnowledgePoint>
                  ))}
                </KnowledgePointList>
              </div>
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
                        <span>📚 {course.materials.length} Knowledge Points</span>
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
      </ContentArea>
    </PortalContainer>
  )
}

export default TeacherPortal

