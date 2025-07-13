'use client'

import React, { useEffect } from 'react'

export interface ToastMessage {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
}

interface ToastProps {
  message: ToastMessage
  onRemove: (id: string) => void
}

const Toast: React.FC<ToastProps> = ({ message, onRemove }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onRemove(message.id)
    }, message.duration || 5000)

    return () => clearTimeout(timer)
  }, [message.id, message.duration, onRemove])

  const getToastStyles = () => {
    const baseStyles = "mb-4 p-4 rounded-lg shadow-lg border-l-4 transition-all duration-300"
    
    switch (message.type) {
      case 'success':
        return `${baseStyles} bg-green-50 border-green-400 text-green-800`
      case 'error':
        return `${baseStyles} bg-red-50 border-red-400 text-red-800`
      case 'warning':
        return `${baseStyles} bg-yellow-50 border-yellow-400 text-yellow-800`
      case 'info':
        return `${baseStyles} bg-blue-50 border-blue-400 text-blue-800`
      default:
        return `${baseStyles} bg-gray-50 border-gray-400 text-gray-800`
    }
  }

  const getIcon = () => {
    switch (message.type) {
      case 'success':
        return '✅'
      case 'error':
        return '❌'
      case 'warning':
        return '⚠️'
      case 'info':
        return 'ℹ️'
      default:
        return '📢'
    }
  }

  return (
    <div className={getToastStyles()}>
      <div className="flex items-start">
        <div className="text-xl mr-3">{getIcon()}</div>
        <div className="flex-1">
          <div className="font-semibold">{message.title}</div>
          {message.message && (
            <div className="mt-1 text-sm opacity-90">{message.message}</div>
          )}
        </div>
        <button
          onClick={() => onRemove(message.id)}
          className="ml-4 text-gray-400 hover:text-gray-600 transition-colors"
        >
          ✕
        </button>
      </div>
    </div>
  )
}

interface ToastContainerProps {
  messages: ToastMessage[]
  onRemove: (id: string) => void
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ messages, onRemove }) => {
  if (messages.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-50 w-96 max-w-full">
      {messages.map((message) => (
        <Toast key={message.id} message={message} onRemove={onRemove} />
      ))}
    </div>
  )
}

export default Toast