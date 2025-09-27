import { useState, useCallback } from 'react'
import { useTaskPolling, TaskUpdate } from './useTaskPolling'

export interface Task {
  id: string
  type: 'reservation' | 'reschedule' | 'cancel' | 'info'
  title: string
  description: string
  status: 'queued' | 'calling' | 'awaiting_input' | 'completed' | 'failed'
  createdAt: string
  scheduledFor?: string
  location?: string
  participants?: number
  outcome?: string
  processId?: string
}

export function useTaskManager() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [activeProcessId, setActiveProcessId] = useState<string | null>(null)
  
  // Use polling for the active process
  const { taskUpdate, error: pollingError, isPolling } = useTaskPolling(activeProcessId)

  // Update task when polling receives updates
  if (taskUpdate && activeProcessId) {
    setTasks(prevTasks => 
      prevTasks.map(task => 
        task.processId === activeProcessId 
          ? { 
              ...task, 
              status: taskUpdate.status,
              ...(taskUpdate.task && taskUpdate.task)
            }
          : task
      )
    )
  }

  const addTask = useCallback((taskData: Omit<Task, 'id' | 'createdAt'>) => {
    const newTask: Task = {
      ...taskData,
      id: Math.random().toString(36).substring(7),
      createdAt: new Date().toISOString()
    }
    
    setTasks(prev => [newTask, ...prev])
    
    // Start polling if this task has a processId
    if (newTask.processId) {
      setActiveProcessId(newTask.processId)
    }
    
    return newTask
  }, [])

  const updateTask = useCallback((id: string, updates: Partial<Task>) => {
    setTasks(prev => 
      prev.map(task => 
        task.id === id ? { ...task, ...updates } : task
      )
    )
  }, [])

  const removeTask = useCallback((id: string) => {
    setTasks(prev => prev.filter(task => task.id !== id))
  }, [])

  const stopPolling = useCallback(() => {
    setActiveProcessId(null)
  }, [])

  return {
    tasks,
    addTask,
    updateTask,
    removeTask,
    isPolling,
    pollingError,
    stopPolling
  }
}