import { useState, useEffect } from 'react'
import styled from '@emotion/styled'
import { motion } from 'framer-motion'
import axios from 'axios'

const ReportContainer = styled.div`
  width: 100%;
  height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 100%);
  color: white;
  padding: 40px;
  overflow-y: auto;
  font-family: 'Press Start 2P', monospace;
  position: relative;
  
  /* 像素风格背景 */
  background-image: 
    linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
  background-size: 20px 20px;
`

const HeaderSection = styled.div`
  text-align: center;
  margin-bottom: 40px;
  padding: 20px;
  background: rgba(102, 126, 234, 0.2);
  border: 4px solid #667eea;
  border-radius: 8px;
  box-shadow: 0 0 20px rgba(102, 126, 234, 0.5);
`

const Title = styled.h1`
  font-size: 28px;
  color: #ffd700;
  text-shadow: 2px 2px 0px #ff6b6b, 4px 4px 0px rgba(0, 0, 0, 0.3);
  margin-bottom: 20px;
  letter-spacing: 2px;
`

const BackButton = styled(motion.button)`
  position: absolute;
  top: 30px;
  left: 30px;
  padding: 15px 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: 3px solid #fff;
  border-radius: 8px;
  color: white;
  font-size: 14px;
  font-family: 'Press Start 2P', monospace;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  transition: all 0.3s;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
  }

  &:active {
    transform: translateY(0px);
  }
`

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
`

const StatCard = styled(motion.div)`
  background: rgba(15, 52, 96, 0.8);
  border: 4px solid #4ecdc4;
  border-radius: 12px;
  padding: 25px;
  text-align: center;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
`

const StatValue = styled.div<{ color?: string }>`
  font-size: 48px;
  color: ${props => props.color || '#4ecdc4'};
  text-shadow: 2px 2px 0px rgba(0, 0, 0, 0.5);
  margin-bottom: 10px;
`

const StatLabel = styled.div`
  font-size: 12px;
  color: #a0a0a0;
  letter-spacing: 1px;
`

const ChartSection = styled.div`
  background: rgba(15, 52, 96, 0.8);
  border: 4px solid #667eea;
  border-radius: 12px;
  padding: 30px;
  margin-bottom: 40px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
`

const ChartTitle = styled.h2`
  font-size: 18px;
  color: #ffd700;
  margin-bottom: 25px;
  text-align: center;
`

const KnowledgePointBar = styled.div`
  margin-bottom: 20px;
`

const KPLabel = styled.div`
  font-size: 11px;
  color: #fff;
  margin-bottom: 8px;
  display: flex;
  justify-content: space-between;
`

const BarContainer = styled.div`
  width: 100%;
  height: 30px;
  background: rgba(0, 0, 0, 0.3);
  border: 2px solid #4ecdc4;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
`

const BarFill = styled(motion.div)<{ accuracy: number }>`
  height: 100%;
  background: ${props => 
    props.accuracy >= 80 ? 'linear-gradient(90deg, #4ecdc4 0%, #44a08d 100%)' :
    props.accuracy >= 60 ? 'linear-gradient(90deg, #f7b731 0%, #f7b731 100%)' :
    'linear-gradient(90deg, #ee5a6f 0%, #c23a4d 100%)'
  };
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 10px;
  font-size: 10px;
  font-weight: bold;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
`

const ReportTextSection = styled.div`
  background: rgba(15, 52, 96, 0.8);
  border: 4px solid #ff6b6b;
  border-radius: 12px;
  padding: 30px;
  margin-bottom: 40px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
`

const AIReportText = styled.div`
  font-size: 13px;
  line-height: 2;
  color: #e0e0e0;
  white-space: pre-wrap;
  font-family: 'Courier New', monospace;
`

const ActionButtons = styled.div`
  display: flex;
  gap: 20px;
  justify-content: center;
  margin-top: 40px;
`

const ActionButton = styled(motion.button)<{ variant?: 'primary' | 'secondary' }>`
  padding: 15px 40px;
  background: ${props => 
    props.variant === 'primary' 
      ? 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
      : 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
  };
  border: 3px solid #fff;
  border-radius: 8px;
  color: white;
  font-size: 14px;
  font-family: 'Press Start 2P', monospace;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  transition: all 0.3s;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(255, 255, 255, 0.4);
  }

  &:active {
    transform: translateY(0px);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`

const LoadingContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 80vh;
`

const LoadingText = styled.div`
  font-size: 18px;
  color: #4ecdc4;
  margin-top: 20px;
  animation: pulse 1.5s infinite;

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
`

const ErrorContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 80vh;
  text-align: center;
`

const ErrorText = styled.div`
  font-size: 16px;
  color: #ff6b6b;
  margin-bottom: 30px;
  max-width: 600px;
  line-height: 1.8;
`

interface ReportViewProps {
  studentId?: string
  onBack: () => void
}

interface ReportData {
  student_id: string
  generated_at: string
  analysis: {
    total_questions: number
    correct_count: number
    accuracy: number
    knowledge_point_stats: Record<string, {
      total: number
      correct: number
      incorrect: number
      error_rate: number
      accuracy: number
    }>
    weak_points: Array<{
      knowledge_point: string
      total: number
      correct: number
      incorrect: number
      error_rate: number
      accuracy: number
    }>
  }
  ai_summary: string
  total_battles: number
}

const ReportView = ({ studentId = 'default_student', onBack }: ReportViewProps) => {
  const [reportData, setReportData] = useState<ReportData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const API_BASE_URL = 'http://127.0.0.1:8001/api'

  useEffect(() => {
    fetchReport()
  }, [studentId])

  const fetchReport = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await axios.get(`${API_BASE_URL}/generate-report/${studentId}`)
      setReportData(response.data)
      console.log('📊 Report loaded:', response.data)
    } catch (err: any) {
      console.error('Failed to fetch report:', err)
      setError(err.response?.data?.error || '报告生成失败，请稍后再试')
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadPDF = () => {
    // TODO: Implement PDF download functionality
    alert('PDF下载功能开发中...')
  }

  if (loading) {
    return (
      <ReportContainer>
        <LoadingContainer>
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          >
            <div style={{ fontSize: '64px' }}>⚡</div>
          </motion.div>
          <LoadingText>正在生成学习报告...</LoadingText>
        </LoadingContainer>
      </ReportContainer>
    )
  }

  if (error) {
    return (
      <ReportContainer>
        <BackButton onClick={onBack} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
          ← 返回
        </BackButton>
        <ErrorContainer>
          <div style={{ fontSize: '64px', marginBottom: '20px' }}>❌</div>
          <ErrorText>{error}</ErrorText>
          <ActionButton onClick={fetchReport} variant="primary">
            重新生成
          </ActionButton>
        </ErrorContainer>
      </ReportContainer>
    )
  }

  if (!reportData) {
    return null
  }

  const { analysis, ai_summary } = reportData

  return (
    <ReportContainer>
      <BackButton onClick={onBack} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
        ← 返回
      </BackButton>

      <HeaderSection>
        <Title>🎓 学习成长报告 🎓</Title>
        <div style={{ fontSize: '12px', color: '#a0a0a0' }}>
          生成时间: {new Date(reportData.generated_at).toLocaleString('zh-CN')}
        </div>
      </HeaderSection>

      <StatsGrid>
        <StatCard
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <StatValue color="#4ecdc4">{analysis.total_questions}</StatValue>
          <StatLabel>总答题数</StatLabel>
        </StatCard>

        <StatCard
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <StatValue color="#f7b731">{analysis.correct_count}</StatValue>
          <StatLabel>答对题数</StatLabel>
        </StatCard>

        <StatCard
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <StatValue 
            color={
              analysis.accuracy >= 80 ? '#4ecdc4' :
              analysis.accuracy >= 60 ? '#f7b731' : '#ee5a6f'
            }
          >
            {analysis.accuracy}%
          </StatValue>
          <StatLabel>总体准确率</StatLabel>
        </StatCard>

        <StatCard
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <StatValue color="#ff6b6b">{analysis.weak_points.length}</StatValue>
          <StatLabel>需要加强的知识点</StatLabel>
        </StatCard>
      </StatsGrid>

      <ChartSection>
        <ChartTitle>📊 知识点掌握情况</ChartTitle>
        {Object.entries(analysis.knowledge_point_stats).map(([kp, stats], index) => (
          <KnowledgePointBar key={kp}>
            <KPLabel>
              <span>{kp}</span>
              <span>{stats.correct}/{stats.total} 题</span>
            </KPLabel>
            <BarContainer>
              <BarFill
                accuracy={stats.accuracy}
                initial={{ width: 0 }}
                animate={{ width: `${stats.accuracy}%` }}
                transition={{ duration: 1, delay: index * 0.1 }}
              >
                {stats.accuracy.toFixed(0)}%
              </BarFill>
            </BarContainer>
          </KnowledgePointBar>
        ))}
      </ChartSection>

      <ReportTextSection>
        <ChartTitle>🤖 AI 学习分析报告</ChartTitle>
        <AIReportText>{ai_summary}</AIReportText>
      </ReportTextSection>

      <ActionButtons>
        <ActionButton 
          variant="primary" 
          onClick={handleDownloadPDF}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          📥 下载PDF
        </ActionButton>
        <ActionButton 
          variant="secondary" 
          onClick={onBack}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          🏠 返回主页
        </ActionButton>
      </ActionButtons>
    </ReportContainer>
  )
}

export default ReportView
