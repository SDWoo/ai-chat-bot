import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

export const API_URL = import.meta.env.VITE_API_URL ?? (import.meta.env.PROD ? '' : 'http://localhost:8000')

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 모든 요청에 Authorization 헤더 추가
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 401 응답 시 logout 및 /login redirect
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      if (typeof window !== 'undefined') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export interface Document {
  id: number
  filename: string
  file_type: string
  file_size: number
  num_chunks: number
  status: string
  created_at: string
  processed_at?: string
}

export interface Message {
  id: number
  role: string
  content: string
  image_url?: string
  sources?: Array<{
    content: string
    source: string
    page: string
    relevance_score: number
  }>
  feedback?: string
  created_at: string
}

export interface Conversation {
  id: number
  session_id: string
  title?: string
  created_at: string
  updated_at?: string
  message_count: number
}

export interface ChatRequest {
  message: string
  image_data?: string
  conversation_id?: string
  collection_name?: string
  top_k?: number
  search_sources?: string[]
}

export interface ChatResponse {
  conversation_id: string
  message: string
  sources: Array<{
    content: string
    source: string
    page: string
    relevance_score: number
  }>
  created_at: string
}

export const documentService = {
  async uploadDocument(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post<Document>('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  async listDocuments() {
    const response = await api.get<Document[]>('/api/documents')
    return response.data
  },

  async getDocument(id: number) {
    const response = await api.get<Document>(`/api/documents/${id}`)
    return response.data
  },

  async deleteDocument(id: number) {
    await api.delete(`/api/documents/${id}`)
  },

  async getDocumentContent(id: number) {
    const response = await api.get<{
      id: number
      filename: string
      file_type: string
      content: string
    }>(`/api/documents/${id}/content`)
    return response.data
  },
}

export const chatService = {
  async sendMessage(request: ChatRequest) {
    const response = await api.post<ChatResponse>('/api/chat', request)
    return response.data
  },

  async *sendMessageStream(
    request: ChatRequest,
    options?: {
      maxRetries?: number
      retryDelay?: number
      onRetry?: (attempt: number, error: Error) => void
    }
  ): AsyncGenerator<{
    type: string
    conversation_id?: string
    sources?: Array<{
      content: string
      source: string
      page: string
      relevance_score: number
    }>
    content?: string
    message?: string
  }> {
    const maxRetries = options?.maxRetries ?? 3
    const retryDelay = options?.retryDelay ?? 1000
    let lastError: Error | null = null

    const token = useAuthStore.getState().token
    const authHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (token) {
      authHeaders['Authorization'] = `Bearer ${token}`
    }

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const response = await fetch(`${API_URL}/api/chat/stream`, {
          method: 'POST',
          headers: authHeaders,
          body: JSON.stringify(request),
          signal: AbortSignal.timeout(120000), // 2 minute timeout
        })

        if (response.status === 401) {
          useAuthStore.getState().logout()
          if (typeof window !== 'undefined') {
            window.location.href = '/login'
          }
          throw new Error('Unauthorized')
        }
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        if (!response.body) {
          throw new Error('Response body is null')
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        try {
          while (true) {
            const { done, value } = await reader.read()
            
            if (done) {
              break
            }

            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split('\n')
            
            // Keep the last incomplete line in the buffer
            buffer = lines.pop() || ''

            for (const line of lines) {
              const trimmedLine = line.trim()
              
              // Skip empty lines and SSE comments
              if (!trimmedLine || trimmedLine.startsWith(':')) {
                continue
              }

              // Parse SSE data format
              if (trimmedLine.startsWith('data: ')) {
                try {
                  const jsonStr = trimmedLine.slice(6) // Remove 'data: ' prefix
                  const data = JSON.parse(jsonStr)
                  
                  // Check for server-sent errors
                  if (data.type === 'error') {
                    throw new Error(data.message || 'Server error')
                  }
                  
                  yield data
                } catch (e) {
                  console.error('Failed to parse SSE data:', trimmedLine, e)
                  throw e
                }
              }
            }
          }
          
          // Successfully completed, exit retry loop
          return
          
        } finally {
          reader.releaseLock()
        }
      } catch (error) {
        lastError = error as Error
        
        // Don't retry on certain errors
        if (
          error instanceof Error &&
          (error.message.includes('HTTP error! status: 4') || // 4xx errors
           error.name === 'AbortError')
        ) {
          throw error
        }

        // If we have retries left, wait and try again
        if (attempt < maxRetries) {
          options?.onRetry?.(attempt + 1, lastError)
          await new Promise(resolve => setTimeout(resolve, retryDelay * (attempt + 1)))
          continue
        }

        // Out of retries
        throw lastError
      }
    }

    // Should never reach here, but TypeScript needs it
    if (lastError) {
      throw lastError
    }
  },
}

export const conversationService = {
  async listConversations() {
    const response = await api.get<Conversation[]>('/api/conversations')
    return response.data
  },

  async getMessages(sessionId: string) {
    const response = await api.get<Message[]>(`/api/conversations/${sessionId}/messages`)
    return response.data
  },

  async deleteConversation(sessionId: string) {
    await api.delete(`/api/conversations/${sessionId}`)
  },

  async submitFeedback(messageId: number, feedback: 'positive' | 'negative') {
    await api.post('/api/conversations/feedback', {
      message_id: messageId,
      feedback,
    })
  },

  async extractKnowledge(sessionId: string, messageIds?: number[]) {
    const response = await api.post(`/api/conversations/${sessionId}/extract-knowledge`, {
      message_ids: messageIds || null,
    })
    return response.data
  },

  async listExtractableConversations(limit: number = 50) {
    const response = await api.get('/api/conversations/extractable', {
      params: { limit },
    })
    return response.data
  },
}

export interface KnowledgeEntry {
  id: number
  title: string
  content: string
  category: string | null
  tags: string[]
  source_type: string
  author: string | null
  status: string
  num_chunks: number
  created_at: string
  updated_at?: string
}

export interface KnowledgeEntryCreate {
  title: string
  content: string
  category?: string | null
  tags?: string[]
  author?: string | null
  status?: 'draft' | 'published'
}

export interface KnowledgeEntryUpdate {
  title?: string
  content?: string
  category?: string | null
  tags?: string[]
  status?: 'draft' | 'published'
}

export const knowledgeService = {
  async createKnowledgeEntry(data: KnowledgeEntryCreate) {
    const response = await api.post<KnowledgeEntry>('/api/knowledge', data)
    return response.data
  },

  async updateKnowledgeEntry(id: number, data: KnowledgeEntryUpdate) {
    const response = await api.put<KnowledgeEntry>(`/api/knowledge/${id}`, data)
    return response.data
  },

  async getKnowledgeEntry(id: number) {
    const response = await api.get<KnowledgeEntry>(`/api/knowledge/${id}`)
    return response.data
  },

  async deleteKnowledgeEntry(id: number) {
    await api.delete(`/api/knowledge/${id}`)
  },

  async listKnowledgeEntries(params?: {
    category?: string
    tags?: string
    status?: string
    skip?: number
    limit?: number
  }) {
    const response = await api.get<KnowledgeEntry[]>('/api/knowledge', { params })
    return response.data
  },

  async listCategories() {
    const response = await api.get<Array<{ id: number; name: string; description: string | null; color: string | null; icon: string | null; display_order: number }>>('/api/knowledge/categories')
    return response.data
  },
}
