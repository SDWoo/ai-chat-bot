import { useEffect } from 'react'
import { CheckCircle, XCircle, AlertCircle, Info, X } from 'lucide-react'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

interface ToastProps {
  id: string
  type: ToastType
  message: string
  duration?: number
  onClose: (id: string) => void
}

export default function Toast({ id, type, message, duration = 5000, onClose }: ToastProps) {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        onClose(id)
      }, duration)
      return () => clearTimeout(timer)
    }
  }, [id, duration, onClose])

  const getIcon = () => {
    switch (type) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500 dark:text-green-400 flex-shrink-0" />
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500 dark:text-red-400 flex-shrink-0" />
      case 'warning':
        return <AlertCircle className="w-5 h-5 text-orange-500 dark:text-orange-400 flex-shrink-0" />
      case 'info':
        return <Info className="w-5 h-5 text-blue-500 dark:text-blue-400 flex-shrink-0" />
    }
  }

  const getStyles = () => {
    switch (type) {
      case 'success':
        return 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
      case 'error':
        return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
      case 'warning':
        return 'bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800'
      case 'info':
        return 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800'
    }
  }

  return (
    <div
      className={`
        flex items-start gap-3 p-4 rounded-xl border shadow-lg
        animate-slide-up transition-all duration-300
        min-w-[320px] max-w-md
        ${getStyles()}
      `}
      role="alert"
    >
      {getIcon()}
      <p className="flex-1 text-sm font-medium text-[#191f28] dark:text-white leading-relaxed">
        {message}
      </p>
      <button
        onClick={() => onClose(id)}
        className="min-w-[32px] min-h-[32px] -mt-1 -mr-1 flex items-center justify-center hover:bg-black/5 dark:hover:bg-white/5 rounded-lg transition-colors"
        aria-label="닫기"
      >
        <X className="w-4 h-4 text-[#8b95a1] dark:text-gray-400" />
      </button>
    </div>
  )
}
