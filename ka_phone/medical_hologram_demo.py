#!/usr/bin/env python3
"""
KA-Enterprise — HOLOGRAMME MÉDICAL SPÉCIALISÉ
=================================================
Crée un hologramme 64×64 dédié au domaine médical
avec une base de connaissances préchargée.

USAGE :
  python medical_hologram_demo.py
"""

import os, sys, json, time
sys.path.insert(0, os.path.dirname(__file__))
from ka_enterprise import EnterpriseManager, EnterpriseHologram, BUSINESS_DOMAINS

# ═══════════════════════════════════════════════════════════════════
# BASE DE CONNAISSANCES MÉDICALES PRÉCHARGÉE
# ═══════════════════════════════════════════════════════════════════

MEDICAL_KNOWLEDGE = {
    "anatomie": [
        "Le cœur humain est un organe musculaire creux situé dans le médiastin, divisé en 4 cavités : 2 oreillettes et 2 ventricules. Il pompe environ 5 litres de sang par minute au repos.",
        "Le cerveau humain pèse environ 1.3 à 1.4 kg et contient environ 86 milliards de neurones. Il est divisé en 3 parties principales : le cerveau, le cervelet et le tronc cérébral.",
        "Les poumons sont des organes spongieux divisés en lobes : 3 lobes à droite, 2 lobes à gauche. La surface alvéolaire totale est d'environ 70 à 100 m².",
        "Le foie est le plus gros organe interne, pesant environ 1.5 kg. Il assure plus de 500 fonctions vitales, dont la détoxification, la synthèse des protéines, et le stockage du glycogène.",
        "Les reins filtrent environ 180 litres de sang par jour et produisent 1.5 à 2 litres d'urine. L'unité fonctionnelle est le néphron, chaque rein en contient environ 1 million.",
        "Le squelette humain adulte compte 206 os. Le fémur est l'os le plus long (environ 50 cm). Les os sont reliés par 360 articulations.",
        "La peau est le plus grand organe du corps humain, avec une surface d'environ 1.5 à 2 m². Elle se compose de 3 couches : épiderme, derme et hypoderme.",
        "Le système digestif mesure environ 9 mètres de long, de la bouche à l'anus. L'intestin grêle (6-7 m) absorbe les nutriments, le gros intestin (1.5 m) réabsorbe l'eau.",
    ],
    "pathologies": [
        "L'hypertension artérielle (HTA) est définie par une pression systolique ≥ 140 mmHg et/ou diastolique ≥ 90 mmHg. Elle touche environ 30% de la population adulte mondiale.",
        "Le diabète de type 2 est caractérisé par une résistance à l'insuline. La glycémie à jeun normale est < 1.10 g/L. Le diagnostic est posé si glycémie à jeun ≥ 1.26 g/L à deux reprises.",
        "L'infarctus du myocarde (crise cardiaque) résulte de l'obstruction d'une artère coronaire. Les symptômes incluent douleur thoracique constrictive irradiant vers le bras gauche, mâchoire ou dos.",
        "L'AVC (accident vasculaire cérébral) peut être ischémique (85% des cas, obstruction) ou hémorragique (15%, rupture). Signes d'alerte FAST : Face affaissée, Attitude (bras qui tombe), Speech (trouble parole), Time (appeler le 15).",
        "La pneumonie est une infection du parenchyme pulmonaire, le plus souvent bactérienne (pneumocoque). Les symptômes incluent fièvre élevée, toux productive, essoufflement, douleur thoracique.",
        "L'appendicite aiguë est l'urgence chirurgicale abdominale la plus fréquente. Douleur localisée en fosse iliaque droite, fièvre modérée, défense abdominale. Le traitement est chirurgical (appendicectomie).",
        "La dépression majeure touche 5 à 15% de la population. Critères DSM-5 : humeur dépressive et/ou anhédonie pendant ≥ 2 semaines, associés à ≥ 4 symptômes (troubles du sommeil, appétit, énergie, concentration, estime de soi, ralentissement, idées noires).",
        "La maladie d'Alzheimer est une pathologie neurodégénérative progressive touchant la mémoire. Les plaques amyloïdes et les dégénérescences neurofibrillaires sont caractéristiques.",
    ],
    "traitements": [
        "Le paracétamol est un antalgique et antipyrétique de palier 1. Dose maximale : 4g/jour chez l'adulte. Toxicité hépatique au-delà de 10g en prise unique.",
        "L'ibuprofène est un AINS (anti-inflammatoire non stéroïdien). Il inhibe les COX-1 et COX-2. Effets secondaires : gastrite, néphrotoxicité, risque cardiovasculaire.",
        "Les IEC (Inhibiteurs de l'Enzyme de Conversion) comme le ramipril ou le lisinopril sont des antihypertenseurs de 1ère ligne. Effet secondaire principal : toux sèche (10-20% des patients).",
        "La metformine est le traitement de 1ère intention du diabète de type 2. Elle réduit la production hépatique de glucose et améliore la sensibilité à l'insuline. Contre-indiquée en cas d'insuffisance rénale sévère (DFG < 30).",
        "Les statines (atorvastatine, rosuvastatine) réduisent la synthèse du cholestérol. Indiquées en prévention cardiovasculaire primaire et secondaire. Effet secondaire : myalgies (douleurs musculaires).",
        "L'amoxicilline est un antibiotique de la famille des pénicillines, à large spectre. Dose usuelle adulte : 1g × 2/jour. Allergie aux pénicillines chez 1 à 10% des patients nécessite une alternative.",
        "La morphine est un antalgique de palier 3, agoniste des récepteurs opioïdes μ. Utilisée pour les douleurs sévères. Effets secondaires : constipation, nausées, dépression respiratoire à haute dose.",
        "Les antidépresseurs ISRS (Fluoxétine, Sertraline, Paroxétine) augmentent la sérotonine synaptique. Délai d'action : 2-6 semaines. Effets secondaires initiaux : nausées, insomnie, anxiété transitoire.",
    ],
    "urgences": [
        "En cas d'arrêt cardiaque : appeler le 15 (SAMU), débuter le massage cardiaque externe immédiatement, 100-120 compressions/minute, profondeur 5-6 cm. Utiliser un DAE si disponible.",
        "Le protocole d'AVC : score NIHSS dans les 24h, imagerie cérébrale en urgence (scanner sans injection ou IRM). Thrombolyse IV si < 4h30 (Altéplase). Thrombectomie mécanique si occlusion proximale < 6h.",
        "Choc anaphylactique : adrénaline IM 0.5 mg (0.5 mL de solution à 1:1000) en urgence, renouvelable après 5-10 minutes. Position Trendelenburg. Oxygénothérapie 15L/min.",
        "Brûlures étendues : règle des 9 de Wallace pour estimer la surface. Refroidir à l'eau tiède (15-25°C) pendant 20 minutes. Pas de glace. Couvrir proprement. Hospitalisation si > 15% chez l'adulte, > 10% chez l'enfant.",
        "Hémorragie externe : compression manuelle directe avec un tissu propre. Garrot si hémorragie non contrôlable et membre atteint. Noter l'heure de pose. Transfusion si pertes > 30% de la volémie.",
    ],
    "diagnostics": [
        "L'ECG (électrocardiogramme) enregistre l'activité électrique du cœur. 12 dérivations. Onde P (dépolarisation auriculaire), complexe QRS (dépolarisation ventriculaire), onde T (repolarisation). Intervalle QT normal < 440 ms.",
        "La NFS (numération formule sanguine) donne : hémoglobine (13-17 g/dL homme, 12-16 g/dL femme), leucocytes (4000-10000/mm³), plaquettes (150000-400000/mm³).",
        "Le bilan hépatique inclut : ASAT, ALAT (normales < 40 UI/L), GGT, PAL, bilirubine totale et conjuguée. ALAT > 1000 évoque une hépatite aiguë virale ou toxique.",
        "La fonction rénale est évaluée par la créatinine sérique (normale 60-110 µmol/L) et le DFG estimé (CKD-EPI). DFG < 60 = insuffisance rénale chronique. Dialyse si DFG < 15.",
        "L'imagerie par résonance magnétique (IRM) n'utilise pas de rayons X mais un champ magnétique puissant. Contre-indiquée si pacemaker non compatible, corps métallique intraoculaire.",
        "Le scanner (TDM) utilise des rayons X et un produit de contraste iodé. Contre-indications : allergie à l'iode, insuffisance rénale (risque de néphropathie au produit de contraste), grossesse.",
        "La glycémie capillaire (HGT) normale à jeun : 0.70-1.10 g/L. Postprandiale < 1.40 g/L. Hypoglycémie si < 0.60 g/L (signes : sueurs, tremblements, confusion). Administration de sucre rapide (15g glucose).",
    ],
    "interactions_medicamenteuses": [
        "AVK (warfarine, coumadine) et AINS (ibuprofène, aspirine > 500 mg) : risque hémorragique majeur par addition des effets anticoagulant et antiagrégant plaquettaire. Contre-indication formelle.",
        "AVK et amoxicilline (antibiotique) : potentialisation de l'effet anticoagulant par destruction de la flore intestinale productrice de vitamine K. Surveillance INR renforcée et adaptation de la posologie de l'AVK.",
        "AVK et statines (atorvastatine) : la warfarine est un substrat du CYP3A4, les statines sont des inhibiteurs du CYP3A4. Risque d'augmentation des concentrations de warfarine et d'hémorragie.",
        "IEC (ramipril, lisinopril) et diurétiques épargneurs de potassium (spironolactone) : risque d'hyperkaliémie mortelle par addition des effets. Contre-indication absolue. Surveillance kaliémie obligatoire.",
        "IEC et AINS (ibuprofène, diclofénac) : diminution de l'effet antihypertenseur de l'IEC et risque d'insuffisance rénale aiguë. Association déconseillée. Surveiller la fonction rénale.",
        "Statines (atorvastatine) et macrolides (clarithromycine, érythromycine) : risque de rhabdomyolyse par inhibition du CYP3A4. Utiliser une statine non métabolisée (pravastatine) ou adapter la dose.",
        "Metformine et produit de contraste iodé : risque d'acidose lactique par néphropathie au produit de contraste. Arrêter la metformine 48h avant l'examen, reprendre 48h après si DFG > 30.",
        "ISRS (fluoxétine, sertraline) et IMAO (phénelzine) : risque de syndrome sérotoninergique mortel (confusion, hyperthermie, rigidité, convulsions). Délai de wash-out de 14 jours minimum entre l'arrêt d'un IMAO et le début d'un ISRS.",
        "Paracétamol et alcool (consommation chronique) : risque de nécrose hépatique fulminante par induction du CYP2E1 et déplétion du glutathion. Ne pas dépasser 2g/jour de paracétamol chez le patient alcoolique chronique.",
        "AINS (ibuprofène) et diurétiques (furosémide) : diminution de l'effet diurétique et risque d'insuffisance rénale aiguë. Surveiller la fonction rénale.",
        "Amiodarone et fluoroquinolones (ciprofloxacine, lévofloxacine) : risque de torsades de pointes par addition des effets allongeant l'intervalle QT. Contre-indication. ECG avant et pendant le traitement.",
        "Lithium et AINS (ibuprofène, diclofénac) : augmentation de la lithémie pouvant atteindre des concentrations toxiques (> 1.5 mmol/L). Contre-indication. Surveillance lithémie si association inévitable.",
        "Digoxine et amiodarone : doublement de la concentration plasmatique de digoxine par inhibition de la P-glycoprotéine. Diviser la dose de digoxine par 2 et surveiller signes de surdosage (nausées, troubles visuels, arythmie).",
        "Méthotrexate (immunosuppresseur) et AINS : risque de toxicité hématologique sévère par diminution de l'élimination rénale du méthotrexate. Ne JAMAIS associer en traitement oncologique (méthotrexate > 20 mg/semaine).",
        "Carbamazépine (antiépileptique) et contraceptifs oraux : diminution de l'efficacité contraceptive par induction du CYP3A4. Utiliser une contraception non hormonale ou un DIU.",
        "Phénytoïne et warfarine : compétition pour la liaison aux protéines plasmatiques avec risque hémorragique puis inefficacité. Surveillance INR extrêmement rapprochée.",
        "AINS (ibuprofène) et antiagrégants plaquettaires (aspirine ≤ 325 mg, clopidogrel) : risque hémorragique digestif accru par addition des effets. Utiliser un IPP en gastroprotection.",
        "Millepertuis (Hypericum perforatum) et contraceptifs oraux, AVK, ISRS : puissant inducteur du CYP3A4 annulant l'efficacité de nombreux médicaments. Vérifier systématiquement la prise de phytothérapie.",
    ],
    "contre_indications_absolues": [
        "Grossesse et isotrétinoïne (anti-acnéique) : tératogénicité majeure (malformations du SNC, cardiaques, faciales). Test de grossesse obligatoire avant et pendant le traitement. Contraception efficace requise 1 mois avant et 1 mois après l'arrêt.",
        "Allergie aux pénicillines : utiliser macrolides (clarithromycine) ou fluoroquinolones selon le spectre. Attention à l'allergie croisée avec céphalosporines (5-10% des cas).",
        "Allaitement et amiodarone : l'amiodarone passe massivement dans le lait maternel (demi-vie longue, 20-100 jours). Contre-indication absolue pendant l'allaitement.",
        "Enfant de moins de 12 ans et codéine : risque de dépression respiratoire mortelle par transformation en morphine (métaboliseurs ultra-rapides du CYP2D6). Contre-indication absolue.",
        "Valproate de sodium (antiépileptique) et grossesse : risque de malformations congénitales majeures (spina bifida, fente palatine, cardiopathies). Le valproate ne doit JAMAIS être utilisé chez la femme enceinte.",
        "Jus de pamplemousse et statines (atorvastatine, simvastatine) : inhibition du CYP3A4 intestinal multipliant par 5 à 15 les concentrations plasmatiques. Risque de rhabdomyolyse. Contre-indication de la consommation de pamplemousse sous statines.",
    ],
    "surveillances_renforcees": [
        "Sous AVK (warfarine) : INR cible 2.0-3.0 (FA, MTEV) ou 2.5-3.5 (valves mécaniques). Surveillance INR hebdomadaire en début de traitement puis mensuelle. Signes d'alerte hémorragique : gingivorragies, hématomes spontanés, hématurie, méléna.",
        "Sous lithium : lithémie cible 0.5-0.8 mmol/L (entretien) ou 0.8-1.2 mmol/L (phase aiguë). Signes de surdosage (> 1.5 mmol/L) : tremblements, confusion, nausées, convulsions, coma. Bilan rénal et thyroïdien avant et pendant le traitement.",
        "Sous clozapine (antipsychotique) : risque d'agranulocytose mortelle (1-2% des patients). NFS hebdomadaire pendant les 18 premières semaines puis mensuelle à vie. Arrêt IMMÉDIAT si leucocytes < 3000/mm³.",
        "Sous amiodarone : bilan thyroïdien (TSH, T4) avant et pendant le traitement (tous les 6 mois). Fond d'œil annuel. Radiographie pulmonaire (fibrose pulmonaire). ECG trimestriel (allongement du QTc).",
        "Sous digoxine : digoxinémie cible 0.5-0.9 ng/mL. Signes de surdosage (> 2.0 ng/mL) : nausées, vomissements, vision colorée (xanthopsie, halo jaune), arythmie. Kaliémie normale obligatoire.",
        "Sous immunosuppresseurs (ciclosporine, tacrolimus) : dosage sanguin régulier. Ciclosporinémie cible 150-250 ng/mL selon le type de greffe. Fonction rénale, bilan hépatique et tension artérielle à chaque consultation.",
    ],
}


def create_medical_hologram():
    """Crée et peuple l'hologramme médical spécialisé."""
    print("=" * 70)
    print("  HOLOGRAMME MÉDICAL SPÉCIALISÉ — Création")
    print("=" * 70)

    # Créer le manager
    manager = EnterpriseManager(storage_dir=os.path.join(os.path.dirname(__file__), "..", "data", "enterprise"))

    # Créer l'hologramme médical
    holo = EnterpriseHologram(domain="medical", company_name="Hôpital Central")

    total_facts = 0
    # Phase 1 : Faits manuels (36 faits)
    for category, facts in MEDICAL_KNOWLEDGE.items():
        for fact in facts:
            holo.ingest_text(fact, source_file=f"kb_medicale_{category}.txt")
            total_facts += 1
        print(f"  [{category:15s}] {len(facts)} faits ingérés (manuel)")
    
    # Phase 2 : Faits générés par DeepSeek (gen_health.txt)
    gen_file = os.path.join(os.path.dirname(__file__), "..", "data", "corpus", "gen_health.txt")
    if os.path.exists(gen_file):
        with open(gen_file, 'r', encoding='utf-8') as f:
            gen_facts = [line.strip() for line in f if len(line.strip()) > 30]
        for fact in gen_facts:
            holo.ingest_text(fact, source_file="gen_health_deepseek.txt")
        total_facts += len(gen_facts)
        print(f"  [deepseek_gen  ] {len(gen_facts)} faits ingérés (DeepSeek)")

    print(f"\n  Total : {total_facts} faits médicaux ingérés")
    print(f"  Énergie hologramme : {holo.energy:.2f}")
    print("=" * 70)

    return holo, manager


def demo_queries(holo: EnterpriseHologram):
    """Démonstration d'interrogation de l'hologramme médical."""
    print("\n" + "=" * 70)
    print("  INTERROGATION DE L'HOLOGRAMME MÉDICAL")
    print("=" * 70)

    questions_medicales = [
        ("Quelle est la dose maximale de paracétamol ?", "traitements", "4g"),
        ("Quels sont les symptômes d'un AVC ?", "pathologies", "affaissée"),
        ("Comment traiter un arrêt cardiaque ?", "urgences", "massage"),
        ("Qu'est-ce que la metformine ?", "traitements", "diabète"),
        ("Quelle est la valeur normale de la glycémie à jeun ?", "diagnostics", "1.10"),
        ("Comment fonctionne le cœur ?", "anatomie", "oreillettes"),
        ("Quels sont les signes de l'appendicite ?", "pathologies", "fosse iliaque"),
        ("Qu'est-ce qu'un IEC ?", "traitements", "conversion"),
    ]

    correct = 0
    for question, expected_category, expected_keyword in questions_medicales:
        results = holo.query(question, k=3)
        found_keyword = False
        best_result = results[0] if results else None
        if results:
            for r in results:
                if expected_keyword.lower() in r["text"].lower():
                    found_keyword = True
                    best_result = r
                    break
            top = best_result or results[0]
            status = "OK" if found_keyword else "KO"
            if found_keyword:
                correct += 1
            print(f"  [{status}] {question}")
            print(f"        → {top['text'][:120]}...")
            print(f"        Score: {top['score']:.3f} | Source: {top.get('source','?')}")
        else:
            print(f"  [KO] {question} → Aucun résultat")
        print()

    print(f"  Résultat : {correct}/{len(questions_medicales)} ({(correct/len(questions_medicales)*100):.0f}%)")
    print("=" * 70)


if __name__ == "__main__":
    holo, manager = create_medical_hologram()
    demo_queries(holo)

    # Sauvegarde optionnelle
    print("\n  Pour chiffrer et sauvegarder :")
    print("    holo.save_encrypted('votre_clé_secrète_hôpital')")
    print("  Pour recharger :")
    print("    holo.load_encrypted('votre_clé_secrète_hôpital', 'data/enterprise/xxxx.enc')")