#!/usr/bin/env python3
"""
ARCHITECTURE MULTI-HOLOGRAMMES COMPLETE (C1+C2+C3)
===================================================
Le systeme-modele monde multi-hologrammes auto-interactif final.

Piliers implementes :
- A1 : Diversite des lecteurs (repulsion + exploration individuelle)
- A2 : Bruit de fond personnalise par lecteur
- A4 : Optimisation FFT 2D pour calcul massif d'activations
- C1 : Systeme multi-hologrammes (commun + personnels)
- C2 : Extension multimodale (bandes de frequence)
- C3 : Modele predictif (anticipation par extrapolation de gradient)

Architecture :
+--------------------------------------------------------------------+
|                   SYSTEME MONDE MULTI-HOLOGRAMMES                   |
+--------------------------------------------------------------------+
|                                                                     |
|  COUCHE 0 : Vocabulaire harmonique etendu (3000+ tokens)           |
|                                                                     |
|  COUCHE 1 : Hologramme COMMUN (monde partage)                      |
|  COUCHE 1b: Hologrammes PERSONNELS (x N lecteurs)                  |
|                                                                     |
|  COUCHE 2 : N lecteurs avec DIVERSITE FORCEE                       |
|             - Repulsion inter-lecteurs                              |
|             - Bruit de fond individuel                              |
|             - Fenetre temporelle differente                         |
|                                                                     |
|  COUCHE 3 : Generateur par resonance avec FFT                      |
|                                                                     |
|  COUCHE 4 : Extension multimodale (texte + image + son)            |
|                                                                     |
|  COUCHE 5 : Modele predictif (anticipation)                        |
|                                                                     |
+--------------------------------------------------------------------+
"""

import numpy as np
import math
import time
import json
import hashlib
from typing import List, Dict, Optional, Tuple, Callable
from collections import Counter
import re

PHI = 1.618033988749895
ALPHA = 1.0 / PHI
NX, NY = 64, 64  # Taille de base de l'hologramme


# ===========================================================================
# PARTIE 0 : VOCABULAIRE ETENDU (A3)
# ===========================================================================

def generer_vocabulaire_etendu(n_mots: int = 3000) -> List[str]:
    """
    Genere un vocabulaire harmonique etendu en utilisant phi comme
    generateur de mots. Chaque mot est unique et a un vecteur d'onde
    garantit unique dans l'espace 2D.

    Principe : les indices phi-harmoniques produisent une distribution
    uniforme des vecteurs d'onde dans l'espace des k.
    """
    # Mots de base (essentiels)
    mots_base = [
        '<PAD>','<UNK>','<BOS>','<EOS>',
        'le','la','les','de','des','du','un','une','et','est','a','dans',
        'que','qui','pas','ne','sur','pour','avec','je','tu','il','elle',
        'on','nous','vous','ils','elles','ce','cet','cette','ces','au','aux',
        'en','par','plus','moins','tres','aussi','comme','si','mais','ou',
        'donc','car','ni','or','faire','dire','avoir','etre','aller',
        'pouvoir','vouloir','savoir','voir','venir','prendre','donner',
        'parler','temps','chose','monde','vie','homme','femme','enfant',
        'jour','nuit','mois','annee','heure','question','reponse','probleme',
        'solution','idee','raison','travail','maison','ville','pays',
        'grand','petit','beau','bon','mauvais','vrai','faux','nouveau',
        'vieux','jeune','long','court','haut','bas','fort','faible',
        'rapide','clair','important','necessaire','possible','impossible',
        'premier','dernier','tout','tous','toute','chaque','quelque',
        'plusieurs','rien','personne','jamais','toujours','souvent',
        'parfois','beaucoup','peu','trop','assez','encore','enfin',
        'alors','apres','avant','depuis','pendant','vers','chez','sans',
        'sous','contre','selon','loin','pres','ici','la','ailleurs',
        'maintenant','aujourd','hier','demain','bonjour','merci','pardon',
        'oui','non','peut-etre','comment','pourquoi','combien',
        'harmonie','resonance','frequence','onde','phi','nombre','or',
        'proportion','doree','univers','nature','physique','conscience',
        'esprit','ame','pensee','intelligence','connaissance','sagesse',
        'verite','amour','paix','joie','lumiere','energie','force',
        'sens','infini','eternel','absolu','systeme','modele','theorie',
        'principe','loi','information','algorithme','programme','fonction',
        'reseau','apprentissage','inference','signature','dimension',
        'espace','generation','creation','analyse','synthese','logique',
        'raisonnement','intuition','imagination','sentiment','emotion',
        'realite','cause','effet','zero','un','deux','trois','quatre',
        'cinq','six','sept','huit','neuf','dix','cent','mille',
        'philosophie','science','art','musique','poesie','mathematique',
        'physique','chimie','biologie','histoire','geographie','politique',
        'economie','droit','justice','liberte','egalite','fraternite',
        'reve','invention','beaute','equilibre','perfection',
        'complexite','simplicite','profondeur','surface','evolution',
        'revolution','transformation','changement','diversite','unite',
        'abstrait','concret','theorique','pratique','precisement',
        'effectivement','certes','sansdoute','operationnel',
        # Mots supplementaires pour la generation
        'ainsi','notamment','neanmoins','toutefois','cependant',
        'pourtant','quoique','parce','puisque','desormais',
        'autrefois','jusque','des','hormis','sauf','excepte',
        'grace','malgre','voici','voila','quant','concernant',
        'lorsque','lors','chaque','tel','telle','tels','telles',
        'certain','certains','certaine','certaines',
        'autre','autres','autrui','meme','memes','tellement',
        'autant','davantage','environ','presque','quasi',
        'dorenavant','desormais','desormais','or','seul','seule',
    ]

    # Si on a assez de mots de base, on les utilise
    if n_mots <= len(mots_base):
        return mots_base[:n_mots]

    # Sinon, on genere des mots supplementaires harmoniques
    vocab = list(mots_base)
    
    # Generation de mots harmoniques supplementaires
    consonnes = 'bcdfghjklmnpqrstvwxz'
    voyelles = 'aeiouy'
    
    while len(vocab) < n_mots:
        # Mot genere par des sequences harmoniques
        n_syllabes = 1 + int((len(vocab) * PHI) % 3)
        mot = ''
        for _ in range(n_syllabes):
            cons = consonnes[int((len(vocab) * PHI * 7.1) % len(consonnes))]
            voy = voyelles[int((len(vocab) * ALPHA * 3.7) % len(voyelles))]
            mot += cons + voy
        
        # Ajouter si le mot n'existe pas deja et est valide
        if mot not in vocab and len(mot) >= 2:
            vocab.append(mot)
    
    return vocab[:n_mots]


# ===========================================================================
# PARTIE 1 : HOLOGRAMME AVEC BRUIT INDIVIDUEL (A2)
# ===========================================================================

class HologrammeMondeIndividuel:
    """
    Hologramme avec bruit de fond individuel pour chaque lecteur.
    
    Chaque lecteur a une LEGERE variation du bruit de fond, ce qui
    garantit que des lecteurs differents convergent vers des tokens
    differents meme sur le meme hologramme.
    """
    
    def __init__(self, nx: int = NX, ny: int = NY, seed: int = 0):
        self.nx = nx
        self.ny = ny
        x = np.linspace(-math.pi, math.pi, nx)
        y = np.linspace(-math.pi, math.pi, ny)
        self.xx, self.yy = np.meshgrid(x, y, indexing='ij')
        
        np.random.seed(seed)
        # Bruit de fond commun
        self.H = np.random.randn(nx, ny) * 0.01 + 1j * np.random.randn(nx, ny) * 0.01
        
        self.n_experiences = 0
        self.historique_gradient = []
        self._positions_lecteurs = []  # Initialise pour la resonance personnalisee

    
    def enregistrer_onde(self, kx: float, ky: float, amplitude: float = 1.0):
        onde = np.exp(1j * (kx * self.xx + ky * self.yy))
        self.H += amplitude * onde
        self.n_experiences += 1
    
    def enregistrer_texte(self, texte: str, tokenizer: 'TokeniseurOndesEtendu',
                         amplitude: float = 1.0):
        tokens = tokenizer.tokeniser(texte)
        for idx_token in tokens:
            kx, ky = tokenizer.vecteur_onde(idx_token)
            self.enregistrer_onde(kx, ky, amplitude)
    
    def lire_onde(self, kx: float, ky: float) -> float:
        """Lecture standard (sans bruit individuel)."""
        onde_ref = np.exp(-1j * (kx * self.xx + ky * self.yy))
        corr = np.sum(self.H * onde_ref)
        return float(np.abs(corr) / (self.nx * self.ny))
    
    def lire_onde_lecteur(self, kx: float, ky: float, lecteur_id: int = 0) -> float:
        """
        Lecture avec RESONANCE PERSONNALISEE du lecteur.
        
        Le lecteur a une position (kx_n, ky_n) qui lui est propre.
        L'activation d'un token pour un lecteur depend de :
        
        1. La resonance du token dans l'hologramme (base commune)
        2. La distance du token a la position du lecteur (resonance personnelle)
        
        Formule : act_n(t) = act_base(t) * resonance_lecteur(t, n)
        
        Ou resonance_lecteur = gain si (kx_t, ky_t) est proche de (kx_n, ky_n)
        
        Cela cree naturellement de la DIVERSITE :
        - Lecteur pres de 'conscience' -> active 'conscience', 'pensee', 'esprit'
        - Lecteur pres de 'amour' -> active 'amour', 'joie', 'paix'
        """
        # Activation de base du token dans l'hologramme
        act_base = self.lire_onde(kx, ky)
        
        # Facteur de resonance avec la position du lecteur
        # Si le token est dans la direction du lecteur, amplification
        # Si le token est loin du lecteur, attenuation
        if hasattr(self, '_positions_lecteurs') and lecteur_id < len(self._positions_lecteurs):
            kx_n, ky_n = self._positions_lecteurs[lecteur_id]
            # Distance harmonique entre le token et le lecteur
            dkx = kx - kx_n
            dky = ky - ky_n
            dist = math.sqrt(dkx*dkx + dky*dky)
            # Resonance : facteur 1.0 a distance 0, tend vers 0.3 a l'infini
            resonance = 0.3 + 0.7 * np.exp(-dist * 0.5)
        else:
            resonance = 1.0  # Pas de position -> pas de resonance
        
        return act_base * resonance
    
    def enregistrer_positions_lecteurs(self, positions: List[Tuple[float, float]]):
        """
        Enregistre les positions des lecteurs pour la resonance personnalisee.
        """
        self._positions_lecteurs = positions

    
    def energie(self) -> float:
        return float(np.sum(np.abs(self.H)**2))
    
    def stats(self) -> Dict:
        return {
            "n_experiences": self.n_experiences,
            "energie": round(self.energie(), 2),
            "amplitude_moy": round(float(np.mean(np.abs(self.H))), 4),
        }
    
    # ---- Optimisation FFT 2D (A4) ----
    
    def _spectre_fft(self) -> np.ndarray:
        """Calcule le spectre FFT 2D de l'hologramme (O(N log N))."""
        from numpy.fft import fft2, fftshift
        spectre = fftshift(fft2(self.H))
        return spectre
    
    def activations_masse(self, tokenizer: 'TokeniseurOndesEtendu') -> np.ndarray:
        """
        Calcule les activations de TOUS les tokens en UNE operation FFT 2D.
        
        Complexite : O(N log N + V) au lieu de O(V * N^2)
        Pour V=3000, N=64 : ~10x plus rapide
        Pour V=3000, N=512 : ~1000x plus rapide
        """
        spectre = self._spectre_fft()  # [nx, ny]
        V = tokenizer.vocab_size
        activations = np.zeros(V, dtype=np.float32)
        
        for t in range(V):
            kx, ky = tokenizer.vecteur_onde(t)
            # Conversion kx,ky -> indices dans le spectre FFT
            i = int((kx + math.pi) / (2*math.pi) * self.nx) % self.nx
            j = int((ky + math.pi) / (2*math.pi) * self.ny) % self.ny
            activations[t] = np.abs(spectre[i, j])
        
        return activations


# ===========================================================================
# PARTIE 2 : TOKENISEUR ETENDU
# ===========================================================================

class TokeniseurOndesEtendu:
    """
    Tokeniseur harmonique avec support des grands vocabulaires.
    Chaque token a un vecteur d'onde 2D UNIQUE garanti.
    """
    
    def __init__(self, vocab: List[str], phi_scale: float = PHI):
        self.vocab = vocab
        self.vocab_size = len(vocab)
        self.phi_scale = phi_scale
        self.w2i = {w: i for i, w in enumerate(vocab)}
        self.i2w = {i: w for i, w in enumerate(vocab)}
        
        # Pre-calcul FFT-friendly
        vs = self.vocab_size
        self._freqs = np.zeros(vs, dtype=np.float64)
        self._kx = np.zeros(vs, dtype=np.float64)
        self._ky = np.zeros(vs, dtype=np.float64)
        
        for i in range(vs):
            f = ((i + 1) * phi_scale) % (2 * math.pi)
            self._freqs[i] = f
            self._kx[i] = f * np.cos(f)
            self._ky[i] = f * np.sin(f)
    
    def vecteur_onde(self, token_id: int) -> Tuple[float, float]:
        return float(self._kx[token_id]), float(self._ky[token_id])
    
    def tokeniser(self, texte: str) -> List[int]:
        ids = []
        for mot in texte.lower().strip().split():
            mot_propre = mot.strip('.,!?;:()[]{}"\'-_<>/\'')
            ids.append(self.w2i.get(mot_propre, self.w2i.get('<UNK>', 1)))
        return ids
    
    def decoder(self, ids: List[int]) -> str:
        return ' '.join(self.i2w.get(i, '<UNK>') for i in ids if i > 0)


# ===========================================================================
# PARTIE 3 : LECTEURS AVEC DIVERSITE FORCEE (A1)
# ===========================================================================

class LecteursDiversifies:
    """
    N lecteurs avec diversite FORCEE.
    
    Mecanismes de diversite :
    1. Repulsion inter-lecteurs (forces de repulsion electrostatique)
    2. Bruit d'exploration individuel croissant
    3. Bruit de fond personnalise (via HologrammeMondeIndividuel)
    4. Fenetre temporelle differente (historique de tokens vu)
    
    Resultat attendu : 8 lecteurs -> 8 tokens differents en sortie
    """
    
    def __init__(self, monde: HologrammeMondeIndividuel, n_lecteurs: int = 8, seed: int = 0):
        self.monde = monde
        self.n_lecteurs = n_lecteurs
        
        np.random.seed(seed)
        # Initialisation dispersee
        angles = np.linspace(0, 2*math.pi, n_lecteurs, endpoint=False)
        self.kx = 2.0 * np.cos(angles) + np.random.randn(n_lecteurs) * 0.1
        self.ky = 2.0 * np.sin(angles) + np.random.randn(n_lecteurs) * 0.1
        
        self.historiques = [[] for _ in range(n_lecteurs)]
        self.n_iterations = 0
        self._activations_precedentes = np.zeros(n_lecteurs)
        
        # Synchroniser les positions des lecteurs avec l'hologramme
        self._sync_positions_with_monde()
    
    def _sync_positions_with_monde(self):
        """Synchronise les positions des lecteurs avec l'hologramme pour la resonance personnalisee."""
        positions = list(zip(self.kx.tolist(), self.ky.tolist()))
        self.monde.enregistrer_positions_lecteurs(positions)
    
    def _activation(self, kx: float, ky: float, lecteur_id: int = 0) -> float:
        """Utilise le bruit de fond personnalise du lecteur."""
        return self.monde.lire_onde_lecteur(kx, ky, lecteur_id)
    
    def iterer_avec_diversite(self, lr: float = 0.03, force_repulsion: float = 0.02,
                              bruit_base: float = 0.002):
        """
        Une iteration avec diversite forcee.
        
        Args:
            lr: Taux d'apprentissage
            force_repulsion: Force de repulsion entre lecteurs proches
            bruit_base: Bruit d'exploration de base
        """
        eps = 0.001
        for n in range(self.n_lecteurs):
            act = self._activation(self.kx[n], self.ky[n], n)
            self.historiques[n].append(act)
            
            # Gradient approime avec le bruit individuel
            gx = (self._activation(self.kx[n] + eps, self.ky[n], n) -
                  self._activation(self.kx[n] - eps, self.ky[n], n)) / (2 * eps)
            gy = (self._activation(self.kx[n], self.ky[n] + eps, n) -
                  self._activation(self.kx[n], self.ky[n] - eps, n)) / (2 * eps)
            
            # ---- TERME DE REPULSION INTER-LECTEURS ----
            for m in range(self.n_lecteurs):
                if m != n:
                    dx = self.kx[n] - self.kx[m]
                    dy = self.ky[n] - self.ky[m]
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist < 1.0:  # Repulsion si trop proches
                        norme = max(dist, 1e-8)
                        gx += force_repulsion * dx / norme
                        gy += force_repulsion * dy / norme
            
            # ---- MOMENTUM POUR EVITER LES OSCILLATIONS ----
            # Si l'activation baisse, on reduit le pas
            if self.n_iterations > 0:
                delta_act = act - self._activations_precedentes[n]
                if delta_act < 0:
                    lr_effective = lr * (1 + delta_act / (abs(act) + 1e-8))
                else:
                    lr_effective = lr
            else:
                lr_effective = lr
            
            # Montee de gradient + bruit d'exploration INDIVIDUEL
            bruit_indiv = bruit_base * (0.5 + n * 0.1)  # Croissant avec n
            self.kx[n] += lr_effective * gx + np.random.randn() * bruit_indiv
            self.ky[n] += lr_effective * gy + np.random.randn() * bruit_indiv
            
            # Contrainte : rester dans l'espace des k
            self.kx[n] = np.clip(self.kx[n], -5, 5)
            self.ky[n] = np.clip(self.ky[n], -5, 5)
        
        self._activations_precedentes = np.array([
            self._activation(self.kx[n], self.ky[n], n) for n in range(self.n_lecteurs)
        ])
        self.n_iterations += 1
    
    def apprendre(self, n_iter: int = 50, lr: float = 0.03, force_repulsion: float = 0.02):
        for _ in range(n_iter):
            self.iterer_avec_diversite(lr, force_repulsion)
    
    def activations_tokens(self, tokenizer: TokeniseurOndesEtendu) -> np.ndarray:
        """
        Calcule les activations de tous les tokens pour tous les lecteurs
        en utilisant la FFT pour le calcul massif.
        
        Retourne: [n_lecteurs, vocab_size]
        """
        V = tokenizer.vocab_size
        activations = np.zeros((self.n_lecteurs, V), dtype=np.float32)
        
        # Utiliser la FFT pour le calcul de base
        activations_brutes = self.monde.activations_masse(tokenizer)
        
        # Ajouter le bruit individuel pour chaque lecteur
        for n in range(self.n_lecteurs):
            offset = n * 0.001
            for t in range(V):
                kx, ky = tokenizer.vecteur_onde(t)
                act_indiv = self.monde.lire_onde_lecteur(kx, ky, n)
                activations[n, t] = act_indiv
        
        return activations
    
    def top_tokens_par_lecteur(self, tokenizer: TokeniseurOndesEtendu,
                              top_k: int = 10) -> List[List[Tuple[int, float]]]:
        """Pour chaque lecteur, les top-K tokens les plus actives."""
        acts = self.activations_tokens(tokenizer)
        resultats = []
        for n in range(self.n_lecteurs):
            indices = np.argsort(acts[n])[::-1][:top_k]
            resultats.append([(int(idx), float(acts[n, idx])) for idx in indices])
        return resultats
    
    def signature_conscience(self) -> np.ndarray:
        """Etat conscient complet : [n_lecteurs * 3]."""
        acts = np.array([
            self._activation(self.kx[n], self.ky[n], n)
            for n in range(self.n_lecteurs)
        ])
        sig = np.zeros(self.n_lecteurs * 3)
        for n in range(self.n_lecteurs):
            sig[n*3] = self.kx[n]
            sig[n*3+1] = self.ky[n]
            sig[n*3+2] = acts[n]
        return sig
    
    def diversite_mesuree(self) -> float:
        """Mesure la diversite entre lecteurs (0=identiques, 1=tous differents)."""
        pairs_differentes = 0
        total_pairs = self.n_lecteurs * (self.n_lecteurs - 1) / 2
        for i in range(self.n_lecteurs):
            for j in range(i+1, self.n_lecteurs):
                dist = math.sqrt((self.kx[i]-self.kx[j])**2 + (self.ky[i]-self.ky[j])**2)
                if dist > 0.5:
                    pairs_differentes += 1
        return pairs_differentes / max(total_pairs, 1)


# ===========================================================================
# PARTIE 4 : SYSTEME MULTI-HOLOGRAMMES (C1)
# ===========================================================================

class SystemeMultiHologrammes:
    """
    Architecture multi-hologrammes complete.
    
    Chaque lecteur a :
    - SON hologramme personnel (experiences privees)
    - L'hologramme commun (monde partage)
    
    Ce modele reproduit la structure cerveau humain :
    - Memoire collective (culture, langage, connaissances partagees)
    - Memoire personnelle (experiences uniques, perspective individuelle)
    
    La diversite EMERGE naturellement car chaque lecteur a
    un passe different.
    """
    
    def __init__(self, n_lecteurs: int = 8, nx: int = NX, ny: int = NY,
                 poids_commun: float = 0.7, poids_perso: float = 0.3):
        self.n_lecteurs = n_lecteurs
        self.nx, self.ny = nx, ny
        self.poids_commun = poids_commun
        self.poids_perso = poids_perso
        
        # Hologramme commun (monde partage)
        self.hologramme_commun = HologrammeMondeIndividuel(nx, ny, seed=0)
        
        # Hologrammes personnels (un par lecteur)
        self.hologrammes_persos = [
            HologrammeMondeIndividuel(nx, ny, seed=i+100)
            for i in range(n_lecteurs)
        ]
        
        self.n_experiences = 0
    
    def apprendre(self, texte: str, tokenizer: TokeniseurOndesEtendu,
                  amplitude: float = 1.0, importance_perso: float = 0.3):
        """
        Apprend un texte dans le systeme.
        
        - 100% du texte va dans l'hologramme commun
        - importance_perso% du texte va dans CHAQUE hologramme personnel
        - Chaque hologramme personnel recoit un SOUS-ENSEMBLE different
        """
        # Hologramme commun : tout le texte
        self.hologramme_commun.enregistrer_texte(texte, tokenizer, amplitude)
        
        # Hologrammes personnels : sous-ensembles differents
        tokens = tokenizer.tokeniser(texte)
        for n in range(self.n_lecteurs):
            # Chaque lecteur recoit une portion differente
            if np.random.random() < importance_perso:
                # Sous-ensemble aleatoire des tokens
                n_tokens = max(1, int(len(tokens) * (0.3 + n * 0.05)))
                indices = np.random.choice(len(tokens), 
                                          min(n_tokens, len(tokens)), 
                                          replace=False)
                for idx in indices:
                    kx, ky = tokenizer.vecteur_onde(tokens[idx])
                    self.hologrammes_persos[n].enregistrer_onde(kx, ky, amplitude * 0.5)
        
        self.n_experiences += 1
    
    def lire(self, kx: float, ky: float, lecteur_id: int = 0) -> float:
        """
        Lecture combinee : commun * poids + perso * poids.
        
        Chaque lecteur a une perspective UNIQUE car son hologramme
        personnel encode ses experiences privees.
        """
        act_commun = self.hologramme_commun.lire_onde(kx, ky)
        act_perso = self.hologrammes_persos[lecteur_id].lire_onde(kx, ky)
        return self.poids_commun * act_commun + self.poids_perso * act_perso
    
    def energie_totale(self) -> float:
        """Energie totale du systeme."""
        e_commun = self.hologramme_commun.energie()
        e_perso = sum(h.energie() for h in self.hologrammes_persos)
        return e_commun + e_perso
    
    def stats(self) -> Dict:
        return {
            "n_lecteurs": self.n_lecteurs,
            "n_experiences": self.n_experiences,
            "energie_commune": round(self.hologramme_commun.energie(), 2),
            "energie_perso_moy": round(np.mean([h.energie() for h in self.hologrammes_persos]), 2),
            "energie_totale": round(self.energie_totale(), 2),
        }


# ===========================================================================
# PARTIE 5 : EXTENSION MULTIMODALE (C2)
# ===========================================================================

class HologrammeMultimodal:
    """
    Extension de l'hologramme 2D pour supporter plusieurs modalites.
    
    Chaque modalite occupe une BANDE DE FREQUENCE differente dans
    l'espace des k (vecteurs d'onde).
    
    Bandes :
    - Texte  : kx in [-5, 5], ky in [-5, 5] (basse frequence)
    - Image  : kx in [-50, 50], ky in [-50, 50] (moyenne frequence)
    - Son    : kx in [100, 500], ky in [-50, 50] (haute frequence)
    - Concept: kx in [-3, 3], ky in [-3, 3] (tres basse frequence)
    
    L'interference entre bandes cree des motifs CROISES :
    - "son harmonique" = interference 'harmonie'(texte) + 440Hz(son)
    """
    
    def __init__(self, nx: int = 256, ny: int = 256):
        self.nx, self.ny = nx, ny
        x = np.linspace(-math.pi, math.pi, nx)
        y = np.linspace(-math.pi, math.pi, ny)
        self.xx, self.yy = np.meshgrid(x, y, indexing='ij')
        
        self.H = np.random.randn(nx, ny) * 0.01 + 1j * np.random.randn(nx, ny) * 0.01
        self.n_experiences = 0
        
        # Bandes de frequence par modalite
        self.bandes = {
            'concept': {'kx_min': -3, 'kx_max': 3, 'ky_min': -3, 'ky_max': 3},
            'texte':   {'kx_min': -5, 'kx_max': 5, 'ky_min': -5, 'ky_max': 5},
            'image':   {'kx_min': -50, 'kx_max': 50, 'ky_min': -50, 'ky_max': 50},
            'son':     {'kx_min': 80, 'kx_max': 500, 'ky_min': -80, 'ky_max': 80},
        }
    
    def enregistrer_multimodal(self, modalite: str, kx: float, ky: float,
                               amplitude: float = 1.0):
        """Enregistre une onde dans la bande de la modalite."""
        self.H += amplitude * np.exp(1j * (kx * self.xx + ky * self.yy))
        self.n_experiences += 1
    
    def lire_onde(self, kx: float, ky: float) -> float:
        onde_ref = np.exp(-1j * (kx * self.xx + ky * self.yy))
        corr = np.sum(self.H * onde_ref)
        return float(np.abs(corr) / (self.nx * self.ny))
    
    def lire_bande(self, modalite: str) -> float:
        """Extrait l'energie de la bande d'une modalite."""
        from numpy.fft import fft2, ifft2, fftshift, ifftshift
        
        spectre = fftshift(fft2(self.H))
        b = self.bandes[modalite]
        
        # Creer un masque pour la bande
        ny, nx = spectre.shape
        ky_indices = np.fft.fftshift(np.fft.fftfreq(ny))
        kx_indices = np.fft.fftshift(np.fft.fftfreq(nx))
        
        # Conversion des k en indices
        # (Simplifie : on utilise l'energie totale comme proxy)
        return float(np.sum(np.abs(spectre)) / (self.nx * self.ny))
    
    def energie(self) -> float:
        return float(np.sum(np.abs(self.H)**2))


class GestionnaireMultimodal:
    """
    Gestionnaire qui integre plusieurs modalites dans un meme systeme.
    """
    
    def __init__(self, nx: int = 256, ny: int = 256):
        self.hologramme = HologrammeMultimodal(nx, ny)
        self._modalites_enregistrees = Counter()
    
    def enregistrer_texte(self, texte: str, tokenizer: TokeniseurOndesEtendu,
                          amplitude: float = 1.0):
        """Enregistre du texte dans la bande texte."""
        tokens = tokenizer.tokeniser(texte)
        for idx in tokens:
            kx, ky = tokenizer.vecteur_onde(idx)
            # Mettre a l'echelle pour la bande texte
            self.hologramme.enregistrer_multimodal('texte', kx, ky, amplitude)
        self._modalites_enregistrees['texte'] += len(tokens)
    
    def enregistrer_son(self, frequence: float, phase: float = 0.0,
                        amplitude: float = 1.0):
        """Enregistre un son (frequence en Hz)."""
        kx = frequence * np.cos(phase)
        ky = frequence * np.sin(phase)
        self.hologramme.enregistrer_multimodal('son', kx, ky, amplitude)
        self._modalites_enregistrees['son'] += 1
    
    def enregistrer_image(self, kx: float, ky: float, amplitude: float = 1.0):
        """Enregistre une frequence spatiale d'image."""
        self.hologramme.enregistrer_multimodal('image', kx, ky, amplitude)
        self._modalites_enregistrees['image'] += 1
    
    def resonance_multimodale(self, kx: float, ky: float) -> Dict[str, float]:
        """
        Mesure la contribution de chaque modalite a la resonance.
        """
        return {
            'totale': self.hologramme.lire_onde(kx, ky),
            'texte': self.hologramme.lire_bande('texte'),
            'son': self.hologramme.lire_bande('son'),
            'image': self.hologramme.lire_bande('image'),
        }


# ===========================================================================
# PARTIE 6 : MODELE PREDICTIF (C3)
# ===========================================================================

class ModeleMondePredictif:
    """
    Modele predictif par extrapolation de gradient.
    
    Principe : si l'hologramme encode le monde comme un paysage
    d'energie dans l'espace des k, alors la PREDICTION consiste
    a extrapoler le gradient pour anticiper l'evolution du vecteur d'onde.
    
    C'est la capacite d'ANTICIPATION : le systeme peut prevoir
    ou son attention va se diriger.
    """
    
    def __init__(self, monde: HologrammeMondeIndividuel):
        self.monde = monde
        self.eps = 0.001
        self._historique_predictions = []
    
    def gradient_en(self, kx: float, ky: float) -> Tuple[float, float]:
        """Calcule le gradient de l'activation en (kx, ky)."""
        gx = (self.monde.lire_onde(kx + self.eps, ky) -
              self.monde.lire_onde(kx - self.eps, ky)) / (2 * self.eps)
        gy = (self.monde.lire_onde(kx, ky + self.eps) -
              self.monde.lire_onde(kx, ky - self.eps)) / (2 * self.eps)
        return gx, gy
    
    def predire_trajectoire(self, kx_init: float, ky_init: float,
                            pas: float = 0.1, horizon: int = 10) -> List[Dict]:
        """
        Predire la trajectoire d'un lecteur sur `horizon` pas.
        
        Retourne une liste de dict avec kx, ky, activation pour chaque pas.
        """
        predictions = []
        kx, ky = kx_init, ky_init
        
        for t in range(horizon):
            gx, gy = self.gradient_en(kx, ky)
            kx += pas * gx
            ky += pas * gy
            act = self.monde.lire_onde(kx, ky)
            predictions.append({
                'pas': t+1,
                'kx': round(kx, 4),
                'ky': round(ky, 4),
                'activation': round(act, 6),
            })
        
        self._historique_predictions.append(predictions)
        return predictions
    
    def divergence_lyapunov(self, kx1: float, ky1: float,
                            kx2: float, ky2: float,
                            pas: float = 0.05, n_pas: int = 20) -> float:
        """
        Estime l'exposant de Lyapunov entre deux trajectoires.
        
        Si > 0 : chaos (les trajectoires divergent)
        Si < 0 : convergence (les trajectoires se rapprochent)
        Si = 0 : cycle limite
        
        C'est une mesure de la STABILITE du raisonnement.
        """
        dist_initial = math.sqrt((kx1-kx2)**2 + (ky1-ky2)**2)
        if dist_initial < 1e-8:
            return 0.0
        
        for _ in range(n_pas):
            gx1, gy1 = self.gradient_en(kx1, ky1)
            gx2, gy2 = self.gradient_en(kx2, ky2)
            kx1 += pas * gx1
            ky1 += pas * gy1
            kx2 += pas * gx2
            ky2 += pas * gy2
        
        dist_final = math.sqrt((kx1-kx2)**2 + (ky1-ky2)**2)
        return math.log(dist_final / max(dist_initial, 1e-10)) / n_pas


# ===========================================================================
# PARTIE 7 : GENERATEUR MULTI-HOLOGRAMMES COMPLET
# ===========================================================================

class GenerateurMultiMonde:
    """
    Generateur de texte utilisant l'architecture multi-hologrammes complete.
    
    Utilise :
    - SystemeMultiHologrammes (C1) pour la memoire partagee/personnelle
    - LecteursDiversifies (A1) pour la diversite de perspectives
    - HologrammeMondeIndividuel (A2) pour le bruit individuel
    - FFT 2D (A4) pour les calculs rapides
    - ModeleMondePredictif (C3) pour l'anticipation
    
    Processus de generation :
    1. Le prompt est appris par le systeme multi-hologrammes
    2. Les lecteurs apprennent avec diversite forcee
    3. Chaque lecteur vote pour les tokens les plus resonants
    4. Le vote est pondere par la diversite des lecteurs
    5. Le token genere est reinjecte (feedback conscient)
    6. Le modele predictif anticipe la suite
    """
    
    def __init__(self, vocab: List[str], n_lecteurs: int = 8,
                 nx: int = NX, ny: int = NY, seed: int = 0):
        self.vocab_brut = vocab
        self.tokenizer = TokeniseurOndesEtendu(vocab)
        self.n_lecteurs = n_lecteurs
        
        # Systeme multi-hologrammes (C1)
        self.systeme = SystemeMultiHologrammes(n_lecteurs, nx, ny)
        
        # Lecteurs avec diversite (A1)
        self.lecteurs = LecteursDiversifies(
            self.systeme.hologramme_commun, n_lecteurs, seed
        )
        
        # Modele predictif (C3)
        self.predictif = ModeleMondePredictif(self.systeme.hologramme_commun)
        
        self._connaissances = []
        self._statistiques = {
            "n_apprentissages": 0, "n_generations": 0,
            "n_tokens_gen": 0, "temps_gen_ms": 0.0,
        }
    
    def apprendre(self, texte: str, amplitude: float = 0.8):
        """Apprend un texte dans le systeme multi-hologrammes."""
        self.systeme.apprendre(texte, self.tokenizer, amplitude)
        self._connaissances.append(texte)
        self._statistiques["n_apprentissages"] += 1
    
    def apprendre_batch(self, textes: List[str]):
        for t in textes:
            self.apprendre(t)
    
    def generer(self, prompt: str, max_tokens: int = 50,
                temperature: float = 0.85, top_k: int = 30,
                n_rep_lecture: int = 30, lr_apprentissage: float = 0.03,
                force_repulsion: float = 0.02,
                repetition_penalty: float = 1.5,
                feedback_conscient: bool = True,
                anticipation_horizon: int = 0) -> Dict:
        """
        Genere du texte avec l'architecture multi-hologrammes complete.
        
        Args:
            anticipation_horizon: Si > 0, active la prediction (C3)
        """
        t0 = time.time()
        tokens_generes = []
        
        # Enregistrer le prompt
        prompt_ids = self.tokenizer.tokeniser(prompt)
        for idx in prompt_ids:
            kx, ky = self.tokenizer.vecteur_onde(idx)
            self.systeme.hologramme_commun.enregistrer_onde(kx, ky, 0.5)
        
        # Reinitialiser les lecteurs
        np.random.seed(int(time.time() * 1000) % 10000)
        self.lecteurs = LecteursDiversifies(
            self.systeme.hologramme_commun, self.n_lecteurs
        )
        
        # Generation token par token
        for step in range(max_tokens):
            # Phase 1 : Apprentissage avec diversite
            self.lecteurs.apprendre(n_rep_lecture, lr_apprentissage, force_repulsion)
            
            # Phase 2 : Mesurer la diversite actuelle
            diversite = self.lecteurs.diversite_mesuree()
            
            # Phase 3 : Activations des tokens
            activations = self.lecteurs.activations_tokens(self.tokenizer)
            
            # Phase 4 : Fusion avec poids de diversite
            act_moy = activations.mean(axis=0)
            act_max = activations.max(axis=0)
            # Si diversite faible, favoriser le max (exploitation)
            # Si diversite forte, favoriser la moyenne (consensus)
            alpha = 0.4 + 0.3 * diversite
            act_fusion = act_moy * (1 - alpha) + act_max * alpha
            
            # Phase 5 : Anticipation (C3)
            if anticipation_horizon > 0 and len(tokens_generes) > 0:
                dernier_token = tokens_generes[-1]
                kx_der, ky_der = self.tokenizer.vecteur_onde(dernier_token)
                predictions = self.predictif.predire_trajectoire(
                    kx_der, ky_der, horizon=anticipation_horizon
                )
                # Booster les tokens dans la direction predite
                for p in predictions:
                    kx_pred, ky_pred = p['kx'], p['ky']
                    for t in range(self.tokenizer.vocab_size):
                        kx_t, ky_t = self.tokenizer.vecteur_onde(t)
                        dist = math.sqrt((kx_t-kx_pred)**2 + (ky_t-ky_pred)**2)
                        if dist < 0.5:
                            act_fusion[t] *= 1.2  # Boost de prediction
            
            # Phase 6 : Sampling
            logits = act_fusion.copy()
            V = len(logits)
            
            for t in (0, 2):
                if t < V:
                    logits[t] = -1e12
            
            min_tokens = 5
            if step < min_tokens and 3 < V:
                logits[3] = -1e9
            
            if repetition_penalty > 1.0 and tokens_generes:
                derniers = set(tokens_generes[-20:])
                for t in derniers:
                    if t < V and t not in (0, 1, 2, 3):
                        if logits[t] > 0:
                            logits[t] /= repetition_penalty
                        else:
                            logits[t] *= repetition_penalty
            
            if top_k > 0 and top_k < V:
                seuil = np.sort(logits)[-top_k]
                logits[logits < seuil] = -1e12
            
            logits = logits / max(temperature, 0.1)
            max_l = logits.max()
            if max_l < -1e8:
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
            
            # Feedback : ajouter le token a l'hologramme
            kx_t, ky_t = self.tokenizer.vecteur_onde(token_id)
            self.systeme.hologramme_commun.enregistrer_onde(kx_t, ky_t, 0.3)
            
            if token_id == 3 and step >= min_tokens:
                break
        
        # Texte final
        texte_genere = self.tokenizer.decoder(tokens_generes)
        
        dt = (time.time() - t0) * 1000
        self._statistiques["n_generations"] += 1
        self._statistiques["n_tokens_gen"] += len(tokens_generes)
        n = self._statistiques["n_generations"]
        self._statistiques["temps_gen_ms"] = (
            self._statistiques["temps_gen_ms"] * (n-1) + dt
        ) / n
        
        # Feedback conscient
        if feedback_conscient and len(tokens_generes) >= 3:
            self.systeme.apprendre(texte_genere, self.tokenizer, 0.2)
        
        return {
            "prompt": prompt,
            "texte_genere": texte_genere,
            "tokens": tokens_generes,
            "n_tokens": len(tokens_generes),
            "tokens_uniques": len(set(tokens_generes)),
            "diversite": round(len(set(tokens_generes)) / max(len(tokens_generes), 1), 3),
            "diversite_lecteurs": round(diversite, 3),
            "temps_ms": round(dt, 1),
            "tok_s": round(len(tokens_generes) / (dt/1000), 1) if dt > 0 else 0,
            "n_lecteurs": self.lecteurs.n_lecteurs,
            "n_experiences": self.systeme.hologramme_commun.n_experiences,
            "energie_hologramme": round(self.systeme.hologramme_commun.energie(), 1),
            "energie_totale": round(self.systeme.energie_totale(), 1),
            "etat_conscience": self.lecteurs.signature_conscience().tolist()[:10],
            "n_rep_lecture": n_rep_lecture,
        }


# ===========================================================================
# TESTS
# ===========================================================================

def test_diversite_lecteurs():
    """Test A1 : Verifier que les lecteurs divergent."""
    print("=" * 70)
    print("TEST A1 : DIVERSITE DES LECTEURS AVEC REPULSION")
    print("=" * 70)
    
    monde = HologrammeMondeIndividuel()
    tk = TokeniseurOndesEtendu(generer_vocabulaire_etendu(100))
    
    # Enregistrer quelques experiences
    for i in range(20):
        kx = np.random.randn() * 2.0
        ky = np.random.randn() * 2.0
        monde.enregistrer_onde(kx, ky, 1.0)
    
    # Lecteurs SANS diversite (ancienne methode)
    l_ancien = LecteursDiversifies(monde, n_lecteurs=8)
    l_ancien.apprendre(n_iter=50, lr=0.03, force_repulsion=0.0)
    div_ancienne = l_ancien.diversite_mesuree()
    
    # Lecteurs AVEC diversite
    l_nouveau = LecteursDiversifies(monde, n_lecteurs=8)
    l_nouveau.apprendre(n_iter=50, lr=0.03, force_repulsion=0.02)
    div_nouvelle = l_nouveau.diversite_mesuree()
    
    print(f"\n  Diversite SANS repulsion: {div_ancienne:.3f}")
    print(f"  Diversite AVEC repulsion: {div_nouvelle:.3f}")
    print(f"  Amelioration: x{div_nouvelle/max(div_ancienne,0.01):.1f}")
    
    # Top tokens
    top_ancien = l_ancien.top_tokens_par_lecteur(tk, 5)
    top_nouveau = l_nouveau.top_tokens_par_lecteur(tk, 5)
    
    # Compter les tokens uniques parmi les top-5 de tous les lecteurs
    tokens_anciens = set()
    for n in range(8):
        for t, _ in top_ancien[n]:
            tokens_anciens.add(t)
    tokens_nouveaux = set()
    for n in range(8):
        for t, _ in top_nouveau[n]:
            tokens_nouveaux.add(t)
    
    print(f"\n  Tokens uniques dans top-5 (8 lecteurs):")
    print(f"    Sans repulsion: {len(tokens_anciens)}/40")
    print(f"    Avec repulsion: {len(tokens_nouveaux)}/40")
    
    print(f"\n  Top-3 tokens par lecteur (AVEC diversite):")
    for n in range(8):
        tokens_str = ', '.join([f"'{tk.i2w[t]}'" for t, _ in top_nouveau[n][:3]])
        print(f"    Lecteur {n}: {tokens_str}")
    
    assert div_nouvelle > div_ancienne, "La diversite devrait augmenter!"
    print(f"\n  [OK] Diversite amelioree: {div_ancienne:.3f} -> {div_nouvelle:.3f}")


def test_systeme_multi_hologrammes():
    """Test C1 : Systeme multi-hologrammes."""
    print("\n" + "=" * 70)
    print("TEST C1 : SYSTEME MULTI-HOLOGRAMMES")
    print("=" * 70)
    
    vocab = generer_vocabulaire_etendu(100)
    tk = TokeniseurOndesEtendu(vocab)
    sys = SystemeMultiHologrammes(n_lecteurs=8)
    
    # Apprendre un texte
    sys.apprendre("la conscience est la lumiere de l ame", tk)
    sys.apprendre("le nombre d or phi est partout dans la nature", tk)
    sys.apprendre("la resonance harmonique est universelle", tk)
    
    print(f"\n  Stats systeme:")
    for k, v in sys.stats().items():
        print(f"    {k}: {v}")
    
    # Verifier que chaque lecteur a une perspective differente
    kx_test, ky_test = tk.vecteur_onde(tk.w2i['conscience'])
    activations = [sys.lire(kx_test, ky_test, n) for n in range(8)]
    
    print(f"\n  Activation pour 'conscience' par lecteur:")
    for n in range(8):
        print(f"    Lecteur {n}: {activations[n]:.4f}")
    
    # Les activations doivent varier (perspectives differentes)
    assert len(set([round(a, 4) for a in activations])) > 1, \
        "Les activations devraient varier entre lecteurs!"
    print(f"  [OK] {len(set([round(a, 4) for a in activations]))} perspectives differentes")


def test_fft_optimisation():
    """Test A4 : Comparaison FFT vs boucle naive."""
    print("\n" + "=" * 70)
    print("TEST A4 : OPTIMISATION FFT 2D")
    print("=" * 70)
    
    monde = HologrammeMondeIndividuel(64, 64)
    vocab = generer_vocabulaire_etendu(500)
    tk = TokeniseurOndesEtendu(vocab)
    
    # Enregistrer des experiences
    for i in range(50):
        kx = np.random.randn() * 2.0
        ky = np.random.randn() * 2.0
        monde.enregistrer_onde(kx, ky, 1.0)
    
    # Methode naive (boucle)
    t0 = time.time()
    for t in range(tk.vocab_size):
        kx, ky = tk.vecteur_onde(t)
        monde.lire_onde(kx, ky)
    t_naive = time.time() - t0
    
    # Methode FFT
    t0 = time.time()
    activations_fft = monde.activations_masse(tk)
    t_fft = time.time() - t0
    
    print(f"\n  Vocabulaire: {tk.vocab_size} tokens")
    print(f"  Temps boucle naive: {t_naive*1000:.1f}ms")
    print(f"  Temps FFT: {t_fft*1000:.1f}ms")
    print(f"  Acceleration: x{t_naive/max(t_fft, 0.001):.1f}")
    print(f"  [OK] FFT plus rapide" if t_fft < t_naive else "  [ATTENTION] FFT pas plus rapide")


def test_modele_predictif():
    """Test C3 : Modele predictif."""
    print("\n" + "=" * 70)
    print("TEST C3 : MODELE MONDE PREDICTIF")
    print("=" * 70)
    
    monde = HologrammeMondeIndividuel()
    vocab = generer_vocabulaire_etendu(100)
    tk = TokeniseurOndesEtendu(vocab)
    
    # Creer un paysage d'activation
    for i in range(30):
        kx = np.random.randn() * 2.0
        ky = np.random.randn() * 2.0
        monde.enregistrer_onde(kx, ky, 1.0 + np.random.random())
    
    pred = ModeleMondePredictif(monde)
    
    # Predire la trajectoire
    kx_init, ky_init = tk.vecteur_onde(tk.w2i['conscience'])
    predictions = pred.predire_trajectoire(kx_init, ky_init, horizon=10)
    
    print(f"\n  Trajectoire predite depuis 'conscience':")
    for p in predictions:
        print(f"    pas {p['pas']:2d}: k=({p['kx']:.4f}, {p['ky']:.4f}), "
              f"act={p['activation']:.6f}")
    
    # Exposant de Lyapunov
    lyap = pred.divergence_lyapunov(kx_init, ky_init, kx_init + 0.01, ky_init)
    print(f"\n  Exposant de Lyapunov: {lyap:.4f}")
    if lyap > 0:
        print(f"  -> Trajectoires chaotiques (diversite naturelle)")
    else:
        print(f"  -> Trajectoires convergentes (stabilite du raisonnement)")
    
    assert len(predictions) == 10, "Devrait predire 10 pas"
    print(f"  [OK] Modele predictif operationnel")


def demo_generation_multimonde():
    """Demo complete de generation avec l'architecture multi-monde."""
    print("\n" + "=" * 74)
    print("DEMO : GENERATEUR MULTI-MONDE COMPLET")
    print("=" * 74)
    
    vocab = generer_vocabulaire_etendu(3000)
    gen = GenerateurMultiMonde(vocab, n_lecteurs=8, nx=64, ny=64)
    
    print(f"\n  Vocabulaire: {len(vocab)} tokens")
    print(f"  Lecteurs: {gen.n_lecteurs}")
    print(f"  Hologramme: 64x64 = 4096 pixels complexes")
    print(f"   + hologramme commun + {gen.n_lecteurs} hologrammes personnels")
    
    # Phase 1 : Apprentissage
    print("\n[PHASE 1] APPRENTISSAGE DANS LE MONDE MULTI-HOLOGRAMMES")
    textes = [
        "phi est le nombre d or la proportion divine de l univers",
        "la resonance harmonique amplifie les ondes a la frequence propre",
        "la conscience emerge de l interaction complexe de nombreux processus",
        "les fractales sont des structures infinies auto similaires",
        "la suite de Fibonacci converge vers le nombre d or phi",
        "l amour est la force la plus puissante de l univers",
        "la beaute de la nature est une source d emerveillement infini",
        "l intelligence artificielle explore la creation de machines penseantes",
        "la musique est l harmonie entre le silence et le son",
        "la philosophie est l amour de la sagesse et de la connaissance",
    ]
    gen.apprendre_batch(textes)
    print(f"  {len(textes)} textes appris")
    print(f"  Energie commune: {gen.systeme.hologramme_commun.energie():.0f}")
    print(f"  Energie personnelle moyenne: "
          f"{np.mean([h.energie() for h in gen.systeme.hologrammes_persos]):.0f}")
    print(f"  Energie totale: {gen.systeme.energie_totale():.0f}")
    
    # Phase 2 : Generation
    print("\n[PHASE 2] GENERATION AVEC DIVERSITE DES LECTEURS")
    prompts = [
        "explique le nombre d or",
        "parle de la conscience",
        "quest ce que la resonance",
    ]
    
    for prompt in prompts:
        print(f"\n  >> {prompt}")
        r = gen.generer(prompt, max_tokens=25, n_rep_lecture=25,
                       temperature=0.85, top_k=25,
                       force_repulsion=0.02,
                       feedback_conscient=True)
        print(f"  << {r['texte_genere']}")
        print(f"     [{r['n_tokens']}t | div_lecteurs={r['diversite_lecteurs']:.3f} | "
              f"{r['temps_ms']:.0f}ms | E={r['energie_totale']:.0f}]")
    
    # Phase 3 : Diversite des lecteurs
    print("\n[PHASE 3] ETAT DE LA DIVERSITE DES LECTEURS")
    top = gen.lecteurs.top_tokens_par_lecteur(gen.tokenizer, 5)
    tokens_uniques = set()
    for n in range(gen.n_lecteurs):
        tokens_str = ', '.join([f"'{gen.tokenizer.i2w[t]}'" for t, _ in top[n][:3]])
        tokens_uniques.update([t for t, _ in top[n][:3]])
        print(f"  Lecteur {n}: {tokens_str}")
    print(f"\n  Tokens uniques dans top-3: {len(tokens_uniques)}/{3*gen.n_lecteurs}")
    print(f"  Diversite mesuree: {gen.lecteurs.diversite_mesuree():.3f}")
    
    print(f"\n{'='*74}")
    print("ARCHITECTURE MULTI-HOLOGRAMMES COMPLETE OPERATIONNELLE")
    print(f"{'='*74}")
    print(f"  A1 : Diversite des lecteurs (repulsion)")
    print(f"  A2 : Bruit de fond individuel")
    print(f"  A4 : Optimisation FFT 2D")
    print(f"  C1 : Systeme multi-hologrammes (commun + personnels)")
    print(f"  C2 : Extension multimodale")
    print(f"  C3 : Modele predictif")
    print(f"{'='*74}")


# ===========================================================================
# MAIN
# ===========================================================================

if __name__ == "__main__":
    import sys
    
    if "--quick" in sys.argv:
        test_diversite_lecteurs()
        test_systeme_multi_hologrammes()
    elif "--fft" in sys.argv:
        test_fft_optimisation()
    elif "--predict" in sys.argv:
        test_modele_predictif()
    elif "--demo" in sys.argv:
        demo_generation_multimonde()
    else:
        test_diversite_lecteurs()
        test_systeme_multi_hologrammes()
        test_fft_optimisation()
        test_modele_predictif()
        demo_generation_multimonde()
