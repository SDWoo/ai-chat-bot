import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { MessageSquare, Trash2 } from 'lucide-react'
import { conversationService } from '@/services/api'
import { useChatStore } from '@/store/chatStore'
import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import ConfirmDialog from './ConfirmDialog'
import { ConversationListSkeleton } from './Skeleton'

export default function ConversationList() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const location = useLocation()
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

  const handleSelectConversation = async (sessionId: string) => {
    try {
      const messages = await conversationService.getMessages(sessionId)
      loadConversation(sessionId, messages)
      
      // 채팅 페이지가 아닌 경우 자동으로 이동
      if (location.pathname !== '/') {
        navigate('/')
      }
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

  if (isLoading) {
    return <ConversationListSkeleton />
  }

  if (!conversations || conversations.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 px-4 text-center">
        <div className="w-12 h-12 bg-gray-100 dark:bg-gray-800 rounded-xl flex items-center justify-center mb-3">
          <MessageSquare size={24} className="text-gray-400 dark:text-gray-600" strokeWidth={1.5} />
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-500 leading-relaxed">
          대화 기록이 없습니다<br />새 대화를 시작해보세요
        </p>
      </div>
    )
  }

  return (
    <>
      <div className="space-y-1 max-h-[300px] overflow-y-auto">
        {conversations.slice(0, 10).map((conv) => (
          <button
            key={conv.id}
            onClick={() => handleSelectConversation(conv.session_id)}
            className={`
              group relative w-full text-left px-4 py-2.5 rounded-lg
              transition-all duration-200
              flex items-center gap-2 min-h-[44px]
              ${
                conv.session_id === conversationId
                  ? 'bg-primary-50 dark:bg-primary-500/10 text-primary-500 dark:text-primary-400 font-semibold'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'
              }
            `}
          >
            <MessageSquare size={14} className="flex-shrink-0" />
            <span className="flex-1 text-sm truncate">{conv.title || '제목 없음'}</span>
            <button
              onClick={(e) => handleDeleteConversation(conv.session_id, conv.id, e)}
              className="opacity-0 group-hover:opacity-100 min-w-[32px] min-h-[32px] flex items-center justify-center hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-all"
              aria-label="대화 삭제"
            >
              <Trash2 size={14} className="text-red-500 dark:text-red-400" />
            </button>
          </button>
        ))}
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
