import { X } from 'lucide-react'

interface ConfirmModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  variant?: 'danger' | 'primary'
}

export default function ConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = '확인',
  cancelText = '취소',
  variant = 'danger',
}: ConfirmModalProps) {
  if (!isOpen) return null

  const handleConfirm = () => {
    onConfirm()
    onClose()
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 dark:bg-black/70 animate-fade-in"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-sm w-full p-6 animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 헤더 */}
        <div className="flex items-start justify-between mb-4">
          <h3 className="text-xl font-bold text-[#191f28] dark:text-white" style={{ letterSpacing: '-0.02em' }}>
            {title}
          </h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-50 dark:hover:bg-gray-800 active:bg-gray-100 dark:active:bg-gray-700 rounded-lg transition-colors"
            aria-label="닫기"
          >
            <X size={20} className="text-[#8b95a1] dark:text-gray-400" />
          </button>
        </div>

        {/* 메시지 */}
        <p className="text-[15px] text-[#4e5968] dark:text-gray-300 leading-relaxed mb-6">
          {message}
        </p>

        {/* 버튼 */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-3 bg-[#f2f4f6] dark:bg-gray-800 text-[#191f28] dark:text-white rounded-xl hover:bg-[#e5e8eb] dark:hover:bg-gray-700 active:bg-[#d1d5db] dark:active:bg-gray-600 transition-all font-semibold focus:outline-none focus:ring-2 focus:ring-gray-400"
          >
            {cancelText}
          </button>
          <button
            onClick={handleConfirm}
            className={`flex-1 px-4 py-3 rounded-xl transition-all font-semibold focus:outline-none focus:ring-2 ${
              variant === 'danger'
                ? 'bg-[#f44336] hover:bg-[#d32f2f] active:bg-[#c62828] text-white focus:ring-red-400'
                : 'bg-primary-500 hover:bg-primary-600 active:bg-primary-700 text-white focus:ring-primary-400'
            }`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}
