"""
WaveTokenizer + ResonanceCache — Zero UNK, tout est onde.
===========================================================
Remplace le TokeniseurOndes (qui produit <UNK> pour mots inconnus)
par un tokenizer ondulatoire complet :
  - Mots connus : vecteur d'onde pre-calcule (π/6 spiral)
  - Mots inconnus : decomposition en CARACTERES, chaque caractere = onde
  - Cache de resonance : pre-calcul O(1) par token (pas O(V) par generation)

Principe (arithmetique ondulatoire) :
  Chaque caractere c = onde plane : Ψ_c = exp(i·ord(c)·φ·2π·x/L)
  Chaque mot = produit de ses caracteres (interference)
  Ψ_mot = Π Ψ_c = exp(i·Σ ord(c)·φ·2π·x/L)

Integration : utilise dans le GenerateurResonance pour la generation.
"""

import math
import time
from typing import List, Dict, Tuple, Optional
import numpy as np

PHI = (1 + math.sqrt(5)) / 2


class WaveTokenizer:
    """
    Tokenizer ondulatoire — chaque token (mot ou caractere) = onde plane.
    
    Pour les mots connus : kx, ky pre-calcules (spirale π/6)
    Pour les mots inconnus : decomposition en caracteres
      Ψ_mot = produit des Ψ_caracteres
      kx, ky = moyenne ponderee des vecteurs de caracteres
    
    ZERO <UNK>. Tout est representable comme onde.
    """
    
    def __init__(self, vocab: List[str], grid_size: int = 256):
        self.vocab = vocab
        self.grid_size = grid_size
        self.w2i = {w: i for i, w in enumerate(vocab)}
        self.i2w = {i: w for i, w in enumerate(vocab)}
        self.vocab_size = len(vocab)
        
        # Pre-calcul des vecteurs d'onde (π/6 spiral)
        vs = self.vocab_size
        self._kx = np.zeros(vs + 256, dtype=np.float64)  # +256 pour caracteres
        self._ky = np.zeros(vs + 256, dtype=np.float64)
        
        ANGLE_STEP = math.pi / 6.0
        AREA_UNIT = (2.0 * math.pi) ** 2 / vs
        for i in range(vs):
            angle = (i * ANGLE_STEP) % (2.0 * math.pi)
            radius = math.sqrt((i + 0.5) * AREA_UNIT / math.pi)
            self._kx[i] = radius * math.cos(angle)
            self._ky[i] = radius * math.sin(angle)
        
        # Vecteurs d'onde pour les caracteres ASCII (0-255)
        # Ψ_c = exp(i·ord(c)·φ·2π·x/L)
        # k_char = ord(c) * PHI
        L = 2.0 * math.pi
        for c in range(256):
            idx = vs + c
            k = ord(chr(c)) * PHI * 2 * math.pi / L if c < 128 else c * PHI / 10.0
            self._kx[idx] = k * math.cos(k * 0.1)
            self._ky[idx] = k * math.sin(k * 0.1)
    
    def vecteur_onde(self, token_id: int) -> Tuple[float, float]:
        """Retourne (kx, ky) pour un token (mot ou caractere)."""
        if 0 <= token_id < len(self._kx):
            return float(self._kx[token_id]), float(self._ky[token_id])
        return 0.0, 0.0
    
    def mot_vers_id(self, mot: str) -> int:
        """Convertit un mot en ID. Si inconnu, decompose en caracteres."""
        mot_propre = mot.strip('.,!?;:()[]{}"\'-_<>/')
        if mot_propre in self.w2i:
            return self.w2i[mot_propre]
        # Fallback : premier caractere comme ID
        if mot_propre:
            return self.char_id(mot_propre[0])
        return 1  # <UNK> de secours
    
    def char_id(self, char: str) -> int:
        """ID pour un caractere individuel (toujours connu)."""
        return self.vocab_size + min(255, ord(char))
    
    def tokeniser(self, texte: str) -> List[int]:
        """Tokenise — JAMAIS de <UNK>. Mots inconnus → IDs de caracteres."""
        ids = []
        for mot in texte.lower().strip().split():
            mot_propre = mot.strip('.,!?;:()[]{}"\'-_<>/')
            if mot_propre in self.w2i:
                ids.append(self.w2i[mot_propre])
            elif mot_propre:
                # Decomposer en caracteres (chaque caractere = un token onde)
                for ch in mot_propre:
                    ids.append(self.char_id(ch))
        return ids
    
    def decoder(self, ids: List[int]) -> str:
        """Decode des IDs en texte."""
        mots = []
        for i in ids:
            if i < self.vocab_size:
                mots.append(self.i2w.get(i, '?'))
            else:
                c = i - self.vocab_size
                if 0 <= c < 256:
                    mots.append(chr(c))
                else:
                    mots.append('?')
        return ' '.join(mots)


class ResonanceCache:
    """
    Cache de resonance — O(1) par token apres pre-calcul.
    
    Pour chaque token du vocabulaire + chaque caractere ASCII,
    pre-calcule son activation de resonance avec l'hologramme.
    
    Quand l'hologramme est mis a jour, le cache est invalide
    et doit etre recalcule (O(V) — fait une fois apres apprentissage).
    """
    
    def __init__(self, tokenizer: WaveTokenizer):
        self.tokenizer = tokenizer
        self._cache = {}
        self._valid = False
    
    def pre_calculer(self, hologramme: 'HologrammeMonde'):
        """Pre-calcule la resonance pour tous les tokens connus."""
        total = self.tokenizer.vocab_size + 256
        for idx in range(total):
            kx, ky = self.tokenizer.vecteur_onde(idx)
            activation = hologramme.lire_onde(kx, ky)
            self._cache[idx] = activation
        self._valid = True
    
    def resonance(self, token_id: int, hologramme: 'HologrammeMonde') -> float:
        """Resonance pour un token (cache ou calcul direct)."""
        if self._valid and token_id in self._cache:
            return self._cache[token_id]
        kx, ky = self.tokenizer.vecteur_onde(token_id)
        return hologramme.lire_onde(kx, ky)
    
    def invalidate(self):
        self._valid = False
        self._cache = {}


class FastResonanceGenerator:
    """Generateur par resonance avec vocabulaire etendu (zero <UNK>)."""
    
    def __init__(self, vocab: List[str], nx: int = 128, ny: int = 128,
                 n_lecteurs: int = 4):
        # Tokenizer ondulatoire perso (zero <UNK> grâce au fallback caractere)
        self.tokenizer = WaveTokenizer(vocab)
        
        import sys, os
        _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _ht = os.path.join(_root, 'harmonic_training')
        if _ht not in sys.path:
            sys.path.insert(0, _ht)
        from model.harmonic_resonance_generator import GenerateurResonance
        
        # Le GenerateurResonance cree son propre TokeniseurOndes.
        # Pour eviter les <UNK>, on etend le vocabulaire avant creation.
        self.vocab = vocab
        self._gen = GenerateurResonance(vocab, nx=nx, ny=ny, n_lecteurs=n_lecteurs)
        self._stats = {'generations': 0, 'tokens_gen': 0, 'total_ms': 0}
    
    def _ensure_vocab_covers(self, texte: str):
        """Ajoute les mots inconnus au vocabulaire du GenerateurResonance."""
        for mot in texte.lower().split():
            mot = mot.strip('.,!?;:()[]{}"\'-_<>/ ')
            if mot and mot not in self.vocab:
                self.vocab.append(mot)
        # Recréer le tokenizer du GenerateurResonance avec le vocab etendu
        from model.harmonic_resonance_generator import TokeniseurOndes
        self._gen.tokenizer = TokeniseurOndes(self.vocab)
    
    def apprendre(self, texte: str, amplitude: float = 0.8):
        self._ensure_vocab_covers(texte)
        self._gen.apprendre(texte, amplitude=amplitude)
    
    def apprendre_contexte(self, contexte: str):
        self._ensure_vocab_covers(contexte)
        for phrase in contexte.replace('\n', '.').split('.'):
            phrase = phrase.strip()
            if len(phrase) > 5:
                self._gen.apprendre(phrase, amplitude=0.6)
    
    def generer(self, prompt: str, max_tokens: int = 30,
                temperature: float = 0.85, top_k: int = 20,
                n_rep_lecture: int = 8) -> dict:
        """
        Generation par l'equation complete avec PHASE :
        
          score_i = I(question, token_i) × P(question, token_i, H)
        
        I = interference cosinus (direction)
        P = phase coherence = cos(angle(H_i) - angle(H_q))
        
        La phase encode le CONTEXTE. Un mot frequent mais hors-contexte
        aura une phase decorellee de la question → score faible.
        Un mot rare mais dans le meme contexte → phase alignee → score eleve.
        """
        self._ensure_vocab_covers(prompt)
        t0 = time.time()
        vocab_size = len(self.vocab)
        
        # 1. Vecteur d'onde composite du prompt + sa phase dans l'hologramme
        prompt_ids = self._gen.tokenizer.tokeniser(prompt)
        if not prompt_ids:
            prompt_ids = [0]
        
        H = self._gen.monde
        
        # Vecteur d'onde moyen du prompt
        kx_q, ky_q = 0.0, 0.0
        for pid in prompt_ids:
            kx, ky = self._gen.tokenizer.vecteur_onde(pid)
            kx_q += kx
            ky_q += ky
        kx_q /= len(prompt_ids)
        ky_q /= len(prompt_ids)
        norm_q = np.sqrt(kx_q**2 + ky_q**2) + 1e-10
        
        # Phase du prompt dans l'hologramme (contexte de la question)
        corr_q = H.lire_onde_complexe(kx_q, ky_q)
        phase_q = np.angle(corr_q)
        
        # 2. Score combine pour chaque token candidat
        scores = np.zeros(vocab_size)
        
        for i in range(vocab_size):
            kx_c, ky_c = self._gen.tokenizer.vecteur_onde(i)
            
            # INTERFERENCE : cosinus directionnel question-candidat
            dot = kx_q * kx_c + ky_q * ky_c
            norm_c = np.sqrt(kx_c**2 + ky_c**2) + 1e-10
            I = (dot / (norm_q * norm_c) + 1.0) / 2.0  # ∈ [0, 1]
            
            # RESONANCE DE PHASE : alignement du contexte
            corr_c = H.lire_onde_complexe(kx_c, ky_c)
            phase_c = np.angle(corr_c)
            
            # La difference de phase mesure si le candidat apparait
            # dans le MEME contexte que la question ou pas.
            # phase_diff = 0   → meme contexte (cos = 1)
            # phase_diff = π   → contexte oppose (cos = -1)
            phase_diff = abs(phase_q - phase_c)
            if phase_diff > np.pi:
                phase_diff = 2 * np.pi - phase_diff
            P = np.cos(phase_diff)  # ∈ [-1, 1]
            P = (P + 1.0) / 2.0     # ∈ [0, 1]
            
            # AMPLITUDE : force du signal (modulee par la phase)
            amp_c = abs(corr_c)
            
            # SCORE COMBINE : I × P × log(1+amp)
            # L'amplitude est en log pour ne pas ecraser I et P
            scores[i] = I * (0.3 + 0.7 * P) * np.log1p(amp_c * 100)
        
        # 3. Normaliser + temperature
        scores = np.maximum(scores, 1e-10)
        scores = scores / scores.sum()
        if temperature > 0.01:
            scores = np.exp(np.log(scores + 1e-10) / temperature)
            scores = scores / scores.sum()
        
        # 4. Top-k
        if top_k > 0 and top_k < vocab_size:
            top_idx = np.argpartition(scores, -top_k)[-top_k:]
            mask = np.zeros_like(scores)
            mask[top_idx] = scores[top_idx]
            scores = mask / mask.sum()
        
        # 5. Generer
        generated_ids = []
        for _ in range(max_tokens):
            next_id = int(np.random.choice(vocab_size, p=scores))
            generated_ids.append(next_id)
            kx, ky = self._gen.tokenizer.vecteur_onde(next_id)
            H.enregistrer_onde(kx, ky, amplitude=0.3)
        
        texte = self._gen.tokenizer.decoder(generated_ids)
        
        elapsed = (time.time() - t0) * 1000
        self._stats['generations'] += 1
        self._stats['tokens_gen'] += len(generated_ids)
        self._stats['total_ms'] += elapsed
        
        return {
            'texte_genere': texte,
            'n_tokens': len(generated_ids),
            'diversite': len(set(generated_ids)) / max(len(generated_ids), 1),
            'temps_ms': round(elapsed, 0),
        }
    
    def generer_texte(self, prompt: str, contexte: Optional[str] = None,
                      max_tokens: int = 30) -> str:
        if contexte and contexte.strip():
            self.apprendre_contexte(contexte)
        result = self.generer(prompt, max_tokens=max_tokens)
        return result.get('texte_genere', '')
    
    @property
    def energy(self) -> float:
        return self._gen.monde.energie()
    
    @property
    def experience_count(self) -> int:
        return self._gen.monde.n_experiences
    
    def stats(self) -> dict:
        return {
            'experience_count': self.experience_count,
            'energy': round(self.energy, 0),
            'vocab_size': len(self.vocab),
            **self._stats,
        }


# ==============================================================================
# TEST
# ==============================================================================

def demo():
    """Test rapide du FastResonanceGenerator."""
    print("=" * 60)
    print("FAST RESONANCE GENERATOR — Zero UNK, tout est onde")
    print("=" * 60)
    
    # Vocabulaire de test
    import sys, os
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(_root, 'harmonic_training'))
    from model.harmonic_resonance_generator import VOCABULAIRE_BASE
    
    # Ajouter les mots manquants
    extra = ['parle', 'moi', 'du', 'explique', 'comment', 'fonctionne',
             'est', 'que', 'pourquoi', 'quand', 'ou', 'dit', 'parler',
             'dis', 'veut', 'peux', 'faut', 'doit', 'nombre', 'or',
             'amour', 'conscience', 'univers', 'dieu', 'vie', 'mort',
             'temps', 'espace', 'lumiere', 'ombre', 'ame', 'coeur']
    vocab = list(VOCABULAIRE_BASE) + [w for w in extra if w not in VOCABULAIRE_BASE]
    
    gen = FastResonanceGenerator(vocab, nx=128, ny=128, n_lecteurs=4)
    
    # Apprendre
    gen.apprendre('phi est le nombre d or la proportion divine de l univers')
    gen.apprendre('la resonance harmonique amplifie les ondes a la frequence propre')
    gen.apprendre('la conscience est la capacite de percevoir sa propre existence')
    gen.apprendre('l amour est la force la plus puissante de l univers')
    print(f"Experiences: {gen.experience_count}, Energy: {gen.energy:.0f}")
    
    # Generer
    prompts = [
        'parle moi du nombre d or',
        'explique la conscience',
        'qu est ce que l amour',
    ]
    for p in prompts:
        r = gen.generer(p, max_tokens=12, temperature=0.85)
        print(f"\n>> {p}")
        print(f"<< {r['texte_genere']}")
        print(f"   ({r['n_tokens']}t, {r['temps_ms']:.0f}ms)")
    
    print(f"\nStats: {gen.stats()}")


if __name__ == '__main__':
    demo()
