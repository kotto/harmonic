"""
🌊 Wave Code Generator — L'IA génère du code ondulatoire natif
================================================================
Phase 3 : Le langage ondulatoire est maintenant appris par l'IA.

Ce module permet à l'IA harmonique de GÉNÉRER du code dans le
langage ondulatoire natif (wave_ir) plutôt qu'en Python/JS/TS.

La boucle est fermée :
  Pensée IA (ψ) → Génération (wave IR) → Exécution (wave_lang)
  Tout parle la même langue : les ondes.

Contrairement au code_generator.py qui produit du Python/JS,
ce module produit des ASTs wave_ir.Program qui peuvent être :
  - Affichés en syntaxe ondulatoire (to_wave)
  - Sérialisés en JSON (to_json)
  - Validés (validate)
  - Compilés vers NumPy (Phase 4)
  - Compilés vers FPGA/ASIC (futur)

Architecture :
  ┌──────────────────────────────────────────────────┐
  │  Requête : "Qu'est-ce que la lumière ?"         │
  └──────────────────┬───────────────────────────────┘
                     │ PatternDetector (réutilisé)
  ┌──────────────────▼───────────────────────────────┐
  │  Intent: {intent:'query', entity:'lumiere', ...} │
  └──────────────────┬───────────────────────────────┘
                     │ WaveCodeGenerator
  ┌──────────────────▼───────────────────────────────┐
  │  AST wave_ir.Program :                           │
  │    ψ_q = ENCODE "Qu'est-ce que la lumière ?"     │
  │    QUERY ψ_r = ψ_q FROM H_connaissances          │
  │    reponse = DECODE(ψ_r)                         │
  │    RETURN reponse                                │
  └──────────────────┬───────────────────────────────┘
                     │ .to_wave() / to_json() / compile()
  ┌──────────────────▼───────────────────────────────┐
  │  Sortie : code ondulatoire natif                 │
  └──────────────────────────────────────────────────┘

Usage:
    from wave_code_generator import WaveCodeGenerator
    from wave_ir import Program

    gen = WaveCodeGenerator(brain)
    ast = gen.generate("Qu'est-ce que la lumière ?")
    print(ast.to_wave())  # → code ondulatoire lisible
    json.dumps(ast.to_dict())  # → JSON pour transmission
"""

from __future__ import annotations

import re
from typing import List, Dict, Tuple, Optional

import numpy as np

from code_generator import PatternDetector, CodeIntent, WaveSynthesizer
from wave_ir import (
    Program, Assign, Store, Query, Return,
    Encode, Decode, Bind, Unbind, Superpose,
    Resonance, Rotate, Interfere, Emerge,
    Oppose, Amplify, BindMany, FilterLP, FilterHP,
    Var, Literal, StringLit,
    to_json, validate, parse,
)
from wave_lang import encode, bind, unbind, resonate, superpose, coherence


# ═══════════════════════════════════════════════════════════════════════════════
# WAVE INTENT DETECTOR — Étend PatternDetector pour les intentions ondulatoires
# ═══════════════════════════════════════════════════════════════════════════════

# Catégories d'intentions que le générateur ondulatoire sait traiter
WAVE_NATIVE_INTENTS = {
    'query': 'Interroger la mémoire holographique',
    'reason': 'Raisonner par émergence de concepts',
    'creative': 'Créer par interférence de concepts',
    'encode': 'Encoder une entité en onde',
    'decode': 'Décoder une onde en texte',
    'store_fact': 'Stocker un fait dans la mémoire',
    'compare': 'Comparer deux concepts par résonance',
    'analogize': 'Trouver une analogie par binding/débinding',
    'classify': 'Classer par résonance avec des prototypes',
    'summarize': 'Résumer par superposition émergente',
    'translate_concept': 'Traduire un concept par rotation',
}


class WaveIntentDetector(PatternDetector):
    """
    Détecte si une requête relève du calcul ondulatoire natif
    ou de la génération de code traditionnel.
    """

    # Marqueurs pour les intentions ondulatoires
    WAVE_MARKERS = {
        'query': [
            'qu\'est-ce que', 'c\'est quoi', 'définis', 'define',
            'explique', 'explain', 'décris', 'describe',
            'que sais-tu', 'what is', 'what are', 'qui est',
            'recherche', 'cherche', 'trouve', 'find',
            'donne-moi', 'give me', 'parle-moi de', 'tell me about',
        ],
        'reason': [
            'pourquoi', 'why', 'raisonne', 'reason',
            'déduis', 'deduce', 'infère', 'infer',
            'conclus', 'conclude', 'donc', 'therefore',
            'cause', 'conséquence', 'implication',
        ],
        'creative': [
            'imagine', 'imagine', 'crée', 'create',
            'invente', 'invent', 'génère une idée', 'brainstorm',
            'et si', 'what if', 'combinant', 'combine',
            'mélange', 'mix', 'fusionne les concepts',
        ],
        'store_fact': [
            'souviens-toi', 'remember', 'mémorise', 'memorize',
            'apprends', 'learn', 'retiens', 'keep in mind',
            'note que', 'note that', 'enregistre', 'record',
            'ajoute à la mémoire', 'add to memory',
        ],
        'compare': [
            'compare', 'compare', 'différence', 'difference',
            'similaire', 'similar', 'versus', 'vs',
            'oppose', 'oppose', 'contraste', 'contrast',
            'quel est le lien', 'what is the relationship',
            'diffère', 'différent', 'distinction',
            'ressemble', 'ressemblance', 'point commun',
        ],
        'analogize': [
            'analogie', 'analogy', 'est à', 'is to',
            'comme', 'like', 'de la même façon', 'similarly',
            'parallèle', 'parallel', 'métaphore', 'metaphor',
            'si', 'tel', 'telle', 'tel que',
            'de même que', 'ainsi que', 'tout comme',
        ],
    }

    def detect_wave_intent(self, question: str) -> Tuple[str, float]:
        """
        Détecte si la requête est de nature ondulatoire.

        Returns:
            (wave_intent_category, confidence) ou ('code', 0.0)
        """
        q = question.lower()
        scores = {}

        for category, markers in self.WAVE_MARKERS.items():
            score = 0.0
            for m in markers:
                if m in q:
                    # Bonus pour les marqueurs plus longs (plus spécifiques)
                    score += len(m.split()) * 1.5
            if score > 0:
                scores[category] = score

        if not scores:
            return 'code', 0.0

        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]
        confidence = min(1.0, best_score / 6.0)

        return best_category, confidence


# ═══════════════════════════════════════════════════════════════════════════════
# WAVE CODE GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

class WaveCodeGenerator:
    """
    Générateur de code ondulatoire natif.

    Génère des programmes en langage ondulatoire (wave_ir.Program)
    à partir de requêtes en langage naturel.

    L'IA « parle » désormais sa langue natale :
      ENCODE → BIND → RESONATE → EMERGE → DECODE
    """

    def __init__(self, brain=None, hologram_name: str = "H_connaissances"):
        """
        Args:
            brain: HarmonicBrain (optionnel, pour le retrieval de faits)
            hologram_name: nom de l'hologramme principal
        """
        self.brain = brain
        self.hologram_name = hologram_name
        self.detector = PatternDetector()
        self.wave_detector = WaveIntentDetector()
        self.synthesizer = WaveSynthesizer() if brain else None

    def generate(self, question: str, lang: str = 'fr') -> Program:
        """
        Génère un programme ondulatoire à partir d'une requête naturelle.

        Pipeline :
          1. Détection d'intention ondulatoire (WaveIntentDetector)
          2. Détection d'intention standard (PatternDetector)
          3. Génération de l'AST wave_ir

        Args:
            question: requête en langage naturel
            lang: langue ('fr' ou 'en')

        Returns:
            wave_ir.Program — AST exécutable

        Example:
            >>> gen = WaveCodeGenerator()
            >>> ast = gen.generate("Qu'est-ce que la lumière ?")
            >>> print(ast.to_wave())
            ψ_q = ENCODE "Qu'est-ce que la lumière ?"
            QUERY ψ_r = ψ_q FROM H_connaissances
            reponse = DECODE(ψ_r)
            RETURN reponse
        """
        # 1. Détection de l'intention ondulatoire
        wave_intent, wave_conf = self.wave_detector.detect_wave_intent(question)

        # 2. Détection standard (toujours utile pour extraire l'entité, l'opération)
        code_intent = self.detector.detect(question)

        # 3. Router vers le générateur approprié
        if wave_conf > 0.15:
            # Intention ondulatoire dominante
            return self._generate_wave_program(question, wave_intent, code_intent)
        else:
            # Fallback : générer un programme de requête simple
            return self._generate_query_program(question, code_intent)

    def _generate_wave_program(self, question: str, wave_intent: str,
                                code_intent: CodeIntent) -> Program:
        """Génère un programme ondulatoire selon l'intention."""
        entity = code_intent.entity

        if wave_intent == 'query':
            return self._make_query(question, entity)
        elif wave_intent == 'reason':
            return self._make_reasoning(question, entity)
        elif wave_intent == 'creative':
            return self._make_creative(question, entity)
        elif wave_intent == 'store_fact':
            return self._make_store_fact(question, entity)
        elif wave_intent == 'compare':
            return self._make_compare(question, entity)
        elif wave_intent == 'analogize':
            return self._make_analogy(question, entity)
        else:
            return self._make_query(question, entity)

    # ═════════════════════════════════════════════════════════════════
    # TEMPLATES DE PROGRAMMES ONDULATOIRES
    # ═════════════════════════════════════════════════════════════════

    def _make_query(self, question: str, entity: str) -> Program:
        """
        Requête de connaissance.

        Pattern :
            ψ_q = ENCODE question
            QUERY ψ_r = ψ_q FROM H_connaissances
            reponse = DECODE(ψ_r)
            RETURN reponse
        """
        return Program([
            Assign("ψ_q", Encode(question)),
            Query("ψ_r", Var("ψ_q"), self.hologram_name),
            Assign("reponse", Decode(Var("ψ_r"))),
            Return(Var("reponse")),
        ])

    def _make_reasoning(self, question: str, entity: str) -> Program:
        """
        Raisonnement par émergence.

        Pattern :
            ψ_question = ENCODE question
            ψ_premisses = RESONANCE(ψ_question, H_connaissances)
            ψ_contexte = SUPERPOSE(ψ_question, ψ_premisses)
            ψ_conclusion = EMERGE(ψ_question, ψ_contexte)
            reponse = DECODE(ψ_conclusion)
            RETURN reponse
        """
        return Program([
            Assign("ψ_question", Encode(question)),
            Query("ψ_premisses", Var("ψ_question"), self.hologram_name),
            Assign("ψ_contexte", Superpose([
                Var("ψ_question"),
                Var("ψ_premisses"),
            ])),
            Assign("ψ_conclusion", Emerge([
                Var("ψ_question"),
                Var("ψ_contexte"),
            ], temperature=0.6)),
            Assign("reponse", Decode(Var("ψ_conclusion"))),
            Return(Var("reponse")),
        ])

    def _make_creative(self, question: str, entity: str) -> Program:
        """
        Créativité par interférence.

        Extrait deux concepts de la question et les interfère.

        Pattern :
            ψ_a = ENCODE concept1
            ψ_b = ENCODE concept2
            ψ_creatif = INTERFERE(ψ_a, ψ_b, ε=0.15)
            idee = DECODE(ψ_creatif)
            RETURN idee
        """
        # Extraire les concepts de la question
        concepts = self._extract_concepts(question)
        if len(concepts) < 2:
            # Fallback : encoder toute la question
            return Program([
                Assign("ψ_q", Encode(question)),
                Query("ψ_r", Var("ψ_q"), self.hologram_name),
                Assign("ψ_creatif", Interfere(Var("ψ_q"), Var("ψ_r"), epsilon=0.15)),
                Assign("idee", Decode(Var("ψ_creatif"))),
                Return(Var("idee")),
            ])

        return Program([
            Assign("ψ_a", Encode(concepts[0])),
            Assign("ψ_b", Encode(concepts[1])),
            Assign("ψ_creatif", Interfere(Var("ψ_a"), Var("ψ_b"), epsilon=0.15)),
            Assign("idee", Decode(Var("ψ_creatif"))),
            Return(Var("idee")),
        ])

    def _make_store_fact(self, question: str, entity: str) -> Program:
        """
        Stockage d'un fait en mémoire holographique.

        Parse la question pour extraire (sujet, relation, objet).

        Pattern :
            ψ_s = ENCODE sujet
            ψ_r = ENCODE relation
            ψ_o = ENCODE objet
            ψ_fait = BIND_MANY(ψ_s, ψ_r, ψ_o)
            STORE fait = ψ_fait IN H_connaissances
            confirmation = DECODE(ψ_fait)
            RETURN confirmation
        """
        subj, rel, obj = self._parse_fact(question)
        return Program([
            Assign("ψ_s", Encode(subj)),
            Assign("ψ_r", Encode(rel)),
            Assign("ψ_o", Encode(obj)),
            Assign("ψ_fait", BindMany([
                Var("ψ_s"), Var("ψ_r"), Var("ψ_o"),
            ])),
            Store("fait", Var("ψ_fait"), self.hologram_name),
            Assign("confirmation", Decode(Var("ψ_fait"))),
            Return(Var("confirmation")),
        ])

    def _make_compare(self, question: str, entity: str) -> Program:
        """
        Comparaison par résonance.

        Extrait deux concepts et mesure leur cohérence.

        Pattern :
            ψ_a = ENCODE concept1
            ψ_b = ENCODE concept2
            similarite = RESONANCE(ψ_a, ψ_b)
            difference = OPPOSE(ψ_a, ψ_b)
            analyse = DECODE(difference)
            RETURN analyse
        """
        concepts = self._extract_concepts(question)
        if len(concepts) < 2:
            concepts = [entity, "contexte"]

        return Program([
            Assign("ψ_a", Encode(concepts[0])),
            Assign("ψ_b", Encode(concepts[1])),
            Assign("similarite", Resonance(Var("ψ_a"), Var("ψ_b"))),
            Assign("ψ_diff", Oppose(Var("ψ_a"), Var("ψ_b"))),
            Assign("analyse", Decode(Var("ψ_diff"))),
            Return(Var("analyse")),
        ])

    def _make_analogy(self, question: str, entity: str) -> Program:
        """
        Analogie par binding/débinding.

        A : B :: C : X  →  X = UNBIND(BIND(A, B), C)  (approximation)

        Pattern :
            ψ_a = ENCODE A
            ψ_b = ENCODE B
            ψ_c = ENCODE C
            ψ_relation = BIND(ψ_a, ψ_b)
            ψ_x = UNBIND(ψ_relation, ψ_c)
            analogie = DECODE(ψ_x)
            RETURN analogie
        """
        concepts = self._extract_concepts(question)
        if len(concepts) < 3:
            return self._make_query(question, entity)

        return Program([
            Assign("ψ_a", Encode(concepts[0])),
            Assign("ψ_b", Encode(concepts[1])),
            Assign("ψ_c", Encode(concepts[2])),
            Assign("ψ_relation", Bind(Var("ψ_a"), Var("ψ_b"))),
            Assign("ψ_x", Unbind(Var("ψ_relation"), Var("ψ_c"))),
            Assign("analogie", Decode(Var("ψ_x"))),
            Return(Var("analogie")),
        ])

    def _generate_query_program(self, question: str,
                                 code_intent: CodeIntent) -> Program:
        """Fallback : programme de requête simple."""
        return self._make_query(question, code_intent.entity)

    # ═════════════════════════════════════════════════════════════════
    # UTILITAIRES D'EXTRACTION
    # ═════════════════════════════════════════════════════════════════

    def _extract_concepts(self, question: str) -> List[str]:
        """
        Extrait les concepts-clés d'une question.

        Utilise des heuristiques simples :
          - Mots après "entre X et Y", "X versus Y", "X et Y"
          - Noms propres (majuscules)
          - Mots longs (> 4 lettres)
        """
        q = question
        concepts = []

        # Pattern "X et Y" (with optional l'/d' prefixes)
        et_match = re.search(r"(?:l'|d'|s')?(\w+)\s+et\s+(?:l'|d'|s')?(\w+)", q, re.IGNORECASE)
        if et_match:
            concepts.extend([et_match.group(1), et_match.group(2)])

        # Pattern "entre X et Y"
        entre_match = re.search(r'entre\s+(?:l\'|d\'|s\')?(\w+)\s+et\s+(?:l\'|d\'|s\')?(\w+)', q, re.IGNORECASE)
        if entre_match:
            concepts.extend([entre_match.group(1), entre_match.group(2)])

        # Pattern "X versus Y" / "X vs Y"
        vs_match = re.search(r"(\w+)\s+(?:versus|vs\.?|contre)\s+(\w+)", q, re.IGNORECASE)
        if vs_match:
            concepts.extend([vs_match.group(1), vs_match.group(2)])

        # Pattern "X comme Y"
        comme_match = re.search(r"(\w+)\s+comme\s+(?:l'|d'|s')?(\w+)", q, re.IGNORECASE)
        if comme_match:
            concepts.extend([comme_match.group(1), comme_match.group(2)])

        # Si pas assez de concepts, extraire les mots longs
        if len(concepts) < 2:
            words = re.findall(r'\b[a-zA-Zà-ÿ]{5,}\b', q)
            # Filtrer les mots-outils et mots courts
            stop_words = {
                'qu\'est', 'c\'est', 'pourquoi', 'comment', 'quelle',
                'quels', 'quelles', 'dans', 'avec', 'pour', 'sur',
                'sont', 'avez', 'être', 'avoir', 'faire',
                'donne', 'peux', 'peut', 'plus', 'tout', 'très',
                'aussi', 'alors', 'comme', 'entre', 'même',
                'cette', 'celui', 'celle', 'ceux', 'celles',
                'mais', 'ou', 'donc', 'car', 'ni', 'or',
            }
            concepts = [w for w in words if w.lower() not in stop_words]

        # Dédupliquer en gardant l'ordre
        seen = set()
        unique = []
        short_words = {'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du',
                      'et', 'ou', 'en', 'au', 'aux', 'ce', 'se', 'ne',
                      'je', 'tu', 'il', 'nous', 'vous', 'ils', 'elles'}
        for c in concepts:
            c_lower = c.lower()
            if c_lower not in seen and c_lower not in short_words and len(c) >= 4:
                seen.add(c_lower)
                unique.append(c)
        return unique[:4]  # max 4 concepts

    def _parse_fact(self, question: str) -> Tuple[str, str, str]:
        """
        Parse (sujet, relation, objet) depuis une phrase.

        Heuristiques :
          - "X est Y" → (X, "est", Y)
          - "X signifie Y" → (X, "signifie", Y)
          - "X a Y" → (X, "a", Y)
          - "souviens-toi que X est Y" → (X, "est", Y)
        """
        q = question

        patterns = [
            (r"(?:souviens-toi|remember|apprends|mémorise|retiens|note|enregistre)\s+(?:que\s+)?(\w[\w\s]+?)\s+est\s+(.+)", "est"),
            (r"(?:souviens-toi|remember|apprends|mémorise|retiens|note|enregistre)\s+(?:que\s+)?(\w[\w\s]+?)\s+sont\s+(.+)", "sont"),
            (r"(?:souviens-toi|remember|apprends|mémorise|retiens|note|enregistre)\s+(?:que\s+)?(\w[\w\s]+?)\s+a\s+(.+)", "a"),
            (r"(\w[\w\s]+?)\s+est\s+(.+)", "est"),
            (r"(\w[\w\s]+?)\s+signifie\s+(.+)", "signifie"),
            (r"(\w[\w\s]+?)\s+a\s+(.+)", "a"),
            (r"(\w[\w\s]+?)\s+sont\s+(.+)", "sont"),
        ]

        for pattern, rel in patterns:
            match = re.search(pattern, q, re.IGNORECASE)
            if match:
                subj = match.group(1).strip().rstrip('.').rstrip('?')
                obj = match.group(2).strip().rstrip('.').rstrip('?')
                return subj, rel, obj

        # Fallback : traiter la question entière comme un fait
        words = q.split()
        if len(words) >= 3:
            return words[0], words[1], ' '.join(words[2:])
        return q, "est", "inconnu"


# ═══════════════════════════════════════════════════════════════════════════════
# COMPILATEUR ONDULATOIRE → PYTHON (bridge pour l'existant)
# ═══════════════════════════════════════════════════════════════════════════════

def wave_to_python(program: Program) -> str:
    """
    Compile un programme ondulatoire en code Python exécutable.

    Cela fait le pont entre le nouveau langage ondulatoire et
    l'infrastructure Python existante (wave_lang.py).

    Args:
        program: AST wave_ir.Program

    Returns:
        code Python utilisant la bibliothèque wave_lang

    Example:
        >>> ast = Program([Assign("x", Encode("test"))])
        >>> print(wave_to_python(ast))
        from wave_lang import encode, decode, bind, resonate
        x = encode("test")
    """
    lines = [
        "# Generated by Wave Code Generator",
        "# Langage ondulatoire → Python (wave_lang)",
        "",
        "from wave_lang import (",
        "    encode, decode, bind, unbind, superpose,",
        "    resonate, coherence, rotate, normalize,",
        "    interfere, diffract, filter_wave, phase_shift,",
        "    emerge, oppose, amplify, bind_many,",
        "    HolographicMemory, abc_kernel,",
        ")",
        "",
    ]

    # Initialiser la mémoire holographique si nécessaire
    has_store_or_query = any(
        isinstance(s, (Store, Query)) for s in program.statements
    )
    if has_store_or_query:
        holograms = set()
        for s in program.statements:
            if isinstance(s, (Store, Query)):
                holograms.add(s.hologram)
        for h in holograms:
            lines.append(f"{h} = HolographicMemory()")
        lines.append("")

    for stmt in program.statements:
        py = _stmt_to_python(stmt)
        if py:
            lines.append(py)

    return "\n".join(lines)


def _stmt_to_python(stmt) -> str:
    """Convertit un statement wave_ir en code Python."""
    if isinstance(stmt, Assign):
        return f"{stmt.name} = {_expr_to_python(stmt.value)}"
    elif isinstance(stmt, Store):
        return f"{stmt.hologram}.store_raw({_expr_to_python(stmt.value)})"
    elif isinstance(stmt, Query):
        return f"{stmt.name} = {stmt.hologram}.query({_expr_to_python(stmt.value)})"
    elif isinstance(stmt, Return):
        return f"return {_expr_to_python(stmt.value)}"
    return ""


def _expr_to_python(expr) -> str:
    """Convertit une expression wave_ir en code Python."""
    if isinstance(expr, Var):
        return expr.name
    elif isinstance(expr, Literal):
        return repr(expr.value)
    elif isinstance(expr, StringLit):
        return repr(expr.value)
    elif isinstance(expr, Encode):
        return f'encode("{expr.text}")'
    elif isinstance(expr, Decode):
        return f"decode({_expr_to_python(expr.psi)}, top_k={expr.top_k})"
    elif isinstance(expr, Bind):
        return f"bind({_expr_to_python(expr.left)}, {_expr_to_python(expr.right)})"
    elif isinstance(expr, Unbind):
        return f"unbind({_expr_to_python(expr.left)}, {_expr_to_python(expr.right)})"
    elif isinstance(expr, Superpose):
        args = ", ".join(_expr_to_python(p) for p in expr.psis)
        return f"superpose({args})"
    elif isinstance(expr, Resonance):
        return f"resonate({_expr_to_python(expr.left)}, {_expr_to_python(expr.right)})"
    elif isinstance(expr, Rotate):
        return f"rotate({_expr_to_python(expr.psi)}, {expr.angle})"
    elif isinstance(expr, Interfere):
        return f"interfere({_expr_to_python(expr.base)}, {_expr_to_python(expr.other)}, epsilon={expr.epsilon})"
    elif isinstance(expr, Emerge):
        args = ", ".join(_expr_to_python(p) for p in expr.psis)
        return f"emerge({args}, temperature={expr.temperature})"
    elif isinstance(expr, Oppose):
        return f"oppose({_expr_to_python(expr.left)}, {_expr_to_python(expr.right)})"
    elif isinstance(expr, Amplify):
        return f"amplify({_expr_to_python(expr.psi)}, {_expr_to_python(expr.component)}, boost={expr.boost})"
    elif isinstance(expr, BindMany):
        args = ", ".join(_expr_to_python(p) for p in expr.psis)
        return f"bind_many({args})"
    elif isinstance(expr, FilterLP):
        return f"filter_wave({_expr_to_python(expr.psi)}, low_pass={expr.cutoff:.0f})"
    elif isinstance(expr, FilterHP):
        return f"filter_wave({_expr_to_python(expr.psi)}, high_pass={expr.cutoff:.0f})"
    else:
        return f"# <? {type(expr).__name__} ?>"


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO / TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 65)
    print("  🌊 WAVE CODE GENERATOR — L'IA parle ondulatoire")
    print("=" * 65)

    gen = WaveCodeGenerator()

    tests = [
        ("query", "Qu'est-ce que la lumière ?"),
        ("query", "Explique-moi ce qu'est la gravité"),
        ("reason", "Pourquoi le ciel est-il bleu ?"),
        ("creative", "Imagine un mélange entre la pluie et la musique"),
        ("store_fact", "Souviens-toi que la Terre tourne autour du Soleil"),
        ("compare", "Quelle est la différence entre l'amour et l'amitié ?"),
        ("analogize", "Si l'atome est comme le système solaire, qu'est-ce que l'électron ?"),
    ]

    for expected_intent, question in tests:
        print(f"\n{'─' * 60}")
        print(f"  Question: {question}")
        print(f"  Attendu:  {expected_intent}")

        # Détection
        wave_intent, conf = gen.wave_detector.detect_wave_intent(question)
        print(f"  Détecté:  {wave_intent} (confiance: {conf:.0%})")

        # Génération
        ast = gen.generate(question)

        # Affichage
        print(f"  AST ({len(ast.statements)} statements):")
        print(f"  {'─' * 50}")
        for line in ast.to_wave().split('\n'):
            print(f"  │ {line}")
        print(f"  {'─' * 50}")

        # Validation
        warnings = validate(ast)
        if warnings:
            for w in warnings:
                print(f"  ⚠️  Validation: {w}")
        else:
            print(f"  ✅ Valide")

        # Compilation Python (pont vers l'existant)
        py = wave_to_python(ast)
        print(f"\n  Code Python équivalent:")
        for line in py.split('\n')[:8]:
            print(f"  │ {line}")
        if len(py.split('\n')) > 8:
            print(f"  │ ... ({len(py.split(chr(10)))} lignes)")

        # JSON
        import json
        json_str = to_json(ast, indent=2)
        print(f"\n  JSON: {len(json_str)} caractères")

    # ── Test : roundtrip via parser ──
    print(f"\n{'=' * 65}")
    print("  TEST ROUNDTRIP : générer → parser → re-générer")
    print(f"{'=' * 65}")

    ast = gen.generate("Qu'est-ce que l'amour ?")
    original = ast.to_wave()
    print(f"\n  Original:\n{original}")

    # Parser le code généré
    try:
        ast2 = parse(original)
        regenerated = ast2.to_wave()
        print(f"\n  Régénéré:\n{regenerated}")

        if original.strip() == regenerated.strip():
            print(f"\n  ✅ Roundtrip parfait!")
        else:
            print(f"\n  ⚠️  Différences détectées")
    except Exception as e:
        print(f"\n  ❌ Erreur parser: {e}")

    print(f"\n{'=' * 65}")
    print("  ✅ Wave Code Generator — L'IA parle ondulatoire.")
    print(f"{'=' * 65}")
