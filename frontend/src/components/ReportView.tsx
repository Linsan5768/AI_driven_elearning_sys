import { useEffect, useMemo, useState } from 'react'
import styled from '@emotion/styled'
import { motion } from 'framer-motion'
import axios from 'axios'

type ReportType = 'module' | 'final' | 'snapshot' | string

interface ReportViewProps {
  studentId?: string
  onBack: () => void
}

interface KnowledgePointStat {
  total: number
  correct: number
  incorrect: number
  error_rate: number
  accuracy: number
}

interface WeakPoint extends KnowledgePointStat {
  knowledge_point: string
}

interface ReportData {
  report_id: string
  student_id: string
  type: ReportType
  area_id?: string | null
  area_name?: string | null
  title: string
  subtitle: string
  generated_at: string
  analysis: {
    total_questions: number
    correct_count: number
    accuracy: number
    knowledge_point_stats: Record<string, KnowledgePointStat>
    weak_points: WeakPoint[]
  }
  ai_summary: string
  metadata?: {
    total_modules?: number
    completed_modules?: number
  }
}

const TYPE_GRADIENTS: Record<string, string> = {
  module: 'linear-gradient(135deg, rgba(96, 119, 255, 0.5) 0%, rgba(82, 67, 194, 0.35) 100%)',
  final: 'linear-gradient(135deg, rgba(255, 214, 109, 0.55) 0%, rgba(236, 164, 64, 0.35) 100%)',
  snapshot: 'linear-gradient(135deg, rgba(78, 205, 196, 0.5) 0%, rgba(66, 134, 244, 0.35) 100%)'
}

const TYPE_ACCENT: Record<string, string> = {
  module: 'rgba(144, 168, 255, 0.9)',
  final: 'rgba(255, 229, 153, 0.95)',
  snapshot: 'rgba(134, 226, 210, 0.95)'
}

const TYPE_BORDER: Record<string, string> = {
  module: 'rgba(144, 168, 255, 0.4)',
  final: 'rgba(255, 229, 153, 0.4)',
  snapshot: 'rgba(134, 226, 210, 0.4)'
}

const Page = styled.div`
  display: grid;
  grid-template-columns: 320px 1fr;
  width: 100%;
  height: 100vh;
  background: radial-gradient(120% 120% at 50% 0%, #1b1f4a 0%, #0a1028 55%, #03040f 100%);
  color: #edf1ff;
  font-family: 'Inter', 'Segoe UI', sans-serif;
`

const Sidebar = styled.aside`
  padding: 44px 28px 32px;
  background: rgba(8, 12, 32, 0.8);
  border-right: 1px solid rgba(120, 146, 255, 0.2);
  backdrop-filter: blur(14px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
`

const SidebarTitle = styled.h2`
  font-size: 22px;
  font-weight: 600;
  margin: 0;
  color: #f6f8ff;
`

const SidebarDescription = styled.p`
  margin: 10px 0 24px;
  font-size: 14px;
  line-height: 1.6;
  color: rgba(214, 221, 255, 0.68);
`

const ReportList = styled.div`
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-right: 6px;
  scroll-behavior: smooth;
  scrollbar-gutter: stable;

  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.04);
    border-radius: 999px;
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(151, 176, 255, 0.35);
    border-radius: 999px;
  }

  &::-webkit-scrollbar-thumb:hover {
    background: rgba(151, 176, 255, 0.55);
  }

  scrollbar-color: rgba(151, 176, 255, 0.45) rgba(255, 255, 255, 0.04);
`

const ReportItem = styled.button<{ $active: boolean; $type: ReportType }>`
  border: 1px solid ${({ $active }) =>
    $active ? 'rgba(140, 162, 255, 0.65)' : 'rgba(140, 162, 255, 0.15)'};
  background: ${({ $active, $type }) =>
    $active ? TYPE_GRADIENTS[$type] ?? TYPE_GRADIENTS.snapshot : 'rgba(255, 255, 255, 0.02)'};
  color: #eef0ff;
  border-radius: 18px;
  padding: 16px 18px;
  cursor: pointer;
  text-align: left;
  transition: border 0.2s ease, transform 0.2s ease, background 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 6px;

  &:hover {
    border-color: rgba(151, 176, 255, 0.45);
    transform: translateY(-2px);
  }

  &:focus {
    outline: none;
    border-color: rgba(151, 176, 255, 0.65);
  }
`

const ReportTitle = styled.span`
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.01em;
`

const ReportMeta = styled.span`
  font-size: 13px;
  color: rgba(214, 221, 255, 0.7);
`

const ReportTypeTag = styled.span<{ $type: ReportType }>`
  align-self: flex-start;
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  padding: 4px 10px;
  border-radius: 999px;
  color: ${({ $type }) => TYPE_ACCENT[$type] ?? TYPE_ACCENT.snapshot};
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid ${({ $type }) => TYPE_BORDER[$type] ?? TYPE_BORDER.snapshot};
`

const EmptySidebarMessage = styled.div`
  margin-top: 40px;
  font-size: 14px;
  color: rgba(214, 221, 255, 0.55);
  line-height: 1.6;
`

const Content = styled.main`
  position: relative;
  padding: 48px 60px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 28px;
`

const BackButton = styled.button`
  align-self: flex-start;
  padding: 10px 20px;
  border-radius: 999px;
  border: 1px solid rgba(140, 162, 255, 0.35);
  background: rgba(255, 255, 255, 0.04);
  color: #e8ecff;
  font-size: 13px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  cursor: pointer;
  transition: border 0.2s ease, transform 0.2s ease;

  &:hover {
    border-color: rgba(140, 162, 255, 0.6);
    transform: translateY(-1px);
  }
`

const Header = styled.div`
  display: flex;
  flex-direction: column;
  gap: 14px;
`

const HeaderTop = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
`

const HeaderBadge = styled.span<{ $variant?: 'default' | 'outline'; $type?: ReportType }>`
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  padding: 6px 12px;
  border-radius: 999px;
  border: ${({ $variant, $type }) =>
    $variant === 'outline'
      ? '1px solid rgba(220, 226, 255, 0.35)'
      : `1px solid ${TYPE_BORDER[$type ?? 'snapshot'] ?? TYPE_BORDER.snapshot}`};
  background: ${({ $variant, $type }) =>
    $variant === 'outline'
      ? 'rgba(255, 255, 255, 0.04)'
      : TYPE_GRADIENTS[$type ?? 'snapshot']};
  color: ${({ $variant, $type }) =>
    $variant === 'outline'
      ? 'rgba(220, 226, 255, 0.85)'
      : TYPE_ACCENT[$type ?? 'snapshot'] ?? TYPE_ACCENT.snapshot};
`

const HeaderTitle = styled.h1`
  margin: 0;
  font-size: 32px;
  font-weight: 600;
  color: #f5f7ff;
  letter-spacing: 0.02em;
`

const HeaderSubtitle = styled.p`
  margin: 0;
  font-size: 16px;
  color: rgba(214, 221, 255, 0.78);
  line-height: 1.6;
`

const Timestamp = styled.span`
  font-size: 13px;
  color: rgba(214, 221, 255, 0.6);
`

const MetadataStrip = styled.div`
  display: flex;
  gap: 18px;
  align-items: center;
  font-size: 13px;
  color: rgba(214, 221, 255, 0.75);
`

const ControlBar = styled.div`
  margin-top: 12px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
`

const PrimaryButton = styled.button`
  padding: 10px 20px;
  border-radius: 999px;
  border: none;
  background: linear-gradient(135deg, rgba(98, 119, 255, 0.9) 0%, rgba(82, 67, 194, 0.8) 100%);
  color: #f5f7ff;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.04em;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 20px rgba(84, 105, 255, 0.24);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    box-shadow: none;
    transform: none;
  }
`

const SecondaryButton = styled.button`
  padding: 10px 20px;
  border-radius: 999px;
  border: 1px solid rgba(140, 162, 255, 0.35);
  background: rgba(255, 255, 255, 0.05);
  color: #e8ecff;
  font-size: 13px;
  letter-spacing: 0.04em;
  cursor: pointer;
  transition: border 0.2s ease, transform 0.2s ease;

  &:hover {
    border-color: rgba(140, 162, 255, 0.6);
    transform: translateY(-1px);
  }
`

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 18px;
`

const MetricCard = styled(motion.div)`
  background: rgba(10, 16, 36, 0.8);
  border-radius: 18px;
  padding: 22px;
  border: 1px solid rgba(126, 140, 220, 0.25);
  box-shadow: 0 12px 28px rgba(6, 12, 32, 0.45);
  display: flex;
  flex-direction: column;
  gap: 12px;
`

const MetricLabel = styled.span`
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(214, 221, 255, 0.55);
`

const MetricValue = styled.span`
  font-size: 34px;
  font-weight: 600;
  color: #f5f7ff;
`

const SectionCard = styled(motion.div)`
  background: rgba(10, 16, 36, 0.8);
  border-radius: 20px;
  padding: 28px 32px;
  border: 1px solid rgba(126, 140, 220, 0.25);
  box-shadow: 0 12px 32px rgba(6, 12, 32, 0.4);
  display: flex;
  flex-direction: column;
  gap: 20px;
`

const SectionTitle = styled.h3`
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 0.03em;
  color: #f5f7ff;
`

const KnowledgeList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 14px;
`

const KnowledgeRow = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`

const KnowledgeHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: rgba(214, 221, 255, 0.82);
`

const ProgressTrack = styled.div`
  width: 100%;
  height: 12px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 999px;
  overflow: hidden;
`

const ProgressFill = styled(motion.div)`
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(96, 119, 255, 0.9) 0%, rgba(66, 134, 244, 0.8) 100%);
`

const KnowledgeStats = styled.div`
  font-size: 12px;
  color: rgba(214, 221, 255, 0.58);
`

const WeakPointGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
`

const WeakPointCard = styled.div`
  background: rgba(255, 204, 143, 0.08);
  border-radius: 16px;
  border: 1px solid rgba(255, 204, 143, 0.25);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  color: rgba(255, 229, 195, 0.92);
`

const SummaryText = styled.p`
  margin: 0;
  font-size: 15px;
  line-height: 1.9;
  color: rgba(227, 232, 255, 0.92);
  white-space: pre-wrap;
`

const LoadingState = styled.div`
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 18px;
  color: rgba(214, 221, 255, 0.75);
  font-size: 16px;
`

const LoadingSpinner = styled(motion.div)`
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 3px solid rgba(214, 221, 255, 0.2);
  border-top-color: rgba(214, 221, 255, 0.75);
`

const ErrorState = styled.div`
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 18px;
  color: rgba(255, 189, 189, 0.85);
  font-size: 16px;
  text-align: center;
  max-width: 440px;
`

const EmptyState = styled.div`
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 18px;
  color: rgba(214, 221, 255, 0.75);
  font-size: 16px;
  text-align: center;
  max-width: 460px;
`

const ReportView = ({ studentId = 'default_student', onBack }: ReportViewProps) => {
  const [reports, setReports] = useState<ReportData[]>([])
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const API_BASE_URL = 'http://127.0.0.1:8001/api'

  const fetchReports = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await axios.get<{ reports: ReportData[] }>(`${API_BASE_URL}/reports/${studentId}`)
      const fetchedReports = response.data?.reports ?? []
      setReports(fetchedReports)

      if (fetchedReports.length > 0) {
        setSelectedReportId(prev =>
          prev && fetchedReports.some(report => report.report_id === prev)
            ? prev
            : fetchedReports[0].report_id
        )
      } else {
        setSelectedReportId(null)
      }
    } catch (err: any) {
      console.error('Failed to fetch reports:', err)
      setError(err.response?.data?.error || 'Unable to load reports. Please try again later.')
    } finally {
      setLoading(false)
    }
  }

  // Fetch reports when component mounts or studentId changes
  useEffect(() => {
    fetchReports()
  }, [studentId])

  const selectedReport = useMemo(
    () => reports.find(report => report.report_id === selectedReportId) ?? null,
    [reports, selectedReportId]
  )

  const knowledgeEntries = useMemo(() => {
    if (!selectedReport) return []
    const stats = selectedReport.analysis.knowledge_point_stats ?? {}
    return Object.entries(stats).sort((a, b) => b[1].accuracy - a[1].accuracy)
  }, [selectedReport])

  const weakPoints = selectedReport?.analysis?.weak_points ?? []

  const formatDateTime = (value: string) =>
    new Date(value).toLocaleString('en-US', {
      hour12: false,
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })

  const handleDownloadPDF = () => {
    alert('PDF export is coming soon.')
  }

  return (
    <Page>
      <Sidebar>
        <SidebarTitle>Report Library</SidebarTitle>
        <SidebarDescription>
          Review every duel the Academy has archived. Select a report to see the full narrative and performance data.
        </SidebarDescription>

        <ReportList>
          {reports.map(report => (
            <ReportItem
              key={report.report_id}
              $active={report.report_id === selectedReportId}
              $type={report.type}
              onClick={() => setSelectedReportId(report.report_id)}
            >
              <ReportTypeTag $type={report.type}>
                {report.type === 'final'
                  ? 'Final Summary'
                  : report.type === 'module'
                  ? 'Module Report'
                  : 'Snapshot'}
              </ReportTypeTag>
              <ReportTitle>{report.title}</ReportTitle>
              <ReportMeta>{formatDateTime(report.generated_at)}</ReportMeta>
            </ReportItem>
          ))}

          {!loading && reports.length === 0 ? (
            <EmptySidebarMessage>No reports yet. Complete a battle to unlock your first performance summary.</EmptySidebarMessage>
          ) : null}
        </ReportList>
      </Sidebar>

      <Content>
        <BackButton onClick={onBack}>Back to Map</BackButton>

        {loading ? (
          <LoadingState>
            <LoadingSpinner
              animate={{ rotate: 360 }}
              transition={{ duration: 1.4, repeat: Infinity, ease: 'linear' }}
            />
            Gathering the latest scrolls...
          </LoadingState>
        ) : error ? (
          <ErrorState>
            <div>{error}</div>
            <SecondaryButton onClick={fetchReports}>Try Again</SecondaryButton>
          </ErrorState>
        ) : !selectedReport ? (
          <EmptyState>
            <div>Select a report from the archive to view detailed performance insights.</div>
          </EmptyState>
        ) : (
          <>
            <Header>
              <HeaderTop>
                <HeaderBadge $type={selectedReport.type}>
                  {selectedReport.type === 'final'
                    ? 'Grand Summary'
                    : selectedReport.type === 'module'
                    ? 'Module Report'
                    : 'Snapshot'}
                </HeaderBadge>
                {selectedReport.area_name ? (
                  <HeaderBadge $variant="outline">{selectedReport.area_name}</HeaderBadge>
                ) : null}
              </HeaderTop>
              <HeaderTitle>{selectedReport.title}</HeaderTitle>
              <HeaderSubtitle>{selectedReport.subtitle}</HeaderSubtitle>
              <Timestamp>Issued on {formatDateTime(selectedReport.generated_at)}</Timestamp>
              {selectedReport.metadata?.total_modules ? (
                <MetadataStrip>
                  <span>
                    Modules completed: {selectedReport.metadata.completed_modules ?? 0} of{' '}
                    {selectedReport.metadata.total_modules}
                  </span>
                </MetadataStrip>
              ) : null}
              <ControlBar>
                <SecondaryButton onClick={fetchReports}>Refresh</SecondaryButton>
                <PrimaryButton onClick={handleDownloadPDF}>Export PDF (Coming Soon)</PrimaryButton>
              </ControlBar>
            </Header>

            <MetricsGrid>
              <MetricCard
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 }}
              >
                <MetricLabel>Total Questions</MetricLabel>
                <MetricValue>{selectedReport.analysis.total_questions}</MetricValue>
              </MetricCard>
              <MetricCard
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                <MetricLabel>Correct Answers</MetricLabel>
                <MetricValue>{selectedReport.analysis.correct_count}</MetricValue>
              </MetricCard>
              <MetricCard
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 }}
              >
                <MetricLabel>Accuracy</MetricLabel>
                <MetricValue>{selectedReport.analysis.accuracy.toFixed(1)}%</MetricValue>
              </MetricCard>
              <MetricCard
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <MetricLabel>Challenging Topics</MetricLabel>
                <MetricValue>{weakPoints.length}</MetricValue>
              </MetricCard>
            </MetricsGrid>

            <SectionCard
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.25 }}
            >
              <SectionTitle>Knowledge Point Mastery</SectionTitle>
              {knowledgeEntries.length === 0 ? (
                <div style={{ color: 'rgba(214, 221, 255, 0.6)' }}>
                  No knowledge points recorded yet. Complete a battle to populate this section.
                </div>
              ) : (
                <KnowledgeList>
                  {knowledgeEntries.map(([key, stats]) => (
                    <KnowledgeRow key={key}>
                      <KnowledgeHeader>
                        <span>{key}</span>
                        <span>{stats.correct}/{stats.total} correct</span>
                      </KnowledgeHeader>
                      <ProgressTrack>
                        <ProgressFill
                          initial={{ width: 0 }}
                          animate={{ width: `${Math.min(Math.max(stats.accuracy, 0), 100)}%` }}
                          transition={{ duration: 0.8 }}
                        />
                      </ProgressTrack>
                      <KnowledgeStats>
                        Accuracy {stats.accuracy.toFixed(1)}% • Error rate {stats.error_rate.toFixed(1)}%
                      </KnowledgeStats>
                    </KnowledgeRow>
                  ))}
                </KnowledgeList>
              )}
            </SectionCard>

            <SectionCard
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <SectionTitle>Focus Areas</SectionTitle>
              {weakPoints.length === 0 ? (
                <div style={{ color: 'rgba(214, 221, 255, 0.6)' }}>
                  No pressing challenges detected. Continue reinforcing your mastery with review sessions.
                </div>
              ) : (
                <WeakPointGrid>
                  {weakPoints.map(point => (
                    <WeakPointCard key={point.knowledge_point}>
                      <strong>{point.knowledge_point}</strong>
                      <span>
                        Accuracy {point.accuracy.toFixed(1)}% ({point.correct}/{point.total} correct)
                      </span>
                      <span>Mistakes {point.incorrect} • Error rate {point.error_rate.toFixed(1)}%</span>
                    </WeakPointCard>
                  ))}
                </WeakPointGrid>
              )}
            </SectionCard>

            <SectionCard
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35 }}
            >
              <SectionTitle>Academy Narrative</SectionTitle>
              <SummaryText>{selectedReport.ai_summary}</SummaryText>
            </SectionCard>
          </>
        )}
      </Content>
    </Page>
  )
}

export default ReportView
