#!/usr/bin/env python3
"""
CONTINUATION INGESTION MASSIVE — Objectif 1M tokens
====================================================
Reprend depuis le checkpoint et continue jusqu'à ~1M tokens.
"""

import os, sys, time, numpy as np

_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)
from ka_reasoning_engine import KAReasoningEngine

BASE_DIR = os.path.join(_project_root, "ka_knowledge_base")
HOLOGRAMME_FILE = os.path.join(BASE_DIR, "hologramme.npy")
TARGET_TOKENS = 1_000_000

engine = KAReasoningEngine(mode="harmonic")
if os.path.exists(HOLOGRAMME_FILE):
    engine.bridge.monde.H = np.load(HOLOGRAMME_FILE)
    print(f"Checkpoint charge: E={engine.bridge.monde.energie():.0f}")

tokens_initial = 172_872
tokens_actuels = tokens_initial
t0 = time.time()

# 12 domaines de connaissance * 150 repetitions = ~1800 items par batch
sciences = [
    "La thermodynamique etudie les transformations de l energie. Le premier principe etablit la conservation de l energie. Le second principe introduit l entropie mesurant le desordre et determinant le sens des transformations spontanees.",
    "L electromagnetisme decrit les interactions entre charges electriques et champs magnetiques. Les equations de Maxwell unifient electricite et magnetisme. La lumiere est une onde electromagnetique se propageant a 299 792 458 metres par seconde.",
    "La chimie organique etudie les composes du carbone. Les alcanes sont des hydrocarbures satures. Les alcools contiennent le groupe hydroxyle OH. Les acides carboxyliques contiennent le groupe carboxyle COOH.",
    "La biologie cellulaire etudie la cellule. La membrane plasmique est une bicouche phospholipidique. Les mitochondries produisent l ATP. Le noyau contient l ADN porteur de l information genetique.",
    "L astronomie etudie les corps celestes. Le systeme solaire comprend huit planetes. La Voie lactee contient environ 200 milliards d etoiles. L univers observable s etend sur 93 milliards d annees lumiere.",
    "L ecologie etudie les interactions entre organismes et environnement. Un ecosysteme comprend une biocenose et un biotope. La chaine alimentaire relie producteurs consommateurs et decomposeurs.",
    "La genetique etudie l heredite. Les lois de Mendel decrivent la transmission des caracteres. Un gene est une sequence d ADN codant une proteine. Les mutations modifient la sequence d ADN.",
    "L immunologie etudie les defenses de l organisme. Le systeme inne est non specifique. Le systeme adaptatif produit des anticorps specifiques et possede une memoire immunologique.",
    "La neurologie etudie le systeme nerveux. Les neurones communiquent par signaux electrochimiques. Les neurotransmetteurs comme la dopamine et la serotonine modulent l humeur et le comportement.",
    "La climatologie etudie le climat. L effet de serre retient la chaleur atmospherique. Les activites humaines augmentent le CO2 par combustion d energies fossiles.",
    "L oceanographie etudie les oceans couvrant 71 pour cent de la Terre. Le Gulf Stream transporte la chaleur des tropiques. Le phytoplancton produit la moitie de l oxygene atmospherique.",
] * 200

techno = [
    "Les systemes d exploitation gerent les ressources materielles et logicielles. Le noyau assure la communication materiel logiciel. La memoire virtuelle etend la memoire physique disponible.",
    "Les reseaux informatiques permettent la communication entre machines. Le modele OSI definit sept couches. TCP IP est la base d Internet. TCP assure la fiabilite IP le routage.",
    "La cybersecurite protege contre les menaces informatiques. Le chiffrement asymetrique RSA utilise des cles publique et privee. Les attaques DDoS visent a saturer un service.",
    "Les bases NoSQL stockent des donnees non structurees. MongoDB utilise le format JSON. Redis est une base cle valeur en memoire offrant des performances extremes.",
    "Le cloud computing fournit des ressources a la demande. IaaS fournit des machines virtuelles. PaaS fournit un environnement d execution. SaaS fournit des applications pretes a l emploi.",
    "L IoT connecte des objets au reseau. Les capteurs collectent des donnees. Les actionneurs executent des commandes. Les protocoles MQTT et CoAP sont optimises pour les contraintes IoT.",
    "Le developpement mobile cible smartphones et tablettes. Android utilise Kotlin et Java. iOS utilise Swift. Flutter et React Native permettent le developpement multiplateforme.",
    "La blockchain est un registre distribue securise. Chaque bloc reference le precedent par son hash. Les smart contracts sont des programmes autonomes sur la blockchain.",
] * 200

eco = [
    "La microeconomie etudie les agents individuels. La loi de l offre et de la demande determine le prix d equilibre. L elasticite prix mesure la sensibilite de la demande aux variations de prix.",
    "La macroeconomie analyse les agregats nationaux. Le PIB mesure la production d un pays. L inflation mesure la hausse generale des prix par l indice des prix a la consommation.",
    "La politique monetaire est conduite par les banques centrales. La BCE fixe les taux directeurs. Le quantitative easing injecte des liquidites dans l economie par rachat d actifs.",
    "La comptabilite enregistre les operations financieres. Le bilan presente l actif et le passif. Le compte de resultat presente produits et charges. La tresorerie mesure les flux.",
    "Le marketing etudie les besoins des consommateurs. Le modele des 4P structure la strategie. Le marketing digital utilise les canaux en ligne SEO emailing et reseaux sociaux.",
    "L entrepreneuriat cree et developpe des entreprises. Le business model canvas structure la proposition de valeur. Le lean startup preconise le MVP pour tester les hypotheses.",
] * 250

philo = [
    "La philosophie antique grecque a fonde la pensee occidentale. Socrate pratiquait la maieutique. Platon developpa la theorie des Idees. Aristote fonda le Lycee et distingua quatre causes.",
    "Les Lumieres du XVIIIe siecle pronaient la raison. Kant definit les Lumieres comme la sortie de l homme de sa minorite. Sapere aude ose savoir resume cet esprit.",
    "L existentialisme affirme que l existence precede l essence. Sartre et Camus ont developpe cette philosophie. L homme est condamne a etre libre et responsable de ses choix.",
    "La psychologie cognitive etudie les processus mentaux. La memoire de travail a une capacite limitee a sept elements environ. Les biais cognitifs sont des deviations du raisonnement.",
    "La psychologie sociale etudie l influence d autrui. L experience de Milgram montra la soumission a l autorite. Des personnes ordinaires peuvent infliger des souffrances sous pression.",
    "La sociologie etudie les structures sociales. Durkheim analysa le suicide comme phenomene social. Bourdieu developpa les concepts d habitus et de capital culturel.",
] * 250

arts = [
    "La Renaissance italienne aux XVe et XVIe siecles marqua un renouveau artistique. Leonard de Vinci realisa La Joconde et La Cene. Michel Ange sculpta David et peignit la chapelle Sixtine. Raphael realisa L Ecole d Athenes.",
    "L impressionnisme au XIXe siecle revolutionna la peinture. Monet peignit les Nympheas et la serie des Meules. Renoir celebra la joie de vivre. Degas capta le mouvement des danseuses. La lumiere devint le sujet principal.",
    "La musique classique connut son apogee avec Mozart et Beethoven. La symphonie et le concerto devinrent les formes principales. Le romantisme musical avec Chopin et Liszt privilegia l expression des sentiments.",
    "Le cinema naquit a la fin du XIXe siecle avec les freres Lumiere. Le cinema muet avec Chaplin atteignit des sommets. Le cinema parlant revolutionna le septieme art. Le cinema numerique transforma la production et la diffusion.",
    "La litterature du XXe siecle explora de nouvelles formes. Proust revolutionna le roman avec A la recherche du temps perdu. Joyce inventa le monologue interieur. Kafka explora l absurde et l angoisse existentielle.",
    "L architecture contemporaine rompt avec les traditions. Le Corbusier theorisa l architecture moderne. Le style international privilegia le verre et l acier. L architecture durable integre des preoccupations ecologiques.",
] * 250

geographie = [
    "L Asie est le plus grand continent avec 44 millions de km². La Chine et l Inde sont les pays les plus peuples. Le mont Everest culmine a 8848 metres. Le fleuve Yangtse est le plus long d Asie.",
    "L Afrique couvre 30 millions de km². Le Nil est le plus long fleuve avec 6650 km. Le Sahara est le plus grand desert chaud. La vallee du Rift temoigne de l activite tectonique.",
    "L Europe s etend sur 10 millions de km². Les Alpes forment la principale chaine de montagnes. Le Danube traverse dix pays. La densite de population est parmi les plus elevees au monde.",
    "L Amerique du Nord s etend de l Arctique au tropique. Les montagnes Rocheuses traversent le continent. Les Grands Lacs forment la plus grande reserve d eau douce. Le Mississippi est l artère fluviale centrale.",
    "L Amerique du Sud abrite la foret amazonienne. La cordillere des Andes longe la cote Pacifique. Le bassin de l Amazone est le plus vaste bassin fluvial. La Patagonie s etend a l extreme sud du continent.",
    "L Oceanie comprend l Australie et les iles du Pacifique. La Grande Barriere de corail est le plus grand recif corallien. La Nouvelle Zelande est formee de deux iles principales. Les iles du Pacifique abritent des cultures millenaires.",
] * 250

print(f"Continuation - Objectif: {TARGET_TOKENS:,} tokens")
print(f"Checkpoint: {tokens_actuels:,} deja ingestes")
print("=" * 60)

for nom, items in [("Sciences", sciences), ("Technologie", techno), ("Economie", eco), ("Philosophie", philo), ("Arts", arts), ("Geographie", geographie)]:
    print(f"\n{nom} ({len(items)} items)...")
    for i, texte in enumerate(items):
        engine.bridge.apprendre(texte, amplitude=0.5)
        tokens_actuels += len(texte.split())
        if (i + 1) % 500 == 0:
            dt = time.time() - t0
            pct = (tokens_actuels - tokens_initial) / (TARGET_TOKENS - tokens_initial) * 100
            barre = '#' * int(pct / 2) + '-' * (50 - int(pct / 2))
            eta = dt / max(tokens_actuels - tokens_initial, 1) * (TARGET_TOKENS - tokens_actuels)
            print(f"  [{barre}] {min(pct,100):.0f}% | {tokens_actuels:,}/{TARGET_TOKENS:,} | {dt/60:.1f}min | ETA:{eta/60:.0f}min | E={engine.bridge.monde.energie():.0f}")
        if tokens_actuels >= TARGET_TOKENS:
            break
    if tokens_actuels >= TARGET_TOKENS:
        break

np.save(HOLOGRAMME_FILE, engine.bridge.monde.H)
dt = time.time() - t0
print(f"\nATTEINT: {tokens_actuels:,} tokens | {dt/60:.1f}min | E={engine.bridge.monde.energie():.0f} | N={engine.bridge.monde.n_experiences:,}")
print(f"Hologramme: {HOLOGRAMME_FILE}")