"""
🌊 conversation_tuner.py — Fine-tuning conversationnel harmonique
=================================================================
Couche de fine-tuning pour optimiser l'expérience utilisateur en mode
conversationnel. Remplace le backprop des LLM par l'ajustement local
d'amplitudes φ — additif, O(1), sans oubli catastrophique.

Trois leviers (tous harmoniques, zéro gradient) :

  1. SURFACE (forme des phrases)
     → SurfaceMemory α : articles, expansions, style syntaxique.
     Le feedback ajuste α → la phraséologie devient celle que l'utilisateur
     aime (ex: utilisateur préfère « le hologramme » plutôt que « Un
     hologramme »).

  2. CONTENU (poids des faits)
     → Amplitudes des faits dans l'hologramme. Un fait apprécié gagne du
     poids (α += η), un fait ignoré/corrigé perd du poids. Le rappel
     pondère par l'amplitude → les faits que l'utilisateur valide remontent.

  3. PROFIL (préférences conversationnelles par utilisateur)
     → émotion préférée, style (warm/balanced/elegant), verbosité,
     correction du prénom, etc. Persisté par user_id.

Captures :
  - Explicite : /api/chat/feedback (rate 1-5, thumbs, correction)
  - Implicite : follow-up rapide = bon signe, abandon = mauvais signe,
    emoji de satisfaction, re-question = le fait n'a pas répondu.

Usage :
  from ka_server.services.conversation_tuner import get_tuner
  tuner = get_tuner()
  tuner.apply_feedback(user_id, rating=5, fact_text=..., phrase_keys=...)
  profile = tuner.get_profile(user_id)
"""

import json
import logging
import time
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

_ENGINE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = _ENGINE_DIR / 'data'
PROFILES_DIR = DATA_DIR / 'conversation_profiles'
PROFILES_DIR.mkdir(parents=True, exist_ok=True)

# ── Paramètres d'apprentissage (équivalents η de renforcement) ──
ETA_STRONG = 0.3      # feedback très positif (5/5, 👍, correction acceptée)
ETA_POSITIVE = 0.1    # feedback positif (4/5, follow-up)
ETA_NEGATIVE = -0.1   # feedback négatif (2/5, abandon)
ETA_STRONG_NEG = -0.3 # feedback très négatif (1/5, 👎, correction rejetée)
ETA_IMPLICIT = 0.05   # signal implicite faible

AMPLITUDE_MIN = 0.1   # plancher d'amplitude d'un fait
AMPLITUDE_MAX = 5.0   # plafond d'amplitude d'un fait


# ═══════════════════════════════════════════════════════════
# PROFIL CONVERSATIONNEL UTILISATEUR
# ═══════════════════════════════════════════════════════════

class UserConversationProfile:
    """Profil conversationnel d'un utilisateur, persisté en JSON."""

    DEFAULTS = {
        'user_name': '',
        'emotion_prefere': 'warm',           # émotion par défaut
        'style_prefere': 'balanced',          # warm | balanced | elegant | minimal
        # verbosité : 0 = court, 0.5 = normal, 1 = détaillé
        'verbosite': 0.5,
        'n_conversations': 0,
        'n_reponses': 0,
        'n_feedback': 0,
        'n_corrections': 0,
        # Historique des amplitudes par fait (contenu)
        'fact_amplitudes': {},               # fait_normalisé -> amplitude
        # Historique des goûts de phraséologie
        'surface_preferences': {},           # structure -> score
        'dernieres_reponses': [],            # (timestamp, question, réponse tronquée, rating)
    }

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.path = PROFILES_DIR / f'{user_id}.json'
        self.data = dict(self.DEFAULTS)
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text(encoding='utf-8'))
                for k, v in self.DEFAULTS.items():
                    self.data[k] = loaded.get(k, v)
            except Exception as e:
                log.warning(f"Profil {self.user_id} illisible: {e}")

    def save(self):
        try:
            self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=1),
                               encoding='utf-8')
        except Exception as e:
            log.warning(f"Profil {self.user_id} non sauvegardé: {e}")

    # ── Accès ──
    def get(self, key, default=None):
        return self.data.get(key, default if default is not None else self.DEFAULTS.get(key))

    def set(self, key, value):
        self.data[key] = value
        self.save()

    # ── Amplitudes de faits (fine-tuning du contenu) ──
    def fact_amplitude(self, fact_key: str, default: float = 1.0) -> float:
        return self.data['fact_amplitudes'].get(fact_key, default)

    def adjust_fact_amplitude(self, fact_key: str, delta: float):
        new = self.fact_amplitude(fact_key) + delta
        new = max(AMPLITUDE_MIN, min(AMPLITUDE_MAX, new))
        self.data['fact_amplitudes'][fact_key] = round(new, 3)

    # ── Préférences de surface (fine-tuning de la forme) ──
    def surface_score(self, structure_key: str) -> float:
        return self.data['surface_preferences'].get(structure_key, 0.0)

    def adjust_surface(self, structure_key: str, delta: float):
        self.data['surface_preferences'][structure_key] = round(
            self.surface_score(structure_key) + delta, 3)

    # ── Stats ──
    def to_dict(self) -> dict:
        return {k: v for k, v in self.data.items()}

    def __repr__(self):
        return (f"UserProfile({self.user_id}, émotion={self.data['emotion_prefere']}, "
                f"style={self.data['style_prefere']}, "
                f"feedback={self.data['n_feedback']})")


# ═══════════════════════════════════════════════════════════
# CONVERSATION TUNER
# ═══════════════════════════════════════════════════════════

class ConversationTuner:
    """Fine-tuning conversationnel global (tous utilisateurs)."""

    def __init__(self):
        self._profiles: Dict[str, UserConversationProfile] = {}
        # Mémoire de session : pour détecter le follow-up implicite
        self._session_state: Dict[str, dict] = {}   # session_id -> état

    # ── Accès profil ──
    def get_profile(self, user_id: str) -> UserConversationProfile:
        if user_id not in self._profiles:
            self._profiles[user_id] = UserConversationProfile(user_id)
        return self._profiles[user_id]

    # ═══════════════════════════════════════════════════════
    # FEEDBACK EXPLICITE
    # ═══════════════════════════════════════════════════════

    def apply_feedback(self, user_id: str, rating: float = 3.0,
                       fact_text: str = '', phrase_keys: List[str] = None,
                       correction: str = '', session_id: str = '',
                       question: str = '') -> dict:
        """
        Applique un feedback utilisateur au fine-tuning.

        Args:
            rating: 1-5 (ou 0.5/1 pour thumbs, -1/1)
            fact_text: le fait concerné (son amplitude sera ajustée)
            phrase_keys: clés de structure de phraséologie utilisées
            correction: si l'utilisateur corrige la réponse
            session_id: pour le contexte de session
            question: la question d'origine

        Returns:
            dict avec les ajustements effectués
        """
        profile = self.get_profile(user_id)
        profile.data['n_feedback'] += 1
        profile.data['n_reponses'] += 1

        # Normaliser le rating vers un delta η
        delta = self._rating_to_delta(rating, correction)

        operations = []

        # 1. Ajouter la correction comme fait appris (mémoire)
        if correction:
            from ka_server.services.memory_first import store_fact
            parts = correction.split('|')
            if len(parts) >= 3:
                s, r, o = parts[0].strip(), parts[1].strip(), parts[2].strip()
                try:
                    store_fact(s, r, o, source=f'correction_{user_id}')
                    operations.append(f'mémoire: ajout "{s} {r} {o}"')
                    profile.data['n_corrections'] += 1
                except Exception as e:
                    log.debug(f"Correction store failed: {e}")

        # 2. Ajuster l'amplitude du fait concerné
        if fact_text:
            fact_key = self._normalize_fact_key(fact_text)
            profile.adjust_fact_amplitude(fact_key, delta)
            operations.append(
                f"amplitude '{fact_key[:40]}...': +{delta:.2f} → "
                f"{profile.fact_amplitude(fact_key):.2f}")

        # 3. Ajuster les préférences de phraséologie
        if phrase_keys:
            for k in phrase_keys:
                profile.adjust_surface(k, delta * 0.5)
            operations.append(f"surface {len(phrase_keys)} structures: +{delta*0.5:.2f}")

        # 4. Ajuster l'émotion/le style selon le feedback positif
        if delta > 0:
            self._reinforce_style(profile, rating)

        # 5. Historique
        profile.data['dernieres_reponses'] = (
            [(time.time(), question[:80], fact_text[:80] if fact_text else '', rating)]
            + profile.data['dernieres_reponses']
        )[:20]

        profile.save()
        return {'delta': delta, 'operations': operations, 'profile': profile.to_dict()}

    # ═══════════════════════════════════════════════════════
    # FEEDBACK IMPLICITE (suivi de session)
    # ═══════════════════════════════════════════════════════

    def register_turn(self, session_id: str, user_id: str,
                      question: str, response: str, latency_ms: float = 0.0):
        """
        Enregistre un tour de conversation pour détecter les signaux implicites.
        Appelé à chaque réponse.
        """
        profile = self.get_profile(user_id)
        profile.data['n_conversations'] += 1
        profile.data['n_reponses'] += 1
        if profile.data['n_reponses'] % 50 == 0:
            profile.save()  # sauvegarde périodique

        # Stocker l'état de la session pour détecter le follow-up
        self._session_state[session_id] = {
            'ts': time.time(),
            'question': question,
            'response': response[:50],
            'user_id': user_id,
        }

    def detect_implicit(self, session_id: str, new_question: str,
                        latency_ms: float = 0.0) -> Optional[dict]:
        """
        Détecte le feedback implicite à la question suivante :
        - follow-up rapide (< 30s) sur le même sujet = bon signe
        - re-question du même concept = le fait n'a pas répondu (mauvais signe)
        - délai très long = l'utilisateur est parti (neutre)

        Returns:
            dict avec les ajustements implicites, ou None
        """
        state = self._session_state.get(session_id)
        if not state:
            return None

        dt = time.time() - state['ts']
        user_id = state['user_id']
        profile = self.get_profile(user_id)

        # Re-question très proche du même sujet (< 5s) = réponse insatisfaisante
        if dt < 5.0:
            old_question = state['question'].lower()
            new_lower = new_question.lower()
            # Chevauchement de mots-clés significatif
            overlap = set(old_question.split()) & set(new_lower.split())
            if overlap:
                profile.adjust_fact_amplitude(old_question[:60], ETA_STRONG_NEG)
                profile.save()
                return {'type': 're-question', 'delta': ETA_STRONG_NEG,
                        'message': 'L\'utilisateur a reposé une question proche → fait affaibli'}

        # Follow-up rapide (5-30s) = bon signe (l'utilisateur continue)
        if 5.0 < dt < 30.0:
            delta = ETA_IMPLICIT * 2
            profile.adjust_fact_amplitude(state['question'][:60], delta)
            profile.save()
            return {'type': 'follow-up', 'delta': delta,
                    'message': 'Follow-up rapide → renforcement doux'}

        return None

    # ═══════════════════════════════════════════════════════
    # UTILISATION DU PROFIL DANS LE PIPELINE
    # ═══════════════════════════════════════════════════════

    def get_response_params(self, user_id: str) -> dict:
        """
        Retourne les paramètres de réponse adaptés à l'utilisateur :
        - émotion par défaut
        - style WaveStylizer
        - verbosité (facteur de longueur de réponse)
        """
        profile = self.get_profile(user_id)
        return {
            'emotion': profile.data['emotion_prefere'],
            'style': profile.data['style_prefere'],
            'verbosite': profile.data['verbosite'],
        }

    def get_fact_weight(self, user_id: str, fact_text: str) -> float:
        """
        Retourne le poids (amplitude) d'un fait pour cet utilisateur.
        Utilisé pour pondérer le score de rappel.
        """
        profile = self.get_profile(user_id)
        return profile.fact_amplitude(self._normalize_fact_key(fact_text))

    # ═══════════════════════════════════════════════════════
    # INTERNES
    # ═══════════════════════════════════════════════════════

    def _rating_to_delta(self, rating: float, correction: str = '') -> float:
        """Convertit un rating 1-5 (ou thumbs -1/1) en delta η."""
        if correction:
            return ETA_STRONG  # une correction acceptée = fort renforcement

        if rating in (-1, 0.5) or (isinstance(rating, (int, float)) and rating <= 1.0):
            return ETA_STRONG_NEG
        if rating <= 2.0:
            return ETA_NEGATIVE
        if rating <= 3.0:
            return 0.0  # neutre
        if rating <= 4.0:
            return ETA_POSITIVE
        return ETA_STRONG  # 5/5

    def _reinforce_style(self, profile: UserConversationProfile, rating: float):
        """Renforce le style utilisé lors d'un bon feedback."""
        # Incrémenter le compteur de style en cours (le style actif est
        # celui appliqué en dernier — on le devine via le profil)
        # Dans une vraie intégration, on saurait quel style a servi.
        pass

    @staticmethod
    def _normalize_fact_key(text: str) -> str:
        """Normalise un fait en clé stable pour les amplitudes."""
        t = unicodedata.normalize('NFD', text.lower())
        t = t.encode('ascii', 'ignore').decode('ascii')
        return re.sub(r'\s+', ' ', t).strip()[:120]

    def stats(self) -> dict:
        return {
            'profiles': len(self._profiles),
            'users': list(self._profiles.keys()),
        }


# ── Import de re (pour normalise) ──
import re  # noqa: E402

# ── Singleton ──
_tuner: Optional[ConversationTuner] = None


def get_tuner() -> ConversationTuner:
    global _tuner
    if _tuner is None:
        _tuner = ConversationTuner()
    return _tuner


# ═══════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("🌊 Conversation Tuner — Test")

    tuner = get_tuner()

    # 1. Feedback positif sur un fait
    print("\n[1] Feedback positif (5/5) sur l'hologramme...")
    r = tuner.apply_feedback('sophie', rating=5,
                             fact_text='hologramme est une figure d interference',
                             phrase_keys=['surface|le hologramme', 'pred|est une'],
                             question='c est quoi un hologramme')
    print(f"   Delta: {r['delta']} · {r['operations'][:2]}")

    # 2. Profil créé
    print("\n[2] Profil utilisateur...")
    prof = tuner.get_profile('sophie')
    print(f"   {prof}")
    print(f"   Amplitude 'hologramme...': {prof.fact_amplitude('hologramme est une figure d interference')}")
    print(f"   Préférences surface: {dict(list(prof.data['surface_preferences'].items())[:2])}")

    # 3. Feedback négatif sur un autre fait
    print("\n[3] Feedback négatif (2/5)...")
    r2 = tuner.apply_feedback('sophie', rating=2,
                              fact_text='lumiere est une onde electromagnetique',
                              question='qu est ce que la lumiere')
    print(f"   Delta: {r2['delta']} · amplitude: "
          f"{prof.fact_amplitude('lumiere est une onde electromagnetique')}")

    # 4. Feedback implicite (re-question rapide)
    print("\n[4] Feedback implicite...")
    tuner.register_turn('sess1', 'sophie', 'c est quoi un hologramme', 'Le hologramme est...')
    r3 = tuner.detect_implicit('sess1', 'mais c est quoi vraiment un hologramme')
    if r3:
        print(f"   {r3['type']}: {r3['message']}")
    else:
        print("   (aucun signal, délai normal)")

    # 5. Paramètres de réponse
    print("\n[5] Paramètres de réponse adaptés...")
    params = tuner.get_response_params('sophie')
    print(f"   {params}")
    print(f"   Poids du fait 'hologramme...': {tuner.get_fact_weight('sophie', 'hologramme est une figure d interference')}")

    print("\n✅ Conversation Tuner test terminé.")