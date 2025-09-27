import { motion, AnimatePresence } from 'framer-motion'
import { Loader2, Mic, Brain, Volume2 } from 'lucide-react'

type TickerState = 'idle' | 'listening' | 'thinking' | 'speaking' | 'calling' | 'confirming'

interface StatusTickerProps {
  state: TickerState
  message?: string
  className?: string
}

const statusMessages = {
  idle: "Ready to help...",
  listening: "Listening...",
  thinking: "Processing...",
  speaking: "Speaking...",
  calling: "Making the call...",
  confirming: "Confirming details..."
}

const statusIcons = {
  idle: null,
  listening: Mic,
  thinking: Brain,
  speaking: Volume2,
  calling: Loader2,
  confirming: Loader2
}

export default function StatusTicker({ state, message, className }: StatusTickerProps) {
  const displayMessage = message || statusMessages[state]
  const Icon = statusIcons[state]
  
  return (
    <motion.div
      className={`flex items-center justify-center gap-2 px-4 py-2 rounded-full 
        bg-space-light/50 backdrop-blur-sm border border-neon-cyan/20 ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
    >
      <AnimatePresence mode="wait">
        {Icon && (
          <motion.div
            key={state}
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            exit={{ scale: 0, rotate: 180 }}
            transition={{ duration: 0.3 }}
            className="text-neon-cyan"
          >
            <Icon 
              size={16} 
              className={`${state === 'calling' || state === 'confirming' ? 'animate-spin' : ''}`}
            />
          </motion.div>
        )}
      </AnimatePresence>
      
      <motion.span
        key={displayMessage}
        initial={{ opacity: 0, x: 10 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -10 }}
        transition={{ duration: 0.2 }}
        className="text-sm font-medium text-text-primary jarvis-text-glow"
      >
        {displayMessage}
      </motion.span>
    </motion.div>
  )
}