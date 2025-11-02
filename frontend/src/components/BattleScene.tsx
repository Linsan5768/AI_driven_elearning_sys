import React, { useState, useEffect } from 'react';
import styled from '@emotion/styled';
import { keyframes } from '@emotion/react';
import axios from 'axios';

// ============= Animations =============
const damageShake = keyframes`
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-8px); }
  75% { transform: translateX(8px); }
`;

const pixelFade = keyframes`
  0% { opacity: 0; }
  100% { opacity: 1; }
`;

// ============= Styled Components =============
const BattleContainer = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: #2a2a2a;
  display: grid;
  grid-template-columns: 1fr 2fr 1fr;
  overflow: hidden;
  z-index: 9999;
  font-family: 'Courier New', monospace;
  image-rendering: pixelated;
`;

// Left/Right side - Characters
const BattleField = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 40px;
  background: #1a1a1a;
  border-right: 4px solid #444;
  position: relative;
  
  &:last-child {
    border-right: none;
    border-left: 4px solid #444;
  }
`;

const Character = styled.div<{ isShaking?: boolean }>`
  display: flex;
  flex-direction: column;
  align-items: center;
  animation: ${props => props.isShaking ? damageShake : 'none'} 0.4s;
`;

const CharacterSprite = styled.div<{ side: 'professor' | 'student'; isAttacking?: boolean; isHit?: boolean }>`
  width: 360px; /* 3x */
  height: 360px; /* 3x */
  background-image: url(${props => {
    if (props.side === 'professor') {
      if (props.isHit) {
        return '/character/A_old_wizard_professor_is_holding_a_magic_wand_with_a_magic_hat._taking-punch_south-west.gif'
      }
      return props.isAttacking 
        ? '/character/A_old_wizard_professor_is_holding_a_magic_wand_with_a_magic_hat._fireball_south-west.gif'
        : '/character/A_old_wizard_professor_is_holding_a_magic_wand_with_a_magic_hat._breathing-idle_south-west.gif';
    } else {
      if (props.isHit) {
        return '/character/A_young_wizard_student_is_holding_a_magic_wand._taking-punch_south-east.gif'
      }
      return props.isAttacking
        ? '/character/A_young_wizard_student_is_holding_a_magic_wand._fireball_south-east.gif'
        : '/character/A_young_wizard_student_is_holding_a_magic_wand._breathing-idle_south-east.gif';
    }
  }});
  background-size: contain;
  background-position: center;
  background-repeat: no-repeat;
  border: 4px solid #000;
  image-rendering: pixelated;
  position: relative;
`;

const CharacterLabel = styled.div`
  color: #fff;
  font-size: 14px;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 2px;
`;

const HPBarContainer = styled.div`
  width: 300px;
  margin-top: 12px;
`;

const HPBarOuter = styled.div`
  width: 100%;
  height: 24px;
  background: #000;
  border: 3px solid #fff;
  position: relative;
  image-rendering: pixelated;
`;

const HPBarInner = styled.div<{ percentage: number; color: string }>`
  height: 100%;
  width: ${props => props.percentage}%;
  background: ${props => props.color};
  transition: width 0.6s steps(10);
  image-rendering: pixelated;
`;

const HPText = styled.div`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #fff;
  font-size: 12px;
  font-weight: bold;
  text-shadow: 1px 1px 0 #000;
`;

// Center - Question & Options
const QuestionPanel = styled.div`
  display: flex;
  flex-direction: column;
  background: #2a2a2a;
  padding: 30px;
  overflow-y: auto;
`;

const WarningBanner = styled.div`
  background: rgba(255, 193, 7, 0.12);
  border: 2px solid rgba(255, 193, 7, 0.35);
  color: #ffe082;
  padding: 12px 16px;
  border-radius: 12px;
  margin-bottom: 20px;
  font-size: 12px;
  line-height: 1.6;
  letter-spacing: 0.04em;
`;
const HeaderBar = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #000;
  border: 3px solid #fff;
  margin-bottom: 20px;
`;

const RoundText = styled.div`
  color: #fff;
  font-size: 16px;
  text-transform: uppercase;
  letter-spacing: 2px;
`;

const CloseButton = styled.button`
  background: #d32f2f;
  color: #fff;
  border: 3px solid #000;
  padding: 8px 16px;
  cursor: pointer;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  text-transform: uppercase;
  
  &:hover {
    background: #f44336;
  }
  
  &:active {
    background: #c62828;
  }
`;

const QuestionBox = styled.div`
  background: #1a1a1a;
  border: 4px solid #fff;
  padding: 25px;
  margin-bottom: 20px;
  flex-shrink: 0;
`;

const QuestionTitle = styled.div`
  font-size: 14px;
  color: #aaa;
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 1px;
`;

const QuestionText = styled.div`
  font-size: 16px;
  color: #fff;
  line-height: 1.6;
`;

const OptionsGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  flex: 1;
`;

const OptionButton = styled.button<{ disabled?: boolean }>`
  background: #3a3a3a;
  border: 4px solid #666;
  padding: 20px;
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  font-family: 'Courier New', monospace;
  font-size: 14px;
  color: #fff;
  text-align: left;
  transition: all 0.1s;
  opacity: ${props => props.disabled ? 0.5 : 1};
  
  &:hover:not(:disabled) {
    background: #4a4a4a;
    border-color: #fff;
  }
  
  &:active:not(:disabled) {
    background: #555;
  }
`;

const OptionLabel = styled.div`
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 8px;
  color: #ffd700;
`;

// No longer using flash effects and result overlays

const BattleEndScreen = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: #000;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 10001;
  font-family: 'Courier New', monospace;
`;

const EndTitle = styled.div<{ isVictory: boolean }>`
  font-size: 48px;
  font-weight: bold;
  color: ${props => props.isVictory ? '#00ff00' : '#ff0000'};
  margin-bottom: 40px;
  text-transform: uppercase;
  letter-spacing: 5px;
`;

const StatsBox = styled.div`
  background: #1a1a1a;
  border: 4px solid #fff;
  padding: 40px 60px;
  color: #fff;
  margin-bottom: 40px;
`;

const StatRow = styled.div`
  font-size: 18px;
  margin: 12px 0;
  letter-spacing: 2px;
`;

const ContinueButton = styled.button`
  background: #4a90e2;
  color: #fff;
  border: 4px solid #000;
  padding: 15px 40px;
  font-size: 18px;
  font-weight: bold;
  cursor: pointer;
  font-family: 'Courier New', monospace;
  text-transform: uppercase;
  letter-spacing: 2px;
  
  &:hover {
    background: #5aa3f5;
  }
  
  &:active {
    background: #3a80d2;
  }
`;

const LoadingScreen = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: #000;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-family: 'Courier New', monospace;
  font-size: 24px;
  letter-spacing: 3px;
  z-index: 10002;
`;

const LoadingText = styled.div`
  margin-bottom: 24px;
  padding: 10px 18px;
  border: 4px solid #fff;
  background: #1a1a1a;
  text-transform: uppercase;
  letter-spacing: 4px;
  box-shadow: 0 0 0 4px #000, 0 0 0 8px #fff;
`;

const ProgressBarOuter = styled.div`
  width: 480px;
  height: 24px;
  background: repeating-linear-gradient(
    to right,
    #111 0 8px,
    #0c0c0c 8px 16px
  );
  border: 4px solid #fff;
  position: relative;
  box-shadow: inset 0 0 0 4px #000, 0 0 0 4px #000;
  image-rendering: pixelated;
`;

const ProgressBarFill = styled.div<{ percentage: number }>`
  height: 100%;
  width: ${props => props.percentage}%;
  background: repeating-linear-gradient(
    to right,
    #16a34a 0 8px,
    #22c55e 8px 16px
  );
  transition: width 0.2s steps(8);
  image-rendering: pixelated;
`;

const ProgressText = styled.div`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #fff;
  font-size: 14px;
  font-weight: bold;
  text-shadow: 1px 1px 0 #000;
`;

// Pixel head (use your duel image as the head of the progress)
const ProgressHead = styled.div<{ percentage: number }>`
  position: absolute;
  top: -18px; /* slightly above the bar */
  left: calc(${props => props.percentage}% - 20px);
  width: 40px;
  height: 40px;
  background-image: url('/ui/duel-head.png');
  background-size: contain;
  background-position: center;
  background-repeat: no-repeat;
  image-rendering: pixelated;
  pointer-events: none;
`;

const HintButton = styled.button<{ disabled?: boolean }>`
  background: #ffd700;
  color: #000;
  border: 3px solid #000;
  padding: 10px 20px;
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  font-family: 'Courier New', monospace;
  font-size: 14px;
  text-transform: uppercase;
  margin-top: 15px;
  opacity: ${props => props.disabled ? 0.5 : 1};
  
  &:hover:not(:disabled) {
    background: #ffed4e;
  }
  
  &:active:not(:disabled) {
    background: #e6c200;
  }
`;

const HintPanel = styled.div`
  background: #1a1a1a;
  border: 4px solid #ffd700;
  padding: 20px;
  margin-top: 15px;
  animation: ${pixelFade} 0.3s;
`;

const HintHeader = styled.div`
  font-size: 12px;
  color: #ffd700;
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 2px;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const HintText = styled.div`
  font-size: 14px;
  color: #fff;
  line-height: 1.6;
`;

const AIBadge = styled.span`
  background: #4a90e2;
  color: #fff;
  padding: 2px 6px;
  font-size: 10px;
  border: 2px solid #000;
  letter-spacing: 1px;
`;

// ============= Types =============
interface BattleSceneProps {
  areaId: string;
  courseData: any;
  learnedKnowledgePoints: Set<number>;
  modelType: string;
  onClose: () => void;
  onBattleComplete: (passed: boolean, score: number) => void;
}

interface Question {
  question: string;
  options: string[];
  correctAnswer: number;
  explanation: string;
  pointTitle: string;
  hint?: string;
}

// ============= Main Component =============
const BattleScene: React.FC<BattleSceneProps> = ({
  areaId,
  courseData,
  learnedKnowledgePoints,
  modelType,
  onClose,
  onBattleComplete
}) => {
  const [professorHP, setProfessorHP] = useState(100);
  const [studentHP, setStudentHP] = useState(100);
  const [currentRound, setCurrentRound] = useState(1);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [isAnswering, setIsAnswering] = useState(false);
  const [isStudentAttacking, setIsStudentAttacking] = useState(false);
  const [isProfessorAttacking, setIsProfessorAttacking] = useState(false);
  const [isStudentHit, setIsStudentHit] = useState(false);
  const [isProfessorHit, setIsProfessorHit] = useState(false);
  const [isProfessorShaking, setIsProfessorShaking] = useState(false);
  const [isStudentShaking, setIsStudentShaking] = useState(false);
  const [correctCount, setCorrectCount] = useState(0);
  const [battleEnded, setBattleEnded] = useState(false);
  const [isVictory, setIsVictory] = useState(false);
  const [isGeneratingQuestions, setIsGeneratingQuestions] = useState(true);
  const [showHint, setShowHint] = useState(false);
  const [isGeneratingHint, setIsGeneratingHint] = useState(false);
  const [currentHint, setCurrentHint] = useState<string>('');
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [systemWarning, setSystemWarning] = useState<string | null>(null);

  // Generate all questions on mount
  useEffect(() => {
    generateAllQuestions();
  }, []);

  // Start first question when questions are ready
  useEffect(() => {
    if (questions.length > 0 && !currentQuestion && !battleEnded) {
      setCurrentQuestion(questions[0]);
      setIsGeneratingQuestions(false);
    }
  }, [questions]);

  const generateAllQuestions = async () => {
    const learnedPoints = Array.from(learnedKnowledgePoints);
    const totalQuestions = learnedPoints.length;

    if (totalQuestions === 0) {
      alert('No learned knowledge points. Please learn some content first!');
      onClose();
      return;
    }

    const generatedQuestions: Question[] = [];

    let llmUnavailableWarned = false;

    for (let i = 0; i < totalQuestions; i++) {
      // Update progress
      const progress = Math.round(((i + 1) / totalQuestions) * 100);
      setLoadingProgress(progress);
      
      const pointNumber = learnedPoints[i];
      const knowledgePointTitle = courseData?.materials?.[pointNumber - 1]?.split('\n')[0] || `Knowledge Point ${pointNumber}`;
      const knowledgePointContent = courseData?.materials?.[pointNumber - 1] || '';

      try {
        console.log(`Generating question ${i + 1}/${totalQuestions} for: ${knowledgePointTitle}`);
        
        const questionPrompt = `You are a test question generator. Always output in English.

Knowledge Point: ${knowledgePointTitle}
Content: ${knowledgePointContent}

Generate ONE multiple-choice question:
- Question: max 30 words, tests understanding
- 4 options: max 20 words each
- Only 1 correct answer
- 3 plausible but wrong options
- Brief explanation: max 50 words

Output ONLY this JSON structure (you may use markdown code blocks):
{
  "question": "Your question text",
  "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
  "correctAnswer": 0,
  "explanation": "Brief explanation"
}

correctAnswer is the index (0-3) of the correct option.`;

        const response = await callLLMForQuestion(questionPrompt, modelType);
        console.log('📥 Raw LLM response:', response.substring(0, 200));
        
        let questionData;
        try {
          // Try to parse JSON - handle markdown code blocks
          let jsonString = response;
          
          // Remove markdown code blocks if present
          jsonString = jsonString.replace(/```json\s*/g, '').replace(/```\s*/g, '');
          
          // Extract JSON object
          const jsonMatch = jsonString.match(/\{[\s\S]*\}/);
          if (jsonMatch) {
            questionData = JSON.parse(jsonMatch[0]);
            console.log('✅ Successfully parsed question:', questionData.question.substring(0, 50));
          } else {
            throw new Error('No JSON found in response');
          }
        } catch (parseError) {
          console.warn('⚠️ Failed to parse LLM response, using fallback:', parseError);
          console.warn('Response was:', response.substring(0, 300));
          questionData = generateFallbackQuestion(pointNumber, knowledgePointTitle, knowledgePointContent);
        }

        generatedQuestions.push({
          ...questionData,
          pointTitle: knowledgePointTitle
        });
      } catch (error) {
        console.error('❌ Error generating question:', error);

        if (!llmUnavailableWarned && error instanceof Error && error.message === 'LOCAL_LLM_NOT_AVAILABLE') {
          llmUnavailableWarned = true;
          const ollamaUrl = import.meta.env.VITE_OLLAMA_URL || (import.meta.env.PROD ? '/ollama' : 'http://127.0.0.1:11434')
          setSystemWarning(`Local LLM service at ${ollamaUrl} is not reachable (HTTP 404). Generating fallback questions instead. Start the Ollama server or switch to a cloud model to restore dynamic questions.`);
        }

        generatedQuestions.push(generateFallbackQuestion(pointNumber, knowledgePointTitle, knowledgePointContent));
      }
    }

    setQuestions(generatedQuestions);
  };

  const callLLMForQuestion = async (prompt: string, model: string): Promise<string> => {
    console.log('🔮 Calling LLM for question generation, model:', model);
    
    // Handle different model types
    if (model === 'qwen2.5' || model === 'ollama-qwen2.5') {
      try {
        const ollamaUrl = import.meta.env.VITE_OLLAMA_URL || (import.meta.env.PROD ? '/ollama' : 'http://127.0.0.1:11434')
        const response = await axios.post(`${ollamaUrl}/api/generate`, {
          model: 'qwen2.5:7b',
          prompt: prompt,
          stream: false,
          options: {
            temperature: 0.7,
            num_predict: 500
          }
        });
        console.log('✅ Qwen2.5 response received');
        return response.data.response;
      } catch (error) {
        console.error('❌ Qwen2.5 error:', error);
        if (axios.isAxiosError(error)) {
          if (error.response?.status === 404) {
            throw new Error('LOCAL_LLM_NOT_AVAILABLE');
          }
        }
        throw error instanceof Error ? error : new Error('LLM request failed');
      }
    } else if (model === 'ollama-llama2') {
      try {
        const ollamaUrl = import.meta.env.VITE_OLLAMA_URL || (import.meta.env.PROD ? '/ollama' : 'http://127.0.0.1:11434')
        const response = await axios.post(`${ollamaUrl}/api/generate`, {
          model: 'llama2',
          prompt: prompt,
          stream: false,
          options: {
            temperature: 0.7,
            num_predict: 500
          }
        });
        console.log('✅ Llama2 response received');
        return response.data.response;
      } catch (error) {
        console.error('❌ Llama2 error:', error);
        if (axios.isAxiosError(error)) {
          if (error.response?.status === 404) {
            throw new Error('LOCAL_LLM_NOT_AVAILABLE');
          }
        }
        throw error instanceof Error ? error : new Error('LLM request failed');
      }
    } else if (model === 'claude-3.5') {
      try {
        const response = await axios.post(`${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api'}/claude-chat`, {
          prompt: prompt,
          stream: false
        });
        console.log('✅ Claude response received');
        return response.data.response;
      } catch (error) {
        console.error('❌ Claude error:', error);
        throw error;
      }
    }
    
    // Default to qwen2.5 if unsupported model
    console.warn('⚠️ Unsupported model, using qwen2.5:7b as fallback');
    const ollamaUrl = import.meta.env.VITE_OLLAMA_URL || (import.meta.env.PROD ? '/ollama' : 'http://127.0.0.1:11434')
    const response = await axios.post(`${ollamaUrl}/api/generate`, {
      model: 'qwen2.5:7b',
      prompt: prompt,
      stream: false,
      options: {
        temperature: 0.7,
        num_predict: 500
      }
    });
    return response.data.response;
  };

  const generateFallbackQuestion = (_pointNumber: number, pointTitle: string, pointContent: string): Question => {
    return {
      question: `Which of the following statements about "${pointTitle}" is correct?`,
      options: [
        pointContent.substring(0, 60) + '...',
        'This is an incorrect option A',
        'This is an incorrect option B',
        'This is an incorrect option C'
      ],
      correctAnswer: 0,
      explanation: `This question tests your understanding of ${pointTitle}. The correct answer summarizes the key concept.`,
      pointTitle: pointTitle
    };
  };

  // Save battle record to backend
  const saveBattleRecord = async (question: string, answer: number, isCorrect: boolean, knowledgePoint: string) => {
    try {
      await axios.post(`${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api'}/save-battle-record`, {
        student_id: 'default_student',
        area_id: areaId,
        question: question,
        answer: answer,
        is_correct: isCorrect,
        knowledge_point: knowledgePoint
      });
      console.log('📝 答题记录已保存');
    } catch (error) {
      console.error('❌ 保存答题记录失败:', error);
    }
  };

  const handleOptionSelect = async (optionIndex: number) => {
    if (isAnswering || !currentQuestion) return;

    setIsAnswering(true);
    const isCorrect = optionIndex === currentQuestion.correctAnswer;

    // 保存答题记录
    saveBattleRecord(
      currentQuestion.question,
      optionIndex,
      isCorrect,
      currentQuestion.pointTitle
    );

    // Calculate damage
    const damage = Math.floor(100 / questions.length);

    if (isCorrect) {
      // Student attacks professor
      // Step 1: Play student attack animation (fireball)
      setIsStudentAttacking(true);
      
      // Step 2: After attack animation completes, shake professor and reduce HP
      setTimeout(() => {
        setIsStudentAttacking(false);
        setIsProfessorHit(true);
        setIsProfessorShaking(true);
        setProfessorHP(prev => Math.max(0, prev - damage));
        
        // Step 3: Stop shaking
        setTimeout(() => {
          setIsProfessorShaking(false);
          setIsProfessorHit(false);
        }, 400);
      }, 800); // Duration of fireball animation
      
      setCorrectCount(prev => prev + 1);
    } else {
      // Professor attacks student
      // Step 1: Play professor attack animation (fireball)
      setIsProfessorAttacking(true);
      
      // Step 2: After attack animation completes, shake student and reduce HP
      setTimeout(() => {
        setIsProfessorAttacking(false);
        setIsStudentHit(true);
        setIsStudentShaking(true);
        setStudentHP(prev => Math.max(0, prev - damage));
        
        // Step 3: Stop shaking
        setTimeout(() => {
          setIsStudentShaking(false);
          setIsStudentHit(false);
        }, 400);
      }, 800); // Duration of fireball animation
    }

    // Wait for all animations to complete, then proceed
    setTimeout(() => {
      // Check battle end conditions
      const newProfessorHP = isCorrect ? Math.max(0, professorHP - damage) : professorHP;
      const newStudentHP = isCorrect ? studentHP : Math.max(0, studentHP - damage);

      if (newProfessorHP <= 0 || newStudentHP <= 0 || currentRound >= questions.length) {
        // Battle ended
        const passRate = (correctCount + (isCorrect ? 1 : 0)) / questions.length * 100;
        const victory = passRate >= 80;
        setIsVictory(victory);
        setBattleEnded(true);
        onBattleComplete(victory, passRate);
      } else {
        // Next round
        setCurrentRound(prev => prev + 1);
        setCurrentQuestion(questions[currentRound]); // currentRound will be updated
        setIsAnswering(false);
        // Reset hint for new question
        setShowHint(false);
        setCurrentHint('');
      }
    }, 1500); // Total animation time
  };

  const handleReturnToArea = () => {
    onClose();
  };

  const handleRequestHint = async () => {
    if (!currentQuestion || isGeneratingHint || showHint) return;

    setIsGeneratingHint(true);

    try {
      const hintPrompt = `You are an AI tutor providing a hint for a test question. Always answer in English.

Question: ${currentQuestion.question}
Knowledge Point: ${currentQuestion.pointTitle}

Provide a helpful hint that:
1. Does NOT give away the answer directly
2. For calculation questions: provide the relevant formula or method
3. For definition questions: provide the key concept or context
4. For conceptual questions: guide the thinking process
5. Keep it brief (max 50 words)

Output ONLY the hint text, no extra formatting or labels.`;

      console.log('💡 Generating hint for question...');
      const response = await callLLMForQuestion(hintPrompt, modelType);
      
      // Clean up the response
      let hint = response.trim();
      
      // Remove common prefixes
      hint = hint.replace(/^(Hint:|HINT:|💡|Tip:|TIP:)\s*/gi, '');
      
      setCurrentHint(hint);
      setShowHint(true);
      console.log('✅ Hint generated:', hint.substring(0, 50));
    } catch (error) {
      console.error('❌ Error generating hint:', error);
      setCurrentHint('Think about the key concepts related to this knowledge point.');
      setShowHint(true);
    } finally {
      setIsGeneratingHint(false);
    }
  };

  if (isGeneratingQuestions) {
    return (
      <LoadingScreen>
        <LoadingText>PREPARING QUESTIONS...</LoadingText>
        <ProgressBarOuter>
          <ProgressBarFill percentage={loadingProgress} />
          <ProgressHead percentage={loadingProgress} />
          <ProgressText>{loadingProgress}%</ProgressText>
        </ProgressBarOuter>
      </LoadingScreen>
    );
  }

  if (battleEnded) {
    const finalScore = Math.round((correctCount / questions.length) * 100);
    return (
      <BattleEndScreen>
        <EndTitle isVictory={isVictory}>
          {isVictory ? 'VICTORY' : 'DEFEAT'}
        </EndTitle>
        <StatsBox>
          <StatRow>TOTAL ROUNDS: {questions.length}</StatRow>
          <StatRow>CORRECT: {correctCount}</StatRow>
          <StatRow>WRONG: {questions.length - correctCount}</StatRow>
          <StatRow>ACCURACY: {finalScore}%</StatRow>
          <StatRow style={{ marginTop: '30px', color: isVictory ? '#00ff00' : '#ff6b6b' }}>
            {isVictory 
              ? 'NEXT AREA UNLOCKED' 
              : 'NEED 80% TO UNLOCK'}
          </StatRow>
        </StatsBox>
        <ContinueButton onClick={handleReturnToArea}>
          CONTINUE
        </ContinueButton>
      </BattleEndScreen>
    );
  }

  return (
    <BattleContainer>
      {/* Left side - Student (Magic Apprentice) */}
      <BattleField>
        <Character isShaking={isStudentShaking}>
          <CharacterLabel>STUDENT (YOU)</CharacterLabel>
          <CharacterSprite side="student" isAttacking={isStudentAttacking} isHit={isStudentHit} />
          <HPBarContainer>
            <HPBarOuter>
              <HPBarInner percentage={studentHP} color="#00ff00" />
              <HPText>HP: {studentHP}</HPText>
            </HPBarOuter>
          </HPBarContainer>
        </Character>
      </BattleField>

      {/* Center - Question panel */}
      <QuestionPanel>
        <HeaderBar>
          <RoundText>ROUND {currentRound} / {questions.length}</RoundText>
          <CloseButton onClick={onClose}>FORFEIT</CloseButton>
        </HeaderBar>

        {systemWarning && (
          <WarningBanner>{systemWarning}</WarningBanner>
        )}

        {currentQuestion && (
          <>
            <QuestionBox>
              <QuestionTitle>QUESTION {currentRound}</QuestionTitle>
              <QuestionText>{currentQuestion.question}</QuestionText>
              
              {/* Hint Button */}
              <HintButton 
                onClick={handleRequestHint}
                disabled={isGeneratingHint || isAnswering}
              >
                {isGeneratingHint ? 'GENERATING HINT...' : showHint ? 'HINT (SHOWN)' : 'GET HINT'}
              </HintButton>

              {/* Hint Panel */}
              {showHint && (
                <HintPanel>
                  <HintHeader>
                    HINT <AIBadge>AI GENERATED</AIBadge>
                  </HintHeader>
                  <HintText>{currentHint}</HintText>
                </HintPanel>
              )}
            </QuestionBox>

            <OptionsGrid>
              {currentQuestion.options.map((option, index) => (
                <OptionButton
                  key={index}
                  onClick={() => handleOptionSelect(index)}
                  disabled={isAnswering}
                >
                  <OptionLabel>[{String.fromCharCode(65 + index)}]</OptionLabel>
                  {option}
                </OptionButton>
              ))}
            </OptionsGrid>
          </>
        )}
      </QuestionPanel>

      {/* Right side - Professor */}
      <BattleField>
        <Character isShaking={isProfessorShaking}>
          <CharacterLabel>PROFESSOR (AI)</CharacterLabel>
          <CharacterSprite side="professor" isAttacking={isProfessorAttacking} isHit={isProfessorHit} />
          <HPBarContainer>
            <HPBarOuter>
              <HPBarInner percentage={professorHP} color="#ff0000" />
              <HPText>HP: {professorHP}</HPText>
            </HPBarOuter>
          </HPBarContainer>
        </Character>
      </BattleField>
    </BattleContainer>
  );
};

export default BattleScene;
