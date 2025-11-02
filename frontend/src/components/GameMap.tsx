import styled from '@emotion/styled'
import { motion } from 'framer-motion'
import React, { useState, useEffect, useRef } from 'react'
import AreaDialog from './AreaDialog'

const MapContainer = styled.div`
  width: 100vw;
  height: 100vh;
  position: relative;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  overflow-x: auto;
  overflow-y: hidden;
  cursor: default;
`

const MapContent = styled.div`
  position: relative;
  min-width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
`

const AreaContainer = styled(motion.div)<{ 
  $x: number; 
  $y: number;
}>`
  position: absolute;
  left: ${props => props.$x}px;
  top: ${props => props.$y}px;
  width: 170px; /* slightly larger */
  height: 170px; /* slightly larger */
  transform: translate(-50%, -50%);
`

const AreaButton = styled(motion.button)<{ 
  $completed: boolean;
  $isAccessible: boolean;
  $isCurrent: boolean;
}>`
  position: relative;
  width: 100%;
  height: 100%;
  padding: 0;
  border: none;
  background: none;
  cursor: ${props => props.$isAccessible ? 'pointer' : 'not-allowed'};
  /* Do not reduce opacity for locked areas */
  opacity: 1;
  z-index: ${props => props.$isCurrent ? 2 : 1};
  transition: all 0.3s ease;
  filter: ${props => {
    if (props.$isCurrent) return 'drop-shadow(0 0 20px rgba(255, 215, 0, 0.8)) brightness(1.1)'
    if (!props.$isAccessible) return 'drop-shadow(0 4px 12px rgba(0,0,0,0.4)) saturate(0.35) brightness(0.95)'
    if (props.$completed) return 'drop-shadow(0 4px 12px rgba(0,0,0,0.4)) brightness(0.95) saturate(0.8)'
    return 'drop-shadow(0 4px 12px rgba(0,0,0,0.4))'
  }};

  /* Locked mask overlay */
  &::after {
    content: '';
    display: ${props => props.$isAccessible ? 'none' : 'block'};
    position: absolute;
    inset: 0;
    background: radial-gradient(rgba(0,0,0,0.0), rgba(0,0,0,0.0)) center/100% 100% no-repeat;
    pointer-events: none;
  }

  /* Lock badge */
  &::before {
    content: '';
    display: ${props => props.$isAccessible ? 'none' : 'block'};
    position: absolute;
    top: 8px;
    right: 8px;
    width: 28px;
    height: 28px;
    background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23ffffff"><path d="M12 1a5 5 0 00-5 5v3H6a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2v-8a2 2 0 00-2-2h-1V6a5 5 0 00-5-5zm-3 8V6a3 3 0 016 0v3H9z"/></svg>') center/cover no-repeat;
    filter: drop-shadow(0 1px 2px rgba(0,0,0,0.6));
    opacity: 0.9;
    pointer-events: none;
  }

  img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    image-rendering: pixelated;
    image-rendering: -moz-crisp-edges;
    image-rendering: crisp-edges;
  }

  &:hover:not(:disabled) {
    transform: scale(1.05) translateY(-5px);
    filter: ${props => {
      if (props.$isCurrent) return 'drop-shadow(0 0 25px rgba(255, 215, 0, 1)) brightness(1.2)'
      if (!props.$isAccessible) return 'drop-shadow(0 6px 16px rgba(0,0,0,0.5)) saturate(0.35) brightness(0.98)'
      if (props.$completed) return 'drop-shadow(0 6px 16px rgba(0,0,0,0.5)) brightness(1) saturate(0.9)'
      return 'drop-shadow(0 6px 16px rgba(0,0,0,0.5)) brightness(1.1)'
    }};
  }

  &:active:not(:disabled) {
    transform: scale(0.98) translateY(-2px);
  }
`

const AreaLabel = styled.span<{ $completed: boolean; $isCurrent: boolean }>`
  position: absolute;
  bottom: -28px;
  left: 50%;
  transform: translateX(-50%);
  color: #ffffff;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
  font-size: 15px;
  font-weight: bold;
  font-family: 'Arial', sans-serif;
  pointer-events: none;
  z-index: 2;
  letter-spacing: 0.5px;
  background: rgba(0, 0, 0, 0.5);
  padding: 4px 12px;
  border-radius: 12px;
  white-space: nowrap;
`

const ProgressBarContainer = styled.div`
  position: absolute;
  top: -40px;
  left: 50%;
  transform: translateX(-50%);
  width: 136px;
  height: 20px;
  background: rgba(0, 0, 0, 0.8);
  border-radius: 9px;
  border: 2px solid rgba(255, 255, 255, 0.4);
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.6);
  pointer-events: none;
`

const ProgressBarFill = styled.div<{ $progress: number }>`
  width: ${props => props.$progress}%;
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #8BC34A);
  transition: width 0.3s ease;
  position: relative;
  
  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(90deg, 
      transparent, 
      rgba(255, 255, 255, 0.4), 
      transparent
    );
    animation: shimmer 2s infinite;
  }
  
  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }
`

const ProgressText = styled.div`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-size: 10px;
  font-weight: bold;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 1);
  z-index: 1;
  pointer-events: none;
`

const TestCompleteBadge = styled.div<{ $completed: boolean }>`
  position: absolute;
  /* Align vertically with the progress bar (20px height): top = -40 + 10 - 10 = -40px */
  top: -40px;
  /* Place immediately to the right of the 136px bar: 68px + 10px gap */
  left: calc(50% + 85px);
  transform: translateX(-50%);
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: ${props => props.$completed 
    ? 'linear-gradient(135deg, #4CAF50, #66BB6A)' 
    : 'rgba(60, 60, 60, 0.8)'};
  border: 2px solid ${props => props.$completed ? '#ffffff' : 'rgba(120, 120, 120, 0.8)'};
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.6);
  pointer-events: none;
  opacity: ${props => props.$completed ? 1 : 0.6};
  transition: all 0.3s ease;
  
  &::before {
    content: '${props => props.$completed ? '✓' : '○'}';
    color: ${props => props.$completed ? '#ffffff' : 'rgba(180, 180, 180, 0.8)'};
    font-weight: bold;
    font-size: ${props => props.$completed ? '14px' : '16px'};
  }
  
  ${props => props.$completed && `
    animation: pulse 2s infinite;
  `}
  
  @keyframes pulse {
    0%, 100% { transform: translateX(-50%) scale(1); box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5); }
    50% { transform: translateX(-50%) scale(1.04); box-shadow: 0 2px 12px rgba(76, 175, 80, 0.7); }
  }
`

const PathContainer = styled(motion.div)`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0; /* Paths at the bottom layer */

  @keyframes pathGlow {
    0% { 
      box-shadow: 0 0 15px currentColor, 0 0 30px currentColor40, inset 0 0 10px currentColor20;
      filter: brightness(1.2);
    }
    100% { 
      box-shadow: 0 0 25px currentColor, 0 0 50px currentColor60, inset 0 0 15px currentColor30;
      filter: brightness(1.5);
    }
  }

  @keyframes pathFlow {
    0% { 
      background-position: 0% 50%;
      opacity: 0.8;
    }
    50% { 
      background-position: 100% 50%;
      opacity: 1;
    }
    100% { 
      background-position: 0% 50%;
      opacity: 0.8;
    }
  }
`

// PathSVG component removed - no longer used

const Character = styled(motion.div)`
  position: absolute;
  width: 112px;
  height: 112px;
  transform-style: flat;
  z-index: 3;
  cursor: pointer;
  margin-left: -56px;
  margin-top: -56px;
  filter: drop-shadow(0 6px 12px rgba(0,0,0,0.5));
  transition: all 0.3s ease;

  img {
    width: 100%;
    height: 100%;
    image-rendering: pixelated;
    image-rendering: -moz-crisp-edges;
    image-rendering: crisp-edges;
  }

  &:hover {
    transform: scale(1.1);
    filter: drop-shadow(0 8px 16px rgba(0,0,0,0.6));
  }

  &:active {
    transform: scale(0.95);
    filter: drop-shadow(0 4px 8px rgba(0,0,0,0.5));
  }
`


interface Area {
  completed: boolean
  position: {
    x: number
    y: number
  }
  connections: string[]
  castle_type: number
  learningProgress?: number
  type?: string  // 'final_destination' for final areas
  parent_subject?: string
  required_areas?: string[]
  name?: string
}

const GameMap: React.FC = () => {
  const [areas, setAreas] = useState<Record<string, Area>>({})
  const [currentArea, setCurrentArea] = useState<string>('start')
  const [characterDirection, setCharacterDirection] = useState<string>('east')
  const [isMoving, setIsMoving] = useState(false)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [selectedAreaId, setSelectedAreaId] = useState<string>('')
  const [mapOffset, setMapOffset] = useState({ x: 0, y: 0 })
  const [movingPosition, setMovingPosition] = useState<{ x: number; y: number } | null>(null)
  const mapRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Fetch game state
    const fetchGameState = async () => {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api'}/game-state`)
        if (response.ok) {
          const data = await response.json()
          console.log('🗺️ Game state loaded:', {
            totalAreas: Object.keys(data.areas).length,
            areaIds: Object.keys(data.areas),
            finalDestinations: Object.entries(data.areas).filter(([_, area]: [string, any]) => area.type === 'final_destination').map(([id, _]: [string, any]) => id)
          })
          setAreas(data.areas)
          setCurrentArea(data.current_area)
          
          // Initialize map offset, center the starting area on screen
          if (data.areas[data.current_area]) {
            const currentPos = data.areas[data.current_area].position
            const centerX = window.innerWidth / 2
            const centerY = window.innerHeight / 2
            setMapOffset({
              x: centerX - currentPos.x,
              y: centerY - currentPos.y
            })
          }
        }
      } catch (error) {
        console.error('Failed to fetch game state:', error)
      }
    }

    fetchGameState()
  }, [])

  useEffect(() => {
    // Calculate map offset to center current area on screen
    if (areas[currentArea]) {
      const currentPos = areas[currentArea].position
      const centerX = window.innerWidth / 2
      const centerY = window.innerHeight / 2
      
      setMapOffset({
        x: centerX - currentPos.x,
        y: centerY - currentPos.y
      })
    }
  }, [currentArea, areas])

  const handleAreaClick = async (areaId: string) => {
    if (!isAccessible(areaId) || isMoving) return

    const targetArea = areas[areaId]
    if (!targetArea) return

    // If clicking the current area, open dialog immediately with no movement
    if (areaId === currentArea) {
      setSelectedAreaId(areaId)
      setIsDialogOpen(true)
      return
    }

    // Start movement animation
    setIsMoving(true)
    const startPos = areas[currentArea]?.position || { x: 0, y: 0 }
    const endPos = targetArea.position

    // Calculate and set character direction
    const direction = calculateDirection(startPos, endPos)
    setCharacterDirection(direction)

    // Calculate screen center
    const centerX = window.innerWidth / 2
    const centerY = window.innerHeight / 2

    // Calculate start and end map offsets
    const startOffset = { x: centerX - startPos.x, y: centerY - startPos.y }
    const endOffset = { x: centerX - endPos.x, y: centerY - endPos.y }

    // Calculate path points
    const duration = 2000 // 2 seconds
    const startTime = Date.now()

    const animate = () => {
      const elapsed = Date.now() - startTime
      const progress = Math.min(elapsed / duration, 1)

      if (progress < 1) {
        // Move map instead of character
        const currentOffset = {
          x: startOffset.x + (endOffset.x - startOffset.x) * progress,
          y: startOffset.y + (endOffset.y - startOffset.y) * progress
        }
        setMapOffset(currentOffset)
        // Move character sprite along the path
        const currentPos = {
          x: startPos.x + (endPos.x - startPos.x) * progress,
          y: startPos.y + (endPos.y - startPos.y) * progress
        }
        setMovingPosition(currentPos)
        requestAnimationFrame(animate)
      } else {
        // Animation complete
        setIsMoving(false)
        setCurrentArea(areaId)
        setMapOffset(endOffset)
        setMovingPosition(null)
        
        // Open dialog
        setSelectedAreaId(areaId)
        setIsDialogOpen(true)
      }
    }

    animate()
  }

  const calculateDirection = (start: { x: number; y: number }, end: { x: number; y: number }): string => {
    const dx = end.x - start.x
    const dy = end.y - start.y
    const angle = Math.atan2(dy, dx) * 180 / Math.PI
    
    // 8-direction determination (starting from east, clockwise)
    // East: -22.5 to 22.5
    // South-East: 22.5 to 67.5
    // South: 67.5 to 112.5
    // South-West: 112.5 to 157.5
    // West: 157.5 to -157.5 (or -180 to -157.5)
    // North-West: -157.5 to -112.5
    // North: -112.5 to -67.5
    // North-East: -67.5 to -22.5
    
    if (angle >= -22.5 && angle < 22.5) return 'east'
    if (angle >= 22.5 && angle < 67.5) return 'south-east'
    if (angle >= 67.5 && angle < 112.5) return 'south'
    if (angle >= 112.5 && angle < 157.5) return 'south-west'
    if (angle >= 157.5 || angle < -157.5) return 'west'
    if (angle >= -157.5 && angle < -112.5) return 'north-west'
    if (angle >= -112.5 && angle < -67.5) return 'north'
    if (angle >= -67.5 && angle < -22.5) return 'north-east'
    
    return 'south' // Default direction
  }

  const getCharacterSprite = (direction: string, isWalking: boolean = false): string => {
    // Updated student sprites: use new idle + walking GIFs
    if (isWalking) {
      // Map 8 directions to 4 available walking directions
      const mapToCardinal = (dir: string) => {
        if (dir.includes('east')) return 'east'
        if (dir.includes('west')) return 'west'
        if (dir.includes('north')) return 'north'
        return 'south'
      }
      const d = mapToCardinal(direction)
      return `/character/A_young_wizard_student_is_holding_a_magic_wand._walking-8-frames_${d}.gif`
    }
    // Idle: always use the classic default idle sprite
    return `/character/wizard_idle.gif`
  }

  const getCastleImage = (castleType: number, areaType?: string, areaId?: string): string => {
    // Special image for start area
    if (areaId === 'start') {
      return `/castles/start.png`
    }
    // Special image for final destination areas
    if (areaType === 'final_destination') {
      return `/castles/final.png`
    }
    // Return corresponding castle image path for regular areas
    return `/castles/castle${castleType}.png`
  }

  const isAccessible = (areaId: string) => {
    // Current area is always accessible
    if (areaId === currentArea) return true;
    
    // Special logic for final destination areas
    const area = areas[areaId]
    if (area?.type === 'final_destination') {
      // Check if all required areas (chapters) are completed
      const requiredAreas = area.required_areas || []
      const allCompleted = requiredAreas.every(reqId => areas[reqId]?.completed === true)
      if (!allCompleted) return false
    }
    
    // Check connections of all completed areas
    for (const [, area] of Object.entries(areas)) {
      if (area.completed && area.connections?.includes(areaId)) {
        return true;
      }
    }
    
    return false;
  }

  const shouldHighlightPath = (fromId: string, toId: string) => {
    return fromId === currentArea || toId === currentArea
  }

  const isPathCompleted = (fromId: string, toId: string) => {
    return areas[fromId]?.completed || areas[toId]?.completed
  }

  const refreshGameState = async () => {
    // Refresh game state, get latest learning progress
    try {
      const response = await fetch('http://127.0.0.1:8001/api/game-state')
      if (response.ok) {
        const data = await response.json()
        // Only refresh areas/progress; keep currentArea as-is to avoid jumping back
        setAreas(data.areas)
        console.log('🔄 Game state refreshed')
      }
    } catch (error) {
      console.error('Failed to refresh game state:', error)
    }
  }

  const handleDialogComplete = async () => {
    if (selectedAreaId) {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api'}/complete-area/${selectedAreaId}`, {
          method: 'POST',
        })
        
        if (response.ok) {
          const result = await response.json()
          setAreas(result.game_state.areas)
          setCurrentArea(result.game_state.current_area)
        }
      } catch (error) {
        console.error('Failed to complete area:', error)
      }
    }
    
    setIsDialogOpen(false)
    setSelectedAreaId('')
  }

  const handleDialogClose = async () => {
    // Refresh game state when closing the dialog to show the latest learning progress
    await refreshGameState()
    setIsDialogOpen(false)
    setSelectedAreaId('')
  }

  return (
    <MapContainer ref={mapRef}>
      <MapContent
        style={{
          transform: `translate(${mapOffset.x}px, ${mapOffset.y}px)`,
          transition: isMoving ? 'none' : 'transform 0.3s ease-out'
        }}
      >
        {/* SVG Definitions for Gradients */}
        <svg style={{ position: 'absolute', width: 0, height: 0 }}>
          <defs>
            <linearGradient id="activeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#2196F3" stopOpacity="1" />
              <stop offset="100%" stopColor="#64B5F6" stopOpacity="1" />
            </linearGradient>
            <linearGradient id="inactiveGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#666" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#999" stopOpacity="0.8" />
            </linearGradient>
            <linearGradient id="completedGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#4CAF50" stopOpacity="1" />
              <stop offset="100%" stopColor="#66BB6A" stopOpacity="1" />
            </linearGradient>
          </defs>
        </svg>

        {/* Paths */}
        <PathContainer>
          {Object.entries(areas).map(([id, area]) => {
            if (area.connections && area.connections.length > 0) {
              return area.connections.map((targetId) => {
                const targetArea = areas[targetId]
                if (!targetArea) return null
                
                const isHighlighted = shouldHighlightPath(id, targetId)
                const isCompleted = isPathCompleted(id, targetId)
                
                // Get start and end coordinates
                const startX = area.position.x
                const startY = area.position.y
                const endX = targetArea.position.x
                const endY = targetArea.position.y
                
                // Calculate path length and angle
                const length = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2))
                const angle = Math.atan2(endY - startY, endX - startX) * 180 / Math.PI
                
                // Use an image as the path (connect from area center)
                return (
                  <div
                    key={`${id}-${targetId}`}
                    style={{
                      position: 'absolute',
                      left: startX,
                      top: startY - 30, // Shift up by half the path height to align the center line
                      width: length,
                      height: 60, // Path image height
                      transformOrigin: '0 50%',
                      transform: `rotate(${angle}deg)`, // Only rotate, no extra offset
                      pointerEvents: 'none',
                      zIndex: 0,
                      opacity: isCompleted ? 0.7 : (isHighlighted ? 1 : 0.8),
                      backgroundImage: 'url(/roads/path.png)',
                      backgroundSize: 'auto 100%',
                      backgroundRepeat: 'repeat-x',
                      imageRendering: 'pixelated',
                      filter: isCompleted 
                        ? 'brightness(0.7) saturate(0.5)' 
                        : (isHighlighted 
                          ? 'brightness(1.1) drop-shadow(0 0 10px rgba(255, 215, 0, 0.5))'
                          : 'none')
                    }}
                  />
                )
              });
            }
            return null;
          })}
        </PathContainer>

        {/* Areas */}
        {Object.entries(areas).map(([id, area]) => (
          <AreaContainer
            key={id}
            $x={area.position.x}
            $y={area.position.y}
          >
            <AreaButton
              $completed={area.completed}
              $isAccessible={isAccessible(id)}
              $isCurrent={id === currentArea}
              onClick={() => {
                if (id === 'start') return
                if (!isAccessible(id)) {
                  window.alert('Complete the previous test to unlock this area')
                  return
                }
                handleAreaClick(id)
              }}
              style={{ cursor: id === 'start' ? 'default' : undefined }}
              title={(!isAccessible(id) && id !== 'start') ? 'Complete the previous test to unlock this area' : undefined}
              whileHover={isAccessible(id) && id !== 'start' ? {
                scale: 1.1,
                transition: { duration: 0.2 }
              } : undefined}
              whileTap={isAccessible(id) && id !== 'start' ? {
                scale: 0.95,
                transition: { duration: 0.1 }
              } : undefined}
            >
              {/* Learning progress and test status - only show for non-start and non-final areas */}
              {id !== 'start' && area.type !== 'final_destination' && (
                <>
                  {/* Learning progress bar */}
                  <ProgressBarContainer>
                    <ProgressBarFill $progress={area.learningProgress || 0} />
                    <ProgressText>{Math.round(area.learningProgress || 0)}%</ProgressText>
                  </ProgressBarContainer>
                  
                  {/* Test completion badge */}
                  <TestCompleteBadge $completed={area.completed} />
                </>
              )}
              
              <img 
                src={getCastleImage(area.castle_type, area.type, id)} 
                alt={id === 'start' ? 'Start' : area.type === 'final_destination' ? 'Final Destination' : `Castle ${id}`}
                onError={(e) => {
                  // If image fails to load, use a fallback image based on area type
                  if (id === 'start') {
                    e.currentTarget.src = '/castles/castle1.png'
                  } else if (area.type === 'final_destination') {
                    e.currentTarget.src = '/castles/castle1.png'
                  } else {
                    e.currentTarget.src = '/castles/castle1.png'
                  }
                }}
              />
              <AreaLabel $completed={area.completed} $isCurrent={id === currentArea}>
                {area.type === 'final_destination' ? '🏆 Final' : id}
              </AreaLabel>
            </AreaButton>
          </AreaContainer>
        ))}

        {/* Character - Anchored to current area position */}
        {(areas[currentArea] || movingPosition) && (
          <div
            style={{
              position: 'absolute',
              left: (movingPosition?.x ?? areas[currentArea].position.x),
              top: (movingPosition?.y ?? areas[currentArea].position.y),
              transform: 'translate(-50%, -50%)',
              zIndex: 1000,
              pointerEvents: 'none'
            }}
          >
            <Character>
              <img
                src={getCharacterSprite(characterDirection, isMoving)}
                alt={isMoving ? 'Character walking' : 'Character idle'}
              />
            </Character>
          </div>
        )}

      </MapContent>

      {/* Area Dialog */}
      <AreaDialog
        isOpen={isDialogOpen}
        onClose={handleDialogClose}
        areaId={selectedAreaId}
        onComplete={handleDialogComplete}
        onExitToLogin={() => {
          // Trigger exit to login by reloading page
          window.location.reload()
        }}
      />
    </MapContainer>
  )
}

export default GameMap