"""
🌊 WaveContextManager — Contexte conversationnel ondulatoire
=============================================================
Maintient le contexte d'une conversation longue via 3 couches THU :

  Couche 1 — Fenêtre glissante (Slot Window)
    Les N derniers échanges (bruts, précision immédiate)

  Couche 2 — Mémoire holographique (Wave Memory)
    superpose(ψ_tour_1, ψ_tour_2, …, ψ_tour_n) ∈ ℂ⁵¹²
    L'ESSENCE sémantique de TOUTE la conversation, compressée
    dans un seul vecteur. Ne vieillit jamais, ne sature pas.

  Couche 3 — Résumé neuronal (Summary)
    Généré en arrière-plan par Phi dès que SUMMARY_TRIGGER est franchi,
    à partir de l'historique complet (_all_turns) — pas seulement de la
    fenêtre glissante. Aimable, non bloquant.

Usage :
  from wave_context_manager import WaveContextManager
  ctx = WaveContextManager(session_id="sess_abc")
  ctx.add_turn("user", "bonjour")
  prompt = ctx.build_prompt(current_message="...")
"""

import json
import logging
import sys
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional
from collections import deque

import numpy as np

log = logging.getLogger(__name__)

_WAVE_DIR = Path(__file__).resolve().parent.parent.parent / 'vital-ka' / 'core' / 'python'
if str(_WAVE_DIR) not in sys.path:
    sys.path.insert(0, str(_WAVE_DIR))

from wave_lang import (  # noqa: E402
    encode, normalize, superpose, resonate,
)

DIM = 512
MAX_SLOTS = 6
SUMMARY_TRIGGER = 8
MAX_HISTORY = 50        # historique complet borné (approx. 20 derniers tours utile pour résumés)
SESSION_TTL_S = 2 * 3600  # expiration des sessions inactives


class WaveContextManager:
    """Gestionnaire de contexte conversationnel à 3 couches."""

    def __init__(self, session_id: str = "", max_slots: int = MAX_SLOTS):
        self.session_id = session_id
        self.max_slots = max_slots

        # Couche 1 : fenêtre glissante
        self._slot_window: deque = deque(maxlen=max_slots)

        # Historique complet borné (pour le résumé)
        self._all_turns: deque = deque(maxlen=MAX_HISTORY)

        # Couche 2 : mémoire holographique
        self._psi_memory: Optional[np.ndarray] = None
        self._turn_count = 0

        # Couche 3 : résumé (async)
        self._summary: str = ""
        self._summary_turn = 0
        self._summary_thread: Optional[threading.Thread] = None

        self._psi_cache: Dict[str, np.ndarray] = {}
        self.last_access = time.time()

    # ═══════════════════════════════════════════════════════════════════════
    # AJOUT D'UN TOUR
    # ═══════════════════════════════════════════════════════════════════════
    def add_turn(self, role: str, content: str):
        self.last_access = time.time()
        turn = {"role": role, "content": content, "turn": self._turn_count}
        self._slot_window.append(turn)
        self._all_turns.append(turn)

        psi_turn = self._encode_turn(role, content)
        if self._psi_memory is None:
            self._psi_memory = normalize(psi_turn)
        else:
            weight = 1.0 + (self._turn_count / 100.0)
            self._psi_memory = normalize(superpose(self._psi_memory, psi_turn * weight))

        self._turn_count += 1

        # Déclencher régénération du résumé en arrière-plan
        if self._turn_count - self._summary_turn >= SUMMARY_TRIGGER:
            self._start_summary_thread()

    # ═══════════════════════════════════════════════════════════════════════
    # ENCODAGE
    # ═══════════════════════════════════════════════════════════════════════
    def _encode_turn(self, role: str, content: str) -> np.ndarray:
        key = f"{role}:{content[:50]}"
        if key in self._psi_cache:
            return self._psi_cache[key].copy()
        psi_role = encode(role, dim=DIM)
        psi_content = encode(content[:200], dim=DIM)
        psi = normalize(superpose(psi_role, psi_content))
        self._psi_cache[key] = psi
        return psi

    def _detect_topic_shift(self, current_content: str) -> float:
        if self._psi_memory is None:
            return 1.0
        psi_current = self._encode_turn("user", current_content)
        return float(resonate(psi_current, self._psi_memory))

    # ═══════════════════════════════════════════════════════════════════════
    # RÉSUMÉ ASYNC
    # ═══════════════════════════════════════════════════════════════════════
    def _start_summary_thread(self, phi_api: Optional[str] = None):
        """Lance un thread de régénération du résumé (sans bloquer)."""
        if self._summary_thread and self._summary_thread.is_alive():
            return  # déjà en cours
        if not phi_api:
            return  # pas de endpoint => pas de résumé

        def _work():
            summary = self._generate_summary(phi_api)
            if summary:
                self._summary = summary
                self._summary_turn = self._turn_count

        self._summary_thread = threading.Thread(target=_work, daemon=True)
        self._summary_thread.start()

    def _generate_summary(self, phi_api: str) -> str:
        """Résume les tours anciens (au-delà de la fenêtre glissante)."""
        # Tours anciens = historique complet hors fenêtre
        older = [t for t in list(self._all_turns)[:-self.max_slots]]
        if not older:
            return ""

        lines = []
        for t in older[-15:]:
            prefix = "User" if t["role"] == "user" else "Assistant"
            lines.append(f"{prefix}: {t['content'][:120]}")
        body = "\n".join(lines)
        prompt = (
            "Résume cette conversation en 2-3 phrases en gardant les infos clés :\n\n"
            + body + "\n\nRésumé:"
        )
        try:
            import requests
            r = requests.post(
                f"{phi_api}/phi/query",
                json={"question": prompt,
                      "system": "Tu es un assistant qui résume des conversations. Sois concis."},
                timeout=30,
            )
            data = r.json()
            return data.get("answer", "").strip()[:300]
        except Exception as e:
            log.debug(f"Summary generation failed: {e}")
            return ""

    # ═══════════════════════════════════════════════════════════════════════
    # CONSTRUCTION DU PROMPT
    # ═══════════════════════════════════════════════════════════════════════
    def build_prompt(self, current_message: str = "",
                     phi_api: str = None) -> str:
        parts = []
        # Couche 3
        if self._summary:
            parts.append(f"[RÉSUMÉ DE LA CONVERSATION]\n{self._summary}\n")
        # Couche 2 (note sujet)
        if self._psi_memory is not None and self._turn_count > 2 and current_message:
            if self._detect_topic_shift(current_message) < 0.2:
                parts.append(
                    "[NOTE: Changement de sujet détecté par rapport "
                    "à la conversation précédente.]\n"
                )
        # Couche 1
        if self._slot_window:
            parts.append("[HISTORIQUE RÉCENT]")
            for turn in self._slot_window:
                prefix = "Utilisateur" if turn["role"] == "user" else "Assistant"
                parts.append(f"{prefix}: {turn['content']}")
            parts.append("")
        # Message actuel
        if current_message:
            parts.append(f"Utilisateur: {current_message}")
            parts.append("Assistant:")
        return "\n".join(parts)

    # ═══════════════════════════════════════════════════════════════════════
    # UTILITAIRES
    # ═══════════════════════════════════════════════════════════════════════
    def get_slot_window(self) -> List[Dict]:
        return list(self._slot_window)

    def get_memory_energy(self) -> float:
        if self._psi_memory is None:
            return 0.0
        return float(np.sum(np.abs(self._psi_memory) ** 2))

    def get_topic_coherence(self, message: str) -> float:
        return self._detect_topic_shift(message)

    def reset(self):
        self._slot_window.clear()
        self._all_turns.clear()
        self._psi_memory = None
        self._turn_count = 0
        self._summary = ""
        self._summary_turn = 0
        self.last_access = time.time()

    def stats(self) -> dict:
        return {
            "session_id": self.session_id,
            "turns": self._turn_count,
            "slot_window_size": len(self._slot_window),
            "memory_energy": round(self.get_memory_energy(), 4),
            "has_summary": bool(self._summary),
            "max_slots": self.max_slots,
            "history_size": len(self._all_turns),
        }


# ═══ Gestionnaire global de sessions ═══
_session_managers: Dict[str, WaveContextManager] = {}
_sessions_lock = threading.Lock()


def _purge_expired_sessions():
    now = time.time()
    expired = [
        sid for sid, mgr in _session_managers.items()
        if now - mgr.last_access > SESSION_TTL_S
    ]
    for sid in expired:
        del _session_managers[sid]
    if expired:
        log.debug(f"Sessions expirées purgées: {len(expired)}")


def get_context(session_id: str) -> WaveContextManager:
    with _sessions_lock:
        _purge_expired_sessions()
        if session_id not in _session_managers:
            _session_managers[session_id] = WaveContextManager(session_id=session_id)
        return _session_managers[session_id]


def reset_session(session_id: str):
    if session_id in _session_managers:
        _session_managers[session_id].reset()
