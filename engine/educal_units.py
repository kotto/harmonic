"""
🎓 EDUCAL KA — Unités Éducatives
================================
Catalogue des unités éducatives (leçons + exercices + quiz + évaluation),
jumeau pédagogique des unités médicales de VITAL KA.

Une unité éducative = un JSON dans data/educal_units/ :
  - métadonnées (discipline, niveau, objectifs, prérequis)
  - leçon structurée (sections markdown)
  - exercices (énoncé + réponse + difficulté)
  - quiz (QCM avec index correct)
  - évaluation (seuil de réussite, benchmark)
  - faits (triplets sujet|relation|objet|secteur) → fusionnés dans l'hologramme
    de la discipline : la leçon s'ancre dans la mémoire harmonique et devient
    interrogable en langage naturel (rappel H ⊗ ψ_query).

Transfert : identique au protocole médical — /api/store/download/<holo_id>
puis /api/store/load. L'unité est la couche pédagogique du hologramme.
"""

import json
import time
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

_ENGINE_DIR = Path(__file__).resolve().parent
UNITS_DIR = _ENGINE_DIR / 'data' / 'educal_units'
PROGRESS_DIR = _ENGINE_DIR / 'data' / 'educal_progress'

# Hologramme de discipline associé à chaque unité (pour fusion des faits)
DISCIPLINE_HOLOGRAMS = {
    'mathématiques': 'edu_mathematiques',
    'maths': 'edu_mathematiques',
    'langues': 'edu_langues',
    'français': 'edu_langues',
    'anglais': 'edu_langues',
    'sciences': 'edu_sciences',
    'histoire': 'edu_histoire_geo',
    'géographie': 'edu_histoire_geo',
    'philosophie': 'edu_philosophie',
    'culture civique': 'edu_culture_civique',
    'méthodologie': 'edu_competences',
    'pédagogie': 'edu_competences',
}


# ════════════════════════════════════════════════════════════════
# CATALOGUE
# ════════════════════════════════════════════════════════════════

def _unit_files() -> List[Path]:
    if not UNITS_DIR.exists():
        return []
    return sorted(p for p in UNITS_DIR.glob('*.json')
                  if p.name not in ('catalog.json', 'catalog_export.json'))


def list_units(discipline: str = None, niveau: str = None) -> List[Dict]:
    """Liste les unités (métadonnées seules, pour l'UI)."""
    units = []
    for p in _unit_files():
        try:
            with open(p, encoding='utf-8') as f:
                u = json.load(f)
        except Exception:
            continue
        if discipline and u.get('discipline', '').lower() != discipline.lower():
            continue
        if niveau and u.get('niveau', '').lower() != niveau.lower():
            continue
        units.append({
            'id': u.get('id'),
            'discipline': u.get('discipline'),
            'niveau': u.get('niveau'),
            'programme': u.get('programme', ''),
            'titre': u.get('titre'),
            'objectifs': u.get('objectifs', []),
            'prerequis': u.get('prerequis', []),
            'duree_estimee_min': u.get('duree_estimee_min', 30),
            'nb_exercices': len(u.get('exercices', [])),
            'nb_quiz': len(u.get('quiz', [])),
            'nb_faits': len(u.get('facts', [])),
            'hologramme': u.get('hologramme_associe'),
            'auteur': u.get('auteur', 'EDUCAL KA'),
            'version': u.get('version', 1),
        })
    return units


def get_unit(unit_id: str) -> Optional[Dict]:
    """Charge une unité complète (leçon + exercices + quiz + faits)."""
    unit_id = unit_id.strip().replace('/', '').replace('\\', '')
    path = UNITS_DIR / f'{unit_id}.json'
    if not path.exists():
        return None
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def unit_catalog() -> Dict:
    """Catalogue structuré : disciplines → niveaux → unités."""
    cat: Dict[str, Any] = {}
    for u in list_units():
        disc = u['discipline']
        niveau = u['niveau']
        cat.setdefault(disc, {}).setdefault(niveau, []).append(u['id'])
    return cat


# ════════════════════════════════════════════════════════════════
# FAITS → HOLOGRAMME (ancrage harmonique de la leçon)
# ════════════════════════════════════════════════════════════════

def facts_from_unit(unit: Dict) -> List[Tuple[str, str, str, str]]:
    """Faits d'une unité : triplets (sujet, relation, objet, secteur)."""
    facts = []
    for f in unit.get('facts', []):
        if isinstance(f, (list, tuple)) and len(f) >= 3:
            facts.append((str(f[0]), str(f[1]), str(f[2]),
                          str(f[3]) if len(f) > 3 else 'EDUCATION'))
        elif isinstance(f, dict):
            facts.append((str(f.get('sujet', '')), str(f.get('relation', '')),
                          str(f.get('objet', '')), str(f.get('secteur', 'EDUCATION'))))
    return facts


def all_unit_facts() -> List[Tuple[str, str, str, str]]:
    """Tous les faits de toutes les unités (pour la construction des hologrammes)."""
    facts = []
    for u in list_units():
        unit = get_unit(u['id'])
        if unit:
            facts.extend(facts_from_unit(unit))
    return facts


# ════════════════════════════════════════════════════════════════
# ÉVALUATION (quiz + exercices)
# ════════════════════════════════════════════════════════════════

def _norm_answer(a: Any) -> str:
    return str(a).strip().lower().replace(',', '.')


def _num_match(expected: Any, given: Any) -> bool:
    """Comparaison numérique tolérante (10, 10.0, '10' équivalents)."""
    try:
        return abs(float(str(expected).replace(',', '.')) -
                   float(str(given).replace(',', '.'))) < 1e-6
    except (ValueError, TypeError):
        return False


def evaluate_quiz(unit: Dict, answers: List[Dict]) -> Dict:
    """
    Corrige un quiz. answers = [{question: <index>, answer: <index ou str>}, ...]
    Retourne score, détail par question, feedback et diagnostic des lacunes.
    """
    quiz = unit.get('quiz', [])
    details = []
    correct_count = 0
    lacunes = []  # objectifs non maîtrisés

    for i, q in enumerate(quiz):
        ans = next((a for a in answers if str(a.get('question', a.get('index', -1))) == str(i)
                    or a.get('question', a.get('index', -1)) == i), None)
        if ans is None:
            details.append({'question': i, 'repondu': False, 'correct': False})
            if q.get('objectif'):
                lacunes.append(q['objectif'])
            continue
        given = ans.get('answer')
        ok = False
        if 'correct' in q:
            expected = q['correct']
            if isinstance(expected, (int, float)) and not isinstance(expected, bool):
                ok = _num_match(expected, given)
            else:
                ok = _norm_answer(expected) == _norm_answer(given)
        elif 'choix' in q and isinstance(given, int):
            ok = given == q.get('correct_index', -1)
        if ok:
            correct_count += 1
        else:
            obj = q.get('objectif', f'Question {i + 1}')
            lacunes.append(obj)
        details.append({'question': i, 'repondu': True, 'correct': ok,
                        'objectif': q.get('objectif', '')})

    total = len(quiz)
    score = correct_count / max(total, 1)
    seuil = unit.get('evaluation', {}).get('seuil_reussite', 0.8)
    return {
        'score': round(score, 3),
        'correct': correct_count,
        'total': total,
        'reussite': score >= seuil,
        'seuil_reussite': seuil,
        'details': details,
        'lacunes': list(dict.fromkeys(lacunes)),
        'feedback': (f'✅ Unité maîtrisée ({correct_count}/{total}) — '
                     f'prêt pour l\'unité suivante !'
                     if score >= seuil else
                     f'📖 {correct_count}/{total} — '
                     f'réviser puis retenter : {", ".join(lacunes[:4]) or "le quiz"}'),
    }


def evaluate_exercises(unit: Dict, answers: List[Dict]) -> Dict:
    """
    Corrige les exercices. answers = [{exercice: <index>, reponse: <str|num>}]
    Retourne score + étapes attendues quand disponibles.
    """
    exos = unit.get('exercices', [])
    details = []
    correct_count = 0

    for i, ex in enumerate(exos):
        ans = next((a for a in answers if str(a.get('exercice', a.get('index', -1))) == str(i)
                    or a.get('exercice', a.get('index', -1)) == i), None)
        if ans is None:
            details.append({'exercice': i, 'repondu': False, 'correct': False})
            continue
        given = ans.get('reponse')
        expected = ex.get('reponse')
        ok = _num_match(expected, given) if expected is not None else False
        if not ok and expected is not None:
            ok = _norm_answer(expected) == _norm_answer(given)
        if ok:
            correct_count += 1
        details.append({
            'exercice': i,
            'repondu': True,
            'correct': ok,
            'etapes': ex.get('etapes', []),
            'reponse_attendue': expected,
        })

    total = len(exos)
    return {
        'score': round(correct_count / max(total, 1), 3),
        'correct': correct_count,
        'total': total,
        'details': details,
    }


# ════════════════════════════════════════════════════════════════
# PROGRESSION ÉLÈVE (carnet d'apprentissage)
# ════════════════════════════════════════════════════════════════

def _progress_path(user_id: str) -> Path:
    safe = user_id.strip().replace('/', '_').replace('\\', '_')
    return PROGRESS_DIR / f'{safe}.json'


def load_progress(user_id: str) -> Dict:
    path = _progress_path(user_id)
    if path.exists():
        try:
            with open(path, encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {'user_id': user_id, 'unites_validees': {}, 'sessions': [], 'skills': {}}


def save_progress(user_id: str, unit_id: str, payload: Dict) -> Dict:
    """Enregistre une session de quiz/exercice + met à jour les compétences."""
    prog = load_progress(user_id)
    unit = get_unit(unit_id)
    session = {
        'unit_id': unit_id,
        'ts': time.time(),
        'date': time.strftime('%Y-%m-%d %H:%M'),
        'quiz_score': payload.get('quiz_score'),
        'exercices_score': payload.get('exercices_score'),
        'lacunes': payload.get('lacunes', []),
    }
    prog['last_unit'] = unit_id
    prog['sessions'].append(session)
    if payload.get('reussite'):
        prog['unites_validees'][unit_id] = time.strftime('%Y-%m-%d')
    # Compétences : chaque objectif validé du quiz devient un skill
    if unit and payload.get('quiz_details'):
        for d in payload['quiz_details']:
            if d.get('correct') and d.get('objectif'):
                prog['skills'][d['objectif']] = max(
                    prog['skills'].get(d['objectif'], 0.0), 1.0)
    # Décroissance de révision : les lacunes abaissent les skills associés
    for lacune in payload.get('lacunes', []):
        prog['skills'][lacune] = 0.0

    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    with open(_progress_path(user_id), 'w', encoding='utf-8') as f:
        json.dump(prog, f, ensure_ascii=False, indent=2)
    return prog


def next_units(user_id: str, unit_id: str) -> List[str]:
    """Unités suivantes suggérées : les unités qui déclarent l'unité courante
    comme prérequis, puis le reste de la discipline."""
    prog = load_progress(user_id)
    current = get_unit(unit_id)
    if not current:
        return []
    suggestions = []
    for u in list_units(discipline=current.get('discipline')):
        if u['id'] == unit_id:
            continue
        if current.get('id') in u.get('prerequis', []):
            suggestions.append(u['id'])
    # Le reste de la discipline, unités non validées d'abord
    rest = [u['id'] for u in list_units(discipline=current.get('discipline'))
            if u['id'] != unit_id and u['id'] not in suggestions]
    rest.sort(key=lambda uid: prog['unites_validees'].get(uid, '0000'))
    return suggestions + rest[:5]


# ════════════════════════════════════════════════════════════════
# DIAGNOSTIC PÉDAGOGIQUE (résonance sur l'hologramme de discipline)
# ════════════════════════════════════════════════════════════════

def diagnose_lacunes(unit: Dict, quiz_result: Dict, holo_store=None) -> Dict:
    """
    Diagnostic pédagogique : pour chaque objectif non maîtrisé, interroge
    l'hologramme de la discipline (H ⊗ ψ_question) et liste les faits à revoir.
    Équivalent pédagogique du diagnostic médical de VITAL KA.
    """
    holo_id = unit.get('hologramme_associe') or 'official_education'
    lacunes = quiz_result.get('lacunes', [])
    if not lacunes:
        return {'holo_id': holo_id, 'lacunes': [], 'faits_a_revoir': [],
                'message': 'Aucune lacune détectée — maîtrise confirmée'}

    faits_a_revoir = []
    if holo_store is not None:
        try:
            for obj in lacunes[:5]:
                results = holo_store.recall(holo_id, obj, top_k=3)
                for s, r, o, sec, score in results:
                    faits_a_revoir.append({
                        'objectif': obj,
                        'fait': f'{s} {r} {o}',
                        'secteur': sec,
                        'score': round(float(score), 3),
                    })
        except Exception:
            pass

    return {
        'holo_id': holo_id,
        'lacunes': lacunes,
        'faits_a_revoir': faits_a_revoir[:9],
        'message': f'{len(lacunes)} objectif(s) à renforcer — '
                   f'{len(faits_a_revoir)} fait(s) à réviser par résonance',
    }


if __name__ == '__main__':
    print(f"📚 EDUCAL KA — {len(list_units())} unités dans {UNITS_DIR}")
    for u in list_units():
        print(f"  • {u['id']:<42s} {u['discipline']:<14s} {u['niveau']:<18s} "
              f"{u['nb_exercices']} exo / {u['nb_quiz']} quiz / {u['nb_faits']} faits")
