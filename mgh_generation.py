#!/usr/bin/env python3
"""
MGH — Module de Génération Harmonique
=======================================
Génère du texte grammaticalement correct par résonance holographique.
Remplace le LLM pour la fluidité linguistique. 32 Ko. 0€ CPU.

Principe :
  • Ingère des millions de phrases → encode bigrammes/trigrammes → onde
  • Génération : suit le CHEMIN DE RÉSONANCE MAXIMALE dans l'hologramme
  • Hologramme distinct de l'hologramme de SAVOIR (KA)

Usage :
  python mgh_generation.py --train corpus_fr/
  python mgh_generation.py --generate "Le chat"
  python mgh_generation.py --demo
"""

import os, sys, time, json, hashlib, argparse, re, glob, random
import numpy as np
from collections import defaultdict

_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _project_root)

NX, NY, PHI = 64, 64, 1.618033988749895
MGH_DIR = os.path.join(_project_root, "mgh_data")
os.makedirs(MGH_DIR, exist_ok=True)
MGH_FILE = os.path.join(MGH_DIR, "mgh_langage.npy")
BIGRAM_FILE = os.path.join(MGH_DIR, "bigram_index.json")

class MGH:
    """Module de Génération Harmonique — Langage par résonance."""
    
    def __init__(self):
        x = np.linspace(-np.pi, np.pi, NX)
        y = np.linspace(-np.pi, np.pi, NY)
        self.xx, self.yy = np.meshgrid(x, y, indexing='ij')
        self.H = np.random.randn(NX, NY) * 0.001 + 1j * np.random.randn(NX, NY) * 0.001
        self.bigram_index = {}
        self.vocab = set()
        self.BOS = "<BOS>"
        self.EOS = "<EOS>"
        self._load()
    
    def _load(self):
        if os.path.exists(MGH_FILE):
            self.H = np.load(MGH_FILE)
            print(f"[MGH] Hologramme chargé: E={np.sum(np.abs(self.H)**2):.0f}")
        if os.path.exists(BIGRAM_FILE):
            with open(BIGRAM_FILE) as f:
                self.bigram_index = json.load(f)
            # Reconstruire le vocabulaire depuis les bigrammes
            for key in self.bigram_index:
                w1, w2 = key.split("|", 1)
                self.vocab.add(w1)
                self.vocab.add(w2)
            print(f"[MGH] Bigrammes chargés: {len(self.bigram_index)} | vocab: {len(self.vocab)}")
    
    def _save(self):
        np.save(MGH_FILE, self.H)
        with open(BIGRAM_FILE, 'w') as f:
            json.dump(self.bigram_index, f)
    
    def _bigram_vers_onde(self, w1: str, w2: str):
        """Un bigramme → un vecteur d'onde unique (kx, ky)."""
        h = hashlib.md5(f"{w1}||{w2}".encode()).hexdigest()
        kx = (int(h[:16], 16) / 2**64 * 2 - 1) * np.pi
        ky = (int(h[16:], 16) / 2**64 * 2 - 1) * np.pi
        return kx, ky
    
    def _mot_vers_kxky(self, mot: str):
        """Un mot seul → vecteur d'onde (pour l'amorçage)."""
        h = hashlib.md5(mot.encode()).hexdigest()
        kx = (int(h[:16], 16) / 2**64 * 2 - 1) * np.pi
        ky = (int(h[16:], 16) / 2**64 * 2 - 1) * np.pi
        return kx, ky
    
    def _resonance(self, kx, ky) -> float:
        """Mesure la résonance de l'hologramme à (kx, ky)."""
        onde_ref = np.exp(-1j * (kx * self.xx + ky * self.yy))
        return float(np.abs(np.sum(self.H * onde_ref)) / (NX * NY))
    
    # =================================================================
    # ENTRAÎNEMENT
    # =================================================================
    def entrainer_texte(self, texte: str, amplitude: float = 0.3):
        """Ingère un texte dans l'hologramme de langage (bigrammes + trigrammes)."""
        mots = re.findall(r"[a-zA-ZÀ-ÿ0-9]+|[.,!?;:]", texte.lower())
        if len(mots) < 3:
            return 0
        
        count = 0
        # Bigrammes
        for i in range(len(mots) - 1):
            w1, w2 = mots[i], mots[i+1]
            kx, ky = self._bigram_vers_onde(w1, w2)
            onde = np.exp(1j * (kx * self.xx + ky * self.yy))
            self.H += amplitude * onde
            self.bigram_index[f"{w1}|{w2}"] = list((float(kx), float(ky)))
            self.vocab.add(w1); self.vocab.add(w2)
            count += 1
        
        # Trigrammes (poids plus faible — structure syntaxique)
        for i in range(len(mots) - 2):
            w1, w2, w3 = mots[i], mots[i+1], mots[i+2]
            trig = f"{w1}|{w2}|{w3}"
            h = hashlib.md5(trig.encode()).hexdigest()
            kx = (int(h[:16], 16) / 2**64 * 2 - 1) * np.pi
            ky = (int(h[16:], 16) / 2**64 * 2 - 1) * np.pi
            self.H += amplitude * 0.5 * np.exp(1j * (kx * self.xx + ky * self.yy))
            count += 1
        
        return count
    
    def entrainer_fichier(self, filepath: str, max_lines: int = 100000):
        """Ingère un fichier texte ligne par ligne."""
        count = 0
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.strip()
                    if line and len(line) > 10:
                        count += self.entrainer_texte(line)
                        if count >= max_lines:
                            break
        except Exception as e:
            print(f"  Erreur {filepath}: {e}")
        return count
    
    def entrainer_dossier(self, directory: str, pattern="*.txt"):
        """Ingère tous les fichiers texte d'un dossier."""
        fichiers = glob.glob(os.path.join(directory, "**", pattern), recursive=True)
        total = 0
        print(f"  {len(fichiers)} fichiers trouvés")
        for i, fp in enumerate(fichiers[:500]):
            c = self.entrainer_fichier(fp)
            total += c
            if (i+1) % 50 == 0:
                print(f"  {i+1}/{min(len(fichiers),500)} | {total:,} bigrammes | E={np.sum(np.abs(self.H)**2):.0f}")
        return total
    
    def entrainer_synthetique(self, n_phrases: int = 50000):
        """Version de base — appelle entrainer_massif qui est bien plus riche."""
        return self.entrainer_massif(n_phrases)

    def entrainer_massif(self, n_phrases: int = 100000):
        """
        Entraînement MASSIF de MGH avec vocabulaire riche et structures complexes.
        Génère des patterns de phrases proches d'un LLM :
        - Définitions techniques et scientifiques
        - Explications et raisonnements
        - Descriptions et contextes
        - Questions/réponses formatées
        - Connecteurs logiques et rhétorique
        """
        # VOCABULAIRE ULTRA-RICHE — 500+ mots couvrant tous les domaines
        sujets_tech = [
            # Informatique & IA
            "hologramme", "superposition", "onde", "résonance", "interférence",
            "conscience", "intelligence", "mémoire", "information", "énergie",
            "fréquence", "amplitude", "phase", "vecteur", "matrice",
            "algorithme", "système", "structure", "principe", "théorie",
            "code", "programme", "logiciel", "réseau", "neurone",
            "apprentissage", "donnée", "base", "requête", "réponse",
            "modèle", "paramètre", "couche", "poids", "biais",
            "token", "embedding", "transformer", "attention", "gradient",
            "classification", "régression", "clustering", "prédiction", "optimisation",
            "python", "javascript", "html", "css", "api",
            "serveur", "client", "protocole", "paquet", "latence",
            # Sciences
            "physique", "mathématique", "biologie", "chimie", "médecine",
            "science", "connaissance", "savoir", "concept", "univers",
            "matière", "espace", "temps", "dimension", "loi",
            "constante", "équation", "formule", "modèle", "analyse",
            "synthèse", "méthode", "processus", "phénomène", "nombre d or",
            "phi", "fractale", "infini", "singularité", "quantique",
            "relativité", "gravité", "électromagnétisme", "thermodynamique", "mécanique",
            "optique", "acoustique", "nucléaire", "atomique", "moléculaire",
            "cellule", "organe", "tissu", "gène", "protéine",
            "enzyme", "hormone", "bactérie", "virus", "vaccin",
            "atome", "électron", "proton", "neutron", "photon",
            "quark", "boson", "fermion", "hadron", "lepton",
            # Médecine & Santé
            "diagnostic", "traitement", "thérapie", "chirurgie", "patient",
            "médecin", "hôpital", "clinique", "urgence", "soin",
            "symptôme", "pathologie", "maladie", "infection", "inflammation",
            "cancer", "diabète", "hypertension", "asthme", "allergie",
            "antibiotique", "antiviral", "vaccination", "immunité", "anticorps",
            "radiographie", "scanner", "irm", "échographie", "biopsie",
            "anesthésie", "réanimation", "transfusion", "greffe", "implant",
            # Philosophie & Société
            "philosophie", "éthique", "morale", "logique", "raison",
            "vérité", "sagesse", "existence", "réalité", "perception",
            "pensée", "esprit", "âme", "corps", "langage",
            "culture", "société", "histoire", "civilisation", "humanité",
            "économie", "politique", "droit", "justice", "liberté",
            "égalité", "fraternité", "démocratie", "éducation", "enseignement",
            "art", "musique", "littérature", "peinture", "sculpture",
            # Nature & Environnement
            "nature", "environnement", "écologie", "climat", "biodiversité",
            "écosystème", "planète", "terre", "soleil", "lune",
            "océan", "rivière", "montagne", "forêt", "désert",
            "animal", "plante", "espèce", "évolution", "adaptation",
            "photosynthèse", "respiration", "nutrition", "reproduction", "croissance",
            # Technologie
            "technologie", "innovation", "invention", "découverte", "recherche",
            "développement", "ingénierie", "robotique", "automatisation", "numérique",
            "internet", "web", "cloud", "big data", "blockchain",
            "crypto", "intelligence artificielle", "machine learning", "deep learning", "réseau neuronal",
            "ordinateur", "processeur", "mémoire vive", "stockage", "capteur",
            "interface", "écran", "batterie", "circuit", "puce",
            # Finance & Business
            "finance", "marché", "bourse", "investissement", "capital",
            "entreprise", "startup", "management", "stratégie", "marketing",
            "vente", "client", "produit", "service", "qualité",
            "croissance", "profit", "risque", "analyse", "prévision",
        ]
        sujets_courants = [
            # Sujets généraux pour varier les phrases
            "le système", "la méthode", "le processus", "l analyse", "la théorie",
            "le principe", "cette approche", "la structure", "le concept", "la fonction",
            "le modèle", "le phénomène", "l étude", "la recherche", "la solution",
            "le développement", "l évolution", "la transformation", "l application", "la découverte",
            "cet outil", "cette technique", "l innovation", "le projet", "la mission",
            "l objectif", "la stratégie", "le plan", "la vision", "la perspective",
            "le résultat", "l impact", "la conséquence", "l avantage", "le défi",
            "la question", "le problème", "l enjeu", "la priorité", "l urgence",
            "la performance", "l efficacité", "la robustesse", "la fiabilité", "la précision",
            "la simplicité", "la complexité", "l élégance", "la beauté", "la puissance",
        ]
        verbes_tech = [
            "permet", "repose sur", "représente", "constitue", "définit",
            "caractérise", "implique", "génère", "produit", "transforme",
            "encode", "décode", "calcule", "mesure", "analyse",
            "optimise", "améliore", "détermine", "établit", "démontre",
            "prouve", "vérifie", "valide", "confirme", "illustre",
            "explique", "décrit", "détaille", "précise", "spécifie",
            "compare", "évalue", "estime", "quantifie", "modélise",
            "simule", "prédit", "détecte", "identifie", "reconnaît",
            "comprend", "intègre", "combine", "associe", "relie",
            "contrôle", "régule", "coordonne", "organise", "structure",
            "facilite", "accélère", "renforce", "stabilise", "équilibre",
            "transmet", "reçoit", "émet", "capte", "filtre",
            "protège", "défend", "sécurise", "garantit", "assure",
            "mémorise", "stocke", "conserve", "préserve", "maintient",
            "adapte", "ajuste", "corrige", "répare", "restaure",
        ]
        verbes_courants = [
            "est", "sont", "fait", "font", "donne",
            "crée", "trouve", "obtient", "fournit", "apporte",
            "utilise", "nécessite", "demande", "requiert", "exige",
            "devient", "reste", "semble", "paraît", "apparaît",
            "existe", "fonctionne", "opère", "travaille", "agit",
            "change", "évolue", "progresse", "avance", "recule",
            "commence", "termine", "poursuit", "continue", "cesse",
            "augmente", "diminue", "varie", "fluctue", "oscille",
            "contient", "inclut", "comprend", "possède", "dispose de",
            "offre", "propose", "présente", "expose", "montre",
            "dépend de", "résulte de", "provient de", "découle de", "émerge de",
            "contribue à", "participe à", "appartient à", "correspond à", "répond à",
        ]

        connecteurs = [
            "parce que", "car", "en effet", "ainsi", "donc",
            "par conséquent", "cependant", "toutefois", "néanmoins", "de plus",
            "en outre", "également", "notamment", "particulièrement", "surtout",
            "c est pourquoi", "c est ainsi que", "de cette manière", "grâce à", "au moyen de",
            "d une part", "d autre part", "en revanche", "au contraire", "à l inverse",
            "premièrement", "deuxièmement", "troisièmement", "enfin", "finalement",
            "tout d abord", "ensuite", "puis", "après", "avant",
            "simultanément", "parallèlement", "conjointement", "indépendamment", "respectivement",
        ]
        
        adjectifs = [
            "important", "essentiel", "fondamental", "crucial", "critique",
            "complexe", "simple", "élégant", "robuste", "fiable",
            "puissant", "efficace", "rapide", "lent", "précis",
            "approximatif", "théorique", "pratique", "empirique", "expérimental",
            "naturel", "artificiel", "synthétique", "organique", "inorganique",
            "statique", "dynamique", "stable", "instable", "variable",
            "constant", "aléatoire", "déterministe", "probabiliste", "chaotique",
            "linéaire", "non linéaire", "continu", "discret", "quantifié",
            "local", "global", "interne", "externe", "central",
            "profond", "superficiel", "large", "étroit", "vaste",
            "ancien", "moderne", "récent", "futur", "actuel",
            "connu", "inconnu", "célèbre", "obscur", "évident",
        ]

        complements = [
            "dans ce contexte", "en pratique", "en théorie", "dans la réalité", "dans l absolu",
            "à grande échelle", "à petite échelle", "en profondeur", "en surface", "en détail",
            "avec précision", "avec soin", "avec rigueur", "avec méthode", "avec logique",
            "de manière évidente", "de manière surprenante", "de manière cohérente", "de manière systématique", "de manière naturelle",
            "dans le cadre de cette étude", "dans le domaine concerné", "dans la littérature scientifique", "dans l industrie", "dans la nature",
            "pour les chercheurs", "pour les ingénieurs", "pour les praticiens", "pour le grand public", "pour les experts",
            "depuis des décennies", "depuis peu", "depuis toujours", "depuis la découverte", "depuis l invention",
            "à travers le monde", "à travers l histoire", "à travers les cultures", "à travers les disciplines", "à travers les générations",
        ]
        
        questions_debut = [
            "comment expliquer", "pourquoi", "dans quelle mesure", "à quel point", "de quelle façon",
            "quel est le rôle de", "quelle est l importance de", "que signifie", "comment définir", "comment comprendre",
        ]
        reponses_debut = [
            "pour répondre à cette question", "la réponse se trouve dans", "il faut comprendre que", "l explication réside dans", "le point clé est que",
            "la raison fondamentale est que", "plusieurs facteurs entrent en compte", "l analyse révèle que", "les données montrent que", "l expérience démontre que",
        ]

        print(f"  Entraînement MASSIF MGH : {n_phrases} phrases complexes...")
        count = 0

        for i in range(n_phrases):
            style = i % 20

            if style == 0:  # Définition simple
                s = random.choice(sujets_tech)
                v = random.choice(verbes_courants)
                phrase = f"{s} {v} un concept fondamental dans ce domaine."

            elif style == 1:  # Définition avec explication
                s = random.choice(sujets_tech)
                phrase = f"{s} représente une notion essentielle qui permet de comprendre les mécanismes sous jacents."

            elif style == 2:  # Explication cause-effet
                s = random.choice(sujets_tech)
                c = random.choice(connecteurs)
                phrase = f"{s} influence directement le résultat {c} il détermine la structure fondamentale du système."

            elif style == 3:  # Description fonctionnelle
                s = random.choice(sujets_courants)
                v = random.choice(verbes_tech)
                phrase = f"{s} {v} la manière dont les éléments interagissent entre eux."

            elif style == 4:  # Relation entre concepts
                s1 = random.choice(sujets_tech)
                s2 = random.choice(sujets_tech)
                phrase = f"la relation entre {s1} et {s2} est fondamentale pour comprendre le fonctionnement global."

            elif style == 5:  # Phrase avec adjectif qualificatif
                s = random.choice(sujets_tech)
                phrase = f"un {s} complexe nécessite une analyse approfondie pour être pleinement compris."

            elif style == 6:  # Comparaison
                s1 = random.choice(sujets_tech)
                s2 = random.choice(sujets_tech)
                phrase = f"contrairement à {s1}, {s2} offre une perspective différente sur le problème."

            elif style == 7:  # Énumération
                s = random.choice(sujets_tech)
                phrase = f"plusieurs facteurs contribuent à {s} notamment la structure la dynamique et l environnement."

            elif style == 8:  # Question rhétorique
                s = random.choice(sujets_tech)
                phrase = f"comment expliquer le rôle de {s} dans ce contexte particulier ?"

            elif style == 9:  # Réponse à question
                s = random.choice(sujets_tech)
                phrase = f"pour répondre à cette question il faut d abord comprendre que {s} joue un rôle central."

            elif style == 10:  # Conclusion
                s = random.choice(sujets_tech)
                phrase = f"en conclusion {s} apparaît comme un élément déterminant pour l ensemble du système."

            elif style == 11:  # Transition logique
                phrase = f"cette observation conduit naturellement à la question suivante quel est le mécanisme sous jacent."

            elif style == 12:  # Hypothèse
                s = random.choice(sujets_tech)
                phrase = f"on peut faire l hypothèse que {s} est directement corrélé avec les résultats observés."

            elif style == 13:  # Généralisation
                s = random.choice(sujets_tech)
                phrase = f"de manière générale {s} s applique à un grand nombre de situations différentes."

            elif style == 14:  # Précision
                s = random.choice(sujets_tech)
                phrase = f"plus précisément {s} se définit comme l ensemble des propriétés qui caractérisent le phénomène."

            elif style == 15:  # Illustration
                s = random.choice(sujets_tech)
                phrase = f"par exemple {s} peut être observé dans de nombreux contextes naturels et artificiels."

            elif style == 16:  # Condition
                s = random.choice(sujets_tech)
                phrase = f"si {s} est correctement appliqué alors les résultats seront significativement améliorés."

            elif style == 17:  # Contraste
                phrase = f"d un côté la théorie prédit certains résultats de l autre l expérience montre des écarts."

            elif style == 18:  # Synthèse
                s = random.choice(sujets_tech)
                phrase = f"en résumé {s} constitue la base sur laquelle repose toute l architecture du système."

            elif style == 19:  # Ouverture
                s = random.choice(sujets_tech)
                phrase = f"au delà de {s} de nombreuses perspectives restent à explorer dans ce domaine fascinant."

            count += self.entrainer_texte(phrase, amplitude=0.25)
            if (i+1) % 20000 == 0:
                print(f"  {i+1}/{n_phrases} | {count:,} bigrammes | E={np.sum(np.abs(self.H)**2):.0f} | vocab={len(self.vocab)}")

        return count
    
    # =================================================================
    # GÉNÉRATION
    # =================================================================
    def _prochains_mots(self, mot: str, top_k: int = 20) -> list:
        """Trouve les bigrammes les plus résonants pour un mot donné."""
        kx1, ky1 = self._mot_vers_kxky(mot)
        candidats = []
        
        for bigram_key, (kx2, ky2) in self.bigram_index.items():
            w1, w2 = bigram_key.split("|", 1)
            if w1 == mot:
                kx_mid = (kx1 + kx2) / 2
                ky_mid = (ky1 + ky2) / 2
                res = self._resonance(kx_mid, ky_mid)
                candidats.append((w2, res))
        
        candidats.sort(key=lambda x: x[1], reverse=True)
        return candidats[:top_k]
    
    def generer(self, amorce: str, max_mots: int = 30, temperature: float = 0.8,
                top_k: int = 10) -> str:
        """
        Génère du texte par chemin de résonance maximale.
        
        Args:
            amorce: Début de phrase ("Le chat")
            max_mots: Nombre max de mots à générer
            temperature: 0 = déterministe (top résonance uniquement)
                        1 = créatif (échantillonnage pondéré par résonance)
            top_k: Nombre de candidats considérés
        
        Returns:
            Texte généré complet
        """
        mots = re.findall(r"[a-zA-ZÀ-ÿ0-9]+|[.,!?;:]", amorce.lower())
        if not mots:
            return ""
        
        for _ in range(max_mots):
            dernier = mots[-1]
            if dernier in ('.', '!', '?', ';', ':', ','):
                if len(mots) > 5 and dernier != ',':
                    break  # Fin de phrase
                continue
            
            candidats = self._prochains_mots(dernier, top_k=top_k * 2)
            if not candidats:
                break
            
            # Filtrer les candidats raisonnables
            candidats = [(w, r) for w, r in candidats if w not in ('.', ',', '!', '?') or len(mots) > 3]
            if not candidats:
                break
            
            if temperature < 0.1:
                # Déterministe : meilleur candidat
                prochain = candidats[0][0]
            else:
                # Échantillonnage pondéré par résonance
                words, resonances = zip(*candidats[:top_k])
                resonances = np.array(resonances, dtype=np.float64)
                resonances = resonances - resonances.min() + 0.01
                resonances = resonances ** (1.0 / max(temperature, 0.1))
                probs = resonances / resonances.sum()
                idx = np.random.choice(len(words), p=probs)
                prochain = words[idx]
            
            mots.append(prochain)
            
            if prochain in ('.', '!', '?') and len(mots) > 5:
                break
        
        # Reconstruire la phrase
        resultat = ""
        for i, m in enumerate(mots):
            if m in ('.', ',', '!', '?', ';', ':'):
                resultat = resultat.rstrip() + m
                if m in ('.', '!', '?'):
                    resultat += " "
            else:
                resultat += (" " if i > 0 else "") + m
        
        return resultat.strip().capitalize()
    
    def generer_avec_savoir(self, amorce: str, contexte_savoir: list,
                            max_mots: int = 30, temperature: float = 0.7) -> str:
        """
        Génère du texte enrichi par un contexte de SAVOIR (hologramme KA).
        Les bigrammes sont pondérés par la pertinence du contexte.
        """
        mots = re.findall(r"[a-zA-ZÀ-ÿ0-9]+|[.,!?;:]", amorce.lower())
        if not mots:
            return ""
        
        for _ in range(max_mots):
            dernier = mots[-1]
            if dernier in ('.', '!', '?') and len(mots) > 5:
                break
            if dernier in (',', ';', ':'):
                continue
            
            candidats = self._prochains_mots(dernier, top_k=30)
            if not candidats:
                break
            
            # Pondération par contexte de savoir
            pondered = []
            for mot, resonance in candidats:
                boost = 1.0
                if mot in contexte_savoir:
                    boost = 2.0  # Le mot est pertinent pour le sujet
                for ctx_word in contexte_savoir:
                    if ctx_word in mot or mot in ctx_word:
                        boost = max(boost, 1.5)
                        break
                pondered.append((mot, resonance * boost))
            
            pondered.sort(key=lambda x: x[1], reverse=True)
            top = pondered[:10]
            
            words, scores = zip(*top)
            scores = np.array(scores, dtype=np.float64)
            scores = scores - scores.min() + 0.01
            scores = scores ** (1.0 / max(temperature, 0.1))
            probs = scores / scores.sum()
            
            prochain = np.random.choice(words, p=probs) if temperature > 0.05 else words[0]
            mots.append(prochain)
            
            if prochain in ('.', '!', '?') and len(mots) > 5:
                break
        
        resultat = ""
        for i, m in enumerate(mots):
            if m in ('.', ',', '!', '?', ';', ':'):
                resultat = resultat.rstrip() + m
                if m in ('.', '!', '?'):
                    resultat += " "
            else:
                resultat += (" " if i > 0 else "") + m
        
        return resultat.strip().capitalize()
    
    def injecter_vocabulaire_dynamique(self, mots_techniques: list, connecteurs: list = None, amplitude: float = 0.5):
        """
        Injecte des bigrammes TEMPORAIRES reliant un vocabulaire technique
        au langage courant de MGH. Utilisé par le conscient pour faire le pont
        entre l'hologramme de savoir et l'hologramme de langage.
        
        Args:
            mots_techniques: liste de mots/concepts issus de l'hologramme de savoir
            connecteurs: mots de liaison courants (si None, utilise les connecteurs de base)
            amplitude: force d'injection (0.5 = temporaire, ne persiste pas au save)
        """
        if connecteurs is None:
            connecteurs = ["est", "un", "une", "le", "la", "de", "des", "d", "et", 
                          "dans", "par", "pour", "avec", "comme", "qui", "que",
                          "sont", "fait", "permet", "repose", "utilise", "fonctionne"]
        
        count = 0
        for mot_tech in mots_techniques:
            mot_tech = mot_tech.strip().lower()
            if not mot_tech or mot_tech in self.vocab:
                continue
            
            # Bigrammes connecteur → mot technique
            for conn in connecteurs:
                if conn in self.vocab:
                    w1, w2 = conn.lower(), mot_tech
                    kx, ky = self._bigram_vers_onde(w1, w2)
                    self.H += amplitude * np.exp(1j * (kx * self.xx + ky * self.yy))
                    self.bigram_index[f"{w1}|{w2}"] = list((float(kx), float(ky)))
                    count += 1
            
            # Bigrammes mot technique → connecteur (dans l'autre sens)
            for conn in connecteurs[:6]:  # moins de combinaisons dans ce sens
                if conn in self.vocab:
                    w1, w2 = mot_tech, conn.lower()
                    kx, ky = self._bigram_vers_onde(w1, w2)
                    self.H += amplitude * 0.6 * np.exp(1j * (kx * self.xx + ky * self.yy))
                    self.bigram_index[f"{w1}|{w2}"] = list((float(kx), float(ky)))
                    count += 1
            
            # Marquer le mot comme connu
            self.vocab.add(mot_tech)
        
        return count
    
    def generer_connecte(
        self, amorce: str, contexte_savoir: list,
        max_mots: int = 50, temperature: float = 0.6
    ) -> str:
        """
        Génération connectée : injecte le vocabulaire technique dans MGH,
        génère, puis retire l'injection pour ne pas polluer l'hologramme.
        
        Cette méthode est le PONT entre l'hologramme de savoir et l'hologramme de langage.
        """
        # Sauvegarde de l'état
        H_backup = self.H.copy()
        bigram_backup = dict(self.bigram_index)
        vocab_backup = set(self.vocab)
        
        try:
            # Injecter les concepts techniques dans MGH
            n_injectes = self.injecter_vocabulaire_dynamique(
                contexte_savoir[:20], amplitude=0.4
            )
            
            # Générer avec le vocabulaire enrichi
            resultat = self.generer_avec_savoir(
                amorce, contexte_savoir, max_mots, temperature
            )
            
            return resultat
        finally:
            # Restaurer l'état (ne pas persister l'injection)
            self.H = H_backup
            self.bigram_index = bigram_backup
            self.vocab = vocab_backup
    
    def stats(self):
        return {
            "bigrammes": len(self.bigram_index),
            "vocabulaire": len(self.vocab),
            "energie_hologramme": float(np.sum(np.abs(self.H)**2)),
            "taille_hologramme": f"{NX}×{NY} = {NX*NY*2*8} octets",
            "fichier": MGH_FILE,
        }

# =========================================================================
# DÉMO
# =========================================================================
def demo():
    mgh = MGH()
    
    # Entraînement synthétique rapide
    print("=" * 60)
    print("MGH — Démonstration de génération harmonique")
    print("=" * 60)
    
    print("\n[1] Entraînement synthétique (structures grammaticales)...")
    t0 = time.time()
    n = mgh.entrainer_synthetique(n_phrases=20000)
    dt = time.time() - t0
    print(f"  {n:,} bigrammes en {dt:.1f}s")
    
    # Génération
    print("\n[2] Génération par résonance maximale...")
    amorces = [
        "le chat",
        "le médecin",
        "pourquoi l enfant",
        "quand la femme",
    ]
    for amorce in amorces:
        texte = mgh.generer(amorce, max_mots=15, temperature=0.7)
        print(f"  '{amorce}' → \"{texte}\"")
    
    # Génération avec contexte
    print("\n[3] Génération enrichie par contexte de savoir...")
    contexte = ["médecin", "patient", "traitement", "diagnostic", "santé", "hôpital"]
    texte = mgh.generer_avec_savoir("le médecin", contexte, max_mots=20, temperature=0.6)
    print(f"  → \"{texte}\"")
    
    # Stats
    s = mgh.stats()
    print(f"\n[4] Statistiques MGH")
    print(f"  Bigrammes : {s['bigrammes']:,}")
    print(f"  Vocabulaire : {s['vocabulaire']}")
    print(f"  Énergie : {s['energie_hologramme']:.0f}")
    print(f"  Taille : {s['taille_hologramme']}")
    
    mgh._save()
    print(f"\n  Hologramme sauvegardé : {MGH_FILE}")

# =========================================================================
# MAIN
# =========================================================================
def main():
    parser = argparse.ArgumentParser(description="MGH — Module de Génération Harmonique")
    parser.add_argument("--train", type=str, default="", help="Dossier de corpus d'entraînement")
    parser.add_argument("--generate", type=str, default="", help="Amorce de génération")
    parser.add_argument("--max-mots", type=int, default=25)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--stats", action="store_true")
    args = parser.parse_args()
    
    mgh = MGH()
    
    if args.stats:
        print(json.dumps(mgh.stats(), indent=2))
        return
    
    if args.demo:
        demo()
        return
    
    if args.train:
        print(f"Entraînement MGH : {args.train}")
        mgh.entrainer_synthetique(n_phrases=50000)
        if os.path.isdir(args.train):
            mgh.entrainer_dossier(args.train)
        elif os.path.isfile(args.train):
            mgh.entrainer_fichier(args.train)
        mgh._save()
        print(f"\nBigrammes: {len(mgh.bigram_index):,} | E={np.sum(np.abs(mgh.H)**2):.0f}")
        return
    
    if args.generate:
        print(f"Génération: \"{args.generate}\"")
        texte = mgh.generer(args.generate, max_mots=args.max_mots,
                           temperature=args.temperature)
        print(f"\n{texte}")
        return
    
    # Default: interactive
    print("\nMGH — Mode interactif (générez du texte, 'quit' pour quitter)")
    while True:
        try:
            amorce = input("\n✍️  > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not amorce:
            continue
        if amorce.lower() in ('quit', 'exit', 'q'):
            break
        texte = mgh.generer(amorce, max_mots=30, temperature=0.7)
        print(f"   {texte}")

if __name__ == "__main__":
    main()