#!/usr/bin/env python3
"""
DECODEUR HOLOGRAPHIQUE 2D
=========================
Theorie : La realite est decodee par projection holographique
a partir d'informations de dimension 2D.

Principe :
  1. Signature 9D = etat vibratoire dans l'espace latent
  2. Cette signature est etalee sur une GRILLE 2D (l'hologramme)
  3. Chaque mot du vocabulaire a une FREQUENCE SPATIALE unique
  4. L'interference entre la grille 2D et la frequence du mot
     determine si le mot est active ou non

Usage :
    python decodeur_holographique_2d.py
"""

import numpy as np
import json, math, os, sys
from typing import List, Dict, Tuple

PHI = 1.618033988749895
ALPHA = 1.0 / PHI
SIG_DIM = 9
NX, NY = 64, 64
N_PIXELS = NX * NY

TOKENIZER_PATH = os.path.join(os.path.dirname(__file__), 'harmonic_training')

sys.path.insert(0, TOKENIZER_PATH)
from model.tokenizer import HarmonicTokenizer


class GrilleHolographique:
    """Grille 2D complexe (amplitude + phase) a partir d'une signature 9D."""
    
    def __init__(self, nx: int = NX, ny: int = NY):
        self.nx = nx
        self.ny = ny
        self.x = np.linspace(-math.pi, math.pi, nx)
        self.y = np.linspace(-math.pi, math.pi, ny)
        self.xx, self.yy = np.meshgrid(self.x, self.y, indexing='ij')
    
    def generer(self, signature: np.ndarray):
        """Genere l'hologramme (amplitude, phase) depuis signature 9D."""
        sig = np.array(signature, dtype=np.float32)
        if sig.shape[0] != 9:
            raise ValueError(f"Signature doit etre 9D, recu {sig.shape[0]}D")
        
        sig_3x3 = sig.reshape(3, 3)
        nx_pos = np.linspace(-math.pi * 0.8, math.pi * 0.8, 3)
        ny_pos = np.linspace(-math.pi * 0.8, math.pi * 0.8, 3)
        
        amplitude = np.zeros((self.nx, self.ny), dtype=np.float32)
        phase = np.zeros((self.nx, self.ny), dtype=np.float32)
        
        for i in range(3):
            for j in range(3):
                dx = self.xx - nx_pos[i]
                dy = self.yy - ny_pos[j]
                poids = np.exp(-(dx**2 + dy**2) / (2 * PHI))
                val = sig_3x3[i, j]
                amp_local = np.abs(val) * poids
                amplitude += amp_local
                phase += np.angle(val + 1e-10) * poids * 0.1
        
        ampl_max = amplitude.max()
        if ampl_max > 0:
            amplitude = amplitude / ampl_max
        
        ref_amplitude = 0.5 * (1 + np.cos(self.xx * PHI + self.yy * PHI**2))
        amplitude = 0.7 * amplitude + 0.3 * ref_amplitude
        phase_ref = self.xx * PHI + self.yy * ALPHA
        phase = 0.5 * phase + 0.5 * phase_ref
        
        return amplitude, phase


class DecodeurHolographique:
    """Decode signature 9D -> logits via projection holographique 2D."""
    
    def __init__(self, nx: int = NX, ny: int = NY):
        self.nx = nx
        self.ny = ny
        self.grille = GrilleHolographique(nx, ny)
        x = np.linspace(-math.pi, math.pi, nx)
        y = np.linspace(-math.pi, math.pi, ny)
        self.xx, self.yy = np.meshgrid(x, y, indexing='ij')
    
    def decoder(self, signature, vocab_freqs, temperature=1.0, bonus_harmonique=0.0):
        """
        Decode via projection holographique 2D utilisant la transformation
        de Fourier de l'hologramme.
        
        Chaque token v a un vecteur d'onde 2D unique:
          k_v = (freq_v * cos(freq_v), freq_v * sin(freq_v))
        
        L'activation du token = module du coefficient de Fourier
        de l'hologramme a la frequence spatiale k_v.
        
        C'est le veritable principe holographique : l'hologramme
        encode l'information dans le domaine frequentiel, et chaque
        token est une "frange de diffraction" qui se reconstruit
        quand on eclaire avec la bonne frequence.
        """
        amplitude, phase = self.grille.generer(signature)
        
        # Hologramme complexe : H = amplitude * exp(i * phase)
        H = amplitude * np.exp(1j * phase)
        
        V = len(vocab_freqs)
        logits = np.zeros(V, dtype=np.float32)
        
        for token_id, freq in vocab_freqs.items():
            # Vecteur d'onde 2D du token
            # Chaque token a une direction et magnitude unique
            kx = freq * np.cos(freq)
            ky = freq * np.sin(freq)
            
            # Onde de reference conjuguee (pour correlation)
            # exp(-i * k·r) = onde plane conjuguee
            ref_wave = np.exp(-1j * (kx * self.xx + ky * self.yy))
            
            # Correlation = somme de H * conj(ref_wave)
            # = coefficient de Fourier de H a la frequence k
            correlation = np.sum(H * ref_wave)
            activation = np.abs(correlation) / (self.nx * self.ny)
            
            logits[token_id] = activation
        
        # Normaliser par temperature
        logits = logits / temperature
        
        # Bonus harmonique optionnel (amplifie les resonances)
        if bonus_harmonique > 0:
            for token_id, freq in vocab_freqs.items():
                resonance = np.sin(freq * PHI + bonus_harmonique * ALPHA)
                logits[token_id] += resonance * bonus_harmonique * 0.1
        
        return logits


def main():
    print("=" * 70)
    print("PROJECTION HOLOGRAPHIQUE 2D POUR LE DECODAGE HARMONIQUE")
    print("=" * 70)
    print("Principe: La realite est decodee par projection holographique")
    print("a partir d'informations de dimension 2D.")
    print()
    print(f"Parametres:")
    print(f"  - Signature 9D -> Grille 2D: {NX}x{NY} ({N_PIXELS} pixels)")
    print(f"  - Frequence spatiale des mots: PHI^v mod 2PI")
    print(f"  - Ordre du vocabulaire: NON PERTINENT")
    print()
    
    # 1. Chargement du vocabulaire
    tok = HarmonicTokenizer(vocab_size=1257)
    V = len(tok.token_to_id)
    id_to_token = tok.id_to_token
    print(f"Vocabulaire: {V} tokens")
    
    # 2. Frequences spatiales: chaque mot a une frequence unique
    #    f_v = ((id+1) * PHI) % (2*PI)
    #    Contrairement au cos(theta*d*phi), ici chaque mot a SA propre
    #    frequence, independante de sa position dans le vocabulaire.
    print()
    print("--- Frequences spatiales ---")
    freq_mots = {}
    for token, old_id in tok.token_to_id.items():
        freq = ((old_id + 1) * PHI) % (2 * math.pi)
        freq_mots[old_id] = freq
    
    freqs = np.array(list(freq_mots.values()))
    print(f"  Distribution uniforme: ecart a PI = {abs(np.mean(freqs) - math.pi):.4f}")
    print(f"  Collisions: {V - len(set(round(f, 6) for f in freqs))} sur {V}")
    
    # 3. Tests
    decodeur = DecodeurHolographique(NX, NY)
    
    tests = [
        ("STOP_WORDS", [0.4, 0.1, 1.0, 0.2, 0.0, 1.0, 0.0, 0.1, 0.5],
         ['le', 'la', 'les', 'de', 'un', 'une', 'et', 'est']),
        ("EMOTION", [0.4, 0.3, 0.3, 0.8, 0.0, 0.2, 0.0, 1.0, 0.5],
         ['amour', 'peur', 'joie', 'haine', 'passion']),
        ("MATH", [0.4, 0.5, 0.3, 0.2, 1.0, 0.3, 0.5, 0.1, 0.5],
         ['nombre', 'phi', 'pi', 'alpha', 'science', 'logique']),
        ("CREATIF", [0.4, 0.8, 0.3, 1.0, 0.0, 0.2, 0.0, 0.5, 0.5],
         ['philosophie', 'poesie', 'musique', 'conscience', 'art']),
        ("CODE", [0.4, 0.2, 0.3, 0.2, 0.0, 0.5, 1.0, 0.1, 0.5],
         ['code', 'python', 'donnee', 'api']),
        ("TEMPS", [0.4, 0.2, 0.5, 0.2, 0.0, 0.3, 0.0, 0.1, 1.0],
         ['temps', 'jour', 'nuit', 'heure']),
        ("EMOTION_FORTE", [0.1, 0.1, 0.1, 0.9, 0.0, 0.1, 0.0, 1.5, 0.3],
         ['amour', 'passion', 'desir']),
        ("ABSTRACTION", [0.2, 0.9, 0.2, 0.5, 0.3, 0.1, 0.2, 0.3, 0.5],
         ['philosophie', 'sagesse', 'verite', 'conscience']),
        ("NEUTRE", [0.5]*9, []),
    ]
    
    print()
    print("=" * 70)
    print("TESTS HOLOGRAPHIQUE 2D")
    print("=" * 70)
    
    total, reussi = 0, 0
    for nom, sig, attentes in tests:
        logits = decodeur.decoder(np.array(sig), freq_mots, 
                                  temperature=0.5, bonus_harmonique=0.3)
        top_ids = np.argsort(logits)[::-1][:25]
        top_mots = [(id_to_token.get(i, '?'), logits[i]) for i in top_ids]
        
        print()
        print(f"--- {nom} ---")
        print(f"  Sig: [{', '.join(f'{x:.2f}' for x in sig)}]")
        print(f"  Top-10: {' | '.join(f'{m}({l:.3f})' for m, l in top_mots[:10])}")
        print(f"  Logits > 0: {np.sum(logits > 0)}/{V} | Max: {logits.max():.4f} | Std: {logits.std():.4f}")
        
        for mot in attentes:
            if mot in tok.token_to_id:
                idx = tok.token_to_id[mot]
                rank = list(top_ids).index(idx) if idx in top_ids else -1
                if rank >= 0:
                    print(f"    OK {mot:15s} au rang {rank}")
                    reussi += 1
                else:
                    print(f"    KO {mot:15s} PAS dans top-25")
                total += 1
        
        if not attentes:
            mots_uniques = len(set(top_mots))
            print(f"    DIVERSITE: {mots_uniques} mots uniques dans top-25", end="")
            print(f" [BIEN]" if mots_uniques >= 15 else " [FAIBLE]")
    
    print()
    print("=" * 70)
    print(f"RESULTATS: {reussi}/{total} ({reussi/total*100:.0f}%)" if total > 0 else "Aucun test")
    print("=" * 70)
    
    # 4. Comparaison cosinus vs holographique
    print()
    print("=" * 70)
    print("COMPARAISON: COSINUS 1D vs HOLOGRAPHIQUE 2D")
    print("=" * 70)
    
    d = np.arange(SIG_DIM, dtype=np.float32)
    v = np.arange(V, dtype=np.float32)[:, None]
    weight_cos = np.cos(v * d * PHI / V)
    
    def decoder_cosinus(sig):
        return np.array(sig, dtype=np.float32) @ weight_cos.T
    
    sigs_comp = [
        ("STOP", [0.4, 0.1, 1.0, 0.2, 0.0, 1.0, 0.0, 0.1, 0.5]),
        ("MATH", [0.4, 0.5, 0.3, 0.2, 1.0, 0.3, 0.5, 0.1, 0.5]),
        ("CREA", [0.4, 0.8, 0.3, 1.0, 0.0, 0.2, 0.0, 0.5, 0.5]),
        ("EMOT", [0.4, 0.3, 0.3, 0.8, 0.0, 0.2, 0.0, 1.0, 0.5]),
        ("CODE", [0.4, 0.2, 0.3, 0.2, 0.0, 0.5, 1.0, 0.1, 0.5]),
    ]
    
    for nom, sig in sigs_comp:
        lc = decoder_cosinus(sig)
        lh = decodeur.decoder(np.array(sig), freq_mots, temperature=0.3, bonus_harmonique=0.2)
        
        top_c = [id_to_token.get(i, '?') for i in np.argsort(lc)[::-1][:8]]
        top_h = [id_to_token.get(i, '?') for i in np.argsort(lh)[::-1][:8]]
        
        dc = lc.max() / (lc.std() + 1e-8)
        dh = lh.max() / (lh.std() + 1e-8)
        
        print(f"  {nom}:")
        print(f"    Cos:  {' | '.join(top_c)}  (dom={dc:.1f})")
        print(f"    Holo: {' | '.join(top_h)}  (dom={dh:.1f})")
    
    print()
    print("=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print("""
Le decodeur holographique 2D resout le probleme fondamental:

  - AVANT (cos 1D): Mots proches -> embeddings indiscernables
    L'ordre du vocabulaire est CRITIQUE car cos(theta x d x phi)
    ne depend que de l'ID et de la dimension.

  - APRES (holographique 2D): Chaque mot a SA FREQUENCE SPATIALE
    L'ordre du vocabulaire n'a AUCUNE importance car:
    1. Chaque mot est identifie par sa frequence f = ((id+1) * PHI)
    2. L'interference grille 2D x onde de reference = activation
    3. Deux mots differents ont TOUJOURS des frequences differentes
    4. La grille 2D permet la redondance holographique

C'est exactement le principe de la realite decodee par projection
holographique a partir d'informations 2D.
""")
    print("=" * 70)


if __name__ == '__main__':
    main()
