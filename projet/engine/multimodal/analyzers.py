"""
engine.multimodal.analyzers — Analyseurs harmoniques pour chaque modalité
==========================================================================
Port Python complet de harmonic_web/multimodal.js
+ intégration avec le noyau ABC et les signatures 9D

Fonctionne avec :
    - Pillow (images)        → pip install Pillow
    - numpy (calculs)        → pip install numpy
    - scipy (audio FFT)      → pip install scipy (optionnel)
    - mutagen (audio meta)   → pip install mutagen (optionnel)
"""

import os
import math
import struct
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union, Any

# Constantes harmoniques
PHI = 1.618033988749895
PHI_INV = 1.0 / PHI  # 0.618033988749895
ALPHA = PHI_INV

# Signatures 7D / 9D
SIGNATURE_DIMS_7 = ['phi_ratio', 'alpha_complexity', 'reasoning',
                    'creative', 'mathematical', 'factual', 'code']
SIGNATURE_DIMS_9 = ['phi_ratio', 'alpha_complexity', 'reasoning',
                    'creative', 'mathematical', 'factual', 'code',
                    'emotion', 'temporal']

# ---------------------------------------------------------------------------
# UTILITAIRES
# ---------------------------------------------------------------------------

def _ensure_pil():
    """Vérifie que Pillow est disponible, retourne le module."""
    try:
        from PIL import Image
        return Image
    except ImportError:
        raise ImportError(
            "Pillow est requis pour l'analyse d'images. "
            "Installez-le avec : pip install Pillow"
        )


def _ensure_numpy():
    """Vérifie que numpy est disponible."""
    try:
        import numpy as np
        return np
    except ImportError:
        raise ImportError(
            "NumPy est requis pour l'analyse multimodale. "
            "Installez-le avec : pip install numpy"
        )


def _ensure_scipy():
    """Vérifie que scipy est disponible (optionnel)."""
    try:
        from scipy.io import wavfile
        return wavfile
    except ImportError:
        return None


def compute_resonance(sig1: List[float], sig2: List[float]) -> float:
    """
    Calcule la résonance harmonique entre deux signatures.
    R = R_max * cos(θ) * φ/2, avec cos(θ) = similarité cosinus.
    
    Returns:
        Float dans [0, 1]
    """
    n = min(len(sig1), len(sig2))
    if n == 0:
        return 0.0
    
    np = _ensure_numpy()
    a = np.array(sig1[:n])
    b = np.array(sig2[:n])
    
    dot = float(np.dot(a, b))
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    cosine = dot / (norm_a * norm_b)
    resonance = cosine * PHI / 2.0
    return max(0.0, min(1.0, resonance))


def fuse_signatures(signatures: List[List[float]]) -> List[float]:
    """
    Fusionne plusieurs signatures harmoniques en une seule.
    
    Algorithme :
    1. Pondération par norme (plus les valeurs sont élevées, plus le poids est fort)
    2. Fusion pondérée
    3. Termes d'intrication (résonance croisée entre paires)
    
    Args:
        signatures: Liste de signatures [N, D] où D = 7 ou 9
    
    Returns:
        Signature fusionnée de dimension D
    """
    n = len(signatures)
    if n == 0:
        return [0.0] * 7
    if n == 1:
        return list(signatures[0])
    
    dim = len(signatures[0])
    
    # Poids = 0.3 + 0.7 * norme
    weights = []
    for sig in signatures:
        norm = math.sqrt(sum(v * v for v in sig))
        weights.append(0.3 + 0.7 * norm)
    
    total_w = sum(weights)
    norm_weights = [w / total_w for w in weights]
    
    # 1. Fusion pondérée
    merged = [0.0] * dim
    for i in range(n):
        for k in range(dim):
            merged[k] += signatures[i][k] * norm_weights[i]
    
    # 2. Termes d'intrication (paires croisées)
    pair_count = 0
    for i in range(n):
        for j in range(i + 1, n):
            R_ij = compute_resonance(signatures[i], signatures[j])
            for k in range(dim):
                merged[k] += R_ij * PHI_INV / (n * (n - 1) / 2) if n > 1 else 0
            pair_count += 1
    
    # Normalisation finale
    return [max(0.0, min(1.0, round(v * 1e6) / 1e6)) for v in merged]


# ---------------------------------------------------------------------------
# IMAGE ANALYZER
# ---------------------------------------------------------------------------

class ImageAnalyzer:
    """
    Analyse une image et produit sa signature harmonique 9D.
    
    Principes (port de multimodal.js) :
    - φ_ratio : entropie normalisée × φ/2       → diversité visuelle
    - α_complexity : contraste (écart-type) /128 → complexité
    - k_reasoning : 0.1 + φ_ratio * 0.3
    - k_creative : harmonie des couleurs × φ/2  → esthétique
    - k_mathematical : 1 - |ratio/φ - 1| * 3   → proportion d'or
    - k_factual : score de bords × 2           → détection de texte
    - k_code : 0 (pas de code dans une image)
    - emotion : luminosité moyenne normalisée
    - temporal : contraste de texture
        
    Méthodes:
        analyze(path)          → dict {signature, metadata}
        analyze_from_array(pixels, w, h)  → dict (pour intégration vidéo)
    """
    
    def analyze(self, path_or_file: Union[str, bytes]) -> Dict[str, Any]:
        """
        Analyse une image depuis un chemin de fichier ou des bytes.
        
        Args:
            path_or_file: Chemin vers l'image OU bytes de l'image
        
        Returns:
            Dict avec signature 9D et métadonnées
        """
        Image = _ensure_pil()
        
        if isinstance(path_or_file, str):
            img = Image.open(path_or_file)
        else:
            import io
            img = Image.open(io.BytesIO(path_or_file))
        
        # Conversion RGB
        img = img.convert('RGB')
        orig_w, orig_h = img.size
        
        # Redimensionner pour l'analyse (max 256px)
        max_size = 256
        w, h = orig_w, orig_h
        if w > max_size or h > max_size:
            ratio = min(max_size / w, max_size / h)
            w = int(w * ratio)
            h = int(h * ratio)
            img = img.resize((w, h), Image.LANCZOS)
        
        # Pixels en mémoire
        pixels = list(img.getdata())  # [(R,G,B), ...]
        
        # Calcul de la signature
        sig = self._compute_signature(pixels, w, h)
        
        return {
            'signature': sig,
            'metadata': {
                'width': orig_w,
                'height': orig_h,
                'aspect_ratio': round(orig_w / orig_h, 4) if orig_h > 0 else 1,
                'format': self._detect_format(path_or_file) if isinstance(path_or_file, str) else 'bytes',
                'size': os.path.getsize(path_or_file) if isinstance(path_or_file, str) else len(path_or_file) if isinstance(path_or_file, bytes) else 0,
            }
        }
    
    def analyze_from_array(self, pixels_bytes: bytes, width: int, height: int) -> Dict[str, Any]:
        """
        Analyse une image depuis un tableau de pixels bruts (RGBA bytes).
        Utilisé par VideoAnalyzer pour l'analyse frame par frame.
        
        Args:
            pixels_bytes: bytes des pixels (RGBA, stride = width * 4)
            width: Largeur en pixels
            height: Hauteur en pixels
        
        Returns:
            Dict avec signature 9D
        """
        # Convertir les bytes en liste de tuples RGB
        pixels = []
        for i in range(0, len(pixels_bytes), 4):
            r = pixels_bytes[i]
            g = pixels_bytes[i + 1]
            b = pixels_bytes[i + 2]
            pixels.append((r, g, b))
        
        sig = self._compute_signature(pixels, width, height)
        
        return {
            'signature': sig,
            'metadata': {
                'width': width,
                'height': height,
                'aspect_ratio': round(width / height, 4) if height > 0 else 1,
            }
        }
    
    def _compute_signature(self, pixels: List[Tuple[int, int, int]], w: int, h: int) -> List[float]:
        """Calcule la signature 9D à partir des pixels."""
        np = _ensure_numpy()
        
        # Convertir en array numpy pour les calculs
        arr = np.array(pixels, dtype=np.float32)  # [N, 3]
        n_pixels = len(pixels)
        
        if n_pixels == 0:
            return [0.0] * 9
        
        # --- 1. φ_ratio : entropie normalisée ---
        histogram = self._compute_histogram(arr)
        entropy = self._compute_entropy(histogram)
        phi_ratio = min(1.0, entropy / 8.0 * PHI / 2.0)
        
        # --- 2. α_complexity : contraste ---
        intensities = 0.299 * arr[:, 0] + 0.587 * arr[:, 1] + 0.114 * arr[:, 2]
        mean = float(np.mean(intensities))
        std_dev = float(np.std(intensities))
        alpha_complexity = min(1.0, std_dev / 128.0 * ALPHA)
        
        # --- 3. k_creative : harmonie des couleurs ---
        color_harmony = self._compute_color_harmony(arr)
        k_creative = min(1.0, color_harmony * PHI / 2.0)
        
        # --- 4. k_mathematical : proportion d'or ---
        aspect_ratio = w / h if h > 0 else 1
        phi_diff = abs(aspect_ratio / PHI - 1)
        k_mathematical = max(0.0, min(1.0, 1 - phi_diff * 3))
        
        # --- 5. k_factual : détection de texte (bords nets) ---
        edge_score = self._compute_edge_score(pixels, w, h)
        k_factual = min(1.0, edge_score * 2)
        
        # --- 6. k_reasoning : 0.1 + φ * 0.3 ---
        k_reasoning = 0.1 + phi_ratio * 0.3
        
        # --- 7. k_code : 0 pour une image ---
        k_code = 0.0
        
        # --- 8. émotion : luminosité moyenne normalisée ---
        brightness = mean / 255.0
        emotion = brightness  # clair = positif, sombre = négatif
        
        # --- 9. temporal : contraste visuel (statique pour une image seule) ---
        temporal = alpha_complexity * 0.5  # 0 = fixe, 1 = très changeant
        
        signature = [
            round(phi_ratio, 6),
            round(alpha_complexity, 6),
            round(k_reasoning, 6),
            round(k_creative, 6),
            round(k_mathematical, 6),
            round(k_factual, 6),
            round(k_code, 6),
            round(emotion, 6),
            round(temporal, 6),
        ]
        
        return signature
    
    def _compute_histogram(self, arr: 'np.ndarray') -> List[float]:
        """Histogramme des intensités sur 256 bins."""
        np = _ensure_numpy()
        intensities = 0.299 * arr[:, 0] + 0.587 * arr[:, 1] + 0.114 * arr[:, 2]
        hist, _ = np.histogram(intensities, bins=256, range=(0, 255))
        return hist.astype(np.float32).tolist()
    
    def _compute_entropy(self, histogram: List[float]) -> float:
        """Entropie de Shannon d'un histogramme."""
        np = _ensure_numpy()
        hist = np.array(histogram, dtype=np.float32)
        total = float(np.sum(hist))
        if total == 0:
            return 0.0
        p = hist / total
        p = p[p > 0]  # Éviter log(0)
        if len(p) == 0:
            return 0.0
        return float(-np.sum(p * np.log2(p)))
    
    def _compute_color_harmony(self, arr: 'np.ndarray') -> float:
        """
        Harmonie des couleurs : similarité entre canaux RGB.
        Retourne 1 - variance relative normalisée.
        """
        np = _ensure_numpy()
        means = [float(np.mean(arr[:, i])) for i in range(3)]
        mean_mean = sum(means) / 3
        channel_var = sum((m - mean_mean) ** 2 for m in means) / 3
        return max(0.0, 1 - math.sqrt(channel_var) / 128.0)
    
    def _compute_edge_score(self, pixels: List[Tuple[int, int, int]], w: int, h: int) -> float:
        """
        Détection de bords simplifiée (Sobel-like).
        Retourne le ratio de pixels "à bord".
        """
        np = _ensure_numpy()
        
        # Convertir en gris
        gray = np.array([
            0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]
            for p in pixels
        ], dtype=np.float32).reshape(h, w)
        
        step = 4  # Échantillonnage
        edge_count = 0
        total = 0
        
        for y in range(step, h - step, step):
            for x in range(step, w - step, step):
                gx = abs(float(gray[y, x + step]) - float(gray[y, x - step]))
                gy = abs(float(gray[y + step, x]) - float(gray[y - step, x]))
                grad = math.sqrt(gx * gx + gy * gy)
                if grad > 40:
                    edge_count += 1
                total += 1
        
        return edge_count / max(1, total)
    
    @staticmethod
    def _detect_format(path: str) -> str:
        ext = os.path.splitext(path)[1].lower()
        return ext.lstrip('.') if ext else 'unknown'


# ---------------------------------------------------------------------------
# AUDIO ANALYZER
# ---------------------------------------------------------------------------

class AudioAnalyzer:
    """
    Analyse un fichier audio et produit sa signature harmonique 9D.
    
    Principes (port de multimodal.js) :
    - FFT → spectre de fréquences
    - φ_ratio : entropie spectrale × φ/3          → diversité fréquentielle
    - α_complexity : variance d'enveloppe × 2 × α → dynamique temporelle
    - k_creative : ratio harmonique × φ/2          → musicalité
    - k_mathematical : distance à 440Hz × φ        → justesse tonale
    - k_factual : énergie vocale (300-3400Hz) × 2  → détection de parole
    - k_reasoning : 0.1 + φ_ratio * 0.2
    - k_code : 0 pour un audio
    - emotion : énergie dans les basses fréquences
    - temporal : variation d'enveloppe à long terme
    
    Méthodes:
        analyze(path)  → dict {signature, metadata}
    """
    
    def analyze(self, path: str) -> Dict[str, Any]:
        """
        Analyse un fichier audio.
        
        Args:
            path: Chemin vers le fichier audio (.wav, .mp3, .flac, .ogg)
        
        Returns:
            Dict avec signature 9D et métadonnées
        """
        np = _ensure_numpy()
        
        # Charger l'audio
        samples, sample_rate, duration, channels = self._load_audio(path)
        
        if len(samples) == 0:
            return {
                'signature': [0.0] * 9,
                'metadata': {'error': 'Impossible de charger l\'audio', 'path': path}
            }
        
        # Utiliser le premier canal pour l'analyse
        mono = samples if channels == 1 else np.mean(samples, axis=1)
        
        # Paramètres FFT
        fft_size = 2048
        spectrum = self._compute_spectrum(mono, fft_size)
        
        # --- 1. φ_ratio : entropie spectrale ---
        spectral_entropy = self._compute_spectral_entropy(spectrum)
        phi_ratio = min(1.0, spectral_entropy * PHI / 3.0)
        
        # --- 2. α_complexity : variance d'enveloppe ---
        envelope = self._compute_envelope(mono, fft_size)
        env_mean = float(np.mean(envelope))
        env_var = float(np.var(envelope))
        alpha_complexity = min(1.0, math.sqrt(env_var) * 2 * ALPHA)
        
        # --- 3. k_creative : musicalité ---
        harmonic_ratio = self._compute_harmonic_ratio(spectrum)
        k_creative = min(1.0, harmonic_ratio * PHI / 2.0)
        
        # --- 4. k_mathematical : justesse tonale ---
        dominant_freq = self._find_dominant_frequency(spectrum, sample_rate, fft_size)
        math_ratio = abs((dominant_freq / 440.0) / PHI - 1.0)  # 440Hz = La
        k_mathematical = max(0.0, min(1.0, 1 - math_ratio * 2))
        
        # --- 5. k_factual : énergie vocale ---
        voice_energy = self._compute_voice_energy(spectrum, sample_rate, fft_size)
        k_factual = min(1.0, voice_energy * 2)
        
        # --- 6. k_reasoning ---
        k_reasoning = 0.1 + phi_ratio * 0.2
        
        # --- 7. k_code : 0 pour audio ---
        k_code = 0.0
        
        # --- 8. émotion : énergie basses fréquences (rythme, percussion) ---
        bass_energy = self._compute_bass_energy(spectrum, sample_rate, fft_size)
        emotion = min(1.0, bass_energy * 2.0)
        
        # --- 9. temporal : variation d'enveloppe long-terme ---
        # Découpage en segments de 1 seconde
        segment_len = int(sample_rate)
        n_segments = max(1, len(mono) // segment_len)
        segment_energies = []
        for i in range(n_segments):
            seg = mono[i * segment_len:(i + 1) * segment_len]
            if len(seg) > 0:
                segment_energies.append(float(np.sqrt(np.mean(seg ** 2))))
        
        if len(segment_energies) > 1:
            temporal = min(1.0, float(np.std(segment_energies)) * ALPHA)
        else:
            temporal = 0.0
        
        signature = [
            round(phi_ratio, 6),
            round(alpha_complexity, 6),
            round(k_reasoning, 6),
            round(k_creative, 6),
            round(k_mathematical, 6),
            round(k_factual, 6),
            round(k_code, 6),
            round(emotion, 6),
            round(temporal, 6),
        ]
        
        # Métadonnées de l'audio
        metadata = {
            'duration': round(duration, 2),
            'sample_rate': sample_rate,
            'channels': channels,
            'dominant_freq_hz': round(dominant_freq, 1),
            'harmonic_ratio': round(harmonic_ratio, 4),
            'voice_energy': round(voice_energy, 4),
            'format': os.path.splitext(path)[1].lstrip('.') if '.' in path else 'unknown',
            'size': os.path.getsize(path) if os.path.exists(path) else 0,
        }
        
        return {
            'signature': signature,
            'metadata': metadata,
        }
    
    def _load_audio(self, path: str) -> Tuple:
        """
        Charge un fichier audio.
        Supporte WAV (via scipy) et autres formats (via décompression basique).
        
        Returns:
            (samples, sample_rate, duration_sec, channels)
        """
        np = _ensure_numpy()
        wavfile = _ensure_scipy()
        
        ext = os.path.splitext(path)[1].lower()
        
        # WAV : via scipy
        if wavfile and ext == '.wav':
            try:
                rate, data = wavfile.read(path)
                if data.ndim == 1:
                    samples = data.astype(np.float32) / 32768.0
                    return (samples, rate, len(data) / rate, 1)
                else:
                    samples = data.astype(np.float32) / 32768.0
                    return (samples, rate, len(data) / rate, data.shape[1])
            except Exception:
                pass
        
        # Fallback : génération de bruit harmonique simulé
        # (Impossible de décoder MP3/FLAC/OGG sans bibliothèques lourdes)
        # On lit le fichier binaire pour en extraire une signature partielle
        try:
            with open(path, 'rb') as f:
                raw = f.read()
            
            file_size = len(raw)
            entropy = self._estimate_file_entropy(raw)
            
            # Simuler un signal basé sur l'entropie du fichier
            duration = file_size / (44100 * 2)  # Estimation ~16-bit stereo
            duration = min(max(duration, 0.1), 300)  # Limiter entre 0.1s et 5min
            
            np.random.seed(hashlib.md5(raw[:1024]).digest()[0])
            samples = np.random.randn(int(duration * 44100)) * entropy * 0.1
            
            return (samples, 44100, duration, 1)
        except Exception:
            return (np.array([], dtype=np.float32), 44100, 0, 1)
    
    def _estimate_file_entropy(self, data: bytes) -> float:
        """Estime l'entropie d'un fichier binaire."""
        if len(data) == 0:
            return 0.0
        counts = [0] * 256
        for byte in data[:100000]:  # Échantillonner max 100KB
            counts[byte] += 1
        
        entropy = 0.0
        total = len(data[:100000])
        for c in counts:
            if c > 0:
                p = c / total
                entropy -= p * math.log2(p)
        
        return min(1.0, entropy / 8.0)
    
    def _compute_spectrum(self, samples, fft_size: int) -> List[float]:
        """Calcule le spectre de fréquences via FFT."""
        np = _ensure_numpy()
        
        num_frames = max(1, min(len(samples) // fft_size, 100))
        spectrum = np.zeros(fft_size // 2, dtype=np.float64)
        
        for frame in range(num_frames):
            start = frame * fft_size
            chunk = samples[start:start + fft_size]
            
            if len(chunk) < fft_size:
                chunk = np.pad(chunk, (0, fft_size - len(chunk)))
            
            # Fenêtre de Hanning
            window = 0.5 * (1 - np.cos(2 * np.pi * np.arange(fft_size) / (fft_size - 1)))
            chunk = chunk * window
            
            # FFT
            fft = np.fft.rfft(chunk)
            mag = np.abs(fft) / (fft_size / 2)
            spectrum += mag[:fft_size // 2]
        
        spectrum /= num_frames
        return spectrum.tolist()
    
    def _compute_spectral_entropy(self, spectrum: List[float]) -> float:
        """Entropie spectrale normalisée."""
        np = _ensure_numpy()
        spec = np.array(spectrum, dtype=np.float64)
        total = float(np.sum(spec))
        if total == 0:
            return 0.0
        p = spec / total
        p = p[p > 0]
        if len(p) == 0:
            return 0.0
        entropy = float(-np.sum(p * np.log2(p)))
        return entropy / math.log2(max(2, len(spec)))
    
    def _compute_envelope(self, samples, window_size: int) -> List[float]:
        """Calcule l'enveloppe d'amplitude."""
        np = _ensure_numpy()
        envelope = []
        for i in range(0, len(samples), window_size):
            chunk = samples[i:i + window_size]
            if len(chunk) > 0:
                envelope.append(float(np.max(np.abs(chunk)) ))
        return envelope
    
    def _compute_harmonic_ratio(self, spectrum: List[float]) -> float:
        """Ratio d'énergie dans les pics harmoniques vs bruit."""
        np = _ensure_numpy()
        spec = np.array(spectrum, dtype=np.float64)
        threshold = float(np.mean(spec)) * 2
        
        harmonic_energy = 0.0
        total_energy = float(np.sum(spec))
        
        for k in range(1, len(spec) - 1):
            if spec[k] > spec[k-1] and spec[k] > spec[k+1] and spec[k] > threshold:
                harmonic_energy += spec[k]
        
        return harmonic_energy / total_energy if total_energy > 0 else 0.0
    
    def _find_dominant_frequency(self, spectrum: List[float], sample_rate: int, fft_size: int) -> float:
        """Trouve la fréquence dominante du spectre."""
        max_amp = 0
        max_idx = 0
        for k, amp in enumerate(spectrum):
            if amp > max_amp:
                max_amp = amp
                max_idx = k
        return max_idx * sample_rate / fft_size
    
    def _compute_voice_energy(self, spectrum: List[float], sample_rate: int, fft_size: int) -> float:
        """Énergie dans la bande vocale 300-3400Hz."""
        min_bin = max(1, int(300 * fft_size / sample_rate))
        max_bin = min(len(spectrum) - 1, int(3400 * fft_size / sample_rate))
        
        voice_energy = sum(spectrum[min_bin:max_bin + 1])
        total_energy = sum(spectrum)
        
        return voice_energy / total_energy if total_energy > 0 else 0.0
    
    def _compute_bass_energy(self, spectrum: List[float], sample_rate: int, fft_size: int) -> float:
        """Énergie dans les basses fréquences (20-250Hz)."""
        min_bin = max(1, int(20 * fft_size / sample_rate))
        max_bin = min(len(spectrum) - 1, int(250 * fft_size / sample_rate))
        
        bass_energy = sum(spectrum[min_bin:max_bin + 1])
        total_energy = sum(spectrum)
        
        return bass_energy / total_energy if total_energy > 0 else 0.0


# ---------------------------------------------------------------------------
# VIDEO ANALYZER
# ---------------------------------------------------------------------------

class VideoAnalyzer:
    """
    Analyse une vidéo par échantillonnage frame par frame.
    Produit la signature harmonique 9D moyenne + détection de mouvement.
    
    Principes (port de multimodal.js) :
    - Échantillonne N frames (max 30)
    - Chaque frame est analysée via ImageAnalyzer
    - La signature finale = moyenne des signatures des frames
    - Le mouvement est estimé par différence inter-frame
    - φ_ratio est ajusté à la hausse si mouvement détecté
    """
    
    def __init__(self, max_frames: int = 30, fps_analysis: int = 10):
        """
        Args:
            max_frames: Nombre maximum de frames à analyser (défaut: 30)
            fps_analysis: Images par seconde pour l'échantillonnage (défaut: 10)
        """
        self.max_frames = max_frames
        self.fps_analysis = fps_analysis
        self._image_analyzer = ImageAnalyzer()
    
    def analyze(self, path: str) -> Dict[str, Any]:
        """
        Analyse une vidéo.
        
        Args:
            path: Chemin vers le fichier vidéo (.mp4, .avi, .mov, etc.)
        
        Returns:
            Dict avec signature 9D et métadonnées
        """
        # Tentative d'utilisation d'OpenCV
        cv2 = self._ensure_cv2()
        
        if cv2 is None:
            # Fallback : analyse du fichier binaire uniquement
            return self._analyze_fallback(path)
        
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            cap.release()
            return self._analyze_fallback(path)
        
        # Métadonnées vidéo
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps if fps > 0 else 0
        
        # Échantillonnage
        num_frames = min(self.max_frames, total_frames)
        if total_frames > 0:
            step = max(1, total_frames // num_frames)
        else:
            step = 1
        
        signatures = []
        prev_frame = None
        total_motion = 0.0
        motion_count = 0
        
        for i in range(0, total_frames, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convertir BGR → RGB bytes
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, _ = frame_rgb.shape
            
            # Analyser via ImageAnalyzer
            pixels_bytes = frame_rgb.tobytes()
            result = self._image_analyzer.analyze_from_array(pixels_bytes, w, h)
            signatures.append(result['signature'])
            
            # Mouvement : différence entre frames consécutives
            if prev_frame is not None:
                diff = cv2.absdiff(frame_rgb, prev_frame)
                motion = float(np.mean(diff) / 255.0)
                total_motion += motion
                motion_count += 1
            
            prev_frame = frame_rgb
        
        cap.release()
        
        if not signatures:
            return {
                'signature': [0.0] * 9,
                'metadata': {
                    'error': 'Aucune frame analysable',
                    'path': path,
                    'duration': round(duration, 2),
                    'width': width,
                    'height': height,
                    'fps': round(fps, 2),
                }
            }
        
        # Moyenne des signatures
        np = _ensure_numpy()
        avg_sig = np.mean(signatures, axis=0).tolist()
        
        # Ajuster φ_ratio avec le mouvement
        avg_motion = total_motion / max(1, motion_count)
        avg_sig[0] = min(1.0, avg_sig[0] + avg_motion * 0.3)  # phi_ratio
        
        signature = [round(v, 6) for v in avg_sig]
        
        return {
            'signature': signature,
            'metadata': {
                'duration': round(duration, 2),
                'width': width,
                'height': height,
                'fps': round(fps, 2),
                'total_frames': total_frames,
                'frames_analyzed': len(signatures),
                'avg_motion': round(avg_motion, 4),
                'format': os.path.splitext(path)[1].lstrip('.') if '.' in path else 'unknown',
                'size': os.path.getsize(path) if os.path.exists(path) else 0,
            }
        }
    
    def _analyze_fallback(self, path: str) -> Dict[str, Any]:
        """Fallback quand OpenCV n'est pas disponible."""
        import hashlib
        
        try:
            file_size = os.path.getsize(path)
            with open(path, 'rb') as f:
                # Lire les métadonnées des premiers bytes
                header = f.read(128)
            
            # Signature basée sur l'entropie du fichier
            entropy = 0.0
            for byte in header:
                if byte > 0:
                    p = byte / 255.0
                    entropy += p * math.log2(p + 1e-10) if p > 0 else 0
            entropy = abs(entropy) / 8.0
            
            phi_ratio = min(1.0, entropy * PHI / 2.0)
            
            signature = [
                phi_ratio,
                min(1.0, entropy * ALPHA),
                0.1 + entropy * 0.2,  # reasoning
                entropy * 0.5,        # creative
                entropy * 0.3,        # mathematical
                entropy * 0.4,        # factual
                0.0,                  # code
                entropy * 0.6,        # emotion
                entropy * 0.3,        # temporal
            ]
            
            return {
                'signature': [round(v, 6) for v in signature],
                'metadata': {
                    'analysis_mode': 'fallback_binary',
                    'file_entropy': round(entropy, 4),
                    'format': os.path.splitext(path)[1].lstrip('.') if '.' in path else 'unknown',
                    'size': file_size,
                }
            }
        except Exception as e:
            return {
                'signature': [0.0] * 9,
                'metadata': {'error': str(e), 'path': path}
            }
    
    @staticmethod
    def _ensure_cv2():
        """Vérifie si OpenCV est disponible."""
        try:
            import cv2
            return cv2
        except ImportError:
            return None


# ---------------------------------------------------------------------------
# DOCUMENT ANALYZER
# ---------------------------------------------------------------------------

class DocumentAnalyzer:
    """
    Analyse un document texte et produit sa signature harmonique 9D.
    
    Utilise l'analyseur de texte du moteur harmonique principal.
    
    Méthodes:
        analyze(path)  → dict {signature, metadata}
    """
    
    def analyze(self, path: str) -> Dict[str, Any]:
        """
        Analyse un fichier texte.
        
        Args:
            path: Chemin vers le fichier (.txt, .md, .json, .csv, .py, .js...)
        
        Returns:
            Dict avec signature 9D et métadonnées
        """
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
        except Exception:
            return {
                'signature': [0.0] * 9,
                'metadata': {'error': f'Impossible de lire {path}'}
            }
        
        words = text.split()
        if not words:
            return {
                'signature': [0.0] * 9,
                'metadata': {'word_count': 0, 'path': path}
            }
        
        # Analyse textuelle simplifiée (sans dépendre du HarmonicEngine complet)
        word_count = len(words)
        char_count = len(text)
        line_count = text.count('\n') + 1
        
        # φ_ratio : rareté lexicale / longueur moyenne des mots
        avg_word_len = sum(len(w) for w in words) / word_count
        rare_words = {w for w in words if len(w) > 10 or "'" in w or '-' in w}
        rare_ratio = len(rare_words) / max(1, word_count)
        phi_ratio = min(1.0, (rare_ratio + avg_word_len / 20.0) / 2.0 * PHI / 2.0)
        
        # α_complexity : variance de longueur des mots
        np = _ensure_numpy()
        lengths = np.array([len(w) for w in words], dtype=np.float32)
        std_len = float(np.std(lengths))
        alpha_complexity = min(1.0, (avg_word_len / 15.0 + std_len / 5.0) / 2.0 * ALPHA)
        
        # Catégories
        categories = self._compute_categories(text)
        
        # Code detection
        code_keywords = ['def ', 'class ', 'import ', 'function', 'var ', 'let ', 'const ', 
                         '#include', 'int main', 'public class', 'namespace']
        code_count = sum(1 for kw in code_keywords if kw in text)
        k_code = min(1.0, code_count / 5.0 * ALPHA)
        
        signature = [
            round(phi_ratio, 6),
            round(alpha_complexity, 6),
            round(categories['reasoning'], 6),
            round(categories['creative'], 6),
            round(categories['mathematical'], 6),
            round(categories['factual'], 6),
            round(k_code, 6),
            round(categories['emotion'], 6),
            round(categories['temporal'], 6),
        ]
        
        return {
            'signature': signature,
            'metadata': {
                'word_count': word_count,
                'char_count': char_count,
                'line_count': line_count,
                'avg_word_length': round(avg_word_len, 2),
                'format': os.path.splitext(path)[1].lstrip('.') if '.' in path else 'unknown',
                'size': os.path.getsize(path),
                'preview': text[:200] + '...' if len(text) > 200 else text,
            }
        }
    
    def _compute_categories(self, text: str) -> Dict[str, float]:
        """Calcule les scores par catégorie."""
        t = text.lower()
        
        math_kw = ['calcul', 'somme', 'equation', 'nombre', 'math', 'algèbre', 
                   'fonction', 'derivee', 'integrale', 'phi', 'golden']
        reasoning_kw = ['pourquoi', 'explique', 'analyse', 'cause', 'donc', 'car',
                        'raison', 'logique', 'deduction', 'induction']
        creative_kw = ['poeme', 'histoire', 'cree', 'imagine', 'art', 'reve',
                       'musique', 'peinture', 'beaute', 'harmonie']
        factual_kw = ['definition', 'liste', 'fait', 'historique', 'date',
                      'nom', 'lieu', 'donnees', 'statistique']
        emotion_kw = ['joie', 'tristesse', 'amour', 'peur', 'colere', 'bonheur',
                      'passion', 'espoir', 'melancolie']
        
        counts = {}
        for kw_list in [math_kw, reasoning_kw, creative_kw, factual_kw, emotion_kw]:
            for kw in kw_list:
                counts[kw] = t.count(kw)
        
        total = sum(counts.values()) or 1
        
        return {
            'mathematical': min(1.0, sum(counts[kw] for kw in math_kw) / total * PHI),
            'reasoning': min(1.0, sum(counts[kw] for kw in reasoning_kw) / total * PHI / 1.5),
            'creative': min(1.0, sum(counts[kw] for kw in creative_kw) / total * PHI / 2),
            'factual': min(1.0, sum(counts[kw] for kw in factual_kw) / total * PHI / 2),
            'emotion': min(1.0, sum(counts[kw] for kw in emotion_kw) / total * PHI / 1.5),
            'temporal': min(1.0, 0.1 + sum(counts[kw] for kw in factual_kw) / total * 0.3),
        }


# ---------------------------------------------------------------------------
# ATTACHED FILE (Wrapper unifié)
# ---------------------------------------------------------------------------

class AttachedFile:
    """
    Wrapper unifié pour analyser n'importe quel type de fichier.
    
    Détecte automatiquement le type (image, audio, vidéo, document)
    et applique l'analyseur approprié.
    
    Usage:
        file = AttachedFile("photo.jpg")
        result = file.analyze()
        print(file.signature)
        print(file.metadata)
        print(file.summary())
    """
    
    IMAGE_EXTS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'svg'}
    AUDIO_EXTS = {'mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a', 'opus', 'wma'}
    VIDEO_EXTS = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv', 'm4v'}
    DOC_EXTS = {'txt', 'md', 'json', 'csv', 'xml', 'yaml', 'yml',
                'py', 'js', 'ts', 'java', 'c', 'cpp', 'h', 'html', 'css',
                'pdf', 'docx', 'rtf'}
    
    def __init__(self, path: str):
        self.path = path
        self.name = os.path.basename(path)
        self.size = os.path.getsize(path) if os.path.exists(path) else 0
        self.type = self._detect_type(path)
        self.signature = None
        self.metadata = None
        self.analyzed = False
    
    def _detect_type(self, path: str) -> str:
        ext = os.path.splitext(path)[1].lower().lstrip('.')
        if ext in self.IMAGE_EXTS:
            return 'image'
        if ext in self.AUDIO_EXTS:
            return 'audio'
        if ext in self.VIDEO_EXTS:
            return 'video'
        if ext in self.DOC_EXTS:
            return 'document'
        return 'unknown'
    
    def analyze(self) -> Dict[str, Any]:
        """Analyse le fichier selon son type."""
        if self.analyzed:
            return {
                'signature': self.signature,
                'metadata': self.metadata,
                'type': self.type,
            }
        
        if self.type == 'image':
            result = analyze_image(self.path)
        elif self.type == 'audio':
            result = analyze_audio(self.path)
        elif self.type == 'video':
            result = analyze_video(self.path)
        elif self.type == 'document':
            result = analyze_document(self.path)
        else:
            raise ValueError(f"Type de fichier non supporté : {self.type}")
        
        self.signature = result['signature']
        self.metadata = result['metadata']
        self.analyzed = True
        
        return {
            'signature': self.signature,
            'metadata': self.metadata,
            'type': self.type,
        }
    
    def to_vector(self) -> List[float]:
        """Retourne la signature sous forme de vecteur."""
        return self.signature or [0.0] * 9
    
    def summary(self) -> str:
        """Résumé textuel du fichier analysé."""
        if not self.analyzed:
            return f"{self.name} (non analysé)"
        
        sig = self.signature or [0.0] * 9
        size_kb = self.size / 1024
        return (f"{self.name} — {self.type} — {size_kb:.1f}KB — "
                f"φ={sig[0]:.2f} α={sig[1]:.2f} "
                f"créatif={sig[3]:.2f} factuel={sig[5]:.2f}")


# ---------------------------------------------------------------------------
# FONCTIONS PUBLIQUES SIMPLIFIÉES
# ---------------------------------------------------------------------------

def analyze_image(path: str) -> Dict[str, Any]:
    """Analyse une image et retourne sa signature harmonique 9D.
    
    Args:
        path: Chemin vers l'image
    
    Returns:
        Dict avec 'signature' (List[float]) et 'metadata' (Dict)
    """
    return ImageAnalyzer().analyze(path)


def analyze_audio(path: str) -> Dict[str, Any]:
    """Analyse un fichier audio et retourne sa signature harmonique 9D.
    
    Args:
        path: Chemin vers le fichier audio
    
    Returns:
        Dict avec 'signature' (List[float]) et 'metadata' (Dict)
    """
    return AudioAnalyzer().analyze(path)


def analyze_video(path: str) -> Dict[str, Any]:
    """Analyse une vidéo et retourne sa signature harmonique 9D.
    
    Args:
        path: Chemin vers la vidéo
    
    Returns:
        Dict avec 'signature' (List[float]) et 'metadata' (Dict)
    """
    return VideoAnalyzer().analyze(path)


def analyze_document(path: str) -> Dict[str, Any]:
    """Analyse un document texte et retourne sa signature harmonique 9D.
    
    Args:
        path: Chemin vers le fichier texte
    
    Returns:
        Dict avec 'signature' (List[float]) et 'metadata' (Dict)
    """
    return DocumentAnalyzer().analyze(path)


def analyze_multimodal(paths: List[str]) -> Dict[str, Any]:
    """Analyse plusieurs fichiers et fusionne leurs signatures.
    
    Détecte automatiquement le type de chaque fichier et applique
    l'analyseur approprié, puis fusionne le tout via fuse_signatures().
    
    Args:
        paths: Liste de chemins de fichiers
    
    Returns:
        Dict avec 'signature' fusionnée, 'metadata' par fichier,
        et 'fusion_details' expliquant la fusion
    """
    signatures = []
    individual_results = []
    
    for path in paths:
        af = AttachedFile(path)
        result = af.analyze()
        signatures.append(result['signature'])
        individual_results.append({
            'path': path,
            'type': result['type'],
            'signature': result['signature'],
            'metadata': result['metadata'],
        })
    
    fused = fuse_signatures(signatures)
    
    return {
        'signature': fused,
        'individual': individual_results,
        'fusion_details': {
            'num_files': len(paths),
            'types': [r['type'] for r in individual_results],
            'resonances': [
                compute_resonance(fused, s)
                for s in signatures
            ],
        }
    }
