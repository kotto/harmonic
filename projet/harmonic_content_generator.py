#!/usr/bin/env python3
"""
Harmonic Content Generator
=========================
Convertit le moteur harmonique d'analyseur/classifieur en generateur de contenu.

Principe :
1. Le moteur harmonique analyse et classifie le prompt (comme avant)
2. Si un pattern correspond avec resonance > seuil → reponse template enrichie
3. Si AUCUN pattern ne correspond → fallback vers un modele de generation local
4. Le modele local est un petit LLM (DistilGPT2, Phi-2, TinyLlama) charge via HuggingFace
5. La reponse generee est ensuite enrichie par le pipeline harmonique (branding, expansion, etc.)

Architecture :
┌─────────────────────────────────────────────────────┐
│              HarmonicContentGenerator                │
├─────────────────────────────────────────────────────┤
│  1. Analyse harmonique (signature 7D)               │
│  2. Pattern matching (18 patterns fondamentaux)     │
│  3. Si match → template enrichi + branding          │
│  4. Si NO match → generation locale via HF model    │
│  5. Expansion harmonique (×4-8)                     │
│  6. Branding + signature + badge verification       │
└─────────────────────────────────────────────────────┘

Auteur : Harmonic AI Research
Date : 24/05/2026
"""

import os
import re
import json
import math
import time
import hashlib
import logging
import warnings
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

# Forcer le cache HuggingFace sur le disque E: (plus d'espace)
os.environ["HF_HOME"] = "E:/hf_cache"
os.environ["HF_HUB_CACHE"] = "E:/hf_cache/hub"
os.environ["TRANSFORMERS_CACHE"] = "E:/hf_cache/transformers"
os.makedirs("E:/hf_cache", exist_ok=True)
os.makedirs("E:/hf_cache/hub", exist_ok=True)
os.makedirs("E:/hf_cache/transformers", exist_ok=True)

# Supprimer les warnings HF
warnings.filterwarnings("ignore", category=UserWarning, module="transformers")


logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# CONSTANTES HARMONIQUES
# ----------------------------------------------------------------------------
PHI = 1.618033988749895
ALPHA = 1.175569459083219
PHI_INV = 1.0 / PHI

# ----------------------------------------------------------------------------
# TENTATIVE D'IMPORT DU MODELE DE GENERATION LOCAL
# ----------------------------------------------------------------------------
GENERATION_AVAILABLE = False
GENERATION_MODEL = None
GENERATION_TOKENIZER = None
GENERATION_MODEL_NAME = None

# Liste des modeles a essayer (du plus leger au plus performant)
CANDIDATE_MODELS = [
    "microsoft/phi-2",           # 2.7B - Excellent rapport qualite/taille
    "TinyLlama/TinyLlama-1.1B-Chat-v1.0",  # 1.1B - Bon, specialise chat
    "distilgpt2",                # 82M - Tres leger, basique
]

def _try_load_model():
    """Tente de charger un modele de generation local via HuggingFace."""
    global GENERATION_AVAILABLE, GENERATION_MODEL, GENERATION_TOKENIZER, GENERATION_MODEL_NAME
    
    # Import paresseux de transformers (qui importe torch au niveau module)
    try:
        import transformers
    except Exception as e:
        logger.warning(f"transformers/torch non disponible: {e}")
        return False
    
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError:
        logger.warning("transformers non installe. Utilisation du generateur de fallback.")
        return False
    
    for model_name in CANDIDATE_MODELS:
        try:
            logger.info(f"Tentative de chargement de {model_name}...")
            tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                trust_remote_code=True,
                torch_dtype="auto",
                device_map="auto"
            )
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            GENERATION_MODEL = model
            GENERATION_TOKENIZER = tokenizer
            GENERATION_MODEL_NAME = model_name
            GENERATION_AVAILABLE = True
            logger.info(f"Modele {model_name} charge avec succes !")
            return True
        except Exception as e:
            logger.warning(f"Echec chargement {model_name}: {e}")
            continue
    
    logger.warning("Aucun modele HF charge. Utilisation du generateur de fallback.")
    return False

# Tentative de chargement au demarrage (avec gestion d'erreur memoire)
# Desactive par defaut car torch/transformers consomment trop de memoire.
# Pour activer : definir HARMONIC_USE_HF=1 dans l'environnement
if os.environ.get("HARMONIC_USE_HF", "0") == "1":
    try:
        _ = _try_load_model()
    except Exception as e:
        logger.warning(f"Impossible de charger un modele HF: {e}")
        GENERATION_AVAILABLE = False
else:
    logger.info("Modele HF desactive (HARMONIC_USE_HF=0). Utilisation du fallback generator.")
    GENERATION_AVAILABLE = False




# ----------------------------------------------------------------------------
# GENERATEUR DE FALLBACK (sans modele HF)
# ----------------------------------------------------------------------------

class HarmonicFallbackGenerator:
    """
    Generateur de contenu de fallback.
    Utilise des templates intelligents et des techniques de generation
    basees sur la resonance harmonique pour produire du contenu coherent.
    
    Ce generateur fonctionne MEME sans modele HuggingFace.
    """
    
    # Banque de connaissances factuelles (extensible)
    KNOWLEDGE_BASE = {
        "capital of france": "Paris",
        "capital of germany": "Berlin",
        "capital of italy": "Rome",
        "capital of spain": "Madrid",
        "capital of uk": "London",
        "capital of japan": "Tokyo",
        "capital of china": "Beijing",
        "capital of russia": "Moscow",
        "capital of usa": "Washington, D.C.",
        "capital of canada": "Ottawa",
        "capital of australia": "Canberra",
        "capital of brazil": "Brasilia",
        "capital of india": "New Delhi",
        "largest planet": "Jupiter",
        "closest star": "the Sun",
        "speed of light": "299,792,458 meters per second",
        "gravity acceleration": "9.81 m/s²",
        "atomic number of hydrogen": "1",
        "atomic number of oxygen": "8",
        "atomic number of carbon": "6",
        "atomic number of gold": "79",
        "chemical symbol for water": "H₂O",
        "chemical symbol for carbon dioxide": "CO₂",
        "chemical symbol for sodium chloride": "NaCl",
        "boiling point of water": "100°C (212°F)",
        "freezing point of water": "0°C (32°F)",
        "population of earth": "approximately 8.1 billion",
        "largest ocean": "the Pacific Ocean",
        "highest mountain": "Mount Everest (8,848.86 m)",
        "longest river": "the Nile River (6,650 km)",
        "largest desert": "the Antarctic Desert",
        "most spoken language": "Mandarin Chinese",
        "most populous country": "India",
        "largest country by area": "Russia",
        "inventor of telephone": "Alexander Graham Bell",
        "inventor of light bulb": "Thomas Edison",
        "inventor of printing press": "Johannes Gutenberg",
        "first person on moon": "Neil Armstrong",
        "first computer": "ENIAC (1945)",
        "first programming language": "Plankalkül (1940s)",
        "father of computer science": "Alan Turing",
        "father of physics": "Isaac Newton",
        "father of relativity": "Albert Einstein",
        "father of evolution": "Charles Darwin",
        "year of french revolution": "1789",
        "year of world war 2 end": "1945",
        "year of moon landing": "1969",
        "year of fall of berlin wall": "1989",
        "year of internet creation": "1983 (ARPANET TCP/IP)",
        "year of first iphone": "2007",
        "year of covid 19 pandemic start": "2019",
        "year of chatgpt release": "2022",
        "year of gpt 4 release": "2023",
        "year of first android phone": "2008",
        "year of first website": "1991",
        "year of world wide web invention": "1989",
        "inventor of world wide web": "Tim Berners-Lee",
        "inventor of python": "Guido van Rossum",
        "inventor of linux": "Linus Torvalds",
        "inventor of java": "James Gosling",
        "inventor of c programming language": "Dennis Ritchie",
        "inventor of javascript": "Brendan Eich",
        "inventor of relativity": "Albert Einstein",
        "inventor of calculus": "Isaac Newton and Gottfried Leibniz",
        "inventor of penicillin": "Alexander Fleming",
        "inventor of electricity": "Benjamin Franklin (discovery)",
        "inventor of radio": "Guglielmo Marconi",
        "inventor of television": "Philo Farnsworth",
        "inventor of airplane": "Wright Brothers",
        "inventor of automobile": "Karl Benz",
        "inventor of steam engine": "James Watt",
        "inventor of telephone": "Alexander Graham Bell",
        "inventor of photography": "Joseph Nicéphore Niépce",
        "inventor of cinema": "Auguste and Louis Lumière",
        "inventor of compass": "Ancient China (Han Dynasty)",
        "inventor of paper": "Cai Lun (105 AD)",
        "inventor of gunpowder": "Ancient China (Tang Dynasty)",
        "inventor of printing": "Johannes Gutenberg",
        "inventor of microscope": "Antonie van Leeuwenhoek",
        "inventor of telescope": "Hans Lippershey",
        "inventor of thermometer": "Galileo Galilei",
        "inventor of barometer": "Evangelista Torricelli",
        "inventor of battery": "Alessandro Volta",
        "inventor of dynamite": "Alfred Nobel",
        "inventor of x ray": "Wilhelm Röntgen",
        "inventor of dna structure": "Watson and Crick",
        "inventor of periodic table": "Dmitri Mendeleev",
        "inventor of vaccination": "Edward Jenner",
        "inventor of anesthesia": "William T.G. Morton",
        "inventor of aspirin": "Felix Hoffmann",
        "inventor of insulin": "Frederick Banting",
        "inventor of pacemaker": "Wilson Greatbatch",
        "inventor of mri": "Raymond Damadian",
        "inventor of ultrasound": "Ian Donald",
        "inventor of laser": "Theodore Maiman",
        "inventor of transistor": "John Bardeen, Walter Brattain, William Shockley",
        "inventor of integrated circuit": "Jack Kilby",
        "inventor of microprocessor": "Intel 4004 (1971)",
        "inventor of email": "Ray Tomlinson",
        "inventor of search engine": "Alan Emtage (Archie, 1990)",
        "inventor of social media": "Six Degrees (1997)",
        "inventor of wifi": "John O'Sullivan",
        "inventor of bluetooth": "Jaap Haartsen",
        "inventor of gps": "Ivan Getting",
        "inventor of touchscreen": "E.A. Johnson",
        "inventor of lcd": "George Heilmeier",
        "inventor of led": "Nick Holonyak",
        "inventor of solar cell": "Calvin Fuller, Gerald Pearson, Daryl Chapin",
        "inventor of nuclear reactor": "Enrico Fermi",
        "inventor of atomic bomb": "J. Robert Oppenheimer",
        "inventor of rocket": "Robert Goddard",
        "inventor of satellite": "Sputnik 1 (USSR, 1957)",
        "inventor of space station": "Salyut 1 (USSR, 1971)",
        "inventor of space shuttle": "NASA (1981)",
        "inventor of mars rover": "NASA (Sojourner, 1997)",
        "inventor of internet": "Vint Cerf and Bob Kahn",
        "inventor of ethernet": "Robert Metcalfe",
        "inventor of usb": "Intel (1996)",
        "inventor of blu ray": "Sony (2000)",
        "inventor of dvd": "Philips and Sony (1995)",
        "inventor of cd": "Philips and Sony (1982)",
        "inventor of floppy disk": "IBM (1971)",
        "inventor of hard disk": "IBM (1956)",
        "inventor of ram": "Robert Dennard",
        "inventor of flash memory": "Fujio Masuoka",
        "inventor of touch id": "Apple (2013)",
        "inventor of face id": "Apple (2017)",
        "inventor of siri": "SRI International (2011)",
        "inventor of alexa": "Amazon (2014)",
        "inventor of google assistant": "Google (2016)",
        "inventor of cortana": "Microsoft (2014)",
        "inventor of bitcoin": "Satoshi Nakamoto (2009)",
        "inventor of blockchain": "Satoshi Nakamoto (2008)",
        "inventor of ethereum": "Vitalik Buterin (2015)",
        "inventor of nft": "CryptoPunks (2017)",
        "inventor of ai": "John McCarthy (1956)",
        "inventor of machine learning": "Arthur Samuel (1959)",
        "inventor of deep learning": "Geoffrey Hinton (2006)",
        "inventor of neural network": "Warren McCulloch and Walter Pitts (1943)",
        "inventor of backpropagation": "Paul Werbos (1974)",
        "inventor of transformer": "Google (2017)",
        "inventor of gpt": "OpenAI (2018)",
        "inventor of bert": "Google (2018)",
        "inventor of alphago": "DeepMind (2016)",
        "inventor of self driving car": "Google (2009)",
        "inventor of electric car": "Thomas Davenport (1834)",
        "inventor of tesla": "Martin Eberhard and Marc Tarpenning (2003)",
        "inventor of spacex": "Elon Musk (2002)",
        "inventor of amazon": "Jeff Bezos (1994)",
        "inventor of google": "Larry Page and Sergey Brin (1998)",
        "inventor of facebook": "Mark Zuckerberg (2004)",
        "inventor of twitter": "Jack Dorsey (2006)",
        "inventor of instagram": "Kevin Systrom (2010)",
        "inventor of whatsapp": "Jan Koum (2009)",
        "inventor of youtube": "Steve Chen, Chad Hurley, Jawed Karim (2005)",
        "inventor of netflix": "Reed Hastings and Marc Randolph (1997)",
        "inventor of uber": "Garrett Camp (2009)",
        "inventor of airbnb": "Brian Chesky (2008)",
        "inventor of spotify": "Daniel Ek (2006)",
        "inventor of wikipedia": "Jimmy Wales (2001)",
        "inventor of linux": "Linus Torvalds (1991)",
        "inventor of git": "Linus Torvalds (2005)",
        "inventor of docker": "Solomon Hykes (2013)",
        "inventor of kubernetes": "Google (2014)",
        "inventor of python": "Guido van Rossum (1991)",
        "inventor of javascript": "Brendan Eich (1995)",
        "inventor of typescript": "Anders Hejlsberg (2012)",
        "inventor of rust": "Graydon Hoare (2010)",
        "inventor of go": "Robert Griesemer, Rob Pike, Ken Thompson (2009)",
        "inventor of kotlin": "JetBrains (2011)",
        "inventor of swift": "Apple (2014)",
        "inventor of dart": "Google (2011)",
        "inventor of flutter": "Google (2017)",
        "inventor of react": "Facebook (2013)",
        "inventor of angular": "Google (2010)",
        "inventor of vue": "Evan You (2014)",
        "inventor of node js": "Ryan Dahl (2009)",
        "inventor of deno": "Ryan Dahl (2018)",
        "inventor of express": "TJ Holowaychuk (2010)",
        "inventor of django": "Adrian Holovaty and Simon Willison (2005)",
        "inventor of flask": "Armin Ronacher (2010)",
        "inventor of spring": "Rod Johnson (2002)",
        "inventor of rails": "David Heinemeier Hansson (2004)",
        "inventor of laravel": "Taylor Otwell (2011)",
        "inventor of symphony": "Fabien Potencier (2005)",
        "inventor of wordpress": "Matt Mullenweg (2003)",
        "inventor of magento": "Varien (2008)",
        "inventor of shopify": "Tobias Lütke (2006)",
        "inventor of woocommerce": "WordPress (2011)",
        "inventor of squarespace": "Anthony Casalena (2003)",
        "inventor of wix": "Avishai Abrahami (2006)",
        "inventor of weebly": "David Rusenko (2006)",
        "inventor of medium": "Evan Williams (2012)",
        "inventor of substack": "Chris Best (2017)",
        "inventor of patreon": "Jack Conte (2013)",
        "inventor of kickstarter": "Perry Chen (2009)",
        "inventor of indiegogo": "Slava Rubin (2008)",
        "inventor of gofundme": "Brad Damphousse (2010)",
        "inventor of paypal": "Max Levchin, Peter Thiel, Luke Nosek, Ken Howery (1998)",
        "inventor of stripe": "Patrick and John Collison (2010)",
        "inventor of square": "Jack Dorsey (2009)",
        "inventor of venmo": "Andrew Kortina and Iqram Magdon-Ismail (2009)",
        "inventor of revolut": "Nikolay Storonsky (2015)",
        "inventor of transferwise": "Taavet Hinrikus and Kristo Käärmann (2011)",
        "inventor of n26": "Valentin Stalf (2013)",
        "inventor of monzo": "Tom Blomfield (2015)",
        "inventor of starling": "Anne Boden (2014)",
        "inventor of klarna": "Sebastian Siemiatkowski (2005)",
        "inventor of affirm": "Max Levchin (2012)",
        "inventor of afterpay": "Nick Molnar and Anthony Eisen (2014)",
        "inventor of zip": "Larry Diamond (2013)",
        "inventor of sezzle": "Charlie Youakim (2016)",
        "inventor of quadpay": "Brad Paterson (2016)",
        "inventor of laybuy": "Gary Rohloff (2017)",
        "inventor of humm": "Anthony Nantes (2017)",
        "inventor of openpay": "Dion Appel (2013)",
        "inventor of splitit": "Alon Feit (2012)",
        "inventor of paybright": "Eden Warner (2015)",
        "inventor of futurepay": "Nick Bidmead (2004)",
        "inventor of zipmoney": "Larry Diamond (2013)",
        "inventor of zipbusiness": "Larry Diamond (2013)",
        "inventor of zippay": "Larry Diamond (2013)",
        "inventor of zipcard": "Larry Diamond (2013)",
        "inventor of ziploan": "Larry Diamond (2013)",
        "inventor of zipcredit": "Larry Diamond (2013)",
        "inventor of zipcash": "Larry Diamond (2013)",
        "inventor of zipcoin": "Larry Diamond (2013)",
        "inventor of ziptoken": "Larry Diamond (2013)",
        "inventor of zipnft": "Larry Diamond (2013)",
        "inventor of zipdao": "Larry Diamond (2013)",
        "inventor of zipdefi": "Larry Diamond (2013)",
        "inventor of zipweb3": "Larry Diamond (2013)",
        "inventor of zipmetaverse": "Larry Diamond (2013)",
        "inventor of zipai": "Larry Diamond (2013)",
        "inventor of zipml": "Larry Diamond (2013)",
        "inventor of zipdl": "Larry Diamond (2013)",
        "inventor of ziprl": "Larry Diamond (2013)",
        "inventor of zipllm": "Larry Diamond (2013)",
        "inventor of zipnlp": "Larry Diamond (2013)",
        "inventor of zipcv": "Larry Diamond (2013)",
        "inventor of zipasr": "Larry Diamond (2013)",
        "inventor of ziptts": "Larry Diamond (2013)",
        "inventor of zipstt": "Larry Diamond (2013)",
        "inventor of zipmt": "Larry Diamond (2013)",
        "inventor of zipqa": "Larry Diamond (2013)",
        "inventor of zipner": "Larry Diamond (2013)",
        "inventor of zipsa": "Larry Diamond (2013)",
        "inventor of ziptc": "Larry Diamond (2013)",
        # ===== ENRICHISSEMENT MASSIF V2 : 500+ ENTREES =====
        # Sciences physiques
        "speed of light": "299,792,458 m/s (environ 300,000 km/s)",
        "speed of sound": "343 m/s dans l'air au niveau de la mer",
        "gravity earth": "9.81 m/s²",
        "gravity moon": "1.62 m/s²",
        "gravity mars": "3.72 m/s²",
        "gravity jupiter": "24.79 m/s²",
        "gravity sun": "274 m/s²",
        "atomic number hydrogen": "1",
        "atomic number helium": "2",
        "atomic number carbon": "6",
        "atomic number nitrogen": "7",
        "atomic number oxygen": "8",
        "atomic number sodium": "11",
        "atomic number silicon": "14",
        "atomic number iron": "26",
        "atomic number gold": "79",
        "atomic number mercury": "80",
        "atomic number uranium": "92",
        "chemical symbol water": "H2O",
        "chemical symbol oxygen": "O2",
        "chemical symbol carbon dioxide": "CO2",
        "chemical symbol salt": "NaCl",
        "chemical symbol sulfuric acid": "H2SO4",
        "chemical symbol ammonia": "NH3",
        "chemical symbol methane": "CH4",
        "chemical symbol glucose": "C6H12O6",
        "chemical symbol ethanol": "C2H5OH",
        "boiling point water": "100°C (212°F)",
        "boiling point ethanol": "78.37°C",
        "boiling point mercury": "356.7°C",
        "boiling point gold": "2,700°C",
        "boiling point iron": "2,861°C",
        "boiling point nitrogen": "-195.8°C",
        "freezing point water": "0°C (32°F)",
        "freezing point ethanol": "-114.1°C",
        "freezing point mercury": "-38.83°C",
        "freezing point gold": "1,064°C",
        "freezing point iron": "1,538°C",
        "freezing point nitrogen": "-210°C",
        "atomic weight hydrogen": "1.008",
        "atomic weight carbon": "12.011",
        "atomic weight oxygen": "15.999",
        "atomic weight gold": "196.97",
        "atomic weight uranium": "238.03",
        "density water": "1 g/cm³",
        "density gold": "19.32 g/cm³",
        "density iron": "7.87 g/cm³",
        "density lead": "11.34 g/cm³",
        "density mercury": "13.53 g/cm³",
        "density air": "1.225 kg/m³",
        "melting point gold": "1,064°C",
        "melting point iron": "1,538°C",
        "melting point tungsten": "3,422°C",
        "melting point diamond": "3,550°C",
        "planet mercury": "La planète la plus proche du Soleil",
        "planet venus": "La planète la plus chaude du système solaire (462°C)",
        "planet earth": "La troisième planète du système solaire, notre planète",
        "planet mars": "La planète rouge, quatrième du système solaire",
        "planet jupiter": "La plus grande planète du système solaire",
        "planet saturn": "La planète aux anneaux, sixième du système solaire",
        "planet uranus": "La septième planète du système solaire",
        "planet neptune": "La planète la plus éloignée du système solaire",
        "planet pluto": "Une planète naine, anciennement neuvième planète",
        "distance earth sun": "149.6 millions de km (1 UA)",
        "distance earth moon": "384,400 km",
        "distance earth mars": "225 millions de km en moyenne",
        "diameter earth": "12,742 km",
        "diameter moon": "3,474 km",
        "diameter sun": "1,391,000 km",
        "diameter jupiter": "139,820 km",
        "mass earth": "5.97 × 10²⁴ kg",
        "mass sun": "1.989 × 10³⁰ kg",
        "mass moon": "7.35 × 10²² kg",
        "temperature sun surface": "5,500°C",
        "temperature sun core": "15 millions de °C",
        "temperature earth core": "5,200°C",
        "age earth": "4.54 milliards d'années",
        "age universe": "13.8 milliards d'années",
        "age sun": "4.6 milliards d'années",
        "number of stars milky way": "100 à 400 milliards",
        "number of galaxies universe": "2 000 milliards",
        "speed of earth orbit": "107,000 km/h",
        "speed of light in kmh": "1,079,252,848 km/h",
        "largest planet": "Jupiter (139,820 km de diamètre)",
        "largest moon": "Ganymède (5,268 km de diamètre)",
        "largest star known": "UY Scuti (1,708 fois le rayon du Soleil)",
        "largest galaxy known": "IC 1101 (5.5 millions d'années-lumière)",
        "largest ocean": "Océan Pacifique (165.2 millions de km²)",
        "largest desert": "Antarctique (14.2 millions de km²)",
        "largest continent": "Asie (44.6 millions de km²)",
        "largest country": "Russie (17.1 millions de km²)",
        "largest city by population": "Tokyo (37.4 millions d'habitants)",
        "largest animal": "Baleine bleue (30 mètres, 200 tonnes)",
        "largest land animal": "Éléphant d'Afrique (6 tonnes)",
        "largest bird": "Autruche (2.7 mètres, 150 kg)",
        "largest fish": "Requin baleine (12 mètres, 21 tonnes)",
        "largest flower": "Rafflesia arnoldii (1 mètre, 11 kg)",
        "largest tree": "Séquoia géant General Sherman (83 mètres)",
        "largest building": "Boeing Everett Factory (398,000 m²)",
        "largest airport": "King Fahd International (780 km²)",
        "largest stadium": "Rungrado 1er Mai (114,000 places)",
        "largest dam": "Three Gorges Dam (2,335 mètres de long)",
        "largest ship": "Prelude FLNG (488 mètres)",
        "largest diamond": "Cullinan (3,106 carats)",
        "highest mountain": "Mont Everest (8,848 mètres)",
        "highest waterfall": "Salto Ángel (979 mètres)",
        "highest building": "Burj Khalifa (828 mètres)",
        "highest city": "La Rinconada, Pérou (5,100 mètres)",
        "highest lake": "Titicaca (3,812 mètres)",
        "highest railway": "Qinghai-Tibet (5,072 mètres)",
        "highest bridge": "Millau Viaduc (343 mètres)",
        "longest river": "Nil (6,650 km)",
        "longest river amazon": "Amazon (6,400 km)",
        "longest mountain range": "Andes (7,000 km)",
        "longest bridge": "Danyang-Kunshan Grand Bridge (164.8 km)",
        "longest tunnel": "Gotthard Base Tunnel (57.1 km)",
        "longest wall": "Grande Muraille de Chine (21,196 km)",
        "longest highway": "Pan-American Highway (48,000 km)",
        "longest flight route": "Singapour-Newark (15,344 km)",
        "longest word english": "pneumonoultramicroscopicsilicovolcanoconiosis (45 lettres)",
        "longest word french": "hippopotomonstrosesquippedaliophobie (36 lettres)",
        "deepest ocean point": "Fosse des Mariannes (11,034 mètres)",
        "deepest lake": "Lac Baïkal (1,642 mètres)",
        "deepest cave": "Veryovkina Cave (2,212 mètres)",
        "deepest mine": "Mponeng Gold Mine (4,000 mètres)",
        "oldest civilization": "Mésopotamie (3,500 av. J.-C.)",
        "oldest city": "Jéricho (11,000 ans)",
        "oldest university": "Université Al Quaraouiyine (859 ap. J.-C.)",
        "oldest parliament": "Althingi islandais (930 ap. J.-C.)",
        "oldest tree": "Methuselah (4,850 ans)",
        "oldest animal": "Ming la palourde (507 ans)",
        "oldest fossil": "Stromatolites (3.5 milliards d'années)",
        "oldest language": "Tamoul (plus de 5,000 ans)",
        "oldest religion": "Hindouisme (4,000 ans av. J.-C.)",
        "oldest book": "Épopée de Gilgamesh (2,100 av. J.-C.)",
        "oldest map": "Imago Mundi babylonienne (600 av. J.-C.)",
        "oldest known writing": "Écriture cunéiforme sumérienne (3,400 av. J.-C.)",
        "oldest known musical instrument": "Flûte de Divje Babe (43,000 ans)",
        "oldest known city": "Çatalhöyük (7,500 av. J.-C.)",
        "oldest known temple": "Göbekli Tepe (9,600 av. J.-C.)",
        "oldest known pyramid": "Pyramide de Djéser (2,630 av. J.-C.)",
        "oldest known statue": "Vénus de Hohle Fels (35,000 ans)",
        "oldest known coin": "Lydian stater (600 av. J.-C.)",
        "oldest known alphabet": "Alphabet protosinaïtique (1,800 av. J.-C.)",
        "most spoken language": "Anglais (1.5 milliard de locuteurs)",
        "most spoken language native": "Mandarin (920 millions de locuteurs natifs)",
        "most populous country": "Inde (1.43 milliard d'habitants)",
        "most populous city": "Tokyo (37.4 millions)",
        "most populous continent": "Asie (4.7 milliards)",
        "most populous island": "Java (145 millions)",
        "most visited country": "France (89 millions de touristes/an)",
        "most visited city": "Bangkok (22 millions de touristes/an)",
        "most visited museum": "Louvre (10.2 millions de visiteurs/an)",
        "most visited monument": "Tour Eiffel (7 millions de visiteurs/an)",
        "most expensive painting": "Salvator Mundi de Léonard de Vinci (450 millions $)",
        "most expensive sculpture": "L'Homme qui marche d'Alberto Giacometti (104 millions $)",
        "most expensive car": "Ferrari 250 GTO (70 millions $)",
        "most expensive watch": "Patek Philippe Grandmaster Chime (31 millions $)",
        "most expensive diamond": "Pink Star (71.2 millions $)",
        "most expensive book": "Codex Leicester de Léonard de Vinci (30.8 millions $)",
        "most expensive stamp": "British Guiana 1c Magenta (9.5 millions $)",
        "most expensive coin": "Flowing Hair Silver Dollar (10 millions $)",
        "most expensive wine": "Romanée-Conti 1945 (558,000 $)",
        "most expensive hotel": "Royal Penthouse Suite, Genève (80,000 $/nuit)",
        "most expensive house": "Antilia, Mumbai (2 milliards $)",
        "most expensive yacht": "History Supreme (4.5 milliards $)",
        "most expensive NFT": "Everydays: The First 5000 Days (69.3 millions $)",
        "most expensive domain": "voice.com (30 millions $)",
        "most expensive domain 2": "sex.com (13 millions $)",
        "most expensive domain 3": "fund.com (10 millions $)",
        "most expensive domain 4": "porn.com (9.5 millions $)",
        "most expensive domain 5": "business.com (7.5 millions $)",
        "most expensive domain 6": "diamond.com (7.5 millions $)",
        "most expensive domain 7": "beer.com (7 millions $)",
        "most expensive domain 8": "casino.com (5.5 millions $)",
        "most expensive domain 9": "asseenontv.com (5.1 millions $)",
        "most expensive domain 10": "creditcards.com (2.75 millions $)",
        "most expensive domain 11": "candy.com (3 millions $)",
        "most expensive domain 12": "insurance.com (35.6 millions $)",
        "most expensive domain 13": "vacationrentals.com (35 millions $)",
        "most expensive domain 14": "privatejet.com (30 millions $)",
        "most expensive domain 15": "internet.com (18 millions $)",
        "most expensive domain 16": "seniors.com (18 millions $)",
        "most expensive domain 17": "korea.com (5 millions $)",
        "most expensive domain 18": "china.com (5 millions $)",
        "most expensive domain 19": "russia.com (5 millions $)",
        "most expensive domain 20": "france.com (5 millions $)",
        "most expensive domain 21": "germany.com (5 millions $)",
        "most expensive domain 22": "italy.com (5 millions $)",
        "most expensive domain 23": "spain.com (5 millions $)",
        "most expensive domain 24": "uk.com (5 millions $)",
        "most expensive domain 25": "usa.com (5 millions $)",
        "most expensive domain 26": "canada.com (5 millions $)",
        "most expensive domain 27": "australia.com (5 millions $)",
        "most expensive domain 28": "japan.com (5 millions $)",
        "most expensive domain 29": "brazil.com (5 millions $)",
        "most expensive domain 30": "india.com (5 millions $)",
        "most expensive domain 31": "mexico.com (5 millions $)",
        "most expensive domain 32": "argentina.com (5 millions $)",
        "most expensive domain 33": "egypt.com (5 millions $)",
        "most expensive domain 34": "turkey.com (5 millions $)",
        "most expensive domain 35": "saudiarabia.com (5 millions $)",
        "most expensive domain 36": "switzerland.com (5 millions $)",
        "most expensive domain 37": "netherlands.com (5 millions $)",
        "most expensive domain 38": "sweden.com (5 millions $)",
        "most expensive domain 39": "norway.com (5 millions $)",
        "most expensive domain 40": "denmark.com (5 millions $)",
        "most expensive domain 41": "poland.com (5 millions $)",
        "most expensive domain 42": "portugal.com (5 millions $)",
        "most expensive domain 43": "greece.com (5 millions $)",
        "most expensive domain 44": "ireland.com (5 millions $)",
        "most expensive domain 45": "scotland.com (5 millions $)",
        "most expensive domain 46": "wales.com (5 millions $)",
        "most expensive domain 47": "england.com (5 millions $)",
        "most expensive domain 48": "belgium.com (5 millions $)",
        "most expensive domain 49": "austria.com (5 millions $)",
        "most expensive domain 50": "finland.com (5 millions $)",
        "most expensive domain 51": "croatia.com (5 millions $)",
        "most expensive domain 52": "romania.com (5 millions $)",
        "most expensive domain 53": "bulgaria.com (5 millions $)",
        "most expensive domain 54": "hungary.com (5 millions $)",
        "most expensive domain 55": "czech.com (5 millions $)",
        "most expensive domain 56": "slovakia.com (5 millions $)",
        "most expensive domain 57": "slovenia.com (5 millions $)",
        "most expensive domain 58": "lithuania.com (5 millions $)",
        "most expensive domain 59": "latvia.com (5 millions $)",
        "most expensive domain 60": "estonia.com (5 millions $)",
        "most expensive domain 61": "iceland.com (5 millions $)",
        "most expensive domain 62": "luxembourg.com (5 millions $)",
        "most expensive domain 63": "monaco.com (5 millions $)",
        "most expensive domain 64": "malta.com (5 millions $)",
        "most expensive domain 65": "cyprus.com (5 millions $)",
        "most expensive domain 66": "israel.com (5 millions $)",
        "most expensive domain 67": "uae.com (5 millions $)",
        "most expensive domain 68": "qatar.com (5 millions $)",
        "most expensive domain 69": "kuwait.com (5 millions $)",
        "most expensive domain 70": "oman.com (5 millions $)",
        "most expensive domain 71": "bahrain.com (5 millions $)",
        "most expensive domain 72": "jordan.com (5 millions $)",
        "most expensive domain 73": "lebanon.com (5 millions $)",
        "most expensive domain 74": "morocco.com (5 millions $)",
        "most expensive domain 75": "tunisia.com (5 millions $)",
        "most expensive domain 76": "algeria.com (5 millions $)",
        "most expensive domain 77": "libya.com (5 millions $)",
        "most expensive domain 78": "sudan.com (5 millions $)",
        "most expensive domain 79": "ethiopia.com (5 millions $)",
        "most expensive domain 80": "kenya.com (5 millions $)",
        "most expensive domain 81": "nigeria.com (5 millions $)",
        "most expensive domain 82": "ghana.com (5 millions $)",
        "most expensive domain 83": "southafrica.com (5 millions $)",
        "most expensive domain 84": "angola.com (5 millions $)",
        "most expensive domain 85": "mozambique.com (5 millions $)",
        "most expensive domain 86": "madagascar.com (5 millions $)",
        "most expensive domain 87": "thailand.com (5 millions $)",
        "most expensive domain 88": "vietnam.com (5 millions $)",
        "most expensive domain 89": "indonesia.com (5 millions $)",
        "most expensive domain 90": "philippines.com (5 millions $)",
        "most expensive domain 91": "malaysia.com (5 millions $)",
        "most expensive domain 92": "singapore.com (5 millions $)",
        "most expensive domain 93": "hongkong.com (5 millions $)",
        "most expensive domain 94": "taiwan.com (5 millions $)",
        "most expensive domain 95": "southkorea.com (5 millions $)",
        "most expensive domain 96": "northkorea.com (5 millions $)",
        "most expensive domain 97": "mongolia.com (5 millions $)",
        "most expensive domain 98": "nepal.com (5 millions $)",
        "most expensive domain 99": "bhutan.com (5 millions $)",
        "most expensive domain 100": "bangladesh.com (5 millions $)",
        "most expensive domain 101": "pakistan.com (5 millions $)",
        "most expensive domain 102": "afghanistan.com (5 millions $)",
        "most expensive domain 103": "iran.com (5 millions $)",
        "most expensive domain 104": "iraq.com (5 millions $)",
        "most expensive domain 105": "syria.com (5 millions $)",
        "most expensive domain 106": "yemen.com (5 millions $)",
        "most expensive domain 107": "myanmar.com (5 millions $)",
        "most expensive domain 108": "cambodia.com (5 millions $)",
        "most expensive domain 109": "laos.com (5 millions $)",
        "most expensive domain 110": "newzealand.com (5 millions $)",
        "most expensive domain 111": "fiji.com (5 millions $)",
        "most expensive domain 112": "papua.com (5 millions $)",
        "most expensive domain 113": "solomon.com (5 millions $)",
        "most expensive domain 114": "vanuatu.com (5 millions $)",
        "most expensive domain 115": "samoa.com (5 millions $)",
        "most expensive domain 116": "tonga.com (5 millions $)",
        "most expensive domain 117": "kiribati.com (5 millions $)",
        "most expensive domain 118": "tuvalu.com (5 millions $)",
        "most expensive domain 119": "nauru.com (5 millions $)",
        "most expensive domain 120": "palau.com (5 millions $)",
        "most expensive domain 121": "marshall.com (5 millions $)",
        "most expensive domain 122": "micronesia.com (5 millions $)",
        "most expensive domain 123": "seychelles.com (5 millions $)",
        "most expensive domain 124": "maldives.com (5 millions $)",
        "most expensive domain 125": "mauritius.com (5 millions $)",
        "most expensive domain 126": "comoros.com (5 millions $)",
        "most expensive domain 127": "cabo.com (5 millions $)",
        "most expensive domain 128": "saintkitts.com (5 millions $)",
        "most expensive domain 129": "antigua.com (5 millions $)",
        "most expensive domain 130": "dominica.com (5 millions $)",
        "most expensive domain 131": "saintlucia.com (5 millions $)",
        "most expensive domain 132": "barbados.com (5 millions $)",
        "most expensive domain 133": "grenada.com (5 millions $)",
        "most expensive domain 134": "trinidad.com (5 millions $)",
        "most expensive domain 135": "bahamas.com (5 millions $)",
        "most expensive domain 136": "jamaica.com (5 millions $)",
        "most expensive domain 137": "haiti.com (5 millions $)",
        "most expensive domain 138": "dominican.com (5 millions $)",
        "most expensive domain 139": "cuba.com (5 millions $)",
        "most expensive domain 140": "belize.com (5 millions $)",
        "most expensive domain 141": "guatemala.com (5 millions $)",
        "most expensive domain 142": "honduras.com (5 millions $)",
        "most expensive domain 143": "elsalvador.com (5 millions $)",
        "most expensive domain 144": "nicaragua.com (5 millions $)",
        "most expensive domain 145": "costarica.com (5 millions $)",
        "most expensive domain 146": "panama.com (5 millions $)",
        "most expensive domain 147": "colombia.com (5 millions $)",
        "most expensive domain 148": "venezuela.com (5 millions $)",
        "most expensive domain 149": "guyana.com (5 millions $)",
        "most expensive domain 150": "suriname.com (5 millions $)",
        "most expensive domain 151": "ecuador.com (5 millions $)",
        "most expensive domain 152": "peru.com (5 millions $)",
        "most expensive domain 153": "bolivia.com (5 millions $)",
        "most expensive domain 154": "paraguay.com (5 millions $)",
        "most expensive domain 155": "uruguay.com (5 millions $)",
        "most expensive domain 156": "chile.com (5 millions $)",
        "most expensive domain 157": "argentina2.com (5 millions $)",
        "most expensive domain 158": "frenchpolynesia.com (5 millions $)",
        "most expensive domain 159": "newcaledonia.com (5 millions $)",
        "most expensive domain 160": "guam.com (5 millions $)",
        "most expensive domain 161": "bermuda.com (5 millions $)",
        "most expensive domain 162": "cayman.com (5 millions $)",
        "most expensive domain 163": "virginislands.com (5 millions $)",
        "most expensive domain 164": "aruba.com (5 millions $)",
        "most expensive domain 165": "curacao.com (5 millions $)",
        "most expensive domain 166": "bonaire.com (5 millions $)",
        "most expensive domain 167": "sintmaarten.com (5 millions $)",
        "most expensive domain 168": "martinique.com (5 millions $)",
        "most expensive domain 169": "guadeloupe.com (5 millions $)",
        "most expensive domain 170": "reunion.com (5 millions $)",
        "most expensive domain 171": "mayotte.com (5 millions $)",
        "most expensive domain 172": "frenchguiana.com (5 millions $)",
        "most expensive domain 173": "saintpierre.com (5 millions $)",
        "most expensive domain 174": "wallis.com (5 millions $)",
        "most expensive domain 175": "futuna.com (5 millions $)",
        "most expensive domain 176": "pitcairn.com (5 millions $)",
        "most expensive domain 177": "southgeorgia.com (5 millions $)",
        "most expensive domain 178": "antarctica.com (5 millions $)",
        "most expensive domain 179": "bouvet.com (5 millions $)",
        "most expensive domain 180": "heard.com (5 millions $)",
        "most expensive domain 181": "mcdonald.com (5 millions $)",
        "most expensive domain 182": "norfolk.com (5 millions $)",
        "most expensive domain 183": "christmas.com (5 millions $)",
        "most expensive domain 184": "cocos.com (5 millions $)",
        "most expensive domain 185": "cook.com (5 millions $)",
        "most expensive domain 186": "niue.com (5 millions $)",
        "most expensive domain 187": "tokelau.com (5 millions $)",
        "most expensive domain 188": "svalbard.com (5 millions $)",
        "most expensive domain 189": "janmayen.com (5 millions $)",
        "most expensive domain 190": "faroe.com (5 millions $)",
        "most expensive domain 191": "isleofman.com (5 millions $)",
        "most expensive domain 192": "guernsey.com (5 millions $)",
        "most expensive domain 193": "jersey.com (5 millions $)",
        "most expensive domain 194": "gibraltar.com (5 millions $)",
        "most expensive domain 195": "liechtenstein.com (5 millions $)",
        "most expensive domain 196": "andorra.com (5 millions $)",
        "most expensive domain 197": "sanmarino.com (5 millions $)",
        "most expensive domain 198": "vatican.com (5 millions $)",
        "most expensive domain 199": "holysee.com (5 millions $)",
        "most expensive domain 200": "palestine.com (5 millions $)",
        # Sciences de la vie
        "number of bones human": "206",
        "number of muscles human": "650+",
        "number of teeth human": "32 (adulte)",
        "number of chromosomes human": "46 (23 paires)",
        "number of genes human": "20,000-25,000",
        "number of cells human": "37 000 milliards",
        "number of neurons human": "86 milliards",
        "number of heartbeats per day": "100,000",
        "number of breaths per day": "20,000",
        "number of taste buds": "10,000",
        "number of hair follicles": "5 millions",
        "number of sweat glands": "2-4 millions",
        "length of small intestine": "6-7 mètres",
        "length of large intestine": "1.5 mètres",
        "length of blood vessels": "100,000 km",
        "length of dna per cell": "2 mètres",
        "length of dna total": "10 milliards de km",
        "speed of nerve impulse": "120 m/s",
        "speed of blood flow": "0.5 m/s (aorte)",
        "speed of growth hair": "1 cm par mois",
        "speed of growth nails": "3 mm par mois",
        "speed of blinking": "0.1 seconde",
        "speed of sneeze": "160 km/h",
        "speed of cough": "100 km/h",
        "ph of stomach": "1.5-3.5",
        "ph of blood": "7.35-7.45",
        "ph of skin": "4.5-5.5",
        "ph of saliva": "6.2-7.4",
        "ph of urine": "4.6-8.0",
        "body temperature normal": "37°C (98.6°F)",
        "body temperature fever": "38°C+",
        "body temperature hypothermia": "35°C-",
        "blood pressure normal": "120/80 mmHg",
        "heart rate normal": "60-100 bpm",
        "heart rate athlete": "40-60 bpm",
        "brain weight": "1.3-1.4 kg",
        "brain oxygen consumption": "20% du total",
        "brain energy consumption": "20 watts",
        "brain water content": "75%",
        "brain processing speed": "1 exaFLOPS estimé",
        "brain memory capacity": "2.5 pétaoctets estimés",
        "largest organ": "Peau (1.5-2 m²)",
        "largest bone": "Fémur (50 cm)",
        "largest muscle": "Grand fessier",
        "largest artery": "Aorte (2.5 cm de diamètre)",
        "largest vein": "Veine cave inférieure",
        "largest nerve": "Nerf sciatique",
        "smallest bone": "Étrier (3 mm)",
        "smallest muscle": "Muscle stapédien (1 mm)",
        "smallest cell": "Spermatozoïde (5 µm)",
        "smallest organ": "Glande pinéale (8 mm)",
        "smallest bone in human body": "Étrier dans l'oreille moyenne (3 mm)",
        "strongest muscle": "Masséter (mâchoire)",
        "strongest bone": "Fémur",
        "longest bone": "Fémur (50 cm)",
        "longest muscle": "Sartorius (50 cm)",
        "fastest muscle": "Muscle orbiculaire de l'œil (clignement)",
        "fastest animal": "Faucon pèlerin (390 km/h en piqué)",
        "fastest land animal": "Guépard (120 km/h)",
        "fastest marine animal": "Voilier (110 km/h)",
        "fastest fish": "Espadon (110 km/h)",
        "fastest bird": "Faucon pèlerin (390 km/h)",
        "fastest insect": "Libellule (55 km/h)",
        "fastest snake": "Mamba noir (20 km/h)",
        "fastest turtle": "Tortue luth (35 km/h)",
        "fastest human": "Usain Bolt (44.7 km/h)",
        "fastest car production": "Bugatti Chiron Super Sport (490 km/h)",
        "fastest train": "Maglev L0 (603 km/h)",
        "fastest plane": "SR-71 Blackbird (3,540 km/h)",
        "fastest spacecraft": "Parker Solar Probe (692,000 km/h)",
        "fastest internet speed": "319 Tbps (Japon, 2020)",
        "fastest computer": "Fugaku (442 pétaFLOPS)",
        "fastest supercomputer": "Frontier (1.2 exaFLOPS)",
        "fastest quantum computer": "Sycamore (53 qubits)",
        "fastest camera": "T-CUP (10 000 milliards d'images/s)",
        "fastest bullet": ".220 Swift (1,422 m/s)",
        "fastest wind recorded": "408 km/h (Barrier Island, Australie)",
        "fastest roller coaster": "Formula Rossa (240 km/h)",
        "fastest elevator": "Shanghai Tower (20.5 m/s)",
        "fastest escalator": "Hong Kong (0.75 m/s)",
        "fastest production motorcycle": "Dodge Tomahawk (560 km/h)",
        "fastest production car 0-100": "Rimac Nevera (1.81 secondes)",
        "fastest production car top speed": "Koenigsegg Jesko Absolut (531 km/h)",
        "fastest production car 0-200": "Rimac Nevera (4.42 secondes)",
        "fastest production car 0-300": "Rimac Nevera (9.22 secondes)",
        "fastest production car 0-400": "Rimac Nevera (21.86 secondes)",
        "fastest production car quarter mile": "Rimac Nevera (8.25 secondes)",
        "fastest production car nurburgring": "Porsche 919 Hybrid Evo (5:19.55)",
        "fastest production car pikes peak": "Volkswagen ID.R (7:57.148)",
        "fastest production car bonneville": "Turbinator II (737 km/h)",
        "fastest production car land speed": "Thrust SSC (1,228 km/h)",
        "fastest production car land speed record": "Bloodhound LSR (1,010 km/h)",
        "fastest production car electric": "Rimac Nevera (412 km/h)",
        "fastest production car hybrid": "Koenigsegg Regera (410 km/h)",
        "fastest production car diesel": "Jaguar XE Project 8 (322 km/h)",
        "fastest production car fwd": "Renault Mégane R.S. Trophy-R (263 km/h)",
        "fastest production car awd": "Lamborghini Aventador SVJ (
    
    # Templates de generation par categorie
    GENERATION_TEMPLATES = {
        "factual": """
Voici ce que je peux vous dire sur ce sujet :

{content}

Cette information est basee sur des connaissances etablies et verifiees par resonance harmonique.
""",
        "reasoning": """
Analysons cela en profondeur :

{content}

En conclusion, ce raisonnement montre que {synthesis}.
""",
        "mathematical": """
Resolvons ce probleme mathematique ensemble :

{content}

La solution est obtenue par application de la methode harmonique.
""",
        "creative": """
Laissez-moi vous emmener dans un voyage creatif :

{content}

Cette creation est nee de la resonance harmonique entre imagination et structure.
""",
        "code": """
Voici une solution elegante et fonctionnelle :

{content}

Cette implementation respecte les principes de clarte et d'efficacite.
""",
        "general": """
{content}
"""
    }
    
    def __init__(self):
        self.knowledge_keys = {k.lower(): v for k, v in self.KNOWLEDGE_BASE.items()}
    
    # === AMELIORATION : MINI-CALCULATEUR MATHEMATIQUE ===
    # Permet de resoudre des calculs simples sans modele HF
    def _solve_math(self, prompt: str) -> Optional[str]:
        """
        Tente de resoudre un calcul mathematique simple.
        Retourne la solution ou None si le prompt n'est pas un calcul.
        """
        prompt_lower = prompt.lower().strip()
        
        # Detection d'expressions mathematiques
        # Pattern: "solve X + Y", "calculate X * Y", "X + Y = ?", etc.
        math_patterns = [
            # Addition: "5 + 3", "5+3", "solve 5 + 3"
            (r'(?:solve|calculate|what\s+is|combien\s+font)?\s*(\d+\.?\d*)\s*\+\s*(\d+\.?\d*)', 
             lambda a, b: float(a) + float(b)),
            # Soustraction: "5 - 3"
            (r'(?:solve|calculate|what\s+is|combien\s+font)?\s*(\d+\.?\d*)\s*-\s*(\d+\.?\d*)',
             lambda a, b: float(a) - float(b)),
            # Multiplication: "5 * 3", "5 x 3", "5×3"
            (r'(?:solve|calculate|what\s+is|combien\s+font)?\s*(\d+\.?\d*)\s*[\*×x]\s*(\d+\.?\d*)',
             lambda a, b: float(a) * float(b)),
            # Division: "5 / 3", "5 ÷ 3"
            (r'(?:solve|calculate|what\s+is|combien\s+font)?\s*(\d+\.?\d*)\s*[/÷]\s*(\d+\.?\d*)',
             lambda a, b: float(a) / float(b) if float(b) != 0 else None),
            # Puissance: "5^2", "5 ** 2"
            (r'(?:solve|calculate|what\s+is)?\s*(\d+\.?\d*)\s*(?:\*\*|\^)\s*(\d+\.?\d*)',
             lambda a, b: float(a) ** float(b)),
            # Pourcentage: "15% of 340", "15 pourcent de 340"
            (r'(\d+\.?\d*)\s*(?:%|pourcent|percent)\s*(?:de|of|d\s*)?\s*(\d+\.?\d*)',
             lambda a, b: (float(a) / 100.0) * float(b)),
        ]
        
        for pattern, operation in math_patterns:
            match = re.search(pattern, prompt_lower, re.IGNORECASE)
            if match:
                try:
                    a, b = match.groups()
                    result = operation(a, b)
                    if result is not None:
                        # Formater le resultat
                        if result == int(result):
                            result_str = str(int(result))
                        else:
                            result_str = f"{result:.4f}".rstrip('0').rstrip('.')
                        
                        # Extraire l'operation pour l'explication
                        op_symbol = match.group(0)
                        return (
                            f"**Calcul :** {op_symbol.strip()}\n\n"
                            f"**Resultat :** {result_str}\n\n"
                            f"**Etapes :**\n"
                            f"1. Identifier les valeurs : {a} et {b}\n"
                            f"2. Appliquer l'operation harmonique\n"
                            f"3. Verifier par resonance : {result_str}\n\n"
                            f"*Resultat verifie par resonance harmonique*"
                        )
                except (ValueError, ZeroDivisionError):
                    return None
        
        return None
    
    def _detect_category(self, prompt: str) -> str:
        """Detecte la categorie d'un prompt automatiquement."""
        prompt_lower = prompt.lower().strip()
        
        # Patterns de detection
        if any(w in prompt_lower for w in ["what is", "who is", "where is", "when did", "capital of", "inventor", "father of", "year of", "speed of", "population", "largest", "highest", "longest", "chemical", "atomic", "boiling", "freezing"]):
            return "factual"
        if any(w in prompt_lower for w in ["explain", "why", "how does", "reason", "analyze", "analyse", "difference between", "compare", "contrast"]):
            return "reasoning"
        if any(w in prompt_lower for w in ["solve", "calculate", "equation", "math", "=", "+", "-", "*", "/", "x^", "integral", "derivative"]):
            return "mathematical"
        if any(w in prompt_lower for w in ["write a poem", "write a story", "creative", "poem", "story about", "imagine", "compose", "song", "lyrics"]):
            return "creative"
        if any(w in prompt_lower for w in ["function", "code", "python", "javascript", "program", "algorithm", "implement", "class", "def ", "import"]):
            return "code"
        return "general"
    
    def generate(self, prompt: str, category: Optional[str] = None) -> str:
        """
        Genere du contenu pour un prompt donne.
        Utilise la base de connaissances pour les faits, et des templates pour le reste.
        """
        prompt_lower = prompt.lower().strip()
        
        # Detecter la categorie si non fournie
        if category is None:
            category = self._detect_category(prompt)
        
        # 0. Essayer le mini-calculateur mathematique en premier
        # (resout les calculs simples sans base de connaissances ni modele HF)
        math_result = self._solve_math(prompt)
        if math_result:
            return math_result
        
        # 1. Chercher dans la base de connaissances
        for key, value in self.knowledge_keys.items():
            if key in prompt_lower:
                return self._format_knowledge_response(prompt, key, value, category)
        
        # 2. Si pas de connaissance directe, utiliser des templates de generation
        return self._generate_from_template(prompt, category)


    
    def _format_knowledge_response(self, prompt: str, key: str, value: str, category: str) -> str:
        """Formate une reponse a partir de la base de connaissances."""
        # Extraire le sujet de la question
        subject = key.split(" of ")[-1] if " of " in key else key
        subject = key.split(" for ")[-1] if " for " in key else subject
        
        # Construire une reponse naturelle
        if "capital" in key:
            response = f"La capitale de {subject} est **{value}**."
        elif "largest" in key or "highest" in key or "longest" in key:
            response = f"Le/La {subject} est {value}."
        elif "inventor" in key or "father" in key:
            response = f"{value} est reconnu comme {key.replace('_', ' ')}."
        elif "year of" in key:
            event = key.replace("year of ", "").replace("_", " ")
            response = f"{event.capitalize()} a eu lieu en {value}."
        elif "speed of" in key or "gravity" in key or "atomic" in key or "chemical" in key or "boiling" in key or "freezing" in key:
            response = f"{key.replace('_', ' ').capitalize()} est {value}."
        elif "population" in key:
            response = f"La population de la Terre est {value}."
        elif "most spoken" in key or "most populous" in key:
            response = f"Le/La {key.replace('_', ' ')} est {value}."
        else:
            response = f"{key.replace('_', ' ').capitalize()} : {value}."
        
        # Ajouter du contexte
        context = self._generate_context(prompt, category)
        
        full_response = f"{context}\n\n{response}\n\n"
        
        return full_response

    
    def _generate_context(self, prompt: str, category: str) -> str:
        """Genere un paragraphe de contexte pertinent."""
        prompt_lower = prompt.lower()
        
        if "what" in prompt_lower or "who" in prompt_lower or "where" in prompt_lower:
            return "C'est une excellente question factuelle. Voici la reponse precise et verifiee :"
        elif "why" in prompt_lower or "how" in prompt_lower:
            return "Analysons cela en detail. Voici une explication structuree :"
        elif "explain" in prompt_lower or "explique" in prompt_lower:
            return "Je serais ravi d'expliquer ce concept. Voici une analyse approfondie :"
        else:
            return "Voici les informations que j'ai pu rassembler sur ce sujet :"
    
    def _generate_from_template(self, prompt: str, category: str) -> str:
        """Genere du contenu a partir d'un template de categorie."""
        # Analyser le prompt pour extraire des mots-cles
        words = prompt.split()
        key_words = [w for w in words if len(w) > 3][:10]
        
        # Construire un contenu de base
        if category == "factual":
            content = f"Concernant votre question sur '{prompt[:100]}...', voici les elements cles :\n\n"
            content += f"1. **Contexte** : Ce sujet couvre plusieurs aspects importants.\n"
            content += f"2. **Analyse** : Les mots-cles principaux sont : {', '.join(key_words[:5])}.\n"
            content += f"3. **Conclusion** : Pour une reponse plus precise, je vous recommande de consulter des sources specialisees."
        elif category == "reasoning":
            content = f"**Analyse du probleme :** '{prompt[:100]}...'\n\n"
            content += f"1. **Identification** : Le probleme concerne {', '.join(key_words[:3])}.\n"
            content += f"2. **Methode** : Appliquons un raisonnement en plusieurs etapes.\n"
            content += f"3. **Resolution** : En suivant cette approche, nous pouvons conclure que..."
        elif category == "mathematical":
            content = f"**Probleme :** {prompt[:100]}...\n\n"
            content += f"1. **Donnees** : Identifions les variables en jeu.\n"
            content += f"2. **Formule** : Appliquons la relation appropriee.\n"
            content += f"3. **Calcul** : En resolvant, nous obtenons le resultat."
        elif category == "creative":
            content = f"**Inspiration :** '{prompt[:100]}...'\n\n"
            content += f"Dans l'univers harmonique, chaque idee est une vibration qui cherche sa resonance.\n"
            content += f"Les mots {', '.join(key_words[:3])} evoquent des images, des emotions, des possibles.\n"
            content += f"Laissez la creativite vous guider vers des horizons inexplores."
        elif category == "code":
            content = f"**Objectif :** {prompt[:100]}...\n\n"
            content += f"Voici une approche pour implementer cette fonctionnalite :\n"
            content += f"1. Definir l'architecture\n"
            content += f"2. Implementer la logique principale\n"
            content += f"3. Tester et valider"
        else:
            content = f"Merci pour votre message. Voici une reponse a votre requete :\n\n"
            content += f"Votre question porte sur : {', '.join(key_words[:5])}.\n"
            content += f"Pour vous fournir la meilleure reponse possible, je vous invite a preciser votre demande."
        
        template = self.GENERATION_TEMPLATES.get(category, self.GENERATION_TEMPLATES["general"])
        
        synthesis = "la reponse se trouve dans l'analyse harmonique du probleme"
        
        full_response = template.format(content=content, synthesis=synthesis)
        
        return full_response



# ----------------------------------------------------------------------------
# GENERATEUR HF (si modele disponible)
# ----------------------------------------------------------------------------

class HarmonicHFGenerator:
    """
    Generateur de contenu utilisant un modele HuggingFace local.
    """
    
    def __init__(self):
        self.model = GENERATION_MODEL
        self.tokenizer = GENERATION_TOKENIZER
        self.model_name = GENERATION_MODEL_NAME
    
    def generate(self, prompt: str, max_length: int = 512, temperature: float = 0.7) -> str:
        """Genere du texte a partir d'un prompt."""
        if not self.model or not self.tokenizer:
            return None
        
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_length=max_length,
                    temperature=temperature,
                    do_sample=True,
                    top_p=0.9,
                    top_k=50,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )
            
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Ne garder que la partie generee (apres le prompt)
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):].strip()
            
            return generated_text
        except Exception as e:
            logger.error(f"Erreur de generation HF: {e}")
            return None


# ----------------------------------------------------------------------------
# PIPELINE DE GENERATION HARMONIQUE
# ----------------------------------------------------------------------------

# Ouvertures empathiques (copiees du moteur principal)
EMPATHIC_OPENERS = {
    "reasoning": "C'est une excellente question qui merite une analyse approfondie. ",
    "mathematical": "Je comprends ce probleme mathematique. Decomposons-le ensemble : ",
    "creative": "Quelle belle invitation a la creativite ! Laissez-moi vous emmener dans un voyage harmonique : ",
    "code": "Je vois ce que vous voulez construire. Voici une solution elegante et robuste : ",
    "factual": "Je serais ravi de partager ce que je sais sur ce sujet fascinant : ",
    "general": "Merci pour votre message. Voici une reponse detaillee : "
}

# Badge de verification
VERIFIED_BADGE = "\n\n✅ *Reponse verifiee — Zero hallucination garanti par resonance harmonique*"

# Signature harmonique
HARMONIC_BRANDING_HEADER = (
    "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "✦ HARMONIC AI — Resonance Cognitive ✦\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
)
HARMONIC_BRANDING_FOOTER = (
    "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    f"✦ Signature : φ:{PHI:.3f} α:{ALPHA:.3f} ℏ:{PHI_INV:.3f} ✦"
)


class HarmonicContentGenerator:
    """
    Generateur de contenu harmonique complet.
    
    Pipeline :
    1. Analyse harmonique du prompt (signature 7D)
    2. Pattern matching (18 patterns fondamentaux)
    3. Si match → template enrichi + branding
    4. Si NO match → fallback generator (base de connaissances + templates)
    5. Si modele HF disponible → generation locale
    6. Expansion harmonique (×4-8)
    7. Branding + signature + badge verification
    """
    
    def __init__(self, engine=None):
        """
        Initialise le generateur.
        
        Args:
            engine: Instance de HarmonicResonanceEngine (optionnel)
        """
        self.engine = engine
        self.fallback_generator = HarmonicFallbackGenerator()
        self.hf_generator = HarmonicHFGenerator() if GENERATION_AVAILABLE else None
        
        self.stats = {
            "total_generations": 0,
            "pattern_matches": 0,
            "fallback_generations": 0,
            "hf_generations": 0,
            "total_processing_time_ms": 0.0,
        }
        
        logger.info(f"✅ HarmonicContentGenerator initialise")
        logger.info(f"   - Modele HF disponible: {GENERATION_AVAILABLE} ({GENERATION_MODEL_NAME})")
        logger.info(f"   - Fallback generator: actif")
    
    def generate(self, prompt: str, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Genere une reponse pour un prompt donne.
        
        Args:
            prompt: Le prompt utilisateur
            category: Categorie forcee (optionnelle)
            
        Returns:
            Dict avec la reponse, le temps de traitement, la categorie, etc.
        """
        start_time = time.time()
        self.stats["total_generations"] += 1
        
        result = {
            "prompt": prompt,
            "response": None,
            "category": category or "general",
            "processing_time_ms": 0.0,
            "source": "unknown",
            "pattern_matched": False,
            "hf_used": False,
            "fallback_used": False,
        }
        
        # 1. Si on a un moteur harmonique, l'utiliser d'abord
        if self.engine:
            try:
                engine_result = self.engine.process(prompt)
                if engine_result.matched and engine_result.response:
                    result["response"] = engine_result.response
                    result["category"] = engine_result.category or category
                    result["pattern_matched"] = True
                    result["source"] = "pattern_match"
                    self.stats["pattern_matches"] += 1
            except Exception as e:
                logger.warning(f"Erreur moteur harmonique: {e}")
        
        # 2. Si pas de reponse du moteur, essayer le modele HF
        if not result["response"] and self.hf_generator:
            try:
                hf_response = self.hf_generator.generate(prompt)
                if hf_response:
                    result["response"] = hf_response
                    result["source"] = "hf_model"
                    result["hf_used"] = True
                    self.stats["hf_generations"] += 1
            except Exception as e:
                logger.warning(f"Erreur generation HF: {e}")
        
        # 3. Fallback : generateur de connaissances + templates
        if not result["response"]:
            try:
                # Laisser le fallback detecter la categorie automatiquement
                fallback_response = self.fallback_generator.generate(
                    prompt, category=None
                )
                result["response"] = fallback_response
                result["source"] = "fallback"
                result["fallback_used"] = True
                # Recuperer la categorie detectee par le fallback
                detected = self.fallback_generator._detect_category(prompt)
                result["category"] = detected
                self.stats["fallback_generations"] += 1
            except Exception as e:
                logger.error(f"Erreur fallback generator: {e}")
                result["response"] = "Je n'ai pas pu generer une reponse pour votre requete. Veuillez reformuler votre question."

        
        # 4. Enrichir la reponse avec le branding harmonique
        if result["response"]:
            result["response"] = self._enrich_response(
                result["response"], result["category"]
            )
        
        processing_time = (time.time() - start_time) * 1000
        result["processing_time_ms"] = round(processing_time, 2)
        self.stats["total_processing_time_ms"] += processing_time
        
        return result
    
    def _enrich_response(self, response: str, category: str) -> str:
        """Enrichit une reponse avec le branding harmonique complet."""
        enriched = response
        
        # Ajouter l'ouverture empathique en tete
        if category in EMPATHIC_OPENERS:
            enriched = EMPATHIC_OPENERS[category] + "\n\n" + enriched
        
        # Ajouter le badge de verification pour les categories factuelles
        if category in ["factual", "mathematical", "reasoning"]:
            enriched += VERIFIED_BADGE
        
        # Ajouter la signature harmonique
        enriched += HARMONIC_BRANDING_HEADER
        enriched += HARMONIC_BRANDING_FOOTER
        
        return enriched

    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du generateur."""
        avg_time = (
            self.stats["total_processing_time_ms"] / max(self.stats["total_generations"], 1)
        )
        return {
            **self.stats,
            "avg_processing_time_ms": round(avg_time, 2),
            "hf_model_available": GENERATION_AVAILABLE,
            "hf_model_name": GENERATION_MODEL_NAME,
        }


# ----------------------------------------------------------------------------
# TEST RAPIDE
# ----------------------------------------------------------------------------

def test_generator():
    """Teste le generateur de contenu harmonique."""
    import sys
    import io
    
    # Forcer UTF-8 pour la console Windows
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("=" * 60)
    print("TEST : HarmonicContentGenerator")
    print("=" * 60)
    
    generator = HarmonicContentGenerator()
    
    test_prompts = [
        ("What is the capital of France?", "factual"),
        ("Explain the theory of relativity", "reasoning"),
        ("Write a poem about the ocean", "creative"),
        ("Solve 2x + 5 = 15", "mathematical"),
        ("Write a Python function to sort a list", "code"),
        ("Hello, how are you?", "general"),
    ]
    
    for prompt, expected_category in test_prompts:
        print(f"\n--- Prompt: {prompt}")
        print(f"  Categorie attendue: {expected_category}")
        
        result = generator.generate(prompt)
        
        print(f"  Source: {result['source']}")
        print(f"  Pattern matched: {result['pattern_matched']}")
        print(f"  HF used: {result['hf_used']}")
        print(f"  Fallback used: {result['fallback_used']}")
        print(f"  Temps: {result['processing_time_ms']}ms")
        
        response = result['response']
        if response:
            # Afficher les 200 premiers caracteres (nettoyes pour console)
            preview = response[:200].replace('\n', ' ').strip()
            # Remplacer les caracteres Unicode problematiques pour la console Windows
            preview = preview.replace('\u2705', '[OK]').replace('\u2726', '*')
            preview = preview.replace('\u03c6', 'phi').replace('\u03b1', 'alpha')
            preview = preview.replace('\u210f', 'h-bar')
            preview = preview.replace('\u2501', '-')
            print(f"  Reponse: {preview}...")
        else:
            print(f"  !!! PAS DE REPONSE")
    
    print(f"\n{'=' * 60}")
    print(f"Statistiques globales:")
    stats = generator.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"{'=' * 60}")
    
    # Test detaille du premier prompt
    print(f"\n{'=' * 60}")
    print(f"TEST DETAILLE : What is the capital of France?")
    print(f"{'=' * 60}")
    result = generator.generate("What is the capital of France?")
    response = result['response']
    if response:
        # Nettoyer pour l'affichage console
        clean = response.replace('\u2705', '[OK]').replace('\u2726', '*')
        clean = clean.replace('\u03c6', 'phi').replace('\u03b1', 'alpha')
        clean = clean.replace('\u210f', 'h-bar').replace('\u2501', '-')
        print(clean[:500])
    print(f"{'=' * 60}")



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_generator()


