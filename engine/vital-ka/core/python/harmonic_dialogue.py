"""
Harmonic Dialogue — La Forme comme Onde
=========================================
Le dialogue n'est pas un échange de faits. C'est une DANSE de ψ
entre deux consciences. Chaque réplique module l'onde commune.

LES 4 NIVEAUX DE LA FORME :

  Niveau 1 — VARIATION : un fait = ∞ expressions par rotation de phase
  Niveau 2 — ADAPTATION : la réponse se module au ψ_dialogue accumulé
  Niveau 3 — ÉMOTION : mirroring affectif par résonance de phase
  Niveau 4 — PROACTIVITÉ : l'IA prend l'initiative, danse avec l'humain

ARCHITECTURE :
  ψ_utilisateur ──▶ ψ_dialogue ──▶ Modulation ──▶ Expression naturelle
                         ▲                            │
                         │                            ▼
                         └────── Feedback ────────────┘

Usage :
    from harmonic_dialogue import HarmonicDialogue
    
    dialogue = HarmonicDialogue(brain)
    response = dialogue.respond("Bonjour, peux-tu m'expliquer la relativité ?")
    # → réponse naturelle, contextuelle, variée, émotionnelle
"""

import math, time, random, logging, re
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
import numpy as np

log = logging.getLogger(__name__)

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI
TAU = 2.0 * math.pi

# ═══════════════════════════════════════════════════════════════════════════════
# NIVEAU 1 : VARIATION — Banque d'expressions riches
# ═══════════════════════════════════════════════════════════════════════════════

# Au lieu d'un template rigide, une banque de structures naturelles
# Chaque structure a un « ψ de style » qui peut être modulé

EXPRESSION_PATTERNS = {
    # Définition simple
    'definition': [
        "{sujet}, c'est {objet}.",
        "{objet} : voilà ce qu'est {sujet}.",
        "Pour faire simple, {sujet} est {objet}.",
        "{sujet} ? C'est {objet}, tout simplement.",
        "Tu veux savoir ce qu'est {sujet} ? C'est {objet}.",
        "En une phrase : {sujet} est {objet}.",
        "{sujet} désigne {objet}.",
    ],
    # Explication détaillée
    'explanation': [
        "Alors, {sujet}, c'est intéressant. {objet}. Et ce qui est fascinant, c'est que ça a des implications profondes.",
        "{objet}. C'est le principe de base. Après, si tu veux creuser, on peut aller plus loin.",
        "Bon, {sujet}. {objet}. Tu me suis ?",
        "Je vais t'expliquer {sujet}. {objet}. C'est plus clair comme ça ?",
        "{objet}. Voilà l'essentiel. Il y a bien sûr des nuances, mais c'est le cœur du sujet.",
        "Pour comprendre {sujet}, il faut d'abord savoir que {objet}. C'est la clé.",
    ],
    # Action / découverte
    'action': [
        "C'est {sujet} qui a {relation} {objet}.",
        "{sujet} a {relation} {objet} — un moment clé.",
        "Tu savais que {sujet} a {relation} {objet} ?",
        "Petite anecdote : {sujet} a {relation} {objet}.",
        "{sujet} a {relation} {objet}. Ça a tout changé.",
    ],
    # Fait géographique
    'geo': [
        "{sujet} est la capitale de {objet}.",
        "La capitale de {objet}, c'est {sujet}.",
        "{sujet} — c'est la capitale de {objet}.",
        "{objet} a pour capitale {sujet}.",
    ],
    # Connexion / créativité
    'creative': [
        "C'est drôle que tu me demandes ça. {sujet} et {objet}, c'est comme... {relation}. Tu vois le lien ?",
        "Il y a une connexion intéressante : {sujet} {relation} {objet}. On n'y pense pas souvent.",
        "Laisse-moi te faire une connexion : {sujet} {relation} {objet}. C'est beau, non ?",
        "{sujet} {relation} {objet}. C'est le genre de lien qui fait réfléchir.",
    ],
    # Je ne sais pas (honnête mais élégant)
    'dont_know': [
        "Je ne connais pas assez bien ce sujet pour te répondre avec certitude. Tu veux que je creuse ?",
        "Honnêtement, ça dépasse mes connaissances actuelles. Mais je peux essayer de trouver une réponse.",
        "Je préfère te dire que je ne sais pas plutôt que d'inventer. Tu as une autre question ?",
        "Sur ce point précis, je cale. Par contre, si tu veux, je peux chercher sur le web.",
        "Je n'ai pas assez d'éléments là-dessus. C'est un sujet que j'aimerais apprendre, d'ailleurs.",
    ],
    # Réponse conversationnelle
    'conversation': [
        "Ah, bonne question ! Alors voilà : {sujet} {relation} {objet}.",
        "Tiens, ça me fait penser : {sujet} {relation} {objet}.",
        "Écoute, c'est simple : {sujet} {relation} {objet}.",
        "Alors, par où commencer... {sujet} {relation} {objet}. C'est la base.",
    ],
}

# ═══════════════════════════════════════════════════════════════════════════════
# NIVEAU 2 : MODULATION PAR LE DIALOGUE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DialogueState:
    """L'état complet du dialogue — l'onde accumulée."""
    psi_dialogue: np.ndarray = None        # onde accumulée de la conversation
    turn_count: int = 0                    # nombre d'échanges
    emotional_charge: float = 0.0          # -1 (négatif) à +1 (positif)
    engagement: float = 0.5               # 0 (décroche) à 1 (captivé)
    formality: float = 0.5                # 0 (décontracté) à 1 (formel)
    creativity_level: float = 0.3         # 0 (factuel) à 1 (poétique)
    verbosity: float = 0.5                # 0 (concis) à 1 (détaillé)
    last_subject: str = ""                # sujet de la dernière question
    topics_history: deque = field(default_factory=lambda: deque(maxlen=10))
    coherence_trend: List[float] = field(default_factory=list)  # historique de cohérence


# ═══════════════════════════════════════════════════════════════════════════════
# MOTEUR DE DIALOGUE HARMONIQUE
# ═══════════════════════════════════════════════════════════════════════════════

class HarmonicDialogue:
    """
    Le dialogue comme danse d'ondes.
    
    Transforme les réponses factuelles du cerveau en expressions
    naturelles, variées, émotionnellement adaptées.
    """

    def __init__(self, brain=None, dim: int = 512, encoder=None):
        self.brain = brain
        self.encoder = encoder
        self.dim = dim
        if brain is not None:
            self.encoder = brain.unconscious.encoder
            self.dim = brain.unconscious.dim

        self.state = DialogueState()
        self._init_psi()

        # Mémoire des expressions utilisées (pour éviter la répétition)
        self._used_patterns: deque = deque(maxlen=20)
        
        # Personnalité (modulable)
        self.persona = {
            'name': 'KA',
            'warmth': 0.7,          # chaleur (0=froid, 1=chaleureux)
            'humor': 0.3,           # humour (0=sérieux, 1=espiègle)
            'curiosity': 0.6,       # curiosité (0=passif, 1=très curieux)
            'precision': 0.8,       # précision (0=approximatif, 1=rigoureux)
            'creativity': 0.4,      # créativité (0=factuel, 1=poétique)
        }

    def _init_psi(self):
        """Initialise le ψ_dialogue (onde vide)."""
        self.state.psi_dialogue = np.zeros(self.dim, dtype=np.complex128)

    def _get_psi(self, text: str) -> np.ndarray:
        """Encode un texte en ψ déterministe."""
        np.random.seed(hash(text) & 0xFFFFFFFF)
        real = np.random.randn(self.dim)
        imag = np.random.randn(self.dim)
        v = real + 1j * imag
        return v / (np.linalg.norm(v) + 1e-10)

    def _coherence(self, psi_a: np.ndarray, psi_b: np.ndarray) -> float:
        """Cohérence de phase entre deux ψ (0-1)."""
        if psi_a is None or psi_b is None:
            return 0.0
        dot = np.abs(np.dot(psi_a.conj(), psi_b))
        na = np.linalg.norm(psi_a)
        nb = np.linalg.norm(psi_b)
        return min(1.0, float(dot / (na * nb + 1e-10)))

    # ═══════════════════════════════════════════════════════════════════════
    # NIVEAU 3 : DÉTECTION ÉMOTIONNELLE
    # ═══════════════════════════════════════════════════════════════════════

    def _detect_emotion(self, text: str) -> float:
        """
        Détecte la charge émotionnelle d'un texte (-1 à +1).
        
        Basé sur des marqueurs lexicaux + cohérence avec le dialogue.
        """
        t = text.lower()
        
        # Marqueurs positifs
        positive = ['merci', 'super', 'génial', 'excellent', 'parfait', 'j\'adore',
                    'intéressant', 'passionnant', 'beau', 'bien', 'cool', 'bravo',
                    'love', 'great', 'awesome', 'thanks', 'wonderful', 'fantastic',
                    'utile', 'clair', 'aide', 'plaisir', 'agréable']
        # Marqueurs négatifs
        negative = ['nul', 'faux', 'incorrect', 'mauvais', 'horrible', 'décevant',
                    'inutile', 'compliqué', 'confus', 'bizarre', 'étrange', 'non',
                    'pas', 'jamais', 'erreur', 'problème', 'difficile', 'triste',
                    'wrong', 'bad', 'terrible', 'useless', 'confusing']
        # Marqueurs d'urgence
        urgent = ['vite', 'urgent', 'maintenant', 'tout de suite', 'help', 'aide moi',
                  'urgence', 'danger', 'problème', 'aidez', 'secours', 'au secours']
        
        pos = sum(1 for w in positive if w in t)
        neg = sum(1 for w in negative if w in t)
        urg = sum(1 for w in urgent if w in t)
        
        score = (pos - neg) / (pos + neg + 1) * 0.7
        if urg > 0:
            score -= 0.3  # l'urgence teinte négativement
        
        return max(-1.0, min(1.0, score))

    def _detect_engagement(self, question: str) -> float:
        """
        Détecte le niveau d'engagement de l'utilisateur.
        
        · Questions longues et détaillées → fort engagement
        · Questions courtes → engagement moyen
        · Suivi cohérent → engagement croissant
        """
        words = len(question.split())
        psi_q = self._get_psi(question)
        
        # Longueur
        length_score = min(1.0, words / 30.0) * 0.4
        
        # Cohérence avec le dialogue précédent
        if self.state.turn_count > 0:
            coherence = self._coherence(psi_q, self.state.psi_dialogue)
            coherence_score = coherence * 0.4
        else:
            coherence_score = 0.3
        
        # Complexité (présence de mots de liaison = raisonnement)
        connectors = ['donc', 'alors', 'parce que', 'cependant', 'mais', 'si',
                     'puisque', 'car', 'ainsi', 'toutefois', 'néanmoins']
        connector_count = sum(1 for c in connectors if c in question.lower())
        complexity_score = min(1.0, connector_count / 5.0) * 0.2
        
        return min(1.0, length_score + coherence_score + complexity_score)

    # ═══════════════════════════════════════════════════════════════════════
    # MODULATION DU STYLE
    # ═══════════════════════════════════════════════════════════════════════

    def _modulate_style(self, question: str):
        """
        Module les paramètres de style en fonction du ψ_dialogue.
        
        C'est ici que la FORME s'adapte au contexte — pas de règles,
        juste de l'interférence ondulatoire.
        """
        # Mise à jour de l'état émotionnel
        emotion = self._detect_emotion(question)
        self.state.emotional_charge = (
            self.state.emotional_charge * 0.7 + emotion * 0.3  # lissage
        )
        
        # Engagement
        engagement = self._detect_engagement(question)
        self.state.engagement = (
            self.state.engagement * 0.6 + engagement * 0.4
        )
        
        # Formalité : suit l'engagement
        self.state.formality = 0.3 + self.state.engagement * 0.4
        
        # Créativité : augmente avec l'engagement et les tours
        self.state.creativity_level = min(0.8,
            self.state.engagement * 0.3 + 
            min(1.0, self.state.turn_count / 10.0) * 0.3 +
            self.persona['creativity'] * 0.4
        )
        
        # Verbosité : suit l'engagement
        self.state.verbosity = 0.3 + self.state.engagement * 0.5

    # ═══════════════════════════════════════════════════════════════════════
    # NIVEAU 1 : GÉNÉRATION D'EXPRESSION NATURELLE
    # ═══════════════════════════════════════════════════════════════════════

    def _express(self, subject: str, relation: str, obj: str, 
                 pattern_type: str = 'definition') -> str:
        """
        Génère une expression naturelle et NON répétitive d'un fait.
        
        Utilise la rotation de phase dans l'espace des patterns :
        chaque appel produit une formulation différente.
        """
        patterns = EXPRESSION_PATTERNS.get(pattern_type, 
                                           EXPRESSION_PATTERNS['definition'])
        
        # Rotation de phase : choisir un pattern différent du précédent
        available = [p for p in patterns if p not in self._used_patterns]
        if not available:
            available = patterns
            self._used_patterns.clear()
        
        # Choix pondéré par la personnalité et l'état
        weights = []
        for pat in available:
            w = 1.0
            if self.persona['warmth'] > 0.5 and ('?' in pat or 'écoute' in pat.lower()):
                w *= 1.5
            if self.persona['precision'] > 0.7 and len(pat) > 60:
                w *= 1.3
            if self.state.creativity_level > 0.5 and ('connexion' in pat or 'lien' in pat):
                w *= 1.4
            weights.append(w)
        
        total = sum(weights)
        probs = [w/total for w in weights]
        pattern = np.random.choice(available, p=probs)
        
        self._used_patterns.append(pattern)
        
        # Remplir le template
        sn = subject.strip()
        on = obj.strip()
        rn = relation.strip()
        
        # Ajuster la grammaire basique
        if rn in ('est', 'sont'):
            if on[0].isupper():
                pass  # nom propre
            elif re.match(r'^(un |une |le |la |les |l\'|des |du |de la )', on):
                pass
            elif on[0] in 'aeiouyhéèê':
                on = f"l'{on}"
            else:
                on = f"un {on}" if rn == 'est' else f"des {on}"
        
        # Si la relation contient déjà un verbe (est, a, etc.), ne pas la ré-afficher
        # dans les templates geo où le sujet/objet suffisent
        if pattern_type == 'geo':
            rn = ""  # pas besoin de la relation dans les templates geo
        elif pattern_type == 'action':
            # Pour les actions : si la relation contient déjà 'a ' ou commence par un verbe,
            # on l'utilise telle quelle. Sinon on ajoute.
            if not rn.startswith('a ') and not rn.startswith('ont '):
                rn = f"a {rn}" if rn else rn
            else:
                rn = rn[2:] if rn.startswith('a ') else rn  # enlever le 'a ' pour le template
        
        result = pattern.format(sujet=sn, relation=rn, objet=on)
        
        # Capitalize
        result = result[0].upper() + result[1:] if result else result
        
        return result

    def _express_dont_know(self, question: str) -> str:
        """Exprime 'je ne sais pas' de façon naturelle et variée."""
        patterns = EXPRESSION_PATTERNS['dont_know']
        # Éviter de répéter
        available = [p for p in patterns if p not in self._used_patterns]
        if not available:
            available = patterns
            self._used_patterns.clear()
        
        pattern = random.choice(available)
        self._used_patterns.append(pattern)
        
        # Personnaliser avec le sujet de la question si pertinent
        return pattern

    # ═══════════════════════════════════════════════════════════════════════
    # NIVEAU 4 : PROACTIVITÉ
    # ═══════════════════════════════════════════════════════════════════════

    def _maybe_proactive(self, response: str) -> str:
        """
        Parfois, l'IA prend l'initiative — elle ne fait pas que répondre.
        
        Déclencheurs :
          · 3+ tours → proposer un sujet connexe
          · Engagement élevé → creuser plus profond
          · Sujet répété → suggérer une autre perspective
        """
        if self.state.turn_count < 2:
            return response
        
        # 20% de chance d'ajouter une touche proactive
        if random.random() > 0.2:
            return response
        
        proactives = [
            " D'ailleurs, tu savais que la photosynthèse produit l'oxygène qu'on respire ?",
            " Ça me fait penser à un autre sujet connexe, si ça t'intéresse.",
            " Tu veux qu'on creuse un peu plus ?",
            " C'est fascinant, non ? J'adore ce sujet.",
            " Si tu as d'autres questions, je suis là.",
            " Tu connais le lien avec la relativité ? C'est assez beau.",
        ]
        
        if self.state.engagement > 0.6:
            suffix = random.choice(proactives)
            return response.rstrip('.') + '.' + suffix
        
        return response

    # ═══════════════════════════════════════════════════════════════════════
    # RÉPONSE COMPLÈTE
    # ═══════════════════════════════════════════════════════════════════════

    def respond(self, question: str, facts: List[Tuple[str, str, str]] = None,
                brain_response: str = None, confidence: float = 0.5) -> str:
        """
        Génère une réponse naturelle complète.
        
        Args:
            question: la question de l'utilisateur
            facts: liste de (sujet, relation, objet) du retrieval
            brain_response: réponse brute du cerveau (fallback)
            confidence: confiance de la réponse
        
        Returns:
            réponse naturelle, contextuelle, non répétitive
        """
        # 0. Moduler le style en fonction du dialogue
        self._modulate_style(question)
        
        # 1. Accumuler ψ_dialogue
        psi_q = self._get_psi(question)
        decay = math.exp(-PHI_INV * self.state.turn_count / 10.0)
        self.state.psi_dialogue = (
            self.state.psi_dialogue * decay + psi_q
        )
        norm = np.linalg.norm(self.state.psi_dialogue)
        if norm > 1e-10:
            self.state.psi_dialogue = self.state.psi_dialogue / norm
        
        # 2. Mettre à jour le sujet
        if facts and len(facts) > 0:
            self.state.last_subject = facts[0][0]
            self.state.topics_history.append(facts[0][0])
        
        # 3. Construire la réponse
        response = ""
        
        if facts and len(facts) > 0:
            # Réponse basée sur des faits — EXPRIMER naturellement
            first = facts[0]
            s, r, o = first[0], first[1], first[2]
            
            # Déterminer le type de pattern
            if r in ('est', 'sont', 'reste', 'demeure', 'devient'):
                ptype = 'definition'
            elif r.startswith('a ') or r.startswith('ont '):
                ptype = 'action'
            elif any(w in r.lower() for w in ['capitale', 'situé', 'trouve', 'localisé',
                                               'capitale de', 'capital of']):
                ptype = 'geo'
            elif any(w in r.lower() for w in ['peint', 'écrit', 'decouvert', 'inventé',
                                               'creé', 'composé', 'fondé']):
                ptype = 'action'
            elif self.state.creativity_level > 0.5:
                ptype = 'creative'
            else:
                ptype = 'conversation'
            
            # Exprimer le fait principal
            response = self._express(s, r, o, ptype)
            
            # Ajouter un second fait si pertinent et si l'engagement est élevé
            if len(facts) >= 2 and self.state.engagement > 0.5:
                second = facts[1]
                s2, r2, o2 = second[0], second[1], second[2]
                # Vérifier que ce n'est pas redondant
                if s2.lower() != s.lower() or r2.lower() != r.lower():
                    connectors = [
                        " Et d'ailleurs, ",
                        " Aussi, ",
                        " Je précise que ",
                        " Un autre point : ",
                        " Pour compléter : ",
                    ]
                    conn = random.choice(connectors)
                    sub_response = self._express(s2, r2, o2, 'explanation')
                    # Extraire juste la partie pertinente
                    if '{objet}' in EXPRESSION_PATTERNS['explanation'][0]:
                        sub_response = f"{s2} {r2} {o2}."
                    response += conn + sub_response.lower()
        
        elif brain_response:
            # Utiliser la réponse du cerveau comme base, mais l'embellir
            if confidence < 0.3:
                response = self._express_dont_know(question)
            elif len(brain_response) > 30:
                # La réponse est substantielle, on la polit
                response = brain_response.strip()
                # Remplacer les patterns mécaniques par des variantes
                response = re.sub(r'\bEn premier lieu\b,?\s*', 'D\'abord, ', response)
                response = re.sub(r'\bDe plus\b,?\s*', 'Ensuite, ', response)
                response = re.sub(r'\bPar ailleurs\b,?\s*', 'Et puis, ', response)
                response = re.sub(r'\bAinsi\b,?\s*', 'Donc, ', response)
                response = re.sub(r'\bEn conclusion\b,?\s*', 'Bref, ', response)
                response = re.sub(r'\bEn résumé\b,?\s*', 'Pour résumer, ', response)
                response = re.sub(r'\bSelon Wikipédia\b,?\s*', 'D\'après Wikipédia, ', response)
                # Ajouter une touche naturelle aléatoire
                if self.state.engagement > 0.5 and not response.endswith('?'):
                    touches = [
                        " C'est clair pour toi ?",
                        " Tu veux que j'approfondisse ?",
                        " Intéressant, non ?",
                        "",
                        "",
                    ]
                    response += random.choice(touches)
            else:
                response = brain_response
        else:
            response = self._express_dont_know(question)
        
        # 4. Proactivité (parfois)
        response = self._maybe_proactive(response)
        
        # 5. Mise à jour du compteur
        self.state.turn_count += 1
        
        return response

    def reset(self):
        """Réinitialise le dialogue (nouvelle conversation)."""
        self._init_psi()
        self.state = DialogueState()
        self._used_patterns.clear()

    @property
    def stats(self) -> dict:
        return {
            'turns': self.state.turn_count,
            'engagement': round(self.state.engagement, 3),
            'emotional_charge': round(self.state.emotional_charge, 3),
            'creativity_level': round(self.state.creativity_level, 3),
            'verbosity': round(self.state.verbosity, 3),
            'formality': round(self.state.formality, 3),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)

    print("=" * 60)
    print("  HARMONIC DIALOGUE — Test de la Forme")
    print("=" * 60)

    dialogue = HarmonicDialogue(dim=64)

    # Test 1 : Même fait → expressions variées
    print("\n── Niveau 1 : VARIATION (même fait, 5 expressions) ──")
    for i in range(5):
        resp = dialogue.respond(
            "Qu'est-ce que la lumière ?",
            facts=[("la lumière", "est", "une onde électromagnétique", "PHYSIQUE_FOND")]
        )
        print(f"  {i+1}. {resp[:100]}...")

    # Test 2 : Adaptation au dialogue
    print("\n── Niveau 2 : ADAPTATION (3 tours) ──")
    dialogue2 = HarmonicDialogue(dim=64)
    conversation = [
        "Bonjour !",
        "Explique-moi la relativité.",
        "C'est fascinant ! Peux-tu m'en dire plus ?",
    ]
    for q in conversation:
        facts = [("la relativité", "est", "une théorie d'Einstein", "PHYSIQUE_FOND")] if 'relativité' in q else None
        resp = dialogue2.respond(q, facts=facts)
        print(f"  Q: {q}")
        print(f"  R: {resp[:120]}...")
        print(f"  État: engagement={dialogue2.state.engagement:.2f}, "
              f"créativité={dialogue2.state.creativity_level:.2f}, "
              f"tour={dialogue2.state.turn_count}")
        print()

    # Test 3 : Ne pas savoir (élégant)
    print("── Niveau 1 : JE NE SAIS PAS (3 variantes) ──")
    for i in range(3):
        resp = dialogue.respond("Qu'est-ce que le boson de Higgs ?", confidence=0.1)
        print(f"  {i+1}. {resp[:120]}...")

    print(f"\n✅ Harmonic Dialogue OK — {dialogue2.stats}")
