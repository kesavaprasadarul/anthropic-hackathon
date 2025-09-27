import { useState, useCallback, useRef, useEffect } from 'react'

type SpeechState = 'idle' | 'listening' | 'processing'

export interface SpeechRecognitionHook {
  state: SpeechState
  isListening: boolean
  startListening: () => Promise<void>
  stopListening: () => void
  lastTranscript: string
  error: string | null
}

// Extend Window interface for speech recognition
declare global {
  interface Window {
    SpeechRecognition: any
    webkitSpeechRecognition: any
  }
}

export function useSpeechRecognition(): SpeechRecognitionHook {
  const [state, setState] = useState<SpeechState>('idle')
  const [lastTranscript, setLastTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)
  const recognitionRef = useRef<any>(null)
  const isListeningRef = useRef(false)

  const startListening = useCallback(async () => {
    try {
      if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        throw new Error('Speech recognition not supported in this browser')
      }

      // Request microphone permissions
      await navigator.mediaDevices.getUserMedia({ audio: true })

      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      const recognition = new SpeechRecognition()

      recognition.continuous = true
      recognition.interimResults = true
      recognition.lang = 'en-US'

      recognition.onstart = () => {
        console.log('🎤 Speech recognition started successfully')
        setState('listening')
        isListeningRef.current = true
        setError(null)
      }

      recognition.onresult = (event) => {
        console.log('🗣️ Speech recognition result received:', event)
        let finalTranscript = ''
        let interimTranscript = ''

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript
          console.log(`Result ${i}: "${transcript}" (final: ${event.results[i].isFinal})`)
          if (event.results[i].isFinal) {
            finalTranscript += transcript
          } else {
            interimTranscript += transcript
          }
        }

        if (finalTranscript) {
          console.log('🎯 Final transcript:', finalTranscript)
          setState('processing')
          setLastTranscript(finalTranscript)
          
          // Return to listening after a brief processing indication
          setTimeout(() => {
            if (isListeningRef.current) {
              console.log('⏪ Returning to listening state')
              setState('listening')
            }
          }, 1000)
        } else if (interimTranscript) {
          console.log('📝 Interim transcript:', interimTranscript)
        }
      }

      recognition.onerror = (event) => {
        console.error('🚨 Speech recognition error:', event.error)
        setError(`Speech recognition error: ${event.error}`)
        setState('idle')
        isListeningRef.current = false
      }

      recognition.onend = () => {
        console.log('🔚 Speech recognition ended')
        if (isListeningRef.current) {
          console.log('🔄 Restarting speech recognition (continuous mode)')
          // Restart recognition if we're still supposed to be listening
          recognition.start()
        } else {
          console.log('✋ Speech recognition stopped by user')
          setState('idle')
        }
      }

      recognitionRef.current = recognition
      recognition.start()

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start speech recognition'
      setError(errorMessage)
      setState('idle')
      console.error('Failed to start speech recognition:', err)
    }
  }, [])

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      isListeningRef.current = false
      recognitionRef.current.stop()
      recognitionRef.current = null
      setState('idle')
    }
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop()
      }
    }
  }, [])

  return {
    state,
    isListening: isListeningRef.current,
    startListening,
    stopListening,
    lastTranscript,
    error
  }
}