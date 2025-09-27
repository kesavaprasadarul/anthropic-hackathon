import { useState, useCallback, useRef, useEffect } from 'react'

export interface AudioVisualizerHook {
  isListening: boolean
  audioData: Float32Array | null
  startAudioAnalysis: () => Promise<void>
  stopAudioAnalysis: () => void
  startTestAudio: () => Promise<void>
  stopTestAudio: () => void
  isPlayingTest: boolean
  error: string | null
  bassFrequency: number
  trebleFrequency: number
  audioSource: 'microphone' | 'test' | null
}

export function useAudioVisualizer(): AudioVisualizerHook {
  const [isListening, setIsListening] = useState(false)
  const [isPlayingTest, setIsPlayingTest] = useState(false)
  const [audioData, setAudioData] = useState<Float32Array | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [bassFrequency, setBassFrequency] = useState(0)
  const [trebleFrequency, setTrebleFrequency] = useState(0)
  const [audioSource, setAudioSource] = useState<'microphone' | 'test' | null>(null)
  
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const sourceRef = useRef<MediaStreamAudioSourceNode | MediaElementAudioSourceNode | null>(null)
  const animationIdRef = useRef<number | null>(null)
  const testAudioRef = useRef<HTMLAudioElement | null>(null)

  const startAudioAnalysis = useCallback(async () => {
    if (isPlayingTest) {
      stopTestAudio()
    }
    
    try {
      console.log('🎵 Starting audio analysis...')
      
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false
        } 
      })

      // Create audio context with fallback for webkit
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext
      const audioContext = new AudioContextClass()
      const source = audioContext.createMediaStreamSource(stream)
      const analyser = audioContext.createAnalyser()

      // Configure analyser settings (following the article)
      analyser.fftSize = 512
      analyser.smoothingTimeConstant = 0.85

      // Connect nodes
      source.connect(analyser)
      // Note: We don't connect to destination to avoid feedback

      audioContextRef.current = audioContext
      analyserRef.current = analyser
      sourceRef.current = source

      const bufferLength = analyser.frequencyBinCount
      const dataArray = new Float32Array(bufferLength)

      setAudioSource('microphone')
      setIsListening(true)

      // Animation loop to continuously analyze audio
      const analyze = () => {
        if (!analyserRef.current || !isListening) return

        analyserRef.current.getFloatFrequencyData(dataArray)
        setAudioData(new Float32Array(dataArray))

        // Split frequencies like in the article
        const lowerHalfArray = dataArray.slice(0, Math.floor(dataArray.length / 2))
        const upperHalfArray = dataArray.slice(Math.floor(dataArray.length / 2))

        // Calculate averages and max values
        const lowerAvg = lowerHalfArray.reduce((a, b) => a + b, 0) / lowerHalfArray.length
        const upperAvg = upperHalfArray.reduce((a, b) => a + b, 0) / upperHalfArray.length
        
        // Normalize values (convert from dB scale)
        const normalizedBass = Math.max(0, (lowerAvg + 100) / 100) // Convert from dB (-100 to 0)
        const normalizedTreble = Math.max(0, (upperAvg + 100) / 100)

        setBassFrequency(normalizedBass)
        setTrebleFrequency(normalizedTreble)

        animationIdRef.current = requestAnimationFrame(analyze)
      }

      analyze()
      console.log('🎵 Audio analysis started successfully')

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start audio analysis'
      setError(errorMessage)
      setIsListening(false)
      setAudioSource(null)
      console.error('🚨 Audio analysis error:', err)
    }
  }, [isListening, isPlayingTest])

  const startTestAudio = useCallback(async () => {
    if (isListening) {
      stopAudioAnalysis()
    }

    try {
      console.log('🎵 Starting test audio...')

      // Create audio context
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext
      const audioContext = new AudioContextClass()
      
      // Create a more pleasant musical tone setup
      const mainOscillator = audioContext.createOscillator()
      const harmonyOscillator = audioContext.createOscillator()
      const mainGain = audioContext.createGain()
      const harmonyGain = audioContext.createGain()
      const analyser = audioContext.createAnalyser()
      const masterGain = audioContext.createGain()

      // Configure oscillators for pleasant musical tones
      mainOscillator.frequency.setValueAtTime(220, audioContext.currentTime) // A3 note
      harmonyOscillator.frequency.setValueAtTime(330, audioContext.currentTime) // E4 note (perfect fifth)
      mainOscillator.type = 'sine'
      harmonyOscillator.type = 'sine'

      // Configure gains for pleasant volume
      mainGain.gain.setValueAtTime(0.1, audioContext.currentTime)
      harmonyGain.gain.setValueAtTime(0.05, audioContext.currentTime)
      masterGain.gain.setValueAtTime(0.3, audioContext.currentTime)

      // Connect nodes
      mainOscillator.connect(mainGain)
      harmonyOscillator.connect(harmonyGain)
      mainGain.connect(masterGain)
      harmonyGain.connect(masterGain)
      masterGain.connect(analyser)
      analyser.connect(audioContext.destination)

      // Configure analyser with better settings
      analyser.fftSize = 2048 // Higher resolution
      analyser.smoothingTimeConstant = 0.8

      // Start oscillators
      mainOscillator.start()
      harmonyOscillator.start()

      audioContextRef.current = audioContext
      analyserRef.current = analyser
      sourceRef.current = masterGain as any
      testAudioRef.current = { mainOscillator, harmonyOscillator, mainGain, harmonyGain, masterGain } as any

      const bufferLength = analyser.frequencyBinCount
      const dataArray = new Uint8Array(bufferLength) // Use Uint8Array for better results

      setIsPlayingTest(true)
      setAudioSource('test')
      setError(null)

      // Create dynamic audio modulation for interesting visual effects
      let time = 0

      // Animation loop with musical modulation
      const analyze = () => {
        if (!analyserRef.current || !isPlayingTest || !testAudioRef.current) return

        time += 0.016 // ~60fps

        // Create pleasant musical variations
        const testAudio = testAudioRef.current as any
        const mainVolume = 0.08 + Math.sin(time * 0.7) * 0.04 // Gentle main volume variation
        const harmonyVolume = 0.03 + Math.sin(time * 1.2) * 0.02 // Gentle harmony variation
        
        // Occasionally change frequencies for musical interest
        const mainFreq = 220 + Math.sin(time * 0.3) * 20 // Gentle frequency modulation
        const harmonyFreq = 330 + Math.sin(time * 0.4) * 15 // Gentle harmony modulation
        
        testAudio.mainGain.gain.setValueAtTime(mainVolume, audioContextRef.current!.currentTime)
        testAudio.harmonyGain.gain.setValueAtTime(harmonyVolume, audioContextRef.current!.currentTime)
        testAudio.mainOscillator.frequency.setValueAtTime(mainFreq, audioContextRef.current!.currentTime)
        testAudio.harmonyOscillator.frequency.setValueAtTime(harmonyFreq, audioContextRef.current!.currentTime)

        // Get frequency data using byte frequency data (more reliable)
        analyserRef.current.getByteFrequencyData(dataArray)
        
        // Debug: log some data
        console.log('📊 Frequency data sample:', dataArray.slice(0, 20))
        
        setAudioData(new Float32Array(dataArray))

        // Simple approach: split the frequency spectrum in half
        const lowerHalf = dataArray.slice(0, Math.floor(dataArray.length / 2))
        const upperHalf = dataArray.slice(Math.floor(dataArray.length / 2))
        
        // Calculate averages (0-255 range from getByteFrequencyData)
        const lowerSum = lowerHalf.reduce((a, b) => a + b, 0)
        const upperSum = upperHalf.reduce((a, b) => a + b, 0)
        const lowerAvg = lowerSum / lowerHalf.length
        const upperAvg = upperSum / upperHalf.length
        
        // Normalize to 0-1 range
        const normalizedBass = Math.min(1, lowerAvg / 128) // Divide by 128 (half of 255)
        const normalizedTreble = Math.min(1, upperAvg / 128)
        
        console.log('🔊 Analysis - Lower avg:', lowerAvg, 'Upper avg:', upperAvg)
        console.log('🎯 Normalized - Bass:', normalizedBass, 'Treble:', normalizedTreble)

        setBassFrequency(normalizedBass)
        setTrebleFrequency(normalizedTreble)

        animationIdRef.current = requestAnimationFrame(analyze)
      }

      analyze()
      console.log('🎵 Test audio started successfully')

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start test audio'
      setError(errorMessage)
      setIsPlayingTest(false)
      setAudioSource(null)
      console.error('🚨 Test audio error:', err)
    }
  }, [isListening, isPlayingTest])

  const stopTestAudio = useCallback(() => {
    console.log('🔇 Stopping test audio...')
    
    if (testAudioRef.current) {
      const testAudio = testAudioRef.current as any
      if (testAudio.mainOscillator) {
        testAudio.mainOscillator.stop()
        testAudio.harmonyOscillator.stop()
      }
      testAudioRef.current = null
    }

    if (animationIdRef.current) {
      cancelAnimationFrame(animationIdRef.current)
      animationIdRef.current = null
    }

    if (sourceRef.current) {
      sourceRef.current.disconnect()
      sourceRef.current = null
    }

    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }

    analyserRef.current = null
    setIsPlayingTest(false)
    setAudioData(null)
    setBassFrequency(0)
    setTrebleFrequency(0)
    setAudioSource(null)
  }, [])

  const stopAudioAnalysis = useCallback(() => {
    console.log('🔇 Stopping audio analysis...')
    
    if (animationIdRef.current) {
      cancelAnimationFrame(animationIdRef.current)
      animationIdRef.current = null
    }

    if (sourceRef.current) {
      sourceRef.current.disconnect()
      sourceRef.current = null
    }

    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }

    analyserRef.current = null
    setIsListening(false)
    setAudioData(null)
    setBassFrequency(0)
    setTrebleFrequency(0)
    setAudioSource(null)
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopAudioAnalysis()
      stopTestAudio()
    }
  }, [stopAudioAnalysis, stopTestAudio])

  return {
    isListening,
    audioData,
    startAudioAnalysis,
    stopAudioAnalysis,
    startTestAudio,
    stopTestAudio,
    isPlayingTest,
    error,
    bassFrequency,
    trebleFrequency,
    audioSource
  }
}