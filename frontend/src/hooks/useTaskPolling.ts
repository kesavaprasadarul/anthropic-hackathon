import { useState, useEffect, useRef } from 'react'

export interface TaskUpdate {
  status: 'queued' | 'calling' | 'awaiting_input' | 'completed' | 'failed'
  task?: {
    id?: string
    type?: 'reservation' | 'reschedule' | 'cancel' | 'info'
    title?: string
    description?: string
    status?: 'queued' | 'calling' | 'awaiting_input' | 'completed' | 'failed'
    createdAt?: string
    scheduledFor?: string
    location?: string
    participants?: number
    outcome?: string
  }
}

interface UseTaskPollingResult {
  taskUpdate: TaskUpdate | null
  error: string | null
  isPolling: boolean
}

export function useTaskPolling(processId: string | null): UseTaskPollingResult {
  const [taskUpdate, setTaskUpdate] = useState<TaskUpdate | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isPolling, setIsPolling] = useState(false)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  const fetchTaskStatus = async (id: string) => {
    try {
      console.log(`[POLLING] Fetching status for process ID: ${id}`)
      const response = await fetch(`http://localhost:80/status/${id}`)
      
      if (!response.ok) {
        console.log(`[POLLING] HTTP Error: ${response.status} ${response.statusText}`)
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      console.log(`[POLLING] Received data:`, data)
      setTaskUpdate(data)
      setError(null)
      
      // Stop polling if task is completed or failed
      if (data.status === 'completed' || data.status === 'failed') {
        console.log(`[POLLING] Task finished with status: ${data.status}. Stopping polling.`)
        setIsPolling(false)
        if (intervalRef.current) {
          clearInterval(intervalRef.current)
          intervalRef.current = null
        }
      }
    } catch (err) {
      console.error('[POLLING] Error fetching task status:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
    }
  }

  useEffect(() => {
    if (!processId) {
      // No processId yet → don’t start polling
      return
    }
  
    console.log("Starting polling for processId:", processId)
    setIsPolling(true)
    console.log(processId)
  
    // Call once immediately
    fetchTaskStatus(processId)
  
    // Poll every second
    intervalRef.current = setInterval(() => {
      console.log("Polling...")
      fetchTaskStatus(processId)
    }, 1000)
  }, [processId])

  return {
    taskUpdate,
    error,
    isPolling
  }
}