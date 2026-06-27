"""
HologrammeConnecteur — Pont entre l'hologramme 64x64 et la generation de texte
=============================================================================
Role : Extraire les connaissances resonantes depuis l'hologramme (ka_knowledge_base/hologramme.npy)
       et les formater pour injection dans le HarmonicGenerator.

Flux :
  1. Charger l'hologramme 64x64 complex depuis le fichier .npy
  2. Creer un TokeniseurOndes + LecteurResonantMultiple (pur numpy)
  3. Pour chaque requete : enregistrer le prompt, faire resonner les lecteurs,
     extraire les top tokens resonants → contexte textuel
  4. Injecter le contexte dans HarmonicGenerator.generate()

Dependances : numpy seulement (pas de torch, pas de LLM)
"""

import os
import sys
import time
import json
import math
import hashlib
import numpy as np
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass

# =========================================================================
# IMPORT DIRECT depuis harmonic_resonance_generator.py (pur numpy)
# Meme mecanisme que bridge_harmonic_deepseek_gguf.py
# =========================================================================
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

import importlib.util

_resonance_path = os.path.join(
    _project_root, "harmonic_training", "model", "harmonic_resonance_generator.py"
)

_spec = importlib.util.spec_from_file_location(
    "harmonic_training.model.harmonic_resonance_generator",
    _resonance_path
)
_resonance_module = importlib.util.module_from_spec(_spec)
sys.modules["harmonic_training.model.harmonic_resonance_generator"] = _resonance_module
_spec.loader.exec_module(_resonance_module)

# Classes importees directement du module pur numpy
HologrammeMonde = _resonance_module.HologrammeMonde
TokeniseurOndes = _resonance_module.TokeniseurOndes
LecteurResonantMultiple = _resonance_module.LecteurResonantMultiple
VOCABULAIRE_BASE = _resonance_module.VOCABULAIRE_BASE
PHI = _resonance_module.PHI
NX = _resonance_module.NX
NY = _resonance_module.NY

# =========================================================================
# VOCABULAIRE ETENDU (import silencieux — echoue gracieusement si absent)
# =========================================================================
try:
    _vocab_path = os.path.join(
        _project_root, "harmonic_training", "model", "vocabulaire_etendu.py"
    )
    _vocab_spec = importlib.util.spec_from_file_location(
        "harmonic_training.model.vocabulaire_etendu", _vocab_path
    )
    _vocab_module = importlib.util.module_from_spec(_vocab_spec)
    sys.modules["harmonic_training.model.vocabulaire_etendu"] = _vocab_module
    _vocab_spec.loader.exec_module(_vocab_module)
    VOCABULAIRE_ETENDU = _vocab_module.VOCABULAIRE_ETENDU
    VOCAB_SIZE_ETENDU = _vocab_module.VOCAB_SIZE_ETENDU
    print(f"  [HologrammeConnecteur] Vocabulaire etendu charge: {VOCAB_SIZE_ETENDU} tokens")
except Exception:
    VOCABULAIRE_ETENDU = VOCABULAIRE_BASE  # fallback
    VOCAB_SIZE_ETENDU = len(VOCABULAIRE_BASE)
    print(f"  [HologrammeConnecteur] Vocabulaire etendu NON DISPONIBLE, fallback base ({VOCAB_SIZE_ETENDU} tokens)")

# =========================================================================
# Import FastText (optionnel — fallback n-gram si absent)
# =========================================================================
try:
    from gensim.models import FastText as GensimFastText
    HAS_FASTTEXT_LIB = True
except ImportError:
    HAS_FASTTEXT_LIB = False

# =========================================================================
# CONSTANTES
# =========================================================================
HOLOGRAMME_PATH = os.path.join(
    _project_root, "ka_knowledge_base", "hologramme.npy"
)
N_LECTEURS = 8
N_REP_LECTURE = 30
TOP_K_RESONANCE = 10
SEUIL_ACTIVATION_MIN = 0.05
SEUIL_COOCCURRENCE_MIN = 1  # Nombre minimum de co-occurrences pour etre retenu

# Chemin vers la matrice de co-occurrence (utilisee pour le retrieval semantique)
COOCCURRENCE_PATH = os.path.join(
    _project_root, "ka_knowledge_base", "cooccurrence.json"
)
FREQUENCE_PATH = os.path.join(
    _project_root, "ka_knowledge_base", "frequence_tokens.json"
)
PPMI_PATH = os.path.join(
    _project_root, "ka_knowledge_base", "ppmi.json"
)
FASTTEXT_MODEL_PATH = os.path.join(
    _project_root, "ka_knowledge_base", "fasttext_model.bin"
)

# Vecteurs pre-entraines fastText (cc.fr.300) pour le bridge OOV
# Telecharges et filtres par scripts/telecharger_vecteurs_pretrained.py
PRETRAINED_VECS_FILE = os.path.join(
    _project_root, "ka_knowledge_base", "vecteurs_pretrained.npy"
)
PRETRAINED_WORDS_FILE = os.path.join(
    _project_root, "ka_knowledge_base", "vecteurs_pretrained_words.json"
)

# Nombre maximum de tokens de substitution pour l'expansion OOV
TOP_K_EXPANSION_OOV = 3
SEUIL_SIMILARITE_OOV = 0.25

# Poids du scoring hybride : alpha * PPMI + (1-alpha) * similarite embedding
# alpha = 0.80 → PPMI domine pour les tokens connus
# Pour les tokens inconnus (OOV), seul le terme embedding compte
SCORE_ALPHA_PPMI = 0.80

# Seuil IDF : un token present dans plus de X% des textes est un stopword
SEUIL_STOPWORD_RATIO = 0.50


# =========================================================================
# HOLOGRAMME CONNECTEUR
# =========================================================================

class HologrammeConnecteur:
    """
    Pont minimal entre l'hologramme 64x64 et le generateur de texte.
    
    Utilise le systeme de resonance inverse (LecteurResonantMultiple)
    pour extraire les informations pertinentes pour un prompt donne.
    
    Architecture :
      HologrammeMonde (64×64 complex) ← stocke les connaissances
      TokeniseurOndes                   ← tokenisation par projection d'ondes
      LecteurResonantMultiple (×8)      ← conscience parallele
    
    Usage :
        >>> connecteur = HologrammeConnecteur()
        >>> resultat = connecteur.resonner("Parle-moi de l'empire du Ghana")
        >>> print(resultat["contexte"])  
        # "Connaissances disponibles : ghana, empire, afrique, commerce, or..."
        >>> print(resultat["top_tokens"])
        # [('ghana', 0.89), ('empire', 0.76), ('afrique', 0.72), ...]
    """
    
    def __init__(self, hologramme_path: Optional[str] = None):
        """
        Initialise le connecteur.
        
        Args:
            hologramme_path: Chemin vers le fichier hologramme.npy.
                             Si None, utilise HOLOGRAMME_PATH par defaut.
        """
        self._chemin = hologramme_path or HOLOGRAMME_PATH
        self._initialise = False
        self._stats = {
            "n_resonances": 0,
            "n_tokens_extraits": 0,
            "temps_total_ms": 0.0,
            "erreurs": 0,
        }
        
        # Initialiser les composants harmoniques
        self._initialiser_hologramme()
    
    def _charger_cooccurrence(self, tokenizer) -> Tuple[Dict[int, Dict[int, int]], Dict[int, int]]:
        """Charge la matrice de co-occurrence ET la frequence des tokens.
        
        La matrice de co-occurrence enregistre, pour chaque paire de tokens,
        le nombre de textes d'injection ou ils apparaissent ensemble.
        La frequence enregistre le nombre de textes ou chaque token apparait.
        
        Ces donnees sont construites par scripts/reinjecter_connaissances.py
        et permettent le retrieval semantique par co-occurrence ponderee IDF.
        
        Args:
            tokenizer: TokeniseurOndes (pour l'affichage debug des stopwords)
        
        Returns:
            (cooc, freq):
                cooc[t1][t2] = nombre de textes ou t1 et t2 co-apparaissent
                freq[t] = nombre de textes ou le token t apparait
        """
        cooc_path = COOCCURRENCE_PATH
        freq_path = FREQUENCE_PATH
        
        if not os.path.exists(cooc_path):
            print(f"  [HologrammeConnecteur] Co-occurrence NON DISPONIBLE ({cooc_path})")
            print(f"  [HologrammeConnecteur] Fallback: delta Fourier uniquement")
            return {}, {}
        
        try:
            # Charger co-occurrence
            with open(cooc_path, 'r', encoding='utf-8') as f:
                cooc_json = json.load(f)
            
            cooc: Dict[int, Dict[int, int]] = {}
            for t1_str, voisins in cooc_json.items():
                t1 = int(t1_str)
                cooc[t1] = {int(t2_str): count for t2_str, count in voisins.items()}
            
            total_pairs = sum(len(v) for v in cooc.values())
            
            # Charger frequence
            freq: Dict[int, int] = {}
            if os.path.exists(freq_path):
                with open(freq_path, 'r', encoding='utf-8') as f:
                    freq_json = json.load(f)
                freq = {int(t): count for t, count in freq_json.items()}
            
            print(f"  [HologrammeConnecteur] Co-occurrence chargee: "
                  f"{len(cooc)} tokens, {total_pairs} paires")
            print(f"  [HologrammeConnecteur] Frequence chargee: {len(freq)} tokens")
            
            # Afficher les stopwords identifies (top 5 tokens les plus frequents)
            top_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"  [HologrammeConnecteur] Stopwords (top frequence):")
            for tid, count in top_freq:
                mot = tokenizer.i2w.get(tid, f'<{tid}>')
                print(f"    '{mot}' (id={tid}): {count} textes")
            
            return cooc, freq
            
        except Exception as e:
            print(f"  [HologrammeConnecteur] ERREUR chargement co-occurrence: {e}")
            return {}, {}

    def _charger_ppmi(self) -> Dict[int, Dict[int, float]]:
        """Charge la matrice PPMI (Positive Pointwise Mutual Information).
        
        La PPMI est une transformation de la matrice de co-occurrence qui
        penalise naturellement les co-occurrences dues au hasard (stopwords).
        
        PPMI(t1,t2) = max(0, log2(N * count / (freq[t1] * freq[t2])))
        
        Returns:
            ppmi[t1][t2] = valeur PPMI (float, > 0)
            Dict vide si fichier indisponible.
        """
        if not os.path.exists(PPMI_PATH):
            print(f"  [HologrammeConnecteur] PPMI NON DISPONIBLE ({PPMI_PATH})")
            return {}
        try:
            with open(PPMI_PATH, 'r', encoding='utf-8') as f:
                ppmi_json = json.load(f)
            ppmi: Dict[int, Dict[int, float]] = {}
            for t1_str, voisins in ppmi_json.items():
                t1 = int(t1_str)
                ppmi[t1] = {int(t2_str): val for t2_str, val in voisins.items()}
            total_pairs = sum(len(v) for v in ppmi.values())
            print(f"  [HologrammeConnecteur] PPMI chargee: "
                  f"{len(ppmi)} tokens, {total_pairs} paires")
            return ppmi
        except Exception as e:
            print(f"  [HologrammeConnecteur] ERREUR chargement PPMI: {e}")
            return {}

    def _charger_fasttext(self):
        """Charge le modele FastText pour l'expansion des tokens OOV.
        
        Si gensim n'est pas installe ou le fichier .bin est absent,
        utilise un fallback base sur la similarite de n-grams caracteres.
        
        Returns:
            True si FastText charge avec succes, False sinon.
        """
        self._fasttext_model = None
        if not os.path.exists(FASTTEXT_MODEL_PATH):
            print(f"  [HologrammeConnecteur] FastText NON DISPONIBLE ({FASTTEXT_MODEL_PATH})")
            print(f"  [HologrammeConnecteur] Fallback: similarite n-grams caracteres")
            return False
        if not HAS_FASTTEXT_LIB:
            print(f"  [HologrammeConnecteur] gensim non installe (pip install gensim)")
            print(f"  [HologrammeConnecteur] Fallback: similarite n-grams caracteres")
            return False
        try:
            self._fasttext_model = GensimFastText.load(FASTTEXT_MODEL_PATH)
            print(f"  [HologrammeConnecteur] FastText charge: "
                  f"{len(self._fasttext_model.wv)} mots")
            return True
        except Exception as e:
            print(f"  [HologrammeConnecteur] ERREUR chargement FastText: {e}")
            return False

    # =========================================================================
    # Vecteurs pre-entraines (cc.fr.300) pour bridge OOV
    # =========================================================================
    def _charger_vecteurs_pretrained(self):
        """Charge les vecteurs fastText pre-entraines (cc.fr.300) filtrés.

        Ces vecteurs sont telecharges et filtres par
        scripts/telecharger_vecteurs_pretrained.py. Ils ne couvrent que
        le vocabulaire etendu (2125 tokens) + termes medicaux/biotech.

        Les vecteurs sont normalises L2 pour permettre la similarite cosinus
        par simple produit scalaire.

        Returns:
            True si les vecteurs sont charges avec succes.
        """
        self._pretrained_words = []
        self._pretrained_vecs = np.array([], dtype=np.float32)
        self._pretrained_word_index = {}
        
        if not os.path.exists(PRETRAINED_VECS_FILE) or not os.path.exists(PRETRAINED_WORDS_FILE):
            print(f"  [HologrammeConnecteur] Vecteurs pre-entraines NON DISPONIBLES")
            print(f"  [HologrammeConnecteur] Lancer: python scripts/telecharger_vecteurs_pretrained.py")
            print(f"  [HologrammeConnecteur] Fallback: modele FastText local + n-grams")
            return False
        
        try:
            # Charger la liste des mots
            with open(PRETRAINED_WORDS_FILE, 'r', encoding='utf-8') as f:
                self._pretrained_words = json.load(f)
            
            # Charger les vecteurs normalises L2
            self._pretrained_vecs = np.load(PRETRAINED_VECS_FILE)
            
            # Creer l'index mot -> position
            self._pretrained_word_index = {
                w: i for i, w in enumerate(self._pretrained_words)
            }
            
            n_mots = len(self._pretrained_words)
            dim = self._pretrained_vecs.shape[1] if self._pretrained_vecs.ndim > 1 else 0
            
            print(f"  [HologrammeConnecteur] Vecteurs pre-entraines charges:")
            print(f"    {n_mots} mots, {dim} dimensions")
            print(f"    Source: cc.fr.300 (Common Crawl, Facebook)")
            return True
            
        except Exception as e:
            print(f"  [HologrammeConnecteur] ERREUR chargement vecteurs pre-entraines: {e}")
            self._pretrained_words = []
            self._pretrained_vecs = np.array([], dtype=np.float32)
            self._pretrained_word_index = {}
            return False

    def _bridge_oov_vectoriel(self, token_str: str,
                              top_k: int = TOP_K_EXPANSION_OOV) -> List[Tuple[str, float]]:
        """Trouve les tokens connus les plus proches d'un token OOV via similarite cosinus.

        Utilise les vecteurs pre-entraines (cc.fr.300) pour trouver, dans l'espace
        semantique continu, les voisins d'un token OOV qui sont presents dans la
        matrice de co-occurrence/PPMI.

        Mecanisme:
          token OOV (ex: 'infarctus') → vecteur 300d → cosine NN →
          {'coeur': 0.71, 'cardiaque': 0.68, 'vasculaire': 0.62} →
          ces tokens connus servent de "pont" vers la co-occurrence

        Args:
            token_str: Token OOV (chaine, ex: 'infarctus')
            top_k: Nombre maximum de ponts a retourner

        Returns:
            Liste de (token_str_connu, similarite_cosinus)
        """
        # Verifier si les vecteurs pre-entraines sont disponibles
        if len(self._pretrained_words) == 0 or self._pretrained_vecs.size == 0:
            return []
        
        # Verifier si le token OOV est dans les vecteurs pre-entraines
        idx = self._pretrained_word_index.get(token_str, -1)
        if idx < 0:
            # Le token peut etre absent des vecteurs pre-entraines.
            # On tente avec le modele FastText local si disponible.
            return []
        
        # Obtenir le vecteur du token OOV (deja normalise L2)
        query_vec = self._pretrained_vecs[idx]
        
        # Ensemble des tokens connus dans la co-occurrence/PPMI
        vocab_connu: Set[str] = set()
        if self._ppmi:
            for tid in self._ppmi.keys():
                w = self.tokenizer.i2w.get(tid, '')
                if w:
                    vocab_connu.add(w)
        for tid in self._cooccurrence.keys():
            w = self.tokenizer.i2w.get(tid, '')
            if w:
                vocab_connu.add(w)
        
        if not vocab_connu:
            return []
        
        # Produit scalaire avec tous les tokens connus (vecteurs normalises = cosine)
        scores: List[Tuple[str, float]] = []
        
        for connu in vocab_connu:
            c_idx = self._pretrained_word_index.get(connu, -1)
            if c_idx < 0 or c_idx == idx:
                continue
            
            # Cosine = produit scalaire (vecteurs normalises L2)
            cosine = float(query_vec @ self._pretrained_vecs[c_idx])
            
            # Appliquer un seuil minimum
            if cosine >= SEUIL_SIMILARITE_OOV:
                scores.append((connu, round(cosine, 4)))
        
        # Trier par similarite decroissante
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:top_k]

    def _embedding_similarity(self, t1_str: str, t2_str: str) -> float:
        """Calcule la similarite cosinus entre deux tokens via vecteurs pre-entraines.

        Utilise les vecteurs cc.fr.300 pour obtenir une similarite semantique
        independante du corpus local. Utile pour le scoring hybride.

        Args:
            t1_str: Premier token (chaine)
            t2_str: Second token (chaine)

        Returns:
            Similarite cosinus (0.0 a 1.0), ou 0.0 si non disponible
        """
        if (len(self._pretrained_words) == 0 or
                self._pretrained_vecs.size == 0):
            return 0.0

        idx1 = self._pretrained_word_index.get(t1_str, -1)
        idx2 = self._pretrained_word_index.get(t2_str, -1)
        if idx1 < 0 or idx2 < 0 or idx1 == idx2:
            return 0.0

        # Vecteurs deja normalises L2 → produit scalaire = cosine
        cosine = float(self._pretrained_vecs[idx1] @ self._pretrained_vecs[idx2])
        return max(0.0, min(1.0, cosine))

    def _expand_oov_token(self, token_id: int,
                          top_k: int = TOP_K_EXPANSION_OOV) -> List[Tuple[int, float]]:
        """Etend un token OOV vers des tokens semantiquement proches.
        
        Un token OOV est un token qui existe dans le vocabulaire etendu mais
        qui n'apparait dans aucun texte d'injection (freq=0). On cherche
        les tokens les plus similaires dans l'espace semantique continu
        (vecteurs pre-entraines cc.fr.300 ou FastText local) pour les
        utiliser comme proxies vers la co-occurrence.
        
        Strategie (3 niveaux):
          1. Bridge vectoriel (cc.fr.300 pre-entraine): cosine NN dans
             un espace semantique riche (300d, entraîne sur Common Crawl)
          2. FastText local: similarite via subword (si notre modele
             entraine sur 108 textes a des vecteurs pertinents)
          3. Fallback n-grams: Jaccard sur les trigrammes de caracteres
        
        Args:
            token_id: ID du token OOV a expandre
            top_k: Nombre maximum de tokens proxies a retourner
        
        Returns:
            Liste de (token_id_proxy, score_similarite)
        """
        token_str = self.tokenizer.i2w.get(token_id, '')
        if not token_str:
            return []
        
        # Ensemble des tokens disponibles dans la co-occurrence ou PPMI
        vocab_cooc: Set[int] = set()
        if self._ppmi:
            vocab_cooc.update(self._ppmi.keys())
        vocab_cooc.update(self._cooccurrence.keys())
        
        if not vocab_cooc:
            return []
        
        # === Methode 1: Bridge vectoriel (cc.fr.300 pre-entraine) ===
        if len(self._pretrained_words) > 0:
            bridge = self._bridge_oov_vectoriel(token_str, top_k=top_k)
            if bridge:
                result = []
                for mot_sim, score in bridge:
                    mot_id = self.tokenizer.w2i.get(mot_sim, -1)
                    if mot_id in vocab_cooc and mot_id >= 0:
                        result.append((mot_id, score))
                    if len(result) >= top_k:
                        break
                if result:
                    debug_str = ", ".join(
                        f"{self.tokenizer.i2w.get(t,'?')}({s:.3f})"
                        for t, s in result
                    )
                    print(f"    [BRIDGE] '{token_str}' -> {debug_str}")
                    return result
        
        # === Methode 2: FastText local ===
        if self._fasttext_model is not None:
            try:
                similar = self._fasttext_model.wv.most_similar(
                    token_str, topn=top_k * 3
                )
                result = []
                for mot_sim, score in similar:
                    if score < SEUIL_SIMILARITE_OOV:
                        continue
                    mot_id = self.tokenizer.w2i.get(mot_sim, -1)
                    if mot_id in vocab_cooc and mot_id >= 0:
                        result.append((mot_id, round(score, 4)))
                    if len(result) >= top_k:
                        break
                if result:
                    debug_str = ", ".join(
                        f"{self.tokenizer.i2w.get(t,'?')}({s:.3f})"
                        for t, s in result
                    )
                    print(f"    [FT] '{token_str}' -> {debug_str}")
                    return result
            except KeyError:
                pass
            except Exception:
                pass
        
        # === Methode 3: Fallback n-grams (Jaccard sur trigrammes) ===
        n = 3  # Trigrammes
        scores_ngram: List[Tuple[int, float]] = []
        
        for vid in vocab_cooc:
            v_str = self.tokenizer.i2w.get(vid, '')
            if not v_str or v_str == token_str:
                continue
            
            ngrams1 = set(token_str[i:i+n] for i in range(len(token_str) - n + 1))
            ngrams2 = set(v_str[i:i+n] for i in range(len(v_str) - n + 1))
            
            if not ngrams1 or not ngrams2:
                continue
            
            intersection = ngrams1 & ngrams2
            union = ngrams1 | ngrams2
            jaccard = len(intersection) / len(union)
            
            len_bonus = 1.0 / (1.0 + abs(len(token_str) - len(v_str)))
            score = jaccard * 0.7 + len_bonus * 0.3
            
            if score > SEUIL_SIMILARITE_OOV:
                scores_ngram.append((vid, round(score, 4)))
        
        scores_ngram.sort(key=lambda x: x[1], reverse=True)
        
        if scores_ngram:
            debug_str = ", ".join(
                f"{self.tokenizer.i2w.get(t,'?')}({s:.3f})"
                for t, s in scores_ngram[:top_k]
            )
            print(f"    [NGRAM] '{token_str}' -> {debug_str}")
        
        return scores_ngram[:top_k]

    def _initialiser_hologramme(self) -> bool:
        """Charge l'hologramme et cree le tokeniseur + lecteurs."""
        try:
            # Creer le monde holographique
            self.monde = HologrammeMonde(NX, NY)
            
            # Charger l'hologramme sauvegarde
            if os.path.exists(self._chemin):
                self.monde.H = np.load(self._chemin)
                # Remettre a zero le compteur (on ne connait pas le nombre exact)
                self.monde.n_experiences = 172872  # Valeur connue depuis progress.json
                self._energie_initiale = self.monde.energie()
                self._hologramme_original = self.monde.H.copy()  # Backup pour restauration
                statut = f"charge (E={self._energie_initiale:.0f})"
            else:
                self._hologramme_original = self.monde.H.copy()
                self._energie_initiale = self.monde.energie()
                statut = "nouvel hologramme (vide)"
            
            # Creer le tokeniseur (mode pi/6 avec vocabulaire etendu)
            self.tokenizer = TokeniseurOndes(VOCABULAIRE_ETENDU, use_pi_over_6=True)
            
            # Charger la matrice de co-occurrence pour le retrieval semantique
            # DOIT etre apres la creation du tokenizer (affiche les stopwords)
            self._cooccurrence, self._frequence = self._charger_cooccurrence(self.tokenizer)

            # Charger la matrice PPMI (bruit reduit par rapport a la co-occurrence)
            self._ppmi = self._charger_ppmi()

            # Charger le modele FastText pour l'expansion OOV
            self._charger_fasttext()

            # Charger les vecteurs pre-entraines (cc.fr.300) pour le bridge OOV
            self._charger_vecteurs_pretrained()

            # Les lecteurs sont crees dynamiquement a chaque resonner()
            self.n_lecteurs = N_LECTEURS

            self._initialise = True
            print(f"  [HologrammeConnecteur] Hologramme {statut}")
            print(f"  [HologrammeConnecteur] Vocabulaire: {self.tokenizer.vocab_size} tokens")
            print(f"  [HologrammeConnecteur] Lecteurs: {self.n_lecteurs}")
            return True
            
        except Exception as e:
            print(f"  [HologrammeConnecteur] ERREUR initialisation: {e}")
            self._initialise = False
            return False
    
    def est_charge(self) -> bool:
        """Verifie si l'hologramme est charge et operationnel."""
        return self._initialise
    
    def _lire_tous_tokens(self, batch_size: int = 500) -> np.ndarray:
        """
        Lit l'activation de TOUS les tokens du vocabulaire dans l'etat actuel
        de l'hologramme. Version vectorisee par batch.
        
        Au lieu d'appeler lire_onde() pour chaque token (boucle Python lente),
        on traite les tokens par batch de 500 avec du broadcasting numpy :
          onde_ref = exp(-1j * (kx * xx + ky * yy))  shape (B, nx, ny)
          corr     = sum(H * onde_ref)                shape (B,)
        
        Args:
            batch_size: Nombre de tokens traites simultanement (defaut: 500).
                        Memoire requise par batch: batch_size * nx * ny * 16 octets.
                        Pour 500*64*64*16 = 32 MB — tres raisonnable.
        
        Returns:
            np.ndarray shape (V,) - activation de chaque token du vocabulaire
        """
        V = self.tokenizer.vocab_size
        activations = np.zeros(V, dtype=np.float64)
        nx, ny = self.monde.nx, self.monde.ny
        
        # References utilisees par lire_onde (formule exacte)
        xx = self.monde.xx  # shape (nx, ny)
        yy = self.monde.yy  # shape (nx, ny)
        H  = self.monde.H   # shape (nx, ny) complexe
        
        # Acces direct aux tableaux numpy de kx, ky (evite les appels Python)
        kx_arr = self.tokenizer._kx  # shape (V,)
        ky_arr = self.tokenizer._ky  # shape (V,)
        
        for start in range(0, V, batch_size):
            end = min(start + batch_size, V)
            batch_kx = kx_arr[start:end]  # shape (B,)
            batch_ky = ky_arr[start:end]  # shape (B,)
            
            # Phase = -(kx*xx + ky*yy) en broadcasting :
            #   (B, 1, 1) * (1, nx, ny) -> (B, nx, ny)
            phase = (batch_kx[:, None, None] * xx[None, :, :] +
                     batch_ky[:, None, None] * yy[None, :, :])
            
            # Onde de reference = exp(-1j * phase) — formule exacte de lire_onde
            onde_ref = np.exp(-1j * phase)  # (B, nx, ny) complexe
            
            # Correlation = somme sur tout le plan holographique
            corr = np.sum(H[None, :, :] * onde_ref, axis=(1, 2))  # (B,) complexe
            
            # Activation normalisee par la surface
            activations[start:end] = np.abs(corr) / (nx * ny)
        
        return activations

    def resonner(self, requete: str, top_k: int = TOP_K_RESONANCE,
                 n_rep: int = N_REP_LECTURE) -> Dict:
        """
        Extrait les connaissances resonantes depuis l'hologramme
        et la matrice de co-occurrence.
        
        Processus (retrieval semantique PPMI + FastText) :
          1. Tokeniser la requete, filtrer les tokens speciaux et stopwords
          2. Phase 1 (PPMI) : Pour chaque token de la requete avec des donnees
             de co-occurrence, accumuler les scores PPMI (bruit reduit)
          3. Phase 2 (RAW IDF) : Fallback vers la co-occurrence brute ponderee
             IDF pour les tokens sans PPMI
          4. Phase 3 (FastText OOV) : Pour les tokens OOV (freq=0 dans les
             textes d'injection), trouver des proxies semantiques via FastText
             (ou similarite n-grams en fallback)
          5. Exclure les tokens de la requete et les tokens speciaux
          6. Retourner les top-K tokens
        
        Pourquoi PPMI + FastText ?
          - PPMI (Positive PMI) elimine naturellement les co-occurrences
            dues au hasard (stopwords), sans seuil arbitraire
          - FastText permet de gerer les tokens OOV comme 'infarctus',
            'hypertension' qui sont dans le vocabulaire mais jamais vus
            dans les textes d'injection
        
        Args:
            requete: Le prompt utilisateur
            top_k: Nombre de tokens resonants a retourner
            n_rep: Ignore (conserve pour compatibilite API)
        
        Returns:
            Dict avec:
                - top_tokens: Liste de (token_string, score) tries par pertinence
                - contexte: Phrases formatees a injecter dans la generation
                - mode_retrieval: "ppmi+fasttext", "cooccurrence" ou "delta_fourier"
                - energie_hologramme: Energie totale de l'hologramme
                - n_experiences: Nombre d'experiences dans l'hologramme
                - temps_ms: Temps de traitement
        """
        if not self._initialise:
            return self._resonance_vide(requete, "Hologramme non initialise")
        
        t0 = time.time()
        
        try:
            # === ETAPE 1 : Tokeniser la requete ===
            prompt_tokens = self.tokenizer.tokeniser(requete)
            
            # Filtrer les tokens speciaux
            tokens_speciaux = {0, 1, 2, 3}  # PAD, UNK, BOS, EOS
            unk_id = self.tokenizer.w2i.get('<UNK>', 1)
            prompt_tokens_filtres = [
                t for t in prompt_tokens
                if t not in tokens_speciaux and t != unk_id
            ]
            
            # === ETAPE 2 : Retrieval semantique par co-occurrence ponderee IDF ===
            if self._cooccurrence:
                mode_retrieval = "cooccurrence"
                scores: Dict[int, float] = defaultdict(float)
                
                # Calculer le nombre total de textes d'injection
                n_textes = max(self._frequence.values()) if self._frequence else 108
                seuil_stopword = max(1, int(n_textes * SEUIL_STOPWORD_RATIO))
                
                # =============================================================
                # PHASE 1 : Scoring PPMI avec scoring hybride (PPMI + embedding)
                # =============================================================
                # La PPMI penalise naturellement les stopwords :
                #   PMI(de, la) = log2(108*99/(104*99)) = 0.054  → quasi nul
                #   PMI(ghana, empire) = log2(108*4/(5*8)) = 3.43  → fort
                #
                # Scoring hybride (SCORE_ALPHA_PPMI = 0.80) :
                #   score = alpha * PPMI + (1-alpha) * similarite_embedding
                # Le terme embedding (via cc.fr.300) penalise les co-occurrences
                # fortuites et renforce les paires semantiquement liees.
                q_str_map: Dict[int, str] = {}  # Cache pour les chaines de tokens
                for q_tok in prompt_tokens_filtres:
                    freq_q = self._frequence.get(q_tok, 1)
                    if freq_q > seuil_stopword:
                        continue
                    
                    # Priorite 1 : PPMI avec hybridation embedding
                    if self._ppmi and q_tok in self._ppmi:
                        q_str = q_str_map.get(q_tok)
                        if q_str is None:
                            q_str = self.tokenizer.i2w.get(q_tok, '')
                            q_str_map[q_tok] = q_str
                        
                        for r_tok, ppmi_val in self._ppmi[q_tok].items():
                            if SCORE_ALPHA_PPMI < 1.0 and q_str:
                                # Scoring hybride : embed_sim vient renforcer
                                # ou affaiblir le score PPMI (coherence semantique)
                                r_str = self.tokenizer.i2w.get(r_tok, '')
                                embed_sim = self._embedding_similarity(q_str, r_str) if r_str else 0.0
                                # PPMI domine, embedding ajuste a la marge
                                hybrid = (SCORE_ALPHA_PPMI * ppmi_val +
                                          (1.0 - SCORE_ALPHA_PPMI) * embed_sim * 5.0)
                                scores[r_tok] += hybrid
                            else:
                                scores[r_tok] += ppmi_val
                        continue
                    
                    # Priorite 2 : Co-occurrence brute avec IDF (fallback)
                    if q_tok in self._cooccurrence:
                        q_str = q_str_map.get(q_tok)
                        if q_str is None:
                            q_str = self.tokenizer.i2w.get(q_tok, '')
                            q_str_map[q_tok] = q_str
                        
                        for r_tok, count in self._cooccurrence[q_tok].items():
                            freq_r = self._frequence.get(r_tok, 1)
                            idf_weight = 1.0 / (1.0 + math.log1p(freq_r) ** 2)
                            
                            if SCORE_ALPHA_PPMI < 1.0 and q_str:
                                r_str = self.tokenizer.i2w.get(r_tok, '')
                                embed_sim = self._embedding_similarity(q_str, r_str) if r_str else 0.0
                                hybrid = (SCORE_ALPHA_PPMI * count * idf_weight +
                                          (1.0 - SCORE_ALPHA_PPMI) * embed_sim * 3.0)
                                scores[r_tok] += hybrid
                            else:
                                scores[r_tok] += count * idf_weight
                
                # =============================================================
                # PHASE 2 : Expansion OOV via Bridge vectoriel / FastText / n-grams
                # =============================================================
                # Les tokens OOV (freq=0) comme 'infarctus', 'hypertension'
                # n'ont aucune entree dans la co-occurrence. On utilise
                # le bridge vectoriel (cc.fr.300), FastText local, ou
                # fallback n-grams pour trouver des proxies semantiques.
                oov_expanded = False
                for q_tok in prompt_tokens_filtres:
                    freq_q = self._frequence.get(q_tok, 1)
                    if freq_q > seuil_stopword:
                        continue
                    
                    # Verifier si ce token a deja des donnees de co-occurrence
                    a_donnees = (q_tok in self._cooccurrence)
                    if self._ppmi:
                        a_donnees = a_donnees or (q_tok in self._ppmi)
                    if a_donnees:
                        continue
                    
                    # Token OOV : utiliser Bridge / FastText / n-grams
                    expanded = self._expand_oov_token(q_tok, top_k=TOP_K_EXPANSION_OOV)
                    if not expanded:
                        continue
                    
                    oov_expanded = True
                    q_str = q_str_map.get(q_tok)
                    if q_str is None:
                        q_str = self.tokenizer.i2w.get(q_tok, '')
                        q_str_map[q_tok] = q_str
                    
                    for proxy_tok, similarity in expanded:
                        if self._ppmi and proxy_tok in self._ppmi:
                            for r_tok, ppmi_val in self._ppmi[proxy_tok].items():
                                # Pour OOV, le scoring est deja pondere par similarity
                                # (cosine du bridge ou similarite FastText/n-gram)
                                if SCORE_ALPHA_PPMI < 1.0 and q_str:
                                    r_str = self.tokenizer.i2w.get(r_tok, '')
                                    embed_sim = self._embedding_similarity(q_str, r_str) if r_str else 0.0
                                    hybrid = (SCORE_ALPHA_PPMI * ppmi_val * similarity +
                                              (1.0 - SCORE_ALPHA_PPMI) * embed_sim * 3.0)
                                    scores[r_tok] += hybrid
                                else:
                                    scores[r_tok] += ppmi_val * similarity
                        elif proxy_tok in self._cooccurrence:
                            for r_tok, count in self._cooccurrence[proxy_tok].items():
                                freq_r = self._frequence.get(r_tok, 1)
                                idf_weight = 1.0 / (1.0 + math.log1p(freq_r) ** 2)
                                
                                if SCORE_ALPHA_PPMI < 1.0 and q_str:
                                    r_str = self.tokenizer.i2w.get(r_tok, '')
                                    embed_sim = self._embedding_similarity(q_str, r_str) if r_str else 0.0
                                    hybrid = (SCORE_ALPHA_PPMI * count * idf_weight * similarity +
                                              (1.0 - SCORE_ALPHA_PPMI) * embed_sim * 3.0)
                                    scores[r_tok] += hybrid
                                else:
                                    scores[r_tok] += count * idf_weight * similarity
                
                if oov_expanded:
                    mode_retrieval = "ppmi+fasttext"
                
                # Retirer les tokens de la requete eux-memes
                for q_tok in prompt_tokens_filtres:
                    scores.pop(q_tok, None)
                
                # Trier par score decroissant
                top_indices = sorted(scores.keys(),
                                     key=lambda t: scores[t],
                                     reverse=True)[:top_k]
                
                # Construire la liste des top tokens
                top_tokens = []
                for tid in top_indices:
                    token_str = self.tokenizer.i2w.get(tid, '<UNK>')
                    top_tokens.append((token_str, round(scores[tid], 4)))
                
                # Informations additionnelles pour le diagnostic
                tokens_utilises = [self.tokenizer.i2w.get(t, f'<{t}>')
                                   for t in prompt_tokens_filtres
                                   if self._frequence.get(t, 1) <= seuil_stopword]
                if tokens_utilises:
                    print(f"  [{mode_retrieval}] Requete -> {tokens_utilises}")
                energie_hologramme = self.monde.energie()
                
            else:
                # === FALLBACK : Delta Fourier (si pas de co-occurrence) ===
                mode_retrieval = "delta_fourier"
                
                # Mesurer l'activation de base de tous les tokens
                energie_avant = self.monde.energie()
                activations_base = self._lire_tous_tokens()
                
                # Enregistrer la requete dans l'hologramme
                for idx in prompt_tokens:
                    kx, ky = self.tokenizer.vecteur_onde(idx)
                    self.monde.enregistrer_onde(kx, ky, 0.3)
                energie_apres = self.monde.energie()
                
                # Mesurer les activations apres enregistrement
                activations_apres = self._lire_tous_tokens()
                
                # Restaurer l'hologramme
                for idx in prompt_tokens:
                    kx, ky = self.tokenizer.vecteur_onde(idx)
                    onde = np.exp(1j * (kx * self.monde.xx + ky * self.monde.yy))
                    self.monde.H -= 0.3 * onde
                
                # Delta normalise
                EPSILON = 1e-3
                delta_brut = activations_apres - activations_base
                delta_norm = delta_brut / (activations_base + EPSILON)
                MASQUE_BASELINE_MIN = activations_base > 1.0
                score = np.where(MASQUE_BASELINE_MIN, delta_norm, -1.0)
                
                tokens_requete = set(prompt_tokens)
                indices = np.argsort(score)[::-1]
                
                top_tokens = []
                for idx in indices:
                    if len(top_tokens) >= top_k:
                        break
                    tid = int(idx)
                    if tid in tokens_speciaux or tid in tokens_requete:
                        continue
                    token_str = self.tokenizer.i2w.get(tid, '<UNK>')
                    score_val = float(score[tid])
                    if score_val < SEUIL_ACTIVATION_MIN:
                        continue
                    top_tokens.append((token_str, round(score_val, 6)))
                
                energie_hologramme = energie_apres
            
            # === ETAPE 3 : Formater le contexte ===
            contexte = self._formater_contexte(top_tokens, requete)
            
            dt = (time.time() - t0) * 1000
            
            # Stats
            self._stats["n_resonances"] += 1
            self._stats["n_tokens_extraits"] += len(top_tokens)
            self._stats["temps_total_ms"] += dt
            
            return {
                "top_tokens": top_tokens,
                "contexte": contexte,
                "mode_retrieval": mode_retrieval,
                "n_requete_tokens": len(prompt_tokens_filtres),
                "energie_hologramme": round(energie_hologramme, 1),
                "n_experiences": self.monde.n_experiences,
                "temps_ms": round(dt, 1),
                "n_lecteurs": self.n_lecteurs,
                "succes": True,
            }
            
        except Exception as e:
            dt = (time.time() - t0) * 1000
            self._stats["erreurs"] += 1
            return self._resonance_vide(requete, str(e), dt)
    
    def _formater_contexte(self, top_tokens: List[Tuple[str, float]],
                           requete: str) -> str:
        """
        Transforme les tokens resonants en phrases contextuelles.
        
        Format : 
          "Connaissances disponibles : mot1, mot2, mot3... 
           L'hologramme contient des donnees sur mot1, mot2..."
        """
        if not top_tokens:
            return ""
        
        mots = [t[0] for t in top_tokens]
        
        # Construire 2-3 phrases informatives
        phrases = []
        
        # Phrase 1 : Introduction des connaissances
        if len(mots) >= 1:
            liste_mots = ", ".join(mots[:5])
            phrases.append(
                f"Connaissances disponibles dans la base holographique : {liste_mots}."
            )
        
        # Phrase 2 : Domaine principal
        if len(mots) >= 3:
            domaine = ", ".join(mots[:3])
            phrases.append(
                f"Domaines conceptuels identifies : {domaine}."
            )
        
        # Phrase 3 : Contexte supplementaire (si assez de tokens)
        if len(mots) >= 6:
            supplement = ", ".join(mots[3:7])
            phrases.append(
                f"Elements contextuels associes : {supplement}."
            )
        
        return " ".join(phrases)
    
    def _resonance_vide(self, requete: str, raison: str = "",
                        temps_ms: float = 0.0) -> Dict:
        """Retourne un resultat vide en cas d'erreur."""
        return {
            "top_tokens": [],
            "contexte": "",
            "activations": [],
            "energie_avant": 0.0,
            "energie_apres": 0.0,
            "n_experiences": 0,
            "temps_ms": round(temps_ms, 1),
            "n_lecteurs": self.n_lecteurs,
            "n_rep": 0,
            "succes": False,
            "erreur": raison,
        }
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques du connecteur."""
        stats = dict(self._stats)
        stats["hologramme_charge"] = self._initialise
        if self._initialise:
            stats["energie_hologramme"] = round(self.monde.energie(), 1)
            stats["n_experiences"] = self.monde.n_experiences
            stats["taille_hologramme"] = f"{self.monde.nx}x{self.monde.ny}"
            stats["vocab_size"] = self.tokenizer.vocab_size
        return stats


# =========================================================================
# TEST UNITE
# =========================================================================

def test_connecteur():
    """Test du connecteur holographique avec la methode delta."""
    print("=" * 70)
    print("TEST : HologrammeConnecteur (delta activation)")
    print("=" * 70)
    
    connecteur = HologrammeConnecteur()
    
    if not connecteur.est_charge():
        print("  [!] Hologramme non charge - tests limites")
        print("  [OK] Fallback fonctionne")
        return
    
    # Test 1 : Resonance simple
    print("\n[Test 1] Resonance sur requete simple...")
    resultat = connecteur.resonner("Bonjour, comment ca va ?", top_k=5)
    print(f"  Tokens resonants (delta): {resultat['top_tokens']}")
    print(f"  Contexte: {resultat['contexte'][:100]}...")
    print(f"  Temps: {resultat['temps_ms']:.0f}ms")
    assert resultat["succes"], "La resonance devrait reussir"
    print("  [OK]")
    
    # Test 2 : Contexte historique
    print("\n[Test 2] Resonance sur sujet historique...")
    resultat2 = connecteur.resonner("Parle-moi de l'empire du Ghana", top_k=8)
    print(f"  Tokens resonants (delta): {resultat2['top_tokens']}")
    print(f"  Contexte: {resultat2['contexte'][:150]}...")
    print(f"  Temps: {resultat2['temps_ms']:.0f}ms")
    print("  [OK]")
    
    # Test 3 : Sujet scientifique
    print("\n[Test 3] Resonance sur sujet scientifique...")
    resultat3 = connecteur.resonner("Explique la theorie de la relativite", top_k=8)
    print(f"  Tokens resonants (delta): {resultat3['top_tokens']}")
    print(f"  Contexte: {resultat3['contexte'][:150]}...")
    print("  [OK]")
    
    # Test 4 : Les 3 requetes doivent produire des resultats DIFFERENTS
    print("\n[Test 4] Verification de diversite des resonances...")
    tokens1 = set(t[0] for t in resultat['top_tokens'])
    tokens2 = set(t[0] for t in resultat2['top_tokens'])
    tokens3 = set(t[0] for t in resultat3['top_tokens'])
    inter12 = tokens1 & tokens2
    inter13 = tokens1 & tokens3
    inter23 = tokens2 & tokens3
    print(f"  Tokens requete 1: {tokens1}")
    print(f"  Tokens requete 2: {tokens2}")
    print(f"  Tokens requete 3: {tokens3}")
    print(f"  Intersection 1<->2: {len(inter12)} tokens communs")
    print(f"  Intersection 1<->3: {len(inter13)} tokens communs")
    print(f"  Intersection 2<->3: {len(inter23)} tokens communs")
    if len(inter12) < len(tokens1) and len(inter23) < len(tokens2):
        print("  [OK] Les resonances sont differentes selon la requete")
    else:
        print("  [ATTENTION] Les resonances sont identiques (probleme de diversite)")
    
    # Test 5 : Stats
    print("\n[Test 5] Statistiques...")
    stats = connecteur.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print("  [OK]")
    
    print(f"\n{'='*70}")
    print("TEST HologrammeConnecteur TERMINE")
    print(f"{'='*70}")


if __name__ == "__main__":
    test_connecteur()
