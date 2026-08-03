#!/usr/bin/env python3
"""
facet_coverage.py — Complétude par facettes (benchmark sans oracle)
====================================================================

La complétude d'un hologramme n'est pas le nombre de faits : c'est la
COUVERTURE DES FACETTES du sujet. « diabete » couvre définition + causes
mais rien sur les symptômes ou le traitement ? L'hologramme n'est pas
complet, même avec 100 faits.

Pour chaque TYPE de sujet (maladie, concept scientifique, personne,
lieu, objet technique, général), un SQUELETTE de facettes canoniques.
Le benchmark de couverture pose la question-type de chaque facette au
rappel M4 : la facette est couverte si un fait pertinent répond —
pertinent = contient le sujet ET un mot-clé de la facette (proxy sans
oracle, même choix que GSM8K M4 : on mesure ce qui est mesurable).

Usages :
  - build() : score de couverture écrit dans le registre (coverage)
  - boucle de complétion : les facettes manquantes pilotent les
    variantes de l'ingestion massive (« traitement de X », « symptomes
    de X »...) jusqu'au seuil
  - mobile : « 80% des aspects couverts — à enrichir : symptomes,
    traitement »
"""

import re
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════════
# SQUELETTES DE FACETTES PAR TYPE DE SUJET
# (facette, [questions-type], [mots-clés attendus dans le fait])
# Les questions utilisent {s} = sujet. La définition n'a pas de mot-clé :
# le fait doit simplement contenir le sujet.
# ═══════════════════════════════════════════════════════════════════════════════

FACET_SKELETONS: Dict[str, List[Tuple[str, List[str], List[str]]]] = {
    'maladie': [
        ('definition', ['Qu est-ce que {s} ?'], []),
        ('types', ['Quels sont les types de {s} ?'],
         ['type', 'forme', 'stade', 'classe', 'variante', 'sorte']),
        ('causes', ['Quelle est la cause de {s} ?', 'Qu est-ce qui cause {s} ?'],
         ['cause', 'causé', 'causee', 'provoque', 'origine', 'facteur',
          'deficience', 'resistance', 'infection']),
        ('symptomes', ['Quels sont les symptomes de {s} ?'],
         ['symptome', 'signe', 'manifeste', 'douleur', 'fievre', 'exces',
          'fatigue', 'soif', 'glucose']),
        ('mecanisme', ['Quel est le mecanisme de {s} ?'],
         ['mecanisme', 'processus', 'cellule', 'gene', 'fonctionne',
          'metabolisme', 'insuline']),
        ('diagnostic', ['Comment diagnostique-t-on {s} ?'],
         ['diagnostique', 'detecte', 'test', 'depistage', 'examen',
          'mise en evidence', 'analyse']),
        ('traitement', ['Comment traite-t-on {s} ?', 'Quel est le traitement de {s} ?'],
         ['traitement', 'traite', 'therapie', 'medicament', 'insuline',
          'metformine', 'soin', 'chirurgie']),
        ('prevention', ['Comment prevenir {s} ?'],
         ['preven', 'evite', 'protege', 'vaccin', 'hygiene', 'regime',
          'activite physique']),
        ('epidemiologie', ['Quelle est la frequence de {s} ?'],
         ['millions', 'population', 'cas', 'prevalence', 'deces',
          'personnes', 'monde', 'france', 'mortalite']),
        ('histoire', ['Quelle est l histoire de {s} ?'],
         ['decouvert', 'invente', 'historique', 'annees', 'epoque',
          'pasteur', 'palus', 'provenance', 'decouverte']),
    ],
    'science': [
        ('definition', ['Qu est-ce que {s} ?'], []),
        ('mecanisme', ['Quel est le mecanisme de {s} ?'],
         ['mecanisme', 'processus', 'fonctionne', 'interaction', 'onde',
          'energie', 'matiere']),
        ('proprietes', ['Quelles sont les proprietes de {s} ?'],
         ['propriete', 'vitesse', 'masse', 'temperature', 'longueur',
          'capacite', 'caracteristique']),
        ('applications', ['Quelles sont les applications de {s} ?'],
         ['application', 'utilise', 'technologie', 'industrie', 'outil',
          'dispositif']),
        ('histoire', ['Quelle est l histoire de {s} ?'],
         ['decouvert', 'invente', 'historique', 'annees', 'epoque',
          'decouverte']),
        ('limites', ['Quelles sont les limites de {s} ?'],
         ['limite', 'contrainte', 'inconvenient', 'probleme', 'defi',
          'difficulte']),
    ],
    'personne': [
        ('biographie', ['Qui est {s} ?'], []),
        ('oeuvre', ['Quelles sont les oeuvres de {s} ?', 'Qu a fait {s} ?'],
         ['ecrit', 'invente', 'decouvert', 'cree', 'oeuvre', 'livre',
          'theorie', 'decouverte']),
        ('contexte', ['Quel est le contexte de {s} ?'],
         ['ne en', 'epoque', 'siecle', 'france', 'universite', 'annees']),
        ('posterite', ['Quelle est l influence de {s} ?'],
         ['influence', 'heritage', 'posterite', 'prix', 'nobel',
          'reconnu', 'impact']),
    ],
    'lieu': [
        ('geographie', ['Ou se trouve {s} ?'], []),
        ('histoire', ['Quelle est l histoire de {s} ?'],
         ['histoire', 'fonde', 'epoque', 'siecle', 'annees', 'ancien']),
        ('population', ['Quelle est la population de {s} ?'],
         ['habitants', 'population', 'millions', 'personnes', 'densite']),
        ('economie', ['Quelle est l economie de {s} ?'],
         ['economie', 'industrie', 'port', 'commerce', 'tourisme',
          'agriculture', 'pib']),
    ],
    'technique': [
        ('principe', ['Quel est le principe de {s} ?'], []),
        ('fonctionnement', ['Comment fonctionne {s} ?'],
         ['fonctionne', 'mecanisme', 'processus', 'etape', 'composant']),
        ('applications', ['Quelles sont les applications de {s} ?'],
         ['application', 'utilise', 'usage', 'domaine', 'industrie']),
        ('limites', ['Quelles sont les limites de {s} ?'],
         ['limite', 'inconvenient', 'probleme', 'cout', 'contrainte']),
    ],
    'general': [
        ('definition', ['Qu est-ce que {s} ?'], []),
        ('types', ['Quels sont les types de {s} ?'],
         ['type', 'forme', 'categorie', 'variante', 'classe']),
        ('mecanisme', ['Comment fonctionne {s} ?'],
         ['fonctionne', 'mecanisme', 'processus', 'etape']),
        ('histoire', ['Quelle est l histoire de {s} ?'],
         ['histoire', 'decouvert', 'epoque', 'annees', 'origine']),
        ('applications', ['Quelles sont les applications de {s} ?'],
         ['application', 'utilise', 'domaine', 'usage']),
    ],
}

# Seuil de complétude : en dessous, la boucle de complétion se déclenche
COVERAGE_THRESHOLD = 0.7

# Mots-clés pour détecter le TYPE de sujet (défaut : général)
_TYPE_HINTS = {
    'maladie': ['maladie', 'diabete', 'cancer', 'paludisme', 'grippe',
                'infection', 'hypertension', 'anemie', 'vaccin', 'sante',
                'symptome', 'traitement', 'medecine', 'antibiotique'],
    'science': ['physique', 'lumiere', 'energie', 'etoile', 'planete',
                'gravite', 'matiere', 'chimie', 'onde', 'quantique',
                'astronomie', 'mathematique', 'atome', 'cellule'],
    'personne': ['pasteur', 'einstein', 'newton', 'curie', 'napoleon',
                 'hugo', 'moliere', 'artist', 'peintre', 'ecrivain'],
    'lieu': ['france', 'paris', 'afrique', 'europe', 'fleuve', 'montagne',
             'ville', 'pays', 'capitale', 'ocean'],
    'technique': ['ordinateur', 'moteur', 'machine', 'technologie',
                  'robot', 'gps', 'avion', 'voiture', 'smartphone'],
}


def _words(text: str) -> List[str]:
    return re.findall(r"[a-zàâäéèêëîïôöùûüç]{3,}", text.lower())


def detect_subject_type(sujet: str) -> str:
    """Type de sujet par indice lexical (défaut : general)."""
    for t, hints in _TYPE_HINTS.items():
        if any(h in sujet.lower() for h in hints):
            return t
    return 'general'


def skeleton_for(meta=None, sujet: str = '') -> List[Tuple]:
    """
    Squelette de facettes : par le style de l'hologramme (medecine →
    maladie, sciences → science, histoire → personne, sport/art →
    general) sinon par le type du sujet.
    """
    style = getattr(meta, 'style', 'auto') if meta is not None else 'auto'
    mapping = {
        'medecine': 'maladie', 'sciences': 'science', 'histoire': 'personne',
    }
    skel = mapping.get(style)
    if skel is None:
        skel = detect_subject_type(sujet)
    return FACET_SKELETONS.get(skel, FACET_SKELETONS['general'])


def _subject_words(sujet: str) -> List[str]:
    """Mots significatifs du sujet (pour l'ancrage dans le fait)."""
    _stop = {'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'est',
             'que', 'qui', 'quoi', 'se', 'ce', 'cette', 'ces', 'de', 'd'}
    return [w for w in _words(sujet) if w not in _stop]


def coverage_score(store, holo_id: str, sujet: str,
                   skeleton: Optional[List[Tuple]] = None) -> Dict:
    """
    Score de complétude : chaque facette du squelette pose sa question au
    rappel M4 ; la facette est couverte si un fait rappelé contient le
    sujet ET un mot-clé de la facette (la définition n'exige que le sujet).

    Returns:
        {'couverture': float 0-1, 'seuil': 0.7, 'complete': bool,
         'facettes': [{nom, couverte, fait, score}...],
         'manquantes': [noms...]}
    """
    meta = store._registry.get(holo_id)
    skeleton = skeleton or skeleton_for(meta, sujet)
    s_words = _subject_words(sujet)

    facets = []
    covered = 0
    for name, questions, kw in skeleton:
        q = questions[0].format(s=sujet)
        hit = False
        best_fact, best_score = None, 0.0
        try:
            recalled = store.recall(holo_id, q, top_k=3)
        except Exception:
            recalled = []
        for s, r, o, sec, sc in recalled:
            text = f'{s} {r} {o}'.lower()
            has_subject = (not s_words) or any(w in text for w in s_words)
            has_kw = (not kw) or any(k in text for k in kw)
            if has_subject and has_kw:
                hit = True
                if sc > best_score:
                    best_score, best_fact = sc, f'{s} {r} {o}'
                break
        if hit:
            covered += 1
        facets.append({'facette': name, 'couverte': hit,
                       'fait': best_fact, 'score': round(best_score, 3)})

    ratio = covered / max(1, len(facets))
    manquantes = [f['facette'] for f in facets if not f['couverte']]
    return {
        'couverture': round(ratio, 3),
        'seuil': COVERAGE_THRESHOLD,
        'complete': ratio >= COVERAGE_THRESHOLD,
        'facettes': facets,
        'manquantes': manquantes,
    }


# Mots-clés de QUESTION → facette (pour la file de complétion : une
# question sans réponse « quels sont les symptomes de X ? » marque la
# facette « symptomes » à enrichir)
_QUESTION_FACET_KEYWORDS = {
    'symptomes': ['symptome', 'symptomes', 'signes', 'se manifeste',
                  'douleur', 'fievre', 'comment se manifeste'],
    'traitement': ['traitement', 'traite', 'traite-t-on', 'soigne',
                   'soigner', 'therapie', 'medicament', 'guerir'],
    'causes': ['cause', 'causes', 'provoque', 'pourquoi', 'origine',
               'facteurs', 'a l origine'],
    'diagnostic': ['diagnostique', 'diagnostic', 'detecte', 'detecter',
                   'test', 'depistage', 'examen', 'comment savoir si'],
    'prevention': ['prevenir', 'prevention', 'eviter', 'evite', 'protege',
                   'vaccin', 'protection'],
    'histoire': ['histoire', 'decouvert', 'invente', 'inventeur',
                 'origine du nom', 'provenance', 'epoque'],
    'types': ['types', 'type de', 'formes', 'variantes', 'categories',
              'quelle difference entre'],
    'mecanisme': ['mecanisme', 'comment fonctionne', 'processus',
                  'comment ca marche'],
    'epidemiologie': ['frequence', 'combien de personnes', 'nombre de cas',
                      'prevalence', 'repandu', 'statistiques'],
}


def detect_facet(question: str) -> str:
    """Facette la plus probable d'une question (défaut : definition).
    Tie-break : le mot-clé le plus long est le plus discriminant
    (« decouvert » bat « vaccin » pour « Qui a decouvert le vaccin ? »)."""
    q = question.lower()
    best, best_count, best_len = 'definition', 0, 0
    for facet, kws in _QUESTION_FACET_KEYWORDS.items():
        matched = [k for k in kws if k in q]
        n = len(matched)
        max_len = max((len(k) for k in matched), default=0)
        if n > best_count or (n == best_count and max_len > best_len):
            best, best_count, best_len = facet, n, max_len
    return best


def coverage_texts(texts: List[str], sujet: str,
                   skeleton: Optional[List[Tuple]] = None) -> Dict:
    """
    Score de complétude pour des TEXTES PLATS (départements Enterprise :
    StoredFact.text) — chaque facette pose sa question et la facette est
    couverte si un texte contient le sujet ET un mot-clé de la facette.
    """
    skeleton = skeleton or skeleton_for(None, sujet)
    s_words = _subject_words(sujet)
    facets, covered = [], 0
    for name, questions, kw in skeleton:
        hit = False
        for t in texts:
            low = t.lower()
            has_subject = (not s_words) or any(w in low for w in s_words)
            has_kw = (not kw) or any(k in low for k in kw)
            if has_subject and has_kw:
                hit = True
                break
        if hit:
            covered += 1
        facets.append({'facette': name, 'couverte': hit})
    ratio = covered / max(1, len(facets))
    return {'couverture': round(ratio, 3),
            'seuil': COVERAGE_THRESHOLD,
            'complete': ratio >= COVERAGE_THRESHOLD,
            'facettes': facets,
            'manquantes': [f['facette'] for f in facets if not f['couverte']]}


def coverage_queries(sujet: str, manquantes: List[str],
                     skeleton: Optional[List[Tuple]] = None) -> List[str]:
    """
    Questions des facettes manquantes — pilotent les variantes de la
    boucle de complétion (« Comment traite-t-on X ? » → requête web
    « X traitement »).
    """
    skeleton = skeleton or skeleton_for(None, sujet)
    by_name = {name: questions for name, questions, _ in skeleton}
    queries = []
    for name in manquantes:
        for q in by_name.get(name, []):
            queries.append(q.format(s=sujet))
    return queries


if __name__ == '__main__':
    # Test rapide : couverture d'un hologramme existant
    import sys, logging
    sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
    logging.basicConfig(level=logging.WARNING)
    from hologram_store import HologramStore
    store = HologramStore()
    for holo in ['personal_diabete', 'personal_paludisme']:
        if holo in store._registry:
            meta = store._registry[holo]
            sujet = holo.replace('personal_', '')
            cov = coverage_score(store, holo, sujet)
            print(f'=== {holo} ({meta.style}) — couverture {cov["couverture"]:.0%} '
                  f'{"✓" if cov["complete"] else "à compléter"}')
            for f in cov['facettes']:
                mark = '✓' if f['couverte'] else '✗'
                print(f'   {mark} {f["facette"]:14s} {f["fait"][:60] if f["fait"] else ""}')
