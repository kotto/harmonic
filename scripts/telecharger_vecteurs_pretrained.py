"""
Telechargement et filtrage des vecteurs fastText pre-entraines (cc.fr.300).

Ce script telecharge le modele fastText francais pre-entraine par Facebook
(Common Crawl, 300 dimensions, 2M mots) et le filtre pour ne garder que
les vecteurs correspondant au vocabulaire etendu (2125 tokens) plus un ensemble
de termes medicaux/biotech courants pour l'expansion OOV.

Le fichier source: https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.fr.300.vec.gz
Taille: ~2.1 GB compresse, ~7 GB decompresse.
Apres filtrage: ~quelques Mo.

Usage:
    python scripts/telecharger_vecteurs_pretrained.py
"""

import os
import sys
import gzip
import json
import time
import math
import struct
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

# Ajouter le chemin racine pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from harmonic_training.model.vocabulaire_etendu import VOCABULAIRE_ETENDU, VOCAB_SIZE_ETENDU
    VOCAB = set(VOCABULAIRE_ETENDU)
    print(f"Vocabulaire etendu charge: {len(VOCAB)} tokens")
except ImportError:
    # Fallback: vocabulaire minimal
    print("[WARN] Vocabulaire etendu non disponible, fallback minimal")
    VOCAB = set()

# =========================================================================
# Configuration
# =========================================================================
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_DIR = os.path.join(PROJECT_ROOT, "ka_knowledge_base")
PRETRAINED_VECS_FILE = os.path.join(KB_DIR, "vecteurs_pretrained.npy")
PRETRAINED_WORDS_FILE = os.path.join(KB_DIR, "vecteurs_pretrained_words.json")
PRETRAINED_META_FILE = os.path.join(KB_DIR, "vecteurs_pretrained_meta.json")

# URL du modele fastText francais pre-entraine
CC_FR_URL = "https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.fr.300.vec.gz"

# Termes medicaux/biotech supplementaires pour l'expansion OOV
TERMES_MEDICAUX = [
    "infarctus", "hypertension", "arterielle", "therapie", "genetique",
    "cardiovasculaire", "neurologique", "psychiatrique", "diabetique",
    "inflammatoire", "degenerative", "metabolique", "respiratoire",
    "gastrointestinal", "hematologique", "oncologique", "pediatrique",
    "geriatrique", "epidemiologie", "pathogenese", "etiologie",
    "diagnostic", "prophylaxie", "pronostic", "symptomatologie",
    "pharmacologique", "physiologique", "anatomique", "histologique",
    "immunohistochimie", "electrophysiologie", "neuroimagerie",
    "biomarqueur", "pharmacogenomique", "therapeutique",
    "antihypertenseur", "anti-inflammatoire", "antidiabetique",
    "anticoagulant", "antiarythmique", "antineoplasique",
    "antibiotherapie", "chimiotherapie", "radiotherapie",
    "psychotherapie", "rehabilitation", "readaptation",
    "insulinoresistance", "hypercholesterolemie", "hyperglycemie",
    "hypoglycemie", "hypotension", "atherosclerose",
    "glomerulopathie", "neuropathie", "retinopathie",
    "nephropathie", "encephalopathie", "myocardiopathie",
    "valvulopathie", "vasculopathie", "lymphadenopathie",
    "myopathie", "arthropathie", "osteoporose",
    "polyarthrite", "spondylarthrite", "dermatose",
    "xenotransplantation", "allotransplantation", "autogreffe",
    "bioprothese", "endoprothese", "exoprothese",
    "pharmacodependance", "iatrogenie", "nosocomial",
    "zoopathie", "anthropozoonose", "zoonose",
    "vectoriel", "palustre", "plasmodial",
    "trypanosomiase", "leishmaniose", "bilharziose",
    "onchocercose", "filariose", "dracunculose",
    "schistosomiase", "amebiase", "giardiase",
    "candidose", "aspergillose", "mucormycose",
    "pneumocystose", "toxoplasmose", "cryptococcose",
    "tuberculose", "leprae", "treponematose",
    "borreliose", "rickettsiose", "leptospirose",
    "brucellose", "tularemie", "pasteurellose",
    "cholangite", "cholecystite", "pancreatite",
    "peritonite", "pleuresie", "pyelonephrite",
    "glomerulonephrite", "cystite", "prostatite",
    "orchite", "epididymite", "salpingite",
    "endometrite", "cervicite", "vaginite",
    "vulvite", "balanite", "posthite",
    "conjonctivite", "keratite", "uveite",
    "retinite", "choroidite", "sclerite",
    "otite", "mastoidite", "sinusite",
    "pharyngite", "laryngite", "tracheite",
    "bronchite", "bronchiolite", "alveolite",
    "mediastinite", "pericardite", "myocardite",
    "endocardite", "lymphangite", "thrombophlebite",
    "arterite", "capillarite", "vasculite",
    "dermohypodermite", "fasciite", "myosite",
    "tenosynovite", "bursite", "arthrite",
    "osteite", "osteomyelite", "spondylodiscite",
    "discite", "sacralite", "coccygodynie",
    "neuropathie", "plexopathie", "radiculopathie",
    "myelopathie", "leucoencephalopathie", "leucodystrophie",
    "adrenoleucodystrophie", "metachromatique", "globoid",
    "krabbe", "tay-sachs", "sandhoff",
    "niemann-pick", "gaucher", "fabry",
    "pompe", "hurler", "hunter",
    "sanfilippo", "morquio", "maroteaux-lamy",
    "sly", "mucopolysaccharidose", "oligosaccharidose",
    "glycogenose", "lipidose", "sphingolipidose",
    "ceroidolipofuscinose", "aminoacidopathie", "organoacidemie",
    "cytopathie", "mitochondriale", "peroxysomale",
    "zellweger", "adrenoleucodystrophie", "refsum",
    "rhizomelique", "chondrodysplasie", "dysplasie",
    "ectodermique", "mesodermique", "entodermique",
    "neuroectodermique", "craniofaciale", "craniosynostose",
    "microphtalmie", "anophtalmie", "colobome",
    "cataracte", "glaucome", "degenerative",
    "maculaire", "retinite", "pigmentaire",
    "stargardt", "best", "vitelliforme",
    "achromatopsie", "monochromatisme", "dyschromatopsie",
    "daltonisme", "hemeralopie", "nyctalopie",
    "photophobie", "xerophtalmie", "keratocone",
    "corneal", "endothelial", "stromal",
    "epithelial", "conjonctival", "scleral",
    "uveal", "choroide", "retine",
    "vitre", "cristallin", "camera",
    "anterieure", "posterieure", "segment",
    "pseudophake", "aphake", "phake",
    "intraoculaire", "intravitreen", "intracameral",
    "perioculaire", "retrobulbaire", "orbitopathie",
    "exophtalmie", "enophtalmie", "strabisme",
    "nystagmus", "diplopie", "amblyopie",
    "anisometropie", "astigmatisme", "myopie",
    "hypermetropie", "presbytie", "accommodation",
    "convergence", "divergence", "vergence",
    "fusionnel", "stereopsie", "vision",
    "binoculaire", "monoculaire", "scotome",
    "hemianopsie", "quadranopsie", "campimetrie",
    "perimetrie", "angiographie", "tomographie",
    "coherence", "optique", "scanning",
    "laser", "ophthalmoscopie", "biomicroscopie",
    "gonioscopie", "tonometrie", "pachymetrie",
    "keratometrie", "aberrometrie", "topographie",
    "corneenne", "speculaire", "microscopie",
    "endotheliale", "fluorophore", "angiogene",
    "photocoagulation", "vitrectomie", "trabeculectomie",
    "iridotomie", "capsulotomie", "cyclophotocoagulation",
    "retinopexie", "cerclage", "indentation",
    "sclerale", "implant", "intraoculaire",
    "phakoemulsification", "extracapsulaire", "intracapsulaire",
    "keratoplastie", "transfixiante", "lamellaire",
    "endotheliale", "descemet", "dmeK",
    "dsek", "pterygion", "pinguecula",
    "chalazion", "orgelet", "blépharite",
    "ectropion", "entropion", "lagophtalmie",
    "ptosis", "retraction", "blépharospasme",
    "fibrillation", "atriale", "ventriculaire",
    "tachycardie", "bradycardie", "arythmie",
    "extrasystole", "bloc", "auriculo",
    "ventriculaire", "sino", "nodal",
    "his", "purkinje", "wolff",
    "parkinson", "white", "long",
    "qt", "court", "brut",
    "cardiomyopathie", "dilatee", "hypertrophique",
    "restrictive", "ischemique", "non",
    "compaction", "dysplasie", "arythmogene",
    "droit", "gauche", "biventriculaire",
    "insuffisance", "cardiaque", "cardiopulmonaire",
    "congenitale", "acquise", "rhumatismale",
    "degenerative", "prothetique", "valvulaire",
    "mitrale", "aortique", "tricuspide",
    "pulmonaire", "regurgitation", "stenose",
    "prolapsus", "bicuspidie", "quadricuspidie",
    "coarctation", "aorte", "bicuspide",
    "canal", "arteriel", "persistant",
    "communication", "interventriculaire", "interauriculaire",
    "tetralogie", "fallot", "transposition",
    "grands", "vaisseaux", "truncus",
    "arteriosus", "retour", "veineux",
    "anormal", "ebstein", "anomalie",
    "coronaropathie", "arteriopathie", "vasculopathie",
    "thromboangiite", "obliterante", "buerger",
    "raynaud", "acrogeria", "vasomoteur",
    "acrocyanose", "erythermalgie", "lymphoedeme",
    "elephantiasis", "varice", "ulcere",
    "veineux", "insuffisance", "veineuse",
    "post", "thrombotique", "lipodermatosclerose",
    "atrophie", "blanche", "dermite",
    "ocre", "hypodermite", "cellulite",
    "infectieuse", "gangrene", "necrose",
    "amputation", "revascularisation", "pontage",
    "endarteriectomie", "angioplastie", "stent",
    "atherectomie", "laser", "thrombolyse",
    "anticoagulation", "antiagregation", "plaquettaire",
    "antivitamine", "k", "heparine",
    "fondaparinux", "hirudine", "bivalirudine",
    "argatroban", "lepirudine", "desirudine",
    "alteplase", "tenecteplase", "reteplase",
    "streptokinase", "urokinase", "pro",
    "activateur", "tissulaire", "plasminogene",
    "fibrinolyse", "fibrinogene", "d-dimeres",
    "temps", "cephaline", "activee",
    "inr", "quiek", "temps",
    "prothrombine", "fibrinogene", "facteur",
    "von", "willebrand", "hemophilie",
    "hemostase", "coagulation", "cascade",
    "plaquette", "thrombocyte", "megacaryocyte",
    "erythropoietine", "granulopoietine", "thrombopoietine",
    "facteur", "croissance", "hematopoietique",
    "cellule", "souche", "hematopoietique",
    "moelle", "osseuse", "greffe",
    "allogenique", "autologue", "syngenique",
    "conditionnement", "myeloablatif", "non",
    "chimere", "hybride", "transgenique",
    "knockout", "knockin", "crispr",
    "cas9", "nucleases", "dediees",
    "zinc", "finger", "talen",
    "megatale", "recombinaison", "homologue",
    "reparation", "dirigee", "gene",
    "suppresseur", "oncogene", "proto",
    "antioncogene", "carene", "tumorale",
    "angiogenese", "metastase", "invasion",
    "proliferation", "apoptose", "necrose",
    "autophagie", "senescence", "immortalisation",
    "transformation", "carcinogene", "mutagene",
    "clastogene", "aneugene", "genotoxique",
    "phototoxique", "photosensibilisant", "allergene",
    "immunogene", "pyrogene", "endotoxine",
    "exotoxine", "enterotoxine", "neurotoxine",
    "cytotoxine", "hemotoxine", "cardiotoxine",
    "hepatotoxine", "nephrotoxine", "pneumotoxine",
    "mycotoxine", "aflatoxine", "ochratoxine",
    "fumonisine", "patuline", "zearalenone",
    "deoxynivalenol", "nivalenol", "t-2",
    "ht-2", "ergot", "alcaloide",
    "psilocybine", "mescaline", "lsd",
    "dmt", "5-meo-dmt", "ibogaine",
    "salvinorine", "cannabinoide", "thc",
    "cbd", "cbn", "cbg",
    "cbc", "cbdv", "thcv",
    "endocannabinoide", "anandamide", "2-ag",
    "cb1", "cb2", "trpv1",
    "nocicepteur", "thermorecepteur", "mecanorecepteur",
    "photorecepteur", "chimiorécepteur", "barorecepteur",
    "propriocepteur", "interocepteur", "exterocepteur",
    "cortex", "somatosensoriel", "moteur",
    "prefrontal", "temporal", "parietal",
    "occipital", "insula", "cingulum",
    "hippocampe", "amygdale", "striatum",
    "thalamus", "hypothalamus", "epiphyse",
    "hypophyse", "glande", "pineale",
    "pituitaire", "surrenale", "thyroide",
    "parathyroide", "endocrine", "exocrine",
    "autocrine", "paracrine", "juxtacrine",
    "intracrine", "neuroendocrine", "neurosecretion",
    "synapse", "neuromediateur", "neuromodulateur",
    "neuropeptide", "neurohormone", "neurotransmetteur",
    "acetylcholine", "dopamine", "noradrenaline",
    "adrenaline", "serotonine", "histamine",
    "glutamate", "gaba", "glycine",
    "aspartate", "taurine", "adenosine",
    "atp", "no", "co",
    "h2s", "endotheline", "bradykinine",
    "substance", "p", "cgrp",
    "somatostatine", "neurotensine", "cholecystokinine",
    "vip", "pacap", "galanine",
    "orexine", "mch", "crh",
    "trh", "gnrh", "gHRH",
    "somatocrinine", "prolactine", "lh",
    "fsh", "tsh", "acth",
    "msh", "adH", "ocytocine",
    "insuline", "glucagon", "somatostatine",
    "gastrine", "secretine", "cck",
    "gIP", "glp-1", "glp-2",
    "oxyntomoduline", "motiline", "substance",
    "p", "neurokinine", "a",
    "b", "kallidine", "bradykinine",
    "des-arg9", "des-arg10", "kallidine",
    "angiotensine", "i", "ii",
    "iii", "iv", "1-7",
    "renine", "ace", "ace2",
    "aldosterone", "cortisol", "corticosterone",
    "dehydroepiandrosterone", "dhea", "androstenedione",
    "testosterone", "dihydrotestosterone", "estradiol",
    "estrone", "estriol", "progesterone",
    "progestatif", "contraceptif", "levonorgestrel",
    "desogestrel", "etonogestrel", "norelgestromine",
    "drospirenone", "cyproterone", "chlormadinone",
    "dienogest", "nomegestrol", "promegestone",
    "progestatif", "anti", "mineralocorticoide",
    "glucocorticoide", "prednisone", "prednisolone",
    "methylprednisolone", "betamethasone", "dexamethasone",
    "triamcinolone", "fluocortolone", "hydrocortisone",
    "cortivazol", "paramethasone", "desoximetasone",
    "alclometasone", "clobetasol", "diflucortolone",
    "fluocinonide", "fluocinolone", "halcinonide",
    "halometasone", "mometasone", "prednicarbate",
    "triamcinolone", "acetonide", "amcinonide",
    "desonide", "diflorasone", "fludroxycortide",
    "flurandrenolide", "ulobetasol", "betamethasone",
    "dipropionate", "valerate", "benzoate",
    "anti", "inflammatoire", "steroidien",
    "non", "aspirine", "ibuprofene",
    "ketoprofene", "naproxene", "diclofenac",
    "indometacine", "sulindac", "etodolac",
    "fenoprofene", "flurbiprofene", "ketorolac",
    "lornoxicam", "meloxicam", "piroxicam",
    "tenoxicam", "celecoxib", "etoricoxib",
    "parecoxib", "rofecoxib", "valdecoxib",
    "nimesulide", "nabumetone", "oxyphenbutazone",
    "phénylbutazone", "azapropazone", "clofezone",
    "kebuzone", "suxibuzone", "acide",
    "mefenamique", "flufenamique", "meclofenamique",
    "niflumique", "tolfenamique", "acide",
    "tiaprofenique", "acide", "acetylsalicylique",
    "salicyle", "salicylate", "methyl",
    "sodium", "choline", "salicylamide",
    "diflunisal", "salsalate", "benorilate",
    "paracetamol", "phenacetine", "propacetamol",
]

TERMES_GENERAUX = [
    "philosophie", "ontologie", "epistemologie", "metaphysique",
    "phenomenologie", "existentialisme", "stoicisme", "platon",
    "aristote", "kant", "nietzsche", "heidegger",
    "descartes", "hume", "locke", "rousseau",
    "justice", "liberte", "egalite", "démocratie",
    "totalitarisme", "souverainete", "citoyennete",
    "economie", "marche", "capitalisme", "socialisme",
    "mondialisation", "developpement", "durable",
    "anthropologie", "sociologie", "psychologie",
    "linguistique", "semiotique", "hermeneutique",
    "dialectique", "rhétorique", "logique",
    "analytique", "continentale", "comparative",
    "politique", "morale", "esthetique",
    "epistemique", "deontique", "axiologique",
    "teleologique", "causalite", "determinisme",
    "indeterminisme", "liberte", "necessite",
    "contingence", "possibilite", "actualite",
    "potentialite", "virtualite", "realite",
    "apparence", "essence", "existence",
    "substance", "accident", "attribut",
    "mode", "propriete", "relation",
    "categorie", "concept", "idee",
    "representation", "perception", "sensation",
    "intuition", "entendement", "raison",
    "intellect", "intelligence", "cognition",
    "conscience", "inconscient", "subconscient",
    "preconscient", "attention", "memorire",
    "apprentissage", "connaissance", "savoir",
    "croyance", "doute", "certitude",
    "verite", "faussete", "vraisemblance",
    "probabilite", "evidence", "demonstration",
    "argument", "raisonnement", "inference",
    "deduction", "induction", "abduction",
    "analogie", "metaphore", "symbole",
    "signe", "signification", "sens",
    "reference", "denotation", "connotation",
    "intension", "extension", "comprehension",
    "universel", "particulier", "singulier",
    "general", "abstrait", "concret",
    "transcendantal", "transcendant", "immanent",
    "apriorique", "aposteriorique", "synthetique",
    "analytique", "empirique", "rationnel",
    "speculatif", "pratique", "theorique",
    "contemplatif", "reflexif", "critique",
    "dogmatique", "sceptique", "relativiste",
    "absolutiste", "pragmatiste", "positiviste",
    "empiriste", "rationaliste", "idealiste",
    "materialiste", "dualiste", "moniste",
    "pluraliste", "holiste", "individualiste",
    "collectiviste", "universaliste", "particulariste",
    "communautariste", "cosmopolite", "patriote",
    "nationaliste", "internationaliste", "federaliste",
    "confederaliste", "unitaire", "regionaliste",
    "autonomiste", "independantiste", "separatiste",
    "revolutionnaire", "reformiste", "conservateur",
    "liberal", "social", "democrate",
    "republicain", "monarchiste", "anarchiste",
    "syndicaliste", "mutualiste", "cooperatiste",
    "militant", "activiste", "engagement",
    "resistance", "dissidence", "contestation",
    "protestation", "revolte", "insurrection",
    "emancipation", "liberation", "affranchissement",
    "autonomie", "independance", "souverainete",
    "colonialisme", "imperialisme", "neocolonialisme",
    "decolonisation", "postcolonialisme", "tiers-mondisme",
    "developpementalisme", "modernisation", "industrialisation",
    "urbanisation", "migration", "diaspora",
    "exil", "refugie", "asile",
    "apatride", "naturalisation", "integration",
    "assimilation", "acculturation", "interculturel",
    "multiculturalisme", "diversite", "inclusion",
    "exclusion", "discrimination", "segregation",
    "apartheid", "racisme", "xenophobie",
    "antisemitisme", "islamophobie", "homophobie",
    "transphobie", "sexisme", "misogynie",
    "patriarcat", "feminisme", "masculinisme",
    "egalite", "parite", "mixite",
    "genre", "identite", "sexualite",
    "orientation", "norme", "deviance",
    "stigmatisation", "marginalisation", "precarite",
    "vulnerabilite", "resilience", "capacitacion",
    "empowerment", "agency", "autodetermination",
    "participation", "representation", "deliberation",
    "concertation", "negociation", "mediation",
    "arbitrage", "conciliation", "transaction",
    "compromis", "consensus", "dissensus",
    "conflit", "cooperation", "competition",
    "collaboration", "solidarite", "reciprocite",
    "altruisme", "egoisme", "interet",
    "utilite", "bien", "mal",
    "vertu", "vice", "ethique",
    "morale", "devoir", "obligation",
    "droit", "loi", "justice",
    "equite", "impartialite", "objectivite",
    "neutralite", "independance", "integrite",
    "honnetete", "probit", "transparence",
    "responsabilite", "imputabilite", "reddition",
    "compte", "gouvernance", "management",
    "administration", "bureaucratie", "technocratie",
    "meritocratie", "plutocratie", "oligarchie",
    "aristocratie", "theocratie", "autocratie",
    "dictature", "tyrannie", "despotisme",
    "absolutisme", "autoritarisme", "totalitarisme",
    "fascisme", "nazisme", "communisme",
    "socialisme", "capitalisme", "liberalisme",
    "neoliberalisme", "conservatisme", "traditionalisme",
    "progressisme", "populisme", "nationalisme",
    "internationalisme", "globalisme", "regionalisme",
    "federalisme", "confederalisme", "centralisme",
    "decentralisation", "subsidiarite", "autonomie",
    "souverainisme", "euroscepticisme", "atlantisme",
    "occidentalisme", "orientalisme", "afrocentrisme",
    "panafricanisme", "négritude", "consciencisme",
    "humanisme", "transhumanisme", "posthumanisme",
    "antihumanisme", "existentialisme", "absurde",
    "nihilisme", "relativisme", "scepticisme",
    "pragmatisme", "instrumentalisme", "fonctionnalisme",
    "structuralisme", "poststructuralisme", "deconstruction",
    "postmodernisme", "modernisme", "classicisme",
    "romantisme", "realisme", "naturalisme",
    "symbolisme", "surrealisme", "expressionnisme",
    "impressionnisme", "abstractionnisme", "cubisme",
    "futurisme", "dadaisme", "lettrisme",
    "situationnisme", "conceptualisme", "minimalisme",
    "art", "esthetique", "beaute",
    "sublime", "tragique", "comique",
    "grotesque", "ironique", "satirique",
    "parodique", "pastiche", "hommage",
    "citation", "intertextualite", "hypertextualite",
    "metatextualite", "architextualite", "paratextualite",
    "narratologie", "poetique", "rhétorique",
    "stylistique", "metrique", "versification",
    "prosodie", "phonologie", "phonetique",
    "morphologie", "syntaxe", "semantique",
    "pragmatique", "lexicologie", "lexicographie",
    "terminologie", "philologie", "etymologie",
    "orthographe", "grammaire", "conjugaison",
    'declinaison', "accord", "rection",
]

# Fusionner tous les termes supplementaires
TERMES_ELARGIS = set(TERMES_MEDICAUX + TERMES_GENERAUX)

def telecharger_et_filtrer():
    """Telecharge cc.fr.300.vec.gz et ne garde que les vecteurs du vocabulaire."""
    os.makedirs(KB_DIR, exist_ok=True)
    
    # Verifier si le fichier filtre existe deja
    if os.path.exists(PRETRAINED_VECS_FILE) and os.path.exists(PRETRAINED_WORDS_FILE):
        print(f"[OK] Vecteurs pre-entraines deja presents:")
        print(f"  Vecteurs: {PRETRAINED_VECS_FILE}")
        print(f"  Mots: {PRETRAINED_WORDS_FILE}")
        return True
    
    # Vocabulaire cible
    vocab_cible = VOCAB | TERMES_ELARGIS
    print(f"Vocabulaire cible: {len(vocab_cible)} mots")
    print(f"  Vocabulaire etendu: {len(VOCAB)}")
    print(f"  Termes elargis: {len(TERMES_ELARGIS)}")
    
    # Telecharger avec requests (streaming)
    print(f"\nTelechargement de {CC_FR_URL}...")
    print(f"  Taille: ~2.1 GB compresse (gz)")
    print(f"  Ceci peut prendre plusieurs minutes...")
    
    try:
        import requests
    except ImportError:
        print("[ERREUR] requests non installe. Installer avec: pip install requests")
        return False
    
    try:
        # Telechargement avec streaming
        t0 = time.time()
        response = requests.get(CC_FR_URL, stream=True, timeout=300)
        response.raise_for_status()
        
        # Compter le total pour la progression
        total_bytes = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        # Decompresser et filtrer en streaming
        mots_gardes: List[str] = []
        vecteurs_gardes: List[List[float]] = []
        
        # Lire le .gz en streaming
        decompressor = gzip.GzipFile(fileobj=response.raw)
        
        # Lire la premiere ligne (header: "nb_mots dim")
        header_line = decompressor.readline().decode('utf-8').strip()
        header_parts = header_line.split()
        n_total = int(header_parts[0]) if len(header_parts) > 0 else 0
        dim = int(header_parts[1]) if len(header_parts) > 1 else 300
        print(f"  Header: {n_total} mots, {dim} dimensions")
        
        # Lire les lignes une par une
        ligne_num = 0
        gardes = 0
        skipped = 0
        last_report = time.time()
        
        for line_bytes in decompressor:
            ligne_num += 1
            if ligne_num % 100000 == 0:
                now = time.time()
                if now - last_report > 2.0:
                    elapsed = now - t0
                    rate = ligne_num / elapsed if elapsed > 0 else 0
                    print(f"    Lu {ligne_num}/{n_total} lignes "
                          f"({ligne_num*100//n_total}%), "
                          f"{gardes} gardes, {rate:.0f} lignes/s")
                    last_report = now
            
            # Decoder la ligne
            line = line_bytes.decode('utf-8', errors='replace').strip()
            if not line:
                continue
            
            # Extraire le mot et les valeurs
            first_space = line.find(' ')
            if first_space < 0:
                skipped += 1
                continue
            
            word = line[:first_space]
            
            # Verifier si le mot est dans notre vocabulaire cible
            if word.lower() not in vocab_cible and word not in vocab_cible:
                skipped += 1
                continue
            
            # Extraire les valeurs du vecteur
            values_str = line[first_space+1:].strip()
            values = values_str.split(' ')
            
            if len(values) != dim:
                skipped += 1
                continue
            
            try:
                vec = [float(v) for v in values]
            except ValueError:
                skipped += 1
                continue
            
            vecteurs_gardes.append(vec)
            mots_gardes.append(word)
            gardes += 1
        
        dt = time.time() - t0
        print(f"\nTelechargement et filtrage termines en {dt:.1f}s")
        print(f"  Lues: {ligne_num} lignes")
        print(f"  Gardes: {gardes} mots")
        print(f"  Ignorees: {skipped} lignes")
        
        if gardes == 0:
            print("[ERREUR] Aucun vecteur garde !")
            return False
        
        # Convertir en numpy array pour stockage compact
        import numpy as np
        vec_array = np.array(vecteurs_gardes, dtype=np.float32)
        
        # Normaliser les vecteurs (L2)
        norms = np.linalg.norm(vec_array, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        vec_array = vec_array / norms
        
        # Sauvegarder
        np.save(PRETRAINED_VECS_FILE, vec_array)
        
        with open(PRETRAINED_WORDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(mots_gardes, f, ensure_ascii=False)
        
        # Metadonnees
        meta = {
            "n_mots": gardes,
            "dimension": dim,
            "source": "cc.fr.300 (Common Crawl, Facebook)",
            "filtre_sur": f"vocabulaire_etendu ({len(VOCAB)} tokens) + termes_elargis ({len(TERMES_ELARGIS)})",
            "normalise": True,
            "norme": "L2",
        }
        with open(PRETRAINED_META_FILE, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        
        size_mb = os.path.getsize(PRETRAINED_VECS_FILE) / (1024 * 1024)
        print(f"\n[OK] Vecteurs pre-entraines sauvegardes:")
        print(f"  Vecteurs: {PRETRAINED_VECS_FILE} ({size_mb:.1f} MB)")
        print(f"  Mots: {PRETRAINED_WORDS_FILE}")
        print(f"  Dimension: {dim}")
        print(f"  {gardes} vecteurs au total")
        
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"[ERREUR] Telechargement echoue: {e}")
        return False
    except Exception as e:
        print(f"[ERREUR] {e}")
        return False


def verifier_structure_fichier_vec(filepath: str) -> bool:
    """Verifie la structure du fichier .vec (format texte fastText)."""
    try:
        import gzip
        with gzip.open(filepath, 'rt', encoding='utf-8', errors='replace') as f:
            header = f.readline().strip()
            parts = header.split()
            if len(parts) >= 2:
                n = int(parts[0])
                dim = int(parts[1])
                print(f"  Fichier .vec valide: {n} mots, {dim} dimensions")
                return True
        return False
    except Exception:
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("TELECHARGEMENT VECTEURS FASTTEXT PRE-ENTRAINES")
    print("=" * 60)
    
    if telecharger_et_filtrer():
        print("\n[SUCCES] Vecteurs pre-entraines prets pour l'expansion OOV !")
        print(f"  Dossier: {KB_DIR}")
    else:
        print("\n[ECHEC] Le telechargement a echoue.")
        print("Verifiez votre connexion internet et reessayez.")
        print("Le systeme continuera de fonctionner avec le fallback n-grams.")
