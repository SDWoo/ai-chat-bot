import { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { MessageSquare, FileText, Menu, X, Moon, Sun, Plus, BookOpen, LogOut, User } from 'lucide-react'
import ConversationList from './ConversationList'
import { useThemeStore } from '@/store/themeStore'
import { useChatStore } from '@/store/chatStore'
import { useAuthStore } from '@/store/authStore'

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)
  const { isDark, toggleTheme, initTheme } = useThemeStore()
  const { clearChat } = useChatStore()
  const { user, logout } = useAuthStore()

  useEffect(() => {
    initTheme()
  }, [initTheme])

  const navItems = [
    { path: '/', label: '채팅', icon: MessageSquare },
    { path: '/knowledge', label: '지식 관리', icon: BookOpen },
    { path: '/documents', label: '문서 관리', icon: FileText },
  ]

  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen)
  const closeSidebar = () => setIsSidebarOpen(false)

  const handleNewChat = () => {
    clearChat()
    closeSidebar()
    if (location.pathname !== '/') {
      navigate('/')
    }
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-dark-bg transition-colors duration-300 ease-in-out">
      {/* Header */}
      <header className="h-12 md:h-14 px-4 md:px-6 bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between z-40 transition-colors duration-300 ease-in-out shadow-soft">
        {/* 햄버거 메뉴 (모바일만) */}
        <button
          onClick={toggleSidebar}
          className="md:hidden min-w-[44px] min-h-[44px] -ml-2 flex items-center justify-center hover:bg-gray-50 dark:hover:bg-gray-800 active:bg-gray-100 dark:active:bg-gray-700 rounded-lg transition-colors"
          aria-label="메뉴 열기"
        >
          <Menu className="w-6 h-6 text-gray-900 dark:text-white" />
        </button>

        {/* 로고 */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg flex items-center justify-center text-white font-bold text-sm shadow-soft">
            S
          </div>
          <h1 className="text-base md:text-lg font-bold text-gray-900 dark:text-white" style={{ letterSpacing: '-0.02em' }}>
            Sindoh AI
          </h1>
        </div>

        {/* 사용자 정보 & 로그아웃 */}
        <div className="flex items-center gap-2">
          <div className="relative">
            <button
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors min-h-[44px]"
              aria-label="사용자 메뉴"
            >
              <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-500/20 flex items-center justify-center">
                <User className="w-4 h-4 text-primary-500 dark:text-primary-400" />
              </div>
              <span className="hidden sm:inline text-sm font-medium text-gray-700 dark:text-gray-300 max-w-[120px] truncate">
                {user?.name || user?.email || '사용자'}
              </span>
            </button>
            {isUserMenuOpen && (
              <>
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setIsUserMenuOpen(false)}
                  aria-hidden="true"
                />
                <div className="absolute right-0 mt-1 w-56 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl shadow-soft-lg z-50">
                  <div className="px-4 py-2 border-b border-gray-100 dark:border-gray-800">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {user?.name || '사용자'}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">
                      {user?.email}
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      logout()
                      setIsUserMenuOpen(false)
                      window.location.href = '/login'
                    }}
                    className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    로그아웃
                  </button>
                </div>
              </>
            )}
          </div>

          {/* 다크모드 토글 */}
          <button
            onClick={toggleTheme}
            className="min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-gray-50 dark:hover:bg-gray-800 active:bg-gray-100 dark:active:bg-gray-700 rounded-lg transition-all duration-200 group"
            aria-label="다크모드 전환"
          >
            {isDark ? (
              <Sun className="w-5 h-5 md:w-6 md:h-6 text-gray-600 dark:text-gray-400 group-hover:text-primary-500 transition-colors" />
            ) : (
              <Moon className="w-5 h-5 md:w-6 md:h-6 text-gray-600 group-hover:text-primary-500 transition-colors" />
            )}
          </button>
        </div>
      </header>

      {/* 메인 영역 */}
      <div className="flex flex-1 overflow-hidden">
        {/* 오버레이 배경 (모바일 사이드바 열릴 때) */}
        {isSidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 dark:bg-black/70 z-30 md:hidden"
            onClick={closeSidebar}
            aria-hidden="true"
          />
        )}

        {/* 네비게이션 사이드바 */}
        <aside
          className={`
            fixed md:relative z-40
            w-64 md:w-64 lg:w-64
            bg-white dark:bg-gray-900 border-r border-gray-100 dark:border-gray-800
            transform transition-all duration-300 ease-in-out
            ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}
            md:translate-x-0
            flex flex-col
            h-full
          `}
          style={{ top: isSidebarOpen ? '48px' : '0' }}
        >
          {/* 모바일 닫기 버튼 */}
          <button
            onClick={closeSidebar}
            className="md:hidden absolute top-4 right-4 min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-gray-50 dark:hover:bg-gray-800 active:bg-gray-100 dark:active:bg-gray-700 rounded-lg transition-colors"
            aria-label="메뉴 닫기"
          >
            <X className="w-6 h-6 text-gray-900 dark:text-white" />
          </button>

          {/* 새 대화 버튼 - 미니멀 디자인 */}
          <div className="p-4 border-b border-gray-100 dark:border-gray-800">
            <button
              onClick={handleNewChat}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-transparent text-[#4e5968] dark:text-gray-400 rounded-xl border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-primary-500 dark:hover:text-primary-400 hover:border-primary-500 dark:hover:border-primary-400 active:scale-[0.98] transition-all font-semibold min-h-[44px]"
            >
              <Plus size={18} strokeWidth={2.5} />
              새 대화
            </button>
          </div>

          {/* 네비게이션 메뉴 */}
          <nav className="px-3 py-4 space-y-1">
            {navItems.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                onClick={closeSidebar}
                className={`
                  relative flex items-center gap-3 px-4 py-3 rounded-xl 
                  transition-all duration-200 min-h-[44px]
                  ${
                    location.pathname === path
                      ? 'bg-primary-50 dark:bg-primary-500/10 text-primary-500 dark:text-primary-400 font-bold before:absolute before:left-0 before:top-1 before:bottom-1 before:w-1 before:bg-primary-500 before:rounded-r-full shadow-soft'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 active:bg-gray-100 dark:active:bg-gray-700 font-semibold'
                  }
                `}
              >
                <Icon size={22} strokeWidth={2} />
                <span className="text-[15px]">{label}</span>
              </Link>
            ))}

            {/* 이전 대화 섹션 */}
            <div className="mt-4 mb-2">
              <div className="px-4 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                이전 대화
              </div>
              <ConversationList />
            </div>
          </nav>
        </aside>

        {/* 메인 컨텐츠 */}
        <main className="flex-1 overflow-hidden bg-gray-50 dark:bg-dark-bg transition-colors duration-300 ease-in-out h-full">{children}</main>
      </div>
    </div>
  )
}
