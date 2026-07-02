"""
Response Composer — Synthèse multi-faits en langage naturel riche
=================================================================
Remplace le StyleEngine qui applique des templates rigides.

Au lieu de :
  "Pour comprendre X, partons du principe que Y. Ceci implique que Z. Ainsi..."

Ce module compose des réponses qui ressemblent à ce qu'un expert humain
écrirait : paragraphes naturels, micro-structures variées, progression
logique adaptée au TYPE de question.

Principes :
  1. ADAPTATION : une définition ≠ une explication de mécanisme ≠ une comparaison
  2. VARIATION : 30+ micro-structures linguistiques, jamais 2 fois la même
  3. PROFONDEUR : courte/standard/détaillée selon l'intention détectée
  4. NATUREL : pas de "intro→lien→conclusion" mécanique
  5. SYNTHÈSE : les faits sont intégrés dans un discours, pas listés

Usage :
  from response_composer import ResponseComposer
  from question_analyzer import analyze_question

  composer = ResponseComposer()
  intent = analyze_question("explique la lumiere")
  facts = [("lumiere", "est une", "onde electromagnetique", "PHYSIQUE_FOND")]
  response = composer.compose(intent, facts)
"""

import random
from typing import List, Tuple, Optional, Dict
from question_analyzer import QuestionIntent, analyze_question

# Tentative d'import de _fix_accents (style_engine)
try:
    from style_engine import _fix_accents, _cap_first
except ImportError:
    def _fix_accents(text): return text
    def _cap_first(text): return text[0].upper() + text[1:] if text else text


# Type alias pour un fait : (sujet, relation, objet, secteur)
Fact = Tuple[str, str, str, str]


# ═══════════════════════════════════════════════════════════════════════════════
# MICRO-STRUCTURES LINGUISTIQUES (variées, naturelles)
# ═══════════════════════════════════════════════════════════════════════════════

# Ouvertures contextuelles (premier fait présenté de manière naturelle)
_OPENINGS = [
    "{sujet} {relation} {objet}.",
    "Il convient d'abord de noter que {sujet} {relation} {objet}.",
    "Pour commencer, {sujet} {relation} {objet}.",
    "L'essentiel à retenir : {sujet} {relation} {objet}.",
    "Fondamentalement, {sujet} {relation} {objet}.",
    "Le point de départ est que {sujet} {relation} {objet}.",
    "Il faut savoir que {sujet} {relation} {objet}.",
    "À la base, {sujet} {relation} {objet}.",
]

# Connecteurs pour faits additionnels (varier à chaque fois)
_ADDITIONS = [
    "De plus, {sujet} {relation} {objet}.",
    "Par ailleurs, {sujet} {relation} {objet}.",
    "Il faut également souligner que {sujet} {relation} {objet}.",
    "Un autre aspect important : {sujet} {relation} {objet}.",
    "On notera aussi que {sujet} {relation} {objet}.",
    "À cela s'ajoute le fait que {sujet} {relation} {objet}.",
    "En complément, {sujet} {relation} {objet}.",
    "Il est par ailleurs établi que {sujet} {relation} {objet}.",
]

# Conclusions naturelles (pas de "Ainsi" systématique)
_CONCLUSIONS = [
    "Ces éléments permettent de mieux cerner la question.",
    "Voilà qui devrait éclairer votre interrogation.",
    "L'ensemble de ces faits dessine une image cohérente.",
    "Ces différents aspects se complètent mutuellement.",
    "C'est cette combinaison de facteurs qui est essentielle ici.",
]

# ─── Spécifique MÉCANISME (comment/pourquoi) ─────────────────────────────────

_MECA_CAUSE = [
    "Cela s'explique par le fait que {sujet} {relation} {objet}.",
    "La raison en est que {sujet} {relation} {objet}.",
    "Ce phénomène tient à ce que {sujet} {relation} {objet}.",
    "On l'explique par : {sujet} {relation} {objet}.",
    "C'est parce que {sujet} {relation} {objet}.",
]

_MECA_CONSEQUENCE = [
    "Cette interaction conduit à : {sujet} {relation} {objet}.",
    "Il en résulte que {sujet} {relation} {objet}.",
    "La conséquence directe est que {sujet} {relation} {objet}.",
    "De cette dynamique découle le fait que {sujet} {relation} {objet}.",
]

# ─── Spécifique DÉFINITION ───────────────────────────────────────────────────

_DEF_OPENINGS = [
    "{sujet} se définit comme {objet}.",
    "Par {sujet}, on entend {objet}.",
    "Le terme de {sujet} désigne {objet}.",
    "{sujet} correspond à {objet}.",
    "On peut définir {sujet} comme {objet}.",
]

_DEF_DETAIL = [
    "Plus précisément, {sujet} {relation} {objet}.",
    "Pour entrer dans le détail, {sujet} {relation} {objet}.",
    "En d'autres termes, {sujet} {relation} {objet}.",
]

# ─── Spécifique IDENTITÉ (qui a découvert/inventé) ───────────────────────────

_IDENTITY_RESPONSES = [
    "C'est {sujet} qui {relation} {objet}.",
    "{sujet} {relation} {objet}.",
    "Il s'agit de {sujet}, qui {relation} {objet}.",
]


# ═══════════════════════════════════════════════════════════════════════════════
# COMPOSEUR DE RÉPONSES
# ═══════════════════════════════════════════════════════════════════════════════

class ResponseComposer:
    """
    Synthétise des faits de la KB en une réponse naturelle et riche.

    Le composeur :
      1. Reçoit l'intention (type de question, sujet, profondeur)
      2. Reçoit les faits pertinents (3-7 triplets)
      3. Compose une réponse adaptée au type de question
      4. Varie la structure pour éviter la mécanicité
    """

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self._used_structures = set()  # anti-répétition

    def compose(self, intent: QuestionIntent, facts: List[Fact],
                enrichissement: Optional[str] = None,
                contexte_precedent: Optional[str] = None) -> str:
        """
        Compose une réponse complète.

        Args:
            intent: analyse de la question (type, sujet, profondeur)
            facts: liste de faits (sujet, relation, objet, secteur)
            enrichissement: bloc explicatif optionnel (paragraphe dense)
            contexte_precedent: sujet de la question précédente (pour follow-up)

        Returns:
            réponse en français naturel
        """
        if not facts and not enrichissement:
            return self._compose_empty(intent)

        # Contexte : si on a un sujet précédent → transition contextuelle
        prefix = ''
        if contexte_precedent and contexte_precedent in intent.original.lower():
            prefix = self._transition_contextuelle(contexte_precedent, intent)

        # Si on a un bloc explicatif ET que la profondeur est détaillée
        # → utiliser directement le bloc (qualité LLM)
        if enrichissement and intent.profondeur in ('detaillee', 'standard'):
            base = enrichissement
            q_sujet = intent.sujet.lower().strip()
            relevant_facts = []
            for f in facts[1:]:
                fact_subject = f[0].lower()
                if q_sujet and q_sujet in fact_subject:
                    relevant_facts.append(f)
            if relevant_facts:
                extra = self._compose_additions(relevant_facts, intent)
                if extra:
                    base += ' ' + extra
            if prefix:
                base = prefix + ' ' + base
            return _fix_accents(base)

        # Composer selon le type de question
        composer_fn = {
            'definition': self._compose_definition,
            'mecanisme': self._compose_mecanisme,
            'identite': self._compose_identite,
            'factualite': self._compose_factualite,
            'comparaison': self._compose_comparaison,
            'procedure': self._compose_procedure,
            'conversation': self._compose_conversation,
        }.get(intent.type, self._compose_definition)

        # Filtrer les faits pour ne garder que les pertinents
        # (le sujet du fait doit correspondre au sujet de la question)
        filtered_facts = self._filter_facts(facts, intent)

        response = composer_fn(intent, filtered_facts)

        # Si réponse courte demandée → tronquer à 1-2 phrases
        if intent.profondeur == 'courte':
            sentences = [s.strip() for s in response.split('.') if s.strip()]
            response = '. '.join(sentences[:2]) + '.'

        # Injecter la transition contextuelle si applicable
        if prefix and prefix not in response:
            response = prefix + response

        return _fix_accents(response)

    # ─── COMPOSITION PAR TYPE ────────────────────────────────────────────────

    def _compose_definition(self, intent: QuestionIntent, facts: List[Fact]) -> str:
        """Compose une réponse de définition."""
        if not facts:
            return f"Je n'ai pas encore de définition précise pour « {intent.sujet} »."

        s0, r0, o0, _ = facts[0]
        parts = []

        # Ouverture : définition principale
        opening = random.choice(_DEF_OPENINGS)
        parts.append(opening.format(sujet=s0, objet=o0))

        # Détails additionnels (2-3 faits max)
        for i, (s, r, o, _) in enumerate(facts[1:4]):
            if intent.profondeur == 'courte':
                break
            detail = random.choice(_DEF_DETAIL)
            parts.append(detail.format(sujet=s, relation=r, objet=o))

        # Conclusion pour profondeur détaillée
        if intent.profondeur == 'detaillee' and len(parts) >= 2:
            parts.append(random.choice(_CONCLUSIONS))

        return ' '.join(parts)

    def _compose_mecanisme(self, intent: QuestionIntent, facts: List[Fact]) -> str:
        """Compose une explication de mécanisme (pourquoi/comment)."""
        if not facts:
            return f"Le mécanisme de « {intent.sujet} » n'est pas encore documenté."

        parts = []

        # Ouverture contextuelle
        s0, r0, o0, _ = facts[0]
        opening = random.choice(_OPENINGS)
        parts.append(opening.format(sujet=s0, relation=r0, objet=o0))

        # Causes / explications
        cause_facts = facts[1:]
        if cause_facts and intent.profondeur != 'courte':
            for i, (s, r, o, _) in enumerate(cause_facts[:3]):
                if i == 0:
                    tmpl = random.choice(_MECA_CAUSE)
                else:
                    tmpl = random.choice(_MECA_CONSEQUENCE + _ADDITIONS)
                parts.append(tmpl.format(sujet=s, relation=r, objet=o))

        # Conclusion
        if intent.profondeur == 'detaillee' and len(parts) >= 3:
            parts.append(random.choice(_CONCLUSIONS))

        return ' '.join(parts)

    def _compose_identite(self, intent: QuestionIntent, facts: List[Fact]) -> str:
        """Compose une réponse d'identité (qui a découvert/inventé)."""
        if not facts:
            return f"Je ne sais pas encore qui est associé à « {intent.sujet} »."

        # Pour l'identité, une réponse courte et directe
        s0, r0, o0, _ = facts[0]
        tmpl = random.choice(_IDENTITY_RESPONSES)
        response = tmpl.format(sujet=_cap_first(s0), relation=r0, objet=o0)

        # Un fait de contexte si disponible et profondeur > courte
        if len(facts) > 1 and intent.profondeur != 'courte':
            s1, r1, o1, _ = facts[1]
            add = random.choice(_ADDITIONS)
            response += ' ' + add.format(sujet=s1, relation=r1, objet=o1)

        return response

    def _compose_factualite(self, intent: QuestionIntent, facts: List[Fact]) -> str:
        """Compose une réponse factuelle courte (quand, où)."""
        if not facts:
            return f"Je n'ai pas cette information sur « {intent.sujet} »."

        # Réponse directe, pas d'enrobage
        s0, r0, o0, _ = facts[0]
        response = f"{_cap_first(s0)} {r0} {o0}."

        if len(facts) > 1 and intent.profondeur != 'courte':
            s1, r1, o1, _ = facts[1]
            add = random.choice(_ADDITIONS)
            response += ' ' + add.format(sujet=s1, relation=r1, objet=o1)

        return response

    def _compose_comparaison(self, intent: QuestionIntent, facts: List[Fact]) -> str:
        """Compose une comparaison entre concepts."""
        if len(facts) < 2:
            if facts:
                s, r, o, _ = facts[0]
                return f"Concernant « {intent.sujet} » : {_cap_first(s)} {r} {o}."
            return f"Je n'ai pas assez d'éléments pour comparer « {intent.sujet} »."

        parts = []
        # Premier concept
        s0, r0, o0, _ = facts[0]
        parts.append(f"{_cap_first(s0)} {r0} {o0}.")

        # Deuxième concept
        s1, r1, o1, _ = facts[1]
        parts.append(f"De son côté, {_cap_first(s1)} {r1} {o1}.")

        # Nuance / synthèse
        if intent.profondeur != 'courte':
            parts.append("Ces deux aspects, bien que distincts, se révèlent complémentaires dans leur domaine.")

        return ' '.join(parts)

    def _compose_procedure(self, intent: QuestionIntent, facts: List[Fact]) -> str:
        """Compose une procédure (étapes)."""
        if not facts:
            return f"Je n'ai pas encore de procédure documentée pour « {intent.sujet} »."

        parts = []
        s0, r0, o0, _ = facts[0]
        parts.append(f"Pour « {intent.sujet} », la première étape est que {_cap_first(s0)} {r0} {o0}.")

        for i, (s, r, o, _) in enumerate(facts[1:4], start=2):
            if intent.profondeur == 'courte':
                break
            parts.append(f"Ensuite, {_cap_first(s)} {r} {o}.")

        if intent.profondeur == 'detaillee':
            parts.append("En suivant ces étapes dans l'ordre, le résultat devrait être atteint.")

        return ' '.join(parts)

    def _compose_conversation(self, intent: QuestionIntent, facts: List[Fact]) -> str:
        """Compose une réponse conversationnelle naturelle."""
        if not facts:
            return f"« {intent.sujet} » est un sujet intéressant. Pouvez-vous préciser votre question ?"

        s0, r0, o0, _ = facts[0]
        return f"À propos de « {intent.sujet} » : {_cap_first(s0)} {r0} {o0}."

    def _compose_additions(self, facts: List[Fact], intent: QuestionIntent) -> str:
        """Compose des faits additionnels (pour compléter un enrichissement)."""
        parts = []
        for s, r, o, _ in facts[:2]:
            add = random.choice(_ADDITIONS)
            parts.append(add.format(sujet=s, relation=r, objet=o))
        return ' '.join(parts)

    def _compose_empty(self, intent: QuestionIntent) -> str:
        """Réponse quand aucun fait n'est trouvé."""
        return (f"Je n'ai pas encore assez de connaissances sur « {intent.sujet} ». "
                f"N'hésitez pas à reformuler ou à préciser votre question.")

    def _transition_contextuelle(self, sujet_precedent: str, intent: QuestionIntent) -> str:
        """
        Génère une transition contextuelle élégante quand l'utilisateur
        pose une question de suivi sur un sujet connexe.

        Ex: "explique la lumière" → "et les couleurs ?" →
            "Dans le prolongement de la lumière, les couleurs..."
        """
        transitions = [
            f"Dans le prolongement de {sujet_precedent}, ",
            f"Pour approfondir ce que nous avons vu sur {sujet_precedent}, ",
            f"En lien avec {sujet_precedent}, ",
            f"Toujours à propos de {sujet_precedent}, ",
            f"En complément de {sujet_precedent}, ",
            f"Pour rester dans le thème de {sujet_precedent}, ",
            f"Ce sujet est étroitement lié à {sujet_precedent}. ",
        ]
        return random.choice(transitions)

    def _filter_facts(self, facts: List[Fact], intent: QuestionIntent) -> List[Fact]:
        """
        Filtre les faits pour ne garder que ceux dont le sujet
        correspond réellement au sujet de la question.

        Évite le bruit où un mot-clé partagé ramène des faits hors-sujet.
        """
        if not facts:
            return facts

        q_sujet = intent.sujet.lower().strip()
        q_keywords = set(intent.mots_cles)

        filtered = []
        for s, r, o, sec in facts:
            s_lower = s.lower().strip()
            # Le fait est pertinent si :
            # 1. Son sujet == sujet de la question, OU
            # 2. Son sujet contient le sujet de la question comme mot entier, OU
            # 3. Son objet contient le sujet de la question ET le sujet partage un mot-clé
            is_relevant = False
            if q_sujet and (s_lower == q_sujet or q_sujet in s_lower.split()):
                is_relevant = True
            elif any(kw == s_lower or kw in s_lower.split() for kw in q_keywords):
                is_relevant = True
            # Exception : pour les questions d'identité, le sujet du fait peut être la personne
            elif intent.type == 'identite' and q_sujet in o.lower():
                is_relevant = True

            if is_relevant:
                filtered.append((s, r, o, sec))

        # Si le filtrage est trop strict (0 fait), retourner au moins le premier
        return filtered if filtered else facts[:1]


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTION DE COMMODITÉ
# ═══════════════════════════════════════════════════════════════════════════════

_composer_instance = None

def compose_response(question: str, facts: List[Fact],
                     enrichissement: Optional[str] = None) -> str:
    """
    Fonction de commodité : analyse + composition en un appel.

    Args:
        question: question utilisateur
        facts: faits pertinents de la KB
        enrichissement: bloc explicatif optionnel

    Returns:
        réponse en français naturel
    """
    global _composer_instance
    if _composer_instance is None:
        _composer_instance = ResponseComposer()
    intent = analyze_question(question)
    return _composer_instance.compose(intent, facts, enrichissement)


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    print("=" * 60)
    print("RESPONSE COMPOSER — Démo")
    print("=" * 60)

    tests = [
        ("explique la lumiere", [
            ("lumiere", "est une", "onde electromagnetique", "PHYSIQUE_FOND"),
            ("lumiere", "se deplace a", "300000 km/s", "PHYSIQUE_FOND"),
            ("lumiere", "est composee de", "photons", "PHYSIQUE_FOND"),
        ]),
        ("pourquoi le coeur pompe le sang", [
            ("coeur", "pompe", "le sang", "BIOLOGIE"),
            ("sang", "transporte", "l oxygene", "BIOLOGIE"),
            ("oxygene", "alimente", "les cellules", "BIOLOGIE"),
        ]),
        ("qui a decouvert la relativite", [
            ("einstein", "a decouvert", "la relativite", "PHYSIQUE_FOND"),
            ("einstein", "a publie", "la theorie en 1905", "PASSE"),
        ]),
        ("qu'est-ce que la conscience", [
            ("conscience", "est", "la perception de soi et du monde", "CONSCIENCE"),
            ("conscience", "emerge de", "l activite cerebrale", "CONSCIENCE"),
        ]),
        ("quelle est la difference entre onde et particule", [
            ("onde", "transporte", "de l energie", "PHYSIQUE_FOND"),
            ("particule", "possede", "une masse", "PHYSIQUE_FOND"),
        ]),
    ]

    for question, facts in tests:
        print(f"\n>> {question}")
        for r in range(3):  # 3 variations pour montrer la diversité
            response = compose_response(question, facts)
            print(f"   [{r+1}] {response}")


if __name__ == '__main__':
    demo()
