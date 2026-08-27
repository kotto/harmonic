/// <reference types="vite/client" />

/**
 * Configuration de l'application KA Hologramme
 *
 * En developpement sur emulateur Android : 10.0.2.2 = host machine
 * En production : URL du serveur déployé
 */

// Detection automatique de l'environnement
const isEmulator = typeof window !== 'undefined' &&
  window.location.hostname === 'localhost' &&
  (window as any).Capacitor?.isNativePlatform?.();

export const API_BASE_URL = isEmulator
  ? 'http://10.0.2.2:8765'   // Emulateur Android -> host machine
  : (typeof import.meta !== 'undefined' ? (import.meta as any).env?.VITE_API_URL : undefined) || 'http://localhost:8765';

export const API_TIMEOUT = 30000;

export const PRODUCT_NAME = 'KA Hologramme';
export const PRODUCT_VERSION = '4.2.0';