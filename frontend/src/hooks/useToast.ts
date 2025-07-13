'use client'

import { useState, useCallback } from 'react'
import { ToastMessage } from '@/components/Toast'

export const useToast = () => {
  const [messages, setMessages] = useState<ToastMessage[]>([])

  const addToast = useCallback((
    type: ToastMessage['type'],
    title: string,
    message?: string,
    duration?: number
  ) => {
    const id = Math.random().toString(36).substr(2, 9)
    const newToast: ToastMessage = {
      id,
      type,
      title,
      message,
      duration
    }

    setMessages(prev => [...prev, newToast])
    return id
  }, [])

  const removeToast = useCallback((id: string) => {
    setMessages(prev => prev.filter(msg => msg.id !== id))
  }, [])

  const clearAllToasts = useCallback(() => {
    setMessages([])
  }, [])

  // Convenience methods
  const success = useCallback((title: string, message?: string, duration?: number) => {
    return addToast('success', title, message, duration)
  }, [addToast])

  const error = useCallback((title: string, message?: string, duration?: number) => {
    return addToast('error', title, message, duration || 8000) // Longer duration for errors
  }, [addToast])

  const warning = useCallback((title: string, message?: string, duration?: number) => {
    return addToast('warning', title, message, duration)
  }, [addToast])

  const info = useCallback((title: string, message?: string, duration?: number) => {
    return addToast('info', title, message, duration)
  }, [addToast])

  return {
    messages,
    addToast,
    removeToast,
    clearAllToasts,
    success,
    error,
    warning,
    info
  }
}