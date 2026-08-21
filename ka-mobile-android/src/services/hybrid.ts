/**
 * Wrapper TypeScript pour ka_hybrid.js — Noyau hybride (local + serveur)
 * Le script legacy s'expose via window.KAHybrid
 */

export interface HybridResponse {
  question: string
  type: string
  response: string
  source: 'serveur-hybride' | 'noyau-local'
  audit: unknown
  valeur?: number
  concept?: string
}

export interface HybridState {
  concepts: string[]
  seuil: number
  stats: {
    CALC: number
    FAIT: number
    REFUS: number
    local: number
    serveur: number
    auditKO: number
  }
}

interface KAHybridGlobal {
  traiter(question: string, opts?: { useServer?: boolean }): Promise<HybridResponse>
  etat(): HybridState
  calculer(expr: string): number | null
  repondre(question: string): {
    type: 'IDENTITE' | 'MEDICAL' | 'CONDUITE' | 'CALC' | 'FAIT' | 'REFUS'
    concept?: string
    valeur?: number
    score?: number
  }
  phraseModele(core: ReturnType<KAHybridGlobal['repondre']>): string
  vocaliser(texte: string): string
}

declare global {
  interface Window {
    KAHybrid?: KAHybridGlobal
  }
}

/** Charge le script legacy à la demande */
async function ensureLoaded(): Promise<KAHybridGlobal> {
  if (window.KAHybrid) return window.KAHybrid
  await new Promise<void>((resolve, reject) => {
    const s = document.createElement('script')
    s.src = '/ka_hybrid.js'
    s.onload = () => resolve()
    s.onerror = () => reject(new Error('Impossible de charger ka_hybrid.js'))
    document.head.appendChild(s)
  })
  return window.KAHybrid!
}

export const hybrid = {
  /** Point d'entrée principal — résout la question (serveur puis noyau local) */
  async traiter(question: string, opts?: { useServer?: boolean }): Promise<HybridResponse> {
    const h = await ensureLoaded()
    return h.traiter(question, opts)
  },

  /** État actuel du noyau */
  async etat(): Promise<HybridState> {
    const h = await ensureLoaded()
    return h.etat()
  },

  /** Calcul arithmétique local */
  async calculer(expr: string): Promise<number | null> {
    const h = await ensureLoaded()
    return h.calculer(expr)
  },

  /** Routage de la réponse sans le modèle de phrase */
  async repondre(question: string) {
    const h = await ensureLoaded()
    return h.repondre(question)
  },

  /** Vocalisation (symboles → mots parlables) */
  async vocaliser(texte: string): Promise<string> {
    const h = await ensureLoaded()
    return h.vocaliser(texte)
  },

  /** Chargé ? */
  isLoaded(): boolean {
    return !!window.KAHybrid
  },
}