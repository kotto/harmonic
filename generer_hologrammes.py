#!/usr/bin/env python3
"""
GÉNÉRATEUR D'HOLOGRAMMES PRÉ-ENTRAÎNÉS — Produits commerciaux
===============================================================
Crée des hologrammes 32 Ko pré-chargés de connaissances pour des domaines spécifiques.
Produits finis, prêts à être vendus/partagés.

Hologrammes disponibles :
  • Juridique France (droit civil, pénal, travail, contrats...)
  • Médical Général (diagnostics, traitements, guidelines)
  • Finance/Trading (analyses, stratégies, marchés)
  • Développement (algorithmes, code, architectures)
  • Éducation (sciences, histoire, littérature)

Format de sortie : .holo (32 Ko) + metadata.json

Usage :
  python generer_hologrammes.py --domaine juridique
  python generer_hologrammes.py --tous
  python generer_hologrammes.py --custom corpus.txt --nom "Expert"
  python generer_hologrammes.py --liste
"""

import os, sys, time, json, hashlib, argparse
from datetime import datetime
import numpy as np

_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)

from ka_reasoning_engine import KAReasoningEngine

HOLOGRAMMES_DIR = os.environ.get("KA_HOLOGRAMMES_DIR", os.path.join(_project_root, "hologrammes_produits"))

CONNAISSANCES = {
    "juridique": {
        "nom": "Juridique France",
        "description": "Droit civil, pénal, travail, sociétés, contrats, RGPD",
        "prix": 199,
        "textes": [
            "Le Code civil français promulgué en 1804 constitue le fondement du droit civil. L article 1101 definit le contrat comme une convention par laquelle une ou plusieurs personnes s obligent envers une ou plusieurs autres a donner a faire ou a ne pas faire quelque chose.",
            "La responsabilite civile regie par l article 1240 du Code civil impose a toute personne de reparer le dommage cause a autrui par sa faute sa negligence ou son imprudence.",
            "Le droit des contrats reforme par l ordonnance du 10 fevrier 2016 a introduit l imprevision la violence economique et la caducite comme nouvelles notions juridiques.",
            "Le Code penal francais classe les infractions en trois categories contraventions delits et crimes selon leur gravite. La presomption d innocence est un principe fondamental.",
            "Le Code du travail regit les relations entre employeurs et salaries. Le CDI est la forme normale du contrat de travail. La duree legale est de 35 heures par semaine.",
            "Les societes commerciales SARL SAS SA sont regies par le Code de commerce. La SAS est la forme la plus repandue pour les startups grace a sa liberte statutaire.",
            "Le Conseil d Etat est la plus haute juridiction administrative. Le recours pour exces de pouvoir permet de contester la legalite d un acte administratif.",
            "La propriete intellectuelle protege les creations de l esprit brevets marques droit d auteur. Un brevet protege une invention technique pour une duree maximale de 20 ans.",
            "Le RGPD applicable depuis le 25 mai 2018 encadre le traitement des donnees personnelles dans l Union europeenne avec droit d acces rectification effacement et portabilite.",
            "Le droit immobilier impose que la vente d un bien soit constatee par acte authentique devant notaire. Le compromis de vente peut etre assorti de conditions suspensives.",
            "La procedure civile est regie par le Code de procedure civile. Le principe du contradictoire impose que chaque partie puisse prendre connaissance des arguments de son adversaire.",
            "Le droit de la famille regit mariage divorce filiation adoption. Le divorce peut etre prononce par consentement mutuel pour faute ou pour alteration definitive du lien conjugal.",
            "Le Code monetaire et financier regit les activites bancaires. L AMF veille a la protection de l epargne et au bon fonctionnement des marches financiers.",
        ] * 30,
    },
    "medical": {
        "nom": "Medical General",
        "description": "Diagnostics, traitements, guidelines cliniques",
        "prix": 249,
        "textes": [
            "L hypertension arterielle est definie par une pression systolique superieure ou egale a 140 mmHg et diastolique superieure ou egale a 90 mmHg. Le traitement de premiere intention repose sur les mesures hygieno-dietetiques.",
            "L asthme est une maladie inflammatoire chronique des voies aeriennes. Le traitement de fond repose sur les corticosteroides inhales. La spirometrie mesure le volume expiratoire maximal.",
            "Le diabete de type 2 est caracterise par une resistance a l insuline. Le diagnostic repose sur une glycemie a jeun superieure a 1.26 g/L. L HbA1c permet le suivi avec un objectif inferieur a 7 pour cent.",
            "Les antibiotiques combattent les infections bacteriennes. La resistance aux antibiotiques est un probleme majeur de sante publique. L amoxicilline est l antibiotique le plus prescrit en France.",
            "La maladie de Parkinson est neurodegenerative avec destruction des neurones dopaminergiques. Les symptomes incluent tremblement de repos rigidite et akinesie. Le traitement repose sur la levodopa.",
            "Le cancer est caracterise par une proliferation anarchique de cellules anormales. Les traitements incluent chirurgie radiotherapie chimiotherapie immunotherapie et therapies ciblees.",
            "Le calendrier vaccinal francais recommande la vaccination contre 11 maladies pour les enfants nes depuis le 1er janvier 2018 incluant DTP coqueluche haemophilus pneumocoque et ROR.",
            "La depression majeure est caracterisee par une humeur triste pendant au moins deux semaines. Le traitement combine psychotherapie et antidepresseurs type ISRS.",
            "L infarctus du myocarde est une urgence vitale avec douleur thoracique constrictive irradiant dans le bras gauche. Le delai de reperfusion coronaire conditionne le pronostic vital.",
            "Les interactions medicamenteuses peuvent potentialiser ou diminuer l effet des medicaments. Le cytochrome P450 est implique dans le metabolisme de nombreux medicaments.",
        ] * 30,
    },
    "finance": {
        "nom": "Finance Trading",
        "description": "Analyses techniques, fondamentales, gestion de portefeuille",
        "prix": 299,
        "textes": [
            "L analyse technique etudie les graphiques de prix pour identifier des tendances et points d entree. Les moyennes mobiles lissent les fluctuations. Le RSI mesure la vitesse des mouvements de prix.",
            "L analyse fondamentale evalue la valeur intrinseque d un actif. Le PER Price Earnings Ratio compare le prix d une action a son benefice par action.",
            "La diversification de portefeuille reduit le risque en investissant dans differentes classes d actifs. La theorie moderne du portefeuille de Markowitz optimise le couple rendement risque.",
            "Le trading algorithmique execute des ordres selon des regles predefinies. Les market makers fournissent de la liquidite en affichant simultanement des prix d achat et de vente.",
            "Les produits derives options et futures permettent de couvrir des risques ou de speculer. Le modele Black Scholes estime la valeur theorique des options europeennes.",
            "La Value at Risk VaR quantifie la perte potentielle maximale sur un horizon donne. Le stress testing simule des scenarios extremes de marche.",
            "Le Private Equity investit dans des societes non cotees. Les fonds de capital risque financent les startups. Les LBO utilisent l endettement pour acquerir une entreprise.",
        ] * 40,
    },
    "dev": {
        "nom": "Developpement Code",
        "description": "Algorithmes, langages, architectures logicielles",
        "prix": 149,
        "textes": [
            "Python est un langage de programmation interprete multi paradigme avec une syntaxe claire et une vaste bibliotheque standard. Les list comprehensions offrent une syntaxe concise.",
            "Les algorithmes de tri sont fondamentaux en informatique. Le tri rapide quicksort a une complexite moyenne de O n log n. Le tri fusion mergesort est stable et garanti O n log n.",
            "Les structures de donnees organisent l information. Les tables de hachage offrent une recherche en O 1. Les arbres binaires de recherche maintiennent les donnees triees.",
            "Git est un systeme de controle de version decentralise. Les branches permettent de developper en parallele. GitHub est la plateforme d hebergement de code la plus utilisee.",
            "Docker conteneurise les applications pour garantir la reproductibilite. Kubernetes orchestre des conteneurs a grande echelle pour le deploiement et la mise a l echelle.",
            "Les API REST exposent des ressources via des endpoints HTTP. GET recupere POST cree PUT modifie DELETE supprime. L authentification se fait par token JWT.",
            "Les bases de donnees SQL utilisent des tables avec des schemas stricts. Les transactions ACID garantissent l integrite. Les index accelerent les requetes.",
        ] * 40,
    },
    "education": {
        "nom": "Education Savoirs",
        "description": "Sciences, histoire, litterature, culture generale",
        "prix": 99,
        "textes": [
            "La Seconde Guerre mondiale 1939 1945 a oppose les Allies aux forces de l Axe. Le debarquement de Normandie du 6 juin 1944 a marque un tournant decisif du conflit.",
            "La litterature francaise du XIXe siecle est marquee par le romantisme avec Victor Hugo le realisme avec Flaubert et Balzac et le naturalisme avec Emile Zola.",
            "La photosynthese est le processus par lequel les plantes convertissent l energie lumineuse en energie chimique. La chlorophylle capte la lumiere et permet la synthese de glucose.",
            "La tectonique des plaques explique la derive des continents et la formation des reliefs. Les frontieres convergentes creent des chaines de montagnes.",
            "La Renaissance est une periode de renouveau artistique et intellectuel en Europe aux XVe et XVIe siecles. Leonard de Vinci incarne l esprit de la Renaissance.",
            "La geometrie euclidienne repose sur cinq postulats enonces par Euclide. Le theoreme de Pythagore etablit que dans un triangle rectangle le carre de l hypothenuse est egal a la somme des carres des autres cotes.",
        ] * 45,
    },
}


class GenerateurHologrammes:
    """Genere des hologrammes pre entraines prets a etre commercialises."""
    
    def __init__(self, output_dir: str = HOLOGRAMMES_DIR):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generer(self, domaine: str, textes: list = None) -> dict:
        if textes is None and domaine in CONNAISSANCES:
            config = CONNAISSANCES[domaine]
            textes = config["textes"]
            nom = config["nom"]
        elif textes is not None:
            nom = domaine
        else:
            return {"erreur": f"Domaine inconnu: {domaine}"}
        
        print(f"\n{'='*60}")
        print(f"GENERATION: {nom}")
        print(f"{'='*60}")
        print(f"  Textes a ingerer: {len(textes)}")
        
        print(f"\n[1/3] Initialisation...")
        engine = KAReasoningEngine(mode="harmonic")
        
        print(f"[2/3] Ingestion one-pass CPU...")
        t0 = time.time()
        tokens_total = 0
        
        for i, texte in enumerate(textes):
            engine.bridge.apprendre(texte, amplitude=0.5)
            tokens_total += len(texte.split())
            if (i + 1) % 100 == 0:
                dt = time.time() - t0
                print(f"  {i+1}/{len(textes)} | {tokens_total:,} tokens | {dt:.1f}s | E={engine.bridge.monde.energie():.0f}")
        
        dt = time.time() - t0
        
        print(f"\n[3/3] Sauvegarde...")
        holo_id = hashlib.sha256(f"{domaine}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        holo_filename = f"KA_{domaine}_{holo_id}"
        holo_path = os.path.join(self.output_dir, holo_filename)
        np.save(holo_path, engine.bridge.monde.H)  # produit holo_path.npy
        holo_file_actual = holo_path + ".npy"
        holo_display = holo_filename + ".holo.npy"
        taille = os.path.getsize(holo_file_actual)
        
        # Renommer pour avoir .holo au lieu de .npy
        holo_final = os.path.join(self.output_dir, holo_filename + ".holo")
        if os.path.exists(holo_final):
            os.remove(holo_final)
        os.rename(holo_file_actual, holo_final)
        holo_file_actual = holo_final
        taille = os.path.getsize(holo_file_actual)
        
        metadata = {
            "id": holo_id,
            "nom": nom if domaine in CONNAISSANCES else domaine,
            "domaine": domaine,
            "description": CONNAISSANCES.get(domaine, {}).get("description", "Hologramme personnalise"),
            "prix_recommande": CONNAISSANCES.get(domaine, {}).get("prix", 99),
            "fichier": holo_filename,
            "taille": taille,
            "tokens_ingeres": tokens_total,
            "entrees": len(textes),
            "energie_hologramme": round(engine.bridge.monde.energie(), 1),
            "temps_generation": round(dt, 1),
            "date_creation": datetime.now().isoformat(),
            "version": "1.0.0",
            "licence": "Proprietaire - Harmonic AI",
        }
        
        meta_path = holo_path.replace('.holo', '.json')
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print(f"HOLOGRAMME GENERE")
        print(f"{'='*60}")
        print(f"  Fichier : {holo_filename}")
        print(f"  Taille  : {taille:,} octets")
        print(f"  Chemin  : {holo_path}")
        print(f"  Tokens  : {tokens_total:,}")
        print(f"  Temps   : {dt:.1f}s")
        print(f"  Energie : {metadata['energie_hologramme']:.0f}")
        print(f"  Prix    : {metadata['prix_recommande']}EUR")
        
        return metadata
    
    def generer_custom(self, fichier_texte: str, nom: str) -> dict:
        print(f"\n  Lecture de {fichier_texte}...")
        textes = []
        try:
            with open(fichier_texte, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.strip()
                    if line and len(line) > 20:
                        textes.append(line)
        except Exception as e:
            return {"erreur": str(e)}
        return self.generer(nom, textes)
    
    def generer_tous(self) -> list:
        resultats = []
        domaines = list(CONNAISSANCES.keys())
        
        print("=" * 70)
        print(f"GENERATION CATALOGUE COMPLET ({len(domaines)} hologrammes)")
        print(f"Demarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        for i, domaine in enumerate(domaines):
            print(f"\n{'─'*60}")
            print(f"[{i+1}/{len(domaines)}] {CONNAISSANCES[domaine]['nom']}")
            print(f"{'─'*60}")
            resultats.append(self.generer(domaine))
        
        print(f"\n{'='*70}")
        print(f"CATALOGUE GENERE")
        print(f"{'='*70}")
        total_tokens = sum(r.get('tokens_ingeres', 0) for r in resultats)
        total_temps = sum(r.get('temps_generation', 0) for r in resultats)
        
        for r in resultats:
            print(f"  OK {r.get('nom','?'):30s} {r.get('fichier','?'):40s} {r.get('prix_recommande',0)}EUR")
        
        print(f"\n  Total tokens : {total_tokens:,}")
        print(f"  Total temps  : {total_temps:.1f}s")
        print(f"  Stockage     : {len(resultats) * 32} Ko")
        print(f"  Catalogue    : {HOLOGRAMMES_DIR}")
        
        return resultats


def charger_hologramme(holo_path: str):
    if not os.path.exists(holo_path):
        raise FileNotFoundError(f"Hologramme introuvable: {holo_path}")
    return np.load(holo_path)


def utiliser_hologramme(holo_path: str, prompt: str, bridge=None) -> str:
    from bridge_harmonic_deepseek_gguf import BridgeHarmoniqueGGUF
    if bridge is None:
        bridge = BridgeHarmoniqueGGUF(mode="harmonic", n_lecteurs=8)
    bridge.monde.H = charger_hologramme(holo_path)
    resultat = bridge.generer(prompt=prompt, max_tokens=200, temperature=0.7)
    return resultat.get("texte_genere", "")


def main():
    parser = argparse.ArgumentParser(description="Generateur d hologrammes pre entraines")
    parser.add_argument("--domaine", type=str, default="", choices=["juridique","medical","finance","dev","education"])
    parser.add_argument("--tous", action="store_true")
    parser.add_argument("--custom", type=str, default="")
    parser.add_argument("--nom", type=str, default="Personnalise")
    parser.add_argument("--output", type=str, default=HOLOGRAMMES_DIR)
    parser.add_argument("--liste", action="store_true")
    
    args = parser.parse_args()
    gen = GenerateurHologrammes(output_dir=args.output)
    
    if args.liste:
        if os.path.exists(args.output):
            fichiers = [f for f in os.listdir(args.output) if f.endswith('.holo')]
            print(f"\n  {len(fichiers)} hologrammes dans {args.output}:")
            for f in sorted(fichiers):
                mp = os.path.join(args.output, f.replace('.holo','.json'))
                if os.path.exists(mp):
                    with open(mp) as mf:
                        meta = json.load(mf)
                    print(f"    {f} - {meta.get('nom','?')} - {meta.get('prix_recommande','?')}EUR")
                else:
                    print(f"    {f} - pas de metadonnees")
        return
    
    if args.tous:
        gen.generer_tous()
    elif args.custom:
        gen.generer_custom(args.custom, args.nom)
    elif args.domaine:
        gen.generer(args.domaine)
    else:
        parser.print_help()
        print("\n  Essayez: python generer_hologrammes.py --tous")
        print("  Ou:      python generer_hologrammes.py --domaine juridique")


if __name__ == "__main__":
    main()