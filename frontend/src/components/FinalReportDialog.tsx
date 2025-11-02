import React, { useState, useEffect } from 'react'
import styled from '@emotion/styled'
import { motion } from 'framer-motion'
import axios from 'axios'

interface FinalReportDialogProps {
  isOpen: boolean
  areaId: string
  subject: string
  onDownload: () => void
  onExit: () => void
}

const DialogOverlay = styled(motion.div)`
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(8px);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
`

const DialogContainer = styled(motion.div)`
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 20px;
  padding: 40px;
  max-width: 900px;
  max-height: 90vh;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  border: 2px solid rgba(255, 215, 0, 0.3);
  display: flex;
  flex-direction: column;
  gap: 24px;
  overflow-y: auto;
  color: #fff;
`

const Header = styled.div`
  text-align: center;
  border-bottom: 2px solid rgba(255, 215, 0, 0.3);
  padding-bottom: 20px;
`

const Title = styled.h1`
  font-size: 32px;
  margin: 0 0 10px 0;
  color: #ffd700;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
`

const Subtitle = styled.p`
  font-size: 18px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
`

const ReportContent = styled.div`
  flex: 1;
  padding: 24px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  line-height: 1.8;
  font-size: 16px;
  white-space: pre-wrap;
  color: rgba(255, 255, 255, 0.9);
`

const ButtonContainer = styled.div`
  display: flex;
  gap: 16px;
  justify-content: center;
  padding-top: 20px;
  border-top: 2px solid rgba(255, 215, 0, 0.3);
`

const Button = styled.button<{ variant?: 'primary' | 'secondary' }>`
  padding: 14px 32px;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  background: ${props => props.variant === 'primary' 
    ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    : 'rgba(255, 255, 255, 0.1)'};
  color: white;
  border: 2px solid ${props => props.variant === 'primary'
    ? 'rgba(255, 255, 255, 0.3)'
    : 'rgba(255, 255, 255, 0.2)'};

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
    background: ${props => props.variant === 'primary'
      ? 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)'
      : 'rgba(255, 255, 255, 0.2)'};
  }

  &:active {
    transform: translateY(0);
  }
`

const LoadingState = styled.div`
  text-align: center;
  padding: 40px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 18px;
`

const FinalReportDialog: React.FC<FinalReportDialogProps> = ({
  isOpen,
  areaId,
  subject,
  onDownload,
  onExit
}) => {
  const [report, setReport] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen && areaId) {
      generateFinalReport()
    }
  }, [isOpen, areaId])

  const generateFinalReport = async () => {
    setLoading(true)
    setError(null)

    try {
      // Generate final report for this subject
      const response = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api'}/reports/generate-subject-final`,
        {
          student_id: 'default_student',
          area_id: areaId,
          subject: subject
        },
        {
          timeout: 60000 // 60 second timeout for LLM generation
        }
      )

      if (response.data) {
        setReport(response.data)
      } else {
        setError('Failed to generate report')
      }
    } catch (err: any) {
      console.error('Failed to generate final report:', err)
      setError(err.response?.data?.error || err.message || 'Failed to generate report. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    if (!report || !report.report_id) {
      console.error('No report or report_id available')
      return
    }

    try {
      console.log('📥 Downloading PDF report:', report.report_id)
      
      // Download PDF from backend
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api'}/reports/${report.report_id}/download-pdf`,
        {
          responseType: 'blob',
          timeout: 30000,
          headers: {
            'Accept': 'application/pdf'
          }
        }
      )

      console.log('✅ PDF downloaded, content-type:', response.headers['content-type'] || response.headers['content-type'])
      console.log('📊 Response data size:', response.data?.size || 'unknown')

      // Check if response is actually an error (JSON response instead of PDF)
      // If response data is small (< 1000 bytes), it might be an error message
      if (response.data?.size < 1000) {
        // Try to read as text to check if it's an error
        const text = await new Promise((resolve) => {
          const reader = new FileReader()
          reader.onload = () => resolve(reader.result as string)
          reader.readAsText(response.data)
        })
        
        // Check if it's JSON error
        try {
          const errorJson = JSON.parse(text as string)
          if (errorJson.error) {
            console.error('❌ Server returned error:', errorJson.error)
            alert(`Failed to download PDF: ${errorJson.error}`)
            return
          }
        } catch {
          // Not JSON, might be actual PDF with small content
          console.log('📄 Small PDF detected, proceeding with download')
        }
      }

      // Verify content type if available
      const contentType = response.headers['content-type'] || response.headers['content-type']
      if (contentType && !contentType.includes('pdf') && !contentType.includes('octet-stream')) {
        console.warn('⚠️ Unexpected content type:', contentType, 'but proceeding with download')
      }

      // Create download link
      const blob = new Blob([response.data], { type: 'application/pdf' })
      
      // Verify blob is valid
      if (blob.size === 0) {
        console.error('❌ PDF blob is empty')
        alert('Failed to download PDF: Empty file received')
        return
      }
      
      console.log('📦 PDF blob created, size:', blob.size, 'bytes')
      
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const subjectName = subject.replace(/\s+/g, '_')
      a.download = `${subjectName}_Final_Report_${Date.now()}.pdf`
      
      // Add to DOM and trigger download
      document.body.appendChild(a)
      a.click()
      
      console.log('✅ PDF download initiated successfully')

      // Clean up after a delay
      setTimeout(() => {
        if (document.body.contains(a)) {
          document.body.removeChild(a)
        }
        URL.revokeObjectURL(url)
        console.log('🧹 Cleaned up download link')
      }, 200)

      // Call callback without showing error (download succeeded)
      onDownload()
    } catch (err: any) {
      // Check if it's actually a network error or if download was successful
      // Sometimes axios throws errors even when download succeeds
      if (err.response?.status === 200 && err.response?.data) {
        // Response status is 200, try to use the data anyway
        console.log('⚠️ Axios error but status is 200, attempting to use response data')
        try {
          const blob = new Blob([err.response.data], { type: 'application/pdf' })
          if (blob.size > 0) {
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            const subjectName = subject.replace(/\s+/g, '_')
            a.download = `${subjectName}_Final_Report_${Date.now()}.pdf`
            document.body.appendChild(a)
            a.click()
            setTimeout(() => {
              if (document.body.contains(a)) {
                document.body.removeChild(a)
              }
              URL.revokeObjectURL(url)
            }, 200)
            console.log('✅ PDF downloaded despite axios error')
            onDownload()
            return
          }
        } catch (fallbackErr) {
          console.error('❌ Fallback download also failed:', fallbackErr)
        }
      }
      
      // Real error occurred
      console.error('❌ Failed to download PDF report:', err)
      console.error('Error details:', {
        message: err.message,
        response: err.response?.data,
        status: err.response?.status
      })
      
      let errorMessage = 'Failed to download PDF report. '
      if (err.response?.status === 500) {
        errorMessage += 'Server error. Please check backend logs.'
      } else if (err.response?.data) {
        // Try to extract error message from response
        if (typeof err.response.data === 'string') {
          try {
            const errorJson = JSON.parse(err.response.data)
            errorMessage += errorJson.error || err.response.data
          } catch {
            errorMessage += err.response.data.substring(0, 100)
          }
        } else if (err.response.data.error) {
          errorMessage += err.response.data.error
        }
      } else if (err.message) {
        errorMessage += err.message
      }
      
      alert(errorMessage)
    }
  }

  if (!isOpen) return null

  return (
    <DialogOverlay
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={(e) => {
        // Only allow closing via exit button
        e.stopPropagation()
      }}
    >
      <DialogContainer
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        <Header>
          <Title>🎓 Subject Completion Report</Title>
          <Subtitle>{subject}</Subtitle>
        </Header>

        {loading ? (
          <LoadingState>Generating your final report...</LoadingState>
        ) : error ? (
          <LoadingState style={{ color: '#ff6b6b' }}>{error}</LoadingState>
        ) : report ? (
          <>
            <ReportContent>
              <div style={{ marginBottom: '20px', fontSize: '20px', fontWeight: 'bold', color: '#ffd700' }}>
                {report.title}
              </div>
              <div style={{ marginBottom: '20px', fontSize: '14px', color: 'rgba(255, 255, 255, 0.7)' }}>
                {report.subtitle}
              </div>
              <div style={{ whiteSpace: 'pre-wrap' }}>
                {report.ai_summary || 'Report summary will appear here.'}
              </div>
            </ReportContent>

            <ButtonContainer>
              <Button variant="primary" onClick={handleDownload}>
                📥 Download Report
              </Button>
              <Button variant="secondary" onClick={onExit}>
                🚪 Exit to Login
              </Button>
            </ButtonContainer>
          </>
        ) : null}
      </DialogContainer>
    </DialogOverlay>
  )
}

export default FinalReportDialog

