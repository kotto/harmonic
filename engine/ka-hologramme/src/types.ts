/** Types partagés de l'application KA Hologramme */

export type Screen = 'home' | 'create' | 'chat' | 'profile';

export interface Hologramme {
  id: string;
  nom: string;
  icone: string;
  exemples: number;
  precision: number;
  temps: string;
  actif: boolean;
}

export interface TemplateHologramme {
  id: string;
  nom: string;
  icone: string;
  description: string;
  exemples: number;
  precision: number;
}

/** Réponse de l'API /api/chat */
export interface ChatResponse {
  response: string;
  engine: string;
  method: string;
  code: string;
  source?: string;
  result?: number;
  expression?: string;
  is_refusal?: boolean;
  error?: string;
  holographic_context?: boolean;
  best_domain?: string;
  intent_frame?: Record<string, unknown>;
  audio_base64?: string;
}

/** Réponse de l'API /api/compress */
export interface CompressResponse {
  success: boolean;
  filename: string;
  original_size: number;
  compressed_size: number;
  ratio: number;
  saved_percent: number;
  quality: string;
  method: string;
  format: string;
  data_base64?: string;
  error?: string;
}

/** Réponse de l'API /api/enhance */
export interface EnhanceResponse {
  success: boolean;
  filename: string;
  original_size: number;
  enhanced_size: number;
  operations: {
    denoise: boolean;
    sharpen: boolean;
    color_correct: boolean;
  };
  data_base64?: string;
  error?: string;
}

/** Réponse de l'API /api/specialize */
export interface SpecializeResponse {
  success: boolean;
  domain: string;
  method: string;
  status?: string;
  facts_created?: number;
  facts_sample?: Record<string, unknown>[];
  hologram_id?: string;
  message: string;
  error?: string;
}

/** Réponse de l'API /api/voice/tts */
export interface TtsResponse {
  success: boolean;
  audio_base64?: string;
  format: string;
  voice: string;
  text_length: number;
  error?: string;
}

/** Réponse de l'API /api/resoudre */
export interface ResoudreResponse {
  success: boolean;
  question: string;
  resultat: number;
  resultat_formate: string;
  operations: string;
  etapes: string;
  style: string;
  error?: string;
}