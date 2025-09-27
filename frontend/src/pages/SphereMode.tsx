import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { MessageCircle, Volume2, VolumeX, Mic, MicOff } from 'lucide-react'
import AudioSphere from '@/components/jarvis/AudioSphere'
import StatusTicker from '@/components/jarvis/StatusTicker'
import SidebarNav from '@/components/jarvis/SidebarNav'
import { Button } from '@/components/ui/button'
import { useNavigate } from 'react-router-dom'
import { useElevenLabsConversation } from '@/hooks/useElevenLabsConversation'

export default function SphereMode() {
  const [isMuted, setIsMuted] = useState(false)
  const navigate = useNavigate()
  const {
    bassLevel,
    midLevel,
    trebleLevel,
    overallLevel,
    isConnected,
    isSpeaking,
    isListening,
    error,
    conversationId,
    startConversation,
    endConversation,
    setVolume
  } = useElevenLabsConversation()


  const getTickerState = () => {
    if (isConnected && isSpeaking) return 'speaking'
    if (isConnected && isListening) return 'listening'
    if (isConnected) return 'thinking'
    return 'idle'
  }

  const getStatusMessage = () => {
    if (error) return `Error: ${error}`
    if (isConnected && isSpeaking) return 'AI is speaking...'
    if (isConnected && isListening) return 'Listening for conversation...'
    if (isConnected) return 'Connected to ElevenLabs AI'
    if (conversationId) return 'Connecting...'
    return 'AI conversation ready'
  }

  const handleSphereInteraction = async () => {
    if (!isConnected) {
      await startConversation()
    } else {
      await endConversation()
    }
  }

  const isActive = isConnected

  return (
    <div className="fixed top-0 left-0 w-screen h-screen bg-black overflow-hidden" style={{ margin: 0, padding: 0 }}>
      
      {/* Navigation */}
      <SidebarNav />
      
      {/* Top Controls */}
      <div className="absolute top-4 right-4 flex gap-2 z-30">
        <Button
          variant="outline" 
          size="sm"
          onClick={isConnected ? endConversation : startConversation}
          className="flex items-center gap-2 bg-space-light/80 backdrop-blur-sm border-neon-cyan/30 
            text-neon-cyan hover:bg-neon-cyan/20"
        >
          {isConnected ? (
            <MicOff className="w-5 h-5" />
          ) : (
            <Mic className="w-5 h-5" />
          )}
          {isConnected ? 'End Chat' : 'Start Chat'}
        </Button>
        
        {isConnected && (
          <Button
            variant="outline"
            size="icon"
            onClick={() => {
              setIsMuted(!isMuted)
              setVolume(isMuted ? 1 : 0)
            }}
            className="jarvis-touch-target bg-space-light/80 backdrop-blur-sm border-neon-cyan/30 
              text-neon-cyan hover:bg-neon-cyan/20"
          >
            {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
          </Button>
        )}
        
        <Button
          variant="outline"
          size="icon"
          onClick={() => navigate('/chat')}
          className="jarvis-touch-target bg-space-light/80 backdrop-blur-sm border-neon-cyan/30 
            text-neon-cyan hover:bg-neon-cyan/20"
        >
          <MessageCircle size={20} />
        </Button>
      </div>
      
      {/* Main Content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center px-4">
        {/* Header */}
        <motion.h1
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="text-4xl md:text-5xl font-bold text-white mb-8 text-center"
        >
          Talk to Jarvis
        </motion.h1>
        
        {/* Sphere Container - Absolutely Centered */}
        <motion.div
          className="flex items-center justify-center"
          initial={{ scale: 0.8 }}
          animate={{ scale: 1 }}
          transition={{ duration: 1, ease: "easeOut" }}
        >
          <AudioSphere
            bassLevel={bassLevel}
            midLevel={midLevel}
            trebleLevel={trebleLevel}
            overallLevel={overallLevel}
            isActive={isActive}
            isSpeaking={isSpeaking}
            onInteraction={handleSphereInteraction}
            className="w-80 h-80 md:w-96 md:h-96"
          />
        </motion.div>
        
        {/* Status Ticker - Fixed position at bottom */}
        <div className="absolute bottom-32">
          <StatusTicker
            state={getTickerState()}
            message={getStatusMessage()}
            className=""
          />
        </div>
      </div>
      
    </div>
  )
}