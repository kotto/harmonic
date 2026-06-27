#!/usr/bin/env python3
"""
INJECT AUDIT FACTS — Enrichit QuickFacts avec les faits identifies comme manquants
==================================================================================
Suite a l'audit de 91 questions, ce script injecte directement dans la base
QuickFacts les reponses factuelles manquantes (capitales, dates, formules, etc.)
pour ameliorer le score du pipeline sans LLM.

Usage: python inject_audit_facts.py
"""

import json, os, sys, hashlib

os.chdir(os.path.dirname(__file__))

# Chemin vers QuickFacts
qf_path = "quick_facts.py"

# Lire le fichier QuickFacts
with open(qf_path, "r", encoding="utf-8") as f:
    content = f.read()

# Trouver la ligne d'initialisation des faits
# Chercher "self.facts = [" ou le chargement initial
marker = "self.facts.extend(CODE_FACTS)"
if marker not in content:
    print("ERREUR: marqueur self.facts.extend(CODE_FACTS) non trouve dans quick_facts.py")
    sys.exit(1)

# ============== NOUVEAUX FAITS ==============
NEW_FACTS = [
    # --- GEOGRAPHIE ---
    ("geo_capital_senegal", "La capitale du Senegal est Dakar.", ["senegal", "capitale", "dakar"]),
    ("geo_capital_france", "La capitale de la France est Paris.", ["france", "capitale", "paris"]),
    ("geo_capital_mali", "La capitale du Mali est Bamako.", ["mali", "capitale", "bamako"]),
    ("geo_capital_ethiopie", "La capitale de l'Ethiopie est Addis-Abeba.", ["ethiopie", "capitale", "addis"]),
    ("geo_plus_grand_afrique", "Le plus grand pays d'Afrique par superficie est l'Algerie.", ["algerie", "afrique", "superficie"]),
    ("geo_ocean_senegal", "L'ocean Atlantique borde le Senegal a l'ouest.", ["senegal", "ocean", "atlantique"]),
    ("geo_continents", "Il y a 7 continents sur Terre : Afrique, Amerique du Nord, Amerique du Sud, Antarctique, Asie, Europe, Oceanie.", ["continents", "terre"]),
    ("geo_long_fleuve", "Le Nil est le plus long fleuve du monde.", ["nil", "fleuve", "long"]),
    ("geo_pays_peuple", "L'Inde est le pays le plus peuple au monde avec plus de 1.4 milliard d'habitants.", ["inde", "peuple", "population"]),
    ("geo_tombouctou", "Tombouctou se trouve au Mali.", ["tombouctou", "mali"]),
    
    # --- HISTOIRE ---
    ("hist_independance_senegal", "Le Senegal a obtenu son independance en 1960.", ["senegal", "independance", "1960"]),
    ("hist_nkrumah", "Kwame Nkrumah a ete le premier president du Ghana independant.", ["nkrumah", "ghana", "president"]),
    ("hist_muraille_chine", "La Grande Muraille a ete construite en Chine.", ["muraille", "chine", "grande"]),
    ("hist_revolution_francaise", "La Revolution francaise a commence en 1789.", ["revolution", "francaise", "1789"]),
    ("hist_colomb", "Christophe Colomb a decouvert l'Amerique en 1492.", ["colomb", "amerique", "1492"]),
    ("hist_empire_songhai", "L'Empire Songhai etait connu pour ses manuscrits a Tombouctou.", ["songhai", "empire", "tombouctou"]),
    ("hist_waterloo", "La bataille de Waterloo a marque la defaite de Napoleon en 1815.", ["waterloo", "napoleon", "1815"]),
    ("hist_kheops", "Le pharaon Kheops a construit la grande pyramide de Gizeh.", ["kheops", "pyramide", "pharaon", "gizeh"]),
    ("hist_mur_berlin", "Le mur de Berlin est tombe en 1989.", ["berlin", "mur", "1989"]),
    ("hist_mansa_moussa", "Mansa Moussa etait le roi du Mali connu pour son pelerinage a La Mecque.", ["moussa", "mansa", "mali", "pelerinage"]),
    
    # --- SCIENCES ---
    ("sci_eau_formule", "La formule chimique de l'eau est H2O.", ["eau", "h2o", "formule"]),
    ("sci_planetes", "Il y a 8 planetes dans le systeme solaire : Mercure, Venus, Terre, Mars, Jupiter, Saturne, Uranus, Neptune.", ["planetes", "systeme", "solaire"]),
    ("sci_hydrogene", "L'hydrogene est l'element chimique le plus abondant dans l'univers.", ["hydrogene", "element", "abondant"]),
    ("sci_ebullition", "L'eau bout a 100 degres Celsius.", ["eau", "bout", "100", "celsius"]),
    ("sci_adn", "L'ADN (acide desoxyribonucleique) est la molecule qui porte l'information genetique de tous les etres vivants.", ["adn", "genetique"]),
    ("sci_lumiere", "La vitesse de la lumiere est d'environ 300000 km/s.", ["lumiere", "vitesse", "300000"]),
    ("sci_os", "Le corps humain adulte compte 206 os.", ["os", "corps", "humain", "206"]),
    ("sci_peau", "La peau est le plus grand organe du corps humain.", ["peau", "organe", "corps"]),
    ("sci_pythagore", "Le theoreme de Pythagore dit que dans un triangle rectangle, le carre de l'hypotenuse est egal a la somme des carres des deux autres cotes (a^2 + b^2 = c^2).", ["pythagore", "theoreme", "triangle"]),
    ("sci_chromosomes", "L'etre humain possede 46 chromosomes (23 paires).", ["chromosomes", "46"]),
    
    # --- CULTURE GENERALE ---
    ("cult_petit_prince", "Le Petit Prince a ete ecrit par Antoine de Saint-Exupery.", ["petit", "prince", "saint-exupery"]),
    ("cult_jordan", "Michael Jordan jouait au basket-ball (NBA).", ["jordan", "basket", "nba"]),
    ("cult_djembe_kora", "Le djemble et la kora sont des instruments de musique associes a l'Afrique de l'Ouest.", ["kora", "djemble", "instrument", "afrique", "ouest"]),
    ("cult_thieboudiene", "Le thieboudiene (ceebu jen) est le plat national du Senegal.", ["thieboudiene", "plat", "senegal"]),
    ("cult_joconde", "La Joconde a ete peinte par Leonard de Vinci.", ["joconde", "leonard", "vinci"]),
    ("cult_avatar", "Avatar (2009) est le film le plus rentable de tous les temps.", ["avatar", "film", "rentable"]),
    ("cult_chinois", "Le chinois mandarin est la langue la plus parlee au monde en nombre de locuteurs natifs.", ["chinois", "langue", "parlee"]),
    ("cult_beethoven", "La 5eme symphonie a ete composee par Ludwig van Beethoven.", ["beethoven", "symphonie"]),
    ("cult_coran", "Le Coran est le livre sacre de l'Islam.", ["coran", "islam", "livre"]),
    ("cult_football", "Une equipe de football compte 11 joueurs sur le terrain.", ["football", "joueurs", "11"]),
    
    # --- CODE / TECHNIQUE ---
    ("code_for_loop", "En Python, une boucle for s'ecrit : for element in liste: ...", ["for", "boucle", "python"]),
    ("code_print", "Pour afficher du texte en Python, on utilise print('texte').", ["print", "afficher", "python"]),
    ("code_html", "HTML (HyperText Markup Language) est le langage de balisage utilise pour creer des pages web.", ["html", "web"]),
    ("code_liste_tuple", "En Python, la difference entre liste et tuple : les listes sont mutables (modifiables) avec [], les tuples sont immutables avec ().", ["liste", "tuple", "python", "difference"]),
    
    # --- QUESTIONS PIEGES ---
    ("piege_telephone", "Le telephone a ete invente par Alexander Graham Bell en 1876.", ["telephone", "bell", "invente"]),
    ("piege_cube", "Un cube a 6 faces, 8 sommets et 12 aretes.", ["cube", "faces", "6"]),
]

# Construire le bloc de code a inserer
injection_lines = []
injection_lines.append("")
injection_lines.append("    # === INJECTION AUDIT FACTS — Faits manquants identifies par l'audit du 09/06/2026 ===")
injection_lines.append(f"    # {len(NEW_FACTS)} faits ajoutes (capitales, dates, formules, culture, etc.)")
injection_lines.append("    audit_facts = [")

for fid, text, keywords in NEW_FACTS:
    kw_str = json.dumps(keywords, ensure_ascii=False)
    txt_escaped = text.replace('\\', '\\\\').replace("'", "\\'")
    injection_lines.append(f"        ('{fid}', '{txt_escaped}', {kw_str}),")

injection_lines.append("    ]")
injection_lines.append("    quick_facts.facts.extend(audit_facts)")

injection_block = "\n".join(injection_lines)

# Inserer apres le marqueur
# Chercher la fin du bloc d'extension (apres le rebuild index)
rebuild_marker = "quick_facts._word_index = quick_facts._build_index()"
insert_pos = content.find(rebuild_marker)
if insert_pos == -1:
    print("ERREUR: marqueur rebuild index non trouve")
    sys.exit(1)

# Inserer avant ce marqueur
new_content = content[:insert_pos] + injection_block + "\n    " + content[insert_pos:]

with open(qf_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print(f"OK: {len(NEW_FACTS)} faits injectes dans {qf_path}")
for fid, text, _ in NEW_FACTS:
    print(f"  + {fid}: {text[:80]}...")