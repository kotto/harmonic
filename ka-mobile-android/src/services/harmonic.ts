/**
 * Wrapper TypeScript pour harmonic_v3.js — HarmonicAI v3 (émergence)
 * Le script legacy s'expose via window.HarmonicAI
 */

export interface DetectedExpr {
  a: number
  op: string
  b: number
}

export interface AskResult {
  candidate: string
  score: number
  verdict: 'true' | '?'
}

export interface TryLocalResult {
  local: boolean
  expression?: string
  result?: number
  method?: string
}

interface HarmonicAIGlobal {
  version: string
  PHI: number
  TAU: number
  solve(expr: string): number
  detect(message: string): DetectedExpr | null
  ingest(sujet: string, relation: string, objet: string): { ok: boolean; facts: number }
  ask(question: string, candidates?: string[]): AskResult[]
  tryLocal(message: string): TryLocalResult
  stats: { emergence: number; fallback: number }
  net: {
    implication(a: string, b: string, strength?: number): void
    exclusion(a: string, b: string): void
    addNode(name: string): void
  }
  solver: {
    add(a: number, b: number): number
    sub(a: number, b: number): number
    solve(expr: string): number
  }
}

declare global {
  interface Window {
    HarmonicAI?: HarmonicAIGlobal
  }
}

async function ensureLoaded(): Promise<HarmonicAIGlobal> {
  if (window.HarmonicAI) return window.HarmonicAI
  await new Promise<void>((resolve, reject) => {
    const s = document.createElement('script')
    s.src = '/harmonic_v3.js'
    s.onload = () => resolve()
    s.onerror = () => reject(new Error('Impossible de charger harmonic_v3.js'))
    document.head.appendChild(s)
  })
  return window.HarmonicAI!
}

export const harmonic = {
  PHI: (1 + Math.sqrt(5)) / 2,

  /** Résout une expression arithmétique via émergence de phase */
  async solve(expr: string): Promise<number> {
    const h = await ensureLoaded()
    const result = h.solve(expr)
    if (Number.isNaN(result)) throw new Error('Expression non résolvable')
    return result
  },

  /** Détecte un motif arithmétique dans un message */
  async detect(message: string): Promise<DetectedExpr | null> {
    const h = await ensureLoaded()
    return h.detect(message)
  },

  /** Ingère un fait dans le réseau de Kuramoto */
  async ingest(sujet: string, relation: string, objet: string): Promise<{ ok: boolean; facts: number }> {
    const h = await ensureLoaded()
    return h.ingest(sujet, relation, objet)
  },

  /** Inférence Kuramoto — scores les candidats */
  async ask(question: string, candidates?: string[]): Promise<AskResult[]> {
    const h = await ensureLoaded()
    return h.ask(question, candidates)
  },

  /** Interception locale avant appel serveur */
  async tryLocal(message: string): Promise<TryLocalResult> {
    const h = await ensureLoaded()
    return h.tryLocal(message)
  },

  /** Stats d'usage */
  async stats(): Promise<{ emergence: number; fallback: number }> {
    const h = await ensureLoaded()
    return h.stats
  },

  isLoaded(): boolean {
    return !!window.HarmonicAI
  },
}