import { motion } from 'framer-motion'
import { 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  Loader2, 
  Calendar,
  MapPin,
  User,
  MoreVertical
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

type TaskStatus = 'queued' | 'calling' | 'awaiting_input' | 'completed' | 'failed'
type TaskType = 'reservation' | 'reschedule' | 'cancel' | 'info'

interface Task {
  id: string
  type: TaskType
  title: string
  description: string
  status: TaskStatus
  createdAt: string
  scheduledFor?: string
  location?: string
  participants?: number
  outcome?: string
}

interface TaskCardProps {
  task: Task
  onClick?: () => void
  className?: string
}

const statusConfig = {
  queued: { icon: Clock, color: 'text-warning', bg: 'bg-warning/20', label: 'Queued' },
  calling: { icon: Loader2, color: 'text-neon-blue', bg: 'bg-neon-blue/20', label: 'Calling' },
  awaiting_input: { icon: AlertCircle, color: 'text-neon-magenta', bg: 'bg-neon-magenta/20', label: 'Needs Input' },
  completed: { icon: CheckCircle, color: 'text-success', bg: 'bg-success/20', label: 'Completed' },
  failed: { icon: AlertCircle, color: 'text-error', bg: 'bg-error/20', label: 'Failed' }
}

const typeIcons = {
  reservation: '🍽️',
  reschedule: '🔁',
  cancel: '❌',
  info: '🔎'
}

export default function TaskCard({ task, onClick, className }: TaskCardProps) {
  const { icon: StatusIcon, color, bg, label } = statusConfig[task.status]
  const typeIcon = typeIcons[task.type]
  
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`jarvis-card rounded-2xl p-4 cursor-pointer group hover:border-neon-cyan/40 
        transition-all duration-300 ${className}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="text-2xl">{typeIcon}</div>
          <div>
            <h3 className="font-semibold text-text-primary group-hover:text-neon-cyan transition-colors">
              {task.title}
            </h3>
            <p className="text-sm text-text-secondary">{task.description}</p>
          </div>
        </div>
        
        <Button variant="ghost" size="icon" className="opacity-0 group-hover:opacity-100 transition-opacity">
          <MoreVertical size={16} />
        </Button>
      </div>
      
      {/* Status Badge */}
      <div className="flex items-center justify-between mb-3">
        <Badge 
          variant="secondary" 
          className={`${bg} ${color} border-current/30 font-medium flex items-center gap-1.5`}
        >
          <StatusIcon 
            size={12} 
            className={task.status === 'calling' ? 'animate-spin' : ''} 
          />
          {label}
        </Badge>
        
        <span className="text-xs text-text-tertiary">
          {new Date(task.createdAt).toLocaleDateString()}
        </span>
      </div>
      
      {/* Details */}
      {(task.scheduledFor || task.location || task.participants) && (
        <div className="space-y-2 pt-3 border-t border-border/50">
          {task.scheduledFor && (
            <div className="flex items-center gap-2 text-sm text-text-secondary">
              <Calendar size={14} />
              <span>{new Date(task.scheduledFor).toLocaleString()}</span>
            </div>
          )}
          
          {task.location && (
            <div className="flex items-center gap-2 text-sm text-text-secondary">
              <MapPin size={14} />
              <span>{task.location}</span>
            </div>
          )}
          
          {task.participants && (
            <div className="flex items-center gap-2 text-sm text-text-secondary">
              <User size={14} />
              <span>{task.participants} people</span>
            </div>
          )}
        </div>
      )}
      
      {/* Outcome */}
      {task.outcome && task.status === 'completed' && (
        <div className="mt-3 p-2 rounded-lg bg-success/10 border border-success/20">
          <p className="text-xs text-success">{task.outcome}</p>
        </div>
      )}
      
      {/* Progress indicator for active tasks */}
      {(task.status === 'calling' || task.status === 'queued') && (
        <div className="mt-3">
          <motion.div
            className="h-1 bg-neon-cyan/20 rounded-full overflow-hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <motion.div
              className="h-full bg-gradient-neon"
              animate={{ x: [-100, 100] }}
              transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
              style={{ width: '50%' }}
            />
          </motion.div>
        </div>
      )}
    </motion.div>
  )
}