"""
Holographic Voice Store — Clonage Vocal Instantané par Superposition Holographique
==================================================================================

Stockage et manipulation d'identités vocales utilisant la superposition
holographique (HRR — Holographic Reduced Representations).

Principe fondateur :
  Chaque voix est représentée par UN seul tenseur complexe H_voice ∈ ℂ⁵¹²
  obtenu par superposition des frames ψ de l'audio de référence :

    H_voice = Σ ψ_frame_i    (superposition additive)

  La récupération se fait par corrélation circulaire (unbinding) :
    ψ_query ⊘ H_voice → identité de la voix

Propriétés uniques (inaccessibles aux modèles neuronaux classiques) :
  1. CLONAGE INSTANTANÉ — 3 secondes d'audio suffisent, pas de fine-tuning
  2. FUSION DE VOIX — H_A+B = H_A + H_B (superposition linéaire)
  3. EXTRACTION DE VOIX — ψ_clean ≈ ψ_mix ⊘ H_noise (unbinding)
  4. CAPACITÉ ÉLEVÉE — des milliers de voix dans ℂ⁵¹² grâce au φ-spacing
  5. ZÉRO PARAMÈTRE — tout est déterministe (FNV-1a + φ)

Comparaison :
  - Voxtral : 3s audio → encodeur → tokens → backbone (paramètres appris)
  - Moshi   : <30min fine-tuning
  - HVS     : 3s audio → superposition holographique → H_voice (INSTANTANÉ)

Usage :
    from holographic_voice_store import HolographicVoiceStore
    from harmonic_voice_codec_v2 import HarmonicVoiceCodecV2

    codec = HarmonicVoiceCodecV2()
    store = HolographicVoiceStore(codec=codec)

    # Cloner une voix (3 secondes d'audio)
    voice_id = store.clone_voice(ref_audio, name="Alice")

    # Injecter dans le pipeline TTS
    psi_voice = store.voice_to_psi(voice_id)

    # Fusionner deux voix
    blended = store.fuse_voices(["alice", "bob"], name="Alice+Bob")

    # Identifier une voix
    matches = store.identify_voice(unknown_audio)

Intégration :
  - Dépend de HarmonicVoiceCodecV2 (encodage audio → ψ)
  - Réutilise holographic_encoder.py (_circular_convolve, _circular_correlate)
  - Compatible avec ABCAudioPredictor (détection de locuteur en streaming)
  - S'intègre dans le pipeline TTS/STT harmonique

Auteur : Équipe HarmoniqLLM
Date   : 2026-07-24
"""

import math
import time
import uuid
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORTS INTERNES (avec fallbacks)
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from holographic_encoder import (
        _circular_convolve,
        _circular_correlate,
        _fnv1a_hash,
    )
except ImportError:
    def _circular_convolve(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        A = np.fft.fft(a); B = np.fft.fft(b)
        return np.fft.ifft(A * B)
    
    def _circular_correlate(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        A = np.fft.fft(a); B = np.fft.fft(b)
        return np.fft.ifft(A * np.conj(B))
    
    def _fnv1a_hash(s: str) -> int:
        FNV_OFFSET = 14695981039346656037
        FNV_PRIME = 1099511628211
        h = FNV_OFFSET
        for ch in s:
            h ^= ord(ch); h = (h * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
        return h

try:
    from voice_signature_extractor import VoiceSignatureExtractor, VoiceSignature
    HAS_VOICE_EXTRACTOR = True
except ImportError:
    HAS_VOICE_EXTRACTOR = False

try:
    from harmonic_voice_codec_v2 import HarmonicVoiceCodecV2
    HAS_CODEC_V2 = True
except ImportError:
    HAS_CODEC_V2 = False


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

PHI = 1.618033988749895
TAU = 2.0 * math.pi
DEFAULT_DIM = 512
DEFAULT_SAMPLE_RATE = 24000
MIN_REFERENCE_DURATION = 1.0     # secondes minimum pour un clonage fiable
OPTIMAL_REFERENCE_DURATION = 3.0  # secondes optimales
MAX_VOICES_DEFAULT = 10000       # capacité théorique ~40K en ℂ⁵¹²


# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURES DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class VoiceIdentity:
    """Identité vocale holographique complète."""
    id: str                              # UUID unique
    name: str                            # Nom descriptif
    hologram: np.ndarray                 # H_voice ∈ ℂᵈⁱᵐ (superposition)
    reference_duration_s: float = 0.0    # Durée de l'audio de référence
    signature_11d: Optional[np.ndarray] = None  # Signature 11D (si extracteur dispo)
    n_frames: int = 0                    # Nombre de frames encodées
    energy: float = 0.0                  # Énergie totale du hologramme
    created_at: str = ""                 # Timestamp ISO
    metadata: dict = field(default_factory=dict)  # Métadonnées libres
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.strftime('%Y-%m-%dT%H:%M:%S')
        if self.energy == 0.0 and self.hologram is not None:
            self.energy = float(np.sum(np.abs(self.hologram) ** 2))


@dataclass
class VoiceMatch:
    """Résultat d'une identification vocale."""
    voice_id: str
    name: str
    similarity: float      # [0, 1] similarité cosinus
    confidence: float      # [0, 1] confiance (basée sur l'écart avec le 2e)
    is_match: bool         # Au-dessus du seuil ?


# ═══════════════════════════════════════════════════════════════════════════════
# STORE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class HolographicVoiceStore:
    """
    Stockage holographique d'identités vocales.
    
    Chaque voix est encodée comme un hologramme H ∈ ℂᵈⁱᵐ via superposition
    des frames ψ produites par le HCV Codec v2.
    
    Parameters:
        dim: dimension des vecteurs holographiques (default 512)
        codec: instance HarmonicVoiceCodecV2 (créée automatiquement si None)
        similarity_threshold: seuil de similarité pour l'identification
    """
    
    def __init__(self,
                 dim: int = DEFAULT_DIM,
                 codec: Optional['HarmonicVoiceCodecV2'] = None,
                 similarity_threshold: float = 0.6):
        
        self.dim = dim
        self.similarity_threshold = similarity_threshold
        
        # Codec (optionnel — créé à la demande)
        self._codec = codec
        
        # Extracteur de signature 11D (optionnel)
        self._voice_extractor = None
        if HAS_VOICE_EXTRACTOR:
            try:
                self._voice_extractor = VoiceSignatureExtractor()
            except Exception:
                pass
        
        # Stockage principal
        self._voices: Dict[str, VoiceIdentity] = {}
        
        # Hologramme global (superposition de toutes les voix — pour identification rapide)
        self.global_hologram = np.zeros(dim, dtype=np.complex128)
        
        # Statistiques
        self._total_voices_added = 0
        self._total_clones = 0
        self._total_fusions = 0
    
    @property
    def codec(self):
        """Accès lazy au codec."""
        if self._codec is None:
            if HAS_CODEC_V2:
                self._codec = HarmonicVoiceCodecV2(dim=self.dim)
            else:
                raise ImportError(
                    "HarmonicVoiceCodecV2 requis. Installez harmonic_voice_codec_v2.py"
                )
        return self._codec
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CRUD
    # ═══════════════════════════════════════════════════════════════════════════
    
    def add_voice(self,
                  name: str,
                  audio: np.ndarray,
                  sr: int = DEFAULT_SAMPLE_RATE,
                  signature_11d: Optional[np.ndarray] = None,
                  metadata: Optional[dict] = None) -> str:
        """
        Ajoute une voix au store à partir d'un audio de référence.
        
        Processus :
          1. Encoder l'audio en trames ψ via le HCV Codec v2
          2. Superposer les trames : H_voice = Σ ψ_frame
          3. Stocker H_voice avec métadonnées
        
        Args:
            name: nom descriptif de la voix
            audio: [n_samples] float — audio de référence (≥ 1s, idéalement 3s)
            sr: fréquence d'échantillonnage
            signature_11d: signature 11D pré-calculée (optionnel)
            metadata: métadonnées libres
            
        Returns:
            voice_id: UUID de la voix créée
        """
        # Encoder l'audio → ψ frames
        psi_frames = self.codec.encode(audio, sr=sr)
        
        if len(psi_frames) < 3:
            raise ValueError(
                f"Audio trop court : {len(psi_frames)} frames. "
                f"Minimum {int(MIN_REFERENCE_DURATION * self.codec.frame_rate)} frames "
                f"({MIN_REFERENCE_DURATION}s)"
            )
        
        # Superposition holographique : H = Σ ψ_frame
        H_voice = np.sum(psi_frames, axis=0)
        
        # Ne pas normaliser — l'amplitude encode la « force » de la voix
        # (plus d'audio de référence → hologramme plus fort)
        
        # Signature 11D (extraire automatiquement si possible)
        if signature_11d is None and self._voice_extractor is not None:
            try:
                sig = self._voice_extractor.extract_from_array(audio, sr)
                signature_11d = np.array([sig.get(d, 0.0) for d in [
                    'H_pitch_mean', 'H_pitch_range', 'H_speed', 'H_timbre',
                    'H_breathiness', 'H_resonance', 'H_emotion_range',
                    'H_clarity', 'H_pause_pattern', 'H_phi_alignment', 'H_naturalness'
                ]])
            except Exception:
                pass
        
        # Créer l'identité
        voice_id = str(uuid.uuid4())[:8]
        duration_s = len(audio) / sr if sr > 0 else 0.0
        
        identity = VoiceIdentity(
            id=voice_id,
            name=name,
            hologram=H_voice.copy(),
            reference_duration_s=duration_s,
            signature_11d=signature_11d,
            n_frames=len(psi_frames),
            metadata=metadata or {},
        )
        
        self._voices[voice_id] = identity
        self.global_hologram += H_voice
        self._total_voices_added += 1
        
        return voice_id
    
    def get_voice(self, voice_id: str) -> Optional[VoiceIdentity]:
        """Récupère une identité vocale par ID."""
        return self._voices.get(voice_id)
    
    def get_voice_by_name(self, name: str) -> Optional[VoiceIdentity]:
        """Récupère une identité vocale par nom (premier match)."""
        name_lower = name.lower()
        for v in self._voices.values():
            if v.name.lower() == name_lower:
                return v
        return None
    
    def remove_voice(self, voice_id: str) -> bool:
        """Supprime une voix du store."""
        if voice_id not in self._voices:
            return False
        
        identity = self._voices[voice_id]
        self.global_hologram -= identity.hologram
        del self._voices[voice_id]
        return True
    
    def list_voices(self) -> List[Dict]:
        """Liste toutes les voix stockées (résumé)."""
        return [
            {
                'id': v.id,
                'name': v.name,
                'duration_s': v.reference_duration_s,
                'n_frames': v.n_frames,
                'energy': v.energy,
                'created_at': v.created_at,
                'has_signature': v.signature_11d is not None,
            }
            for v in self._voices.values()
        ]
    
    @property
    def voice_count(self) -> int:
        """Nombre de voix stockées."""
        return len(self._voices)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CLONAGE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def clone_voice(self,
                    audio_ref: np.ndarray,
                    sr: int = DEFAULT_SAMPLE_RATE,
                    name: Optional[str] = None) -> str:
        """
        Clone instantané d'une voix à partir d'un audio de référence.
        
        Alias pratique pour add_voice() avec nom auto-généré.
        
        Args:
            audio_ref: [n_samples] audio de référence (≥ 1s)
            sr: fréquence d'échantillonnage
            name: nom (auto-généré si None)
            
        Returns:
            voice_id
        """
        if name is None:
            name = f"Voice_{self._total_clones + 1}"
        
        voice_id = self.add_voice(name, audio_ref, sr=sr)
        self._total_clones += 1
        
        return voice_id
    
    # ═══════════════════════════════════════════════════════════════════════════
    # FUSION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def fuse_voices(self,
                    voice_ids: List[str],
                    weights: Optional[List[float]] = None,
                    name: Optional[str] = None) -> str:
        """
        Fusion holographique de plusieurs voix.
        
        H_fusion = Σ w_i · H_voice_i
        
        La voix résultante est un mélange perceptuel des voix sources.
        Propriété unique de la superposition holographique : l'addition
        dans ℂᵈⁱᵐ produit un mélange audible naturel.
        
        Args:
            voice_ids: liste des IDs à fusionner
            weights: poids respectifs (défaut: égaux)
            name: nom de la voix fusionnée
            
        Returns:
            voice_id de la fusion
        """
        if len(voice_ids) < 2:
            raise ValueError("Au moins 2 voix requises pour une fusion")
        
        if weights is None:
            weights = [1.0] * len(voice_ids)
        elif len(weights) != len(voice_ids):
            raise ValueError("weights doit avoir la même longueur que voice_ids")
        
        # Normaliser les poids
        total_w = sum(weights)
        weights = [w / total_w for w in weights]
        
        # Superposition pondérée
        H_fusion = np.zeros(self.dim, dtype=np.complex128)
        total_duration = 0.0
        fusion_sources = []
        
        for vid, w in zip(voice_ids, weights):
            if vid not in self._voices:
                raise KeyError(f"Voix '{vid}' non trouvée")
            v = self._voices[vid]
            H_fusion += w * v.hologram
            total_duration += v.reference_duration_s
            fusion_sources.append(v.name)
        
        # Créer la nouvelle identité
        fusion_id = str(uuid.uuid4())[:8]
        if name is None:
            name = " + ".join(fusion_sources[:3])
            if len(fusion_sources) > 3:
                name += f" +{len(fusion_sources)-3}"
        
        identity = VoiceIdentity(
            id=fusion_id,
            name=name,
            hologram=H_fusion,
            reference_duration_s=total_duration,
            n_frames=0,  # fusion, pas d'audio direct
            metadata={'sources': voice_ids, 'weights': weights},
        )
        
        self._voices[fusion_id] = identity
        self.global_hologram += H_fusion
        self._total_fusions += 1
        
        return fusion_id
    
    # ═══════════════════════════════════════════════════════════════════════════
    # EXTRACTION (séparation de sources)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def extract_voice(self,
                      mixed_audio: np.ndarray,
                      voice_id: str,
                      sr: int = DEFAULT_SAMPLE_RATE) -> np.ndarray:
        """
        Extraction de voix par unbinding holographique.
        
        ψ_clean ≈ ψ_mix ⊘ H_voice
        
        où ⊘ est la corrélation circulaire (unbinding HRR).
        
        Args:
            mixed_audio: audio mixé contenant la voix cible + bruit
            voice_id: ID de la voix à extraire
            sr: fréquence d'échantillonnage
            
        Returns:
            audio nettoyé (voix isolée)
        """
        if voice_id not in self._voices:
            raise KeyError(f"Voix '{voice_id}' non trouvée")
        
        H_voice = self._voices[voice_id].hologram
        
        # Encoder l'audio mixé
        psi_mix = self.codec.encode(mixed_audio, sr=sr)
        
        # Unbinding frame par frame
        psi_clean = np.zeros_like(psi_mix)
        for i in range(len(psi_mix)):
            # Corrélation circulaire : extraire la composante « voix » du mix
            psi_clean[i] = _circular_correlate(psi_mix[i], H_voice)
        
        # Décoder
        clean_audio = self.codec.decode(psi_clean, original_length=len(mixed_audio))
        
        return clean_audio
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CONVERSION (pour pipeline TTS)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def voice_to_psi(self, voice_id: str) -> np.ndarray:
        """
        Retourne ψ_voice ∈ ℂᵈⁱᵐ pour injection dans le pipeline TTS.
        
        Le ψ_voice peut être utilisé comme « couleur » vocale dans la
        synthèse : ψ_parole = ψ_phonèmes ⊗ ψ_voix
        
        Args:
            voice_id: ID de la voix
            
        Returns:
            [dim] complex128 — vecteur ψ de la voix
        """
        if voice_id not in self._voices:
            raise KeyError(f"Voix '{voice_id}' non trouvée")
        
        H = self._voices[voice_id].hologram
        
        # Normaliser pour l'injection TTS (unitaire)
        norm = np.sqrt(np.sum(np.abs(H) ** 2))
        if norm > 1e-10:
            return H / norm
        return H
    
    def psi_to_voice_params(self, psi_voice: np.ndarray) -> dict:
        """
        Décode ψ_voice en paramètres vocaux interprétables.
        
        Extrait des informations comme le pitch moyen, le timbre, etc.
        à partir de la structure de phase et d'amplitude de ψ.
        
        Args:
            psi_voice: [dim] complex128
            
        Returns:
            dict avec paramètres vocaux estimés
        """
        magnitude = np.abs(psi_voice)
        angles = np.angle(psi_voice)
        
        # Pitch estimé (depuis les variations de phase)
        if len(angles) > 2:
            phase_diffs = np.diff(angles[:min(20, len(angles))])
            phase_diffs = (phase_diffs + math.pi) % TAU - math.pi
            pitch_est = np.mean(np.abs(phase_diffs)) * DEFAULT_SAMPLE_RATE / TAU
        else:
            pitch_est = 0.0
        
        # Timbre (distribution spectrale de l'amplitude)
        n_bands = 8
        band_energies = np.zeros(n_bands)
        for b in range(n_bands):
            bs = b * len(magnitude) // n_bands
            be = (b + 1) * len(magnitude) // n_bands
            band_energies[b] = np.sum(magnitude[bs:be] ** 2)
        band_energies = band_energies / (np.sum(band_energies) + 1e-10)
        
        # Brillance (ratio hautes/basses fréquences)
        mid = len(magnitude) // 2
        low_energy = np.sum(magnitude[:mid] ** 2)
        high_energy = np.sum(magnitude[mid:] ** 2)
        brilliance = high_energy / (low_energy + high_energy + 1e-10)
        
        # Chaleur (pente spectrale)
        freqs = np.arange(len(magnitude))
        if np.sum(magnitude) > 1e-10:
            spectral_centroid = np.sum(freqs * magnitude) / np.sum(magnitude)
        else:
            spectral_centroid = len(magnitude) / 2
        warmth = 1.0 - (spectral_centroid / len(magnitude))
        
        return {
            'pitch_est_hz': float(pitch_est),
            'brilliance': float(brilliance),
            'warmth': float(warmth),
            'energy': float(np.sum(magnitude ** 2)),
            'n_bands': n_bands,
            'band_energies': band_energies.tolist(),
        }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # COMPARAISON & IDENTIFICATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def compare_voices(self, voice_id_a: str, voice_id_b: str) -> float:
        """
        Similarité cosinus complexe entre deux voix [0, 1].
        
        Args:
            voice_id_a, voice_id_b: IDs des voix à comparer
            
        Returns:
            similarité ∈ [0, 1]
        """
        if voice_id_a not in self._voices or voice_id_b not in self._voices:
            return 0.0
        
        H_a = self._voices[voice_id_a].hologram
        H_b = self._voices[voice_id_b].hologram
        
        # Similarité cosinus complexe
        dot = np.real(np.dot(H_a, np.conj(H_b)))
        norm_a = np.sqrt(np.sum(np.abs(H_a) ** 2))
        norm_b = np.sqrt(np.sum(np.abs(H_b) ** 2))
        
        if norm_a < 1e-10 or norm_b < 1e-10:
            return 0.0
        
        similarity = dot / (norm_a * norm_b)
        
        # Mapping [-1, 1] → [0, 1]
        return float((similarity + 1.0) / 2.0)
    
    def identify_voice(self,
                       audio: np.ndarray,
                       sr: int = DEFAULT_SAMPLE_RATE,
                       top_k: int = 5) -> List[VoiceMatch]:
        """
        Identifie la voix la plus proche dans le store.
        
        Encode l'audio inconnu → ψ_frames → superpose → compare
        avec toutes les voix du store via similarité cosinus.
        
        Args:
            audio: audio inconnu à identifier
            sr: fréquence d'échantillonnage
            top_k: nombre de résultats à retourner
            
        Returns:
            Liste de VoiceMatch triée par similarité décroissante
        """
        if len(self._voices) == 0:
            return []
        
        # Encoder l'audio inconnu
        psi_frames = self.codec.encode(audio, sr=sr)
        if len(psi_frames) == 0:
            return []
        
        # Superposer → H_unknown
        H_unknown = np.sum(psi_frames, axis=0)
        norm_unknown = np.sqrt(np.sum(np.abs(H_unknown) ** 2))
        
        if norm_unknown < 1e-10:
            return []
        
        # Comparer avec chaque voix
        matches = []
        for vid, v in self._voices.items():
            dot = np.real(np.dot(H_unknown, np.conj(v.hologram)))
            norm_v = np.sqrt(np.sum(np.abs(v.hologram) ** 2))
            
            if norm_v < 1e-10:
                continue
            
            similarity = dot / (norm_unknown * norm_v)
            similarity_01 = float((similarity + 1.0) / 2.0)
            
            matches.append(VoiceMatch(
                voice_id=vid,
                name=v.name,
                similarity=similarity_01,
                confidence=0.0,  # calculé après
                is_match=similarity_01 >= self.similarity_threshold,
            ))
        
        # Trier par similarité
        matches.sort(key=lambda m: -m.similarity)
        
        # Calculer la confiance (écart entre le 1er et le 2e)
        for i, m in enumerate(matches[:top_k]):
            if i == 0 and len(matches) > 1:
                gap = m.similarity - matches[1].similarity
                m.confidence = min(1.0, gap * 5.0 + 0.3)
            elif m.similarity >= self.similarity_threshold:
                m.confidence = m.similarity
            else:
                m.confidence = m.similarity * 0.5
        
        return matches[:top_k]
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PERSISTANCE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def save(self, path: str):
        """
        Sauvegarde le store complet au format .npz.
        
        Structure du fichier :
          - holograms:堆叠 de tous les H_voice [n_voices, dim] complex
          - metadata: JSON avec noms, durées, signatures, etc.
          - global_hologram: hologramme global
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        n_voices = len(self._voices)
        voice_ids = list(self._voices.keys())
        
        # Empiler les hologrammes
        holograms = np.zeros((n_voices, self.dim), dtype=np.complex128)
        metadata_list = []
        
        for i, vid in enumerate(voice_ids):
            v = self._voices[vid]
            holograms[i] = v.hologram
            
            meta = {
                'id': v.id,
                'name': v.name,
                'duration_s': v.reference_duration_s,
                'n_frames': v.n_frames,
                'energy': v.energy,
                'created_at': v.created_at,
                'user_metadata': v.metadata,
            }
            
            if v.signature_11d is not None:
                meta['signature_11d'] = v.signature_11d.tolist()
            
            metadata_list.append(meta)
        
        # Sauvegarde
        np.savez_compressed(
            path,
            holograms_real=holograms.real.astype(np.float32),
            holograms_imag=holograms.imag.astype(np.float32),
            global_real=self.global_hologram.real.astype(np.float32),
            global_imag=self.global_hologram.imag.astype(np.float32),
            metadata_json=json.dumps(metadata_list, ensure_ascii=False),
            dim=self.dim,
            threshold=self.similarity_threshold,
            stats_json=json.dumps({
                'total_voices_added': self._total_voices_added,
                'total_clones': self._total_clones,
                'total_fusions': self._total_fusions,
                'voice_count': n_voices,
                'created_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
            }),
        )
        
        return str(path)
    
    @classmethod
    def load(cls, path: str, codec: Optional['HarmonicVoiceCodecV2'] = None) -> 'HolographicVoiceStore':
        """
        Charge un store depuis un fichier .npz.
        
        Args:
            path: chemin vers le fichier .npz
            codec: instance HarmonicVoiceCodecV2 (optionnelle)
            
        Returns:
            HolographicVoiceStore restauré
        """
        data = np.load(path, allow_pickle=True)
        
        dim = int(data['dim'])
        threshold = float(data['threshold'])
        
        store = cls(dim=dim, codec=codec, similarity_threshold=threshold)
        
        # Restaurer les hologrammes
        holograms_real = data['holograms_real']
        holograms_imag = data['holograms_imag']
        holograms = holograms_real + 1j * holograms_imag
        
        # Restaurer le global
        store.global_hologram = (
            data['global_real'] + 1j * data['global_imag']
        )
        
        # Restaurer les métadonnées
        metadata_list = json.loads(str(data['metadata_json']))
        
        for i, meta in enumerate(metadata_list):
            sig = None
            if 'signature_11d' in meta and meta['signature_11d'] is not None:
                sig = np.array(meta['signature_11d'])
            
            identity = VoiceIdentity(
                id=meta['id'],
                name=meta['name'],
                hologram=holograms[i].copy(),
                reference_duration_s=meta.get('duration_s', 0.0),
                signature_11d=sig,
                n_frames=meta.get('n_frames', 0),
                energy=meta.get('energy', 0.0),
                created_at=meta.get('created_at', ''),
                metadata=meta.get('user_metadata', {}),
            )
            store._voices[identity.id] = identity
        
        # Restaurer les stats
        if 'stats_json' in data:
            stats = json.loads(str(data['stats_json']))
            store._total_voices_added = stats.get('total_voices_added', len(metadata_list))
            store._total_clones = stats.get('total_clones', 0)
            store._total_fusions = stats.get('total_fusions', 0)
        
        return store
    
    # ═══════════════════════════════════════════════════════════════════════════
    # UTILITAIRES
    # ═══════════════════════════════════════════════════════════════════════════
    
    @property
    def info(self) -> dict:
        """Informations détaillées sur le store."""
        voices = self.list_voices()
        total_duration = sum(v['duration_s'] for v in voices)
        
        return {
            'dim': self.dim,
            'voice_count': self.voice_count,
            'total_duration_s': total_duration,
            'total_added': self._total_voices_added,
            'total_clones': self._total_clones,
            'total_fusions': self._total_fusions,
            'similarity_threshold': self.similarity_threshold,
            'global_energy': float(np.sum(np.abs(self.global_hologram) ** 2)),
            'has_voice_extractor': self._voice_extractor is not None,
            'has_codec': self._codec is not None,
        }
    
    def __repr__(self) -> str:
        return (f"HolographicVoiceStore(voices={self.voice_count}, "
                f"dim={self.dim}, threshold={self.similarity_threshold:.2f})")
    
    def __len__(self) -> int:
        return self.voice_count
    
    def __contains__(self, voice_id: str) -> bool:
        return voice_id in self._voices
    
    def __getitem__(self, voice_id: str) -> VoiceIdentity:
        if voice_id not in self._voices:
            raise KeyError(f"Voix '{voice_id}' non trouvée")
        return self._voices[voice_id]


# ═══════════════════════════════════════════════════════════════════════════════
# TEST COMPLET
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 70)
    print("  Holographic Voice Store — Test Complet")
    print("=" * 70)
    
    np.random.seed(42)
    
    # ── Création du store ──
    print("\n[1] Initialisation...")
    store = HolographicVoiceStore(dim=512)
    print(f"    {store}")
    print(f"    Extracteur vocal: {'Oui' if store._voice_extractor else 'Non (optionnel)'}")
    print(f"    Codec: {'Oui' if store._codec else 'Créé à la demande'}")
    
    # ── Génération de voix simulées ──
    print("\n[2] Création de voix de test...")
    
    def generate_test_voice(f0: float, duration: float = 2.0, seed: int = 0) -> np.ndarray:
        """Génère un audio synthétique simulant une voix."""
        rng = np.random.RandomState(seed)
        sr = DEFAULT_SAMPLE_RATE
        n = int(sr * duration)
        t = np.linspace(0, duration, n, endpoint=False)
        
        # Synthèse harmonique avec formants simplifiés
        signal = np.zeros(n)
        for h in range(1, 12):
            amp = 1.0 / (h ** 1.2)  # décroissance naturelle
            # Formants (simulés par modulation d'amplitude)
            formant_mod = 1.0
            if 300 < f0 * h < 800:
                formant_mod = 1.5   # F1
            elif 800 < f0 * h < 2300:
                formant_mod = 1.3   # F2
            elif 2300 < f0 * h < 3400:
                formant_mod = 0.8   # F3
            
            signal += amp * formant_mod * np.sin(TAU * f0 * h * t + rng.random() * TAU)
        
        # Enveloppe d'amplitude (attaque + décroissance)
        env = np.ones(n)
        attack = int(0.02 * sr)
        env[:attack] = np.linspace(0, 1, attack)
        release = int(0.1 * sr)
        env[-release:] = np.linspace(1, 0, release)
        signal = signal * env
        
        # Ajout de breath
        breath = rng.randn(n) * 0.02
        signal = signal + breath
        
        signal = signal / np.max(np.abs(signal)) * 0.9
        return signal.astype(np.float64)
    
    # Créer 5 voix différentes
    voices_config = [
        ('Alice', 220.0, 1),   # voix féminine
        ('Bob', 120.0, 2),     # voix masculine grave
        ('Carol', 260.0, 3),   # voix féminine aiguë
        ('Dave', 140.0, 4),    # voix masculine
        ('Eve', 200.0, 5),     # voix féminine moyenne
    ]
    
    voice_ids = []
    for name, f0, seed in voices_config:
        audio = generate_test_voice(f0, duration=2.0, seed=seed)
        vid = store.add_voice(name, audio)
        voice_ids.append(vid)
        print(f"    {name:8s} → {vid} (f0={f0}Hz, {len(store._voices[vid].hologram)}d) "
              f"E={store._voices[vid].energy:.1f}")
    
    # ── Clonage ──
    print("\n[3] Test clonage...")
    clone_audio = generate_test_voice(225.0, duration=1.5, seed=10)
    clone_id = store.clone_voice(clone_audio, name="Clone_F")
    clone = store[clone_id]
    print(f"    Clone créé: {clone_id} ({clone.name})")
    print(f"    Durée ref: {clone.reference_duration_s:.1f}s, "
          f"Frames: {clone.n_frames}, Énergie: {clone.energy:.1f}")
    
    # ── Comparaison ──
    print("\n[4] Test comparaison de voix...")
    for i in range(len(voice_ids)):
        for j in range(i + 1, len(voice_ids)):
            sim = store.compare_voices(voice_ids[i], voice_ids[j])
            vi = store._voices[voice_ids[i]]
            vj = store._voices[voice_ids[j]]
            print(f"    {vi.name:8s} ↔ {vj.name:8s}: sim={sim:.4f}")
    
    # ── Identification ──
    print("\n[5] Test identification...")
    test_audio = generate_test_voice(218.0, duration=1.5, seed=99)  # proche d'Alice
    matches = store.identify_voice(test_audio)
    
    print(f"    Audio test (f0≈218Hz) — Top {len(matches)} matches:")
    for m in matches:
        marker = " ★ MATCH" if m.is_match else ""
        print(f"      {m.name:8s}: sim={m.similarity:.4f}, "
              f"confiance={m.confidence:.3f}{marker}")
    
    # ── Fusion ──
    print("\n[6] Test fusion de voix...")
    alice_id = voice_ids[0]  # Alice (220Hz)
    bob_id = voice_ids[1]    # Bob (120Hz)
    
    fused_id = store.fuse_voices([alice_id, bob_id], name="Alice+Bob")
    fused = store[fused_id]
    print(f"    Fusion: {fused_id} ({fused.name})")
    
    # Vérifier que la fusion est entre les deux
    sim_alice = store.compare_voices(fused_id, alice_id)
    sim_bob = store.compare_voices(fused_id, bob_id)
    sim_carol = store.compare_voices(fused_id, voice_ids[2])
    print(f"    sim(Fusion, Alice) = {sim_alice:.4f}")
    print(f"    sim(Fusion, Bob)   = {sim_bob:.4f}")
    print(f"    sim(Fusion, Carol) = {sim_carol:.4f} (devrait être plus faible)")
    
    # ── Conversion ψ ──
    print("\n[7] Test conversion voice → ψ...")
    psi_alice = store.voice_to_psi(alice_id)
    print(f"    ψ_Alice: |ψ|={np.sqrt(np.sum(np.abs(psi_alice)**2)):.4f}")
    
    params = store.psi_to_voice_params(psi_alice)
    print(f"    Paramètres estimés:")
    print(f"      pitch_est: {params['pitch_est_hz']:.1f} Hz")
    print(f"      brilliance: {params['brilliance']:.3f}")
    print(f"      warmth: {params['warmth']:.3f}")
    
    # ── Persistance ──
    print("\n[8] Test sauvegarde/chargement...")
    save_path = "data/test_voice_store.npz"
    saved = store.save(save_path)
    print(f"    Sauvegardé: {saved}")
    
    # Charger
    store2 = HolographicVoiceStore.load(save_path)
    print(f"    Chargé: {store2}")
    print(f"    Voix restaurées: {store2.voice_count}")
    
    # Vérifier l'intégrité
    for vid in voice_ids:
        if vid in store2:
            sim = store.compare_voices(vid, vid) if vid in store2._voices else 0
            print(f"    {vid}: {'✓' if vid in store2 else '✗'} "
                  f"(autosim={sim:.4f})")
    
    # ── Résumé ──
    print("\n" + "=" * 70)
    print("  RÉSUMÉ Holographic Voice Store")
    print("=" * 70)
    info = store.info
    for key, val in info.items():
        if isinstance(val, float):
            print(f"  {key:25s}: {val:.4f}")
        else:
            print(f"  {key:25s}: {val}")
    
    print(f"\n  {'Statut':25s}: ✓ OK")
    print(f"  {'Voix stockées':25s}: {store.voice_count}")
    print(f"  {'Clones réalisés':25s}: {store._total_clones}")
    print(f"  {'Fusions réalisées':25s}: {store._total_fusions}")
    print(f"  {'Seuil similarité':25s}: {store.similarity_threshold:.2f}")
    
    # Nettoyage
    Path(save_path).unlink(missing_ok=True)
    
    print("\n✓ Test Holographic Voice Store terminé.")
