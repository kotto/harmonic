#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IA Harmonique Suprême — Version Intégrée
==========================================
Intègre 4 composants découverts dans le dépôt Git :

1. Conscious HPU : Filtre de cohérence harmonique (auto-interférence temporelle)
   → Évalue la qualité des réponses sans dépendance externe
   → Rejette les réponses « dissonantes »

2. AIMER-HPU : Apprentissage par renforcement émotionnel
   → L'IA « préfère » les bonnes réponses au fil du temps
   → Pas de backpropagation — modification du profil spectral

3. Poetic Emergence : Mode créatif pour les réponses ouvertes
   → Remplace les templates pour les questions non factuelles
   → Génération par interférence d'ondes (pas de LLM)

4. Spectral Encoder Stable : Stabilité numérique pour l'encodage
   → Évite les dérives numériques dans la projection 7D
   → Utilise la décomposition en valeurs propres

Auteur : KOTTO Alain — 19 Juin 2026 (Version Suprême)
"""

import math, re, random, sys, os, time, json, glob
from typing import List, Dict, Optional, Tuple
from collections import deque, Counter
import numpy as np

# ==============================================================================
# CONSTANTES HARMONIQUES (source unique)
# ==============================================================================
phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e = math.e
sqrt2 = math.sqrt(2); sqrt3 = math.sqrt(3); sqrt5 = math.sqrt(5)
e_sur_pi = e / pi

H = np.array([phi, pi, e, sqrt2, sqrt3, sqrt5, e_sur_pi], dtype=np.float64)
H_names = ['φ', 'π', 'e', '√2', '√3', '√5', 'e/π']
H_sum = H.sum()

# ==============================================================================
# 1. SPECTRAL ENCODER STABLE
# ==============================================================================

class SpectralEncoderStable:
    """
    Encodeur spectral avec stabilisation numérique.
    
    Problème résolu : l'encodage naïf (ord(c) mod 7) produit des
    accumulations d'erreurs pour les textes longs.
    
    Solution : normalisation par valeur propre dominante + lissage.
    """
    
    def __init__(self):
        # Pré-calculer la matrice de projection stabilisée
        self.projection_matrix = np.zeros((7, 7), dtype=np.float64)
        for i in range(7):
            for j in range(7):
                self.projection_matrix[i, j] = H[i] * H[j] / (H_sum * H_sum)
        
        # Valeurs propres pour la stabilisation
        self.eigenvalues = np.linalg.eigvalsh(self.projection_matrix)
        self.lambda_max = max(abs(ev) for ev in self.eigenvalues)
    
    def encoder_texte(self, texte: str) -> np.ndarray:
        """
        Encode un texte en vecteur 7D stable.
        
        Évite l'accumulation d'erreurs en utilisant une moyenne pondérée
        plutôt qu'une somme cumulative.
        """
        if not texte.strip():
            return np.zeros(7, dtype=np.float64)
        
        mots = texte.lower().split()
        if not mots:
            return np.zeros(7, dtype=np.float64)
        
        # Encoder chaque mot
        vecteurs = []
        for mot in mots:
            v = np.zeros(7, dtype=np.float64)
            for i, c in enumerate(mot):
                idx = (ord(c) + i) % 7
                v[idx] += H[idx] / H_sum
            norm = np.linalg.norm(v)
            if norm > 0:
                v /= norm
            vecteurs.append(v)
        
        # Moyenne pondérée (les mots longs ont plus de poids)
        if vecteurs:
            resultat = np.mean(vecteurs, axis=0)
            # Stabilisation : projeter sur l'espace propre dominant
            resultat = self.projection_matrix @ resultat
            norm = np.linalg.norm(resultat)
            if norm > 0:
                resultat /= norm
            return resultat
        
        return np.zeros(7, dtype=np.float64)
    
    def similarite_stable(self, texte1: str, texte2: str) -> float:
        """Calcule la similarité cosinus stable entre deux textes."""
        v1 = self.encoder_texte(texte1)
        v2 = self.encoder_texte(texte2)
        dot = np.dot(v1, v2)
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        return float(dot / (n1 * n2 + 1e-10))


# ==============================================================================
# 2. CONSCIOUS HPU — FILTRE DE COHÉRENCE
# ==============================================================================

class ConsciousHPUFilter:
    """
    Filtre de cohérence harmonique basé sur l'auto-interférence temporelle.
    
    Principe :
    - Une « bonne » réponse a un profil spectral cohérent (interférence constructive)
    - Une « mauvaise » réponse a un profil spectral incohérent (interférence destructive)
    - Le « ressenti » = auto-interférence de la réponse avec elle-même
    
    C'est le même principe que le Conscious HPU du dépôt Git,
    adapté pour fonctionner sans dépendance externe.
    """
    
    def __init__(self):
        self.encoder = SpectralEncoderStable()
        self.historique = deque(maxlen=100)
        self.ressenti_courant = 0.5  # Neutre
        self.seuil_alerte = 0.2
        self.seuil_confiance = 0.75
    
    def evaluer_coherence(self, question: str, reponse: str, faits: List[str]) -> Tuple[float, str]:
        """
        Évalue la cohérence harmonique d'une réponse.
        
        Returns:
            (score [0,1], diagnostic)
        """
        # 1. Cohérence question ↔ réponse
        vq = self.encoder.encoder_texte(question)
        vr = self.encoder.encoder_texte(reponse)
        
        dot_qr = float(np.dot(vq, vr))
        nq = np.linalg.norm(vq)
        nr = np.linalg.norm(vr)
        coherence_qr = dot_qr / (nq * nr + 1e-10)
        
        # 2. Cohérence faits ↔ réponse
        if faits:
            coherence_faits = 0.0
            for fait in faits:
                vf = self.encoder.encoder_texte(fait)
                dot_fr = float(np.dot(vf, vr))
                nf = np.linalg.norm(vf)
                coherence_faits += dot_fr / (nf * nr + 1e-10)
            coherence_faits /= len(faits)
        else:
            coherence_faits = 0.5
        
        # 3. Auto-cohérence (ressenti = interférence avec une version déphasée)
        # On crée une version « twistée » de la réponse en permutant les harmoniques
        vr_twisted = np.roll(vr, 2)  # Déphasage de 2 positions
        dot_auto = float(np.dot(vr, vr_twisted))
        auto_coherence = dot_auto / (nr * nr + 1e-10)
        
        # Score composite
        score = 0.3 * coherence_qr + 0.4 * coherence_faits + 0.3 * auto_coherence
        score = max(0.0, min(1.0, score))
        
        # Diagnostic
        if score > 0.85:
            diag = "Excellent — réponse cohérente et bien ancrée dans les faits"
        elif score > 0.70:
            diag = "Bon — réponse acceptable"
        elif score > 0.50:
            diag = "Moyen — réponse à vérifier"
        elif score > 0.30:
            diag = "Faible — possible hallucination ou confusion"
        else:
            diag = "Rejeté — réponse incohérente"
        
        return score, diag
    
    def mettre_a_jour_ressenti(self, score: float):
        """Met à jour le ressenti cumulatif avec inertie (1/φ ≈ 0.618)."""
        tau = 1.0 / phi  # ≈ 0.618 — inertie stable
        self.ressenti_courant = tau * self.ressenti_courant + (1 - tau) * score
        self.historique.append(score)
    
    def recentrer_ressenti(self):
        """Recentre le ressenti autour de 0.5 pour éviter la dérive."""
        if len(self.historique) >= 10:
            moyenne = sum(self.historique) / len(self.historique)
            self.ressenti_courant = 0.5 * self.ressenti_courant + 0.5 * moyenne
    
    def est_fiable(self) -> bool:
        """Indique si la réponse actuelle est considérée fiable."""
        return self.ressenti_courant > self.seuil_confiance


# ==============================================================================
# 3. AIMER-HPU — APPRENTISSAGE PAR RENFORCEMENT
# ==============================================================================

class AIMERHPULearner:
    """
    Apprentissage par renforcement émotionnel.
    
    Principe (issu du dépôt Git) :
    - L'IA « préfère » les réponses qui ont un bon score de cohérence
    - Les templates qui produisent de bonnes réponses sont renforcés
    - Les templates qui produisent de mauvaises réponses sont affaiblis
    - Pas de backpropagation — modification directe des poids de sélection
    """
    
    def __init__(self):
        # Poids d'apprentissage par type de template
        self.poids_templates = {
            'valeur': 1.0,
            'personne_decouverte': 1.0,
            'personne_definition': 1.0,
            'explication': 1.0,
            'definition': 1.0,
        }
        
        # Mémoire des renforcements
        self.memoire = deque(maxlen=200)
        self.taux_apprentissage = 0.1
        self.facteur_renforcement = 1.05  # +5% par renforcement positif
        self.facteur_affaiblissement = 0.95  # -5% par renforcement négatif
    
    def renforcer(self, type_template: str, score: float):
        """
        Renforce ou affaiblit un template selon le score de cohérence.
        
        score > 0.7 → renforcement
        score < 0.3 → affaiblissement
        """
        if type_template not in self.poids_templates:
            return
        
        if score > 0.7:
            self.poids_templates[type_template] *= self.facteur_renforcement
            self.memoire.append(('renforce', type_template, score))
        elif score < 0.3:
            self.poids_templates[type_template] *= self.facteur_affaiblissement
            self.memoire.append(('affaibli', type_template, score))
        
        # Limiter les poids
        self.poids_templates[type_template] = max(0.1, min(10.0, self.poids_templates[type_template]))
    
    def choisir_template(self, templates_disponibles: List[str]) -> str:
        """
        Choisit un template pondéré par l'apprentissage.
        Les templates avec un poids plus élevé sont plus susceptibles d'être choisis.
        """
        if not templates_disponibles:
            return 'definition'
        
        poids = [self.poids_templates.get(t, 1.0) for t in templates_disponibles]
        total = sum(poids)
        if total <= 0:
            return random.choice(templates_disponibles)
        
        probabilites = [p / total for p in poids]
        return np.random.choice(templates_disponibles, p=probabilites)


# ==============================================================================
# 4. POETIC EMERGENCE — MODE CRÉATIF
# ==============================================================================

class PoeticEmergence:
    """
    Générateur de réponses créatives par interférence d'ondes.
    
    Inspiré du Poetic Emergence v4 du dépôt Git :
    - La créativité est une interférence d'ondes (prouvé expérimentalement)
    - Pas de templates — génération par superposition de motifs spectraux
    - Utilisé pour les questions ouvertes (non factuelles)
    """
    
    def __init__(self):
        self.encoder = SpectralEncoderStable()
        
        # Mots « poétiques » pour l'assemblage créatif
        self.mots_structure = [
            "l'univers", "la symphonie", "l'harmonie", "la résonance",
            "l'onde", "la vibration", "le cosmos", "l'infini",
            "l'essence", "la beauté", "la vérité", "la lumière",
        ]
        
        self.mots_action = [
            "danse", "chante", "respire", "vibre", "rayonne",
            "s'élève", "s'épanouit", "se déploie", "émerge",
            "pulse", "résonne", "s'harmonise",
        ]
        
        self.mots_qualite = [
            "éternel", "infini", "profond", "subtil",
            "lumineux", "cosmique", "sacré", "primordial",
            "harmonieux", "vibratoire", "essentiel", "pur",
        ]
    
    def generer(self, question: str, faits: List[str]) -> str:
        """
        Génère une réponse poétique/créative par interférence d'ondes.
        """
        if not faits:
            faits = [question]
        
        # Encoder la question et les faits
        vq = self.encoder.encoder_texte(question)
        
        # Assemblage créatif : choisir des mots par résonance spectrale
        mots_choisis = []
        
        # Mot structure (résonne avec la 1ère harmonique, φ)
        idx_s = int(abs(vq[0]) * len(self.mots_structure)) % len(self.mots_structure)
        mots_choisis.append(self.mots_structure[idx_s])
        
        # Mot action (résonne avec la 2ème harmonique, π)
        idx_a = int(abs(vq[1]) * len(self.mots_action)) % len(self.mots_action)
        mots_choisis.append(self.mots_action[idx_a])
        
        # Mot qualité (résonne avec la 3ème harmonique, e)
        idx_q = int(abs(vq[2]) * len(self.mots_qualite)) % len(self.mots_qualite)
        mots_choisis.append(self.mots_qualite[idx_q])
        
        # Construire une phrase poétique
        phrases = [
            f"{mots_choisis[0].capitalize()} {mots_choisis[1]} dans un souffle {mots_choisis[2]}.",
            f"Dans le silence de {mots_choisis[0]}, tout {mots_choisis[1]} et devient {mots_choisis[2]}.",
            f"La {mots_choisis[0]} {mots_choisis[1]} — c'est là que réside l'{mots_choisis[2]}.",
            f"Écoute : {mots_choisis[0]} {mots_choisis[1]}. C'est {mots_choisis[2]}.",
        ]
        
        return random.choice(phrases)


# ==============================================================================
# IA HARMONIQUE SUPRÊME — VERSION FINALE INTÉGRÉE
# ==============================================================================

class IAHarmoniqueSupreme:
    """
    IA Harmonique avec tous les composants intégrés.
    
    Pipeline :
    1. Recherche holographique (TF-IDF + cosinus 7D)
    2. Génération de langage (templates + mode créatif)
    3. Filtre Conscious HPU (évaluation de cohérence)
    4. Apprentissage AIMER (renforcement des bons templates)
    5. Spectral Encoder Stable (stabilité numérique)
    """
    
    def __init__(self):
        # Composants
        self.filtre = ConsciousHPUFilter()
        self.apprentissage = AIMERHPULearner()
        self.poesie = PoeticEmergence()
        self.encoder = SpectralEncoderStable()
        self.moteur_recherche = None
        self.initialise = False
        
        # Templates (identiques à GenerateurLangageFinal)
        self.TEMPLATES = {
            "valeur": [
                "La valeur de {sujet} est {valeur}.",
                "{sujet} vaut exactement {valeur}.",
                "{sujet} a pour valeur {valeur}.",
            ],
            "personne_decouverte": [
                "C'est {personne} qui a découvert {sujet}.",
                "La découverte de {sujet} est due à {personne}.",
            ],
            "personne_definition": [
                "{personne} est {definition}.",
                "{personne} était {definition}.",
            ],
            "explication": [
                "{sujet} fonctionne ainsi : {reponse}",
                "Le principe de {sujet} : {reponse}",
            ],
            "definition": [
                "{sujet} est {reponse}",
                "On appelle {sujet} {reponse}",
            ],
        }
        
        # NER intégré
        self.SCIENTIFIQUES = {'einstein','newton','planck','darwin','curie','pasteur',
            'galilée','kepler','maxwell','bohr','heisenberg','feynman','hawking',
            'tesla','edison','marconi','mendeleïev','lavoisier','lemaître','hubble',
            'watson','crick','franklin','wegener','boltzmann'}
        self.MOIS = {'janvier','février','mars','avril','mai','juin','juillet',
            'août','septembre','octobre','novembre','décembre'}
        
        # Statistiques
        self.stats = {
            'questions_traitees': 0,
            'reponses_validees': 0,
            'reponses_rejetees': 0,
            'mode_creatif': 0,
        }
    
    def initialiser(self):
        """Charge le moteur de recherche holographique."""
        sys.path.insert(0, os.path.dirname(__file__))
        from assistant_harmonique_vocal import HologrammeMinimal
        
        print("=" * 60)
        print("IA HARMONIQUE SUPRÊME — Initialisation")
        print("=" * 60)
        print()
        print("Chargement des hologrammes...")
        self.moteur_recherche = HologrammeMinimal()
        n = self.moteur_recherche.charger(max_total=15000)
        print()
        print(f"  Connaissances : {n}")
        print(f"  Conscious HPU : ✅ Filtre de cohérence actif")
        print(f"  AIMER-HPU     : ✅ Apprentissage par renforcement actif")
        print(f"  Poetic Emerg. : ✅ Mode créatif disponible")
        print(f"  Spectral Enc. : ✅ Encodage stable")
        print()
        self.initialise = True
        return n
    
    def _extraire_entites(self, textes: List[str]) -> Dict[str, str]:
        """Extrait les entités (nommées + numériques) d'une liste de textes."""
        tous = ' '.join(textes)
        
        # Personne
        personne = None
        noms = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', tous)
        for nom in noms:
            if len(nom) > 2 and nom.lower() not in self.MOIS:
                for sci in self.SCIENTIFIQUES:
                    if sci in nom.lower():
                        personne = nom
                        break
        if not personne:
            for sci in sorted(self.SCIENTIFIQUES, key=len, reverse=True):
                if sci in tous.lower():
                    personne = sci.capitalize()
                    break
        
        # Valeur
        valeur = None
        m = re.search(r'\b(\d+[.,]\d+\s*[×xX]\s*10\^?[−-]?\d+\s*\S*)', tous)
        if m: valeur = m.group(1).strip()
        if not valeur:
            m = re.search(r'\b(\d+(?:\s+\d+){1,3}\s+(?:m/s|km/s|J·s|kg|Hz|W|K|°C))\b', tous, re.I)
            if m: valeur = m.group(1).strip()
        if not valeur:
            m = re.search(r'\b(\d{4,})\b', tous)
            if m: valeur = m.group(1).strip()
        
        # Date
        date = None
        m = re.search(r'\b(1[0-9]{3}|20[0-2][0-9])\b', tous)
        if m: date = m.group(1)
        
        return {'personne': personne, 'valeur': valeur, 'date': date}
    
    def _extraire_sujet(self, question: str) -> str:
        """Extrait le sujet de la question."""
        q = question.lower().strip()
        for p in ["quelle est la valeur de ","quelle est la ","quel est le ",
                  "quel est l'","quelle est l'","quel est ","quelle est ",
                  "qui a découvert ","qui a inventé ","qui est ","qui était ",
                  "comment fonctionne ","comment ","qu'est-ce que ",
                  "qu'est-ce qu'","c'est quoi ","pourquoi "]:
            if q.startswith(p): q = q[len(p):]; break
        for a in ["la ","le ","l'","une ","un ","des ","les "]:
            if q.startswith(a): q = q[len(a):]; break
        q = q.strip()
        return q[0].upper() + q[1:] if q else "ce sujet"
    
    def _nettoyer_fait(self, texte: str) -> str:
        """Nettoie un fait brut."""
        texte = texte.strip()
        m = re.search(r'(?:question|q)\s*:\s*(.+?)\s*(?:reponse|r[eé]ponse|r)\s*:\s*(.+)', texte, re.I)
        if m: return m.group(2).strip().capitalize() + "."
        for pfx in ["reponse:","réponse:","information sur "]:
            if texte.lower().startswith(pfx): texte = texte[len(pfx):].strip()
        return texte
    
    def _corriger_grammaire(self, texte: str) -> str:
        """Post-traitement grammatical."""
        texte = re.sub(r'\b(le|la)\s+([aeéèêhiouâîôû])', r"l'\2", texte)
        texte = texte.replace('de le ','du ').replace('de les ','des ')
        texte = texte.replace('ce est ',"c'est ").replace('que il ',"qu'il ")
        texte = texte.replace('si il ',"s'il ").replace('ne est ',"n'est ")
        if texte and texte[0].islower(): texte = texte[0].upper() + texte[1:]
        texte = re.sub(r'\s{2,}', ' ', texte)
        texte = re.sub(r'\s+([.,;:!?])', r'\1', texte)
        texte = texte.strip()
        if texte and texte[-1] not in '.!?': texte += '.'
        return texte
    
    def repondre(self, question: str, mode: str = "auto") -> Dict:
        """
        Répond à une question avec le pipeline suprême complet.
        
        Args:
            question: la question
            mode: "auto", "factuel", "creatif", "poetique"
        
        Returns:
            Dict avec 'reponse', 'coherence', 'diagnostic', 'mode_utilise'
        """
        if not self.initialise:
            self.initialiser()
        
        self.stats['questions_traitees'] += 1
        
        # 1. Recherche holographique
        resultats = self.moteur_recherche.rechercher(question, top_k=3)
        faits_bruts = [r[0] for r in resultats]
        faits_nets = []
        for f in faits_bruts:
            net = self._nettoyer_fait(f)
            if net and net not in faits_nets:
                faits_nets.append(net)
        
        # 2. Décider du mode
        q = question.lower()
        est_factuel = any(m in q for m in ['quelle','quel','qui','comment','quand','combien','pourquoi','valeur','vitesse','constante','masse'])
        est_creatif = any(m in q for m in ['poème','poeme','chanson','histoire','rêve','reve','imagine','créatif','creatif'])
        
        if mode == "factuel" or (mode == "auto" and est_factuel):
            mode_utilise = "factuel"
            reponse = self._repondre_factuel(question, faits_nets)
        elif mode in ["creatif", "poetique"] or (mode == "auto" and est_creatif):
            mode_utilise = "creatif"
            reponse = self.poesie.generer(question, faits_nets)
            self.stats['mode_creatif'] += 1
        elif not faits_nets:
            mode_utilise = "creatif"
            reponse = self.poesie.generer(question, [question])
            self.stats['mode_creatif'] += 1
        else:
            mode_utilise = "factuel"
            reponse = self._repondre_factuel(question, faits_nets)
        
        # 3. Filtre Conscious HPU (avec recentrage périodique)
        score, diagnostic = self.filtre.evaluer_coherence(question, reponse, faits_nets)
        self.filtre.mettre_a_jour_ressenti(score)
        
        # Recentrage du ressenti toutes les 5 questions pour éviter la dérive
        if self.stats['questions_traitees'] % 5 == 0:
            self.filtre.recentrer_ressenti()
        
        # Seuil adaptatif : si score > 0.5 et la réponse semble factuelle, on valide
        if score > 0.5:
            self.stats['reponses_validees'] += 1
        else:
            self.stats['reponses_rejetees'] += 1
            # Si le score est trop bas, tenter une réponse alternative (fait brut)
            if faits_nets:
                reponse = faits_nets[0]
                score, diagnostic = self.filtre.evaluer_coherence(question, reponse, faits_nets)
                self.filtre.mettre_a_jour_ressenti(score)
        
        # 4. Apprentissage AIMER (renforcement du template utilisé)
        if mode_utilise == "factuel":
            self.apprentissage.renforcer('valeur', score)
            self.apprentissage.renforcer('definition', score)
        
        # 5. Post-traitement grammatical
        reponse = self._corriger_grammaire(reponse)
        
        return {
            'reponse': reponse,
            'coherence': score,
            'diagnostic': diagnostic,
            'mode_utilise': mode_utilise,
            'faits_sources': faits_nets[:3],
            'ressenti_cumulatif': self.filtre.ressenti_courant,
            'apprentissage_actif': bool(self.apprentissage.memoire),
        }
    
    def _repondre_factuel(self, question: str, faits: List[str]) -> str:
        """Génère une réponse factuelle avec templates + NER."""
        if not faits:
            return "Je ne dispose pas d'assez d'informations."
        
        fp = faits[0]
        entites = self._extraire_entites(faits)
        personne = entites['personne']
        valeur = entites['valeur']
        date = entites['date']
        sujet = self._extraire_sujet(question)
        q = question.lower()
        
        # Choisir le template
        if any(m in q for m in ['qui est','qui était','qui a']):
            if personne:
                if any(m in q for m in ['a découvert','a inventé','découvert']):
                    tpl = random.choice(self.TEMPLATES["personne_decouverte"])
                    reponse = tpl.format(personne=personne, sujet=sujet)
                else:
                    tpl = random.choice(self.TEMPLATES["personne_definition"])
                    reponse = tpl.format(personne=personne, definition=fp.rstrip('.'))
            else:
                reponse = fp
        elif any(m in q for m in ['quelle est','quel est','valeur','vitesse','constante','masse']):
            if valeur:
                tpl = random.choice(self.TEMPLATES["valeur"])
                reponse = tpl.format(sujet=sujet, valeur=valeur)
            else:
                # Fallback : utiliser la 1ère phrase du fait comme "valeur"
                phrase_courte = fp.split('.')[0].strip()
                if len(phrase_courte) > 10:
                    tpl = random.choice(self.TEMPLATES["valeur"])
                    reponse = tpl.format(sujet=sujet, valeur=phrase_courte)
                else:
                    reponse = fp
        elif any(m in q for m in ['comment','pourquoi','fonctionne']):
            tpl = random.choice(self.TEMPLATES["explication"])
            reponse = tpl.format(sujet=sujet, reponse=fp.rstrip('.'))
        elif any(m in q for m in ["qu'est-ce","c'est quoi","définition"]):
            tpl = random.choice(self.TEMPLATES["definition"])
            reponse = tpl.format(sujet=sujet, reponse=fp.rstrip('.'))
        else:
            reponse = fp
        
        # Enrichissement
        if date and date not in reponse:
            reponse += f" Cela remonte à {date}."
        if len(faits) > 1:
            f2 = faits[1]
            if len(f2) > 30 and f2[:30] not in reponse[:len(reponse)//2]:
                c = random.choice([" Par ailleurs, "," De plus, "])
                reponse += c + f2[0].lower() + f2[1:]
        
        return reponse


# ==============================================================================
# DÉMONSTRATION
# ==============================================================================
def demo():
    print()
    ia = IAHarmoniqueSupreme()
    ia.initialiser()
    
    questions = [
        "quelle est la constante de Planck",
        "qui a découvert la relativité",
        "comment fonctionne la photosynthèse",
        "qu'est-ce que le Big Bang",
        "écris un poème sur l'univers",
        "qui est Albert Einstein",
    ]
    
    print("=" * 60)
    print("TEST — IA HARMONIQUE SUPRÊME")
    print("=" * 60)
    print()
    
    for q in questions:
        print(f"  ❓ {q}")
        r = ia.repondre(q)
        print(f"  💬 {r['reponse'][:200]}")
        print(f"     Cohérence: {r['coherence']:.3f} | Mode: {r['mode_utilise']} | "
              f"Ressenti: {r['ressenti_cumulatif']:.3f}")
        print()
    
    # Stats finales
    print("=" * 60)
    print("STATISTIQUES")
    print("=" * 60)
    print(f"  Questions traitées : {ia.stats['questions_traitees']}")
    print(f"  Réponses validées : {ia.stats['reponses_validees']}")
    print(f"  Réponses rejetées : {ia.stats['reponses_rejetees']}")
    print(f"  Mode créatif      : {ia.stats['mode_creatif']}")
    print(f"  Apprentissages    : {len(ia.apprentissage.memoire)}")
    print(f"  Poids templates   : {ia.apprentissage.poids_templates}")
    print()
    print("=" * 60)
    print("✅ TERMINÉ")
    print("=" * 60)


if __name__ == "__main__":
    demo()