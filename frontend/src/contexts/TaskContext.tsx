import React, { createContext, useContext, ReactNode } from 'react'
import { useTaskManager, Task } from '@/hooks/useTaskManager'

interface TaskContextType {
  tasks: Task[]
  addTask: (taskData: Omit<Task, 'id' | 'createdAt'>) => Task
  updateTask: (id: string, updates: Partial<Task>) => void
  removeTask: (id: string) => void
  isPolling: boolean
  pollingError: string | null
  stopPolling: () => void
}

const TaskContext = createContext<TaskContextType | undefined>(undefined)

export function TaskProvider({ children }: { children: ReactNode }) {
  const taskManager = useTaskManager()
  
  return (
    <TaskContext.Provider value={taskManager}>
      {children}
    </TaskContext.Provider>
  )
}

export function useTask() {
  const context = useContext(TaskContext)
  if (context === undefined) {
    throw new Error('useTask must be used within a TaskProvider')
  }
  return context
}