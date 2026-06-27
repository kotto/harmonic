#!/usr/bin/env python3
"""Safe fact injector - uses json to handle quotes properly."""
import json, os

os.chdir(os.path.dirname(__file__))

# Facts with single quotes escaped via json
FACTS = json.loads(r"""
[
  ["ocean_atlantique", "L'ocean Atlantique borde l'Afrique et l'Europe a l'ouest.", ["ocean", "atlantique"]],
  ["ocean_pacifique", "L'ocean Pacifique est le plus grand ocean du monde.", ["ocean", "pacifique"]],
  ["ocean_indien", "L'ocean Indien borde l'Afrique a l'est.", ["ocean", "indien"]],
  ["continent_afrique_fact", "L'Afrique est le deuxieme plus grand continent.", ["continent", "afrique"]],
  ["continent_asie_fact", "L'Asie est le plus grand continent.", ["continent", "asie"]],
  ["nombre_continents", "Il y a 7 continents sur Terre : Afrique, Amerique, Asie, Europe, Oceanie, Antarctique.", ["continents", "7", "terre"]],
  ["pays_plus_peuple", "L'Inde est le pays le plus peuple au monde avec 1.45 milliard d'habitants.", ["peuple", "plus", "pays"]],
  ["independance_senegal", "Le Senegal a obtenu son independance le 4 avril 1960.", ["independance", "senegal", "1960"]],
  ["empire_mali", "L'empire du Mali (XIIIe-XVe siecles) dominait l'Afrique de l'Ouest.", ["empire", "mali", "afrique"]],
  ["empire_songhai", "L'empire Songhai succeda a l'empire du Mali, avec Tombouctou comme centre intellectuel.", ["empire", "songhai", "tombouctou"]],
  ["tombouctou", "Tombouctou est une ville historique du Mali, ancien centre intellectuel et commercial.", ["tombouctou", "mali", "pays"]],
  ["ghana_nkrumah", "Kwame Nkrumah fut le premier president du Ghana independant (1957-1966).", ["nkrumah", "ghana", "president"]],
  ["pharaon_kheops", "Kheops (Khufu) etait le pharaon de la IVe dynastie, constructeur de la Grande Pyramide.", ["pharaon", "kheops", "pyramide"]],
  ["bataille_waterloo", "La bataille de Waterloo (18 juin 1815) marqua la defaite finale de Napoleon.", ["bataille", "waterloo", "1815", "napoleon"]],
  ["plat_thieboudiene", "Le thieboudiene (ceebu jen) est le plat national du Senegal : riz au poisson.", ["plat", "senegal", "thieboudiene"]],
  ["symphonie_beethoven", "La 5e symphonie de Beethoven (1808) est l'une des plus celebres oeuvres classiques.", ["symphonie", "beethoven", "musique"]],
  ["coran_livre_sacre", "Le Coran est le livre sacre de l'Islam, revele au prophete Muhammad.", ["coran", "islam", "livre", "sacre"]],
  ["jordan_basket", "Michael Jordan est le plus grand joueur de basketball de tous les temps.", ["michael jordan", "basket", "basketball"]],
  ["coupe_monde_2022", "L'Argentine a gagne la Coupe du Monde 2022 au Qatar.", ["coupe du monde", "2022", "argentine"]],
  ["langue_chinois", "Le chinois (mandarin) est la langue la plus parlee au monde avec 1.1 milliard de locuteurs.", ["langue", "chinois", "parlee"]],
  ["planetes_nombre", "Il y a 8 planetes dans le systeme solaire : Mercure, Venus, Terre, Mars, Jupiter, Saturne, Uranus, Neptune.", ["planetes", "8", "systeme solaire"]],
  ["chromosomes_humains", "L'etre humain a 46 chromosomes (23 paires), dont une paire determine le sexe (XX ou XY).", ["chromosomes", "46", "humain"]],
  ["peau_organe", "La peau est le plus grand organe du corps humain (environ 2 m2 chez l'adulte).", ["peau", "organe", "corps"]],
  ["element_hydrogene", "L'hydrogene est l'element le plus abondant dans l'univers (environ 75% de la matiere).", ["hydrogene", "element", "univers", "abondant"]],
  ["sci_oxygen_element", "L'oxygene est l'element le plus abondant dans la croute terrestre (46%).", ["oxygene", "element", "croute", "terrestre"]],
  ["sci_nitrogen_atmosphere", "L'azote (N) constitue 78% de l'atmosphere terrestre.", ["azote", "atmosphere", "air"]],
  ["sci_mitochondrie_energie", "Les mitochondries produisent l'ATP, la monnaie energetique des cellules.", ["mitochondrie", "atp", "energie", "cellule"]],
  ["geo_groenland_ile", "Le Groenland est la plus grande ile du monde.", ["groenland", "ile", "plus grande"]],
  ["hist_chute_urss", "L'URSS fut dissoute en decembre 1991.", ["urss", "1991", "dissolution"]],
  ["tech_wikipedia_creation", "Wikipedia fut lancee le 15 janvier 2001 par Jimmy Wales et Larry Sanger.", ["wikipedia", "2001", "jimmy wales"]]
]""")

with open('quick_facts.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Build facts string safely
facts_str = ""
for fid, text, keywords in FACTS:
    kw_list = ", ".join(f'"{kw}"' for kw in keywords)
    facts_str += f'    ("{fid}", {json.dumps(text)}, [{kw_list}]),\n'

# Insert before currency_dirham
if "    ('currency_dirham'" in content:
    content = content.replace("    ('currency_dirham'", facts_str + "    ('currency_dirham'")
    with open('quick_facts.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Injected {len(FACTS)} facts safely using json.dumps")
else:
    print("ERROR: insertion marker not found")