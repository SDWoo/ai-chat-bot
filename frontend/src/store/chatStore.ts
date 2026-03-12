import { create } from 'zustand'
import { Message } from '@/services/api'

interface ChatStore {
  messages: Message[]
  conversationId: string | null
  isLoading: boolean
  setMessages: (messages: Message[]) => void
  addMessage: (message: Message) => void
  updateMessage: (id: number, updates: Partial<Message>) => void
  setConversationId: (id: string) => void
  setIsLoading: (loading: boolean) => void
  clearChat: () => void
  loadConversation: (sessionId: string, messages: Message[]) => void
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  conversationId: null,
  isLoading: false,
  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  updateMessage: (id, updates) => 
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg
      ),
    })),
  setConversationId: (id) => set({ conversationId: id }),
  setIsLoading: (loading) => set({ isLoading: loading }),
  clearChat: () => set({ messages: [], conversationId: null }),
  loadConversation: (sessionId, messages) => set({ 
    conversationId: sessionId, 
    messages: messages 
  }),
}))
