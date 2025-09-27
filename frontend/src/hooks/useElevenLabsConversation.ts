import { useCallback, useRef, useState, useEffect } from 'react'
import { useConversation } from '@11labs/react'
import { sendConversationToBackend } from '@/lib/conversationLogger'

interface ConversationState {
  isConnected: boolean
  isSpeaking: boolean
  isListening: boolean
  bassLevel: number
  midLevel: number
  trebleLevel: number
  overallLevel: number
  error: string | null
  conversationId: string | null
}

interface ConversationHook extends ConversationState {
  startConversation: () => Promise<void>
  endConversation: () => Promise<void>
  setVolume: (volume: number) => Promise<void>
}

export function useElevenLabsConversation(): ConversationHook {
  const [error, setError] = useState<string | null>(null)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [audioLevels, setAudioLevels] = useState({
    bassLevel: 0,
    midLevel: 0,
    trebleLevel: 0,
    overallLevel: 0
  })

  // Audio analysis setup
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const dataArrayRef = useRef<Uint8Array | null>(null)
  const animationFrameRef = useRef<number | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  // AI speech simulation
  const aiSpeechAnimationRef = useRef<number | null>(null)
  const aiStartTimeRef = useRef<number>(0)

  // Conversation tracking
  const currentUserMessageRef = useRef<string>('')
  const currentAgentResponseRef = useRef<string>('')

  const conversation = useConversation({
    onConnect: () => {
      console.log('Connected to ElevenLabs conversation')
      setError(null)
    },
    onDisconnect: () => {
      console.log('Disconnected from ElevenLabs conversation')
      stopAudioAnalysis()
      stopAISpeechSimulation()
    },
    onError: (error) => {
      console.error('ElevenLabs conversation error:', error)
      setError(typeof error === 'string' ? error : 'Connection error')
    },
    onMessage: (message) => {
      console.log('Conversation message:', message)
      
      if (message.source === 'user' && message.message) {
        currentUserMessageRef.current = message.message
      } else if (message.source === 'ai' && message.message) {
        currentAgentResponseRef.current = message.message
        
        // Send complete conversation to backend
        if (currentUserMessageRef.current && currentAgentResponseRef.current) {
          sendConversationToBackend({
            userMessage: currentUserMessageRef.current,
            agentResponse: currentAgentResponseRef.current,
            timestamp: new Date().toISOString(),
            conversationType: 'voice',
            conversationId
          })
          
          // Reset for next conversation
          currentUserMessageRef.current = ''
          currentAgentResponseRef.current = ''
        }
      }
    }
  })

  // Audio analysis functions
  const analyzeFrequencies = useCallback((frequencies: Uint8Array) => {
    // Normalize frequency data (0-255 to 0-1)
    const normalizedFreqs = Array.from(frequencies).map(f => f / 255)
    
    // Define frequency ranges
    const bassRange = normalizedFreqs.slice(0, Math.floor(frequencies.length * 0.1))
    const midRange = normalizedFreqs.slice(
      Math.floor(frequencies.length * 0.1), 
      Math.floor(frequencies.length * 0.4)
    )
    const trebleRange = normalizedFreqs.slice(Math.floor(frequencies.length * 0.4))
    
    // Calculate averages with smoothing
    const bass = bassRange.reduce((sum, val) => sum + val, 0) / bassRange.length
    const mid = midRange.reduce((sum, val) => sum + val, 0) / midRange.length  
    const treble = trebleRange.reduce((sum, val) => sum + val, 0) / trebleRange.length
    const overall = normalizedFreqs.reduce((sum, val) => sum + val, 0) / normalizedFreqs.length
    
    // Apply smoothing
    setAudioLevels(prev => ({
      bassLevel: prev.bassLevel * 0.7 + bass * 0.3,
      midLevel: prev.midLevel * 0.7 + mid * 0.3,
      trebleLevel: prev.trebleLevel * 0.7 + treble * 0.3,
      overallLevel: prev.overallLevel * 0.7 + overall * 0.3
    }))
  }, [])

  // Simulate AI speech audio levels with proper smoothing
  const simulateAISpeech = useCallback(() => {
    const now = Date.now()
    const elapsed = (now - aiStartTimeRef.current) / 1000
    
    // Create much gentler, smoother waves with slower frequency changes
    const bassWave = (Math.sin(elapsed * 0.8) + 1) / 2 * 0.3 + 0.1  // Even gentler range
    const midWave = (Math.sin(elapsed * 1.2 + 1) + 1) / 2 * 0.25 + 0.1
    const trebleWave = (Math.sin(elapsed * 1.6 + 2) + 1) / 2 * 0.15 + 0.05
    const overallWave = (bassWave + midWave + trebleWave) / 3
    
    // Apply heavy smoothing similar to real audio analysis
    setAudioLevels(prev => ({
      bassLevel: prev.bassLevel * 0.85 + bassWave * 0.15,  // Much heavier smoothing
      midLevel: prev.midLevel * 0.85 + midWave * 0.15,
      trebleLevel: prev.trebleLevel * 0.85 + trebleWave * 0.15,
      overallLevel: prev.overallLevel * 0.85 + overallWave * 0.15
    }))
    
    aiSpeechAnimationRef.current = requestAnimationFrame(simulateAISpeech)
  }, [])

  const startAISpeechSimulation = useCallback(() => {
    aiStartTimeRef.current = Date.now()
    simulateAISpeech()
  }, [simulateAISpeech])

  const stopAISpeechSimulation = useCallback(() => {
    if (aiSpeechAnimationRef.current) {
      cancelAnimationFrame(aiSpeechAnimationRef.current)
      aiSpeechAnimationRef.current = null
    }
  }, [])

  const updateAudioData = useCallback(() => {
    // Always analyze microphone input 
    if (analyserRef.current && dataArrayRef.current) {
      analyserRef.current.getByteFrequencyData(dataArrayRef.current)
      
      // Check if there's actual user audio input
      const hasUserInput = Array.from(dataArrayRef.current).some(level => level > 10) // threshold for activity
      
      // Only use microphone data if there's actual user input OR AI is not speaking
      if (hasUserInput || !conversation.isSpeaking) {
        analyzeFrequencies(dataArrayRef.current)
      }
    }
    animationFrameRef.current = requestAnimationFrame(updateAudioData)
  }, [analyzeFrequencies, conversation.isSpeaking])

  const startAudioAnalysis = useCallback(async () => {
    try {
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      })
      streamRef.current = stream

      // Setup audio context and analyser
      audioContextRef.current = new AudioContext()
      analyserRef.current = audioContextRef.current.createAnalyser()
      analyserRef.current.fftSize = 512
      analyserRef.current.smoothingTimeConstant = 0.8

      const source = audioContextRef.current.createMediaStreamSource(stream)
      source.connect(analyserRef.current)

      dataArrayRef.current = new Uint8Array(analyserRef.current.frequencyBinCount)
      
      // Start analysis loop
      updateAudioData()
      
      setError(null)
    } catch (err) {
      console.error('Audio analysis setup failed:', err)
      setError('Microphone access denied')
    }
  }, [updateAudioData])

  const stopAudioAnalysis = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }

    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }

    analyserRef.current = null
    dataArrayRef.current = null
  }, [])

  const startConversation = useCallback(async () => {
    try {
      setError(null)
      
      // Start audio analysis first
      await startAudioAnalysis()
      
      // Generate signed URL directly for the conversation
      const agentId = 'agent_4201k623jy58ehzat15qh2pktbtb'
      const apiKey = import.meta.env.VITE_ELEVENLABS_API_KEY
      
      if (!apiKey) {
        throw new Error('ElevenLabs API key not found. Please set VITE_ELEVENLABS_API_KEY environment variable.')
      }
      
      const response = await fetch(
        `https://api.elevenlabs.io/v1/convai/conversation/get_signed_url?agent_id=${agentId}`,
        {
          method: 'GET',
          headers: {
            'xi-api-key': apiKey
          }
        }
      )
      
      if (!response.ok) {
        throw new Error(`ElevenLabs API error: ${response.status}`)
      }
      
      const data = await response.json()
      const id = await conversation.startSession({ signedUrl: data.signed_url })
      setConversationId(id)
      
    } catch (err) {
      console.error('Failed to start conversation:', err)
      setError(err instanceof Error ? err.message : 'Failed to start conversation')
      stopAudioAnalysis()
    }
  }, [conversation, startAudioAnalysis, stopAudioAnalysis])

  const endConversation = useCallback(async () => {
    try {
      await conversation.endSession()
      setConversationId(null)
      stopAudioAnalysis()
      stopAISpeechSimulation()
    } catch (err) {
      console.error('Failed to end conversation:', err)
      setError(err instanceof Error ? err.message : 'Failed to end conversation')
    }
  }, [conversation, stopAudioAnalysis, stopAISpeechSimulation])

  const setVolume = useCallback(async (volume: number) => {
    try {
      await conversation.setVolume({ volume })
    } catch (err) {
      console.error('Failed to set volume:', err)
      setError(err instanceof Error ? err.message : 'Failed to set volume')
    }
  }, [conversation])

  // Handle AI speaking state changes - only start simulation if no active user input
  useEffect(() => {
    if (conversation.isSpeaking) {
      // Add slight delay to ensure user isn't speaking
      const timer = setTimeout(() => {
        if (conversation.isSpeaking) { // Double check it's still speaking
          startAISpeechSimulation()
        }
      }, 100)
      return () => clearTimeout(timer)
    } else {
      stopAISpeechSimulation()
    }
  }, [conversation.isSpeaking, startAISpeechSimulation, stopAISpeechSimulation])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopAudioAnalysis()
      stopAISpeechSimulation()
    }
  }, [stopAudioAnalysis, stopAISpeechSimulation])

  return {
    isConnected: conversation.status === 'connected',
    isSpeaking: conversation.isSpeaking,
    isListening: conversation.status === 'connected',
    bassLevel: audioLevels.bassLevel,
    midLevel: audioLevels.midLevel,
    trebleLevel: audioLevels.trebleLevel,
    overallLevel: audioLevels.overallLevel,
    error,
    conversationId,
    startConversation,
    endConversation,
    setVolume
  }
}