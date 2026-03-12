import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface AuthUser {
  id: number
  email: string
  name: string | null
}

interface AuthState {
  user: AuthUser | null
  token: string | null
  isInitialized: boolean
  setAuth: (user: AuthUser, token: string) => void
  logout: () => void
  loadFromStorage: () => void
  setInitialized: (value: boolean) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isInitialized: false,
      setAuth: (user, token) => set({ user, token }),
      logout: () => set({ user: null, token: null }),
      loadFromStorage: () => {
        // persist middleware가 자동으로 localStorage에서 복원함
        set({ isInitialized: true })
      },
      setInitialized: (value) => set({ isInitialized: value }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ user: state.user, token: state.token }),
    }
  )
)
