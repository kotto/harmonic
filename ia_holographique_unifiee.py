#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IA Harmono-Holographique Unifiée
=================================
Intégration complète des 3 systèmes :

1. IA Harmonique (modèle de langage minimal)
2. Générateur d'Images Harmoniques
3. Hologramme de Connaissance (mémoire distribuée)

Nouveautés :
- L'IA utilise maintenant l'hologramme comme mémoire
- Les connaissances sont stockées de manière distribuée
- La prédiction combine similarité cosinus + résonance holographique
- Capacité d'apprentissage continu (nouvelles connaissances sans oubli)
- Interface unifiée : texte → hologramme → prédiction
- Génération d'images à partir de requêtes textuelles

Auteur : KOTTO Alain — 19 Juin 2026 (Version Unifiée)
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

H = np.array([phi, pi, e, sqrt2, sqrt3, sqrt5, e_sur_pi], dtype=np.float64)
H_complex = np.array([phi, pi, e, sqrt2, sqrt3, sqrt5, e_sur_pi], dtype=np.complex128)
H_names = ['φ', 'π', 'e', '√2', '√3', '√5', 'e/π']
H_sum = H.sum()

# Physique
c_light = 299792458.0
hbar = 6.62607015e-34 / (2 * pi)
G = 6.67430e-11
l_P = math.sqrt(hbar * G / c_light**3)

def N_PSU(rayon_m): return 4 * rayon_m**2 / l_P**2

# ==============================================================================
# HOLOGRAMME DE CONNAISSANCE (version optimisée pour l'IA)
# ==============================================================================

class HologrammeConnaissanceV2:
    """Mémoire holographique distribuée, optimisée pour l'IA."""
    
    def __init__(self, taille: int = 64):
        self.taille = taille
        self.hologramme = np.zeros((taille, taille, 7), dtype=np.complex128)
        self.n_connaissances = 0
        self.connaissances_stockees = []
        self.facteur_attenuation = 0.999
        
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
        """Encode une connaissance dans l'hologramme."""
        if identifiant is None:
            identifiant = f"K{self.n_connaissances:04d}"
        
        vecteur_7d = self._texte_vers_vecteur(texte)
        graine = hash(texte) % (2**31)
        onde_ref = self._generer_motif_reference(graine)
        onde_objet = self._generer_motif_objet(vecteur_7d)
        
        motif_interference = np.conj(onde_ref) * onde_objet + onde_ref * np.conj(onde_objet)
        for n in range(7):
            self.hologramme[:, :, n] += motif_interference * H_complex[n] / H_sum
        
        self.n_connaissances += 1
        self.connaissances_stockees.append({
            'id': identifiant, 'texte': texte[:100],
            'graine': graine, 'timestamp': time.time(),
            'vecteur_norme': float(np.linalg.norm(np.abs(vecteur_7d))),
            'mots_cles': set(texte.lower().split()),
        })
        return identifiant
    
    def requete(self, requete: str, top_k: int = 5) -> List[Tuple[str, float, str]]:
        """Interroge l'hologramme par résonance."""
        vecteur_requete = self._texte_vers_vecteur(requete)
        onde_lecture = self._generer_motif_objet(vecteur_requete)
        mots_requete = set(requete.lower().split())
        
        scores = []
        for conn in self.connaissances_stockees:
            onde_ref = self._generer_motif_reference(conn['graine'])
            intensite = 0.0
            for n in range(7):
                reconstruction = self.hologramme[:, :, n] * onde_ref
                correlation = np.abs(np.sum(reconstruction * np.conj(onde_lecture)))
                intensite += correlation * H[n] / H_sum
            
            # Bonus de correspondance par mots-clés
            mots_conn = conn['mots_cles']
            intersection = mots_requete & mots_conn
            union = mots_requete | mots_conn
            jaccard = len(intersection) / max(len(union), 1) if intersection else 0.0
            
            # Score composite : holographique + Jaccard
            score_holographique = intensite / max(intensite, 1e-10)
            score_jaccard = jaccard * 5.0  # Booster le poids des mots-clés
            score_final = score_holographique + score_jaccard
            
            scores.append((conn['id'], float(score_final), conn['texte']))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Filtrer les scores nuls
        resultats = [(s[0], s[1], s[2]) for s in scores if s[1] > 1e-6]
        return resultats[:top_k] if resultats else scores[:top_k]
    
    def injecter_corpus(self, corpus: List[str]):
        """Injecte un corpus de connaissances."""
        for i, texte in enumerate(corpus):
            self.encoder(texte, f"K{i:04d}")


# ==============================================================================
# IA HARMONIQUE UNIFIÉE
# ==============================================================================

class IAHarmoniqueUnifiee:
    """
    IA Harmonique avec mémoire holographique intégrée.
    
    Combine :
    - Modèle de langage par similarité cosinus
    - Hologramme de connaissance pour la mémoire long-terme
    - Filtre anti-hallucination holographique
    - Génération d'images à partir de requêtes
    """
    
    def __init__(self, taille_hologramme: int = 64):
        self.hologramme = HologrammeConnaissanceV2(taille_hologramme)
        self.vocabulaire = {}
        self.embeddings = {}
        self.mot_to_id = {}
        self.id_to_mot = {}
        self._initialiser_vocabulaire()
        self.historique = []
    
    def _initialiser_vocabulaire(self):
        """Initialise le vocabulaire avec des embeddings harmoniques."""
        mots_base = [
            "univers", "onde", "harmonie", "frequence", "energie", "matiere",
            "lumiere", "temps", "espace", "constante", "fondamental",
            "courbure", "croissance", "structure", "information", "signal",
            "resonance", "equilibre", "emergence", "particule", "atome",
            "elements", "tableau", "periodique", "symphonie", "cosmique",
            "gravite", "force", "electromagnetique", "nucleaire", "faible",
            "forte", "interaction", "champ", "quantique", "classique",
            "conscience", "biologie", "cellule", "organe", "cerveau",
            "pensee", "perception", "realite", "observateur", "holographique",
            "est", "et", "de", "la", "le", "les", "des", "une", "un",
            "dans", "par", "pour", "avec", "sans", "sur", "sous",
        ]
        for mot in mots_base:
            self.ajouter_mot(mot)
    
    def _mot_vers_spectre(self, mot: str) -> np.ndarray:
        """Convertit un mot en vecteur spectral 7D."""
        spectre = np.zeros(7, dtype=np.float64)
        for i, char in enumerate(mot):
            idx = (ord(char) + i) % 7
            spectre[idx] += H[idx] / H_sum
        norm = np.linalg.norm(spectre)
        if norm > 0:
            spectre /= norm
        return spectre
    
    def ajouter_mot(self, mot: str):
        """Ajoute un mot au vocabulaire."""
        if mot not in self.vocabulaire:
            idx = len(self.vocabulaire)
            self.vocabulaire[mot] = idx
            self.mot_to_id[mot] = idx
            self.id_to_mot[idx] = mot
            self.embeddings[mot] = self._mot_vers_spectre(mot)
    
    def encoder_phrase(self, phrase: str) -> np.ndarray:
        """Encode une phrase en vecteur spectral 7D."""
        mots = phrase.lower().split()
        if not mots:
            return np.zeros(7, dtype=np.float64)
        vecteur = np.zeros(7, dtype=np.float64)
        for mot in mots:
            if mot not in self.embeddings:
                self.ajouter_mot(mot)
            vecteur += self.embeddings[mot]
        norm = np.linalg.norm(vecteur)
        if norm > 0:
            vecteur /= norm
        return vecteur
    
    def apprendre(self, texte: str):
        """
        Apprend une nouvelle connaissance.
        
        1. L'encode dans l'hologramme (mémoire long-terme distribuée)
        2. Ajoute les mots inconnus au vocabulaire
        """
        self.hologramme.encoder(texte)
        for mot in texte.lower().split():
            if mot not in self.vocabulaire:
                self.ajouter_mot(mot)
    
    def apprendre_corpus(self, corpus: List[str]):
        """Apprend un corpus entier de connaissances."""
        for texte in corpus:
            self.apprendre(texte)
    
    def predire(self, contexte: str, top_k: int = 5,
                utiliser_hologramme: bool = True) -> Dict:
        """
        Prédiction unifiée combinant :
        1. Similarité cosinus dans l'espace des embeddings (rapide)
        2. Résonance holographique (mémoire long-terme)
        """
        vecteur_contexte = self.encoder_phrase(contexte)
        
        # Prédiction par similarité cosinus (vocabulaire)
        scores_locaux = []
        for mot, emb in self.embeddings.items():
            sim = max(0, np.dot(vecteur_contexte, emb))
            scores_locaux.append((mot, sim))
        scores_locaux.sort(key=lambda x: x[1], reverse=True)
        
        # Prédiction par résonance holographique (mémoire long-terme)
        scores_holographiques = []
        if utiliser_hologramme and self.hologramme.n_connaissances > 0:
            scores_holographiques = self.hologramme.requete(contexte, top_k)
        
        # Fusion : holographiques d'abord (plus pertinents), puis vocabulaire
        predictions = []
        
        # Top holographiques en premier
        for id_conn, score, texte in scores_holographiques[:5]:
            predictions.append({
                'type': 'holographique',
                'mot': None,
                'score': score,
                'texte': texte,
                'id': id_conn,
            })
        
        # Top locales ensuite
        for mot, score in scores_locaux[:5]:
            predictions.append({
                'type': 'vocabulaire',
                'mot': mot,
                'score': score,
                'texte': mot,
            })
        
        # Filtre anti-hallucination
        diagnostic = self._diagnostiquer(contexte, scores_locaux[0][0] if scores_locaux else "?")
        
        return {
            'contexte': contexte,
            'predictions': predictions,
            'diagnostic': diagnostic,
            'n_connaissances': self.hologramme.n_connaissances,
        }
    
    def _diagnostiquer(self, contexte: str, prediction: str) -> str:
        """Diagnostic harmonique de la prédiction."""
        vec_c = self.encoder_phrase(contexte)
        vec_p = self.embeddings.get(prediction, np.zeros(7))
        
        sim = np.dot(vec_c, vec_p)
        coherence = 0.5 + 0.5 * max(0, sim)
        
        if coherence > 0.75:
            return f"HARMONIQUE (coh={coherence:.3f})"
        elif coherence > 0.5:
            return f"INCERTAIN (coh={coherence:.3f})"
        else:
            return f"HALLUCINATION PROBABLE (coh={coherence:.3f})"
    
    def repondre(self, question: str) -> str:
        """
        Répond à une question en utilisant la mémoire holographique.
        
        Processus :
        1. Interroge l'hologramme
        2. Si une connaissance pertinente est trouvée, la retourne
        3. Sinon, utilise le modèle de langage local
        """
        resultat = self.predire(question)
        
        # Chercher une réponse holographique avec un bon score
        for pred in resultat['predictions']:
            if pred['type'] == 'holographique' and pred['score'] > 0.05:
                return f"[HOLOGRAMME] {pred['texte']}"
        
        # Fallback : meilleure prédiction locale
        for pred in resultat['predictions']:
            if pred['type'] == 'vocabulaire' and pred['score'] > 0.5:
                return f"[VOCABULAIRE] {pred['mot']}"
        
        return "[INCERTAIN] Aucune connaissance pertinente trouvée."
    
    def generer_image(self, requete: str, taille: int = 256,
                      mode: str = "cosmique") -> np.ndarray:
        """
        Génère une image à partir d'une requête textuelle.
        
        La requête détermine la phase et le mode de génération.
        """
        # Hash de la requête → graine déterministe
        graine = hash(requete) % (2**31)
        np.random.seed(graine)
        
        # La requête détermine la phase initiale
        vecteur = self.encoder_phrase(requete)
        phase = float(np.sum(vecteur)) % (2 * pi)
        
        # Mode basé sur la dominante harmonique
        dominante = np.argmax(np.abs(vecteur))
        modes = ["cercle", "spirale", "grille", "fractal", "cosmique", "cosmique", "cosmique"]
        mode_auto = modes[dominante % len(modes)]
        if mode == "auto":
            mode = mode_auto
        
        # Génération (même algorithme que GenerateurImagesHarmoniques)
        hauteur = largeur = taille
        y, x = np.ogrid[:hauteur, :largeur]
        centre_y, centre_x = hauteur / 2, largeur / 2
        xn = (x - centre_x) / (largeur / 2)
        yn = (y - centre_y) / (hauteur / 2)
        r = np.sqrt(xn**2 + yn**2)
        theta = np.arctan2(yn, xn)
        
        image = np.zeros((hauteur, largeur), dtype=np.float64)
        
        for n in range(7):
            h_n = H[n]
            freq = (n + 1) * pi / 4
            
            if mode == "cercle":
                motif = h_n * np.cos(freq * r * 8 + phase)
            elif mode == "spirale":
                motif = h_n * np.cos(freq * r * 8 + (n + 1) * theta + phase)
            elif mode == "grille":
                motif = h_n * (np.cos(freq * xn * 8 + phase) *
                               np.cos(freq * yn * 8 + phase))
            elif mode == "fractal":
                motif = h_n * np.cos(freq * np.log(r + 0.1) * 8 + (n + 1) * theta + phase)
            else:  # cosmique
                onde_radiale = np.cos(freq * r * 6 + phase)
                onde_angulaire = np.cos((n + 1) * theta + phase * 0.5)
                bruit = np.sin(r * 20 + theta * 3) * 0.3
                motif = h_n * (onde_radiale * onde_angulaire + bruit)
            
            image += motif
        
        img_min, img_max = image.min(), image.max()
        if img_max > img_min:
            image = (image - img_min) / (img_max - img_min) * 255
        
        return np.clip(image, 0, 255).astype(np.uint8)


# ==============================================================================
# DÉMONSTRATION
# ==============================================================================
def demo():
    print("=" * 70)
    print("IA HARMONO-HOLOGRAPHIQUE UNIFIÉE")
    print("Hologramme + Modèle de Langage + Génération d'Images")
    print("=" * 70)
    print()
    
    # Création de l'IA
    ia = IAHarmoniqueUnifiee(taille_hologramme=64)
    print(f"  IA initialisée : {len(ia.vocabulaire)} mots, hologramme 64×64×7")
    print()
    
    # Apprentissage
    corpus = [
        "l'univers est une symphonie d'ondes harmoniques",
        "la constante de structure fine alpha vaut environ 1/137",
        "le nombre d'or phi est egal a 1.618034",
        "pi est le rapport entre la circonference et le diametre d'un cercle",
        "la resonance de Schumann est la frequence fondamentale de la Terre",
        "la masse du proton sur masse de l'electron est environ 1836",
        "le principe holographique encode l'information du volume sur la surface",
        "la derivee ABC d'ordre 1/phi modelise les systemes avec memoire",
        "les sept constantes harmoniques sont phi pi e sqrt2 sqrt3 sqrt5 et e/pi",
        "la compression harmonique utilise la projection sur les 7 constantes",
    ]
    
    print("  Apprentissage du corpus...")
    ia.apprendre_corpus(corpus)
    print(f"  {ia.hologramme.n_connaissances} connaissances stockées dans l'hologramme")
    print()
    
    # Tests de réponse
    print("  Tests de réponse :")
    print()
    
    questions = [
        "quelle est la constante de structure fine",
        "qu'est-ce que la resonance de Schumann",
        "quelle est la valeur du nombre d'or",
        "comment fonctionne la compression harmonique",
        "qu'est-ce que le principe holographique",
        "quelles sont les sept constantes",
    ]
    
    for q in questions:
        reponse = ia.repondre(q)
        print(f"  Q: \"{q}\"")
        print(f"  R: {reponse}")
        print()
    
    # Génération d'images
    print("  Génération d'images à partir de requêtes...")
    
    try:
        from PIL import Image
        for i, q in enumerate(questions[:3]):
            img = ia.generer_image(q, taille=64)
            Image.fromarray(img).save(f"ia_image_{i+1}.png")
            print(f"  → ia_image_{i+1}.png (requête: \"{q[:40]}...\")")
        print()
    except ImportError:
        print("  PIL non installé")
        print()
    
    print("=" * 70)
    print("TERMINÉ")
    print("=" * 70)


if __name__ == "__main__":
    demo()