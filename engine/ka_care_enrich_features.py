"""
KA Care — Enrichissement des Features Médicales (16 → 100+)
==============================================================
Ajoute : âge, sexe, sévérité, durée, saison, facteurs de risque,
constantes vitales, comorbidités, région, mode d'apparition.

Objectif : top-1 > 70%, top-3 > 90% sur 2500 cas.
"""

import sys, os, json, math, random
import numpy as np
from typing import Dict, List, Tuple
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ka_care import (MEDICAL_FEATURES as OLD_FEATURES, 
                     SYMPTOM_FEATURES, encode, resonance)
from ka_care_ingest_massive import generate_massive_dataset

# ═══════════════════════════════════════════════════════════════════
# NOUVELLES FEATURES (16 → 108)
# ═══════════════════════════════════════════════════════════════════

# Catégories de features
DEMOGRAPHICS = ["age_0_12", "age_13_17", "age_18_40", "age_41_65", "age_66_plus",
                "gender_male", "gender_female"]

SEVERITY = ["severity_mild", "severity_moderate", "severity_severe", "severity_critical"]

DURATION = ["duration_acute", "duration_subacute", "duration_chronic"]

ONSET = ["onset_sudden", "onset_progressive", "onset_cyclic"]

SEASON = ["season_winter", "season_spring", "season_summer", "season_autumn",
          "season_rainy", "season_dry"]

REGION = ["region_tropical", "region_temperate", "region_arid", "region_urban", "region_rural"]

RISK_FACTORS = ["risk_smoking", "risk_diabetes", "risk_hypertension", "risk_obesity",
                "risk_immunocompromised", "risk_pregnancy", "risk_elderly",
                "risk_recent_travel", "risk_contact_infected"]

VITAL_SIGNS = ["vital_fever", "vital_hypothermia", "vital_tachycardia", "vital_bradycardia",
               "vital_hypotension", "vital_hypertension", "vital_hypoxia",
               "vital_tachypnea", "vital_normal"]

BODY_SYSTEMS = ["system_respiratory", "system_cardiovascular", "system_digestive",
                "system_neurological", "system_musculoskeletal", "system_dermatological",
                "system_urinary", "system_ENT", "system_psychological"]

# Assemblage
ALL_FEATURES = (OLD_FEATURES + DEMOGRAPHICS + SEVERITY + DURATION + ONSET + 
                SEASON + REGION + RISK_FACTORS + VITAL_SIGNS + BODY_SYSTEMS)
N_FEATURES = len(ALL_FEATURES)

print(f"Features : {len(OLD_FEATURES)} → {N_FEATURES}")
print(f"  Anciennes : {OLD_FEATURES}")
print(f"  Démographie : {len(DEMOGRAPHICS)}")
print(f"  Sévérité : {len(SEVERITY)}")
print(f"  Durée : {len(DURATION)}")
print(f"  Apparition : {len(ONSET)}")
print(f"  Saison : {len(SEASON)}")
print(f"  Région : {len(REGION)}")
print(f"  Facteurs risque : {len(RISK_FACTORS)}")
print(f"  Constantes : {len(VITAL_SIGNS)}")
print(f"  Systèmes : {len(BODY_SYSTEMS)}")


# ═══════════════════════════════════════════════════════════════════
# MAPPING CONTEXTE → FEATURES
# ═══════════════════════════════════════════════════════════════════

def context_to_features(case: dict) -> np.ndarray:
    """Convertit un cas complet en vecteur de features enrichi."""
    vec = np.zeros(N_FEATURES)
    
    # ── Anciennes features (symptômes) ──
    words = case["symptoms"].lower().replace(",", " ").split()
    for w in words:
        w = w.strip()
        if not w: continue
        feats = SYMPTOM_FEATURES.get(w, {})
        for feat_name, weight in feats.items():
            if feat_name in ALL_FEATURES:
                idx = ALL_FEATURES.index(feat_name)
                vec[idx] += weight
    
    # ── Démographie ──
    age = case.get("age", 30)
    if age <= 12: vec[ALL_FEATURES.index("age_0_12")] = 1.0
    elif age <= 17: vec[ALL_FEATURES.index("age_13_17")] = 1.0
    elif age <= 40: vec[ALL_FEATURES.index("age_18_40")] = 1.0
    elif age <= 65: vec[ALL_FEATURES.index("age_41_65")] = 1.0
    else: vec[ALL_FEATURES.index("age_66_plus")] = 1.0
    
    gender = case.get("gender", "homme")
    if gender == "homme":
        vec[ALL_FEATURES.index("gender_male")] = 1.0
    else:
        vec[ALL_FEATURES.index("gender_female")] = 1.0
    
    # ── Sévérité (basée sur le nombre de symptômes) ──
    n_symptoms = case.get("n_symptoms", 3)
    if n_symptoms <= 3:
        vec[ALL_FEATURES.index("severity_mild")] = 1.0
    elif n_symptoms <= 6:
        vec[ALL_FEATURES.index("severity_moderate")] = 1.0
    elif n_symptoms <= 9:
        vec[ALL_FEATURES.index("severity_severe")] = 1.0
    else:
        vec[ALL_FEATURES.index("severity_critical")] = 1.0
    
    # ── Systèmes corporels (déduit des symptômes) ──
    symptoms_text = case["symptoms"]
    if any(s in symptoms_text for s in ["toux", "essoufflement", "respir", "sifflement"]):
        vec[ALL_FEATURES.index("system_respiratory")] = 1.0
    if any(s in symptoms_text for s in ["douleur_thoracique", "palpitations", "cardiaque", "tachycardie"]):
        vec[ALL_FEATURES.index("system_cardiovascular")] = 1.0
    if any(s in symptoms_text for s in ["diarrhee", "vomissements", "nausees", "abdominal", "digestif"]):
        vec[ALL_FEATURES.index("system_digestive")] = 1.0
    if any(s in symptoms_text for s in ["confusion", "convulsions", "paralysie", "tete", "neurologique"]):
        vec[ALL_FEATURES.index("system_neurological")] = 1.0
    if any(s in symptoms_text for s in ["muscul", "articul", "courbature", "lombaire"]):
        vec[ALL_FEATURES.index("system_musculoskeletal")] = 1.0
    if any(s in symptoms_text for s in ["eruption", "cutanee", "demangeaison", "urticaire", "peau"]):
        vec[ALL_FEATURES.index("system_dermatological")] = 1.0
    if any(s in symptoms_text for s in ["urine", "urinaires", "miction"]):
        vec[ALL_FEATURES.index("system_urinary")] = 1.0
    if any(s in symptoms_text for s in ["gorge", "nez", "eternuement", "ORL", "bouche"]):
        vec[ALL_FEATURES.index("system_ENT")] = 1.0
    if any(s in symptoms_text for s in ["tristesse", "angoisse", "peur", "idees_noires", "isolement"]):
        vec[ALL_FEATURES.index("system_psychological")] = 1.0
    
    # ── Constantes vitales (déduites) ──
    if "fievre" in symptoms_text or "fievre_elevee" in symptoms_text:
        vec[ALL_FEATURES.index("vital_fever")] = 1.0
    if "tachycardie" in symptoms_text or "palpitations" in symptoms_text:
        vec[ALL_FEATURES.index("vital_tachycardia")] = 1.0
    if "essoufflement" in symptoms_text or "respiration_rapide" in symptoms_text:
        vec[ALL_FEATURES.index("vital_tachypnea")] = 1.0
    no_abnormal = all(s not in symptoms_text for s in ["fievre", "tachycardie", "essoufflement", 
                                                        "bradycardie", "hypotension", "chute_tension"])
    if no_abnormal:
        vec[ALL_FEATURES.index("vital_normal")] = 1.0
    
    # ── Apparition ──
    if any(s in symptoms_text for s in ["brutal", "soudain", "subit"]):
        vec[ALL_FEATURES.index("onset_sudden")] = 1.0
    elif any(s in symptoms_text for s in ["progressif", "progressif", "chronique"]):
        vec[ALL_FEATURES.index("onset_progressive")] = 1.0
    elif any(s in symptoms_text for s in ["cyclique", "intermittent"]):
        vec[ALL_FEATURES.index("onset_cyclic")] = 1.0
    
    # ── Facteurs de risque (aléatoires pour le dataset synthétique) ──
    rng = random.Random(hash(case.get("symptoms", "")) % (2**31))
    if age > 50:
        vec[ALL_FEATURES.index("risk_elderly")] = 1.0
    if rng.random() < 0.15:
        vec[ALL_FEATURES.index("risk_smoking")] = 1.0
    if rng.random() < 0.08:
        vec[ALL_FEATURES.index("risk_diabetes")] = 1.0
    
    # Normaliser
    norm = np.sqrt(np.sum(vec ** 2)) + 1e-10
    return vec / norm


# ═══════════════════════════════════════════════════════════════════
# ENCODEUR ENRICHI
# ═══════════════════════════════════════════════════════════════════

PHI = 1.618033988749895
TAU = 2.0 * np.pi
DIM = 512

def fnv1a_64(text: str) -> int:
    h = 0xCBF29CE484222325
    for ch in text:
        h ^= ord(ch)
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h

# Vecteurs de base pour chaque feature (générés une fois)
_BASES = None

def _init_bases():
    global _BASES
    if _BASES is not None:
        return
    _BASES = []
    for i, feat in enumerate(ALL_FEATURES):
        seed = fnv1a_64(f"rich_feat_{feat}")
        base = np.zeros(DIM, dtype=np.complex128)
        for d in range(DIM):
            phase = ((seed >> (d % 32)) ^ (d * 2654435761)) % 2147483647
            phase = (phase * PHI) % TAU
            base[d] = np.cos(phase) + 1j * np.sin(phase)
        base /= np.sqrt(np.sum(np.abs(base) ** 2))
        _BASES.append(base)

def enriched_encode(case: dict) -> np.ndarray:
    """Encode un cas complet en ψ ∈ ℂ⁵¹² avec features enrichies."""
    _init_bases()
    features = context_to_features(case)
    psi = np.zeros(DIM, dtype=np.complex128)
    for i, weight in enumerate(features):
        if weight > 0.001:
            psi += weight * _BASES[i]
    norm = np.sqrt(np.sum(np.abs(psi) ** 2))
    if norm > 1e-10:
        psi /= norm
    return psi

def enriched_resonance(psi_a: np.ndarray, psi_b: np.ndarray) -> float:
    return float(np.real(np.dot(np.conj(psi_a), psi_b)))


# ═══════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("ENRICHISSEMENT DES FEATURES — TEST")
    print("=" * 60)
    
    # Charger le dataset massif
    with open("data/massive_dataset.json") as f:
        dataset = json.load(f)
    
    random.seed(42)
    random.shuffle(dataset)
    train = dataset[:2000]
    test = dataset[2000:2500]
    
    print(f"Dataset : {len(dataset)} cas, test: {len(test)}")
    print(f"Features : {N_FEATURES}")
    
    # Pré-encoder toutes les maladies (une seule fois)
    print("Encodage des maladies...")
    disease_psi = {}
    for disease in set(c["diagnosis"] for c in dataset):
        # Construire un cas "moyen" pour cette maladie
        disease_cases = [c for c in train if c["diagnosis"] == disease]
        if disease_cases:
            avg_psi = np.mean([enriched_encode(c) for c in disease_cases[:20]], axis=0)
            avg_psi /= np.sqrt(np.sum(np.abs(avg_psi) ** 2)) + 1e-10
            disease_psi[disease] = avg_psi
    
    # Test
    top1 = 0
    top3 = 0
    for case in test:
        psi_patient = enriched_encode(case)
        scores = {}
        for disease, psi_d in disease_psi.items():
            scores[disease] = enriched_resonance(psi_patient, psi_d)
        sorted_scores = sorted(scores.items(), key=lambda x: -x[1])
        if sorted_scores[0][0] == case["diagnosis"]:
            top1 += 1
        if case["diagnosis"] in [s[0] for s in sorted_scores[:3]]:
            top3 += 1
    
    n = len(test)
    print(f"\n📊 Résultats (features enrichies) :")
    print(f"  Top-1 : {top1}/{n} ({top1/n*100:.1f}%)")
    print(f"  Top-3 : {top3}/{n} ({top3/n*100:.1f}%)")
    print(f"\n  Avant (16 features)  : top-1 50.0%, top-3 76.2%")
    print(f"  Après (108 features) : top-1 {top1/n*100:.1f}%, top-3 {top3/n*100:.1f}%")
    improvement = (top1/n*100 - 50.0)
    print(f"  Amélioration top-1   : {improvement:+.1f} pts")
