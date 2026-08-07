/**
 * KA HCV — Harmonic Compression Video (Pure JS)
 * ===============================================
 * Implémente le codec Delta-H en JavaScript pur pour la compression
 * de frames vidéo dans le navigateur. Aucun serveur requis.
 * 
 * Algorithme Delta-H (issu de la Théorie Harmonique) :
 *   Pour chaque canal (R,G,B) et chaque ligne de pixels :
 *     diff[col] = pixel[col] - pixel[col-1]
 *   La première colonne est gardée en référence.
 *   Les différences sont encodées en entiers signés 8-bit.
 *   Le résultat est compressé avec un RLE simple.
 * 
 * Usage :
 *   const compressed = HCV.compressFrame(canvas);
 *   const imageData = HCV.decompressFrame(compressed);
 *   ctx.putImageData(imageData, 0, 0);
 */

const HCV = {
  VERSION: '1.0.0',
  
  /**
   * Compresse une frame canvas en buffer Delta-H
   * @param {HTMLCanvasElement|ImageData} source - Canvas ou ImageData
   * @param {Object} opts - Options { quality: 0-100, maxWidth: number }
   * @returns {{ data: Uint8Array, width: number, height: number, ratio: number }}
   */
  compressFrame(source, opts = {}) {
    const quality = opts.quality || 75;
    let imageData;
    
    if (source instanceof HTMLCanvasElement) {
      const ctx = source.getContext('2d');
      imageData = ctx.getImageData(0, 0, source.width, source.height);
    } else if (source.data && source.width) {
      imageData = source;
    } else {
      throw new Error('Source must be Canvas or ImageData');
    }
    
    const w = imageData.width;
    const h = imageData.height;
    const pixels = imageData.data; // Uint8ClampedArray RGBA
    
    // Étape 1 : Extraire RGB (ignorer alpha), appliquer sous-échantillonnage si qualité basse
    const step = quality < 40 ? 2 : 1;
    const cw = Math.floor(w / step);
    const ch = Math.floor(h / step);
    
    // Buffer de sortie : header (8 bytes) + données delta
    // Header: [w_hi, w_lo, h_hi, h_lo, step, quality, flags, reserved]
    const headerSize = 8;
    // Estimation taille : cw * ch * 3 canaux + header
    const maxSize = headerSize + cw * ch * 3 * 2; // *2 pour marge RLE
    const buffer = new Uint8Array(maxSize);
    let pos = headerSize;
    
    // Header
    buffer[0] = (cw >> 8) & 0xFF;
    buffer[1] = cw & 0xFF;
    buffer[2] = (ch >> 8) & 0xFF;
    buffer[3] = ch & 0xFF;
    buffer[4] = step;
    buffer[5] = quality;
    buffer[6] = 0; // flags
    buffer[7] = 0; // reserved
    
    // Étape 2 : Delta-H sur chaque canal (R, G, B)
    for (let channel = 0; channel < 3; channel++) {
      for (let y = 0; y < ch; y++) {
        let prev = 0;
        for (let x = 0; x < cw; x++) {
          const srcIdx = (y * step * w + x * step) * 4 + channel;
          const pixel = pixels[srcIdx];
          const diff = pixel - prev;
          prev = pixel;
          
          // Encoder le delta en signed 8-bit (-128 à 127)
          // On ajoute 128 pour stocker en 0-255
          const encoded = (diff + 128) & 0xFF;
          buffer[pos++] = encoded;
        }
      }
    }
    
    // Étape 3 : RLE simple sur le buffer delta
    const rleData = this._rleEncode(buffer.slice(headerSize, pos));
    
    // Assembler: header + RLE data
    const finalSize = headerSize + rleData.length;
    const result = new Uint8Array(finalSize);
    result.set(buffer.slice(0, headerSize), 0);
    result.set(rleData, headerSize);
    
    const originalSize = w * h * 3;
    const ratio = originalSize / finalSize;
    
    return {
      data: result,
      width: cw,
      height: ch,
      ratio: ratio,
      originalSize: originalSize,
      compressedSize: finalSize
    };
  },
  
  /**
   * Décompresse un buffer Delta-H en ImageData
   * @param {{ data: Uint8Array }} compressed - Buffer compressé
   * @returns {ImageData}
   */
  decompressFrame(compressed) {
    const buf = compressed.data;
    let pos = 0;
    
    // Header
    const cw = (buf[pos] << 8) | buf[pos + 1]; pos += 2;
    const ch = (buf[pos] << 8) | buf[pos + 1]; pos += 2;
    const step = buf[pos]; pos += 1;
    const quality = buf[pos]; pos += 1;
    pos += 2; // skip flags + reserved
    
    // Décoder RLE
    const rleData = buf.slice(pos);
    const deltaData = this._rleDecode(rleData);
    
    // Reconstruire l'image
    const imageData = new ImageData(cw, ch);
    const pixels = imageData.data;
    let dp = 0;
    
    for (let channel = 0; channel < 3; channel++) {
      for (let y = 0; y < ch; y++) {
        let prev = 0;
        for (let x = 0; x < cw; x++) {
          const encoded = deltaData[dp++];
          const diff = (encoded - 128) | 0; // signed
          const pixel = (prev + diff) & 0xFF;
          prev = pixel;
          
          const dstIdx = (y * cw + x) * 4;
          pixels[dstIdx + channel] = pixel;
        }
      }
    }
    
    // Remplir alpha = 255
    for (let i = 0; i < cw * ch; i++) {
      pixels[i * 4 + 3] = 255;
    }
    
    return imageData;
  },
  
  /**
   * Run-Length Encoding simple
   * Format: [count_hi, count_lo, value] pour les runs >= 4
   *         valeur brute sinon
   */
  _rleEncode(data) {
    const result = [];
    let i = 0;
    
    while (i < data.length) {
      const val = data[i];
      let run = 1;
      while (i + run < data.length && data[i + run] === val && run < 65535) {
        run++;
      }
      
      if (run >= 4) {
        // Encoder le run
        result.push(0); // marqueur RLE
        result.push((run >> 8) & 0xFF);
        result.push(run & 0xFF);
        result.push(val);
        i += run;
      } else {
        result.push(val);
        i++;
      }
    }
    
    return new Uint8Array(result);
  },
  
  /**
   * Run-Length Decoding
   */
  _rleDecode(data) {
    const result = [];
    let i = 0;
    
    while (i < data.length) {
      if (data[i] === 0 && i + 3 < data.length) {
        // Run encodé
        const count = (data[i + 1] << 8) | data[i + 2];
        const val = data[i + 3];
        for (let j = 0; j < count; j++) {
          result.push(val);
        }
        i += 4;
      } else {
        result.push(data[i]);
        i++;
      }
    }
    
    return new Uint8Array(result);
  },
  
  /**
   * Calcule le ratio de compression pour les stats
   */
  stats(compressed) {
    return {
      originalSize: compressed.originalSize,
      compressedSize: compressed.compressedSize,
      ratio: compressed.ratio,
      savings: ((1 - 1 / compressed.ratio) * 100).toFixed(1) + '%',
      dimensions: compressed.width + 'x' + compressed.height
    };
  }
};

// Export global
if (typeof window !== 'undefined') {
  window.HCV = HCV;
}
