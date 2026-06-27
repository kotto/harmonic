#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entraîneur Harmonique (Phases 5+6)
===================================
Phase 5 : Apprentissage non supervisé des transitions de bigrammes.
Phase 6 : Templates grammaticaux pour structurer les réponses.

Intégré avec le décodeur harmonique pour produire des phrases
cohérentes sans dépendance externe.

Auteur : KOTTO Alain — 19 Juin 2026
"""

import math, time, sys, os, random
from typing import List, Tuple, Dict, Optional, Set
from collections import Counter, defaultdict
import numpy as np

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
H_sum = H.sum()

# ==============================================================================
# PHASE 5 : ENTRAÎNEMENT NON SUPERVISÉ (BIGRAMMES)
# ==============================================================================

class EntraineurBigrammes:
    """
    Apprend les transitions naturelles entre tokens à partir d'un corpus.
    
    Pour chaque bigramme (mot_i, mot_{i+1}) dans le corpus :
    - on incrémente un compteur de co-occurrence
    - on calcule un score de transition normalisé
    
    Ce score est utilisé pour biaiser le décodeur vers des
    transitions naturelles.
    """
    
    def __init__(self):
        # Compteurs de bigrammes : (mot_i, mot_{i+1}) → count
        self.bigrammes = defaultdict(Counter)
        # Total des occurrences par mot source
        self.totaux = Counter()
        # Vocabulaire complet
        self.vocab = set()
    
    def entrainer(self, corpus: List[str]):
        """
        Apprend les transitions de bigrammes depuis un corpus.
        
        Args:
            corpus: liste de phrases (strings)
        """
        for phrase in corpus:
            mots = phrase.lower().split()
            if len(mots) < 2:
                continue
            
            self.vocab.update(mots)
            
            for i in range(len(mots) - 1):
                mot_i = mots[i]
                mot_j = mots[i + 1]
                self.bigrammes[mot_i][mot_j] += 1
                self.totaux[mot_i] += 1
    
    def score_transition(self, mot_source: str, mot_cible: str, lissage: float = 0.01) -> float:
        """
        Calcule le score de transition P(mot_cible | mot_source).
        
        Avec lissage additif pour les transitions non observées.
        """
        if mot_source in self.bigrammes and mot_cible in self.bigrammes[mot_source]:
            count = self.bigrammes[mot_source][mot_cible]
            total = self.totaux[mot_source]
            return count / total
        else:
            # Lissage additif
            return lissage / (self.totaux.get(mot_source, 1) + 1)
    
    def transitions_possibles(self, mot_source: str, top_k: int = 20) -> List[Tuple[str, float]]:
        """
        Retourne les transitions les plus probables depuis un mot source.
        """
        if mot_source not in self.bigrammes:
            return []
        
        total = self.totaux[mot_source]
        scores = [(cible, count / total)
                  for cible, count in self.bigrammes[mot_source].most_common(top_k)]
        return scores


# ==============================================================================
# PHASE 6 : TEMPLATES GRAMMATICAUX
# ==============================================================================

class TemplatesGrammaticaux:
    """
    Génère des réponses structurées en utilisant des templates
    grammaticaux adaptés au type de question.
    
    Types de questions détectés :
    - "quelle/quel est" → définition
    - "qui" → personne/historique
    - "comment" → explication/mécanisme
    - "qu'est-ce que" → définition/concept
    - "pourquoi" → causalité
    """
    
    def __init__(self):
        self.templates = {
            "definition": [
                "{sujet} est {reponse}.",
                "{sujet} désigne {reponse}.",
                "On appelle {sujet} {reponse}.",
                "{sujet} correspond à {reponse}.",
            ],
            "personne": [
                "C'est {sujet} qui a découvert {reponse}.",
                "{reponse} a été découvert par {sujet}.",
                "{sujet} est le scientifique derrière {reponse}.",
                "La découverte de {reponse} est due à {sujet}.",
            ],
            "explication": [
                "{sujet} fonctionne de la manière suivante : {reponse}.",
                "Le principe de {sujet} repose sur {reponse}.",
                "{sujet} consiste en {reponse}.",
                "Pour comprendre {sujet}, il faut savoir que {reponse}.",
            ],
            "valeur": [
                "{sujet} vaut exactement {reponse}.",
                "La valeur de {sujet} est {reponse}.",
                "{sujet} est égal à {reponse}.",
                "On mesure {sujet} comme étant {reponse}.",
            ],
            "date_evenement": [
                "{sujet} s'est produit en {reponse}.",
                "{sujet} date de {reponse}.",
                "C'est en {reponse} que {sujet} a eu lieu.",
                "{reponse} est la date clé de {sujet}.",
            ],
            "general": [
                "{sujet} : {reponse}.",
                "Concernant {sujet}, {reponse}.",
                "À propos de {sujet} : {reponse}.",
                "{reponse} — voilà ce qu'on sait de {sujet}.",
            ],
        }
    
    def detecter_type_question(self, question: str) -> str:
        """Détecte le type de question à partir des mots-clés."""
        q = question.lower()
        
        if any(mot in q for mot in ["quelle est", "quel est", "quelle", "quel"]):
            if any(mot in q for mot in ["valeur", "vitesse", "constante", "masse", "égale", "vaut"]):
                return "valeur"
            if any(mot in q for mot in ["date", "quand", "année", "siècle"]):
                return "date_evenement"
            return "definition"
        
        if any(mot in q for mot in ["qui", "qui a", "découvert"]):
            return "personne"
        
        if any(mot in q for mot in ["comment", "fonctionne", "marche", "passe"]):
            return "explication"
        
        if any(mot in q for mot in ["qu'est-ce que", "c'est quoi", "définition"]):
            return "definition"
        
        if any(mot in q for mot in ["pourquoi", "cause", "raison"]):
            return "explication"
        
        return "general"
    
    def extraire_sujet(self, question: str, type_q: str) -> str:
        """Extrait le sujet de la question."""
        q = question.lower()
        
        # Patterns de nettoyage
        nettoyages = [
            "quelle est la valeur de ", "quelle est la ", "quel est le ", "quel est l'",
            "quelle est l'", "quel est ", "quelle est ",
            "qui a découvert ", "qui a inventé ", "qui est ", "qui était ",
            "comment fonctionne ", "comment marche ", "comment ",
            "qu'est-ce que ", "qu'est-ce qu'", "c'est quoi ",
            "pourquoi ", "explique ", "décris ",
        ]
        
        sujet = q
        for pattern in nettoyages:
            if sujet.startswith(pattern):
                sujet = sujet[len(pattern):]
                break
        
        # Nettoyer les articles restants
        for art in ["la ", "le ", "l'", "une ", "un ", "des ", "les "]:
            if sujet.startswith(art):
                sujet = sujet[len(art):]
                break
        
        return sujet.strip()
    
    def formuler(self, question: str, reponse_brute: str) -> str:
        """
        Formule une réponse en utilisant le template approprié.
        
        Args:
            question: la question posée
            reponse_brute: la réponse factuelle (texte brut)
        
        Returns:
            Réponse formulée
        """
        type_q = self.detecter_type_question(question)
        sujet = self.extraire_sujet(question, type_q)
        
        # Nettoyer la réponse brute (enlever les tirets, les numéros)
        reponse = reponse_brute.strip()
        for prefix in ["reponse: ", "réponse: ", "reponse :", "réponse :"]:
            if reponse.lower().startswith(prefix):
                reponse = reponse[len(prefix):]
        
        # Réduire la réponse à une phrase courte
        phrases = reponse.split(".")
        reponse_courte = phrases[0].strip() if phrases else reponse
        if len(reponse_courte) > 150:
            reponse_courte = reponse_courte[:147] + "..."
        
        # Choisir un template aléatoire du type approprié
        templates_dispo = self.templates.get(type_q, self.templates["general"])
        template = random.choice(templates_dispo)
        
        return template.format(sujet=sujet.capitalize(), reponse=reponse_courte)


# ==============================================================================
# GÉNÉRATEUR HARMONIQUE COMPLET (Phase 5 + 6 intégrées)
# ==============================================================================

class GenerateurHarmoniqueComplet:
    """
    Générateur de langage harmonique complet.
    
    Combine :
    - Décodeur auto-régressif (Phase 1)
    - Entraînement bigrammes (Phase 5)
    - Templates grammaticaux (Phase 6)
    
    Pour produire des réponses naturelles à partir de faits.
    """
    
    def __init__(self, decodeur, entraineur: EntraineurBigrammes,
                 templates: TemplatesGrammaticaux):
        self.decodeur = decodeur
        self.entraineur = entraineur
        self.templates = templates
        self.tokeniseur = decodeur.tokeniseur
    
    def _score_bigramme(self, token_precedent: Optional[str],
                        token_candidat: str) -> float:
        """
        Calcule le bonus de score basé sur les bigrammes appris.
        """
        if token_precedent is None:
            return 1.0
        
        proba = self.entraineur.score_transition(token_precedent, token_candidat)
        # Amplifier les transitions apprises
        return 1.0 + proba * 3.0 if proba > 0.01 else 1.0
    
    def _generer_avec_bigrammes(self, contexte: str, max_tokens: int = 50,
                                 temperature: float = 0.5) -> str:
        """
        Génération avec conditionnement par bigrammes.
        
        À chaque étape, le score d'un token = 
        cosinus(état, embedding(token)) × bonus_bigramme(token_précédent, token)
        """
        from decodeur_harmonique import DecodeurHarmonique
        
        etat = self.decodeur._initialiser_etat(contexte)
        tokens_generees = []
        tokens_vus = set()
        dernier_mot = None
        
        for _ in range(max_tokens):
            scores = []
            for tid in self.decodeur.tokeniseur.embeddings:
                if tid in self.decodeur.tokens_speciaux:
                    continue
                
                score_cos = self.decodeur._score_cosinus(etat, tid)
                if score_cos <= 0:
                    continue
                
                # Bonus bigramme (Phase 5)
                mot_candidat = self.decodeur.tokeniseur.id_to_token.get(tid, "")
                bonus = self._score_bigramme(dernier_mot, mot_candidat)
                
                # Pénalité de répétition
                if tid in tokens_vus:
                    score_cos *= 0.7
                
                score_final = score_cos * bonus
                scores.append((tid, score_final))
            
            if not scores:
                break
            
            # Échantillonner avec température
            ids = np.array([s[0] for s in scores], dtype=np.int32)
            vals = np.array([s[1] for s in scores], dtype=np.float64)
            
            if temperature > 0:
                vals = vals / temperature
                vals = np.exp(vals - np.max(vals))
                vals = vals / vals.sum()
                idx = np.random.choice(len(ids), p=vals)
            else:
                idx = np.argmax(vals)
            
            next_token = int(ids[idx])
            tokens_generees.append(next_token)
            tokens_vus.add(next_token)
            
            # Mettre à jour le dernier mot
            dernier_mot = self.decodeur.tokeniseur.id_to_token.get(next_token, "")
            
            # Évoluer l'état
            etat = self.decodeur._evoluer_etat(etat, next_token)
        
        return self.tokeniseur.decoder(tokens_generees)
    
    def generer_reponse(self, question: str, faits: List[str],
                        mode: str = "auto") -> str:
        """
        Génère une réponse complète à partir de faits.
        
        Args:
            question: la question
            faits: liste de textes factuels trouvés
            mode: "auto" (choisit le meilleur), "template" (template grammatical),
                  "bigramme" (génération pure), "factuel" (meilleur fait brut)
        
        Returns:
            Réponse en langage naturel
        """
        if not faits:
            return "[Aucune information trouvée]"
        
        # Mode template : utiliser les templates grammaticaux (Phase 6)
        if mode in ["auto", "template"]:
            # Sélectionner le meilleur fait
            meilleur_fait = faits[0]
            
            # Si on a un fait de type Q/R, extraire la réponse
            if "reponse:" in meilleur_fait.lower() or "réponse:" in meilleur_fait.lower():
                for ligne in meilleur_fait.split("."):
                    if "reponse:" in ligne.lower() or "réponse:" in ligne.lower():
                        meilleur_fait = ligne.strip()
                        break
            
            reponse_template = self.templates.formuler(question, meilleur_fait)
            
            # Si le template a fonctionné (contient des informations)
            if len(reponse_template) > 30 and reponse_template != meilleur_fait[:50]:
                return reponse_template
        
        # Mode bigramme : génération pure (Phase 5)
        if mode in ["auto", "bigramme"]:
            contexte = f"{question} {' '.join(faits[:2])}"
            texte_genere = self._generer_avec_bigrammes(contexte, max_tokens=30, temperature=0.4)
            
            # Si la génération a produit quelque chose de raisonnable
            if len(texte_genere.split()) > 3:
                return texte_genere
        
        # Fallback : meilleur fait brut
        return faits[0]


# ==============================================================================
# DÉMONSTRATION
# ==============================================================================
def demo():
    """Démonstration complète des Phases 5 et 6."""
    print("=" * 60)
    print("ENTRAÎNEUR HARMONIQUE (Phases 5+6)")
    print("Bigrammes + Templates Grammaticaux")
    print("=" * 60)
    print()
    
    # Charger le corpus
    print("Chargement du corpus d'entraînement...")
    from assistant_harmonique_vocal import HologrammeMinimal
    
    holo = HologrammeMinimal()
    holo.charger(max_total=10000)
    corpus = [c['texte'] for c in holo.connaissances[:5000]]
    print(f"  {len(corpus)} textes chargés")
    print()
    
    # === Phase 5 : Entraînement bigrammes ===
    print("Phase 5 : Entraînement des bigrammes...")
    t1 = time.time()
    entraineur = EntraineurBigrammes()
    entraineur.entrainer(corpus)
    t_bigrammes = time.time() - t1
    print(f"  {len(entraineur.bigrammes):,} bigrammes appris en {t_bigrammes:.1f}s")
    print()
    
    # Exemples de transitions apprises
    print("  Transitions apprises (exemples) :")
    for mot_test in ["la", "constante", "de", "est", "le", "lumiere", "big", "einstein"]:
        if mot_test in entraineur.bigrammes:
            tops = entraineur.transitions_possibles(mot_test, top_k=3)
            print(f"    \"{mot_test}\" → {', '.join(f'{m}({s:.2f})' for m,s in tops)}")
    print()
    
    # === Phase 6 : Templates grammaticaux ===
    print("Phase 6 : Test des templates grammaticaux...")
    templates = TemplatesGrammaticaux()
    
    questions_test = [
        ("quelle est la constante de Planck",
         ["La constante de Planck h = 6.626×10⁻³⁴ J·s.",
          "Max Planck a introduit le quantum d'action en 1900."]),
        
        ("qui a découvert la relativité",
         ["Einstein a publié la relativité restreinte en 1905.",
          "La relativité générale décrit la gravité comme courbure de l'espace-temps."]),
        
        ("comment fonctionne la photosynthèse",
         ["La photosynthèse convertit CO2 et H2O en glucose.",
          "6CO₂ + 6H₂O + lumière → C₆H₁₂O₆ + 6O₂."]),
        
        ("quelle est la vitesse de la lumière",
         ["La vitesse de la lumière est 299 792 458 m/s.",
          "C'est une constante fondamentale de la physique."]),
        
        ("qu'est-ce que le Big Bang",
         ["Le Big Bang s'est produit il y a 13.8 milliards d'années.",
          "La théorie a été proposée par Lemaître en 1927."]),
    ]
    
    print()
    for question, faits in questions_test:
        type_q = templates.detecter_type_question(question)
        sujet = templates.extraire_sujet(question, type_q)
        print(f"  Q: \"{question}\"")
        print(f"     Type détecté: {type_q}, Sujet: \"{sujet}\"")
        reponse = templates.formuler(question, faits[0])
        print(f"     Template: \"{reponse}\"")
        print()
    
    # === Générateur complet ===
    print("Test du générateur complet (Phases 5+6 intégrées)...")
    print()
    
    from decodeur_harmonique import TokeniseurHarmonique, DecodeurHarmonique
    
    tokeniseur = TokeniseurHarmonique()
    tokeniseur.construire_depuis_corpus(corpus[:3000], min_freq=2, max_tokens=5000)
    decodeur = DecodeurHarmonique(tokeniseur)
    
    generateur = GenerateurHarmoniqueComplet(decodeur, entraineur, templates)
    
    for question, faits in questions_test[:3]:
        print(f"  Q: \"{question}\"")
        reponse = generateur.generer_reponse(question, faits, mode="template")
        print(f"  R: \"{reponse}\"")
        print()
    
    print("=" * 60)
    print("✅ TERMINÉ")
    print("=" * 60)


if __name__ == "__main__":
    demo()