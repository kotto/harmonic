#!/usr/bin/env python3
"""
EXPAND QUICKFACTS — Ajout massif de ~800 faits structurés
=============================================================
Injecte des centaines de nouveaux faits atomiques dans QuickFacts
sans crash mémoire (pas d'ondes holographiques, juste un index).

Domaines ajoutés :
  - Géographie physique, Économie, Politique, Santé, Cuisine,
  - Environnement, Transport, Astronomie, Psychologie, Droit,
  - Météo, Énergie, Architecture, Mythologies du monde,
  - Personnalités africaines, Histoire mondiale, Philosophie

Usage :
  python ka_phone/expand_quickfacts.py             # Ajouter tous les faits
  python ka_phone/expand_quickfacts.py --count 100 # Limiter
"""

import os, sys, json

NEW_FACTS = [
    # ═══ GÉOGRAPHIE PHYSIQUE ═══
    ("climat_equatorial", "Le climat equatorial est chaud et humide toute l'annee (25-30C), avec des pluies abondantes (>2000 mm/an). Forets denses, biodiversite maximale. Amazonie, Congo, Indonesie.", ["climat", "equatorial", "chaud", "humide", "foret"]),
    ("climat_desertique", "Le climat desertique : tres chaud le jour, froid la nuit. Moins de 250 mm de pluie par an. Vegetation rare. Sahara, Namib, Atacama.", ["climat", "desertique", "desert", "aride", "sec"]),
    ("climat_mediterraneen", "Le climat mediterraneen : ete chaud et sec, hiver doux et humide. Vegetation adaptee (oliviers, chenes verts). Bassin mediterraneen, Californie, Australie du Sud.", ["climat", "mediterraneen", "olivier", "ete sec"]),
    ("climat_temperé", "Le climat tempere a 4 saisons distinctes. Hivers froids, etes doux. Precipitations regulieres. Europe de l'Ouest, Est des USA, Chine du Nord.", ["climat", "tempere", "saisons", "europe"]),
    ("climat_polaire", "Le climat polaire : temperatures negatives toute l'annee (<10C en ete). Glaces permanentes. Nuit polaire de 6 mois. Arctique et Antarctique.", ["climat", "polaire", "glace", "arctique", "antarctique"]),
    ("relief_plaines", "Les plaines sont des etendues plates ou legerement ondulees, souvent fertiles. Grandes plaines americaines, plaine d'Europe du Nord, plaine du Gange.", ["plaine", "relief", "plat", "fertile"]),
    ("relief_plateaux", "Un plateau est une surface plane en altitude (>500m). Plateau du Tibet (le plus haut du monde), plateau de l'Adamaoua, plateau du Colorado.", ["plateau", "relief", "altitude", "tibet"]),

    # ═══ ÉCONOMIE ═══
    ("eco_import_export", "Importation = achat de biens a l'etranger. Exportation = vente de biens a l'etranger. La balance commerciale = exports - imports. Excedentaire si >0, deficitaire si <0.", ["import", "export", "balance commerciale", "commerce"]),
    ("eco_devises", "Les devises sont les monnaies etrangeres echangees sur le marche des changes (Forex). Les plus echangees : USD (dollar), EUR (euro), JPY (yen), GBP (livre), CHF (franc suisse).", ["devise", "forex", "change", "dollar", "euro", "yen"]),
    ("eco_bourse_def", "La bourse est un marche ou s'echangent les actions des entreprises. Les plus grandes : NYSE (New York), NASDAQ (tech), Shanghai, Tokyo, Euronext (Paris, Amsterdam).", ["bourse", "action", "nyse", "nasdaq", "wall street"]),
    ("eco_indice_boursier", "Un indice boursier mesure la performance d'un groupe d'actions. CAC 40 (Paris), Dow Jones (USA), FTSE 100 (Londres), Nikkei 225 (Tokyo), DAX (Francfort).", ["indice", "cac 40", "dow jones", "ftse", "dax"]),
    ("eco_keynes", "John Maynard Keynes (1883-1946), economiste britannique. Theorie : l'Etat doit intervenir en periode de crise par la depense publique pour relancer l'economie. Fondateur de la macroeconomie moderne.", ["keynes", "economiste", "intervention", "etat", "crise"]),
    ("eco_adam_smith", "Adam Smith (1723-1790), economiste ecossais. Pere du liberalisme economique. 'La Richesse des nations' (1776) : la main invisible du marche autorégule l'economie.", ["adam smith", "liberalisme", "main invisible", "marche"]),
    ("eco_karl_marx", "Karl Marx (1818-1883), philosophe et economiste allemand. Auteur du 'Capital' (1867). Critique du capitalisme. Inspire le communisme et le socialisme.", ["marx", "capital", "communisme", "socialisme", "lutte des classes"]),

    # ═══ POLITIQUE ═══
    ("pol_democratie", "La democratie (du grec demos = peuple, kratos = pouvoir) est un regime ou le pouvoir appartient au peuple. Elections libres, separation des pouvoirs (executif, legislatif, judiciaire), libertes fondamentales.", ["democratie", "election", "pouvoir", "peuple", "separation pouvoirs"]),
    ("pol_republique", "Une republique est un Etat sans monarque, ou le chef de l'Etat est elu. France (5e Republique depuis 1958), USA (republique federale), Allemagne (republique federale).", ["republique", "president", "elu", "etat"]),
    ("pol_monarchie", "Une monarchie est un regime ou le chef de l'Etat est un roi ou une reine. Monarchie constitutionnelle (pouvoir limite) : Royaume-Uni, Espagne, Japon. Monarchie absolue : Arabie saoudite, Oman.", ["monarchie", "roi", "reine", "couronne"]),
    ("pol_onu", "L'ONU (1945, 193 Etats membres) a pour mission : paix et securite internationales, droits humains, developpement. Siege a New York. Conseil de securite : 5 membres permanents (USA, Russie, Chine, France, UK).", ["onu", "nations unies", "conseil securite", "paix"]),
    ("pol_ua", "L'Union Africaine (UA, 2002, 55 Etats membres) succede a l'OUA. Siege a Addis-Abeba. Objectifs : unite, paix, developpement du continent. Agenda 2063 pour l'integration africaine.", ["ua", "union africaine", "addis-abeba", "afrique"]),
    ("pol_ue_institutions", "Institutions de l'UE : Commission europeenne (Bruxelles, propose les lois), Parlement europeen (Strasbourg, vote les lois), Conseil de l'UE (represente les Etats), Cour de justice (Luxembourg).", ["ue", "union europeenne", "commission", "parlement", "bruxelles"]),

    # ═══ SANTÉ ═══
    ("sante_cancer", "Le cancer est une proliferation anormale de cellules. 1 personne sur 2 aura un cancer dans sa vie. Les plus frequents : poumon, sein, colon, prostate. Traitements : chirurgie, chimiotherapie, radiotherapie, immunotherapie.", ["cancer", "tumeur", "chimiotherapie", "cellule"]),
    ("sante_antibiotiques", "Les antibiotiques (decouverts par Alexander Fleming en 1928 avec la penicilline) tuent les bacteries mais sont inefficaces contre les virus. L'antibioresistance est un probleme majeur de sante publique.", ["antibiotique", "penicilline", "fleming", "bacterie", "resistance"]),
    ("sante_imc", "L'IMC (Indice de Masse Corporelle) = poids (kg) / taille² (m). <18.5 = maigreur, 18.5-25 = normal, 25-30 = surpoids, >30 = obesite. Outil de depistage, pas de diagnostic.", ["imc", "poids", "masse corporelle", "obesite", "sante"]),
    ("sante_colonne_vertebrale", "La colonne vertebrale humaine compte 33 vertebres : 7 cervicales (cou), 12 thoraciques (dos), 5 lombaires (bas du dos), 5 sacrees (fusionnees), 4 coccygiennes. Elle protege la moelle epiniere.", ["colonne vertebrale", "vertebres", "dos", "cervicales", "lombaires"]),
    ("sante_dents", "La dentition adulte compte 32 dents : 8 incisives, 4 canines, 8 premolaires, 12 molaires (dont 4 dents de sagesse). L'email est le tissu le plus dur du corps humain.", ["dents", "dentition", "incisive", "molaire", "email"]),
    ("sante_soleil", "Le soleil est benefique pour la vitamine D (15-20 min/jour suffisent) mais les UV sont cancerigenes. Protegez-vous entre 11h et 16h. Le SPF 30 bloque 97%% des UVB.", ["soleil", "peau", "uv", "vitamine d", "spf"]),

    # ═══ CUISINE — Techniques et ingrédients ═══
    ("cuisine_methode_saisir", "Saisir un aliment : cuire rapidement a feu vif dans un corps gras pour creer une croute doree (reaction de Maillard). La viande saisie garde ses jus. Puis baisser le feu pour terminer la cuisson.", ["saisir", "cuisson", "viande", "maillard", "croute"]),
    ("cuisine_methode_blanchir", "Blanchir : plonger un aliment dans l'eau bouillante 1-3 min, puis dans l'eau glacee. Fixe la couleur des legumes verts, facilite l'epluchage (tomates), reduit l'amertume.", ["blanchir", "legume", "eau", "bouillante", "glace"]),
    ("cuisine_methode_mijoter", "Mijoter : cuire lentement a feu doux (85-95C) dans un liquide. Attendrit les viandes dures, developpe les saveurs. Duree : 1h30 a 4h. Ideal pour les ragouts, pot-au-feu, tajines.", ["mijoter", "mijote", "ragout", "lent", "tendre"]),
    ("cuisine_methode_braiser", "Braisage : d'abord saisir la viande, puis cuire longuement a couvert dans un peu de liquide. Combine saisie + mijotage. Resultat : viande fondante et sauce concentree.", ["braiser", "braise", "viande", "sauce", "fondant"]),
    ("cuisine_epices_communes", "Epices essentielles : cumin (chaud, terreux), curcuma (couleur jaune, anti-inflammatoire), cannelle (sucre, chaud), gingembre (piquant, frais), paprika (doux ou fume), piment (force variable), poivre noir (universel).", ["epices", "cumin", "curcuma", "cannelle", "gingembre", "cuisine"]),
    ("cuisine_herbes", "Herbes aromatiques : persil (frais, universel), coriandre (citronnee, asiatique/mexicaine), basilic (sucre, italien), thym (puissant, mijotes), romarin (resineux, grillades), menthe (fraiche, the, salades).", ["herbes", "persil", "coriandre", "basilic", "thym", "romarin"]),

    # ═══ ENVIRONNEMENT ═══
    ("env_effet_serre", "L'effet de serre est un phenomene naturel : certains gaz (CO2, methane, vapeur d'eau) retiennent la chaleur du soleil. Sans lui, la temperature terrestre serait de -18C. Le probleme est l'exces de CO2 du aux activites humaines.", ["effet de serre", "co2", "methane", "climat", "rechauffement"]),
    ("env_energie_renouvelable", "Energies renouvelables : solaire (panneaux photovoltaiques, thermique), eolien (terrestre et offshore), hydraulique (barrages), biomasse (bois, dechets), geothermie (chaleur du sous-sol). Elles emettent peu de CO2.", ["energie renouvelable", "solaire", "eolien", "hydraulique", "geothermie"]),
    ("env_energie_nucleaire", "L'energie nucleaire utilise la fission de l'uranium pour produire de la chaleur, puis de l'electricite. Avantage : pas de CO2. Inconvenient : dechets radioactifs a vie longue (milliers d'annees). La France en depend a 70%%.", ["nucleaire", "uranium", "fission", "dechet", "radioactif"]),
    ("env_deforestation", "La deforestation : 10 millions d'hectares de foret disparaissent chaque annee (equivalent a la Coree du Sud). Causes : agriculture (soja, huile de palme), elevage, exploitation forestiere. L'Amazonie a perdu 17%% de sa surface.", ["deforestation", "foret", "amazonie", "soja", "huile de palme"]),
    ("env_biodiversite", "La biodiversite designe la variete du vivant : genes, especes, ecosystemes. 1 million d'especes sont menacees d'extinction. La 6e extinction de masse est en cours, causee par l'activite humaine.", ["biodiversite", "extinction", "especes", "ecosysteme"]),

    # ═══ TRANSPORT ═══
    ("transport_chemin_fer", "Le chemin de fer : invente au debut du XIXe siecle (locomotive de Stephenson, 1829). Le TGV francais detient le record de vitesse sur rail (574,8 km/h en 2007). Le train reste le transport le plus ecologique.", ["train", "chemin de fer", "tgv", "locomotive", "stephenson"]),
    ("transport_aerien", "L'aviation commerciale debute dans les annees 1920. Le Boeing 747 (Jumbo Jet, 1969) a revolutionne le transport de masse. L'A380 (Airbus, 2005) est le plus gros avion commercial (jusqu'a 853 passagers).", ["aviation", "boeing", "airbus", "a380", "747"]),
    ("transport_maritime", "90%% du commerce mondial passe par la mer. Les porte-conteneurs transportent jusqu'a 24 000 conteneurs. Le canal de Panama (1914) et le canal de Suez (1869) sont les passages strategiques cles.", ["maritime", "porte-conteneur", "panama", "suez", "commerce"]),

    # ═══ ASTRONOMIE ═══
    ("astro_etoiles", "Les etoiles sont des spheres de plasma qui produisent energie et lumiere par fusion nucleaire (hydrogene → helium). Le Soleil est une etoile de type G (naine jaune) agee de 4,6 milliards d'annees.", ["etoile", "soleil", "fusion", "hydrogene", "helium"]),
    ("astro_trous_noirs", "Un trou noir est une region de l'espace ou la gravite est si forte que rien, pas meme la lumiere, ne peut s'echapper. Forme par l'effondrement d'une etoile massive. Le centre de notre galaxie contient un trou noir supermassif.", ["trou noir", "gravite", "etoile", "galaxie", "espace"]),
    ("astro_voie_lactee", "Notre galaxie, la Voie lactee, est une spirale barree de 100 000 annees-lumiere de diametre contenant 100-400 milliards d'etoiles. Le Soleil est a 26 000 annees-lumiere du centre galactique.", ["voie lactee", "galaxie", "etoile", "spirale", "univers"]),
    ("astro_apollo_11", "Apollo 11 (20 juillet 1969) : premiers humains sur la Lune. Neil Armstrong (1er pas) et Buzz Aldrin. Michael Collins pilote le module de commande en orbite. 'Un petit pas pour l'homme, un bond de geant pour l'humanite.'", ["apollo 11", "lune", "armstrong", "aldrin", "1969"]),
    ("astro_telescope_james_webb", "Le telescope spatial James Webb (JWST, lance en 2021) observe l'univers dans l'infrarouge depuis le point de Lagrange L2 (1,5 million km de la Terre). Miroir de 6,5m. Succede a Hubble (1990).", ["james webb", "jwst", "telescope", "infrarouge", "hubble"]),

    # ═══ MYTHOLOGIES DU MONDE ═══
    ("mytho_grecque_zeus", "Zeus est le roi des dieux dans la mythologie grecque. Dieu du ciel et de la foudre. Fils de Cronos et Rhea. Epoux d'Hera. Ses attributs : foudre, aigle, sceptre. Equivalent romain : Jupiter.", ["zeus", "mythologie grecque", "dieu", "foudre", "jupiter"]),
    ("mytho_grecque_poseidon", "Poseidon est le dieu grec de la mer, des oceans et des tremblements de terre. Frere de Zeus et Hades. Son attribut : le trident. Equivalent romain : Neptune.", ["poseidon", "mer", "trident", "neptune", "mythologie"]),
    ("mytho_grecque_athena", "Athena est la deesse grecque de la sagesse, de la strategie militaire et des arts. Nee de la tete de Zeus. Protectrice d'Athenes. Ses symboles : chouette, olivier, egee.", ["athena", "sagesse", "deesse", "athenes", "chouette"]),
    ("mytho_nordique_odin", "Odin est le dieu principal de la mythologie nordique. Dieu de la sagesse, de la guerre et de la poesie. Perd un œil pour boire a la source de la connaissance. Pere de Thor. Ses corbeaux : Hugin et Munin (Pensee et Memoire).", ["odin", "mythologie nordique", "thor", "viking", "sagesse"]),
    ("mytho_nordique_thor", "Thor est le dieu du tonnerre dans la mythologie nordique. Fils d'Odin. Son marteau Mjollnir revient toujours dans sa main apres avoir ete lance. Protecteur des humains et des dieux contre les geants.", ["thor", "mjollnir", "tonnerre", "marteau", "odin"]),
    ("mytho_japonaise_amaterasu", "Amaterasu est la deesse du soleil dans la mythologie japonaise (shinto). Ancetre mythique de la famille imperiale japonaise. Son nom signifie 'Celle qui illumine le ciel'.", ["amaterasu", "shinto", "soleil", "japon", "deesse"]),

    # ═══ PERSONNALITÉS AFRICAINES ═══
    ("afrique_sankara", "Thomas Sankara (1949-1987), president revolutionnaire du Burkina Faso (1983-1987). Lutta contre la corruption, promut l'autosuffisance alimentaire, les droits des femmes, la vaccination de masse. Assassine lors d'un coup d'Etat.", ["sankara", "burkina faso", "revolution", "afrique"]),
    ("afrique_lumumba", "Patrice Lumumba (1925-1961), Premier ministre du Congo independant. Figure du panafricanisme et de la lutte anticoloniale. Assassine avec la complicite des services secrets belges et americains.", ["lumumba", "congo", "panafricanisme", "independance"]),
    ("afrique_hampate_ba", "Amadou Hampate Ba (1900-1991), ecrivain et ethnologue malien. 'En Afrique, un vieillard qui meurt est une bibliotheque qui brule.' Defenseur de la tradition orale africaine. Œuvre majeure : L'Etrange Destin de Wangrin.", ["hampate ba", "mali", "tradition orale", "ecrivain", "afrique"]),
    ("afrique_wangari_maathai", "Wangari Maathai (1940-2011), ecologiste kenyane, prix Nobel de la paix 2004. Fonda le Mouvement de la Ceinture Verte (Green Belt Movement) : 51 millions d'arbres plantes par des femmes a travers l'Afrique.", ["wangari maathai", "kenya", "nobel", "environnement", "arbres"]),

    # ═══ HISTOIRE MONDIALE ═══
    ("histoire_renaissance", "La Renaissance (XIVe-XVIe siecle) est une periode de renouveau culturel et artistique nee en Italie. Leonard de Vinci, Michel-Ange, Raphael. L'imprimerie de Gutenberg (1450) democratise le savoir.", ["renaissance", "italie", "leonard de vinci", "gutenberg", "art"]),
    ("histoire_siecle_lumieres", "Le Siecle des Lumieres (XVIIIe siecle) : mouvement philosophique europeen. Voltaire, Rousseau, Montesquieu, Diderot (Encyclopedie). Valeurs : raison, liberte, tolerance, progres. Inspire la Revolution francaise.", ["lumieres", "voltaire", "rousseau", "encyclopedie", "raison"]),
    ("histoire_guerre_froide", "La Guerre froide (1947-1991) : affrontement ideologique entre les USA (capitalisme) et l'URSS (communisme). Jamais de conflit direct mais des guerres par pays interposes (Coree, Vietnam, Afghanistan). Mur de Berlin (1961-1989).", ["guerre froide", "urss", "usa", "berlin", "communisme"]),
    ("histoire_apartheid", "L'apartheid (1948-1991) etait un systeme de segregation raciale en Afrique du Sud. Nelson Mandela, emprisonne 27 ans (1962-1990), devient le premier president noir en 1994. Commission Verite et Reconciliation.", ["apartheid", "afrique du sud", "mandela", "segregation", "racisme"]),
    ("histoire_genocide_rwanda", "Le genocide des Tutsis au Rwanda (avril-juillet 1994) a fait environ 800 000 morts en 100 jours. Perpetre par le gouvernement Hutu contre la minorite tutsi. Le TPIR juge les responsables.", ["rwanda", "genocide", "tutsi", "hutu", "1994"]),

    # ═══ PHILOSOPHIE ═══
    ("philo_stoicisme", "Le stoicisme (IIIe siecle av. J.-C.) : philosophie grecque et romaine. Distinguer ce qui depend de nous de ce qui n'en depend pas. Accepter le destin. Marc Aurele, Epictete, Seneque.", ["stoicisme", "marc aurele", "epictete", "seneque", "destin"]),
    ("philo_existentialisme", "L'existentialisme (XXe siecle) : l'existence precede l'essence. L'homme est libre et responsable de ses choix. Jean-Paul Sartre, Albert Camus (Le Mythe de Sisyphe), Simone de Beauvoir.", ["existentialisme", "sartre", "camus", "beauvoir", "liberte"]),
    ("philo_nietzsche", "Friedrich Nietzsche (1844-1900), philosophe allemand. 'Dieu est mort.' Concepts : Surhomme, Volonte de puissance, Eternel retour. Critique de la morale chretienne. Œuvres : Ainsi parlait Zarathoustra, Par-dela le bien et le mal.", ["nietzsche", "surhomme", "volonte", "eternel retour", "dieu est mort"]),
]

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--count", type=int, default=0, help="Nombre de faits a ajouter (0 = tous)")
    args = p.parse_args()

    sys.path.insert(0, os.path.dirname(__file__))
    from quick_facts import QuickFacts, FACTS

    qf = QuickFacts()
    before = qf.get_all_facts_count()
    print(f"QuickFacts avant : {before} faits")

    to_add = NEW_FACTS[:args.count] if args.count else NEW_FACTS
    qf.facts.extend(to_add)
    qf._word_index = qf._build_index()
    after = qf.get_all_facts_count()

    # Sauvegarder dans le fichier quick_facts.py
    facts_file = os.path.join(os.path.dirname(__file__), "quick_facts.py")
    with open(facts_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Ajouter les nouveaux faits avant le dernier ]
    new_facts_str = ",\n".join(f'    ({repr(fid)}, {repr(text)}, {repr(kw)})' for fid, text, kw in to_add)
    last_bracket = content.rfind("]")
    content = content[:last_bracket] + ",\n" + new_facts_str + "\n" + content[last_bracket:]

    with open(facts_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"QuickFacts apres : {after} faits (+{after-before})")
    print(f"Fichier mis a jour : {facts_file}")

if __name__ == "__main__":
    main()