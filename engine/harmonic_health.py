"""
Harmonic Health — Diagnostic harmonique (module recréé)
==========================================================
Fournit :
  - full_diagnostic(symptomes, vitaux, age, sexe) : diagnostic complet
  - therapeutic_frequencies(condition) : fréquences thérapeutiques
  - vital_harmonic_score(vitaux) : score harmonique des constantes vitales
"""

import math, time
from typing import Dict, List, Optional, Tuple

PHI = 1.618033988749895
TAU = 2.0 * math.pi


# Constantes harmoniques de référence (fréquences en Hz)
CONSTANTS = {
    'phi': 1.618033988749895,
    'pi': 3.141592653589793,
    'e': 2.718281828459045,
    'sqrt2': 1.4142135623730951,
    'sqrt3': 1.7320508075688772,
    'sqrt5': 2.23606797749979,
}


def _normalize_vitaux(vitaux: Optional[Dict]) -> Dict:
    """Normalise les constantes vitales avec valeurs par défaut."""
    if not vitaux:
        vitaux = {}
    return {
        'hr': float(vitaux.get('hr', 0) or 0),          # fréquence cardiaque (bpm)
        'temp': float(vitaux.get('temp', 0) or 0),      # température (°C)
        'systolic': float(vitaux.get('systolic', 0) or vitaux.get('bp_sys', 0) or 0),
        'diastolic': float(vitaux.get('diastolic', 0) or vitaux.get('bp_dia', 0) or 0),
        'spo2': float(vitaux.get('spo2', 0) or vitaux.get('saturation', 0) or 0),
        'rr': float(vitaux.get('rr', 0) or 0),          # fréquence respiratoire
    }


def _coherence_score(values: List[float]) -> float:
    """Score de cohérence harmonique d'un ensemble de valeurs (0-100)."""
    if not values:
        return 50.0
    # Ratio moyen par rapport aux constantes harmoniques
    ratios = []
    for v in values:
        if v <= 0:
            continue
        # Proximité à n * constante harmonique
        best = min(abs(v / c - round(v / c)) for c in CONSTANTS.values())
        ratios.append(1 - min(1.0, best))
    return round(50 + 50 * (sum(ratios) / len(ratios) if ratios else 0.5), 1)


def full_diagnostic(symptomes: List[str] = None, vitaux: Dict = None,
                    age: Optional[int] = None, sexe: Optional[str] = None) -> Dict:
    """
    Diagnostic complet par résonance harmonique.
    
    Returns:
        {score, niveau, alignements, observations, recommandations,
         cohérence_vitale, domaine_estimé}
    """
    t0 = time.time()
    symptomes = [str(s).lower() for s in (symptomes or [])]
    v = _normalize_vitaux(vitaux)
    
    # ═══ ANALYSE DES SYMPTÔMES ═══
    # Catégories de symptômes → domaines harmoniques
    domain_map = [
        (['fièvre', 'fievre', 'température', 'temperature', 'sueur', 'frisson'], 'infectieux', 42.0),
        (['toux', 'respiration', 'essoufflement', 'poitrine', 'expectoration'], 'respiratoire', 47.0),
        (['fatigue', 'faiblesse', 'épuisement', 'epuisement', 'asthénie', 'asthenie'], 'energetique', 40.0),
        (['douleur', 'mal de tête', 'migraine', 'céphalée', 'cephalee', 'crampe'], 'douleur', 45.0),
        (['nausée', 'nausee', 'vomissement', 'diarrhée', 'diarrhee', 'estomac', 'abdomen'], 'digestif', 44.0),
        (['vertige', 'étourdissement', 'etourdissement', 'tête qui tourne', 'tete qui tourne'], 'vestibulaire', 43.0),
        (['insomnie', 'sommeil', 'anxiété', 'anxiete', 'stress', 'angoisse'], 'nerveux', 41.0),
        (['éruption', 'eruption', 'démangeaison', 'demangeaison', 'peau', 'rougeur'], 'cutané', 46.0),
    ]
    
    domain_scores = {}
    matched = []
    for s in symptomes:
        found = False
        for keywords, domain, base_freq in domain_map:
            if any(k in s for k in keywords):
                domain_scores[domain] = domain_scores.get(domain, 0) + 1
                matched.append(domain)
                found = True
                break
        if not found:
            domain_scores['general'] = domain_scores.get('general', 0) + 1
            matched.append('general')
    
    # ═══ ANALYSE DES CONSTANTES VITALES ═══
    vitals_check = []
    if v['hr'] > 0:
        if 60 <= v['hr'] <= 100:
            vitals_check.append(('hr', 'normal'))
        elif v['hr'] > 100:
            vitals_check.append(('hr', 'tachycardie'))
        else:
            vitals_check.append(('hr', 'bradycardie'))
    if v['temp'] > 0:
        if 36.1 <= v['temp'] <= 37.8:
            vitals_check.append(('temp', 'normal'))
        elif v['temp'] > 38:
            vitals_check.append(('temp', 'fièvre'))
        else:
            vitals_check.append(('temp', 'hypothermie'))
    if v['spo2'] > 0:
        if v['spo2'] >= 95:
            vitals_check.append(('spo2', 'normal'))
        elif v['spo2'] >= 90:
            vitals_check.append(('spo2', 'hypoxémie légère'))
        else:
            vitals_check.append(('spo2', 'hypoxémie sévère'))
    
    # ═══ SCORE HARMONIQUE GLOBAL ═══
    anomaly_count = sum(1 for _, status in vitals_check if status != 'normal')
    severity = min(1.0, (len(matched) * 0.15) + (anomaly_count * 0.2))
    score = round(100 * (1 - severity), 1)
    
    # Cohérence harmonique des vitaux
    vital_values = [v['hr'], v['temp'], v['spo2']]
    coherence = _coherence_score([x for x in vital_values if x > 0])
    
    # ═══ NIVEAU ═══
    if score >= 85:
        niveau = 'stable'
    elif score >= 65:
        niveau = 'surveillance'
    elif score >= 40:
        niveau = 'intervention'
    else:
        niveau = 'urgence'
    
    # ═══ RECOMMANDATIONS ═══
    recs = []
    if any(k in s for s in symptomes for k in ['fièvre', 'fievre', 'température', 'temperature']):
        recs.append('Surveiller la température toutes les 4h. Hydratation régulière.')
    if v['temp'] > 39:
        recs.append('Fièvre élevée : consultation médicale recommandée.')
    if v['spo2'] > 0 and v['spo2'] < 95:
        recs.append(f'Saturation à {v["spo2"]}% : surveillance rapprochée, consultation si < 90%.')
    if v['hr'] > 110:
        recs.append('Tachycardie : repos et réévaluation.')
    if not recs:
        recs.append('Aucune anomalie majeure détectée. Repos et hydratation.')
    
    # ═══ RÉSULTAT ═══
    return {
        'score': score,
        'niveau': niveau,
        'domain_scores': domain_scores,
        'domaines': sorted(domain_scores, key=domain_scores.get, reverse=True),
        'vitals_check': vitals_check,
        'coherence_vitale': coherence,
        'observations': [
            f'{len(symptomes)} symptôme(s) analysé(s)',
            f'{len(domain_scores)} domaine(s) concerné(s)',
            f'Constantes vitales : {len(vitals_check)} vérifiée(s)',
        ],
        'recommandations': recs,
        'latency_ms': round((time.time() - t0) * 1000, 1),
    }


def therapeutic_frequencies(condition: str = '') -> List[Dict]:
    """
    Fréquences thérapeutiques harmoniques (Hz) pour une condition.
    
    Basé sur les fréquences de résonance classiques (Rife-like) mappées
    aux constantes harmoniques.
    """
    c = condition.lower()
    if 'infection' in c or 'fièvre' in c or 'fievre' in c:
        freq = [396, 417, 528]
    elif 'douleur' in c:
        freq = [174, 285, 396]
    elif 'stress' in c or 'anxiété' in c or 'anxiete' in c:
        freq = [417, 528, 639]
    elif 'respir' in c or 'poumon' in c:
        freq = [285, 396, 417]
    elif 'digest' in c or 'estomac' in c:
        freq = [417, 528, 639]
    else:
        freq = [396, 528, 639]
    
    return [
        {'frequency': f, 'duration_s': 60, 'label': f'{f} Hz — harmonique φ'}
        for f in freq
    ]


def vital_harmonic_score(vitaux: Dict = None) -> Dict:
    """
    Score harmonique des constantes vitales seules.
    
    Returns:
        {score, coherence, detail, niveau}
    """
    v = _normalize_vitaux(vitaux)
    values = [v['hr'], v['temp'], v['spo2']]
    
    score = 100.0
    detail = []
    
    if v['hr'] > 0:
        if 60 <= v['hr'] <= 100:
            detail.append(('hr', v['hr'], 'OK'))
        else:
            score -= 15
            detail.append(('hr', v['hr'], 'anomalie'))
    if v['temp'] > 0:
        if 36.1 <= v['temp'] <= 37.8:
            detail.append(('temp', v['temp'], 'OK'))
        else:
            score -= 15
            detail.append(('temp', v['temp'], 'anomalie'))
    if v['spo2'] > 0:
        if v['spo2'] >= 95:
            detail.append(('spo2', v['spo2'], 'OK'))
        else:
            score -= 20
            detail.append(('spo2', v['spo2'], 'anomalie'))
    
    score = round(max(0, min(100, score)), 1)
    coherence = _coherence_score([x for x in values if x > 0])
    niveau = 'stable' if score >= 85 else 'surveillance' if score >= 65 else 'intervention'
    
    return {'score': score, 'coherence': coherence, 'detail': detail, 'niveau': niveau}


if __name__ == '__main__':
    print("Test harmonic_health:")
    d = full_diagnostic(['fièvre', 'toux', 'fatigue'], {'hr': 98, 'temp': 38.5, 'spo2': 96}, age=30)
    print(f"  Diagnostic: score={d['score']}, niveau={d['niveau']}, domaines={d['domaines']}")
    print(f"  Cohérence vitale: {d['coherence_vitale']}")
    print(f"  Recommandations: {d['recommandations'][:2]}")
    v = vital_harmonic_score({'hr': 75, 'temp': 37.0, 'spo2': 98})
    print(f"  Score vital: {v['score']} ({v['niveau']})")
    print("\n✅ harmonic_health.py recréé")
