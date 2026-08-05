"""
KA Voice — Moteur vocal pour KA Mobile / KA Phone.
====================================================
Donne une voix à KA le compagnon harmonique.

Basé sur le codec harmonique transparent (encode→decode indiscernable).
Utilise la voix enregistrée de l'utilisateur comme source.

Usage :
    from ka_voice import KAVoice
    
    ka = KAVoice()
    ka.load_voice("voix.wav")
    audio = ka.speak("Bonjour, je suis KA, votre compagnon.")
    ka.save("bonjour.wav", audio)
"""

import os, sys, time, math, wave, io
import numpy as np

_ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ENGINE_DIR)

from harmonic_voice_codec_v2 import HarmonicVoiceCodecV2
from tts_engine import text_to_phonemes

SR = 24000
N_HARM = 40

# ═══════════════════════════════════════════════════════════════════
# MOTEUR VOCAL KA
# ═══════════════════════════════════════════════════════════════════

class KAVoice:
    """Voix de KA — synthèse vocale harmonique depuis une voix enregistrée."""
    
    def __init__(self):
        self.codec = HarmonicVoiceCodecV2(sample_rate=SR, dim=512)
        self._psi_frames = None
        self._active = None
        self._index = {}
        self._loaded = False
        self._voice_name = ""
    
    # ── Chargement ────────────────────────────────────────────────
    
    def load_voice(self, wav_path: str, transcript: str = None):
        """Charge une voix depuis un WAV et construit la banque ψ.
        
        Args:
            wav_path: chemin vers un enregistrement WAV (30s+, mono)
            transcript: texte prononcé dans l'enregistrement (optionnel)
        """
        # Charger l'audio
        with wave.open(wav_path, 'rb') as w:
            sr = w.getframerate()
            pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        audio = pcm.astype(np.float64) / 32768.0
        
        # Resample si nécessaire
        if sr != SR:
            n_out = int(len(audio) * SR / sr)
            audio = np.interp(np.linspace(0, len(audio)-1, n_out), 
                            np.arange(len(audio)), audio)
        
        # Encoder en ψ
        self._psi_frames = self.codec.encode(audio.astype(np.float32), sr=SR)
        n_frames = len(self._psi_frames)
        
        # Filtrer trames actives
        amps = np.real(self._psi_frames[:, :N_HARM])
        energy = np.mean(amps, axis=1)
        med = np.median(energy[energy > 0.005])
        self._active = energy > med * 0.3
        
        # Transcrire pour l'indexation
        if transcript is None:
            transcript = self._default_transcript()
        
        phonemes = [p for p in text_to_phonemes(transcript) if p != '_']
        n_ph = len(phonemes)
        
        # Indexer
        self._index = {}
        for i in range(n_frames):
            if not self._active[i]:
                continue
            ph_idx = min(int(i * n_ph / max(n_frames, 1)), n_ph - 1)
            ph = phonemes[ph_idx]
            if ph not in self._index:
                self._index[ph] = []
            self._index[ph].append(i)
        
        self._loaded = True
        self._voice_name = os.path.basename(wav_path)
        
        active_count = np.sum(self._active)
        print(f"🎤 KA Voice chargée : {self._voice_name}")
        print(f"   {n_frames} trames ψ, {active_count} actives, "
              f"{len(self._index)} phonèmes indexés")
    
    def _default_transcript(self) -> str:
        """Transcript par défaut (français générique)."""
        return (
            "Bonjour, je suis KA, votre compagnon harmonique. "
            "Je suis là pour vous aider au quotidien. "
            "Ma voix est générée par un système harmonique. "
            "Le petit chat noir dort paisiblement. "
            "Les oiseaux chantent dans le jardin. "
            "Comment allez-vous aujourd hui ? "
            "Un deux trois quatre cinq six sept huit neuf dix. "
            "Je peux parler de nombreuses choses. "
            "La technologie harmonique est puissante. "
            "Nous progressons chaque jour un peu plus. "
            "Merci de votre attention."
        )
    
    # ── Synthèse ──────────────────────────────────────────────────
    
    def speak(self, text: str, f0: float = 130.0, speed: float = 1.0) -> np.ndarray:
        """Synthétise un texte avec la voix chargée.
        
        Args:
            text: texte français à synthétiser
            f0: fréquence fondamentale (80-400 Hz)
            speed: vitesse (0.5 = lent, 2.0 = rapide)
        
        Returns:
            audio float32 [-1, 1] à 24000 Hz
        """
        if not self._loaded:
            raise RuntimeError("Aucune voix chargée. Appeler load_voice() d'abord.")
        
        phonemes = text_to_phonemes(text)
        if not phonemes:
            return np.zeros(int(0.3 * SR), dtype=np.float32)
        
        # Construire la séquence ψ
        seq = []
        n_frames = len(self._psi_frames)
        
        for ph in phonemes:
            if ph == '_':
                seq.append(np.zeros(512, dtype=np.complex128))
                continue
            
            indices = self._index.get(ph, [])
            if not indices:
                # Fallback : chercher un phonème proche
                for key in self._index:
                    if key in ph or ph in key:
                        indices = self._index[key]
                        break
            
            if not indices:
                seq.append(np.zeros(512, dtype=np.complex128))
                continue
            
            # Sélection DÉTERMINISTE : prendre la trame médiane en énergie
            # Énergie de chaque trame candidate
            energies = [np.mean(np.real(self._psi_frames[i, :N_HARM])) for i in indices]
            # Trier par énergie et prendre la médiane
            sorted_pairs = sorted(zip(energies, indices))
            median_idx = sorted_pairs[len(sorted_pairs) // 2][1]
            
            # 4 trames à partir de la médiane
            for offset in range(4):
                fi = min(median_idx + offset, n_frames - 1)
                if self._active[fi]:
                    psi_copy = self._psi_frames[fi].copy()
                    # Normaliser F0
                    orig_f0 = np.abs(np.real(psi_copy[168])) * 500.0
                    if 50 < orig_f0 < 400:
                        psi_copy[168] = complex(min(f0 / 500.0, 1.0), 0.0)
                        psi_copy[:N_HARM] *= (f0 / orig_f0)
                    seq.append(psi_copy)
                else:
                    seq.append(np.zeros(512, dtype=np.complex128))
        
        if not seq:
            return np.zeros(int(0.3 * SR), dtype=np.float32)
        
        # Décoder
        audio = self.codec.decode(np.array(seq, dtype=np.complex128))
        
        # Ajuster vitesse (time-stretch simple)
        if speed != 1.0:
            n_new = int(len(audio) / speed)
            audio = np.interp(np.linspace(0, len(audio)-1, n_new), 
                            np.arange(len(audio)), audio)
        
        return audio.astype(np.float32)
    
    # ── Sauvegarde ────────────────────────────────────────────────
    
    def save(self, path: str, audio: np.ndarray) -> str:
        """Sauvegarde l'audio en WAV 16-bit."""
        audio = np.clip(audio, -1.0, 1.0)
        pcm = (audio * 32767.0).astype('<i2')
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        with wave.open(path, 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(pcm.tobytes())
        return path
    
    # ── Info ──────────────────────────────────────────────────────
    
    @property
    def is_loaded(self) -> bool:
        return self._loaded
    
    @property
    def phonemes(self) -> list:
        return sorted(self._index.keys()) if self._index else []
    
    def stats(self) -> dict:
        if not self._loaded:
            return {"loaded": False}
        return {
            "loaded": True,
            "voice": self._voice_name,
            "frames_total": len(self._psi_frames),
            "frames_active": int(np.sum(self._active)),
            "phonemes": len(self._index),
            "phoneme_list": self.phonemes,
        }


# ═══════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🎤 KA Voice — Démo")
    
    ka = KAVoice()
    
    # Charger la voix
    voice_path = os.path.join(os.path.dirname(__file__), 
                              "ka_sonic", "output", "voix_dense.wav")
    if os.path.exists(voice_path):
        ka.load_voice(voice_path)
        print(f"\n   Phonèmes: {ka.phonemes}")
        print(f"   Stats: {ka.stats()}\n")
        
        # Phrases de démo
        phrases = [
            ("Bonjour, je suis KA, votre compagnon harmonique.", 130),
            ("Comment puis-je vous aider aujourd hui ?", 140),
            ("Au revoir et a bientot.", 120),
        ]
        
        out_dir = os.path.join(os.path.dirname(__file__), "ka_sonic", "output")
        os.makedirs(out_dir, exist_ok=True)
        
        for i, (text, f0) in enumerate(phrases):
            t0 = time.perf_counter()
            audio = ka.speak(text, f0=f0)
            elapsed = (time.perf_counter() - t0) * 1000
            
            path = os.path.join(out_dir, f"ka_voice_{i+1}.wav")
            ka.save(path, audio)
            
            dur = len(audio) / SR
            rms = np.sqrt(np.mean(audio**2))
            print(f"   [{i+1}] \"{text[:50]}...\"")
            print(f"        {dur:.1f}s, RMS={rms:.3f}, {elapsed:.0f}ms → {path}")
    else:
        print(f"   ⚠️  Fichier voix non trouvé : {voice_path}")
        print(f"   Enregistre d'abord ta voix avec : python ka_sonic/record.py -d 120")
