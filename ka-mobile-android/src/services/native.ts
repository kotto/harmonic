/**
 * Wrapper TypeScript pour ka_native.js — Pont natif Capacitor
 * Le script legacy s'expose via window.SpeechRecognition (polyfill)
 */

export interface NativeStatus {
  isNative: boolean
  isApp: boolean
  platform: 'android' | 'ios' | 'web'
}

/** Vérifie si on est dans Capacitor (app native) */
export function isNative(): boolean {
  return !!(window as any).Capacitor
}

/** Vérifie si on est dans l'app KA (vs navigateur) */
export function isApp(): boolean {
  return isNative() && !!(window as any).Capacitor?.isNativePlatform
}

/** Détection de plateforme */
export function getPlatform(): 'android' | 'ios' | 'web' {
  if (!isNative()) return 'web'
  const platform = (window as any).Capacitor?.getPlatform?.()
  if (platform === 'android') return 'android'
  if (platform === 'ios') return 'ios'
  return 'web'
}

/** Charge le script du pont natif */
export async function ensureNativeLoaded(): Promise<void> {
  if (isNative()) return // Capacitor est déjà chargé
  if ((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition) return
  await new Promise<void>((resolve, reject) => {
    const s = document.createElement('script')
    s.src = '/ka_native.js'
    s.onload = () => resolve()
    s.onerror = () => reject(new Error('Impossible de charger ka_native.js'))
    document.head.appendChild(s)
  })
}

/** Wrapper pour la reconnaissance vocale native */
export function createSpeechRecognition(): any {
  if (!isNative()) return null
  const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  if (!SR) return null
  return new SR()
}

/** Appelle un plugin Capacitor directement */
export async function callPlugin<T = unknown>(
  plugin: string,
  method: string,
  options?: Record<string, unknown>,
): Promise<T> {
  const Cap = (window as any).Capacitor
  if (!Cap) throw new Error('Capacitor non disponible')
  
  try {
    return await Cap.Plugins[plugin][method](options || {})
  } catch (e) {
    // Fallback nativePromise
    return await Cap.nativePromise(plugin, method, options || {})
  }
}

export const native = {
  isNative,
  isApp,
  getPlatform,
  ensureNativeLoaded,
  createSpeechRecognition,
  callPlugin,
}