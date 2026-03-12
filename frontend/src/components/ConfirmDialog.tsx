import { useEffect } from 'react'
import { createPortal } from 'react-dom'

interface ConfirmDialogProps {
  title: string
  message: string
  onConfirm: () => void
  onCancel: () => void
  isOpen: boolean
}

export default function ConfirmDialog({
  title,
  message,
  onConfirm,
  onCancel,
  isOpen,
}: ConfirmDialogProps) {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  if (!isOpen) return null

  return createPortal(
    <div 
      className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-[100] animate-fade-in"
      onClick={onCancel}
      style={{ left: 0, top: 0 }}
    >
      <div 
        className="bg-white dark:bg-gray-800 rounded-2xl p-6 max-w-sm w-full mx-4 shadow-xl animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-lg font-bold mb-2 text-[#191f28] dark:text-white" style={{ letterSpacing: '-0.02em' }}>
          {title}
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-6 leading-relaxed">
          {message}
        </p>
        <div className="flex gap-3">
          <button 
            onClick={onCancel}
            className="flex-1 px-4 py-3 rounded-xl bg-gray-100 dark:bg-gray-700 text-[#191f28] dark:text-white font-semibold hover:bg-gray-200 dark:hover:bg-gray-600 active:scale-95 transition-all"
          >
            취소
          </button>
          <button 
            onClick={onConfirm}
            className="flex-1 px-4 py-3 rounded-xl bg-primary-500 text-white font-semibold hover:bg-primary-600 active:bg-primary-700 active:scale-95 transition-all shadow-sm hover:shadow-md"
          >
            확인
          </button>
        </div>
      </div>
    </div>,
    document.body
  )
}
