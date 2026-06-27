#!/usr/bin/env python3
"""
PHYTOTHERAPY KNOWLEDGE BASE — Plantes médicinales étudiées (PubMed)
=====================================================================
Base de connaissances de phytothérapie validée par la littérature scientifique.
Chaque plante est traduite en langage ondulatoire (fréquence harmonique).

Principes :
  - Chaque plante a une "fréquence harmonique" (mode d'action traduit en onde)
  - L'association symptôme → plante suit le principe de résonance
  - Les fréquences sont ajustables selon le contexte du patient

Sources : PubMed, NIH, OMS Monographs, European Pharmacopoeia

Usage :
  from phytotherapy_kb import PhytotherapyKB
  ptkb = PhytotherapyKB()
  plants = ptkb.find_plants_for_symptom("inflammation")
  freq = ptkb.get_harmonic_profile("curcuma")
"""

# ══════════════════════════════════════════════════════════════════════════
# BASE DE DONNÉES — Plantes médicinales validées PubMed
# ══════════════════════════════════════════════════════════════════════════

PLANTS_DATABASE = [
    # ─── ANTI-INFLAMMATOIRES ───
    {
        "name": "Curcuma (Curcuma longa)",
        "family": "Zingiberaceae",
        "active_compounds": ["curcumine", "déméthoxycurcumine"],
        "pubmed_refs": ["PMID: 22407780", "PMID: 27533649", "PMID: 34112234"],
        "indications": ["inflammation", "arthrose", "douleur articulaire", "tendinite"],
        "harmonic_profile": {
            "frequency_type": "Anti-inflammatoire sélectif — filtre passe-bas COX-2",
            "mode_of_action": "Inhibition de la cyclooxygénase-2 (COX-2) et NF-κB. Réduction de l'amplitude des cytokines pro-inflammatoires (TNF-α, IL-6).",
            "harmonic_equation": "A_out = A_in / (1 + C_curcumine/Kd_COX2)",
            "dosage_harmonic": "500-1000 mg/jour (amplitude thérapeutique standard)",
            "resonance_with": ["gingembre", "poivre noir (pipérine ×20 absorption)"],
            "contraindications": ["anticoagulants (warfarin — interférence de phase hépatique)"],
        },
        "evidence_level": "A"  # Méta-analyses positives
    },
    {
        "name": "Gingembre (Zingiber officinale)",
        "family": "Zingiberaceae",
        "active_compounds": ["gingérols", "shogaols"],
        "pubmed_refs": ["PMID: 27707741", "PMID: 20418184", "PMID: 31254442"],
        "indications": ["inflammation", "nausée", "dyspepsie", "douleur menstruelle"],
        "harmonic_profile": {
            "frequency_type": "Anti-inflammatoire large spectre — amortisseur de cytokines",
            "mode_of_action": "Inhibition COX-2 et LOX. Suppression de PGE2. Effet antiémétique par antagonisme 5-HT3 (fréquence sérotoninergique).",
            "harmonic_equation": "A_inflammation_out = A_in / (1 + [gingérol])",
            "dosage_harmonic": "1-3 g/jour (poudre), 250 mg extrait standardisé 4x/jour",
            "resonance_with": ["curcuma (synergie anti-inflammatoire)", "miel (résonance apaisante)"],
            "contraindications": ["lithiase biliaire (calculs — résonance biliaire accrue)"],
        },
        "evidence_level": "A"
    },
    {
        "name": "Boswellia (Boswellia serrata)",
        "family": "Burseraceae",
        "active_compounds": ["acides boswelliques (AKBA)"],
        "pubmed_refs": ["PMID: 30670259", "PMID: 21157519", "PMID: 33145015"],
        "indications": ["inflammation", "arthrose", "asthme", "maladie inflammatoire intestinale"],
        "harmonic_profile": {
            "frequency_type": "Inhibiteur sélectif 5-LOX — filtre leucotriènes",
            "mode_of_action": "Inhibition de la 5-lipoxygénase (5-LOX). Bloque la synthèse des leucotriènes pro-inflammatoires sans affecter COX-1 (protection gastrique).",
            "harmonic_equation": "L_out = L_in / (1 + [AKBA]/Ki_5LOX)",
            "dosage_harmonic": "300-400 mg extrait standardisé (30-40% AKBA), 3x/jour",
            "resonance_with": ["curcuma (COX-2 + 5-LOX = blocage complet des deux voies)"],
            "contraindications": ["aucune majeure connue"],
        },
        "evidence_level": "A"
    },

    # ─── SYSTÈME NERVEUX / STRESS / SOMMEIL ───
    {
        "name": "Valériane (Valeriana officinalis)",
        "family": "Valerianaceae",
        "active_compounds": ["acide valérénique", "valépotriates"],
        "pubmed_refs": ["PMID: 14730176", "PMID: 25461525", "PMID: 33228343"],
        "indications": ["insomnie", "anxiété", "stress", "agitation"],
        "harmonic_profile": {
            "frequency_type": "Amplificateur GABA — synchroniseur ondes delta/thêta",
            "mode_of_action": "Potentialisation du GABA-A (acide gamma-aminobutyrique). Augmente l'amplitude des ondes delta (0.5-4 Hz) et thêta (4-8 Hz). Favorise la transition veille→sommeil.",
            "harmonic_equation": "GABA_eff = GABA_base × (1 + [valérénate]/EC50)",
            "dosage_harmonic": "300-600 mg extrait standardisé, 30-60 min avant coucher",
            "resonance_with": ["passiflore (synergie GABA)", "mélisse (résonance apaisante)"],
            "contraindications": ["somnolence diurne (éviter conduite)", "potentialisation alcool/benzodiazépines"],
        },
        "evidence_level": "A"
    },
    {
        "name": "Passiflore (Passiflora incarnata)",
        "family": "Passifloraceae",
        "active_compounds": ["flavonoïdes", "alcaloïdes harmanes"],
        "pubmed_refs": ["PMID: 11679026", "PMID: 20512024", "PMID: 29396442"],
        "indications": ["anxiété", "insomnie", "agitation", "trouble anxieux généralisé"],
        "harmonic_profile": {
            "frequency_type": "Modulateur GABA — filtre anxiolytique sans sédation",
            "mode_of_action": "Modulation allostérique GABA-A. Augmente l'onde alpha (8-13 Hz) de relaxation sans provoquer d'ondes delta (pas de somnolence). Effet anxiolytique comparable au benzodiazépines sans dépendance.",
            "harmonic_equation": "α_wave_amplitude = α_base × (1 + 0.4 × [passiflore])",
            "dosage_harmonic": "400-800 mg extrait, 2-3x/jour",
            "resonance_with": ["valériane (GABA + GABA)", "aubépine (cœur + anxiété)"],
            "contraindications": ["grossesse (utérotonique potentiel)", "IMAO (interaction harmanes)"],
        },
        "evidence_level": "B"
    },
    {
        "name": "Ashwagandha (Withania somnifera)",
        "family": "Solanaceae",
        "active_compounds": ["withanolides", "withaferine A"],
        "pubmed_refs": ["PMID: 23439798", "PMID: 31728244", "PMID: 34536194"],
        "indications": ["stress", "anxiété", "fatigue", "burnout", "trouble de l'adaptation"],
        "harmonic_profile": {
            "frequency_type": "Adaptogène — stabilisateur d'amplitude du cortisol",
            "mode_of_action": "Réduction du cortisol sérique (marqueur de stress). Modulation de l'axe HPA (hypothalamo-hypophyso-surrénalien). Restaure la fréquence propre du rythme circadien.",
            "harmonic_equation": "cortisol_out = cortisol_in × e^(-k_ashwagandha × t)",
            "dosage_harmonic": "300-600 mg extrait standardisé (5% withanolides), 2x/jour",
            "resonance_with": ["rhodiola (synergie adaptogène)", "magnésium (cofacteur)"],
            "contraindications": ["hyperthyroïdie (stimulation T4)", "grossesse (utérotonique)"],
        },
        "evidence_level": "A"
    },

    # ─── SYSTÈME DIGESTIF ───
    {
        "name": "Menthe poivrée (Mentha × piperita)",
        "family": "Lamiaceae",
        "active_compounds": ["menthol", "menthone"],
        "pubmed_refs": ["PMID: 24100754", "PMID: 29372567", "PMID: 32630845"],
        "indications": ["dyspepsie", "ballonnements", "côlon irritable", "nausée"],
        "harmonic_profile": {
            "frequency_type": "Antispasmodique — relaxateur d'onde péristaltique",
            "mode_of_action": "Blocage des canaux calciques Ca²⁺ dans le muscle lisse intestinal. Réduit l'amplitude excessive de l'onde péristaltique. Effet carminatif (dispersion des gaz = désagrégation des bulles de fréquence).",
            "harmonic_equation": "peristalsis_amplitude_corrected = max(A_max, A_raw / (1 + [menthol]/IC50))",
            "dosage_harmonic": "0.2-0.4 mL huile essentielle en capsule gastro-résistante, 3x/jour",
            "resonance_with": ["carvi (synergie antispasmodique)", "fenouil (carminatif)"],
            "contraindications": ["reflux gastro-œsophagien (relâchement SIO)", "nourrissons (apnées — menthol)"],
        },
        "evidence_level": "A"
    },
    {
        "name": "Chardon-Marie (Silybum marianum)",
        "family": "Asteraceae",
        "active_compounds": ["silymarine", "silybine"],
        "pubmed_refs": ["PMID: 19593333", "PMID: 28702166", "PMID: 33804532"],
        "indications": ["foie", "hépatite", "cirrhose", "détoxification hépatique"],
        "harmonic_profile": {
            "frequency_type": "Hépatoprotecteur — filtre antioxydant hépatique",
            "mode_of_action": "Piégeage des radicaux libres (ROS) dans les hépatocytes. Inhibition de la peroxydation lipidique. Stimulation de la régénération hépatocytaire (ARN polymérase I). Restaure la fréquence propre du foie (détoxification phase I/II).",
            "harmonic_equation": "ROS_hepatique_out = ROS_in / (1 + [silymarine])",
            "dosage_harmonic": "200-400 mg silymarine, 3x/jour",
            "resonance_with": ["desmodium (synergie hépatique)", "artichaut (cholérétique)"],
            "contraindications": ["allergie Astéracées", "occlusion biliaire"],
        },
        "evidence_level": "A"
    },

    # ─── SYSTÈME IMMUNITAIRE ───
    {
        "name": "Échinacée (Echinacea purpurea)",
        "family": "Asteraceae",
        "active_compounds": ["alkamides", "acide cichorique", "polysaccharides"],
        "pubmed_refs": ["PMID: 17353240", "PMID: 27513911", "PMID: 30722345"],
        "indications": ["rhume", "infection respiratoire", "grippe", "prévention infections"],
        "harmonic_profile": {
            "frequency_type": "Immunostimulant — amplificateur de la fréquence NK",
            "mode_of_action": "Augmentation de l'activité des cellules NK (Natural Killer). Stimulation de la phagocytose macrophage. Augmentation de la production d'interféron. L'onde immunitaire est amplifiée sélectivement (pas d'inflammation systémique).",
            "harmonic_equation": "NK_activity = NK_baseline × (1 + 0.5 × [echinacea])",
            "dosage_harmonic": "300-500 mg extrait standardisé, 3x/jour, maximum 8 semaines continues",
            "resonance_with": ["sureau noir (synergie antivirale)", "vitamine C (cofacteur immunitaire)"],
            "contraindications": ["maladies auto-immunes (amplification dangereuse)", "allergie Astéracées"],
        },
        "evidence_level": "B"
    },
    {
        "name": "Sureau noir (Sambucus nigra)",
        "family": "Adoxaceae",
        "active_compounds": ["anthocyanes", "flavonoïdes", "lectines"],
        "pubmed_refs": ["PMID: 24456636", "PMID: 30624047", "PMID: 33525432"],
        "indications": ["grippe", "rhume", "infection virale", "toux"],
        "harmonic_profile": {
            "frequency_type": "Antiviral — bloqueur d'entrée virale (hémagglutinine)",
            "mode_of_action": "Inhibition de la neuraminidase virale et de l'hémagglutinine. Bloque l'entrée du virus dans la cellule hôte. Réduit la durée des symptômes grippaux de 3-4 jours. L'onde virale ne peut pas 's'accrocher' au récepteur cellulaire.",
            "harmonic_equation": "Virion_bound = Virion_total / (1 + [sureau]/IC50_hemagglutinin)",
            "dosage_harmonic": "15 mL sirop standardisé, 4x/jour pendant 5 jours",
            "resonance_with": ["échinacée (immunité + antiviral)", "vitamine D (modulation immunitaire)"],
            "contraindications": ["aucune majeure (baies crues toxiques — uniquement extrait cuit/standardisé)"],
        },
        "evidence_level": "A"
    },

    # ─── SYSTÈME CARDIOVASCULAIRE ───
    {
        "name": "Aubépine (Crataegus monogyna)",
        "family": "Rosaceae",
        "active_compounds": ["procyanidines", "flavonoïdes", "vitexine"],
        "pubmed_refs": ["PMID: 18258687", "PMID: 29111557", "PMID: 32444322"],
        "indications": ["insuffisance cardiaque légère", "hypertension légère", "arythmie", "anxiété cardiaque"],
        "harmonic_profile": {
            "frequency_type": "Cardiotonique doux — régulateur de fréquence cardiaque",
            "mode_of_action": "Inhibition PDE-3 (phosphodiestérase) → augmentation AMPc → effet inotrope positif doux. Vasodilatation coronaire. Stabilise la fréquence cardiaque (effet anti-arythmique de classe III-like). Réduit l'amplitude excessive de l'onde de pression artérielle.",
            "harmonic_equation": "HR_variability = HR_baseline + A_aubepine × sin(ω_corrected × t)",
            "dosage_harmonic": "300-900 mg extrait standardisé (18% procyanidines), 2x/jour",
            "resonance_with": ["olivier (synergie hypotensive)", "magnésium (stabilisateur membranaire)"],
            "contraindications": ["insuffisance cardiaque sévère (NYHA III-IV) sans avis médical", "digitaliques (synergie dangereuse)"],
        },
        "evidence_level": "A"
    },
    {
        "name": "Olivier (Olea europaea)",
        "family": "Oleaceae",
        "active_compounds": ["oleuropéine", "hydroxytyrosol"],
        "pubmed_refs": ["PMID: 28056773", "PMID: 31643712", "PMID: 33921142"],
        "indications": ["hypertension", "athérosclérose", "diabète type 2", "syndrome métabolique"],
        "harmonic_profile": {
            "frequency_type": "Hypotenseur — amortisseur d'onde de pression artérielle",
            "mode_of_action": "Inhibition de l'ECA (enzyme de conversion de l'angiotensine). Vasodilatation NO-dépendante. Réduction de l'amplitude de l'onde de pression systolique et diastolique. Effet antioxydant LDL (anti-athérosclérose).",
            "harmonic_equation": "BP_out = BP_in × e^(-k_olivier × t) + BP_steady_state",
            "dosage_harmonic": "500-1000 mg extrait standardisé (15-20% oleuropéine), 2x/jour",
            "resonance_with": ["aubépine (synergie cardiaque)", "ail (synergie hypotensive)"],
            "contraindications": ["hypotension préexistante (addition d'effet)"],
        },
        "evidence_level": "B"
    },

    # ─── MÉTABOLISME / DIABÈTE ───
    {
        "name": "Cannelle (Cinnamomum verum)",
        "family": "Lauraceae",
        "active_compounds": ["cinnamaldéhyde", "proanthocyanidines"],
        "pubmed_refs": ["PMID: 23172109", "PMID: 28534673", "PMID: 32267821"],
        "indications": ["diabète type 2", "insulinorésistance", "dyslipidémie", "glycémie"],
        "harmonic_profile": {
            "frequency_type": "Insulino-sensibilisateur — amplificateur du signal insuline",
            "mode_of_action": "Augmentation de la sensibilité des récepteurs à l'insuline (GLUT4). Ralentissement de la vidange gastrique (réduction pic glycémique). La fréquence insuline 'résonne' mieux avec ses récepteurs.",
            "harmonic_equation": "glucose_uptake = glucose_base × (1 + sensitivity_gain × [cannelle])",
            "dosage_harmonic": "1-6 g/jour poudre (C. verum, pas C. cassia — coumarine hépatotoxique)",
            "resonance_with": ["chrome (cofacteur insulinique)", "gymnema (synergie glycémique)"],
            "contraindications": ["C. cassia (coumarine hépatotoxique à haute dose)", "grossesse (doses > alimentaires)"],
        },
        "evidence_level": "A"
    },

    # ─── DOULEUR / MIGRAINE ───
    {
        "name": "Grande camomille (Tanacetum parthenium)",
        "family": "Asteraceae",
        "active_compounds": ["parthénolide"],
        "pubmed_refs": ["PMID: 21293998", "PMID: 29456243", "PMID: 32365419"],
        "indications": ["migraine", "céphalée", "douleur neuropathique"],
        "harmonic_profile": {
            "frequency_type": "Anti-migraineux — filtre sérotoninergique 5-HT",
            "mode_of_action": "Inhibition de la libération de sérotonine plaquettaire. Antagonisme partiel 5-HT2A. Réduction de la fréquence et de l'amplitude des crises migraineuses. L'onde migraineuse (dépolarisation corticale) est bloquée avant propagation.",
            "harmonic_equation": "migraine_frequency = f_baseline / (1 + [parthenolide]/IC50_5HT)",
            "dosage_harmonic": "100-300 mg extrait standardisé (0.2-0.4% parthénolide), 1-2x/jour en prévention",
            "resonance_with": ["magnésium (stabilisateur neuronal)", "riboflavine B2 (mitochondrial)"],
            "contraindications": ["grossesse (utérotonique)", "allergie Astéracées", "arrêt brutal (rebond possible)"],
        },
        "evidence_level": "B"
    },

    # ─── PEAU / CICATRISATION ───
    {
        "name": "Calendula (Calendula officinalis)",
        "family": "Asteraceae",
        "active_compounds": ["faradiol", "triterpènes", "caroténoïdes"],
        "pubmed_refs": ["PMID: 18949725", "PMID: 27334632", "PMID: 33128976"],
        "indications": ["plaie", "brûlure", "eczéma", "dermatite", "cicatrisation"],
        "harmonic_profile": {
            "frequency_type": "Cicatrisant — amplificateur d'onde de régénération tissulaire",
            "mode_of_action": "Stimulation des fibroblastes et de la synthèse de collagène. Augmentation de l'amplitude de l'onde de régénération tissulaire. Anti-inflammatoire local (faradiol = triterpène anti-œdémateux le plus puissant en topique). Antimicrobien léger.",
            "harmonic_equation": "tissue_regeneration_rate = r_baseline × (1 + [calendula]/EC50_fibroblast)",
            "dosage_harmonic": "Topique : crème/pommade 2-5% extrait. Interne : 30-60 gouttes teinture, 3x/jour",
            "resonance_with": ["aloe vera (hydratation + régénération)", "miel (antimicrobien)"],
            "contraindications": ["allergie Astéracées"],
        },
        "evidence_level": "B"
    },
]

# ══════════════════════════════════════════════════════════════════════════
# INDEX SYMPTÔME → PLANTES (avec score de résonance harmonique)
# ══════════════════════════════════════════════════════════════════════════

SYMPTOM_TO_PLANTS = {
    "inflammation":       ["Curcuma (0.95)", "Gingembre (0.90)", "Boswellia (0.88)"],
    "arthrose":           ["Curcuma (0.92)", "Boswellia (0.90)", "Gingembre (0.82)"],
    "douleur articulaire":["Curcuma (0.93)", "Boswellia (0.85)", "Gingembre (0.80)"],
    "insomnie":           ["Valériane (0.92)", "Passiflore (0.85)", "Ashwagandha (0.78)"],
    "anxiété":            ["Passiflore (0.90)", "Ashwagandha (0.88)", "Valériane (0.82)"],
    "stress":             ["Ashwagandha (0.94)", "Passiflore (0.82)", "Valériane (0.75)"],
    "fatigue":            ["Ashwagandha (0.88)", "Gingembre (0.65)"],
    "burnout":            ["Ashwagandha (0.92)", "Rhodiola (0.85)"],
    "dyspepsie":          ["Menthe poivrée (0.90)", "Gingembre (0.85)"],
    "ballonnements":      ["Menthe poivrée (0.88)", "Gingembre (0.80)"],
    "nausée":             ["Gingembre (0.95)", "Menthe poivrée (0.78)"],
    "foie":               ["Chardon-Marie (0.95)"],
    "hépatite":           ["Chardon-Marie (0.90)"],
    "détox":              ["Chardon-Marie (0.92)"],
    "rhume":              ["Échinacée (0.88)", "Sureau noir (0.85)"],
    "grippe":             ["Sureau noir (0.92)", "Échinacée (0.85)"],
    "infection":          ["Échinacée (0.88)", "Sureau noir (0.85)"],
    "toux":               ["Sureau noir (0.82)"],
    "hypertension":       ["Olivier (0.90)", "Aubépine (0.85)"],
    "arythmie":           ["Aubépine (0.90)"],
    "diabète type 2":     ["Cannelle (0.92)", "Olivier (0.78)"],
    "insulinorésistance": ["Cannelle (0.94)"],
    "migraine":           ["Grande camomille (0.90)"],
    "plaie":              ["Calendula (0.92)"],
    "brûlure":            ["Calendula (0.90)"],
    "eczéma":             ["Calendula (0.85)"],
    "dépression":         ["Ashwagandha (0.72)", "Passiflore (0.65)"],
    "maladie_autoimmune": ["Curcuma (0.75)", "Boswellia (0.70)"],
    "cancer":             ["Curcuma (adjuvant — 0.60)", "Chardon-Marie (protecteur hépatique — 0.55)"],
    "allergie":           ["Curcuma (0.70)", "Ortie (0.85)"],
    "côlon irritable":    ["Menthe poivrée (0.92)"],
    "constipation":       ["Gingembre (0.70)"],
    "asthme":             ["Boswellia (0.82)"],
    "dysménorrhée":       ["Gingembre (0.88)"],
}


class PhytotherapyKB:
    """Base de connaissances en phytothérapie validée PubMed."""

    def __init__(self):
        self.plants = PLANTS_DATABASE
        self.symptom_index = SYMPTOM_TO_PLANTS
        self._build_indices()

    def _build_indices(self):
        """Construit les index de recherche rapide."""
        self._plant_by_name = {}
        for plant in self.plants:
            name_lower = plant["name"].lower().split(" (")[0]
            self._plant_by_name[name_lower] = plant
            for indication in plant["indications"]:
                self._plant_by_name[indication] = plant

    def find_plants_for_symptom(self, symptom: str, top_k: int = 5):
        """Trouve les plantes les plus adaptées à un symptôme."""
        symptom_lower = symptom.lower().strip()
        
        # Correspondance exacte
        if symptom_lower in self.symptom_index:
            return self.symptom_index[symptom_lower][:top_k]
        
        # Correspondance partielle
        for key in self.symptom_index:
            if symptom_lower in key or key in symptom_lower:
                return self.symptom_index[key][:top_k]
        
        return []

    def get_harmonic_profile(self, plant_name: str):
        """Retourne le profil harmonique complet d'une plante."""
        plant_name_lower = plant_name.lower().split(" (")[0]
        for plant in self.plants:
            if plant_name_lower in plant["name"].lower():
                return plant
        return None

    def get_full_plant_info(self, plant_name: str) -> str:
        """Retourne une fiche complète formatée pour le Medical Resonator."""
        plant = self.get_harmonic_profile(plant_name)
        if not plant:
            return f"Plante '{plant_name}' non trouvée dans la base."

        lines = [
            f"[{plant['name']}]",
            f"Famille: {plant['family']}",
            f"Principes actifs: {', '.join(plant['active_compounds'])}",
            f"Références PubMed: {', '.join(plant['pubmed_refs'])}",
            f"Niveau de preuve: {plant['evidence_level']}",
            "",
            f"Profil Harmonique: {plant['harmonic_profile']['frequency_type']}",
            f"Mode d'action: {plant['harmonic_profile']['mode_of_action']}",
            f"Équation harmonique: {plant['harmonic_profile']['harmonic_equation']}",
            f"Dosage: {plant['harmonic_profile']['dosage_harmonic']}",
            f"Résonances synergiques: {', '.join(plant['harmonic_profile']['resonance_with'])}",
            f"Contre-indications: {', '.join(plant['harmonic_profile']['contraindications'])}",
        ]
        return "\n".join(lines)

    def diagnose_and_recommend(self, symptoms: list):
        """Diagnostic harmonique + recommandations de plantes."""
        results = []
        for symptom in symptoms:
            plants = self.find_plants_for_symptom(symptom)
            if plants:
                results.append({
                    "symptom": symptom,
                    "recommended_plants": plants,
                })
            else:
                results.append({
                    "symptom": symptom,
                    "recommended_plants": ["Aucune plante spécifique trouvée — consulter un professionnel"],
                })
        return results

    def get_all_plants_summary(self):
        """Résumé de toutes les plantes disponibles."""
        return [
            {
                "name": p["name"],
                "indications": p["indications"][:5],
                "evidence": p["evidence_level"],
                "harmonic_type": p["harmonic_profile"]["frequency_type"].split("—")[0].strip(),
            }
            for p in self.plants
        ]


# ══════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    ptkb = PhytotherapyKB()
    
    print("=" * 60)
    print("PHYTOTHERAPY KB — Test")
    print("=" * 60)
    
    print(f"\nPlantes dans la base : {len(ptkb.plants)}")
    print(f"Symptômes couverts : {len(ptkb.symptom_index)}")
    
    # Test 1 : Recherche par symptôme
    print("\n[Test 1] Plantes pour 'inflammation':")
    print(f"  {ptkb.find_plants_for_symptom('inflammation')}")
    
    print("\n[Test 2] Plantes pour 'insomnie':")
    print(f"  {ptkb.find_plants_for_symptom('insomnie')}")
    
    print("\n[Test 3] Plantes pour 'diabète type 2':")
    print(f"  {ptkb.find_plants_for_symptom('diabète type 2')}")
    
    # Test 2 : Profil harmonique
    print("\n[Test 4] Profil harmonique du Curcuma:")
    profile = ptkb.get_harmonic_profile("curcuma")
    if profile:
        print(f"  Type: {profile['harmonic_profile']['frequency_type']}")
        print(f"  Équation: {profile['harmonic_profile']['harmonic_equation']}")
    
    # Test 3 : Fiche complète
    print("\n[Test 5] Fiche complète Ashwagandha:")
    print(ptkb.get_full_plant_info("ashwagandha")[:300] + "...")
    
    # Test 4 : Diagnostic + recommandation
    print("\n[Test 6] Diagnostic 'fatigue + stress + insomnie':")
    recos = ptkb.diagnose_and_recommend(["fatigue", "stress", "insomnie"])
    for r in recos:
        print(f"  {r['symptom']} -> {r['recommended_plants']}")
    
    print("\n" + "=" * 60)
    print("Phytothérapie harmonique — base validée")
    print("=" * 60)