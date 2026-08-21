import { useState, useCallback, useRef, useEffect } from 'react'
import { sendChat, type ChatRequest } from '@/services/api'
import { hybrid } from '@/services/hybrid'
import { harmonic } from '@/services/harmonic'

export interface ChatMessage {
  id: string
  text: string
  sender: 'user' | 'ka' | 'contact'
  timestamp: Date
}

interface UseChatOptions {
  simulatedReplies?: string[]
}

const SERVER_TIMEOUT_MS = 5000
const STORAGE_KEY = 'ka_chat_history'
const MAX_HISTORY = 50

function saveMessages(messages: ChatMessage[]) {
  try {
    const toSave = messages.slice(-MAX_HISTORY).map(m => ({
      ...m,
      timestamp: m.timestamp instanceof Date ? m.timestamp.toISOString() : m.timestamp,
    }))
    localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave))
  } catch { /* localStorage plein ou désactivé */ }
}

function loadMessages(): ChatMessage[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return parsed.map((m: any) => ({
      ...m,
      timestamp: new Date(m.timestamp),
    })).slice(-MAX_HISTORY)
  } catch {
    return []
  }
}

export function useChat(options: UseChatOptions = {}) {
  const {
    simulatedReplies = ['😊 Super !', 'Parfait, à demain !', '👍 On se retrouve où ?', 'Cool !', 'Avec plaisir 🎉'],
  } = options

  const [messages, setMessages] = useState<ChatMessage[]>(loadMessages)
  const [isProcessing, setIsProcessing] = useState(false)
  const idRef = useRef(messages.length)

  // Persister à chaque changement
  useEffect(() => { saveMessages(messages) }, [messages])

  const addMessage = useCallback((text: string, sender: 'user' | 'ka' | 'contact') => {
    idRef.current++
    setMessages(prev => [...prev, {
      id: `msg-${idRef.current}`,
      text,
      sender,
      timestamp: new Date(),
    }])
  }, [])

  const send = useCallback(async (text: string) => {
    if (!text.trim() || isProcessing) return

    addMessage(text, 'user')
    setIsProcessing(true)

    try {
      const local = await harmonic.tryLocal(text)
      if (local.local && local.result !== undefined) {
        addMessage(`⚡ ${local.expression} = ${local.result}`, 'ka')
        setIsProcessing(false)
        return
      }
    } catch { /* continuer */ }

    try {
      const response = await hybrid.traiter(text, { useServer: false })
      addMessage(response.response, 'ka')
      setIsProcessing(false)
      return
    } catch { /* continuer */ }

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), SERVER_TIMEOUT_MS)
      const req: ChatRequest = { message: text, stream: false }
      const response = await sendChat(req)
      clearTimeout(timeoutId)
      addMessage(response.response, 'ka')
      setIsProcessing(false)
      return
    } catch { /* continuer */ }

    try {
      if (hybrid.isLoaded()) {
        const response = await hybrid.traiter(text, { useServer: false })
        if (response.type !== 'REFUS') {
          addMessage(response.response, 'ka')
          setIsProcessing(false)
          return
        }
      }
    } catch { /* rien */ }

    if (simulatedReplies.length > 0) {
      const reply = simulatedReplies[Math.floor(Math.random() * simulatedReplies.length)]
      addMessage(reply, 'contact')
    } else {
      addMessage('Je ne peux pas répondre à ça.', 'ka')
    }
    setIsProcessing(false)
  }, [addMessage, isProcessing, simulatedReplies])

  const clear = useCallback(() => {
    setMessages([])
    idRef.current = 0
    localStorage.removeItem(STORAGE_KEY)
  }, [])

  return {
    messages,
    isProcessing,
    send,
    clear,
    addMessage,
  }
}