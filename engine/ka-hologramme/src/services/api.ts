/**
 * Services API — Couche de communication avec le backend KA Server
 *
 * Tous les appels backend sont centralisés ici.
 * Chaque fonction est typée et gère les erreurs proprement.
 */

import { API_BASE_URL, API_TIMEOUT } from '../config';
import type {
  ChatResponse,
  CompressResponse,
  EnhanceResponse,
  SpecializeResponse,
  TtsResponse,
  ResoudreResponse,
} from '../types';

// ─── Helper : timeout sur fetch ──────────────────────────────────────────────
function fetchWithTimeout(url: string, init: RequestInit, ms = API_TIMEOUT) {
  const ctrl = new AbortController();
  const id = setTimeout(() => ctrl.abort(), ms);
  return fetch(url, { ...init, signal: ctrl.signal }).finally(() => clearTimeout(id));
}

// ─── Helper : lire la reponse JSON ou jeter ──────────────────────────────────
async function toJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`HTTP ${res.status}: ${body.slice(0, 200)}`);
  }
  return res.json();
}

// ─── Helper : construire l'URL de base ───────────────────────────────────────
function api(path: string) {
  return `${API_BASE_URL}${path}`;
}

// ═══════════════════════════════════════════════════════════════════════════════
// CHAT
// ═══════════════════════════════════════════════════════════════════════════════

export async function chat(
  message: string,
  options?: { mode?: string; session_id?: string; user_id?: string; stream?: boolean },
): Promise<ChatResponse> {
  const res = await fetchWithTimeout(api('/api/chat'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      mode: options?.mode ?? 'auto',
      session_id: options?.session_id ?? '',
      user_id: options?.user_id ?? 'ka-hologramme',
      stream: options?.stream ?? false,
    }),
  });
  return toJson<ChatResponse>(res);
}

// ═══════════════════════════════════════════════════════════════════════════════
// CHAT AVEC REPONSE VOCALE
// ═══════════════════════════════════════════════════════════════════════════════

export async function chatVoice(
  message: string,
  voice = 'fr_FR',
): Promise<ChatResponse & { audio_base64?: string }> {
  const res = await fetchWithTimeout(api('/api/chat/voice'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, voice }),
  });
  return toJson<ChatResponse>(res);
}

// ═══════════════════════════════════════════════════════════════════════════════
// COMPRESSION HCV
// ═══════════════════════════════════════════════════════════════════════════════

export async function compressImage(
  file: File,
  quality = 'standard',
  method = 'auto',
): Promise<CompressResponse> {
  const fd = new FormData();
  fd.append('file', file);
  fd.append('quality', quality);
  fd.append('method', method);
  fd.append('base64', 'true');

  const res = await fetchWithTimeout(api('/api/compress'), {
    method: 'POST',
    body: fd,
  });
  const data = await toJson<CompressResponse>(res);
  return data;
}

// ═══════════════════════════════════════════════════════════════════════════════
// AMELIORATION IMAGE
// ═══════════════════════════════════════════════════════════════════════════════

export async function enhanceImage(
  file: File,
  options?: { denoise?: boolean; sharpen?: boolean; color_correct?: boolean },
): Promise<EnhanceResponse> {
  const fd = new FormData();
  fd.append('file', file);
  fd.append('denoise', String(options?.denoise ?? true));
  fd.append('sharpen', String(options?.sharpen ?? true));
  fd.append('color_correct', String(options?.color_correct ?? false));
  fd.append('base64', 'true');

  const res = await fetchWithTimeout(api('/api/enhance'), {
    method: 'POST',
    body: fd,
  });
  return toJson<EnhanceResponse>(res);
}

// ═══════════════════════════════════════════════════════════════════════════════
// SPECIALISATION (Creation d'hologramme)
// ═══════════════════════════════════════════════════════════════════════════════

export async function specialize(
  domain: string,
  options?: { user_kbs?: string[]; force_refresh?: boolean; mode?: string },
): Promise<SpecializeResponse> {
  const res = await fetchWithTimeout(api('/api/specialize'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      domain,
      user_kbs: options?.user_kbs ?? [],
      force_refresh: options?.force_refresh ?? false,
      mode: options?.mode ?? 'auto',
    }),
  });
  return toJson<SpecializeResponse>(res);
}

// ═══════════════════════════════════════════════════════════════════════════════
// SYNTHESE VOCALE (TTS)
// ═══════════════════════════════════════════════════════════════════════════════

export async function textToSpeech(
  text: string,
  voice = 'fr_FR',
  speed = 1.0,
): Promise<TtsResponse> {
  const res = await fetchWithTimeout(api('/api/voice/tts'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text,
      voice,
      speed,
      return_base64: true,
    }),
  });
  return toJson<TtsResponse>(res);
}

// ═══════════════════════════════════════════════════════════════════════════════
// RESOLUTION (ancien /api/resoudre via solveur_structure.py)
// ═══════════════════════════════════════════════════════════════════════════════

export async function resoudre(
  question: string,
  style = 'conversationnel',
): Promise<ResoudreResponse> {
  const res = await fetchWithTimeout(api('/api/resoudre'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, style }),
  });
  return toJson<ResoudreResponse>(res);
}

// ─── Helper : jouer un audio base64 ──────────────────────────────────────────
export function playAudioBase64(b64: string) {
  try {
    const blob = base64ToBlob(b64, 'audio/wav');
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.play().catch(() => {});
  } catch (e) {
    console.warn('Audio playback failed:', e);
  }
}

function base64ToBlob(b64: string, mime: string): Blob {
  const bin = atob(b64);
  const buf = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
  return new Blob([buf], { type: mime });
}

// ─── Helper : selectionne un fichier via FilePicker ─────────────────────────
export function openFilePicker(accept = 'image/*'): Promise<File | null> {
  return new Promise((resolve) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = accept;
    input.onchange = () => {
      resolve(input.files?.[0] ?? null);
    };
    input.click();
  });
}