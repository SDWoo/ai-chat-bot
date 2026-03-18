import { useCallback, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, FileCode2, Trash2, CheckCircle, Clock, XCircle, Loader2, Eye } from 'lucide-react'
import { documentService, Document } from '@/services/api'
import { DocumentListSkeleton } from '@/components/Skeleton'
import EmptyState from '@/components/EmptyState'
import ConfirmDialog from '@/components/ConfirmDialog'
import SqlPreviewModal from '@/components/SqlPreviewModal'

export default function DocumentsPage() {
  const queryClient = useQueryClient()
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [deleteTarget, setDeleteTarget] = useState<Document | null>(null)
  const [sqlPreview, setSqlPreview] = useState<{ isOpen: boolean; documentId: number | null; filename: string }>({
    isOpen: false, documentId: null, filename: '',
  })

  const { data: documents, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: documentService.listDocuments,
    refetchInterval: 5000,
  })

  const uploadMutation = useMutation({
    mutationFn: documentService.uploadDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      setUploadProgress(100)
      setTimeout(() => {
        setUploading(false)
        setUploadProgress(0)
      }, 500)
    },
    onError: () => {
      setUploading(false)
      setUploadProgress(0)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: documentService.deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setUploading(true)
      setUploadProgress(0)
      
      // 프로그레스 시뮬레이션
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + Math.random() * 15
        })
      }, 200)
      
      uploadMutation.mutate(acceptedFiles[0])
    }
  }, [uploadMutation])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt', '.sql'],
      'text/markdown': ['.md'],
      'text/csv': ['.csv'],
    },
    maxFiles: 1,
    disabled: uploading,
  })

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="text-green-500" size={20} />
      case 'processing':
        return <Clock className="text-yellow-500 animate-spin" size={20} />
      case 'failed':
        return <XCircle className="text-red-500" size={20} />
      default:
        return <FileText size={20} />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return '완료'
      case 'processing':
        return '처리 중...'
      case 'failed':
        return '실패'
      default:
        return status
    }
  }

  return (
    <div className="h-full overflow-y-auto p-4 md:p-6 lg:p-8 bg-[#f9fafb] dark:bg-[#1a1a1a]" style={{ WebkitOverflowScrolling: 'touch' }}>
      <div className="max-w-6xl mx-auto animate-slide-up">
        <div className="mb-6 md:mb-8">
          <h1 className="text-2xl md:text-3xl font-bold text-[#191f28] dark:text-white mb-2" style={{ letterSpacing: '-0.02em' }}>
            문서 관리
          </h1>
          <p className="text-[#4e5968] dark:text-gray-400 text-sm md:text-[17px]">AI가 학습할 문서를 업로드하고 관리하세요</p>
        </div>

        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-2xl md:rounded-3xl p-8 md:p-12 text-center cursor-pointer transition-all mb-6 md:mb-8 bg-white dark:bg-gray-900 ${
            isDragActive
              ? 'border-primary-500 bg-primary-50 dark:bg-primary-500/10 scale-[1.01]'
              : 'border-gray-200 dark:border-gray-700 hover:border-primary-500 hover:shadow-soft-lg'
          } ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          <input {...getInputProps()} />
          <div className="w-14 h-14 md:w-16 md:h-16 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl md:rounded-2xl mx-auto mb-3 md:mb-4 flex items-center justify-center shadow-soft">
            {uploading ? (
              <Loader2 className="text-white animate-spin" size={28} strokeWidth={2} />
            ) : (
              <Upload className="text-white" size={28} strokeWidth={2} />
            )}
          </div>
          {uploading ? (
            <div className="space-y-3 md:space-y-4">
              <p className="text-base md:text-lg font-bold text-[#191f28] dark:text-white mb-2">
                업로드 중... {Math.round(uploadProgress)}%
              </p>
              <div className="w-full max-w-md mx-auto h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-primary-500 to-primary-600 transition-all duration-300 ease-out"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-xs md:text-sm text-gray-600 dark:text-gray-400 animate-pulse">
                문서를 처리하고 있습니다. 잠시만 기다려주세요.
              </p>
            </div>
          ) : isDragActive ? (
            <p className="text-base md:text-lg font-bold text-primary-500">
              파일을 여기에 놓으세요
            </p>
          ) : (
            <div>
              <p className="text-base md:text-lg font-bold text-[#191f28] dark:text-white mb-2">
                파일을 드래그하거나 클릭하여 업로드
              </p>
              <p className="text-xs md:text-sm text-gray-600 dark:text-gray-400">
                지원 형식: PDF, DOCX, TXT, MD, CSV, SQL (최대 50MB)
              </p>
            </div>
          )}
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-2xl md:rounded-3xl shadow-soft border border-gray-100 dark:border-gray-800 overflow-hidden">
          <div className="px-4 md:px-6 py-4 md:py-5 border-b border-gray-100 dark:border-gray-800">
            <h2 className="text-lg md:text-xl font-bold text-[#191f28] dark:text-white" style={{ letterSpacing: '-0.01em' }}>
              업로드된 문서 <span className="text-primary-500">({documents?.length || 0})</span>
            </h2>
          </div>

          {isLoading ? (
            <DocumentListSkeleton />
          ) : documents && documents.length > 0 ? (
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {documents.map((doc: Document) => (
                <div
                  key={doc.id}
                  className="px-4 md:px-6 py-4 md:py-5 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-all"
                >
                  <div className="flex items-start md:items-center justify-between gap-3 md:gap-4">
                    <div className="flex items-start md:items-center gap-3 md:gap-4 flex-1 min-w-0">
                      <div className={`w-10 h-10 md:w-12 md:h-12 bg-gradient-to-br ${
                        doc.file_type === '.sql' ? 'from-emerald-500 to-teal-600' : 'from-primary-500 to-primary-600'
                      } rounded-lg md:rounded-xl flex items-center justify-center flex-shrink-0 shadow-soft`}>
                        {doc.file_type === '.sql' ? (
                          <FileCode2 className="text-white" size={20} strokeWidth={2} />
                        ) : (
                          <FileText className="text-white" size={20} strokeWidth={2} />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm md:text-[15px] font-bold text-[#191f28] dark:text-white truncate mb-1">
                          {doc.filename}
                        </h3>
                        <div className="flex flex-wrap items-center gap-2 md:gap-3 text-xs md:text-sm text-gray-600 dark:text-gray-400">
                          <span className="font-medium">{formatFileSize(doc.file_size)}</span>
                          <span className="hidden sm:inline">•</span>
                          <span className="font-medium">{doc.num_chunks}개 청크</span>
                          <span className="hidden sm:inline">•</span>
                          <span className="font-medium">
                            {new Date(doc.created_at).toLocaleDateString('ko-KR')}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-col md:flex-row items-end md:items-center gap-2 md:gap-3">
                      <div className="flex items-center gap-2 px-2.5 md:px-3 py-1.5 md:py-2 bg-gray-50 dark:bg-gray-800 rounded-lg md:rounded-xl">
                        {getStatusIcon(doc.status)}
                        <span className="text-xs md:text-sm font-bold text-[#191f28] dark:text-white whitespace-nowrap">
                          {getStatusText(doc.status)}
                        </span>
                      </div>

                      {['.sql', '.txt', '.md'].includes(doc.file_type) && doc.status === 'completed' && (
                        <button
                          onClick={() => setSqlPreview({ isOpen: true, documentId: doc.id, filename: doc.filename })}
                          className="min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 active:bg-gray-200 rounded-lg md:rounded-xl transition-all"
                          aria-label="미리보기"
                        >
                          <Eye size={18} strokeWidth={2} />
                        </button>
                      )}
                      <button
                        onClick={() => setDeleteTarget(doc)}
                        disabled={deleteMutation.isPending}
                        className="min-w-[44px] min-h-[44px] flex items-center justify-center text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 active:bg-red-100 dark:active:bg-red-900/30 rounded-lg md:rounded-xl transition-all disabled:opacity-50"
                        aria-label="문서 삭제"
                      >
                        <Trash2 size={18} strokeWidth={2} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={FileText}
              title="업로드된 문서가 없습니다"
              description="위의 드래그 앤 드롭 영역을 사용하여 첫 문서를 업로드해보세요."
            />
          )}
        </div>
      </div>

      <ConfirmDialog
        isOpen={!!deleteTarget}
        title="문서 삭제"
        message={deleteTarget ? `"${deleteTarget.filename}" 문서를 삭제하시겠습니까? 삭제된 문서는 복구할 수 없습니다.` : ''}
        onConfirm={() => {
          if (deleteTarget) {
            const id = deleteTarget.id
            setDeleteTarget(null)
            deleteMutation.mutate(id)
          }
        }}
        onCancel={() => setDeleteTarget(null)}
      />

      <SqlPreviewModal
        isOpen={sqlPreview.isOpen}
        documentId={sqlPreview.documentId}
        filename={sqlPreview.filename}
        onClose={() => setSqlPreview({ isOpen: false, documentId: null, filename: '' })}
      />
    </div>
  )
}
