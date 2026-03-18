import { useState, useRef, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Send, ThumbsUp, ThumbsDown, MessageSquare, BookmarkPlus, Loader2, FileCode2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import { useChatStore } from '@/store/chatStore'
import { chatService, conversationService, Message } from '@/services/api'
import SqlPreviewModal from '@/components/SqlPreviewModal'

export default function ChatPage() {
  const [input, setInput] = useState('')
  const [processingStatus, setProcessingStatus] = useState<string>('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [_streamingMessageId, setStreamingMessageId] = useState<number | null>(null)
  const [retryCount, setRetryCount] = useState(0)
  const [sqlPreview, setSqlPreview] = useState<{ isOpen: boolean; documentId: number | null; filename: string }>({
    isOpen: false, documentId: null, filename: '',
  })
  const [searchSources, setSearchSources] = useState<string[]>(['documents', 'knowledge'])
  const [extractingKnowledge, setExtractingKnowledge] = useState(false)
  const [feedbackStates, setFeedbackStates] = useState<Record<number, 'positive' | 'negative' | null>>({})
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const prevMessagesLengthRef = useRef(0)
  const { messages, conversationId, isLoading, addMessage, updateMessage, setConversationId, setIsLoading } = useChatStore()

  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    messagesEndRef.current?.scrollIntoView({ behavior, block: 'end' })
  }

  // 새 메시지 추가 시 스크롤
  useEffect(() => {
    if (messages.length > prevMessagesLengthRef.current) {
      scrollToBottom('smooth')
    }
    prevMessagesLengthRef.current = messages.length
  }, [messages.length])

  // 스트리밍 중에는 내용이 늘어날 때마다 스크롤이 따라가도록
  const lastMessage = messages[messages.length - 1]
  useEffect(() => {
    if (isStreaming && lastMessage?.role === 'assistant' && lastMessage?.content) {
      scrollToBottom('smooth')
    }
  }, [isStreaming, lastMessage?.content])

  // 스트리밍 완료 시 한 번 더 스크롤
  useEffect(() => {
    if (!isStreaming && messages.length > 0) {
      scrollToBottom('smooth')
    }
  }, [isStreaming])

  const sendMessageMutation = useMutation({
    mutationFn: async (message: string) => {
      const userMessage: Message = {
        id: Date.now(),
        role: 'user',
        content: message,
        created_at: new Date().toISOString(),
      }
      addMessage(userMessage)
      setIsLoading(true)
      setIsStreaming(true)
      
      setProcessingStatus('문서 검색 중...')
      
      try {
        const assistantMessageId = Date.now() + 1
        const assistantMessage: Message = {
          id: assistantMessageId,
          role: 'assistant',
          content: '',
          created_at: new Date().toISOString(),
        }
        addMessage(assistantMessage)
        setStreamingMessageId(assistantMessageId)

        // 재시도 시에도 동일한 conversation_id 사용 (중복 대화창 방지)
        const conversationIdToUse = conversationId || crypto.randomUUID()
        if (!conversationId) {
          setConversationId(conversationIdToUse)
        }
        let sources: any[] = []
        let fullContent = ''

        setTimeout(() => {
          setProcessingStatus('답변 생성 중...')
        }, 500)

        for await (const chunk of chatService.sendMessageStream(
          {
            message,
            conversation_id: conversationIdToUse,
            top_k: 4,
            search_sources: searchSources,
          },
          {
            maxRetries: 3,
            retryDelay: 1000,
            onRetry: (attempt, error) => {
              console.log(`Retrying... Attempt ${attempt}/3`, error)
              setRetryCount(attempt)
              setProcessingStatus(`연결 재시도 중... (${attempt}/3)`)
            },
          }
        )) {
          if (chunk.type === 'metadata') {
            if (chunk.conversation_id) {
              setConversationId(chunk.conversation_id)
            }
            if (chunk.sources) {
              sources = chunk.sources
            }
            setProcessingStatus('답변 생성 중...')
          } else if (chunk.type === 'content' && chunk.content) {
            fullContent += chunk.content
            updateMessage(assistantMessageId, {
              content: fullContent,
            })
          } else if (chunk.type === 'done') {
            updateMessage(assistantMessageId, {
              content: fullContent,
              sources,
            })
            setProcessingStatus('')
          } else if (chunk.type === 'error') {
            throw new Error(chunk.message || 'Streaming error')
          }
        }

        setIsLoading(false)
        setIsStreaming(false)
        setStreamingMessageId(null)
        setRetryCount(0)
      } catch (error) {
        console.error('Streaming error:', error)
        setIsLoading(false)
        setIsStreaming(false)
        setStreamingMessageId(null)
        setRetryCount(0)
        setProcessingStatus('')
        
        const errorMessage: Message = {
          id: Date.now() + 2,
          role: 'assistant',
          content: '죄송합니다. 응답을 생성하는 중 오류가 발생했습니다. 다시 시도해주세요.',
          created_at: new Date().toISOString(),
        }
        addMessage(errorMessage)
        
        throw error
      }
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    sendMessageMutation.mutate(input)
    setInput('')
  }

  const handleFeedback = async (messageId: number, feedback: 'positive' | 'negative') => {
    try {
      await conversationService.submitFeedback(messageId, feedback)
      setFeedbackStates(prev => ({ ...prev, [messageId]: feedback }))
    } catch (error) {
      console.error('Failed to submit feedback:', error)
    }
  }

  const handleExtractKnowledge = async () => {
    if (!conversationId) {
      alert('대화 ID가 없습니다.')
      return
    }

    try {
      setExtractingKnowledge(true)
      const result = await conversationService.extractKnowledge(conversationId)
      alert(`지식이 성공적으로 추출되었습니다!\n\n제목: ${result.title}\n카테고리: ${result.category}\n상태: 검토 대기 (draft)`)
    } catch (error: any) {
      console.error('Failed to extract knowledge:', error)
      const errorMsg = error.response?.data?.detail || '지식 추출에 실패했습니다.'
      alert(`오류: ${errorMsg}`)
    } finally {
      setExtractingKnowledge(false)
    }
  }

  const handleSourceToggle = (source: string) => {
    setSearchSources((prev) => {
      if (prev.includes(source)) {
        const next = prev.filter((s) => s !== source)
        return next.length > 0 ? next : prev
      }
      return [...prev, source]
    })
  }

  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-dark-bg transition-colors duration-200">
      <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden px-4 md:px-6 py-6 md:py-8" style={{ scrollBehavior: 'smooth' }}>
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-12 md:py-20 animate-slide-up">
              <div className="w-16 h-16 md:w-20 md:h-20 bg-gradient-to-br from-primary-500 to-primary-600 rounded-3xl mx-auto mb-4 md:mb-6 flex items-center justify-center shadow-soft-lg">
                <MessageSquare size={32} className="md:w-10 md:h-10 text-white" strokeWidth={2} />
              </div>
              <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-2 md:mb-3" style={{ letterSpacing: '-0.02em' }}>
                Sindoh AI에 오신 것을 환영합니다
              </h2>
              <p className="text-base md:text-[17px] text-gray-600 dark:text-gray-400 leading-relaxed px-4">
                업로드한 문서에 대해 무엇이든 물어보세요
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-slide-up`}
              >
                <div
                  className={`max-w-full md:max-w-3xl transition-all duration-200 ${
                    message.role === 'user'
                      ? 'bg-primary-50 dark:bg-primary-500/10 text-gray-900 dark:text-white rounded-2xl px-4 py-3 border border-primary-100 dark:border-primary-500/20'
                      : 'text-gray-900 dark:text-gray-100 px-1 py-2 md:px-2'
                  }`}
                >
                  {/* 응답 생성 중일 때 타이핑 애니메이션 표시 */}
                  {message.role === 'assistant' && isStreaming && message.content === '' && (
                    <div className="flex items-center gap-2 py-2">
                      <div className="flex space-x-1.5">
                        <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }}></div>
                        <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }}></div>
                      </div>
                      <span className={`text-sm font-medium text-gray-600 dark:text-gray-400 ${retryCount > 0 ? 'text-orange-600 dark:text-orange-400' : ''}`}>
                        {processingStatus || '답변 생성 중...'}
                      </span>
                    </div>
                  )}
                  
                  <div className={`markdown-content ${message.role === 'user' ? 'markdown-content-user' : ''}`}>
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]} 
                      rehypePlugins={[rehypeHighlight]}
                    >
                      {message.content}
                    </ReactMarkdown>
                  </div>

                  {message.sources && message.sources.length > 0 && message.sources.some((s: { content?: string }) => s?.content) && (
                    <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700/50">
                      <p className="text-sm font-bold text-gray-900 dark:text-white mb-3">📄 참고 문서</p>
                      <div className="space-y-2">
                        {message.sources
                          .filter((s: { content?: string }) => s?.content)
                          .map((source: { source?: string; page?: string; content?: string; file_type?: string; document_id?: number; sql_type?: string }, idx: number) => {
                            const isSql = source.file_type === '.sql'
                            const canPreview = isSql && source.document_id
                            return (
                              <div
                                key={idx}
                                className={`text-sm p-3 bg-[#f9fafb] dark:bg-gray-900 rounded-xl border border-gray-100 dark:border-gray-700 transition-all ${
                                  canPreview ? 'cursor-pointer hover:border-primary-300 dark:hover:border-primary-500/40 hover:shadow-sm' : ''
                                }`}
                                onClick={() => {
                                  if (canPreview && source.document_id) {
                                    setSqlPreview({ isOpen: true, documentId: source.document_id, filename: source.source || 'SQL' })
                                  }
                                }}
                              >
                                <p className="font-semibold text-gray-900 dark:text-white mb-1 flex items-center gap-1.5 min-w-0" title={source.source}>
                                  {isSql && <FileCode2 size={14} className="text-emerald-500 shrink-0" />}
                                  <span className="truncate">{source.source}</span>
                                  {source.page && source.page !== 'N/A' && (
                                    <span className="text-gray-500 dark:text-gray-400 shrink-0">• p.{source.page}</span>
                                  )}
                                  {isSql && source.sql_type && (
                                    <span className="text-xs px-1.5 py-0.5 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 rounded-md shrink-0 font-medium">
                                      {source.sql_type}
                                    </span>
                                  )}
                                  {canPreview && (
                                    <span className="text-xs text-primary-500 shrink-0 font-medium ml-auto">미리보기</span>
                                  )}
                                </p>
                                <p className="text-gray-600 dark:text-gray-400 text-xs leading-relaxed">
                                  {source.content}...
                                </p>
                              </div>
                            )
                          })}
                      </div>
                    </div>
                  )}

                  {message.role === 'assistant' && (
                    <div className="flex gap-2 mt-4 pt-3 border-t border-gray-100 dark:border-gray-700/50">
                      <button
                        onClick={() => handleFeedback(message.id, 'positive')}
                        className={`touch-target p-2 hover:bg-green-50 dark:hover:bg-green-900/20 active:bg-green-100 dark:active:bg-green-900/30 rounded-lg transition-all group ${
                          feedbackStates[message.id] === 'positive' ? 'bg-green-50 dark:bg-green-900/20' : ''
                        }`}
                      >
                        <ThumbsUp 
                          size={18} 
                          className={`transition-all ${
                            feedbackStates[message.id] === 'positive' 
                              ? 'text-green-600 dark:text-green-400 fill-current' 
                              : 'text-gray-500 dark:text-gray-400 group-hover:text-green-600 dark:group-hover:text-green-400 group-hover:scale-110'
                          }`} 
                        />
                      </button>
                      <button
                        onClick={() => handleFeedback(message.id, 'negative')}
                        className={`touch-target p-2 hover:bg-red-50 dark:hover:bg-red-900/20 active:bg-red-100 dark:active:bg-red-900/30 rounded-lg transition-all group ${
                          feedbackStates[message.id] === 'negative' ? 'bg-red-50 dark:bg-red-900/20' : ''
                        }`}
                      >
                        <ThumbsDown 
                          size={18} 
                          className={`transition-all ${
                            feedbackStates[message.id] === 'negative' 
                              ? 'text-red-600 dark:text-red-400 fill-current' 
                              : 'text-gray-500 dark:text-gray-400 group-hover:text-red-600 dark:group-hover:text-red-400 group-hover:scale-110'
                          }`} 
                        />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="border-t border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900 px-4 md:px-6 py-4 md:py-5 shadow-sm transition-colors duration-200">
        {/* 지식으로 저장 버튼 */}
        {conversationId && Object.values(feedbackStates).some(f => f === 'positive') && (
          <div className="max-w-4xl mx-auto mb-3">
            <button
              onClick={handleExtractKnowledge}
              disabled={extractingKnowledge}
              className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-xl hover:bg-primary-600 active:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-400 disabled:opacity-50 disabled:cursor-not-allowed font-bold text-sm shadow-soft transition-all hover:shadow-soft-lg"
            >
              {extractingKnowledge ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>지식 추출 중...</span>
                </>
              ) : (
                <>
                  <BookmarkPlus size={16} />
                  <span>지식으로 저장</span>
                </>
              )}
            </button>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
              긍정 피드백을 받은 답변에서 지식을 자동으로 추출합니다.
            </p>
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="mb-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-semibold text-gray-900 dark:text-white">검색 소스:</span>
              {[
                { id: 'documents', label: '문서', icon: '📄' },
                { id: 'knowledge', label: '지식베이스', icon: '💡' },
                { id: 'web', label: '웹 검색', icon: '🌐' },
              ].map(({ id, label, icon }) => {
                const isActive = searchSources.includes(id)
                return (
                  <button
                    key={id}
                    type="button"
                    onClick={() => handleSourceToggle(id)}
                    disabled={isLoading}
                    className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed ${
                      isActive
                        ? 'bg-primary-50 dark:bg-primary-500/20 text-primary-600 dark:text-primary-300 border border-primary-200 dark:border-primary-500/40 hover:bg-primary-100 dark:hover:bg-primary-500/30'
                        : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border border-transparent hover:bg-gray-200 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-gray-200'
                    }`}
                  >
                    <span>{icon}</span>
                    <span>{label}</span>
                  </button>
                )
              })}
            </div>
          </div>
          
          <div className="relative">
            <div className="flex gap-2 md:gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="메시지를 입력하세요"
                disabled={isLoading}
                className="flex-1 px-4 md:px-5 py-3 md:py-4 bg-gray-100 dark:bg-gray-800 border-none rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 disabled:opacity-50 font-medium text-sm md:text-[15px] transition-all"
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="px-5 md:px-7 py-3 md:py-4 bg-primary-500 text-white rounded-2xl hover:bg-primary-600 active:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-400 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-bold shadow-soft transition-all hover:shadow-soft-lg active:scale-95"
              >
                <Send size={18} className="md:w-5 md:h-5" strokeWidth={2.5} />
                <span className="hidden md:inline">전송</span>
              </button>
            </div>
          </div>
        </form>
      </div>

      <SqlPreviewModal
        isOpen={sqlPreview.isOpen}
        documentId={sqlPreview.documentId}
        filename={sqlPreview.filename}
        onClose={() => setSqlPreview({ isOpen: false, documentId: null, filename: '' })}
      />
    </div>
  )
}
