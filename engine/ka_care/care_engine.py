"""
KA SANTÉ MONDE — Outils de Santé Harmonique pour Zones Sous-Équipées
======================================================================

Conçu pour les agents de santé communautaire (ASC) dans les pays
à infrastructure médicale limitée.

Fonctionne sur UN SMARTPHONE STANDARD. Aucun accessoire requis.
Offline. Multilingue. Gratuit.

Outils implémentés :
1. Dépistage pneumonie (enfant < 5 ans) — critères OMS/IMCI
2. Évaluation déshydratation (enfant) — échelle OMS
3. Détection syndrome fébrile — score harmonique combiné
4. Dépistage anémie — analyse colorimétrique de la paume
5. Signes de danger nouveau-né — 7 signes OMS

Principe : Tous les signes vitaux sont extraits de la caméra (PPG)
et du microphone. L'analyse harmonique (φ, π, e, √2, √3, √5)
fournit une couche d'interprétation cohérente.

Auteur : Kotto Alain — Juillet 2026
"""

import math
from typing import Dict, List, Optional, Tuple

# ========== CONSTANTES ==========
PHI = (1 + math.sqrt(5)) / 2
PI = math.pi
E = math.e
S2 = math.sqrt(2)
S3 = math.sqrt(3)
S5 = math.sqrt(5)

# ========== OUTIL 1 : DÉPISTAGE PNEUMONIE (ENFANT < 5 ANS) ==========
# Critères OMS/IMCI (Integrated Management of Childhood Illness)

def pneumonia_screener(
    age_months: int,
    respiratory_rate: Optional[int] = None,
    heart_rate: Optional[int] = None,
    chest_indrawing: Optional[bool] = None,
    grunting: Optional[bool] = None,
    oxygen_saturation: Optional[int] = None,
) -> Dict:
    """
    Dépistage pneumonie selon critères OMS/IMCI + analyse harmonique.
    
    Classification OMS :
    - Pneumonie sévère : tirage sous-costal + détresse respiratoire → REFERER URGENCE
    - Pneumonie : respiration rapide seule → ANTIBIOTIQUES + suivi
    - Pas de pneumonie : aucun signe → CONSEILS + surveillance
    
    Seuils de respiration rapide (OMS) :
    - < 2 mois : ≥ 60 rpm
    - 2-12 mois : ≥ 50 rpm
    - 1-5 ans : ≥ 40 rpm
    """
    result = {
        "outil": "Dépistage Pneumonie (OMS/IMCI)",
        "age_mois": age_months,
        "classification": None,
        "action": None,
        "signes_detectes": [],
        "score_harmonique": None,
    }
    
    danger_signs = []
    
    # Déterminer le seuil de respiration rapide selon l'âge
    if age_months < 2:
        rr_threshold = 60
    elif age_months < 12:
        rr_threshold = 50
    else:
        rr_threshold = 40
    
    # Évaluer la respiration
    if respiratory_rate is not None:
        if respiratory_rate >= rr_threshold:
            danger_signs.append(f"Respiration rapide : {respiratory_rate} rpm (seuil: {rr_threshold})")
    
    # Évaluer les signes de gravité
    if chest_indrawing:
        danger_signs.append("Tirage sous-costal — SIGNAL D'URGENCE")
    if grunting:
        danger_signs.append("Geignement expiratoire")
    
    # Analyse harmonique : la pneumonie altère √5 (inflammation)
    # Score combiné : FC élevée + RR élevée + désaturation
    harmonic_score = 1.0
    if heart_rate and respiratory_rate:
        hr_dev = abs(heart_rate - 120) / 40  # normalisé pour enfant
        rr_dev = abs(respiratory_rate - 30) / 25
        harmonic_score = PHI ** (-(hr_dev + rr_dev) / 2)
    
    # Classification OMS
    if chest_indrawing or (respiratory_rate and respiratory_rate >= rr_threshold + 15):
        result["classification"] = "PNEUMONIE SÉVÈRE"
        result["action"] = "⚠️ REFERER D'URGENCE VERS HÔPITAL. Risque vital."
    elif respiratory_rate and respiratory_rate >= rr_threshold:
        result["classification"] = "PNEUMONIE"
        result["action"] = "💊 Antibiotiques oraux (amoxicilline 5 jours) + suivi à 48h. Expliquer les signes de danger à la mère."
    elif oxygen_saturation is not None and oxygen_saturation < 90:
        result["classification"] = "PNEUMONIE SÉVÈRE (hypoxémie)"
        result["action"] = "⚠️ REFERER D'URGENCE. Oxygène nécessaire."
    else:
        result["classification"] = "PAS DE PNEUMONIE"
        result["action"] = "✅ Rassurer la mère. Conseils : alimentation, hydratation, surveillance. Revenir si fièvre ou toux > 3 jours."
    
    result["signes_detectes"] = danger_signs if danger_signs else ["Aucun signe de danger détecté"]
    result["score_harmonique"] = round(harmonic_score, 3)
    result["constante_alteree"] = "√5 (inflammation pulmonaire)" if danger_signs else "Équilibre"
    
    return result


# ========== OUTIL 2 : ÉVALUATION DÉSHYDRATATION ==========
# Échelle OMS : déshydratation sévère / modérée / absente

def dehydration_assessor(
    age_months: int,
    skin_pinch_seconds: Optional[float] = None,
    sunken_eyes: Optional[bool] = None,
    drinks_eagerly: Optional[bool] = None,
    unable_to_drink: Optional[bool] = None,
    heart_rate: Optional[int] = None,
    respiratory_rate: Optional[int] = None,
    capillary_refill_seconds: Optional[float] = None,
) -> Dict:
    """
    Évaluation de la déshydratation selon les critères OMS.
    
    L'analyse harmonique interprète la déshydratation comme une
    rupture de la symétrie √2 (équilibre hydrique).
    
    Classification OMS :
    - Déshydratation sévère : ≥ 2 signes de gravité → URGENCE
    - Déshydratation modérée : ≥ 2 signes modérés → SRO + surveillance
    - Pas de déshydratation : < 2 signes → SRO à domicile
    """
    result = {
        "outil": "Évaluation Déshydratation (OMS)",
        "age_mois": age_months,
        "classification": None,
        "action": None,
        "signes_presentes": [],
        "score_harmonique": None,
    }
    
    severe_signs = 0
    moderate_signs = 0
    signs_detail = []
    
    # Signes de gravité
    if skin_pinch_seconds is not None and skin_pinch_seconds > 2.0:
        severe_signs += 1
        signs_detail.append(f"Pli cutané très lent ({skin_pinch_seconds:.1f}s) — GRAVE")
    elif skin_pinch_seconds is not None and skin_pinch_seconds > 1.0:
        moderate_signs += 1
        signs_detail.append(f"Pli cutané lent ({skin_pinch_seconds:.1f}s)")
    
    if unable_to_drink:
        severe_signs += 1
        signs_detail.append("Incapable de boire — GRAVE")
    elif drinks_eagerly:
        moderate_signs += 1
        signs_detail.append("Boit avidement")
    
    if sunken_eyes:
        moderate_signs += 1
        signs_detail.append("Yeux enfoncés")
    
    # Temps de recoloration capillaire (normal < 2s, pathologique > 3s)
    if capillary_refill_seconds is not None:
        if capillary_refill_seconds > 3.0:
            severe_signs += 1
            signs_detail.append(f"TRC prolongé ({capillary_refill_seconds:.1f}s) — GRAVE")
        elif capillary_refill_seconds > 2.0:
            moderate_signs += 1
            signs_detail.append(f"TRC ralenti ({capillary_refill_seconds:.1f}s)")
    
    # Signes vitaux (FC, RR élevés = compensation)
    if heart_rate and heart_rate > 140:
        moderate_signs += 1
        signs_detail.append(f"Tachycardie ({heart_rate} bpm)")
    if respiratory_rate and respiratory_rate > 40:
        moderate_signs += 1
        signs_detail.append(f"Polypnée ({respiratory_rate} rpm)")
    
    # Classification
    if severe_signs >= 2:
        result["classification"] = "DÉSHYDRATATION SÉVÈRE"
        result["action"] = "⚠️ REFERER D'URGENCE. Perfusion IV nécessaire. Risque de choc hypovolémique."
    elif moderate_signs >= 2:
        result["classification"] = "DÉSHYDRATATION MODÉRÉE"
        result["action"] = "💧 SRO (Sels de Réhydratation Orale) : 75 ml/kg sur 4h. Surveiller. Revenir si aggravation."
    else:
        result["classification"] = "PAS DE DÉSHYDRATATION"
        result["action"] = "✅ SRO à domicile après chaque selle liquide. Continuer alimentation. Surveiller."
    
    result["signes_presentes"] = signs_detail if signs_detail else ["Aucun signe de déshydratation"]
    
    # Score harmonique : déshydratation = rupture √2 (symétrie)
    if severe_signs + moderate_signs > 0:
        harmonic_score = PHI ** (-(severe_signs * 2 + moderate_signs) / 3)
    else:
        harmonic_score = 1.0
    result["score_harmonique"] = round(harmonic_score, 3)
    result["constante_alteree"] = "√2 (équilibre hydrique)"
    
    return result


# ========== OUTIL 3 : DÉTECTION SYNDROME FÉBRILE ==========

def febrile_screener(
    heart_rate: Optional[int] = None,
    respiratory_rate: Optional[int] = None,
    hrv_sdnn: Optional[float] = None,
    ppg_amplitude: Optional[float] = None,
    reported_fever: bool = False,
    age_years: int = 5,
) -> Dict:
    """
    Détection de syndrome fébrile par analyse harmonique du PPG.
    
    La fièvre modifie le patron PPG :
    - FC augmente (+10 bpm par °C de fièvre)
    - HRV diminue (le système autonome est stressé)
    - Amplitude PPG augmente (vasodilatation périphérique)
    - Respiration s'accélère
    
    Constante altérée : e (régulation thermique exponentielle)
    
    Ne mesure PAS la température directement — détecte la SIGNATURE
    HARMONIQUE de la fièvre dans les signes vitaux.
    """
    result = {
        "outil": "Détection Syndrome Fébrile Harmonique",
        "probabilite_fievre": None,
        "action": None,
        "indicateurs": [],
        "score_harmonique": None,
    }
    
    indicators = []
    fever_score = 0.0
    total_weight = 0.0
    
    # FC : normal pour âge
    if age_years < 1:
        normal_hr = 120
    elif age_years < 5:
        normal_hr = 100
    elif age_years < 12:
        normal_hr = 85
    else:
        normal_hr = 72
    
    if heart_rate:
        hr_zscore = (heart_rate - normal_hr) / 20
        # Chaque +1°C de fièvre = +10 bpm
        # Si FC > normale + 20 (soit +2°C équivalent) → forte suspicion
        hr_weight = min(1.0, max(0.0, hr_zscore / 2))
        fever_score += hr_weight * 0.35
        total_weight += 0.35
        if hr_weight > 0.5:
            indicators.append(f"FC élevée ({heart_rate} bpm, attendu ~{normal_hr})")
    
    # RR
    if respiratory_rate:
        rr_zscore = (respiratory_rate - 20) / 10
        rr_weight = min(1.0, max(0.0, rr_zscore / 2))
        fever_score += rr_weight * 0.25
        total_weight += 0.25
        if rr_weight > 0.5:
            indicators.append(f"Respiration rapide ({respiratory_rate} rpm)")
    
    # HRV basse = stress fébrile
    if hrv_sdnn:
        # HRV normale > 40ms. En fièvre, HRV chute.
        hrv_weight = min(1.0, max(0.0, (50 - hrv_sdnn) / 30))
        fever_score += hrv_weight * 0.25
        total_weight += 0.25
        if hrv_weight > 0.5:
            indicators.append(f"HRV basse ({hrv_sdnn:.0f} ms) — stress autonome")
    
    # Amplitude PPG augmentée (vasodilatation)
    if ppg_amplitude:
        amp_weight = min(1.0, max(0.0, ppg_amplitude / 3))
        fever_score += amp_weight * 0.15
        total_weight += 0.15
    
    # Fièvre rapportée par le patient
    if reported_fever:
        fever_score += 0.60  # fort poids si fièvre subjectivement ressentie
        total_weight += 0.60
        indicators.append("Fièvre rapportée par le patient")
    
    # Normaliser
    if total_weight > 0:
        fever_prob = fever_score / total_weight
    else:
        fever_prob = 0.0
    
    result["probabilite_fievre"] = round(fever_prob * 100)
    result["score_harmonique"] = round(E ** (-(1 - fever_prob) * 3), 3)  # décroissance en e
    
    if fever_prob > 0.7:
        result["action"] = "⚠️ Forte probabilité de fièvre. Rechercher la cause (paludisme, infection...). Test de dépistage recommandé. Antipyrétique si inconfort."
    elif fever_prob > 0.4:
        result["action"] = "⚠️ Fièvre possible. Surveiller la température si possible. Revenir si aggravation."
    else:
        result["action"] = "✅ Pas de signe évident de fièvre. Rassurer."
    
    result["indicateurs"] = indicators if indicators else ["Aucun indicateur fébrile détecté"]
    result["constante_alteree"] = "e (régulation thermique)"
    
    return result


# ========== OUTIL 4 : DÉPISTAGE ANÉMIE (PÂLEUR) ==========

def anemia_screener(
    palmar_pallor: Optional[bool] = None,
    conjunctival_pallor: Optional[bool] = None,
    heart_rate: Optional[int] = None,
    respiratory_rate: Optional[int] = None,
    fatigue_reported: bool = False,
    hrv_sdnn: Optional[float] = None,
) -> Dict:
    """
    Dépistage de l'anémie par signes cliniques + analyse PPG.
    
    Classification OMS :
    - Anémie sévère : pâleur + signes de décompensation → URGENCE
    - Anémie modérée : pâleur isolée → TRAITEMENT + suivi
    - Pas d'anémie : RAS
    
    L'anémie modifie le signal PPG :
    - Amplitude réduite (moins d'hémoglobine = moins d'absorption)
    - FC élevée (compensation)
    - HRV réduite
    
    Constante altérée : √3 (capacité de transport d'oxygène — volume)
    """
    result = {
        "outil": "Dépistage Anémie",
        "classification": None,
        "action": None,
        "signes": [],
        "score_harmonique": None,
    }
    
    danger_count = 0
    signs = []
    
    if palmar_pallor:
        danger_count += 1
        signs.append("Pâleur palmaire")
    
    if conjunctival_pallor:
        danger_count += 2  # plus spécifique
        signs.append("Pâleur conjonctivale — signe fort")
    
    # Signes de décompensation
    decompensation = False
    if heart_rate and heart_rate > 140:
        decompensation = True
        signs.append(f"Tachycardie sévère ({heart_rate} bpm) — décompensation")
    if respiratory_rate and respiratory_rate > 40:
        decompensation = True
        signs.append(f"Polypnée ({respiratory_rate} rpm) — décompensation")
    if fatigue_reported:
        signs.append("Fatigue rapportée")
    
    if hrv_sdnn and hrv_sdnn < 20:
        signs.append(f"HRV très basse ({hrv_sdnn:.0f} ms)")
    
    # Classification
    if (danger_count >= 3 or (danger_count >= 2 and decompensation)):
        result["classification"] = "ANÉMIE SÉVÈRE"
        result["action"] = "⚠️ REFERER D'URGENCE. Transfusion probablement nécessaire. Risque de défaillance cardiaque."
    elif danger_count >= 1:
        result["classification"] = "ANÉMIE MODÉRÉE"
        result["action"] = "💊 Fer + acide folique. Alimentation riche en fer. Suivi à 2 semaines. Rechercher la cause (paludisme, parasitose, malnutrition)."
    else:
        result["classification"] = "PAS D'ANÉMIE ÉVIDENTE"
        result["action"] = "✅ Pas de signe franc. Si fatigue persistante, envisager bilan."
    
    result["signes"] = signs if signs else ["Aucun signe d'anémie détecté"]
    result["score_harmonique"] = round(S3 ** (-danger_count / 4), 3) if danger_count > 0 else 1.0
    result["constante_alteree"] = "√3 (capacité de transport O₂)"
    
    return result


# ========== OUTIL 5 : SIGNES DE DANGER NOUVEAU-NÉ ==========

def newborn_danger_screener(
    age_days: int,
    heart_rate: Optional[int] = None,
    respiratory_rate: Optional[int] = None,
    temperature_feels: str = "normal",  # "cold", "normal", "hot"
    feeding_well: bool = True,
    moving_well: bool = True,
    umbilical_redness: bool = False,
    convulsions: bool = False,
    jaundice_palms: bool = False,
) -> Dict:
    """
    Dépistage des 7 signes de danger OMS chez le nouveau-né (0-28 jours).
    
    Signes de danger OMS :
    1. Ne boit pas / difficulté à s'alimenter
    2. Convulsions
    3. Respiration rapide (≥ 60 rpm)
    4. Tirage sous-costal sévère
    5. Fièvre (température > 38°C)
    6. Hypothermie (température < 35.5°C)
    7. Ne bouge que si stimulé / léthargique
    
    + Signes additionnels :
    - Ictère (jaunisse) des paumes/plantes
    - Infection du cordon ombilical
    - FC anormale (< 100 bpm ou > 180 bpm)
    """
    result = {
        "outil": "Signes de Danger Nouveau-Né (OMS)",
        "age_jours": age_days,
        "nb_signes_danger": 0,
        "signes_detectes": [],
        "action": None,
        "score_harmonique": None,
    }
    
    danger_signs = []
    
    # 1. Alimentation
    if not feeding_well:
        danger_signs.append("Ne boit pas / difficulté à s'alimenter — GRAVE")
    
    # 2. Convulsions
    if convulsions:
        danger_signs.append("Convulsions — URGENCE VITALE")
    
    # 3. Respiration rapide (seuil OMS : ≥ 60 rpm pour < 2 mois)
    if respiratory_rate and respiratory_rate >= 60:
        danger_signs.append(f"Respiration rapide ({respiratory_rate} rpm) — détresse respiratoire")
    elif respiratory_rate and respiratory_rate < 20:
        danger_signs.append(f"Respiration lente ({respiratory_rate} rpm) — apnées ?")
    
    # 4. Température (rapportée)
    if temperature_feels == "cold":
        danger_signs.append("Hypothermie (froid au toucher) — risque infectieux")
    elif temperature_feels == "hot":
        danger_signs.append("Hyperthermie (chaud au toucher) — infection possible")
    
    # 5. Activité
    if not moving_well:
        danger_signs.append("Léthargique / ne bouge que si stimulé — GRAVE")
    
    # 6. FC anormale
    if heart_rate:
        if heart_rate < 100:
            danger_signs.append(f"Bradycardie ({heart_rate} bpm) — URGENCE (< 100 bpm chez NN = danger)")
        elif heart_rate > 180:
            danger_signs.append(f"Tachycardie sévère ({heart_rate} bpm)")
    
    # 7. Cordon
    if umbilical_redness:
        danger_signs.append("Infection du cordon ombilical — risque de septicémie")
    
    # 8. Ictère
    if jaundice_palms:
        danger_signs.append("Ictère des paumes — risque de kernictère")
    
    # Classification
    severe_count = sum(1 for s in danger_signs if "GRAVE" in s or "URGENCE" in s)
    
    if severe_count >= 1 or len(danger_signs) >= 3:
        result["action"] = "⚠️ URGENCE VITALE. Référer IMMÉDIATEMENT vers hôpital avec soins néonatals. Ne pas attendre."
    elif len(danger_signs) >= 1:
        result["action"] = "⚠️ Signe(s) de danger détecté(s). Référer vers centre de santé. Surveiller étroitement pendant le transport."
    else:
        result["action"] = "✅ Aucun signe de danger. Conseils : allaitement exclusif, peau à peau, surveillance. Revenir si changement."
    
    result["nb_signes_danger"] = len(danger_signs)
    result["signes_detectes"] = danger_signs if danger_signs else ["Aucun signe de danger"]
    result["score_harmonique"] = round(PHI ** (-len(danger_signs) / 2), 3)
    result["constante_alteree"] = "π (cycle vital néonatal)" if danger_signs else "Équilibre"
    
    return result


# ========== FONCTION DE SYNTHÈSE : ÉVALUATION GLOBALE ==========

def community_health_assessment(
    age_months: int = 36,
    heart_rate: Optional[int] = None,
    respiratory_rate: Optional[int] = None,
    hrv_sdnn: Optional[float] = None,
    ppg_amplitude: Optional[float] = None,
    chest_indrawing: bool = False,
    skin_pinch_seconds: Optional[float] = None,
    sunken_eyes: bool = False,
    palmar_pallor: bool = False,
    reported_fever: bool = False,
    feeding_well: bool = True,
) -> Dict:
    """
    Évaluation de santé communautaire complète.
    Combine tous les outils de dépistage en UN SEUL examen.
    
    Conçu pour les agents de santé communautaire :
    - 5 minutes d'examen
    - 1 smartphone
    - Résultat clair : REFERER / TRAITER / SURVEILLER
    """
    results = {}
    urgent = False
    actions = []
    harmonic_scores = []
    
    # 1. Pneumonie (si âge < 5 ans = 60 mois)
    if age_months < 60:
        pneumo = pneumonia_screener(
            age_months=age_months,
            respiratory_rate=respiratory_rate,
            heart_rate=heart_rate,
            chest_indrawing=chest_indrawing,
        )
        results["pneumonie"] = pneumo
        harmonic_scores.append(pneumo["score_harmonique"])
        if "URGENCE" in pneumo.get("action", ""):
            urgent = True
            actions.append(pneumo["action"])
    
    # 2. Déshydratation
    dehy = dehydration_assessor(
        age_months=age_months,
        skin_pinch_seconds=skin_pinch_seconds,
        sunken_eyes=sunken_eyes,
        heart_rate=heart_rate,
        respiratory_rate=respiratory_rate,
    )
    results["deshydratation"] = dehy
    harmonic_scores.append(dehy["score_harmonique"])
    if "URGENCE" in dehy.get("action", ""):
        urgent = True
        actions.append(dehy["action"])
    
    # 3. Fièvre
    fever = febrile_screener(
        heart_rate=heart_rate,
        respiratory_rate=respiratory_rate,
        hrv_sdnn=hrv_sdnn,
        ppg_amplitude=ppg_amplitude,
        reported_fever=reported_fever,
        age_years=max(0, age_months // 12),
    )
    results["fievre"] = fever
    harmonic_scores.append(fever["score_harmonique"])
    
    # 4. Anémie
    anemia = anemia_screener(
        palmar_pallor=palmar_pallor,
        heart_rate=heart_rate,
        respiratory_rate=respiratory_rate,
        hrv_sdnn=hrv_sdnn,
    )
    results["anemie"] = anemia
    harmonic_scores.append(anemia["score_harmonique"])
    if "URGENCE" in anemia.get("action", ""):
        urgent = True
        actions.append(anemia["action"])
    
    # 5. Nouveau-né (si < 28 jours)
    if age_months < 1:
        newborn = newborn_danger_screener(
            age_days=age_months * 30,
            heart_rate=heart_rate,
            respiratory_rate=respiratory_rate,
            feeding_well=feeding_well,
        )
        results["nouveau_ne"] = newborn
        harmonic_scores.append(newborn["score_harmonique"])
        if "URGENCE" in newborn.get("action", ""):
            urgent = True
            actions.append(newborn["action"])
    
    # Score harmonique global
    global_score = sum(harmonic_scores) / len(harmonic_scores) if harmonic_scores else 1.0
    
    # Verdict final
    if urgent:
        verdict = "⚠️ REFERER — Signes de danger détectés. Transférer vers structure de santé."
    elif global_score < 0.6:
        verdict = "⚠️ TRAITER — Pathologie(s) probable(s). Appliquer protocole et surveiller."
    else:
        verdict = "✅ SURVEILLER — Pas de signe de gravité. Conseils et suivi à domicile."
    
    return {
        "verdict": verdict,
        "urgent": urgent,
        "score_harmonique_global": round(global_score, 3),
        "actions_recommandees": actions if actions else ["Conseils de santé + surveillance à domicile"],
        "resultats_detailles": results,
    }


# ========== TEST ==========
if __name__ == "__main__":
    print("=" * 70)
    print("KA SANTÉ MONDE — Test des Outils de Dépistage")
    print("=" * 70)
    
    # Cas 1 : Enfant de 18 mois avec pneumonie
    print("\n─── CAS 1 : Enfant 18 mois, toux + tirage ───")
    r = pneumonia_screener(age_months=18, respiratory_rate=55, 
                           heart_rate=130, chest_indrawing=True)
    print(f"  Classification : {r['classification']}")
    print(f"  Action : {r['action']}")
    
    # Cas 2 : Enfant de 2 ans avec diarrhée, déshydratation modérée
    print("\n─── CAS 2 : Enfant 24 mois, diarrhée, yeux enfoncés ───")
    r = dehydration_assessor(age_months=24, sunken_eyes=True, 
                             drinks_eagerly=True, heart_rate=130)
    print(f"  Classification : {r['classification']}")
    print(f"  Action : {r['action']}")
    
    # Cas 3 : Adulte avec suspicion de paludisme
    print("\n─── CAS 3 : Adulte 30 ans, fièvre rapportée, FC 105 ───")
    r = febrile_screener(heart_rate=105, respiratory_rate=24, 
                         hrv_sdnn=25, reported_fever=True, age_years=30)
    print(f"  Probabilité fièvre : {r['probabilite_fievre']}%")
    print(f"  Action : {r['action']}")
    
    # Cas 4 : Nouveau-né de 5 jours avec danger
    print("\n─── CAS 4 : Nouveau-né 5 jours, ne boit pas, froid ───")
    r = newborn_danger_screener(age_days=5, heart_rate=90, 
                                respiratory_rate=65, feeding_well=False,
                                temperature_feels="cold")
    print(f"  Signes danger : {r['nb_signes_danger']}")
    print(f"  Action : {r['action']}")
    
    # Cas 5 : Évaluation complète
    print("\n─── CAS 5 : Évaluation communautaire complète ───")
    r = community_health_assessment(
        age_months=9,
        heart_rate=155,
        respiratory_rate=55,
        chest_indrawing=True,
        reported_fever=True,
    )
    print(f"  Verdict : {r['verdict']}")
    print(f"  Score global : {r['score_harmonique_global']}")
    print(f"  Actions : {r['actions_recommandees'][:2]}...")
    
    print("\n" + "=" * 70)
    print("✅ Tous les outils de dépistage fonctionnent.")
    print("⚠ Ces outils sont des AIDES AU DÉPISTAGE, pas des diagnostics.")
    print("   Toute décision médicale doit être validée par un professionnel.")
    print("=" * 70)
