#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IA Harmono-Holographique Corrigée
==================================
Corrections appliquées :
1. TF-IDF au lieu du Jaccard brut (poids des mots rares)
2. Injection de TOUTES les connaissances (plus de limite)
3. Score cosinus 7D en bonus (discrimination par domaine)
4. Tag de domaine pour filtrage

Auteur : KOTTO Alain — 19 Juin 2026 (Version Corrigée)
"""

import math, cmath, time, sys, os, json, glob
import numpy as np
from collections import Counter
from typing import Dict, List, Tuple, Optional

sys.path.insert(0, os.path.dirname(__file__))

# ==============================================================================
# CONSTANTES HARMONIQUES
# ==============================================================================
phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e = math.e
sqrt2 = math.sqrt(2); sqrt3 = math.sqrt(3); sqrt5 = math.sqrt(5)
e_sur_pi = e / pi

H = np.array([phi, pi, e, sqrt2, sqrt3, sqrt5, e_sur_pi], dtype=np.float64)
H_complex = np.array([phi, pi, e, sqrt2, sqrt3, sqrt5, e_sur_pi], dtype=np.complex128)
H_names = ['φ','π','e','√2','√3','√5','e/π']; H_sum = H.sum()

# ==============================================================================
# HOLOGRAMME V2 AMÉLIORÉ (TF-IDF)
# ==============================================================================

class HologrammeConnaissanceV2Ameliore:
    """Hologramme V2 avec TF-IDF au lieu du Jaccard."""
    
    def __init__(self, taille=64):
        self.taille = taille
        self.hologramme = np.zeros((taille, taille, 7), dtype=np.complex128)
        self.n_connaissances = 0
        self.connaissances_stockees = []
        self.idf = {}  # IDF par mot
        self.doc_count = Counter()  # Nombre de documents contenant chaque mot
        
        y, x = np.ogrid[:taille, :taille]
        self.grille_y = (y - taille/2) / (taille/2)
        self.grille_x = (x - taille/2) / (taille/2)
        self.grille_r = np.sqrt(self.grille_x**2 + self.grille_y**2)
        self.grille_theta = np.arctan2(self.grille_y, self.grille_x)
    
    def _texte_vers_vecteur(self, texte):
        v = np.zeros(7, dtype=np.complex128)
        for i, c in enumerate(texte):
            idx = (ord(c) + i) % 7
            ph = (ord(c) * phi + i * pi) % (2*pi)
            v[idx] += H_complex[idx] * cmath.exp(1j*ph)
        n = np.linalg.norm(np.abs(v))
        return v/n if n > 0 else v
    
    def _vecteur_float(self, vc): return np.abs(vc).astype(np.float64)
    
    def _motif_reference(self, graine):
        np.random.seed(graine)
        angle = (graine * phi) % (2*pi)
        kx, ky = math.cos(angle), math.sin(angle)
        return np.exp(1j*(kx*self.grille_x + ky*self.grille_y)*10*pi)
    
    def _motif_objet(self, v):
        onde = np.zeros((self.taille, self.taille), dtype=np.complex128)
        for n in range(7):
            amp = abs(v[n]); ph = cmath.phase(v[n]) if amp > 0 else 0.0
            freq = (n+1)*pi/4
            onde += amp * np.exp(1j*(freq*self.grille_r*6 + (n+1)*self.grille_theta + ph))
        return onde
    
    def encoder(self, texte, identifiant=None, domaine=""):
        if identifiant is None:
            identifiant = f"K{self.n_connaissances:06d}"
        
        v = self._texte_vers_vecteur(texte)
        vf = self._vecteur_float(v)
        graine = hash(texte) % (2**31)
        
        onde_ref = self._motif_reference(graine)
        onde_obj = self._motif_objet(v)
        motif = np.conj(onde_ref)*onde_obj + onde_ref*np.conj(onde_obj)
        for n in range(7):
            self.hologramme[:,:,n] += motif * H_complex[n]/H_sum
        
        # Mots-clés pour TF-IDF
        mots = set(texte.lower().split())
        for mot in mots:
            self.doc_count[mot] += 1
        
        self.n_connaissances += 1
        self.connaissances_stockees.append({
            'id': identifiant, 'texte': texte[:200],
            'graine': graine, 'timestamp': time.time(),
            'vecteur_norme': float(np.linalg.norm(vf)),
            'mots_cles': mots,
            'vecteur_7d': vf,
            'domaine': domaine,
        })
        return identifiant
    
    def calculer_idf(self):
        """Calcule l'IDF pour chaque mot après injection."""
        N = self.n_connaissances
        for mot, count in self.doc_count.items():
            self.idf[mot] = math.log((N + 1) / (count + 1)) + 1
    
    def requete(self, requete, top_k=5):
        """Requête avec TF-IDF + holographique + cosinus 7D."""
        v = self._texte_vers_vecteur(requete)
        vf = self._vecteur_float(v)
        onde_lecture = self._motif_objet(v)
        mots_requete = set(requete.lower().split())
        
        # Calculer TF-IDF de la requête
        tf_requete = {}
        for mot in mots_requete:
            tf_requete[mot] = 1.0 / len(mots_requete) if mots_requete else 0
        
        scores = []
        for conn in self.connaissances_stockees:
            onde_ref = self._motif_reference(conn['graine'])
            intensite = 0.0
            for n in range(7):
                reconstruction = self.hologramme[:,:,n] * onde_ref
                correlation = np.abs(np.sum(reconstruction * np.conj(onde_lecture)))
                intensite += correlation * H[n]/H_sum
            
            # === TF-IDF (remplace Jaccard) ===
            mots_conn = conn['mots_cles']
            score_tfidf = 0.0
            for mot in mots_conn:
                if mot in tf_requete:
                    idf = self.idf.get(mot, 1.0)
                    score_tfidf += tf_requete[mot] * idf
            
            # === Cosinus 7D (discrimination par domaine) ===
            vc = conn['vecteur_7d']
            dot = np.dot(vf, vc)
            norm_r = np.linalg.norm(vf); norm_c = np.linalg.norm(vc)
            cos_sim = max(0, dot/(norm_r*norm_c + 1e-10))
            
            # Score composite
            score_holographique = intensite / max(intensite, 1e-10)
            score_final = score_holographique + score_tfidf * 8.0 + cos_sim * 3.0
            
            scores.append((conn['id'], float(score_final), conn['texte'], conn.get('domaine','')))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return [(s[0], s[1], s[2]) for s in scores[:top_k] if s[1] > 1e-6]
    
    def injecter_corpus(self, corpus, domaine=""):
        for i, texte in enumerate(corpus):
            self.encoder(texte, f"{domaine}_{i:06d}", domaine)


# ==============================================================================
# IA UNIFIÉE CORRIGÉE
# ==============================================================================

class IAHarmoniqueCorrigee:
    """IA harmonique avec TF-IDF, injection complète, score cosinus."""
    
    def __init__(self, taille_hologramme=128):
        self.hologramme = HologrammeConnaissanceV2Ameliore(taille_hologramme)
        self.vocabulaire = {}
        self.embeddings = {}
        self._init_vocabulaire()
    
    def _init_vocabulaire(self):
        mots = [
            "univers","onde","harmonie","frequence","energie","matiere",
            "lumiere","temps","espace","constante","fondamental",
            "gravite","force","electromagnetique","nucleaire","quantique",
            "conscience","biologie","cellule","organe","cerveau",
            "est","et","de","la","le","les","des","une","un",
            "dans","par","pour","avec","sans","sur","sous",
        ]
        for mot in mots:
            self._ajouter_mot(mot)
    
    def _mot_vers_spectre(self, mot):
        s = np.zeros(7, dtype=np.float64)
        for i, c in enumerate(mot):
            s[(ord(c)+i)%7] += H[(ord(c)+i)%7]/H_sum
        n = np.linalg.norm(s)
        return s/n if n>0 else s
    
    def _ajouter_mot(self, mot):
        if mot not in self.vocabulaire:
            idx = len(self.vocabulaire)
            self.vocabulaire[mot] = idx
            self.embeddings[mot] = self._mot_vers_spectre(mot)
    
    def apprendre(self, texte, domaine=""):
        self.hologramme.encoder(texte, domaine=domaine)
        for mot in texte.lower().split():
            if mot not in self.vocabulaire:
                self._ajouter_mot(mot)
    
    def apprendre_corpus(self, corpus, domaine=""):
        for texte in corpus:
            self.apprendre(texte, domaine)
    
    def finaliser(self):
        """À appeler après toutes les injections pour calculer l'IDF."""
        self.hologramme.calculer_idf()
    
    def repondre(self, question):
        if self.hologramme.n_connaissances == 0:
            return "[VIDE] Aucune connaissance."
        resultats = self.hologramme.requete(question, top_k=3)
        if resultats:
            return f"[HOLOGRAMME] {resultats[0][2]}"
        return "[INCERTAIN] Aucune connaissance pertinente."


# ==============================================================================
# CHARGEUR
# ==============================================================================
def charger_et_injecter(ia, dossier="data/holograms"):
    """Charge tous les hologrammes et injecte TOUTES les connaissances."""
    total = 0
    for fichier_npy in sorted(glob.glob(os.path.join(dossier, "hologram64_*.npy"))):
        base = os.path.basename(fichier_npy)
        domaine = base.replace("hologram64_","").replace(".npy","")
        fichier_json = fichier_npy.replace(".npy","_data.json")
        
        textes = []
        if os.path.exists(fichier_json):
            with open(fichier_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'texts' in data:
                    textes = data['texts']
                elif isinstance(data, list):
                    textes = data
                elif isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, list) and len(v)>0 and isinstance(v[0], str):
                            textes = v; break
        
        n_avant = ia.hologramme.n_connaissances
        for texte in textes:
            if texte and len(texte.strip()) > 10:
                ia.apprendre(texte.strip(), domaine)
        n_injecte = ia.hologramme.n_connaissances - n_avant
        total += n_injecte
        print(f"    {domaine:<20s} : {n_injecte} connaissances")
    
    return total


# ==============================================================================
# TEST
# ==============================================================================
def test_corrige():
    print("="*70)
    print("IA HARMONO-HOLOGRAPHIQUE CORRIGÉE")
    print("TF-IDF + Injection complète + Score cosinus 7D")
    print("="*70)
    print()
    
    print("Chargement et injection de TOUTES les connaissances...")
    ia = IAHarmoniqueCorrigee(taille_hologramme=128)
    n = charger_et_injecter(ia)
    ia.finaliser()
    print(f"  TOTAL : {n} connaissances injectées")
    print(f"  Vocabulaire : {len(ia.vocabulaire)} mots")
    print(f"  IDF calculé sur {len(ia.hologramme.idf)} mots")
    print()
    
    requetes = [
        "quelle est la constante de Planck",
        "qui a decouvert la relativite",
        "quelle est la vitesse de la lumiere",
        "quelle est la masse de l electron",
        "qu est ce que le Big Bang",
        "qui est Einstein",
        "quelle est la constante gravitationnelle",
        "comment fonctionne la photosynthese",
        "qu est ce que la resonance de Schumann",
        "qu est ce que le principe holographique",
    ]
    
    print("Test de requêtes :")
    print()
    ok = 0
    for req in requetes:
        reponse = ia.repondre(req)
        print(f"  Q: \"{req}\"")
        print(f"  R: {reponse[:120]}")
        # Heuristique simple pour évaluer la pertinence
        bons_mots = {
            "Planck": ["planck", "6.626"],
            "relativite": ["einstein", "relativite"],
            "lumiere": ["lumiere", "299", "300"],
            "electron": ["electron", "9.109"],
            "Big Bang": ["big bang", "13.8"],
            "Einstein": ["einstein", "relativite", "physicien"],
            "gravitationnelle": ["gravitation", "6.674", "newton"],
            "photosynthese": ["photosynthese", "plante", "co2"],
            "Schumann": ["schumann", "7.83"],
            "holographique": ["holographique", "hologramme", "surface"],
        }
        for cle, mots_attendus in bons_mots.items():
            if cle.lower() in req.lower():
                if any(m in reponse.lower() for m in mots_attendus):
                    ok += 1
                break
        print()
    
    print(f"  Score estimé : {ok}/10")
    print()
    print("="*70)
    print("TERMINÉ")
    print("="*70)


if __name__ == "__main__":
    test_corrige()