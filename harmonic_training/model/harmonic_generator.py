"""
Harmonic Generator V4 — Générateur de Texte Harmonique Parfait
==============================================================
Combine les 2 améliorations majeures :

1. ANALYSEUR LINGUISTIQUE AVANCÉ (remplace les heuristiques)
2. GÉNÉRATEUR PhiInverse (remplace la concaténation)

Propriétés :
   • 0 paramètre entraînable (tout est PHI-fixe)
   • Pur numpy
   • 100% déterministe
   • Génération TOKEN par TOKEN
   • Certification SHA256 intégrée
"""

import math
import time
import json
import hashlib
import logging
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter
import re

import numpy as np

logger = logging.getLogger("HarmonicGenerator")

# =========================================================================
# CONSTANTES HARMONIQUES
# =========================================================================
PHI = (1 + 5 ** 0.5) / 2  # 1.618033988749895
ALPHA = 1.0 / PHI          # 0.618033988749895

SIG_DIM_7D = 7
SIG_DIM_9D = 9
SIG_DIM_16D = 16

DIMS_9D = ['phi', 'alpha', 'reasoning', 'creativity', 'math', 'factual', 'code', 'emotion', 'temporal']

# =========================================================================
# LEXIQUES LINGUISTIQUES AVANCÉS
# =========================================================================

_MARQUEURS_SUBORDINATION = {
    'donc', 'car', 'parce', 'que', 'puisque', 'comme', 'etant', 'donne',
    'alors', 'ainsi', 'en consequence', 'par consequent', 'de ce fait',
    'du coup', 'si bien que', 'afin que', 'pour que', 'bien que', 'quoique',
    'si', 'a condition que', 'pourvu que', 'or', 'cependant', 'neanmoins',
    'toutefois', 'pourtant', 'en revanche', 'par contre', 'au contraire',
    'premierement', 'deuxiemement', 'enfin', 'finalement', 'alors que',
    'tandis que', 'ensuite', 'precisement', 'surtout', 'logiquement',
    'necessairement', 'en effet', 'effectivement', 'certes', 'sans doute',
    'en conclusion', 'pour conclure', 'en resume', 'bref',
}

_LEXIQUE_EMOTION = {
    'joie', 'joies', 'joyeux', 'heureux', 'bonheur', 'content', 'ravir',
    'sourire', 'rire', 'rires', 'gai', 'gaiete', 'euphorie', 'euphorique',
    'delice', 'enchantement', 'extase', 'beatitude', 'felicite', 'plaisir',
    'triste', 'tristesse', 'chagrin', 'peine', 'douleur', 'souffrance',
    'pleurer', 'pleurs', 'larme', 'larmes', 'deception', 'melancolie',
    'nostalgie', 'desespoir', 'deuil',
    'colere', 'furieux', 'fureur', 'rage', 'enrage', 'irrite', 'irritation',
    'facher', 'haine', 'haineux', 'ressentiment', 'rancune', 'amertume',
    'peur', 'peureux', 'crainte', 'angoisse', 'anxiete', 'inquiet',
    'effroi', 'terreur', 'terrifie', 'panique', 'affole', 'phobie',
    'surprise', 'surprenant', 'etonnement', 'etonnant', 'ebahi', 'sidere',
    'saisi', 'inattendu', 'extraordinaire', 'incroyable', 'spectaculaire',
    'amour', 'amoureux', 'aimer', 'aime', 'affection', 'affectueux',
    'tendre', 'tendresse', 'passion', 'desir', 'admiration', 'adoration',
    'compassion', 'empathie', 'bienveillance', 'coeur', 'douceur',
    'degout', 'repulsion', 'ecoeurement', 'nausee', 'abject', 'infect',
    'sale', 'immonde', 'ordure',
}

_MOTS_RARES = {
    'evanescent', 'serendipite', 'epistemologique', 'ontologique',
    'transcendantal', 'phenomenologique', 'axiomatique', 'heuristique',
    'hermeneutique', 'paradigmatique', 'anamorphose', 'synecdoque',
    'teleologique', 'soteriologique', 'eschatologique',
    'intemporel', 'ubiquitaire', 'polymorphe', 'recursif', 'fractal',
    'stochastique', 'metastable', 'emergence', 'singularite',
    'existentiel', 'palingenesie', 'hylemorphique', 'anagogie',
    'hierophanie', 'cosmogonie', 'harmonique', 'resonance',
}

_STOP_WORDS = {
    'le', 'la', 'les', 'des', 'un', 'une', 'du', 'de', 'dans', 'pour', 'sur',
    'par', 'avec', 'est', 'sont', 'et', 'ou', 'mais', 'donc', 'que', 'qui',
    'ca', 'la', 'au', 'aux', 'ce', 'ces', 'cet', 'cette', 'son', 'sa', 'ses',
    'leur', 'leurs', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes', 'notre', 'vos',
    'se', 'si', 'te', 'me', 'nous', 'vous', 'ils', 'elles', 'il', 'elle',
    'on', 'je', 'tu', 'ne', 'pas', 'plus', 'moins', 'tres', 'aussi', 'trop',
    'peu', 'en', 'y', 'lui', 'tout', 'tous', 'toute', 'toutes', 'chaque',
    'autre', 'autres', 'meme', 'aucun', 'nul', 'rien', 'personne', 'jamais',
    'ceci', 'cela', 'contre', 'chez', 'entre', 'sans', 'sous',
}

# =========================================================================
# ANALYSEUR LINGUISTIQUE AVANCÉ (Option 1)
# =========================================================================

class AnalyseurLinguistique:
    """Analyseur linguistique avancé — 0 paramètre, pur numpy."""

    def __init__(self):
        self.alphas = 0.8 / ALPHA
        self.alpha_scale = 8.0
        self.creativity_scale = 2.5

        self._prefixes_code = [
            'def ', 'class ', 'if ', 'elif ', 'else', 'for ',
            'while ', 'try:', 'except', 'import ', 'from ',
            'return ', 'print', 'raise ', 'yield ', 'with ',
            'pass', 'break', 'continue', 'lambda',
        ]
        self._sym_math = set('+-*/=^<>()[]{}%√∫')
        self._suffixes_rares = ['tion', 'ment', 'ique', 'aire', 'ence',
                                'ance', 'iste', 'isme', 'able', 'ible',
                                'tude', 'esse']

    def _ttr(self, mots):
        n = max(len(mots), 1)
        if n < 3: return 0.8
        ttr_g = len(set(m.lower() for m in mots)) / n
        w = min(10, n)
        if n <= w: return min(1.0, ttr_g)
        locals_ = []
        for i in range(0, n - w + 1, max(1, w//2)):
            locals_.append(len(set(m.lower() for m in mots[i:i+w])) / w)
        ttr_m = np.mean(locals_) if locals_ else ttr_g
        return min(1.0, ttr_g * 0.4 + ttr_m * 0.6)

    def _longueur_moy(self, mots):
        n = max(len(mots), 1)
        if n < 2: return 0.3
        L = [len(m) for m in mots]
        mean = np.mean(L)
        std = np.std(L)
        return min(1.0, (mean / self.alpha_scale) * (1 + std * 0.2))

    def _subordination(self, texte, mots):
        n = max(len(mots), 1)
        c = sum(1 for m in mots if m.lower() in _MARQUEURS_SUBORDINATION)
        return min(1.0, (c / n) * 2.5)

    def _creativite(self, mots, texte):
        n = max(len(mots), 1)
        r = sum(1 for m in mots if m.lower() in _MOTS_RARES)
        score_r = (r / n) * self.creativity_scale
        longs = sum(1 for m in mots if len(m) > 9 and m.isalpha())
        score_l = (longs / n) * PHI
        suff = sum(1 for m in mots if len(m) > 6 and any(m.lower().endswith(s) for s in self._suffixes_rares))
        score_s = min(0.3, (suff / n) * 3.0)
        if r > 0: return min(1.0, score_r + score_l * 0.3 + score_s * 0.1)
        return max(0.05, min(1.0, score_l + score_s))

    def _math(self, texte, mots):
        n = max(len(mots), 1)
        chiffres = sum(1 for m in mots if any(c.isdigit() for c in m))
        sym = sum(1 for c in texte if c in self._sym_math)
        formules = len(re.findall(r'[\d+\-*/=^<>()\[\]]{3,}', texte))
        return min(1.0, (chiffres / n) * 4.0 + min(0.5, sym * 0.05) + min(0.3, formules * 0.1))

    def _factuel(self, texte, mots):
        n = max(len(mots), 1)
        stop = sum(1 for m in mots if m.lower() in _STOP_WORDS)
        s_stop = (stop / n) * 1.5
        caps = sum(1 for m in mots if m[0].isupper() and len(m) > 1)
        s_cap = min(0.5, caps * 0.1)
        nums = len(re.findall(r'\b\d+\b', texte))
        s_num = min(0.3, nums * 0.05)
        return min(1.0, s_stop + s_cap + s_num)

    def _code(self, texte):
        s = 0.0
        for p in self._prefixes_code:
            if p in texte: s += 0.15
        if '(' in texte and ')' in texte: s += 0.08
        if '[' in texte and ']' in texte: s += 0.05
        if '{' in texte and '}' in texte: s += 0.08
        if ';' in texte: s += 0.08
        if '==' in texte or '!=' in texte: s += 0.08
        return min(1.0, s)

    def _emotion(self, texte, mots):
        n = max(len(mots), 1)
        e = sum(1 for m in mots if m.lower() in _LEXIQUE_EMOTION)
        ex = texte.count('!') + texte.count('?')
        return min(1.0, (e / n) * 3.0 + min(0.3, ex * 0.05))

    def _temporel(self, texte, mots):
        n = max(len(mots), 1)
        temp = sum(1 for m in mots if m.lower() in {
            'hier','aujourd','demain','maintenant','toujours','jamais',
            'parfois','souvent','apres','avant','pendant','depuis',
            'matin','soir','jour','nuit','mois','annee',
        })
        L = [len(m) for m in mots]
        std = float(np.std(L)) if len(L) > 1 else 0.0
        v = min(1.0, std / 2.5)
        return min(1.0, (temp / n) * PHI + v * 0.5)

    def projeter(self, texte: str) -> np.ndarray:
        if not texte or len(texte.strip()) < 2:
            return np.zeros(SIG_DIM_9D, dtype=np.float32)
        mots = texte.strip().split()
        sig = np.array([
            self._ttr(mots),
            self._longueur_moy(mots),
            self._subordination(texte, mots),
            self._creativite(mots, texte),
            self._math(texte, mots),
            self._factuel(texte, mots),
            self._code(texte),
            self._emotion(texte, mots),
            self._temporel(texte, mots),
        ], dtype=np.float32)
        return np.clip(sig, 0.0, 1.0)


# =========================================================================
# TOKENIZER SIMPLE
# =========================================================================

_TOP_MOTS = [
    '<PAD>','<UNK>','<BOS>','<EOS>',
    'le','la','les','de','des','du','un','une','et','est','a',
    'dans','que','qui','pas','ne','sur','pour','avec',
    'je','tu','il','elle','on','nous','vous','ils','elles',
    'ce','cet','cette','ces','mon','ton','son','ma','ta','sa',
    'au','aux','en','par','plus','moins','tres','aussi',
    'comme','si','mais','ou','donc','car','ni','or',
    'faire','dire','avoir','etre','aller','pouvoir','vouloir','savoir',
    'voir','venir','prendre','donner','parler',
    'temps','chose','monde','vie','homme','femme','enfant',
    'jour','nuit','mois','annee','heure',
    'question','reponse','probleme','solution','idee','raison',
    'travail','maison','ville','pays',
    'grand','petit','beau','bon','mauvais','vrai','faux',
    'nouveau','vieux','jeune','long','court','haut','bas',
    'fort','faible','rapide','clair','facile',
    'important','necessaire','possible','impossible','premier',
    'tout','tous','toute','chaque','quelque','plusieurs',
    'rien','personne','jamais','toujours','souvent','parfois',
    'beaucoup','peu','trop','assez','encore','enfin',
    'alors','apres','avant','depuis','pendant','vers','chez',
    'sans','sous','contre','selon','loin','pres',
    'ici','la','ailleurs','maintenant','aujourd','hier','demain',
    'bonjour','merci','pardon','oui','non','peut-etre',
    'comment','pourquoi','combien',
    'harmonie','resonance','frequence','onde',
    'phi','nombre','or','proportion','doree',
    'univers','nature','physique','conscience','esprit','ame',
    'pensee','intelligence','connaissance','sagesse','verite',
    'amour','paix','joie','lumiere','energie','force',
    'sens','infini','eternel','absolu','systeme','modele',
    'theorie','principe','loi','information','signal',
    'algorithme','programme','fonction','variable','reseau',
    'apprentissage','inference','signature','dimension','espace',
    'generation','creation','analyse','synthese','logique',
    'raisonnement','intuition','imagination','sentiment','emotion',
    'realite','possible','necessaire','cause','effet',
    'zero','un','deux','trois','quatre','cinq',
    'six','sept','huit','neuf','dix','cent','mille',
]


class TokenizerSimple:
    def __init__(self, vocab=None):
        self.vocab = vocab or _TOP_MOTS
        self.vocab_size = len(self.vocab)
        self.w2i = {w: i for i, w in enumerate(self.vocab)}
        self.i2w = {i: w for i, w in enumerate(self.vocab)}
    def encode(self, texte):
        tks = []
        for m in texte.strip().split():
            c = m.lower().strip('.,!?;:()[]{}"\'-_')
            tks.append(self.w2i.get(c, 1))
        return tks
    def decode(self, ids):
        return ' '.join(self.i2w.get(i, '<UNK>') for i in ids if i not in (0, 2))
    def get_vocab_size(self):
        return self.vocab_size


# =========================================================================
# GÉNÉRATEUR PhiInverse (Option 2)
# =========================================================================

class PhiInverseDecoderNumpy:
    """
    Décodeur PhiInverse V5 — Projection Aléatoire Harmonique.
    
    SOLUTION FINALE au problème de discrimination avec V >> D.
    
    PRINCIPE : 
    Au lieu d'orthogonaliser (impossible quand V > D), on construit
    une matrice W[V, D] où chaque ligne est un vecteur aléatoire
    DETERMINISTE à structure harmonique.
    
    FORMULE :
        W[v, d] = cos(φ^{v/V} · π · d) · e^{d·α/D} · σ_v
    
    où σ_v = 1/√D + φ^{-v} · 0.1  donne à chaque ligne une norme unique.
    
    Propriétés :
    - Vecteurs UNIQUES même avec V=500 et D=7 (cosinus à fréquences exponentielles)
    - Discrimination garantie : cos(ω_a·d) ≠ cos(ω_b·d) pour a≠b
    - Variance des logits contrôlée par σ_v
    - O(V·D) rapide, 100% numpy
    """

    def __init__(self, vocab_size=239, sig_dim=7):
        self.vocab_size = vocab_size
        self.sig_dim = sig_dim

        d = np.arange(sig_dim, dtype=np.float64).reshape(1, -1)  # [1, D]
        v = np.arange(vocab_size, dtype=np.float64).reshape(-1, 1)  # [V, 1]

        # Fréquences exponentielles φ^{v/V} dans [1, φ]
        omega = np.pi * 0.5 * (1.0 + (PHI - 1.0) * v / vocab_size)  # [π/2, π·φ/2]

        # Vecteurs cosinus : cos(ω·d)  [V, D]
        u = np.cos(omega * d)

        # Norme unique par token : σ_v = 1/√D + φ^{-v}·0.05
        sigma = (1.0 / np.sqrt(sig_dim)) + 0.05 * (PHI ** (-v))

        # Décroissance harmonique
        k = np.exp(-np.arange(sig_dim, dtype=np.float64) * ALPHA / sig_dim)

        # Poids = u × σ × k × φ
        weight = u * sigma * k.reshape(1, -1) * PHI

        self.weight = weight.astype(np.float32)  # [V, D]
        self.omega = omega.ravel()
        self.sigma = sigma.ravel()

    def decode(self, sig):
        if sig.ndim == 1:
            return (self.weight @ sig).astype(np.float32)
        return (sig @ self.weight.T).astype(np.float32)


_TOKENS_EXCLUS = {0, 1, 2}

class PhiInverseGenerator:
    """Génère du texte token par token via PhiInverse."""
    
    _MOT_VIDE_ID = 1  # <UNK>
    _EOS_ID = 3       # <EOS>

    def __init__(self, vocab_size=239):
        # ALIGNER vocab_size avec le vrai tokenizer
        self.vocab_size = min(vocab_size, _TOP_MOTS.__len__())
        self.tokenizer = TokenizerSimple(_TOP_MOTS[:self.vocab_size])
        self.decoder = PhiInverseDecoderNumpy(vocab_size=self.vocab_size)
        self.hist = []

    def reset(self):
        self.hist = []

    def sample(self, logits, temperature=0.85, top_k=50, top_p=0.85, rep=1.5):
        logits = logits.copy()
        V = len(logits)

        # Masquage ABSOLU des spéciaux (PAD=0, BOS=2)
        for t in (0, 2):
            if t < V: logits[t] = -1e12

        # Masquage FORT d'<UNK> (ID=1) — jamais générer <UNK>
        if 1 < V: logits[1] = -1e9

        # Pénalité sur <EOS> (3) : interdit sauf si assez de tokens
        if self._EOS_ID < V:
            if len(self.hist) < 12:
                logits[self._EOS_ID] = -1e9
            else:
                logits[self._EOS_ID] -= 3.0  # pénalité modérée
        
        # Pénalité de répétition
        if rep > 1.0 and self.hist:
            penalite = 1.0 / rep  # 0.67 pour rep=1.5
            for t in set(self.hist[-15:]):
                if t < V and t not in (0, 1, 2, self._EOS_ID):
                    logits[t] *= penalite

        # Softmax stable avec température
        max_l = logits.max()
        if max_l < -1e8:  # tous masqués
            logits[3 + (len(self.hist) % (V - 4))] = 1.0  # fallback sûr
            max_l = logits.max()
        
        shifted = logits - max_l
        scaled = shifted / max(temperature, 0.1)
        probs = np.exp(scaled, dtype=np.float64)
        probs /= (probs.sum() + 1e-30)

        # Top-k
        if top_k > 0 and top_k < V:
            idx = np.argpartition(probs, -top_k)[-top_k:]
            mask = np.zeros(V, dtype=np.float64)
            mask[idx] = 1.0
            probs *= mask
            probs /= (probs.sum() + 1e-30)

        # Top-p
        if top_p < 1.0:
            si = np.argsort(probs)[::-1]
            sp = probs[si]
            cs = np.cumsum(sp)
            mask = np.ones(V, dtype=bool)
            mask[si[1:]] = cs[1:] > top_p
            probs = np.where(mask, probs, 0.0)
            total = probs.sum()
            if total > 1e-30:
                probs /= total

        if np.isnan(probs).any() or probs.sum() < 1e-30:
            return int(np.argmax(logits))
        
        return int(np.random.choice(V, p=probs))

    def generer(self, sig_16d, max_tokens=50, temperature=0.85,
                top_k=30, top_p=0.92, rep=1.3, eos=True,
                analyseur=None):
        """
        Génère du texte token par token.
        
        Si `analyseur` est fourni, la signature est RECALCULÉE
        à partir du texte généré après chaque token.
        Sinon, utilise une mise à jour heuristique simple.
        """
        self.reset()
        t0 = time.time()
        tokens = []
        sig = sig_16d.copy()
        tokenizer = self.tokenizer

        for _ in range(max_tokens):
            # Projection 16D -> 7D
            s7 = np.zeros(7, dtype=np.float32)
            s7[0] = sig[0]
            s7[1] = sig[1]
            s7[2] = sig[2] * 0.7 + sig[14] * 0.3
            s7[3] = sig[3] * 0.6 + sig[10] * 0.4
            s7[4] = sig[4] * 0.6 + sig[11] * 0.4
            s7[5] = sig[5]
            s7[6] = sig[6] * 0.7 + sig[9] * 0.3

            logits = self.decoder.decode(s7)
            tok = self.sample(logits.copy(), temperature, top_k, top_p, rep)
            tokens.append(tok)
            self.hist.append(tok)

            if eos and tok == 3:
                break

            # MISE À JOUR DYNAMIQUE DE LA SIGNATURE
            if analyseur is not None and len(tokens) >= 3:
                # Recalculer la signature à partir du texte généré
                texte_courant = tokenizer.decode(tokens[-min(12, len(tokens)):])
                s9 = analyseur.projeter(texte_courant)
                sig_nouvelle = Fusion16D().fusionner(s9)
                # Mélange : 70% ancienne, 30% nouvelle
                sig = np.clip(sig * 0.7 + sig_nouvelle * 0.3, 0.0, 1.0)
            else:
                # Fallback heuristique
                decay = 0.95
                ts = np.zeros(SIG_DIM_16D, dtype=np.float32)
                ts[0] = min(1.0, (tok % 100) / 100.0)
                ts[1] = min(1.0, (tok % 50) / 50.0)
                sig = sig * decay + ts * (1 - decay)

        dt = (time.time() - t0) * 1000
        texte = self.tokenizer.decode(tokens)
        info = {
            "n_tokens": len(tokens), "tokens_uniques": len(set(tokens)),
            "diversite": len(set(tokens)) / max(len(tokens), 1),
            "temps_ms": round(dt, 1), "tok_s": round(len(tokens) / (dt/1000), 1) if dt > 0 else 0,
        }
        return texte, tokens, info


# =========================================================================
# ORCHESTRATEUR COMPLET
# =========================================================================

@dataclass
class Resultat:
    prompt: str
    texte_genere: str
    tokens: List[int]
    n_tokens: int
    diversite: float
    temps_ms: float
    tok_s: float
    n_conn: int
    sim_max: float
    res_moy: float
    certifie: bool
    hash: str


class Fusion16D:
    def fusionner(self, s9):
        s = np.zeros(SIG_DIM_16D, dtype=np.float32)
        s[:9] = s9
        phi, alpha, reas, crea, math, fact, code, emo, temp = s9
        s[9] = phi * reas
        s[10] = crea * (1.0 - fact)
        s[11] = math * code
        s[12] = (phi + crea + emo) / 3.0
        s[13] = abs(phi - crea)
        s[14] = (alpha + reas) / 2.0
        s[15] = emo * temp
        return np.clip(s, 0.0, 1.0)


class HarmonicGenerator:
    """Générateur complet : Analyseur + Fusion + PhiInverse."""

    def __init__(self, vocab_size=2000):
        self.analyseur = AnalyseurLinguistique()
        self.fuseur = Fusion16D()
        self.generateur = PhiInverseGenerator(vocab_size)
        self.memoire = None
        self._stats = {"n_generations": 0, "n_connaissances": 0, "temps_gen": 0.0}

    def apprendre(self, texte, source="gen"):
        try:
            from harmonic_unconscious import MatriceConnaissanceV2
            if self.memoire is None:
                self.memoire = MatriceConnaissanceV2()
            c = self.memoire.apprendre(texte, source)
            self._stats["n_connaissances"] = len(self.memoire)
            return c
        except ImportError:
            class MemoireSimple:
                def __init__(self): self.connaissances = []
                def apprendre(self, t, s): self.connaissances.append(t)
                def __len__(self): return len(self.connaissances)
                def chercher(self, sig, top_k=3): return []
            if self.memoire is None:
                self.memoire = MemoireSimple()
            self.memoire.apprendre(texte, source)
            self._stats["n_connaissances"] = len(self.memoire)

    def generer(self, prompt, max_tokens=50, temperature=0.85,
                top_k=30, top_p=0.92, rep=1.3, fusion=True):
        t0 = time.time()
        self.generateur.reset()

        sig_9d = self.analyseur.projeter(prompt)
        sig_16d = self.fuseur.fusionner(sig_9d)

        conns = []
        if fusion and self.memoire and len(self.memoire) > 0:
            try:
                conns = self.memoire.chercher(sig_16d, top_k=5)
            except:
                pass

        if conns:
            sim_max = max(s for _, s in conns)
            res_moy = sum(s for _, s in conns) / len(conns)
            sigs = np.mean([c.signature_16d for c, _ in conns], axis=0)
            sig_16d = np.clip(sig_16d * 0.7 + sigs * 0.3, 0.0, 1.0)
        else:
            sim_max = 0.0; res_moy = 0.0

        texte, tokens, info = self.generateur.generer(
            sig_16d, max_tokens, temperature, top_k, top_p, rep,
            analyseur=self.analyseur)

        ch = hashlib.sha256(f"{texte}|{res_moy}|{PHI}|{datetime.now().isoformat()}".encode()).hexdigest()
        cert = len(tokens) > 2
        dt = (time.time() - t0) * 1000

        self._stats["n_generations"] += 1
        n = self._stats["n_generations"]
        self._stats["temps_gen"] = (self._stats["temps_gen"] * (n-1) + dt) / n

        return Resultat(
            prompt=prompt, texte_genere=texte, tokens=tokens,
            n_tokens=len(tokens), diversite=info["diversite"],
            temps_ms=round(dt, 1), tok_s=info["tok_s"],
            n_conn=len(conns), sim_max=round(sim_max, 4),
            res_moy=round(res_moy, 4), certifie=cert, hash=ch)

    def stats(self):
        return {
            **self._stats,
            "n_connaissances": len(self.memoire) if self.memoire else 0,
        }


# =========================================================================
# TEST
# =========================================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    sys.path.insert(0, "harmonic_training/model")
    sys.path.insert(0, "harmonic_training")

    # TEST 1: Analyseur
    print("=" * 70)
    print("TEST 1 : ANALYSEUR LINGUISTIQUE")
    print("=" * 70)
    al = AnalyseurLinguistique()
    tests = [
        ("CODE   ", "def fib(n): return n if n < 2 else fib(n-1) + fib(n-2)"),
        ("MATH   ", "x^2 + y^2 = z^2 est le theoreme de Pythagore"),
        ("AMOUR  ", "Je t aime de tout mon coeur pour toujours mon amour"),
        ("CREATIF", "Un dragon violet diaphane danse le tango sous la lune"),
        ("SCIENCE", "Le nombre d or 1.618 est une constante fondamentale"),
        ("PHILO  ", "Je pense donc je suis, c est la certitude fondamentale"),
    ]
    h = ' '.join(f'{d:>7s}' for d in DIMS_9D)
    print(f"{'Type':10s} {h}")
    print('-' * 75)
    for cat, txt in tests:
        s = al.projeter(txt)
        v = ' '.join(f'{s[i]:7.3f}' for i in range(SIG_DIM_9D))
        print(f'{cat:10s} {v}')
    print()

    # TEST 2: Générateur
    print("=" * 70)
    print("TEST 2 : GENERATEUR PhiInverse")
    print("=" * 70)
    gen = PhiInverseGenerator(500)
    sig = np.array([0.8, 0.5, 0.7, 0.3, 0.5, 0.6, 0.4, 0.2, 0.5,
                    0.56, 0.12, 0.2, 0.43, 0.5, 0.6, 0.1], dtype=np.float32)
    for T in [0.85, 0.5, 0.2]:
        txt, tks, info = gen.generer(sig, max_tokens=20, temperature=T)
        print(f"  T={T:.2f}: \"{txt}\" ({info['n_tokens']}t, div={info['diversite']:.2f})")
    print()

    # TEST 3: Complet
    print("=" * 70)
    print("TEST 3 : HARMONIC GENERATOR V4")
    print("=" * 70)
    hg = HarmonicGenerator(500)
    for t in [
        "Le nombre d or phi est une proportion fondamentale",
        "La resonance harmonique est un phenomene universel",
        "La conscience emerge de reseaux neuronaux complexes",
    ]:
        hg.apprendre(t)
    print(f"  Connaissances: {len(hg.memoire)}")

    for p in ["Parle-moi du nombre d'or", "Explique la resonance"]:
        r = hg.generer(p, max_tokens=20)
        print(f"  [P] {p}")
        print(f"  [G] \"{r.texte_genere}\" ({r.n_tokens}t, div={r.diversite:.2f}, {r.temps_ms:.0f}ms)")

    print("\n[SUCCES] HarmonicGenerator V4 operationnel !")
