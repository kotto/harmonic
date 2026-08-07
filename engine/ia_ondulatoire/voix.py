# -*- coding: utf-8 -*-
"""
voix.py — KA Voice : pont TTS vers le serveur voix existant (ka_voice_server :8420).

Le serveur voix (Piper offline, port 8420) est conservé tel quel ; le nouveau
moteur ondulatoire le proxie avec les mêmes contrats que ka_server :8765 :

    GET  /api/voice/health        → état du moteur Piper
    GET  /api/voice/offline/caps  → capacités offline
    POST /api/voice/stream        → WAV mono 16-bit (contrat PWA : text, emotion, voice)
    POST /api/voice/speak         → alias de stream

Dégradation propre : si le serveur voix est hors ligne, les routes répondent
503 avec un message clair (l'UI le gère).
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Dict, Optional, Tuple

PORT_VOIX = 8420

# émotion → (vitesse, voix) — réglages harmoniques légers
EMOTIONS = {
    "warm": (1.0, "fr_FR-siwis-medium"),
    "chaleureux": (1.0, "fr_FR-siwis-medium"),
    "calme": (0.95, "fr_FR-siwis-medium"),
    "joyeux": (1.05, "fr_FR-siwis-medium"),
    "neutre": (1.0, "fr_FR-siwis-medium"),
    "default": (1.0, "fr_FR-siwis-medium"),
}


class VoixOndulatoire:
    """Proxy ondulatoire vers le serveur voix Piper (ka_voice_server :8420)."""

    def __init__(self, base: str = f"http://127.0.0.1:{PORT_VOIX}",
                 timeout: float = 30.0):
        self.base = base.rstrip("/")
        self.timeout = timeout

    # ── état ────────────────────────────────────────────────────────────
    def sante(self) -> Dict:
        """GET /api/voice/health — état détaillé (ou dégradé si hors ligne)."""
        try:
            with urllib.request.urlopen(f"{self.base}/api/voice/health",
                                        timeout=4) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            return {"status": "offline", "piper_loaded": False,
                    "error": f"serveur voix injoignable ({self.base}) : {e}"}

    def capacites(self) -> Dict:
        """GET /api/voice/offline/caps — capacités offline."""
        try:
            with urllib.request.urlopen(f"{self.base}/api/voice/offline/caps",
                                        timeout=4) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            return {"offline_ready": False, "error": str(e)}

    # ── synthèse ────────────────────────────────────────────────────────
    def synthetiser(self, texte: str, voix: Optional[str] = None,
                    vitesse: float = 1.0, rehausse: bool = True) -> Tuple[bytes, Optional[str]]:
        """POST /api/voice/offline → (WAV bytes, erreur ou None)."""
        payload = json.dumps({"text": texte[:2000], "voice": voix,
                              "speed": vitesse, "enhanced": rehausse}).encode("utf-8")
        try:
            requete = urllib.request.Request(
                f"{self.base}/api/voice/offline", data=payload,
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(requete, timeout=self.timeout) as r:
                return r.read(), None
        except urllib.error.HTTPError as e:
            try:
                detail = json.loads(e.read().decode("utf-8"))
                return b"", f"serveur voix : {detail.get('error', e)}"
            except Exception:
                return b"", f"serveur voix : HTTP {e.code}"
        except Exception as e:
            return b"", f"serveur voix injoignable : {e}"

    def stream(self, texte: str, emotion: str = "warm",
               voix: Optional[str] = None) -> Dict:
        """Contrat PWA POST /api/voice/stream → {wav, mimetype} ou erreur."""
        texte = (texte or "").strip()
        if not texte:
            return {"error": "texte vide"}
        vitesse, voix_defaut = EMOTIONS.get((emotion or "default").lower(),
                                            EMOTIONS["default"])
        wav, erreur = self.synthetiser(texte, voix=voix or voix_defaut,
                                       vitesse=vitesse)
        if erreur:
            return {"error": erreur}
        return {"wav": wav, "mimetype": "audio/wav", "octets": len(wav),
                "latence_ms": 0}

    def sante_ok(self) -> bool:
        return self.sante().get("status") in ("ok", "degraded")
