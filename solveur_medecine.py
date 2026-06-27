#!/usr/bin/env python3
"""
SOLVEUR MÉDECINE — Extension harmonique au domaine médical
===========================================================
Module pluggable pour le système harmonique universel.
Chaque domaine fournit : vocabulaire, extracteur, solveur.

Domaines couverts :
  - Diagnostic différentiel (symptômes → hypothèses diagnostiques)
  - Pharmacologie (posologie : dose, poids, fréquence, Clairance créatinine)
  - Physiologie (IMC/BMI, tension artérielle, FC cible, surface corporelle)
  - Scores cliniques (Glasgow, APACHE II, CHA₂DS₂-VASc, Wells)
  - Calculs pratiques (débit perfusion, conversion unités, dilution)

Usage :
  python solveur_medecine.py                       # démo
  python solveur_medecine.py -p "IMC 70 kg 1.75 m"
"""

import re
import math
from typing import Dict, List, Tuple, Optional

# ═══════════════════════════════════════════════════════════════
# VOCABULAIRE MÉDICAL (~180 tokens)
# ═══════════════════════════════════════════════════════════════

VOCAB_MEDICAL = [
    # Signes vitaux
    'temperature', 'tension', 'pouls', 'frequence_cardiaque', 'fc',
    'frequence_respiratoire', 'fr', 'saturation', 'spo2',
    'pression_arterielle', 'systolique', 'diastolique', 'mmhg', 'mm_hg',
    'douleur', 'echelle', 'eva', 'glasgow', 'conscience',
    # Mensurations
    'poids', 'taille', 'imc', 'bmi', 'surface_corporelle', 'sc',
    'kg', 'cm', 'm', 'lb', 'lbs', 'pouces', 'inches', 'feet',
    # Pharmacologie
    'dose', 'posologie', 'mg', 'g', 'μg', 'mcg', 'mg/kg', 'mg/m²',
    'comprime', 'ampoule', 'flacon', 'sirop', 'injection', 'perfusion',
    'debit', 'ml', 'ml/h', 'gouttes', 'gtt', 'dilution', 'volume',
    'clairance', 'creatinine', 'creat', 'cockcroft', 'mdrd', 'ckd-epi',
    'demi_vie', 'biodisponibilite', 'voie', 'orale', 'iv', 'im', 'sc',
    # Pathologies / Symptômes
    'fievre', 'toux', 'dyspnee', 'douleur_thoracique', 'cephalée',
    'nausee', 'vomissement', 'diarrhee', 'constipation', 'oedeme',
    'fatigue', 'vertige', 'palpitations', 'syncope', 'convulsion',
    'diabete', 'hta', 'hypertension', 'hypotension', 'avc',
    'infarctus', 'idm', 'embolie', 'thrombose', 'infection',
    'paludisme', 'covid', 'grippe', 'pneumonie', 'meningite',
    'cancer', 'tumeur', 'metastase', 'insuffisance', 'renale',
    'cardiaque', 'respiratoire', 'hepatique',
    # Scores
    'score', 'echelle', 'glasgow', 'apache', 'sofa', 'qsofa',
    'chads', 'cha2ds2', 'vasc', 'wells', 'has_bled', 'curb65',
    # Biologie
    'sodium', 'potassium', 'creatinine', 'uree', 'glycemie',
    'hb', 'hemoglobine', 'plaquettes', 'leucocytes', 'crp',
    'inr', 'tca', 'ph', 'bicarbonates', 'lactates',
    'mmol', 'μmol', 'g/dl', 'g/l', 'mg/dl', 'ui', 'meq',
    # Mots-clés calculatoires
    'calcule', 'calculer', 'determiner', 'quelle', 'quel', 'dose',
    'imc', 'bmi', 'clairance', 'debit', 'score', 'index',
    # Tokens utilitaires (opérateurs, nombres)
    '0','1','2','3','4','5','6','7','8','9','10',
    '12','15','18','20','25','30','40','50','60','70','75','80',
    '90','100','120','150','180','200','250','500','1000',
    '+','-','*','/','=','^','(',')','.',',',
]

# ═══════════════════════════════════════════════════════════════
# BASE DE CONNAISSANCES MÉDICALES (symptômes → diagnostics)
# ═══════════════════════════════════════════════════════════════

DIAGNOSTICS_DIFFERENTIELS = {
    'fievre': ['infection', 'paludisme', 'covid', 'grippe', 'pneumonie',
               'meningite', 'infection_urinaire', 'abcès'],
    'toux': ['grippe', 'covid', 'pneumonie', 'bronchite', 'asthme',
             'bpco', 'tuberculose'],
    'dyspnee': ['pneumonie', 'embolie_pulmonaire', 'insuffisance_cardiaque',
                'asthme', 'bpco', 'covid'],
    'douleur_thoracique': ['infarctus', 'embolie_pulmonaire', 'pericardite',
                           'pneumothorax', 'angor'],
    'cephalée': ['migraine', 'meningite', 'avc', 'hta', 'sinusite',
                 'tumeur_cerebrale'],
    'oedeme': ['insuffisance_cardiaque', 'insuffisance_renale',
               'insuffisance_hepatique', 'thrombose_veineuse'],
    'palpitations': ['arythmie', 'hyperthyroidie', 'anxiété',
                     'insuffisance_cardiaque'],
    'vertige': ['vertige_positionnel', 'meniere', 'avc_vertebrobasilaire',
                'hypotension_orthostatique'],
    'fatigue': ['anemie', 'hypothyroidie', 'depression', 'insuffisance_renale',
                'cancer', 'diabete'],
}

# ═══════════════════════════════════════════════════════════════
# EXTRACTEUR MÉDICAL
# ═══════════════════════════════════════════════════════════════

def extraire_medecine(texte: str) -> Dict:
    """
    Extrait les paramètres d'un problème médical.

    Types supportés :
    - diagnostic : symptômes → hypothèses
    - physiologie : IMC/BMI, surface corporelle
    - pharmacologie : dose, posologie, clairance créatinine
    - scores : Glasgow, CHA₂DS₂-VASc
    """
    t = texte.lower()
    nums = [float(n) for n in re.findall(r'(\d+\.?\d*)', texte)]
    params = {'type_probleme': 'inconnu', 'numeros': nums}

    # ── Détection du type ──
    if any(m in t for m in ['symptome', 'symptomes', 'diagnostic', 'diagnostique',
                              'maladie', 'pathologie', 'signe', 'signes',
                              'differentiel', 'probable']):
        params['type_probleme'] = 'diagnostic'
        params['symptomes'] = _extraire_symptomes(t)

    elif any(m in t for m in ['dose', 'posologie', 'mg/kg', 'mg/m²',
                                'clairance', 'creatinine', 'creat',
                                'cockcroft', 'perfusion', 'debit', 'dilution']):
        params['type_probleme'] = 'pharmacologie'
        _extraire_pharmaco(texte, params)

    elif any(m in t for m in ['imc', 'bmi', 'indice_masse', 'poids', 'taille',
                                'surface_corporelle', 'bsa']):
        params['type_probleme'] = 'physiologie'
        _extraire_mensurations(texte, params)

    elif any(m in t for m in ['score', 'glasgow', 'apache', 'chads',
                                'cha2ds2', 'vasc', 'wells', 'sofa']):
        params['type_probleme'] = 'score'
        _extraire_score(texte, params)

    return params


def _extraire_symptomes(texte_lower: str) -> List[str]:
    """Extrait les symptômes mentionnés dans le texte."""
    symptomes_trouves = []
    for symptome in DIAGNOSTICS_DIFFERENTIELS:
        if symptome in texte_lower:
            symptomes_trouves.append(symptome)
    if not symptomes_trouves:
        # Chercher des mots individuels
        for mot in ['fievre', 'toux', 'douleur', 'maux', 'fatigue', 'nausee',
                     'vomissement', 'diarrhee', 'vertige', 'oedeme']:
            if mot in texte_lower:
                symptomes_trouves.append(mot)
    return symptomes_trouves


def _extraire_mensurations(texte, params):
    """Extrait poids, taille, âge."""
    # Poids
    m_p = re.search(r'(\d+\.?\d*)\s*(kg|kilos?)', texte)
    if not m_p:
        m_p = re.search(r'(\d+\.?\d*)\s*(lb|lbs)', texte)
        if m_p:
            params['poids'] = round(float(m_p.group(1)) * 0.4536, 2)
            params['poids_unite'] = 'kg (converti de lbs)'
    if m_p and 'poids_unite' not in params:
        params['poids'] = float(m_p.group(1))
        params['poids_unite'] = 'kg'

    # Taille
    m_t = re.search(r'(\d+[.,]?\d*)\s*m\b', texte)
    if m_t:
        params['taille'] = float(m_t.group(1).replace(',', '.'))
        params['taille_unite'] = 'm'
    else:
        m_t = re.search(r'(\d+)\s*cm', texte)
        if m_t:
            params['taille'] = float(m_t.group(1)) / 100.0
            params['taille_unite'] = 'm (converti de cm)'

    # Âge
    m_a = re.search(r'(\d+)\s*ans?', texte)
    if m_a: params['age'] = int(m_a.group(1))


def _extraire_pharmaco(texte, params):
    """Extrait les paramètres pharmacologiques."""
    # Dose prescrite
    m_dose = re.search(r'(\d+\.?\d*)\s*(mg|g|μg|mcg)', texte)
    if m_dose:
        val = float(m_dose.group(1))
        unite = m_dose.group(2)
        # Convertir en mg si nécessaire
        if unite in ('g',): val *= 1000
        elif unite in ('μg', 'mcg'): val /= 1000
        params['dose'] = val
        params['dose_unite'] = 'mg'

    # Poids patient
    m_p = re.search(r'(\d+\.?\d*)\s*(kg|kilos?)', texte)
    if m_p: params['poids'] = float(m_p.group(1))

    # Créatinine
    m_creat = re.search(r'creatinine?\s*[=:]\s*(\d+\.?\d*)', texte)
    if not m_creat:
        m_creat = re.search(r'creat\s*[=:]\s*(\d+\.?\d*)', texte)
    if not m_creat:
        m_creat = re.search(r'(\d+\.?\d*)\s*(μmol|mmol|mg/dl)', texte)
    if m_creat:
        params['creatinine'] = float(m_creat.group(1))

    # Volume perfusion
    m_vol = re.search(r'(\d+\.?\d*)\s*ml', texte)
    if m_vol: params['volume'] = float(m_vol.group(1))

    # Durée
    m_duree = re.search(r'(\d+\.?\d*)\s*(h|heures?|min)', texte)
    if m_duree:
        val = float(m_duree.group(1))
        if m_duree.group(2).startswith('min'): val /= 60
        params['duree_h'] = val

    # Âge (pour Cockcroft)
    _extraire_mensurations(texte, params)


def _extraire_score(texte, params):
    """Extrait les paramètres pour les scores cliniques."""
    t = texte.lower()
    params['type_score'] = 'inconnu'

    if any(m in t for m in ['glasgow', 'gcs']):
        params['type_score'] = 'glasgow'
        # O=ouverture yeux, V=verbale, M=motrice
        m_o = re.search(r'[oO]\s*[=:]\s*(\d)', texte)
        m_v = re.search(r'[vV]\s*[=:]\s*(\d)', texte)
        m_m = re.search(r'[mM]\s*[=:]\s*(\d)', texte)
        if m_o: params['O'] = int(m_o.group(1))
        if m_v: params['V'] = int(m_v.group(1))
        if m_m: params['M'] = int(m_m.group(1))

    elif any(m in t for m in ['chads', 'cha2ds2', 'vasc']):
        params['type_score'] = 'cha2ds2_vasc'
        # Facteurs de risque
        params['age'] = params.get('age', 0)
        params['age_75'] = '75' in texte or '≥75' in texte or '>75' in texte
        params['sexe_f'] = any(m in t for m in ['femme', 'feminin', 'f'])
        params['hta'] = any(m in t for m in ['hta', 'hypertension'])
        params['diabete'] = any(m in t for m in ['diabete', 'diabète'])
        params['ic'] = any(m in t for m in ['insuffisance_cardiaque', 'ic',
                                              'cardiaque'])
        params['avc'] = any(m in t for m in ['avc', 'aom', 'embolie',
                                              'thrombose', 'thromboembolique'])


# ═══════════════════════════════════════════════════════════════
# SOLVEUR MÉDICAL
# ═══════════════════════════════════════════════════════════════

def resoudre_medecine(params: Dict) -> Dict:
    """Résout un problème médical."""
    ptype = params.get('type_probleme', 'inconnu')
    resultat = {
        'domaine': 'medecine',
        'type_probleme': ptype,
    }

    if ptype == 'diagnostic':
        return _resoudre_diagnostic(params)

    elif ptype == 'physiologie':
        return _resoudre_physiologie(params)

    elif ptype == 'pharmacologie':
        return _resoudre_pharmacologie(params)

    elif ptype == 'score':
        return _resoudre_score(params)

    else:
        resultat['erreur'] = f'Type de problème non reconnu: {ptype}'
        return resultat


# ── Diagnostic différentiel ──

def _resoudre_diagnostic(params):
    symptomes = params.get('symptomes', [])
    if not symptomes:
        return {'type_probleme': 'diagnostic',
                'erreur': 'Aucun symptôme reconnu dans le texte'}

    # Compter les occurrences pour chaque diagnostic
    scores_diag = {}
    for symptome in symptomes:
        if symptome in DIAGNOSTICS_DIFFERENTIELS:
            for diag in DIAGNOSTICS_DIFFERENTIELS[symptome]:
                scores_diag[diag] = scores_diag.get(diag, 0) + 1

    # Trier par score décroissant
    diags_tries = sorted(scores_diag.items(), key=lambda x: -x[1])

    # Calculer la probabilité relative
    total = sum(s for _, s in diags_tries) if diags_tries else 1
    hypotheses = []
    for diag, score in diags_tries[:5]:
        hypotheses.append({
            'diagnostic': diag.replace('_', ' ').title(),
            'score': score,
            'probabilite': round(score / total * 100, 1),
        })

    return {
        'type_probleme': 'diagnostic',
        'symptomes_identifies': symptomes,
        'hypotheses': hypotheses,
        'recommandation': ('ATTENTION : Ceci est une aide au diagnostic '
                          'et ne remplace pas un avis médical. '
                          'Consultez un professionnel de santé.'),
    }


# ── Physiologie ──

def _resoudre_physiologie(params):
    poids = params.get('poids')
    taille = params.get('taille')
    resultat = {'type_probleme': 'physiologie'}

    if poids is not None and taille is not None and taille > 0:
        imc = poids / (taille ** 2)
        resultat['imc'] = round(imc, 1)
        resultat['imc_unite'] = 'kg/m²'

        # Interprétation IMC (OMS)
        if imc < 16.5:
            interpretation = 'Dénutrition sévère'
        elif imc < 18.5:
            interpretation = 'Maigreur'
        elif imc < 25:
            interpretation = 'Normal'
        elif imc < 30:
            interpretation = 'Surpoids'
        elif imc < 35:
            interpretation = 'Obésité modérée (classe I)'
        elif imc < 40:
            interpretation = 'Obésité sévère (classe II)'
        else:
            interpretation = 'Obésité morbide (classe III)'
        resultat['interpretation_imc'] = interpretation

        # Poids idéal (formule de Lorentz)
        # Simplifié : IMC 22 pour le poids idéal
        poids_ideal = 22 * (taille ** 2)
        resultat['poids_ideal'] = round(poids_ideal, 1)
        resultat['poids_ideal_unite'] = 'kg'

        # Surface corporelle (Mosteller)
        sc = math.sqrt((taille * 100 * poids) / 3600)
        resultat['surface_corporelle'] = round(sc, 2)
        resultat['surface_corporelle_unite'] = 'm²'

    elif poids is not None and taille is None and 'imc' in str(params):
        resultat['erreur'] = 'Taille requise pour calculer l\'IMC'
    elif taille is not None and poids is None and 'imc' in str(params):
        resultat['erreur'] = 'Poids requis pour calculer l\'IMC'
    else:
        resultat['erreur'] = 'Poids (kg) et taille (m) requis'

    return resultat


# ── Pharmacologie ──

def _resoudre_pharmacologie(params):
    resultat = {'type_probleme': 'pharmacologie'}
    dose = params.get('dose')
    poids = params.get('poids')
    creatinine = params.get('creatinine')
    age = params.get('age')
    volume = params.get('volume')
    duree_h = params.get('duree_h')

    # ── Clairance créatinine (Cockcroft-Gault) ──
    if creatinine is not None and age is not None and poids is not None:
        # Formule Cockcroft-Gault (homme par défaut, ×0.85 si femme)
        clair = ((140 - age) * poids) / (creatinine * 0.814)  # μmol/L → mg/dL (/88.4)
        # Correction plus simple si créatinine en μmol/L
        clair_ml_min = ((140 - age) * poids * 1.23) / creatinine  # si créat en μmol/L
        resultat['clairance_cockcroft'] = round(clair_ml_min, 1)
        resultat['clairance_unite'] = 'ml/min'
        resultat['formule'] = 'Cockcroft-Gault : ((140-âge)×poids×1.23)/créat(μmol/L)'

        # Stade IRC
        if clair_ml_min >= 90:
            stade = 'Stade 1 — Fonction rénale normale'
        elif clair_ml_min >= 60:
            stade = 'Stade 2 — IRC légère'
        elif clair_ml_min >= 30:
            stade = 'Stade 3 — IRC modérée'
        elif clair_ml_min >= 15:
            stade = 'Stade 4 — IRC sévère'
        else:
            stade = 'Stade 5 — IRC terminale (dialyse)'
        resultat['stade_irc'] = stade

    # ── Dose en mg/kg ──
    if dose is not None and poids is not None:
        dose_kg = dose / poids
        resultat['dose_mg_kg'] = round(dose_kg, 3)
        resultat['dose_mg_kg_unite'] = 'mg/kg'

    # ── Débit de perfusion ──
    if volume is not None and duree_h is not None and duree_h > 0:
        debit = volume / duree_h
        resultat['debit_perfusion'] = round(debit, 1)
        resultat['debit_unite'] = 'ml/h'
        # En gouttes/min (si 1 ml = 20 gouttes standard)
        gouttes_min = debit * 20 / 60
        resultat['gouttes_min'] = round(gouttes_min, 1)
        resultat['gouttes_unite'] = 'gouttes/min'

    if not resultat or len(resultat) <= 1:
        resultat['erreur'] = 'Données insuffisantes pour le calcul pharmacologique'

    return resultat


# ── Scores cliniques ──

def _resoudre_score(params):
    score_type = params.get('type_score', 'inconnu')
    resultat = {'type_probleme': 'score', 'type_score': score_type}

    if score_type == 'glasgow':
        O = params.get('O', 0)
        V = params.get('V', 0)
        M = params.get('M', 0)
        total = O + V + M
        resultat['score_glasgow'] = total
        resultat['composantes'] = f'O={O} + V={V} + M={M}'
        resultat['echelle'] = '/15'

        if total == 15:
            interpretation = 'Conscience normale'
        elif total >= 13:
            interpretation = 'Trouble léger de la conscience'
        elif total >= 9:
            interpretation = 'Trouble modéré — surveillance étroite'
        elif total >= 6:
            interpretation = 'Trouble sévère — protection des voies aériennes'
        else:
            interpretation = 'Coma profond — intubation probable'
        resultat['interpretation'] = interpretation

    elif score_type == 'cha2ds2_vasc':
        score = 0
        details = []

        # Insuffisance cardiaque = 1
        if params.get('ic'):
            score += 1
            details.append('IC (+1)')
        # HTA = 1
        if params.get('hta'):
            score += 1
            details.append('HTA (+1)')
        # Âge ≥ 75 = 2
        if params.get('age_75'):
            score += 2
            details.append('Âge≥75 (+2)')
        elif params.get('age', 0) >= 65:
            score += 1
            details.append('Âge 65-74 (+1)')
        # Diabète = 1
        if params.get('diabete'):
            score += 1
            details.append('Diabète (+1)')
        # AVC/ATCD thromboembolique = 2
        if params.get('avc'):
            score += 2
            details.append('AVC/AOM (+2)')
        # Sexe féminin = 1
        if params.get('sexe_f'):
            score += 1
            details.append('Sexe F (+1)')

        resultat['score_cha2ds2_vasc'] = score
        resultat['details'] = details

        if score == 0:
            reco = 'Pas d\'anticoagulation'
        elif score == 1:
            reco = 'Anticoagulation à considérer (bénéfice modéré)'
        else:
            reco = 'Anticoagulation recommandée (bénéfice net)'
        resultat['recommandation'] = reco

    else:
        resultat['erreur'] = f'Score non implémenté: {score_type}'

    return resultat


# ═══════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════

EXEMPLES_MEDECINE = [
    "Symptomes : fievre toux dyspnee. Quel diagnostic probable ?",
    "IMC pour un patient de 70 kg et 1.75 m",
    "Clairance creatinine : age 65 ans, poids 70 kg, creatinine 120 μmol/L",
    "Dose en mg/kg : dose 500 mg, poids 70 kg",
    "Score de Glasgow : O=4 V=5 M=6",
    "Score CHA2DS2-VASc : homme 72 ans, HTA, diabete",
    "Debit perfusion : volume 500 ml sur 4 heures",
]


def test_medecine():
    print(f"\n{'='*75}")
    print(f"  SOLVEUR MÉDECINE — Test extracteur + solveur")
    print(f"{'='*75}\n")
    for i, texte in enumerate(EXEMPLES_MEDECINE):
        params = extraire_medecine(texte)
        resultat = resoudre_medecine(params)
        ptype = params.get('type_probleme', '?')
        print(f"  [{i+1}] {texte[:60]:<60s}")
        print(f"      Type: {ptype:<15s}")

        if 'symptomes_identifies' in resultat:
            print(f"      Symptômes : {resultat['symptomes_identifies']}")
        if 'hypotheses' in resultat:
            for h in resultat['hypotheses']:
                print(f"      -> {h['diagnostic']:<30s} {h['probabilite']:.0f}%")
        if 'imc' in resultat:
            print(f"      IMC = {resultat['imc']} kg/m² ({resultat.get('interpretation_imc', '')})")
            if 'surface_corporelle' in resultat:
                print(f"      Surface corporelle = {resultat['surface_corporelle']} m²")
                print(f"      Poids idéal = {resultat['poids_ideal']} kg")
        if 'clairance_cockcroft' in resultat:
            print(f"      Clairance = {resultat['clairance_cockcroft']} ml/min ({resultat.get('stade_irc', '')})")
        if 'dose_mg_kg' in resultat:
            print(f"      Dose = {resultat['dose_mg_kg']} mg/kg")
        if 'score_glasgow' in resultat:
            print(f"      Glasgow = {resultat['score_glasgow']}/15 -> {resultat.get('interpretation', '')}")
        if 'score_cha2ds2_vasc' in resultat:
            print(f"      Score = {resultat['score_cha2ds2_vasc']} ({', '.join(resultat.get('details', []))})")
            print(f"      -> {resultat.get('recommandation', '')}")
        if 'debit_perfusion' in resultat:
            print(f"      Débit = {resultat['debit_perfusion']} ml/h ({resultat.get('gouttes_min', '')} gouttes/min)")
        if 'erreur' in resultat:
            print(f"      [ERREUR] {resultat['erreur']}")
        print()


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Solveur Médecine Harmonique')
    p.add_argument('--test', '-t', action='store_true', help='Lancer les tests')
    p.add_argument('--probleme', '-p', type=str, default=None, help='Résoudre un problème')
    args = p.parse_args()

    if args.probleme:
        params = extraire_medecine(args.probleme)
        resultat = resoudre_medecine(params)
        import json
        print(json.dumps(resultat, ensure_ascii=False, indent=2, default=str))
    else:
        test_medecine()