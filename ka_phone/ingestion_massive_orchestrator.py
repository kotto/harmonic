#!/usr/bin/env python3
"""
INGESTION MASSIVE ORCHESTRATOR — Phase 1 : Passage à l'échelle
================================================================
Combine les pipelines existants en un flux unifié :
  1. Corpus généraliste → Hologramme 256×256 (ingest_corpus_massive)
  2. QA synthétiques → Hologramme couches multiples (generate_1m_holographic)  
  3. Extraction structurée → QuickFacts (faits atomiques)
  4. Audit → Inject faits manquants → Re-test (batch_ingestion_cyclique)

Usage:
  python ingestion_massive_orchestrator.py --phase all     # Tout lancer
  python ingestion_massive_orchestrator.py --phase quick   # Mode rapide (test)
  python ingestion_massive_orchestrator.py --status        # Voir progression
"""

import os, sys, json, time, re, subprocess, argparse
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "massive_ingestion")
os.makedirs(DATA_DIR, exist_ok=True)
STATUS_FILE = os.path.join(DATA_DIR, "ingestion_status.json")

# ══════════════════════════════════════════════════════════════════════════
# LOTS DE FAITS PRÉ-EXISTANTS À INJECTER DIRECTEMENT DANS QUICKFACTS
# ══════════════════════════════════════════════════════════════════════════

# Chaque fait est (id, texte, [mots_clés])
# Format QuickFacts compatible

FACTS_SCIENCE = [
    ("sci_oxygen_element", "L'oxygene est l'element le plus abondant dans la croute terrestre (46%).", ["oxygene", "element", "croute", "terrestre"]),
    ("sci_nitrogen_atmosphere", "L'azote (N) constitue 78% de l'atmosphere terrestre.", ["azote", "atmosphere", "air"]),
    ("sci_mitochondrie_energie", "Les mitochondries produisent l'ATP, la monnaie energetique des cellules.", ["mitochondrie", "atp", "energie", "cellule"]),
    ("sci_sang_composition", "Le sang est compose de plasma (55%) et de cellules (45%): globules rouges, blancs, plaquettes.", ["sang", "composition", "globules", "plaquettes"]),
    ("sci_neurone_fonction", "Les neurones transmettent l'influx nerveux via des synapses, par neurotransmetteurs.", ["neurone", "synapse", "neurotransmetteur"]),
    ("sci_magnetisme_terre", "Le champ magnetique terrestre protege la Terre des vents solaires.", ["magnetisme", "champ", "terrestre"]),
    ("sci_tsunami_origine", "Les tsunamis sont causes par des seismes sous-marins deplacant de grandes masses d'eau.", ["tsunami", "seisme", "sous-marin"]),
    ("sci_erosion_types", "L'erosion peut etre hydrique, eolienne, glaciaire ou chimique.", ["erosion", "types", "hydrique", "eolienne"]),
    ("sci_gene_dominant", "Un gene dominant s'exprime meme en un seul exemplaire. Un gene recessif necessite deux copies.", ["gene", "dominant", "recessif", "heredite"]),
    ("sci_clonage_principe", "Le clonage consiste a creer une copie genetiquement identique d'un organisme.", ["clonage", "copie", "genetique"]),
    ("sci_noyau_atomique", "Le noyau atomique est compose de protons (charge +) et de neutrons (neutre).", ["noyau", "proton", "neutron", "atomique"]),
    ("sci_radioactivite_types", "Radioactivite alpha (noyau d'helium), beta (electron/positron), gamma (photon).", ["radioactivite", "alpha", "beta", "gamma"]),
    ("sci_systeme_solaire_age", "Le systeme solaire s'est forme il y a environ 4.6 milliards d'annees.", ["systeme", "solaire", "age", "formation"]),
    ("sci_telescope_fonction", "Un telescope collecte et concentre la lumiere pour observer des objets celestes.", ["telescope", "lumiere", "observation", "celeste"]),
    ("sci_satellite_artificiel", "Un satellite artificiel est un objet place en orbite autour de la Terre.", ["satellite", "orbite", "artificiel"]),
    ("sci_metamorphose", "La metamorphose est une transformation profonde du corps (ex: chenille -> papillon).", ["metamorphose", "transformation", "insecte"]),
    ("sci_ecosysteme_definition", "Un ecosysteme est l'ensemble forme par une communaute d'etres vivants et leur environnement.", ["ecosysteme", "communaute", "environnement"]),
    ("sci_couche_ozone", "La couche d'ozone absorbe les rayons UV nocifs du soleil.", ["ozone", "couche", "uv", "soleil"]),
    ("sci_effet_serre_explication", "L'effet de serre est un phenomene naturel ou les gaz retiennent la chaleur du soleil.", ["effet de serre", "gaz", "chaleur", "soleil"]),
    ("sci_volcan_formation", "Un volcan se forme quand le magma remonte a la surface par des fissures de la croute terrestre.", ["volcan", "magma", "eruption", "croute"]),
]

FACTS_HISTORY = [
    ("hist_universite_creation", "La premiere universite fut fondee a Bologne (Italie) en 1088.", ["universite", "bologne", "1088", "premiere"]),
    ("hist_code_hammurabi", "Le code d'Hammurabi (1750 av. J.-C.) est l'un des plus anciens codes de lois connus.", ["hammurabi", "code", "lois", "babylone"]),
    ("hist_croisades_dates", "Les croisades eurent lieu de 1095 a 1291.", ["croisades", "1095", "1291", "jerusalem"]),
    ("hist_guerre_100_ans", "La guerre de Cent Ans (1337-1453) opposa la France et l'Angleterre.", ["guerre", "cent ans", "1337", "1453", "france", "angleterre"]),
    ("hist_peste_noire_morts", "La peste noire (1347-1351) causa 25 a 50 millions de morts en Europe.", ["peste", "noire", "morts", "1347"]),
    ("hist_decouverte_amerique_1492", "Christophe Colomb atteint les Ameriques le 12 octobre 1492.", ["colomb", "1492", "amerique", "decouverte"]),
    ("hist_renaissance_periode", "La Renaissance est une periode de renouveau culturel et artistique en Europe (XIVe-XVIe).", ["renaissance", "periode", "culture", "art"]),
    ("hist_reforme_protestante", "La Reforme protestante debuta en 1517 avec les 95 theses de Martin Luther.", ["reforme", "protestante", "1517", "luther"]),
    ("hist_guillotine_revolution", "La guillotine fut utilisee pendant la Revolution francaise (1792-1794).", ["guillotine", "revolution", "francaise"]),
    ("hist_napoleon_couronnement", "Napoleon Bonaparte fut couronne empereur le 2 decembre 1804.", ["napoleon", "couronne", "empereur", "1804"]),
    ("hist_abolition_esclavage_usa", "L'esclavage fut aboli aux Etats-Unis par le 13e amendement en 1865.", ["abolition", "esclavage", "usa", "1865", "amendement"]),
    ("hist_ere_meiji", "L'ere Meiji (1868-1912) modernisa le Japon et l'ouvrit au monde.", ["meiji", "japon", "modernisation", "1868"]),
    ("hist_scramble_for_africa_date", "La conference de Berlin (1884-1885) reglementa la colonisation de l'Afrique.", ["berlin", "1884", "colonisation", "afrique"]),
    ("hist_premiere_guerre_mondiale_debut", "La Premiere Guerre mondiale eclata en 1914 apres l'assassinat de Francois-Ferdinand.", ["premiere", "guerre", "mondiale", "1914", "ferdinand"]),
    ("hist_mur_berlin_construction", "Le mur de Berlin fut construit en aout 1961 pour separer Berlin-Est et Berlin-Ouest.", ["mur", "berlin", "1961", "construction"]),
    ("hist_homme_lune_1969", "Le 20 juillet 1969, Neil Armstrong fut le premier homme a marcher sur la Lune.", ["lune", "1969", "armstrong", "apollo"]),
    ("hist_chute_urss", "L'URSS fut dissoute en decembre 1991.", ["urss", "1991", "dissolution"]),
    ("hist_attentat_11_septembre", "Les attentats du 11 septembre 2001 frapperent le World Trade Center a New York.", ["11 septembre", "2001", "world trade center"]),
    ("hist_creation_euro", "L'euro fut introduit comme monnaie electronique en 1999, puis en pieces et billets en 2002.", ["euro", "monnaie", "1999", "2002"]),
]

FACTS_GEO = [
    ("geo_plus_haut_sommet_afrique", "Le Kilimandjaro (5895 m) est le plus haut sommet d'Afrique.", ["kilimandjaro", "sommet", "afrique", "5895"]),
    ("geo_plus_grand_lac_afrique", "Le lac Victoria est le plus grand lac d'Afrique (68 870 km²).", ["lac", "victoria", "afrique", "plus grand"]),
    ("geo_desert_sahara_superficie", "Le Sahara est le plus grand desert chaud du monde (9.2M km²).", ["sahara", "desert", "superficie"]),
    ("geo_fleuve_amazone", "L'Amazone est le plus grand fleuve du monde par le debit.", ["amazone", "fleuve", "debit"]),
    ("geo_plus_haut_sommet_monde", "L'Everest (8849 m) est le plus haut sommet du monde.", ["everest", "sommet", "monde", "8849"]),
    ("geo_fosse_mariannes", "La fosse des Mariannes est le point le plus profond des oceans (11 034 m).", ["mariannes", "fosse", "profond", "ocean"]),
    ("geo_monde_pays_nombre", "Il y a environ 195 pays dans le monde (193 membres de l'ONU + 2 observateurs).", ["pays", "nombre", "monde", "195"]),
    ("geo_plus_grand_pays_russie", "La Russie est le plus grand pays du monde (17.1M km²).", ["russie", "plus grand", "pays"]),
    ("geo_plus_petit_pays_vatican", "Le Vatican est le plus petit pays du monde (0.44 km²).", ["vatican", "plus petit", "pays"]),
    ("geo_mer_morte", "La mer Morte est le point le plus bas de la surface terrestre (-430 m).", ["mer", "morte", "bas", "altitude"]),
    ("geo_foret_amazonienne", "La foret amazonienne est la plus grande foret tropicale du monde.", ["foret", "amazonienne", "tropicale"]),
    ("geo_plus_grande_ile_groenland", "Le Groenland est la plus grande ile du monde.", ["groenland", "ile", "plus grande"]),
    ("geo_ocean_pacifique_superficie", "L'ocean Pacifique est le plus grand ocean (165M km²).", ["pacifique", "ocean", "plus grand"]),
    ("geo_rift_africain", "Le rift est-africain est une zone de fracture de la croute terrestre qui s'ecarte.", ["rift", "africain", "fracture"]),
    ("geo_chute_victoria", "Les chutes Victoria (Zimbabwe/Zambie) sont les plus grandes chutes du monde.", ["victoria", "chutes", "zimbabwe", "zambie"]),
]

FACTS_OTHER = [
    ("cul_nobel_prix_creation", "Les prix Nobel furent crees par Alfred Nobel en 1901. Categories: paix, litterature, medecine, physique, chimie.", ["nobel", "prix", "1901", "alfred"]),
    ("cul_nobel_litterature_francais", "Prix Nobel de litterature francais: Sully Prudhomme (1901), Camus (1957), Sartre (1964, refuse), Le Clezio (2008), Modiano (2014).", ["nobel", "litterature", "francais"]),
    ("cul_oscar_creation", "Les Oscars du cinema furent crees en 1929 par l'Academy of Motion Picture Arts and Sciences.", ["oscar", "cinema", "1929"]),
    ("cul_grammy_award", "Les Grammy Awards recompensent l'industrie musicale depuis 1959.", ["grammy", "musique", "1959"]),
    ("sport_olympiques_modernes_date", "Les premiers Jeux Olympiques modernes eurent lieu a Athenes en 1896.", ["olympiques", "1896", "athenes"]),
    ("sport_cyclisme_tour_de_france", "Le Tour de France cycliste fut cree en 1903 par Henri Desgrange.", ["tour de france", "cyclisme", "1903"]),
    ("sport_tennis_grand_chelem", "Les tournois du Grand Chelem: Open d'Australie, Roland-Garros, Wimbledon, US Open.", ["grand chelem", "tennis", "open"]),
    ("sport_natation_phelps_medailles", "Michael Phelps detient le record de medailles olympiques: 28 dont 23 en or.", ["phelps", "medailles", "natation", "olympiques"]),
    ("eco_pib_definition", "Le PIB (Produit Interieur Brut) mesure la valeur totale des biens et services produits dans un pays.", ["pib", "produit", "interieur", "brut"]),
    ("eco_inflation_definition", "L'inflation est la hausse generale et durable des prix. Mesuree par l'IPC.", ["inflation", "prix", "ipc"]),
    ("eco_wall_street_krach_1929", "Le krach de Wall Street (24 octobre 1929) declencha la Grande Depression.", ["krach", "1929", "wall street", "depression"]),
    ("eco_crypto_bitcoin_creation", "Le Bitcoin fut cree en 2009 par une personne ou un groupe sous le pseudonyme Satoshi Nakamoto.", ["bitcoin", "2009", "satoshi", "crypto"]),
    ("jur_declaration_droits_homme_date", "La Declaration des droits de l'homme et du citoyen fut adoptee le 26 aout 1789.", ["droits", "homme", "1789", "declaration"]),
    ("jur_age_majorite_france", "L'age de la majorite civile en France est fixe a 18 ans depuis 1974.", ["majorite", "18 ans", "civile"]),
    ("tech_premier_ordinateur_eniac", "L'ENIAC (1946) est considere comme le premier ordinateur electronique a usage general.", ["eniac", "1946", "ordinateur", "premier"]),
    ("tech_premier_smartphone", "L'IBM Simon (1994) est considere comme le premier smartphone.", ["smartphone", "premier", "ibm", "simon"]),
    ("tech_creation_wikipedia", "Wikipedia fut lancee le 15 janvier 2001 par Jimmy Wales et Larry Sanger.", ["wikipedia", "2001", "jimmy wales"]),
    ("tech_creation_youtube", "YouTube fut cree en fevrier 2005 par trois anciens de PayPal.", ["youtube", "2005", "creation"]),
    ("tech_wifi_definition", "Le Wi-Fi est une technologie de reseau sans fil basee sur les normes IEEE 802.11.", ["wifi", "ieee", "reseau", "sans fil"]),
    ("tech_bluetooth_origine", "Le Bluetooth fut invente par Ericsson en 1994. Le nom vient du roi danois Harald Bluetooth.", ["bluetooth", "1994", "ericsson"]),
]

def get_all_new_facts():
    """Retourne tous les faits organises en lots."""
    return {
        "science": FACTS_SCIENCE,
        "histoire": FACTS_HISTORY,
        "geographie": FACTS_GEO,
        "general": FACTS_OTHER,
    }

# ══════════════════════════════════════════════════════════════════════════
# ORCHESTRATEUR
# ══════════════════════════════════════════════════════════════════════════

def run_step(name, cmd, timeout=300):
    """Execute une etape du pipeline."""
    print(f"\n{'='*60}")
    print(f"  ETAPE: {name}")
    print(f"  CMD: {cmd}")
    print(f"{'='*60}")
    t0 = time.time()
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, 
                              timeout=timeout, cwd=os.path.dirname(__file__))
        elapsed = time.time() - t0
        print(f"  Status: {result.returncode}")
        print(f"  Time: {elapsed:.1f}s")
        if result.stdout:
            print(result.stdout[-500:])
        if result.stderr:
            print(f"  STDERR: {result.stderr[-200:]}")
        return result.returncode == 0, elapsed
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT after {timeout}s")
        return False, timeout

def inject_facts_to_quickfacts(facts_list):
    """Injecte une liste de faits directement dans quick_facts.py."""
    print(f"  Injection de {len(facts_list)} faits dans QuickFacts...")
    
    quickfacts_path = os.path.join(os.path.dirname(__file__), "quick_facts.py")
    with open(quickfacts_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Trouver le point d'insertion (avant le dernier ])
    # Chercher la fermeture de FACTS
    insertion_marker = "('currency_dirham'"
    if insertion_marker in content:
        new_facts_str = ""
        for fid, text, keywords in facts_list:
            kw_str = ", ".join(f"'{kw}'" for kw in keywords)
            new_facts_str += f"    ('{fid}', '{text}', [{kw_str}]),\n"
        
        # Insérer avant currency_dirham
        content = content.replace("    ('currency_dirham'", 
                                  new_facts_str + "    ('currency_dirham'")
        
        with open(quickfacts_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  [OK] {len(facts_list)} faits injectes dans QuickFacts")
        return True
    else:
        print(f"  ⚠️ Point d'insertion non trouve, skip QuickFacts injection")
        return False

def save_status(data):
    with open(STATUS_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', default='quick', choices=['quick', 'facts', 'corpus', 'all', 'status'])
    parser.add_argument('--timeout', type=int, default=600)
    args = parser.parse_args()
    
    if args.phase == 'status':
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE) as f:
                print(json.dumps(json.load(f), indent=2))
        else:
            print("Aucun statut. Lancez --phase quick d'abord.")
        return
    
    status = {
        "started": datetime.now().isoformat(),
        "phase": args.phase,
        "steps": {}
    }
    
    if args.phase in ('quick', 'all'):
        # Injecter les faits pre-structures
        all_facts = get_all_new_facts()
        total_facts = sum(len(v) for v in all_facts.values())
        print(f"\nPhase 1a: Injection de {total_facts} faits structures...")
        
        all_flat = []
        for category, facts in all_facts.items():
            all_flat.extend(facts)
        
        ok = inject_facts_to_quickfacts(all_flat)
        status["steps"]["facts_injected"] = {
            "count": total_facts,
            "success": ok,
            "time": time.time()
        }
    
    if args.phase in ('corpus', 'all'):
        # Lancer l'ingestion massive corpus (peut prendre des heures)
        print("\nPhase 1b: Ingestion corpus massif dans l'hologramme...")
        ok, elapsed = run_step("Corpus Massif", 
                              f"python ingest_corpus_massive.py --quick", 
                              timeout=args.timeout)
        status["steps"]["corpus_massive"] = {"success": ok, "time": elapsed}
    
    # Sauvegarde statut
    status["finished"] = datetime.now().isoformat()
    save_status(status)
    
    print(f"\n{'='*60}")
    print(f"  INGESTION TERMINEE")
    print(f"  Phase: {args.phase}")
    print(f"  Fichier statut: {STATUS_FILE}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()