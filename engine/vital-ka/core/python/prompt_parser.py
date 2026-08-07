"""
Prompt Parser — Parseur Ondulatoire de Question
=================================================
Transforme une question brute en représentation structurée
compréhensible par le cerveau harmonique.

Usage :
    from prompt_parser import PromptParser
    parser = PromptParser()
    parsed = parser.parse("c'est qui le type qui a peint la joconde")
    print(parsed.type)      # "identite"
    print(parsed.entities)  # ["peintre", "joconde", "mona lisa"]
    print(parsed.weighted_tokens)  # {"joconde": 5.0, "peint": 3.0, ...}
"""

import re
import math
from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass, field

PHI = 1.618033988749895
TAU = 2.0 * math.pi

# ═══════════════════════════════════════════════════════════════════════════════
# STOPWORDS + PATTERNS
# ═══════════════════════════════════════════════════════════════════════════════

_STOPWORDS = {
    'the','a','an','is','are','was','were','of','in','on','at','to',
    'for','with','by','from','and','it','its','that','this',
    'le','la','les','un','une','des','de','du','d','l','est','sont',
    'a','ont','que','qui','quoi','dont','dans','sur','pour','par',
    'avec','et','il','elle','ils','elles','ce','cet','cette','ces',
    'ne','pas','plus','moins','très','trop','aussi','mais','donc','or','car',
}

# Mots vides supplémentaires à ignorer
_FILLER_WORDS = {
    'c est', 'c etait', 'il y a', 'est ce que', 'qu est ce que',
    'je voudrais', 'je veux', 'peux tu', 'pouvez vous', 'dis moi',
    'parle moi', 'explique moi', 'donne moi', 'j aimerais',
    'what is', 'what are', 'who is', 'who are', 'can you', 'could you',
    'tell me', 'i want', 'i would like', 'please', 'thanks',
}

# ═══════════════════════════════════════════════════════════════════════════════
# TYPES D'INTENTION
# ═══════════════════════════════════════════════════════════════════════════════

_INTENT_PATTERNS = {
    'identite': {
        'markers': ['qui est', 'c est qui', 'qui a', 'who is', 'who was',
                    'who discovered', 'who painted', 'who wrote', 'who invented',
                    'qui a decouvert', 'qui a peint', 'qui a ecrit', 'qui a invente',
                    'qui etait', 'connais tu', 'do you know'],
        'format': 'nom + fait',
    },
    'explication': {
        'markers': ['pourquoi', 'explique', 'comment', 'en quoi',
                    'why', 'explain', 'how does', 'how do', 'how',
                    'decris', 'describe', 'what is the reason',
                    'comment fonctionne', 'a quoi sert'],
        'format': 'cause + mécanisme + conséquence',
    },
    'factuel': {
        'markers': ['quelle est', 'quel est', 'quels sont', 'combien',
                    'what is', 'what are', 'how many', 'how much',
                    'quand', 'when', 'where', 'ou', 'ou se trouve',
                    'donne moi', 'donnez moi', 'liste', 'cite'],
        'format': 'fait précis',
    },
    'comparaison': {
        'markers': ['compare', 'comparer', 'différence', 'difference',
                    'similaire', 'similar', 'versus', 'vs', 'ou bien',
                    'oppose', 'what is the difference'],
        'format': 'deux faits parallèles',
    },
    'procedure': {
        'markers': ['comment faire', 'etapes', 'steps', 'tutoriel',
                    'recette', 'comment cuisiner', 'comment fabriquer',
                    'comment installer', 'how to'],
        'format': 'étapes séquentielles',
    },
    'definition': {
        'markers': ['definis', 'define', 'definition', 'c est quoi',
                    'qu est ce que', "qu'est ce qu", 'signifie',
                    'what does', 'meaning of'],
        'format': 'définition + contexte',
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# DATACLASS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class StructuredPrompt:
    """Représentation structurée d'une question."""
    raw: str                              # question originale
    type: str                             # identite, explication, factuel, etc.
    lang: str                             # 'fr' ou 'en'
    entities: List[str] = field(default_factory=list)      # concepts clés extraits
    expanded_entities: List[str] = field(default_factory=list)  # après expansion
    weighted_tokens: Dict[str, float] = field(default_factory=dict)  # token → poids
    expected_format: str = ""             # format de réponse attendu
    is_explanatory: bool = False          # mérite un paragraphe
    subject: str = ""                     # sujet central extrait

    @property
    def key_tokens(self) -> List[str]:
        """Tokens avec poids > 0, triés par poids décroissant."""
        return sorted(self.weighted_tokens, key=lambda t: -self.weighted_tokens[t])


# ═══════════════════════════════════════════════════════════════════════════════
# PARSEUR PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class PromptParser:
    """
    Parseur ondulatoire de question.

    Transforme une question brute en StructuredPrompt avec :
      - Type d'intention détecté
      - Entités extraites et expansées
      - Tokens pondérés par pertinence
      - Format de réponse attendu
    """

    def __init__(self):
        # Cache pour l'expansion d'entités
        self._entity_cache: Dict[str, List[str]] = {}

    # ═════════════════════════════════════════════════════════════════════
    # PARSE PRINCIPAL
    # ═════════════════════════════════════════════════════════════════════

    def parse(self, question: str) -> StructuredPrompt:
        """Parse une question brute en représentation structurée."""
        q = question.strip()
        q_lower = q.lower()

        # 1. Détection de la langue
        lang = self._detect_lang(q_lower)

        # 2. Détection de l'intention
        intent_type, intent_format = self._detect_intent(q_lower, lang)

        # 3. Nettoyage : retirer les mots de remplissage
        cleaned = self._remove_fillers(q_lower)

        # 4. Extraction du sujet central
        subject = self._extract_subject(cleaned, intent_type, lang)

        # 5. Extraction des entités
        entities = self._extract_entities(cleaned, lang)

        # 6. Expansion des entités (synonymes, concepts liés)
        expanded = self._expand_entities(entities)

        # 7. Pondération des tokens
        weights = self._weight_tokens(cleaned, entities, intent_type, lang)

        # 8. Type explicatif ?
        is_explanatory = intent_type in ('explication', 'definition', 'comparaison')

        return StructuredPrompt(
            raw=q,
            type=intent_type,
            lang=lang,
            entities=entities,
            expanded_entities=expanded,
            weighted_tokens=weights,
            expected_format=intent_format,
            is_explanatory=is_explanatory,
            subject=subject,
        )

    # ═════════════════════════════════════════════════════════════════════
    # ÉTAPE 1 : LANGUE
    # ═════════════════════════════════════════════════════════════════════

    def _detect_lang(self, q: str) -> str:
        en = {'what', 'who', 'when', 'where', 'why', 'how', 'the', 'is', 'are', 'of'}
        fr = {'est', 'sont', 'dans', 'pour', 'avec', 'quoi', 'comment', 'pourquoi'}
        score_en = sum(1 for w in q.split() if w.strip('?!.') in en)
        score_fr = sum(1 for w in q.split() if w.strip('?!.') in fr)
        return 'en' if score_en > score_fr else 'fr'

    # ═════════════════════════════════════════════════════════════════════
    # ÉTAPE 2 : INTENTION
    # ═════════════════════════════════════════════════════════════════════

    def _detect_intent(self, q: str, lang: str) -> Tuple[str, str]:
        """Détecte le type d'intention et le format attendu."""
        best_type = 'factuel'
        best_len = 0

        for intent_type, config in _INTENT_PATTERNS.items():
            for marker in config['markers']:
                if marker in q:
                    if len(marker) > best_len:  # préfère le marqueur le plus long
                        best_type = intent_type
                        best_len = len(marker)

        return best_type, _INTENT_PATTERNS[best_type]['format']

    # ═════════════════════════════════════════════════════════════════════
    # ÉTAPE 3 : NETTOYAGE
    # ═════════════════════════════════════════════════════════════════════

    def _remove_fillers(self, q: str) -> str:
        """Retire les mots de remplissage et normalise."""
        # Remplacer les filler phrases par rien
        for filler in sorted(_FILLER_WORDS, key=len, reverse=True):
            if q.startswith(filler):
                q = q[len(filler):].strip()
                break
        # Nettoyer la ponctuation résiduelle
        q = re.sub(r'\s+', ' ', q).strip('?!.,;: ')
        return q

    # ═════════════════════════════════════════════════════════════════════
    # ÉTAPE 4 : SUJET CENTRAL
    # ═════════════════════════════════════════════════════════════════════

    def _extract_subject(self, q: str, intent_type: str, lang: str) -> str:
        """Extrait le sujet central de la question."""
        # Retirer les préfixes d'intention
        prefixes = _INTENT_PATTERNS.get(intent_type, {}).get('markers', [])
        for pfx in sorted(prefixes, key=len, reverse=True):
            if q.startswith(pfx):
                q = q[len(pfx):].strip()
                break

        # Retirer les articles et mots vides au début
        articles = {'le ', 'la ', 'les ', 'l ', 'un ', 'une ', 'des ',
                    'the ', 'a ', 'an '}
        for art in articles:
            if q.startswith(art):
                q = q[len(art):].strip()

        # Prendre les premiers mots significatifs (max 4)
        words = q.split()
        significant = [w for w in words if w not in _STOPWORDS and len(w) >= 2]
        return ' '.join(significant[:4]) if significant else q[:50]

    # ═════════════════════════════════════════════════════════════════════
    # ÉTAPE 5 : ENTITÉS
    # ═════════════════════════════════════════════════════════════════════

    def _extract_entities(self, q: str, lang: str) -> List[str]:
        """
        Extrait les entités (concepts clés) de la question.

        Stratégie :
          - Mots longs (> 5 caractères) → probablement des entités
          - Mots avec majuscule → noms propres
          - N-grammes non-stopwords → concepts composés
        """
        tokens = [w.strip('?!.,;:()[]{}«»"') for w in q.split()
                  if w not in _STOPWORDS and len(w) >= 2]

        entities = []

        # 1. Mots longs (probablement spécifiques)
        for t in tokens:
            if len(t) >= 6:
                entities.append(t)

        # 2. Bigrammes significatifs (deux mots non-stopwords consécutifs)
        for i in range(len(tokens) - 1):
            if len(tokens[i]) >= 3 and len(tokens[i+1]) >= 3:
                bigram = f"{tokens[i]} {tokens[i+1]}"
                # Filtrer les combos verbe + article
                if not any(v in bigram for v in ('est ', 'sont ', 'a ', 'ont ')):
                    entities.append(bigram)

        # 3. Mots qui ressemblent à des noms propres (pas dans le dico commun)
        common_words = {
            'type', 'truc', 'machin', 'chose', 'gens', 'personne', 'homme', 'femme',
            'trucs', 'machins', 'choses', 'personnes', 'hommes', 'femmes',
            'celui', 'celle', 'ceux', 'celles', 'cela', 'ça',
        }
        for t in tokens:
            if t not in common_words and len(t) >= 3:
                if t not in entities:
                    entities.append(t)

        return entities

    # ═════════════════════════════════════════════════════════════════════
    # ÉTAPE 6 : EXPANSION
    # ═════════════════════════════════════════════════════════════════════

    def _expand_entities(self, entities: List[str]) -> List[str]:
        """
        Expansion sémantique des entités via le plongement spectral.

        Condition : qualité spectrale > 0.7 (sinon, pas d'expansion).
        """
        expanded = list(entities)
        try:
            from spectral_embedding import _SPECTRAL
            if _SPECTRAL and _SPECTRAL.is_ready and len(_SPECTRAL.phases) > 100:
                # Vérifier rapidement la qualité (2-3 paires test)
                test_pairs = [('lumiere', 'onde'), ('capitale', 'ville')]
                test_sims = [_SPECTRAL.get_similarity(a, b) for a, b in test_pairs]
                avg_sim = sum(s for s in test_sims if s is not None) / max(len([s for s in test_sims if s is not None]), 1)
                # Si similarité < 0.3 → bruit → pas d'expansion
                if avg_sim < 0.3:
                    return expanded

                for entity in entities:
                    phase = _SPECTRAL.get_phase(entity)
                    if phase is not None:
                        neighbors = []
                        for w, w_phase in _SPECTRAL.phases.items():
                            if w == entity or w in expanded or len(w) < 3:
                                continue
                            d = abs(phase - w_phase) % TAU
                            d = min(d, TAU - d)
                            if d < math.pi / 8:
                                neighbors.append((w, d))
                        neighbors.sort(key=lambda x: x[1])
                        for n, _ in neighbors[:3]:
                            if n not in expanded:
                                expanded.append(n)
        except ImportError:
            pass

        return expanded

    # ═════════════════════════════════════════════════════════════════════
    # ÉTAPE 7 : PONDÉRATION
    # ═════════════════════════════════════════════════════════════════════

    def _weight_tokens(self, q: str, entities: List[str],
                       intent_type: str, lang: str) -> Dict[str, float]:
        """
        Pondère chaque token selon sa pertinence.

        Poids :
          5.0 → entité nommée (Joconde, Einstein)
          4.0 → verbe d'action spécifique (peint, découvert)
          3.0 → mot long > 6 caractères
          2.0 → mot moyen > 4 caractères
          1.0 → mot court ≥ 2 caractères
          0.0 → stopword / filler
        """
        tokens = [w.strip('?!.,;:()[]{}«»"') for w in q.split()
                  if len(w) >= 2]

        # Verbes d'action forts
        action_verbs = {
            'peint', 'decouvert', 'invente', 'ecrit', 'compose', 'fonde',
            'painted', 'discovered', 'invented', 'wrote', 'composed', 'founded',
            'cree', 'realise', 'concu', 'developpe', 'explique', 'demontre',
            'created', 'developed', 'explained', 'demonstrated',
        }

        # Entités connues (noms propres célèbres)
        known_entities = {
            'joconde', 'mona lisa', 'einstein', 'newton', 'mozart', 'beethoven',
            'napoleon', 'shakespeare', 'picasso', 'darwin', 'curie', 'tesla',
            'paris', 'londres', 'tokyo', 'new york', 'france', 'japon',
        }

        weights = {}
        for t in tokens:
            t_clean = t.lower()

            if t_clean in _STOPWORDS:
                weights[t] = 0.0
            elif t_clean in known_entities:
                weights[t] = 5.0
            elif t_clean in action_verbs:
                weights[t] = 4.0
            elif any(t_clean in e or e in t_clean for e in entities) and len(t) >= 5:
                weights[t] = 3.0
            elif len(t) >= 6:
                weights[t] = 2.5
            elif len(t) >= 4:
                weights[t] = 2.0
            else:
                weights[t] = 1.0

        return weights


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    parser = PromptParser()

    tests = [
        "c'est qui le type qui a peint la joconde",
        "pourquoi le ciel est bleu",
        "quelle est la capitale du japon",
        "explique la relativite",
        "compare mozart et beethoven",
        "who painted the mona lisa",
        "what is the golden ratio",
        "comment fonctionne le coeur humain",
    ]

    for q in tests:
        p = parser.parse(q)
        print(f"Q: {q}")
        print(f"   type={p.type} | lang={p.lang} | sujet={p.subject!r}")
        print(f"   entités={p.entities}")
        print(f"   expand={p.expanded_entities}")
        print(f"   tokens pondérés={dict(sorted(p.weighted_tokens.items(), key=lambda x: -x[1])[:5])}")
        print(f"   format={p.expected_format}")
        print()
