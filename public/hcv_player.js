/**
 * HCV16 Player — Lecteur JavaScript du format .hcv16
 * Implémente le décodage côté client :
 *   - Parsing header HCV16
 *   - Décompression zstd (via DecompressionStream ou fflate)
 *   - Reconstruction signal (Delta-H + inter-frame diff)
 *   - Grain synthesis V16 (seed dérivé, sigma_curve du header)
 *   - Audio delta-DPCM lossless → Web Audio API
 *   - Rendu canvas frame par frame
 *
 * Dépendance optionnelle : fflate (zstd) — chargé dynamiquement si disponible.
 * Sans fflate, seul le mode LOSSLESS avec zlib est supporté.
 */

// ── Constantes container .hcv16 ───────────────────────────────────────────────
const HCV_MAGIC        = 0x36564348; // 'HCV6' little-endian
const HCV_VERSION      = 0x01;
const MODE_LOSSLESS    = 0x01;
const MODE_GRAIN_SYNTH = 0x02;
const MODE_SIGNAL_ONLY = 0x03;
const CS_BGR           = 0x01;
const CS_YUV           = 0x02;
const CS_MONO          = 0x03;
const FTYPE_I          = 0x49;
const FTYPE_P          = 0x50;
const STYPE_AUDIO      = 0x02;
const SIGMA_CURVE_PTS  = 8;

// ── Seed dérivé (identique au Python) ────────────────────────────────────────
function deriveSeed(frameIdx, seqId) {
  return ((seqId * 999983 + frameIdx * 6271 + 31337) & 0xFFFFFFFF) >>> 0;
}

// ── PRNG simple (xorshift32) pour grain synthesis ─────────────────────────────
function makeRng(seed) {
  let s = seed >>> 0 || 1;
  return {
    next() {
      s ^= s << 13; s ^= s >>> 17; s ^= s << 5;
      return (s >>> 0) / 4294967296;
    },
    // Box-Muller pour distribution normale
    randn() {
      const u1 = Math.max(1e-10, this.next());
      const u2 = this.next();
      return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    }
  };
}

// ── Décompression zstd avec fallbacks multiples ──────────────────────────────
async function zstdDecompress(data) {
  const errors = [];
  
  // Méthode 1: DecompressionStream native (Chrome 80+, Firefox 113+)
  if (typeof DecompressionStream !== 'undefined') {
    try {
      const ds = new DecompressionStream('deflate-raw');
      const writer = ds.writable.getWriter();
      const reader = ds.readable.getReader();
      writer.write(data);
      writer.close();
      const chunks = [];
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        chunks.push(value);
      }
      const total = chunks.reduce((s, c) => s + c.length, 0);
      const out = new Uint8Array(total);
      let off = 0;
      for (const c of chunks) { out.set(c, off); off += c.length; }
      return out;
    } catch (e) { 
      errors.push(`DecompressionStream: ${e.message}`);
    }
  }
  
  // Méthode 2: fflate (si chargé)
  if (typeof window !== 'undefined' && window.fflate) {
    try {
      return new Promise((resolve, reject) => {
        window.fflate.decompress(data, (err, result) => {
          if (err) reject(err); else resolve(result);
        });
      });
    } catch (e) {
      errors.push(`fflate: ${e.message}`);
    }
  }
  
  // Méthode 3: pako (si chargé)
  if (typeof window !== 'undefined' && window.pako) {
    try {
      return window.pako.inflate(data);
    } catch (e) {
      errors.push(`pako: ${e.message}`);
    }
  }
  
  // Méthode 4: Chargement dynamique de fflate
  try {
    if (typeof window !== 'undefined' && !window.fflate) {
      await loadScript('https://unpkg.com/fflate@0.8.1/lib/browser.js');
      if (window.fflate) {
        return new Promise((resolve, reject) => {
          window.fflate.decompress(data, (err, result) => {
            if (err) reject(err); else resolve(result);
          });
        });
      }
    }
  } catch (e) {
    errors.push(`Dynamic fflate: ${e.message}`);
  }
  
  // Méthode 5: WebAssembly fallback (si disponible)
  try {
    if (typeof WebAssembly !== 'undefined') {
      const wasmResult = await wasmDecompress(data);
      if (wasmResult) return wasmResult;
    }
  } catch (e) {
    errors.push(`WASM: ${e.message}`);
  }
  
  throw new Error(`Décompression zstd échouée. Tentatives: ${errors.join(', ')}. Installez fflate.js ou utilisez un navigateur récent.`);
}

// Helper pour charger des scripts dynamiquement
function loadScript(src) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = src;
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

// Fallback WebAssembly simple (placeholder)
async function wasmDecompress(data) {
  // Implémentation WebAssembly pour zstd si nécessaire
  // Pour l'instant, retourne null pour indiquer non disponible
  return null;
}

// ── Décodage buffer encodé (_enc_buf / _dec_buf Python) ───────────────────────
async function decodeEncBuf(raw, shape) {
  const flag = raw[0];
  const compressed = raw.slice(1);
  const decompressed = await zstdDecompress(compressed);
  const totalElems = shape.reduce((a, b) => a * b, 1);

  let arr;
  if (flag === 0x08) {        // int8
    arr = new Int8Array(decompressed.buffer, decompressed.byteOffset, totalElems);
  } else if (flag === 0x16) { // int16
    arr = new Int16Array(decompressed.buffer, decompressed.byteOffset, totalElems);
  } else {                    // int32
    arr = new Int32Array(decompressed.buffer, decompressed.byteOffset, totalElems);
  }
  // Convertir en Int32Array pour les calculs
  return Int32Array.from(arr);
}

// ── Delta-H decode (cumsum sur axis=1) ────────────────────────────────────────
function dhDecode(d, shape) {
  const [h, w, nc] = shape;
  const out = new Uint16Array(h * w * nc);
  for (let c = 0; c < nc; c++) {
    for (let y = 0; y < h; y++) {
      let acc = 0;
      for (let x = 0; x < w; x++) {
        acc += d[y * w * nc + x * nc + c];
        out[y * w * nc + x * nc + c] = Math.max(0, Math.min(65535, acc));
      }
    }
  }
  return out;
}

// ── Grain synthesis V16 ───────────────────────────────────────────────────────
function applyGrain(sigFrame, shape, sigmaCurve, seed, maxval) {
  const [h, w, nc] = shape;
  const nPts = sigmaCurve.length;
  const rng  = makeRng(seed);
  const out  = new Uint16Array(sigFrame.length);

  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      // Luminance locale (moyenne des canaux)
      let lum = 0;
      for (let c = 0; c < nc; c++) lum += sigFrame[(y * w + x) * nc + c];
      lum /= nc;

      // Interpolation sigma depuis la LUT
      const lumNorm = Math.min((lum / maxval) * (nPts - 1), nPts - 1);
      const idxLo   = Math.floor(lumNorm);
      const idxHi   = Math.min(idxLo + 1, nPts - 1);
      const t       = lumNorm - idxLo;
      const sigma   = sigmaCurve[idxLo] * (1 - t) + sigmaCurve[idxHi] * t;

      for (let c = 0; c < nc; c++) {
        const noise = rng.randn() * sigma;
        const idx   = (y * w + x) * nc + c;
        out[idx]    = Math.max(0, Math.min(maxval, sigFrame[idx] + noise));
      }
    }
  }
  return out;
}

// ── Audio delta-DPCM decode ───────────────────────────────────────────────────
async function decodeAudio(audioBytes) {
  const view = new DataView(audioBytes.buffer, audioBytes.byteOffset);
  let off = 0;
  const sr   = view.getUint32(off, true); off += 4;
  const nc   = view.getUint16(off, true); off += 2;
  const n    = view.getUint32(off, true); off += 4;
  const fb   = view.getUint32(off, true); off += 4;  // first bytes
  const szC  = view.getUint32(off, true); off += 4;

  const compressed = audioBytes.slice(off, off + szC);
  const raw = await zstdDecompress(compressed);

  // Reconstruct : first sample + cumsum of diffs
  const firstSamples = new Int32Array(raw.buffer, raw.byteOffset, fb / 4);
  const diffs        = new Int32Array(raw.buffer, raw.byteOffset + fb, (n - 1) * nc);

  const samples = new Int16Array(n * nc);
  // First frame
  for (let c = 0; c < nc; c++) samples[c] = firstSamples[c];
  // Cumsum
  for (let i = 1; i < n; i++) {
    for (let c = 0; c < nc; c++) {
      const prev = i === 1 ? firstSamples[c] : samples[(i - 1) * nc + c];
      samples[i * nc + c] = Math.max(-32768, Math.min(32767,
        prev + diffs[(i - 1) * nc + c]
      ));
    }
  }

  return { samples, sr, nc, n };
}

// ── Rendu frame → ImageData (BGR uint16 → RGBA uint8) ────────────────────────
function frameToImageData(frame, shape, maxval) {
  const [h, w, nc] = shape;
  const imgData = new ImageData(w, h);
  const scale   = 255 / maxval;

  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const src = (y * w + x) * nc;
      const dst = (y * w + x) * 4;
      if (nc === 3) {
        // BGR → RGB
        imgData.data[dst]     = Math.round(frame[src + 2] * scale); // R
        imgData.data[dst + 1] = Math.round(frame[src + 1] * scale); // G
        imgData.data[dst + 2] = Math.round(frame[src]     * scale); // B
      } else {
        const v = Math.round(frame[src] * scale);
        imgData.data[dst] = imgData.data[dst+1] = imgData.data[dst+2] = v;
      }
      imgData.data[dst + 3] = 255;
    }
  }
  return imgData;
}

// ═══════════════════════════════════════════════════════════════════════════════
// HCV16Player — classe principale
// ═══════════════════════════════════════════════════════════════════════════════
class HCV16Player {
  constructor(canvas, options = {}) {
    this.canvas    = canvas;
    this.ctx       = canvas.getContext('2d');
    this.onStatus  = options.onStatus  || (() => {});
    this.onProgress = options.onProgress || (() => {});
    this.onError   = options.onError   || console.error;

    this._frames      = [];
    this._header      = null;
    this._audioCtx    = null;
    this._audioBuffer = null;
    this._audioSource = null;
    this._playing     = false;
    this._frameIdx    = 0;
    this._rafId       = null;
    this._startTime   = 0;
  }

  // ── Chargement depuis URL (download sécurisé) ──────────────────────────────
  async loadFromUrl(url, token) {
    this.onStatus('Téléchargement…');
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const resp = await fetch(url, { headers, credentials: 'include' });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

    const buffer = await resp.arrayBuffer();
    await this.loadFromBuffer(buffer);
  }

  // ── Chargement depuis ArrayBuffer ─────────────────────────────────────────
  async loadFromBuffer(buffer) {
    try {
      this.onStatus('Parsing header…');
      
      // Validation taille minimale
      if (buffer.byteLength < 64) {
        throw new Error(`Fichier trop petit: ${buffer.byteLength} bytes (minimum 64)`);
      }
      
      const bytes = new Uint8Array(buffer);
      const view  = new DataView(buffer);

      // Vérification magic avec diagnostic détaillé
      const magic = view.getUint32(0, true);
      if (magic !== HCV_MAGIC) {
        const magicHex = magic.toString(16).padStart(8, '0').toUpperCase();
        const expectedHex = HCV_MAGIC.toString(16).padStart(8, '0').toUpperCase();
        throw new Error(`Magic invalide: 0x${magicHex} (attendu: 0x${expectedHex}). Fichier non-HCV16 ou corrompu.`);
      }

      // CRC32 avec validation de taille
      if (buffer.byteLength < 4) {
        throw new Error('Fichier trop petit pour contenir un CRC32');
      }
      
      const crcStored   = view.getUint32(buffer.byteLength - 4, true);
      const payloadBytes = bytes.slice(0, buffer.byteLength - 4);
      const crcComputed = crc32(payloadBytes);
      
      if (crcStored !== crcComputed) {
        const storedHex = crcStored.toString(16).padStart(8, '0').toUpperCase();
        const computedHex = crcComputed.toString(16).padStart(8, '0').toUpperCase();
        throw new Error(`CRC32 invalide: ${storedHex} (calculé: ${computedHex}). Fichier corrompu ou modifié.`);
      }

    let off = 4; // après magic

    // Header struct : version(1) mode(1) cs(1) bits(1) w(4) h(4) nf(4) fpsN(4) fpsD(4) seqId(4) nStreams(2) pad(2)
    const version   = view.getUint8(off++);
    const modeId    = view.getUint8(off++);
    const csId      = view.getUint8(off++);
    const bitDepth  = view.getUint8(off++);
    const width     = view.getUint32(off, true); off += 4;
    const height    = view.getUint32(off, true); off += 4;
    const nFrames   = view.getUint32(off, true); off += 4;
    const fpsNum    = view.getUint32(off, true); off += 4;
    const fpsDen    = view.getUint32(off, true); off += 4;
    const seqId     = view.getUint32(off, true); off += 4;
    const nStreams  = view.getUint16(off, true); off += 2;
    off += 2; // padding

    // sigma_curve (32 bytes = 8 × float32)
    const sigmaCurve = new Float32Array(buffer, off, SIGMA_CURVE_PTS);
    off += SIGMA_CURVE_PTS * 4;

    // Index frames (8 bytes × nFrames)
    const offsets = [];
    for (let i = 0; i < nFrames; i++) {
      // BigInt pour les offsets 64-bit
      const lo = view.getUint32(off, true);
      const hi = view.getUint32(off + 4, true);
      offsets.push(lo + hi * 4294967296);
      off += 8;
    }

    // Streams additionnels (audio)
    let audioBytes = null;
    for (let s = 1; s < nStreams; s++) {
      const stype = view.getUint8(off++);
      const slo   = view.getUint32(off, true);
      const shi   = view.getUint32(off + 4, true);
      const ssize = slo + shi * 4294967296;
      off += 8;
      const sdata = bytes.slice(off, off + ssize);
      if (stype === STYPE_AUDIO) audioBytes = sdata;
      off += ssize;
    }

    const dataBase = off;
    const nc       = csId === CS_MONO ? 1 : 3;
    const shape    = [height, width, nc];
    const maxval   = (1 << bitDepth) - 1;
    const fps      = fpsNum / Math.max(1, fpsDen);

    this._header = {
      version, modeId, csId, bitDepth, width, height, nFrames,
      fpsNum, fpsDen, fps, seqId, nStreams, sigmaCurve, shape, maxval, nc
    };

    this.canvas.width  = width;
    this.canvas.height = height;

    this.onStatus(`Décodage ${nFrames} frames (${width}×${height} ${bitDepth}bit)…`);

    // ── Décodage frames ────────────────────────────────────────────────────
    this._frames = [];
    let refFrame = null;

    for (let i = 0; i < nFrames; i++) {
      const base  = dataBase + offsets[i];
      const fsz   = view.getUint32(base, true);
      const ftype = view.getUint8(base + 4);
      const fdata = bytes.slice(base + 5, base + 5 + fsz);

      const decoded = await this._decodeFrame(fdata, ftype, i, refFrame, shape, maxval, modeId, sigmaCurve, seqId);
      this._frames.push(decoded);
      refFrame = decoded; // pour les P-frames
      this.onProgress(Math.round((i + 1) / nFrames * 100));
    }

    // ── Décodage audio ─────────────────────────────────────────────────────
    if (audioBytes) {
      this.onStatus('Décodage audio…');
      try {
        const { samples, sr, nc: aNc, n } = await decodeAudio(audioBytes);
        await this._prepareAudio(samples, sr, aNc, n);
      } catch (e) {
        this.onError('Audio decode warning: ' + e.message);
      }
    }

    this.onStatus(`Prêt — ${nFrames} frames @ ${fps.toFixed(3)} fps`);
    this._renderFrame(0);
  }

  // ── Décodage d'une frame ───────────────────────────────────────────────────
  async _decodeFrame(fdata, ftype, idx, refFrame, shape, maxval, modeId, sigmaCurve, seqId) {
    const [h, w, nc] = shape;
    let sig;

    if (ftype === FTYPE_I) {
      // I-frame : Delta-H decode
      const d = await decodeEncBuf(fdata, shape);
      sig = dhDecode(d, shape);
    } else {
      // P-frame : diff + ref
      const diff = await decodeEncBuf(fdata, shape);
      sig = new Uint16Array(h * w * nc);
      const ref = refFrame || new Uint16Array(h * w * nc);
      for (let j = 0; j < sig.length; j++) {
        sig[j] = Math.max(0, Math.min(maxval, ref[j] + diff[j]));
      }
    }

    // Grain synthesis V16
    if (modeId === MODE_GRAIN_SYNTH) {
      const seed = deriveSeed(idx, seqId);
      return applyGrain(sig, shape, sigmaCurve, seed, maxval);
    }
    return sig;
  }

  // ── Préparation audio Web Audio API ───────────────────────────────────────
  async _prepareAudio(samples, sr, nc, n) {
    if (!window.AudioContext && !window.webkitAudioContext) return;
    this._audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: sr });
    const buf = this._audioCtx.createBuffer(nc, n, sr);
    const scale = 1 / 32768;
    for (let c = 0; c < nc; c++) {
      const ch = buf.getChannelData(c);
      for (let i = 0; i < n; i++) {
        ch[i] = samples[i * nc + c] * scale;
      }
    }
    this._audioBuffer = buf;
  }

  // ── Rendu d'une frame sur le canvas ───────────────────────────────────────
  _renderFrame(idx) {
    if (!this._frames[idx]) return;
    const { shape, maxval } = this._header;
    const imgData = frameToImageData(this._frames[idx], shape, maxval);
    this.ctx.putImageData(imgData, 0, 0);
    this._frameIdx = idx;
  }

  // ── Lecture ───────────────────────────────────────────────────────────────
  play() {
    if (this._playing || !this._frames.length) return;
    this._playing   = true;
    this._startTime = performance.now() - (this._frameIdx / this._header.fps) * 1000;

    // Audio
    if (this._audioCtx && this._audioBuffer) {
      if (this._audioCtx.state === 'suspended') this._audioCtx.resume();
      this._audioSource = this._audioCtx.createBufferSource();
      this._audioSource.buffer = this._audioBuffer;
      this._audioSource.connect(this._audioCtx.destination);
      const audioOffset = this._frameIdx / this._header.fps;
      this._audioSource.start(0, audioOffset);
    }

    this._loop();
  }

  _loop() {
    if (!this._playing) return;
    const elapsed = performance.now() - this._startTime;
    const targetFrame = Math.min(
      Math.floor(elapsed / 1000 * this._header.fps),
      this._frames.length - 1
    );
    if (targetFrame !== this._frameIdx) {
      this._renderFrame(targetFrame);
    }
    if (targetFrame >= this._frames.length - 1) {
      this._playing = false;
      this.onStatus('Lecture terminée');
      return;
    }
    this._rafId = requestAnimationFrame(() => this._loop());
  }

  pause() {
    this._playing = false;
    if (this._rafId) cancelAnimationFrame(this._rafId);
    if (this._audioSource) { try { this._audioSource.stop(); } catch {} }
  }

  seek(frameIdx) {
    const wasPlaying = this._playing;
    this.pause();
    this._renderFrame(Math.max(0, Math.min(frameIdx, this._frames.length - 1)));
    if (wasPlaying) this.play();
  }

  get duration() {
    return this._header ? this._frames.length / this._header.fps : 0;
  }
  get currentTime() {
    return this._header ? this._frameIdx / this._header.fps : 0;
  }
  get totalFrames() {
    return this._frames.length;
  }
  get headerInfo() {
    return this._header;
  }
}

// ── CRC32 (IEEE 802.3) ────────────────────────────────────────────────────────
function crc32(bytes) {
  let crc = 0xFFFFFFFF;
  for (let i = 0; i < bytes.length; i++) {
    crc ^= bytes[i];
    for (let j = 0; j < 8; j++) {
      crc = (crc >>> 1) ^ (crc & 1 ? 0xEDB88320 : 0);
    }
  }
  return (crc ^ 0xFFFFFFFF) >>> 0;
}

// Export
if (typeof module !== 'undefined') module.exports = { HCV16Player };
