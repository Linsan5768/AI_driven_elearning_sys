import { useState, useEffect } from 'react'
import styled from '@emotion/styled'
import { motion, AnimatePresence } from 'framer-motion'
import GameMap from './components/GameMap'
import AreaView from './components/AreaView'
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

const API_BASE_URL = 'http://127.0.0.1:8001/api'  // 更新为新的端口
const BACKEND_URL = 'http://127.0.0.1:8001'  // 更新为新的端口

function App() {
  const [gameState, setGameState] = useState<any>(null)
  const [currentView, setCurrentView] = useState('map')
  const [selectedArea, setSelectedArea] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [connectionStatus, setConnectionStatus] = useState<string>('Checking connection...')

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

  // 这个函数现在由GameMap组件内部处理
  // const handleAreaClick = (areaId: string) => {
  //   setSelectedArea(areaId)
  //   setCurrentView('area')
  // }

  if (error) {
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

  if (!gameState) {
    return (
      <AppContainer>
        <div style={{ textAlign: 'center' }}>
          <h2>Loading game...</h2>
          <div style={{ marginTop: '20px', color: '#666' }}>
            Status: {connectionStatus}
          </div>
        </div>
      </AppContainer>
    )
  }

  return (
    <AppContainer>
      <AnimatePresence mode="wait">
        {currentView === 'map' ? (
          <motion.div
            key="map"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
          >
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