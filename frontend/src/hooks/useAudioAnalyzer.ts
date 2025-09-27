import { useState, useRef, useCallback, useEffect } from 'react'

interface AudioAnalyzerState {
  isListening: boolean
  isPlayingTest: boolean
  error: string | null
  audioSource: 'microphone' | 'test' | null
  // Frequency analysis
  bassLevel: number      // 0-1 normalized
  midLevel: number       // 0-1 normalized  
  trebleLevel: number    // 0-1 normalized
  overallLevel: number   // 0-1 normalized
  frequencyData: Uint8Array | null
}

export const useAudioAnalyzer = () => {
  const [state, setState] = useState<AudioAnalyzerState>({
    isListening: false,
    isPlayingTest: false,
    error: null,
    audioSource: null,
    bassLevel: 0,
    midLevel: 0,
    trebleLevel: 0,
    overallLevel: 0,
    frequencyData: null,
  })

  // Audio context and nodes
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const sourceRef = useRef<MediaStreamAudioSourceNode | AudioBufferSourceNode | null>(null)
  const animationFrameRef = useRef<number | null>(null)
  const gainNodeRef = useRef<GainNode | null>(null)
  
  // Test audio oscillators
  const oscillator1Ref = useRef<OscillatorNode | null>(null)
  const oscillator2Ref = useRef<OscillatorNode | null>(null)

  // Smoothing arrays for frequency analysis
  const bassHistoryRef = useRef<number[]>([])
  const midHistoryRef = useRef<number[]>([])
  const trebleHistoryRef = useRef<number[]>([])
  const overallHistoryRef = useRef<number[]>([])

  const SMOOTHING_FACTOR = 0.7
  const HISTORY_LENGTH = 5

  // Enhanced frequency analysis with proper ranges
  const analyzeFrequencies = useCallback((frequencyData: Uint8Array) => {
    const sampleRate = audioContextRef.current?.sampleRate || 44100
    const nyquist = sampleRate / 2
    const binCount = frequencyData.length
    const binWidth = nyquist / binCount

    // Define frequency ranges (Hz)
    const bassRange = { min: 20, max: 250 }     // Sub-bass to bass
    const midRange = { min: 250, max: 4000 }    // Low-mid to high-mid
    const trebleRange = { min: 4000, max: 16000 } // High frequencies

    // Convert Hz to bin indices
    const bassBins = {
      start: Math.floor(bassRange.min / binWidth),
      end: Math.floor(bassRange.max / binWidth)
    }
    const midBins = {
      start: Math.floor(midRange.min / binWidth),
      end: Math.floor(midRange.max / binWidth)
    }
    const trebleBins = {
      start: Math.floor(trebleRange.min / binWidth),
      end: Math.floor(trebleRange.max / binWidth)
    }

    // Calculate average amplitude for each range
    const calculateRangeLevel = (startBin: number, endBin: number): number => {
      let sum = 0
      let count = 0
      for (let i = startBin; i < Math.min(endBin, binCount); i++) {
        sum += frequencyData[i]
        count++
      }
      return count > 0 ? (sum / count) / 255 : 0 // Normalize to 0-1
    }

    const bass = calculateRangeLevel(bassBins.start, bassBins.end)
    const mid = calculateRangeLevel(midBins.start, midBins.end)
    const treble = calculateRangeLevel(trebleBins.start, trebleBins.end)
    
    // Overall level (RMS of all frequencies)
    let rms = 0
    for (let i = 0; i < binCount; i++) {
      rms += frequencyData[i] * frequencyData[i]
    }
    const overall = Math.sqrt(rms / binCount) / 255

    // Apply smoothing
    const smoothValue = (value: number, history: number[]): number => {
      history.push(value)
      if (history.length > HISTORY_LENGTH) {
        history.shift()
      }
      return history.reduce((sum, val) => sum + val, 0) / history.length
    }

    const smoothedBass = smoothValue(bass, bassHistoryRef.current)
    const smoothedMid = smoothValue(mid, midHistoryRef.current)
    const smoothedTreble = smoothValue(treble, trebleHistoryRef.current)
    const smoothedOverall = smoothValue(overall, overallHistoryRef.current)

    return {
      bassLevel: Math.min(smoothedBass * 1.5, 1), // Boost sensitivity
      midLevel: Math.min(smoothedMid * 1.2, 1),
      trebleLevel: Math.min(smoothedTreble * 1.3, 1),
      overallLevel: Math.min(smoothedOverall * 1.1, 1),
    }
  }, [])

  // Audio analysis loop
  const updateAudioData = useCallback(() => {
    if (!analyserRef.current) return

    const frequencyData = new Uint8Array(analyserRef.current.frequencyBinCount)
    analyserRef.current.getByteFrequencyData(frequencyData)

    const levels = analyzeFrequencies(frequencyData)

    setState(prev => ({
      ...prev,
      ...levels,
      frequencyData: frequencyData.slice() // Copy array
    }))

    animationFrameRef.current = requestAnimationFrame(updateAudioData)
  }, [analyzeFrequencies])

  // Start microphone analysis
  const startMicrophoneAnalysis = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, error: null }))

      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false
        }
      })

      // Create audio context
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
      const analyser = audioContext.createAnalyser()
      
      // Configure analyser for better frequency resolution
      analyser.fftSize = 2048  // Higher resolution
      analyser.smoothingTimeConstant = SMOOTHING_FACTOR

      // Connect nodes
      const source = audioContext.createMediaStreamSource(stream)
      source.connect(analyser)

      // Store references
      audioContextRef.current = audioContext
      analyserRef.current = analyser
      sourceRef.current = source

      setState(prev => ({
        ...prev,
        isListening: true,
        audioSource: 'microphone'
      }))

      // Start analysis loop
      updateAudioData()

    } catch (error) {
      console.error('Microphone access failed:', error)
      setState(prev => ({
        ...prev,
        error: 'Microphone access denied. Please allow microphone permissions.',
        isListening: false,
        audioSource: null
      }))
    }
  }, [updateAudioData])

  // Start test audio with musical tones
  const startTestAudio = useCallback(() => {
    try {
      setState(prev => ({ ...prev, error: null }))

      // Create audio context
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
      const analyser = audioContext.createAnalyser()
      analyser.fftSize = 2048
      analyser.smoothingTimeConstant = SMOOTHING_FACTOR

      // Create gain node for volume control
      const gainNode = audioContext.createGain()
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)

      // Create oscillators for pleasant ambient sound
      const osc1 = audioContext.createOscillator()
      const osc2 = audioContext.createOscillator()
      const osc3 = audioContext.createOscillator()
      
      // Gentle ambient frequencies: A3 (220 Hz), C5 (523.25 Hz), and E5 (659.25 Hz) - A major chord
      osc1.frequency.setValueAtTime(220, audioContext.currentTime)     // Low bass tone
      osc2.frequency.setValueAtTime(523.25, audioContext.currentTime)  // Mid frequency
      osc3.frequency.setValueAtTime(659.25, audioContext.currentTime)  // Higher frequency
      
      // Use gentle sine waves for smooth, pleasant sound
      osc1.type = 'sine'
      osc2.type = 'sine'
      osc3.type = 'sine'

      // Connect with different gain levels for balance
      const gain1 = audioContext.createGain()
      const gain2 = audioContext.createGain()
      const gain3 = audioContext.createGain()
      
      gain1.gain.setValueAtTime(0.4, audioContext.currentTime)  // Stronger bass
      gain2.gain.setValueAtTime(0.2, audioContext.currentTime)  // Medium mid
      gain3.gain.setValueAtTime(0.15, audioContext.currentTime) // Gentle treble

      // Connect audio graph: oscillators -> individual gains -> main gain -> analyser -> destination
      osc1.connect(gain1)
      osc2.connect(gain2)
      osc3.connect(gain3)
      
      gain1.connect(gainNode)
      gain2.connect(gainNode)
      gain3.connect(gainNode)
      gainNode.connect(analyser)
      gainNode.connect(audioContext.destination)

      // Add very gentle frequency modulation for subtle movement
      const lfo = audioContext.createOscillator()
      const lfoGain = audioContext.createGain()
      lfo.frequency.setValueAtTime(0.3, audioContext.currentTime) // Slow 0.3 Hz modulation
      lfoGain.gain.setValueAtTime(5, audioContext.currentTime)    // Very subtle ±5 Hz modulation
      
      lfo.type = 'sine'
      lfo.connect(lfoGain)
      lfoGain.connect(osc2.frequency) // Only modulate the mid frequency slightly
      
      // Start all oscillators
      osc1.start()
      osc2.start()
      osc3.start()
      lfo.start()

      // Store references (now we have 3 oscillators)
      audioContextRef.current = audioContext
      analyserRef.current = analyser
      gainNodeRef.current = gainNode
      oscillator1Ref.current = osc1
      oscillator2Ref.current = osc2
      // Store the third oscillator in a different way since we only have 2 refs
      ;(osc3 as any)._isThirdOscillator = true

      setState(prev => ({
        ...prev,
        isPlayingTest: true,
        audioSource: 'test'
      }))

      // Start analysis
      updateAudioData()

    } catch (error) {
      console.error('Test audio failed:', error)
      setState(prev => ({
        ...prev,
        error: 'Failed to create test audio',
        isPlayingTest: false,
        audioSource: null
      }))
    }
  }, [updateAudioData])

  // Stop all audio analysis
  const stopAnalysis = useCallback(() => {
    // Stop animation frame
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
    }

    // Stop oscillators
    if (oscillator1Ref.current) {
      oscillator1Ref.current.stop()
      oscillator1Ref.current = null
    }
    if (oscillator2Ref.current) {
      oscillator2Ref.current.stop()
      oscillator2Ref.current = null
    }

    // Stop microphone stream
    if (sourceRef.current && 'mediaStream' in sourceRef.current) {
      const stream = (sourceRef.current as any).mediaStream
      if (stream) {
        stream.getTracks().forEach((track: MediaStreamTrack) => track.stop())
      }
    }

    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }

    // Clear references
    analyserRef.current = null
    sourceRef.current = null
    gainNodeRef.current = null

    // Clear smoothing history
    bassHistoryRef.current = []
    midHistoryRef.current = []
    trebleHistoryRef.current = []
    overallHistoryRef.current = []

    setState(prev => ({
      ...prev,
      isListening: false,
      isPlayingTest: false,
      audioSource: null,
      bassLevel: 0,
      midLevel: 0,
      trebleLevel: 0,
      overallLevel: 0,
      frequencyData: null
    }))
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopAnalysis()
    }
  }, [stopAnalysis])

  return {
    ...state,
    startMicrophoneAnalysis,
    startTestAudio,
    stopAnalysis,
  }
}