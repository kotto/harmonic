#!/usr/bin/env python3
"""
enterprise_onboard.py — Onboarding des entreprises (KA Enterprise)
===================================================================

L'entreprise décrit SON environnement (secteur + description) → l'analyse
extrait les domaines d'activité → des HOLOGRAMMES (départements) sont
proposés et créés avec un seed web initial. L'entreprise héberge le tout
sur son VPS (voir deploy_vps.sh) et enrichit ensuite par ingestion de
documents.

Principes :
  - MAPPING SECTEUR → DOMAINES : chaque secteur d'activité (santé,
    juridique, finance...) définit les hologrammes canoniques.
  - DÉTECTION PAR MOTS-CLÉS : la description libre est scannée contre
    les mots-clés de chaque secteur — les domaines réellement présents
    dans l'environnement décrit sont proposés (max 5).
  - SEED WEB INITIAL : chaque département créé reçoit un contenu initial
    depuis Wikipedia (l'équivalent Enterprise du seed web direct) —
    l'entreprise peut immédiatement poser des questions avant même
    d'ingérer ses documents.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# MAPPING SECTEUR → HOLOGRAMMES CANONIQUES
# (sujet_du_département, description_courte)
# ═══════════════════════════════════════════════════════════════════════════════

ENVIRONMENT_DOMAINS: Dict[str, Dict] = {
    'sante': {
        'label': 'Santé & Médical',
        'keywords': ['clinique', 'hopital', 'hospitalier', 'sante', 'santé',
                     'medical', 'médical', 'cabinet medical', 'pharmacie',
                     'medecine', 'médecine', 'patient', 'patients', 'soin',
                     'soins', 'sante publique', 'santé publique', 'hospice',
                     'laboratoire', 'biologie medicale'],
        'holograms': [
            ('medecine clinique', 'diagnostics, pathologies et protocoles'),
            ('pharmacologie', 'medicaments, posologies et interactions'),
            ('gestion etablissement de sante', 'administration hospitaliere'),
        ],
    },
    'juridique': {
        'label': 'Droit & Juridique',
        'keywords': ['droit', 'avocat', 'avocats', 'juridique', 'cabinet',
                     'notaire', 'notaires', 'legal', 'légal', 'contentieux',
                     'conformite', 'conformité', 'reglementation',
                     'réglementation', 'contrats', 'justice', 'procédure',
                     'procedure'],
        'holograms': [
            ('droit des affaires', 'societes, fusions et fiscalite'),
            ('droit du travail', 'contrats de travail et litiges'),
            ('conformite reglementaire', 'reglementations et audits'),
        ],
    },
    'finance': {
        'label': 'Finance & Assurance',
        'keywords': ['banque', 'bancaire', 'finance', 'financier', 'assurance',
                     'assurances', 'comptabilite', 'comptabilité', 'tresorerie',
                     'trésorerie', 'credit', 'crédit', 'investissement',
                     'gestion de patrimoine', 'actuariat', 'bourse'],
        'holograms': [
            ('finance d entreprise', 'tresorerie, budget et investissement'),
            ('comptabilite', 'normes comptables et reporting'),
            ('gestion des risques', 'risques financiers et assurances'),
        ],
    },
    'informatique': {
        'label': 'Informatique & Tech',
        'keywords': ['informatique', 'logiciel', 'logiciels', 'developpement',
                     'développement', 'it', 'cybersecurite', 'cybersécurité',
                     'securite informatique', 'sécurité informatique',
                     'donnees', 'données', 'cloud', 'data', 'intelligence',
                     'artificielle', 'réseau', 'reseau', 'devops', 'saas'],
        'holograms': [
            ('informatique', 'systemes, reseaux et logiciels'),
            ('cybersecurite', 'menaces, protection et conformite'),
            ('donnees et intelligence artificielle', 'data, modeles et gouvernance'),
        ],
    },
    'industrie': {
        'label': 'Industrie & Production',
        'keywords': ['industrie', 'industriel', 'production', 'manufacture',
                     'manufacturier', 'usine', 'qualite', 'qualité',
                     'maintenance', 'logistique', 'approvisionnement',
                     'supply chain', 'fabrication', 'atelier', 'chantier',
                     'bâtiment', 'batiment', 'travaux'],
        'holograms': [
            ('production industrielle', 'processus et cadences'),
            ('qualite et normes', 'controle qualite et certifications'),
            ('maintenance industrielle', 'preventive et curative'),
        ],
    },
    'rh': {
        'label': 'Ressources Humaines',
        'keywords': ['ressources humaines', 'rh', 'recrutement', 'paie',
                     'formation', 'employes', 'employés', 'salaries',
                     'salariés', 'carriere', 'carrière', 'gestion des talents',
                     'management', 'organigramme'],
        'holograms': [
            ('ressources humaines', 'administration du personnel'),
            ('recrutement', 'processus et entretiens'),
            ('formation professionnelle', 'parcours et competences'),
        ],
    },
    'commerce': {
        'label': 'Commerce & Distribution',
        'keywords': ['commerce', 'vente', 'ventes', 'e-commerce', 'ecommerce',
                     'distribution', 'marketing', 'clients', 'retail',
                     'boutique', 'magasin', 'catalogue', 'stock', 'fidélité',
                     'fidelite'],
        'holograms': [
            ('commerce et distribution', 'canaux et operationnel'),
            ('marketing', 'strategies et campagnes'),
            ('service client', 'relation et satisfaction'),
        ],
    },
    'education': {
        'label': 'Éducation & Formation',
        'keywords': ['ecole', 'école', 'formation', 'education', 'éducation',
                     'universite', 'université', 'enseignement', 'pedagogie',
                     'pédagogie', 'apprentissage', 'etudiants', 'étudiants',
                     'lycee', 'lycée', 'college', 'collège', 'cursus'],
        'holograms': [
            ('formation professionnelle', 'parcours et referentiels'),
            ('pedagogie', 'methodes et outils'),
        ],
    },
    'energie': {
        'label': 'Énergie & Environnement',
        'keywords': ['energie', 'énergie', 'electricite', 'électricité',
                     'gaz', 'renouvelable', 'solaire', 'eolien', 'éolien',
                     'environnement', 'climat', 'carbone', 'developpement durable',
                     'développement durable', 'dechets', 'déchets', 'eau'],
        'holograms': [
            ('energies renouvelables', 'solaire, eolien et stockage'),
            ('environnement et climat', 'reglementation et transitions'),
        ],
    },
    'agriculture': {
        'label': 'Agriculture & Agroalimentaire',
        'keywords': ['agriculture', 'agricole', 'ferme', 'elevage', 'élevage',
                     'agroalimentaire', 'cultures', 'viticulture', 'exploitation',
                     'agronomie', 'recolte', 'récolte', 'semences'],
        'holograms': [
            ('agronomie', 'cultures et sols'),
            ('elevage', 'especes et bien-etre animal'),
        ],
    },
    'transport': {
        'label': 'Transport & Logistique',
        'keywords': ['transport', 'transports', 'logistique', 'flotte',
                     'livraison', 'expedition', 'expédition', 'fret',
                     'maritime', 'aérien', 'aerien', 'routier', 'entrepot',
                     'entrepôt', 'derniere', 'dernière'],
        'holograms': [
            ('logistique', 'entrepots et flux'),
            ('transport de marchandises', 'fret et reglementation'),
        ],
    },
    'immobilier': {
        'label': 'Immobilier & Construction',
        'keywords': ['immobilier', 'immobiliere', 'immobilière', 'logement',
                     'locatif', 'bail', 'baux', 'promotion immobiliere',
                     'promotion immobilière', 'gestion locative', 'foncier',
                     'hypotheque', 'hypothèque'],
        'holograms': [
            ('immobilier', 'transactions et valorisation'),
            ('gestion locative', 'baux et entretien'),
        ],
    },
}

# Secteurs non reconnus → hologrammes génériques
GENERIC_HOLOGRAMS = [
    ('activites de l entreprise', 'operations courantes'),
    ('cadre reglementaire', 'reglementations applicables'),
    ('gestion interne', 'processus et organisation'),
]

# ═══════════════════════════════════════════════════════════════════════════════
# CORPUS HORS-LIGNE — fallback du seed web
# Chaque hologramme canonique reçoit un contenu initial immédiatement
# opérationnel (3-4 faits courts), utilisé quand le réseau est indisponible.
# L'entreprise peut donc poser ses premières questions dès la création,
# même sans connexion au moment de l'installation sur le VPS.
# ═══════════════════════════════════════════════════════════════════════════════

SEED_CORPUS: Dict[str, str] = {
    'medecine clinique': (
        "La medecine clinique repose sur l'examen du patient, l'anamnese et les examens complementaires pour etablir un diagnostic. "
        "Le diagnostic clinique s'appuie sur les signes fonctionnels rapportes par le patient et les signes physiques observes. "
        "La demarche clinique suit un raisonnement hypothetico-deductif : hypotheses, tests, validation ou rejet. "
        "Le dossier medical doit consigner chaque observation et chaque decision therapeutique pour garantir la continuite des soins."),
    'pharmacologie': (
        "La pharmacologie etudie l'action des medicaments sur l'organisme, de leur absorption a leur elimination. "
        "La posologie depend de l'age, du poids, de la fonction renale et hepatique du patient. "
        "Les interactions medicamenteuses peuvent modifier l'efficacite ou la securite d'un traitement. "
        "La dispensation pharmaceutique exige la verification des contre-indications et des allergies declarees."),
    'gestion etablissement de sante': (
        "La gestion d'un etablissement de sante couvre le budget, le personnel soignant et les parcours de soins. "
        "L'administration hospitaliere assure la coordination entre services, urgences et consultations. "
        "Les indicateurs de qualite hospitaliers mesurent la securite des soins et la satisfaction des patients. "
        "La tarification a l'activite finance les etablissements selon les sejours realises et les actes effectues."),
    'droit des affaires': (
        "Le droit des affaires encadre la creation de societes, leurs statuts et leur fonctionnement. "
        "Les fusions et acquisitions sont soumises a des obligations d'information et de publicite legale. "
        "Le droit fiscal des entreprises regit l'imposition des resultats et la TVA. "
        "Les contrats commerciaux doivent mentionner l'objet, le prix et les conditions de resolution des litiges."),
    'droit du travail': (
        "Le contrat de travail fixe la duree, la remuneration et les conditions d'emploi du salarie. "
        "Le licenciement doit reposer sur un motif reel et serieux, avec une procedure contradictoire. "
        "Les litiges individuels du travail relevent du conseil de prud'hommes. "
        "La duree legale du travail est de 35 heures hebdomadaires, modulable par accord collectif."),
    'conformite reglementaire': (
        "La conformite reglementaire consiste a respecter les lois, reglements et normes applicables a l'activite. "
        "Les programmes de conformite reposent sur une cartographie des risques et des controles periodiques. "
        "Les obligations de vigilance portent sur l'anti-blanchiment, la protection des donnees et la lutte contre la corruption. "
        "Les audits de conformite produisent des rapports documentes et des plans d'action correctifs."),
    'finance d entreprise': (
        "La gestion de tresorerie assure la solvabilite de l'entreprise a court terme. "
        "Le budget de l'entreprise fixe les objectifs de recettes et de depenses par service. "
        "L'investissement est evalue par la valeur actuelle nette et le taux de rentabilite interne. "
        "Les indicateurs financiers cles sont le fonds de roulement, le besoin en fonds de roulement et la trésorerie nette."),
    'comptabilite': (
        "La comptabilite enregistre chronologiquement toutes les operations de l'entreprise. "
        "Les normes comptables internationales IFRS encadrent la presentation des etats financiers. "
        "Le bilan presente l'actif et le passif, le compte de resultat mesure la performance. "
        "Le reporting financier est produit mensuellement, trimestriellement et annuellement."),
    'gestion des risques': (
        "La gestion des risques identifie, evalue et traite les menaces pesant sur l'entreprise. "
        "Les risques financiers incluent le risque de credit, de liquidite et de marche. "
        "L'assurance transfere le risque a un tiers moyennant une prime calculee sur la probabilite du sinistre. "
        "La cartographie des risques classe les menaces par probabilite et impact."),
    'informatique': (
        "L'informatique d'entreprise gere les systemes, les reseaux et les logiciels de production. "
        "L'infrastructure repose sur les serveurs, le stockage et la virtualisation. "
        "Les bonnes pratiques devops automatisent le deploiement et la surveillance des applications. "
        "La sauvegarde reguliere des donnees et le plan de reprise d'activite garantissent la continuite."),
    'cybersecurite': (
        "La cybersecurite protege les systemes d'information contre les attaques et les fuites. "
        "Les menaces courantes sont le phishing, les rançongiciels et les attaques par deni de service. "
        "L'authentification multi-facteurs et la segmentation des reseaux reduisent la surface d'attaque. "
        "La conformite exige la declaration des incidents de securite sous 72 heures."),
    'donnees et intelligence artificielle': (
        "La gouvernance des donnees definit qui peut acceder a quelles donnees et dans quel but. "
        "Un modele d'intelligence artificielle est entraine sur des donnees de qualite et valide sur des donnees de test. "
        "Le RGPD encadre la collecte, le stockage et le traitement des donnees personnelles. "
        "Les decisions algorithmiques doivent etre explicables et auditables."),
    'production industrielle': (
        "La production industrielle organise la transformation des matieres premieres en produits finis. "
        "Les methodes lean visent a eliminer les gaspillages et a fluidifier les flux. "
        "Le suivi des cadences mesure l'efficacite des chaines de fabrication. "
        "La planification de production equilibre la demande et la capacite des machines."),
    'qualite et normes': (
        "Le controle qualite verifie la conformite des produits aux specifications. "
        "La norme ISO 9001 structure le systeme de management de la qualite. "
        "Les certifications exigent des audits internes et externes periodiques. "
        "Les non-conformites sont traitees par des actions correctives et preventives."),
    'maintenance industrielle': (
        "La maintenance preventive planifie les interventions avant la panne. "
        "La maintenance curative repare les equipements apres la defaillance. "
        "La maintenance predictive utilise les capteurs pour anticiper les pannes. "
        "Le taux de disponibilite mesure le temps de fonctionnement des machines."),
    'ressources humaines': (
        "La gestion des ressources humaines administre les contrats, la paie et les carrières. "
        "Le dossier du salarie conserve les documents legaux et les entretiens annuels. "
        "La paie integre le salaire de base, les primes, les cotisations et l'impot sur le revenu. "
        "Les entretiens professionnels orientent le developpement des competences."),
    'recrutement': (
        "Le recrutement commence par la definition du poste et du profil recherche. "
        "Les annonces decrivent les missions, les competences requises et les conditions. "
        "L'entretien structure evalue les competences techniques et comportementales. "
        "L'integration du nouvel arrivant se planifie des la signature du contrat."),
    'formation professionnelle': (
        "La formation professionnelle developpe les competences des salaries tout au long de la carriere. "
        "Le plan de formation de l'entreprise repond aux besoins identifies par les managers. "
        "Les referentiels de competences decrivent les savoir-faire attendus par poste. "
        "La validation des acquis de l'experience permet de reconnaitre les competences sans diplome."),
    'commerce et distribution': (
        "La distribution organise l'acheminement des produits du fabricant au consommateur. "
        "Les canaux de vente incluent le magasin, le web et les places de marche. "
        "La gestion des stocks equilibre la disponibilite et le cout de detention. "
        "Le taux de service mesure la part des demandes clients satisfaites."),
    'marketing': (
        "Le marketing etudie les besoins des clients pour definir l'offre et sa communication. "
        "Les campagnes multi-canaux combinent reseaux sociaux, email et publicite. "
        "La segmentation decoupe le marche en groupes de clients aux attentes homogenes. "
        "Les indicateurs cles sont le taux de conversion et le cout d'acquisition client."),
    'service client': (
        "Le service client traite les demandes, reclamations et retours des clients. "
        "La satisfaction client se mesure par le net promoter score et les enquetes. "
        "Les delais de reponse et de resolution sont les indicateurs de performance principaux. "
        "Une reclamation bien traitee renforce la fidelite du client."),
    'pedagogie': (
        "La pedagogie choisit les methodes et outils qui favorisent l'apprentissage. "
        "La pedagogie active implique l'apprenant par des projets et des mises en situation. "
        "L'evaluation mesure les acquis par des controles continus et finaux. "
        "La differenciation adapte les parcours au niveau de chaque apprenant."),
    'energies renouvelables': (
        "L'energie solaire photovoltaique convertit la lumiere du soleil en electricite. "
        "L'energie eolienne utilise le vent pour faire tourner des turbines electriques. "
        "Le stockage par batteries lisse la production intermittente des renouvelables. "
        "Les objectifs climatiques europeens visent la neutralite carbone en 2050."),
    'environnement et climat': (
        "Le changement climatique resulte de l'augmentation des gaz a effet de serre. "
        "Les reglementations environnementales encadrent les emissions, les dechets et l'eau. "
        "Le bilan carbone mesure les emissions directes et indirectes d'une organisation. "
        "Les transitions energetique et ecologique transforment les modeles de production."),
    'agronomie': (
        "L'agronomie etudie les interactions entre les cultures, les sols et le climat. "
        "La rotation des cultures preserve la fertilite des sols et limite les maladies. "
        "L'irrigation doit etre raisonnee pour economiser l'eau. "
        "Les intrants agricoles (engrais, traitements) sont reglementes et doses."),
    'elevage': (
        "L'elevage regroupe les especes bovines, ovines, porcines, avicoles et aquacoles. "
        "Le bien-etre animal impose des conditions d'hebergement, d'alimentation et de soins. "
        "La tracabilite des animaux garantit la securite sanitaire de la chaine alimentaire. "
        "Les normes d'elevage exigent la declaration des exploitations et le suivi veterinaire."),
    'logistique': (
        "La logistique gere les flux de marchandises entre les fournisseurs et les clients. "
        "L'entreposage organise la reception, le stockage et la preparation des commandes. "
        "Les indicateurs cles sont le taux de rupture, le delai de livraison et le cout de transport. "
        "Les systemes de gestion d'entrepot pilotent les operations en temps reel."),
    'transport de marchandises': (
        "Le transport de marchandises combine les modes routier, ferroviaire, maritime et aerien. "
        "Le fret routier est reglemente par les temps de conduite et les licences de transport. "
        "La lettre de voiture documente le contrat de transport et la marchandise. "
        "Les douanes controlent les echanges internationaux et percoivent les droits."),
    'immobilier': (
        "L'immobilier recouvre la transaction, la valorisation et la gestion des biens. "
        "La valeur d'un bien depend de sa localisation, de sa surface et de son etat. "
        "Le compromis de vente engage l'acheteur et le vendeur sous conditions suspensives. "
        "La loi encadre les diagnostics obligatoires avant la vente d'un bien."),
    'gestion locative': (
        "La gestion locative administre les baux, les loyers et l'entretien des biens loues. "
        "Le bail definit la duree, le loyer, le depot de garantie et les obligations des parties. "
        "Le proprietaire doit realiser les travaux d'entretien et de mise en conformite. "
        "La procedure d'expulsion est encadree par des delais legaux stricts."),
    'activites de l entreprise': (
        "Les activites de l'entreprise couvrent la production, la vente et l'administration. "
        "Chaque service dispose de processus documentes et d'indicateurs de performance. "
        "La qualite des operations garantit la satisfaction des clients et des partenaires. "
        "L'entreprise doit respecter les obligations legales, fiscales et sociales."),
    'cadre reglementaire': (
        "Le cadre reglementaire de l'entreprise comprend les codes, les lois et les decrets. "
        "Les obligations declaatives varient selon l'activite et la taille de l'entreprise. "
        "La veille reglementaire identifie les evolutions des textes applicables. "
        "Le non-respect des reglementations expose a des sanctions administratives et penales."),
    'gestion interne': (
        "La gestion interne organise les processus, les roles et la prise de decision. "
        "Les procedures documentees standardisent les operations recurrentes. "
        "Le controle de gestion suit les ecarts entre le budget et le reel. "
        "La communication interne assure la circulation de l'information entre les services."),
}


def _corpus_fallback(sujet: str) -> str:
    """Texte hors-ligne de secours pour un hologramme, si le seed web échoue."""
    return SEED_CORPUS.get(sujet.lower().strip(), '')


def _score_domain(description: str, domain_cfg: Dict) -> int:
    d = description.lower()
    return sum(1 for kw in domain_cfg['keywords'] if kw in d)


def analyze_environment(description: str,
                        secteur: Optional[str] = None,
                        max_domains: int = 5) -> Dict:
    """
    Analyse la description de l'environnement → domaines détectés avec
    leurs hologrammes proposés.

    Returns:
        {'secteurs': [{secteur, label, score, holograms: [(sujet, desc)...]}],
         'recommandation': 'description'}
    """
    description = (description or '').strip()
    if secteur:
        # Le secteur déclaré compte fort (x3)
        cfg = ENVIRONMENT_DOMAINS.get(secteur.lower())
        if cfg:
            description = description + ' ' + ' '.join(cfg['keywords'])

    scored = []
    for key, cfg in ENVIRONMENT_DOMAINS.items():
        score = _score_domain(description, cfg)
        bonus = 3 if secteur and secteur.lower() == key else 0
        if score + bonus > 0:
            scored.append((score + bonus, key, cfg))

    scored.sort(key=lambda x: -x[0])
    top = scored[:max_domains]

    if not top:
        return {'secteurs': [], 'recommandation': 'general',
                'message': 'Aucun secteur reconnu — hologrammes génériques proposés.'}

    result = []
    for score, key, cfg in top:
        result.append({
            'secteur': key,
            'label': cfg['label'],
            'score': score,
            'holograms': [{'sujet': s, 'description': d}
                          for s, d in cfg['holograms']],
        })
    return {'secteurs': result, 'recommandation': top[0][1]}


def create_environment(engine, name: str, email: str,
                       description: str, secteur: Optional[str] = None,
                       max_domains: int = 5,
                       holograms: Optional[List[str]] = None) -> Dict:
    """
    Crée l'environnement complet : tenant + départements (hologrammes)
    avec seed initial.

    holograms : liste optionnelle des sujets à créer (filtrés sur la
    proposition d'analyse) — si vide, tous les hologrammes proposés sont
    créés.

    Returns:
        {'tenant': {...}, 'departments': [...], 'secteurs': [...]}
    """
    analysis = analyze_environment(description, secteur, max_domains)

    # Filtre des hologrammes choisis par l'entreprise (insensible à la casse)
    wanted = None
    if holograms:
        wanted = {h.strip().lower() for h in holograms if h and h.strip()}

    # 1. Tenant
    try:
        tenant = engine.create_tenant(name, email)
    except Exception as e:
        return {'error': f'Création du tenant: {e}'}

    # 2. Départements + seed
    departments = []
    sectors = analysis.get('secteurs', [])
    if not sectors:
        sectors = [{'secteur': 'general', 'label': 'Général',
                    'holograms': GENERIC_HOLOGRAMS}]

    for sec in sectors:
        for h in sec['holograms']:
            sujet = h['sujet']
            desc = h['description']
            if wanted is not None and sujet.lower() not in wanted:
                continue
            try:
                dept = engine.create_department(tenant.id, sujet)
                seeded = _seed_department(engine, dept.id, sujet, desc)
                departments.append({
                    'id': dept.id,
                    'sujet': sujet,
                    'description': desc,
                    'secteur': sec['secteur'],
                    'facts': dept.fact_count,
                    'seeded': seeded,
                    'couverture': _department_coverage(engine, dept.id, sujet),
                })
            except Exception as e:
                log.error(f"⚠ Département {sujet}: {e}")
                continue

    return {
        'tenant': {'id': tenant.id, 'name': tenant.name},
        'departments': departments,
        'secteurs': [{'secteur': s['secteur'], 'label': s['label']}
                     for s in sectors],
    }


def _department_coverage(engine, department_id: str, sujet: str) -> Dict:
    """Couverture par facettes du département (holo prêt à répondre ?)."""
    try:
        from facet_coverage import coverage_texts
        facts = engine.facts.get(department_id, [])
        texts = [f.text for f in facts]
        if not texts:
            return {'couverture': 0.0, 'manquantes': []}
        cov = coverage_texts(texts, sujet)
        return {'couverture': cov.get('couverture', 0.0),
                'manquantes': cov.get('manquantes', [])}
    except Exception:
        return {'couverture': 0.0, 'manquantes': []}


def _seed_department(engine, department_id: str, sujet: str,
                     description: str, lang: str = 'fr') -> bool:
    """
    Seed initial : Wikipedia sur le sujet → ingest_text ; si le réseau est
    indisponible (ou le sujet introuvable), fallback sur le corpus
    hors-ligne. L'entreprise peut poser des questions immédiatement.
    """
    text = None
    try:
        from enterprise_completion import wikipedia_text
        text = wikipedia_text(sujet, lang)
    except Exception:
        text = None

    if not text or len(text) < 150:
        # 🌐 Réseau indisponible → corpus hors-ligne (toujours disponible)
        text = _corpus_fallback(sujet)
        source = 'corpus_hors_ligne'
    else:
        source = 'wikipedia'

    if not text:
        return False
    try:
        engine.ingest_text(department_id, text)
        log.info(f"🌱 Seed « {sujet} » [{source}]: {len(text)} chars ingérés")
        return True
    except Exception as e:
        log.warning(f"⚠ Seed « {sujet} »: {e}")
        return False


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # Test d'analyse
    for desc in [
        "Nous sommes une clinique privée avec un service de pharmacie et des laboratoires d'analyses",
        "Cabinet d'avocats spécialisé en droit des affaires et conformité réglementaire",
        "Nous développons des logiciels SaaS et gérons l'infrastructure cloud de nos clients",
    ]:
        res = analyze_environment(desc)
        print(f"\n=== {desc[:50]}...")
        for s in res['secteurs']:
            print(f"  [{s['secteur']} (score {s['score']})] {s['label']}")
            for h in s['holograms']:
                print(f"      🧠 {h['sujet']} — {h['description']}")
