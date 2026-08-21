/**
 * Wrapper TypeScript pour vital_ka_voice.js — Synthèse vocale
 * Le script legacy s'expose via window.KA_VOICE
 */

export type VoiceProfile = 'conseiller' | 'compagnon'

export interface VoiceServer {
  available: boolean | null
  detect(): Promise<boolean>
  unlock(): void
  stopAudio(): void
}

interface KAVoiceGlobal {
  speak(text: string, profile?: VoiceProfile): Promise<boolean>
  speakSync(text: string, profile?: VoiceProfile): boolean
  stop(): void
  isSpeaking(): boolean
  isSupported(): boolean
  isEnabled(): boolean
  setEnabled(on: boolean): void
  prewarm(): void
  server: VoiceServer
  buildDiagnosisSpeech(diag: { top: { name: string; score: number } }): string
  speakLastDiagnosis(profile?: string): Promise<boolean>
  PROFILES: Record<string, { rate: number; pitch: number; speed: number; voice: string }>
}

declare global {
  interface Window {
    KA_VOICE?: KAVoiceGlobal
    aiSpeakLast?: () => void
    speakDiagnosisResult?: (btn: HTMLElement) => void
    voiceStop?: () => void
  }
}

async function ensureLoaded(): Promise<KAVoiceGlobal> {
  if (window.KA_VOICE) return window.KA_VOICE
  await new Promise<void>((resolve, reject) => {
    const s = document.createElement('script')
    s.src = '/vital_ka_voice.js'
    s.onload = () => resolve()
    s.onerror = () => reject(new Error('Impossible de charger vital_ka_voice.js'))
    document.head.appendChild(s)
  })
  return window.KA_VOICE!
}

export const voice = {
  /** Parle un texte avec un profil vocal */
  async speak(text: string, profile?: VoiceProfile): Promise<boolean> {
    const v = await ensureLoaded()
    return v.speak(text, profile)
  },

  /** Version synchrone (utilise le cache) */
  speakSync(text: string, profile?: VoiceProfile): boolean {
    if (!window.KA_VOICE) return false
    return window.KA_VOICE.speakSync(text, profile)
  },

  /** Arrête la parole */
  async stop(): Promise<void> {
    const v = await ensureLoaded()
    v.stop()
  },

  /** Vérifie si la parole est active */
  async isSpeaking(): Promise<boolean> {
    const v = await ensureLoaded()
    return v.isSpeaking()
  },

  /** Vérifie si la synthèse est supportée */
  isSupported(): boolean {
    return !!window.speechSynthesis
  },

  /** Active/désactive la voix */
  async setEnabled(on: boolean): Promise<void> {
    const v = await ensureLoaded()
    v.setEnabled(on)
  },

  /** Préchauffe la détection du serveur */
  async prewarm(): Promise<void> {
    const v = await ensureLoaded()
    v.prewarm()
  },

  /** Déverrouille le contexte audio (dans un click handler) */
  async unlock(): Promise<void> {
    const v = await ensureLoaded()
    v.server.unlock()
  },

  /** Détecte le serveur Piper */
  async detectServer(): Promise<boolean> {
    const v = await ensureLoaded()
    return v.server.detect()
  },

  isLoaded(): boolean {
    return !!window.KA_VOICE
  },
}