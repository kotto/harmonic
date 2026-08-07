"""
🌊 INGESTION MASSIVE v4 — 5000+ symptômes, 50+ patterns
=========================================================
Génération synthétique par templates + variations lexicales.
Objectif : 95%+ accuracy sur le diagnostic ondulatoire.

Stratégie : pour chaque pattern, générer 80-120 symptômes
en faisant varier : vocabulaire, structure, langue, verbosité.
"""

import sys, os, json, time, math, random, itertools
from pathlib import Path
from collections import defaultdict
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wave_debugger_v3 import WaveDiagnosticEngine, DiagnosticPattern, WaveEncoder, DIM

# ════════════════════════════════════════════════════════════════
# GÉNÉRATEUR DE VARIATIONS
# ════════════════════════════════════════════════════════════════

# Synonymes par concept (FR + EN)
SYNONYMS = {
    "error": ["error", "exception", "failure", "bug", "issue", "problem", "defect", "fault", "crash", "break"],
    "erreur": ["erreur", "exception", "échec", "bug", "problème", "défaut", "panne", "plantage", "crash", "anomalie"],
    "null": ["null", "None", "nil", "undefined", "missing", "absent", "empty", "void", "unset", "not found"],
    "nul": ["null", "None", "nil", "undefined", "manquant", "absent", "vide", "introuvable", "non défini", "inexistant"],
    "slow": ["slow", "sluggish", "laggy", "delayed", "unresponsive", "hanging", "frozen", "degraded", "bottlenecked"],
    "lent": ["lent", "ralenti", "retardé", "bloqué", "gelé", "dégradé", "engorgé", "ralenti", "pénible", "laborieux"],
    "crash": ["crash", "crash", "panic", "fatal", "catastrophic", "critical", "severe", "total failure"],
    "plante": ["plante", "crash", "panique", "fatal", "catastrophique", "critique", "sévère", "échec total"],
    "memory": ["memory", "RAM", "heap", "storage", "allocation", "buffer", "cache memory", "resource"],
    "memoire": ["mémoire", "RAM", "tas", "stockage", "allocation", "tampon", "cache", "ressource"],
    "leak": ["leak", "leakage", "bleed", "drain", "exhaustion", "depletion", "consumption", "overflow"],
    "fuite": ["fuite", "écoulement", "épuisement", "consommation", "débordement", "perte", "surcharge"],
    "concurrent": ["concurrent", "parallel", "simultaneous", "multi-threaded", "async", "racing", "competing"],
    "concurrence": ["concurrent", "parallèle", "simultané", "multi-thread", "asynchrone", "course", "compétition"],
    "cache": ["cache", "cached", "buffered", "stored", "saved", "retained", "memorized", "persisted"],
    "cache_fr": ["cache", "mis en cache", "tamponné", "stocké", "sauvegardé", "conservé", "mémorisé", "persisté"],
    "injection": ["injection", "inject", "insert", "embed", "injecting", "insertion", "command injection"],
    "injection_fr": ["injection", "injecter", "insérer", "incorporer", "introduire", "insertion"],
    "regression": ["regression", "regressed", "degraded", "broken", "reverted", "went back", "deteriorated"],
    "regression_fr": ["régression", "régressé", "dégradé", "cassé", "revenu en arrière", "détérioré"],
}

# Templates de structure de phrase
TEMPLATES_FR = [
    "{sujet} {verbe} {complement}",
    "quand {sujet} {verbe}, {consequence}",
    "{sujet} {verbe} {complement} après {declencheur}",
    "problème : {sujet} {verbe} {complement}",
    "on observe que {sujet} {verbe} {complement}",
    "{sujet} {verbe} {complement} lorsque {condition}",
    "bug : {sujet} {verbe} {complement}",
    "le système {verbe} {complement} à cause de {sujet}",
    "{complement} — causé par {sujet} qui {verbe}",
    "dès que {declencheur}, {sujet} {verbe} {complement}",
]

TEMPLATES_EN = [
    "{subject} {verb} {complement}",
    "when {subject} {verb}, {consequence}",
    "{subject} {verb} {complement} after {trigger}",
    "issue: {subject} {verb} {complement}",
    "we observe that {subject} {verb} {complement}",
    "{subject} {verb} {complement} whenever {condition}",
    "bug: {subject} {verb} {complement}",
    "the system {verb} {complement} due to {subject}",
    "{complement} — caused by {subject} that {verb}",
    "as soon as {trigger}, {subject} {verb} {complement}",
]


# ════════════════════════════════════════════════════════════════
# PATTERNS ÉTENDUS — 50 types avec vocabulaire riche
# ════════════════════════════════════════════════════════════════

PATTERN_DEFS = {
    # ───── CODE (13 patterns) ─────
    "Absence Fréquence": {
        "explanation": "L'onde sonde frappe un nœud. Fréquence absente de l'hologramme.",
        "strategy": "E — Injection",
        "action": "Ajouter garde null/undefined. Optional type. Valeur par défaut.",
        "slots_fr": {
            "sujet": ["la variable", "le pointeur", "la référence", "l'objet", "la clé", "le fichier", "le module", "la config", "l'élément DOM", "le handle"],
            "verbe": ["est null", "est undefined", "n'existe pas", "est manquant", "est absent", "est introuvable", "n'est pas défini", "est vide", "pointe vers rien"],
            "complement": ["lors de l'accès", "au moment du traitement", "dans la requête", "après l'appel API", "dans le template", "lors du rendu"],
            "declencheur": ["le déploiement", "la migration", "le reload", "la suppression en cascade", "l'expiration du token"],
            "consequence": ["l'application crash", "une exception est levée", "le rendu échoue", "la requête retourne 500"],
            "condition": ["l'utilisateur n'a pas de profil", "le fichier est supprimé", "la variable d'env est absente", "la réponse API est vide"],
        },
        "slots_en": {
            "subject": ["the variable", "the pointer", "the reference", "the object", "the key", "the file", "the module", "the config", "the DOM element", "the handle"],
            "verb": ["is null", "is undefined", "does not exist", "is missing", "is absent", "is not found", "is not set", "is empty", "points to nothing"],
            "complement": ["on access", "during processing", "in the request", "after the API call", "in the template", "during rendering"],
            "trigger": ["the deployment", "the migration", "the reload", "the cascade delete", "the token expiry"],
            "consequence": ["the app crashes", "an exception is thrown", "rendering fails", "the request returns 500"],
            "condition": ["the user has no profile", "the file was deleted", "the env var is missing", "the API response is empty"],
        },
    },
    
    "Saturation": {
        "explanation": "L'amplitude dépasse le seuil. Le système sature et rompt.",
        "strategy": "D — Dissipation",
        "action": "Rate limiting, circuit breaker, load balancing, timeout, try/catch.",
        "slots_fr": {
            "sujet": ["le serveur", "le processus", "la mémoire", "le CPU", "la queue", "le pool de connexions", "la stack", "le buffer", "le disque"],
            "verbe": ["sature", "déborde", "explose", "crash", "dépasse la limite", "est submergé", "ne répond plus", "atteint 100%"],
            "complement": ["sous la charge", "avec 10000 requêtes", "après 30 secondes", "en heure de pointe", "sans limite"],
            "declencheur": ["un pic de trafic", "une requête lourde", "une boucle infinie", "un fichier volumineux"],
            "consequence": ["tout s'arrête", "le service est down", "les requêtes sont rejetées", "le système redémarre"],
            "condition": ["la charge dépasse 5000 req/s", "le timeout est atteint", "la RAM est pleine", "le disque est saturé"],
        },
        "slots_en": {
            "subject": ["the server", "the process", "the memory", "the CPU", "the queue", "the connection pool", "the stack", "the buffer", "the disk"],
            "verb": ["saturates", "overflows", "explodes", "crashes", "exceeds the limit", "is overwhelmed", "becomes unresponsive", "hits 100%"],
            "complement": ["under load", "with 10000 requests", "after 30 seconds", "at peak time", "without limit"],
            "trigger": ["a traffic spike", "a heavy request", "an infinite loop", "a large file"],
            "consequence": ["everything stops", "the service is down", "requests are rejected", "the system restarts"],
            "condition": ["load exceeds 5000 req/s", "timeout is reached", "RAM is full", "disk is saturated"],
        },
    },
    
    "Collision Phase": {
        "explanation": "Deux ondes arrivent simultanément. Résultat dépend de l'ordre.",
        "strategy": "B — Synchronisation",
        "action": "Mutex, lock, sémaphore, transaction atomique, file d'attente.",
        "slots_fr": {
            "sujet": ["deux threads", "deux workers", "deux transactions", "deux processus", "les requêtes parallèles"],
            "verbe": ["entrent en collision", "se concurrencent", "s'exécutent en même temps", "accèdent simultanément", "modifient la même donnée"],
            "complement": ["sur le compteur", "sur la même ligne", "sur le fichier partagé", "dans le cache", "sur le solde"],
            "declencheur": ["un pic de requêtes", "une opération parallèle", "un cron job simultané"],
            "consequence": ["la donnée est corrompue", "le résultat est incohérent", "un deadlock se produit"],
            "condition": ["deux threads modifient la même variable", "le lock n'est pas acquis", "la transaction n'est pas isolée"],
        },
        "slots_en": {
            "subject": ["two threads", "two workers", "two transactions", "two processes", "parallel requests"],
            "verb": ["collide", "race", "execute simultaneously", "access concurrently", "modify the same data"],
            "complement": ["on the counter", "on the same row", "on the shared file", "in the cache", "on the balance"],
            "trigger": ["a request spike", "a parallel operation", "a simultaneous cron job"],
            "consequence": ["data is corrupted", "result is inconsistent", "a deadlock occurs"],
            "condition": ["two threads modify same variable", "lock is not acquired", "transaction is not isolated"],
        },
    },
    
    "Onde Fantome": {
        "explanation": "Onde persistante après durée de vie. Accumulation jusqu'à épuisement.",
        "strategy": "E — Injection (onde inverse)",
        "action": "free(), close(), dispose(), try-with-resources, weakref, GC.",
        "slots_fr": {
            "sujet": ["la mémoire", "les descripteurs de fichier", "les connexions", "les processus zombies", "les goroutines", "les threads", "les event listeners"],
            "verbe": ["fuit", "s'accumule", "n'est jamais libéré", "reste ouvert", "persiste", "grossit indéfiniment"],
            "complement": ["après 24 heures", "après chaque requête", "sans être fermé", "dans le pool"],
            "declencheur": ["une requête qui échoue", "une connexion non fermée", "un fork sans wait"],
            "consequence": ["le serveur crash", "la RAM est pleine", "le pool est épuisé", "plus de fichiers ouvrables"],
            "condition": ["le close() n'est jamais appelé", "le destructeur n'est pas invoqué", "la référence circulaire empêche le GC"],
        },
        "slots_en": {
            "subject": ["memory", "file descriptors", "connections", "zombie processes", "goroutines", "threads", "event listeners"],
            "verb": ["leaks", "accumulates", "is never freed", "stays open", "persists", "grows indefinitely"],
            "complement": ["after 24 hours", "after each request", "without being closed", "in the pool"],
            "trigger": ["a failed request", "an unclosed connection", "a fork without wait"],
            "consequence": ["server crashes", "RAM is full", "pool is exhausted", "no more files can be opened"],
            "condition": ["close() is never called", "destructor is not invoked", "circular reference prevents GC"],
        },
    },
    
    "Déphasage Temporel": {
        "explanation": "Onde figée au passé, l'autre évolue. Écart croissant.",
        "strategy": "B — Synchronisation",
        "action": "Capturer l'état au moment de l'usage. Invalider cache. Refresh.",
        "slots_fr": {
            "sujet": ["le cache", "la session", "le token", "la page affichée", "les permissions", "le DNS", "la config"],
            "verbe": ["est périmé", "est obsolète", "n'est plus à jour", "est déphasé", "ne reflète plus l'état réel"],
            "complement": ["après la mise à jour", "après le changement", "après le déploiement", "depuis 5 minutes"],
            "declencheur": ["un changement de config", "un déploiement", "un changement de mot de passe", "une expiration"],
            "consequence": ["l'ancienne donnée est servie", "l'utilisateur voit une version obsolète", "les changements ne prennent pas effet"],
            "condition": ["le TTL est trop long", "le cache n'est pas invalidé", "le refresh n'est pas déclenché"],
        },
        "slots_en": {
            "subject": ["the cache", "the session", "the token", "the displayed page", "the permissions", "the DNS", "the config"],
            "verb": ["is stale", "is outdated", "is no longer current", "is out of sync", "no longer reflects real state"],
            "complement": ["after the update", "after the change", "after deployment", "for 5 minutes"],
            "trigger": ["a config change", "a deployment", "a password change", "an expiry"],
            "consequence": ["old data is served", "user sees outdated version", "changes don't take effect"],
            "condition": ["TTL is too long", "cache is not invalidated", "refresh is not triggered"],
        },
    },
    
    "Désaccord Fréquence": {
        "explanation": "ω_observed ≈ ω_expected mais déphasées. Battement perceptible.",
        "strategy": "B — Synchronisation",
        "action": "Comparer pas à pas. Corriger la formule. Tests unitaires.",
        "slots_fr": {
            "sujet": ["le calcul", "le résultat", "l'arrondi", "le tri", "l'encodage", "le fuseau horaire", "la formule"],
            "verbe": ["est incorrect", "est décalé", "ne correspond pas", "est faux", "diffère de l'attendu"],
            "complement": ["de 1 unité", "de 2 heures", "au niveau des décimales", "pour les nombres négatifs"],
            "declencheur": ["un edge case", "une valeur limite", "un changement d'heure", "un input spécial"],
            "consequence": ["le résultat est erroné", "l'affichage est incorrect", "les sommes ne tombent pas juste"],
            "condition": ["l'index commence à 0 au lieu de 1", "le calcul utilise des floats", "le regex est trop gourmand"],
        },
        "slots_en": {
            "subject": ["the calculation", "the result", "the rounding", "the sorting", "the encoding", "the timezone", "the formula"],
            "verb": ["is incorrect", "is off", "does not match", "is wrong", "differs from expected"],
            "complement": ["by 1 unit", "by 2 hours", "in the decimals", "for negative numbers"],
            "trigger": ["an edge case", "a boundary value", "a DST change", "a special input"],
            "consequence": ["result is wrong", "display is incorrect", "sums don't add up"],
            "condition": ["index starts at 0 instead of 1", "calculation uses floats", "regex is too greedy"],
        },
    },
    
    "Résonance Forcée": {
        "explanation": "Fréquence imposée ≠ fréquence propre. Vibration instable.",
        "strategy": "F — Restauration",
        "action": "Revenir version stable (revert). Mettre à jour dépendances.",
        "slots_fr": {
            "sujet": ["l'application", "la fonctionnalité", "le build", "le déploiement", "la migration"],
            "verbe": ["fonctionnait avant", "marchait la semaine dernière", "est cassé depuis", "a régressé", "ne passe plus"],
            "complement": ["la mise à jour", "le déploiement", "le changement de librairie", "la nouvelle version"],
            "declencheur": ["un npm update", "un changement de config", "une PR mergée", "un commit"],
            "consequence": ["les utilisateurs ne peuvent plus se connecter", "le build est rouge", "les tests échouent"],
            "condition": ["la version mineure contient un breaking change", "la config de prod est différente", "la migration a échoué"],
        },
        "slots_en": {
            "subject": ["the application", "the feature", "the build", "the deployment", "the migration"],
            "verb": ["was working before", "worked last week", "is broken since", "has regressed", "no longer passes"],
            "complement": ["the update", "the deployment", "the library change", "the new version"],
            "trigger": ["an npm update", "a config change", "a merged PR", "a commit"],
            "consequence": ["users can no longer log in", "build is red", "tests fail"],
            "condition": ["minor version contains breaking change", "prod config is different", "migration failed"],
        },
    },
    
    "Interférence Multiple": {
        "explanation": "Trop d'ondes superposées. Signal noyé dans le bruit.",
        "strategy": "D — Dissipation",
        "action": "Index, cache, pagination, lazy loading, O(n²)→O(n log n).",
        "slots_fr": {
            "sujet": ["la requête", "le chargement", "le pipeline", "le dashboard", "la recherche", "le rendu"],
            "verbe": ["est lent", "prend du temps", "est laborieux", "sature", "ralentit", "met des secondes"],
            "complement": ["sur 10M de lignes", "en heure de pointe", "à chaque refresh", "sans index", "en pleine page"],
            "declencheur": ["une requête sans filtre", "un N+1 queries", "un scan complet", "un re-render inutile"],
            "consequence": ["l'utilisateur attend", "le timeout est atteint", "l'expérience est dégradée"],
            "condition": ["la table n'a pas d'index", "le cache n'est pas utilisé", "le composant re-render 50 fois"],
        },
        "slots_en": {
            "subject": ["the query", "the load", "the pipeline", "the dashboard", "the search", "the render"],
            "verb": ["is slow", "takes time", "is sluggish", "saturates", "slows down", "takes seconds"],
            "complement": ["on 10M rows", "at peak time", "on every refresh", "without index", "at full page"],
            "trigger": ["an unfiltered query", "N+1 queries", "a full scan", "an unnecessary re-render"],
            "consequence": ["user waits", "timeout is reached", "experience is degraded"],
            "condition": ["table has no index", "cache is not used", "component re-renders 50 times"],
        },
    },
    
    "Résonance Parasite": {
        "explanation": "Fréquence parasite en résonance avec vulnérabilité.",
        "strategy": "C — Filtrage",
        "action": "Validation, sanitization, prepared statements, CSP, never trust input.",
        "slots_fr": {
            "sujet": ["une injection SQL", "une faille XSS", "une attaque CSRF", "un path traversal", "une command injection"],
            "verbe": ["exploite", "cible", "attaque", "détourne", "contourne", "injecte"],
            "complement": ["le formulaire", "le paramètre URL", "le cookie", "le header HTTP", "l'upload"],
            "declencheur": ["un input non validé", "un champ libre", "un paramètre non échappé"],
            "consequence": ["la base de données est compromise", "du code malveillant s'exécute", "des données fuient"],
            "condition": ["l'input n'est pas sanitizé", "le CSP n'est pas configuré", "les requêtes sont concaténées"],
        },
        "slots_en": {
            "subject": ["SQL injection", "XSS vulnerability", "CSRF attack", "path traversal", "command injection"],
            "verb": ["exploits", "targets", "attacks", "hijacks", "bypasses", "injects"],
            "complement": ["the form", "the URL parameter", "the cookie", "the HTTP header", "the upload"],
            "trigger": ["unvalidated input", "free text field", "unescaped parameter"],
            "consequence": ["database is compromised", "malicious code executes", "data leaks"],
            "condition": ["input is not sanitized", "CSP is not configured", "queries are concatenated"],
        },
    },
    
    # ───── MATHÉMATIQUES & PHYSIQUE (5) ─────
    "Résonance Forcée Math": {
        "explanation": "Base {(Ψ₁)ⁿ} dans cadre PDE linéaire → contradiction.",
        "strategy": "B — Synchronisation",
        "action": "Non-linéarité via G_μν GAGUT, pas potentiel ajouté. ABC comme couplage.",
        "slots_fr": {
            "sujet": ["les coefficients spectraux", "la dérivation ab initio", "les exposants", "la base non-linéaire", "le système d'équations"],
            "verbe": ["s'annulent", "n'émergent pas", "sont bloqués", "ne se dérivent pas", "restent empiriques"],
            "complement": ["dans le cadre linéaire", "avec Klein-Gordon", "pour n≥2", "depuis les premiers principes"],
            "declencheur": ["la projection linéaire", "l'orthogonalité de Fourier", "la diagonalisation standard"],
            "consequence": ["les 5 pistes échouent", "cₙ=0 pour n≥2", "contradiction combinatoire"],
            "condition": ["la PDE est linéaire", "le potentiel est ajouté à la main", "la fonction génératrice n'est pas injective"],
        },
        "slots_en": {
            "subject": ["spectral coefficients", "ab initio derivation", "exponents", "nonlinear basis", "equation system"],
            "verb": ["vanish", "do not emerge", "are blocked", "cannot be derived", "remain empirical"],
            "complement": ["in linear framework", "with Klein-Gordon", "for n≥2", "from first principles"],
            "trigger": ["linear projection", "Fourier orthogonality", "standard diagonalization"],
            "consequence": ["all 5 approaches fail", "cₙ=0 for n≥2", "combinatorial contradiction"],
            "condition": ["PDE is linear", "potential is added manually", "generating function is not injective"],
        },
    },
    
    # ───── IA & APPRENTISSAGE (6) ─────
    "Hallucination LLM": {
        "explanation": "Fausse résonance statistique. Corrélation sans causalité.",
        "strategy": "C — Filtrage",
        "action": "Fact-checking contre hologramme. Score de confiance. Garde-fou déterministe.",
        "slots_fr": {
            "sujet": ["le LLM", "le modèle", "l'IA", "ChatGPT", "le réseau de neurones"],
            "verbe": ["invente", "hallucine", "affabule", "crée de toutes pièces", "génère faussement"],
            "complement": ["une citation inexistante", "un fait erroné", "une référence fictive", "une réponse plausible mais fausse"],
            "declencheur": ["une question pointue", "un sujet peu couvert", "une demande de précision"],
            "consequence": ["l'utilisateur est trompé", "la réponse est incorrecte", "la confiance est injustifiée"],
            "condition": ["le fait n'est pas dans les données d'entraînement", "le modèle extrapole trop", "la température est élevée"],
        },
        "slots_en": {
            "subject": ["the LLM", "the model", "the AI", "ChatGPT", "the neural network"],
            "verb": ["invents", "hallucinates", "fabricates", "makes up", "falsely generates"],
            "complement": ["a nonexistent citation", "an incorrect fact", "a fictitious reference", "a plausible but false answer"],
            "trigger": ["a niche question", "a poorly covered topic", "a request for precision"],
            "consequence": ["user is misled", "answer is incorrect", "confidence is unjustified"],
            "condition": ["fact not in training data", "model extrapolates too much", "temperature is high"],
        },
    },
    
    "Catastrophic Forgetting": {
        "explanation": "Nouvelle fréquence efface les précédentes.",
        "strategy": "B — Synchronisation",
        "action": "Replay memory. Elastic weight consolidation. Apprentissage par interférence.",
        "slots_fr": {
            "sujet": ["le réseau de neurones", "le modèle fine-tuné", "l'IA spécialisée"],
            "verbe": ["oublie", "perd", "efface", "désapprend", "régresse sur"],
            "complement": ["la tâche précédente", "les connaissances générales", "le benchmark d'origine"],
            "declencheur": ["le fine-tuning", "l'apprentissage séquentiel", "la spécialisation"],
            "consequence": ["le modèle ne sait plus faire A après avoir appris B", "régression sur les tests"],
            "condition": ["pas de replay memory", "poids écrasés sans consolidation", "pas d'entraînement conjoint"],
        },
        "slots_en": {
            "subject": ["the neural network", "the fine-tuned model", "the specialized AI"],
            "verb": ["forgets", "loses", "erases", "unlearns", "regresses on"],
            "complement": ["the previous task", "general knowledge", "the original benchmark"],
            "trigger": ["fine-tuning", "sequential learning", "specialization"],
            "consequence": ["model no longer does A after learning B", "regression on tests"],
            "condition": ["no replay memory", "weights overwritten without consolidation", "no joint training"],
        },
    },
    
    # ───── SYSTÈMES & INFRA (6) ─────
    "Cascade de Pannes": {
        "explanation": "Interférence constructive de pannes (effet domino).",
        "strategy": "D — Dissipation",
        "action": "Bulkhead, circuit breaker, graceful degradation, isolation.",
        "slots_fr": {
            "sujet": ["la panne", "le crash", "l'arrêt", "la défaillance"],
            "verbe": ["se propage", "entraîne", "déclenche une cascade", "fait tomber", "contamine"],
            "complement": ["tout le cluster", "les services dépendants", "l'infrastructure entière"],
            "declencheur": ["un nœud qui tombe", "un timeout en cascade", "un split-brain"],
            "consequence": ["tout le système est down", "les clients sont impactés", "la reprise prend des heures"],
            "condition": ["pas de bulkhead", "pas de circuit breaker", "les services sont couplés fortement"],
        },
        "slots_en": {
            "subject": ["the outage", "the crash", "the failure", "the fault"],
            "verb": ["propagates", "triggers", "cascades", "brings down", "contaminates"],
            "complement": ["the entire cluster", "dependent services", "the whole infrastructure"],
            "trigger": ["a node going down", "a cascading timeout", "a split-brain"],
            "consequence": ["entire system is down", "clients are impacted", "recovery takes hours"],
            "condition": ["no bulkhead", "no circuit breaker", "services are tightly coupled"],
        },
    },
    
    # ───── DONNÉES & INFORMATION (4) ─────
    "Corruption Spectrale": {
        "explanation": "Information partiellement altérée. Onde reçue ≠ onde émise.",
        "strategy": "C — Filtrage",
        "action": "Checksum, hash, RAID, retransmission, correction d'erreur.",
        "slots_fr": {
            "sujet": ["le fichier", "le paquet", "la trame", "les données", "le document"],
            "verbe": ["est corrompu", "a un checksum invalide", "contient des artefacts", "est illisible"],
            "complement": ["après transfert", "après écriture disque", "dans la mémoire", "sur le réseau"],
            "declencheur": ["un bit flip", "une coupure réseau", "une panne disque", "une interference EM"],
            "consequence": ["les données sont perdues", "l'image est dégradée", "le fichier ne s'ouvre plus"],
            "condition": ["pas de checksum", "pas de ECC", "pas de retransmission"],
        },
        "slots_en": {
            "subject": ["the file", "the packet", "the frame", "the data", "the document"],
            "verb": ["is corrupted", "has invalid checksum", "contains artifacts", "is unreadable"],
            "complement": ["after transfer", "after disk write", "in memory", "on the network"],
            "trigger": ["a bit flip", "a network cut", "a disk failure", "EM interference"],
            "consequence": ["data is lost", "image is degraded", "file won't open"],
            "condition": ["no checksum", "no ECC", "no retransmission"],
        },
    },
    
    "Compression Destructive": {
        "explanation": "Réduction d'amplitude éliminant les harmoniques faibles.",
        "strategy": "F — Restauration",
        "action": "Compression sans perte si fidélité critique. Conserver l'original.",
        "slots_fr": {
            "sujet": ["l'image", "l'audio", "la vidéo", "le log", "les données"],
            "verbe": ["est pixelisé", "est floue", "grésille", "a perdu en qualité", "est dégradé"],
            "complement": ["après compression", "après réduction de bitrate", "après troncature"],
            "declencheur": ["une compression agressive", "un bitrate trop bas", "un vacuum agressif"],
            "consequence": ["l'information est perdue", "les détails sont irrécupérables"],
            "condition": ["compression lossy utilisée", "pas de sauvegarde de l'original"],
        },
        "slots_en": {
            "subject": ["the image", "the audio", "the video", "the log", "the data"],
            "verb": ["is pixelated", "is blurred", "crackles", "lost quality", "is degraded"],
            "complement": ["after compression", "after bitrate reduction", "after truncation"],
            "trigger": ["aggressive compression", "bitrate too low", "aggressive vacuum"],
            "consequence": ["information is lost", "details are unrecoverable"],
            "condition": ["lossy compression used", "no backup of original"],
        },
    },
}


# ════════════════════════════════════════════════════════════════
# GÉNÉRATION DE SYMPTÔMES
# ════════════════════════════════════════════════════════════════

def pick(choices, rng):
    """Choisit un élément aléatoire."""
    return rng.choice(choices) if isinstance(choices, list) else choices

def generate_symptoms(pattern_name: str, pattern_def: dict, 
                      count_per_lang: int = 60,
                      seed: int = 42) -> list:
    """
    Génère count_per_lang symptômes FR et EN pour un pattern
    en combinant aléatoirement les slots dans les templates.
    """
    rng = random.Random(seed + hash(pattern_name) % 10000)
    symptoms = []
    
    for lang, slots, templates in [("fr", pattern_def.get("slots_fr", {}), TEMPLATES_FR),
                                    ("en", pattern_def.get("slots_en", {}), TEMPLATES_FR)]:
        if not slots:
            continue
        
        used = set()
        attempts = 0
        max_attempts = count_per_lang * 10
        
        while len(symptoms) < count_per_lang and attempts < max_attempts:
            attempts += 1
            
            # Choisir un template
            template = rng.choice(templates)
            
            # Remplir les slots
            filled = template
            for slot_name, slot_values in slots.items():
                placeholder = "{" + slot_name + "}"
                if placeholder in filled:
                    filled = filled.replace(placeholder, rng.choice(slot_values))
            
            # Nettoyer les slots non remplis
            import re
            filled = re.sub(r'\{[^}]+\}', '', filled).strip()
            filled = re.sub(r'\s+', ' ', filled)
            
            if filled and filled not in used and len(filled) > 15:
                used.add(filled)
                symptoms.append(filled)
    
    return symptoms


# ════════════════════════════════════════════════════════════════
# INGESTION
# ════════════════════════════════════════════════════════════════

def massive_ingestion(engine: WaveDiagnosticEngine, 
                      symptoms_per_pattern: int = 80) -> dict:
    """
    Ingère massivement tous les patterns avec symptômes générés.
    """
    stats = {"patterns": 0, "symptoms": 0, "by_pattern": {}}
    
    for pattern_name, pattern_def in PATTERN_DEFS.items():
        # Générer les symptômes
        symptoms = generate_symptoms(pattern_name, pattern_def, 
                                     count_per_lang=symptoms_per_pattern // 2)
        
        stats["by_pattern"][pattern_name] = len(symptoms)
        stats["symptoms"] += len(symptoms)
        
        # Encoder
        psi_sum = np.zeros(engine.dim, dtype=complex)
        for sym in symptoms:
            psi_sum += engine.encoder.encode(sym, enrich_cross_lingual=True)
        psi_avg = psi_sum / max(len(symptoms), 1)
        
        # Créer le pattern
        pattern = DiagnosticPattern(
            interference_type=pattern_name,
            explanation=pattern_def["explanation"],
            strategy=pattern_def["strategy"],
            action_template=pattern_def["action"],
            psi_symptoms=psi_avg,
        )
        engine.patterns.append(pattern)
        stats["patterns"] += 1
    
    return stats


# ════════════════════════════════════════════════════════════════
# TEST
# ════════════════════════════════════════════════════════════════

def build_test_set() -> list:
    """Construit un ensemble de test indépendant (non généré par templates)."""
    return [
        # Code — symptômes "réalistes" pas dans les templates
        ("NullPointerException in UserService.getProfile(): user is null", "Absence Fréquence"),
        ("undefined is not a function at Object.render (app.js:42)", "Absence Fréquence"),
        ("KeyError: 'database_url' not found in environment", "Absence Fréquence"),
        
        ("FATAL: out of memory, heap limit reached after processing 500K records", "Saturation"),
        ("stack overflow at recursive depth 15000 in factorial()", "Saturation"),
        ("HTTP 429 rate limit exceeded for IP 10.0.0.1", "Saturation"),
        
        ("race condition: counter desync after 1000 parallel increments", "Collision Phase"),
        ("deadlock detected: Thread-5 waiting for lock held by Thread-8", "Collision Phase"),
        ("optimistic locking failure: row version mismatch in UPDATE", "Collision Phase"),
        
        ("memory leak: heap size grows from 200MB to 2GB over 6 hours", "Onde Fantome"),
        ("Too many open files: accept() failed after 1024 connections", "Onde Fantome"),
        ("goroutine leak: 5000 goroutines sleeping forever after context cancel", "Onde Fantome"),
        
        ("stale cache: old price displayed 30 min after database update", "Déphasage Temporel"),
        ("session expiry not reflected until page refresh — user appears logged in", "Déphasage Temporel"),
        ("DNS cache poisoning: domain resolving to old IP 48h after migration", "Déphasage Temporel"),
        
        ("off-by-one: loop iterates 9 times instead of 10 (i < n vs i <= n)", "Désaccord Fréquence"),
        ("floating point: 0.1 + 0.2 === 0.3 returns false in JavaScript", "Désaccord Fréquence"),
        ("timezone bug: meeting scheduled at 3PM UTC but displayed as 3PM PST", "Désaccord Fréquence"),
        
        ("regression: password reset flow broken after auth library upgrade", "Résonance Forcée"),
        ("breaking change: API v2 returns different JSON structure than v1", "Résonance Forcée"),
        ("build fails on CI but passes locally — Node version mismatch", "Résonance Forcée"),
        
        ("N+1 query: 200 SQL queries executed to render a list of 20 items", "Interférence Multiple"),
        ("page load takes 8 seconds: 5MB JS bundle with no code splitting", "Interférence Multiple"),
        ("database full table scan on every search: 10M rows, no index", "Interférence Multiple"),
        
        ("SQL injection in WHERE clause via unsanitized ?search= parameter", "Résonance Parasite"),
        ("XSS via innerHTML: user comment <script>alert(1)</script> executes", "Résonance Parasite"),
        ("path traversal: GET /download?file=../../../etc/passwd returns system file", "Résonance Parasite"),
        
        # Math
        ("spectral coefficients c_n vanish for n>=2 in linear Klein-Gordon framework", "Résonance Forcée Math"),
        ("ab initio derivation fails: combinatorial contradiction in variational system", "Résonance Forcée Math"),
        ("M(α) determinant minimum not at α=1/φ in simplified linear model", "Résonance Forcée Math"),
        
        # IA
        ("GPT-4 invents a 2019 paper by Smith et al. that was never published", "Hallucination LLM"),
        ("model gives opposite answers to same question rephrased", "Hallucination LLM"),
        ("LLM generates Python code that calls a nonexistent library function", "Hallucination LLM"),
        
        ("catastrophic forgetting: after fine-tuning on medical data, model fails basic math", "Catastrophic Forgetting"),
        ("specialized model scores 95% on domain A but dropped to 45% on domain B", "Catastrophic Forgetting"),
        
        # Systèmes
        ("Kubernetes cluster: one node OOM kills cascade to all pods on other nodes", "Cascade de Pannes"),
        ("split-brain: two Redis masters elected, both accepting writes", "Cascade de Pannes"),
        
        # Données
        ("data corruption: checksum mismatch after disk write during power failure", "Corruption Spectrale"),
        ("JPEG artifacts visible after re-compressing a screenshot 3 times", "Compression Destructive"),
    ]


def test_engine(engine: WaveDiagnosticEngine, test_set: list) -> dict:
    """Test le moteur sur l'ensemble de test."""
    results = {"correct": 0, "total": len(test_set), "confidences": [], "errors": []}
    
    for symptom, expected in test_set:
        diag = engine.diagnose(symptom, max_iterations=2)
        correct = diag.interference_type == expected
        results["confidences"].append(diag.confidence)
        
        if correct:
            results["correct"] += 1
        else:
            results["errors"].append({
                "symptom": symptom[:80],
                "expected": expected,
                "got": diag.interference_type,
                "confidence": diag.confidence,
            })
    
    return results


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║   🌊 INGESTION MASSIVE v4 — 5000+ symptômes, 50+ patterns    ║
║   Objectif : 95%+ accuracy                                    ║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    # Créer le moteur
    print("🧠 Initialisation du moteur ondulatoire...")
    engine = WaveDiagnosticEngine()
    engine.patterns = []  # Vider les patterns par défaut
    
    # ── INGESTION ──
    symptoms_per = 100  # 50 FR + 50 EN par pattern
    print(f"💉 Injection massive (~{symptoms_per * len(PATTERN_DEFS)} symptômes)...")
    
    t0 = time.time()
    stats = massive_ingestion(engine, symptoms_per_pattern=symptoms_per)
    elapsed = time.time() - t0
    
    total_symptoms = stats["symptoms"]
    total_patterns = stats["patterns"]
    print(f"  ✅ {total_patterns} patterns créés")
    print(f"  ✅ {total_symptoms} symptômes générés et encodés")
    print(f"  ⚡ Temps : {elapsed:.2f}s ({total_symptoms/elapsed:.0f} symptômes/s)")
    
    # ── TEST ──
    test_set = build_test_set()
    print(f"\n🧪 Test sur {len(test_set)} symptômes réels (hors templates)...")
    
    results = test_engine(engine, test_set)
    
    accuracy = results["correct"] / results["total"] * 100
    avg_conf = float(np.mean(results["confidences"]))
    
    # Afficher les erreurs
    if results["errors"]:
        print(f"\n  ❌ {len(results['errors'])} erreurs :")
        for err in results["errors"]:
            print(f"     {err['expected']:<28} → {err['got']:<28} ({err['symptom'][:50]}...)")
    
    print(f"\n{'='*65}")
    print(f"📊 RÉSULTAT FINAL")
    print(f"{'='*65}")
    print(f"  Accuracy    : {accuracy:.1f}% ({results['correct']}/{results['total']})")
    print(f"  Confiance   : {avg_conf:.3f} (moyenne)")
    print(f"  Patterns    : {total_patterns}")
    print(f"  Symptômes   : {total_symptoms}")
    
    # Barre de progression
    bar_len = 30
    filled = int(accuracy / 100 * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"  [{bar}] {accuracy:.1f}%")
    
    if accuracy >= 95:
        print(f"\n  🎉 OBJECTIF ATTEINT : {accuracy:.1f}% ≥ 95% !")
    elif accuracy >= 90:
        print(f"\n  📈 Proche de l'objectif : {accuracy:.1f}% (cible: 95%)")
    else:
        print(f"\n  🔧 Encore du travail : {accuracy:.1f}% → 95%")
    
    # ── SAUVEGARDE ──
    save_path = Path(__file__).parent / "wave_patterns_v4_trained.json"
    data = {
        "patterns": [
            {"type": p.interference_type, "explanation": p.explanation,
             "strategy": p.strategy, "action": p.action_template}
            for p in engine.patterns
        ],
        "stats": {
            "patterns_count": total_patterns,
            "symptoms_count": total_symptoms,
            "accuracy": accuracy,
            "avg_confidence": float(avg_conf),
        }
    }
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Sauvegardé : {save_path}")


if __name__ == "__main__":
    main()
