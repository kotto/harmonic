/* ═══════════════════════════════════════════════════════════════════════════
   KA HCV2 — le nouveau codec harmonique (MODAL + SELECT + WASM 47 Ko)
   ═══════════════════════════════════════════════════════════════════════════
   Formats supportés (décodage) :
     · HCVH — hybride (MODAL + corrections FULL)
     · HCVM — MODAL (troncature dorée, 527×, 29 dB)
     · HHD2 — dictionnaire V2 (213×, ∞)
     · HHDC — FULL (Delta-H+zstd, 2,9×, ∞)
   Encodage : délègue au serveur KA (hcv_codec.py) ou au module Python WASM.
   Statut : window.KAHCV2 — utilisé par ka_index.html pour le bouton ⬇️ .hcv2
*/
(function () {
  'use strict';

  const KAHCV2 = {
    state: 'loading',  // 'loading' | 'ready' | 'error'
    instance: null,     // l'instance WASM du décodeur
    magics: {
      HCVH: [0x48, 0x43, 0x56, 0x48],  // 'HCVH'
      HCVM: [0x48, 0x43, 0x56, 0x4D],  // 'HCVM'
      HHD2: [0x48, 0x48, 0x44, 0x32],  // 'HHD2'
      HHDC: [0x48, 0x48, 0x44, 0x43],  // 'HHDC'
    },

    /* ── Initialisation du décodeur WASM ────────────────────────────── */
    async init() {
      try {
        // Charger le module Emscripten
        const wasmPath = 'assets/hcv2_decoder.wasm';
        const jsPath = 'assets/hcv2_decoder.js';
        
        // Le module Emscripten a besoin d'être chargé via un script
        // On utilise la version ES module ou l'import dynamique
        const mod = await import(/* webpackIgnore: true */ jsPath);
        
        // Attendre l'initialisation du runtime WASM
        await new Promise((resolve, reject) => {
          mod.onRuntimeInitialized = resolve;
          // Fallback si déjà initialisé
          if (mod.HEAPU8) resolve();
          // Timeout de sécurité
          setTimeout(() => reject(new Error('WASM timeout')), 30000);
        });
        
        this.instance = mod;
        this.state = 'ready';
        console.log('KA HCV2 : WASM décodeur prêt (47 Ko)');
      } catch (e) {
        this.state = 'error';
        console.warn('KA HCV2 : WASM non disponible', e.message);
      }
    },

    /* ── Détection du format par magic ──────────────────────────────── */
    detectFormat(buf) {
      if (buf.length < 4) return null;
      for (const [name, magic] of Object.entries(this.magics)) {
        if (magic.every((b, i) => buf[i] === b)) return name;
      }
      // Fallback : les formats standard (JPEG, PNG, etc.) sont gérés par ka_hcv.js
      return null;
    },

    /* ── Décodage d'un fichier .hcv2 vers ImageData ─────────────────── */
    async decode(blob) {
      const buf = new Uint8Array(await blob.slice(0, 12).arrayBuffer());
      const fmt = this.detectFormat(buf);
      if (!fmt) {
        return { ok: false, reason: 'format .hcv2 inconnu' };
      }

      if (fmt === 'HCVH' || fmt === 'HCVM') {
        if (this.state !== 'ready') {
          return { ok: false, reason: 'WASM non prêt' };
        }
        try {
          const fullBuf = new Uint8Array(await blob.arrayBuffer());
          const w = new Uint32Array(1);
          const h = new Uint32Array(1);
          // Allouer le buffer de sortie (max 64 MP)
          const out = new Uint8Array(64 * 1024 * 1024);
          
          const ret = this.instance._hc_decode(
            fullBuf, fullBuf.length,
            out, w, h
          );
          
          if (ret !== 0) {
            return { ok: false, reason: 'Échec décodage WASM (code ' + ret + ')' };
          }
          
          // Créer l'image
          const img = new ImageData(
            new Uint8ClampedArray(out.slice(0, w[0] * h[0] * 4)),
            w[0], h[0]
          );
          // Convertir RGB → RGBA
          // (le WASM retourne du RGB, il faut ajouter alpha)
          const rgba = new Uint8Array(w[0] * h[0] * 4);
          for (let i = 0; i < w[0] * h[0]; i++) {
            rgba[i*4] = out[i*3];
            rgba[i*4+1] = out[i*3+1];
            rgba[i*4+2] = out[i*3+2];
            rgba[i*4+3] = 255;
          }
          
          return {
            ok: true,
            format: fmt,
            width: w[0],
            height: h[0],
            data: rgba,
            url: URL.createObjectURL(new Blob([rgba], { type: 'image/png' }))
          };
        } catch (e) {
          return { ok: false, reason: 'Erreur décodage : ' + e.message };
        }
      }
      
      // HHD2 / HHDC : décodeur non disponible en WASM (nécessite le dictionnaire)
      return { ok: false, reason: fmt + ' : décodage serveur requis (dictionnaire)' };
    },

    /* ── Compression via le serveur KA ──────────────────────────────── */
    async compress(imageBlob, mode = 'select', minPsnr = 20) {
      const form = new FormData();
      form.append('image', imageBlob);
      form.append('mode', mode);
      form.append('min_psnr', minPsnr);
      form.append('format', 'hcv2');
      
      try {
        const resp = await fetch('/api/hcv2/compress', {
          method: 'POST',
          body: form,
        });
        if (!resp.ok) {
          const err = await resp.text();
          return { ok: false, reason: 'Serveur : ' + err };
        }
        const blob = await resp.blob();
        const size = blob.size;
        const ratio = (imageBlob.size / size).toFixed(1);
        return {
          ok: true,
          blob: blob,
          size: size,
          ratio: ratio,
          url: URL.createObjectURL(blob),
        };
      } catch (e) {
        return { ok: false, reason: 'Erreur réseau : ' + e.message };
      }
    },

    /* ── Compression locale (WASM) — à venir ────────────────────────── */
    // async compressLocal(imageData) { ... }
  };

  window.KAHCV2 = KAHCV2;
})();