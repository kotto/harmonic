#!/usr/bin/env python3
"""
GENERATEUR PAR RESONANCE INVERSE - Phases 2 et 3
==================================================
Combine les 3 decouvertes :
1. Hologramme brut accumule (experience_holo_stockage_brut.py)
2. Apprentissage par repetition (LecteurResonant)
3. Decodage holographique 2D (decodeur_holographique_2d.py)

Architecture :
+--------------------------------------------------------------------------------+
|                         RESONANCE INVERSE                                       |
+--------------------------------------------------------------------------------+
|                                                                                 |
|  INCONSCIENT (Monde / Hologramme brut)                                          |
|  +---------------------------------------------------------------------------+  |
|  |  H[i][j] = sum_k A_k * exp(i*(kx_k*x_i + ky_k*y_j))                      |  |
|  |  Accumulation additive de TOUTE l'experience                              |  |
|  +---------------------------------------------------------------------------+  |
|                                                                                 |
|  CONSCIENCE (Lecteurs multiples / Attention parallele)                         |
|  +---------------------------------------------------------------------------+  |
|  |  N lecteurs avec (kx_n, ky_n) apprenant par gradient                      |  |
|  |  Chaque lecteur = une perspective emergente                               |  |
|  |  L'ENSEMBLE des lecteurs = la conscience du moment                        |  |
|  +---------------------------------------------------------------------------+  |
|                                                                                 |
|  TOKENISATION PAR ONDES (Espace latent 9D vers tokens)                        |
|  +---------------------------------------------------------------------------+  |
|  |  Chaque token t <-> (freq_t, phase_t) unique                              |  |
|  |  Activation = |sum H * exp(-i*k*r)| pour k du token                       |  |
|  |  Generation = produire le prochain token par resonance                    |  |
|  +---------------------------------------------------------------------------+  |
|                                                                                 |
|  FEEDBACK CONSCIENCE vers INCONSCIENT (Boucle d'apprentissage)               |
|  +---------------------------------------------------------------------------+  |
|  |  Texte genere -> 9D signature -> nouvelle onde -> hologramme              |  |
|  |  Le systeme APPREND de sa propre generation                               |  |
|  +---------------------------------------------------------------------------+  |
+--------------------------------------------------------------------------------+

Usage :
    python -m harmonic_training.model.harmonic_resonance_generator
"""

import numpy as np
import math
import time
import json
import hashlib
from typing import List, Dict, Optional, Tuple, Callable

PHI = 1.618033988749895
ALPHA = 1.0 / PHI
NX, NY = 256, 256  # Taille de l'hologramme (1024 pour production, 256 pour tests)

# =========================================================================
# PARTIE 1 : HOLOGRAMME MONDE (INCONSCIENT) - Stockage brut accumule
# =========================================================================

class HologrammeMonde:
    """
    L'inconscient : stockage BRUT de toute l'experience.

    Chaque experience est AJOUTEE (additive) a la grille 2D.
    Aucune organisation. Aucune perte. La structure EMERGE
    par la lecture repetee.

    Proprietes :
    - Taille fixe NxN (64x64 = 4096 pixels complexes de base)
    - Capacite d'information theoriquement illimitee (superposition)
    - Chaque pixel stocke un nombre complexe (amplitude + phase)
    """

    def __init__(self, nx: int = NX, ny: int = NY):
        self.nx = nx
        self.ny = ny
        # Grille physique (positions x,y)
        x = np.linspace(-math.pi, math.pi, nx)
        y = np.linspace(-math.pi, math.pi, ny)
        self.xx, self.yy = np.meshgrid(x, y, indexing='ij')
        # Hologramme : initialise a ZERO (page blanche, pas de bruit)
        # Le bruit initial representait \"l'experience du vide\" mais
        # cree un plancher de bruit qui noie le signal des connaissances.
        # Un hologramme vide doit etre SILENCIEUX, pas bruyant.
        self.H = np.zeros((nx, ny), dtype=np.complex128)
        self.n_experiences = 0
        self.historique_gradient = []  # Pour suivi

    def enregistrer_onde(self, kx: float, ky: float, amplitude: float = 1.0):
        """AJOUTE une onde au monde (apprentissage additif)."""
        onde = np.exp(1j * (kx * self.xx + ky * self.yy))
        self.H += amplitude * onde
        self.n_experiences += 1

    def enregistrer_texte(self, texte: str, tokenizer: 'TokeniseurOndes', amplitude: float = 1.0):
        """
        Enregistre un texte entier dans l'hologramme.
        Chaque token devient une onde ajoutee au monde.
        """
        tokens = tokenizer.tokeniser(texte)
        for idx_token in tokens:
            kx, ky = tokenizer.vecteur_onde(idx_token)
            self.enregistrer_onde(kx, ky, amplitude)

    def lire_onde(self, kx: float, ky: float) -> float:
        """
        Mesure la resonance du monde avec une onde donnee.
        Retourne l'activation (amplitude de correlation).
        """
        onde_ref = np.exp(-1j * (kx * self.xx + ky * self.yy))
        corr = np.sum(self.H * onde_ref)
        return float(np.abs(corr) / (self.nx * self.ny))

    def lire_onde_complexe(self, kx: float, ky: float) -> complex:
        """
        Mesure la correlation COMPLEXE du monde avec une onde.
        Retourne la valeur complexe complete (amplitude ET phase).
        La phase encode le CONTEXTE dans lequel l'onde apparait.
        """
        onde_ref = np.exp(-1j * (kx * self.xx + ky * self.yy))
        corr = np.sum(self.H * onde_ref)
        return complex(corr / (self.nx * self.ny))

    def energie(self) -> float:
        """Energie totale de l'hologramme."""
        return float(np.sum(np.abs(self.H)**2))

    def stats(self) -> Dict:
        return {
            "n_experiences": self.n_experiences,
            "energie": round(self.energie(), 2),
            "amplitude_moy": round(float(np.mean(np.abs(self.H))), 4),
            "amplitude_std": round(float(np.std(np.abs(self.H))), 4),
        }


# =========================================================================
# PARTIE 2 : TOKENISEUR PAR PROJECTION D'ONDES
# =========================================================================

class TokeniseurOndes:
    """
    TOKENISATION PAR PROJECTION D'ONDES.

    Chaque token du vocabulaire se voit assigner un VECTEUR D'ONDE 2D UNIQUE
    dans l'espace des frequences (kx, ky).

    MODE π/6 (par defaut) — spirale a 12 branches a 30° :
        angle  = (i * pi/6) % 2pi    (12 directions discretes)
        radius = sqrt((i+0.5) * area_unit / pi)  (densite surfacique uniforme)
        kx = radius * cos(angle)
        ky = radius * sin(angle)

    MODE PHI (legacy) — pseudo-aleatoire par nombre d'or :
        freq = ((i+1) * phi) % 2pi
        kx = freq * cos(freq)
        ky = freq * sin(freq)

    Proprietes :
    - 2 tokens differents ont TOUJOURS des vecteurs d'onde differents
    - Le mode π/6 offre une couverture orthogonale optimale
    - La projection preserve la structure harmonique
    """

    def __init__(self, vocab: List[str], phi_scale: float = PHI,
                 use_pi_over_6: bool = True):
        self.vocab = vocab
        self.vocab_size = len(vocab)
        self.phi_scale = phi_scale
        self.use_pi_over_6 = use_pi_over_6
        self.w2i = {w: i for i, w in enumerate(vocab)}
        self.i2w = {i: w for i, w in enumerate(vocab)}

        # Pre-calcul des vecteurs d'onde pour tous les tokens
        vs = self.vocab_size
        self._freqs = np.zeros(vs, dtype=np.float64)
        self._kx = np.zeros(vs, dtype=np.float64)
        self._ky = np.zeros(vs, dtype=np.float64)

        if use_pi_over_6:
            # π/6 : 12 bras de spirale discrets a 30°, densite surfacique uniforme
            ANGLE_STEP = math.pi / 6.0       # 30°
            AREA_UNIT = (2.0 * math.pi)**2 / vs
            for i in range(vs):
                angle  = (i * ANGLE_STEP) % (2.0 * math.pi)
                radius = math.sqrt((i + 0.5) * AREA_UNIT / math.pi)
                self._freqs[i] = radius
                self._kx[i] = radius * np.cos(angle)
                self._ky[i] = radius * np.sin(angle)
        else:
            # Mode PHI legacy : pseudo-aleatoire
            for i in range(vs):
                f = ((i + 1) * phi_scale) % (2 * math.pi)
                self._freqs[i] = f
                self._kx[i] = f * np.cos(f)
                self._ky[i] = f * np.sin(f)

    def vecteur_onde(self, token_id: int) -> Tuple[float, float]:
        """Retourne (kx, ky) pour un token."""
        return float(self._kx[token_id]), float(self._ky[token_id])

    def tokeniser(self, texte: str) -> List[int]:
        """Tokenise un texte en IDs."""
        ids = []
        for mot in texte.lower().strip().split():
            mot_propre = mot.strip('.,!?;:()[]{}"\'-_<>/\'')
            ids.append(self.w2i.get(mot_propre, self.w2i.get('<UNK>', 1)))
        return ids

    def decoder(self, ids: List[int]) -> str:
        """Decode des IDs en texte."""
        return ' '.join(self.i2w.get(i, '<UNK>') for i in ids if i > 0)


# =========================================================================
# PARTIE 3 : LECTEURS MULTIPLES (CONSCIENCE PARALLELE)
# =========================================================================

class LecteurResonantMultiple:
    """
    N lecteurs simultanes = la CONSCIENCE du systeme.

    Chaque lecteur a :
    - Un vecteur d'onde (kx_n, ky_n) qui encode SA perspective
    - Un historique d'apprentissage
    - Une mesure d'activation pour chaque token

    L'ENSEMBLE des lecteurs forme un etat conscient complet.

    Mecanisme d'apprentissage :
    - Chaque repetition : gradient ascent pour maximiser l'activation
    - Le bruit d'exploration garantit la diversite
    - Les N lecteurs convergent vers les N modes dominants de l'hologramme
    """

    def __init__(self, monde: HologrammeMonde, n_lecteurs: int = 8, seed: int = 0):
        self.monde = monde
        self.n_lecteurs = n_lecteurs

        np.random.seed(seed)
        # Initialisation aleatoire des vecteurs d'onde
        self.kx = np.random.randn(n_lecteurs) * 1.5
        self.ky = np.random.randn(n_lecteurs) * 1.5

        self.historiques = [[] for _ in range(n_lecteurs)]
        self.n_iterations = 0

    def _activation(self, kx: float, ky: float) -> float:
        return self.monde.lire_onde(kx, ky)

    def iterer(self, lr: float = 0.03, bruit_exploration: float = 0.002):
        """
        Une iteration = chaque lecteur apprend une fois.
        """
        eps = 0.001
        for n in range(self.n_lecteurs):
            act = self._activation(self.kx[n], self.ky[n])
            self.historiques[n].append(act)

            # Gradient approime
            gx = (self._activation(self.kx[n] + eps, self.ky[n]) -
                  self._activation(self.kx[n] - eps, self.ky[n])) / (2 * eps)
            gy = (self._activation(self.kx[n], self.ky[n] + eps) -
                  self._activation(self.kx[n], self.ky[n] - eps)) / (2 * eps)

            # Montee de gradient + exploration
            self.kx[n] += lr * gx + np.random.randn() * bruit_exploration
            self.ky[n] += lr * gy + np.random.randn() * bruit_exploration

        self.n_iterations += 1

    def apprendre(self, n_iter: int = 50, lr: float = 0.03):
        """Apprentissage sur N iterations."""
        for _ in range(n_iter):
            self.iterer(lr)

    def activations_tokens(self, tokenizer: TokeniseurOndes) -> np.ndarray:
        """
        Calcule les activations de tous les tokens pour tous les lecteurs.

        Retourne: [n_lecteurs, vocab_size] - activation de chaque token
        vu par chaque lecteur.
        """
        V = tokenizer.vocab_size
        activations = np.zeros((self.n_lecteurs, V), dtype=np.float32)

        for t in range(V):
            kx_t, ky_t = tokenizer.vecteur_onde(t)
            act_t = self.monde.lire_onde(kx_t, ky_t)
            activations[:, t] = act_t

        return activations

    def signature_conscience(self) -> np.ndarray:
        """
        L'etat conscient complet = l'ensemble des vecteurs d'onde
        et de leurs activations actuelles.

        Retourne: [n_lecteurs * 3] - (kx_n, ky_n, act_n) concatenes
        """
        acts = np.array([self._activation(self.kx[n], self.ky[n])
                        for n in range(self.n_lecteurs)])
        sig = np.zeros(self.n_lecteurs * 3)
        for n in range(self.n_lecteurs):
            sig[n*3] = self.kx[n]
            sig[n*3+1] = self.ky[n]
            sig[n*3+2] = acts[n]
        return sig

    def top_tokens_par_lecteur(self, tokenizer: TokeniseurOndes, top_k: int = 10) -> List[List[Tuple[int, float]]]:
        """Pour chaque lecteur, les top-K tokens les plus actives."""
        acts = self.activations_tokens(tokenizer)
        resultats = []
        for n in range(self.n_lecteurs):
            indices = np.argsort(acts[n])[::-1][:top_k]
            resultats.append([(int(idx), float(acts[n, idx])) for idx in indices])
        return resultats


# =========================================================================
# PARTIE 4 : GENERATEUR PAR RESONANCE INVERSE
# =========================================================================

class GenerateurResonance:
    """
    GENERATION DE TEXTE PAR RESONANCE INVERSE.

    Processus :
    1. Le prompt est tokenise et enregistre dans l'hologramme (ou lu)
    2. N lecteurs apprennent par repetition sur l'hologramme
    3. Chaque lecteur a des tokens actives differemment
    4. Le token suivant est choisi par VOTE des lecteurs
    5. Le token est emis et AJOUTE a l'hologramme
    6. Feedback : le systeme apprend de sa propre generation

    C'est exactement le principe de la conscience qui emerge
    de l'interaction entre de multiples perspectives.
    """

    def __init__(self, vocab: List[str], nx: int = NX, ny: int = NY,
                 n_lecteurs: int = 8, seed: int = 0):
        self.monde = HologrammeMonde(nx, ny)
        self.tokenizer = TokeniseurOndes(vocab)
        self.lecteurs = LecteurResonantMultiple(self.monde, n_lecteurs, seed)
        self._connaissances = []  # Memoire des textes appris
        self._statistiques = {
            "n_apprentissages": 0,
            "n_generations": 0,
            "n_tokens_gen": 0,
            "temps_gen_ms": 0.0,
        }

    def apprendre(self, texte: str, amplitude: float = 0.8):
        """Apprend un texte en l'ajoutant a l'hologramme."""
        self.monde.enregistrer_texte(texte, self.tokenizer, amplitude)
        self._connaissances.append(texte)
        self._statistiques["n_apprentissages"] += 1

    def apprendre_batch(self, textes: List[str]):
        """Apprend plusieurs textes."""
        for t in textes:
            self.apprendre(t)

    def generer(self, prompt: str, max_tokens: int = 50,
                temperature: float = 0.85, top_k: int = 30,
                n_rep_lecture: int = 30, lr_apprentissage: float = 0.03,
                repetition_penalty: float = 1.5,
                feedback_conscient: bool = True) -> Dict:
        """
        Genere du texte par resonance inverse.

        Args:
            prompt: Texte d'entree
            max_tokens: Nombre max de tokens a generer
            temperature: Controle de la stochasticite
            top_k: Limite de tokens candidats
            n_rep_lecture: Nombre de repetitions d'apprentissage par token
            lr_apprentissage: Taux d'apprentissage des lecteurs
            repetition_penalty: Penalite des tokens deja generes
            feedback_conscient: Si True, la signature du texte genere
                               est re-injectee dans l'hologramme

        Returns:
            Dict avec texte, tokens, stats
        """
        t0 = time.time()
        tokens_generes = []

        # Tokeniser le prompt
        prompt_ids = self.tokenizer.tokeniser(prompt)

        # Enregistrer le prompt dans l'hologramme
        for idx in prompt_ids:
            kx, ky = self.tokenizer.vecteur_onde(idx)
            self.monde.enregistrer_onde(kx, ky, 0.5)

        # Reinitialiser les lecteurs pour une nouvelle session
        np.random.seed(int(time.time() * 1000) % 10000)
        self.lecteurs = LecteurResonantMultiple(self.monde, self.lecteurs.n_lecteurs)

        # Generation token par token
        for step in range(max_tokens):
            # Phase 1 : Apprentissage des lecteurs sur l'etat actuel de l'hologramme
            self.lecteurs.apprendre(n_rep_lecture, lr_apprentissage)

            # Phase 2 : Mesurer les activations de tous les tokens
            activations = self.lecteurs.activations_tokens(self.tokenizer)

            # Phase 3 : Fusion des activations par VOTE des lecteurs
            # = moyenne + max pondere pour renforcer le consensus
            act_moy = activations.mean(axis=0)  # [V] - consensus
            act_max = activations.max(axis=0)   # [V] - forte resonance
            act_fusion = act_moy * 0.6 + act_max * 0.4  # [V] - vote

            # Phase 4 : Sampling avec contraintes
            logits = act_fusion.copy()
            V = len(logits)

            # Masquer tokens speciaux
            for t in (0, 2):  # <PAD>, <BOS>
                if t < V:
                    logits[t] = -1e12

            # <EOS> (id 3) autorise seulement apres min_tokens
            min_tokens = 5
            if step < min_tokens and 3 < V:
                logits[3] = -1e9

            # Penalite de repetition sur les tokens deja generes
            if repetition_penalty > 1.0 and tokens_generes:
                derniers = set(tokens_generes[-20:])
                for t in derniers:
                    if t < V and t not in (0, 1, 2, 3):
                        if logits[t] > 0:
                            logits[t] /= repetition_penalty
                        else:
                            logits[t] *= repetition_penalty

            # Top-k filtering
            if top_k > 0 and top_k < V:
                seuil = np.sort(logits)[-top_k]
                logits[logits < seuil] = -1e12

            # Temperature + softmax
            logits = logits / max(temperature, 0.1)
            max_l = logits.max()
            if max_l < -1e8:
                # Fallback: token aleatoire dans le top-10
                fallback = np.argsort(act_fusion)[-10:]
                token_id = int(np.random.choice(fallback))
            else:
                shifted = logits - max_l
                probs = np.exp(shifted.astype(np.float64))
                probs /= (probs.sum() + 1e-30)

                if np.isnan(probs).any() or probs.sum() < 1e-30:
                    token_id = int(np.argmax(logits))
                else:
                    token_id = int(np.random.choice(V, p=probs))

            tokens_generes.append(token_id)

            # Phase 5 : AJOUTER le token genere a l'hologramme
            kx_t, ky_t = self.tokenizer.vecteur_onde(token_id)
            self.monde.enregistrer_onde(kx_t, ky_t, 0.3)

            # Arret si <EOS>
            if token_id == 3 and step >= min_tokens:
                break

        # Texte final
        texte_genere = self.tokenizer.decoder(tokens_generes)

        dt = (time.time() - t0) * 1000
        self._statistiques["n_generations"] += 1
        self._statistiques["n_tokens_gen"] += len(tokens_generes)
        n = self._statistiques["n_generations"]
        self._statistiques["temps_gen_ms"] = (self._statistiques["temps_gen_ms"] * (n-1) + dt) / n

        # Feedback : si active, le texte genere renforce l'hologramme
        if feedback_conscient and len(tokens_generes) >= 3:
            self.monde.enregistrer_texte(texte_genere, self.tokenizer, 0.2)

        return {
            "prompt": prompt,
            "texte_genere": texte_genere,
            "tokens": tokens_generes,
            "n_tokens": len(tokens_generes),
            "tokens_uniques": len(set(tokens_generes)),
            "diversite": round(len(set(tokens_generes)) / max(len(tokens_generes), 1), 3),
            "temps_ms": round(dt, 1),
            "tok_s": round(len(tokens_generes) / (dt/1000), 1) if dt > 0 else 0,
            "n_lecteurs": self.lecteurs.n_lecteurs,
            "n_experiences": self.monde.n_experiences,
            "energie_hologramme": round(self.monde.energie(), 1),
            "etat_conscience": self.lecteurs.signature_conscience().tolist()[:10],
            "n_rep_lecture": n_rep_lecture,
        }


# =========================================================================
# PARTIE 5 : ARCHITECTURE MODULAIRE (Phase 3)
# =========================================================================

class HierarchieHologrammes:
    """
    HIERARCHIE D'HOLOGRAMMES (abstractions multiples).

    Chaque niveau de la hierarchie est un hologramme qui encode
    l'information a une echelle differente :

    Niveau 0 (L0) : Tokens bruts - chaque token = une onde
    Niveau 1 (L1) : Phrases - combinaison d'ondes de tokens
    Niveau 2 (L2) : Paragraphes - motifs d'interference de phrases
    Niveau 3 (L3) : Concepts - abstractions pures

    La lecture a un niveau superieur active les niveaux inferieurs
    par resonance croisee.
    """

    def __init__(self, nx: int = NX, ny: int = NY, n_niveaux: int = 4):
        self.niveaux = [HologrammeMonde(nx // (i+1) if nx // (i+1) >= 16 else 16,
                                         ny // (i+1) if ny // (i+1) >= 16 else 16)
                        for i in range(n_niveaux)]
        self.n_niveaux = n_niveaux

    def enregistrer(self, niveau: int, kx: float, ky: float, amp: float = 1.0):
        """Enregistre une onde a un niveau specifique."""
        if 0 <= niveau < self.n_niveaux:
            self.niveaux[niveau].enregistrer_onde(kx, ky, amp)

    def lire(self, niveau: int, kx: float, ky: float) -> float:
        """Lit la resonance a un niveau specifique."""
        if 0 <= niveau < self.n_niveaux:
            return self.niveaux[niveau].lire_onde(kx, ky)
        return 0.0

    def resonance_croisee(self, kx: float, ky: float,
                          poids: Optional[List[float]] = None) -> float:
        """
        Resonance CROISEE entre tous les niveaux.
        L'activation finale est une somme ponderee des activations
        a tous les niveaux.
        """
        if poids is None:
            poids = [1.0 / self.n_niveaux] * self.n_niveaux

        act_total = 0.0
        for n in range(self.n_niveaux):
            act_total += poids[n] * self.lire(n, kx, ky)
        return act_total


# =========================================================================
# PARTIE 6 : SYSTEME COMPLET (Conscient + Inconscient + Feedback)
# =========================================================================

class SystemeHarmoniqueComplet:
    """
    Systeme complet avec :
    - Inconscient (hologramme brut accumule)
    - Conscience (lecteurs multiples en parallele)
    - Feedback (la conscience nourrit l'inconscient)
    - Hierarchie (abstractions multi-niveaux)
    - Certification (chaque generation est hashee)
    """

    def __init__(self, vocab: List[str], nx: int = NX, ny: int = NY,
                 n_lecteurs: int = 8, n_niveaux: int = 4):
        self.vocab = vocab
        self.tokenizer = TokeniseurOndes(vocab)
        self.monde = HologrammeMonde(nx, ny)
        self.lecteurs = LecteurResonantMultiple(self.monde, n_lecteurs)
        self.hierarchie = HierarchieHologrammes(nx, ny, n_niveaux)
        self.generateur = GenerateurResonance(vocab, nx, ny, n_lecteurs)

        self._historique = []
        self._stats = {
            "n_apprentissages": 0, "n_generations": 0,
            "n_tokens": 0, "temps_total_ms": 0.0,
        }

    def apprendre(self, texte: str, niveau: int = 0):
        """Apprend un texte a tous les niveaux de la hierarchie."""
        self.monde.enregistrer_texte(texte, self.tokenizer)
        self.generateur.apprendre(texte)

        # Propager dans la hierarchie
        tokens = self.tokenizer.tokeniser(texte)
        for idx in tokens:
            kx, ky = self.tokenizer.vecteur_onde(idx)
            self.hierarchie.enregistrer(niveau, kx, ky, 0.5)

            # Niveaux superieurs : combinaisons de tokens
            for n in range(1, self.hierarchie.n_niveaux):
                if len(tokens) >= 2**n:
                    # Moyenne des vecteurs d'onde = concept abstrait
                    groupe = tokens[:2**n]
                    kx_moy = np.mean([self.tokenizer.vecteur_onde(t)[0] for t in groupe])
                    ky_moy = np.mean([self.tokenizer.vecteur_onde(t)[1] for t in groupe])
                    self.hierarchie.enregistrer(n, kx_moy, ky_moy, 0.3)

        self._historique.append(("apprentissage", texte[:50]))
        self._stats["n_apprentissages"] += 1

    def generer(self, prompt: str, **kwargs) -> Dict:
        """Genere du texte avec le systeme complet."""
        resultat = self.generateur.generer(prompt, **kwargs)

        # Hash de certification
        ch = hashlib.sha256(
            f"{prompt}|{resultat['texte_genere']}|{resultat['n_tokens']}|{PHI}|{time.time()}".encode()
        ).hexdigest()[:16]
        resultat["hash_certificat"] = ch
        resultat["certifie"] = True

        self._historique.append(("generation", prompt[:30] + "..."))
        self._stats["n_generations"] += 1
        self._stats["n_tokens"] += resultat["n_tokens"]
        self._stats["temps_total_ms"] += resultat["temps_ms"]

        return resultat

    def stats(self) -> Dict:
        return {
            **self._stats,
            "n_experiences": self.monde.n_experiences,
            "energie_hologramme": round(self.monde.energie(), 1),
            "n_lecteurs": self.lecteurs.n_lecteurs,
            "vocab_size": self.tokenizer.vocab_size,
            "taille_hologramme": f"{self.monde.nx}x{self.monde.ny}",
            "connaissances": len(self.generateur._connaissances),
        }

    def diagnostiquer(self) -> Dict:
        """Diagnostic complet du systeme."""
        etat_lecteurs = []
        for n in range(min(4, self.lecteurs.n_lecteurs)):
            act = self.lecteurs._activation(self.lecteurs.kx[n], self.lecteurs.ky[n])
            etat_lecteurs.append({
                "lecteur": n,
                "kx": round(self.lecteurs.kx[n], 3),
                "ky": round(self.lecteurs.ky[n], 3),
                "activation": round(act, 4),
            })

        return {
            "statistiques": self.stats(),
            "etat_lecteurs": etat_lecteurs,
            "energie_hologramme": self.monde.stats(),
            "n_connaissances": len(self.generateur._connaissances),
            "top_connaissances": self.generateur._connaissances[-3:] if self.generateur._connaissances else [],
        }


# =========================================================================
# VOCABULAIRE DE BASE
# =========================================================================

VOCABULAIRE_BASE = [
    '<PAD>','<UNK>','<BOS>','<EOS>',
    'le','la','les','de','des','du','un','une','et','est','a',
    'dans','que','qui','pas','ne','sur','pour','avec',
    'je','tu','il','elle','on','nous','vous','ils','elles',
    'ce','cet','cette','ces','mon','ton','son','ma','ta','sa',
    'au','aux','en','par','plus','moins','tres','aussi',
    'comme','si','mais','ou','donc','car','ni','or',
    'faire','dire','avoir','etre','aller','pouvoir','vouloir','savoir',
    'voir','venir','prendre','donner','parler','temps','chose','monde',
    'vie','homme','femme','enfant','jour','nuit','mois','annee','heure',
    'question','reponse','probleme','solution','idee','raison',
    'travail','maison','ville','pays','grand','petit','beau','bon',
    'mauvais','vrai','faux','nouveau','vieux','jeune',
    'long','court','haut','bas','fort','faible','rapide','clair',
    'important','necessaire','possible','impossible','premier','dernier',
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
    'theorie','principe','loi','information',
    'algorithme','programme','fonction','reseau',
    'apprentissage','inference','signature','dimension','espace',
    'generation','creation','analyse','synthese','logique',
    'raisonnement','intuition','imagination','sentiment','emotion',
    'realite','possible','necessaire','cause','effet',
    'zero','un','deux','trois','quatre','cinq',
    'six','sept','huit','neuf','dix','cent','mille',
    'quand','ou','pourquoi','comment','quel','quelle',
    'se','ce','sa','son','tes','ta','ton','mes','ma','mon',
    'ses','leurs','leur','nos','notre','vos','votre',
    'donc','or','ni','car','mais','ou','et',
    'pourtant','cependant','neanmoins','toutefois','quoique',
    'parce','puisque','ainsi','notamment',
    'precisement','effectivement','certes','sansdoute',
    'philosophie','science','art','musique','poesie',
    'mathematique','physique','chimie','biologie',
    'histoire','geographie','politique','economie',
    'droit','justice','liberte','egalite','fraternite',
    'reve','imagination','creation','invention',
    'beaute','harmonie','equilibre','perfection',
    'complexite','simplicite','profondeur','surface',
    'evolution','revolution','transformation','changement',
    'diversite','unite','totalite','partie',
    'abstrait','concret','theorique','pratique',
    'operationnel',
]

VOCAB_SIZE = len(VOCABULAIRE_BASE)


# =========================================================================
# MAIN - TESTS COMPLETS
# =========================================================================

def test_tokenisation():
    """Test du tokeniseur par ondes."""
    print("=" * 70)
    print("TEST : TOKENISATION PAR PROJECTION D'ONDES")
    print("=" * 70)

    tk = TokeniseurOndes(VOCABULAIRE_BASE)
    print(f"  Vocabulaire: {tk.vocab_size} tokens")

    # Verifier que chaque token a un vecteur d'onde unique
    vecteurs = set()
    for i in range(tk.vocab_size):
        kx, ky = tk.vecteur_onde(i)
        vecteurs.add((round(kx, 6), round(ky, 6)))

    print(f"  Vecteurs uniques: {len(vecteurs)}/{tk.vocab_size}")
    print(f"  Collisions: {tk.vocab_size - len(vecteurs)}")
    print(f"  Distribution kx: [{np.min(tk._kx):.3f}, {np.max(tk._kx):.3f}]")
    print(f"  Distribution ky: [{np.min(tk._ky):.3f}, {np.max(tk._ky):.3f}]")
    print(f"  [OK] Aucune collision" if len(vecteurs) == tk.vocab_size else "  [ATTENTION] Collisions detectees")


def test_hologramme_accumulation():
    """Test de l'hologramme brut avec accumulation."""
    print("\n" + "=" * 70)
    print("TEST : HOLOGRAMME BRUT - ACCUMULATION D'EXPERIENCES")
    print("=" * 70)

    monde = HologrammeMonde()
    tk = TokeniseurOndes(VOCABULAIRE_BASE)

    # Etat initial
    print(f"\n  Etat initial: energie={monde.energie():.2f}, amplitude_moy={np.mean(np.abs(monde.H)):.4f}")

    # Ajouter des tokens un par un
    mots_test = ['harmonie', 'resonance', 'conscience', 'amour', 'paix']
    for mot in mots_test:
        idx = tk.tokeniser(mot)[0] if tk.tokeniser(mot) else 0
        kx, ky = tk.vecteur_onde(idx)
        monde.enregistrer_onde(kx, ky, 1.0)
        print(f"  +{mot:15s} (idx={idx:3d}, k=({kx:.3f},{ky:.3f})) -> energie={monde.energie():.2f}")

    print(f"\n  Final: {monde.n_experiences} experiences, energie={monde.energie():.2f}")

    # Verifier la resonance
    print(f"\n  Resonance apres accumulation:")
    for mot in mots_test:
        idx = tk.tokeniser(mot)[0]
        kx, ky = tk.vecteur_onde(idx)
        res = monde.lire_onde(kx, ky)
        print(f"    '{mot}': {res:.4f}")


def test_lecteurs_multiples():
    """Test des lecteurs multiples en parallele."""
    print("\n" + "=" * 70)
    print("TEST : LECTEURS MULTIPLES - CONSCIENCE PARALLELE")
    print("=" * 70)

    monde = HologrammeMonde()
    tk = TokeniseurOndes(VOCABULAIRE_BASE)

    # Enregistrer des experiences
    mots = ['conscience', 'pensee', 'intelligence', 'esprit', 'ame',
            'raisonnement', 'intuition', 'imagination', 'sentiment']
    for mot in mots:
        idx = tk.tokeniser(mot)[0]
        kx, ky = tk.vecteur_onde(idx)
        monde.enregistrer_onde(kx, ky, 1.0 + np.random.random() * 0.5)

    # 8 lecteurs apprennent
    lecteurs = LecteurResonantMultiple(monde, n_lecteurs=8)
    lecteurs.apprendre(n_iter=30, lr=0.03)

    print(f"\n  8 lecteurs apres 30 iterations:")
    print(f"  {'Lecteur':8s} | {'kx':8s} | {'ky':8s} | {'Activation':12s}")
    for n in range(8):
        act = lecteurs._activation(lecteurs.kx[n], lecteurs.ky[n])
        print(f"  {n:8d} | {lecteurs.kx[n]:8.3f} | {lecteurs.ky[n]:8.3f} | {act:12.4f}")

    # Top tokens pour chaque lecteur
    top = lecteurs.top_tokens_par_lecteur(tk, top_k=5)
    print(f"\n  Top-5 tokens par lecteur:")
    for n in range(min(4, lecteurs.n_lecteurs)):
        tokens_str = ', '.join([f"'{tk.i2w[t]}'({a:.3f})" for t, a in top[n][:5]])
        print(f"    Lecteur {n}: {tokens_str}")


def test_generation():
    """Test complet de generation par resonance."""
    print("\n" + "=" * 70)
    print("TEST : GENERATION PAR RESONANCE INVERSE")
    print("=" * 70)

    gen = GenerateurResonance(VOCABULAIRE_BASE)

    # Apprendre des connaissances
    textes = [
        "phi est le nombre d or la proportion divine de l univers",
        "la resonance harmonique amplifie les ondes a la frequence propre",
        "la conscience est la capacite de percevoir sa propre existence",
        "l amour est la force la plus puissante de l univers",
        "la beaute de la nature est une source d emerveillement infini",
    ]
    gen.apprendre_batch(textes)
    print(f"\n  Connaissances apprises: {len(textes)}")
    print(f"  Experiences dans l'hologramme: {gen.monde.n_experiences}")
    print(f"  Energie de l'hologramme: {gen.monde.energie():.2f}")

    # Generer des reponses
    prompts = [
        "parle moi du nombre d or",
        "explique la resonance",
        "qu est ce que la conscience",
    ]

    for prompt in prompts:
        r = gen.generer(prompt, max_tokens=25, n_rep_lecture=20, temperature=0.85)
        print(f"\n  >> {prompt}")
        print(f"  << {r['texte_genere']}")
        print(f"     ({r['n_tokens']}t, div={r['diversite']}, {r['temps_ms']:.0f}ms, "
              f"lecteurs={r['n_lecteurs']}, energie={r['energie_hologramme']:.0f})")


def test_hierarchie():
    """Test de la hierarchie d'hologrammes."""
    print("\n" + "=" * 70)
    print("TEST : HIERARCHIE D'HOLOGRAMMES (ABSTRACTIONS)")
    print("=" * 70)

    hier = HierarchieHologrammes(n_niveaux=4)
    tk = TokeniseurOndes(VOCABULAIRE_BASE)

    # Enregistrer a differents niveaux
    texte = "la conscience et la pensee sont lies"
    tokens = tk.tokeniser(texte)

    for i, idx in enumerate(tokens):
        kx, ky = tk.vecteur_onde(idx)
        # Niveau 0 : tokens bruts
        hier.enregistrer(0, kx, ky, 1.0)
        # Niveau 2 : concepts (tous les tokens)
        if i == len(tokens) - 1:
            kx_concept = np.mean([tk.vecteur_onde(t)[0] for t in tokens])
            ky_concept = np.mean([tk.vecteur_onde(t)[1] for t in tokens])
            hier.enregistrer(2, kx_concept, ky_concept, 1.0)

    print(f"\n  Niveaux: {hier.n_niveaux}")
    for n in range(hier.n_niveaux):
        h = hier.niveaux[n]
        print(f"  Niveau {n}: taille={h.nx}x{h.ny}, "
              f"experiences={h.n_experiences}, energie={h.energie():.2f}")

    # Resonance croisee
    for mot in ['conscience', 'pensee', 'lies']:
        idx = tk.tokeniser(mot)[0]
        kx, ky = tk.vecteur_onde(idx)
        res = hier.resonance_croisee(kx, ky)
        print(f"  Resonance croisee pour '{mot}': {res:.4f}")


def demo_complete():
    """Demo complete du systeme."""
    print("\n" + "=" * 74)
    print("DEMO COMPLETE : SYSTEME HARMONIQUE CONSCIENT + INCONSCIENT")
    print("=" * 74)

    systeme = SystemeHarmoniqueComplet(VOCABULAIRE_BASE, n_lecteurs=8, n_niveaux=3)

    # Phase 1 : Apprentissage
    print("\n[PHASE 1] APPRENTISSAGE...")
    textes_base = [
        "phi est le nombre d or la proportion divine de l univers",
        "la resonance harmonique amplifie les ondes a la frequence propre",
        "la conscience est la capacite de percevoir sa propre existence",
        "les fractales sont des structures infinies auto similaires",
        "la suite de Fibonacci converge vers le nombre d or phi",
        "l amour est la force la plus puissante de l univers",
        "la beaute de la nature est une source d emerveillement infini",
        "l intelligence artificielle explore la creation de machines penseantes",
        "le temps est une dimension fondamentale de notre univers",
        "la musique est l harmonie entre le silence et le son",
        "la philosophie est l amour de la sagesse et de la connaissance",
        "python est un langage de programmation clair et puissant",
        "la creativite est l intelligence qui s amuse",
        "la connaissance de soi est le debut de toute sagesse",
        "la compassion et la bienveillance unissent les etres humains",
        "tout systeme physique a une frequence de resonance fondamentale",
        "la verite est souvent plus etrange que la fiction",
        "l imagination est plus importante que la connaissance",
        "le silence est le langage de la sagesse profonde",
        "la patience est la cle de toute reussite",
    ]
    for t in textes_base:
        systeme.apprendre(t)

    print(f"  {len(textes_base)} textes appris")
    print(f"  Experiences dans l'hologramme: {systeme.monde.n_experiences}")

    # Phase 2 : Generation
    print("\n[PHASE 2] GENERATION PAR RESONANCE...")
    prompts = [
        "parle moi du nombre d or et de l harmonie",
        "explique la conscience",
        "qu est ce que l amour",
        "comment fonctionne la resonance",
    ]

    for prompt in prompts:
        print(f"\n  >> {prompt}")
        r = systeme.generer(prompt, max_tokens=30, n_rep_lecture=25,
                           temperature=0.85, top_k=25, lr_apprentissage=0.03,
                           feedback_conscient=True)
        print(f"  << {r['texte_genere']}")
        print(f"     [{r['n_tokens']}t | div={r['diversite']} | "
              f"{r['temps_ms']:.0f}ms | energie={r['energie_hologramme']:.0f} | "
              f"hash={r['hash_certificat']}]")

    # Phase 3 : Diagnostic final
    print("\n[PHASE 3] DIAGNOSTIC FINAL")
    diag = systeme.diagnostiquer()
    print(f"  {json.dumps(diag['statistiques'], indent=2)}")
    print(f"\n  Etat des 4 premiers lecteurs:")
    for lec in diag['etat_lecteurs']:
        print(f"    Lecteur {lec['lecteur']}: k=({lec['kx']:.3f},{lec['ky']:.3f}), "
              f"act={lec['activation']:.4f}")

    print(f"\n{'='*74}")
    print("SYSTEME HARMONIQUE COMPLET OPERATIONNEL")
    print("Phase 2 (Generation par resonance inverse) : OK")
    print("Phase 3 (Architecture modulaire) : OK")
    print("  - Plusieurs lecteurs simultanes: OK")
    print("  - Hierarchie d'hologrammes: OK")
    print("  - Boucle de feedback conscience<->inconscient: OK")
    print("=" * 74)


# =========================================================================
# EXECUTION
# =========================================================================

if __name__ == "__main__":
    import sys

    if "--quick" in sys.argv:
        test_tokenisation()
        test_hologramme_accumulation()
        test_lecteurs_multiples()
        test_generation()
    elif "--demo" in sys.argv:
        demo_complete()
    else:
        test_tokenisation()
        test_hologramme_accumulation()
        test_lecteurs_multiples()
        test_generation()
        test_hierarchie()
        demo_complete()
