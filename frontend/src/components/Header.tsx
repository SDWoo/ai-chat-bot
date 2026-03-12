import { Moon, Sun } from 'lucide-react'
import { useThemeStore } from '@/store/themeStore'

export default function Header() {
  const { isDark, toggleTheme } = useThemeStore()

  return (
    <header className="sticky top-0 z-50 bg-white dark:bg-[#1a1a1a] border-b border-gray-100 dark:border-gray-800 px-6 py-4 transition-colors">
      <div className="flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center shadow-md">
            <span className="text-white font-bold text-lg">S</span>
          </div>
          <div>
            <h1 className="text-xl font-bold text-[#191f28] dark:text-white" style={{ letterSpacing: '-0.02em' }}>
              Sindoh AI
            </h1>
            <p className="text-xs text-[#8b95a1] dark:text-gray-400">문서 기반 지식 대화</p>
          </div>
        </div>

        <button
          onClick={toggleTheme}
          className="p-3 rounded-xl bg-[#f2f4f6] dark:bg-gray-800 hover:bg-[#e5e8eb] dark:hover:bg-gray-700 active:bg-[#d1d5db] dark:active:bg-gray-600 transition-all focus:outline-none focus:ring-2 focus:ring-primary-500 group"
          aria-label={isDark ? '라이트 모드로 전환' : '다크 모드로 전환'}
        >
          {isDark ? (
            <Sun size={20} className="text-[#f59e0b] group-hover:rotate-45 transition-transform" />
          ) : (
            <Moon size={20} className="text-[#4e5968] group-hover:-rotate-12 transition-transform" />
          )}
        </button>
      </div>
    </header>
  )
}
