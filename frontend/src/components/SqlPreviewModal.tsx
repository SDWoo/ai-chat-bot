import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { X, Copy, Check, FileCode2, Loader2 } from 'lucide-react'
import { documentService } from '@/services/api'

interface SqlPreviewModalProps {
  isOpen: boolean
  documentId: number | null
  filename: string
  onClose: () => void
}

export default function SqlPreviewModal({
  isOpen,
  documentId,
  filename,
  onClose,
}: SqlPreviewModalProps) {
  const [content, setContent] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (isOpen && documentId) {
      setLoading(true)
      setError(null)
      documentService
        .getDocumentContent(documentId)
        .then((data) => setContent(data.content))
        .catch((err) => setError(err?.response?.data?.detail || '파일을 불러올 수 없습니다.'))
        .finally(() => setLoading(false))
    }
    return () => {
      setContent('')
      setError(null)
    }
  }, [isOpen, documentId])

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

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      /* noop */
    }
  }

  if (!isOpen) return null

  return createPortal(
    <div
      className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-[100] animate-fade-in"
      onClick={onClose}
      style={{ left: 0, top: 0 }}
    >
      <div
        className="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-4xl mx-4 shadow-xl animate-slide-up flex flex-col"
        style={{ maxHeight: '85vh' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-9 h-9 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center shrink-0">
              <FileCode2 size={18} className="text-white" />
            </div>
            <div className="min-w-0">
              <h3 className="text-base font-bold text-gray-900 dark:text-white truncate">
                {filename}
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">SQL 미리보기</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {content && (
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-xl bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-all"
              >
                {copied ? (
                  <>
                    <Check size={14} /> <span>복사됨</span>
                  </>
                ) : (
                  <>
                    <Copy size={14} /> <span>복사</span>
                  </>
                )}
              </button>
            )}
            <button
              onClick={onClose}
              className="p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-700 transition-all"
            >
              <X size={20} className="text-gray-500 dark:text-gray-400" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-auto p-5">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16 text-gray-500 dark:text-gray-400">
              <Loader2 size={32} className="animate-spin mb-3" />
              <p className="text-sm font-medium">SQL 파일 로딩 중...</p>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-16 text-red-500">
              <p className="text-sm font-medium">{error}</p>
            </div>
          ) : (
            <pre className="text-sm leading-relaxed font-mono whitespace-pre-wrap break-words text-gray-800 dark:text-gray-200 bg-gray-50 dark:bg-gray-900 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
              {content}
            </pre>
          )}
        </div>
      </div>
    </div>,
    document.body
  )
}
