import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react'

export type KaTheme = 'ocean' | 'v2'

interface ThemeContextValue {
  theme: KaTheme
  setTheme: (t: KaTheme) => void
  toggle: () => void
}

const STORAGE_KEY = 'ka_theme'

const ThemeContext = createContext<ThemeContextValue>({
  theme: 'ocean',
  setTheme: () => {},
  toggle: () => {},
})

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<KaTheme>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored === 'v2' || stored === 'ocean') return stored
    } catch { /* ignore */ }
    return 'ocean'
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    try {
      localStorage.setItem(STORAGE_KEY, theme)
    } catch { /* ignore */ }
  }, [theme])

  const setTheme = useCallback((t: KaTheme) => setThemeState(t), [])
  const toggle = useCallback(() => setThemeState(prev => prev === 'ocean' ? 'v2' : 'ocean'), [])

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggle }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  return useContext(ThemeContext)
}