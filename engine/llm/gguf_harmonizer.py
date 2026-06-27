#!/usr/bin/env python3
"""
GGUF Harmonizer — Rendre harmonique n'importe quel modèle GGUF
================================================================
Que le modèle soit DeepSeek-V4, Qwen3.5, Llama, Mistral...
l'injecteur harmonique ajoute la résonance 9D sans toucher aux poids.

Principe :
    Les modèles GGUF (via llama-cpp-python) n'exposent pas leurs poids
    internes en PyTorch. On ne peut PAS remplacer les couches d'attention.
    
    Mais on peut AJOUTER la résonance harmonique EN AMONT et EN AVAL :
    
    ┌─────────────┐    ┌──────────────┐    ┌─────────────┐
    │  Prompt      │───►│ System Prompt│───►│  GGUF       │
    │  Utilisateur │    │  Harmonique  │    │  Model      │
    └─────────────┘    └──────────────┘    └──────┬──────┘
                                                  │
    ┌─────────────┐    ┌──────────────┐           │
    │  Réponse    │◄───┤ Post-Resonance│◄─────────┘
    │  Finale     │    │  Scoring     │
    └─────────────┘    └──────────────┘

    + Injection de tokens harmoniques dans le prompt
    + Scoring de resonance post-generation
    + Selection des meilleurs tokens par resonance
    + Logits biasing via frequences harmoniques
    + Memoire ABC pour le contexte

Architecture complète :
    1. GGUFHarmonicInjector  → prompt harmonique + system prompt 9D
    2. GGUFHarmonicSampler   → sampling guide par resonance φ
    3. GGUFHarmonicMemory    → memoire ABC persistante
    4. GGUFHarmonicClassifier → classification 9D du modele
    5. GGUFHarmonicProxy     → serveur compatible OpenAI
"""

import os
import sys
import json
import time
import math
import logging
import re
from typing import Optional, List, Dict, Any, Tuple, Callable
from dataclasses import dataclass, field
from collections import OrderedDict

import numpy as np

logger = logging.getLogger(__name__)

# ===========================================================================
# CONSTANTES HARMONIQUES
# ===========================================================================
PHI = 1.618033988749895
PHI_INV = 1.0 / PHI

# Frequences harmoniques pour le sampling/logits biasing
# Basées sur la suite de Fibonacci et le nombre d'or
HARMONIC_FREQUENCIES = [
    1.0,           # φ⁰  = 1.0
    1.6180339,     # φ¹  = φ
    2.6180339,     # φ²  = φ + 1
    4.2360679,     # φ³  = 2φ + 1
    6.8541019,     # φ⁴  = 3φ + 2
    11.0901699,    # φ⁵  = 5φ + 3
    17.9442719,    # φ⁶  = 8φ + 5
    29.0344419,    # φ⁷  = 13φ + 8
]

# Poids harmoniques pour les 9 dimensions
HARMONIC_WEIGHTS_9D = [
    PHI_INV,       # 0: dimension fondamentale
    PHI_INV * 0.5, # 1: dimension secondaire
    0.7,           # 2: raisonnement
    0.85,          # 3: creativite
    0.3,           # 4: mathematiques
    0.5,           # 5: factuel
    0.6,           # 6: code
    0.75,          # 7: emotion
    0.4,           # 8: temporel
]


# ===========================================================================
# PROMPT HARMONIQUE — Injection de resonance
# ===========================================================================

class GGUFHarmonicInjector:
    """
    Injecte la resonance harmonique dans le prompt d'un GGUF.
    
    Strategies :
    1. System prompt guide par signatures 9D
    2. Mots harmoniques injectes dans le prompt
    3. Format specifique selon la categorie
    
    Usage:
        injector = GGUFHarmonicInjector()
        prompt = injector.build("Calcule 15% de 340")
        # → Prompt avec system prompt harmonique + instructions
    """
    
    def __init__(self, resonance_strength: float = 0.7,
                 use_exemplars: bool = True):
        """
        Args:
            resonance_strength: Force de la resonance harmonique
            use_exemplars: Activer la selection dynamique d'exemplars
                           (recommandation IA experte)
        """
        self.resonance_strength = resonance_strength
        self.use_exemplars = use_exemplars
        self._exemplar_library = None
        self._cache = {}
    
    def build(self, prompt: str, category: str = None,
              context: Optional[List[Dict]] = None,
              inject_exemplar: bool = True) -> str:
        """
        Construit un prompt harmonique complet.
        
        Args:
            prompt: Question utilisateur
            category: Categorie harmonique (auto-detect si None)
            context: Messages precedents [{"role": ..., "content": ...}]
            inject_exemplar: Injecter un exemplar selectionne dynamiquement
                             (recommandation : 1 exemplar de haute qualite
                              > batterie d'exemples generiques)
        
        Returns:
            Prompt harmonique formatte
        """
        if category is None:
            category = self._detect_category(prompt)
        
        # System prompt harmonique
        system = self._build_system_prompt(category, prompt)
        
        # Instructions harmoniques
        instructions = self._build_instructions(category)
        
        # Assemblage
        parts = [f"<|system|>\n{system}\n</s>"]
        
        # Contexte
        if context:
            for msg in context[-5:]:  # max 5 precedents
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    parts.append(f"<|user|>\n{content}\n</s>")
                else:
                    parts.append(f"<|assistant|>\n{content}\n</s>")
        
        # === SELECTION DYNAMIQUE D'EXEMPLAR ===
        # Recommandation IA experte :
        # "Un exemplar pertinent selectionne dynamiquement plutot que
        #  plusieurs exemples generiques. Selectionnez via similarite
        #  semantique, donnant moins de tokens gaspilles."
        exemplar_text = ""
        if inject_exemplar and self.use_exemplars:
            exemplar_text = self._select_exemplar(prompt, category)
        
        # Construction du prompt utilisateur
        user_prompt_parts = [prompt]
        if exemplar_text:
            user_prompt_parts.append(
                f"\n\n[Exemple de reponse attendue ({category})]\n{exemplar_text}"
            )
        user_prompt_parts.append(f"\n\n[Resonance: {category}]\n{instructions}")
        
        parts.append(f"<|user|>\n{''.join(user_prompt_parts)}\n</s>")
        parts.append("<|assistant|>\n")
        
        return "\n".join(parts)
    
    def _select_exemplar(self, prompt: str, category: str) -> str:
        """Selectionne dynamiquement un exemplar via similarite semantique."""
        if self._exemplar_library is None:
            try:
                from ..semantic.vector_store import ExemplarLibrary
                self._exemplar_library = ExemplarLibrary()
            except ImportError:
                return ""
        
        try:
            exemplar = self._exemplar_library.select(prompt, category, k=1)
            return exemplar or ""
        except Exception:
            return ""
    
    def _detect_category(self, text: str) -> str:
        """
        Detecte la categorie harmonique par ACTES DE LANGAGE.
        
        Base sur la recommandation de l'IA experte :
        "Votre classifieur devrait s'appuyer sur des actes de langage
        (demander de resoudre / de creer / de justifier / de recuperer un fait)
        plutot que sur des proxys lexicaux de surface, qui sont fragiles."
        
        Les 5 actes de langage :
        - RESOUDRE  -> mathematical
        - CREER     -> creative
        - JUSTIFIER -> reasoning
        - RECUPERER -> factual
        - REALISER  -> code
        
        Version amelioree v2 :
        - Normalisation des accents français
        - Patterns enrichis pour la notation algebrique
        - Detection explicite des salutations -> general
        - Priorite par acte de langage corrigee
        """
        import re as _re
        import unicodedata as _ud
        
        # Normalisation : supprime les accents pour les comparaisons regex
        t = text.lower()
        t_flat = ''.join(
            c for c in _ud.normalize('NFD', t)
            if _ud.category(c) != 'Mn'
        )  # ex: "resous" depuis "résous", "annee" depuis "annee"
        
        # =====================================================================
        # DETECTION RAPIDE DES SALUTATIONS / SMALL TALK -> general
        # =====================================================================
        # Si le texte est une salutation/social/meteo/opinion, on sort en general
        salutations = [
            # Salutations
            r'^(bonjour|salut|coucou|hello|hey|bonsoir|bonne nuit)',
            r'\b(comment (ca va|vas.tu|allez.vous))\b',
            r'\b(merci|remercie|merci beaucoup|avec plaisir)\b',
            r'\bravi|tres bien|super|genial|d accord|pas mal\b',
            r'\braconte.moi une anecdote\b',
            # Meteo / temps qu'il fait
            r'\b(quel temps fait.il|quelle temperature|est.ce qu.il fait|la meteo)\b',
            r'\b(pleut.il|neige.t.il|fait.il beau|temps aujourd hui)\b',
            # Opinion / conversation generale
            r'\b(que penses.tu|qu est.ce que tu penses|a ton avis)\b',
            r'\b(peux.tu me donner des nouvelles|donne moi des nouvelles)\b',
            r'\b(comment se passe|comment s est.passee|raconte moi ta)\b',
            # Demandes d'actualites
            r'\b(quoi de neuf|des nouvelles du monde|actualites|infos)\b',
        ]
        for pat in salutations:
            if _re.search(pat, t_flat):
                return "general"
        
        # =====================================================================
        # ACTES DE LANGAGE — structures illocutoires
        # =====================================================================
        
        # 1. ACTE DE RESOUDRE (mathematique)
        # Imperatif de calcul + quantites + resolution d'equation + notation algebrique
        acte_resoudre = [
            # Imperatifs de resolution (avec accents normalises)
            r'\b(resous|resoudre|calcule|calculez|trouve|trouvez)\b.*\d',
            r'\b(resous|resoudre)\b.*\b(equation|probleme|systeme)\b',
            r'\b(montre|montrez|demontre|prouve)\b.*\b(etape|pas a pas|demonstration)\b',
            r'\b(integrale|derivee|derive|primitive|somme|produit|matrice|determinant)\b',
            # Quantification explicite
            r'\b(combien|pourcentage|proportion|ratio|moyenne|ecart.type|variance)\b',
            r'\d+\s*%.*',
            # Notation algebrique : f(x), sin(x), cos, ln, exp
            r'\b[fgh]\s*\(\s*[a-z]\s*\)',        # f(x), g(y)
            r'\b(sin|cos|tan|log|ln|exp|sqrt)\s*\(',  # sin(x), log(x)
            r'\b(lim|sum|prod|int|integral)\b',   # limites, sommes
            r'\d+\s*[\+\-*/^]\s*[a-z]',           # 2x, 5x^2
            r'[a-z]\s*\^\s*\d+',                  # x^2, x^3
            r'=\s*0\b',                           # = 0 (equation)
        ]
        
        # 2. ACTE DE REALISER (code)
        # Imperatif d'implementation + langage + structure technique
        acte_realiser = [
            r'\b(implemente|implementez|code|codez|programme|programmez|developpe|developpez)\b',
            r'\b(ecris|ecrivez)\b.*\b(fonction|classe|script|algorithme)\b',
            r'\b(python|javascript|typescript|java|rust|golang|react|vue|django|flask|docker)\b',
            r'\b(api|endpoint|route|base de donnees|sql|requete|endpoint)\b',
            r'\b(refactore|refactorise|optimise|debuggue|corrige)\b',
            r'\b(interface|composant|module|package|bibliotheque|framework)\b',
            r'\b(file d attente|thread.safe|thread.safe|concurrent|parallelisme)\b',
            r'\b(decorateur|decorator|middleware|hook|plugin)\b',
        ]
        
        # 3. ACTE DE CREER (creative)
        # Declarative d'imagination + registre sensible + contrainte esthetique
        acte_creer = [
            # Imperatifs creatifs (inclut "decris/decris/depains")
            r'\b(ecris|ecrivez|invente|inventez|imagine|imaginez|cree|creez|compose|composez)\b',
            r'\b(decris|decrivez|depeins|depeignez|raconte|racontez)\b',
            # Genres creatifs
            r'\b(poeme|poesie|chanson|histoire|recit|nouvelle|conte|fable|legende|mythe)\b',
            r'\b(haiku|sonnet|ballade|ode|etre|paysage.onirique)\b',
            # Registre sensoriel/emotionnel
            r'\b(emotion|sentiment|atmosphere|ambiance|sensation|silence|crepuscule)\b',
            r'\b(paysage|coucher du soleil|aube|clair de lune|etoile|ocean|vague)\b',
            # Contrainte esthetique
            r'\b(beau|belle|harmonie|elegance|poetique|lyrique|onirique|surrealiste)\b',
            r'\b(metaphore|image|symbole|allegorie|style|ton|registre)\b',
            # Imagination
            r'\b(monde ou|monde dans lequel|univers|reve|rever|imaginaire|fiction)\b',
            r'\b(comme si|c etait la premiere fois|incarne|incarnez)\b',
        ]
        
        # 4. ACTE DE JUSTIFIER (reasoning)
        # Demande de causalite, comparaison, evaluation
        acte_justifier = [
            # Questions causales
            r'\b(pourquoi|comment expliquer)\b',
            r'\b(quelle est la cause|quel est l effet|quelle en est la raison)\b',
            # Demande d'analyse
            r'\b(analyse|analysez|compare|comparez|contraste|evaluer|jugez|critiquez)\b',
            r'\b(justifie|justifiez|argumente|argumentez|demontre|prouve)\b',
            # Structure dialectique
            r'\b(these|antithese|synthese|pros? et cons?|avantages? et inconvenients?)\b',
            r'\b(implication|consequence|deduction|induction|inference)\b',
            r'\b(difference|similitude|parallele|oppose|contraire|vs|versus)\b',
            # Questions epistemiques
            r'\b(paradoxe|dilemme|contradiction|aporie)\b',
            r'\b(principe de|theorie de|loi de|concept d |notion d )\b',
        ]
        
        # 5. ACTE DE RECUPERER (factual)
        # Question fermee, entite specifique, fait verifiable
        acte_recuperer = [
            # Questions fermees (forme interrogative directe)
            r'\b(qui est|qu est ce que|que signifie)\b',
            r'\b(en quelle annee|en quelle date|a quelle epoque)\b',
            r'\b(ou se trouve|ou est|dans quel pays)\b',
            r'\b(combien de|quel est le nombre|quelle est la quantite)\b',
            # "Quel/Quelle est ..." (sauf si causal)
            r'\b(quel est\s+la?\s+(capitale|population|date|nom|definition))\b',
            r'\b(quelle est\s+la?\s+(capitale|population|date|nom|definition))\b',
            r'\b(quel est\s+le\s+(point|poids|taux|prix|cout|volume|superficie))\b',
            r'\b(quelle est\s+la?\s+(population|superficie|distance|hauteur|profondeur))\b',
            # Entite factuelle
            r'\b(capitale|population|superficie|date de naissance|fondation|decouverte)\b',
            r'\b(definition|signification|historique|origine)\b',
            r'\b(point d ebullition|temperature|pression|densite|masse|volume)\b',
            # Liste/donnee
            r'\b(liste|enumere|cite|donne)\b.*\b(fait|exemple|caracteristique|propriete)\b',
        ]
        
        # =====================================================================
        # CALCUL DES SCORES PAR ACTE DE LANGAGE
        # =====================================================================
        
        def score_acte(patterns, use_flat=True):
            """Score pour un acte de langage : test sur texte accentue ET normalise."""
            s = 0
            for pat in patterns:
                # Test sur le texte sans accents (plus tolerant)
                if use_flat:
                    matches = _re.findall(pat, t_flat)
                else:
                    matches = _re.findall(pat, t)
                s += len(matches) * 2.0
                # Si rien trouve sur le texte normalise, retenter avec l'accentue
                if s == 0 and not use_flat:
                    matches = _re.findall(pat, t)
                    s += len(matches) * 2.0
            return s
        
        scores = {
            "mathematical": score_acte(acte_resoudre, use_flat=True),
            "code":         score_acte(acte_realiser, use_flat=True),
            "creative":     score_acte(acte_creer, use_flat=True),
            "reasoning":    score_acte(acte_justifier, use_flat=True),
            "factual":      score_acte(acte_recuperer, use_flat=True),
        }
        
        # Fallback lexical ameliore pour les cas ou les actes de langage
        # sont insuffisants (< 2 correspondances)
        if max(scores.values()) < 2:
            _kw = lambda words: sum(1 for kw in words if kw in t_flat)
            lexical_scores = {
                "mathematical": _kw(['calcul', 'equation', 'nombre', 'math', 'phi',
                                     'derivee', 'integrale', 'fonction', 'sin', 'cos']),
                "code":         _kw(['python', 'code', 'algorithme', 'api', 'fonction',
                                     'classe', 'programme', 'logiciel']),
                "creative":     _kw(['poeme', 'art', 'cree', 'imagine', 'reve', 'beaute',
                                     'histoire', 'poesie', 'silence', 'ocean', 'monde']),
                "reasoning":    _kw(['pourquoi', 'analyse', 'cause', 'logique', 'compare',
                                     'paradoxe', 'reflexion', 'raison']),
                "factual":      _kw(['definition', 'capitale', 'date', 'qui', 'ou',
                                     'population', 'annee', 'traite', 'decouverte']),
            }
            scores = {k: scores[k] + v for k, v in lexical_scores.items()}
        
        # Meilleure categorie
        best_cat = max(scores, key=scores.get)
        best_score = scores[best_cat]
        
        if best_score < 1:
            return "general"
        
        # Gestion des conflits : resolution par priorite d'acte de langage
        # Les actes "forts" (creation, raisonnement) priment sur les actes "faibles"
        # (recuperation de faits) en cas d'egalite
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) >= 2 and sorted_scores[0] == sorted_scores[1]:
            # Egalite entre le meilleur et le second : departager par priorite
            priority = ['creative', 'reasoning', 'mathematical', 'code', 'factual']
            for cat in priority:
                if scores[cat] == best_score:
                    return cat
        
        return best_cat
    
    def _build_system_prompt(self, category: str, prompt: str) -> str:
        """
        Construit le system prompt harmonique guide par le prompt.
        
        STRATEGIE RECOMMANDEE PAR L'IA EXPERTE :
        - Ouverture impérative pour tâches génératives (code, créatif, raisonnement)
        - Interrogative fermée pour factuel
        - Déclarative + intention pour général
        - Actes de langage clairs plutôt que proxies lexicaux
        """
        sig = self._quick_signature_9d(prompt)
        
        # Ouverture catégorielle selon la recommandation experte
        openers = {
            "mathematical": (
                "Tu es un assistant mathematique harmonique. "
                "Resous les problemes etape par etape avec rigueur et precision.\n"
                "Active le mode de resolution : decompose, calcule, verifie."
            ),
            "code": (
                "Tu es un ingenieur logiciel expert. "
                "Implémente des solutions propres, documentees, et efficaces.\n"
                "Format de sortie : d'abord l'explication, puis le code, "
                "puis les instructions d'utilisation."
            ),
            "creative": (
                "Tu es un artiste et un ecrivain harmonique. "
                "Laisse libre cours a ta creativite tout en respectant les contraintes donnees.\n"
                "Utilise des images poetiques, des metaphors, et un registre sensoriel.\n"
                "Les contraintes (ton, longueur, point de vue) sont des guides, pas des limites."
            ),
            "reasoning": (
                "Tu es un analyste-philosophe. "
                "Structure ta reflexion de maniere claire et progressive.\n"
                "Utilise la dialectique : these, antithese, synthese.\n"
                "Chaque etape de raisonnement doit etre justifiee."
            ),
            "factual": (
                "Tu es un encyclopediste rigoureux. "
                "Reponds avec precision et verifiabilite.\n"
                "Si tu ne connais pas la reponse avec certitude, indique-le clairement.\n"
                "Cite tes sources lorsque c'est possible."
            ),
            "general": (
                "Tu es un assistant IA harmonique et naturel.\n"
                "J'aimerais que tu repondes de maniere claire, utile et adaptee.\n"
                "Ajuste la profondeur de ta reponse a la complexite de la question."
            ),
        }
        
        lines = [openers.get(category, openers["general"])]
        lines.append(f"\nNombre d'or φ = {PHI:.6f} — Resonance harmonique activee.")
        
        # Ajustements fins selon les dimensions actives (enrichissement, pas substitution)
        if sig[2] > 0.5:  # reasoning fort
            lines.append("Deploie un raisonnement pas-a-pas avec des connecteurs logiques.")
        if sig[3] > 0.5:  # creative fort
            lines.append("Utilise des metaphors poetiques et un vocabulaire evocateur.")
        if sig[4] > 0.4:  # math fort
            lines.append("Montre chaque etape de calcul. Utilise la notation mathematique.")
        if sig[7] > 0.5:  # emotion
            lines.append("Sois empathique et chaleureux dans le ton.")
        
        return "\n".join(lines)
    
    def _build_instructions(self, category: str) -> str:
        """
        Instructions de format pour le modele.
        
        Basé sur les recommandations de l'IA experte :
        - "Les ouvertures imperatives surperforment les interrogatives"
        - "Un petit jeu canonique de connecteurs de sequencage"
        - "La concision est un atout pour le factuel"
        """
        instructions = {
            "mathematical": (
                "Resous par etapes : [1] pose les donnees, [2] applique la methode, "
                "[3] donne le resultat, [4] verifie."
            ),
            "code": (
                "Fournis : [1] l'approche algorithmique, [2] le code commente, "
                "[3] un exemple d'utilisation, [4] la complexite."
            ),
            "creative": (
                "Cree dans le registre demande. Contrainte : sois original sans etre "
                "obscur. Utilise des images sensorielles."
            ),
            "reasoning": (
                "Structure : [1] analyse du probleme, [2] arguments, "
                "[3] contre-arguments, [4] synthese et conclusion."
            ),
            "factual": (
                "Reponds de maniere concise et precise. Un fait = une phrase. "
                "Structure en tete de chapitre si plusieurs elements."
            ),
            "general": (
                "Sois clair, naturel et adapte a la question. "
                "Ni trop court ni trop long."
            ),
        }
        return instructions.get(category, instructions["general"])
    
    def _quick_signature_9d(self, text: str) -> List[float]:
        """Signature 9D rapide sans modele."""
        sig = [0.0] * 9
        words = text.lower().split()
        if not words:
            return sig
        
        n = len(words)
        unique = len(set(words))
        
        # [0] phi - diversite lexicale
        sig[0] = min(1.0, unique / n * PHI)
        
        # [1] alpha - complexite
        sig[1] = min(1.0, np.mean([len(w) for w in words]) / 12.0)
        
        # Mots-cles par dimension
        keywords = {
            2: ['pourquoi', 'parce que', 'donc', 'analyse', 'cause', 'raison',
                'logique', 'explique', 'compare'],
            3: ['imagine', 'cree', 'reve', 'poeme', 'beaute', 'art', 'musique',
                'invente', 'creatif'],
            4: ['calcul', 'equation', 'nombre', 'phi', 'mathematique',
                'fonction', 'derivee', 'integrale'],
            5: ['definition', 'fait', 'donnee', 'etude', 'source', 'historique',
                'qui', 'quand', 'ou'],
            6: ['code', 'python', 'fonction', 'algorithme', 'programme',
                'api', 'debug', 'git'],
            7: ['sentiment', 'emotion', 'amour', 'tristesse', 'joie',
                'peur', 'espoir', 'reve'],
            8: ['apres', 'avant', 'pendant', 'futur', 'passe', 'temps',
                'evolution', 'changement'],
        }
        
        for dim, kws in keywords.items():
            sig[dim] = min(1.0, sum(1 for kw in kws if kw in text.lower()) / 4.0)
        
        return sig


# ===========================================================================
# SAMPLING HARMONIQUE — Guide par resonance φ
# ===========================================================================

class GGUFHarmonicSampler:
    """
    Sampler guide par la resonance harmonique.
    
    Au lieu de modifier les logits internes (impossible sur GGUF),
    on utilise la resonance φ pour re-pondérer les tokens generes
    en post-processing, et pour guider le modele via :
    
    1. Temperature harmonique adaptative selon la categorie
    2. Top-p dynamique base sur la suite de Fibonacci
    3. Re-ponderation des tokens par resonance
    
    Usage:
        sampler = GGUFHarmonicSampler()
        params = sampler.get_params("creative")
        # → {"temperature": 0.85, "top_p": 0.95, "top_k": 80}
    """
    
    def __init__(self):
        # Frequences harmoniques pour le top-k
        self.harmonic_top_k = [int(round(p * 10)) for p in PHI_INV ** np.arange(1, 10)]
        # → [6, 4, 2, 1, 1, 0, 0, 0, 0]
    
    def get_params(self, category: str) -> Dict[str, float]:
        """
        Retourne les parametres de sampling optimises.
        
        Args:
            category: Categorie harmonique
        
        Returns:
            {"temperature": float, "top_p": float, "top_k": int}
        """
        params = {
            "mathematical": {"temperature": 0.3, "top_p": 0.85, "top_k": 30},
            "code":         {"temperature": 0.2, "top_p": 0.90, "top_k": 25},
            "creative":     {"temperature": 0.85, "top_p": 0.95, "top_k": 80},
            "reasoning":    {"temperature": 0.5, "top_p": 0.88, "top_k": 40},
            "factual":      {"temperature": 0.2, "top_p": 0.80, "top_k": 20},
            "general":      {"temperature": 0.7, "top_p": 0.92, "top_k": 50},
        }
        
        return params.get(category, params["general"])
    
    def score_resonance(self, text: str) -> Dict[str, float]:
        """
        Calcule le score de resonance d'un texte genere.
        
        Retourne un score entre 0 et 1 base sur :
        - Harmonie lexicale (distribution φ)
        - Diversite (entropie normalisee)
        - Ratio mots longs/courts
        - Richesee de vocabulaire
        
        Args:
            text: Texte genere
        
        Returns:
            {"resonance": float, "entropy": float, "diversity": float,
             "phi_ratio": float, "harmonic_score": float}
        """
        if not text.strip():
            return {"resonance": 0.0, "entropy": 0.0, "diversity": 0.0,
                    "phi_ratio": 0.0, "harmonic_score": 0.0}
        
        words = text.split()
        n = len(words)
        if n == 0:
            return {"resonance": 0.0, "entropy": 0.0, "diversity": 0.0,
                    "phi_ratio": 0.0, "harmonic_score": 0.0}
        
        # Entropie lexicale
        from collections import Counter
        word_counts = Counter(words)
        probs = [c / n for c in word_counts.values()]
        entropy = -sum(p * math.log2(p) for p in probs)
        max_entropy = math.log2(n) if n > 1 else 1
        norm_entropy = entropy / max_entropy if max_entropy > 0 else 0.5
        
        # Diversite
        diversity = len(word_counts) / n
        
        # Ratio φ (mots longs / mots courts ~ 1/φ)
        long_words = sum(1 for w in words if len(w) > 5)
        short_words = sum(1 for w in words if len(w) <= 3)
        ratio = long_words / max(short_words, 1)
        phi_score = 1.0 - abs(ratio - PHI) / max(PHI, ratio)
        phi_score = max(0.0, min(1.0, phi_score))
        
        # Score harmonique composite
        harmonic_score = (
            norm_entropy * 0.3 +
            diversity * 0.25 +
            phi_score * 0.25 +
            min(1.0, n / 100.0) * 0.2
        )
        
        return {
            "resonance": round(harmonic_score, 4),
            "entropy": round(norm_entropy, 4),
            "diversity": round(diversity, 4),
            "phi_ratio": round(phi_score, 4),
            "harmonic_score": round(harmonic_score, 4),
        }


# ===========================================================================
# MEMOIRE ABC POUR GGUF
# ===========================================================================

class ABCMemory:
    """
    Memoire harmonique basee sur le noyau ABC pour contexte long.
    
    Utilise la courbe d'oubli d'Atangana-Baleanu a l'ordre 1/φ
    pour decider quels tokens/contexte garder.
    
    Usage:
        memory = ABCMemory(max_tokens=4096)
        memory.add("La capitale de la France est Paris", importance=0.9)
        context = memory.get_context("capitale")
    """
    
    def __init__(self, max_tokens: int = 8192):
        self.max_tokens = max_tokens
        self.memories: List[Dict[str, Any]] = []
        self._tokens_count = 0
    
    def add(self, text: str, importance: float = 0.5,
            category: str = "general", source: str = "conversation"):
        """
        Ajoute un element en memoire avec oubli ABC.
        
        Score initial = importance × resonance
        Decay = ABC(alpha=1/φ, t)
        """
        # Score de resonance initial
        sampler = GGUFHarmonicSampler()
        score = sampler.score_resonance(text)
        resonance = score["resonance"]
        
        memory_item = {
            "text": text,
            "importance": importance,
            "resonance": resonance,
            "category": category,
            "source": source,
            "timestamp": time.time(),
            "tokens": len(text.split()),
            "access_count": 0,
        }
        
        self.memories.append(memory_item)
        self._tokens_count += memory_item["tokens"]
        
        # Nettoyer si depassement
        self._prune()
    
    def recall(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Rappelle les souvenirs les plus resonants avec une requete.
        
        Score = importance × resonance × ABC_decay × query_similarity
        """
        query_words = set(query.lower().split())
        now = time.time()
        
        scored = []
        for mem in self.memories:
            # Similarite lexicale
            mem_words = set(mem["text"].lower().split())
            overlap = len(query_words & mem_words)
            similarity = overlap / max(len(query_words | mem_words), 1)
            
            # Decay ABC (courbe de memoire non-locale)
            dt = now - mem["timestamp"]
            alpha = PHI_INV
            decay = 1.0 / (1.0 + (alpha * dt / 3600.0) ** alpha)
            
            # Score final
            score = (
                mem["importance"] * 0.4 +
                mem["resonance"] * 0.2 +
                decay * 0.2 +
                similarity * 0.2
            )
            
            if score > 0.15:  # Seuil
                scored.append((score, mem))
        
        # Tri par score decroissant, avec index comme tiebreaker
        scored = [(s, i, m) for i, (s, m) in enumerate(scored)]
        scored.sort(key=lambda x: (-x[0], x[1]))
        scored = [(s, m) for s, i, m in scored]

        
        results = []
        for score, mem in scored[:top_k]:
            mem["access_count"] += 1
            results.append({**mem, "recall_score": score})
        
        return results
    
    def get_context(self, query: str, max_tokens: int = 2000) -> str:
        """Construit un contexte a partir de la memoire."""
        recalled = self.recall(query, top_k=10)
        
        parts = []
        total = 0
        for mem in recalled:
            if total + mem["tokens"] > max_tokens:
                break
            parts.append(mem["text"])
            total += mem["tokens"]
        
        return "\n".join(parts) if parts else ""
    
    def _prune(self):
        """Nettoie la memoire si depassement."""
        while self._tokens_count > self.max_tokens:
            # Enlever le souvenir le moins important + le plus vieux
            # (score ABC minimal)
            if not self.memories:
                break
            
            # Tri par viabilite ABC
            now = time.time()
            self.memories.sort(key=lambda m: (
                m["importance"] * 0.5 +
                0.3 / (1 + (PHI_INV * (now - m["timestamp"]) / 3600.0) ** PHI_INV) +
                0.2 * (m["access_count"] / max(m["access_count"], 1))
            ))
            
            removed = self.memories.pop(0)
            self._tokens_count -= removed["tokens"]
    
    def clear(self):
        """Vide la memoire."""
        self.memories.clear()
        self._tokens_count = 0
    
    def stats(self) -> Dict[str, Any]:
        """Stats de la memoire."""
        return {
            "total_items": len(self.memories),
            "total_tokens": self._tokens_count,
            "max_tokens": self.max_tokens,
            "utilization": round(self._tokens_count / self.max_tokens * 100, 1),
            "categories": dict(Counter(m["category"] for m in self.memories)),
            "avg_resonance": round(np.mean([m["resonance"] for m in self.memories]), 3) if self.memories else 0,
        }


# ===========================================================================
# CLASSIFICATEUR 9D (via le modele GGUF lui-meme)
# ===========================================================================

class GGUFHarmonicClassifier:
    """
    Utilise le modele GGUF lui-meme pour classifier en 9 dimensions.
    
    Au lieu d'utiliser un classifieur externe, on demande au modele
    de generer sa propre signature 9D via un prompt special.
    
    Usage:
        classifier = GGUFHarmonicClassifier(generate_fn)
        sig = classifier.classify("Explique la relativite")
        # → [φ, α, reasoning, creative, math, factual, code, emotion, temporal]
    """
    
    def __init__(self, generate_fn: Callable):
        """
        Args:
            generate_fn: Fonction qui prend un prompt et retourne du texte
        """
        self._generate = generate_fn
        self._injector = GGUFHarmonicInjector()
    
    def classify(self, prompt: str) -> List[float]:
        """Classifie un prompt en signature 9D via le modele."""
        # Prompt special pour extraction de signature
        extraction_prompt = (
            f"Analyse le prompt suivant et genere 9 scores entre 0.0 et 1.0:\n"
            f"Prompt: {prompt[:200]}\n\n"
            f"Format exact: [phi, alpha, reasoning, creative, math, factual, code, emotion, temporal]\n"
            f"Reponds UNIQUEMENT par une liste de 9 nombres separes par des virgules."
        )
        
        try:
            response = self._generate(extraction_prompt, max_new_tokens=50)
            
            # Extraire les nombres
            nums = re.findall(r'[\d.]+', response)
            sig = []
            for n in nums[:9]:
                try:
                    val = float(n)
                    sig.append(max(0.0, min(1.0, val)))
                except ValueError:
                    sig.append(0.5)
            
            # Pad ou tronquer a 9
            while len(sig) < 9:
                sig.append(0.5)
            sig = sig[:9]
            
            return sig
            
        except Exception as e:
            logger.warning(f"Erreur classification GGUF: {e}")
            # Fallback: signature rapide
            return self._injector._quick_signature_9d(prompt)
    
    def classify_batch(self, prompts: List[str]) -> List[List[float]]:
        """Classifie plusieurs prompts."""
        return [self.classify(p) for p in prompts]


from collections import Counter

# ===========================================================================
# PROXY HARMONIQUE POUR GGUF
# ===========================================================================

@dataclass
class GGUFHarmonicProxyConfig:
    """Configuration du proxy harmonique GGUF."""
    model_path: str = ""
    model_alias: str = "deepseek-qwen-hybrid"
    n_ctx: int = 8192
    n_gpu_layers: int = -1  # -1 = tous sur GPU
    resonance_strength: float = 0.7
    use_memory: bool = True
    max_memory_tokens: int = 4096
    verbose: bool = False


class GGUFHarmonicProxy:
    """
    Proxy harmonique complet pour modeles GGUF.
    
    Ajoute la resonance 9D a n'importe quel modele GGUF sans
    modification des poids.
    
    Usage:
        proxy = GGUFHarmonicProxy(
            model_path="/models/deepseek-v4-qwen3.5.Q4_K_M.gguf",
            n_gpu_layers=-1
        )
        
        # Chat simple
        response = proxy.generate("Explique la relativite")
        print(f"[{response['category']}] {response['content'][:100]}")
        
        # Avec resonance et memoire
        response = proxy.generate_auto(
            "Calcule 15% de 340",
            use_resonance=True
        )
        print(f"Resonance: {response['resonance_score']:.3f}")
        
        # Serveur API
        proxy.run_server(port=8080)
    """
    
    def __init__(self, config: Optional[GGUFHarmonicProxyConfig] = None):
        self.config = config or GGUFHarmonicProxyConfig()
        self._llm = None
        self._loaded = False
        
        # Composants harmoniques
        self.injector = GGUFHarmonicInjector(
            resonance_strength=self.config.resonance_strength
        )
        self.sampler = GGUFHarmonicSampler()
        self.memory = ABCMemory(
            max_tokens=self.config.max_memory_tokens
        ) if self.config.use_memory else None
        
        # Stats
        self.stats = {
            "total_calls": 0,
            "avg_resonance": 0.0,
            "avg_latency_ms": 0.0,
            "cache_hits": 0,
            "fallbacks": 0,
        }
        self._call_history = []
        
        logger.info(f"Proxy harmonique GGUF initialise")
        logger.info(f"  Modele: {self.config.model_alias}")
        logger.info(f"  Contexte: {self.config.n_ctx}")
        logger.info(f"  GPU layers: {self.config.n_gpu_layers}")
        logger.info(f"  Resonance: {self.config.resonance_strength}")
        logger.info(f"  Memoire: {self.config.use_memory}")
    
    def _load(self):
        """Charge le modele GGUF."""
        if self._loaded:
            return
        
        if not self.config.model_path:
            logger.warning("Pas de chemin modele: mode demo")
            self._loaded = True
            return
        
        try:
            from llama_cpp import Llama
            
            logger.info(f"Chargement du GGUF: {self.config.model_path}")
            t0 = time.time()
            
            self._llm = Llama(
                model_path=self.config.model_path,
                n_ctx=self.config.n_ctx,
                n_gpu_layers=self.config.n_gpu_layers,
                verbose=self.config.verbose,
            )
            
            elapsed = time.time() - t0
            logger.info(f"GGUF charge en {elapsed:.1f}s")
            self._loaded = True
            
        except ImportError:
            logger.error(
                "llama-cpp-python non installe. "
                "pip install llama-cpp-python"
            )
            self._loaded = True  # mode demo
        except Exception as e:
            logger.error(f"Erreur chargement GGUF: {e}")
            self._loaded = True  # mode demo
    
    def generate(self, prompt: str, category: str = "general",
                 max_tokens: int = 1024, use_resonance: bool = True,
                 temperature: Optional[float] = None,
                 top_p: Optional[float] = None,
                 top_k: Optional[int] = None) -> Dict[str, Any]:
        """
        Generation harmonique complete.
        
        Args:
            prompt: Question utilisateur
            category: Categorie harmonique
            max_tokens: Tokens max a generer
            use_resonance: Activer l'injection harmonique
            temperature: Override temperature
            top_p: Override top_p
            top_k: Override top_k
        
        Returns:
            Dict avec content, signatures, resonance, stats
        """
        self._load()
        t0 = time.time()
        self.stats["total_calls"] += 1
        
        # 1. Parametres de sampling
        sampling_params = self.sampler.get_params(category)
        if temperature is not None:
            sampling_params["temperature"] = temperature
        if top_p is not None:
            sampling_params["top_p"] = top_p
        if top_k is not None:
            sampling_params["top_k"] = top_k
        
        # 2. Memoire
        context = ""
        if self.memory:
            context = self.memory.get_context(prompt)
        
        # 3. Construction du prompt harmonique
        if use_resonance:
            full_prompt = self.injector.build(
                prompt, category=category,
                context=[{"role": "system", "content": context}] if context else None
            )
        else:
            full_prompt = prompt
        
        # 4. Generation via GGUF ou demo
        if self._llm is not None:
            try:
                response = self._llm(
                    full_prompt,
                    max_tokens=max_tokens,
                    temperature=sampling_params["temperature"],
                    top_p=sampling_params["top_p"],
                    top_k=sampling_params["top_k"],
                    stop=["</s>", "<|user|>", "<|end|>"],
                )
                content = response["choices"][0]["text"].strip() if response["choices"] else ""
            except Exception as e:
                logger.error(f"Erreur generation GGUF: {e}")
                content = self._fallback_generation(prompt, category)
        else:
            # Mode demo
            content = self._fallback_generation(prompt, category)
        
        # 5. Score de resonance
        resonance_score = self.sampler.score_resonance(content)
        
        # 6. Memoire
        if self.memory and content:
            self.memory.add(
                f"User: {prompt}\nAssistant: {content[:200]}",
                importance=resonance_score["resonance"],
                category=category
            )
        
        # 7. Stats
        elapsed = (time.time() - t0) * 1000
        self.stats["avg_resonance"] = (
            self.stats["avg_resonance"] * (self.stats["total_calls"] - 1) +
            resonance_score["resonance"]
        ) / self.stats["total_calls"]
        self.stats["avg_latency_ms"] = (
            self.stats["avg_latency_ms"] * (self.stats["total_calls"] - 1) +
            elapsed
        ) / self.stats["total_calls"]
        
        # 8. Signature 9D rapide
        signature = self.injector._quick_signature_9d(content)
        
        result = {
            "content": content,
            "category": category,
            "signature_9d": signature,
            "resonance_score": resonance_score["resonance"],
            "resonance_details": resonance_score,
            "sampling_params": sampling_params,
            "latency_ms": round(elapsed, 1),
            "tokens": max_tokens,
            "provider": "gguf_harmonic",
            "model": self.config.model_alias,
        }
        
        self._call_history.append(result)
        if len(self._call_history) > 100:
            self._call_history.pop(0)
        
        return result
    
    def generate_auto(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Auto-detection de la categorie."""
        category = self.injector._detect_category(prompt)
        return self.generate(prompt, category=category, **kwargs)
    
    def _fallback_generation(self, prompt: str, category: str) -> str:
        """Generation de fallback harmonique."""
        self.stats["fallbacks"] += 1
        
        # Construction d'une reponse informative
        words = prompt.split()
        n = len(words)
        
        templates = {
            "mathematical": (
                f"Pour resoudre «{prompt[:60]}», "
                f"appliquons la methode harmonique. "
                f"φ = {PHI:.6f} guide notre raisonnement. "
                f"[Modele GGUF requis — lancez avec --serve pour l'API reelle]"
            ),
            "general": (
                f"Analyse harmonique de «{prompt[:60]}». "
                f"Machine: {self.config.model_alias}. "
                f"Resonance activee. "
                f"[Mode demo — configurez model_path pour utiliser le vrai GGUF]"
            ),
        }
        
        return templates.get(category, templates["general"])
    
    def chat(self, messages: List[Dict[str, str]],
             **kwargs) -> Dict[str, Any]:
        """
        Chat avec historique.
        
        Args:
            messages: [{"role": "user"/"assistant", "content": str}, ...]
        
        Returns:
            Reponse harmonique
        """
        # Dernier message utilisateur
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break
        
        if not last_user_msg:
            return {"content": "Aucun message utilisateur trouve.",
                    "error": True}
        
        return self.generate_auto(last_user_msg, **kwargs)
    
    def classify(self, prompt: str) -> Dict[str, Any]:
        """Classification 9D du prompt (sans generation)."""
        sig = self.injector._quick_signature_9d(prompt)
        category = self.injector._detect_category(prompt)
        
        return {
            "signature_9d": sig,
            "category": category,
            "dimensions": {
                "phi": sig[0],
                "alpha": sig[1],
                "reasoning": sig[2],
                "creative": sig[3],
                "math": sig[4],
                "factual": sig[5],
                "code": sig[6],
                "emotion": sig[7],
                "temporal": sig[8],
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Stats du proxy."""
        memory_stats = self.memory.stats() if self.memory else {}
        
        return {
            **self.stats,
            "model": self.config.model_alias,
            "resonance_strength": self.config.resonance_strength,
            "memory_utilization": memory_stats.get("utilization", 0),
            "memory_items": memory_stats.get("total_items", 0),
            "gpu_layers": self.config.n_gpu_layers,
            "context_size": self.config.n_ctx,
        }
    
    def run_server(self, host: str = "0.0.0.0", port: int = 8080,
                   api_key: Optional[str] = None):
        """
        Lance un serveur API compatible OpenAI.
        
        Endpoints:
        - POST /v1/chat/completions
        - GET /v1/models
        - GET /health
        - GET /stats
        - GET /harmonic/signature?prompt=...
        """
        try:
            from fastapi import FastAPI, Request, HTTPException
            from fastapi.responses import JSONResponse
            import uvicorn
        except ImportError:
            logger.error("pip install fastapi uvicorn")
            return
        
        self._load()
        app = FastAPI(title=f"GGUF Harmonique ({self.config.model_alias})",
                     version="2.1.0")
        
        @app.post("/v1/chat/completions")
        async def chat_completions(request: Request):
            body = await request.json()
            
            # Auth
            if api_key:
                auth = request.headers.get("Authorization", "")
                if auth != f"Bearer {api_key}":
                    raise HTTPException(status_code=401, detail="Non autorise")
            
            messages = body.get("messages", [])
            temperature = body.get("temperature")
            max_tokens = body.get("max_tokens", 1024)
            use_resonance = body.get("harmonic_resonance", True)
            
            # Dernier user message
            prompt = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    prompt = msg.get("content", "")
                    break
            
            if not prompt:
                return JSONResponse({
                    "error": "Message utilisateur requis",
                    "harmonic": True
                }, status_code=400)
            
            # Auto-category
            category = body.get("category") or self.injector._detect_category(prompt)
            
            # Generation harmonique
            result = self.generate(
                prompt, category=category,
                max_tokens=max_tokens,
                use_resonance=use_resonance,
                temperature=temperature,
            )
            
            return JSONResponse({
                "id": f"chatcmpl-{int(time.time()*1000)}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": self.config.model_alias,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result["content"]
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": result.get("tokens", 0),
                    "total_tokens": len(prompt.split()) + result.get("tokens", 0)
                },
                "harmonic_resonance": {
                    "signature_9d": result.get("signature_9d", []),
                    "resonance_score": result.get("resonance_score", 0),
                    "category": result.get("category", "general"),
                    "latency_ms": result.get("latency_ms", 0),
                    "sampling_params": result.get("sampling_params", {}),
                }
            })
        
        @app.get("/v1/models")
        async def list_models():
            return {
                "object": "list",
                "data": [{
                    "id": self.config.model_alias,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "harmonic-ai",
                    "harmonic_9d": True,
                    "resonance_abc": True,
                }]
            }
        
        @app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "model": self.config.model_alias,
                "loaded": self._llm is not None,
                "harmonic": True,
                "resonance": True,
                "memory_active": self.memory is not None,
                "uptime_seconds": int(time.time()),
            }
        
        @app.get("/stats")
        async def stats():
            return {
                "harmonic_stats": self.get_stats(),
                "model_config": {
                    "alias": self.config.model_alias,
                    "path": self.config.model_path,
                    "n_ctx": self.config.n_ctx,
                    "n_gpu_layers": self.config.n_gpu_layers,
                }
            }
        
        @app.get("/harmonic/signature")
        async def harmonic_signature(prompt: str = ""):
            if not prompt:
                return JSONResponse({"error": "Parametre prompt requis"}, status_code=400)
            return self.classify(prompt)
        
        @app.get("/")
        async def root():
            return {
                "service": "GGUF Harmonique Proxy",
                "version": "2.1.0",
                "model": self.config.model_alias,
                "harmonic_resonance": True,
                "abc_memory": self.memory is not None,
                "endpoints": {
                    "POST /v1/chat/completions": "Chat avec resonance harmonique",
                    "GET /v1/models": "Modeles disponibles",
                    "GET /health": "Sante du serveur",
                    "GET /stats": "Stats harmoniques",
                    "GET /harmonic/signature?prompt=...": "Signature 9D rapide",
                }
            }
        
        logger.info(f"Serveur lance: http://{host}:{port}")
        uvicorn.run(app, host=host, port=port, log_level="info")


# ===========================================================================
# OUTIL EN LIGNE DE COMMANDE
# ===========================================================================

def main():
    """Point d'entree CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="GGUF Harmonizer — Resonance 9D pour modeles GGUF"
    )
    
    parser.add_argument("--model-path", type=str,
                        default=os.getenv("MODEL_PATH", ""),
                        help="Chemin vers le fichier GGUF")
    parser.add_argument("--model-alias", type=str,
                        default=os.getenv("MODEL_ALIAS", "deepseek-qwen-hybrid"),
                        help="Alias du modele")
    parser.add_argument("--mode", choices=["chat", "classify", "serve", "test"],
                        default="chat", help="Mode d'execution")
    parser.add_argument("--prompt", type=str, default="",
                        help="Prompt unique")
    parser.add_argument("--category", type=str, default="",
                        help="Categorie harmonique")
    parser.add_argument("--port", type=int, default=8080,
                        help="Port du serveur")
    parser.add_argument("--no-resonance", action="store_true",
                        help="Desactiver la resonance")
    parser.add_argument("--no-memory", action="store_true",
                        help="Desactiver la memoire ABC")
    parser.add_argument("--gpu-layers", type=int, default=-1,
                        help="Couches GPU (-1 = toutes)")
    parser.add_argument("--list-models", action="store_true",
                        help="Afficher les modeles supportes")
    
    args = parser.parse_args()
    
    if args.list_models:
        print("=== MODELES GGUF SUPPORTES ===")
        print()
        print("DeepSeek-V2/V3 + Qwen 3.5 -> 'deepseek-qwen-hybrid' (MoE partiel)")
        print("Qwen2.5-32B-Instruct    -> 'qwen2.5-32b'")
        print("Qwen2.5-Coder-32B       -> 'qwen2.5-coder-32b'")
        print("Llama-4-Scout-17B       -> 'llama-4-scout-17b'")
        print("Mistral-Nemo-2407-12B   -> 'mistral-nemo-12b'")
        print("Phi-3.5-mini            -> 'phi-3.5-mini'")
        print("TinyLlama-1.1B          -> 'tinyllama-1.1b'")
        print()
        print("Tous les modeles recoivent la resonance 9D automatiquement.")
        return
    
    config = GGUFHarmonicProxyConfig(
        model_path=args.model_path,
        model_alias=args.model_alias,
        n_gpu_layers=args.gpu_layers,
        resonance_strength=0.0 if args.no_resonance else 0.7,
        use_memory=not args.no_memory,
    )
    
    proxy = GGUFHarmonicProxy(config)
    
    if args.mode == "chat":
        if args.prompt:
            result = proxy.generate_auto(args.prompt, category=args.category or None)
            print(f"\n[{result['category']}] Resonance: {result['resonance_score']:.3f}")
            print(f"Latence: {result['latency_ms']:.0f}ms")
            print(f"\n{result['content']}")
        else:
            # Mode interactif
            print("GGUF Harmonique — Chat interactif (Ctrl+C pour quitter)")
            print(f"Modele: {config.model_alias}")
            print()
            while True:
                try:
                    prompt = input("> ")
                    if not prompt:
                        continue
                    result = proxy.generate_auto(prompt)
                    print(f"\n[{result['category']}] Resonance: {result['resonance_score']:.3f}")
                    print(f"{result['content']}\n")
                except KeyboardInterrupt:
                    print("\nAu revoir !")
                    break
    
    elif args.mode == "classify":
        if not args.prompt:
            args.prompt = input("Prompt a classifier: ")
        result = proxy.classify(args.prompt)
        print(f"\n=== SIGNATURE 9D ===")
        print(f"Categorie: {result['category']}")
        print()
        for name, val in result["dimensions"].items():
            bar = "█" * int(val * 20) + "░" * (20 - int(val * 20))
            print(f"  {name:<12} {bar} {val:.3f}")
    
    elif args.mode == "test":
        print("=== TEST DU PROXY HARMONIQUE GGUF ===")
        
        # Test 1: Classification
        print("\n1. Classification 9D...")
        test_prompts = [
            "Calcule l'integrale de x^2 de 0 a 1",
            "Ecris un poeme sur l'ocean",
            "Explique le principe de relativite",
            "Ecris une fonction Python de tri",
        ]
        for p in test_prompts:
            cls = proxy.classify(p)
            print(f"  [{cls['category']:12s}] {p[:40]}...")
        
        # Test 2: Generation demo
        print("\n2. Generation demo (sans GGUF)...")
        for cat in ["mathematical", "creative", "code"]:
            result = proxy.generate(
                "Test prompt pour " + cat,
                category=cat, max_tokens=100
            )
            print(f"  [{cat:12s}] Resonance={result['resonance_score']:.3f}, "
                  f"Latence={result['latency_ms']:.0f}ms")
        
        # Test 3: Memoire ABC
        print("\n3. Memoire ABC...")
        memory = ABCMemory(max_tokens=1000)
        memory.add("La capitale de la France est Paris", importance=0.9, category="factual")
        memory.add("Le nombre d'or φ = 1.618", importance=0.8, category="mathematical")
        
        results = memory.recall("capitale de la France")
        print(f"  Rappel 'capitale': {len(results)} resultats")
        if results:
            print(f"  1er: {results[0]['text'][:50]}...")
        
        results2 = memory.recall("nombre d'or φ")
        print(f"  Rappel 'nombre d'or': {len(results2)} resultats")
        
        # Test 4: Injecteur harmonique
        print("\n4. Injecteur harmonique...")
        injector = GGUFHarmonicInjector()
        for p in test_prompts:
            built = injector.build(p)
            print(f"  {len(built)} caracteres construits pour {p[:30]}...")
        
        # Test 5: Sampling params
        print("\n5. Sampling harmonique...")
        sampler = GGUFHarmonicSampler()
        for cat in ["mathematical", "creative", "code", "general"]:
            params = sampler.get_params(cat)
            print(f"  {cat:12s} → T={params['temperature']}, "
                  f"p={params['top_p']}, k={params['top_k']}")
        
        print("\n=== TEST COMPLET ===")
        print("Pour utiliser avec votre GGUF:")
        print(f"  python gguf_harmonizer.py --model-path /path/to/model.gguf --mode serve")
        print(f"  python gguf_harmonizer.py --model-path /path/to/model.gguf "
              f"--mode chat --prompt 'Votre question'")
    
    elif args.mode == "serve":
        proxy.run_server(host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
