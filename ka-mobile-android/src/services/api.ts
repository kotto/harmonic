import axios from 'axios'
import type { AxiosInstance } from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8765'

const api: AxiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

/* ─── Chat ─── */
export interface ChatRequest {
  message: string
  stream?: boolean
  context?: Record<string, unknown>
}

export interface ChatResponse {
  response: string
  source?: 'hybrid' | 'memory-first' | 'holographic' | 'llm'
  confidence?: number
}

export async function sendChat(req: ChatRequest): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>('/api/chat', req)
  return data
}

/* ─── Voice TTS ─── */
export async function textToSpeech(text: string): Promise<ArrayBuffer> {
  const { data } = await api.post('/api/voice/tts', { text }, {
    responseType: 'arraybuffer',
  })
  return data
}

/* ─── Health Diagnostic ─── */
export interface HealthDiagnostic {
  diagnostic_harmonique?: {
    pathologie_principale?: string
    score_confiance: number
  }
  analyse_vitales?: {
    score_harmonique_global: number
  }
  recommandations?: string[]
}

export async function healthDiagnostic(vitals: {
  frequence_cardiaque?: number
  saturation_oxygene?: number
  temperature?: number
}): Promise<HealthDiagnostic> {
  const { data } = await api.post<HealthDiagnostic>('/api/health/diagnostic', {
    symptomes: [],
    vitaux: vitals,
  })
  return data
}

/* ─── HCV Compression ─── */
export async function compressFile(file: File, quality: 'archive' | 'standard' | 'eco' = 'standard'): Promise<Blob> {
  const form = new FormData()
  form.append('file', file)
  form.append('quality', quality)
  const { data } = await api.post('/api/compress', form, {
    responseType: 'blob',
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

/* ─── Hologram Store ─── */
export interface Hologram {
  id: string
  name: string
  description: string
  category: string
  size: string
  price?: string
}

export async function getHolograms(): Promise<Hologram[]> {
  const { data } = await api.get<{ holograms: Hologram[] }>('/api/store/holograms')
  return data.holograms
}

/* ─── Server health ─── */
export async function checkHealth(): Promise<boolean> {
  try {
    await api.get('/api/health', { timeout: 3000 })
    return true
  } catch {
    return false
  }
}

export default api