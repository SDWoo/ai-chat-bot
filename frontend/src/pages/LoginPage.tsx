import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { MessageSquare } from 'lucide-react'
import { useThemeStore } from '@/store/themeStore'
import { useAuthStore } from '@/store/authStore'
import { api, API_URL } from '@/services/api'

const LOGIN_URL = `${API_URL}/api/auth/login`

const ERROR_MESSAGES: Record<string, string> = {
  no_code: '인증 코드를 받지 못했습니다. 다시 시도해 주세요.',
  token_exchange_failed: '토큰 교환에 실패했습니다. 다시 시도해 주세요.',
  invalid_user_info: '사용자 정보를 가져올 수 없습니다. 다시 시도해 주세요.',
  ms_not_configured: 'Microsoft 로그인이 설정되지 않았습니다. 아래 개발용 로그인을 사용해 주세요.',
}

export default function LoginPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const error = searchParams.get('error')
  const { isDark } = useThemeStore()
  const { setAuth } = useAuthStore()
  const [devLoginLoading, setDevLoginLoading] = useState(false)
  const [devLoginError, setDevLoginError] = useState<string | null>(null)

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [isDark])

  const handleMicrosoftLogin = () => {
    window.location.href = LOGIN_URL
  }

  const handleDevLogin = async () => {
    setDevLoginLoading(true)
    setDevLoginError(null)
    try {
      const res = await api.post<{ token: string; user: { id: number; email: string; name: string | null } }>(
        '/api/auth/dev-login'
      )
      const { token, user } = res.data
      setAuth({ id: user.id, email: user.email, name: user.name ?? null }, token)
      navigate('/', { replace: true })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setDevLoginError(msg || '개발 로그인에 실패했습니다.')
    } finally {
      setDevLoginLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 dark:bg-dark-bg px-4 transition-colors duration-200">
      <div className="w-full max-w-md animate-slide-up">
        {/* 로고 & 환영 메시지 */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl text-white shadow-soft-lg mb-6">
            <MessageSquare className="w-8 h-8" strokeWidth={2} />
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-2" style={{ letterSpacing: '-0.02em' }}>
            Sindoh AI
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-base">
            환영합니다. Microsoft 계정으로 로그인해 주세요.
          </p>
        </div>

        {/* 에러 메시지 */}
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
            <p className="text-red-600 dark:text-red-400 text-sm">
              {ERROR_MESSAGES[error] || `오류가 발생했습니다. (${error})`}
            </p>
          </div>
        )}

        {/* Microsoft 로그인 버튼 - Toss 스타일 */}
        <button
          onClick={handleMicrosoftLogin}
          className="w-full flex items-center justify-center gap-3 px-6 py-4 rounded-xl font-semibold text-base min-h-[52px] transition-all duration-200
            bg-[#2F2F2F] dark:bg-white hover:bg-[#1f1f1f] dark:hover:bg-gray-100 
            text-white dark:text-[#2F2F2F]
            shadow-soft hover:shadow-soft-lg active:scale-[0.98]
            border border-transparent"
        >
          <svg className="w-5 h-5" viewBox="0 0 21 21" fill="none">
            <rect x="1" y="1" width="9" height="9" fill="#F25022" />
            <rect x="11" y="1" width="9" height="9" fill="#7FBA00" />
            <rect x="1" y="11" width="9" height="9" fill="#00A4EF" />
            <rect x="11" y="11" width="9" height="9" fill="#FFB900" />
          </svg>
          Microsoft로 로그인
        </button>

        <p className="mt-6 text-center text-xs text-gray-500 dark:text-gray-400">
          회사 또는 학교 Microsoft 계정으로 로그인할 수 있습니다.
        </p>

        {/* 개발용 로그인 (MS 미설정 시) */}
        <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-400 text-center mb-3">
            Microsoft 설정이 없을 때만 사용
          </p>
          <button
            onClick={handleDevLogin}
            disabled={devLoginLoading}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-medium text-sm
              bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300
              hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-50 transition-all"
          >
            {devLoginLoading ? '로그인 중...' : '개발용 로그인'}
          </button>
          {devLoginError && (
            <p className="mt-2 text-sm text-red-600 dark:text-red-400 text-center">{devLoginError}</p>
          )}
        </div>
      </div>
    </div>
  )
}
