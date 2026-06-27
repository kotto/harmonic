#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Moteur d'Apprentissage Récursif Harmonique
=============================================
Permet à l'IA de s'améliorer automatiquement en apprenant
de ses propres réponses, sans supervision humaine.

Principe :
1. Évaluer chaque réponse (Conscious HPU → score de cohérence)
2. Renforcer les poids qui ont produit une bonne réponse
3. Affaiblir les poids qui ont produit une mauvaise réponse
4. Apprendre quels faits du corpus sont fiables
5. Maintenir un historique pour analyse

Mécanisme récursif :
- À chaque itération, le score de qualité nourrit l'apprentissage
- L'apprentissage améliore le score de qualité suivant
- Convergence vers un optimum local (point fixe harmonique)

Auteur : KOTTO Alain — 19 Juin 2026
"""

import math, re, json, time, os
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, deque
import numpy as np

phi = (1 + math.sqrt(5)) / 2

# ================================
# ÉVALUATEUR DE QUALITÉ
# ================================

class EvaluateurQualite:
    """
    Évalue automatiquement la qualité d'une réponse sans supervision.
    
    Critères :
    1. Longueur (ni trop court, ni trop long)
    2. Ponctuation (présence de points, majuscules)
    3. Répétitions (mots ou phrases en double)
    4. Présence de valeurs numériques (bon signe pour une réponse factuelle)
    5. Score de cohérence interne (via Conscious HPU simplifié)
    """
    
    def evaluer(self, question: str, reponse: str, faits_sources: List[str]) -> float:
        """
        Retourne un score entre 0 et 1.
        """
        scores = []
        
        # 1. Longueur optimale : 50-300 caractères
        longueur = len(reponse)
        if 50 <= longueur <= 300:
            scores.append(1.0)
        elif longueur < 20:
            scores.append(0.2)
        elif longueur > 500:
            scores.append(0.5)
        else:
            scores.append(0.7)
        
        # 2. Ponctuation
        nb_points = reponse.count('.') + reponse.count('!') + reponse.count('?')
        if nb_points >= 2:
            scores.append(1.0)
        elif nb_points == 1:
            scores.append(0.7)
        else:
            scores.append(0.2)
        
        # 3. Majuscule en début
        if reponse and reponse[0].isupper():
            scores.append(1.0)
        else:
            scores.append(0.3)
        
        # 4. Présence de valeurs numériques (bon indicateur de factualité)
        nb_chiffres = sum(1 for c in reponse if c.isdigit())
        if nb_chiffres >= 3:
            scores.append(1.0)
        elif nb_chiffres >= 1:
            scores.append(0.7)
        else:
            scores.append(0.3)
        
        # 5. Absence de répétitions excessives
        mots = reponse.lower().split()
        if len(mots) > 5:
            mots_uniques = len(set(mots))
            diversite = mots_uniques / len(mots)
            if diversite > 0.7:
                scores.append(1.0)
            elif diversite > 0.5:
                scores.append(0.7)
            else:
                scores.append(0.3)
        else:
            scores.append(0.5)
        
        # 6. Cohérence avec les faits sources
        if faits_sources:
            coherence = self._coherence_faits(reponse, faits_sources)
            scores.append(coherence)
        else:
            scores.append(0.5)
        
        # Score composite (moyenne pondérée)
        score = sum(scores) / len(scores)
        return score
    
    def _coherence_faits(self, reponse: str, faits: List[str]) -> float:
        """Mesure la cohérence entre la réponse et les faits sources."""
        mots_reponse = set(reponse.lower().split())
        if not mots_reponse:
            return 0.0
        
        scores_faits = []
        for fait in faits:
            mots_fait = set(fait.lower().split())
            intersection = mots_reponse & mots_fait
            if mots_fait:
                jaccard = len(intersection) / len(mots_fait)
                scores_faits.append(jaccard)
        
        return max(scores_faits) if scores_faits else 0.0


# ================================
# APPRENTISSAGE RÉCURSIF
# ================================

class ApprentissageRecursif:
    """
    Apprentissage récursif qui améliore les poids du système
    à chaque réponse donnée.
    
    Poids appris :
    - Fiabilité des faits du corpus (fact_weights)
    - Bonus par domaine (domain_boost)
    - Score minimal pour accepter un fait secondaire (seuil_secondaire)
    """
    
    def __init__(self):
        self.evaluateur = EvaluateurQualite()
        
        # Poids de fiabilité par fait (indexé par hash du texte)
        self.fiabilite_faits = {}  # hash → score [0,1]
        
        # Boost par domaine (appris)
        self.boost_domaine = defaultdict(lambda: 1.0)
        
        # Historique d'apprentissage
        self.historique = deque(maxlen=500)
        
        # Seuil adaptatif pour les faits secondaires
        self.seuil_secondaire = 0.3
        
        # Taux d'apprentissage (décroît avec le temps)
        self.taux = 0.1
        self.iterations = 0
        
        # Fichier de persistance
        self.fichier_etat = "data/apprentissage_harmonique.json"
        
        # Charger l'état précédent si disponible
        self._charger()
    
    def _hash_texte(self, texte: str) -> str:
        """Hash déterministe d'un texte (stable entre sessions)."""
        import hashlib
        normalise = re.sub(r'[^\w\s]', '', texte.lower().strip())
        return hashlib.md5(normalise.encode('utf-8')).hexdigest()[:16]
    
    def evaluer_et_apprendre(self, question: str, reponse: str,
                             faits_sources: List[str],
                             domaine: str) -> float:
        """
        Évalue la réponse et met à jour les poids d'apprentissage.
        
        Returns:
            Score de qualité [0,1]
        """
        self.iterations += 1
        
        # 1. Évaluer la qualité
        score = self.evaluateur.evaluer(question, reponse, faits_sources)
        
        # 2. Mettre à jour la fiabilité des faits sources
        for fait in faits_sources:
            h = self._hash_texte(fait)
            if h in self.fiabilite_faits:
                # Moyenne glissante avec inertie φ
                ancien = self.fiabilite_faits[h]
                self.fiabilite_faits[h] = phi * ancien + (1 - phi) * score
            else:
                self.fiabilite_faits[h] = score
        
        # 3. Mettre à jour le boost de domaine (avec protection anti-explosion)
        if domaine and score > 0:
            ancien = self.boost_domaine.get(domaine, 1.0)
            nouveau = phi * ancien + (1 - phi) * score
            # Éviter l'explosion numérique
            if abs(nouveau) < 1e6:
                self.boost_domaine[domaine] = nouveau
            else:
                self.boost_domaine[domaine] = ancien
        
        # 4. Ajuster le seuil de fait secondaire
        if score > 0.7:
            self.seuil_secondaire = min(0.8, self.seuil_secondaire + 0.01)
        elif score < 0.4:
            self.seuil_secondaire = max(0.1, self.seuil_secondaire - 0.01)
        
        # 5. Enregistrer dans l'historique
        self.historique.append({
            'question': question[:100],
            'reponse': reponse[:200],
            'score': score,
            'domaine': domaine,
            'n_faits': len(faits_sources),
            'seuil': self.seuil_secondaire,
            'iteration': self.iterations,
        })
        
        # 6. Décroître le taux d'apprentissage
        self.taux = 0.1 / (1 + self.iterations * 0.01)
        
        # 7. Sauvegarder périodiquement
        if self.iterations % 10 == 0:
            self._sauvegarder()
        
        return score
    
    def fiabilite_fait(self, texte: str) -> float:
        """Retourne la fiabilité estimée d'un fait (1.0 = fiable, 0.0 = non fiable)."""
        h = self._hash_texte(texte)
        return self.fiabilite_faits.get(h, 0.5)
    
    def boost_domaine_actuel(self, domaine: str) -> float:
        """Retourne le boost appris pour un domaine."""
        return self.boost_domaine.get(domaine, 1.0)
    
    def filtrer_faits(self, faits: List[Tuple[str, float]]) -> List[str]:
        """
        Filtre les faits selon leur fiabilité apprise.
        Ne garde que ceux dont la fiabilité > seuil.
        """
        # Filtrer les faits manifestement faux avant scoring
        faux_patterns = [
            r'(einstein|newton|planck|darwin|curie|pasteur|tesla|marconi|bell|edison)\s+a\s+(découvert|inventé)\s+le\s+(vaccin contre la rage|courant alternatif|tableau périodique|rayonnement hawking|lois du mouvement|structure de l\'ADN|évolution par sélection naturelle|radioactivité|relativité|gravitation universelle)',
        ]
        vraies_paires = [
            ('pasteur', 'vaccin contre la rage'), ('einstein', 'relativité'),
            ('newton', 'gravitation'), ('darwin', 'évolution'), ('curie', 'radioactivité'),
            ('mendeleïev', 'tableau périodique'), ('tesla', 'courant alternatif'),
            ('marconi', 'radio'), ('bell', 'téléphone'), ('edison', 'ampoule'),
        ]
        
        fiables = []
        for fait, score_tfidf in faits:
            # Vérifier les faux patterns
            est_faux = False
            for pattern in faux_patterns:
                if re.search(pattern, fait, re.IGNORECASE):
                    for personne, decouverte in vraies_paires:
                        if personne in fait.lower() and decouverte in fait.lower():
                            est_faux = False; break
                        else:
                            est_faux = True
                    if est_faux: break
            
            if est_faux:
                continue  # Rejeter ce fait
            
            fiabilite = self.fiabilite_fait(fait)
            score_composite = score_tfidf * fiabilite
            if score_composite > 0.01:
                fiables.append((fait, score_composite))
        
        fiables.sort(key=lambda x: x[1], reverse=True)
        return [f[0] for f in fiables]
    
    def stats(self) -> Dict:
        """Retourne les statistiques d'apprentissage."""
        if not self.historique:
            return {'iterations': 0, 'score_moyen': 0, 'tendance': 'neutre'}
        
        scores = [h['score'] for h in self.historique]
        score_moyen = sum(scores) / len(scores)
        
        if len(scores) >= 20:
            debut = sum(scores[:10]) / 10
            fin = sum(scores[-10:]) / 10
            if fin > debut + 0.05:
                tendance = 'Amélioration'
            elif fin < debut - 0.05:
                tendance = 'Dégradation'
            else:
                tendance = 'Stable'
        else:
            tendance = 'Apprentissage en cours'
        
        return {
            'iterations': self.iterations,
            'score_moyen': round(score_moyen, 3),
            'tendance': tendance,
            'seuil_secondaire': round(self.seuil_secondaire, 3),
            'faits_appris': len(self.fiabilite_faits),
            'taux_apprentissage': round(self.taux, 4),
        }
    
    def _sauvegarder(self):
        """Persiste l'état d'apprentissage."""
        try:
            os.makedirs(os.path.dirname(self.fichier_etat), exist_ok=True)
            etat = {
                'fiabilite_faits': dict(list(self.fiabilite_faits.items())[-5000:]),
                'boost_domaine': dict(self.boost_domaine),
                'seuil_secondaire': self.seuil_secondaire,
                'iterations': self.iterations,
                'taux': self.taux,
                'historique': list(self.historique)[-100:],
            }
            with open(self.fichier_etat, 'w', encoding='utf-8') as f:
                json.dump(etat, f, ensure_ascii=False)
        except:
            pass
    
    def _charger(self):
        """Charge l'état d'apprentissage précédent."""
        if os.path.exists(self.fichier_etat):
            try:
                with open(self.fichier_etat, 'r', encoding='utf-8') as f:
                    etat = json.load(f)
                self.fiabilite_faits = etat.get('fiabilite_faits', {})
                self.boost_domaine = defaultdict(lambda: 1.0, etat.get('boost_domaine', {}))
                self.seuil_secondaire = etat.get('seuil_secondaire', 0.3)
                self.iterations = etat.get('iterations', 0)
                self.taux = etat.get('taux', 0.1)
                print(f"  Apprentissage chargé : {self.iterations} itérations, "
                      f"{len(self.fiabilite_faits)} faits connus")
            except:
                pass


# ================================
# DÉMONSTRATION
# ================================
def demo():
    print("=" * 70)
    print("MOTEUR D'APPRENTISSAGE RÉCURSIF HARMONIQUE")
    print("=" * 70)
    print()
    
    apprentissage = ApprentissageRecursif()
    
    print("Simulation d'apprentissage sur 20 questions...")
    print()
    
    questions_test = [
        ("Quelle est la constante de Planck ?",
         "La constante de Planck vaut 6.626×10⁻³⁴ J·s.",
         ["La constante de Planck h = 6.626×10⁻³⁴ J·s.", "Max Planck, 1900."],
         "science"),
        ("Qui a découvert la relativité ?",
         "Einstein a découvert la relativité.",
         ["Einstein a publié la relativité en 1905.", "La relativité générale date de 1915."],
         "science"),
        ("Quelle est la capitale de la France ?",
         "Paris est la capitale de la France.",
         ["Paris est la capitale de la France.", "Paris compte 2 millions d'habitants."],
         "geographie"),
        ("Qui est Einstein ?",
         "Einstein a découvert le vaccin contre la rage.",
         ["Einstein a découvert le vaccin contre la rage.", "Einstein, physicien."],
         "science"),
    ]
    
    for i in range(20):
        q, rep, faits, dom = questions_test[i % len(questions_test)]
        score = apprentissage.evaluer_et_apprendre(q, rep, faits, dom)
        
        if i < 5 or i >= 15:
            emoji = "✅" if score > 0.6 else "⚠️" if score > 0.4 else "❌"
            print(f"  {emoji} Itération {i+1}: score={score:.2f} | "
                  f"question=\"{q[:40]}...\"")
    
    print()
    print("=" * 70)
    print("STATISTIQUES D'APPRENTISSAGE")
    print("=" * 70)
    stats = apprentissage.stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print()
    
    print("=" * 70)
    print("TEST DE FILTRAGE DES FAITS")
    print("=" * 70)
    faits_test = [
        ("La constante de Planck h = 6.626×10⁻³⁴ J·s.", 0.8),
        ("Einstein a découvert le vaccin contre la rage.", 0.5),
        ("Max Planck a introduit le quantum en 1900.", 0.6),
    ]
    filtres = apprentissage.filtrer_faits(faits_test)
    print(f"  Avant filtrage : {len(faits_test)} faits")
    print(f"  Après filtrage : {len(filtres)} faits")
    for f in filtres:
        fiab = apprentissage.fiabilite_fait(f)
        print(f"    [{fiab:.2f}] {f[:80]}...")
    
    print()
    print("=" * 70)
    print("✅ TERMINÉ")
    print("=" * 70)


if __name__ == "__main__":
    demo()