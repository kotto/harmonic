/**
 * Wrapper TypeScript pour ka_hcv.js — Codec HCV (compression)
 * Le script legacy s'expose via window.KAHCV
 */

export interface HCVDecodeResult {
  ok: boolean
  type: string
  name: string
  url: string
  blob: Blob
  reason?: string
}

export interface HCVEncodeResult {
  blob: Blob
  codec: string
  url: string
}

export interface HCVStatus {
  wasm: string
  formats: string[]
  honesty: string
}

interface KAHCVGlobal {
  init(): Promise<void>
  decode(blob: Blob): Promise<HCVDecodeResult>
  encode(blob: Blob, quality?: string): Promise<HCVEncodeResult>
  status(): HCVStatus
  wasmState: string
}

declare global {
  interface Window {
    KAHCV?: KAHCVGlobal
  }
}

async function ensureLoaded(): Promise<KAHCVGlobal> {
  if (window.KAHCV) return window.KAHCV
  await new Promise<void>((resolve, reject) => {
    const s = document.createElement('script')
    s.src = '/ka_hcv.js'
    s.onload = () => resolve()
    s.onerror = () => reject(new Error('Impossible de charger ka_hcv.js'))
    document.head.appendChild(s)
  })
  return window.KAHCV!
}

export const hcv = {
  /** Initialise le codec (vérifie WASM) */
  async init(): Promise<void> {
    const h = await ensureLoaded()
    return h.init()
  },

  /** Décode un blob (sniff formats standard) */
  async decode(blob: Blob): Promise<HCVDecodeResult> {
    const h = await ensureLoaded()
    return h.decode(blob)
  },

  /** Compresse via serveur */
  async encode(blob: Blob, quality?: string): Promise<HCVEncodeResult> {
    const h = await ensureLoaded()
    return h.encode(blob, quality)
  },

  /** État du codec */
  async status(): Promise<HCVStatus> {
    const h = await ensureLoaded()
    return h.status()
  },

  isLoaded(): boolean {
    return !!window.KAHCV
  },
}