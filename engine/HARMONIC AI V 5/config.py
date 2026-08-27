# HARMONIC AI V 5 — Configuration
# ============================================================
# Agent-compagnon de téléphone haute performance,
# équivalent Hermes sans le superflu.

from pathlib import Path

# ═══════════════════════════════════════════════════════════
# CONSTANTES FONDAMENTALES
# ═══════════════════════════════════════════════════════════

PHI      = 1.618033988749895
TAU      = 6.283185307179586
PHI_INV  = 1.0 / PHI

# ═══════════════════════════════════════════════════════════
# ESPACE DES PHASES
# ═══════════════════════════════════════════════════════════

DIM_PSI       = 512        # Dimension de l'espace des phases (ℂ⁵¹²)
DIM_HOLOGRAM  = 512        # Dimension de la mémoire holographique
N_HARMONICS   = 7          # Les 7 constantes fondamentales H_n

# ═══════════════════════════════════════════════════════════
# AUDIO / VOIX
# ═══════════════════════════════════════════════════════════

SAMPLE_RATE   = 24000
FRAME_SIZE    = 1920       # 80ms
STRIDE        = 960         # 40ms
FFT_SIZE      = 2048
FREQ_BINS     = FFT_SIZE // 2 + 1

# ═══════════════════════════════════════════════════════════
# PIPELINE
# ═══════════════════════════════════════════════════════════

INTENT_THRESHOLD     = 0.45   # Seuil de confiance pour détection d'intention
COHERENCE_THRESHOLD  = 0.15   # Seuil minimal pour émettre une réponse / rappel mémoire
MAX_STEPS_PER_TASK   = 12     # Étapes max par tâche agentique
MAX_BACKGROUND_TASKS = 5      # Tâches background simultanées
HISTORY_DEPTH        = 100    # Profondeur d'historique conversationnel

# ═══════════════════════════════════════════════════════════
# APPRENTISSAGE
# ═══════════════════════════════════════════════════════════

ABC_ALPHA       = PHI_INV     # α = 1/φ ~ 0.618 (équilibre mémoire/amnésie)
LEARNING_RATE   = 0.001
PHASE_LEARNER_EPOCHS = 50

# ═══════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════

ROOT_DIR      = Path(__file__).parent
DATA_DIR      = ROOT_DIR / "data"
HOLOGRAM_DIR  = DATA_DIR / "holograms"
VOICE_DIR     = DATA_DIR / "voices"
CACHE_DIR     = DATA_DIR / "cache"

for d in [DATA_DIR, HOLOGRAM_DIR, VOICE_DIR, CACHE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════
# ÉMOTIONS DISPONIBLES
# ═══════════════════════════════════════════════════════════

EMOTIONS = {
    'neutral':      {'pitch_shift': 0.00, 'energy_boost': 1.00, 'speed_factor': 1.00, 'breathiness': 0.02, 'formant_spread': 1.00},
    'warm':         {'pitch_shift': 0.05, 'energy_boost': 0.90, 'speed_factor': 0.90, 'breathiness': 0.04, 'formant_spread': 1.05},
    'joyful':       {'pitch_shift': 0.12, 'energy_boost': 1.20, 'speed_factor': 1.15, 'breathiness': 0.01, 'formant_spread': 1.10},
    'sad':          {'pitch_shift':-0.08, 'energy_boost': 0.70, 'speed_factor': 0.75, 'breathiness': 0.08, 'formant_spread': 0.90},
    'urgent':       {'pitch_shift': 0.08, 'energy_boost': 1.50, 'speed_factor': 1.40, 'breathiness': 0.01, 'formant_spread': 0.95},
    'calm':         {'pitch_shift':-0.05, 'energy_boost': 0.70, 'speed_factor': 0.70, 'breathiness': 0.06, 'formant_spread': 1.05},
    'authoritative':{'pitch_shift':-0.03, 'energy_boost': 1.10, 'speed_factor': 0.95, 'breathiness': 0.01, 'formant_spread': 0.90},
    'playful':      {'pitch_shift': 0.15, 'energy_boost': 1.10, 'speed_factor': 1.25, 'breathiness': 0.02, 'formant_spread': 1.15},
    'whisper':      {'pitch_shift': 0.00, 'energy_boost': 0.30, 'speed_factor': 0.80, 'breathiness': 0.25, 'formant_spread': 0.80},
    'excited':      {'pitch_shift': 0.18, 'energy_boost': 1.60, 'speed_factor': 1.30, 'breathiness': 0.01, 'formant_spread': 1.20},
}

# ═══════════════════════════════════════════════════════════
# 7 INTENTIONS PRINCIPALES
# ═══════════════════════════════════════════════════════════

INTENTIONS = {
    'query':      {'keywords': ['quoi', 'qui', 'où', 'quand', 'comment', 'quel', 'quelle', 'combien', 'définition', 'c\'est quoi', 'qu\'est-ce', 'explique', 'décris', 'montre']},
    'reason':     {'keywords': ['pourquoi', 'cause', 'conséquence', 'implique', 'déduis', 'conclus', 'prouve', 'démontre', 'argument', 'raison', 'logique', 'si alors']},
    'creative':   {'keywords': ['imagine', 'crée', 'invente', 'histoire', 'poème', 'chanson', 'dessine', 'raconte', 'fiction', 'blague', 'humour', 'drôle']},
    'store_fact': {'keywords': ['rappelle', 'souviens', 'note', 'enregistre', 'mémorise', 'retenir', 'apprends', 'sache', 'note que']},
    'compare':    {'keywords': ['compare', 'différence', 'similaire', 'versus', 'contre', 'opposé', 'mieux', 'pire', 'avantage', 'inconvénient']},
    'analogize':  {'keywords': ['analogie', 'comme', 'tel', 'ressemble', 'métaphore', 'pareil', 'équivalent', 'similaire']},
    'classify':   {'keywords': ['classe', 'catégorie', 'type', 'genre', 'famille', 'groupe', 'trie', 'organise', 'étiquette']},
}

# ═══════════════════════════════════════════════════════════
# OUTILS TÉLÉPHONE — Configuration
# ═══════════════════════════════════════════════════════════

PHONE_TOOLS = {
    'contacts': {
        'description': "Gestion du répertoire holographique",
        'keywords': ['contact', 'annuaire', 'répertoire', 'carnet', 'adresses', 'numéro', 'téléphone'],
    },
    'voice_call': {
        'description': "Appel vocal avec synthèse KA",
        'keywords': ['appelle', 'call', 'téléphone', 'voix', 'parler', 'joindre', 'sonner', 'biper'],
    },
    'message': {
        'description': "Envoi de messages texte ou vocaux",
        'keywords': ['message', 'sms', 'texto', 'envoie', 'msg', 'envoyer', 'écris'],
    },
    'reminder': {
        'description': "Programmation de rappels et notifications",
        'keywords': ['rappelle', 'souviens', 'agenda', 'rendez-vous', 'rdv', 'alarme', 'notif', 'n\'oublie'],
    },
    'search': {
        'description': "Recherche web et synthèse",
        'keywords': ['cherche', 'recherche', 'google', 'trouve', 'search', 'find', 'info', 'actualité'],
    },
    'dashboard': {
        'description': "Tableau de bord du téléphone",
        'keywords': ['résumé', 'dashboard', 'état', 'status', 'bilan', 'today', 'aujourd\'hui'],
    },
    'dictation': {
        'description': "Dictée vocale → texte",
        'keywords': ['dicte', 'dictée', 'transcris', 'note vocale', 'enregistre'],
    },
}

print(f"[HARMONIC AI V5] Configuration chargée — ℂ{DIM_PSI} · {len(EMOTIONS)} émotions · {len(PHONE_TOOLS)} outils téléphone")