import { useState, useEffect } from 'react'
import styled from '@emotion/styled'
import { motion } from 'framer-motion'

const AreaContainer = styled.div`
  width: 800px;
  height: 600px;
  background: #2a2a2a;
  border-radius: 20px;
  padding: 20px;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
`

const TaskContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-top: 40px;
`

const NumberButton = styled(motion.button)<{ $completed: boolean }>`
  width: 80px;
  height: 80px;
  border-radius: 10px;
  border: none;
  background: ${props => props.$completed ? '#4CAF50' : '#2196F3'};
  color: white;
  font-size: 24px;
  cursor: ${props => props.$completed ? 'default' : 'pointer'};
  opacity: ${props => props.$completed ? 0.7 : 1};
`

const BackButton = styled.button`
  position: absolute;
  top: 20px;
  left: 20px;
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  background: #666;
  color: white;
  cursor: pointer;

  &:hover {
    background: #777;
  }
`

const Instructions = styled.div`
  margin-top: 20px;
  font-size: 18px;
  color: #ddd;
`

interface AreaViewProps {
  areaId: string
  onComplete: () => void
  onBack: () => void
}

const AreaView = ({ areaId, onComplete, onBack }: AreaViewProps) => {
  const [numbers, setNumbers] = useState<number[]>([])
  const [currentNumber, setCurrentNumber] = useState(1)
  const [completed, setCompleted] = useState<number[]>([])

  useEffect(() => {
    // Generate random positions for numbers 1-3
    const shuffled = [1, 2, 3].sort(() => Math.random() - 0.5)
    setNumbers(shuffled)
  }, [])

  const handleNumberClick = (number: number) => {
    if (number === currentNumber && !completed.includes(number)) {
      setCompleted([...completed, number])
      setCurrentNumber(prev => prev + 1)

      if (number === 3) {
        // Task completed
        setTimeout(() => {
          onComplete()
        }, 500)
      }
    }
  }

  return (
    <AreaContainer>
      <BackButton onClick={onBack}>Back to Map</BackButton>
      <h2>Area: {areaId}</h2>
      <Instructions>
        Click the numbers in order: {currentNumber} → {currentNumber < 3 ? currentNumber + 1 : '✓'}
      </Instructions>
      <TaskContainer>
        {numbers.map(number => (
          <NumberButton
            key={number}
            onClick={() => handleNumberClick(number)}
            $completed={completed.includes(number)}
            whileHover={completed.includes(number) ? {} : { scale: 1.1 }}
            whileTap={completed.includes(number) ? {} : { scale: 0.95 }}
          >
            {number}
          </NumberButton>
        ))}
      </TaskContainer>
    </AreaContainer>
  )
}

export default AreaView


