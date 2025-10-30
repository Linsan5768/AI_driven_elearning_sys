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
  width: 150px;
  height: 150px;
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
  opacity: ${props => props.$isAccessible ? 1 : 0.5};
  z-index: ${props => props.$isCurrent ? 2 : 1};
  transition: all 0.3s ease;
  filter: ${props => {
    if (props.$isCurrent) return 'drop-shadow(0 0 20px rgba(255, 215, 0, 0.8)) brightness(1.1)'
    if (props.$completed) return 'drop-shadow(0 4px 12px rgba(0,0,0,0.4)) brightness(0.9) saturate(0.7)'
    return 'drop-shadow(0 4px 12px rgba(0,0,0,0.4))'
  }};

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
      if (props.$completed) return 'drop-shadow(0 6px 16px rgba(0,0,0,0.5)) brightness(1) saturate(0.8)'
      return 'drop-shadow(0 6px 16px rgba(0,0,0,0.5)) brightness(1.1)'
    }};
  }

  &:active:not(:disabled) {
    transform: scale(0.98) translateY(-2px);
  }
`

const AreaLabel = styled.span<{ $completed: boolean; $isCurrent: boolean }>`
  position: absolute;
  bottom: -25px;
  left: 50%;
  transform: translateX(-50%);
  color: #ffffff;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
  font-size: 14px;
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
  top: -35px;
  left: 50%;
  transform: translateX(-50%);
  width: 120px;
  height: 18px;
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
  /* Align vertically with the progress bar center: top = -35 + 9 - (badgeH/2) = -36px */
  top: -36px;
  /* Place immediately to the right of the 120px progress bar: 60px + 6px gap + 10px (badge half) */
  left: calc(50% + 76px);
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

const PathSVG = styled.svg<{ $active: boolean }>`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: visible;

  path {
    fill: none;
    stroke: ${props => props.$active 
      ? 'url(#activeGradient)' 
      : 'url(#inactiveGradient)'
    };
    stroke-width: 8;
    stroke-dasharray: 20 12;
    stroke-linecap: round;
    filter: ${props => props.$active 
      ? 'drop-shadow(0 0 15px rgba(33, 150, 243, 0.4))' 
      : 'drop-shadow(0 0 8px rgba(0,0,0,0.3))'
    };
    opacity: ${props => props.$active ? 1 : 0.6};
    animation: ${props => props.$active ? 'pathFlow 2s linear infinite' : 'none'};
    transition: all 0.3s ease;
  }

  @keyframes pathFlow {
    0% { stroke-dashoffset: 0; }
    100% { stroke-dashoffset: 32; }
  }
`

const Character = styled(motion.div)`
  position: absolute;
  width: 96px;
  height: 96px;
  transform-style: flat;
  z-index: 3;
  cursor: pointer;
  margin-left: -48px;
  margin-top: -48px;
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
        const response = await fetch('http://127.0.0.1:8001/api/game-state')
        if (response.ok) {
          const data = await response.json()
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
    // If character is moving, show walking animation; otherwise show idle stance
    if (isWalking) {
      return `/character/full_body_wizard_walk_${direction}.gif`
    }
    return `/character/wizard_idle.gif`
  }

  const getCastleImage = (castleType: number): string => {
    // Return corresponding castle image path
    return `/castles/castle${castleType}.png`
  }

  const isAccessible = (areaId: string) => {
    // Current area is always accessible
    if (areaId === currentArea) return true;
    
    // Check connections of all completed areas
    for (const [id, area] of Object.entries(areas)) {
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
        const response = await fetch(`http://127.0.0.1:8001/api/complete-area/${selectedAreaId}`, {
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
    // 关闭对话框时也刷新游戏状态，以显示最新的学习进度
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
                
                // 获取起点和终点坐标
                const startX = area.position.x
                const startY = area.position.y
                const endX = targetArea.position.x
                const endY = targetArea.position.y
                
                // 计算路径长度和角度
                const length = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2))
                const angle = Math.atan2(endY - startY, endX - startX) * 180 / Math.PI
                
                // 使用图片作为路径（从区域中心点连接）
                return (
                  <div
                    key={`${id}-${targetId}`}
                    style={{
                      position: 'absolute',
                      left: startX,
                      top: startY - 30, // 向上偏移路径高度的一半，使路径中心线对齐区域中心
                      width: length,
                      height: 60, // 路径图片高度
                      transformOrigin: '0 50%',
                      transform: `rotate(${angle}deg)`, // 只旋转，不需要额外偏移
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
              {/* 学习进度和测试状态 - 只在非起点区域显示 */}
              {id !== 'start' && (
                <>
                  {/* 学习进度条 */}
                  <ProgressBarContainer>
                    <ProgressBarFill $progress={area.learningProgress || 0} />
                    <ProgressText>{Math.round(area.learningProgress || 0)}%</ProgressText>
                  </ProgressBarContainer>
                  
                  {/* 测试完成标记 */}
                  <TestCompleteBadge $completed={area.completed} />
                </>
              )}
              
              <img 
                src={getCastleImage(area.castle_type)} 
                alt={`Castle ${id}`}
                onError={(e) => {
                  // 如果图片加载失败，使用备用图片
                  e.currentTarget.src = '/castles/castle1.png'
                }}
              />
              <AreaLabel $completed={area.completed} $isCurrent={id === currentArea}>{id}</AreaLabel>
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
      />
    </MapContainer>
  )
}

export default GameMap