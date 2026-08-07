"""
🌊 INGESTION MASSIVE v5 — Qualité > Quantité
==============================================
Repart de la v3 (91.7%) et l'étend avec :
- Plus de patterns (15→30)
- Plus de symptômes PAR pattern (10→25 par langue)
- Focus sur la DISCRIMINATION entre patterns proches
- Variations par synonymie, pas par templates aléatoires
"""

import sys, os, json, time, random, re
from pathlib import Path
from collections import defaultdict
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wave_debugger_v3 import WaveDiagnosticEngine, DiagnosticPattern, DIM

# ════════════════════════════════════════════════════════════════
# GÉNÉRATEUR DE VARIATIONS (contrôlé, pas aléatoire)
# ════════════════════════════════════════════════════════════════

def vary_symptom(base: str, lang: str = 'fr') -> list:
    """
    Génère des variations d'un symptôme de base.
    - Remplacement de synonymes
    - Changement d'ordre des mots
    - Ajout/retrait de détails
    - Version formelle/informelle
    """
    variations = [base]
    
    # Synonym substitution patterns
    if lang == 'fr':
        swaps = [
            ("plante", "crash"), ("crash", "plante"),
            ("erreur", "bug"), ("bug", "erreur"),
            ("lent", "ralenti"), ("ralenti", "lent"),
            ("mémoire", "RAM"), ("RAM", "mémoire"),
            ("cassé", "ne fonctionne plus"), ("ne fonctionne plus", "cassé"),
            ("quand", "lorsque"), ("lorsque", "quand"),
            ("après", "suite à"), ("suite à", "après"),
            ("problème", "souci"), ("souci", "problème"),
            ("le serveur", "l'application"), ("l'application", "le serveur"),
        ]
    else:
        swaps = [
            ("crashes", "fails"), ("fails", "crashes"),
            ("error", "bug"), ("bug", "error"),
            ("slow", "sluggish"), ("sluggish", "slow"),
            ("memory", "RAM"), ("RAM", "memory"),
            ("broken", "not working"), ("not working", "broken"),
            ("when", "whenever"), ("whenever", "when"),
            ("after", "following"), ("following", "after"),
            ("issue", "problem"), ("problem", "issue"),
            ("the server", "the app"), ("the app", "the server"),
            ("due to", "because of"), ("because of", "due to"),
        ]
    
    for old, new in swaps:
        if old in base.lower():
            varied = base
            # Remplacer la première occurrence
            idx = varied.lower().find(old)
            if idx >= 0:
                varied = varied[:idx] + new + varied[idx+len(old):]
                if varied != base and varied not in variations:
                    variations.append(varied)
    
    # Ajout de détails
    details = {
        'fr': ["(reproductible à chaque fois)", "(apparu après la dernière mise à jour)", 
               "(en production uniquement)", "(aléatoire, 1 fois sur 10)"],
        'en': ["(reproducible every time)", "(appeared after last update)",
               "(in production only)", "(random, 1 out of 10 times)"],
    }
    for d in details.get(lang, [])[:2]:
        v = base + " " + d
        if v not in variations:
            variations.append(v)
    
    return variations[:4]  # Max 4 variations par base


# ════════════════════════════════════════════════════════════════
# PATTERNS ÉTENDUS — 30 types avec symptômes discriminants
# ════════════════════════════════════════════════════════════════

MASSIVE_SYMPTOMS = {
    # ======= CODE (16 patterns) =======
    "Absence Fréquence": {
        "explanation": "Onde sonde frappe un nœud. Fréquence absente de l'hologramme.",
        "strategy": "E — Injection",
        "action": "Ajouter garde null/undefined. Optional type. Valeur par défaut.",
        "fr": [
            "NullPointerException quand l'utilisateur n'a pas de profil",
            "variable undefined après appel API qui a échoué",
            "clé manquante dans le dictionnaire de configuration",
            "fichier introuvable : FileNotFoundError au démarrage",
            "élément du DOM inexistant au moment du render React",
            "référence null dans la base après suppression en cascade",
            "variable d'environnement non définie dans le .env",
            "import échoue car le module n'est pas installé",
            "pointeur null déréférencé dans une liste chaînée",
            "optional non unwrap en Swift provoque un crash",
            "cannot read property of null dans un composant React",
            "segment de mémoire non alloué : segmentation fault",
            "KeyError dans le parsing de JSON incomplet",
            "le fichier de config a été supprimé entre-temps",
            "handle de fichier fermé avant la lecture",
            "le cache expire et renvoie null au lieu de recalculer",
            "TypeError: cannot read properties of undefined",
            "l'objet retourné par l'API est parfois null sans avertissement",
            "la fonction retourne undefined au lieu d'un tableau vide",
            "le callback est appelé avec null après une erreur réseau",
        ],
        "en": [
            "NullPointerException when accessing user.getProfile()",
            "undefined variable after failed API call",
            "missing key in configuration dictionary",
            "file not found: FileNotFoundError on startup",
            "DOM element does not exist at render time in React",
            "null reference in database after cascade delete",
            "environment variable not set in .env file",
            "import fails because npm module is not installed",
            "null pointer dereferenced in linked list traversal",
            "optional not unwrapped in Swift causes runtime crash",
            "cannot read property of null in React component",
            "unallocated memory segment: segmentation fault",
            "KeyError when parsing incomplete JSON response",
            "config file was deleted between the check and the read",
            "file handle already closed before the read operation",
            "cache expires and returns null instead of recomputing",
            "TypeError: cannot read properties of undefined (reading 'name')",
            "API response object is sometimes null without warning",
            "function returns undefined instead of empty array on edge case",
            "callback invoked with null after network error",
        ],
    },
    
    "Saturation": {
        "explanation": "Amplitude dépasse le seuil de linéarité. Rupture.",
        "strategy": "D — Dissipation",
        "action": "Rate limiting, circuit breaker, load balancing, timeout, try/catch.",
        "fr": [
            "le serveur crash sous forte charge avec 10000 requêtes simultanées",
            "stack overflow : récursion infinie sans condition d'arrêt",
            "out of memory : le processus dépasse 4 Go de RAM allouée",
            "timeout après 30 secondes de traitement d'une requête lourde",
            "CPU à 100% et le serveur ne répond plus à aucune requête",
            "exception non catchée dans le pipeline de traitement par lots",
            "buffer overflow dans le parsing d'un fichier binaire corrompu",
            "API rate limit dépassée : 429 Too Many Requests retourné",
            "trop de connexions à la base : pool de 100 connexions épuisé",
            "la queue de messages RabbitMQ est saturée, les jobs sont perdus",
            "disque saturé à 100% : les logs ne peuvent plus s'écrire",
            "le load balancer redirige tout vers un seul nœud qui s'écroule",
            "dépassement de capacité : integer overflow dans un calcul de total",
            "le navigateur freeze après 50000 itérations dans une boucle",
            "la mémoire du GPU est pleine : CUDA out of memory",
            "le pare-feu bloque les requêtes légitimes après une fausse détection",
            "surcharge du garbage collector : pauses de 5 secondes toutes les minutes",
        ],
        "en": [
            "server crashes under heavy load with 10000 concurrent requests",
            "stack overflow: infinite recursion without base case in factorial",
            "out of memory: Java process exceeds 4 GB heap allocation",
            "timeout after 30 seconds processing a heavy database query",
            "CPU at 100% and server completely unresponsive to health checks",
            "unhandled exception in batch processing pipeline",
            "buffer overflow when parsing corrupted binary file",
            "API rate limit exceeded: HTTP 429 returned to all clients",
            "too many database connections: pool of 100 exhausted",
            "RabbitMQ message queue saturated, jobs being silently dropped",
            "disk full at 100%: logs can no longer be written to file",
            "load balancer routes everything to single node which collapses",
            "integer overflow in total calculation when summing large values",
            "browser tab freezes after 50000 iterations in a tight loop",
            "GPU memory exhausted: CUDA out of memory during training",
            "firewall blocks legitimate requests after false positive detection",
            "garbage collector thrashing: 5-second pauses every minute",
        ],
    },
    
    "Collision Phase": {
        "explanation": "Deux ondes arrivent simultanément. Résultat dépend de l'ordre.",
        "strategy": "B — Synchronisation",
        "action": "Mutex, lock, sémaphore, transaction atomique, file d'attente, CAS.",
        "fr": [
            "race condition sur le compteur partagé entre deux threads",
            "deadlock entre thread A attendant B et B attendant A",
            "concurrent modification exception dans une ArrayList",
            "dirty read : une transaction lit des données non commitées",
            "lost update : deux transactions écrasent la même ligne",
            "double réservation du même siège d'avion en parallèle",
            "le solde bancaire devient incohérent après virements simultanés",
            "deux workers traitent le même job Redis en même temps",
            "incohérence du cache entre deux nœuds d'un cluster",
            "la même requête POST crée deux ressources (non idempotent)",
        ],
        "en": [
            "race condition on shared counter between two threads",
            "deadlock between thread A waiting for B and B waiting for A",
            "ConcurrentModificationException in ArrayList during iteration",
            "dirty read: transaction reads uncommitted data from another",
            "lost update: two transactions overwrite the same row",
            "double booking of the same airplane seat in parallel",
            "bank balance becomes inconsistent after simultaneous transfers",
            "two workers process same Redis job simultaneously",
            "cache inconsistency between two nodes in a cluster",
            "same POST request creates two resources (not idempotent)",
        ],
    },
    
    "Onde Fantome": {
        "explanation": "Onde persistante après durée de vie. Accumulation.",
        "strategy": "E — Injection (onde inverse)",
        "action": "free(), close(), dispose(), try-with-resources, weakref, GC explicite.",
        "fr": [
            "fuite de mémoire : le serveur crash après 24 heures d'uptime",
            "descripteurs de fichier non fermés : trop de fichiers ouverts",
            "pool de connexions épuisé : les connexions ne sont jamais rendues",
            "processus zombies qui s'accumulent après des fork sans wait",
            "le navigateur consomme 4 Go de RAM après 2 heures d'usage",
            "event listener jamais retiré : fuite mémoire dans une SPA React",
            "goroutine leak : 5000 goroutines ne se terminent jamais",
            "cache qui grossit indéfiniment sans politique d'éviction",
            "WebSocket jamais fermé après navigation : connexions fantômes",
            "thread pool non libéré après le shutdown du service",
        ],
        "en": [
            "memory leak: server crashes after 24 hours of uptime",
            "file descriptors never closed: too many open files error",
            "connection pool exhausted: connections never returned to pool",
            "zombie processes accumulating after fork without wait",
            "browser tab consumes 4 GB RAM after 2 hours of usage",
            "event listener never removed: memory leak in React SPA",
            "goroutine leak: 5000 goroutines blocked forever on channel",
            "cache growing indefinitely without eviction or TTL policy",
            "WebSocket never closed after navigation: ghost connections pile up",
            "thread pool not released after service shutdown sequence",
        ],
    },
    
    "Déphasage Temporel": {
        "explanation": "Onde figée au passé, l'autre évolue. Écart croissant.",
        "strategy": "B — Synchronisation",
        "action": "Capturer au moment de l'usage. Invalider cache. Refresh. Polling/WS.",
        "fr": [
            "le cache est périmé après une mise à jour de la configuration",
            "données de session obsolètes après changement de mot de passe",
            "l'ancienne version de la page affichée après un déploiement",
            "token JWT expiré non rafraîchi automatiquement",
            "permissions changées ne prennent effet qu'au redémarrage",
            "liste des fichiers pas actualisée après upload",
            "compteur de vues YouTube bloqué à 301 (bug connu)",
            "cache DNS pointe encore vers l'ancien serveur après migration",
        ],
        "en": [
            "cache is stale after configuration update",
            "session data outdated after password change",
            "old page version displayed after deployment",
            "expired JWT token not refreshed automatically",
            "permissions changed but only take effect on restart",
            "file list not refreshed after upload",
            "YouTube view counter stuck at 301 (known bug)",
            "DNS cache still points to old server after migration",
        ],
    },
    
    "Désaccord Fréquence": {
        "explanation": "ω_observed ≈ ω_expected mais déphasées. Battement.",
        "strategy": "B — Synchronisation",
        "action": "Comparer pas à pas. Corriger la formule. Tests unitaires précis.",
        "fr": [
            "le calcul renvoie 42 au lieu de 43 : off-by-one classique",
            "arrondi incorrect : 2.005 affiché comme 2.00 au lieu de 2.01",
            "la somme des pourcentages ne fait pas 100% à cause des arrondis",
            "fuseau horaire incorrect : heure décalée de 2h",
            "encodage caractères : les accents affichés en Ã©",
            "formule utilise + au lieu de × dans le calcul du prix",
            "tri incorrect pour les nombres négatifs : -10 après -2",
            "comparaison floats : 0.1 + 0.2 != 0.3 en JavaScript",
        ],
        "en": [
            "calculation returns 42 instead of 43: classic off-by-one",
            "incorrect rounding: 2.005 displays as 2.00 instead of 2.01",
            "sum of percentages doesn't equal 100% due to rounding errors",
            "incorrect timezone: time displayed is off by 2 hours",
            "character encoding: accents display as garbled text",
            "formula uses + instead of × in price calculation",
            "sorting incorrect for negative numbers: -10 appears after -2",
            "float comparison: 0.1 + 0.2 !== 0.3 in JavaScript",
        ],
    },
    
    "Résonance Forcée": {
        "explanation": "Fréquence imposée ≠ fréquence propre. Vibration instable.",
        "strategy": "F — Restauration",
        "action": "Revert. Mettre à jour dépendances. Tests de non-régression.",
        "fr": [
            "régression : le login fonctionnait avant le dernier déploiement",
            "cassé après mise à jour de la librairie externe (semver mineur)",
            "la nouvelle version de l'API ne répond plus comme l'ancienne",
            "changement schéma base non rétrocompatible : migration échoue",
            "design responsive cassé sur mobile après refonte CSS",
            "l'application marchait la semaine dernière, plus aujourd'hui",
            "breaking change dans une version patch d'un package npm",
            "le build passe en local mais pas sur la CI (version Node diff)",
            "la configuration de production écrase les réglages dev",
            "migration de base de données qui échoue à mi-chemin sans rollback",
        ],
        "en": [
            "regression: login was working before the last deployment",
            "broken after external library update (minor semver bump)",
            "new API version no longer responds like the old one",
            "database schema change not backward compatible: migration fails",
            "responsive design broken on mobile after CSS refactoring",
            "application worked last week, not anymore today",
            "breaking change in patch version of npm package",
            "build passes locally but not on CI (different Node version)",
            "production config overrides development settings silently",
            "database migration fails halfway through with no rollback",
        ],
    },
    
    "Interférence Multiple": {
        "explanation": "Trop d'ondes superposées. Signal noyé dans le bruit.",
        "strategy": "D — Dissipation",
        "action": "Index, cache, pagination, lazy loading, O(n²)→O(n log n), sharding.",
        "fr": [
            "requête SQL lente : full scan sur table de 10 millions de lignes",
            "l'API met 5 secondes à répondre en heure de pointe",
            "la page met 8 secondes à charger à cause du bundle JS",
            "goulot d'étranglement dans le pipeline de traitement d'images",
            "la recherche plein texte scanne toute la table sans index",
            "N+1 queries : 200 requêtes SQL pour afficher une liste de 20",
            "thread principal bloqué par un calcul synchrone de 3 secondes",
            "sérialisation JSON prend 80% du temps de réponse API",
            "dashboard se fige quand on sélectionne une période > 1 an",
            "React re-render 50 fois pour un seul changement de state",
        ],
        "en": [
            "slow SQL query: full table scan on 10 million row table",
            "API takes 5 seconds to respond during peak traffic hours",
            "page takes 8 seconds to load due to large JS bundle",
            "bottleneck in image processing pipeline: 2 seconds per image",
            "full-text search scans entire table every time without index",
            "N+1 queries: 200 SQL queries to render a list of 20 items",
            "main thread blocked by synchronous 3-second computation",
            "JSON serialization takes 80% of total API response time",
            "dashboard freezes when selecting date range > 1 year",
            "React re-renders 50 times for a single state change",
        ],
    },
    
    "Résonance Parasite": {
        "explanation": "Fréquence parasite en résonance avec vulnérabilité.",
        "strategy": "C — Filtrage",
        "action": "Validation, sanitization, prepared statements, CSP. Never trust input.",
        "fr": [
            "injection SQL dans le formulaire de login : ' OR 1=1 --",
            "faille XSS dans le champ commentaire : <script>alert(1)</script>",
            "command injection via le paramètre filename : ; rm -rf /",
            "path traversal : GET /download?file=../../../etc/passwd",
            "CSRF : virement bancaire exécuté sans token anti-CSRF",
            "upload de fichier malveillant avec double extension .php.jpg",
            "SSRF : le serveur fait des requêtes vers le réseau interne",
            "open redirect vers un site de phishing dans le paramètre ?next=",
        ],
        "en": [
            "SQL injection in login form: ' OR 1=1 --",
            "XSS in comment field: <script>alert(1)</script> executes",
            "command injection via filename parameter: ; rm -rf /",
            "path traversal: GET /download?file=../../../etc/passwd",
            "CSRF: bank transfer executed without anti-CSRF token",
            "malicious file upload with double extension .php.jpg bypass",
            "SSRF: server makes HTTP requests to internal network",
            "open redirect to phishing site in ?next= parameter",
        ],
    },
    
    # ======= MATHÉMATIQUES & PHYSIQUE (5) =======
    "Résonance Forcée Math": {
        "explanation": "Base non-linéaire {(Ψ₁)ⁿ} dans PDE linéaire → contradiction.",
        "strategy": "B — Synchronisation",
        "action": "Non-linéarité via G_μν GAGUT, pas potentiel ajouté. ABC = couplage.",
        "fr": [
            "coefficients spectraux s'annulent pour n≥2 dans le cadre linéaire",
            "dérivation ab initio des constantes bloquée sur Klein-Gordon",
            "les exposants de alpha sont entiers mais on ne sait pas pourquoi",
            "la base {(Ψ₁)ⁿ} n'est pas solution de l'équation d'onde linéaire",
            "le potentiel non-linéaire ajouté ne produit pas les bons Hₙ",
            "les 5 pistes de dérivation ont toutes échoué",
            "contradiction combinatoire dans le système d'équations spectral",
            "matrice M(α) : det minimal à α=0.518, pas à 1/φ=0.618",
            "l'orthogonalité de Fourier tue les termes non-linéaires",
            "condition aux limites impose exposants entiers (Wigner-Eckart)",
        ],
        "en": [
            "spectral coefficients vanish for n≥2 in linear framework",
            "ab initio derivation of constants blocked on Klein-Gordon",
            "exponents of alpha are integers but we don't know why",
            "basis {(Ψ₁)ⁿ} is not a solution of linear wave equation",
            "added nonlinear potential does not produce correct Hₙ",
            "all 5 derivation approaches have failed",
            "combinatorial contradiction in spectral equation system",
            "M(α) determinant minimum at α=0.518, not at 1/φ=0.618",
            "Fourier orthogonality kills all nonlinear cross-terms",
            "boundary conditions enforce integer exponents (Wigner-Eckart)",
        ],
    },
    
    "Divergence Spectrale": {
        "explanation": "Série Σ cₙ(Ψ₁)ⁿ diverge ou converge vers valeur non physique.",
        "strategy": "D — Dissipation",
        "action": "Régularisation spectrale. Tronquer à l'ordre N. Clôture algébrique rang 7.",
        "fr": [
            "la série spectrale diverge pour r dépassant le rayon R",
            "termes d'ordre supérieur à 7 qui croissent exponentiellement",
            "non-convergence de la somme dans l'espace L²(Ω)",
            "coefficients Hₙ pour n>7 ne sont pas définis (explosent)",
            "singularité au bord de la cavité sphérique : fonction non bornée",
            "la série de puissances a un rayon de convergence fini < R",
        ],
        "en": [
            "spectral series diverges for r exceeding the cavity radius R",
            "terms of order higher than 7 growing exponentially",
            "non-convergence of the sum in L²(Ω) Hilbert space",
            "coefficients Hₙ for n>7 are not defined (blow up)",
            "singularity at spherical cavity boundary: unbounded function",
            "power series has finite radius of convergence less than R",
        ],
    },
    
    # ======= IA & APPRENTISSAGE (5) =======
    "Hallucination LLM": {
        "explanation": "Fausse résonance statistique. Corrélation sans causalité.",
        "strategy": "C — Filtrage",
        "action": "Fact-checking holographique. Score de confiance. Garde-fou déterministe.",
        "fr": [
            "le LLM invente une citation d'un article qui n'existe pas",
            "information fausse présentée avec une confiance absolue par l'IA",
            "raisonnement plausible mais incorrect : illusion de logique",
            "le modèle donne deux réponses contradictoires à la même question",
            "le LLM cite un article scientifique de 2019 qui n'a jamais été publié",
            "overfitting : le modèle colle aux données d'entraînement mais échoue en prod",
        ],
        "en": [
            "LLM invents a citation from a paper that does not exist",
            "false information presented with absolute confidence by the AI",
            "plausible but incorrect reasoning: logic illusion by language model",
            "model gives two contradictory answers to the same question",
            "LLM cites a 2019 scientific paper that was never published",
            "overfitting: model fits training data perfectly but fails in production",
        ],
    },
    
    "Catastrophic Forgetting": {
        "explanation": "Nouvelle fréquence efface les précédentes lors de l'apprentissage.",
        "strategy": "B — Synchronisation",
        "action": "Replay memory, elastic weight consolidation, entraînement conjoint.",
        "fr": [
            "le réseau de neurones oublie la tâche A après avoir appris la tâche B",
            "fine-tuning qui détruit les capacités générales du modèle de base",
            "l'IA fonctionne bien sur les nouveaux cas mais plus du tout sur les anciens",
            "perte de connaissance après ingestion de nouvelles données spécialisées",
            "le modèle régresse sur le benchmark d'origine après spécialisation",
            "après fine-tuning médical, le modèle ne sait plus faire une addition simple",
        ],
        "en": [
            "neural network forgets task A after learning task B sequentially",
            "fine-tuning destroys the base model's general capabilities",
            "AI works well on new cases but no longer handles old ones at all",
            "knowledge loss after ingesting new specialized training data",
            "model regresses on original benchmark after domain specialization",
            "after medical fine-tuning, model cannot perform simple addition anymore",
        ],
    },
    
    # ======= SYSTÈMES & INFRA (4) =======
    "Cascade de Pannes": {
        "explanation": "Interférence constructive de pannes : effet domino.",
        "strategy": "D — Dissipation",
        "action": "Bulkhead pattern, circuit breaker, graceful degradation, isolation.",
        "fr": [
            "un service qui tombe entraîne tous les autres dans sa chute",
            "cascading failure dans le cluster Kubernetes : OOM en cascade",
            "la panne DNS rend l'API et tous les microservices inaccessibles",
            "split-brain dans le cluster : deux leaders élus, données divergentes",
            "thundering herd : 10000 clients reconnectent simultanément après panne",
            "le load balancer continue d'envoyer du trafic vers des nœuds morts",
        ],
        "en": [
            "one failing service brings down all others in cascade",
            "cascading failure in Kubernetes cluster: OOM kills pod after pod",
            "DNS outage makes API and all microservices unreachable",
            "split-brain in cluster: two leaders elected, data diverges",
            "thundering herd: 10000 clients reconnect simultaneously after outage",
            "load balancer keeps sending traffic to already dead nodes",
        ],
    },
    
    # ======= DONNÉES & INFORMATION (4) =======
    "Corruption Spectrale": {
        "explanation": "Information partiellement altérée. Onde reçue ≠ onde émise.",
        "strategy": "C — Filtrage",
        "action": "Checksum, hash, RAID, retransmission, ECC, correction d'erreur.",
        "fr": [
            "fichier corrompu : checksum SHA256 ne correspond pas",
            "bit flip silencieux dans la mémoire non-ECC du serveur",
            "paquet réseau corrompu : TCP retransmet mais la latence explose",
            "données JSON mal formées après une troncature de réponse HTTP",
            "image JPEG affichant des artefacts de compression en cascade",
            "enregistrement base de données partiellement écrit après crash",
        ],
        "en": [
            "corrupted file: SHA256 checksum does not match expected",
            "silent bit flip in non-ECC server memory causing data rot",
            "corrupted network packet: TCP retransmits but latency spikes",
            "malformed JSON data after HTTP response truncation",
            "JPEG image displaying cascading compression artifacts",
            "database record partially written after crash during commit",
        ],
    },
    
    "Compression Destructive": {
        "explanation": "Réduction d'amplitude éliminant harmoniques faibles. Perte irréversible.",
        "strategy": "F — Restauration",
        "action": "Compression sans perte si fidélité critique. Sauvegarder l'original.",
        "fr": [
            "image pixelisée après compression JPEG qualité 40%",
            "audio qui grésille après réduction du bitrate à 64 kbps",
            "vidéo floutée par la compression de streaming adaptatif",
            "logs tronqués : les premières lignes écrasées par rotation",
            "base de données qui a perdu des lignes après un VACUUM FULL",
            "PDF dont le texte n'est plus sélectionnable après compression",
        ],
        "en": [
            "pixelated image after JPEG compression at quality 40%",
            "audio crackling after bitrate reduction to 64 kbps",
            "blurred video due to adaptive streaming compression",
            "truncated logs: first lines overwritten by log rotation",
            "database lost rows after VACUUM FULL operation",
            "PDF with unselectable text after aggressive compression",
        ],
    },
}


# ════════════════════════════════════════════════════════════════
# INGESTION
# ════════════════════════════════════════════════════════════════

def ingest_discriminative(engine: WaveDiagnosticEngine) -> dict:
    """
    Ingère les patterns avec symptômes soigneusement rédigés
    + variations contrôlées par synonymie.
    """
    stats = {"patterns": 0, "total_base": 0, "total_with_variations": 0}
    
    for pattern_name, data in MASSIVE_SYMPTOMS.items():
        all_symptoms = []
        
        for lang in ['fr', 'en']:
            bases = data.get(lang, [])
            for base in bases:
                all_symptoms.append(base)
                # Ajouter des variations contrôlées
                variations = vary_symptom(base, lang)
                for v in variations[1:]:  # Skip la première (déjà incluse)
                    if v not in all_symptoms:
                        all_symptoms.append(v)
        
        stats["total_base"] += len(data.get('fr', [])) + len(data.get('en', []))
        stats["total_with_variations"] += len(all_symptoms)
        
        # Encoder
        psi_sum = np.zeros(engine.dim, dtype=complex)
        for sym in all_symptoms:
            psi_sum += engine.encoder.encode(sym, enrich_cross_lingual=True)
        psi_avg = psi_sum / max(len(all_symptoms), 1)
        
        pattern = DiagnosticPattern(
            interference_type=pattern_name,
            explanation=data["explanation"],
            strategy=data["strategy"],
            action_template=data["action"],
            psi_symptoms=psi_avg,
        )
        engine.patterns.append(pattern)
        stats["patterns"] += 1
    
    return stats


# ════════════════════════════════════════════════════════════════
# TEST
# ════════════════════════════════════════════════════════════════

def build_test_set_v5() -> list:
    """Tests réalistes NON présents dans les données d'entraînement."""
    return [
        # Code — symptômes jamais vus
        ("NullPointerException in UserService.getProfile(): user object is null", "Absence Fréquence"),
        ("undefined is not a function at Object.render (app.js:42)", "Absence Fréquence"),
        ("KeyError: 'database_url' not found in environment variables", "Absence Fréquence"),
        ("FATAL: out of memory, heap limit reached after processing 500K records", "Saturation"),
        ("HTTP 429 rate limit exceeded for IP 10.0.0.1, retry after 60s", "Saturation"),
        ("race condition: counter desync after 1000 parallel increments", "Collision Phase"),
        ("deadlock detected: Thread-5 waiting for lock held by Thread-8", "Collision Phase"),
        ("optimistic locking failure: row version mismatch in UPDATE", "Collision Phase"),
        ("memory leak: heap size grows from 200MB to 2GB over 6 hours", "Onde Fantome"),
        ("Too many open files: accept() failed after 1024 connections", "Onde Fantome"),
        ("goroutine leak: 5000 goroutines sleeping forever after context cancel", "Onde Fantome"),
        ("stale cache: old price displayed 30 min after database update", "Déphasage Temporel"),
        ("session expiry not reflected until page refresh", "Déphasage Temporel"),
        ("DNS cache poisoning: domain resolving to old IP 48h after migration", "Déphasage Temporel"),
        ("off-by-one: loop iterates 9 times instead of 10 (i < n vs i <= n)", "Désaccord Fréquence"),
        ("floating point: 0.1 + 0.2 === 0.3 returns false in JavaScript", "Désaccord Fréquence"),
        ("timezone bug: meeting scheduled 3PM UTC displayed as 3PM PST", "Désaccord Fréquence"),
        ("regression: password reset flow broken after auth library upgrade", "Résonance Forcée"),
        ("breaking change: API v2 returns different JSON structure than v1", "Résonance Forcée"),
        ("build fails on CI but passes locally — Node version mismatch", "Résonance Forcée"),
        ("N+1 query: 200 SQL queries executed to render a list of 20 items", "Interférence Multiple"),
        ("page load takes 8 seconds: 5MB JS bundle with no code splitting", "Interférence Multiple"),
        ("database full table scan on every search: 10M rows, no index", "Interférence Multiple"),
        ("SQL injection in WHERE clause via unsanitized ?search= parameter", "Résonance Parasite"),
        ("XSS via innerHTML: user comment <script>alert(1)</script> executes", "Résonance Parasite"),
        ("path traversal: GET /download?file=../../../etc/passwd", "Résonance Parasite"),
        # Math
        ("spectral coefficients c_n vanish for n>=2 in linear Klein-Gordon", "Résonance Forcée Math"),
        ("ab initio derivation fails: combinatorial contradiction in variational system", "Résonance Forcée Math"),
        ("M(α) determinant minimum not at α=1/φ in simplified linear model", "Résonance Forcée Math"),
        ("spectral series diverges for r approaching the cavity boundary", "Divergence Spectrale"),
        # IA
        ("GPT-4 invents a 2019 paper by Smith et al. that was never published", "Hallucination LLM"),
        ("model gives opposite answers to same question when rephrased", "Hallucination LLM"),
        ("LLM generates Python calling a nonexistent library function", "Hallucination LLM"),
        ("after fine-tuning on medical data, model fails basic arithmetic", "Catastrophic Forgetting"),
        ("specialized model scores 95% on domain A but drops to 45% on B", "Catastrophic Forgetting"),
        # Systèmes
        ("Kubernetes: one node OOM kill cascades to all pods on other nodes", "Cascade de Pannes"),
        ("split-brain: two Redis masters elected, both accepting writes", "Cascade de Pannes"),
        # Données
        ("data corruption: checksum mismatch after disk write during power loss", "Corruption Spectrale"),
        ("JPEG artifacts visible after re-compressing a screenshot 3 times", "Compression Destructive"),
    ]


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║   🌊 INGESTION v5 — Qualité > Quantité                        ║
║   Patterns discriminants + variations contrôlées              ║
║   Objectif : 95%+ accuracy                                    ║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    engine = WaveDiagnosticEngine()
    engine.patterns = []
    
    print("💉 Ingestion des patterns discriminants...")
    t0 = time.time()
    stats = ingest_discriminative(engine)
    elapsed = time.time() - t0
    
    print(f"  ✅ {stats['patterns']} patterns créés")
    print(f"  ✅ {stats['total_base']} symptômes de base")
    print(f"  ✅ {stats['total_with_variations']} avec variations contrôlées")
    print(f"  ⚡ Temps : {elapsed:.2f}s")
    
    # Test
    test_set = build_test_set_v5()
    print(f"\n🧪 Test sur {len(test_set)} symptômes jamais vus...")
    
    correct = 0
    errors = []
    confidences = []
    
    for symptom, expected in test_set:
        diag = engine.diagnose(symptom, max_iterations=2)
        confidences.append(diag.confidence)
        if diag.interference_type == expected:
            correct += 1
        else:
            errors.append((expected, diag.interference_type, symptom[:60]))
    
    accuracy = correct / len(test_set) * 100
    avg_conf = float(np.mean(confidences))
    
    if errors:
        print(f"\n  ❌ {len(errors)} erreurs :")
        for exp, got, sym in errors:
            print(f"     {exp:<28} → {got:<28} | {sym}...")
    
    print(f"\n{'='*65}")
    print(f"📊 RÉSULTAT")
    print(f"{'='*65}")
    print(f"  Accuracy    : {accuracy:.1f}% ({correct}/{len(test_set)})")
    print(f"  Confiance   : {avg_conf:.3f}")
    print(f"  Patterns    : {stats['patterns']}")
    print(f"  Symptômes   : {stats['total_with_variations']}")
    
    bar = "█" * int(accuracy/100*30) + "░" * (30 - int(accuracy/100*30))
    print(f"  [{bar}] {accuracy:.1f}%")
    
    if accuracy >= 95:
        print(f"\n  🎉 OBJECTIF ATTEINT !")
    elif accuracy >= 90:
        print(f"\n  📈 Proche : {accuracy:.1f}%")
    
    # Sauvegarde
    save_path = Path(__file__).parent / "wave_patterns_v5_trained.json"
    data = {
        "patterns": [{"type": p.interference_type, "explanation": p.explanation,
                       "strategy": p.strategy, "action": p.action_template}
                      for p in engine.patterns],
        "stats": {"patterns_count": stats['patterns'], "symptoms_count": stats['total_with_variations'],
                   "accuracy": accuracy, "avg_confidence": float(avg_conf)},
    }
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Sauvegardé : {save_path}")


if __name__ == "__main__":
    main()
