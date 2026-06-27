#!/usr/bin/env python3
"""
Integration Multimodale + Fusion Quantique ABC dans LM Arena
=============================================================
Permet de joindre des fichiers (images, audio, video, documents) au prompt,
de les analyser via signature harmonique 7D, de fusionner via ABC,
et d'enrichir la reponse du moteur LM Arena.

Usage:
    from harmonic_multimodal_integration import MultimodalHarmonicIntegrator
    
    integrator = MultimodalHarmonicIntegrator()
    result = integrator.process(prompt="Decris cette image", files=[...])
"""

import os
import io
import json
import math
import base64
import hashlib
import tempfile
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# =========================================================================
# CONSTANTES HARMONIQUES
# =========================================================================
PHI = 1.618033988749895
PHI_INV = 0.6180339887498949
ALPHA = 0.618033988749895  # 1/PHI
B_1_PHI = 0.8506508083
ALPHA_CONST = 1.1755694591  # 1/B(1/PHI)
HARMONIC_DIMS = 7

# =========================================================================
# TYPES DE FICHIERS SUPPORTES
# =========================================================================
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
AUDIO_EXTS = {'.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a'}
VIDEO_EXTS = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
DOC_EXTS   = {'.txt', '.md', '.json', '.csv', '.pdf', '.docx', '.py', '.js', '.html', '.css'}

# =========================================================================
# STRUCTURES DE DONNEES
# =========================================================================

@dataclass
class FileAnalysis:
    """Resultat de l'analyse d'un fichier."""
    filename: str
    file_type: str
    file_size: int
    mime_type: str
    signature_7d: List[float] = field(default_factory=lambda: [0.0] * 7)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    content_hash: str = ""
    
    def to_dict(self) -> dict:
        return {
            'filename': self.filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'signature_7d': [round(v, 6) for v in self.signature_7d],
            'metadata': self.metadata,
            'error': self.error,
            'content_hash': self.content_hash,
        }


@dataclass
class MultimodalResult:
    """Resultat complet du traitement multimodal."""
    prompt: str
    files: List[FileAnalysis] = field(default_factory=list)
    fused_signature: List[float] = field(default_factory=lambda: [0.0] * 7)
    resonance_matrix: List[List[float]] = field(default_factory=list)
    enriched_prompt: str = ""
    response: str = ""
    processing_time_ms: float = 0.0
    quantum_entropy: float = 0.0
    harmonic_resonance: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            'prompt': self.prompt[:200],
            'num_files': len(self.files),
            'files': [f.to_dict() for f in self.files],
            'fused_signature': [round(v, 6) for v in self.fused_signature],
            'resonance_matrix': [[round(v, 4) for v in row] for row in self.resonance_matrix],
            'enriched_prompt': self.enriched_prompt[:500],
            'response': self.response[:500],
            'processing_time_ms': round(self.processing_time_ms, 2),
            'quantum_entropy': round(self.quantum_entropy, 6),
            'harmonic_resonance': round(self.harmonic_resonance, 6),
        }


# =========================================================================
# ANALYSEUR D'IMAGES
# =========================================================================

class ImageAnalyzer:
    """Analyse une image et produit sa signature harmonique 7D."""
    
    def analyze(self, filepath: str) -> FileAnalysis:
        try:
            from PIL import Image
            import numpy as np
            
            img = Image.open(filepath).convert('RGB')
            width, height = img.size
            
            max_size = 256
            if width > max_size or height > max_size:
                ratio = min(max_size / width, max_size / height)
                img = img.resize((int(width * ratio), int(height * ratio)), Image.LANCZOS)
                width, height = img.size
            
            pixels = np.array(img, dtype=np.float32)
            
            gray = 0.299 * pixels[:,:,0] + 0.587 * pixels[:,:,1] + 0.114 * pixels[:,:,2]
            hist, _ = np.histogram(gray, bins=256, range=(0, 255))
            hist = hist / hist.sum()
            entropy = -np.sum(hist * np.log2(hist + 1e-10))
            phi_ratio = min(1.0, entropy / 8.0 * PHI / 2.0)
            
            std_dev = np.std(gray)
            alpha_complexity = min(1.0, std_dev / 128.0 * ALPHA)
            
            r_mean, g_mean, b_mean = pixels[:,:,0].mean(), pixels[:,:,1].mean(), pixels[:,:,2].mean()
            all_mean = (r_mean + g_mean + b_mean) / 3.0
            channel_var = ((r_mean - all_mean)**2 + (g_mean - all_mean)**2 + (b_mean - all_mean)**2) / 3.0
            color_harmony = max(0.0, 1.0 - math.sqrt(channel_var) / 128.0)
            k_creative = min(1.0, color_harmony * PHI / 2.0)
            
            aspect_ratio = width / height if height > 0 else 1.0
            phi_diff = abs(aspect_ratio / PHI - 1.0)
            k_mathematical = min(1.0, max(0.0, 1.0 - phi_diff * 3.0))
            
            edge_score = self._compute_edge_score(gray)
            k_factual = min(1.0, edge_score * 2.0)
            k_reasoning = 0.1 + phi_ratio * 0.3
            k_code = 0.0
            
            signature = [phi_ratio, alpha_complexity, k_reasoning, k_creative,
                        k_mathematical, k_factual, k_code]
            
            return FileAnalysis(
                filename=os.path.basename(filepath), file_type='image',
                file_size=os.path.getsize(filepath),
                mime_type=f'image/{os.path.splitext(filepath)[1][1:]}',
                signature_7d=signature,
                metadata={'width': width, 'height': height,
                         'aspect_ratio': round(aspect_ratio, 2),
                         'entropy': round(entropy, 2), 'contrast': round(std_dev, 1)})
        except Exception as e:
            return FileAnalysis(filename=os.path.basename(filepath), file_type='image',
                              file_size=os.path.getsize(filepath), mime_type='image/unknown', error=str(e))
    
    def _compute_edge_score(self, gray) -> float:
        import numpy as np
        h, w = gray.shape
        step, edge_count, total = 4, 0, 0
        for y in range(step, h - step, step):
            for x in range(step, w - step, step):
                total += 1
                gx = abs(float(gray[y, x + step]) - float(gray[y, x - step]))
                gy = abs(float(gray[y + step, x]) - float(gray[y - step, x]))
                if math.sqrt(gx * gx + gy * gy) > 40:
                    edge_count += 1
        return edge_count / max(total, 1)


# =========================================================================
# ANALYSEUR AUDIO
# =========================================================================

class AudioAnalyzer:
    """Analyse un fichier audio et produit sa signature harmonique 7D."""
    
    def analyze(self, filepath: str) -> FileAnalysis:
        try:
            import numpy as np
            try:
                import librosa
                samples, sr = librosa.load(filepath, sr=22050, mono=True, duration=30)
            except ImportError:
                try:
                    from scipy.io import wavfile
                    sr, samples = wavfile.read(filepath)
                    if samples.ndim > 1:
                        samples = samples.mean(axis=1)
                    samples = samples.astype(np.float32) / 32768.0
                except:
                    return FileAnalysis(filename=os.path.basename(filepath), file_type='audio',
                                      file_size=os.path.getsize(filepath), mime_type='audio/unknown',
                                      signature_7d=[0.3, 0.3, 0.2, 0.4, 0.2, 0.2, 0.0])
            
            fft_size = 2048
            spectrum = self._compute_spectrum(samples, fft_size)
            spectral_entropy = self._compute_spectral_entropy(spectrum)
            phi_ratio = min(1.0, spectral_entropy * PHI / 3.0)
            
            envelope = self._compute_envelope(samples, fft_size)
            alpha_complexity = min(1.0, math.sqrt(np.var(envelope)) * 2.0 * ALPHA)
            
            harmonic_ratio = self._compute_harmonic_ratio(spectrum)
            k_creative = min(1.0, harmonic_ratio * PHI / 2.0)
            
            dominant_freq = self._find_dominant_frequency(spectrum, sr, fft_size)
            math_ratio = abs((dominant_freq / 440.0) / PHI - 1.0) if dominant_freq > 0 else 1.0
            k_mathematical = min(1.0, max(0.0, 1.0 - math_ratio * 2.0))
            
            voice_energy = self._compute_voice_energy(spectrum, sr, fft_size)
            k_factual = min(1.0, voice_energy * 2.0)
            k_reasoning = 0.1 + phi_ratio * 0.2
            k_code = 0.0
            
            return FileAnalysis(
                filename=os.path.basename(filepath), file_type='audio',
                file_size=os.path.getsize(filepath),
                mime_type=f'audio/{os.path.splitext(filepath)[1][1:]}',
                signature_7d=[phi_ratio, alpha_complexity, k_reasoning, k_creative,
                            k_mathematical, k_factual, k_code],
                metadata={'duration': round(len(samples)/sr, 1), 'sample_rate': sr,
                         'dominant_freq': round(dominant_freq, 1)})
        except Exception as e:
            return FileAnalysis(filename=os.path.basename(filepath), file_type='audio',
                              file_size=os.path.getsize(filepath), mime_type='audio/unknown', error=str(e))
    
    def _compute_spectrum(self, samples, fft_size):
        import numpy as np
        num_frames = max(1, len(samples) // fft_size)
        spectrum = np.zeros(fft_size // 2)
        for frame in range(min(num_frames, 100)):
            start = frame * fft_size
            segment = samples[start:start + fft_size]
            if len(segment) < fft_size:
                segment = np.pad(segment, (0, fft_size - len(segment)))
            fft = np.fft.rfft(segment * np.hanning(fft_size))
            spectrum += np.abs(fft)
        return spectrum / min(num_frames, 100)
    
    def _compute_spectral_entropy(self, spectrum):
        import numpy as np
        total = spectrum.sum()
        if total == 0: return 0
        p = spectrum / total
        return -np.sum(p * np.log2(p + 1e-10)) / math.log2(len(spectrum))
    
    def _compute_envelope(self, samples, window_size):
        import numpy as np
        return np.array([np.max(np.abs(samples[i:i+window_size])) 
                        for i in range(0, len(samples), window_size) if len(samples[i:i+window_size]) > 0])
    
    def _compute_harmonic_ratio(self, spectrum):
        import numpy as np
        threshold = spectrum.mean() * 2
        harmonic_energy = sum(spectrum[k] for k in range(1, len(spectrum)-1)
                            if spectrum[k] > spectrum[k-1] and spectrum[k] > spectrum[k+1] and spectrum[k] > threshold)
        total = spectrum.sum()
        return harmonic_energy / total if total > 0 else 0
    
    def _find_dominant_frequency(self, spectrum, sr, fft_size):
        import numpy as np
        return np.argmax(spectrum) * sr / fft_size
    
    def _compute_voice_energy(self, spectrum, sr, fft_size):
        min_bin, max_bin = int(300 * fft_size / sr), int(3400 * fft_size / sr)
        total = spectrum.sum()
        return sum(spectrum[min_bin:max_bin+1]) / total if total > 0 else 0


# =========================================================================
# ANALYSEUR DE DOCUMENTS
# =========================================================================

class DocumentAnalyzer:
    """Analyse un document texte et produit sa signature harmonique 7D."""
    
    RARE_WORDS = {'paradigme', 'epistemologique', 'ontologique', 'phenomenologique',
                  'transcendantal', 'axiomatique', 'heuristique', 'stochastique',
                  'quantique', 'relativiste', 'algorithmique', 'computationnel'}
    
    def analyze(self, filepath: str) -> FileAnalysis:
        try:
            text = self._extract_text(filepath)
            if not text:
                return FileAnalysis(filename=os.path.basename(filepath), file_type='document',
                                  file_size=os.path.getsize(filepath), mime_type='text/plain', error='Texte vide')
            
            words = text.lower().split()
            wc = len(words)
            if wc == 0:
                return FileAnalysis(filename=os.path.basename(filepath), file_type='document',
                                  file_size=os.path.getsize(filepath), mime_type='text/plain', error='Aucun mot')
            
            rare_count = sum(1 for w in words if w.strip('.,!?;:') in self.RARE_WORDS)
            phi_ratio = min(1.0, (rare_count / wc) * PHI)
            
            avg_len = sum(len(w) for w in words) / wc
            variance = sum((len(w) - avg_len) ** 2 for w in words) / wc
            alpha_complexity = min(1.0, ((avg_len / 15.0 + math.sqrt(variance) / 5.0) / 2.0) * ALPHA_CONST)
            
            cat_words = {
                'reasoning': {'pourquoi', 'donc', 'car', 'si', 'alors', 'cause', 'effet', 'analyse', 'conclusion'},
                'creative': {'poeme', 'histoire', 'art', 'imagination', 'reve', 'beaute', 'musique', 'couleur'},
                'mathematical': {'calcul', 'equation', 'nombre', 'somme', 'derivee', 'theoreme', 'formule'},
                'factual': {'definition', 'fait', 'donnee', 'statistique', 'mesure', 'observation', 'resultat'},
                'code': {'python', 'java', 'code', 'fonction', 'classe', 'algorithme', 'variable', 'boucle'},
            }
            
            cats = {}
            for cat, kws in cat_words.items():
                cats[cat] = min(1.0, sum(1 for w in words if w in kws) / wc * PHI * 3)
            
            return FileAnalysis(
                filename=os.path.basename(filepath), file_type='document',
                file_size=os.path.getsize(filepath), mime_type='text/plain',
                signature_7d=[phi_ratio, alpha_complexity, cats['reasoning'], cats['creative'],
                            cats['mathematical'], cats['factual'], cats['code']],
                metadata={'word_count': wc, 'char_count': len(text), 'avg_word_length': round(avg_len, 1)})
        except Exception as e:
            return FileAnalysis(filename=os.path.basename(filepath), file_type='document',
                              file_size=os.path.getsize(filepath), mime_type='text/plain', error=str(e))
    
    def _extract_text(self, filepath: str) -> str:
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.pdf':
            try:
                import PyPDF2
                text = ""
                with open(filepath, 'rb') as f:
                    for page in PyPDF2.PdfReader(f).pages:
                        text += page.extract_text() or ""
                return text
            except ImportError:
                pass
        elif ext == '.docx':
            try:
                import docx
                return '\n'.join(p.text for p in docx.Document(filepath).paragraphs)
            except ImportError:
                pass
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except:
            return ""


# =========================================================================
# ANALYSEUR VIDEO
# =========================================================================

class VideoAnalyzer:
    """Analyse une video par echantillonnage de frames."""
    
    def analyze(self, filepath: str) -> FileAnalysis:
        try:
            import numpy as np
            from PIL import Image
            frames = self._extract_frames(filepath, max_frames=10)
            if not frames:
                return FileAnalysis(filename=os.path.basename(filepath), file_type='video',
                                  file_size=os.path.getsize(filepath), mime_type='video/unknown',
                                  signature_7d=[0.4, 0.3, 0.2, 0.3, 0.1, 0.2, 0.0])
            
            img_analyzer = ImageAnalyzer()
            sigs = []
            for frame in frames:
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    fp = tmp.name
                    frame.save(fp)
                sigs.append(img_analyzer.analyze(fp).signature_7d)
                os.unlink(fp)
            
            avg = [sum(s[i] for s in sigs) / len(sigs) for i in range(7)]
            if len(frames) > 1:
                motion = self._estimate_motion(frames)
                avg[0] = min(1.0, avg[0] + motion * 0.3)
            
            return FileAnalysis(filename=os.path.basename(filepath), file_type='video',
                              file_size=os.path.getsize(filepath),
                              mime_type=f'video/{os.path.splitext(filepath)[1][1:]}',
                              signature_7d=avg,
                              metadata={'num_frames': len(frames), 'width': frames[0].width, 'height': frames[0].height})
        except Exception as e:
            return FileAnalysis(filename=os.path.basename(filepath), file_type='video',
                              file_size=os.path.getsize(filepath), mime_type='video/unknown', error=str(e))
    
    def _extract_frames(self, filepath: str, max_frames: int = 10):
        frames = []
        try:
            import cv2
            from PIL import Image
            cap = cv2.VideoCapture(filepath)
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total <= 0:
                cap.release()
                return frames
            step = max(1, total // max_frames)
            for i in range(0, total, step):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if ret:
                    frames.append(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
                if len(frames) >= max_frames:
                    break
            cap.release()
        except ImportError:
            pass
        return frames
    
    def _estimate_motion(self, frames):
        import numpy as np
        motion = 0.0
        for i in range(1, len(frames)):
            motion += np.mean(np.abs(np.array(frames[i], dtype=np.float32) - np.array(frames[i-1], dtype=np.float32))) / 255.0
        return motion / max(len(frames) - 1, 1)


# =========================================================================
# FUSION QUANTIQUE ABC
# =========================================================================

class QuantumFusionABC:
    """
    Fusion quantique de signatures harmoniques via le noyau ABC.
    Chaque signature = etat quantique |psi_i> dans l'espace 7D.
    Resonance R_ij = cos(theta) * PHI / 2.
    Fusion ponderee par resonances + intrication + filtre ABC.
    """
    
    def __init__(self):
        try:
            from harmonic_training.model.abc_kernel import ABCKernel
            self.abc_kernel = ABCKernel(max_len=HARMONIC_DIMS)
            self.abc_available = True
        except ImportError:
            self.abc_available = False
    
    def compute_resonance(self, sig1: List[float], sig2: List[float]) -> float:
        dot = sum(a * b for a, b in zip(sig1, sig2))
        n1 = math.sqrt(sum(a ** 2 for a in sig1))
        n2 = math.sqrt(sum(b ** 2 for b in sig2))
        if n1 * n2 == 0: return 0.0
        return min(1.0, max(0.0, (dot / (n1 * n2)) * PHI / 2.0))
    
    def fuse(self, signatures: List[List[float]]) -> Tuple[List[float], List[List[float]], float]:
        n = len(signatures)
        if n == 0: return [0.0] * 7, [], 0.0
        if n == 1: return signatures[0], [[1.0]], 0.0
        
        # Matrice de resonance
        R = [[self.compute_resonance(signatures[i], signatures[j]) for j in range(n)] for i in range(n)]
        
        # Poids : norme + resonance moyenne
        weights = []
        for i in range(n):
            norm = math.sqrt(sum(v ** 2 for v in signatures[i]))
            avg_r = sum(R[i][j] for j in range(n) if j != i) / max(n - 1, 1)
            weights.append(0.3 + 0.4 * norm + 0.3 * avg_r)
        total_w = sum(weights)
        w_norm = [w / total_w for w in weights]
        
        # Fusion ponderee
        fused = [sum(signatures[i][k] * w_norm[i] for i in range(n)) for k in range(7)]
        
        # Termes d'intrication (paires croisees)
        pair_count = n * (n - 1) / 2
        if pair_count > 0:
            for i in range(n):
                for j in range(i + 1, n):
                    for k in range(7):
                        fused[k] += R[i][j] * PHI_INV / pair_count
        
        # Filtre ABC
        if self.abc_available and n > 1:
            import torch
            filtered = self.abc_kernel.apply_to_sequence(torch.tensor(fused, dtype=torch.float32))
            fused = filtered.tolist() if hasattr(filtered, 'tolist') else fused
        
        fused = [min(1.0, max(0.0, v)) for v in fused]
        
        # Entropie quantique
        qe = 0.0
        for i in range(n):
            for j in range(n):
                if R[i][j] > 0:
                    qe -= R[i][j] * math.log2(R[i][j] + 1e-10)
        
        return fused, R, qe / max(n * n, 1)


# =========================================================================
# ENRICHISSEMENT DU PROMPT
# =========================================================================

class PromptEnricher:
    """Enrichit un prompt avec le contexte multimodal fusionne."""
    
    def enrich(self, prompt: str, files: List[FileAnalysis], fused_sig: List[float]) -> str:
        if not files:
            return prompt
        
        parts = [prompt, "\n\n[CONTEXTE MULTIMODAL FUSIONNE]"]
        
        for f in files:
            if f.error: continue
            sig = ", ".join(f"{v:.3f}" for v in f.signature_7d)
            parts.append(f"\n- {f.filename} ({f.file_type}, {f.file_size//1024}KB)")
            parts.append(f"  Signature 7D: [{sig}]")
            if f.metadata:
                meta = ", ".join(f"{k}={v}" for k, v in f.metadata.items() if not isinstance(v, (list, dict)))
                parts.append(f"  [{meta}]")
        
        fused = ", ".join(f"{v:.3f}" for v in fused_sig)
        parts.append(f"\nSignature fusionnee (ABC): [{fused}]")
        
        dims = ['phi_ratio', 'alpha_complexity', 'k_reasoning', 'k_creative',
                'k_mathematical', 'k_factual', 'k_code']
        dominant = sorted(zip(dims, fused_sig), key=lambda x: -x[1])[:3]
        parts.append(f"\nDimensions dominantes: {', '.join(f'{n}={v:.2f}' for n, v in dominant)}")
        
        parts.append("\n\n[INSTRUCTION] Utilise le contexte multimodal ci-dessus. "
                     "Les fichiers ont ete analyses et fusionnes par le noyau quantique ABC. "
                     "Adapte le style et la profondeur de ta reponse selon les signatures harmoniques.")
        
        return "".join(parts)


# =========================================================================
# INTEGRATEUR PRINCIPAL
# =========================================================================

class MultimodalHarmonicIntegrator:
    """
    Integrateur multimodal principal.
    Orchestre : analyse -> fusion quantique ABC -> enrichissement -> reponse.
    """
    
    def __init__(self):
        self.image_analyzer = ImageAnalyzer()
        self.audio_analyzer = AudioAnalyzer()
        self.video_analyzer = VideoAnalyzer()
        self.doc_analyzer = DocumentAnalyzer()
        self.quantum_fusion = QuantumFusionABC()
        self.prompt_enricher = PromptEnricher()
    
    def detect_file_type(self, filepath: str) -> str:
        ext = os.path.splitext(filepath)[1].lower()
        if ext in IMAGE_EXTS: return 'image'
        if ext in AUDIO_EXTS: return 'audio'
        if ext in VIDEO_EXTS: return 'video'
        if ext in DOC_EXTS: return 'document'
        return 'unknown'
    
    def analyze_file(self, filepath: str) -> FileAnalysis:
        if not os.path.exists(filepath):
            return FileAnalysis(filename=os.path.basename(filepath), file_type='unknown',
                              file_size=0, mime_type='unknown', error='Fichier introuvable')
        ftype = self.detect_file_type(filepath)
        if ftype == 'image': return self.image_analyzer.analyze(filepath)
        if ftype == 'audio': return self.audio_analyzer.analyze(filepath)
        if ftype == 'video': return self.video_analyzer.analyze(filepath)
        if ftype == 'document': return self.doc_analyzer.analyze(filepath)
        return FileAnalysis(filename=os.path.basename(filepath), file_type='unknown',
                          file_size=os.path.getsize(filepath), mime_type='unknown',
                          error=f'Type non supporte: {ftype}')
    
    def analyze_from_bytes(self, data: bytes, filename: str) -> FileAnalysis:
        with tempfile.NamedTemporaryFile(suffix=os.path.splitext(filename)[1], delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            result = self.analyze_file(tmp_path)
            result.filename = filename
            return result
        finally:
            try: os.unlink(tmp_path)
            except: pass
    
    def process(self, prompt: str, files: Optional[List[str]] = None,
                file_data: Optional[List[Tuple[bytes, str]]] = None,
                use_lm_arena: bool = False) -> MultimodalResult:
        import time
        start = time.time()
        
        analyses = []
        if files:
            for f in files:
                if os.path.exists(f):
                    analyses.append(self.analyze_file(f))
        if file_data:
            for data, name in file_data:
                analyses.append(self.analyze_from_bytes(data, name))
        
        sigs = [a.signature_7d for a in analyses if a.error is None]
        fused, R, qe = self.quantum_fusion.fuse(sigs)
        
        hr = 0.0
        if R and len(R) > 1:
            n = len(R)
            hr = sum(R[i][j] for i in range(n) for j in range(i+1, n)) / max(n*(n-1)/2, 1)
        
        enriched = self.prompt_enricher.enrich(prompt, analyses, fused)
        
        response = ""
        if use_lm_arena:
            try:
                from harmonic_lm_arena_engine import HarmonicLMArenaEngine
                response = HarmonicLMArenaEngine().generate(enriched)
            except Exception as e:
                response = f"[Erreur: {e}]"
        
        return MultimodalResult(prompt=prompt, files=analyses, fused_signature=fused,
                              resonance_matrix=R, enriched_prompt=enriched,
                              response=response, processing_time_ms=(time.time()-start)*1000,
                              quantum_entropy=qe, harmonic_resonance=hr)
    
    def process_base64(self, prompt: str, base64_files: List[Tuple[str, str, str]]) -> MultimodalResult:
        file_data = []
        for name, b64, mime in base64_files:
            try:
                file_data.append((base64.b64decode(b64), name))
            except: pass
        return self.process(prompt=prompt, file_data=file_data)


# =========================================================================
# API ENDPOINT (FastAPI)
# =========================================================================

def create_multimodal_router():
    """
    Cree un routeur FastAPI pour l'integration multimodale.
    
    Usage:
        from fastapi import FastAPI
        from harmonic_multimodal_integration import create_multimodal_router
        app = FastAPI()
        app.include_router(create_multimodal_router(), prefix="/api/v1/multimodal")
    """
    from fastapi import APIRouter, UploadFile, File, Form, HTTPException
    from fastapi.responses import JSONResponse
    
    router = APIRouter()
    integrator = MultimodalHarmonicIntegrator()
    
    @router.post("/analyze")
    async def analyze_multimodal(prompt: str = Form(...), files: List[UploadFile] = File(None)):
        try:
            file_data = []
            if files:
                for f in files:
                    content = await f.read()
                    file_data.append((content, f.filename))
            result = integrator.process(prompt=prompt, file_data=file_data if file_data else None, use_lm_arena=True)
            return JSONResponse(content=result.to_dict())
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/analyze-base64")
    async def analyze_multimodal_base64(data: dict):
        try:
            prompt = data.get('prompt', '')
            files = [(f['name'], f['data'], f.get('mime_type', '')) for f in data.get('files', [])]
            result = integrator.process_base64(prompt, files)
            return JSONResponse(content=result.to_dict())
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/health")
    async def health_check():
        return {"status": "ok", "abc_available": integrator.quantum_fusion.abc_available,
                "supported_types": {"image": list(IMAGE_EXTS), "audio": list(AUDIO_EXTS),
                                   "video": list(VIDEO_EXTS), "document": list(DOC_EXTS)}}
    
    return router


# =========================================================================
# TEST UNITAIRE
# =========================================================================

def test_multimodal_integration():
    """Teste l'integration multimodale complete."""
    print("=" * 70)
    print("TEST : Integration Multimodale + Fusion Quantique ABC")
    print("=" * 70)
    
    integrator = MultimodalHarmonicIntegrator()
    
    # Test 1 : Analyse document texte
    print("\n[Test 1] Analyse document texte...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("L'analyse harmonique quantique revolutionne le NLP avec le noyau ABC.")
        tp = f.name
    a = integrator.analyze_file(tp)
    os.unlink(tp)
    assert a.file_type == 'document' and len(a.signature_7d) == 7 and a.error is None
    print(f"  [OK] Signature: [{', '.join(f'{v:.3f}' for v in a.signature_7d)}]")
    
    # Test 2 : Fusion quantique
    print("\n[Test 2] Fusion quantique ABC...")
    s1, s2, s3 = [0.8,0.3,0.2,0.1,0.9,0.4,0.0], [0.3,0.6,0.1,0.8,0.1,0.2,0.0], [0.5,0.4,0.7,0.2,0.3,0.6,0.1]
    fused, R, qe = integrator.quantum_fusion.fuse([s1, s2, s3])
    assert len(fused) == 7 and len(R) == 3
    print(f"  [OK] Fusion: [{', '.join(f'{v:.3f}' for v in fused)}]")
    print(f"  [OK] Entropie quantique: {qe:.4f}")
    
    # Test 3 : Resonance
    print("\n[Test 3] Resonance entre signatures...")
    R12 = integrator.quantum_fusion.compute_resonance(s1, s2)
    R11 = integrator.quantum_fusion.compute_resonance(s1, s1)
    assert 0 <= R12 <= 1
    print(f"  [OK] R(s1,s2)={R12:.4f}, R(s1,s1)={R11:.4f} (attendu ~{PHI/2:.4f})")
    
    # Test 4 : Enrichissement prompt
    print("\n[Test 4] Enrichissement du prompt...")
    enricher = PromptEnricher()
    enriched = enricher.enrich("Analyse ce document", [a], fused)
    assert len(enriched) > len("Analyse ce document")
    assert "[CONTEXTE MULTIMODAL FUSIONNE]" in enriched
    print(f"  [OK] Prompt enrichi ({len(enriched)} car.)")
    
    # Test 5 : Pipeline complet
    print("\n[Test 5] Pipeline complet...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("L'analyse harmonique quantique revolutionne le NLP.")
        dp = f.name
    result = integrator.process(prompt="Analyse ce document", files=[dp])
    os.unlink(dp)
    assert len(result.files) == 1 and len(result.fused_signature) == 7
    print(f"  [OK] {len(result.files)} fichier(s), fusion 7D, temps={result.processing_time_ms:.1f}ms")
    
    # Test 6 : Gestion erreurs
    print("\n[Test 6] Gestion des erreurs...")
    err = integrator.analyze_file("fichier_inexistant.xyz")
    assert err.error is not None
    print(f"  [OK] Fichier inexistant: {err.error}")
    
    # Test 7 : API structure
    print("\n[Test 7] Structure API...")
    router = create_multimodal_router()
    routes = [r.path for r in router.routes]
    print(f"  [OK] Routes: {routes}")
    
    print(f"\n{'=' * 70}")
    print(f"RESULTAT: 7/7 TESTS REUSSIS")
    print(f"{'=' * 70}")
    return True


# =========================================================================
# POINT D'ENTREE
# =========================================================================

if __name__ == '__main__':
    test_multimodal_integration()
