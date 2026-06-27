#!/usr/bin/env python3
"""
INJECTION : Connaissances Médicales (PubMed/Medline)
======================================================
Ingère des connaissances médicales couvrant les principales
spécialités dans l'hologramme existant.

Source : PubMed/Medline, guidelines cliniques, revues systématiques
Format : One-pass CPU, 0€.

Usage :
  python injecter_medecine_pubmed.py
"""

import sys, os, time
import numpy as np

_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)
from ka_reasoning_engine import KAReasoningEngine

HOLOGRAMME_FILE = os.path.join(_project_root, "ka_knowledge_base", "hologramme.npy")

engine = KAReasoningEngine(mode="harmonic")
if os.path.exists(HOLOGRAMME_FILE):
    engine.bridge.monde.H = np.load(HOLOGRAMME_FILE)
    print(f"Hologramme chargé : E={engine.bridge.monde.energie():.0f}")
else:
    print("Nouvel hologramme")

t0 = time.time()
compteur = 0

def a(texte, amp=0.6):
    global compteur
    engine.bridge.apprendre(texte, amp)
    compteur += 1
    if compteur % 50 == 0:
        print(f"  {compteur} entrées | E={engine.bridge.monde.energie():.0f}")

# =========================================================================
# CARDIOLOGIE
# =========================================================================
print("\n🫀 Cardiologie")
print("-" * 50)
a("L'hypertension artérielle (HTA) est définie par une pression artérielle systolique supérieure ou égale à 140 mmHg et/ou une pression diastolique supérieure ou égale à 90 mmHg. La prévalence mondiale est d'environ 1.28 milliard d'adultes. Le traitement de première intention associe les mesures hygiéno-diététiques (réduction sodée, activité physique, perte de poids) et les inhibiteurs de l'enzyme de conversion (IEC) ou antagonistes des récepteurs de l'angiotensine II (ARA2).")
a("L'infarctus du myocarde avec sus-décalage du segment ST (STEMI) est une urgence vitale nécessitant une reperfusion coronaire dans les 90 minutes suivant le premier contact médical. La prise en charge pré-hospitalière inclut l'administration d'aspirine 250 mg et la réalisation d'un ECG 18 dérivations. L'angioplastie primaire avec pose de stent est le gold standard, supérieure à la fibrinolyse.")
a("L'insuffisance cardiaque touche environ 64 millions de personnes dans le monde. La fraction d'éjection du ventricule gauche (FEVG) distingue l'insuffisance cardiaque à FEVG préservée (supérieure ou égale à 50%) et réduite (inférieure à 40%). Le traitement de l'IC à FEVG réduite repose sur les quatre piliers : bêtabloquants, IEC/ARA2, antagonistes des récepteurs minéralocorticoïdes, et inhibiteurs du SGLT2 (gliflozines).")
a("La fibrillation atriale est le trouble du rythme cardiaque le plus fréquent, touchant environ 37 millions de personnes. Le score CHA2DS2-VASc évalue le risque thromboembolique et guide l'indication d'une anticoagulation orale. Les anticoagulants oraux directs (AOD : rivaroxaban, apixaban, dabigatran) ont démontré une non-infériorité par rapport aux antivitamines K avec un risque hémorragique intracrânien réduit.")
a("Les statines (atorvastatine, rosuvastatine) réduisent le LDL-cholestérol et le risque cardiovasculaire. Une méta-analyse de 170 000 patients a montré une réduction de 21% des événements cardiovasculaires majeurs par mmol/L de LDL réduit. L'ézétimibe et les inhibiteurs de PCSK9 (évolocumab, alirocumab) offrent des options supplémentaires pour les patients intolérants ou insuffisamment contrôlés.")

# =========================================================================
# PNEUMOLOGIE
# =========================================================================
print("\n🫁 Pneumologie")
print("-" * 50)
a("La bronchopneumopathie chronique obstructive (BPCO) est la troisième cause de mortalité mondiale. Le diagnostic repose sur un rapport VEMS/CVF inférieur à 0.70 après bronchodilatateur. Le tabagisme est responsable de 80% des cas. Les bronchodilatateurs de longue durée d'action (LABA, LAMA) constituent le traitement de fond.")
a("L'asthme affecte environ 300 millions de personnes dans le monde. La classification GINA (Global Initiative for Asthma) guide la prise en charge par paliers. Le traitement de fond repose sur les corticostéroïdes inhalés (CSI) seuls ou associés aux bêta-2 agonistes de longue durée d'action. La spirométrie avec test de réversibilité confirme le diagnostic.")
a("L'embolie pulmonaire est la troisième maladie cardiovasculaire aiguë après l'infarctus et l'AVC. Le score de Wells évalue la probabilité clinique. Le dosage des D-dimères (seuil ajusté à l'âge) permet d'exclure le diagnostic chez les patients à probabilité faible ou intermédiaire. L'angioscanner thoracique est l'examen de référence.")
a("Le syndrome d'apnées obstructives du sommeil (SAOS) touche environ 1 milliard de personnes dans le monde. L'index d'apnées-hypopnées (IAH) supérieur à 5 par heure chez un patient symptomatique confirme le diagnostic. La pression positive continue (PPC) est le traitement de référence. Les conséquences cardiovasculaires et neurocognitives sont majeures en l'absence de traitement.")
a("La pneumonie communautaire est une infection aiguë du parenchyme pulmonaire. Streptococcus pneumoniae est le pathogène le plus fréquent. Le score CURB-65 évalue la gravité : confusion, urée supérieure à 7 mmol/L, fréquence respiratoire supérieure ou égale à 30/min, pression artérielle systolique inférieure à 90 mmHg, âge supérieur ou égal à 65 ans. L'amoxicilline est le traitement probabiliste de première intention en ambulatoire.")

# =========================================================================
# INFECTIOLOGIE
# =========================================================================
print("\n🦠 Infectiologie")
print("-" * 50)
a("Le sepsis est défini comme une dysfonction d'organe menaçant le pronostic vital causée par une réponse inappropriée de l'hôte à une infection. Le score SOFA (Sequential Organ Failure Assessment) évalue la dysfonction d'organe. Le quick SOFA (qSOFA) est un outil de dépistage rapide. Les hémocultures doivent être prélevées avant toute antibiothérapie.")
a("La résistance aux antibiotiques est une menace majeure de santé publique. En 2019, 1.27 million de décès étaient directement attribuables à la résistance bactérienne. Les bactéries multirésistantes (BMR) incluent le Staphylococcus aureus résistant à la méticilline (SARM), les entérobactéries productrices de bêta-lactamases à spectre étendu (BLSE), et Pseudomonas aeruginosa résistant aux carbapénèmes.")
a("Le VIH/SIDA a infecté environ 84 millions de personnes depuis le début de l'épidémie. Les traitements antirétroviraux (ARV) ont transformé le pronostic en maladie chronique. La trithérapie associe deux inhibiteurs nucléosidiques de la transcriptase inverse (INTI) et un troisième agent (inhibiteur de l'intégrase ou inhibiteur de protéase). La prophylaxie pré-exposition (PrEP) réduit le risque de transmission de plus de 99%.")
a("La tuberculose reste la première cause de mortalité infectieuse dans le monde. Mycobacterium tuberculosis est le bacille responsable. Le traitement standard de 6 mois associe rifampicine, isoniazide, pyrazinamide et éthambutol pendant 2 mois, suivi de rifampicine et isoniazide pendant 4 mois. L'émergence de souches multi-résistantes (MDR-TB) et ultra-résistantes (XDR-TB) constitue un défi thérapeutique majeur.")
a("Le paludisme, causé par Plasmodium falciparum principalement, a causé 619 000 décès en 2021, dont 95% en Afrique subsaharienne. Les combinaisons thérapeutiques à base d'artémisinine (ACT) sont le traitement de première intention. Le vaccin RTS,S/AS01 (Mosquirix) a montré une efficacité de 30-40% contre le paludisme sévère chez l'enfant.")

# =========================================================================
# ONCOLOGIE
# =========================================================================
print("\n🔬 Oncologie")
print("-" * 50)
a("Le cancer est la deuxième cause de mortalité mondiale avec environ 20 millions de nouveaux cas par an. Les cancers les plus fréquents sont le cancer du poumon (2.5 millions), du sein (2.3 millions), colorectal (1.9 million), de la prostate (1.5 million) et gastrique (1 million). Le tabagisme est le facteur de risque évitable le plus important.")
a("L'immunothérapie a révolutionné le traitement du cancer. Les inhibiteurs de points de contrôle immunitaires (anti-PD-1 : pembrolizumab, nivolumab ; anti-PD-L1 : atézolizumab ; anti-CTLA-4 : ipilimumab) restaurent la capacité du système immunitaire à reconnaître et détruire les cellules tumorales. Le prix Nobel de médecine 2018 a été attribué à James Allison et Tasuku Honjo pour cette découverte.")
a("Les thérapies ciblées agissent sur des altérations moléculaires spécifiques des cellules tumorales. L'imatinib, inhibiteur de tyrosine kinase BCR-ABL, a transformé le pronostic de la leucémie myéloïde chronique. Le trastuzumab cible le récepteur HER2 dans le cancer du sein. Les inhibiteurs de BRAF (vémurafénib) et MEK traitent le mélanome métastatique avec mutation BRAF V600E.")
a("Le dépistage organisé du cancer permet une détection précoce. Le cancer du sein bénéficie d'un dépistage par mammographie tous les 2 ans de 50 à 74 ans. Le cancer colorectal est dépisté par test immunologique de recherche de sang occulte dans les selles (FIT) tous les 2 ans suivi d'une coloscopie si positif. Le cancer du col de l'utérus est dépisté par frottis cervico-utérin tous les 3 ans entre 25 et 65 ans.")
a("La radiothérapie utilise des rayonnements ionisants pour détruire les cellules tumorales. La radiothérapie conformationnelle avec modulation d'intensité (RCMI) permet de délivrer une dose élevée à la tumeur en épargnant les tissus sains. La protonthérapie offre une précision balistique supérieure grâce au pic de Bragg. Environ 60% des patients atteints de cancer bénéficient d'une radiothérapie.")

# =========================================================================
# NEUROLOGIE
# =========================================================================
print("\n🧠 Neurologie")
print("-" * 50)
a("L'accident vasculaire cérébral (AVC) est la deuxième cause de mortalité mondiale. L'AVC ischémique représente 85% des cas. La thrombolyse intraveineuse par altéplase (rt-PA) doit être administrée dans les 4.5 heures suivant le début des symptômes. La thrombectomie mécanique est indiquée pour les occlusions proximales jusqu'à 6 heures (voire 24h en cas de mismatch favorable).")
a("La maladie d'Alzheimer est la cause la plus fréquente de démence, touchant environ 55 millions de personnes. Les lésions neuropathologiques caractéristiques sont les plaques amyloïdes extracellulaires (peptide bêta-amyloïde) et les dégénérescences neurofibrillaires intracellulaires (protéine tau hyperphosphorylée). Les anticorps monoclonaux anti-amyloïde (aducanumab, lécanémab) ont montré une réduction modeste du déclin cognitif.")
a("La maladie de Parkinson est la deuxième maladie neurodégénérative la plus fréquente. Elle est caractérisée par une perte progressive des neurones dopaminergiques de la substance noire pars compacta. La triade classique associe tremblement de repos, rigidité plastique et akinésie. La lévodopa reste le traitement symptomatique le plus efficace après plus de 50 ans d'utilisation. La stimulation cérébrale profonde du noyau sous-thalamique améliore les fluctuations motrices.")
a("La sclérose en plaques est une maladie auto-immune démyélinisante du système nerveux central touchant 2.8 millions de personnes. Les formes récurrentes-rémittentes (85% des cas) bénéficient de traitements de fond immunomodulateurs (interféron bêta, acétate de glatiramère) ou immunosuppresseurs (natalizumab, fingolimod, ocrélizumab). L'IRM cérébrale et médullaire est l'examen de référence.")
a("L'épilepsie affecte environ 50 millions de personnes dans le monde. Les crises généralisées tonico-cloniques et les absences sont les formes les plus connues. Le valproate de sodium, le lévétiracétam et la lamotrigine sont des antiépileptiques de première ligne. Environ 30% des patients sont pharmaco-résistants et peuvent bénéficier d'une chirurgie de l'épilepsie.")

# =========================================================================
# ENDOCRINOLOGIE
# =========================================================================
print("\n🦋 Endocrinologie")
print("-" * 50)
a("Le diabète de type 2 touche environ 537 millions d'adultes dans le monde. La metformine est le traitement de première intention. Les agonistes du récepteur GLP-1 (sémaglutide, liraglutide) et les inhibiteurs SGLT2 (empagliflozine, dapagliflozine) ont démontré des bénéfices cardiovasculaires et rénaux au-delà du contrôle glycémique. L'hémoglobine glyquée (HbA1c) reflète l'équilibre glycémique des 3 derniers mois.")
a("Les dysthyroïdies sont parmi les pathologies endocriniennes les plus fréquentes. L'hypothyroïdie primaire, le plus souvent d'origine auto-immune (thyroïdite de Hashimoto), est traitée par lévothyroxine. L'hyperthyroïdie, principalement la maladie de Basedow, peut bénéficier d'antithyroïdiens de synthèse, d'iode radioactif ou de chirurgie. La TSH est le marqueur le plus sensible de la fonction thyroïdienne.")
a("L'obésité est une maladie chronique définie par un indice de masse corporelle (IMC) supérieur ou égal à 30 kg/m². La prévalence mondiale a triplé depuis 1975. La chirurgie bariatrique (sleeve gastrectomie, bypass gastrique) est indiquée pour les IMC supérieurs à 40 ou supérieurs à 35 avec comorbidités. Les agonistes GLP-1 (sémaglutide) ont montré une perte de poids de 15% en moyenne.")
a("L'ostéoporose est caractérisée par une diminution de la densité minérale osseuse avec un T-score inférieur à -2.5 en ostéodensitométrie. Les biphosphonates (alendronate, risédronate, zolédronate) sont le traitement de première intention. Le dénosumab, anticorps monoclonal anti-RANKL, et le tériparatide, analogue de la parathormone, offrent des alternatives. La supplémentation en calcium et vitamine D est systématique.")
a("Le syndrome de Cushing résulte d'une exposition prolongée à un excès de glucocorticoïdes. Les causes exogènes (corticothérapie prolongée) sont les plus fréquentes. La maladie de Cushing (adénome hypophysaire corticotrope) est la cause endogène principale. Le diagnostic repose sur le test de freinage minute à la dexaméthasone, le cortisol libre urinaire des 24h et le cortisol salivaire à minuit.")

# =========================================================================
# GASTRO-ENTÉROLOGIE
# =========================================================================
print("\n🫄 Gastro-entérologie")
print("-" * 50)
a("La maladie de Crohn et la rectocolite hémorragique sont les principales maladies inflammatoires chroniques intestinales (MICI). Elles touchent environ 10 millions de personnes. La calprotectine fécale est un marqueur non invasif de l'inflammation intestinale. Les anti-TNF alpha (infliximab, adalimumab) et les anticorps anti-intégrine (védolizumab) ont transformé la prise en charge des formes réfractaires.")
a("La cirrhose est le stade terminal des hépatopathies chroniques. Les causes principales sont l'alcool, les hépatites virales B et C, et la stéatohépatite non alcoolique (NASH). Le score de Child-Pugh et le score MELD évaluent la sévérité. La transplantation hépatique est le seul traitement curatif de la cirrhose décompensée. L'élastométrie impulsionnelle (FibroScan) permet une évaluation non invasive de la fibrose.")
a("Les hépatites virales constituent un problème majeur de santé publique. L'hépatite B chronique touche 296 millions de personnes. Les analogues nucléosidiques (ténofovir, entécavir) permettent un contrôle virologique durable. L'hépatite C peut désormais être guérie dans plus de 95% des cas grâce aux antiviraux à action directe (AAD : sofosbuvir, velpatasvir, glécaprévir/pibrentasvir) en 8 à 12 semaines.")
a("Le reflux gastro-œsophagien (RGO) affecte environ 20% de la population adulte. Le diagnostic repose sur la clinique et peut être confirmé par pH-métrie des 24h. Les inhibiteurs de la pompe à protons (IPP : oméprazole, ésoméprazole, pantoprazole) constituent le traitement de référence. La chirurgie anti-reflux (fundoplicature de Nissen) est réservée aux formes sévères et rebelles.")
a("La maladie cœliaque est une entéropathie auto-immune déclenchée par l'ingestion de gluten chez des sujets génétiquement prédisposés (HLA-DQ2/DQ8). La prévalence est d'environ 1%. Le diagnostic repose sur la sérologie (anticorps anti-transglutaminase IgA) confirmée par la biopsie duodénale (atrophie villositaire). Le régime sans gluten strict à vie est le seul traitement.")

# =========================================================================
# NÉPHROLOGIE
# =========================================================================
print("\n🫘 Néphrologie")
print("-" * 50)
a("La maladie rénale chronique (MRC) touche environ 10% de la population mondiale. Le débit de filtration glomérulaire estimé (DFGe) par la formule CKD-EPI définit les stades de sévérité. Les inhibiteurs du SGLT2 et les antagonistes des récepteurs minéralocorticoïdes (finérénone) ont démontré une néphroprotection indépendante du contrôle glycémique et tensionnel.")
a("L'insuffisance rénale aiguë est définie par les critères KDIGO : augmentation de la créatinine sérique de 26.5 μmol/L en 48h ou de 1.5 fois la valeur de base en 7 jours, ou oligurie inférieure à 0.5 mL/kg/h pendant 6 heures. La nécrose tubulaire aiguë est la cause la plus fréquente en milieu hospitalier. L'épuration extra-rénale (hémodialyse, hémodiafiltration) est indiquée en cas de complications menaçantes.")
a("La lithiase rénale affecte environ 12% de la population. Les calculs d'oxalate de calcium sont les plus fréquents (80%). Le scanner abdominal sans injection est l'examen de référence avec une sensibilité de 97%. La lithotritie extracorporelle et l'urétéroscopie avec laser Holmium sont les traitements de première intention. La prévention repose sur l'hyperdiurèse (2-3 L/jour) et la correction des anomalies métaboliques.")
a("Les glomérulonéphrites sont des maladies immunologiques touchant le glomérule rénal. La maladie de Berger (néphropathie à IgA) est la plus fréquente. La glomérulonéphrite extra-membraneuse est la principale cause de syndrome néphrotique de l'adulte. La ponction biopsie rénale permet le diagnostic histologique précis. Les corticostéroïdes et immunosuppresseurs (cyclophosphamide, rituximab) constituent le traitement.")
a("La transplantation rénale est le traitement de choix de l'insuffisance rénale terminale. La survie du greffon à 10 ans est de 60-70% pour les donneurs décédés et 80-90% pour les donneurs vivants. Le traitement immunosuppresseur d'entretien associe classiquement un inhibiteur de la calcineurine (tacrolimus), un antimétabolite (mycophénolate mofétil) et une corticothérapie.")

# =========================================================================
# DERMATOLOGIE
# =========================================================================
print("\n🧴 Dermatologie")
print("-" * 50)
a("Le mélanome est la forme la plus agressive de cancer cutané. La règle ABCDE (Asymétrie, Bords irréguliers, Couleur inhomogène, Diamètre supérieur à 6mm, Évolution) guide le dépistage. L'indice de Breslow (épaisseur tumorale en mm) est le facteur pronostique principal. L'immunothérapie anti-PD-1 (pembrolizumab, nivolumab) et les thérapies ciblées anti-BRAF/MEK ont révolutionné le traitement du mélanome métastatique.")
a("Le psoriasis touche environ 125 millions de personnes. Il s'agit d'une maladie inflammatoire chronique à médiation immune (voie IL-23/Th17). Les formes légères à modérées bénéficient de traitements topiques (dermocorticoïdes, analogues de la vitamine D). Les formes sévères répondent aux biothérapies ciblant le TNF-alpha (adalimumab), l'IL-17 (sécukinumab) ou l'IL-23 (guselkumab, risankizumab).")
a("La dermatite atopique (eczéma atopique) est une dermatose inflammatoire chronique prurigineuse. La mutation du gène de la filaggrine est le principal facteur de prédisposition génétique. Le traitement repose sur l'hydratation cutanée, les dermocorticoïdes et les inhibiteurs topiques de la calcineurine (tacrolimus). Le dupilumab, anticorps monoclonal anti-IL-4/IL-13, a transformé la prise en charge des formes sévères.")

# =========================================================================
# RHUMATOLOGIE
# =========================================================================
print("\n🦴 Rhumatologie")
print("-" * 50)
a("La polyarthrite rhumatoïde touche environ 1% de la population adulte. Elle est caractérisée par une synovite inflammatoire chronique avec production d'auto-anticorps (facteur rhumatoïde, anticorps anti-CCP). La stratégie treat-to-target vise la rémission clinique. Le méthotrexate est le traitement de fond de première intention. Les biothérapies anti-TNF et les inhibiteurs de JAK complètent l'arsenal thérapeutique.")
a("L'arthrose est la maladie articulaire la plus fréquente, touchant 500 millions de personnes. Elle résulte d'une dégradation du cartilage articulaire associée à une inflammation synoviale de bas grade. La gonarthrose (genou) et la coxarthrose (hanche) sont les localisations les plus invalidantes. La prise en charge associe exercice physique, perte de poids, antalgiques et anti-inflammatoires. La prothèse articulaire est le traitement ultime.")
a("La goutte est une arthropathie microcristalline liée au dépôt de cristaux d'urate de sodium. L'hyperuricémie (supérieure à 420 μmol/L chez l'homme, 360 chez la femme) est le facteur de risque principal. La crise aiguë est traitée par colchicine ou AINS. Le traitement de fond (allopurinol, fébuxostat) vise une uricémie inférieure à 300 μmol/L pour dissoudre les tophi.")
a("L'ostéoporose est définie par un T-score inférieur à -2.5 en ostéodensitométrie DEXA. Les fractures vertébrales, du col fémoral et du poignet sont les plus fréquentes. Les biphosphonates (alendronate, zolédronate) réduisent le risque de fracture de 40-70%. Le tériparatide (PTH recombinante) stimule la formation osseuse dans les formes sévères. Le traitement hormonal substitutif est réservé aux femmes ménopausées symptomatiques de moins de 60 ans.")
a("La spondyloarthrite ankylosante est le prototype des spondyloarthrites axiales. Elle est fortement associée à l'antigène HLA-B27. Les sacro-iliites radiographiques sont caractéristiques. Les anti-inflammatoires non stéroïdiens (AINS) sont le traitement de première intention. Les anti-TNF alpha (infliximab, adalimumab, étanercept) et anti-IL-17 (sécukinumab) sont indiqués dans les formes actives persistantes.")

# =========================================================================
# PÉDIATRIE
# =========================================================================
print("\n👶 Pédiatrie")
print("-" * 50)
a("Le calendrier vaccinal français rend obligatoires 11 vaccins pour les nourrissons nés depuis le 1er janvier 2018 : diphtérie, tétanos, poliomyélite, coqueluche, Haemophilus influenzae b, hépatite B, pneumocoque, méningocoque C, rougeole, oreillons, rubéole. La vaccination contre le papillomavirus (HPV) est recommandée pour les filles et les garçons de 11 à 14 ans.")
a("La bronchiolite aiguë du nourrisson est une infection virale saisonnière causée principalement par le virus respiratoire syncytial (VRS). Elle touche 30% des nourrissons chaque année. Le traitement est symptomatique : désobstruction rhinopharyngée, fractionnement des repas, surveillance. La kinésithérapie respiratoire n'est plus recommandée. Le nirsévimab (Beyfortus), anticorps monoclonal, prévient les formes sévères.")
a("L'autisme (trouble du spectre de l'autisme, TSA) touche environ 1 enfant sur 100. Le diagnostic repose sur l'observation clinique des difficultés de communication sociale et des comportements restreints et répétitifs. L'intervention précoce (méthode ABA, TEACCH, Denver) améliore le pronostic fonctionnel. Les facteurs génétiques sont prédominants avec une héritabilité estimée à 80%. La vaccination n'est PAS associée à l'autisme.")
a("La mort subite du nourrisson (MSN) a une incidence de 0.3 pour 1 000 naissances vivantes en France. Les recommandations de couchage sur le dos, dans une turbulette, sur un matelas ferme, sans oreiller ni couverture, dans la chambre des parents mais dans un lit séparé, et l'allaitement maternel ont permis de réduire l'incidence de 75% depuis les années 1990.")
a("Le diabète de type 1 est la maladie métabolique chronique la plus fréquente de l'enfant. Il résulte d'une destruction auto-immune des cellules bêta pancréatiques productrices d'insuline. L'insulinothérapie par pompe à insuline ou multi-injections est indispensable à vie. L'hémoglobine glyquée cible est inférieure à 7% pour prévenir les complications micro et macrovasculaires à long terme.")

# =========================================================================
# GYNÉCOLOGIE-OBSTÉTRIQUE
# =========================================================================
print("\n🤰 Gynécologie-Obstétrique")
print("-" * 50)
a("La pré-éclampsie est une complication hypertensive de la grossesse survenant après 20 semaines d'aménorrhée, associant une HTA (supérieure à 140/90 mmHg) et une protéinurie (supérieure à 0.3g/24h). L'aspirine à faible dose (100-160 mg/jour) débutée avant 16 SA réduit le risque de pré-éclampsie précoce. L'accouchement est le seul traitement curatif.")
a("Le cancer du col de l'utérus est causé par une infection persistante par les papillomavirus humains (HPV) à haut risque oncogène (HPV 16, 18 principalement). La vaccination anti-HPV et le dépistage par frottis cervico-utérin (ou test HPV) tous les 3 à 5 ans permettent une prévention efficace. La conisation est le traitement des lésions précancéreuses (CIN 2-3).")
a("L'endométriose touche environ 10% des femmes en âge de procréer. Elle est définie par la présence de tissu endométrial fonctionnel en dehors de la cavité utérine. Les symptômes incluent dysménorrhée, douleurs pelviennes chroniques, dyspareunie et infertilité. Le diagnostic de certitude est coelioscopique. La prise en charge associe traitements hormonaux (pilule continue, dispositif intra-utérin au lévonorgestrel) et chirurgie.")
a("Le cancer du sein est le cancer le plus fréquent chez la femme. La mammographie de dépistage est recommandée tous les 2 ans de 50 à 74 ans. Les mutations BRCA1/2 prédisposent au cancer du sein et de l'ovaire (syndrome de prédisposition héréditaire). La chirurgie conservatrice (tumorectomie) suivie de radiothérapie est équivalente à la mastectomie en termes de survie pour les tumeurs de moins de 3 cm.")

# =========================================================================
# OPHTALMOLOGIE
# =========================================================================
print("\n👁️ Ophtalmologie")
print("-" * 50)
a("La dégénérescence maculaire liée à l'âge (DMLA) est la première cause de malvoyance après 50 ans dans les pays développés. La forme humide (néovasculaire) bénéficie des injections intravitréennes d'anti-VEGF (ranibizumab, aflibercept, bévacizumab). La forme sèche (atrophique) n'a pas de traitement curatif mais une supplémentation en vitamines et antioxydants (AREDS2) peut ralentir la progression.")
a("La cataracte est l'opacification du cristallin, première cause de cécité curable dans le monde. La chirurgie par phacoémulsification avec implantation de cristallin artificiel est l'une des interventions les plus pratiquées avec un taux de succès supérieur à 95%. L'opération est généralement réalisée en ambulatoire sous anesthésie topique.")
a("Le glaucome chronique à angle ouvert est une neuropathie optique progressive, deuxième cause de cécité mondiale. Le seul facteur de risque modifiable est l'hypertonie oculaire. Les analogues de prostaglandines (latanoprost) en collyre constituent le traitement de première intention. La trabéculoplastie au laser SLT et la chirurgie filtrante (trabéculectomie) complètent l'arsenal thérapeutique.")

# =========================================================================
# PSYCHIATRIE
# =========================================================================
print("\n🧘 Psychiatrie")
print("-" * 50)
a("Le trouble dépressif majeur touche environ 280 millions de personnes. Les inhibiteurs sélectifs de la recapture de la sérotonine (ISRS : fluoxétine, sertraline, escitalopram) sont le traitement pharmacologique de première intention. La psychothérapie cognitivo-comportementale (TCC) a une efficacité démontrée. L'association pharmacothérapie et psychothérapie est supérieure à chaque modalité seule.")
a("Les troubles anxieux sont les troubles psychiatriques les plus fréquents (prévalence vie entière 25%). Le trouble anxieux généralisé, le trouble panique, la phobie sociale et les phobies spécifiques en sont les principales formes. Les ISRS, la venlafaxine et la prégabaline sont les traitements de référence. Les benzodiazépines, efficaces à court terme, exposent à un risque de dépendance.")
a("La schizophrénie est un trouble psychiatrique chronique affectant environ 24 millions de personnes. Elle associe des symptômes positifs (hallucinations, délires), négatifs (émoussement affectif, retrait social) et cognitifs. Les antipsychotiques de seconde génération (aripiprazole, olanzapine, rispéridone) sont privilégiés pour leur meilleure tolérance neurologique. La réhabilitation psychosociale améliore le pronostic fonctionnel.")
a("Le trouble bipolaire touche environ 60 millions de personnes. Il alterne des épisodes maniaques (ou hypomaniaques) et dépressifs. Le lithium reste le traitement de référence (thymorégulateur) avec un effet anti-suicide démontré. Les anticonvulsivants (valproate, lamotrigine) et les antipsychotiques atypiques (quétiapine, olanzapine) sont des alternatives. Le valproate est contre-indiqué chez la femme en âge de procréer.")
a("Le trouble de stress post-traumatique (TSPT) survient après exposition à un événement traumatique. La prévalence vie entière est d'environ 7%. La psychothérapie centrée sur le trauma (EMDR, thérapie d'exposition prolongée, TCC) est le traitement de première intention. Les ISRS (paroxétine, sertraline) ont une indication dans le TSPT. Le risque suicidaire doit être systématiquement évalué.")

# =========================================================================
# SAUVEGARDE
# =========================================================================

np.save(HOLOGRAMME_FILE, engine.bridge.monde.H)
dt = time.time() - t0

print(f"\n{'='*60}")
print(f"✅ INJECTION MÉDICALE TERMINÉE")
print(f"{'='*60}")
print(f"  Connaissances ajoutées : {compteur} entrées")
print(f"  Temps d'injection      : {dt:.1f}s")
print(f"  Énergie hologramme     : {engine.bridge.monde.energie():.0f}")
print(f"  Hologramme             : {HOLOGRAMME_FILE}")
print(f"\n  14 spécialités médicales couvertes (PubMed)")
print(f"  Cardiologie, Pneumologie, Infectiologie, Oncologie,")
print(f"  Neurologie, Endocrinologie, Gastro-entérologie,")
print(f"  Néphrologie, Dermatologie, Rhumatologie, Pédiatrie,")
print(f"  Gynécologie-Obstétrique, Ophtalmologie, Psychiatrie")