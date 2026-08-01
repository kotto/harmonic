"""
💉 enrich_holograms.py — Enrichissement des domaines faibles
=============================================================
Ajoute des faits médicaux standard (OMS/PEV/CNHU) aux domaines
sous-alimentés puis ré-entraîne les hologrammes concernés.

Domaines cibles (faits < 200) :
  VACCINATION (37), PALUDISME (62), NUTRITION (91), PHYTOTHERAPIE (89),
  VIH_TB (113), MNT (120), MERE_ENFANT (127), PEDIATRIE (146),
  SANTE_MENTALE (149), CHRONIQUES (170)

Usage : python enrich_holograms.py [--all | --domain VACCINATION ...]
"""

import sys, json, time
from pathlib import Path

_ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE))

from train_medical_holograms import train_hologram

HOLO_DIR = _ENGINE / "data" / "medical_holograms"

# ════════════════════════════════════════════════════════════════
# FAITS D'ENRICHISSEMENT (format : (s, r, o))
# ════════════════════════════════════════════════════════════════

ENRICHMENT = {
    'VACCINATION': [
        # Calendrier PEV (Programme Élargi de Vaccination)
        ('BCG', 'age_recommande', 'à la naissance', 'VACCINATION'),
        ('BCG', 'voie', 'intradermique, bras droit', 'VACCINATION'),
        ('BCG', 'maladies_previent', 'tuberculose', 'VACCINATION'),
        ('VPO 0', 'age_recommande', 'à la naissance', 'VACCINATION'),
        ('VPO 0', 'maladies_previent', 'poliomyélite', 'VACCINATION'),
        ('DTC-HepB-Hib 1', 'age_recommande', '6 semaines', 'VACCINATION'),
        ('DTC-HepB-Hib 1', 'maladies_previent', 'diphtérie, tétanos, coqueluche, hépatite B, Hib', 'VACCINATION'),
        ('DTC-HepB-Hib 2', 'age_recommande', '10 semaines', 'VACCINATION'),
        ('DTC-HepB-Hib 3', 'age_recommande', '14 semaines', 'VACCINATION'),
        ('VPI', 'age_recommande', '14 semaines', 'VACCINATION'),
        ('VPI', 'maladies_previent', 'poliomyélite', 'VACCINATION'),
        ('VPO 1', 'age_recommande', '6 semaines', 'VACCINATION'),
        ('VPO 2', 'age_recommande', '10 semaines', 'VACCINATION'),
        ('VPO 3', 'age_recommande', '14 semaines', 'VACCINATION'),
        ('Pneumocoque 1', 'age_recommande', '6 semaines', 'VACCINATION'),
        ('Pneumocoque 2', 'age_recommande', '10 semaines', 'VACCINATION'),
        ('Pneumocoque 3', 'age_recommande', '14 semaines', 'VACCINATION'),
        ('Pneumocoque', 'maladies_previent', 'pneumonie, méningite à pneumocoque', 'VACCINATION'),
        ('Rota 1', 'age_recommande', '6 semaines', 'VACCINATION'),
        ('Rota 2', 'age_recommande', '10 semaines', 'VACCINATION'),
        ('Rota', 'maladies_previent', 'diarrhée à rotavirus', 'VACCINATION'),
        ('Rougeole 1', 'age_recommande', '9 mois', 'VACCINATION'),
        ('Rougeole 1', 'maladies_previent', 'rougeole', 'VACCINATION'),
        ('Rougeole 2', 'age_recommande', '15-18 mois', 'VACCINATION'),
        ('Fièvre jaune', 'age_recommande', '9 mois', 'VACCINATION'),
        ('Fièvre jaune', 'maladies_previent', 'fièvre jaune', 'VACCINATION'),
        ('Méningite A (MenAfriVac)', 'age_recommande', '9-18 mois', 'VACCINATION'),
        ('Méningite A', 'maladies_previent', 'méningite à méningocoque A', 'VACCINATION'),
        ('VAT (vaccin antitétanique)', 'age_recommande', 'grossesse : 2 doses', 'VACCINATION'),
        ('VAT', 'maladies_previent', 'tétanos néonatal', 'VACCINATION'),
        ('DTC de rappel', 'age_recommande', '15-18 mois et 5-6 ans', 'VACCINATION'),
        ('Vaccination', 'conduite_à_tenir', 'chaîne du froid 2-8°C obligatoire', 'VACCINATION'),
        ('Vaccination', 'contre_indications', 'fièvre élevée, infection aiguë sévère', 'VACCINATION'),
        ('Vaccination', 'effets_secondaires', 'fièvre légère 24-48h, douleur au point d\'injection', 'VACCINATION'),
        ('Rougeole', 'urgence', 'épidémie possible si couverture < 95%', 'VACCINATION'),
    ],
    'PALUDISME': [
        ('Paludisme simple', 'traitement', 'Artéméther-Luméfantrine 20/120 mg selon poids', 'PALUDISME'),
        ('Paludisme simple', 'dose_adulte', '4 comprimés à H0, H8, H24, H36, H48, H60 (3 jours)', 'PALUDISME'),
        ('Paludisme simple', 'dose_enfant', 'selon poids : 5-14 kg = 1 comp, 15-24 kg = 2 comp', 'PALUDISME'),
        ('Paludisme grave', 'traitement', 'Artesunate IV 2.4 mg/kg à H0, H12, H24 puis 1x/jour', 'PALUDISME'),
        ('Paludisme grave', 'urgence', 'hospitalisation immédiate', 'PALUDISME'),
        ('Paludisme grave', 'signes_cliniques', 'convulsions, coma, anémie sévère, détresse respiratoire', 'PALUDISME'),
        ('Paludisme femme enceinte', 'traitement', 'TPI avec Sulfadoxine-Pyriméthamine à partir du 2e trimestre', 'PALUDISME'),
        ('Paludisme femme enceinte', 'prévention', 'moustiquaire imprégnée + TPI', 'PALUDISME'),
        ('Paludisme', 'diagnostic', 'TDR ou goutte épaisse avant tout traitement', 'PALUDISME'),
        ('Paludisme', 'prévention', 'moustiquaires imprégnées d\'insecticide (MII)', 'PALUDISME'),
        ('Paludisme', 'prévention', 'pulvérisation intradomiciliaire à effet rémanent', 'PALUDISME'),
        ('Paludisme', 'complications', 'anémie, hypoglycémie, insuffisance rénale, œdème pulmonaire', 'PALUDISME'),
        ('Paludisme non compliqué', 'traitement', 'ACT 3 jours (Artéméther-Luméfantrine, Artésunate-Amodiaquine)', 'PALUDISME'),
        ('Quinine', 'dose_adulte', '8 mg/kg x3/jour pendant 7 jours (si ACT indisponible)', 'PALUDISME'),
        ('Paludisme', 'délai_consultation', 'consultation dans les 24h suivant fièvre en zone endémique', 'PALUDISME'),
    ],
    'NUTRITION': [
        ('Malnutrition aiguë sévère', 'diagnostic', 'PB < 115 mm ou œdème bilatéral', 'NUTRITION'),
        ('Malnutrition aiguë modérée', 'diagnostic', 'PB 115-124 mm', 'NUTRITION'),
        ('Malnutrition aiguë sévère', 'traitement', 'F-75 puis F-100 ou Plumpy\'Nut 10-15 g/kg/jour', 'NUTRITION'),
        ('Malnutrition aiguë sévère', 'urgence', 'complications = hospitalisation (protocole PCIMA)', 'NUTRITION'),
        ('Kwashiorkor', 'traitement', 'F-75 à H0 puis transition F-100', 'NUTRITION'),
        ('Marasme', 'traitement', 'réhabilitation nutritionnelle progressive', 'NUTRITION'),
        ('Allaitement maternel', 'prévention', 'allaitement exclusif pendant 6 mois', 'NUTRITION'),
        ('Allaitement maternel', 'conduite_à_tenir', 'poursuivre pendant les épisodes de maladie', 'NUTRITION'),
        ('Vitamine A', 'dose_enfant', '100 000 UI à 6-11 mois, 200 000 UI à 12-59 mois', 'NUTRITION'),
        ('Vitamine A', 'prévention', 'supplémentation 2x/an en zones carencées', 'NUTRITION'),
        ('Fer', 'dose', 'fer + acide folique : 60 mg fer + 400 µg AF chez la femme enceinte', 'NUTRITION'),
        ('Fer', 'prévention', 'supplémentation systématique grossesse', 'NUTRITION'),
        ('Zinc', 'dose', '10-20 mg/jour pendant 10-14 jours en cas de diarrhée', 'NUTRITION'),
        ('Malnutrition', 'signes_cliniques', 'perte de poids, œdèmes, fonte musculaire, apathie', 'NUTRITION'),
        ('Dépistage malnutrition', 'conduite_à_tenir', 'PB + œdèmes + poids/taille tous les mois', 'NUTRITION'),
    ],
    'VIH_TB': [
        ('VIH', 'traitement', 'TARV : Ténofovir + Lamivudine + Dolutégravir (1cp/jour)', 'VIH_TB'),
        ('VIH', 'diagnostic', 'TROD puis confirmation par test de laboratoire', 'VIH_TB'),
        ('VIH', 'prévention', 'préservatifs, PTME, prophylaxie pré-exposition (PrEP)', 'VIH_TB'),
        ('Tuberculose', 'diagnostic', 'examen des crachats (BAAR) ou GeneXpert', 'VIH_TB'),
        ('Tuberculose', 'traitement', 'RHZE 2 mois puis RH 4 mois (schéma 6 mois)', 'VIH_TB'),
        ('Tuberculose', 'signes_cliniques', 'toux > 2 semaines, sueurs nocturnes, amaigrissement, hémoptysie', 'VIH_TB'),
        ('Tuberculose multirésistante', 'traitement', 'schéma allongé 9-20 mois, spécialiste requis', 'VIH_TB'),
        ('Co-infection VIH-TB', 'traitement', 'TARV + traitement TB simultanés', 'VIH_TB'),
        ('Co-infection VIH-TB', 'prévention', 'cotrimoxazole prophylactique', 'VIH_TB'),
        ('VIH', 'délai_consultation', 'initiation TARV le jour même du diagnostic (Test and Treat)', 'VIH_TB'),
        ('PTME', 'traitement', 'TARV pendant grossesse + allaitement + ARV néonatal', 'VIH_TB'),
        ('VIH', 'complications', 'infections opportunistes, cancers, cachexie', 'VIH_TB'),
    ],
    'PEDIATRIE': [
        ('Déshydratation', 'signes_cliniques', 'yeux enfoncés, pli cutané, soif, léthargie', 'PEDIATRIE'),
        ('Déshydratation sévère', 'traitement', 'SRO IV (Ringer Lactate) 100 ml/kg', 'PEDIATRIE'),
        ('Diarrhée aiguë', 'traitement', 'SRO + zinc 10-20 mg/jour 10-14 jours', 'PEDIATRIE'),
        ('Diarrhée aiguë', 'conduite_à_tenir', 'poursuivre alimentation et allaitement', 'PEDIATRIE'),
        ('Pneumonie', 'diagnostic', 'toux + respiration rapide + tirage sous-costal', 'PEDIATRIE'),
        ('Pneumonie', 'traitement', 'amoxicilline 40 mg/kg 2x/jour pendant 5 jours', 'PEDIATRIE'),
        ('Pneumonie grave', 'urgence', 'hospitalisation + O2 + antibiotique IV', 'PEDIATRIE'),
        ('Fièvre', 'traitement', 'paracétamol 15 mg/kg toutes les 6h si fièvre > 38.5°C', 'PEDIATRIE'),
        ('Fièvre', 'conduite_à_tenir', 'rechercher paludisme, infection urinaire, méningite selon signes', 'PEDIATRIE'),
        ('Convulsions fébriles', 'traitement', 'diazepam rectal 0.5 mg/kg, hospitaliser', 'PEDIATRIE'),
        ('Convulsions fébriles', 'urgence', 'position latérale, ne rien mettre en bouche', 'PEDIATRIE'),
        ('PCIME', 'conduite_à_tenir', 'classifier : rose (urgent), jaune (traiter), verte (conseils)', 'PEDIATRIE'),
        ('Prématuré', 'conduite_à_tenir', 'méthode kangourou, allaitement précoce, hypothermie à éviter', 'PEDIATRIE'),
        ('Toux', 'conduite_à_tenir', 'compter respirations en 1 min, chercher tirage', 'PEDIATRIE'),
    ],
    'MERE_ENFANT': [
        ('CPN 1', 'conduite_à_tenir', 'avant 14 SA : bilan, groupe sanguin, TPI', 'MERE_ENFANT'),
        ('CPN', 'calendrier', '4 consultations prénatales minimum', 'MERE_ENFANT'),
        ('CPN', 'dose', 'fer + acide folique tous les jours', 'MERE_ENFANT'),
        ('CPN', 'prévention', 'TPI paludisme à partir de 13 SA', 'MERE_ENFANT'),
        ('Accouchement', 'urgence', 'toute complication = référence immédiate', 'MERE_ENFANT'),
        ('Signes danger grossesse', 'urgence', 'saignements, fièvre, convulsions, œdèmes, douleurs abdominales', 'MERE_ENFANT'),
        ('Hémorragie post-partum', 'traitement', 'utérotoniques (ocytocine) + réanimation + référence', 'MERE_ENFANT'),
        ('Hémorragie post-partum', 'urgence', 'cause n°1 de mortalité maternelle', 'MERE_ENFANT'),
        ('Post-partum', 'conduite_à_tenir', 'consultation à J3, J7, J42', 'MERE_ENFANT'),
        ('Allaitement', 'conduite_à_tenir', 'exclusif 6 mois, mise au sein dans l\'heure', 'MERE_ENFANT'),
        ('Pré-éclampsie', 'signes_cliniques', 'HTA > 140/90 + protéinurie après 20 SA', 'MERE_ENFANT'),
        ('Pré-éclampsie', 'traitement', 'MgSO4 si convulsions, référence urgente', 'MERE_ENFANT'),
        ('Nouveau-né', 'conduite_à_tenir', 'soins immédiats : sécher, peau-à-peau, cordon propre', 'MERE_ENFANT'),
        ('Nouveau-né', 'urgence', 'réanimation néonatale si non-viable à 1 min', 'MERE_ENFANT'),
        ('Planning familial', 'conduite_à_tenir', 'proposer contraception dès J42 post-partum', 'MERE_ENFANT'),
    ],
    'URGENCES': [
        ('ABCDE', 'conduite_à_tenir', 'Airway, Breathing, Circulation, Disability, Exposure', 'URGENCES'),
        ('Hémorragie', 'traitement', 'compression directe, garrot si membre, remplissage vasculaire', 'URGENCES'),
        ('Arrêt cardiaque', 'traitement', 'RCP 30:2, défibrillation précoce, adrénaline 1 mg/3-5 min', 'URGENCES'),
        ('Choc hypovolémique', 'traitement', '2 voies veineuses, solutés 20 ml/kg, O2', 'URGENCES'),
        ('Détresse respiratoire', 'traitement', 'O2, position demi-assise, cause (asthme, corps étranger...)', 'URGENCES'),
        ('Corps étranger', 'urgence', 'manœuvre de Heimlich si obstruction complète', 'URGENCES'),
        ('Brûlure', 'traitement', 'refroidir 20 min à l\'eau, pansement, évaluation surface', 'URGENCES'),
        ('Brûlure grave', 'urgence', '> 10% surface corps enfant / 15% adulte = référence', 'URGENCES'),
        ('Traumatisme crânien', 'urgence', 'GCS < 15 = scanner, surveillance 24h', 'URGENCES'),
        ('Intoxication', 'conduite_à_tenir', 'identifier toxique, ne pas faire vomir systématiquement', 'URGENCES'),
        ('Morsure serpent', 'traitement', 'immobiliser membre, sérum antivenimeux, référence', 'URGENCES'),
        ('Morsure serpent', 'urgence', 'bandage non compressif, pas de garrot', 'URGENCES'),
        ('Envenimation scorpion', 'urgence', 'antivenin si classe III, sinon surveillance', 'URGENCES'),
        ('Hypoglycémie', 'traitement', 'sucre PO si conscient, G30% IV si inconscient', 'URGENCES'),
        ('Résumé', 'conduite_à_tenir', 'tout patient instable : ABCDE + O2 + voies + référence', 'URGENCES'),
    ],
    'CHRONIQUES': [
        ('Diabète type 2', 'diagnostic', 'glycémie à jeun ≥ 1.26 g/L (7 mmol/L) à 2 reprises', 'CHRONIQUES'),
        ('Diabète type 2', 'traitement', 'metformine 500-2000 mg/jour + hygiène de vie', 'CHRONIQUES'),
        ('Diabète', 'prévention', 'activité physique 150 min/semaine, alimentation équilibrée', 'CHRONIQUES'),
        ('Diabète', 'complications', 'rétinopathie, néphropathie, neuropathie, pied diabétique', 'CHRONIQUES'),
        ('HTA', 'diagnostic', '≥ 140/90 mmHg à 2 consultations séparées', 'CHRONIQUES'),
        ('HTA', 'traitement', 'Amlodipine 5-10 mg ou IEC, selon protocole', 'CHRONIQUES'),
        ('HTA', 'complications', 'AVC, infarctus, insuffisance rénale', 'CHRONIQUES'),
        ('Asthme', 'traitement', 'salbutamol inhalé à la demande (crise), corticoïdes inhalés (fond)', 'CHRONIQUES'),
        ('Asthme crise', 'urgence', 'salbutamol 2-4 bouffées, répéter, O2 si grave', 'CHRONIQUES'),
        ('Épilepsie', 'traitement', 'phénobarbital 2-5 mg/kg/jour (1ère ligne Afrique)', 'CHRONIQUES'),
        ('Drépanocytose', 'conduite_à_tenir', 'crise vaso-occlusive : hydratation, antalgiques, O2', 'CHRONIQUES'),
        ('Drépanocytose', 'prévention', 'acide folique, pénicilline prophylactique, vaccins', 'CHRONIQUES'),
        ('Insuffisance rénale', 'conduite_à_tenir', 'réduire sel, contrôler tension, éviter AINS', 'CHRONIQUES'),
        ('Maladie chronique', 'conduite_à_tenir', 'suivi régulier + observance + éducation thérapeutique', 'CHRONIQUES'),
    ],
    'SANTE_MENTALE': [
        ('Dépression', 'diagnostic', 'humeur triste + perte d\'intérêt ≥ 2 semaines', 'SANTE_MENTALE'),
        ('Dépression', 'traitement', 'psychothérapie + antidépresseurs (ISRS) si modérée-sévère', 'SANTE_MENTALE'),
        ('Anxiété', 'traitement', 'TCC, relaxation, gestion du stress', 'SANTE_MENTALE'),
        ('Psychose', 'traitement', 'antipsychotiques + suivi psychiatrique', 'SANTE_MENTALE'),
        ('Risque suicidaire', 'urgence', 'ne pas laisser seul, retirer moyens, référence immédiate', 'SANTE_MENTALE'),
        ('Risque suicidaire', 'signes_cliniques', 'propos de mort, isolement, dons d\'objets, amélioration soudaine', 'SANTE_MENTALE'),
        ('Épilepsie psychogène', 'diagnostic', 'distinguer des crises épileptiques vraies', 'SANTE_MENTALE'),
        ('Trouble bipolaire', 'traitement', 'stabilisateurs d\'humeur (lithium, valproate)', 'SANTE_MENTALE'),
        ('Stress post-traumatique', 'traitement', 'TCC centrée sur le trauma, soutien psychologique', 'SANTE_MENTALE'),
        ('Santé mentale', 'prévention', 'soutien communautaire, réduction de la stigmatisation', 'SANTE_MENTALE'),
        ('Insomnie', 'traitement', 'hygiène du sommeil avant tout, éviter benzodiazépines au long cours', 'SANTE_MENTALE'),
    ],
    'PHYTOTHERAPIE': [
        ('Artemisia annua', 'indication', 'paludisme (usage traditionnel — combiner avec TDR et ACT)', 'PHYTOTHERAPIE'),
        ('Artemisia annua', 'mode_preparation', 'infusion de feuilles séchées 5g/L', 'PHYTOTHERAPIE'),
        ('Artemisia annua', 'contre_indications', 'grossesse (1er trimestre), femmes allaitantes sans avis', 'PHYTOTHERAPIE'),
        ('Moringa', 'indication', 'carence nutritionnelle, source de vitamines et fer', 'PHYTOTHERAPIE'),
        ('Moringa', 'partie_utilisee', 'feuilles', 'PHYTOTHERAPIE'),
        ('Gingembre', 'indication', 'nausées, vomissements', 'PHYTOTHERAPIE'),
        ('Citronnelle', 'indication', 'fièvre, répulsif moustiques', 'PHYTOTHERAPIE'),
        ('Nim (Azadirachta indica)', 'indication', 'fièvre, paludisme (usage traditionnel)', 'PHYTOTHERAPIE'),
        ('Aloe vera', 'indication', 'brûlures, plaies superficielles', 'PHYTOTHERAPIE'),
        ('Cochlospermum (faux kinkéliba)', 'indication', 'paludisme, ictère (usage traditionnel)', 'PHYTOTHERAPIE'),
        ('Plantes médicinales', 'conduite_à_tenir', 'toujours croiser avec avis médical ; risque de toxicité et d\'interactions', 'PHYTOTHERAPIE'),
        ('Plantes médicinales', 'contre_indications', 'grossesse, enfants < 2 ans, insuffisance hépatique/rénale', 'PHYTOTHERAPIE'),
    ],
    'MNT': [
        ('Bilharziose', 'traitement', 'Praziquantel 40 mg/kg en dose unique', 'MNT'),
        ('Bilharziose', 'signes_cliniques', 'sang dans les urines, douleurs pelviennes', 'MNT'),
        ('Filariose lymphatique', 'traitement', 'IVM + DEC (albendazole annuel, masse)', 'MNT'),
        ('Filariose lymphatique', 'prévention', 'chimiothérapie préventive annuelle', 'MNT'),
        ('Onchocercose', 'traitement', 'Ivermectine annuelle', 'MNT'),
        ('Onchocercose', 'prévention', 'lutte anti-vecteur, ivermectine de masse', 'MNT'),
        ('Trypanosomiase', 'traitement', 'selon stade : pentamidine ou nifurtimox-éflornithine', 'MNT'),
        ('Trypanosomiase', 'signes_cliniques', 'chancre, fièvre, troubles du sommeil', 'MNT'),
        ('Dengue', 'traitement', 'repos, paracétamol (pas d\'AINS !), hydratation', 'MNT'),
        ('Dengue', 'urgence', 'signes alarme : douleurs abdominales, vomissements, saignements', 'MNT'),
        ('Chikungunya', 'traitement', 'antalgiques, repos', 'MNT'),
        ('Lèpre', 'traitement', 'multithérapie (rifampicine, clofazimine, dapsone)', 'MNT'),
        ('Lèpre', 'signes_cliniques', 'taches hypopigmentées insensibles, nerfs épaissis', 'MNT'),
        ('Géohelminthiases', 'traitement', 'albendazole 400 mg 1-2x/an (déparasitage de masse)', 'MNT'),
        ('MNT', 'prévention', 'eau potable, assainissement, lutte anti-vecteur', 'MNT'),
    ],
}


# ════════════════════════════════════════════════════════════════
# APPLICATION
# ════════════════════════════════════════════════════════════════

def apply_enrichment(domains: list) -> dict:
    """Ajoute les faits d'enrichissement aux fichiers _facts.json."""
    added = {}
    for domain in domains:
        facts_file = HOLO_DIR / f"{domain}_facts.json"
        new_facts = ENRICHMENT.get(domain, [])
        if not new_facts:
            continue
        # Charger les faits existants
        existing = []
        if facts_file.exists():
            with open(facts_file, encoding='utf-8') as f:
                existing = json.load(f)
        # Dédupliquer (s, r, o)
        seen = {(str(x.get('s')), str(x.get('r')), str(x.get('o'))) for x in existing}
        to_add = []
        for s, r, o, sec in new_facts:
            key = (s, r, o)
            if key not in seen:
                to_add.append({'s': s, 'r': r, 'o': o, 'sec': sec})
                seen.add(key)
        if to_add:
            existing.extend(to_add)
            with open(facts_file, 'w', encoding='utf-8') as f:
                json.dump(existing, f, ensure_ascii=False, indent=1)
        added[domain] = len(to_add)
    return added


def retrain_domains(domains: list):
    """Ré-entraîne les hologrammes des domaines enrichis."""
    print(f"\n🎯 Ré-entraînement de {len(domains)} domaines...")
    for i, domain in enumerate(domains):
        facts_file = HOLO_DIR / f"{domain}_facts.json"
        with open(facts_file, encoding='utf-8') as f:
            facts = json.load(f)
        facts_tuples = [(x['s'], x['r'], x['o'], x.get('sec', domain))
                        for x in facts]
        print(f"  [{i+1}/{len(domains)}] {domain} ({len(facts_tuples)} faits)...")
        train_hologram(domain, facts_tuples, HOLO_DIR)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--all', action='store_true',
                        help='Enrichir tous les domaines de ENRICHMENT')
    parser.add_argument('--domain', nargs='*', default=[],
                        help='Domaines spécifiques (ex: VACCINATION PALUDISME)')
    parser.add_argument('--no-retrain', action='store_true',
                        help='Ne pas ré-entraîner (mise à jour faits uniquement)')
    args = parser.parse_args()

    if args.all:
        domains = list(ENRICHMENT.keys())
    else:
        domains = [d.upper() for d in args.domain if d.upper() in ENRICHMENT]
    if not domains:
        print("⚠️  Aucun domaine — utiliser --all ou --domain VACCINATION PALUDISME ...")
        return

    print("=" * 60)
    print("  💉 ENRICHISSEMENT DES HOLOGRAMMES MÉDICAUX")
    print("=" * 60)
    t0 = time.time()

    # 1. Enrichir les fichiers de faits
    print("\n📝 Mise à jour des fichiers _facts.json...")
    added = apply_enrichment(domains)
    for d, n in added.items():
        print(f"  ✅ {d}: +{n} faits")

    # 2. Ré-entraîner
    if not args.no_retrain:
        retrain_domains(domains)
        print(f"\n  ⏱️  Total : {time.time()-t0:.0f}s")
    else:
        print("\n  (sans ré-entraînement — ok)")


if __name__ == "__main__":
    main()
