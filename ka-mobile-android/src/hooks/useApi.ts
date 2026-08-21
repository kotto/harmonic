import { useEffect, useState } from 'react'
import { checkHealth } from '@/services/api'

export function useServerStatus() {
  const [online, setOnline] = useState(false)
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    let mounted = true
    const check = async () => {
      const ok = await checkHealth()
      if (mounted) {
        setOnline(ok)
        setChecking(false)
      }
    }
    check()
    const iv = setInterval(check, 30000)
    return () => {
      mounted = false
      clearInterval(iv)
    }
  }, [])

  return { online, checking }
}