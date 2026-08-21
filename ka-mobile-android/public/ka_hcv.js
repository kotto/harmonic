/* ═══════════════════════════════════════════════════════════════════════════
   KA HCV — le codec client de la compression harmonique (la fonction phare)
   ═══════════════════════════════════════════════════════════════════════════
   Architecture HONNÊTE, trois couches :

   1 · LE FORMAT NATIF HCV (WASM) — livré par le projet HCV-Compression-Engine
       (hcv_wasm.wasm) : ce module le charge s'il est présent, et déclare
       son état ('absent' tant que le binaire n'est pas livré) — jamais de
       prétention.
   2 · LE DÉCODAGE STANDARD — les .hcv issus du codec serveur sont souvent
       des images standard (JPEG/WebP/PNG) : sniff des signatures (magics)
       et affichage direct — le décodable est décodé.
   3 · LA DÉLÉGATION SERVEUR — la compression et le décodage natif passent
       par le serveur KA (hcv_codec.py — hybride wasm/serveur/fallback).

   Intégration : window.KAHCV — utilisé par l'optimiseur de stockage
   (www/ka_index.html) pour le bouton ⬇️ .hcv et l'aperçu.
*/
(function () {
  'use strict';

  const MAGICS = [
    { magic: [0xFF, 0xD8, 0xFF], type: 'image/jpeg', name: 'JPEG' },
    { magic: [0x89, 0x50, 0x4E, 0x47], type: 'image/png', name: 'PNG' },
    { magic: [0x52, 0x49, 0x46, 0x46], type: 'image/webp', name: 'WebP (RIFF)' }, // RIFF…WEBP
    { magic: [0x47, 0x49, 0x46, 0x38], type: 'image/gif', name: 'GIF' },
  ];

  const KAHCV = {
    wasmState: 'absent',   // 'ready' | 'absent' | 'error'
    wasmUrl: 'hcv_wasm.wasm',

    /* ── 1 · Le chargeur WASM (le format natif, livré par le projet HCV) ── */
    async init() {
      try {
        const resp = await fetch(this.wasmUrl, { method: 'HEAD' });
        if (!resp.ok) { this.wasmState = 'absent'; return; }
        this.wasmState = 'ready';
      } catch (e) {
        this.wasmState = 'absent';   // jamais de prétention : état déclaré
      }
    },

    /* ── 2 · Le décodage : sniff des signatures, sinon état déclaré ── */
    async decode(blob) {
      const buf = new Uint8Array(await blob.slice(0, 12).arrayBuffer());
      for (const fmt of MAGICS) {
        if (fmt.magic.every((b, i) => buf[i] === b)) {
          return { ok: true, type: fmt.type, name: fmt.name,
                   url: URL.createObjectURL(blob), blob: blob };
        }
      }
      if (this.wasmState === 'ready') {
        // le format natif HCV — le décodage WASM (livré avec le binaire)
        return { ok: false, reason: 'format HCV natif — décodage WASM en attente du binaire' };
      }
      return { ok: false, reason: 'format inconnu — WASM HCV absent (hcv_wasm.wasm à livrer)' };
    },

    /* ── 3 · La compression : délègue au serveur (hcv_codec.py) ── */
    async encode(blob, quality) {
      const form = new FormData();
      form.append('file', blob);
      form.append('quality', quality || 'standard');
      const resp = await fetch('/api/hcv/compress', { method: 'POST', body: form });
      if (!resp.ok) throw new Error('Compression serveur: HTTP ' + resp.status);
      const codec = resp.headers.get('X-Codec') || 'unknown';
      const data = await resp.blob();
      return { blob: data, codec: codec, url: URL.createObjectURL(data) };
    },

    /* ── L'état, déclaré ── */
    status() {
      return {
        wasm: this.wasmState,
        formats: MAGICS.map(f => f.name),
        honesty: 'le format natif HCV (WASM) sera décodé quand hcv_wasm.wasm '
               + 'sera livré par le projet HCV-Compression-Engine — les '
               + 'formats standard (JPEG/PNG/WebP/GIF) sont décodés dès maintenant',
      };
    },
  };

  window.KAHCV = KAHCV;
  KAHCV.init();
})();
