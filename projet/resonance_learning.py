#!/usr/bin/env python
"""
APPRENTISSAGE PAR RÉSONANCE
===========================
Mécanisme d'apprentissage sans backprop qui remplace le gradient descent.

Principe :
1. Chaque phrase d'entraînement est tokenisée
2. Les paires de tokens qui co-occurrent dans une fenêtre glissante
   voient leur "résonance" augmenter
3. La résonance est stockée dans une matrice N×N (N = vocab_size)
4. À la génération, les tokens avec forte résonance mutuelle sont boostés
5. La mémoire épisodique stocke les signatures des phrases

Ce mécanisme est l'équivalent harmonique de l'apprentissage hebbien :
    "Neurons that fire together, wire together"
    → "Tokens that resonate together, strengthen together"

Usage :
    python resonance_learning.py                     # Test
    python resonance_learning.py --train phrases.txt # Entraînement
    python resonance_learning.py --api               # API
"""
import numpy as np
import json, os, sys, math, time, hashlib
from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass
from datetime import datetime

PHI = (1 + 5 ** 0.5) / 2
ALPHA = 1.0 / PHI

# Vocab depuis ordonnancement
try:
    from ordonnancement_vocabulaire import _VOCAB_FR, EmbeddingHarmonique, OrdonnanceurHarmonique
    VOCAB = _VOCAB_FR
except ImportError:
    VOCAB = ['<PAD>','<UNK>','<BOS>','<EOS>','le','la','les','de','et','est','un','une','dans']

VOCAB_SIZE = len(VOCAB)
W2I = {w: i for i, w in enumerate(VOCAB)}
I2W = {i: w for i, w in enumerate(VOCAB)}


# =====================================================================
# MATRICE DE RÉSONANCE (apprentissage hebbien sans backprop)
# =====================================================================

class MatriceResonance:
    """
    Matrice de résonance N×N.
    
    R[i,j] = force de résonance entre le token i et le token j.
    
    Apprentissage :
        Pour chaque phrase P = [t₁, t₂, ..., tₙ] :
            Pour chaque fenêtre de taille W :
                R[tᵢ, tⱼ] += 1 / distance(tᵢ, tⱼ)
        
        Puis normalisation et application de PHI.
    
    Génération :
        score(tⱼ | contexte) += Σ R[tᵢ, tⱼ] pour tᵢ dans le contexte
    """
    
    def __init__(self, vocab_size: int = VOCAB_SIZE, decroissance: float = ALPHA):
        self.vocab_size = vocab_size
        self.decroissance = decroissance  # Facteur de décroissance harmonique
        
        # Matrice de résonance (symétrique, sparse en pratique)
        self.R = np.zeros((vocab_size, vocab_size), dtype=np.float32)
        
        # Compteurs de fréquence
        self.freq = np.zeros(vocab_size, dtype=np.float32)
        
        # Statistiques
        self.n_phrases = 0
        self.n_tokens = 0
    
    def apprendre_phrase(self, ids: List[int], fenetre: int = 5):
        """
        Apprend les co-occurrences dans une phrase.
        
        Args:
            ids: Liste d'IDs de tokens
            fenetre: Taille de la fenêtre de co-occurrence (défaut: 5)
        """
        n = len(ids)
        for i in range(n):
            t_i = ids[i]
            if t_i >= self.vocab_size:
                continue
            self.freq[t_i] += 1.0
            
            # Fenêtre glissante autour de t_i
            debut = max(0, i - fenetre)
            fin = min(n, i + fenetre + 1)
            
            for j in range(debut, fin):
                if i == j:
                    continue
                t_j = ids[j]
                if t_j >= self.vocab_size:
                    continue
                
                # Distance (inverse = plus proche = plus forte résonance)
                dist = abs(i - j)
                poids = 1.0 / (dist ** self.decroissance)  # Décroissance harmonique
                
                # Mise à jour hebbienne (symétrique)
                self.R[t_i, t_j] += poids
                self.R[t_j, t_i] += poids
        
        self.n_phrases += 1
        self.n_tokens += n
    
    def apprendre_batch(self, textes: List[str], fenetre: int = 5,
                        tokenizer: Optional['Tokenizer'] = None):
        """Apprend un lot de textes."""
        if tokenizer is None:
            tokenizer = Tokenizer()
        
        for texte in textes:
            ids = tokenizer.encoder(texte)
            if len(ids) >= 2:
                self.apprendre_phrase(ids, fenetre)
        
        print(f"  [RESONANCE] {len(textes)} phrases -> {self.n_tokens} tokens appris")
    
    def normaliser(self):
        """Normalise la matrice de résonance finalement."""
        # Éviter division par zéro
        max_val = self.R.max()
        if max_val > 0:
            self.R = self.R / max_val
        
        # Appliquer PHI pour briser la symétrie parfaite
        self.R = self.R * PHI
        self.R = np.clip(self.R, 0.0, 1.0)
    
    def resonner(self, contexte: List[int], top_k: int = 20,
                 penalite_repetition: float = 0.5) -> np.ndarray:
        """
        Calcule les scores de résonance pour un contexte donné.
        
        Args:
            contexte: Liste d'IDs de tokens du contexte
            top_k: Nombre de tokens à considérer
            penalite_repetition: Facteur de pénalité pour les tokens déjà utilisés
        
        Returns:
            scores: Tableau [vocab_size] des scores de résonance
        """
        if not contexte:
            return np.zeros(self.vocab_size, dtype=np.float32)
        
        # Agréger les résonances de tous les tokens du contexte
        scores = np.zeros(self.vocab_size, dtype=np.float32)
        n_valides = 0
        
        for t in contexte:
            if t < self.vocab_size:
                scores += self.R[t]
                n_valides += 1
        
        if n_valides > 0:
            scores = scores / n_valides
        
        # Pénalité de répétition harmonique
        vu = set(contexte[-10:])  # Fenêtre de 10 tokens
        for t in vu:
            if t < self.vocab_size:
                scores[t] *= penalite_repetition
        
        return scores
    
    def top_suivants(self, contexte: List[int], k: int = 10) -> List[Tuple[int, float]]:
        """Retourne les k tokens les plus résonants pour le contexte."""
        scores = self.resonner(contexte)
        idx = np.argsort(scores)[::-1]
        result = []
        for i in idx:
            if scores[i] > 0.01:
                result.append((int(i), float(scores[i])))
                if len(result) >= k:
                    break
        return result
    
    def matrice(self) -> np.ndarray:
        """Retourne la matrice de résonance."""
        return self.R
    
    def stats(self) -> Dict:
        return {
            "n_phrases": self.n_phrases,
            "n_tokens": self.n_tokens,
            "connexions_non_nulles": int(np.sum(self.R > 0)),
            "densite": float(np.sum(self.R > 0)) / (self.vocab_size ** 2),
            "resonance_moyenne": float(self.R.mean()),
        }
    
    def sauvegarder(self, chemin: str = "matrice_resonance.npz"):
        np.savez_compressed(chemin, R=self.R, freq=self.freq,
                           n_phrases=self.n_phrases, n_tokens=self.n_tokens)
        print(f"[SAVE] Matrice résonance -> {chemin} ({self.n_phrases} phrases)")
    
    def charger(self, chemin: str = "matrice_resonance.npz"):
        data = np.load(chemin, allow_pickle=True)
        self.R = data['R']
        self.freq = data['freq']
        self.n_phrases = int(data['n_phrases'])
        self.n_tokens = int(data['n_tokens'])
        print(f"[LOAD] Matrice résonance <- {chemin} ({self.n_phrases} phrases)")


# =====================================================================
# TOKENIZER SIMPLE
# =====================================================================

class Tokenizer:
    """Tokenizer simple pour l'apprentissage par résonance."""
    def __init__(self, vocab: Optional[List[str]] = None):
        self.vocab = vocab or VOCAB
        self.w2i = W2I
        self.i2w = I2W
        self.vocab_size = len(self.vocab)
    
    def encoder(self, texte: str) -> List[int]:
        tks = []
        for m in texte.lower().strip().split():
            c = m.strip('.,!?;:()[]{}"\'-_«»\'’\\/')
            if c in self.w2i:
                tks.append(self.w2i[c])
            elif 1 in self.w2i:
                tks.append(self.w2i['<UNK>'])
        return tks
    
    def decoder(self, ids: List[int]) -> str:
        return ' '.join(self.i2w.get(i, '<UNK>') for i in ids if i not in (0,))


# =====================================================================
# MÉMOIRE ÉPISODIQUE AVEC RÉSONANCE
# =====================================================================

@dataclass
class TraceEpisodique:
    """Une trace de phrase apprise avec sa signature et son hash."""
    id: str
    texte: str
    ids: List[int]
    signature_9d: np.ndarray  # [9] features harmoniques
    frequences: Dict[int, float]  # Fréquence des tokens
    hash: str
    date: str
    
class MemoireEpisodique:
    """
    Mémoire épisodique : stocke les phrases sous forme de traces.
    
    Différence avec MemoireAssociative :
    - Stocke les phrases entières (pas seulement leurs signatures)
    - Peut rappeler des phrases similaires par résonance
    - Maintient un index de fréquence des tokens
    """
    
    def __init__(self):
        self.traces: List[TraceEpisodique] = []
        self._index_signatures: Optional[np.ndarray] = None
        self._index_built = False
    
    def ajouter(self, ids: List[int], texte: str, signature_9d: np.ndarray):
        """Ajoute une trace épisodique."""
        freq = {}
        for t in ids:
            freq[t] = freq.get(t, 0) + 1
        
        trace = TraceEpisodique(
            id=hashlib.md5(f"{texte}{time.time()}".encode()).hexdigest()[:12],
            texte=texte, ids=ids,
            signature_9d=np.asarray(signature_9d, dtype=np.float32),
            frequences=freq,
            hash=hashlib.sha256(f"{texte}{len(self.traces)}".encode()).hexdigest()[:16],
            date=datetime.now().isoformat()
        )
        self.traces.append(trace)
        self._index_built = False
        return trace
    
    def _rebuild_index(self):
        if not self.traces:
            self._index_signatures = np.zeros((0, 9), dtype=np.float32)
            self._index_built = True
            return
        sigs = np.stack([t.signature_9d for t in self.traces], axis=0)
        norms = np.linalg.norm(sigs, axis=1, keepdims=True)
        self._index_signatures = sigs / (norms + 1e-8)
        self._index_built = True
    
    def chercher(self, query_sig: np.ndarray, top_k: int = 5,
                 seuil: float = 0.3) -> List[Tuple[TraceEpisodique, float]]:
        """Cherche des traces par similarité de signature."""
        self._rebuild_index() if not self._index_built else None
        if self._index_signatures.shape[0] == 0:
            return []
        qn = query_sig / (np.linalg.norm(query_sig) + 1e-8)
        sims = self._index_signatures @ qn
        idx = np.argsort(sims)[::-1][:top_k]
        return [(self.traces[i], float(sims[i])) for i in idx if sims[i] >= seuil]
    
    def __len__(self):
        return len(self.traces)


# =====================================================================
# APPRENTISSAGE COMPLET PAR RÉSONANCE
# =====================================================================

class ApprentissageResonance:
    """
    Système d'apprentissage complet par résonance.
    
    Combine :
    1. Matrice de résonance (apprentissage hebbien des co-occurrences)
    2. Mémoire épisodique (stockage des phrases complètes)
    3. Analyse harmonique (signature 9D de chaque phrase)
    
    Usage :
        ar = ApprentissageResonance()
        ar.apprendre_phrase("le chat mange la souris")
        ar.apprendre_phrase("le chien mange la viande")
        
        # Test : que vient après "le" ?
        top = ar.top_suivants("le")  # ['chat', 'chien', ...]
        
        # Génération guidée par résonance
        prompt = [id_le]
        for _ in range(10):
            resonance = ar.resonner(prompt)
            next_id = sample(resonance)  # guidé par la résonance
            prompt.append(next_id)
    """
    
    def __init__(self, vocab_size: int = VOCAB_SIZE):
        self.vocab_size = vocab_size
        self.tokenizer = Tokenizer()
        self.matrice = MatriceResonance(vocab_size)
        self.memoire = MemoireEpisodique()
        
        # Analyseur harmonique intégré
        self._init_analyseur()
    
    def _init_analyseur(self):
        """Initialise l'analyseur harmonique intégré."""
        self._LEXIQUE_EMO = {
            'amour','joie','triste','peur','colere','haine','espoir','paix','bonheur',
            'douleur','passion','desir','plaisir','peine','regret','honte','fierte',
            'tendre','douceur','serenite','calme'
        }
        self._MARQ_SUB = {
            'que','qui','dont','ou','car','puisque','comme',
            'alors','donc','or','cependant','neanmoins','pourtant','quoique',
            'apres','avant','pendant','depuis','lorsque','quand','sans','malgre'
        }
    
    def _signature_9d(self, texte: str) -> np.ndarray:
        """Calcule la signature 9D d'un texte."""
        if not texte or len(texte.strip()) < 2:
            return np.zeros(9, dtype=np.float32)
        mots = texte.lower().strip().split()
        n = max(len(mots), 1)
        
        s = np.zeros(9, dtype=np.float32)
        
        # 0: phi - diversité
        s[0] = min(1.0, len(set(mots)) / n * PHI)
        
        # 1: alpha - complexité
        if len(mots) >= 2:
            L = np.array([len(m) for m in mots])
            s[1] = min(1.0, (L.mean() / 5.0) * (1 + L.std() * 0.2))
        else:
            s[1] = 0.3
        
        # 2: reasoning
        sub = sum(1 for m in mots if m in self._MARQ_SUB)
        s[2] = min(1.0, (sub / n) * 2.5)
        
        # 3: creativity
        rare = sum(1 for m in mots if len(m) > 9 and m.isalpha())
        s[3] = min(1.0, (rare / n) * PHI + 0.05)
        
        # 4: math
        chiffres = sum(1 for m in mots if any(c.isdigit() for c in m))
        s[4] = min(1.0, (chiffres / n) * 4.0)
        
        # 5: factuel
        s[5] = min(1.0, (sub / n) * 1.5)
        
        # 6: code
        s[6] = 0.0
        if 'def ' in texte: s[6] = 0.15
        if '(' in texte and ')' in texte: s[6] += 0.05
        
        # 7: emotion
        emo = sum(1 for m in mots if m in self._LEXIQUE_EMO)
        s[7] = min(1.0, (emo / n) * 3.0 + min(0.3, texte.count('!') * 0.05))
        
        # 8: temporel
        temp_mots = {'hier','aujourd','demain','maintenant','toujours','jamais','parfois'}
        temp = sum(1 for m in mots if m in temp_mots)
        if len(mots) > 1:
            std = float(np.std([len(m) for m in mots]))
        else:
            std = 0.0
        s[8] = min(1.0, (temp / n) * PHI + min(1.0, std / 2.5) * 0.5)
        
        return np.clip(s, 0.0, 1.0)
    
    def apprendre_phrase(self, texte: str, fenetre: int = 5):
        """Apprend une phrase par résonance."""
        ids = self.tokenizer.encoder(texte)
        if len(ids) < 2:
            return
        
        # 1. Mettre à jour la matrice de résonance
        self.matrice.apprendre_phrase(ids, fenetre)
        
        # 2. Stocker dans la mémoire épisodique
        sig = self._signature_9d(texte)
        self.memoire.ajouter(ids, texte, sig)
    
    def apprendre_batch(self, textes: List[str], fenetre: int = 5):
        """Apprend un lot de phrases."""
        for texte in textes:
            self.apprendre_phrase(texte, fenetre)
        print(f"[APPRENTISSAGE] {len(textes)} phrases apprises par résonance")
        print(f"  Matrice : {self.matrice.stats()['connexions_non_nulles']} connexions")
        print(f"  Mémoire : {len(self.memoire)} traces épisodiques")
    
    def resonner(self, contexte_ids: List[int], top_k: int = 20) -> np.ndarray:
        """
        Calcule les scores de résonance pour un contexte.
        Combien matrice de résonance + mémoire épisodique.
        """
        # Score de la matrice
        scores = self.matrice.resonner(contexte_ids, top_k)
        
        # Bonus mémoire épisodique
        if len(self.memoire) > 0:
            # Signature du contexte
            texte_contexte = self.tokenizer.decoder(contexte_ids)
            sig = self._signature_9d(texte_contexte)
            
            # Traces similaires
            traces = self.memoire.chercher(sig, top_k=3, seuil=0.3)
            for trace, sim in traces:
                bonus = sim * 0.1  # Petit bonus harmonique
                for t in trace.ids:
                    if t < self.vocab_size:
                        scores[t] += bonus
        
        return scores
    
    def top_suivants(self, contexte: str, k: int = 10) -> List[Tuple[str, float]]:
        """Retourne les k mots les plus probables après un contexte."""
        ids = self.tokenizer.encoder(contexte)
        if not ids:
            return []
        scores = self.resonner(ids)
        idx = np.argsort(scores)[::-1]
        result = []
        for i in idx:
            if scores[i] > 0.01 and i < self.vocab_size:
                mot = self.tokenizer.i2w.get(i, '<UNK>')
                if mot not in ('<PAD>', '<UNK>', '<BOS>', '<EOS>'):
                    result.append((mot, float(scores[i])))
                    if len(result) >= k:
                        break
        return result
    
    def generer(self, prompt: str, max_tokens: int = 20,
                temperature: float = 0.85) -> str:
        """
        Génération guidée par résonance complète.
        Combine :
        - Matrice de résonance (co-occurrences apprises)
        - Mémoire épisodique (phrases similaires)
        - Penalité de répétition
        """
        ids = self.tokenizer.encoder(prompt)
        if not ids:
            return ""
        
        generated = ids.copy()
        
        for _ in range(max_tokens):
            # Score de résonance
            scores = self.resonner(generated)
            
            # Pénalité de répétition
            for t in set(generated[-10:]):
                scores[t] *= 0.3
            
            # Masquer tokens spéciaux
            scores[0] = -1  # <PAD>
            scores[1] = -1  # <UNK>
            scores[2] = -1  # <BOS>
            
            # Température
            if temperature > 0:
                scores = scores / temperature
            
            # Softmax
            scores = scores - scores.max()
            exp_s = np.exp(scores.astype(np.float64) - scores.max().astype(np.float64))
            probs = exp_s / (exp_s.sum() + 1e-10)
            
            # Sampling
            next_id = np.random.choice(self.vocab_size, p=probs)
            
            # Arrêt si EOS
            if next_id == 3:
                break
            
            generated.append(next_id)
        
        return self.tokenizer.decoder(generated[len(ids):])
    
    def stats(self) -> Dict:
        return {
            **self.matrice.stats(),
            "memoire_traces": len(self.memoire),
        }
    
    def sauvegarder(self, prefix: str = "resonance"):
        self.matrice.sauvegarder(f"{prefix}_matrice.npz")
        # Sauvegarder mémoire épisodique
        data = {
            "traces": [
                {"id": t.id, "texte": t.texte, "ids": t.ids,
                 "signature": t.signature_9d.tolist(),
                 "hash": t.hash, "date": t.date}
                for t in self.memoire.traces
            ]
        }
        with open(f"{prefix}_memoire.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"[SAVE] Mémoire épisodique -> {prefix}_memoire.json")
    
    def charger(self, prefix: str = "resonance"):
        if os.path.exists(f"{prefix}_matrice.npz"):
            self.matrice.charger(f"{prefix}_matrice.npz")
        if os.path.exists(f"{prefix}_memoire.json"):
            with open(f"{prefix}_memoire.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
            for t in data["traces"]:
                trace = TraceEpisodique(
                    id=t["id"], texte=t["texte"], ids=t["ids"],
                    signature_9d=np.array(t["signature"], dtype=np.float32),
                    frequences={},
                    hash=t["hash"], date=t["date"]
                )
                self.memoire.traces.append(trace)
            self.memoire._index_built = False
            print(f"[LOAD] Mémoire épisodique <- {prefix}_memoire.json ({len(data['traces'])} traces)")


# =====================================================================
# VALIDATION
# =====================================================================

def main():
    print("=" * 70)
    print("APPRENTISSAGE PAR RÉSONANCE")
    print("=" * 70)
    
    ar = ApprentissageResonance()
    
    # Phrases d'entraînement
    phrases = [
        # bigrammes de base
        "le chat mange la souris",
        "le chien mange la viande",
        "le chat dort sur le lit",
        "le chien court dans le jardin",
        "la souris est petite et rapide",
        "le soleil brille dans le ciel",
        "la lune eclaire la nuit noire",
        "les etoiles brillent dans le ciel",
        "le vent souffle sur la mer",
        "la pluie tombe sur la terre",
        "l eau coule dans la riviere",
        "le feu brule dans la cheminee",
        "l amour est plus fort que tout",
        "la philosophie est l amour de la sagesse",
        "le nombre d or est la proportion divine",
        "la resonance harmonique amplifie les ondes",
        "la conscience est la capacite de percevoir",
        "python est un langage de programmation",
        "l intelligence artificielle explore la creation",
        "la creativite est l intelligence qui s amuse",
    ]
    
    print(f"\n[ENTRAINEMENT] {len(phrases)} phrases...")
    ar.apprendre_batch(phrases)
    
    # Test
    print("\n[TEST] Prédiction par résonance :")
    
    contextes = [
        "le", "la", "les", "dans", "sur", "est",
        "chat", "ciel", "amour",
    ]
    
    for ctx in contextes:
        top = ar.top_suivants(ctx, k=5)
        mots = [m for m, s in top]
        scores = [f"{s:.3f}" for m, s in top]
        print(f"  '{ctx}' -> {mots} (scores: {scores})")
    
    # Test de génération
    print("\n[GENERATION] Guidée par résonance :")
    prompts = [
        "le chat", "la philosophie", "le nombre", "l amour",
    ]
    for prompt in prompts:
        gen = ar.generer(prompt, max_tokens=8, temperature=0.85)
        print(f"  '{prompt}' -> '{gen}'")
    
    print(f"\n[STATS] {ar.stats()}")
    print(f"[OK] Apprentissage par résonance opérationnel")
    
    ar.sauvegarder()
    return ar


if __name__ == '__main__':
    if '--train' in sys.argv:
        # Entraîner depuis un fichier
        ar = ApprentissageResonance()
        fichier = sys.argv[sys.argv.index('--train') + 1]
        with open(fichier, 'r', encoding='utf-8') as f:
            textes = [l.strip() for l in f if l.strip()]
        ar.apprendre_batch(textes)
        ar.sauvegarder()
    else:
        main()
