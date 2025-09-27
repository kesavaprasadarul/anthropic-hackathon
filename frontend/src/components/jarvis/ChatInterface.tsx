import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Mic, Square } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface PreviousAppointment {
  id: string
  salon: string
  service: string
  date: string
  time: string
  price: string
}

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  isConfirmation?: boolean
  actions?: Array<{ label: string; action: () => void }>
  previousAppointments?: PreviousAppointment[]
}

interface ChatInterfaceProps {
  messages: Message[]
  onSendMessage: (message: string) => void
  onVoiceStart?: () => void
  onVoiceStop?: () => void
  isListening?: boolean
  className?: string
}

const quickActions = [
  { label: 'Reserve', emoji: '🍽️' },
  { label: 'Reschedule', emoji: '🔁' },
  { label: 'Cancel', emoji: '❌' },
  { label: 'Info', emoji: '🔎' },
]

export default function ChatInterface({ 
  messages, 
  onSendMessage, 
  onVoiceStart, 
  onVoiceStop, 
  isListening,
  className 
}: ChatInterfaceProps) {
  const [inputValue, setInputValue] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }
  
  useEffect(() => {
    scrollToBottom()
  }, [messages])
  
  const handleSend = () => {
    if (inputValue.trim()) {
      onSendMessage(inputValue.trim())
      setInputValue('')
    }
  }
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }
  
  const toggleRecording = () => {
    if (isRecording) {
      setIsRecording(false)
      onVoiceStop?.()
    } else {
      setIsRecording(true)
      onVoiceStart?.()
    }
  }
  
  const handleQuickAction = (action: string) => {
    onSendMessage(`Help me ${action.toLowerCase()} something`)
  }
  
  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
                  message.type === 'user'
                    ? 'bg-gradient-neon text-space-dark font-medium'
                    : 'jarvis-card text-text-primary'
                }`}
              >
                <p className="text-sm">{message.content}</p>
                
                {/* Confirmation actions */}
                {message.isConfirmation && message.actions && (
                  <div className="flex gap-2 mt-3">
                    {message.actions.map((action, index) => (
                      <Button
                        key={index}
                        size="sm"
                        variant={index === 0 ? "default" : "outline"}
                        onClick={action.action}
                        className="text-xs"
                      >
                        {action.label}
                      </Button>
                    ))}
                  </div>
                )}

                {/* Previous Appointments */}
                {message.previousAppointments && (
                  <div className="mt-3 space-y-2">
                    {message.previousAppointments.map((appointment) => (
                      <motion.div
                        key={appointment.id}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="jarvis-card p-3 border border-border/30 rounded-lg hover:border-neon-cyan/50 
                          transition-all cursor-pointer group"
                        onClick={() => onSendMessage(`Book appointment with ${appointment.salon} for ${appointment.service}`)}
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <h4 className="font-medium text-text-primary text-sm group-hover:text-neon-cyan transition-colors">
                              {appointment.salon}
                            </h4>
                            <p className="text-xs text-text-secondary mt-1">{appointment.service}</p>
                            <p className="text-xs text-text-tertiary mt-1">
                              {appointment.date} at {appointment.time}
                            </p>
                          </div>
                          <div className="text-right">
                            <span className="text-sm font-medium text-neon-cyan">{appointment.price}</span>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
                
                <div className="text-xs opacity-60 mt-1">
                  {message.timestamp.toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                  })}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </div>
      
      {/* Quick Actions */}
      <div className="px-4 py-2">
        <div className="flex gap-2 mb-3 overflow-x-auto">
          {quickActions.map((action) => (
            <Button
              key={action.label}
              variant="outline"
              size="sm"
              onClick={() => handleQuickAction(action.label)}
              className="whitespace-nowrap text-text-secondary border-border/50 
                hover:border-neon-cyan/50 hover:text-neon-cyan transition-all"
            >
              <span className="mr-2">{action.emoji}</span>
              {action.label}
            </Button>
          ))}
        </div>
      </div>
      
      {/* Input Area */}
      <div className="p-4 border-t border-border/50">
        <div className="flex gap-2 items-end">
          <div className="flex-1 relative">
            <Input
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask Jarvis to help you..."
              className="bg-space-light/50 border-border/50 text-text-primary 
                placeholder:text-text-tertiary focus:border-neon-cyan/50"
            />
          </div>
          
          {/* Voice Button */}
          <Button
            variant="outline"
            size="icon"
            onClick={toggleRecording}
            className={`jarvis-touch-target transition-all duration-300 ${
              isRecording || isListening
                ? 'bg-neon-magenta/20 border-neon-magenta text-neon-magenta animate-pulse'
                : 'border-border/50 text-text-secondary hover:border-neon-cyan/50 hover:text-neon-cyan'
            }`}
          >
            {isRecording || isListening ? (
              <Square size={18} />
            ) : (
              <Mic size={18} />
            )}
          </Button>
          
          {/* Send Button */}
          <Button
            onClick={handleSend}
            disabled={!inputValue.trim()}
            className="jarvis-touch-target bg-gradient-neon hover:opacity-90 
              disabled:opacity-50 transition-all"
          >
            <Send size={18} />
          </Button>
        </div>
      </div>
    </div>
  )
}