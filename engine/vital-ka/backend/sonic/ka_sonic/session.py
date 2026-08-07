"""
SessionManager — Gestion des sessions TTS per-user avec TTL.

Chaque utilisateur a son propre HarmonicBridge isolé (cache KD-tree,
voix clonées, statistiques). Le modèle sous-jacent (banque de diphones
synthétiques) est partagé car stateless.

Thread-safe. Nettoyage automatique des sessions inactives.
"""

import time
import threading
import logging
from typing import Dict, Optional
from dataclasses import dataclass, field

log = logging.getLogger("ka_sonic.session")


@dataclass
class UserSession:
    """Session TTS isolée par utilisateur."""
    user_id: str
    bridge: object  # HarmonicBridge
    created_at: float = field(default_factory=time.time)
    last_access: float = field(default_factory=time.time)

    def touch(self):
        self.last_access = time.time()

    @property
    def idle_seconds(self) -> float:
        return time.time() - self.last_access


class SessionManager:
    """Gestionnaire de sessions TTS per-user avec TTL et éviction.

    Usage:
        mgr = SessionManager(ttl=3600, max_sessions=50)
        bridge = mgr.get_bridge("user_abc")
        wav = bridge.speak("Bonjour", voice="femme", emotion="joyeux")
    """

    def __init__(
        self,
        ttl: int = 3600,           # 1 heure d'inactivité → cleanup
        max_sessions: int = 50,     # max sessions simultanées
        sample_rate: int = 22050,
    ):
        self._sessions: Dict[str, UserSession] = {}
        self._lock = threading.Lock()
        self._ttl = ttl
        self._max_sessions = max_sessions
        self._sample_rate = sample_rate
        self._cleanup_interval = 300  # 5 minutes
        self._cleanup_thread: Optional[threading.Thread] = None
        self._running = False
        self._start_cleanup_daemon()

    # ── Sessions ────────────────────────────────────────────────────

    def get_bridge(self, user_id: str = "anonymous"):
        """Retourne (ou crée) le HarmonicBridge pour un utilisateur."""
        from .bridge import HarmonicBridge

        user_id = user_id.strip() or "anonymous"

        with self._lock:
            session = self._sessions.get(user_id)
            if session is not None:
                session.touch()
                return session.bridge

            # Limite de sessions → éviction du plus ancien
            if len(self._sessions) >= self._max_sessions:
                self._evict_oldest()

            # Créer un nouveau bridge avec sa propre banque
            bridge = HarmonicBridge(sr=self._sample_rate)
            bridge.build_bank()  # ~7s, une fois par user
            
            session = UserSession(user_id=user_id, bridge=bridge)
            self._sessions[user_id] = session
            log.info(f"👤 Session créée : {user_id} "
                     f"({len(self._sessions)} sessions actives)")
            return bridge

    def clone_voice(self, user_id: str, wav_path: str, name: str) -> bool:
        """Clone une voix dans la session de l'utilisateur."""
        bridge = self.get_bridge(user_id)
        return bridge.clone_voice(wav_path, name)

    def remove_session(self, user_id: str):
        """Supprime explicitement une session."""
        with self._lock:
            if user_id in self._sessions:
                del self._sessions[user_id]
                log.info(f"🗑️ Session supprimée : {user_id}")

    def _evict_oldest(self):
        """Évince la session la plus ancienne."""
        if not self._sessions:
            return
        oldest_id = min(
            self._sessions.keys(),
            key=lambda uid: self._sessions[uid].last_access,
        )
        log.warning(f"⚠️ Limite sessions ({self._max_sessions}) — éviction de {oldest_id}")
        del self._sessions[oldest_id]

    # ── Nettoyage ───────────────────────────────────────────────────

    def _start_cleanup_daemon(self):
        """Thread daemon de nettoyage périodique."""
        if self._cleanup_thread is not None:
            return
        self._running = True
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            name="tts-session-cleanup",
            daemon=True,
        )
        self._cleanup_thread.start()

    def _cleanup_loop(self):
        while self._running:
            time.sleep(self._cleanup_interval)
            self.cleanup_expired()

    def cleanup_expired(self) -> int:
        """Supprime les sessions inactives. Retourne le compte."""
        now = time.time()
        expired = []
        with self._lock:
            for uid, session in self._sessions.items():
                if now - session.last_access > self._ttl:
                    expired.append(uid)
            for uid in expired:
                del self._sessions[uid]
        if expired:
            log.info(f"🧹 Sessions expirées : {len(expired)}")
        return len(expired)

    def stop(self):
        """Arrête le thread de nettoyage."""
        self._running = False

    # ── Stats ───────────────────────────────────────────────────────

    def stats(self) -> dict:
        with self._lock:
            sessions = {
                uid: {
                    "created_at": s.created_at,
                    "last_access": s.last_access,
                    "idle_s": s.idle_seconds,
                }
                for uid, s in self._sessions.items()
            }
        return {
            "active_sessions": len(self._sessions),
            "max_sessions": self._max_sessions,
            "ttl_s": self._ttl,
            "sessions": sessions,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton global
# ═══════════════════════════════════════════════════════════════════════════════

_session_manager: Optional[SessionManager] = None
_manager_lock = threading.Lock()


def get_session_manager(**kwargs) -> SessionManager:
    """Retourne l'instance unique du gestionnaire de sessions."""
    global _session_manager
    if _session_manager is None:
        with _manager_lock:
            if _session_manager is None:
                _session_manager = SessionManager(**kwargs)
    return _session_manager
