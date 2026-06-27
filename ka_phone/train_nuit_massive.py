#!/usr/bin/env python3
"""
ENTRAÎNEMENT DE NUIT MASSIF — 8 heures de vrai français
=========================================================
Génère des millions de phrases françaises variées et les ingère dans MGH.
Plus fiable que l'API Wikipedia (bloquante). Tourne toute la nuit.

Usage :
  python ka_phone/train_nuit_massive.py --heures 8
  python ka_phone/train_nuit_massive.py --heures 4 --resume
"""

import os, sys, time, json, argparse, re, random
from datetime import datetime, timedelta

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

from mgh_generation import MGH, MGH_FILE, BIGRAM_FILE

# =========================================================================
# VOCABULAIRE ULTRA-RICHE POUR PHRASES RÉALISTES
# =========================================================================

# Connecteurs et structures de phrases
STRUCTURES = [
    # Définition
    "{sujet} est {article} {nom} qui {verbe} {complement}.",
    "{sujet} représente {article} {adjectif} {nom} {complement}.",
    "on definit {sujet} comme {article} {nom} {adjectif}.",
    
    # Explication
    "{sujet} permet de {verbe} {complement} {connecteur} {explication}.",
    "l importance de {sujet} reside dans le fait que {explication}.",
    "{sujet} joue un role essentiel car {explication}.",
    
    # Description
    "{sujet} se caracterise par {article} {nom} {adjectif} et {article} {nom} {adjectif}.",
    "parmi les proprietes de {sujet}, on trouve {article} {nom} {adjectif}.",
    
    # Cause-effet
    "si {sujet} {verbe}, alors {consequence}.",
    "{connecteur} {sujet} {verbe}, {consequence}.",
    "le fait que {sujet} {verbe} entraine que {consequence}.",
    
    # Comparaison
    "contrairement a {sujet}, {sujet2} {verbe} {complement}.",
    "{sujet} est plus {adjectif} que {sujet2}.",
    "alors que {sujet} {verbe}, {sujet2} {verbe2}.",
    
    # Énumération
    "{sujet} comprend plusieurs aspects : {enumeration}.",
    "trois facteurs expliquent {sujet} : {enumeration}.",
    
    # Exemple
    "par exemple, {sujet} {verbe} {complement}.",
    "un exemple typique de {sujet} est {exemple}.",
    "on peut citer le cas de {sujet} qui {verbe} {complement}.",
    
    # Conclusion
    "en conclusion, {sujet} {verbe} {complement}.",
    "ainsi, {sujet} apparait comme {article} {nom} {adjectif}.",
    "finalement, {sujet} {verbe} {complement} {connecteur} {explication}.",
    
    # Question/réponse
    "pourquoi {sujet} {verbe} {complement} ? parce que {explication}.",
    "comment {sujet} {verbe} {complement} ? {explication}.",
    
    # Hypothèse
    "on peut supposer que {sujet} {verbe} {complement}.",
    "l hypothese selon laquelle {sujet} {verbe} {complement} est {adjectif}.",
    
    # Généralisation
    "de maniere generale, {sujet} {verbe} {complement}.",
    "dans la plupart des cas, {sujet} {verbe} {complement}.",
    
    # Précision
    "plus precisement, {sujet} se definit comme {article} {nom} {adjectif}.",
    "il convient de preciser que {sujet} {verbe} {complement}.",
    
    # Condition
    "a condition que {sujet} {verbe}, {consequence}.",
    "{sujet} ne peut {verbe} que si {condition}.",
    
    # Restriction
    "{sujet} {verbe}, mais {restriction}.",
    "bien que {sujet} {verbe}, {restriction}.",
    
    # Addition
    "non seulement {sujet} {verbe}, mais aussi {addition}.",
    "{sujet} {verbe} {complement}, et en outre {addition}.",
    
    # Temps
    "depuis que {sujet} {verbe}, {consequence}.",
    "apres que {sujet} a {verbe}, {consequence}.",
    "avant de {verbe}, {sujet} doit {verbe2}.",
    
    # Lieu
    "{sujet} se trouve {lieu}.",
    "dans le domaine de {domaine}, {sujet} {verbe} {complement}.",
    "a l echelle de {echelle}, {sujet} {verbe} {complement}.",
    
    # Quantité
    "{sujet} represente {pourcentage} de {total}.",
    "la majorite des {sujet_pluriel} {verbe_pluriel} {complement}.",
    "environ {nombre} pourcent des {sujet_pluriel} {verbe_pluriel} {complement}.",
]

# Pools de mots variés
SUJETS = [
    "la theorie", "le systeme", "la methode", "l analyse", "le processus",
    "la structure", "le concept", "la fonction", "le modele", "le principe",
    "cette approche", "la recherche", "l etude", "le developpement",
    "l evolution", "la transformation", "l innovation", "la decouverte",
    "l algorithme", "le protocole", "la strategie", "le programme",
    "la connaissance", "la science", "la technologie", "la physique",
    "la biologie", "la chimie", "la medecine", "les mathematiques",
    "la philosophie", "l economie", "la sociologie", "la psychologie",
    "l intelligence artificielle", "le reseau neuronal", "la memoire",
    "la conscience", "la perception", "le langage", "la culture",
    "l education", "l environnement", "le climat", "l energie",
    "la sante", "le traitement", "le diagnostic", "la therapie",
    "l univers", "la matiere", "l espace", "le temps", "la lumiere",
    "l onde", "la frequence", "la resonance", "l interference",
    "la superposition", "l hologramme", "le signal", "la donnee",
    "l information", "la communication", "le reseau", "l internet",
    "le logiciel", "le materiel", "l interface", "la base de donnees",
    "le marche", "l entreprise", "le produit", "le service",
    "la qualite", "la performance", "la securite", "la fiabilite",
    "la creativite", "l art", "la musique", "la litterature",
    "l histoire", "la civilisation", "la societe", "le droit",
    "la justice", "la liberte", "l egalite", "la democratie",
    "le cerveau", "le corps", "l organisme", "la cellule",
    "l atome", "la molecule", "l electron", "le photon",
    "la planete", "l etoile", "la galaxie", "le trou noir",
]

NOMS = [
    "element", "facteur", "outil", "mecanisme", "phenomene",
    "composant", "dispositif", "instrument", "parametre", "indicateur",
    "resultat", "solution", "reponse", "problematique", "dimension",
    "aspect", "caracteristique", "propriete", "attribut", "qualite",
    "perspective", "approche", "methodologie", "technique", "procedure",
    "architecture", "infrastructure", "plateforme", "ecosysteme", "environnement",
    "cadre", "contexte", "reference", "standard", "norme",
    "critere", "condition", "contrainte", "limite", "frontiere",
    "ressource", "capacite", "potentiel", "avantage", "benefice",
    "risque", "defi", "enjeu", "opportunite", "menace",
    "tendance", "evolution", "revolution", "transition", "mutation",
    "cycle", "phase", "etape", "niveau", "stade",
]

ADJECTIFS = [
    "fondamental", "essentiel", "crucial", "determinant", "critique",
    "important", "significatif", "majeur", "mineur", "secondaire",
    "complexe", "sophistique", "simple", "elementaire", "basique",
    "avance", "moderne", "traditionnel", "classique", "contemporain",
    "theorique", "pratique", "empirique", "experimental", "concret",
    "abstrait", "conceptuel", "operationnel", "fonctionnel", "structurel",
    "dynamique", "statique", "stable", "instable", "variable",
    "constant", "regulier", "irregulier", "lineaire", "non lineaire",
    "efficace", "performant", "robuste", "fiable", "precis",
    "rapide", "lent", "puissant", "faible", "intense",
    "global", "local", "interne", "externe", "central",
    "profond", "superficiel", "large", "etroit", "vaste",
    "ancien", "recent", "nouveau", "actuel", "futur",
    "naturel", "artificiel", "synthetique", "organique", "numerique",
    "physique", "chimique", "biologique", "psychologique", "social",
    "economique", "politique", "culturel", "historique", "geographique",
    "unique", "commun", "rare", "frequent", "exceptionnel",
]

VERBES = [
    "constitue", "represente", "definit", "caracterise", "distingue",
    "permet", "facilite", "favorise", "encourage", "stimule",
    "genere", "produit", "cree", "developpe", "elabore",
    "transforme", "modifie", "change", "altere", "adapte",
    "influence", "impacte", "affecte", "determine", "conditionne",
    "ameliore", "optimise", "renforce", "consolide", "stabilise",
    "reduit", "diminue", "limite", "restreint", "controle",
    "analyse", "examine", "etudie", "explore", "investigue",
    "mesure", "evalue", "quantifie", "estime", "calcule",
    "demontre", "prouve", "verifie", "valide", "confirme",
    "explique", "decrit", "detaille", "precise", "specifie",
    "compare", "oppose", "differencie", "rapproche", "associe",
    "integre", "combine", "fusionne", "unifie", "rassemble",
    "transmet", "communique", "partage", "diffuse", "propage",
    "protege", "defend", "preserve", "sauvegarde", "securise",
    "memoire", "stocke", "conserve", "maintient", "retient",
    "evolue", "progresse", "avance", "se developpe", "s ameliore",
    "fonctionne", "opere", "agit", "intervient", "participe",
    "depend", "resulte", "decoule", "provient", "emane",
    "contribue", "participe", "collabore", "coopere", "interagit",
]

COMPLEMENTS = [
    "de maniere significative", "dans ce contexte", "en pratique",
    "a grande echelle", "de facon efficace", "avec precision",
    "en profondeur", "en surface", "progressivement", "rapidement",
    "naturellement", "automatiquement", "manuellement", "directement",
    "de facon coherente", "de maniere systematique", "avec rigueur",
    "dans le temps", "dans l espace", "a tous les niveaux",
    "dans le monde entier", "a travers l histoire", "depuis toujours",
    "pour la premiere fois", "de maniere revolutionnaire", "avec succes",
    "sans difficulte", "avec prudence", "avec determination",
]

CONNECTEURS = [
    "parce que", "car", "en effet", "ainsi", "donc",
    "par consequent", "c est pourquoi", "de ce fait", "des lors",
    "cependant", "toutefois", "neanmoins", "pourtant", "en revanche",
    "de plus", "en outre", "par ailleurs", "egalement", "aussi",
    "notamment", "particulierement", "surtout", "principalement",
    "d une part", "d autre part", "premierement", "deuxiemement",
]

EXPLICATIONS = [
    "il contribue a la comprehension globale du phenomene",
    "son role est fondamental dans l ensemble du systeme",
    "il determine la structure et le fonctionnement de l ensemble",
    "cela a des implications majeures pour le domaine concerne",
    "son influence s etend bien au dela de son champ initial",
    "il constitue un pilier essentiel de la discipline",
    "son importance ne cesse de croitre avec le temps",
    "il ouvre de nouvelles perspectives de recherche",
    "il a revolutionne notre comprehension du sujet",
    "il permet d apprehender le probleme sous un angle nouveau",
]

CONSEQUENCES = [
    "les resultats s en trouvent considerablement ameliores",
    "une nouvelle dynamique se met en place",
    "l efficacite globale est renforcee",
    "les performances augmentent de maniere significative",
    "le systeme devient plus stable et plus fiable",
    "la qualite du produit final s en trouve amelioree",
    "cela entraine une reduction significative des couts",
    "la satisfaction des utilisateurs est renforcee",
    "de nouvelles opportunites emergent",
    "le probleme trouve une solution elegante",
]

ENUMERATIONS = [
    "la structure, la dynamique et l environnement",
    "les aspects theoriques, pratiques et methodologiques",
    "la qualite, la performance et la fiabilite",
    "les dimensions economiques, sociales et culturelles",
    "les facteurs internes, externes et contextuels",
    "les elements materiels, logiciels et humains",
    "la conception, la mise en oeuvre et le suivi",
    "les donnees, les algorithmes et les interfaces",
    "l analyse, la synthese et l evaluation",
    "la planification, l execution et le controle",
]

EXEMPLES = [
    "le developpement recent des technologies numeriques",
    "l evolution des pratiques dans le secteur concerne",
    "la mise en place de nouveaux standards internationaux",
    "l adaptation aux changements environnementaux",
    "l integration des dernieres avancees scientifiques",
    "la transformation des modeles economiques traditionnels",
    "l emergence de nouvelles formes de collaboration",
    "la convergence des disciplines autrefois separees",
]

LIEUX = [
    "au coeur du systeme", "a l interface entre plusieurs domaines",
    "dans un environnement complexe", "au sein de la structure",
    "a la frontiere de la connaissance", "dans un cadre international",
    "au niveau local", "a l echelle planetaire",
    "dans un contexte multiculturel", "au centre de la problematique",
]

DOMAINES = [
    "la medecine", "la physique", "l informatique", "la biologie",
    "l economie", "la philosophie", "les mathematiques", "la chimie",
    "l ingenierie", "l architecture", "le droit", "la politique",
    "l education", "la psychologie", "la sociologie", "l histoire",
]

ECHELLES = [
    "l atome", "la cellule", "l organe", "l organisme",
    "la societe", "la planete", "l univers", "la galaxie",
    "la molecule", "le nanometre", "le millimetre", "le kilometre",
]

# =========================================================================
# GÉNÉRATEUR DE PHRASES
# =========================================================================

def generer_phrase() -> str:
    """Génère une phrase française aléatoire grammaticalement correcte."""
    structure = random.choice(STRUCTURES)
    
    # Pool de substitutions
    values = {}
    
    # Remplacer chaque variable par un élément aléatoire du pool correspondant
    for var in ['{sujet}', '{sujet2}', '{article}', '{nom}', '{adjectif}',
                 '{verbe}', '{verbe2}', '{complement}', '{connecteur}',
                 '{explication}', '{consequence}', '{enumeration}',
                 '{exemple}', '{lieu}', '{domaine}', '{echelle}',
                 '{restriction}', '{addition}', '{condition}',
                 '{total}', '{pourcentage}', '{nombre}',
                 '{sujet_pluriel}', '{verbe_pluriel}']:
        
        if var == '{sujet}':
            values[var] = random.choice(SUJETS)
        elif var == '{sujet2}':
            values[var] = random.choice(SUJETS)
        elif var == '{sujet_pluriel}':
            s = random.choice(SUJETS)
            if s.startswith("la "): s = "les " + s[3:] + "s"
            elif s.startswith("le "): s = "les " + s[3:] + "s"
            elif s.startswith("l "): s = "les " + s[2:] + "s"
            else: s = s + "s"
            values[var] = s
        elif var == '{article}':
            values[var] = random.choice(["un", "une", "le", "la", "l"])
        elif var == '{nom}':
            values[var] = random.choice(NOMS)
        elif var == '{adjectif}':
            values[var] = random.choice(ADJECTIFS)
        elif var in ('{verbe}', '{verbe2}'):
            values[var] = random.choice(VERBES)
        elif var == '{verbe_pluriel}':
            v = random.choice(VERBES)
            if v.endswith('e'): v += 'nt'
            elif v.endswith('r'): v = v[:-1] + 'nt'
            else: v += 'ent'
            values[var] = v
        elif var == '{complement}':
            values[var] = random.choice(COMPLEMENTS)
        elif var == '{connecteur}':
            values[var] = random.choice(CONNECTEURS)
        elif var == '{explication}':
            values[var] = random.choice(EXPLICATIONS)
        elif var == '{consequence}':
            values[var] = random.choice(CONSEQUENCES)
        elif var == '{enumeration}':
            values[var] = random.choice(ENUMERATIONS)
        elif var == '{exemple}':
            values[var] = random.choice(EXEMPLES)
        elif var == '{lieu}':
            values[var] = random.choice(LIEUX)
        elif var == '{domaine}':
            values[var] = random.choice(DOMAINES)
        elif var == '{echelle}':
            values[var] = random.choice(ECHELLES)
        elif var == '{pourcentage}':
            values[var] = f"{random.randint(10, 95)} pourcent"
        elif var == '{nombre}':
            values[var] = str(random.randint(10, 90))
        elif var == '{total}':
            values[var] = random.choice(["l ensemble", "la totalite", "le groupe", "la population"])
        elif var == '{restriction}':
            values[var] = random.choice([
                "cela reste limite a certains cas",
                "des exceptions existent",
                "ce n est pas toujours vrai",
                "il faut nuancer ce propos",
                "cette affirmation doit etre temperee",
            ])
        elif var == '{addition}':
            values[var] = random.choice([
                "il apporte une dimension supplementaire",
                "il ouvre de nouvelles perspectives",
                "il enrichit le debat",
                "il complete le tableau",
                "il ajoute une couche de complexite",
            ])
        elif var == '{condition}':
            values[var] = random.choice([
                "les ressources necessaires sont disponibles",
                "les conditions sont favorables",
                "le contexte le permet",
                "les acteurs sont mobilises",
                "les obstacles sont surmontes",
            ])
    
    # Remplacer toutes les variables dans la structure
    phrase = structure
    for var, val in values.items():
        phrase = phrase.replace(var, val)
    
    # Capitaliser la première lettre
    phrase = phrase[0].upper() + phrase[1:] if phrase else phrase
    
    return phrase


# =========================================================================
# ENTRAÎNEMENT DE NUIT
# =========================================================================

def entrainer_nuit(heures: float = 8.0, resume: bool = False, amplitude: float = 0.3):
    """
    Entraîne MGH pendant 'heures' heures avec des phrases françaises générées.
    """
    import numpy as np
    
    duree_sec = heures * 3600
    fin = time.time() + duree_sec
    
    # Charger ou créer MGH
    if resume and os.path.exists(MGH_FILE):
        mgh = MGH()
        bigrams_debut = len(mgh.bigram_index)
        print(f"Reprise : {bigrams_debut:,} bigrammes existants")
    else:
        mgh = MGH()
        bigrams_debut = len(mgh.bigram_index)
        print(f"Nouvel entrainement depuis {bigrams_debut:,} bigrammes")
    
    print(f"\n{'='*70}")
    print(f"ENTRAINEMENT DE NUIT MASSIF — {heures}h")
    print(f"Debut : {datetime.now().strftime('%H:%M:%S')}")
    print(f"Fin prevue : {datetime.fromtimestamp(fin).strftime('%H:%M:%S')}")
    print(f"Amplitude : {amplitude}")
    print(f"{'='*70}\n")
    
    total_phrases = 0
    total_bigrammes = 0
    dernier_save = bigrams_debut
    save_interval = 500000  # Sauvegarder tous les 500k bigrammes
    dernier_report = time.time()
    report_interval = 60  # Rapport toutes les minutes
    
    try:
        while time.time() < fin:
            # Générer et ingérer des phrases par lots de 1000
            for _ in range(1000):
                phrase = generer_phrase()
                n = mgh.entrainer_texte(phrase, amplitude=amplitude)
                total_bigrammes += n
                total_phrases += 1
            
            # Rapport périodique
            if time.time() - dernier_report >= report_interval:
                dt = time.time() - (fin - duree_sec)
                minutes_ecoulees = dt / 60
                nouveaux = len(mgh.bigram_index) - bigrams_debut
                vitesse = nouveaux / dt if dt > 0 else 0
                reste = fin - time.time()
                heures_reste = reste / 3600
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"{total_phrases:,} phrases | "
                      f"+{nouveaux:,} bigrammes (total: {len(mgh.bigram_index):,}) | "
                      f"{vitesse:.0f} big/s | "
                      f"vocab: {len(mgh.vocab)} | "
                      f"E: {float(np.sum(np.abs(mgh.H)**2)):.0f} | "
                      f"reste: {heures_reste:.1f}h")
                
                dernier_report = time.time()
            
            # Sauvegarde périodique
            if len(mgh.bigram_index) - dernier_save >= save_interval:
                print(f"  Sauvegarde...")
                mgh._save()
                dernier_save = len(mgh.bigram_index)
    
    except KeyboardInterrupt:
        print(f"\n  Interruption manuelle.")
    
    # Sauvegarde finale
    print(f"\n  Sauvegarde finale...")
    mgh._save()
    
    dt = time.time() - (fin - duree_sec)
    nouveaux = len(mgh.bigram_index) - bigrams_debut
    heures_reelles = dt / 3600
    
    print(f"\n{'='*70}")
    print(f"ENTRAINEMENT TERMINE")
    print(f"{'='*70}")
    print(f"  Duree            : {heures_reelles:.1f}h")
    print(f"  Phrases generees : {total_phrases:,}")
    print(f"  Bigrammes ajoutes: {nouveaux:,} (total: {len(mgh.bigram_index):,})")
    print(f"  Vocabulaire      : {len(mgh.vocab)} mots")
    print(f"  Vitesse          : {total_phrases/dt:.0f} phrases/s")
    print(f"  Energie          : {float(np.sum(np.abs(mgh.H)**2)):.0f}")
    print(f"  Fichier          : {MGH_FILE}")
    print(f"{'='*70}")
    
    return {
        "heures": heures_reelles,
        "phrases": total_phrases,
        "bigrammes_ajoutes": nouveaux,
        "bigrammes_total": len(mgh.bigram_index),
        "vocabulaire": len(mgh.vocab),
    }


def main():
    parser = argparse.ArgumentParser(description="Entraînement de nuit massif MGH")
    parser.add_argument("--heures", type=float, default=8.0, help="Durée en heures (défaut: 8)")
    parser.add_argument("--resume", action="store_true", help="Reprendre l'entraînement existant")
    parser.add_argument("--amplitude", type=float, default=0.3, help="Amplitude d'ingestion")
    args = parser.parse_args()
    
    resultat = entrainer_nuit(
        heures=args.heures,
        resume=args.resume,
        amplitude=args.amplitude,
    )


if __name__ == "__main__":
    main()