import { useState } from 'react'
import { motion } from 'framer-motion'
import { ArrowLeft, Volume2, VolumeX } from 'lucide-react'
import ChatInterface from '@/components/jarvis/ChatInterface'
import { Button } from '@/components/ui/button'
import { useNavigate } from 'react-router-dom'
import { sendConversationToBackend } from '@/lib/conversationLogger'

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

export default function ChatMode() {
  const navigate = useNavigate()
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: 'Hi! I\'m Jarvis, your AI assistant. I can help you make reservations, reschedule appointments, cancel bookings, or get information. What would you like me to help you with?',
      timestamp: new Date()
    }
  ])
  const [isListening, setIsListening] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  
  const handleSendMessage = (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])
    
    // Simulate AI response
    setTimeout(() => {
      let assistantContent = ''
      let isConfirmation = false
      let actions: Array<{ label: string; action: () => void }> = []
      
      if (content.toLowerCase().includes('hairdresser') || content.toLowerCase().includes('hair appointment') || content.toLowerCase().includes('haircut')) {
        assistantContent = 'I found 2 previous appointments with hairdressers in your history. Would you like me to use the same details or book with a new salon?'
        isConfirmation = true
        actions = [
          { 
            label: 'Use Previous Data', 
            action: () => handlePreviousAppointments()
          },
          { 
            label: 'New Salon', 
            action: () => handleConfirmAction('What type of hair service are you looking for and when would you prefer?')
          }
        ]
      } else if (content.toLowerCase().includes('reservation') || content.toLowerCase().includes('reserve')) {
        assistantContent = 'I can help you make a dinner reservation! I found availability at Bella Ciao for tonight at 7:30 PM for 2 people. Should I book this for you?'
        isConfirmation = true
        actions = [
          { 
            label: 'Book it', 
            action: () => handleConfirmAction('Booking confirmed! I\'ll call the restaurant now and notify you once it\'s done.')
          },
          { 
            label: 'Different time', 
            action: () => handleConfirmAction('What time would you prefer? I can check other available slots.')
          }
        ]
      } else if (content.toLowerCase().includes('reschedule')) {
        assistantContent = 'I can help you reschedule your appointment. Which booking would you like to change?'
      } else if (content.toLowerCase().includes('cancel')) {
        assistantContent = 'I can help you cancel a booking. Which reservation would you like me to cancel?'
      } else if (content.toLowerCase().includes('info') || content.toLowerCase().includes('information')) {
        assistantContent = 'I can get information for you. What would you like to know about?'
      } else {
        assistantContent = 'I understand you need help with something. Could you be more specific? I can help with reservations, rescheduling, cancellations, or getting information.'
      }
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: assistantContent,
        timestamp: new Date(),
        isConfirmation,
        actions: actions.length > 0 ? actions : undefined
      }
      
      setMessages(prev => [...prev, assistantMessage])
      
      // Send conversation to backend
      sendConversationToBackend({
        userMessage: content,
        agentResponse: assistantContent,
        timestamp: new Date().toISOString(),
        conversationType: 'text'
      })
    }, 1000)
  }
  
  const handleConfirmAction = (responseContent: string) => {
    const responseMessage: Message = {
      id: Date.now().toString(),
      type: 'assistant',
      content: responseContent,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, responseMessage])
  }
  
  const handlePreviousAppointments = () => {
    const mockPreviousAppointments: PreviousAppointment[] = [
      {
        id: '1',
        salon: 'Bella Hair Studio',
        service: 'Cut & Style',
        date: 'March 15, 2024',
        time: '2:30 PM',
        price: '$85'
      },
      {
        id: '2',
        salon: 'Urban Cuts',
        service: 'Color & Highlights',
        date: 'January 22, 2024',
        time: '11:00 AM',
        price: '$145'
      }
    ]
    
    const responseMessage: Message = {
      id: Date.now().toString(),
      type: 'assistant',
      content: 'Here are your previous hair appointments. Which one would you like to use as reference for your new booking?',
      timestamp: new Date(),
      previousAppointments: mockPreviousAppointments
    }
    
    setMessages(prev => [...prev, responseMessage])
  }
  
  const handleVoiceStart = () => {
    setIsListening(true)
    // Simulate voice recognition
    setTimeout(() => {
      setIsListening(false)
      handleSendMessage("Make a reservation for 2 people tonight at 7 PM")
    }, 3000)
  }
  
  const handleVoiceStop = () => {
    setIsListening(false)
  }
  
  return (
    <div className="min-h-screen bg-gradient-space flex flex-col">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between p-4 border-b border-border/20 backdrop-blur-sm"
      >
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate('/')}
            className="jarvis-touch-target text-neon-cyan hover:bg-neon-cyan/20"
          >
            <ArrowLeft size={20} />
          </Button>
          
          <div>
            <h1 className="font-bold text-text-primary jarvis-text-glow">Chat Mode</h1>
            <p className="text-xs text-text-secondary">Text-based conversation</p>
          </div>
        </div>
        
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsMuted(!isMuted)}
          className="jarvis-touch-target text-neon-cyan hover:bg-neon-cyan/20"
        >
          {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
        </Button>
      </motion.header>
      
      {/* Chat Interface */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="flex-1"
      >
        <ChatInterface
          messages={messages}
          onSendMessage={handleSendMessage}
          onVoiceStart={handleVoiceStart}
          onVoiceStop={handleVoiceStop}
          isListening={isListening}
        />
      </motion.div>
    </div>
  )
}