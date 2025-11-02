import { useState, useEffect } from 'react'
import styled from '@emotion/styled'
import { motion, AnimatePresence } from 'framer-motion'
import GameMap from './components/GameMap'
import AreaView from './components/AreaView'
import TeacherPortal from './components/TeacherPortal'
import ReportView from './components/ReportView'
import axios from 'axios'

const AppContainer = styled.div`
  width: 100vw;
  height: 100vh;
  background: #1a1a1a;
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
`

const LandingContainer = styled.div`
  width: 100vw;
  height: 100vh;
  background: url('/HP.png') center/cover no-repeat;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
`

const LandingCard = styled.div`
  background: rgba(10, 10, 10, 0.78);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 48px 56px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  max-width: 420px;
  width: 100%;
`

const LandingTitle = styled.h1`
  font-size: 36px;
  font-weight: 700;
  text-align: center;
  margin: 0;
  letter-spacing: 1px;
`

const LandingSubtitle = styled.p`
  margin: 0;
  text-align: center;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.6;
`

const LandingButtonGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
`

const LandingButton = styled.button<{ $background: string }>`
  width: 100%;
  padding: 18px 20px;
  border-radius: 14px;
  border: none;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  color: #ffffff;
  letter-spacing: 0.5px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  background: ${({ $background }) => `url('${$background}') center/cover no-repeat`};
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
  position: relative;
  overflow: hidden;
  text-transform: uppercase;

  &::after {
    content: '';
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.35);
    transition: background 0.2s ease;
  }

  span {
    position: relative;
    z-index: 1;
  }

  &:hover::after {
    background: rgba(0, 0, 0, 0.45);
  }

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.35);
  }

  &:active {
    transform: translateY(0);
  }
`

const LandingStatus = styled.div`
  text-align: center;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  line-height: 1.6;
`

import { API_BASE_URL, BACKEND_URL } from './config/apiConfig'

function App() {
  const [gameState, setGameState] = useState<any>(null)
  const [currentView, setCurrentView] = useState('map')
  const [selectedArea, setSelectedArea] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [connectionStatus, setConnectionStatus] = useState<string>('Checking connection...')
  const [mode, setMode] = useState<'login' | 'student' | 'teacher'>('login')

  useEffect(() => {
    checkBackendStatus()
  }, [])

  const checkBackendStatus = async () => {
    try {
      setError(null)
      setConnectionStatus('Checking backend server...')
      
      console.log('Checking backend status at:', BACKEND_URL)
      const statusResponse = await axios.get(BACKEND_URL)
      console.log('Backend status response:', statusResponse.data)
      
      if (statusResponse.data.status === 'ok') {
        setConnectionStatus('Backend connected, fetching game state...')
        await fetchGameState()
      }
    } catch (error: any) {
      console.error('Failed to connect to backend:', error)
      setError(`Failed to connect to game server: ${error.message}`)
      setConnectionStatus('Connection failed')
    }
  }

  const fetchGameState = async () => {
    try {
      setConnectionStatus('Fetching game state...')
      console.log('Fetching game state from:', `${API_BASE_URL}/game-state`)
      const response = await axios.get(`${API_BASE_URL}/game-state`)
      console.log('Game state received:', response.data)
      setGameState(response.data)
      setConnectionStatus('Game state loaded')
    } catch (error: any) {
      console.error('Failed to fetch game state:', error)
      setError(`Failed to fetch game state: ${error.message}`)
      setConnectionStatus('Failed to load game state')
      throw error
    }
  }

  const enterStudentMode = async () => {
    setMode('student')
    setCurrentView('map')
    setSelectedArea(null)
    if (!gameState) {
      try {
        await fetchGameState()
      } catch {
        // error is handled within fetchGameState
      }
    }
  }

  const enterTeacherMode = () => {
    setMode('teacher')
    setCurrentView('map')
    setSelectedArea(null)
  }

  const handleLogout = () => {
    setMode('login')
    setCurrentView('map')
    setSelectedArea(null)
  }

  const handleAreaComplete = async (areaId: string) => {
    try {
      await axios.post(`${API_BASE_URL}/complete-area/${areaId}`)
      await fetchGameState()
      setCurrentView('map')
      setSelectedArea(null)
    } catch (error: any) {
      console.error('Failed to complete area:', error)
      setError(`Failed to update game state: ${error.message}`)
    }
  }

  // This function is now handled inside GameMap component
  // const handleAreaClick = (areaId: string) => {
  //   setSelectedArea(areaId)
  //   setCurrentView('area')
  // }

  if (error && mode !== 'login') {
    return (
      <AppContainer>
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <h2 style={{ color: '#ff4444' }}>{error}</h2>
          <div style={{ marginTop: '10px', color: '#666' }}>
            Connection Status: {connectionStatus}
          </div>
          <button 
            onClick={checkBackendStatus}
            style={{
              marginTop: '20px',
              padding: '10px 20px',
              background: '#2196F3',
              border: 'none',
              borderRadius: '5px',
              color: 'white',
              cursor: 'pointer'
            }}
          >
            Retry Connection
          </button>
          <div style={{ marginTop: '20px', color: '#666' }}>
            <p>Backend URL: {BACKEND_URL}</p>
            <p>API URL: {API_BASE_URL}</p>
            <p>
              Try visiting{' '}
              <a 
                href={BACKEND_URL} 
                target="_blank" 
                rel="noopener noreferrer"
                style={{ color: '#2196F3' }}
              >
                {BACKEND_URL}
              </a>
              {' '}to check if the backend is running
            </p>
          </div>
        </div>
      </AppContainer>
    )
  }

  if (mode === 'login') {
    return (
      <LandingContainer>
        <LandingCard>
          <LandingTitle>Magic Learning Realm</LandingTitle>
          <LandingSubtitle>
            Choose your role to enter the learning world. Teachers manage courses, students explore the map.
          </LandingSubtitle>
          <LandingButtonGroup>
            <LandingButton $background="/button1.png" onClick={enterStudentMode}>
              <span>Enter Student Mode</span>
            </LandingButton>
            <LandingButton $background="/button2.png" onClick={enterTeacherMode}>
              <span>Enter Teacher Mode</span>
            </LandingButton>
          </LandingButtonGroup>
          <LandingStatus>
            Status: {connectionStatus}
            {error ? (
              <>
                <br />
                <span style={{ color: '#ff8080' }}>{error}</span>
              </>
            ) : null}
          </LandingStatus>
          <button
            onClick={checkBackendStatus}
            style={{
              padding: '10px 20px',
              background: 'rgba(255, 255, 255, 0.12)',
              border: '1px solid rgba(255, 255, 255, 0.25)',
              borderRadius: '12px',
              color: '#fff',
              cursor: 'pointer'
            }}
          >
            Check Server Status
          </button>
        </LandingCard>
      </LandingContainer>
    )
  }

  if (!gameState) {
    return (
      <AppContainer>
        <div style={{ textAlign: 'center' }}>
          <h2>Loading game...</h2>
          <div style={{ marginTop: '20px', color: '#666' }}>
            Status: {connectionStatus}
          </div>
          <button 
            onClick={checkBackendStatus}
            style={{
              marginTop: '20px',
              padding: '10px 20px',
              background: '#2196F3',
              border: 'none',
              borderRadius: '5px',
              color: 'white',
              cursor: 'pointer'
            }}
          >
            Retry Connection
          </button>
        </div>
      </AppContainer>
    )
  }

  // Teacher mode
  if (mode === 'teacher') {
    return (
      <AppContainer>
        <TeacherPortal 
          onSwitchToStudent={() => {
            setMode('student')
            // Refresh game state when switching back to student view
            fetchGameState()
          }} 
          onCourseApplied={() => {
            // Refresh game state after course applied successfully
            fetchGameState()
          }}
          onLogout={handleLogout}
        />
      </AppContainer>
    )
  }

  // Student mode
  return (
    <AppContainer>
      <AnimatePresence mode="wait">
        {currentView === 'report' ? (
          <ReportView 
            studentId="default_student"
            onBack={() => setCurrentView('map')}
          />
        ) : currentView === 'map' ? (
          <motion.div
            key="map"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            style={{ width: '100%', height: '100%', position: 'relative' }}
          >
            {/* Teacher mode switch button and Report button */}
            <div style={{
              position: 'fixed',
              top: '20px',
              right: '20px',
              zIndex: 1000,
              display: 'flex',
              gap: '10px'
            }}>
              <button
                onClick={() => setCurrentView('report')}
                style={{
                  padding: '12px 24px',
                  background: 'rgba(244, 143, 177, 0.9)',
                  border: '2px solid rgba(255, 255, 255, 0.3)',
                  borderRadius: '25px',
                  color: 'white',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  backdropFilter: 'blur(10px)',
                  boxShadow: '0 4px 15px rgba(0, 0, 0, 0.3)',
                  transition: 'all 0.3s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)'
                  e.currentTarget.style.boxShadow = '0 6px 20px rgba(244, 143, 177, 0.5)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)'
                  e.currentTarget.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.3)'
                }}
              >
                View Report
              </button>
              <button
                onClick={() => setMode('teacher')}
                style={{
                  padding: '12px 24px',
                  background: 'rgba(102, 126, 234, 0.9)',
                  border: '2px solid rgba(255, 255, 255, 0.3)',
                  borderRadius: '25px',
                  color: 'white',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  backdropFilter: 'blur(10px)',
                  boxShadow: '0 4px 15px rgba(0, 0, 0, 0.3)',
                  transition: 'all 0.3s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)'
                  e.currentTarget.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.5)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)'
                  e.currentTarget.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.3)'
                }}
              >
                Teacher Portal
              </button>
              <button
                onClick={handleLogout}
                style={{
                  padding: '12px 24px',
                  background: 'rgba(244, 67, 54, 0.9)',
                  border: '2px solid rgba(255, 255, 255, 0.3)',
                  borderRadius: '25px',
                  color: 'white',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  backdropFilter: 'blur(10px)',
                  boxShadow: '0 4px 15px rgba(0, 0, 0, 0.3)',
                  transition: 'all 0.3s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)'
                  e.currentTarget.style.boxShadow = '0 6px 20px rgba(244, 67, 54, 0.5)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)'
                  e.currentTarget.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.3)'
                }}
              >
                Return to Login
              </button>
            </div>
            <GameMap />
          </motion.div>
        ) : (
          <motion.div
            key="area"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
          >
            <AreaView
              areaId={selectedArea!}
              onComplete={() => handleAreaComplete(selectedArea!)}
              onBack={() => setCurrentView('map')}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </AppContainer>
  )
}

export default App
