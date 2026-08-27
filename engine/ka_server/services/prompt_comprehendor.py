"""
🌊 PromptComprehendor — Compréhension Ondulatoire de Prompts
=============================================================
Module THU-native de compréhension de prompts pour KA Mobile.
Remplace la cascade if/else dispersée par un routeur d'intention unifié
à trois niveaux :

  Niveau 1 — LEXICAL    : Patterns regex + mots-clés (rapide, 80-90% des cas)
  Niveau 2 — SPECTRAL   : Résonance wave_lang pour désambiguïsation
  Niveau 3 — SÉMANTIQUE : Embeddings appris (semantic_wave_embedding) si dispo

Principes THU :
  - encode(prompt) → ψ_prompt ∈ ℂ⁵¹²
  - encode("intention:X") → ψ_intent ∈ ℂ⁵¹²  (prototypes d'intention)
  - resonate(ψ_prompt, ψ_intent) → score ∈ [-1, 1]
  - unbind(ψ_prompt, ψ_intent) → slots (résidu après dé-liaison)
  - diffract(ψ_prompt) → composantes (séparation multi-intentions)
  - superpose(ψ_histoire, ψ_courant) → contexte de session

Architecture :
  ┌──────────────────────────────────────────────────┐
  │              PromptComprehendor                   │
  │                                                   │
  │  message ──► [Normaliser] ──► [Encoder ψ]         │
  │                  │                  │              │
  │                  ▼                  ▼              │
  │            tokens propres     ψ ∈ ℂ⁵¹²            │
  │                  │                  │              │
  │                  └────────┬─────────┘              │
  │                           ▼                        │
  │            [Classer par intention]                 │
  │            (lexical + résonance)                   │
  │                           │                        │
  │                           ▼                        │
  │            [Désambiguïser si nécessaire]           │
  │                           │                        │
  │                           ▼                        │
  │            [Extraire les slots]                    │
  │                           │                        │
  │                           ▼                        │
  │            ┌──────────────────────┐                │
  │            │    PromptFrame       │                │
  │            │  .intent             │                │
  │            │  .confidence         │                │
  │            │  .slots              │                │
  │            │  .segments           │                │
  │            │  .ambiguity          │                │
  │            │  .psi_prompt         │                │
  │            └──────────────────────┘                │
  └──────────────────────────────────────────────────┘

Usage :
  from ka_server.services.prompt_comprehendor import PromptComprehendor

  pc = PromptComprehendor()
  frame = pc.comprehend("nettoie mon téléphone")
  # → PromptFrame(intent='storage_action', confidence=0.95, ...)

  frame = pc.comprehend("combien font 15*7 ?")
  # → PromptFrame(intent='arithmetic', confidence=0.98, ...)

  frame = pc.comprehend("compare le prix du riz et du maïs au Congo")
  # → PromptFrame(intent='comparison', confidence=0.85,
  #               slots={'entities': ['riz', 'maïs'], 'location': 'Congo'})

Auteur : Équipe KA — Univers-Holistique
Date   : 2026-08-24
"""

import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

import numpy as np

log = logging.getLogger(__name__)

# ── Moteur wave_lang ──────────────────────────────────────────────────────────
_WAVE_DIR = Path(__file__).resolve().parent.parent.parent / 'vital-ka' / 'core' / 'python'
if str(_WAVE_DIR) not in sys.path:
    sys.path.insert(0, str(_WAVE_DIR))

from wave_lang import (  # noqa: E402
    encode, decode, bind, unbind, superpose, resonate, resonate_batch,
    rotate, normalize, interfere, diffract, filter_wave, phase_shift,
    emerge, stats, HolographicMemory,
)

DIM = 512  # ℂ⁵¹² — limite de Bekenstein


# ═══════════════════════════════════════════════════════════════════════════════
# TAXONOMIE D'INTENTIONS — pour KA Mobile
# ═══════════════════════════════════════════════════════════════════════════════
#
# Chaque intention est définie par :
#   - intent_id       : identifiant unique
#   - patterns        : regex pour la détection lexicale (niveau 1)
#   - keywords        : mots-clés associés (renforcement)
#   - handler         : module cible dans le pipeline
#   - description     : description humaine
#   - priority        : priorité (les intents plus spécifiques d'abord)
#   - slot_extractors : patterns pour extraire les slots
#   - ψ_prototype     : encodage spectral (calculé à l'init)
# ═══════════════════════════════════════════════════════════════════════════════

INTENT_DEFINITIONS = [
    {
        'intent_id': 'storage_action',
        'patterns': [
            # Questions/réponses polies
            r'(?i)\b(?:peux|peut|pourrais|pourrait|est[- ]ce\s+que)\s+(?:tu|vous|on)\s+(?:me\s+)?(?:netto[iy]|compress|lib[eéèêë]r|optimis)\w*\b',
            r'(?i)\bcomment\s+(?:lib[eéèêë]r\w*|gagner|nettoi[ey]|compress|optimis)\w*\b.*(?:espace|place|stockage|t[eéèêë]l[eéèêë]phon|m[eéèêë]moire)',
            # Nettoyage
            r'(?i)\b(?:netto[iy])\w*\b.*(?:mon|le|la|ton|votre|son)\s+(?:t[eéèêë]l[eéèêë]phon|appareil|stockage|m[eéèêë]moire)',
            r'(?i)\b(?:netto[iy])\w*\b.*(?:appareil|t[eéèêë]l[eéèêë]phon|portable)',
            # Compression
            r'(?i)\bcompress\w*\b.*(?:t[eéèêë]l[eéèêë]phon|donn[eéèêë]e|photo|vid[eéèêë]o|fichier|appareil)',
            r'(?i)\blib[eéèêë]r\w*\b.*(?:espace|stockag|m[eéèêë]moir|t[eéèêë]l[eéèêë]phon|place|appareil)',
            # État du stockage
            r'(?i)\b(?:stockage|espace)\b.*(?:plein|satur|rempli|insuffisant|manqu)',
            r'(?i)\bstockage\s+(?:plein|satur[eéèêë]|insuffisant)\b',
            # Optimisation
            r'(?i)\boptimis\w*\b.*(?:stockage|espace|t[eéèêë]l[eéèêë]phon|appareil)',
            r'(?i)\bgagner\b.*(?:espace|place|go|gb|mo)',
            # Vider/supprimer
            r'(?i)\b(?:vider|vid[eéèêë]|nettoi[ey])\w*\b.*(?:corbeille|cache|fichier\w*\s+temporaire)',
            r'(?i)\bvider?\s+(?:la\s+)?corbeille\b',
            r'(?i)(?:faire|font?|fais|faites|fait)\s+(?:(?:le|la|du|un|mon|ton|son)\s+)?m[eéèêë]nage\b',
            r'(?i)\bsupprim\w*\b.*(?:fichier|donn[eéèêë]e|photo|vid[eéèêë]o|appli|inutil)',
            r'(?i)\b(?:espace|place)\s+(?:sur|dans)\s+mon\b',
            r'(?i)\b(?:veux|voudrais|souhaite|aimerais)\s+(?:lib[eéèêë]r\w*|gagner|nettoi[ey]|compress)\w*\b',
            # Analyse / vérification
            r'(?i)\banalys\w*\b.*(?:mon|le|ma|ton|votre)?\s*(?:t[eéèêë]l[eéèêë]phon|appareil|stockage|m[eéèêë]moire|donn[eéèêë]es?)',
            r'(?i)\bv[eéèêë]rifi\w*\b.*(?:mon|le|ma)?\s*(?:t[eéèêë]l[eéèêë]phon|appareil|stockage|m[eéèêë]moire)',
            r'(?i)\bcheck\w*\b.*(?:mon|le)?\s*(?:t[eéèêë]l[eéèêë]phon|appareil|stockage)',
            r'(?i)\bregard\w*\b.*(?:mon|le)?\s*(?:t[eéèêë]l[eéèêë]phon|appareil|stockage)',
            r'(?i)\b(?:fais|faire)\s+(?:une? )?(?:analyse|v[eéèêë]rification|scan|diagnostic)\b.*(?:t[eéèêë]l[eéèêë]phon|appareil|stockage)',
            r'(?i)\bexamin\w*\b.*(?:mon|le|ma)?\s*(?:t[eéèêë]l[eéèêë]phon|appareil|stockage|m[eéèêë]moire)',
        ],
        'keywords': ['nettoie', 'nettoyer', 'nettoyage', 'compresse', 'compresser', 'compression',
                     'libère', 'libérer', 'stockage', 'espace', 'place',
                     'optimise', 'optimiser', 'ménage', 'vider', 'vide', 'corbeille',
                     'cache', 'supprime', 'supprimer', 'saturé', 'plein',
                     'gagner', 'go', 'gb', 'mo', 'données', 'fichiers', 'fichier',
                     'analyse', 'analyser', 'vérifier', 'vérification', 'check', 'checker',
                     'regarder', 'scan', 'diagnostic', 'examine', 'examiner', 'examen'],
        'handler': 'storage_saver',
        'description': "Action de nettoyage/compression du téléphone",
        'priority': 100,
        'slot_extractors': {
            'target': [r'(?:mon|le|ma|la|mes|les)\s+(t[eéèêë]l[eéèêë]phon\w*|appareil|stockage|m[eéèêë]moire|donn[eéèêë]es?)'],
            'action_type': [r'(nettoi[ey]\w*|compress\w*|lib[eéèêë]re\w*|optimis\w*|vider|vide|supprim\w*|gagner)'],
        },
    },
    {
        'intent_id': 'action_command',
        'patterns': [
            r'(?i)\bappell?e\w*\b',                    # appeler
            r'(?i)\b(?:envoi\w*|[eéèêë]cri\w*)\s+(?:un\s+)?(?:sms|message|texto)\b',  # envoyer SMS
            r'(?i)\b(?:sms|texto)\s+(?:[àa]\s+)?\w+',  # SMS à quelqu'un
            # Ouvrir / lancer une application
            r'(?i)\b(?:ouvre\w*|lanc\w*)\s+(?:l[\' ]?|mon? |ma |ton? |votre)?(?:appli|application|\w+)',  # ouvrir/lancer app
            r'(?i)\b(?:ouvre\w*|lanc\w*)\s+(?:l[\' ]?)?(?:\w+)',
            r'(?i)\blanc\w*\s+(?:l[\' ]?)?application\b',
            # Appareil / système
            r'(?i)\b(?:batterie|autonomie|charge)\b',   # batterie
            r'(?i)\b(?:wifi|bluetooth|r[eéèêë]seau|connexion)\b',  # connectivité
            r'(?i)\b(?:active|d[eéèêë]sactive|coupe|allume)\b',  # toggle
        ],
        'keywords': ['appelle', 'appeler', 'sms', 'message', 'envoyer', 
                     'ouvre', 'ouvrir', 'lance', 'lancer',
                     'batterie', 'wifi', 'bluetooth', 'active', 'désactive'],
        'handler': 'agent_action',
        'description': "Commande agentique (téléphone)",
        'priority': 100,
        'slot_extractors': {
            'contact': [r'(?:appell?e\w*|sms|message|texto)\s+(?:[àa]\s+)?(\w+(?:\s+\w+)?)'],
            'app_name': [r'(?:ouvre\w*|lanc\w*)\s+(?:l[\' ]?)?(\w+(?:\s+\w+)?)'],
        },
    },
    {
        'intent_id': 'arithmetic',
        'patterns': [
            r'\d+\s*[\+\-\*×÷/\^%]\s*\d+',               # opération directe (y compris ^, %)
            r'(?i)\bcombien\s+font?\b',                 # "combien font X ?"
            r'(?i)\bcalcul\w*\b',                       # "calcule X"
            r'(?i)\bracine\s+carr[eéèêë]e?\b',            # racine carrée
            r'(?i)\bfactorielle?\b',                    # factorielle
            r'(?i)\bpourcent(?:age)?\s+(?:de\s+)?\d+', # pourcentage
            r'(?i)\bpuissance\b',                       # puissance
            r'(?i)\bexposant\b',                        # exposant
            r'(?i)\bmodulo\b',                          # modulo
            r'\d+\s*\^\s*\d+',                          # 2^3
            r'\d+\s*%\s*\d+',                           # 15 % 4
        ],
        'keywords': ['combien', 'font', 'fois', 'plus', 'moins', 'divisé', 'calcul',
                     'racine', 'carrée', 'factorielle', 'pourcent', 'puissance',
                     'exposant', 'modulo', 'reste'],
        'handler': 'arithmetic_emergence',
        'description': "Calcul arithmétique",
        'priority': 90,
        'slot_extractors': {
            'expression': [r'(\d+[\+\-\*×÷/]\d+)', r'(?:combien\s+font?\s+)?(.+)'],
        },
    },
    {
        'intent_id': 'reason',
        'patterns': [
            # Arithmétique étendue (détection par FHRR)
            r'(?i)\bcombien\s+font?\b',                 
            r'(?i)\bcalcul\w*\b',
            r'(?i)\bcalcule\s+moi\b',
            r'(?i)\br[eéèêë]solv\w*\b',                    # "résout X"
            r'(?i)\bsi\s+.+\s+alors\b',                    # "si X alors Y"
            # Comparaison avancée
            r'(?i)\bquel\s+(?:est\s+)?(?:le|la)\s+(?:meilleur|pire|plus\s+\w+|moins\s+\w+|mieux)\s+(?:entre|que|pour)\b',
            r'(?i)\bqui\s+(?:est\s+)?(?:le|la)\s+(?:meilleur|pire|plus|mieux)\b',
            # Logique / inférence
            r'(?i)\bdonc\s+.*\?',                          # "X, donc Y ?"
            r'(?i)\best[\s-]ce\s+que\s+.+\s+(?:implique|signifie|entra[iîê]ne|prouve|montre)\b',
            # Raisonnement explicite
            r'(?i)\braisonn\w*\b',
            r'(?i)\bstp\s+(?:r[eéèêë]solv|trouve|calcule)\b',
        ],
        'keywords': ['combien', 'calcule', 'résous', 'résout', 'raisonne', 'raisonnement',
                     'si', 'alors', 'donc', 'comparaison', 'meilleur', 'pire',
                     'implique', 'signifie', 'prouve', 'montre', 'logique',
                     'inférence', 'déduction', 'conclusion'],
        'handler': 'wave_reasoner',
        'description': "Raisonnement harmonique (arithmétique FHRR, logique, comparaison)",
        'priority': 85,
        'slot_extractors': {
            'expression': [r'(.+)'],  # fallback : tout le message
        },
    },
    {
        'intent_id': 'specialize_request',
        'patterns': [
            r'(?i)\bsp[eéèêë]cialise?\w*\s*(?:-moi\s+)?(?:sur|en|dans)?\s+',
            r'(?i)\bcr[eéèêë]e\w*\s+(?:un|une)\s+hologramme\b',
            r'(?i)\bdeviens?\s+(?:un\s+)?expert\b',
            r'(?i)\bcr[eéèêë]e\w*\s+(?:un|une)\s+sp[eéèêë]cialis\w*\b',
            r'(?i)\bapprends?\s+(?:moi|nous)?\s+(?:sur|le|la|les?)\s+domaine\b',
            r'(?i)\bconnais\s*-?\s*tu\s+(?:le|la|les?)\s+domaine\b',
        ],
        'keywords': ['spécialise', 'spécialisation',
                     'crée un hologramme', 'crée une spécialisation', 'deviens expert'],
        'handler': 'specialize',
        'description': "Demande de spécialisation/création d'hologramme",
        'priority': 95,
        'slot_extractors': {
            'domain': [
                r'(?:sur|en|dans|le|la|les?|domaine\s+(?:de\s+)?)\s+([\w\séèêëàâîïôûùçœæ\'\-]{3,50}?)(?:\s*\?|\s*$|\s*\.)',
                r'(?:hologramme|expert|sp[eéèêë]cialis)\w*\s+(?:sur|en|dans|de\s+)?\s+([\w\séèêëàâîïôûùçœæ\'\-]{3,50}?)(?:\s*\?|\s*$|\s*\.)',
            ],
        },
    },
    {
        'intent_id': 'learning',
        'patterns': [
            r'(?i)\bapprends?\s*:\s*',                  # "apprends: X"
            r'(?i)\bretiens?\s*(?:que|:)?\s*',         # "retiens que X"
            r'(?i)\bm[eéèêë]moris\w*\s*:\s*',             # "mémorise: X"
            r'(?i)\benregistr\w*\s*(?:que|:)?\s*',     # "enregistre X"
            r'(?i)\bnote\s*(?:que|:)?\s*',             # "note que X"
            r'(?i)\bsouviens?\s*-?\s*toi\s*(?:que|de|:)?\s*',  # "souviens-toi X"
            r'(?i)\bstore\s*fact\b',                    # "store fact X"
        ],
        'keywords': ['apprends', 'retiens', 'mémorise', 'enregistre', 'note', 'souviens-toi',
                     'store', 'fact'],
        'handler': 'learning',
        'description': "Apprentissage explicite d'un fait",
        'priority': 100,
        'slot_extractors': {
            'fact': [r'(?:apprends|retiens|m[eéèêë]moris|enregistr|note|souviens-toi)\w*\s*(?:que|:)?\s*(.+)'],
        },
    },
    {
        'intent_id': 'comparison',
        'patterns': [
            r'(?i)\bcompar\w*\b',                       # "compare X et Y"
            r'(?i)\bdiff[eéèêë]rence\w*\s+entre\b',       # "différence entre X et Y"
            r'(?i)\b(?:vs\.?|versus)\b',                # "X vs Y"
            r'(?i)\b(?:lequel|laquelle)\s+(?:est\s+)?(?:mieux|meilleur|pire)\b',  # choix
            r'(?i)\bmieux\s+entre\b',                   # "mieux entre X et Y"
            r"(?i)\bqu['\s]est\s*-?\s*ce\s+qui\s+(?:est\s+)?mieux\b",
        ],
        'keywords': ['compare', 'différence', 'versus', 'vs', 'lequel', 'laquelle',
                     'mieux', 'meilleur', 'pire', 'entre'],
        'handler': 'comparison',
        'description': "Comparaison entre entités",
        'priority': 85,
        'slot_extractors': {
            'entities': [
                r'(?:entre|compar\w*|vs\.?|versus)\s+([\w\séèêëàâîïôûùçœæ\'\-]+?)\s+(?:et|&|,)\s+([\w\séèêëàâîïôûùçœæ\'\-]+?)(?:\s+(?:au?|en|dans|sur)\s+\w+)?(?:\s*\?|\s*$)',
                r"(?:diff[eéèêë]rence\w*\s+entre)\s+([\w\séèêëàâîïôûùçœæ\'\-]+?)\s+et\s+([\w\séèêëàâîïôûùçœæ\'\-]+?)(?:\s*\?|\s*$)",
            ],
            'location': [r'(?:au?|en|dans|sur)\s+([\w\séèêëàâîïôûùçœæ\'\-]+?)(?:\s*\?|\s*$)'],
        },
    },
    {
        'intent_id': 'generation',
        'patterns': [
            r'(?i)\b[eéèêë]cris?\b',                       # "écris un poème"
            r'(?i)\bg[eéèêë]n[eéèêë]re\w*\b',                 # "génère un briefing"
            r'(?i)\bcr[eéèêë]e\w*\b(?!\s+(?:un|une)\s+(?:hologramme|sp[eéèêë]cialis))',  # "crée" mais pas hologramme
            r'(?i)\binvente\w*\b',                      # "invente une histoire"
            r'(?i)\bimagin\w*\b',                       # "imagine un scénario"
            r'(?i)\bracont\w*\b',                       # "raconte une histoire"
            r'(?i)\bpo[eéèêë]me\b',                        # mention de poème
            r'(?i)\bbriefing\b',                        # briefing
        ],
        'keywords': ['écris', 'génère', 'crée', 'invente', 'imagine', 'raconte',
                     'poème', 'briefing', 'histoire', 'scénario'],
        'handler': 'generation',
        'description': "Génération créative",
        'priority': 75,
        'slot_extractors': {
            'topic': [r'(?:[eéèêë]cris?|g[eéèêë]n[eéèêë]re\w*|cr[eéèêë]e\w*|invente\w*|imagin\w*|racont\w*)\s+(?:un|une|le|la|les?|des?)\s+(.+)'],
        },
    },
    {
        'intent_id': 'identity_question',
        'patterns': [
            # Formes accentuées + non accentuées pour mobile
            r'(?i)\bqui\s+(?:es[\s-]?tu|etes[\s-]?tu|êtes[\s-]?vous|etes[\s-]?vous|suis[\s-]?je)\b',
            r'(?i)\btu\s+es\s+qui\b',
            r'(?i)\bvous\s+etes\s+qui\b',
            r'(?i)\bc[\'\s]est\s+quoi\s+(?:KA|tu|vous|ca)\b',
            r'(?i)\bc[\'\s]est\s+qui\s+(?:KA|tu|vous)\b',
            r'(?i)\b(?:KA|tu)\s+c[\'\s]est\s+quoi\b',
            r'(?i)\b(?:presente[\s-]?toi|présente[\s-]?toi|presentez[\s-]?vous|présentez[\s-]?vous)\b',
            r'(?i)\bqui\s+est\s+tu\b',
            r'(?i)\bdis[\s-]?moi\s+(?:qui\s+tu\s+es|ce\s+que\s+tu\s+es)\b',
            r'(?i)\bexplique[\s-]?moi\s+(?:qui\s+tu\s+es|ton\s+role|ce\s+que\s+tu\s+es|ton\s+histoire)\b',
            r'(?i)\braconte[\s-]?moi\s+(?:ton\s+histoire|qui\s+tu\s+es)\b',
            r'(?i)\bparle[\s-]?moi\s+de\s+toi\b',
            r'(?i)\btu\s+es\s+quoi\b',
            r'(?i)\b(?:a\s+quoi|à\s+quoi)\s+sers[\s-]?(?:tu|vous)\b',
            r'(?i)\bquel\s+(?:est\s+)?ton\s+(?:role|rôle|but|objectif|nom)\b',
            # Annuaire de phrases directes (priorité haute)
            r'(?i)\bcomment\s+(?:tu\s+t[\'\s]*appelles|vous\s+vous\s+appelez)\b',
            r'(?i)\btu\s+peux\s+faire\s+quoi\b',
            r'(?i)\bque\s+(?:peux[\s-]?(?:tu|je)|pouvez[\s-]?vous)\s+(?:faire|m[\'\s]apporter|me\s+proposer)\b',
            r'(?i)\bquel\s+(?:est\s+)?(?:ton|votre)\s+(?:role|rôle|but|objectif|nom)\b',
            r'(?i)\bqui\s+etes[\s-]?vous\b',
            r'(?i)\bc[\'\s]est\s+quoi\s+(?:ka|tu|vous)\b',
        ],
        'keywords': ['qui es-tu', 'qui es tu', 'tu es qui', 'presente toi',
                     'presentez-vous', 'c\'est quoi', 'ka', 'assistant',
                     'que peux-tu faire', 'ton role', 'a quoi sers-tu',
                     'comment tu t\'appelles', 'comment tu t appelles', 'ton nom', 'c\'est quoi ka',
                     'explique moi qui tu es', 'ton histoire', 'parle moi de toi',
                     'qui etes vous', 'qui êtes-vous', 'tu es quoi'],
        'handler': 'identity',
        'description': "Question sur l'identité de KA",
        'priority': 110,
        'slot_extractors': {},
    },
    {
        'intent_id': 'greeting',
        'patterns': [
            r'(?i)^(bonjour|salut|coucou|hello|hey|yo|wesh)\b',
            r'(?i)^(bonsoir|bonne\s+nuit|bonne\s+journ[eéèêë]e)\b',
            r'(?i)^(merci|thanks?|thank\s+you)\b',
            r'(?i)^([çc]a\s+va|comment\s+(?:[çc]a\s+)?va|quoi\s+de\s+neuf)\b',
            r'(?i)^(au\s+revoir|bye|[àa]\s+bient[ôo]t|adieu)\b',
        ],
        'keywords': ['bonjour', 'salut', 'coucou', 'hello', 'hey', 'bonsoir',
                     'merci', 'ça va', 'au revoir', 'bye'],
        'handler': 'greeting',
        'description': "Salutation / conversation sociale",
        'priority': 60,
        'slot_extractors': {},
    },
    {
        'intent_id': 'factual_question',
        'patterns': [
            r'(?i)\bqui\s+(?:est|a|[eéèêë]tait|a\s+fait|a\s+d[eéèêë]couvert)\b',
            r'(?i)\bquand\b',
            r'(?i)\bo[uù]\b',
            r'(?i)\bpourquoi\b',
            r'(?i)\bcomment\s+(?:[çc]a\s+)?(?:marche|fonctionne|fait|peut)\b',
            r'(?i)\bquel(?:le|s)?\s+(?:est|sont)\b',
            r'(?i)\bque\s+(?:signifie|veut\s+dire|repr[eéèêë]sente)\b',
            r"(?i)\bqu['\s]est\s*-?\s*ce\s+que\b",
            r"(?i)\bqu['\s]est\s*-?\s*ce\s+qu['\s]\b",
            r'(?i)\bd[eéèêë]fini\w*\b',
            r'(?i)\bexpliqu\w*\b',
            r"(?i)\bc['\s]est\s+quoi\b",
        ],
        'keywords': ['qui', 'quand', 'où', 'pourquoi', 'comment', 'quel', 'quelle',
                     'signifie', 'définition', 'explique', 'c\'est quoi',
                     'qu\'est-ce que', 'qu\'est-ce qu\''],
        'handler': 'knowledge_retrieval',
        'description': "Question factuelle / de connaissance",
        'priority': 70,
        'slot_extractors': {
            'topic': [r'(?:qui\s+(?:est|a|[eéèêë]tait)|quand|o[uù]|pourquoi|comment|quel(?:le|s)?\s+(?:est|sont)|que\s+(?:signifie|veut\s+dire|repr[eéèêë]sente)|qu[\'e]st-ce\s+que|c[\'e]est\s+quoi)\s+(.+)'],
        },
    },
]

# ── Intent par défaut (fallback quand rien ne matche) ────────────────────────
DEFAULT_INTENT = {
    'intent_id': 'general_chat',
    'patterns': [r'.*'],  # match tout
    'keywords': [],
    'handler': 'llm_fallback',
    'description': "Conversation générale (fallback LLM)",
    'priority': 0,
    'slot_extractors': {},
}


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPT FRAME — la structure de sortie
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PromptFrame:
    """Résultat structuré de la compréhension d'un prompt."""
    original: str                                    # message original
    normalized: str                                  # après normalisation
    intent: str                                      # intention principale (intent_id)
    sub_intent: str = ""                             # sous-intention (optionnel)
    confidence: float = 0.0                          # score [-1, 1]
    slots: Dict[str, Any] = field(default_factory=dict)       # paramètres extraits
    segments: List['PromptFrame'] = field(default_factory=list)  # sous-prompts si multi
    psi_prompt: Optional[np.ndarray] = None          # encodage spectral
    ambiguity: bool = False                          # ambiguïté détectée
    clarification_question: str = ""                 # question de clarification
    suggested_handler: str = ""                      # module cible
    all_scores: Dict[str, float] = field(default_factory=dict)  # scores de toutes les intents
    metadata: Dict[str, Any] = field(default_factory=dict)      # métadonnées
    
    def to_dict(self) -> dict:
        """Sérialisation JSON-safe."""
        return {
            'original': self.original,
            'normalized': self.normalized,
            'intent': self.intent,
            'sub_intent': self.sub_intent,
            'confidence': self.confidence,
            'slots': self.slots,
            'segments': [s.to_dict() for s in self.segments],
            'ambiguity': self.ambiguity,
            'clarification_question': self.clarification_question,
            'suggested_handler': self.suggested_handler,
            'all_scores': self.all_scores,
            'metadata': self.metadata,
        }
    
    def __repr__(self) -> str:
        slots_str = ', '.join(f'{k}={v}' for k, v in self.slots.items())
        amb = '⚠️ AMBIGU ' if self.ambiguity else ''
        seg = f' [{len(self.segments)} segments]' if self.segments else ''
        return (f"PromptFrame({amb}intent={self.intent}, "
                f"conf={self.confidence:.2f}, "
                f"slots={{{slots_str}}}, "
                f"handler={self.suggested_handler}{seg})")


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPT COMPREHENDOR — le cœur
# ═══════════════════════════════════════════════════════════════════════════════

class PromptComprehendor:
    """
    Compréhension de prompts en trois niveaux (THU-native).
    
    Niveau 1 — LEXICAL : Patterns regex + mots-clés → première classification
    Niveau 2 — SPECTRAL : Résonance wave_lang → désambiguïsation + confiance
    Niveau 3 — SÉMANTIQUE : Embeddings appris (si semantic_wave_embedding dispo)
    
    Usage :
        pc = PromptComprehendor()
        frame = pc.comprehend("nettoie mon téléphone")
        if frame.ambiguity:
            # poser frame.clarification_question à l'utilisateur
            ...
        else:
            # router vers frame.suggested_handler
            ...
    """
    
    def __init__(self, dim: int = DIM, use_semantic: bool = True):
        self.dim = dim
        self.use_semantic = use_semantic
        self._intents = INTENT_DEFINITIONS
        
        # ── Pré-encoder les prototypes d'intention ──
        self._psi_intents: Dict[str, np.ndarray] = {}
        self._psi_cache: Dict[str, np.ndarray] = {}
        
        for intent_def in self._intents:
            intent_id = intent_def['intent_id']
            # Le prototype est l'encodage de "intention:ID + description + keywords"
            proto_text = f"intention:{intent_id} {intent_def['description']} {' '.join(intent_def['keywords'])}"
            self._psi_intents[intent_id] = encode(proto_text, dim=self.dim)
            # Normaliser
            self._psi_intents[intent_id] = normalize(self._psi_intents[intent_id])
        
        # ── Semantic embedding (optionnel, niveau 3) ──
        self._semantic_encoder = None
        if use_semantic:
            self._init_semantic()
        
        # ── État du dialogue ──
        self._session_context: Dict[str, np.ndarray] = {}  # session_id → ψ_contexte
        self._session_last_intent: Dict[str, str] = {}     # session_id → dernière intention
        
        log.info(f"🧠 PromptComprehendor initialisé : {len(self._intents)} intentions, "
                 f"dim={dim}, semantic={self._semantic_encoder is not None}")
    
    def _init_semantic(self):
        """Initialise l'encodeur sémantique (niveau 3) si disponible."""
        try:
            from semantic_wave_embedding import SemanticWaveEmbedding
            self._semantic_encoder = SemanticWaveEmbedding(dim=self.dim)
            log.info("  📐 SemanticWaveEmbedding chargé (niveau 3)")
        except Exception as e:
            log.debug(f"  ⚠️ SemanticWaveEmbedding non disponible: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # NORMALISATION (Niveau 1 — pré-traitement)
    # ═══════════════════════════════════════════════════════════════════════════
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalise un prompt : minuscules, sans accents excessifs,
        espaces normalisés, ponctuation conservative.
        """
        import unicodedata
        
        # Minuscules
        t = text.lower().strip()
        
        # Normaliser les espaces
        t = re.sub(r'\s+', ' ', t)
        
        # Normaliser les accents (garde les accents français mais uniformise)
        t = unicodedata.normalize('NFC', t)
        
        # Normaliser les apostrophes courbes → droites
        t = t.replace('\u2019', "'").replace('\u2018', "'")
        
        # Normaliser les guillements
        t = t.replace('\u00ab', '"').replace('\u00bb', '"')
        t = t.replace('\u201c', '"').replace('\u201d', '"')
        
        return t
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CLASSIFICATION LEXICALE (Niveau 1)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _lexical_score(self, text: str, intent_def: dict) -> float:
        """
        Score lexical : patterns matchés + densité de mots-clés.
        
        Stratégie robuste (ne pénalise PAS les intents avec beaucoup de patterns) :
        - Tout pattern qui matche → +0.75 de base, +0.05 par match supplémentaire (max 0.90)
        - Mots-clés : fraction des keywords trouvés × 0.30
        - Score final = min(pattern_score + keyword_score, 1.0)
        
        Retourne un score ∈ [0, 1].
        """
        patterns = intent_def.get('patterns', [])
        keywords = intent_def.get('keywords', [])
        
        if not patterns and not keywords:
            return 0.0
        
        # ── Patterns : présence → score fort, pas de pénalité pour les non-matchs ──
        pattern_matches = 0
        for pattern in patterns:
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    pattern_matches += 1
            except re.error:
                pass
        
        if pattern_matches > 0:
            pattern_score = min(0.75 + (pattern_matches - 1) * 0.05, 0.90)
        else:
            pattern_score = 0.0
        
        # ── Keywords : densité de hits (fraction des mots-clés présents) ──
        if keywords:
            kw_hits = sum(1 for kw in keywords if kw in text)
            kw_score = (kw_hits / len(keywords)) * 0.30
        else:
            kw_score = 0.0
        
        return min(pattern_score + kw_score, 1.0)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # RÉSONANCE SPECTRALE (Niveau 2)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _encode_prompt(self, text: str) -> np.ndarray:
        """
        Encode un prompt en ψ ∈ ℂ⁵¹².
        
        Stratégie :
        - Si semantic_encoder dispo → utiliser l'encodage sémantique
        - Sinon → wave_lang.encode() (hash déterministe)
        - Pour les prompts courts, superposer les ψ des tokens individuels
        """
        if text in self._psi_cache:
            return self._psi_cache[text].copy()
        
        if self._semantic_encoder is not None:
            try:
                psi = self._semantic_encoder.encode(text)
                if psi is not None and psi.shape[0] == self.dim:
                    psi = normalize(psi)
                    self._psi_cache[text] = psi
                    return psi
            except Exception:
                pass
        
        # Fallback : wave_lang.encode (hash FNV-1a + φ-spacing)
        # Pour les prompts multi-mots, on superpose les ψ des tokens
        tokens = text.lower().split()
        if len(tokens) == 0:
            psi = encode("", dim=self.dim)
        elif len(tokens) == 1:
            psi = encode(tokens[0], dim=self.dim)
        else:
            # Superposer les ψ de chaque token (pondération par longueur)
            psis = []
            for tok in tokens:
                if len(tok) >= 2:  # ignorer les tokens trop courts
                    psis.append(encode(tok, dim=self.dim))
            if psis:
                psi = superpose(*psis)
            else:
                psi = encode(text, dim=self.dim)
        
        psi = normalize(psi)
        self._psi_cache[text] = psi
        return psi
    
    def _spectral_score(self, psi_prompt: np.ndarray, intent_id: str) -> float:
        """
        Score spectral : résonance entre ψ_prompt et ψ_intent.
        Retourne un score ∈ [-1, 1].
        """
        if intent_id not in self._psi_intents:
            return 0.0
        
        psi_intent = self._psi_intents[intent_id]
        score = float(resonate(psi_prompt, psi_intent))
        return score
    
    def _combined_score(self, text: str, psi_prompt: np.ndarray, 
                        intent_def: dict) -> Tuple[float, float, float]:
        """
        Score combiné : lexical (0-1) + spectral (-1,1) → score final pondéré.
        
        Pondération adaptative :
        - Avec semantic encoder : lexical 40%, spectral 60%
        - Sans semantic encoder : lexical 95%, spectral 5% (le hash n'est pas sémantique)
        
        Un bonus de priorité (tiny, ~0.01 max) est ajouté pour départager
        les intentions à scores très proches — la priorité la plus haute gagne.
        
        Returns:
            (final_score, lexical_score, spectral_score)
        """
        intent_id = intent_def['intent_id']
        
        lexical = self._lexical_score(text, intent_def)
        spectral = self._spectral_score(psi_prompt, intent_id)
        
        # Normaliser le spectral de [-1,1] vers [0,1]
        spectral_norm = (spectral + 1.0) / 2.0  # → [0, 1]
        
        if self._semantic_encoder is not None:
            # Mode sémantique : le spectral est fiable
            combined = 0.4 * lexical + 0.6 * spectral_norm
        else:
            # Mode hash-only : le spectral est du bruit → quasi ignoré
            combined = 0.95 * lexical + 0.05 * spectral_norm
        
        # Bonus de priorité (tiebreaker — assez fort pour départager les cas ambigus)
        priority = intent_def.get('priority', 50)
        priority_bonus = priority / 800.0  # max 0.1375 (priority=110)
        combined += priority_bonus
        
        # Pénalité pour les intents sans pattern matché (évite les faux positifs)
        if lexical < 0.01:
            combined *= 0.1  # quasi éliminé
        
        return min(combined, 1.0), lexical, spectral

    # ═══════════════════════════════════════════════════════════════════════════
    # EXTRACTION DE SLOTS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _extract_slots(self, text: str, intent_def: dict) -> Dict[str, Any]:
        """Extrait les slots/paramètres via les patterns définis."""
        slots = {}
        extractors = intent_def.get('slot_extractors', {})
        
        for slot_name, patterns in extractors.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    # Prendre le dernier groupe (le plus spécifique)
                    groups = match.groups()
                    if groups:
                        value = groups[-1].strip()
                        if value:
                            slots[slot_name] = value
                            break
        
        return slots
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DÉSAMBIGUÏSATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    AMBIGUITY_THRESHOLD = 0.12      # écart maximal entre top-1 et top-2 pour ambiguïté
    CONFIDENCE_MINIMUM = 0.12       # score minimum pour considérer une intention valide
                                    # (assez bas car lexical-only donne ~0.75 pour un hit)
    
    def _check_ambiguity(self, scores: List[Tuple[str, float]], 
                         top_n: int = 3) -> Tuple[bool, str]:
        """
        Détecte l'ambiguïté quand :
        - Le top score est trop bas (< CONFIDENCE_MINIMUM)
        - L'écart entre top-1 et top-2 est trop faible (< seuil adaptatif)
        
        Le seuil d'ambiguïté est adaptatif :
        - Si top > 0.80 : seuil = 0.05 (très confiant, besoin d'un gros écart)
        - Si top > 0.60 : seuil = 0.08 (modérément confiant)
        - Sinon : seuil = 0.12 (peu confiant)
        
        Returns:
            (is_ambiguous, clarification_question)
        """
        if not scores:
            return True, "Je n'ai pas bien compris. Pouvez-vous reformuler ?"
        
        if len(scores) == 1:
            top_score = scores[0][1]
            if top_score < self.CONFIDENCE_MINIMUM:
                return True, "Je ne suis pas sûr de comprendre. Que voulez-vous faire exactement ?"
            return False, ""
        
        top_intent, top_score = scores[0]
        second_intent, second_score = scores[1]
        
        # Seuil adaptatif selon la confiance
        # Plus le score est élevé, plus on tolère un petit écart
        if top_score >= 0.85:
            threshold = 0.002  # très confiant : seuls les écarts vraiment infimes déclenchent
        elif top_score >= 0.70:
            threshold = 0.05   # confiant : écart raisonnable requis
        elif top_score >= 0.50:
            threshold = 0.08   # modéré
        else:
            threshold = self.AMBIGUITY_THRESHOLD  # peu confiant
        
        # Cas 1 : score trop bas
        if top_score < self.CONFIDENCE_MINIMUM:
            return True, "Je n'ai pas bien compris votre demande. Pouvez-vous préciser ?"
        
        # Cas 2 : plusieurs intents proches
        gap = top_score - second_score
        if gap < threshold:
            # Exemption : si l'intention top a une priorité nettement plus haute,
            # elle mérite de gagner même avec un petit écart
            top_def = self._get_intent_def(top_intent)
            second_def = self._get_intent_def(second_intent)
            if top_def and second_def:
                priority_gap = top_def.get('priority', 50) - second_def.get('priority', 50)
                if priority_gap >= 25:  # écart de priorité significatif
                    log.debug(f"  Priority exemption: {top_intent}(prio={top_def.get('priority')}) "
                             f"> {second_intent}(prio={second_def.get('priority')}) gap={gap:.4f}")
                    return False, ""
            
            return True, self._build_ambiguity_question(top_intent, second_intent,
                                                        top_score, second_score)
        
        return False, ""
    
    def _build_ambiguity_question(self, top_intent: str, second_intent: str,
                                   top_score: float, second_score: float) -> str:
        """Construit une question de clarification contextuelle."""
        intents_fr = {
            'storage_action': 'nettoyer/compresser votre téléphone',
            'action_command': 'exécuter une action (appeler, envoyer un SMS…)',
            'arithmetic': 'faire un calcul',
            'specialize_request': 'créer un hologramme de connaissance',
            'learning': 'mémoriser une information',
            'comparison': 'comparer des choses',
            'generation': 'générer du contenu créatif',
            'greeting': 'simplement dire bonjour',
            'factual_question': 'poser une question de connaissance',
            'identity_question': 'me demander qui je suis',
            'general_chat': 'discuter',
        }
        
        desc_top = intents_fr.get(top_intent, top_intent)
        desc_sec = intents_fr.get(second_intent, second_intent)
        
        return (f"J'hésite entre {desc_top} ou {desc_sec}. "
                f"Que souhaitez-vous faire ?")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SEGMENTATION MULTI-INTENTIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    MULTI_INTENT_SEPARATORS = [
        r'\s+et\s+(?:ensuite|apr[eéèêë]s|puis|aussi|[eéèêë]galement)\s+',
        r'\s*;\s*',
        r'\s+puis\s+',
        r'\s+ensuite\s+',
        r'\s+apr[eéèêë]s\s+',
        r'\s*\.\s+(?=[a-zàâäéèêëîïôöùûüçæœ])',  # point suivi d'une phrase
    ]
    
    def _segment(self, text: str) -> List[str]:
        """
        Segmente un prompt multi-intentions en sous-prompts.
        Utilise des séparateurs explicites + heuristiques.
        
        Exemples :
          "compresse mes photos et ensuite analyse ma batterie"
          → ["compresse mes photos", "analyse ma batterie"]
        """
        # Vérifier si le texte contient un séparateur
        for sep_pattern in self.MULTI_INTENT_SEPARATORS:
            parts = re.split(sep_pattern, text, maxsplit=3)
            parts = [p.strip() for p in parts if p.strip()]
            if len(parts) >= 2:
                # Vérifier que chaque partie a une longueur minimale
                if all(len(p) > 5 for p in parts):
                    return parts
        
        # Pas de segmentation → prompt unique
        return [text]
    
    # ═══════════════════════════════════════════════════════════════════════════
    # COMPRÉHENSION PRINCIPALE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def comprehend(self, message: str, 
                   session_id: str = "",
                   user_id: str = "anonymous") -> PromptFrame:
        """
        Point d'entrée principal : comprend un prompt utilisateur.
        
        Args:
            message: Le texte du prompt utilisateur
            session_id: Identifiant de session (pour le contexte)
            user_id: Identifiant utilisateur
        
        Returns:
            PromptFrame avec l'intention, les slots, la confiance, etc.
        """
        if not message or not message.strip():
            return PromptFrame(
                original=message,
                normalized="",
                intent='general_chat',
                confidence=1.0,
                suggested_handler='greeting',
            )
        
        original = message.strip()
        normalized = self.normalize_text(original)
        
        # ── Encodage spectral ──
        psi_prompt = self._encode_prompt(normalized)
        
        # ── Segmentation multi-intentions ──
        segments_text = self._segment(normalized)
        segments = []
        if len(segments_text) > 1:
            for seg_text in segments_text:
                seg_frame = self.comprehend(seg_text, session_id, user_id)
                segments.append(seg_frame)
        
        # ── Calcul des scores pour toutes les intentions ──
        all_scores = {}
        for intent_def in self._intents:
            intent_id = intent_def['intent_id']
            combined, lexical, spectral = self._combined_score(
                normalized, psi_prompt, intent_def
            )
            all_scores[intent_id] = {
                'combined': round(combined, 4),
                'lexical': round(lexical, 4),
                'spectral': round(spectral, 4),
            }
        
        # ── Trier par score combiné décroissant ──
        ranked = sorted(all_scores.items(), 
                       key=lambda x: x[1]['combined'], 
                       reverse=True)
        
        # ── Prendre le top intent ──
        if not ranked:
            best_intent_id = 'general_chat'
            best_score = 0.0
        else:
            best_intent_id = ranked[0][0]
            best_score = ranked[0][1]['combined']
        
        # ── Vérifier l'ambiguïté ──
        score_tuples = [(intent_id, info['combined']) 
                       for intent_id, info in ranked[:5]]
        is_ambiguous, clarification = self._check_ambiguity(score_tuples)
        
        # ── Extraire les slots ──
        intent_def = self._get_intent_def(best_intent_id)
        slots = self._extract_slots(normalized, intent_def) if intent_def else {}
        
        # ── Construire le PromptFrame ──
        frame = PromptFrame(
            original=original,
            normalized=normalized,
            intent=best_intent_id,
            confidence=round(best_score, 4),
            slots=slots,
            segments=segments,
            psi_prompt=psi_prompt,
            ambiguity=is_ambiguous,
            clarification_question=clarification,
            suggested_handler=intent_def.get('handler', 'llm_fallback') if intent_def else 'llm_fallback',
            all_scores={k: v['combined'] for k, v in all_scores.items()},
            metadata={
                'session_id': session_id,
                'user_id': user_id,
                'all_details': all_scores,
            },
        )
        
        # ── Mettre à jour le contexte de session ──
        if session_id:
            self._update_session(session_id, frame)
        
        return frame
    
    def _get_intent_def(self, intent_id: str) -> Optional[dict]:
        """Récupère la définition d'une intention par son ID."""
        for intent_def in self._intents:
            if intent_def['intent_id'] == intent_id:
                return intent_def
        return None
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GESTION DU CONTEXTE DE SESSION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _update_session(self, session_id: str, frame: PromptFrame):
        """Met à jour le contexte holographique de la session."""
        if frame.psi_prompt is not None:
            if session_id in self._session_context:
                # Superposer au contexte existant (mémoire holographique)
                existing = self._session_context[session_id]
                self._session_context[session_id] = normalize(
                    superpose(existing, frame.psi_prompt)
                )
            else:
                self._session_context[session_id] = frame.psi_prompt.copy()
        
        self._session_last_intent[session_id] = frame.intent
    
    def get_session_context(self, session_id: str) -> Optional[np.ndarray]:
        """Récupère le contexte holographique d'une session."""
        return self._session_context.get(session_id)
    
    def reset_session(self, session_id: str):
        """Réinitialise le contexte d'une session."""
        self._session_context.pop(session_id, None)
        self._session_last_intent.pop(session_id, None)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # UTILITAIRES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def list_intents(self) -> List[Dict[str, str]]:
        """Liste toutes les intentions disponibles."""
        return [
            {
                'id': d['intent_id'],
                'handler': d['handler'],
                'description': d['description'],
                'priority': d['priority'],
                'keywords_count': len(d['keywords']),
                'patterns_count': len(d['patterns']),
            }
            for d in self._intents
        ]
    
    def stats(self) -> dict:
        """Statistiques du module."""
        return {
            'intents': len(self._intents),
            'dim': self.dim,
            'semantic_encoder': self._semantic_encoder is not None,
            'active_sessions': len(self._session_context),
            'psi_cache_size': len(self._psi_cache),
            'mechanism': '3 niveaux : lexical → spectral → sémantique',
            'ambiguity_threshold': self.AMBIGUITY_THRESHOLD,
            'confidence_minimum': self.CONFIDENCE_MINIMUM,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON — pour usage dans les routes
# ═══════════════════════════════════════════════════════════════════════════════

_comprehendor: Optional[PromptComprehendor] = None


def get_comprehendor() -> PromptComprehendor:
    """Récupère ou crée le singleton PromptComprehendor."""
    global _comprehendor
    if _comprehendor is None:
        _comprehendor = PromptComprehendor()
    return _comprehendor


def comprehend(message: str, session_id: str = "", 
               user_id: str = "anonymous") -> PromptFrame:
    """
    Fonction d'accès rapide : comprend un prompt en une ligne.
    
    Usage :
        from ka_server.services.prompt_comprehendor import comprehend
        
        frame = comprehend("nettoie mon téléphone")
        print(frame.intent)  # → 'storage_action'
        print(frame.suggested_handler)  # → 'storage_saver'
    """
    return get_comprehendor().comprehend(message, session_id, user_id)