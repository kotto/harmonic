#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hologramme de Connaissance Harmono-Holographique
=================================================
Implémentation d'une mémoire holographique distribuée basée sur
Ψ = Σ Hₙ · fⁿ et le principe holographique.

Principe :
- La connaissance n'est pas stockée dans des cases séparées
- Chaque connaissance est une interférence d'ondes superposée
  dans une matrice holographique 64×64×7
- La requête agit comme une "onde de lecture" qui fait résonner
  les motifs pertinents
- L'information est distribuée : chaque cellule contient un fragment
  de TOUTES les connaissances (propriété holographique)
- Dégradation progressive (pas catastrophique)
- Oubli naturel par atténuation exponentielle

Auteur : KOTTO Alain — 19 Juin 2026
"""

import math
import cmath
import time
import random
from typing import Dict, List, Tuple, Optional, Any
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

H = np.array([phi, pi, e, sqrt2, sqrt3, sqrt5, e_sur_pi], dtype=np.complex128)
H_names = ['φ', 'π', 'e', '√2', '√3', '√5', 'e/π']
H_sum = H.real.sum()

# ==============================================================================
# HOLOGRAMME DE CONNAISSANCE
# ==============================================================================

class HologrammeConnaissance:
    """
    Mémoire holographique distribuée.
    
    Architecture :
    - Matrice complexe 64×64×7 (28 672 valeurs complexes)
    - Chaque cellule contient la superposition de toutes les connaissances
    - Encodage : addition d'un motif d'interférence (onde de référence + onde objet)
    - Requête : multiplication par l'onde de lecture → émergence du motif recherché
    """
    
    def __init__(self, taille: int = 64):
        """
        Initialise l'hologramme de connaissance.
        
        Args:
            taille : dimension de la grille holographique (64×64 recommandé)
        """
        self.taille = taille
        # Matrice holographique : grille 2D × 7 harmoniques, valeurs complexes
        self.hologramme = np.zeros((taille, taille, 7), dtype=np.complex128)
        
        # Métadonnées
        self.n_connaissances = 0
        self.connaissances_stockees = []  # Liste des IDs pour traçabilité
        self.facteur_attenuation = 0.999  # Oubli progressif (1.0 = pas d'oubli)
        self.timestamp_dernier_acces = time.time()
        
        # Grille de coordonnées précalculée
        y, x = np.ogrid[:taille, :taille]
        self.grille_y = (y - taille/2) / (taille/2)
        self.grille_x = (x - taille/2) / (taille/2)
        self.grille_r = np.sqrt(self.grille_x**2 + self.grille_y**2)
        self.grille_theta = np.arctan2(self.grille_y, self.grille_x)
    
    def _generer_motif_reference(self, graine: int) -> np.ndarray:
        """
        Génère un motif d'onde de référence unique pour une connaissance.
        
        L'onde de référence est une onde plane de phase déterminée par la graine.
        C'est l'équivalent du faisceau laser de référence en holographie optique.
        
        Returns:
            Motif complexe de forme (taille, taille)
        """
        np.random.seed(graine)
        # Direction de l'onde de référence (angles aléatoires stables)
        angle = (graine * phi) % (2 * pi)
        kx = math.cos(angle)
        ky = math.sin(angle)
        
        # Onde plane de référence
        onde_ref = np.exp(1j * (kx * self.grille_x + ky * self.grille_y) * 10 * pi)
        return onde_ref
    
    def _texte_vers_vecteur_7d(self, texte: str) -> np.ndarray:
        """
        Convertit un texte en vecteur spectral 7D complexe.
        
        Chaque caractère contribue aux harmoniques Hₙ avec une phase.
        Plus le texte est long, plus le vecteur est riche.
        """
        vecteur = np.zeros(7, dtype=np.complex128)
        for i, char in enumerate(texte):
            idx = (ord(char) + i) % 7
            phase = (ord(char) * phi + i * pi) % (2 * pi)
            vecteur[idx] += H[idx] * cmath.exp(1j * phase)
        
        # Normalisation
        norm = np.linalg.norm(np.abs(vecteur))
        if norm > 0:
            vecteur /= norm
        return vecteur
    
    def _generer_motif_objet(self, vecteur_7d: np.ndarray) -> np.ndarray:
        """
        Génère le motif d'onde objet à partir du vecteur spectral 7D.
        
        L'onde objet est une superposition de 7 harmoniques spatiales,
        chacune modulée par la composante correspondante du vecteur.
        
        Returns:
            Motif complexe de forme (taille, taille)
        """
        onde_objet = np.zeros((self.taille, self.taille), dtype=np.complex128)
        
        for n in range(7):
            amplitude = abs(vecteur_7d[n])
            phase = cmath.phase(vecteur_7d[n]) if amplitude > 0 else 0.0
            freq = (n + 1) * pi / 4
            
            # Harmonique spatiale
            motif_n = amplitude * np.exp(1j * (
                freq * self.grille_r * 6 +
                (n + 1) * self.grille_theta +
                phase
            ))
            onde_objet += motif_n
        
        return onde_objet
    
    def encoder_connaissance(self, texte: str, identifiant: Optional[str] = None) -> str:
        """
        Encode une connaissance dans l'hologramme.
        
        Processus :
        1. Texte → vecteur spectral 7D (onde objet)
        2. Génération d'une onde de référence unique
        3. Interférence : hologramme += onde_ref* · onde_objet + onde_ref · onde_objet*
           (enregistrement de l'intensité d'interférence)
        4. La connaissance est maintenant distribuée dans TOUTE la matrice
        
        Args:
            texte : connaissance à encoder (phrase, concept, fait)
            identifiant : ID optionnel pour traçabilité
        
        Returns:
            Identifiant de la connaissance
        """
        if identifiant is None:
            identifiant = f"K{self.n_connaissances:04d}"
        
        # Vecteur spectral de la connaissance
        vecteur_7d = self._texte_vers_vecteur_7d(texte)
        
        # Onde de référence (basée sur un hash du texte pour reproductibilité)
        graine = hash(texte) % (2**31)
        onde_ref = self._generer_motif_reference(graine)
        
        # Onde objet (la connaissance elle-même)
        onde_objet = self._generer_motif_objet(vecteur_7d)
        
        # INTERFÉRENCE : enregistrement holographique
        # H = |R + O|² = |R|² + |O|² + R*O + RO*
        # On ne garde que les termes d'interférence R*O + RO*
        # (les termes |R|² et |O|² sont le fond continu, ignoré)
        
        motif_interference = (
            np.conj(onde_ref) * onde_objet +
            onde_ref * np.conj(onde_objet)
        )
        
        # Ajout à l'hologramme (superposition)
        for n in range(7):
            self.hologramme[:, :, n] += motif_interference * H[n] / H_sum
        
        # Métadonnées
        self.n_connaissances += 1
        self.connaissances_stockees.append({
            'id': identifiant,
            'texte': texte[:100],  # Tronqué pour la trace
            'graine': graine,
            'timestamp': time.time(),
            'vecteur_norme': np.linalg.norm(np.abs(vecteur_7d)),
        })
        
        # Oubli progressif
        self._appliquer_oubli()
        
        return identifiant
    
    def _appliquer_oubli(self):
        """
        Applique l'oubli progressif à l'hologramme.
        
        L'information s'estompe exponentiellement si elle n'est pas
        renforcée par de nouvelles requêtes. C'est le pendant
        holographique de la mémoire humaine.
        """
        maintenant = time.time()
        dt = maintenant - self.timestamp_dernier_acces
        self.timestamp_dernier_acces = maintenant
        
        # Atténuation exponentielle
        facteur = self.facteur_attenuation ** (dt / 3600.0)  # Échelle : heures
        self.hologramme *= facteur
    
    def requete_resonance(self, requete: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Interroge l'hologramme par résonance.
        
        Processus :
        1. Requête → vecteur spectral 7D (onde de lecture)
        2. L'onde de lecture est diffusée à travers l'hologramme
        3. Les motifs qui résonnent avec la requête émergent
        4. On mesure l'intensité de résonance pour chaque connaissance
        
        Args:
            requete : texte de la requête
            top_k : nombre de résultats à retourner
        
        Returns:
            Liste de (identifiant, score) triée par score décroissant
        """
        # Ondes de lecture pour chaque harmonique
        vecteur_requete = self._texte_vers_vecteur_7d(requete)
        onde_lecture = self._generer_motif_objet(vecteur_requete)
        
        scores = []
        
        for conn in self.connaissances_stockees:
            # Régénérer l'onde de référence de cette connaissance
            onde_ref = self._generer_motif_reference(conn['graine'])
            
            # Reconstruction : multiplier l'hologramme par l'onde de référence
            # devrait faire émerger l'onde objet originale
            intensite = 0.0
            for n in range(7):
                reconstruction = self.hologramme[:, :, n] * onde_ref
                # Corrélation avec l'onde de lecture
                correlation = np.abs(np.sum(reconstruction * np.conj(onde_lecture)))
                intensite += correlation * H[n].real / H_sum
            
            # Normalisation par la norme du vecteur original
            norme = conn['vecteur_norme'] if conn['vecteur_norme'] > 0 else 1.0
            score = intensite / (norme * self.taille * self.taille)
            scores.append((conn['id'], score, conn['texte']))
        
        # Trier par score décroissant
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Mise à jour du timestamp (renforce l'hologramme)
        self.timestamp_dernier_acces = time.time()
        
        return [(s[0], s[1]) for s in scores[:top_k]]
    
    def injecter_corpus(self, corpus: List[str]):
        """
        Injecte un corpus de connaissances dans l'hologramme.
        
        Args:
            corpus : liste de phrases/concepts à encoder
        """
        for i, texte in enumerate(corpus):
            self.encoder_connaissance(texte, f"K{i:04d}")
    
    def etat_hologramme(self) -> Dict:
        """
        Retourne l'état actuel de l'hologramme.
        """
        energie_totale = np.sum(np.abs(self.hologramme)**2)
        saturation = np.max(np.abs(self.hologramme))
        return {
            'n_connaissances': self.n_connaissances,
            'taille': self.taille,
            'energie_totale': float(energie_totale),
            'saturation': float(saturation),
            'facteur_attenuation': self.facteur_attenuation,
            'memoire_octets': self.hologramme.nbytes,
        }
    
    def visualiser_hologramme(self, harmonique: int = 0) -> np.ndarray:
        """
        Extrait une visualisation 2D de l'hologramme pour une harmonique donnée.
        
        Returns:
            Array (taille, taille) — module de l'hologramme
        """
        return np.abs(self.hologramme[:, :, harmonique])
    
    def test_robustesse(self, fraction_a_detruire: float = 0.5) -> Dict:
        """
        Teste la robustesse holographique en détruisant une fraction
        de la matrice et en mesurant la dégradation des requêtes.
        
        Args:
            fraction_a_detruire : fraction de cellules à mettre à zéro
        
        Returns:
            Dictionnaire avec les scores avant/après destruction
        """
        # Sauvegarde
        hologramme_original = self.hologramme.copy()
        
        # Requête test
        if self.connaissances_stockees:
            requete_test = self.connaissances_stockees[0]['texte'][:50]
        else:
            return {'erreur': 'Aucune connaissance stockée'}
        
        # Score avant destruction
        scores_avant = self.requete_resonance(requete_test, top_k=3)
        
        # Destruction aléatoire
        masque = np.random.random(self.hologramme.shape) > fraction_a_detruire
        self.hologramme *= masque
        
        # Score après destruction
        scores_apres = self.requete_resonance(requete_test, top_k=3)
        
        # Restauration
        self.hologramme = hologramme_original
        
        # Analyse
        if scores_avant and scores_apres:
            degradation = (scores_avant[0][1] - scores_apres[0][1]) / max(scores_avant[0][1], 1e-10)
        else:
            degradation = 0.0
        
        return {
            'fraction_detruite': fraction_a_detruire,
            'score_avant': scores_avant[0][1] if scores_avant else 0,
            'score_apres': scores_apres[0][1] if scores_apres else 0,
            'degradation_pct': degradation * 100,
            'top1_preserve': scores_avant[0][0] == scores_apres[0][0] if scores_avant and scores_apres else False,
        }


# ==============================================================================
# DÉMONSTRATION
# ==============================================================================
def demo_hologramme():
    """Démonstration complète de l'hologramme de connaissance."""
    print("=" * 70)
    print("HOLOGRAMME DE CONNAISSANCE HARMONO-HOLOGRAPHIQUE")
    print("Mémoire distribuée basée sur Ψ = Σ Hₙ · fⁿ")
    print("=" * 70)
    print()
    
    # Création de l'hologramme
    holo = HologrammeConnaissance(taille=64)
    print(f"  Hologramme créé : {holo.taille}×{holo.taille}×7 = {holo.taille**2 * 7:,} cellules")
    print(f"  Mémoire : {holo.hologramme.nbytes:,} octets")
    print()
    
    # Corpus de connaissances
    corpus = [
        "l'univers est une symphonie d'ondes harmoniques",
        "la gravité émerge de la courbure de l'espace-temps",
        "la constante de structure fine vaut environ 1/137",
        "le nombre d'or phi gouverne la croissance auto-similaire",
        "pi est le rapport entre la circonférence et le diamètre",
        "la dérivée ABC d'ordre 1/phi encode la mémoire non-locale",
        "le principe holographique dit que l'information du volume est codée sur la surface",
        "la masse du proton sur masse de l'électron vaut phi^-1 * pi * e^-2 * sqrt5^11",
        "la résonance de Schumann est la fréquence fondamentale de la Terre à 7.83 Hz",
        "les sept constantes harmoniques sont phi, pi, e, sqrt2, sqrt3, sqrt5, e/pi",
    ]
    
    print("  Injection du corpus de connaissances...")
    holo.injecter_corpus(corpus)
    print(f"  {holo.n_connaissances} connaissances encodées dans l'hologramme")
    print()
    
    # État de l'hologramme
    etat = holo.etat_hologramme()
    print(f"  État :")
    print(f"    Énergie totale : {etat['energie_totale']:.2e}")
    print(f"    Saturation     : {etat['saturation']:.4f}")
    print()
    
    # Test de requêtes
    print("  Tests de requête par résonance :")
    print()
    
    requetes = [
        "constante de structure fine",
        "principe holographique",
        "fréquence de la Terre",
        "masse du proton",
        "les sept constantes",
    ]
    
    for req in requetes:
        print(f"  Requête : \"{req}\"")
        resultats = holo.requete_resonance(req, top_k=2)
        for i, (id_conn, score) in enumerate(resultats):
            # Retrouver le texte
            conn = holo.connaissances_stockees[int(id_conn[1:])]
            texte_court = conn['texte'][:70]
            barre = "█" * int(score * 20 / max(r[1] for r in resultats)) if resultats else ""
            print(f"    {i+1}. [{id_conn}] {texte_court}")
            print(f"       score={score:.4f}  {barre}")
        print()
    
    # Test de robustesse holographique
    print("  Test de robustesse holographique :")
    for fraction in [0.1, 0.3, 0.5, 0.7, 0.9]:
        robustesse = holo.test_robustesse(fraction)
        status = "✅" if robustesse['top1_preserve'] else "❌"
        print(f"    Destruction {fraction*100:3.0f}% : "
              f"score {robustesse['score_avant']:.4f} → {robustesse['score_apres']:.4f} "
              f"({robustesse['degradation_pct']:5.1f}% dégradation) "
              f"top-1 préservé: {status}")
    print()
    
    print("=" * 70)
    print("TERMINÉ")
    print("=" * 70)


# ==============================================================================
# EXÉCUTION
# ==============================================================================
if __name__ == "__main__":
    demo_hologramme()