#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IA et Génération d'Images Harmono-Holographiques
=================================================
Deux systèmes basés sur Ψ = Σ Hₙ · fⁿ :

1. IA HARMONIQUE : Modèle de langage minimal utilisant les 7 constantes
   Hₙ = {φ, π, e, √2, √3, √5, e/π} comme alphabet sémantique.
   - Encodage harmonique des mots → vecteurs 7D
   - Prédiction par résonance spectrale (pas de Transformer)
   - Filtre anti-hallucination intégré

2. GÉNÉRATION D'IMAGES : Création d'images à partir de la somme harmonique
   - Chaque image est une cavité résonante
   - Ψ = Σ Hₙ · fⁿ génère l'image couche par couche
   - Paramètres : R (taille), phase, n_harmoniques

Auteur : KOTTO Alain — 19 Juin 2026
"""

import math
import struct
import time
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
H_names = ['φ', 'π', 'e', '√2', '√3', '√5', 'e/π']
H_sum = H.sum()

# ==============================================================================
# PARTIE 1 : IA HARMONIQUE (Modèle de Langage)
# ==============================================================================

class IAHarmonique:
    """
    Modèle de langage minimal basé sur les 7 constantes harmoniques.
    
    Principe :
    - Chaque mot est encodé en un vecteur spectral 7D
    - La similarité entre mots = similarité cosinus dans l'espace Hₙ
    - La prédiction du mot suivant = le mot dont le spectre résonne le plus
      avec le contexte
    - Le filtre anti-hallucination vérifie que la prédiction est harmonique
    """
    
    def __init__(self):
        """Initialise le vocabulaire et les embeddings harmoniques."""
        self.vocabulaire = {}
        self.embeddings = {}  # mot → vecteur 7D
        self.id_to_mot = {}
        self.mot_to_id = {}
        self._initialiser_vocabulaire()
    
    def _initialiser_vocabulaire(self):
        """Initialise un vocabulaire de base avec embeddings harmoniques."""
        mots_base = [
            # Structure
            "univers", "onde", "harmonie", "frequence", "energie", "matiere",
            "lumiere", "temps", "espace", "constante", "fondamental",
            # Dynamique
            "courbure", "croissance", "structure", "information", "signal",
            "resonance", "equilibre", "emergence", "particule", "atome",
            # États
            "elements", "tableau", "periodique", "symphonie", "cosmique",
            # Gravité/Forces
            "gravite", "force", "electromagnetique", "nucléaire", "faible",
            "forte", "interaction", "champ", "quantique", "classique",
            # Conscience/Vie
            "conscience", "biologie", "cellule", "organe", "cerveau",
            "pensee", "perception", "realite", "observateur",
            # Connecteurs
            "est", "et", "de", "la", "le", "les", "des", "une", "un",
            "dans", "par", "pour", "avec", "sans", "sur", "sous",
        ]
        
        for i, mot in enumerate(mots_base):
            self.ajouter_mot(mot)
    
    def _mot_vers_spectre(self, mot: str) -> np.ndarray:
        """
        Convertit un mot en vecteur spectral 7D.
        
        Algorithme : somme pondérée des caractères projetée sur Hₙ.
        Chaque caractère contribue proportionnellement à H[char % 7].
        """
        spectre = np.zeros(7, dtype=np.float64)
        for i, char in enumerate(mot):
            idx = (ord(char) + i) % 7
            spectre[idx] += H[idx] / H_sum
        # Normalisation
        norm = np.linalg.norm(spectre)
        if norm > 0:
            spectre /= norm
        return spectre
    
    def ajouter_mot(self, mot: str):
        """Ajoute un mot au vocabulaire avec son embedding harmonique."""
        if mot not in self.vocabulaire:
            idx = len(self.vocabulaire)
            self.vocabulaire[mot] = idx
            self.mot_to_id[mot] = idx
            self.id_to_mot[idx] = mot
            self.embeddings[mot] = self._mot_vers_spectre(mot)
    
    def encoder_phrase(self, phrase: str) -> np.ndarray:
        """
        Encode une phrase en vecteur spectral 7D.
        
        La phrase est la somme des embeddings de ses mots,
        pondérée par leurs coefficients harmoniques.
        """
        mots = phrase.lower().split()
        if not mots:
            return np.zeros(7, dtype=np.float64)
        
        vecteur = np.zeros(7, dtype=np.float64)
        for mot in mots:
            if mot in self.embeddings:
                vecteur += self.embeddings[mot]
            else:
                self.ajouter_mot(mot)
                vecteur += self.embeddings[mot]
        
        # Normalisation
        norm = np.linalg.norm(vecteur)
        if norm > 0:
            vecteur /= norm
        return vecteur
    
    def predire_mot_suivant(self, contexte: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Prédit le mot suivant par résonance spectrale.
        
        Le mot prédit est celui dont l'embedding a la plus grande
        similarité cosinus avec le vecteur de contexte.
        """
        vecteur_contexte = self.encoder_phrase(contexte)
        
        scores = []
        for mot, emb in self.embeddings.items():
            # Similarité cosinus
            dot = np.dot(vecteur_contexte, emb)
            norm_c = np.linalg.norm(vecteur_contexte)
            norm_e = np.linalg.norm(emb)
            if norm_c > 0 and norm_e > 0:
                sim = dot / (norm_c * norm_e)
            else:
                sim = 0.0
            scores.append((mot, sim))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
    
    def coherence_prediction(self, mot: str, contexte: str) -> float:
        """
        Mesure la cohérence harmonique d'une prédiction.
        
        Score [0,1] : 0 = hallucination probable, 1 = prédiction fiable.
        """
        if mot not in self.embeddings:
            return 0.0
        
        vec_mot = self.embeddings[mot]
        vec_contexte = self.encoder_phrase(contexte)
        
        # Similarité cosinus
        dot = np.dot(vec_mot, vec_contexte)
        norm_m = np.linalg.norm(vec_mot)
        norm_c = np.linalg.norm(vec_contexte)
        
        if norm_m > 0 and norm_c > 0:
            sim = dot / (norm_m * norm_c)
        else:
            sim = 0.0
        
        # Score : 0.5 + 0.5 * sim (centré sur 0.5)
        return 0.5 + 0.5 * max(0, sim)
    
    def harmoniser_vecteur(self, vecteur: np.ndarray) -> np.ndarray:
        """
        Projette un vecteur quelconque sur la grille harmonique.
        Chaque composante est arrondie au multiple de H[n] le plus proche.
        """
        harmonise = np.zeros(7, dtype=np.float64)
        for n in range(7):
            # Trouver le multiple de H[n]/H_sum le plus proche
            step = H[n] / H_sum
            k = round(vecteur[n] / step) if step > 0 else 0
            harmonise[n] = k * step
        return harmonise
    
    def filtrer_hallucination(self, prediction: str, contexte: str,
                               seuil: float = 0.6) -> Dict:
        """
        Filtre anti-hallucination complet.
        
        Retourne un diagnostic détaillé.
        """
        coherence = self.coherence_prediction(prediction, contexte)
        est_hallucination = coherence < seuil
        
        # Si hallucination, proposer une correction
        correction = None
        if est_hallucination:
            alternatives = self.predire_mot_suivant(contexte, top_k=3)
            if alternatives:
                correction = alternatives[0][0]
        
        return {
            'prediction': prediction,
            'coherence': coherence,
            'est_hallucination': est_hallucination,
            'correction': correction,
            'diagnostic': 'HARMONIQUE' if not est_hallucination else 'HALLUCINATION POTENTIELLE',
        }


# ==============================================================================
# PARTIE 2 : GÉNÉRATION D'IMAGES HARMONIQUES
# ==============================================================================

class GenerateurImagesHarmoniques:
    """
    Générateur d'images basé sur Ψ = Σ Hₙ · fⁿ.
    
    Chaque image est une cavité résonante de rayon R.
    Les 7 harmoniques sont superposées pour créer l'image.
    
    Paramètres :
    - R : rayon de la cavité (détermine la résolution/fréquence)
    - n_harmoniques : nombre d'harmoniques (7 max)
    - phase_initiale : déphasage pour varier les motifs
    - mode : "cercle", "spirale", "grille", "fractal", "cosmique"
    """
    
    def __init__(self):
        self.H = H
        self.H_names = H_names
    
    def generer(self, largeur: int = 256, hauteur: int = 256,
                n_harmoniques: int = 7, mode: str = "cosmique",
                phase_initiale: float = 0.0,
                graine: Optional[int] = None) -> np.ndarray:
        """
        Génère une image harmonique.
        
        Args:
            largeur, hauteur : dimensions de l'image
            n_harmoniques : nombre d'harmoniques à utiliser (1-7)
            mode : type de motif ("cercle", "spirale", "grille", "fractal", "cosmique")
            phase_initiale : déphasage (0 à 2π)
            graine : graine aléatoire pour la reproductibilité
        
        Returns:
            Array numpy (hauteur, largeur) en uint8 [0,255]
        """
        if graine is not None:
            np.random.seed(graine)
        
        n_harmoniques = min(n_harmoniques, 7)
        
        y, x = np.ogrid[:hauteur, :largeur]
        centre_y, centre_x = hauteur / 2, largeur / 2
        
        # Coordonnées normalisées
        xn = (x - centre_x) / (largeur / 2)
        yn = (y - centre_y) / (hauteur / 2)
        
        # Distance au centre et angle
        r = np.sqrt(xn**2 + yn**2)
        theta = np.arctan2(yn, xn)
        
        image = np.zeros((hauteur, largeur), dtype=np.float64)
        
        for n in range(n_harmoniques):
            h_n = H[n]
            freq = (n + 1) * pi / 4  # Fréquence croissante
            
            if mode == "cercle":
                # Ondes concentriques
                motif = h_n * np.cos(freq * r * 8 + phase_initiale)
            
            elif mode == "spirale":
                # Spirales logarithmiques
                motif = h_n * np.cos(freq * r * 8 + (n + 1) * theta + phase_initiale)
            
            elif mode == "grille":
                # Grille rectangulaire
                motif = h_n * (np.cos(freq * xn * 8 + phase_initiale) *
                               np.cos(freq * yn * 8 + phase_initiale))
            
            elif mode == "fractal":
                # Motif fractal auto-similaire
                motif = h_n * np.cos(freq * np.log(r + 0.1) * 8 +
                                     (n + 1) * theta + phase_initiale)
            
            elif mode == "cosmique":
                # Superposition complexe (le plus beau visuellement)
                onde_radiale = np.cos(freq * r * 6 + phase_initiale)
                onde_angulaire = np.cos((n + 1) * theta + phase_initiale * 0.5)
                bruit = np.sin(r * 20 + theta * 3) * 0.3
                motif = h_n * (onde_radiale * onde_angulaire + bruit)
            
            else:
                motif = h_n * np.cos(freq * r * 8 + (n + 1) * theta + phase_initiale)
            
            image += motif
        
        # Normalisation à [0, 255]
        img_min = image.min()
        img_max = image.max()
        if img_max > img_min:
            image = (image - img_min) / (img_max - img_min) * 255
        else:
            image = np.zeros_like(image)
        
        return np.clip(image, 0, 255).astype(np.uint8)
    
    def generer_serie(self, n_images: int = 5, largeur: int = 256, hauteur: int = 256,
                      mode: str = "cosmique") -> List[np.ndarray]:
        """
        Génère une série d'images en faisant varier la phase.
        Crée une animation de la cavité résonante.
        """
        images = []
        for i in range(n_images):
            phase = 2 * pi * i / n_images
            img = self.generer(largeur, hauteur, n_harmoniques=7,
                              mode=mode, phase_initiale=phase, graine=42)
            images.append(img)
        return images
    
    def extraire_signature(self, image: np.ndarray) -> np.ndarray:
        """
        Extrait la signature harmonique 7D d'une image.
        
        Projette l'image sur les 7 motifs harmoniques.
        Retourne un vecteur 7D de coefficients spectraux.
        """
        hauteur, largeur = image.shape
        data = image.astype(np.float64) / 255.0
        
        signature = np.zeros(7, dtype=np.float64)
        
        y, x = np.ogrid[:hauteur, :largeur]
        centre_y, centre_x = hauteur / 2, largeur / 2
        xn = (x - centre_x) / (largeur / 2)
        yn = (y - centre_y) / (hauteur / 2)
        r = np.sqrt(xn**2 + yn**2)
        theta = np.arctan2(yn, xn)
        
        for n in range(7):
            freq = (n + 1) * pi / 4
            motif = H[n] * np.cos(freq * r * 6) * np.cos((n + 1) * theta)
            motif_norm = motif / (np.abs(motif).max() + 1e-10)
            signature[n] = np.sum(data * motif_norm) / (hauteur * largeur)
        
        # Normalisation
        norm = np.linalg.norm(signature)
        if norm > 0:
            signature /= norm
        
        return signature


# ==============================================================================
# DÉMONSTRATION
# ==============================================================================
def demo_ia():
    """Démonstration de l'IA harmonique."""
    print("=" * 70)
    print("DÉMO 1 : IA HARMONIQUE — Prédiction par résonance spectrale")
    print("=" * 70)
    print()
    
    ia = IAHarmonique()
    
    print(f"  Vocabulaire : {len(ia.vocabulaire)} mots")
    print()
    
    # Test de prédiction
    tests = [
        "l'univers est une",
        "la gravite est une",
        "la lumiere et la",
        "le temps et l'",
        "la conscience emerge de",
    ]
    
    for contexte in tests:
        print(f"  Contexte : \"{contexte}\"")
        predictions = ia.predire_mot_suivant(contexte, top_k=3)
        for mot, score in predictions:
            coherence = ia.coherence_prediction(mot, contexte)
            barre = "█" * int(score * 20)
            print(f"    {mot:<15s}  sim={score:.4f}  coh={coherence:.4f}  {barre}")
        
        # Filtre anti-hallucination sur la meilleure prédiction
        if predictions:
            diagnostic = ia.filtrer_hallucination(predictions[0][0], contexte)
            print(f"    → Diagnostic : {diagnostic['diagnostic']}")
        print()
    
    # Test du filtre anti-hallucination
    print(f"  Test filtre anti-hallucination :")
    # Un mot qui n'existe pas dans le vocabulaire
    diag = ia.filtrer_hallucination("xyztruc", "l'univers est")
    print(f"    Mot inconnu 'xyztruc' : {diag['diagnostic']} (coh={diag['coherence']:.4f})")
    
    # Un mot cohérent
    diag2 = ia.filtrer_hallucination("symphonie", "l'univers est une")
    print(f"    Mot cohérent 'symphonie' : {diag2['diagnostic']} (coh={diag2['coherence']:.4f})")
    print()


def demo_generation():
    """Démonstration de la génération d'images."""
    print("=" * 70)
    print("DÉMO 2 : GÉNÉRATION D'IMAGES HARMONIQUES")
    print("Ψ = Σ Hₙ · fⁿ → Image")
    print("=" * 70)
    print()
    
    try:
        from PIL import Image
    except ImportError:
        print("  PIL non installé. Installation : pip install Pillow")
        return
    
    gen = GenerateurImagesHarmoniques()
    
    print(f"  Génération d'images en 5 modes...")
    print()
    
    modes = ["cercle", "spirale", "grille", "fractal", "cosmique"]
    signatures = {}
    
    for mode in modes:
        img = gen.generer(256, 256, n_harmoniques=7, mode=mode, graine=42)
        Image.fromarray(img).save(f"harmonique_{mode}.png")
        
        # Extraire la signature harmonique
        signature = gen.extraire_signature(img)
        signatures[mode] = signature
        
        print(f"  {mode:<10s} → harmonique_{mode}.png (256×256)")
        print(f"    Signature 7D : [{', '.join(f'{s:+.4f}' for s in signature)}]")
        print()
    
    # Série d'images (animation)
    print(f"  Génération d'une série de 5 images (mode cosmique)...")
    serie = gen.generer_serie(5, 128, 128, mode="cosmique")
    for i, img in enumerate(serie):
        Image.fromarray(img).save(f"harmonique_serie_{i+1}.png")
    print(f"  → harmonique_serie_1..5.png sauvegardées")
    print()


# ==============================================================================
# EXÉCUTION
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("IA & GÉNÉRATION D'IMAGES HARMONO-HOLOGRAPHIQUES")
    print("Ψ = Σ Hₙ · fⁿ")
    print("=" * 70)
    print()
    print(f"  Constantes : φ={phi:.6f} π={pi:.6f} e={e:.6f}")
    print(f"              √2={sqrt2:.6f} √3={sqrt3:.6f} √5={sqrt5:.6f} e/π={e_sur_pi:.6f}")
    print()
    
    # Démo IA
    demo_ia()
    
    # Démo Génération d'images
    demo_generation()
    
    print("=" * 70)
    print("TERMINÉ")
    print("=" * 70)