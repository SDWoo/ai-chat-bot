import { useEffect } from 'react'
import { useAuthStore } from '@/store/authStore'
import { api } from '@/services/api'

interface AuthMeResponse {
  id: number
  email: string
  name: string | null
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { token, setAuth, logout, setInitialized } = useAuthStore()

  useEffect(() => {
    const validateToken = async () => {
      if (!token) {
        setInitialized(true)
        return
      }

      try {
        const response = await api.get<AuthMeResponse>('/api/auth/me', {
          headers: { Authorization: `Bearer ${token}` },
        })
        const data = response.data
        setAuth(
          {
            id: data.id,
            email: data.email,
            name: data.name ?? null,
          },
          token
        )
      } catch {
        logout()
      } finally {
        setInitialized(true)
      }
    }

    validateToken()
  }, [token, setAuth, logout, setInitialized])

  return <>{children}</>
}
