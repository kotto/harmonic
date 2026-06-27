#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hologramme de Connaissance V4 — LSH O(1) + Benchmark 1M
========================================================
Locality-Sensitive Hashing sur les signatures 7D pour
des requêtes en O(1) approximatif.

Principe LSH :
- N_hyperplans hyperplans aléatoires (vecteurs 7D)
- Chaque signature 7D → hash binaire de N_hyperplans bits
- Connaissances regroupées par hash
- Requête : hash → bucket → corrélation holographique
- Complexité : O(1) en moyenne (taille bucket ~ n/2^N_hyperplans)

Ajout d'un benchmark sur 1M de connaissances synthétiques.

Auteur : KOTTO Alain — 19 Juin 2026 (V4)
"""

import math
import cmath
import time
import random
import sys
import os
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

# ==============================================================================
# LSH INDEX
# ==============================================================================

class LSHIndex:
    """
    Locality-Sensitive Hashing pour vecteurs 7D.
    
    Utilise N_hyperplans hyperplans aléatoires pour projeter
    les signatures 7D en hash binaires. Les signatures similaires
    ont une forte probabilité d'avoir le même hash.
    """
    
    def __init__(self, n_hyperplans: int = 14, n_tables: int = 3):
        """
        Args:
            n_hyperplans : nombre d'hyperplans par table (14 → 2^14 = 16384 buckets)
            n_tables : nombre de tables de hachage indépendantes
        """
        self.n_hyperplans = n_hyperplans
        self.n_tables = n_tables
        
        # Générer les hyperplans aléatoires pour chaque table
        self.hyperplans = []
        for t in range(n_tables):
            # Matrice (n_hyperplans × 7) de normales aléatoires
            hp = np.random.randn(n_hyperplans, 7).astype(np.float64)
            # Normaliser chaque hyperplan
            for i in range(n_hyperplans):
                norm = np.linalg.norm(hp[i])
                if norm > 0:
                    hp[i] /= norm
            self.hyperplans.append(hp)
        
        # Tables de hachage : hash → liste d'indices
        self.tables = [{} for _ in range(n_tables)]
        
        # Seuils (bias) pour la randomisation
        self.seuils = [np.random.uniform(-1, 1, n_hyperplans) for _ in range(n_tables)]
    
    def hash_vecteur(self, vecteur: np.ndarray, table_id: int) -> int:
        """
        Calcule le hash LSH d'un vecteur pour une table donnée.
        
        Pour chaque hyperplan, signe(produit_scalaire - seuil) → bit.
        Résultat : entier de n_hyperplans bits.
        """
        hp = self.hyperplans[table_id]
        seuils = self.seuils[table_id]
        
        # Produit scalaire avec tous les hyperplans
        projections = hp @ vecteur  # (n_hyperplans,)
        
        # Signe : 1 si projection > seuil, 0 sinon
        bits = (projections > seuils).astype(np.int32)
        
        # Convertir en entier
        hash_val = 0
        for i in range(self.n_hyperplans):
            if bits[i]:
                hash_val |= (1 << i)
        
        return hash_val
    
    def inserer(self, idx: int, vecteur: np.ndarray):
        """Insère un indice dans les tables LSH."""
        for t in range(self.n_tables):
            h = self.hash_vecteur(vecteur, t)
            if h not in self.tables[t]:
                self.tables[t][h] = []
            self.tables[t][h].append(idx)
    
    def rechercher(self, vecteur: np.ndarray, max_candidats: int = 200) -> List[int]:
        """
        Recherche les candidats par LSH.
        
        Récupère l'union des buckets correspondant au hash
        de la requête dans chaque table.
        """
        candidats_set = set()
        for t in range(self.n_tables):
            h = self.hash_vecteur(vecteur, t)
            if h in self.tables[t]:
                candidats_set.update(self.tables[t][h])
                if len(candidats_set) >= max_candidats:
                    break
        
        return list(candidats_set)[:max_candidats]
    
    def statistiques(self) -> Dict:
        """Statistiques de l'index LSH."""
        stats = {}
        for t in range(self.n_tables):
            buckets = self.tables[t]
            tailles = [len(b) for b in buckets.values()]
            stats[f'table_{t}'] = {
                'n_buckets': len(buckets),
                'taille_moyenne': np.mean(tailles) if tailles else 0,
                'taille_max': max(tailles) if tailles else 0,
                'taux_remplissage': len(buckets) / (2**self.n_hyperplans),
            }
        return stats


# ==============================================================================
# HOLOGRAMME V4 AVEC LSH
# ==============================================================================

class HologrammeConnaissanceV4:
    """
    Hologramme avec index LSH pour requêtes O(1).
    
    Mêmes capacités que V2/V3 + index LSH pour le scaling.
    """
    
    def __init__(self, taille: int = 128, n_hyperplans_lsh: int = 14):
        self.taille = taille
        self.hologramme = np.zeros((taille, taille, 7), dtype=np.complex128)
        self.n_connaissances = 0
        self.connaissances_stockees = []
        
        # LSH Index
        self.lsh = LSHIndex(n_hyperplans=n_hyperplans_lsh, n_tables=3)
        self.vecteurs_7d = []
        
        # Grille précalculée
        y, x = np.ogrid[:taille, :taille]
        self.grille_y = (y - taille/2) / (taille/2)
        self.grille_x = (x - taille/2) / (taille/2)
        self.grille_r = np.sqrt(self.grille_x**2 + self.grille_y**2)
        self.grille_theta = np.arctan2(self.grille_y, self.grille_x)
    
    def _texte_vers_vecteur(self, texte: str) -> np.ndarray:
        vecteur = np.zeros(7, dtype=np.complex128)
        for i, char in enumerate(texte):
            idx = (ord(char) + i) % 7
            phase = (ord(char) * phi + i * pi) % (2 * pi)
            vecteur[idx] += H_complex[idx] * cmath.exp(1j * phase)
        norm = np.linalg.norm(np.abs(vecteur))
        if norm > 0:
            vecteur /= norm
        return vecteur
    
    def _vecteur_vers_float(self, vc: np.ndarray) -> np.ndarray:
        return np.abs(vc).astype(np.float64)
    
    def _generer_motif_reference(self, graine: int) -> np.ndarray:
        np.random.seed(graine)
        angle = (graine * phi) % (2 * pi)
        kx, ky = math.cos(angle), math.sin(angle)
        return np.exp(1j * (kx * self.grille_x + ky * self.grille_y) * 10 * pi)
    
    def _generer_motif_objet(self, v: np.ndarray) -> np.ndarray:
        onde = np.zeros((self.taille, self.taille), dtype=np.complex128)
        for n in range(7):
            amp = abs(v[n])
            ph = cmath.phase(v[n]) if amp > 0 else 0.0
            freq = (n + 1) * pi / 4
            onde += amp * np.exp(1j * (freq * self.grille_r * 6 + (n+1) * self.grille_theta + ph))
        return onde
    
    def encoder(self, texte: str, identifiant: Optional[str] = None) -> str:
        if identifiant is None:
            identifiant = f"K{self.n_connaissances:08d}"
        
        v = self._texte_vers_vecteur(texte)
        vf = self._vecteur_vers_float(v)
        graine = hash(texte) % (2**31)
        
        # Interférence holographique
        onde_ref = self._generer_motif_reference(graine)
        onde_obj = self._generer_motif_objet(v)
        motif = np.conj(onde_ref) * onde_obj + onde_ref * np.conj(onde_obj)
        for n in range(7):
            self.hologramme[:, :, n] += motif * H_complex[n] / H_sum
        
        idx = self.n_connaissances
        self.n_connaissances += 1
        
        # === INDEXATION LSH ===
        self.lsh.inserer(idx, vf)
        self.vecteurs_7d.append(vf)
        
        self.connaissances_stockees.append({
            'id': identifiant, 'texte': texte[:100],
            'graine': graine, 'timestamp': time.time(),
            'vecteur_norme': float(np.linalg.norm(vf)),
            'mots_cles': set(texte.lower().split()),
        })
        return identifiant
    
    def requete(self, requete: str, top_k: int = 5) -> List[Tuple[str, float, str]]:
        """
        Requête O(1) via LSH.
        
        1. Hash LSH de la requête → candidats
        2. Corrélation holographique sur les candidats
        """
        v = self._texte_vers_vecteur(requete)
        vf = self._vecteur_vers_float(v)
        onde_lecture = self._generer_motif_objet(v)
        mots_requete = set(requete.lower().split())
        
        # === ÉTAPE 1 : LSH → candidats O(1) ===
        candidats = self.lsh.rechercher(vf, max_candidats=500)
        
        if not candidats:
            return []
        
        # === ÉTAPE 2 : Corrélation holographique ===
        scores = []
        for idx in candidats:
            if idx >= len(self.connaissances_stockees):
                continue
            conn = self.connaissances_stockees[idx]
            onde_ref = self._generer_motif_reference(conn['graine'])
            
            intensite = 0.0
            for n in range(7):
                reconstruction = self.hologramme[:, :, n] * onde_ref
                correlation = np.abs(np.sum(reconstruction * np.conj(onde_lecture)))
                intensite += correlation * H[n] / H_sum
            
            mots_conn = conn['mots_cles']
            intersection = mots_requete & mots_conn
            union = mots_requete | mots_conn
            jaccard = len(intersection) / max(len(union), 1) if intersection else 0.0
            
            score = intensite / max(intensite, 1e-10) + jaccard * 5.0
            scores.append((conn['id'], float(score), conn['texte']))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return [(s[0], s[1], s[2]) for s in scores[:top_k] if s[1] > 1e-6]
    
    def injecter_corpus(self, corpus: List[str]):
        for i, texte in enumerate(corpus):
            self.encoder(texte, f"K{i:08d}")
    
    def stats(self) -> Dict:
        lsh_stats = self.lsh.statistiques()
        return {
            'n_connaissances': self.n_connaissances,
            'lsh': lsh_stats,
            'memoire_mo': self.hologramme.nbytes / (1024*1024),
        }


# ==============================================================================
# GÉNÉRATION DE CORPUS MASSIF
# ==============================================================================
def generer_corpus_1M(n: int) -> List[str]:
    """Génère un corpus synthétique de n connaissances uniques."""
    templates = [
        "la constante physique numero {i} a pour valeur {v:.6e}",
        "le parametre mathematique {i} est egal a {v:.6f}",
        "le concept harmonique {i} est lie a la constante {c}",
        "l'equation {i} de la theorie harmonique predit {v:.4f}",
        "la propriete holographique {i} concerne la surface de rayon R{i}",
        "le coefficient spectral H{i} est associe au phenomene {i}",
        "la mesure experimentale {i} confirme la prediction {v:.3f}",
        "le fait scientifique {i} est etabli par l'experience {i}",
        "la connaissance {i} est encodee dans l'hologramme de taille T{i}",
        "l'information numero {i} est stockee de maniere distribuee",
    ]
    
    corpus = []
    for i in range(n):
        tmpl = templates[i % len(templates)]
        v = (i * phi) % 1000
        c = H_names[i % 7]
        texte = tmpl.format(i=i, v=v, c=c)
        corpus.append(texte)
    
    return corpus


# ==============================================================================
# BENCHMARK 1M
# ==============================================================================
def benchmark_1M():
    """Benchmark de la V4 avec 1 million de connaissances."""
    print("=" * 80)
    print("BENCHMARK 1M — Hologramme V4 avec LSH O(1)")
    print("=" * 80)
    print()
    
    # Créer l'hologramme
    print("Création de l'hologramme 256×256×7...")
    debut = time.time()
    holo = HologrammeConnaissanceV4(taille=256, n_hyperplans_lsh=14)
    print(f"  Taille : 256×256×7 = {256**2*7:,} cellules")
    print(f"  Mémoire : {holo.hologramme.nbytes / (1024*1024):.1f} Mo")
    print(f"  LSH : 14 hyperplans × 3 tables = {2**14:,} buckets/table")
    print()
    
    # Générer le corpus
    print("Génération du corpus 1M...")
    corpus = generer_corpus_1M(1_000_000)
    print(f"  {len(corpus):,} connaissances générées")
    print()
    
    # Injection par lots de 200k
    print("Injection progressive :")
    print(f"  {'Connaissances':>15s}  {'Temps (s)':>10s}  {'Energie':>12s}  {'Saturation':>11s}  {'µs/conn':>10s}")
    print(f"  {'-'*15}  {'-'*10}  {'-'*12}  {'-'*11}  {'-'*10}")
    
    lots = [100_000, 250_000, 500_000, 750_000, 1_000_000]
    dernier = 0
    
    for n_total in lots:
        debut_lot = time.time()
        for i in range(dernier, n_total):
            holo.encoder(corpus[i])
        duree = time.time() - debut_lot
        
        n_ajoutes = n_total - dernier
        us = (duree / n_ajoutes) * 1e6
        
        energie = float(np.sum(np.abs(holo.hologramme)**2))
        saturation = float(np.max(np.abs(holo.hologramme)))
        
        print(f"  {n_total:>15,d}  {duree:>9.1f}s  {energie:>12.2e}  {saturation:>11.2f}  {us:>9.1f}")
        dernier = n_total
    
    duree_totale = time.time() - debut
    print()
    print(f"  Temps total d'injection : {duree_totale:.1f}s")
    print(f"  Connaissances injectées : {holo.n_connaissances:,}")
    print()
    
    # Statistiques LSH
    stats = holo.stats()
    print("  Statistiques LSH :")
    for t_name, t_stats in stats['lsh'].items():
        print(f"    {t_name} : {t_stats['n_buckets']:,} buckets, "
              f"taille moyenne {t_stats['taille_moyenne']:.1f}, "
              f"max {t_stats['taille_max']:,}, "
              f"remplissage {t_stats['taux_remplissage']*100:.1f}%")
    print()
    
    # Test de requêtes
    print("  Test de requêtes O(1) :")
    print()
    
    requetes_test = [
        "constante physique 42",
        "parametre mathematique 100",
        "concept harmonique 500",
        "propriete holographique 1000",
        "coefficient spectral 777",
    ]
    
    for req in requetes_test:
        debut = time.time()
        resultats = holo.requete(req, top_k=2)
        duree = (time.time() - debut) * 1000  # ms
        
        if resultats:
            best = resultats[0]
            print(f"  Q: \"{req}\"")
            print(f"  R: [{best[0]}] {best[2][:60]}")
            print(f"     score={best[1]:.3f}  temps={duree:.2f}ms")
        else:
            print(f"  Q: \"{req}\" → aucun résultat (temps={duree:.2f}ms)")
        print()
    
    print("=" * 80)
    print("TERMINÉ")
    print("=" * 80)


# ==============================================================================
# EXÉCUTION
# ==============================================================================
if __name__ == "__main__":
    benchmark_1M()