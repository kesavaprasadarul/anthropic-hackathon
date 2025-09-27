import { useState } from 'react'
import { motion } from 'framer-motion'
import { ArrowLeft, Filter, Search } from 'lucide-react'
import TaskCard from '@/components/jarvis/TaskCard'
import SidebarNav from '@/components/jarvis/SidebarNav'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { useNavigate } from 'react-router-dom'

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

const mockTasks: Task[] = [
  {
    id: '1',
    type: 'reservation',
    title: 'Dinner Reservation',
    description: 'Bella Ciao • Table for 2',
    status: 'completed',
    createdAt: '2024-01-15T10:30:00Z',
    scheduledFor: '2024-01-15T19:30:00Z',
    location: 'Bella Ciao Restaurant',
    participants: 2,
    outcome: 'Reservation confirmed for 7:30 PM'
  },
  {
    id: '2',
    type: 'reschedule',
    title: 'Dentist Appointment',
    description: 'Move to next week',
    status: 'awaiting_input',
    createdAt: '2024-01-14T14:15:00Z',
    scheduledFor: '2024-01-20T09:00:00Z',
    location: 'Dr. Smith Dental',
    participants: 1
  },
  {
    id: '3',
    type: 'cancel',
    title: 'Gym Session',
    description: 'Cancel today\'s training',
    status: 'calling',
    createdAt: '2024-01-14T08:45:00Z',
    location: 'FitCore Gym'
  },
  {
    id: '4',
    type: 'info',
    title: 'Restaurant Hours',
    description: 'Check opening times',
    status: 'completed',
    createdAt: '2024-01-13T16:20:00Z',
    location: 'The Garden Bistro',
    outcome: 'Open daily 5 PM - 11 PM'
  },
  {
    id: '5',
    type: 'reservation',
    title: 'Weekend Brunch',
    description: 'Saturday morning • 4 people',
    status: 'failed',
    createdAt: '2024-01-12T11:30:00Z',
    scheduledFor: '2024-01-14T10:00:00Z',
    participants: 4,
    outcome: 'No availability found'
  }
]

const filterOptions = [
  { label: 'All', value: 'all' },
  { label: 'In Progress', value: 'in_progress' },
  { label: 'Needs Input', value: 'awaiting_input' },
  { label: 'Completed', value: 'completed' }
]

export default function TasksPage() {
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')
  const [activeFilter, setActiveFilter] = useState('all')
  
  const filteredTasks = mockTasks.filter(task => {
    const matchesSearch = task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         task.description.toLowerCase().includes(searchQuery.toLowerCase())
    
    if (!matchesSearch) return false
    
    switch (activeFilter) {
      case 'in_progress':
        return ['queued', 'calling'].includes(task.status)
      case 'awaiting_input':
        return task.status === 'awaiting_input'
      case 'completed':
        return task.status === 'completed'
      default:
        return true
    }
  })
  
  const getStatusCount = (filter: string) => {
    switch (filter) {
      case 'in_progress':
        return mockTasks.filter(t => ['queued', 'calling'].includes(t.status)).length
      case 'awaiting_input':
        return mockTasks.filter(t => t.status === 'awaiting_input').length
      case 'completed':
        return mockTasks.filter(t => t.status === 'completed').length
      default:
        return mockTasks.length
    }
  }
  
  const handleTaskClick = (task: Task) => {
    // Navigate to task detail page (to be implemented)
    console.log('Task clicked:', task)
  }
  
  return (
    <div className="min-h-screen bg-gradient-space">
      {/* Navigation */}
      <SidebarNav />
      
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="sticky top-0 z-30 backdrop-blur-xl border-b border-border/20 bg-space-dark/80"
      >
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate('/')}
              className="jarvis-touch-target text-neon-cyan hover:bg-neon-cyan/20 md:hidden"
            >
              <ArrowLeft size={20} />
            </Button>
            
            <div>
              <h1 className="font-bold text-text-primary jarvis-text-glow">Task History</h1>
              <p className="text-xs text-text-secondary">
                {filteredTasks.length} of {mockTasks.length} tasks
              </p>
            </div>
          </div>
          
          <Button variant="ghost" size="icon" className="text-neon-cyan hover:bg-neon-cyan/20">
            <Filter size={20} />
          </Button>
        </div>
        
        {/* Search */}
        <div className="px-4 pb-4">
          <div className="relative">
            <Search size={18} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-tertiary" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search tasks..."
              className="pl-10 bg-space-light/50 border-border/50 text-text-primary 
                placeholder:text-text-tertiary focus:border-neon-cyan/50"
            />
          </div>
        </div>
      </motion.header>
      
      {/* Filter Chips */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="px-4 py-3 border-b border-border/10"
      >
        <div className="flex gap-2 overflow-x-auto">
          {filterOptions.map((filter) => (
            <Button
              key={filter.value}
              variant={activeFilter === filter.value ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveFilter(filter.value)}
              className={`whitespace-nowrap transition-all ${
                activeFilter === filter.value
                  ? 'bg-gradient-neon text-space-dark'
                  : 'border-border/50 text-text-secondary hover:border-neon-cyan/50 hover:text-neon-cyan'
              }`}
            >
              {filter.label}
              <Badge 
                variant="secondary" 
                className="ml-2 text-xs bg-current/20 text-current border-none"
              >
                {getStatusCount(filter.value)}
              </Badge>
            </Button>
          ))}
        </div>
      </motion.div>
      
      {/* Task List */}
      <div className="p-4 space-y-4">
        {filteredTasks.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12"
          >
            <div className="w-16 h-16 bg-space-light rounded-full flex items-center justify-center mx-auto mb-4">
              <Search size={24} className="text-text-tertiary" />
            </div>
            <h3 className="text-text-primary font-medium mb-2">No tasks found</h3>
            <p className="text-text-secondary text-sm">
              {searchQuery ? 'Try adjusting your search terms' : 'Your task history will appear here'}
            </p>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="space-y-3"
          >
            {filteredTasks.map((task, index) => (
              <motion.div
                key={task.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <TaskCard
                  task={task}
                  onClick={() => handleTaskClick(task)}
                />
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </div>
  )
}