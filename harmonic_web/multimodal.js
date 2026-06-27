/**
 * Multimodal Analyzer — JavaScript
 * ==================================
 * Analyse les fichiers joints (image, audio, vidéo, document)
 * et produit leur signature harmonique 7D.
 * 
 * Fonctionne 100% côté client, sans serveur.
 * Les fichiers ne sont jamais envoyés à un serveur.
 * 
 * Principe :
 * - Une image est lue via Canvas → pixels → histogrammes → signature 7D
 * - Un audio est lu via Web Audio API → FFT → spectre → signature 7D
 * - Une vidéo est échantillonnée frame par frame → signatures → moyenne
 * - Un document est extrait en texte → analyseur existant
 */

// =========================================================================
// IMAGE ANALYZER
// =========================================================================

class ImageAnalyzer {
    /**
     * Analyse une image (File ou Blob) et produit sa signature harmonique 7D.
     * @param {File|Blob|string} source - Fichier image ou URL data:
     * @returns {Promise<{signature: number[], metadata: object}>}
     */
    async analyze(source) {
        const img = await this._loadImage(source);
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        // Redimensionner pour l'analyse (max 256px)
        const maxSize = 256;
        let w = img.width, h = img.height;
        if (w > maxSize || h > maxSize) {
            const ratio = Math.min(maxSize / w, maxSize / h);
            w = Math.round(w * ratio);
            h = Math.round(h * ratio);
        }
        canvas.width = w;
        canvas.height = h;
        ctx.drawImage(img, 0, 0, w, h);
        
        const imageData = ctx.getImageData(0, 0, w, h);
        const pixels = imageData.data;
        
        // 1. φ_ratio : diversité visuelle (entropie normalisée)
        const histogram = this._computeHistogram(pixels);
        const entropy = this._computeEntropy(histogram);
        const phiRatio = Math.min(1, entropy / 8.0 * PHI / 2);
        
        // 2. α_complexity : contraste (écart-type des intensités)
        const intensities = [];
        for (let i = 0; i < pixels.length; i += 4) {
            intensities.push(0.299 * pixels[i] + 0.587 * pixels[i+1] + 0.114 * pixels[i+2]);
        }
        const mean = intensities.reduce((s, v) => s + v, 0) / intensities.length;
        const variance = intensities.reduce((s, v) => s + (v - mean) ** 2, 0) / intensities.length;
        const stdDev = Math.sqrt(variance);
        const alphaComplexity = Math.min(1, stdDev / 128.0 * ALPHA);
        
        // 3. k_creative : score esthétique (harmonie des couleurs)
        const colorHarmony = this._computeColorHarmony(pixels);
        const kCreative = Math.min(1, colorHarmony * PHI / 2);
        
        // 4. k_mathematical : ratio hauteur/largeur / φ
        const aspectRatio = img.width / img.height;
        const phiDiff = Math.abs(aspectRatio / PHI - 1);
        const kMathematical = Math.min(1, Math.max(0, 1 - phiDiff * 3));
        
        // 5. k_factual : détection de texte (présence de bords nets)
        const edgeScore = this._computeEdgeScore(pixels, w, h);
        const kFactual = Math.min(1, edgeScore * 2);
        
        // 6. k_reasoning : 0 par défaut pour une image sans contexte
        const kReasoning = 0.1 + phiRatio * 0.3;
        
        // 7. k_code : 0 pour une image
        const kCode = 0;
        
        const signature = [
            Math.round(phiRatio * 1e6) / 1e6,
            Math.round(alphaComplexity * 1e6) / 1e6,
            Math.round(kReasoning * 1e6) / 1e6,
            Math.round(kCreative * 1e6) / 1e6,
            Math.round(kMathematical * 1e6) / 1e6,
            Math.round(kFactual * 1e6) / 1e6,
            Math.round(kCode * 1e6) / 1e6
        ];
        
        return {
            signature,
            metadata: {
                width: img.width,
                height: img.height,
                aspectRatio: aspectRatio.toFixed(2),
                entropy: entropy.toFixed(2),
                contrast: stdDev.toFixed(1),
                colorHarmony: colorHarmony.toFixed(2),
                format: source.type || source.name?.split('.').pop() || 'unknown',
                size: source.size || 0
            },
            analyze() {
                return { toVector: () => this.signature };
            }
        };
    }
    
    _loadImage(source) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.onerror = () => reject(new Error('Impossible de charger l\'image'));
            
            if (source instanceof File || source instanceof Blob) {
                const reader = new FileReader();
                reader.onload = (e) => { img.src = e.target.result; };
                reader.onerror = () => reject(new Error('Erreur de lecture du fichier'));
                reader.readAsDataURL(source);
            } else {
                img.src = source;
            }
        });
    }
    
    _computeHistogram(pixels) {
        // Histogramme RGB sur 256 niveaux (on moyenne les 3 canaux)
        const hist = new Array(256).fill(0);
        for (let i = 0; i < pixels.length; i += 4) {
            const gray = Math.round(0.299 * pixels[i] + 0.587 * pixels[i+1] + 0.114 * pixels[i+2]);
            hist[Math.min(255, Math.max(0, gray))]++;
        }
        return hist;
    }
    
    _computeEntropy(histogram) {
        const total = histogram.reduce((s, v) => s + v, 0);
        if (total === 0) return 0;
        let entropy = 0;
        for (const count of histogram) {
            if (count > 0) {
                const p = count / total;
                entropy -= p * Math.log2(p);
            }
        }
        return entropy;
    }
    
    _computeColorHarmony(pixels) {
        // Mesure de l'harmonie des couleurs : similarité des canaux RGB
        let rSum = 0, gSum = 0, bSum = 0;
        const n = pixels.length / 4;
        for (let i = 0; i < pixels.length; i += 4) {
            rSum += pixels[i];
            gSum += pixels[i+1];
            bSum += pixels[i+2];
        }
        const rMean = rSum / n, gMean = gSum / n, bMean = bSum / n;
        const meanMean = (rMean + gMean + bMean) / 3;
        
        // Harmonie = 1 - variance relative entre les canaux
        const channelVar = ((rMean - meanMean)**2 + (gMean - meanMean)**2 + (bMean - meanMean)**2) / 3;
        return Math.max(0, 1 - Math.sqrt(channelVar) / 128);
    }
    
    _computeEdgeScore(pixels, w, h) {
        // Détection simple de bords (Sobel-like) : contraste local
        let edgeCount = 0;
        const step = 4; // Échantillonnage pour performance
        for (let y = step; y < h - step; y += step) {
            for (let x = step; x < w - step; x += step) {
                const idx = (y * w + x) * 4;
                const idxLeft = (y * w + (x - step)) * 4;
                const idxRight = (y * w + (x + step)) * 4;
                const idxUp = ((y - step) * w + x) * 4;
                const idxDown = ((y + step) * w + x) * 4;
                
                const gx = Math.abs(pixels[idxRight] - pixels[idxLeft]);
                const gy = Math.abs(pixels[idxDown] - pixels[idxUp]);
                const grad = Math.sqrt(gx * gx + gy * gy);
                
                if (grad > 40) edgeCount++;
            }
        }
        const totalSamples = Math.floor(w / step) * Math.floor(h / step);
        return edgeCount / Math.max(1, totalSamples);
    }
}

// =========================================================================
// AUDIO ANALYZER
// =========================================================================

class AudioAnalyzer {
    /**
     * Analyse un fichier audio et produit sa signature harmonique 7D.
     * @param {File} file - Fichier audio
     * @returns {Promise<{signature: number[], metadata: object}>}
     */
    async analyze(file) {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const arrayBuffer = await file.arrayBuffer();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        
        const samples = audioBuffer.getChannelData(0);
        const sampleRate = audioBuffer.sampleRate;
        const duration = audioBuffer.duration;
        
        // 1. FFT → spectre de fréquences
        const fftSize = 2048;
        const spectrum = this._computeSpectrum(samples, fftSize);
        
        // 2. φ_ratio : diversité spectrale
        const spectralEntropy = this._computeSpectralEntropy(spectrum);
        const phiRatio = Math.min(1, spectralEntropy * PHI / 3);
        
        // 3. α_complexity : variance temporelle (enveloppe)
        const envelope = this._computeEnvelope(samples, fftSize);
        const envMean = envelope.reduce((s, v) => s + v, 0) / envelope.length;
        const envVar = envelope.reduce((s, v) => s + (v - envMean)**2, 0) / envelope.length;
        const alphaComplexity = Math.min(1, Math.sqrt(envVar) * 2 * ALPHA);
        
        // 4. k_creative : musicalité (ratio harmoniques / bruit)
        const harmonicRatio = this._computeHarmonicRatio(spectrum);
        const kCreative = Math.min(1, harmonicRatio * PHI / 2);
        
        // 5. k_math : ratio fréquence dominante / φ
        const dominantFreq = this._findDominantFrequency(spectrum, sampleRate, fftSize);
        const mathRatio = Math.abs((dominantFreq / 440) / PHI - 1); // 440Hz = La
        const kMathematical = Math.min(1, Math.max(0, 1 - mathRatio * 2));
        
        // 6. k_factual : détection de voix (présence dans 300-3400Hz)
        const voiceEnergy = this._computeVoiceEnergy(spectrum, sampleRate, fftSize);
        const kFactual = Math.min(1, voiceEnergy * 2);
        
        // 7. k_reasoning
        const kReasoning = 0.1 + phiRatio * 0.2;
        
        // 8. k_code
        const kCode = 0;
        
        const signature = [
            Math.round(phiRatio * 1e6) / 1e6,
            Math.round(alphaComplexity * 1e6) / 1e6,
            Math.round(kReasoning * 1e6) / 1e6,
            Math.round(kCreative * 1e6) / 1e6,
            Math.round(kMathematical * 1e6) / 1e6,
            Math.round(kFactual * 1e6) / 1e6,
            Math.round(kCode * 1e6) / 1e6
        ];
        
        audioContext.close();
        
        return {
            signature,
            metadata: {
                duration: duration.toFixed(1),
                sampleRate: sampleRate,
                channels: audioBuffer.numberOfChannels,
                dominantFreq: dominantFreq.toFixed(1),
                harmonicRatio: harmonicRatio.toFixed(2),
                format: file.type || file.name?.split('.').pop() || 'unknown',
                size: file.size
            }
        };
    }
    
    _computeSpectrum(samples, fftSize) {
        const numFrames = Math.floor(samples.length / fftSize);
        const spectrum = new Float32Array(fftSize / 2);
        
        for (let frame = 0; frame < Math.min(numFrames, 100); frame++) {
            const start = frame * fftSize;
            const real = new Float32Array(fftSize);
            const imag = new Float32Array(fftSize);
            
            for (let i = 0; i < fftSize && (start + i) < samples.length; i++) {
                // Hanning window
                const window = 0.5 * (1 - Math.cos(2 * Math.PI * i / (fftSize - 1)));
                real[i] = samples[start + i] * window;
            }
            
            // FFT simplifiée (on utilise la corrélation avec sin/cos)
            for (let k = 0; k < fftSize / 2; k++) {
                let sumCos = 0, sumSin = 0;
                for (let i = 0; i < fftSize; i++) {
                    const angle = 2 * Math.PI * k * i / fftSize;
                    sumCos += real[i] * Math.cos(angle);
                    sumSin += real[i] * Math.sin(angle);
                }
                spectrum[k] += Math.sqrt(sumCos * sumCos + sumSin * sumSin) / (fftSize / 2);
            }
        }
        
        // Moyenne
        for (let k = 0; k < spectrum.length; k++) {
            spectrum[k] /= Math.min(numFrames, 100);
        }
        
        return spectrum;
    }
    
    _computeSpectralEntropy(spectrum) {
        const total = spectrum.reduce((s, v) => s + v, 0);
        if (total === 0) return 0;
        let entropy = 0;
        for (const amp of spectrum) {
            if (amp > 0) {
                const p = amp / total;
                entropy -= p * Math.log2(p);
            }
        }
        return entropy / Math.log2(spectrum.length);
    }
    
    _computeEnvelope(samples, windowSize) {
        const envelope = [];
        for (let i = 0; i < samples.length; i += windowSize) {
            let maxAmp = 0;
            for (let j = 0; j < windowSize && (i + j) < samples.length; j++) {
                maxAmp = Math.max(maxAmp, Math.abs(samples[i + j]));
            }
            envelope.push(maxAmp);
        }
        return envelope;
    }
    
    _computeHarmonicRatio(spectrum) {
        // Ratio d'énergie dans les pics (harmoniques) vs bruit de fond
        const threshold = spectrum.reduce((s, v) => s + v, 0) / spectrum.length * 2;
        let harmonicEnergy = 0, totalEnergy = 0;
        
        for (let k = 1; k < spectrum.length - 1; k++) {
            totalEnergy += spectrum[k];
            if (spectrum[k] > spectrum[k-1] && spectrum[k] > spectrum[k+1] && spectrum[k] > threshold) {
                harmonicEnergy += spectrum[k];
            }
        }
        
        return totalEnergy > 0 ? harmonicEnergy / totalEnergy : 0;
    }
    
    _findDominantFrequency(spectrum, sampleRate, fftSize) {
        let maxAmp = 0, maxIdx = 0;
        for (let k = 1; k < spectrum.length; k++) {
            if (spectrum[k] > maxAmp) {
                maxAmp = spectrum[k];
                maxIdx = k;
            }
        }
        return maxIdx * sampleRate / fftSize;
    }
    
    _computeVoiceEnergy(spectrum, sampleRate, fftSize) {
        // Énergie dans la bande vocale 300-3400Hz
        const minBin = Math.floor(300 * fftSize / sampleRate);
        const maxBin = Math.ceil(3400 * fftSize / sampleRate);
        let voiceEnergy = 0, totalEnergy = 0;
        
        for (let k = 0; k < spectrum.length; k++) {
            totalEnergy += spectrum[k];
            if (k >= minBin && k <= maxBin) {
                voiceEnergy += spectrum[k];
            }
        }
        
        return totalEnergy > 0 ? voiceEnergy / totalEnergy : 0;
    }
}

// =========================================================================
// VIDEO ANALYZER
// =========================================================================

class VideoAnalyzer {
    /**
     * Analyse une vidéo par échantillonnage de frames.
     */
    async analyze(file) {
        const video = document.createElement('video');
        video.preload = 'metadata';
        const url = URL.createObjectURL(file);
        video.src = url;
        
        await new Promise((resolve) => {
            video.onloadedmetadata = resolve;
        });
        
        const duration = video.duration;
        const fps = 10; // Frames par seconde pour l'analyse
        const numFrames = Math.min(Math.floor(duration * fps), 30);
        const imageAnalyzer = new ImageAnalyzer();
        
        let signatures = [];
        let totalMotion = 0;
        let prevFrameData = null;
        
        for (let i = 0; i < numFrames; i++) {
            video.currentTime = i / fps;
            await new Promise((resolve) => { video.onseeked = resolve; });
            
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0);
            
            const dataUrl = canvas.toDataURL('image/jpeg', 0.5);
            const result = await imageAnalyzer.analyze(dataUrl);
            signatures.push(result.signature);
            
            // Flux optique simplifié (différence entre frames consécutives)
            if (prevFrameData) {
                const currentData = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
                let diff = 0;
                const step = 16; // Échantillonnage
                for (let y = 0; y < canvas.height; y += step) {
                    for (let x = 0; x < canvas.width; x += step) {
                        const idx = (y * canvas.width + x) * 4;
                        const prevIdx = idx;
                        diff += Math.abs(currentData[idx] - prevFrameData[prevIdx]);
                    }
                }
                totalMotion += diff / ((canvas.width / step) * (canvas.height / step) * 255);
            }
            
            // Sauvegarder frame pour le calcul de mouvement
            prevFrameData = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
        }
        
        URL.revokeObjectURL(url);
        
        // Moyenne des signatures
        const avgSig = [0, 0, 0, 0, 0, 0, 0];
        for (const sig of signatures) {
            for (let i = 0; i < 7; i++) avgSig[i] += sig[i];
        }
        for (let i = 0; i < 7; i++) avgSig[i] /= signatures.length;
        
        // Ajuster φ_ratio avec le mouvement
        const avgMotion = totalMotion / Math.max(1, numFrames - 1);
        avgSig[0] = Math.min(1, avgSig[0] + avgMotion * 0.3);
        
        return {
            signature: avgSig.map(v => Math.round(v * 1e6) / 1e6),
            metadata: {
                duration: duration.toFixed(1),
                width: video.videoWidth,
                height: video.videoHeight,
                frames: numFrames,
                avgMotion: avgMotion.toFixed(3),
                format: file.type || file.name?.split('.').pop() || 'unknown',
                size: file.size
            }
        };
    }
}

// =========================================================================
// DOCUMENT ANALYZER
// =========================================================================

class DocumentAnalyzer {
    /**
     * Analyse un document texte et produit sa signature 7D.
     * Utilise l'analyseur existant du moteur harmonique.
     */
    async analyze(file) {
        const text = await file.text();
        const words = text.split(/\s+/).filter(w => w.length > 0);
        
        if (words.length === 0) {
            return {
                signature: [0, 0, 0, 0, 0, 0, 0],
                metadata: { wordCount: 0, format: file.name?.split('.').pop() || 'unknown', size: file.size }
            };
        }
        
        // Utiliser l'analyseur existant
        const analyzer = new HarmonicEngine.HarmonicAnalyzer();
        const sig = analyzer.analyze(text);
        
        return {
            signature: sig.toVector().map(v => Math.round(v * 1e6) / 1e6),
            analyze() { return { toVector: () => this.signature }; },
            metadata: {
                wordCount: words.length,
                charCount: text.length,
                lineCount: text.split('\n').length,
                format: file.name?.split('.').pop() || 'unknown',
                size: file.size,
                preview: text.substring(0, 200) + '...'
            }
        };
    }
}

// =========================================================================
// ATTACHED FILE (wrapper unifié)
// =========================================================================

class AttachedFile {
    constructor(file) {
        this.file = file;
        this.name = file.name;
        this.size = file.size;
        this.type = this._detectType(file.name);
        this.mimeType = file.type || 'application/octet-stream';
        this.signature = null;
        this.metadata = null;
        this.analyzed = false;
    }
    
    _detectType(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'];
        const audioExts = ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a'];
        const videoExts = ['mp4', 'avi', 'mov', 'mkv', 'webm'];
        const docExts = ['txt', 'md', 'json', 'csv', 'pdf', 'docx'];
        
        if (imageExts.includes(ext)) return 'image';
        if (audioExts.includes(ext)) return 'audio';
        if (videoExts.includes(ext)) return 'video';
        if (docExts.includes(ext)) return 'document';
        return 'unknown';
    }
    
    async analyze() {
        if (this.analyzed) return;
        
        let result;
        switch (this.type) {
            case 'image':
                result = await new ImageAnalyzer().analyze(this.file);
                break;
            case 'audio':
                result = await new AudioAnalyzer().analyze(this.file);
                break;
            case 'video':
                result = await new VideoAnalyzer().analyze(this.file);
                break;
            case 'document':
                result = await new DocumentAnalyzer().analyze(this.file);
                break;
            default:
                throw new Error(`Type de fichier non supporté : ${this.type}`);
        }
        
        this.signature = result.signature;
        this.metadata = result.metadata;
        this.analyzed = true;
    }
    
    toVector() {
        return this.signature || [0, 0, 0, 0, 0, 0, 0];
    }
    
    summary() {
        if (!this.analyzed) return `${this.name} (non analysé)`;
        return `${this.name} — ${this.type} — ${(this.size / 1024).toFixed(1)}KB — ` +
               `φ=${this.signature[0].toFixed(2)} α=${this.signature[1].toFixed(2)}`;
    }
    
    getPreviewUrl() {
        if (this.type === 'image' || this.type === 'video') {
            return URL.createObjectURL(this.file);
        }
        return null;
    }
}

// =========================================================================
// FUSION MULTIMODALE
// =========================================================================

function fuseSignatures(signatures) {
    const n = signatures.length;
    if (n === 0) return [0, 0, 0, 0, 0, 0, 0];
    if (n === 1) return signatures[0];
    
    const weights = signatures.map(sig => {
        const norm = Math.sqrt(sig.reduce((s, v) => s + v * v, 0));
        return 0.3 + norm * 0.7;
    });
    const totalW = weights.reduce((s, w) => s + w, 0);
    const normalizedW = weights.map(w => w / totalW);
    
    // Fusion pondérée
    const merged = [0, 0, 0, 0, 0, 0, 0];
    for (let i = 0; i < n; i++) {
        for (let k = 0; k < 7; k++) {
            merged[k] += signatures[i][k] * normalizedW[i];
        }
    }
    
    // Termes d'intrication (paires croisées)
    let pairCount = 0;
    for (let i = 0; i < n; i++) {
        for (let j = i + 1; j < n; j++) {
            const R_ij = computeResonance(signatures[i], signatures[j]);
            for (let k = 0; k < 7; k++) {
                merged[k] += R_ij * PHI_INV / (n * (n - 1) / 2);
            }
            pairCount++;
        }
    }
    
    return merged.map(v => Math.min(1, Math.max(0, Math.round(v * 1e6) / 1e6)));
}

// =========================================================================
// EXPORT
// =========================================================================

window.HarmonicMultimodal = {
    ImageAnalyzer,
    AudioAnalyzer,
    VideoAnalyzer,
    DocumentAnalyzer,
    AttachedFile,
    fuseSignatures
};