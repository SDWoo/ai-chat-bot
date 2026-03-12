import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { MessageSquare, Plus, Trash2, Clock } from 'lucide-react'
import { conversationService } from '@/services/api'
import { useChatStore } from '@/store/chatStore'
import ConfirmDialog from './ConfirmDialog'

export default function ChatHistory() {
  const queryClient = useQueryClient()
  const { conversationId, clearChat, loadConversation } = useChatStore()
  const [deleteDialogState, setDeleteDialogState] = useState<{
    isOpen: boolean
    sessionId: string | null
    convId: number | null
  }>({
    isOpen: false,
    sessionId: null,
    convId: null,
  })

  const { data: conversations, isLoading } = useQuery({
    queryKey: ['conversations'],
    queryFn: conversationService.listConversations,
    refetchInterval: 5000,
  })

  const deleteConversationMutation = useMutation({
    mutationFn: conversationService.deleteConversation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })

  const handleNewChat = () => {
    clearChat()
  }

  const handleSelectConversation = async (sessionId: string) => {
    try {
      const messages = await conversationService.getMessages(sessionId)
      loadConversation(sessionId, messages)
    } catch (error) {
      console.error('Failed to load conversation:', error)
    }
  }

  const handleDeleteConversation = (sessionId: string, convId: number, e: React.MouseEvent) => {
    e.stopPropagation()
    setDeleteDialogState({
      isOpen: true,
      sessionId,
      convId,
    })
  }

  const confirmDelete = async () => {
    if (deleteDialogState.sessionId) {
      await deleteConversationMutation.mutateAsync(deleteDialogState.sessionId)
      if (conversationId === deleteDialogState.sessionId) {
        clearChat()
      }
    }
    setDeleteDialogState({ isOpen: false, sessionId: null, convId: null })
  }

  const cancelDelete = () => {
    setDeleteDialogState({ isOpen: false, sessionId: null, convId: null })
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)

    if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}시간 전`
    } else if (diffInHours < 48) {
      return '어제'
    } else {
      return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })
    }
  }

  return (
    <>
      <div className="flex flex-col h-full bg-white dark:bg-gray-900 transition-colors duration-200">
        <div className="p-4 border-b border-gray-200 dark:border-gray-800">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary-500 text-white rounded-xl hover:bg-primary-600 active:bg-primary-700 transition-all font-bold shadow-sm hover:shadow-md active:scale-95 min-h-[44px]"
          >
            <Plus size={20} strokeWidth={2.5} />
            새 대화
          </button>
        </div>

        <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-800">
          <h3 className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            이전 대화
          </h3>
        </div>

        <div className="flex-1 overflow-y-auto p-3">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-8 text-gray-500 dark:text-gray-400">
              <div className="w-8 h-8 border-3 border-primary-500 border-t-transparent rounded-full animate-spin mb-3"></div>
              <p className="text-sm font-medium">로딩 중...</p>
            </div>
          ) : conversations && conversations.length > 0 ? (
            <div className="space-y-1">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => handleSelectConversation(conv.session_id)}
                  className={`group relative px-3 py-3 rounded-lg cursor-pointer transition-all ${
                    conv.session_id === conversationId
                      ? 'bg-primary-50 dark:bg-primary-500/10 border-l-4 border-primary-500'
                      : 'hover:bg-[#f9fafb] dark:hover:bg-gray-800 border-l-4 border-transparent'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <MessageSquare
                      size={16}
                      className={`mt-1 flex-shrink-0 ${
                        conv.session_id === conversationId 
                          ? 'text-primary-500' 
                          : 'text-gray-500 dark:text-gray-400'
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <p
                        className={`text-sm font-semibold truncate ${
                          conv.session_id === conversationId 
                            ? 'text-primary-500' 
                            : 'text-[#191f28] dark:text-white'
                        }`}
                      >
                        {conv.title || '제목 없음'}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <Clock size={12} className="text-gray-500 dark:text-gray-400" />
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {formatDate(conv.updated_at || conv.created_at)}
                        </p>
                        <span className="text-xs text-gray-500 dark:text-gray-400">•</span>
                        <p className="text-xs text-gray-500 dark:text-gray-400">{conv.message_count}개 메시지</p>
                      </div>
                    </div>
                    <button
                      onClick={(e) => handleDeleteConversation(conv.session_id, conv.id, e)}
                      className="opacity-0 group-hover:opacity-100 min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-red-50 dark:hover:bg-red-900/20 active:bg-red-100 dark:active:bg-red-900/30 rounded-lg transition-all md:opacity-100 lg:opacity-0"
                      aria-label="대화 삭제"
                    >
                      <Trash2 size={16} className="text-red-500 dark:text-red-400" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
              <MessageSquare size={48} className="text-gray-300 dark:text-gray-700 mb-3" strokeWidth={1.5} />
              <p className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-1">대화 기록 없음</p>
              <p className="text-xs text-gray-500 dark:text-gray-500 leading-relaxed">
                새 대화를 시작해보세요
              </p>
            </div>
          )}
        </div>

        <div className="p-4 border-t border-gray-100 dark:border-gray-800 bg-[#f9fafb] dark:bg-gray-900/50 transition-colors">
          <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
            <p className="font-medium">Sindoh AI</p>
          </div>
        </div>
      </div>

      <ConfirmDialog
        isOpen={deleteDialogState.isOpen}
        title="대화 삭제"
        message="이 대화를 삭제하시겠습니까? 삭제된 대화는 복구할 수 없습니다."
        onConfirm={confirmDelete}
        onCancel={cancelDelete}
      />
    </>
  )
}
