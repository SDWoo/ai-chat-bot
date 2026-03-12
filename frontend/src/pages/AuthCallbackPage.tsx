import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { api } from '@/services/api'

interface AuthMeResponse {
  id: number
  email: string
  name: string | null
}

export default function AuthCallbackPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const token = searchParams.get('token')
  const { setAuth } = useAuthStore()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const handleCallback = async () => {
      if (!token) {
        setError('토큰이 없습니다.')
        setTimeout(() => navigate('/login'), 2000)
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
        navigate('/', { replace: true })
      } catch {
        setError('인증에 실패했습니다.')
        setTimeout(() => navigate('/login'), 2000)
      }
    }

    handleCallback()
  }, [token, setAuth, navigate])

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 dark:bg-dark-bg">
        <p className="text-red-600 dark:text-red-400">{error}</p>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">로그인 페이지로 이동합니다...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 dark:bg-dark-bg">
      <div className="w-10 h-10 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
      <p className="mt-4 text-gray-600 dark:text-gray-400">로그인 처리 중...</p>
    </div>
  )
}
