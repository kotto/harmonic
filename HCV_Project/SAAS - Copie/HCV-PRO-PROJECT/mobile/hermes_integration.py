"""
HCV PRO - Hermes Integration
Stub local — remplace le package 'hermes-agent' avec intégration système.

Expose les métriques système réelles (CPU, RAM, handles ouverts)
via psutil. Étendre ici pour brancher un vrai service Hermes
si/quand il devient disponible.
"""

import time
import threading
import psutil
from typing import Optional


class HermesService:
    """
    Service d'intégration Hermes.
    Actuellement : métriques système réelles via psutil.
    Interface stable — brancher un backend réel sans changer bridge_server.py.
    """

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stats = {
            'active_handles': 0,
            'cpu_percent': 0.0,
            'ram_used_mb': 0,
            'ram_total_mb': 0,
        }
        self._lock = threading.Lock()

    def start(self):
        """Démarre la collecte de métriques en arrière-plan."""
        self._running = True
        self._thread = threading.Thread(
            target=self._poll_loop,
            daemon=True,
            name="hermes-poll"
        )
        self._thread.start()
        print("🪶 HermesService démarré (métriques système).")

    def stop(self):
        """Arrête proprement."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        print("🪶 HermesService arrêté.")

    def get_stats(self) -> dict:
        """Retourne un snapshot thread-safe des dernières métriques."""
        with self._lock:
            return dict(self._stats)

    # ------------------------------------------------------------------
    # Boucle interne
    # ------------------------------------------------------------------

    def _poll_loop(self):
        """Met à jour les métriques toutes les secondes."""
        proc = psutil.Process()

        while self._running:
            try:
                ram = psutil.virtual_memory()
                # Sur Windows, open_files() peut lever AccessDenied
                try:
                    handles = len(proc.open_files())
                except (psutil.AccessDenied, OSError):
                    handles = proc.num_handles() if hasattr(proc, 'num_handles') else 0

                with self._lock:
                    self._stats = {
                        'active_handles': handles,
                        'cpu_percent': psutil.cpu_percent(interval=None),
                        'ram_used_mb': ram.used // (1024 * 1024),
                        'ram_total_mb': ram.total // (1024 * 1024),
                    }
            except Exception as e:
                print(f"[Hermes] Erreur collecte métriques : {e}")

            time.sleep(1.0)
