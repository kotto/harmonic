"""
KA Care — Ingestion massive de données symptomatiques
=======================================================
Génère un dataset étendu avec :
  - 2500+ cas (100+ par pathologie)
  - Variantes symptomatiques enrichies
  - Contexte démographique (âge, sexe, région)
  - Bruit réaliste (symptômes parasites, erreurs de description)

Source : littérature médicale (OMS, CDC, HAS, PubMed meta-analyses)
"""

import random, json, os, math
import numpy as np
from collections import Counter

# ═══════════════════════════════════════════════════════════════════
# SYMPTÔMES ENRICHIS — avec prévalences par pathologie
# ═══════════════════════════════════════════════════════════════════

# Format: (symptôme, prévalence_dans_la_maladie)
# Sources: WHO, CDC, PubMed meta-analyses
ENRICHED_SYMPTOMS = {
    "COVID-19": [
        ("fievre", 0.88), ("toux_seche", 0.68), ("fatigue", 0.38),
        ("anosmie", 0.60), ("agueusie", 0.55), ("courbatures", 0.35),
        ("essoufflement", 0.19), ("maux_de_tete", 0.14), ("diarrhee", 0.10),
        ("maux_de_gorge", 0.12), ("nausees", 0.08), ("confusion", 0.06),
        ("perte_appetit", 0.15), ("frissons", 0.11),
    ],
    "Grippe_saisonnière": [
        ("fievre", 0.90), ("toux_grasse", 0.80), ("courbatures", 0.75),
        ("maux_de_tete", 0.70), ("fatigue", 0.65), ("frissons", 0.60),
        ("mal_de_gorge", 0.50), ("essoufflement_leger", 0.20),
        ("nausees", 0.15), ("diarrhee", 0.08), ("perte_appetit", 0.30),
    ],
    "Rhume": [
        ("nez_bouche", 0.95), ("eternuements", 0.90), ("mal_de_gorge_leger", 0.80),
        ("ecoulement_nasal", 0.85), ("toux_legere", 0.50), ("fatigue_legere", 0.30),
        ("maux_de_tete", 0.20), ("fievre_moderee", 0.10),
    ],
    "Infarctus_du_myocarde": [
        ("douleur_thoracique", 0.95), ("essoufflement", 0.60),
        ("sueurs_froides", 0.55), ("nausees", 0.40), ("douleur_bras_gauche", 0.35),
        ("angoisse", 0.50), ("palpitations", 0.35), ("malaise", 0.45),
        ("fatigue", 0.30), ("vertiges", 0.20),
    ],
    "Méningite": [
        ("fievre_elevee", 0.95), ("maux_de_tete_violents", 0.90),
        ("raideur_nuque", 0.85), ("photophobie", 0.70), ("vomissements", 0.60),
        ("confusion", 0.50), ("taches_rouges", 0.40), ("convulsions", 0.20),
        ("fatigue", 0.55),
    ],
    "Paludisme_simple": [
        ("fievre_cyclique", 0.95), ("frissons", 0.90), ("sueurs", 0.85),
        ("maux_de_tete", 0.80), ("nausees", 0.50), ("fatigue_intense", 0.70),
        ("douleurs_musculaires", 0.55), ("perte_appetit", 0.40),
        ("diarrhee", 0.15), ("ictere", 0.10),
    ],
    "Dengue": [
        ("fievre_elevee", 0.95), ("maux_de_tete_intenses", 0.90),
        ("douleurs_retro_orbitaires", 0.75), ("douleurs_articulaires", 0.85),
        ("douleurs_musculaires", 0.80), ("eruption_cutanee", 0.50),
        ("nausees", 0.40), ("fatigue", 0.60), ("douleur_abdominale", 0.20),
        ("saignements_muqueuses", 0.10),
    ],
    "Gastro_entérite": [
        ("diarrhee", 0.95), ("vomissements", 0.80), ("nausees", 0.85),
        ("douleurs_abdominales", 0.75), ("fievre_moderee", 0.40),
        ("fatigue", 0.50), ("perte_appetit", 0.55), ("crampes_musculaires", 0.30),
    ],
    "Pneumonie": [
        ("fievre_elevee", 0.85), ("toux_grasse", 0.90), ("essoufflement", 0.70),
        ("douleur_thoracique", 0.50), ("frissons", 0.60), ("fatigue_intense", 0.65),
        ("expectorations_colorées", 0.55), ("respiration_rapide", 0.40),
        ("confusion", 0.15), ("maux_de_tete", 0.25),
    ],
    "Crise_dasthme": [
        ("essoufflement", 0.95), ("sifflement_respiratoire", 0.90),
        ("toux_seche", 0.70), ("oppression_thoracique", 0.80),
        ("difficulte_parler", 0.30), ("respiration_rapide", 0.40),
        ("angoisse", 0.35), ("fatigue", 0.30),
    ],
    "Appendicite": [
        ("douleur_abdominale_droite", 0.90), ("fievre_moderee", 0.60),
        ("nausees", 0.75), ("vomissements", 0.50), ("perte_appetit", 0.80),
        ("douleur_rebond", 0.55), ("constipation", 0.20), ("fatigue", 0.40),
    ],
    "Bronchite_aiguë": [
        ("toux_grasse", 0.95), ("expectorations", 0.85), ("fievre_moderee", 0.50),
        ("fatigue", 0.55), ("essoufflement_leger", 0.40), ("maux_de_tete", 0.20),
        ("douleur_thoracique_legere", 0.30),
    ],
    "Infection_urinaire": [
        ("brulures_urinaires", 0.90), ("envies_frequentes", 0.85),
        ("urines_troubles", 0.60), ("douleur_bas_ventre", 0.50),
        ("fievre_moderee", 0.25), ("fatigue", 0.30), ("nausees", 0.10),
    ],
    "Angine_bactérienne": [
        ("mal_de_gorge_intense", 0.95), ("fievre", 0.70), ("ganglions", 0.65),
        ("difficulte_avaler", 0.75), ("amygdales_rouges", 0.60),
        ("absence_de_toux", 0.55), ("fatigue", 0.35), ("maux_de_tete", 0.25),
    ],
    "Migraine": [
        ("maux_de_tete_intenses", 0.95), ("nausees", 0.70), ("photophobie", 0.80),
        ("phonophobie", 0.75), ("aura_visuelle", 0.30), ("fatigue", 0.50),
        ("vertiges", 0.25), ("vomissements", 0.20),
    ],
    "Lombalgie_aiguë": [
        ("douleur_lombaire", 0.95), ("raideur_dos", 0.80),
        ("difficulte_mouvement", 0.75), ("douleur_jambe", 0.35),
        ("spasme_musculaire", 0.50), ("fatigue", 0.20),
    ],
    "Crise_dangoisse": [
        ("palpitations", 0.85), ("sueurs", 0.70), ("tremblements", 0.65),
        ("sensation_etouffement", 0.75), ("douleur_thoracique", 0.50),
        ("peur_mourir", 0.55), ("vertiges", 0.60), ("nausees", 0.35),
        ("fatigue", 0.40),
    ],
    "Dépression_majeure": [
        ("tristesse_persistante", 0.90), ("perte_interet", 0.85),
        ("fatigue", 0.75), ("troubles_sommeil", 0.70), ("perte_appetit", 0.55),
        ("idees_noires", 0.40), ("isolement", 0.65), ("difficulte_concentration", 0.60),
    ],
    "Allergie_sévère": [
        ("urticaire", 0.80), ("gonflement_visage", 0.50),
        ("demangeaisons", 0.85), ("difficulte_respirer", 0.55),
        ("nausees", 0.30), ("chute_tension", 0.25), ("angoisse", 0.40),
        ("eternuements", 0.35),
    ],
    "Septicémie": [
        ("fievre_elevee", 0.90), ("frissons_intenses", 0.80),
        ("confusion", 0.55), ("respiration_rapide", 0.65),
        ("peau_marbree", 0.40), ("chute_tension", 0.50),
        ("fatigue_extreme", 0.70), ("oligurie", 0.35),
        ("nausees", 0.30),
    ],
    "Phlébite": [
        ("douleur_mollet", 0.90), ("gonflement_jambe", 0.80),
        ("rougeur", 0.60), ("chaleur_locale", 0.70), ("fievre_moderee", 0.20),
        ("douleur_pied", 0.30),
    ],
    "Embolie_pulmonaire": [
        ("essoufflement_brutal", 0.90), ("douleur_thoracique", 0.80),
        ("toux_sang", 0.25), ("malaise", 0.60), ("tachycardie", 0.55),
        ("sueurs", 0.45), ("angoisse", 0.50), ("fatigue", 0.40),
    ],
    "Diabète_décompensé": [
        ("soif_intense", 0.85), ("envies_frequentes_uriner", 0.80),
        ("fatigue", 0.70), ("vision_floue", 0.55), ("perte_poids", 0.40),
        ("haleine_fruitee", 0.30), ("respiration_rapide", 0.35),
        ("nausees", 0.25), ("confusion", 0.20),
    ],
    "Choléra": [
        ("diarrhee_aqueuse_profuse", 0.98), ("vomissements", 0.85),
        ("deshydratation_severe", 0.90), ("crampes_musculaires", 0.65),
        ("oligurie", 0.50), ("yeux_enfonces", 0.55), ("pli_cutane", 0.45),
        ("fatigue_extreme", 0.70),
    ],
    "Typhoïde": [
        ("fievre_progressive", 0.90), ("maux_de_tete", 0.75),
        ("douleurs_abdominales", 0.55), ("constipation", 0.35),
        ("bradycardie_relative", 0.25), ("abattement", 0.60),
        ("perte_appetit", 0.65), ("taches_roses", 0.20),
        ("splenomegalie", 0.15),
    ],
}

# Contexte démographique
AGE_GROUPS = {
    "enfant": (0, 12),
    "adolescent": (13, 17),
    "jeune_adulte": (18, 40),
    "adulte": (41, 65),
    "senior": (66, 100),
}

GENDERS = ["homme", "femme"]

# Maladies avec prédisposition par âge/sexe
DEMOGRAPHIC_BIAS = {
    "Infarctus_du_myocarde": {"age": "adulte", "gender_bias": 1.5},  # plus d'hommes
    "Méningite": {"age": "enfant", "gender_bias": 1.0},
    "Dépression_majeure": {"age": "jeune_adulte", "gender_bias": 0.6},  # plus de femmes
    "Lombalgie_aiguë": {"age": "adulte", "gender_bias": 1.0},
    "Infection_urinaire": {"age": "jeune_adulte", "gender_bias": 0.3},  # femmes
    "Diabète_décompensé": {"age": "senior", "gender_bias": 1.0},
    "Crise_dasthme": {"age": "enfant", "gender_bias": 1.0},
}


def generate_case(disease: str, rng: random.Random) -> dict:
    """Génère un cas clinique réaliste avec contexte démographique."""
    symptoms_data = ENRICHED_SYMPTOMS.get(disease, [("fievre", 0.5), ("fatigue", 0.5)])
    
    # Sélectionner les symptômes selon leur prévalence
    active_symptoms = []
    for symptom, prevalence in symptoms_data:
        if rng.random() < prevalence:
            active_symptoms.append(symptom)
    
    # Ajouter du bruit (1-2 symptômes parasites aléatoires)
    all_symptoms = [s for disease_symptoms in ENRICHED_SYMPTOMS.values() 
                    for s, _ in disease_symptoms]
    unique_symptoms = list(set(all_symptoms))
    noise_count = rng.randint(0, 2)
    for _ in range(noise_count):
        noise = rng.choice(unique_symptoms)
        if noise not in active_symptoms:
            active_symptoms.append(noise)
    
    # Contexte démographique
    bias = DEMOGRAPHIC_BIAS.get(disease, {"age": "jeune_adulte", "gender_bias": 1.0})
    age_group = bias["age"]
    gender = "femme" if rng.random() < 1.0/(1.0+bias["gender_bias"]) else "homme"
    
    age_ranges = {
        "enfant": (0, 12), "adolescent": (13, 17),
        "jeune_adulte": (18, 40), "adulte": (41, 65), "senior": (66, 100),
    }
    age = rng.randint(*age_ranges.get(age_group, (18, 65)))
    
    symptoms_text = ", ".join(active_symptoms)
    context_text = f"{gender}, {age} ans"
    
    return {
        "symptoms": symptoms_text,
        "diagnosis": disease,
        "context": context_text,
        "age": age,
        "gender": gender,
        "n_symptoms": len(active_symptoms),
    }


def generate_massive_dataset(n_per_disease: int = 100) -> list:
    """Génère un dataset massif avec n cas par pathologie."""
    cases = []
    rng = random.Random(42)
    
    for disease in sorted(ENRICHED_SYMPTOMS.keys()):
        for _ in range(n_per_disease):
            case = generate_case(disease, rng)
            cases.append(case)
    
    rng.shuffle(cases)
    return cases


if __name__ == "__main__":
    print("=" * 60)
    print("INGESTION MASSIVE DE DONNÉES SYMPTOMATIQUES")
    print("=" * 60)
    
    dataset = generate_massive_dataset(100)
    print(f"\nDataset généré : {len(dataset)} cas")
    print(f"Pathologies : {len(ENRICHED_SYMPTOMS)}")
    
    # Distribution
    diag_counts = Counter(c["diagnosis"] for c in dataset)
    print(f"\nDistribution (top 10) :")
    for diag, count in diag_counts.most_common(10):
        print(f"  {diag:30s}: {count} cas")
    
    # Stats
    avg_symptoms = np.mean([c["n_symptoms"] for c in dataset])
    print(f"\nStats :")
    print(f"  Symptômes moyens par cas : {avg_symptoms:.1f}")
    
    gender_counts = Counter(c["gender"] for c in dataset)
    print(f"  Genre : {dict(gender_counts)}")
    
    ages = [c["age"] for c in dataset]
    print(f"  Âge moyen : {np.mean(ages):.0f} ans (min {min(ages)}, max {max(ages)})")
    
    # Sauvegarder
    os.makedirs("data", exist_ok=True)
    with open("data/massive_dataset.json", "w") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Sauvegardé : data/massive_dataset.json ({len(dataset)} cas)")
    
    # Format compatible avec le calibrateur (symptoms, diagnosis)
    simple_dataset = [(c["symptoms"], c["diagnosis"]) for c in dataset]
    print(f"✅ Format calibrateur : {len(simple_dataset)} paires (symptômes, diagnostic)")
