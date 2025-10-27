import styled from '@emotion/styled'
import { motion, AnimatePresence } from 'framer-motion'
import React, { useState, useEffect, useRef } from 'react'
import AreaDialog from './AreaDialog'

const MapContainer = styled.div`
  width: 100vw;
  height: 100vh;
  position: relative;
  background: #1a1a1a;
  overflow: hidden;
  cursor: grab;
  &:active {
    cursor: grabbing;
  }
`

const MapContent = styled(motion.div)`
  position: absolute;
  width: 100%;
  height: 100%;
  transform-origin: center center;
  /* 移除等轴视角变换，使用平面2D */
  transform: none;
`

const AreaContainer = styled(motion.div)<{ 
  $x: number; 
  $y: number;
}>`
  position: absolute;
  left: ${props => props.$x}px;
  top: ${props => props.$y}px;
  width: 120px;
  height: 120px;
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
  opacity: ${props => props.$isAccessible ? 1 : 0.4};
  z-index: ${props => props.$isCurrent ? 2 : 1};
  transform-style: flat;
  transform: none;
  transition: all 0.3s ease;

  &::before, &::after {
    content: '';
    position: absolute;
    width: 100%;
    height: 100%;
    transition: all 0.3s ease;
  }

  /* Top face */
  &::before {
    top: 0;
    left: 0;
    background: ${props => props.$completed ? '#4CAF50' : '#2196F3'};
    border: 3px solid ${props => props.$completed ? '#388E3C' : '#1976D2'};
    border-radius: 50%;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    filter: ${props => props.$isCurrent ? 'drop-shadow(0 0 15px rgba(33, 150, 243, 0.4))' : 'none'};
  }

  /* Side face for 3D effect */
  &::after {
    top: 4px;
    left: 4px;
    background: ${props => props.$completed ? '#388E3C' : '#1976D2'};
    border-radius: 50%;
    filter: brightness(0.7);
    z-index: -1;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  }

  &:hover {
    &::before {
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(0,0,0,0.4);
    }
    &::after {
      transform: translateY(-1px);
    }
  }

  &:active {
    &::before {
      transform: translateY(0px);
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    &::after {
      transform: translateY(0px);
    }
  }
`

const AreaLabel = styled.span<{ $completed: boolean; $isCurrent: boolean }>`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #ffffff;
  text-shadow: 2px 2px 0 rgba(0,0,0,0.8);
  font-size: 16px;
  font-weight: bold;
  font-family: 'Arial', sans-serif;
  pointer-events: none;
  z-index: 2;
  letter-spacing: 0.5px;
`

const PathContainer = styled(motion.div)`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0; /* 路径在最底层 */

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
  width: 40px;
  height: 40px;
  transform-style: flat;
  z-index: 3;
  cursor: pointer;
  /* 移除transform，使用margin来居中 */
  margin-left: -20px;
  margin-top: -20px;

  &::before {
    content: '';
    position: absolute;
    width: 100%;
    height: 100%;
    background: #ff5722;
    border-radius: 50%;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    animation: characterPulse 2s ease-in-out infinite;
    transition: all 0.3s ease;
  }

  &::after {
    content: '';
    position: absolute;
    width: 100%;
    height: 100%;
    top: 4px;
    left: 4px;
    background: #d84315;
    border-radius: 50%;
    filter: brightness(0.7);
    z-index: -1;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    transition: all 0.3s ease;
  }

  &:hover {
    &::before {
      transform: scale(1.1);
      box-shadow: 0 6px 16px rgba(0,0,0,0.4);
    }
    &::after {
      transform: scale(1.05);
    }
  }

  &:active {
    &::before {
      transform: scale(0.95);
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    &::after {
      transform: scale(0.95);
    }
  }

  @keyframes characterPulse {
    0%, 100% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.05);
    }
  }
`

const ZoomControls = styled.div`
  position: fixed;
  right: 20px;
  bottom: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 1000;
`

const ZoomButton = styled.button`
  width: 50px;
  height: 50px;
  border: none;
  border-radius: 50%;
  background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
  color: white;
  font-size: 24px;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 
    0 4px 8px rgba(0,0,0,0.3),
    0 0 15px rgba(33, 150, 243, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%);
    transform: translateY(-2px);
    box-shadow: 
      0 6px 12px rgba(0,0,0,0.4),
      0 0 20px rgba(33, 150, 243, 0.5);
  }

  &:active {
    transform: translateY(0px);
    box-shadow: 
      0 2px 4px rgba(0,0,0,0.3),
      0 0 10px rgba(33, 150, 243, 0.3);
  }
`

interface Area {
  completed: boolean
  position: {
    x: number
    y: number
  }
  connections: string[]
}

const GameMap: React.FC = () => {
  const [areas, setAreas] = useState<Record<string, Area>>({})
  const [currentArea, setCurrentArea] = useState<string>('start')
  const [characterPosition, setCharacterPosition] = useState<{ x: number; y: number } | null>(null)
  const [isMoving, setIsMoving] = useState(false)
  const [mapOffset, setMapOffset] = useState({ x: 0, y: 0 })
  const [scale, setScale] = useState(1)
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [selectedAreaId, setSelectedAreaId] = useState<string>('')
  const mapRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // 获取游戏状态
    const fetchGameState = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8001/api/game-state')
        if (response.ok) {
          const data = await response.json()
          setAreas(data.areas)
          setCurrentArea(data.current_area)
        }
      } catch (error) {
        console.error('Failed to fetch game state:', error)
      }
    }

    fetchGameState()
  }, [])

  useEffect(() => {
    // 初始化地图位置，使当前区域在中心
    if (mapRef.current && areas[currentArea]) {
      const container = mapRef.current
      const currentPos = areas[currentArea].position
      const centerX = window.innerWidth / 2 - currentPos.x
      const centerY = window.innerHeight / 2 - currentPos.y
      setMapOffset({ x: centerX, y: centerY })
    }
  }, [currentArea, areas])

  const handleAreaClick = async (areaId: string) => {
    if (!isAccessible(areaId) || isMoving) return

    const targetArea = areas[areaId]
    if (!targetArea) return

    // 开始移动动画
    setIsMoving(true)
    const startPos = areas[currentArea]?.position || { x: 0, y: 0 }
    const endPos = targetArea.position

    // 计算路径点
    const duration = 2000 // 2秒
    const startTime = Date.now()

    const animate = () => {
      const elapsed = Date.now() - startTime
      const progress = Math.min(elapsed / duration, 1)

      if (progress < 1) {
        const pathPoint = calculatePathPoint(startPos, endPos, progress)
        setCharacterPosition(pathPoint)
        requestAnimationFrame(animate)
      } else {
        // 动画完成
        setCharacterPosition(null)
        setIsMoving(false)
        setCurrentArea(areaId)
        
        // 打开对话框
        setSelectedAreaId(areaId)
        setIsDialogOpen(true)
      }
    }

    animate()
  }

  const calculatePathPoint = (start: { x: number; y: number }, end: { x: number; y: number }, progress: number) => {
    const t = progress
    const curveX = start.x + (end.x - start.x) * t
    const curveHeight = Math.min(Math.sqrt(Math.pow(end.x - start.x, 2) + Math.pow(end.y - start.y, 2)) * 0.3, 80)
    const curveY = start.y + (end.y - start.y) * t + Math.sin(Math.PI * t) * curveHeight
    
    return {
      x: curveX,
      y: curveY
    }
  }

  const isAccessible = (areaId: string) => {
    if (areaId === currentArea) return true;
    return areas[currentArea]?.connections.includes(areaId);
  }

  const shouldHighlightPath = (fromId: string, toId: string) => {
    return fromId === currentArea || toId === currentArea
  }

  const isPathCompleted = (fromId: string, toId: string) => {
    return areas[fromId]?.completed || areas[toId]?.completed
  }

  const handleMouseDown = (e: React.MouseEvent) => {
    if (isDragging) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    const dx = e.clientX - dragStart.x;
    const dy = e.clientY - dragStart.y;
    setMapOffset(prev => ({ x: prev.x + dx, y: prev.y + dy }));
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY * 0.001;
    handleZoom(delta);
  };

  const handleZoom = (delta: number) => {
    setScale(prev => Math.max(0.5, Math.min(2, prev - delta)));
  };

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

  return (
    <MapContainer
      ref={mapRef}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onWheel={handleWheel}
    >
      <MapContent
        style={{
          transform: `translate(${mapOffset.x}px, ${mapOffset.y}px) scale(${scale})`
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
                
                // 计算路径的样式
                const strokeColor = isCompleted ? "#4CAF50" : (isHighlighted ? "#2196F3" : "#666")
                const strokeWidth = 4
                
                // 计算路径长度和角度
                const length = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2))
                const angle = Math.atan2(endY - startY, endX - startX) * 180 / Math.PI
                
                // 创建单个连贯的路径
                return (
                  <div
                    key={`${id}-${targetId}`}
                    style={{
                      position: 'absolute',
                      left: startX,
                      top: startY,
                      width: length,
                      height: strokeWidth,
                      backgroundColor: strokeColor,
                      transformOrigin: '0 50%',
                      transform: `rotate(${angle}deg)`,
                      pointerEvents: 'none',
                      zIndex: 0,
                      opacity: isHighlighted ? 1 : 0.6,
                      borderRadius: '2px',
                      boxShadow: isHighlighted 
                        ? `0 0 8px ${strokeColor}`
                        : `0 0 4px rgba(0,0,0,0.3)`,
                      // 添加虚线效果
                      backgroundImage: isHighlighted 
                        ? `repeating-linear-gradient(90deg, ${strokeColor} 0px, ${strokeColor} 8px, transparent 8px, transparent 16px)`
                        : `repeating-linear-gradient(90deg, ${strokeColor} 0px, ${strokeColor} 6px, transparent 6px, transparent 12px)`
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
              onClick={() => handleAreaClick(id)}
              whileHover={isAccessible(id) ? {
                scale: 1.1,
                transition: { duration: 0.2 }
              } : undefined}
              whileTap={isAccessible(id) ? {
                scale: 0.95,
                transition: { duration: 0.1 }
              } : undefined}
            >
              <AreaLabel $completed={area.completed} $isCurrent={id === currentArea}>{id}</AreaLabel>
            </AreaButton>
          </AreaContainer>
        ))}

        {/* Character */}
        <AnimatePresence>
          {characterPosition ? (
            <Character
              style={{
                left: `${characterPosition.x}px`,
                top: `${characterPosition.y}px`
              }}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0 }}
              transition={{
                scale: { duration: 0.2 }
              }}
            />
          ) : (
            // 默认显示角色在当前区域，确保中心点对齐
            <Character
              style={{
                left: `${areas[currentArea]?.position.x || 0}px`,
                top: `${areas[currentArea]?.position.y || 0}px`
              }}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{
                scale: { duration: 0.2 }
              }}
            />
          )}
        </AnimatePresence>
      </MapContent>

      {/* Zoom Controls */}
      <ZoomControls>
        <ZoomButton onClick={() => handleZoom(0.1)}>+</ZoomButton>
        <ZoomButton onClick={() => handleZoom(-0.1)}>-</ZoomButton>
      </ZoomControls>

      {/* Area Dialog */}
      <AreaDialog
        isOpen={isDialogOpen}
        onClose={() => setIsDialogOpen(false)}
        areaId={selectedAreaId}
        onComplete={handleDialogComplete}
      />
    </MapContainer>
  )
}

export default GameMap