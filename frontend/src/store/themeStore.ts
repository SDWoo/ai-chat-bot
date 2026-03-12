import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface ThemeState {
  isDark: boolean
  toggleTheme: () => void
  setDarkMode: (isDark: boolean) => void
  initTheme: () => void
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      isDark: false,
      toggleTheme: () =>
        set((state) => {
          const newMode = !state.isDark
          updateHtmlClass(newMode)
          return { isDark: newMode }
        }),
      setDarkMode: (isDark) => {
        updateHtmlClass(isDark)
        set({ isDark })
      },
      initTheme: () => {
        const { isDark } = get()
        updateHtmlClass(isDark)
      },
    }),
    {
      name: 'theme-storage',
    }
  )
)

function updateHtmlClass(isDark: boolean) {
  if (isDark) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}
