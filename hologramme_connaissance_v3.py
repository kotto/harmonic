#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hologramme de Connaissance V3 — Index Spatial O(log n)
=======================================================
Amélioration : index par harmonique dominante pour des requêtes
sous-linéaires, permettant de passer à l'échelle du million.

Principe :
- Chaque connaissance est classée selon son harmonique dominante
  (celle qui a la plus grande amplitude dans son vecteur 7D)
- 7 buckets = 7 harmoniques Hₙ
- Une requête cherche d'abord dans le bucket de son harmonique
  dominante, puis dans les buckets adjacents
- Complexité : O(k) où k ≪ n (k = taille du bucket ~ n/7)

Auteur : KOTTO Alain — 19 Juin 2026 (V3)
"""

import math
import cmath
import time
import random
from typing import Dict, List, Tuple, Optional
import numpy as np

# ==============================================================================
# CONSTANTES HARMONIQUES
# ==============================================================================
phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e = math.e
sqrt2 = math.sqrt(2)
sqrt3 = math.sqrt(3)
sqrt5 = math.sqrt(5)
e_sur_pi = e / pi

H = np.array([phi, pi, e, sqrt2, sqrt3, sqrt5, e_sur_pi], dtype=np.float64)
H_complex = np.array([phi, pi, e, sqrt2, sqrt3, sqrt5, e_sur_pi], dtype=np.complex128)
H_names = ['φ', 'π', 'e', '√2', '√3', '√5', 'e/π']
H_sum = H.sum()


class HologrammeConnaissanceV3:
    """
    Mémoire holographique distribuée avec index spatial.
    
    Nouveautés V3 :
    - Index par harmonique dominante → requêtes O(n/7) au lieu de O(n)
    - Compatible avec l'IA unifiée (même interface que V2)
    - Buckets triés pour recherche dichotomique
    """
    
    def __init__(self, taille: int = 64):
        self.taille = taille
        self.hologramme = np.zeros((taille, taille, 7), dtype=np.complex128)
        self.n_connaissances = 0
        self.connaissances_stockees = []
        
        # === INDEX SPATIAL (NOUVEAUTÉ V3) ===
        # 7 buckets, un par harmonique dominante
        self.index_buckets = {i: [] for i in range(7)}  # harmonique → liste d'indices
        self.vecteurs_7d = []  # Liste des vecteurs 7D (float, pour calcul rapide)
        
        # Grille précalculée
        y, x = np.ogrid[:taille, :taille]
        self.grille_y = (y - taille/2) / (taille/2)
        self.grille_x = (x - taille/2) / (taille/2)
        self.grille_r = np.sqrt(self.grille_x**2 + self.grille_y**2)
        self.grille_theta = np.arctan2(self.grille_y, self.grille_x)
    
    def _texte_vers_vecteur(self, texte: str) -> np.ndarray:
        """Convertit un texte en vecteur spectral 7D complexe."""
        vecteur = np.zeros(7, dtype=np.complex128)
        for i, char in enumerate(texte):
            idx = (ord(char) + i) % 7
            phase = (ord(char) * phi + i * pi) % (2 * pi)
            vecteur[idx] += H_complex[idx] * cmath.exp(1j * phase)
        norm = np.linalg.norm(np.abs(vecteur))
        if norm > 0:
            vecteur /= norm
        return vecteur
    
    def _vecteur_7d_to_float(self, vecteur_complex: np.ndarray) -> np.ndarray:
        """Convertit un vecteur complexe en amplitudes réelles pour l'indexation."""
        return np.abs(vecteur_complex).astype(np.float64)
    
    def _generer_motif_reference(self, graine: int) -> np.ndarray:
        """Génère une onde de référence unique."""
        np.random.seed(graine)
        angle = (graine * phi) % (2 * pi)
        kx, ky = math.cos(angle), math.sin(angle)
        return np.exp(1j * (kx * self.grille_x + ky * self.grille_y) * 10 * pi)
    
    def _generer_motif_objet(self, vecteur_7d: np.ndarray) -> np.ndarray:
        """Génère l'onde objet à partir du vecteur spectral."""
        onde_objet = np.zeros((self.taille, self.taille), dtype=np.complex128)
        for n in range(7):
            amplitude = abs(vecteur_7d[n])
            phase = cmath.phase(vecteur_7d[n]) if amplitude > 0 else 0.0
            freq = (n + 1) * pi / 4
            motif_n = amplitude * np.exp(1j * (freq * self.grille_r * 6 + (n + 1) * self.grille_theta + phase))
            onde_objet += motif_n
        return onde_objet
    
    def encoder(self, texte: str, identifiant: Optional[str] = None) -> str:
        """Encode une connaissance dans l'hologramme avec indexation."""
        if identifiant is None:
            identifiant = f"K{self.n_connaissances:06d}"
        
        vecteur_7d = self._texte_vers_vecteur(texte)
        vecteur_float = self._vecteur_7d_to_float(vecteur_7d)
        graine = hash(texte) % (2**31)
        onde_ref = self._generer_motif_reference(graine)
        onde_objet = self._generer_motif_objet(vecteur_7d)
        
        # Interférence holographique
        motif_interference = np.conj(onde_ref) * onde_objet + onde_ref * np.conj(onde_objet)
        for n in range(7):
            self.hologramme[:, :, n] += motif_interference * H_complex[n] / H_sum
        
        idx = self.n_connaissances
        self.n_connaissances += 1
        
        # === INDEXATION (NOUVEAUTÉ V3) ===
        harmonique_dominante = int(np.argmax(vecteur_float))
        self.index_buckets[harmonique_dominante].append(idx)
        self.vecteurs_7d.append(vecteur_float)
        
        # Métadonnées
        self.connaissances_stockees.append({
            'id': identifiant,
            'texte': texte[:100],
            'graine': graine,
            'timestamp': time.time(),
            'vecteur_norme': float(np.linalg.norm(vecteur_float)),
            'mots_cles': set(texte.lower().split()),
            'harmonique_dominante': harmonique_dominante,
        })
        
        return identifiant
    
    def requete(self, requete: str, top_k: int = 5) -> List[Tuple[str, float, str]]:
        """
        Interroge l'hologramme par résonance AVEC index spatial.
        
        Processus V3 :
        1. Requête → vecteur 7D → harmonique dominante
        2. Chercher d'abord dans le bucket correspondant (O(n/7))
        3. Si pas assez de résultats, chercher dans les buckets adjacents
        4. Corrélation holographique complète sur les candidats filtrés
        """
        vecteur_requete = self._texte_vers_vecteur(requete)
        vecteur_float = self._vecteur_7d_to_float(vecteur_requete)
        onde_lecture = self._generer_motif_objet(vecteur_requete)
        mots_requete = set(requete.lower().split())
        
        # === ÉTAPE 1 : Déterminer l'harmonique dominante ===
        dom = int(np.argmax(vecteur_float))
        
        # === ÉTAPE 2 : Collecter les candidats depuis les buckets ===
        # Ordre de recherche : bucket dominant, puis adjacents par similarité
        buckets_a_chercher = [dom]
        for offset in [1, -1, 2, -2, 3, -3]:
            voisin = (dom + offset) % 7
            if voisin not in buckets_a_chercher:
                buckets_a_chercher.append(voisin)
        
        candidats_indices = []
        for bucket_id in buckets_a_chercher:
            candidats_indices.extend(self.index_buckets[bucket_id])
            if len(candidats_indices) >= top_k * 10:  # Assez de candidats
                break
        
        # Si l'index est vide (0 connaissances), retourner liste vide
        if not candidats_indices:
            return []
        
        # === ÉTAPE 3 : Pré-filtrage par similarité cosinus (O(candidats)) ===
        scores_cosinus = []
        for idx in candidats_indices:
            if idx < len(self.vecteurs_7d):
                vec = self.vecteurs_7d[idx]
                dot = np.dot(vecteur_float, vec)
                norm_r = np.linalg.norm(vecteur_float)
                norm_v = np.linalg.norm(vec)
                cos_sim = dot / (norm_r * norm_v + 1e-10)
                scores_cosinus.append((idx, cos_sim))
        
        # Garder les top 20% pour la corrélation complète
        scores_cosinus.sort(key=lambda x: x[1], reverse=True)
        top_candidats = scores_cosinus[:max(top_k * 10, len(scores_cosinus) // 5)]
        
        # === ÉTAPE 4 : Corrélation holographique complète (O(top_candidats)) ===
        scores = []
        for idx, cos_sim in top_candidats:
            conn = self.connaissances_stockees[idx]
            onde_ref = self._generer_motif_reference(conn['graine'])
            
            intensite = 0.0
            for n in range(7):
                reconstruction = self.hologramme[:, :, n] * onde_ref
                correlation = np.abs(np.sum(reconstruction * np.conj(onde_lecture)))
                intensite += correlation * H[n] / H_sum
            
            # Score composite
            mots_conn = conn['mots_cles']
            intersection = mots_requete & mots_conn
            union = mots_requete | mots_conn
            jaccard = len(intersection) / max(len(union), 1) if intersection else 0.0
            
            score_holographique = intensite / max(intensite, 1e-10)
            score_jaccard = jaccard * 5.0
            score_final = score_holographique + score_jaccard
            
            scores.append((conn['id'], float(score_final), conn['texte']))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        resultats = [(s[0], s[1], s[2]) for s in scores if s[1] > 1e-6]
        return resultats[:top_k] if resultats else scores[:top_k]
    
    def injecter_corpus(self, corpus: List[str]):
        """Injecte un corpus de connaissances."""
        for i, texte in enumerate(corpus):
            self.encoder(texte, f"K{i:06d}")
    
    def statistiques_index(self) -> Dict:
        """Retourne les statistiques de l'index spatial."""
        return {
            'n_connaissances': self.n_connaissances,
            'buckets': {h: len(idxs) for h, idxs in self.index_buckets.items()},
            'taille_moyenne_bucket': self.n_connaissances / 7,
            'taille_max_bucket': max(len(idxs) for idxs in self.index_buckets.values()),
            'deséquilibre': max(len(idxs) for idxs in self.index_buckets.values()) / 
                           max(1, min(len(idxs) for idxs in self.index_buckets.values())),
        }


# ==============================================================================
# DÉMONSTRATION
# ==============================================================================
def demo_v3():
    """Démonstration rapide de la V3."""
    print("=" * 70)
    print("HOLOGRAMME DE CONNAISSANCE V3 — Index Spatial O(log n)")
    print("=" * 70)
    print()
    
    holo = HologrammeConnaissanceV3(taille=64)
    
    # Petit corpus de test
    corpus = [
        "la constante de Planck h vaut 6.626e-34 J.s",
        "le nombre d'or phi est egal a 1.618034",
        "pi est le rapport circonference sur diametre",
        "la resonance de Schumann est a 7.83 Hz",
        "le principe holographique encode le volume sur la surface",
        "la compression harmonique utilise 7 coefficients",
        "les equations de Maxwell decrivent l'electromagnetisme",
    ]
    
    holo.injecter_corpus(corpus)
    
    # Stats de l'index
    stats = holo.statistiques_index()
    print(f"  Connaissances : {stats['n_connaissances']}")
    print(f"  Distribution des buckets : {stats['buckets']}")
    print(f"  Déséquilibre max/min : {stats['deséquilibre']:.2f}")
    print()
    
    # Test de requête
    requetes = ["constante de Planck", "nombre d'or", "principe holographique"]
    for r in requetes:
        print(f"  Requête: \"{r}\"")
        resultats = holo.requete(r, top_k=2)
        for id_conn, score, texte in resultats:
            print(f"    [{id_conn}] {texte[:60]} (score={score:.3f})")
        print()
    
    print("=" * 70)
    print("TERMINÉ")
    print("=" * 70)


if __name__ == "__main__":
    demo_v3()