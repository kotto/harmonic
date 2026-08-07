"""
🧠 enterprise_holograms.py — Hologrammes métier pour l'entreprise
===================================================================
Utilise enterprise_connector.py pour extraire les faits,
puis train_holograms.py pour créer les experts par département.

Usage :
  from enterprise_holograms import EnterpriseHolograms
  eh = EnterpriseHolograms()
  eh.train_all()                    # entraîne tous les hologrammes
  reponse = eh.ask("CA client Dupont ?")  # question → réponse

Intégration :
  Compatible avec enterprise_server.py (API REST existante)
  et hwat_bridge.py (fallback automatique)
"""

import sys, os, json, time, math
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

_ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE))


class EnterpriseHolograms:
    """Gestionnaire d'hologrammes métier pour l'entreprise."""

    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or (_ENGINE / "data")
        self.holograms_dir = self.data_dir / "holograms_enterprise"
        self.holograms_dir.mkdir(parents=True, exist_ok=True)
        self.connector = None
        self.router = None
        self._ready = False

    # ── Étape 1 : Extraire les faits ────────────────────────────

    def extract_faits(self) -> dict:
        """Extrait les faits et les groupe par secteur."""
        from enterprise_connector import EnterpriseConnector
        self.connector = EnterpriseConnector(self.data_dir)
        self.connector.extract_all()

        stats = self.connector.stats()
        print(f"  📊 {stats['total_faits']} faits, "
              f"{stats['secteurs']} secteurs")
        return self.connector.group_by_sector()

    # ── Étape 2 : Entraîner les hologrammes ─────────────────────

    def train_all(self, min_faits: int = 5, max_domaines: int = 10):
        """Entraîne un hologramme par secteur."""
        print("═" * 55)
        print("  🧠 ENTERPRISE HOLOGRAMS — Entraînement")
        print("═" * 55)

        # Extraire
        groups = self.extract_faits()

        # Filtrer
        eligible = [(s, f) for s, f in groups.items()
                    if len(f) >= min_faits]
        eligible.sort(key=lambda x: -len(x[1]))
        eligible = eligible[:max_domaines]

        if not eligible:
            print("  ⚠ Aucun secteur avec assez de faits.")
            return

        print(f"\n  {len(eligible)} domaines à entraîner:\n")

        # Entraîner chaque hologramme
        from train_holograms import train_hologram, MiniHWAT

        results = {}
        t0 = time.time()

        for i, (secteur, faits) in enumerate(eligible):
            print(f"  [{i+1}/{len(eligible)}] {secteur} "
                  f"({len(faits)} faits)...", end=" ")
            result = train_hologram(secteur, faits, self.holograms_dir)
            results[secteur] = result
            print(f"PPL={result.get('ppl', '?')}")

        dt = time.time() - t0
        print(f"\n  ✅ {len(results)} hologrammes en {dt:.0f}s")

        # Construire le routeur
        self._build_router(results)
        self._ready = True
        return results

    def _build_router(self, results: dict):
        """Construit le fichier router.json."""
        router = {'domains': {}}
        for secteur, result in results.items():
            if 'path' in result:
                router['domains'][secteur] = {
                    'path': result['path'],
                    'n_facts': result.get('n_facts', 0),
                    'ppl': result.get('ppl', 0),
                }
        router_path = self.holograms_dir / "router.json"
        with open(router_path, 'w') as f:
            json.dump(router, f, indent=2, ensure_ascii=False)
        print(f"  📡 Routeur: {router_path}")

    # ── Étape 3 : Interroger ────────────────────────────────────

    def ask(self, question: str) -> dict:
        """Pose une question au système d'hologrammes."""
        if not self._ready:
            # Essayer de charger le routeur existant
            router_path = self.holograms_dir / "router.json"
            if not router_path.exists():
                return {'error': 'Aucun hologramme entraîné. '
                        'Lancez .train_all() d\'abord.'}
            self._ready = True

        try:
            from hologram_router import HologramRouter
            # Router pointant vers les hologrammes entreprise
            self.router = HologramRouter(str(self.holograms_dir))
            result = self.router.query(question)
            result['status'] = 'ok'
            return result
        except Exception as e:
            return {'error': str(e), 'status': 'error'}

    def chat(self, message: str) -> str:
        """Interface conversationnelle simple."""
        result = self.ask(message)
        if 'error' in result:
            return f"❌ {result['error']}"

        parts = []
        for f in result.get('facts', []):
            parts.append(
                f"[{f['domain']}] confiance={f['confidence']:.0%}, "
                f"{f['n_facts']} faits"
            )
        return f"🌊 {result['question']}\n" + '\n'.join(parts)

    def info(self) -> dict:
        router_path = self.holograms_dir / "router.json"
        if router_path.exists():
            with open(router_path) as f:
                r = json.load(f)
            return {
                'status': 'ready',
                'domains': len(r['domains']),
                'list': list(r['domains'].keys()),
            }
        return {'status': 'not_trained'}


# ════════════════════════════════════════════════════════════════
# DÉMO
# ════════════════════════════════════════════════════════════════

def demo():
    import numpy as np

    print("═" * 55)
    print("  🧠 Enterprise Holograms — Démo complète")
    print("═" * 55)

    # Simuler des données enterprise
    from enterprise_connector import EnterpriseConnector
    ec = EnterpriseConnector()

    # Finance
    ec.from_dict({
        "finance": [
            {"id": "client_1", "nom": "Dupont SA", "ca": "450000", "secteur": "Industrie"},
            {"id": "client_2", "nom": "Martin SARL", "ca": "120000", "secteur": "Services"},
            {"id": "facture_01", "client": "client_1", "montant": "15000", "date": "2024-01-15"},
            {"id": "facture_02", "client": "client_2", "montant": "8000", "date": "2024-02-20"},
        ]
    }, secteur="FINANCE")

    # RH
    ec.from_dict({
        "rh": [
            {"id": "emp_1", "nom": "Alice", "departement": "R&D", "manager": "emp_3"},
            {"id": "emp_2", "nom": "Bob", "departement": "Finance", "manager": "emp_3"},
            {"id": "emp_3", "nom": "Charlie", "departement": "Direction", "manager": None},
            {"id": "emp_4", "nom": "Diane", "departement": "R&D", "manager": "emp_1"},
        ]
    }, secteur="RH")

    # Logistique
    ec.from_dict({
        "logistique": [
            {"id": "cmd_1", "client": "client_1", "statut": "expédiée", "date": "2024-07-20"},
            {"id": "cmd_2", "client": "client_2", "statut": "en préparation", "date": "2024-07-22"},
            {"id": "cmd_3", "client": "client_1", "statut": "livrée", "date": "2024-07-18"},
        ]
    }, secteur="LOGISTIQUE")

    ec.save("data/faits_entreprise_demo.json")
    stats = ec.stats()
    print(f"\n📊 {stats['total_faits']} faits extraits\n")

    # Entraîner les hologrammes
    eh = EnterpriseHolograms()
    eh.connector = ec  # injecter le connecteur déjà rempli

    # Override extract_faits pour utiliser les données déjà chargées
    original_extract = eh.extract_faits
    eh.extract_faits = lambda: ec.group_by_sector()

    results = eh.train_all(min_faits=3, max_domaines=5)

    # Test
    print(f"\n{'═'*55}")
    print(f"  TEST")
    print(f"{'═'*55}")

    tests = [
        "CA du client Dupont",
        "manager de Alice",
        "statut commande cmd_1",
    ]
    for q in tests:
        r = eh.ask(q)
        print(f"\n  Q: {q}")
        for f in r.get('facts', []):
            print(f"    → [{f['domain']}] conf={f['confidence']:.0%}, "
                  f"PPL={f.get('ppl','?')}")

    print(f"\n  ✅ Enterprise Holograms prêts.")


if __name__ == "__main__":
    demo()
