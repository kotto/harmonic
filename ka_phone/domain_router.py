#!/usr/bin/env python3
"""
DOMAIN ROUTER — Classificateur de domaine pour KA Phone
=========================================================
Détecte automatiquement le domaine d'une question utilisateur
pour orienter le pipeline vers les bons templates et la bonne KB.

Fonctionne par triple détection :
  1. Mots-clés par domaine (rapide, ~0ms)
  2. Fréquence harmonique (kx, ky) → domaine le plus proche
  3. Fallback "conversation_courante"

Domaines supportés (27) :
  cuisine_gastronomie, sport_loisirs, musique_arts, psychologie_bienetre,
  voyage_tourisme, vie_pratique, animaux_nature, economie_finances,
  education_apprentissage, egypte_ancienne, pop_culture,
  sciences, medecine, histoire, geographie, langue_francaise,
  societe, philosophie, technologie, conversation_courante,
  arithmetique, algebre, calcul, geometrie, probabilite, logique, general

Usage:
  from domain_router import DomainRouter
  router = DomainRouter()
  domain, confidence = router.classify("Comment faire une quiche lorraine ?")
  # → ("cuisine_gastronomie", 0.95)
"""

import re, hashlib, os, json
from typing import Tuple, Dict, List, Optional
import math

# ══════════════════════════════════════════════════════════════════════════
# DOMAIN KEYWORD MAPS
# ══════════════════════════════════════════════════════════════════════════

DOMAIN_KEYWORDS = {
    "cuisine_gastronomie": [
        "cuisine", "recette", "cuisiner", "préparer", "ingrédient", "ingrédients",
        "manger", "plat", "repas", "restaurant", "chef", "gastronomie",
        "fromage", "vin", "pain", "pâtisserie", "dessert", "sauce", "épice",
        "chocolat", "café", "thé", "bière", "sushi", "pizza", "pâtes",
        "quiche", "tarte", "soupe", "salade", "grillade", "rôti", "poêle",
        "four", "casserole", "mijoter", "marinade", "assaisonner",
        "boulangerie", "viennoiserie", "croissant", "baguette",
        "gourmet", "dégustation", "sommelier", "terroir",
    ],
    "sport_loisirs": [
        "sport", "football", "foot", "rugby", "tennis", "basket", "basketball",
        "natation", "nager", "course", "courir", "marathon", "cyclisme", "vélo",
        "ski", "surf", "yoga", "fitness", "musculation", "gymnastique",
        "match", "tournoi", "championnat", "équipe", "joueur", "entraîneur",
        "arbitre", "but", "essai", "médaillé", "olympique", "olympiques",
        "randonnée", "escalade", "plongée", "parachutisme", "patinage",
        "échecs", "jeu", "jeux", "loisir", "loisirs", "passe-temps",
        "danse", "théâtre", "cirque", "magie", "cinéma",
        "pêche", "chasse", "jardinage", "bricolage",
    ],
    "musique_arts": [
        "musique", "chanson", "chanter", "chant", "chanteur", "chanteuse",
        "guitare", "piano", "violon", "batterie", "orchestre", "concert",
        "opéra", "jazz", "rock", "classique", "hip-hop", "rap", "électro",
        "compositeur", "compositrice", "album", "disque", "single", "tube",
        "peinture", "peintre", "tableau", "sculpture", "sculpteur",
        "musée", "exposition", "galerie", "artiste", "œuvre", "œuvre",
        "louvre", "monet", "picasso", "van gogh", "léonard de vinci",
        "architecture", "design", "mode", "couture", "photographie",
        "poésie", "poème", "roman", "littérature", "écrivain", "auteur",
        "bande dessinée", "bd", "cinéma", "film", "acteur", "actrice",
    ],
    "psychologie_bienetre": [
        "psychologie", "psychologue", "émotion", "sentiment", "ressentir",
        "stress", "anxiété", "angoissé", "angoissée", "dépression", "déprimé",
        "sommeil", "dormir", "insomnie", "rêve", "cauchemar",
        "méditation", "méditer", "pleine conscience", "relaxation", "respirer",
        "bonheur", "heureux", "malheur", "triste", "tristesse",
        "colère", "énervé", "peur", "amour", "aimer", "amitié", "ami",
        "confiance", "estime de soi", "motivation", "burn-out", "épuisement",
        "thérapie", "psy", "psychanalyse", "développement personnel",
        "bien-être", "bienêtre", "santé mentale", "équilibre",
        "relation", "couple", "famille", "parent", "enfant", "éducation",
        "deuil", "solitude", "résilience", "empathie",
    ],
    "voyage_tourisme": [
        "voyage", "voyager", "tourisme", "touriste", "visiter", "destination",
        "hôtel", "avion", "train", "bateau", "aéroport", "gare", "vol",
        "passeport", "visa", "douane", "bagage", "valise", "guide",
        "paris", "londres", "new york", "tokyo", "rome", "barcelone",
        "bangkok", "sydney", "marrakech", "amsterdam", "venise",
        "tour eiffel", "grande muraille", "taj mahal", "machu picchu",
        "unesco", "patrimoine mondial", "camping", "auberge", "croisière",
        "écotourisme", "randonnée", "itinéraire", "décalage horaire",
        "vacances", "séjour", "excursion", "change", "monnaie",
    ],
    "vie_pratique": [
        "logement", "appartement", "maison", "immobilier", "location", "acheter",
        "déménagement", "déménager", "loyer", "propriétaire", "locataire",
        "budget", "argent", "impôt", "impôts", "taxe", "déclaration",
        "assurance", "banque", "compte", "épargne", "crédit", "prêt",
        "bricolage", "bricoler", "réparer", "plomberie", "électricité",
        "peinture", "outil", "outils", "tournevis", "marteau", "perceuse",
        "jardin", "jardinage", "plante", "potager", "arroser",
        "ménage", "nettoyer", "lessive", "recyclage", "poubelle",
        "voiture", "permis", "code de la route", "transports",
        "administration", "papiers", "carte d'identité", "passeport",
        "démarche", "démarches", "formulaire", "mairie", "préfecture",
    ],
    "animaux_nature": [
        "animal", "animaux", "chien", "chat", "cheval", "oiseau", "oiseaux",
        "poisson", "insecte", "mammifère", "reptile", "amphibien",
        "lion", "tigre", "éléphant", "dauphin", "baleine", "requin",
        "loup", "ours", "singe", "serpent", "araignée", "abeille",
        "papillon", "fourmi", "zoo", "aquarium", "vétérinaire",
        "biodiversité", "écosystème", "forêt", "océan", "rivière", "lac",
        "montagne", "désert", "jungle", "savane", "nature", "environnement",
        "écologie", "climat", "espèce", "extinction", "protection",
        "parc national", "réserve naturelle",
    ],
    "economie_finances": [
        "économie", "économique", "finance", "bourse", "action", "investir",
        "investissement", "épargne", "retraite", "salaire", "smic",
        "chômage", "emploi", "entreprise", "start-up", "entrepreneur",
        "commerce", "marché", "croissance", "inflation", "pib",
        "monnaie", "euro", "dollar", "bitcoin", "crypto", "cryptomonnaie",
        "banque", "banquier", "crédit", "dette", "impôt", "taxe",
        "budget", "déficit", "mondialisation", "protectionnisme",
        "consommation", "pouvoir d'achat", "inégalités",
    ],
    "education_apprentissage": [
        "éducation", "école", "collège", "lycée", "université", "fac",
        "cours", "apprendre", "étudier", "étudiant", "professeur", "prof",
        "diplôme", "bac", "baccalauréat", "doctorat", "master", "licence",
        "formation", "pédagogie", "méthode", "enseignement", "cours en ligne",
        "langue", "langues", "français", "anglais", "espagnol", "chinois",
        "grammaire", "orthographe", "conjugaison", "vocabulaire",
        "lecture", "écriture", "mémoire", "apprentissage",
        "montessori", "mooc", "dyslexie", "illectronisme",
    ],
    "egypte_ancienne": [
        "égypte", "égyptien", "égyptienne", "pharaon", "pharaonique",
        "pyramide", "pyramides", "gizeh", "sphinx", "momification", "momie",
        "hiéroglyphe", "hiéroglyphes", "mythologie égyptienne",
        "osiris", "isis", "horus", "anubis", "rê", "thot", "bastet", "seth",
        "nil", "alexandrie", "le caire", "karnak", "vallée des rois",
        "toutânkhamon", "ramsès", "cléopâtre", "néfertiti", "akhénaton",
        "obélisque", "scarabée", "ânkh", "maât", "ka",
        "livre des morts", "mastaba",
    ],
    "pop_culture": [
        "film", "série", "netflix", "youtube", "tiktok", "instagram",
        "facebook", "twitter", "podcast", "streaming",
        "star wars", "harry potter", "seigneur des anneaux", "marvel",
        "manga", "anime", "jeu vidéo", "jeux vidéo", "playstation",
        "xbox", "nintendo", "minecraft", "fortnite", "league of legends",
        "geek", "cosplay", "mème", "influenceur", "influenceuse",
        "taylor swift", "beyoncé", "beatles", "pop", "rock",
        "festival", "coachella", "glastonbury", "science-fiction", "fantasy",
        "astérix", "tintin", "bd", "comics", "super-héros", "super-héros",
    ],
    "sciences": [
        "physique", "chimie", "biologie", "science", "scientifique",
        "atome", "molécule", "cellule", "gène", "génétique", "adn",
        "évolution", "darwin", "gravité", "relativité", "quantique",
        "électromagnétisme", "optique", "thermodynamique", "mécanique",
        "newton", "einstein", "curie", "pasteur", "galilée",
        "expérience", "théorie", "loi", "principe", "hypothèse",
        "découverte", "recherche", "laboratoire",
    ],
    "medecine": [
        "médecine", "médecin", "docteur", "hôpital", "clinique", "patient",
        "maladie", "symptôme", "traitement", "médicament", "vaccin",
        "chirurgie", "opération", "diagnostic", "radio", "irm", "scanner",
        "cancer", "diabète", "hypertension", "cardiaque", "cœur",
        "poumon", "foie", "rein", "cerveau", "neurologie",
        "psychiatrie", "psychologie", "santé", "épidémie", "virus",
        "bactérie", "infection", "antibiotique", "douleur", "fièvre",
        "allergie", "asthme", "urgence", "samu", "pompiers",
    ],
    "histoire": [
        "histoire", "historique", "guerre", "révolution", "empire", "royaume",
        "roi", "reine", "empereur", "napoléon", "louis xiv", "gandhi",
        "mandela", "de gaulle", "moyen âge", "renaissance", "antiquité",
        "préhistoire", "rome", "grecque", "gréco-romain", "viking",
        "guerre mondiale", "guerre froide", "indépendance", "colonie",
        "civilisation", "dynastie", "siècle", "millénaire", "date",
        "chronologie", "bataille", "traité", "armistice",
    ],
    "geographie": [
        "géographie", "pays", "capitale", "continent", "océan", "mer",
        "fleuve", "rivière", "montagne", "volcan", "désert", "forêt",
        "population", "superficie", "climat", "latitude", "longitude",
        "france", "allemagne", "italie", "espagne", "angleterre",
        "états-unis", "chine", "inde", "japon", "brésil", "canada",
        "afrique", "asie", "europe", "amérique", "océanie", "antarctique",
        "carte", "atlas", "frontière", "drapeau",
    ],
    "arithmetique": [
        "calcul", "calculer", "addition", "soustraction", "multiplication",
        "division", "somme", "différence", "produit", "quotient",
        "pourcentage", "fraction", "nombre", "chiffre", "entier", "décimal",
        "combien", "fois", "plus", "moins", "divisé", "multiplié",
        "factoriel", "factorielle", "puissance", "racine carrée",
    ],
    "algebre": [
        "équation", "équations", "inconnue", "variable", "x =", "résoudre",
        "polynôme", "factoriser", "développer", "racine", "racines",
        "système d'équation", "inéquation", "matrice", "déterminant",
        "vecteur", "espace vectoriel", "linéaire", "quadratique",
    ],
    "calcul": [
        "dérivée", "dériver", "intégrale", "intégrer", "limite", "tendre vers",
        "fonction", "f(x)", "dx", "dy/dx", "analyse", "calcul différentiel",
        "calcul intégral", "primitive", "taylor", "série", "convergence",
    ],
    "geometrie": [
        "géométrie", "triangle", "cercle", "carré", "rectangle", "aire",
        "périmètre", "volume", "angle", "degré", "radian",
        "pythagore", "thalès", "hypoténuse", "diamètre", "rayon",
        "coordonnées", "vecteur", "cosinus", "sinus", "tangente",
    ],
    "probabilite": [
        "probabilité", "probable", "chance", "statistique", "statistiques",
        "moyenne", "médiane", "variance", "écart-type", "distribution",
        "aléatoire", "tirage", "lancer de dé", "pile ou face",
        "espérance", "loi", "échantillon", "sondage", "corrélation",
    ],
    "logique": [
        "logique", "logiquement", "raisonnement", "raisonner",
        "syllogisme", "déduction", "induction", "prémisse", "conclusion",
        "si...alors", "donc", "implique", "équivaut", "contraposée",
        "vrai", "faux", "tous", "aucun", "certains", "quelques",
    ],
}

# ══════════════════════════════════════════════════════════════════════════
# DOMAIN FREQUENCY SIGNATURES (harmonic kx, ky)
# ══════════════════════════════════════════════════════════════════════════

def _generate_domain_signature(domain_name: str) -> Tuple[float, float]:
    """Génère une signature fréquentielle unique pour chaque domaine."""
    h = hashlib.sha256(domain_name.encode()).hexdigest()
    kx = (int(h[:16], 16) % 2000) / 100.0 - 10.0
    ky = (int(h[16:32], 16) % 2000) / 100.0 - 10.0
    return (kx, ky)


DOMAIN_SIGNATURES = {d: _generate_domain_signature(d) for d in DOMAIN_KEYWORDS}
DOMAIN_SIGNATURES["conversation_courante"] = _generate_domain_signature("conversation_courante")
DOMAIN_SIGNATURES["general"] = _generate_domain_signature("general")


# ══════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════

class DomainRouter:
    """
    Classificateur de domaine pour les questions utilisateur.

    Stratégie :
      Niveau 1 : Mots-clés exacts → score immédiat
      Niveau 2 : Chevauchement partiel de mots → score cumulatif
      Niveau 3 : Fréquence harmonique → domaine le plus proche
      Niveau 4 : Fallback "conversation_courante"
    """

    def __init__(self):
        self.domain_keywords = DOMAIN_KEYWORDS
        self.domain_signatures = DOMAIN_SIGNATURES
        # Construire un index inversé mot→domaines pour lookup rapide
        self._word_index = self._build_word_index()

    def _build_word_index(self) -> Dict[str, List[str]]:
        """Index inversé : un mot → liste de domaines associés."""
        index = {}
        for domain, keywords in self.domain_keywords.items():
            for kw in keywords:
                kw_lower = kw.lower()
                if kw_lower not in index:
                    index[kw_lower] = []
                if domain not in index[kw_lower]:
                    index[kw_lower].append(domain)
        return index

    def classify(self, prompt: str, detailed: bool = False) -> Tuple[str, float]:
        """
        Classifie une question en domaine.

        Args:
            prompt: La question utilisateur
            detailed: Si True, retourne aussi les scores de tous les domaines

        Returns:
            (domaine, confiance) ou (domaine, confiance, tous_les_scores)
        """
        p = prompt.lower().strip()
        words = set(re.findall(r'[a-zéèêëàâîïôûùçœæ]+', p))

        # Phase 1 : Mots-clés exacts (multi-mot prioritaire)
        domain_scores = {}
        for domain, keywords in self.domain_keywords.items():
            score = 0.0
            for kw in keywords:
                kw_lower = kw.lower()
                # Chercher le mot-clé comme sous-chaîne dans la phrase complète
                # (permet "je voudrais cuisiner" → cuisine)
                if kw_lower in p:
                    # Bonus pour les mots-clés plus longs (plus spécifiques)
                    score += len(kw_lower) * 0.5

            if score > 0:
                domain_scores[domain] = score

        # Phase 2 : Chevauchement de mots individuels
        for word in words:
            if word in self._word_index:
                for domain in self._word_index[word]:
                    domain_scores[domain] = domain_scores.get(domain, 0) + 1.0

        # Phase 3 : Math detection (check for numbers, operators, math terms)
        if re.search(r'[+\-*/^=×÷]|\d+\s*[+\-*/^]\s*\d+|dérivée|intégrale|équation|probabilité', p):
            # Determine which math subdomain
            if re.search(r'\d+\s*[+\-*/^]\s*\d+|combien|fois|plus|moins|divisé|multiplié|pourcentage|factoriel', p):
                domain_scores["arithmetique"] = domain_scores.get("arithmetique", 0) + 8.0
            if re.search(r'équation|inconnue|résoudre|polynôme|factoriser|matrice|x\s*=', p):
                domain_scores["algebre"] = domain_scores.get("algebre", 0) + 8.0
            if re.search(r'dérivée|intégrale|limite|primitive|f\(x\)|dy/dx|taylor', p):
                domain_scores["calcul"] = domain_scores.get("calcul", 0) + 8.0
            if re.search(r'triangle|cercle|aire|périmètre|volume|pythagore|angle|carré', p):
                domain_scores["geometrie"] = domain_scores.get("geometrie", 0) + 8.0
            if re.search(r'probabilité|statistique|moyenne|médiane|chance', p):
                domain_scores["probabilite"] = domain_scores.get("probabilite", 0) + 8.0
            if re.search(r'logique|syllogisme|déduction|si.*alors|tous|aucun|implique', p):
                domain_scores["logique"] = domain_scores.get("logique", 0) + 8.0

        # Phase 4 : Si aucun mot-clé trouvé, utiliser la signature fréquentielle
        if not domain_scores:
            kx, ky = self._prompt_signature(prompt)
            best_domain = "conversation_courante"
            best_dist = float('inf')
            for domain, (dkx, dky) in self.domain_signatures.items():
                dist = math.sqrt((kx - dkx) ** 2 + (ky - dky) ** 2)
                if dist < best_dist:
                    best_dist = dist
                    best_domain = domain
            confidence = max(0.3, 1.0 - best_dist / 15.0)
            if detailed:
                return best_domain, confidence, {best_domain: confidence}
            return best_domain, confidence

        # Phase 5 : Normaliser les scores et trouver le meilleur
        if not domain_scores:
            if detailed:
                return "conversation_courante", 0.3, {"conversation_courante": 0.3}
            return "conversation_courante", 0.3

        # Trier par score décroissant
        sorted_domains = sorted(domain_scores.items(), key=lambda x: -x[1])
        best_domain, best_score = sorted_domains[0]

        # Calculer la confiance (normalisée par rapport au 2e meilleur)
        if len(sorted_domains) > 1:
            runner_up_score = sorted_domains[1][1]
            confidence = min(1.0, best_score / (best_score + runner_up_score + 1.0))
        else:
            confidence = min(1.0, best_score / 15.0)

        confidence = max(0.4, confidence)

        if detailed:
            normalized = {d: s / max(domain_scores.values(), 1) for d, s in domain_scores.items()}
            return best_domain, confidence, normalized

        return best_domain, confidence

    def _prompt_signature(self, prompt: str) -> Tuple[float, float]:
        """Génère une signature fréquentielle pour un texte."""
        h = hashlib.sha256(prompt.encode()[:200]).hexdigest()
        kx = (int(h[:16], 16) % 2000) / 100.0 - 10.0
        ky = (int(h[16:32], 16) % 2000) / 100.0 - 10.0
        return (kx, ky)

    def get_domains(self) -> List[str]:
        """Retourne la liste de tous les domaines supportés."""
        return sorted(list(self.domain_keywords.keys()) +
                      ["conversation_courante", "general",
                       "conseil_sommeil", "conseil_stress", "conseil_productivite",
                       "conseil_communication", "conseil_confiance", "conseil_motivation",
                       "conseil_decision", "conseil_finances", "conseil_apprentissage",
                       "conseil_alimentation"])

    def get_domain_template_name(self, domain: str) -> str:
        """
        Mappe un domaine vers le nom de template correspondant dans HybridWriter.
        Gère les alias et la normalisation.
        Détecte aussi les demandes de conseil pour orienter vers les templates auto-suffisants.
        """
        alias_map = {
            "arithmetique": "arithmetic",
            "algebre": "equation_solve",
            "geometrie": "geometry_formula",
            "probabilite": "probability",
            "logique": "yes_no",
            "calcul": "calculus_derivative",
            "medecine": "medecine",
            "histoire": "histoire",
            "geographie": "geographie",
            "sciences": "sciences",
            "conversation_courante": "conversation_courante",
            # Conseils auto-suffisants
            "conseil_sommeil": "conseil_sommeil",
            "conseil_stress": "conseil_stress",
            "conseil_productivite": "conseil_productivite",
            "conseil_communication": "conseil_communication",
            "conseil_confiance": "conseil_confiance",
            "conseil_motivation": "conseil_motivation",
            "conseil_decision": "conseil_decision",
            "conseil_finances": "conseil_finances",
            "conseil_apprentissage": "conseil_apprentissage",
            "conseil_alimentation": "conseil_alimentation",
        }
        return alias_map.get(domain, domain)

    def is_advice_request(self, prompt: str) -> Tuple[bool, Optional[str]]:
        """
        Détecte si la question est une demande de conseil (vs une demande de fait).
        Retourne (True, conseil_domain) ou (False, None).

        Patterns détectés :
        - "comment + verbe d'action" → conseil pratique
        - "que faire pour/contre" → conseil
        - "conseil/astuce/technique pour" → conseil explicite
        - "quel est le meilleur moyen de" → conseil
        - Verbes modaux : "dois-je", "devrais-je" → conseil décision
        - "par où commencer", "comment débuter" → conseil débutant
        """
        p = prompt.lower().strip()

        # Patterns de demande de conseil explicite
        advice_patterns = [
            (r'(?:comment|comment faire pour|comment puis-je)\s+(?:mieux\s+)?(?:dormir|m\'endormir|trouver le sommeil)', "conseil_sommeil"),
            (r'(?:comment|comment faire pour)\s+(?:gerer|reduire|diminuer|calmer)\s+(?:le\s+)?stress', "conseil_stress"),
            (r'(?:comment|comment faire pour)\s+(?:etre|devenir)\s+(?:plus\s+)?productif', "conseil_productivite"),
            (r'(?:comment|comment faire pour)\s+(?:mieux\s+)?communiquer', "conseil_communication"),
            (r'(?:comment|comment faire pour)\s+(?:avoir|retrouver|renforcer)\s+(?:confiance|estime)', "conseil_confiance"),
            (r'(?:comment|comment faire pour)\s+(?:se|me|trouver la)\s+motiv', "conseil_motivation"),
            (r'(?:comment|comment faire pour)\s+(?:prendre|faire)\s+(?:une|un)\s+(?:decision|choix)', "conseil_decision"),
            (r'(?:comment|comment faire pour)\s+(?:gerer|mieux gerer|epargner)\s+(?:son|mon|ton|mes|tes|ses)\s+(?:argent|budget|finance)', "conseil_finances"),
            (r'(?:comment|comment faire pour)\s+(?:mieux\s+)?(?:apprendre|memoriser|retenir|etudier)', "conseil_apprentissage"),
            (r'(?:comment|comment faire pour)\s+(?:mieux\s+)?manger', "conseil_alimentation"),
            (r'(?:as-tu|avez-vous|donne-moi|donnez-moi|quel|quelle)\s+(?:un|une|des?)\s+conseil', "conseil_pratique"),
            (r'\b(?:conseil|conseils|astuce|astuces|technique|methode)\b', "conseil_pratique"),
            (r'(?:que faire|quoi faire)\s+(?:pour|contre|en cas de|face a)', "conseil_pratique"),
            (r'(?:quel est|quelle est)\s+(?:le meilleur|la meilleure|le bon|la bonne)\s+(?:moyen|façon|maniere|methode)', "conseil_pratique"),
            (r'\b(?:dois-je|devrais-je|devrais-tu|dois-tu|faut-il|est-ce que je dois)\b', "conseil_pratique"),
            (r'(?:par ou|comment)\s+(?:commencer|debuter|demarrer|se lancer)', "conseil_pratique"),
        ]

        for pattern, conseil_domain in advice_patterns:
            if re.search(pattern, p):
                return True, conseil_domain

        # Si la question contient "comment" + un domaine pratique = probablement un conseil
        if re.search(r'\bcomment\b', p):
            if "dormir" in p or "sommeil" in p or "insomnie" in p:
                return True, "conseil_sommeil"
            if "stress" in p or "anxiet" in p or "angoiss" in p:
                return True, "conseil_stress"
            if "productif" in p or "concentr" in p or "focus" in p:
                return True, "conseil_productivite"
            if "communiqu" in p or "parler" in p or "dialogue" in p:
                return True, "conseil_communication"
            if "confiance" in p or "estime" in p or "oser" in p:
                return True, "conseil_confiance"
            if "motiv" in p or "procrastin" in p:
                return True, "conseil_motivation"
            if "decid" in p or "choisir" in p or "choix" in p:
                return True, "conseil_decision"
            if "argent" in p or "budget" in p or "epargn" in p or "invest" in p:
                return True, "conseil_finances"
            if "apprendre" in p or "memoris" in p or "retenir" in p or "etudi" in p:
                return True, "conseil_apprentissage"
            if "manger" in p or "aliment" in p or "nourr" in p:
                return True, "conseil_alimentation"
            return True, "conseil_pratique"

        return False, None


# ══════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    router = DomainRouter()

    tests = [
        "Comment faire une quiche lorraine ?",
        "Quelles sont les règles du rugby ?",
        "Qui est Claude Monet ?",
        "Pourquoi je stresse avant de dormir ?",
        "Où se trouve le Machu Picchu ?",
        "Comment réparer un robinet qui fuit ?",
        "Que mange un hérisson ?",
        "C'est quoi le bitcoin ?",
        "Comment apprendre l'espagnol rapidement ?",
        "Qui était Toutânkhamon ?",
        "Qui a gagné la dernière saison de Star Wars ?",
        "Quelle est la capitale du Brésil ?",
        "15 fois 7 plus 3",
        "dérivée de x au carré",
        "Bonjour, comment ça va ?",
        "Quelle est la probabilité d'avoir un 6 au dé ?",
        "Résous x² - 3x + 2 = 0",
        "Quels sont les symptômes de la grippe ?",
        "Quand a eu lieu la Révolution française ?",
        "Quel temps fait-il à Paris ?",
    ]

    print(f"{'QUESTION':<55} | {'DOMAINE':<28} | {'CONFIANCE':<10}")
    print("-" * 95)

    for q in tests:
        d, c = router.classify(q)
        print(f"{q[:52]:<55} | {d:<28} | {c:.3f}")