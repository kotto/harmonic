#!/usr/bin/env python3
"""
INGESTION DE VRAI FRANÇAIS DANS MGH
====================================
Télécharge des articles Wikipedia français via l'API
et les ingère dans MGH (bigrammes + trigrammes réels).

Usage :
  python ka_phone/ingest_real_french.py --articles 5000   # 5000 articles (~2h)
  python ka_phone/ingest_real_french.py --articles 20000  # 20k articles (~8h)
  python ka_phone/ingest_real_french.py --resume          # Reprendre

Les articles sont choisis pour couvrir un large spectre :
sciences, médecine, histoire, philosophie, technologie, etc.
"""

import os, sys, time, json, argparse, re, urllib.request, urllib.parse, urllib.error
import xml.etree.ElementTree as ET
import random

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

from mgh_generation import MGH, MGH_FILE, BIGRAM_FILE

# =========================================================================
# LISTES DE PAGES WIKIPEDIA FRANÇAISES PAR DOMAINE
# =========================================================================

WIKIPEDIA_ARTICLES = {
    "sciences": [
        "Physique", "Mathématiques", "Biologie", "Chimie", "Astronomie",
        "Mécanique_quantique", "Relativité_générale", "Thermodynamique",
        "Électromagnétisme", "Optique", "Acoustique", "Physique_nucléaire",
        "Physique_des_particules", "Théorie_des_cordes", "Principe_holographique",
        "Mécanique_classique", "Hydrodynamique", "Aérodynamique",
        "Algèbre", "Géométrie", "Analyse_(mathématiques)", "Probabilité",
        "Statistique", "Théorie_des_nombres", "Topologie", "Logique_mathématique",
        "Théorème_de_Pythagore", "Nombre_d'or", "Suite_de_Fibonacci",
        "Fractale", "Théorie_du_chaos", "Système_dynamique",
        "Biologie_cellulaire", "Génétique", "Évolution_(biologie)",
        "Écologie", "Biologie_moléculaire", "Biochimie", "Microbiologie",
        "Botanique", "Zoologie", "Neurosciences", "Physiologie",
        "Chimie_organique", "Chimie_inorganique", "Chimie_physique",
        "Tableau_périodique_des_éléments", "Réaction_chimique",
        "Atome", "Molécule", "Liaison_chimique",
        "Système_solaire", "Galaxie", "Trou_noir", "Big_Bang",
        "Étoile", "Planète", "Terre", "Lune", "Soleil",
        "Cosmologie", "Astrophysique", "Exoplanète",
    ],
    "médecine": [
        "Médecine", "Anatomie", "Physiologie_humaine", "Pathologie",
        "Cancer", "Diabète", "Hypertension_artérielle", "Maladie_cardiovasculaire",
        "Système_immunitaire", "Vaccination", "Antibiotique", "Chirurgie",
        "Imagerie_médicale", "Radiographie", "IRM", "Scanner",
        "Neurosciences", "Psychiatrie", "Psychologie", "Neurologie",
        "Maladie_d'Alzheimer", "Maladie_de_Parkinson", "Sclérose_en_plaques",
        "Virologie", "Bactériologie", "Épidémiologie", "Santé_publique",
        "Pharmacologie", "Anesthésie", "Urgence_médicale",
        "Pédiatrie", "Gériatrie", "Cardiologie", "Pneumologie",
        "Hépatologie", "Néphrologie", "Endocrinologie", "Dermatologie",
        "Ophtalmologie", "Oto-rhino-laryngologie", "Rhumatologie",
    ],
    "technologie": [
        "Informatique", "Internet", "World_Wide_Web", "Intelligence_artificielle",
        "Apprentissage_automatique", "Réseau_de_neurones_artificiels",
        "Deep_learning", "Traitement_automatique_du_langage_naturel",
        "Algorithme", "Programmation_informatique", "Python_(langage)",
        "JavaScript", "HTML", "CSS", "Base_de_données", "SQL",
        "Système_d'exploitation", "Linux", "Windows", "macOS",
        "Réseau_informatique", "Protocole_Internet", "Wi-Fi", "Bluetooth",
        "Téléphone_mobile", "Smartphone", "Ordinateur", "Microprocesseur",
        "Électronique", "Robotique", "Impression_3D", "Nanotechnologie",
        "Cryptographie", "Blockchain", "Bitcoin", "Cybersécurité",
        "Réalité_virtuelle", "Réalité_augmentée", "Cloud_computing",
        "Big_data", "Internet_des_objets", "Véhicule_autonome",
        "Énergie_renouvelable", "Énergie_solaire", "Énergie_éolienne",
        "Batterie_électrique", "Voiture_électrique",
    ],
    "philosophie": [
        "Philosophie", "Éthique", "Métaphysique", "Épistémologie",
        "Logique", "Esthétique", "Philosophie_politique", "Philosophie_des_sciences",
        "Platon", "Aristote", "Descartes", "Kant", "Nietzsche",
        "Socrate", "Hegel", "Spinoza", "Heidegger", "Sartre",
        "Phénoménologie", "Existentialisme", "Stoïcisme", "Épicurisme",
        "Rationalisme", "Empirisme", "Idéalisme", "Matérialisme",
        "Libre_arbitre", "Conscience", "Déterminisme", "Humanisme",
        "Philosophie_de_l'esprit", "Philosophie_du_langage",
    ],
    "histoire": [
        "Histoire", "Préhistoire", "Antiquité", "Moyen_Âge", "Renaissance",
        "Époque_moderne", "Époque_contemporaine", "Révolution_française",
        "Première_Guerre_mondiale", "Seconde_Guerre_mondiale", "Guerre_froide",
        "Empire_romain", "Grèce_antique", "Égypte_antique", "Civilisation",
        "Révolution_industrielle", "Colonisation", "Décolonisation",
        "Histoire_de_France", "Histoire_de_l'Europe", "Histoire_de_l'Afrique",
        "Histoire_des_sciences", "Histoire_de_la_médecine",
        "Napoléon_Ier", "Louis_XIV", "Gandhi", "Martin_Luther_King",
        "Nelson_Mandela", "Charles_de_Gaulle", "Marie_Curie",
        "Albert_Einstein", "Isaac_Newton", "Galilée", "Darwin",
    ],
    "société": [
        "Société_(sciences_sociales)", "Économie_(activité_humaine)",
        "Politique", "Droit", "Justice", "Éducation", "Culture",
        "Art", "Musique", "Littérature", "Cinéma", "Théâtre",
        "Religion", "Démocratie", "République", "État", "Nation",
        "Mondialisation", "Développement_durable", "Environnement",
        "Climat", "Biodiversité", "Écologie_politique",
        "Urbanisme", "Architecture", "Transport", "Agriculture",
        "Psychologie_sociale", "Sociologie", "Anthropologie", "Ethnologie",
        "Langage", "Linguistique", "Communication", "Média",
        "Famille", "Travail", "Chômage", "Inégalités_sociales",
    ],
    "géographie": [
        "Géographie", "Europe", "Asie", "Afrique", "Amérique_du_Nord",
        "Amérique_du_Sud", "Océanie", "Antarctique", "Océan_Pacifique",
        "Océan_Atlantique", "Océan_Indien", "France", "Allemagne",
        "Royaume-Uni", "Italie", "Espagne", "États-Unis", "Chine",
        "Inde", "Japon", "Brésil", "Russie", "Canada", "Australie",
        "Paris", "Londres", "New_York", "Tokyo", "Montagne",
        "Fleuve", "Lac", "Désert", "Forêt", "Volcan",
        "Climat", "Météorologie", "Cartographie", "GPS",
    ],
    "langue_française": [
        "Français", "Grammaire_française", "Conjugaison", "Orthographe",
        "Syntaxe", "Littérature_française", "Poésie", "Roman_(littérature)",
        "Victor_Hugo", "Molière", "Balzac", "Flaubert", "Zola",
        "Baudelaire", "Rimbaud", "Verlaine", "Proust", "Camus",
        "Voltaire", "Rousseau", "Montesquieu", "Diderot", "Montaigne",
        "Académie_française", "Dictionnaire", "Encyclopédie",
    ],
    # ═══ NOUVEAUX DOMAINES — GÉNÉRALISATION KA PHONE ═══
    "cuisine_gastronomie": [
        "Cuisine_française", "Cuisine_italienne", "Cuisine_japonaise",
        "Cuisine_chinoise", "Cuisine_indienne", "Cuisine_méditerranéenne",
        "Pâtisserie", "Boulangerie", "Fromage", "Vin", "Bière",
        "Café", "Thé", "Chocolat", "Régime_alimentaire",
        "Nutrition", "Gastronomie", "Restaurant", "Recette_de_cuisine",
        "Cuisine_moléculaire", "Art_culinaire", "Sauces", "Épices",
        "Huile_d'olive", "Truffe_(champignon)", "Caviar",
        "Sushi", "Pizza", "Pain", "Croissant_(viennoiserie)",
        "Pomme_de_terre", "Tomate", "Riz", "Blé", "Viande",
        "Poisson_(alimentation)", "Légume", "Fruit_(alimentation)",
        "Herbes_aromatiques", "Alimentation_durable",
    ],
    "sport_loisirs": [
        "Sport", "Football", "Rugby", "Tennis", "Basket-ball",
        "Natation", "Athlétisme", "Cyclisme", "Ski", "Surf",
        "Arts_martiaux", "Judo", "Karaté", "Boxe", "Yoga",
        "Randonnée_pédestre", "Escalade", "Course_à_pied", "Marathon",
        "Jeux_olympiques", "Coupe_du_monde_de_football", "Tour_de_France",
        "Échecs", "Jeu_vidéo", "Jeu_de_société", "Loisir",
        "Jardinage", "Bricolage", "Pêche_(loisir)", "Chasse",
        "Danse", "Théâtre", "Cirque", "Magie_(illusion)",
        "Patinage", "Gymnastique", "Golf", "Formule_1",
        "Voile_(sport)", "Plongée_sous-marine", "Parachutisme",
    ],
    "musique_arts": [
        "Musique", "Musique_classique", "Jazz", "Rock", "Hip-hop",
        "Musique_électronique", "Opéra", "Piano", "Guitare", "Violon",
        "Batterie_(instrument)", "Chant", "Compositeur", "Orchestre",
        "Peinture", "Sculpture", "Photographie", "Cinéma",
        "Architecture", "Littérature", "Bande_dessinée", "Graf",
        "Art_contemporain", "Musée", "Louvre", "Design",
        "Mode_(habillement)", "Haute_couture", "Parfum",
        "Céramique", "Tapisserie", "Vitrail", "Mosaïque",
        "Opéra_Garnier", "Festival_de_Cannes", "Prix_Nobel_de_littérature",
        "Beethoven", "Mozart", "Picasso", "Monet", "Van_Gogh",
        "Léonard_de_Vinci", "Michel-Ange", "Shakespeare",
    ],
    "psychologie_bienetre": [
        "Psychologie", "Psychologie_cognitive", "Psychologie_sociale",
        "Émotion", "Bonheur", "Tristesse", "Peur", "Colère",
        "Amour", "Amitié", "Empathie", "Intelligence_émotionnelle",
        "Sommeil", "Rêve", "Insomnie", "Méditation", "Pleine_conscience",
        "Stress", "Anxiété", "Dépression_(psychiatrie)", "Burn-out",
        "Développement_personnel", "Estime_de_soi", "Motivation",
        "Résilience_(psychologie)", "Deuil", "Solitude",
        "Psychanalyse", "Thérapie_cognitive", "Hypnose",
        "Relation_humaine", "Couple", "Famille", "Parentalité",
        "Communication_non_violente", "Gestalt-thérapie",
        "Psychologie_positive", "Bien-être", "Santé_mentale",
    ],
    "voyage_tourisme": [
        "Tourisme", "Voyage", "Hôtel", "Avion", "Train",
        "Bateau", "Aéroport", "Gare", "Passeport", "Visa_(document)",
        "Paris", "Londres", "New_York", "Tokyo", "Rome",
        "Barcelone", "Bangkok", "Sydney", "Rio_de_Janeiro",
        "Marrakech", "Le_Caire", "Venise", "Amsterdam",
        "Tour_Eiffel", "Grande_Muraille", "Taj_Mahal", "Machu_Picchu",
        "Patrimoine_mondial", "UNESCO", "Guide_touristique",
        "Camping", "Auberge_de_jeunesse", "Croisière",
        "Écotourisme", "Voyage_d'affaires", "Sac_à_dos_(voyage)",
        "Décalage_horaire", "Change_(monnaie)", "Douane",
        "Assurance_voyage", "Itinéraire",
    ],
    "vie_pratique": [
        "Logement", "Immobilier", "Location", "Achat_immobilier",
        "Crédit_immobilier", "Budget", "Impôt", "Déclaration_de_revenus",
        "Assurance", "Banque", "Épargne", "Retraite",
        "Bricolage", "Plomberie", "Électricité", "Peinture_(bâtiment)",
        "Jardinage", "Potager", "Plante_d'intérieur", "Animal_de_compagnie",
        "Chien", "Chat", "Aquarium", "Permis_de_conduire",
        "Voiture", "Code_de_la_route", "Transport_en_commun",
        "Ménage", "Lessive", "Recyclage", "Compostage",
        "Zéro_déchet", "Basse_consommation", "Déménagement",
        "Administration", "Carte_d'identité", "Mairie",
        "École", "Université", "Diplôme",
    ],
    "animaux_nature": [
        "Animal", "Mammifère", "Oiseau", "Reptile", "Poisson",
        "Insecte", "Chien", "Chat", "Cheval", "Vache", "Mouton",
        "Loup", "Ours", "Lion", "Tigre", "Éléphant",
        "Dauphin", "Baleine", "Requin", "Aigle", "Chouette",
        "Serpent", "Grenouille", "Papillon", "Abeille", "Fourmi",
        "Biodiversité", "Écosystème", "Forêt", "Océan", "Rivière",
        "Montagne", "Désert", "Jungle", "Savane", "Corail",
        "Extinction_des_espèces", "Protection_de_la_nature",
        "Parc_national", "Réserve_naturelle", "Jardin_botanique",
    ],
    "economie_finances": [
        "Économie", "Capitalisme", "Socialisme", "Libéralisme",
        "Monnaie", "Euro", "Dollar", "Banque_centrale",
        "Inflation", "Croissance_économique", "Produit_intérieur_brut",
        "Chômage", "Emploi", "Salaire", "SMIC", "Retraite",
        "Bourse_(économie)", "Action_(finance)", "Cryptomonnaie",
        "Bitcoin", "Finance", "Investissement", "Épargne",
        "Crédit", "Dette", "Impôt", "Taxe_sur_la_valeur_ajoutée",
        "Commerce_international", "Mondialisation", "Protectionnisme",
        "Fonds_monétaire_international", "Banque_mondiale",
        "Consommation", "Pouvoir_d'achat", "Inégalités_économiques",
        "Microcrédit", "Économie_collaborative", "Économie_circulaire",
        "Entreprise", "Start-up", "Entrepreneuriat",
    ],
    "education_apprentissage": [
        "Éducation", "École_primaire", "Collège", "Lycée", "Université",
        "Pédagogie", "Apprentissage", "Mémoire_(psychologie)",
        "Lecture", "Écriture", "Mathématiques", "Langue_étrangère",
        "Méthode_Montessori", "Enseignement_à_distance", "MOOC",
        "Diplôme", "Baccalauréat", "Doctorat", "Formation_professionnelle",
        "Alphabétisation", "Illettrisme", "Orthographe", "Grammaire",
        "Langue_française", "Anglais", "Espagnol", "Chinois",
        "Traduction", "Linguistique", "Polyglotte",
        "Neurosciences_cognitives", "Trouble_de_l'apprentissage",
        "Dyslexie", "Précocité_intellectuelle", "Échec_scolaire",
        "Orientation_scolaire", "Reconversion_professionnelle",
    ],
    "egypte_ancienne": [
        "Égypte_antique", "Pharaon", "Pyramide", "Pyramide_de_Khéops",
        "Gizeh", "Sphinx_de_Gizeh", "Momification", "Hiéroglyphe",
        "Mythologie_égyptienne", "Osiris", "Isis", "Horus",
        "Anubis", "Rê", "Thot", "Bastet", "Seth",
        "Livre_des_morts", "Temple_de_Karnak", "Vallée_des_Rois",
        "Toutânkhamon", "Ramsès_II", "Cléopâtre_VII", "Néfertiti",
        "Nil", "Alexandrie", "Le_Caire", "Mastaba",
        "Obélisque", "Scarabée", "Ânkh", "Ouadjet",
        "Egypte_antique_art", "Egypte_antique_musique",
        "Cosmogonie_égyptienne", "Ka_(spiritualité_égyptienne)",
        "Ba_(spiritualité_égyptienne)", "Akh",
        "Maat", "Aménophis_IV", "Époque_ptolémaïque",
    ],
    "pop_culture": [
        "Culture_populaire", "Cinéma", "Série_télévisée",
        "Star_Wars", "Harry_Potter", "Le_Seigneur_des_anneaux",
        "Marvel_Comics", "DC_Comics", "Manga", "Anime",
        "Jeu_vidéo", "PlayStation", "Xbox", "Nintendo",
        "Minecraft", "Fortnite", "League_of_Legends",
        "Réseautage_social", "Facebook", "Instagram", "TikTok",
        "YouTube", "Netflix", "Streaming", "Podcast",
        "Musique_pop", "Taylor_Swift", "Beyoncé", "The_Beatles",
        "Festival_de_musique", "Coachella", "Glastonbury",
        "Bande_dessinée_franco-belge", "Astérix", "Tintin",
        "Science-fiction", "Fantasy", "Horreur_(genre)",
        "Cosplay", "Geek", "Mème_internet", "Influenceur_web",
    ],
}


def telecharger_article_wikipedia(titre: str, langue: str = "fr") -> str:
    """
    Télécharge le contenu texte d'un article Wikipedia.
    Retourne le texte nettoyé (sans markup wiki).
    
    Stratégie de fallback :
    1. Titre exact
    2. Titre sans accents (normalisé ASCII)
    3. Recherche via l'API Wikipedia pour trouver le vrai titre
    """
    def _fetch_page(page_title):
        """Tente de récupérer une page avec un titre donné."""
        url = f"https://{langue}.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "titles": page_title,
            "prop": "extracts",
            "exintro": 0,
            "explaintext": 1,
            "exsectionformat": "plain",
        }
        query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        full_url = f"{url}?{query_string}"
        req = urllib.request.Request(full_url, headers={"User-Agent": "MGH-KA/1.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
        pages = data.get("query", {}).get("pages", {})
        for page_id, page_info in pages.items():
            if "missing" in page_info:
                return None
            texte = page_info.get("extract", "")
            if texte and len(texte) > 200:
                texte = re.sub(r'\n{3,}', '\n\n', texte)
                texte = re.sub(r'={2,}\s*(.*?)\s*={2,}', r'\1.', texte)
                return texte.strip()
        return None
    
    # Essaye 1 : Titre exact
    try:
        result = _fetch_page(titre)
        if result:
            return result
    except Exception:
        pass
    
    # Essaye 2 : Titre avec underscores remplacés par espaces
    try:
        titre_espaces = titre.replace("_", " ")
        if titre_espaces != titre:
            result = _fetch_page(titre_espaces)
            if result:
                return result
    except Exception:
        pass
    
    # Essaye 3 : Normaliser les accents et caractères spéciaux
    try:
        import unicodedata
        # Remplacer les caractères accentués par leur version non accentuée
        titre_ascii = unicodedata.normalize('NFKD', titre).encode('ASCII', 'ignore').decode('ASCII')
        # Remplacer les underscores par des espaces
        titre_ascii = titre_ascii.replace("_", " ")
        if titre_ascii != titre:
            result = _fetch_page(titre_ascii)
            if result:
                return result
    except Exception:
        pass
    
    # Essaye 4 : Recherche Wikipedia pour trouver le vrai titre
    try:
        url = f"https://{langue}.wikipedia.org/w/api.php"
        search_term = titre.replace("_", " ")
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": search_term,
            "srlimit": 3,
            "srwhat": "title",
        }
        query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        full_url = f"{url}?{query_string}"
        req = urllib.request.Request(full_url, headers={"User-Agent": "MGH-KA/1.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
        search_results = data.get("query", {}).get("search", [])
        if search_results:
            # Prendre le premier résultat de recherche
            best_title = search_results[0]["title"]
            result = _fetch_page(best_title)
            if result:
                return result
    except Exception:
        pass
    
    return ""


def ingerer_articles_wikipedia(
    mgh: MGH,
    n_articles: int = 5000,
    langue: str = "fr",
    amplitude: float = 0.4,
):
    """
    Ingère des articles Wikipedia français dans MGH.
    """
    import numpy as np
    total_articles = sum(len(liste) for liste in WIKIPEDIA_ARTICLES.values())
    print(f"\n  {total_articles} articles Wikipedia disponibles")
    print(f"  Objectif : {n_articles} articles")
    
    # Collecter tous les titres, mélangés pour diversité
    all_titles = []
    for domaine, titres in WIKIPEDIA_ARTICLES.items():
        all_titles.extend([(t, domaine) for t in titres])
    
    random.shuffle(all_titles)
    selected = all_titles[:n_articles]
    
    bigrammes_avant = len(mgh.bigram_index)
    total_bigrammes = 0
    articles_ok = 0
    erreurs = 0
    t0 = time.time()
    
    print(f"\n  Début ingestion ({len(selected)} articles)...")
    
    for i, (titre, domaine) in enumerate(selected):
        # Télécharger l'article
        texte = telecharger_article_wikipedia(titre, langue)
        
        if not texte or len(texte) < 200:
            erreurs += 1
            continue
        
        # Ingérer dans MGH
        n = mgh.entrainer_texte(texte, amplitude=amplitude)
        total_bigrammes += n
        articles_ok += 1
        
        # Progression
        if (i + 1) % 50 == 0:
            dt = time.time() - t0
            vitesse = (i + 1) / dt
            eta = (len(selected) - i - 1) / vitesse / 60 if vitesse > 0 else 0
            nouveaux = len(mgh.bigram_index) - bigrammes_avant
            print(f"  [{i+1}/{len(selected)}] {articles_ok} OK, {erreurs} err | "
                  f"+{nouveaux:,} bigrammes | {vitesse:.0f} art/min | "
                  f"ETA: {eta:.0f}min | E={np.sum(np.abs(mgh.H)**2):.0f}")
    
    dt = time.time() - t0
    nouveaux = len(mgh.bigram_index) - bigrammes_avant
    
    print(f"\n  {'='*60}")
    print(f"  INGESTION TERMINÉE")
    print(f"  Articles ingérés : {articles_ok} / {len(selected)}")
    print(f"  Erreurs          : {erreurs}")
    print(f"  Bigrammes ajoutés: {nouveaux:,} (total: {len(mgh.bigram_index):,})")
    print(f"  Vocabulaire      : {len(mgh.vocab)} mots")
    print(f"  Énergie          : {np.sum(np.abs(mgh.H)**2):.0f}")
    print(f"  Durée            : {dt/60:.1f} min")
    print(f"  {'='*60}")
    
    return {
        "articles_ok": articles_ok,
        "erreurs": erreurs,
        "bigrammes_ajoutes": nouveaux,
        "bigrammes_total": len(mgh.bigram_index),
        "vocabulaire": len(mgh.vocab),
    }


def main():
    import numpy as np
    
    parser = argparse.ArgumentParser(description="Ingestion de vrai français dans MGH")
    parser.add_argument("--articles", type=int, default=2000,
                       help="Nombre d'articles Wikipedia à ingérer (défaut: 2000)")
    parser.add_argument("--resume", action="store_true",
                       help="Reprendre l'ingestion sur MGH existant")
    args = parser.parse_args()
    
    print("=" * 70)
    print("INGESTION DE VRAI FRANCAIS - MGH")
    print(f"{args.articles} articles Wikipedia -> bigrammes + trigrammes")
    print("=" * 70)
    
    # Charger MGH existant (avec l'entraînement synthétique 1M)
    mgh = MGH()
    bigrams_avant = len(mgh.bigram_index)
    
    if not args.resume or bigrams_avant == 0:
        print(f"  MGH chargé : {bigrams_avant:,} bigrammes, {len(mgh.vocab)} mots")
    
    # Ingérer les articles
    resultat = ingerer_articles_wikipedia(
        mgh,
        n_articles=args.articles,
        amplitude=0.35  # Amplitude modérée pour ne pas écraser les patterns synthétiques
    )
    
    # Sauvegarde
    print(f"\n  Sauvegarde...")
    mgh._save()
    print(f"  [OK] {MGH_FILE}")
    print(f"  [OK] {BIGRAM_FILE}")
    print(f"\n  MGH peut maintenant etre utilise par KA Phone :")
    print(f"    python ka_phone/ka_phone_server.py --port 8900")


if __name__ == "__main__":
    main()