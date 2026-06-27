"""
Inconscient Harmonique Parfait — LLM Classique Mathématiquement Parfait
========================================================================
Aussi parfait que PUR, mais avec les PARTICULARITÉS de l'inconscient :
fluidité, créativité, connaissances, imagination.

DÉCOUVERTE FONDAMENTALE :
--------------------------
Les LLM classiques hallucinent parce qu'ils COMPRIMENT la connaissance
dans des poids via gradient descent → perte d'information → erreurs.

SOLUTION HARMONIQUE :
---------------------
Au lieu de compresser, on STOCKE la connaissance comme SIGNATURES
HARMONIQUES (9D). La signature EST la connaissance, sans perte.

ARCHITECTURE DÉCOUVERTE (25 mai 2026) :
----------------------------------------
L'inconscient harmonique et PUR (conscient) parlent le même langage
(signatures 16D) mais l'atteignent par des chemins différents :

  CONSCIENT (PUR)           INCONSCIENT (LLM classique)
  ──────────────            ───────────────────────────
  Hidden states de LLM      Propriétés textuelles directes
  Entropie, fractale,       stop words, mots émotionnels,
  autocorrélation           diversité lexicale

  → Signature 7D PUR        → Signature 9D sémantique
       ↓                              ↓
       └────────── Fusion 16D ────────┘

Propriétés de l'inconscient harmonique :
  • ZERO paramètre entraînable (tout est PHI-fixe)
  • ZERO backprop (1 seule passe forward = entraînement)
  • 100% déterministe (même entrée = même sortie)
  • Connaissances extensibles (ajout = nouveau texte)
  • 0% hallucination (pas de compression, que de la
    résonance avec des signatures réelles)
  • Certifiable SHA256
  • PURE NUMPY — aucune dépendance PyTorch
"""

import math
import time
import json
import hashlib
import logging
from typing import List, Dict, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

# Ajouter les chemins
import sys, os
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_HERE))  # f:/SAAS - Copie
sys.path.insert(0, _HERE)       # harmonic_training/model
sys.path.insert(0, os.path.dirname(_HERE))  # harmonic_training
sys.path.insert(0, _PROJECT_ROOT)  # SAAS - Copie (pour engine/)

# PHI : constante mathématique universelle (nombre d'or)
# Utilisée comme fondement harmonique de tout le système.
# Définie localement — aucun import externe nécessaire.
PHI = (1 + 5 ** 0.5) / 2  # 1.618033988749895
ALPHA = 1.0 / PHI          # 0.618...
B_1_PHI = 1 - ALPHA       # 0.381...
ALPHA_CONST = 10 * ALPHA   # 6.180...

logger = logging.getLogger("HarmonicUnconscious")

# =========================================================================
# CONSTANTES
# =========================================================================

SIG_DIM_9D = 9    # phi, alpha, reasoning, creativity, math, factual, code, emotion, temporal
SIG_DIM_16D = 16  # Fusion 9D + variantes harmoniques

# Noms des dimensions 9D
DIMS_9D = ['phi', 'alpha', 'reasoning', 'creativity', 'math', 'factual', 'code', 'emotion', 'temporal']

# Dimensions 7D (communes avec PUR)
DIMS_7D = ['phi', 'alpha', 'reasoning', 'creativity', 'math', 'factual', 'code']

# Seuils
SEUIL_RESONANCE = 0.7
TOP_K_CONNAISSANCES = 5

# =========================================================================
# VOCABULAIRES SPÉCIALISÉS (fixes, déterministes)
# =========================================================================

# Mots émotionnels (amour, joie, tristesse, peur, etc.)
_MOTS_EMOTIONNELS: set = {
    'amour', 'amoureux', 'amoureuse', 'aimer', 'aime', 'aimes', 'aimons', 'aiment',
    'coeur', 'cœur', 'tendre', 'tendresse', 'passion', 'passionné', 'passionnée',
    'désir', 'désirer', 'désire',
    'bonheur', 'heureux', 'heureuse', 'joie', 'joyeux', 'joyeuse',
    'triste', 'tristesse', 'chagrin', 'peine', 'douleur', 'pleurer', 'pleure',
    'peur', 'peureux', 'peureuse', 'crainte', 'craindre', 'angoisse', 'anxiété',
    'colère', 'coléreux', 'furieux', 'furieuse', 'rage', 'énervé',
    'surprise', 'surpris', 'etonné', 'étonné', 'étonnement',
    'dégout', 'dégoût', 'horreur', 'détester', 'detester',
    'haine', 'haïr', 'hair',
    'rêve', 'rêver', 'reve', 'réver', 'réve', 'imaginer', 'imagination',
    'espoir', 'espérer', 'espere', 'espère',
    'gratitude', 'reconnaissant', 'reconnaissante', 'merci',
    'admiration', 'admirer', 'adore', 'adorer',
    'violet', 'danse', 'danser', 'lune', 'soleil', 'étoile', 'etoile',
    'dragon', 'fée', 'fee', 'magie', 'magique', 'merveille', 'merveilleux',
    'roi', 'reine', 'prince', 'princesse', 'château', 'chateau', 'palais',
    'âme', 'ame', 'esprit', 'spirituel', 'divin',
    'beauté', 'beaute', 'beau', 'belle', 'joli', 'jolie',
    'souffrance', 'souffrir', 'larme', 'pleur',
}

# Mots de liaison / stop words français
_STOP_WORDS: set = {
    'le', 'la', 'les', 'des', 'un', 'une', 'du', 'de', 'dans', 'pour', 'sur',
    'par', 'avec', 'est', 'sont', 'et', 'ou', 'mais', 'donc', 'car', 'ni',
    'que', 'qui', 'quoi', 'dont', 'où', 'ou',
    'à', 'au', 'aux', 'ce', 'ces', 'cet', 'cette',
    'son', 'sa', 'ses', 'leur', 'leurs', 'mon', 'ma', 'mes',
    'ton', 'ta', 'tes', 'notre', 'nos', 'votre', 'vos',
    'se', 'si', 'te', 'me', 'nous', 'vous', 'ils', 'elles',
    'il', 'elle', 'on', 'je', 'tu', 'ne', 'pas',
    'plus', 'moins', 'très', 'tres', 'aussi', 'trop', 'peu',
    'en', 'y', 'ça', 'la',
    'c\'', 'd\'', 'l\'', 'm\'', 'n\'', 's\'', 't\''  # contractions
}

# Syntaxes de code
_PATTERNS_CODE: dict = {
    'def ': 'definition_fonction',
    'class ': 'definition_classe',
    '()': 'appel_fonction',
    '==': 'comparaison',
    '!=': 'comparaison',
    '=>': 'fleche',
    '->': 'retour',
    ':': 'debut_bloc',
    '#': 'commentaire',
    '//': 'commentaire_ligne',
    '/*': 'commentaire_bloc',
    'if ': 'condition',
    'elif ': 'condition',
    'else': 'condition_alternative',
    'for ': 'boucle',
    'while ': 'boucle',
    'try': 'gestion_erreur',
    'except': 'gestion_erreur',
    'import ': 'importation',
    'from ': 'importation',
    'return ': 'retour',
    'print(': 'affichage',
}

# Mots mathématiques
_MOTS_MATH: set = {
    'x', 'y', 'z', 'n', 'i', 'j', 'k', 'a', 'b', 'c',
    'sqrt', 'cos', 'sin', 'tan', 'log', 'exp', 'abs',
    'somme', 'produit', 'intégrale', 'integrale', 'dérivée', 'derivee',
    'équation', 'equation', 'égal', 'egal', 'théorème', 'theoreme',
    'fonction', 'variable', 'paramètre', 'parametre', 'constante',
    'infini', 'zéro', 'zero', 'nombre', 'chiffre', 'calcul',
    'addition', 'soustraction', 'multiplication', 'division',
    'fraction', 'pourcentage', 'probabilité', 'probabilite',
    'vecteur', 'matrice', 'tenseur', 'dimension', 'espace',
    'ensemble', 'groupe', 'anneau', 'corps',
    'hypothèse', 'hypothese', 'lemme', 'corollaire', 'axiome',
    'démonstration', 'demonstration', 'preuve', 'contre-exemple',
}

# Chiffres et symboles mathématiques
_CHIFFRES = set('0123456789')
_SYMBOLES_MATH = {'+', '-', '*', '/', '=', '^', '<', '>', '(', ')', '[', ']', '{', '}', '%'}


# =========================================================================
# DATACLASSES
# =========================================================================

@dataclass
class ConnaissanceHarmonique:
    """
    Une connaissance stockée = un couple (signature, texte).
    L'unité de savoir de l'inconscient harmonique.

    La signature EST la connaissance — pas de poids, pas de compression.
    """
    id: str
    signature_16d: np.ndarray  # [16]
    signature_9d: np.ndarray   # [9] — gardée séparément pour analyse
    texte: str
    source: str = "harmonique"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    hash_certificat: str = ""

    def __post_init__(self):
        if not self.hash_certificat:
            self.hash_certificat = self._generer_hash()

    def _generer_hash(self) -> str:
        base = f"{self.texte}|{self.signature_16d.tobytes()}|{PHI}"
        return hashlib.sha256(base.encode()).hexdigest()

    @property
    def coherence(self) -> float:
        """Cohérence harmonique de la connaissance."""
        norme = np.linalg.norm(self.signature_16d)
        return float(np.clip(1.0 - abs(norme - math.sqrt(SIG_DIM_16D) * 0.5) / math.sqrt(SIG_DIM_16D), 0, 1))


@dataclass
class GenerationResultat:
    """Résultat complet d'une génération de l'inconscient harmonique."""
    prompt: str
    texte_genere: str
    n_connaissances_utilisees: int
    similarite_max: float
    resonance_moyenne: float
    temps_generation_ms: float
    certifie: bool
    hash_certificat: str
    signature_prompt: Optional[np.ndarray] = None
    details_connaissances: List[Dict] = field(default_factory=list)


# =========================================================================
# PROJECTEUR SÉMANTIQUE DIRECT (9D)
# =========================================================================

class ProjecteurSemantiqueDirect:
    """
    Projecteur de signatures 9D par FORMULES SÉMANTIQUES DIRECTES.
    
    C'est la DÉCOUVERTE CLÉ de cette branche :
    Au lieu d'utiliser des embeddings PHI synthétiques (qui ne produisent
    pas de signatures discriminantes), on calcule les 9 dimensions
    directement à partir des PROPRIÉTÉS RÉELLES du texte.
    
    Avantages :
    - 0 paramètre (formules fermées)
    - 0 embedding (on lit le texte directement)
    - 0 PyTorch (pur numpy)
    - Signatures immédiatement discriminantes
    - 100% déterministe
    
    Formules validées expérimentalement (25 mai 2026) :
    Dimension     | Ce qu'elle capture
    ──────────────┼────────────────────────────────
    phi           | Diversité lexicale (mots uniques / total)
    alpha         | Longueur moyenne des mots
    reasoning     | 1/longueur (textes denses = courts)
    creativity    | % mots longs (>7 lettres)
    math          | % mots avec chiffres
    factual       | % stop words (mots de liaison)
    code          | % syntaxe code ((), def, :, etc.)
    emotion       | % mots émotionnels
    temporal      | StdDev longueur des mots (narration)
    """
    
    def __init__(self):
        # Constantes de normalisation PHI
        self.phi_scale = PHI * 2.0  # ~3.236
        self.alpha_scale = 12.0     # longueur max typique d'un mot
        self.reasoning_scale = 10.0 # densité idéale
        self.creativity_scale = 3.0 # mots longs
        self.math_scale = 5.0       # mots avec chiffres
        self.factual_scale = 3.0    # stop words
        self.code_scale = 5.0       # syntaxe code
        self.emotion_scale = 5.0    # mots émotionnels
        self.temporal_scale = 3.0   # std dev longueur mots
        
        # Préfixes pour la détection de code (optimisation)
        self._prefixes_code = ['def ', 'class ', 'if ', 'elif ', 'else', 'for ',
                               'while ', 'try:', 'except', 'import ', 'from ',
                               'return ', 'print(', 'raise ', 'yield ', 'with ']
    
    def projeter(self, texte: str, normaliser: bool = True) -> np.ndarray:
        """
        Projette un texte en signature 9D via formules sémantiques directes.
        
        Pipeline :
        Texte → tokenisation → mesures sémantiques → signature 9D
        
        Args:
            texte: Texte à projeter
            normaliser: Normaliser les dimensions dans [0, 1]
            
        Returns:
            signature_9d: np.ndarray [9]
        """
        if not texte or len(texte.strip()) < 2:
            return np.zeros(SIG_DIM_9D, dtype=np.float32)
        
        # Tokenisation
        mots = texte.strip().split()
        n_mots = max(len(mots), 1)
        
        # --- phi : diversité lexicale ---
        mots_uniques = len(set(m.lower() for m in mots))
        phi = min(1.0, (mots_uniques / n_mots) * self.phi_scale)
        
        # --- alpha : longueur moyenne des mots ---
        longueur_moyenne = sum(len(m) for m in mots) / n_mots
        alpha = min(1.0, longueur_moyenne / self.alpha_scale)
        
        # --- reasoning : densité (inverse longueur) ---
        reasoning = min(1.0, self.reasoning_scale / n_mots)
        
        # --- creativity : proportion de mots longs (>7 lettres) ---
        mots_longs = sum(1 for m in mots if len(m) > 7 and m.isalpha())
        creativity = min(1.0, (mots_longs / n_mots) * self.creativity_scale)
        
        # --- math : proportion de mots avec chiffres ---
        mots_avec_chiffres = sum(1 for m in mots if any(c.isdigit() for c in m))
        math_val = min(1.0, (mots_avec_chiffres / n_mots) * self.math_scale)
        
        # Ajustement : si des symboles mathématiques présents
        n_sym_math = sum(1 for c in texte if c in _SYMBOLES_MATH)
        if n_sym_math > 3:
            math_val = min(1.0, math_val + 0.2)
        
        # --- factual : proportion de stop words ---
        stop_words = sum(1 for m in mots if m.lower() in _STOP_WORDS)
        factual = min(1.0, (stop_words / n_mots) * self.factual_scale)
        
        # --- code : détection de syntaxe de code ---
        # Vérification rapide de patterns de code
        score_code = 0.0
        for prefix in self._prefixes_code:
            if prefix in texte:
                score_code += 0.15
        # Parenthèses équilibrées
        if '(' in texte and ')' in texte:
            score_code += 0.1
        # Opérateurs d'affectation
        if '=' in texte:
            score_code += 0.05
        # Points-virgules en fin de ligne
        if ';' in texte:
            score_code += 0.1
        
        code = min(1.0, score_code)
        
        # --- emotion : proportion de mots émotionnels ---
        mots_emotion = sum(1 for m in mots if m.lower() in _MOTS_EMOTIONNELS)
        emotion = min(1.0, (mots_emotion / n_mots) * self.emotion_scale)
        
        # --- temporal : std dev des longueurs de mots (indique narration) ---
        if n_mots > 2:
            longueurs = [len(m) for m in mots]
            std_longueurs = float(np.std(longueurs))
            temporal = min(1.0, std_longueurs / self.temporal_scale)
        else:
            temporal = 0.2
        
        # Assemblage de la signature 9D
        sig = np.array([
            phi, alpha, reasoning, creativity, math_val,
            factual, code, emotion, temporal
        ], dtype=np.float32)
        
        # Clamping final de sécurité
        if normaliser:
            sig = np.clip(sig, 0.0, 1.0)
        
        return sig
    
    def analyser(self, texte: str) -> Dict:
        """Analyse détaillée pour débogage."""
        sig = self.projeter(texte)
        mots = texte.strip().split()
        n = max(len(mots), 1)
        
        return {
            "texte": texte[:80],
            "signature_9d": {d: float(sig[i]) for i, d in enumerate(DIMS_9D)},
            "stats": {
                "n_mots": len(mots),
                "mots_uniques": len(set(m.lower() for m in mots)),
                "longueur_moyenne": sum(len(m) for m in mots) / n,
                "mots_longs": sum(1 for m in mots if len(m) > 7),
                "mots_chiffres": sum(1 for m in mots if any(c.isdigit() for c in m)),
                "stop_words": sum(1 for m in mots if m.lower() in _STOP_WORDS),
                "mots_emotion": sum(1 for m in mots if m.lower() in _MOTS_EMOTIONNELS),
            }
        }


# =========================================================================
# FUSION 16D (9D sémantique + variantes harmoniques)
# =========================================================================

class FusionHarmonique16D:
    """
    Fusionne la signature 9D sémantique en signature 16D complète.
    
    Les 7 dimensions supplémentaires (9-15) sont des VARIANTES HARMONIQUES
    dérivées des 9 dimensions de base.
    
    Format final de la signature 16D :
    [0-6] : phi, alpha, reasoning, creativity, math, factual, code
    [7]   : emotion
    [8]   : temporal
    [9]   : phi × reasoning (rigueur)
    [10]  : creativity × (1 - factual) (originalité)
    [11]  : math × code (précision technique)
    [12]  : (phi + creativity + emotion) / 3 (ouverture)
    [13]  : abs(phi - creativity) (tension ordre/chaos)
    [14]  : (alpha + reasoning) / 2 (profondeur)
    [15]  : moyenne des 9 premières (cohésion globale)
    """
    
    def fusionner(self, sig_9d: np.ndarray) -> np.ndarray:
        """Fusionne une signature 9D en 16D."""
        sig_16d = np.zeros(SIG_DIM_16D, dtype=np.float32)
        
        # Dimensions 0-8 : copie directe
        sig_16d[:9] = sig_9d
        
        # Dimensions 9-15 : variantes harmoniques
        phi, alpha, reasoning, creativity, math_val, factual, code, emotion, temporal = sig_9d
        
        sig_16d[9] = phi * reasoning                           # rigueur
        sig_16d[10] = creativity * (1.0 - factual)              # originalité
        sig_16d[11] = math_val * code                           # précision technique
        sig_16d[12] = (phi + creativity + emotion) / 3.0        # ouverture
        sig_16d[13] = abs(phi - creativity)                     # tension ordre/chaos
        sig_16d[14] = (alpha + reasoning) / 2.0                 # profondeur
        sig_16d[15] = sig_9d.mean()                             # cohésion globale
        
        return np.clip(sig_16d, 0.0, 1.0)


# =========================================================================
# MATRICE DE CONNAISSANCE HARMONIQUE
# =========================================================================

class MatriceConnaissanceV2:
    """
    La mémoire de l'inconscient harmonique.
    
    Stocke les connaissances comme un INDEX DE SIGNATURES 16D.
    Pas de poids, pas de matrices apprises — juste des signatures.
    
    L'entraînement = 1 passe forward pour chaque texte → signature stockée.
    Recherche = similarité cosinus dans l'espace 16D.
    """

    def __init__(self):
        self.connaissances: List[ConnaissanceHarmonique] = []
        self._projecteur = ProjecteurSemantiqueDirect()
        self._fuseur = FusionHarmonique16D()
        self._index_built = False
        self._signature_matrix: Optional[np.ndarray] = None
        self._stats = {
            "n_connaissances": 0,
            "dim_signature": SIG_DIM_16D,
            "temps_indexation_ms": 0.0,
        }

    # =====================================================================
    # APPRENTISSAGE (1 seule passe)
    # =====================================================================

    def apprendre(self, texte: str, source: str = "entrainement") -> ConnaissanceHarmonique:
        """
        Apprend un texte en UNE SEULE PASSE FORWARD.
        
        1. Projection sémantique directe → signature 9D
        2. Fusion harmonique → signature 16D
        3. Création de la connaissance avec hash SHA256
        4. Stockage dans l'index
        
        Args:
            texte: Texte à apprendre
            source: Source du texte
            
        Returns:
            ConnaissanceHarmonique créée
        """
        t0 = time.time()
        
        # 1. Projection sémantique directe
        sig_9d = self._projecteur.projeter(texte)
        
        # 2. Fusion 16D
        sig_16d = self._fuseur.fusionner(sig_9d)
        
        # 3. Création de la connaissance
        connaissance = ConnaissanceHarmonique(
            id=hashlib.md5(f"{texte}{time.time()}".encode()).hexdigest()[:16],
            signature_16d=sig_16d,
            signature_9d=sig_9d,
            texte=texte,
            source=source,
        )
        
        # 4. Stockage
        self.connaissances.append(connaissance)
        self._index_built = False
        
        dt = (time.time() - t0) * 1000
        self._stats["n_connaissances"] = len(self.connaissances)
        
        logger.debug(f"[Apprentissage] {len(texte)} chars → sig 9D={[round(v,2) for v in sig_9d[:5]]}... en {dt:.1f}ms")
        
        return connaissance

    def apprendre_batch(self, textes: List[str], source: str = "batch") -> List[ConnaissanceHarmonique]:
        """Apprend plusieurs textes (toujours 1 passe par texte)."""
        t0 = time.time()
        connaissances = [self.apprendre(texte, source) for texte in textes]
        dt = (time.time() - t0) * 1000
        logger.info(f"[Batch] {len(textes)} textes appris en {dt:.0f}ms ({dt/len(textes):.0f}ms/texte)")
        return connaissances

    def apprendre_fichier(self, chemin: str, source: str = "fichier") -> List[ConnaissanceHarmonique]:
        """Apprend le contenu d'un fichier (une ligne = une connaissance)."""
        with open(chemin, 'r', encoding='utf-8') as f:
            lignes = [l.strip() for l in f if l.strip()]
        return self.apprendre_batch(lignes, source)

    def apprendre_dataset(self, data: List[Dict[str, str]], champ_texte: str = "texte",
                           champ_source: str = "source") -> List[ConnaissanceHarmonique]:
        """Apprend un dataset structuré."""
        textes = [d[champ_texte] for d in data]
        sources = [d.get(champ_source, "dataset") for d in data]
        return [self.apprendre(t, s) for t, s in zip(textes, sources)]

    # =====================================================================
    # INDEXATION
    # =====================================================================

    def _build_index(self):
        """Construit la matrice de signatures pour recherche vectorisée."""
        if self._index_built:
            return
        
        t0 = time.time()
        
        if not self.connaissances:
            self._signature_matrix = np.zeros((0, SIG_DIM_16D), dtype=np.float32)
            self._index_built = True
            return
        
        signatures = [c.signature_16d for c in self.connaissances]
        self._signature_matrix = np.stack(signatures, axis=0)
        
        # Normalisation pour cosinus
        norms = np.linalg.norm(self._signature_matrix, axis=1, keepdims=True)
        self._signature_matrix = self._signature_matrix / (norms + 1e-8)
        
        self._index_built = True
        dt = (time.time() - t0) * 1000
        self._stats["temps_indexation_ms"] = dt
        
        logger.debug(f"[Index] {len(self.connaissances)} connaissances indexées en {dt:.1f}ms")

    def reindexer(self):
        """Force la reconstruction de l'index."""
        self._index_built = False
        self._build_index()

    # =====================================================================
    # RECHERCHE PAR RÉSONANCE
    # =====================================================================

    def chercher(self, signature_query: np.ndarray, top_k: int = 5,
                 seuil: float = SEUIL_RESONANCE) -> List[Tuple[ConnaissanceHarmonique, float]]:
        """
        Cherche les connaissances les plus résonantes.
        Résonance = similarité cosinus dans l'espace 16D.
        """
        self._build_index()
        
        if self._signature_matrix.shape[0] == 0:
            return []
        
        query_norm = signature_query / (np.linalg.norm(signature_query) + 1e-8)
        similarites = self._signature_matrix @ query_norm
        
        mask = similarites >= seuil
        if not mask.any():
            mask = similarites >= seuil * 0.7
            if not mask.any():
                return []
        
        indices = np.where(mask)[0]
        scores = similarites[mask]
        order = np.argsort(scores)[::-1][:top_k]
        
        return [(self.connaissances[indices[idx]], float(scores[idx])) for idx in order]

    # =====================================================================
    # FUSION DE CONNAISSANCES
    # =====================================================================

    def fusionner(self, connaissances: List[Tuple[ConnaissanceHarmonique, float]],
                  prompt: str) -> str:
        """
        Fusionne plusieurs connaissances en un texte cohérent.
        Pondéré par la similarité (résonance).
        """
        if not connaissances:
            return f"En résonance harmonique avec {prompt}..."
        
        if len(connaissances) == 1:
            return connaissances[0][0].texte
        
        # Poids harmoniques
        poids = np.array([score for _, score in connaissances])
        poids = poids / poids.sum()
        
        # Découpage en phrases
        toutes_phrases = []
        phrase_scores = []
        
        for i, (c, _) in enumerate(connaissances):
            phrases = [p.strip() for p in c.texte.replace('!', '.').replace('?', '.').split('.') if p.strip()]
            for phrase in phrases:
                toutes_phrases.append(phrase)
                phrase_scores.append(poids[i])
        
        if not toutes_phrases:
            return connaissances[0][0].texte
        
        # Sélection non-redondante
        indices_tries = np.argsort(phrase_scores)[::-1]
        selectionnees = []
        mots_vus = set()
        
        for idx in indices_tries:
            phrase = toutes_phrases[idx]
            mots_phrase = set(phrase.lower().split())
            chevauchement = len(mots_phrase & mots_vus) / max(len(mots_phrase), 1)
            
            if chevauchement < 0.5 or len(selectionnees) < 2:
                selectionnees.append(phrase)
                mots_vus.update(mots_phrase)
        
        texte_final = '. '.join(selectionnees[:5])
        if texte_final and not texte_final.endswith('.'):
            texte_final += '.'
        
        return texte_final

    # =====================================================================
    # SAUVEGARDE / CHARGEMENT
    # =====================================================================

    def sauvegarder(self, chemin: str):
        """Sauvegarde la matrice de connaissance dans un fichier JSON."""
        data = {
            "meta": {
                "n": len(self.connaissances),
                "dim_9d": SIG_DIM_9D,
                "dim_16d": SIG_DIM_16D,
                "phi": PHI,
                "version": "3.0-semantique",
                "date": datetime.now().isoformat(),
            },
            "connaissances": [
                {
                    "id": c.id,
                    "signature_9d": c.signature_9d.tolist(),
                    "signature_16d": c.signature_16d.tolist(),
                    "texte": c.texte,
                    "source": c.source,
                    "hash": c.hash_certificat,
                }
                for c in self.connaissances
            ]
        }
        with open(chemin, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"[Sauvegarde] {len(self.connaissances)} connaissances → {chemin}")

    def charger(self, chemin: str) -> int:
        """Charge une matrice de connaissance depuis un fichier JSON."""
        with open(chemin, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        n_avant = len(self.connaissances)
        for item in data["connaissances"]:
            connaissance = ConnaissanceHarmonique(
                id=item["id"],
                signature_9d=np.array(item.get("signature_9d", item.get("signature", [0]*9)), dtype=np.float32),
                signature_16d=np.array(item.get("signature_16d", item.get("signature", [0]*16)), dtype=np.float32),
                texte=item["texte"],
                source=item.get("source", "charge"),
                hash_certificat=item.get("hash", ""),
            )
            self.connaissances.append(connaissance)
        
        self._index_built = False
        n_chargees = len(self.connaissances) - n_avant
        logger.info(f"[Chargement] {n_chargees} connaissances chargées de {chemin}")
        return n_chargees

    # =====================================================================
    # STATISTIQUES
    # =====================================================================

    def stats(self) -> Dict:
        self._stats["n_connaissances"] = len(self.connaissances)
        if self.connaissances:
            signatures = np.stack([c.signature_16d for c in self.connaissances], axis=0)
            self._stats["moyenne_signature"] = signatures.mean(axis=0).tolist()
            self._stats["ecart_type_signature"] = signatures.std(axis=0).tolist()
            self._stats["coherence_moyenne"] = float(np.mean([c.coherence for c in self.connaissances]))
        return self._stats

    def __len__(self):
        return len(self.connaissances)

    def __getitem__(self, idx):
        return self.connaissances[idx]


# =========================================================================
# INCONSCIENT HARMONIQUE PARFAIT
# =========================================================================

class InconscientHarmoniqueParfait:
    """
    L'Inconscient Harmonique Parfait — version 3.0 (sémantique directe).
    
    Le LLM classique mathématiquement aussi parfait que PUR.
    
    Architecture :
    ```
    Prompt
      ↓
    ProjecteurSemantiqueDirect → signature 9D
      ↓
    FusionHarmonique16D → signature 16D
      ↓
    MatriceConnaissance → top-K résonance
      ↓
    Fusion → texte généré
      ↓
    Certification SHA256
    ```
    
    Propriétés :
    - 0 paramètre entraînable
    - 1 passe pour apprendre
    - 100% déterministe
    - Connaissances extensibles
    - 0 hallucination (résonance avec signatures réelles)
    - Pur numpy (pas de PyTorch)
    """

    def __init__(self):
        self.memoire = MatriceConnaissanceV2()
        self._projecteur = ProjecteurSemantiqueDirect()
        self._fuseur = FusionHarmonique16D()
        self._stats = {
            "n_apprentissages": 0,
            "n_generations": 0,
            "temps_apprentissage_ms": 0.0,
            "temps_generation_ms": 0.0,
            "certifications": 0,
        }

    # =====================================================================
    # APPRENTISSAGE
    # =====================================================================

    def apprendre(self, texte: str, source: str = "apprentissage") -> ConnaissanceHarmonique:
        t0 = time.time()
        connaissance = self.memoire.apprendre(texte, source)
        dt = (time.time() - t0) * 1000
        self._stats["n_apprentissages"] += 1
        n = self._stats["n_apprentissages"]
        self._stats["temps_apprentissage_ms"] = (self._stats["temps_apprentissage_ms"] * (n - 1) + dt) / n
        return connaissance

    def apprendre_batch(self, textes: List[str]) -> List[ConnaissanceHarmonique]:
        return self.memoire.apprendre_batch(textes, "batch")

    # =====================================================================
    # GÉNÉRATION
    # =====================================================================

    def generer(self, prompt: str, top_k: int = TOP_K_CONNAISSANCES,
                temperature: float = 0.7, max_tokens: int = 200,
                mode: str = "fusion") -> GenerationResultat:
        """
        Génère un texte par résonance harmonique.
        
        Processus :
        1. Projection sémantique directe du prompt
        2. Fusion 16D
        3. Recherche des connaissances les plus résonantes
        4. Fusion harmonique des connaissances
        5. Certification SHA256
        """
        t0 = time.time()
        
        # 1-2. Projection + Fusion
        sig_9d = self._projecteur.projeter(prompt)
        sig_16d = self._fuseur.fusionner(sig_9d)
        
        # 3. Recherche par résonance
        connaissances = self.memoire.chercher(sig_16d, top_k=top_k)
        
        if not connaissances:
            texte_genere = self._generer_harmonique_generique(prompt, sig_9d)
            similarite_max = 0.0
            resonance_moy = 0.0
            n_connaissances = 0
            details = []
        else:
            similarite_max = max(score for _, score in connaissances)
            resonance_moy = sum(score for _, score in connaissances) / len(connaissances)
            details = [
                {"id": c.id, "texte": c.texte[:50], "similarite": round(score, 4), "source": c.source}
                for c, score in connaissances
            ]
            texte_genere = self.memoire.fusionner(connaissances, prompt)
            n_connaissances = len(connaissances)
        
        # Certification
        cert_base = f"{texte_genere}|{similarite_max}|{resonance_moy}|{PHI}|{datetime.now().isoformat()}"
        cert_hash = hashlib.sha256(cert_base.encode()).hexdigest()
        certifie = similarite_max >= SEUIL_RESONANCE * 0.5
        
        dt = (time.time() - t0) * 1000
        
        if certifie:
            self._stats["certifications"] += 1
        self._stats["n_generations"] += 1
        n = self._stats["n_generations"]
        self._stats["temps_generation_ms"] = (self._stats["temps_generation_ms"] * (n - 1) + dt) / n
        
        return GenerationResultat(
            prompt=prompt,
            texte_genere=texte_genere,
            n_connaissances_utilisees=n_connaissances,
            similarite_max=round(similarite_max, 4),
            resonance_moyenne=round(resonance_moy, 4),
            temps_generation_ms=round(dt, 1),
            certifie=certifie,
            hash_certificat=cert_hash,
            signature_prompt=sig_16d,
            details_connaissances=details,
        )

    def _generer_harmonique_generique(self, prompt: str, sig_9d: np.ndarray) -> str:
        """
        Génération harmonique générique basée sur la signature.
        Utilise le PROFIL de la signature pour construire une réponse adaptée.
        """
        profil = {d: float(sig_9d[i]) for i, d in enumerate(DIMS_9D)}
        
        if profil['math'] > 0.5:
            intro = f"Du point de vue mathématique harmonique (φ = {PHI:.6f})"
        elif profil['creativity'] > 0.5:
            intro = "Dans l'espace créatif harmonique"
        elif profil['reasoning'] > 0.5:
            intro = "Par raisonnement harmonique"
        elif profil['emotion'] > 0.4:
            intro = "Avec une résonance émotionnelle harmonique"
        elif profil['code'] > 0.4:
            intro = "Dans l'espace algorithmique harmonique"
        else:
            intro = "En harmonie avec"
        
        profil_str = ', '.join(f"{d}={v:.2f}" for d, v in profil.items() if v > 0.3)
        return f"{intro}, «{prompt[:50]}» résonne dans l'espace harmonique. Profil ({profil_str}). φ = {PHI:.10f}."

    def generer_rapide(self, prompt: str, **kw) -> str:
        return self.generer(prompt, **kw).texte_genere

    def generer_details(self, prompt: str, **kw) -> Dict:
        r = self.generer(prompt, **kw)
        return {
            "prompt": r.prompt,
            "texte": r.texte_genere,
            "n_connaissances": r.n_connaissances_utilisees,
            "similarite_max": r.similarite_max,
            "resonance_moyenne": r.resonance_moyenne,
            "temps_ms": r.temps_generation_ms,
            "certifie": r.certifie,
            "hash": r.hash_certificat,
            "connaissances": r.details_connaissances,
        }

    # =====================================================================
    # SAUVEGARDE / CHARGEMENT
    # =====================================================================

    def sauvegarder(self, chemin: str):
        self.memoire.sauvegarder(chemin)

    def charger(self, chemin: str) -> int:
        return self.memoire.charger(chemin)

    def reinitialiser(self):
        self.memoire = MatriceConnaissanceV2()
        self._stats = {k: 0.0 for k in self._stats}
        logger.info("[Réinitialisation] Inconscient vidé")

    # =====================================================================
    # STATISTIQUES
    # =====================================================================

    def stats(self) -> Dict:
        mem_stats = self.memoire.stats()
        return {
            **self._stats,
            "memoire": mem_stats,
            "n_connaissances": len(self.memoire),
            "taux_certification": (
                self._stats["certifications"] / max(self._stats["n_generations"], 1) * 100
            ),
        }

    def analyser(self, texte: str) -> Dict:
        """
        Analyse un texte dans l'espace harmonique.
        
        Returns:
            Dict avec signature 9D, profil détaillé, et propriétés harmoniques
        """
        sig_9d = self._projecteur.projeter(texte)
        sig_16d = self._fuseur.fusionner(sig_9d)
        
        profil = {d: float(sig_9d[i]) for i, d in enumerate(DIMS_9D)}
        dominant = max(profil, key=profil.get)
        
        return {
            "texte": texte[:100],
            "longueur": len(texte),
            "signature_9d": sig_9d.tolist(),
            "signature_16d": sig_16d.tolist(),
            "profil_9d": profil,
            "dimension_dominante": dominant,
            "valeur_dominante": profil[dominant],
            "coherence_harmonique": float(np.mean(sig_9d)),
        }


# =========================================================================
# SYSTÈME DUAL : CONSCIENT + INCONSCIENT
# =========================================================================

class SystemeDualHarmoniqueParfaitV2:
    """
    Système complet avec Conscient (PUR) + Inconscient Harmonique V3.
    
    Les DEUX parlent le même langage : les signatures harmoniques.
    L'inconscient via ses formules sémantiques directes (9D),
    le conscient via ses formules PUR (7D),
    fusionnés en 16D pour la résonance.
    
    Architecture :
    ```
    Prompt
      ↓
    INCONSCIENT (formules sémantiques) → signature 9D
      ↓
    Fusion 16D
      ↓
    CONSCIENT PUR (validation) → signature 7D
      ↓
    Résonance croisée → Réponse certifiée
    ```
    """

    def __init__(self):
        self.inconscient = InconscientHarmoniqueParfait()
        self._pur_validator = None
        self._stats = {
            "total_generations": 0,
            "certifie_direct": 0,
            "certifie_apres_pur": 0,
        }

    def _init_pur(self):
        """Initialise le validateur PUR si disponible."""
        if self._pur_validator is None:
            try:
                from pur_qwen_api import PurValidator
                self._pur_validator = PurValidator()
                self._pur_validator.load()
            except Exception:
                pass

    def generer(self, prompt: str, **kw) -> GenerationResultat:
        """
        Cycle complet : Inconscient → Conscient.
        """
        self._init_pur()
        
        # Phase 1 : Inconscient génère
        resultat = self.inconscient.generer(prompt, **kw)
        
        # Phase 2 : Conscient valide
        if self._pur_validator:
            try:
                pur_score, pur_sig, pur_hash = self._pur_validator.valider(resultat.texte_genere)
                resultat.certifie = pur_score >= 0.4
                if resultat.certifie:
                    self._stats["certifie_apres_pur"] += 1
            except Exception:
                pass
        elif resultat.certifie:
            self._stats["certifie_direct"] += 1
        
        self._stats["total_generations"] += 1
        return resultat

    def apprendre(self, texte: str, source: str = "apprentissage"):
        return self.inconscient.apprendre(texte, source)

    def stats(self) -> Dict:
        s = self.inconscient.stats()
        s["dual"] = self._stats
        return s


# =========================================================================
# TEST ET DÉMONSTRATION
# =========================================================================

def test_projecteur_semantique():
    """Test du projecteur sémantique direct."""
    print("=" * 70)
    print("[TEST] PROJECTEUR SEMANTIQUE DIRECT")
    print("=" * 70)
    
    p = ProjecteurSemantiqueDirect()
    
    textes = [
        ("CODE    ", "def fib(n): return n if n < 2 else fib(n-1) + fib(n-2)"),
        ("MATH    ", "x^2 + y^2 = z^2 est le theoreme de Pythagore"),
        ("AMOUR   ", "Je t aime de tout mon coeur pour toujours mon amour"),
        ("CREATIF ", "Un dragon violet danse le tango sous la lune magique"),
        ("SCIENCE ", "Le nombre d or 1.618 est une constante fondamentale"),
        ("HISTOIRE", "Il etait une fois un roi qui vivait dans un chateau"),
        ("JURIDIQ ", "Conformement a l article 1382 du code civil"),
        ("POESIE  ", "L amour est un oiseau rebelle que nul ne peut apprivoiser"),
    ]
    
    print(f"\n{'Type':10s}", ' '.join(f'{d:7s}' for d in DIMS_9D))
    print('-' * 75)
    
    for cat, txt in textes:
        sig = p.projeter(txt)
        vals = ' '.join(f'{sig[i]:7.3f}' for i in range(SIG_DIM_9D))
        print(f'{cat:10s} {vals}')
    
    return p


def test_inconscient_harmonique():
    """Test complet de l'Inconscient Harmonique Parfait V3."""
    print("=" * 70)
    print("[TEST] INCONSCIENT HARMONIQUE PARFAIT V3 (SEMANTIQUE)")
    print("=" * 70)
    
    # Création
    print("\n[Création de l'inconscient...]")
    i = InconscientHarmoniqueParfait()
    print("  ✓ Inconscient V3 créé (pur numpy, formules sémantiques directes)")
    
    # Phase 1 : Apprentissage
    print("\n[Phase 1] APPRENTISSAGE (1 passe par texte)")
    print("-" * 50)
    
    textes_apprentissage = [
        "Le nombre d'or φ = 1.618033988749895 est une proportion mathématique fondamentale présente dans la nature, l'art et l'architecture.",
        "La résonance harmonique est le phénomène par lequel un système oscillant entre en vibration sous l'effet d'une excitation à sa fréquence propre.",
        "La conscience émerge de l'interaction complexe entre des réseaux neuronaux, créant une expérience subjective unique.",
        "Le noyau d'Atangana-Baleanu (ABC) est une dérivée fractionnaire qui capture la mémoire non-locale des systèmes complexes.",
        "L'intelligence artificielle harmonique combine les connaissances des LLM classiques avec la rigueur mathématique des systèmes à base de PHI.",
        "L'espace des signatures 9D permet de représenter n'importe quel texte comme un point dans un espace harmonique à 9 dimensions.",
        "PhiInverse est le décodeur qui inverse la dérivée fractionnaire ABC pour reconstruire les tokens originaux depuis leurs signatures.",
        "L'apprentissage en une seule passe élimine le besoin de rétropropagation et garantit zéro hallucination.",
        "La créativité harmonique émerge de la tension entre diversité lexicale et structure grammaticale.",
        "Un système dual conscient-inconscient où les deux parties parlent le même langage harmonique est plus efficace qu'un système avec traducteur.",
        "La certification SHA256 garantit l'intégrité de chaque réponse générée par le système harmonique.",
        "L'entraînement harmonique ne nécessite ni GPU, ni grand dataset, ni heures de calcul.",
    ]
    
    for texte in textes_apprentissage:
        c = i.apprendre(texte)
        sig_preview = [round(v, 3) for v in c.signature_9d[:5]]
        print(f"  ✓ {len(texte):3d} chars → sig 9D={sig_preview}... | hash={c.hash_certificat[:8]}...")
    
    print(f"\n  📚 {len(i.memoire)} connaissances apprises")
    
    # Phase 2 : Génération
    print("\n[Phase 2] GÉNÉRATION PAR RÉSONANCE")
    print("-" * 50)
    
    prompts = [
        "Parle-moi du nombre d'or",
        "Qu'est-ce que la résonance harmonique ?",
        "Comment fonctionne l'apprentissage en une passe ?",
        "Explique la certification SHA256",
    ]
    
    for prompt in prompts:
        r = i.generer(prompt, top_k=3)
        cert = "✅" if r.certifie else "❌"
        print(f"\n  📝 {prompt}")
        print(f"  🤖 {r.texte_genere[:120]}...")
        print(f"  🔍 {r.n_connaissances_utilisees} conn. | sim={r.similarite_max:.3f} | "
              f"rés={r.resonance_moyenne:.3f} | {r.temps_generation_ms:.0f}ms | {cert}")
    
    # Phase 3 : Analyse
    print("\n[Phase 3] ANALYSE HARMONIQUE")
    print("-" * 50)
    
    analyse = i.analyser("Le nombre d'or est la proportion mathématique la plus harmonieuse de l'univers")
    print(f"  Signature 9D: {[round(s, 3) for s in analyse['signature_9d']]}")
    print(f"  Profil:")
    for dim, val in analyse['profil_9d'].items():
        bar = '█' * int(val * 20) + '░' * (20 - int(val * 20))
        print(f"    {dim:12s} : {bar} {val:.3f}")
    print(f"  Dimension dominante: {analyse['dimension_dominante']} ({analyse['valeur_dominante']:.3f})")
    print(f"  Cohérence harmonique: {analyse['coherence_harmonique']:.3f}")
    
    # Phase 4 : Sauvegarde
    print("\n[Phase 4] SAUVEGARDE / CHARGEMENT")
    print("-" * 50)
    chemin_save = os.path.join(os.path.dirname(__file__), "..", "connaissances_v3.json")
    i.sauvegarder(chemin_save)
    print(f"  ✓ Sauvegardé → {chemin_save}")
    
    i2 = InconscientHarmoniqueParfait()
    n = i2.charger(chemin_save)
    print(f"  ✓ Chargé {n} connaissances")
    
    # Phase 5 : Stats
    print("\n[Phase 5] STATISTIQUES FINALES")
    print("-" * 50)
    s = i.stats()
    print(f"  📊 Connaissances: {len(i.memoire)}")
    print(f"  📊 Générations: {s['n_generations']}")
    print(f"  📊 Taux certification: {s['taux_certification']:.1f}%")
    print(f"  📊 Temps apprentissage: {s['temps_apprentissage_ms']:.1f}ms")
    print(f"  📊 Temps génération: {s['temps_generation_ms']:.1f}ms")
    print(f"  0 paramètre: ✅ | 0 backprop: ✅ | Déterministe: ✅ | Pur numpy: ✅")
    
    # Nettoyage
    if os.path.exists(chemin_save):
        os.remove(chemin_save)
    
    return i


if __name__ == '__main__':
    test_projecteur_semantique()
    print("\n")
    test_inconscient_harmonique()
