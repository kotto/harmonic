"""
🔌 enterprise_connector.py — Extracteur de faits depuis le SI entreprise
==========================================================================
Transforme les données structurées de l'entreprise en faits (s,r,o,sec)
compatibles avec les hologrammes HWAT.

Sources supportées :
  - JSON (fichiers, APIs)
  - CSV (exports ERP, tableurs)
  - SQL (via connecteur psycopg2 optionnel)
  - Dictionnaires Python (intégration directe)
  - Base de faits existante (data/enterprise_tenants.json)

Usage :
  from enterprise_connector import EnterpriseConnector
  ec = EnterpriseConnector()
  faits = ec.extract_all()
  # → liste de (sujet, relation, objet, secteur)

Intégration avec l'existant :
  - Lit enterprise_tenants.json (structure existante)
  - Compatible avec enterprise_specializer.py
  - Extensible par plugins de connecteurs
"""

import sys, os, json, csv, re, io
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from collections import defaultdict

_ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE))


# ════════════════════════════════════════════════════════════════
# CONNECTEURS
# ════════════════════════════════════════════════════════════════

class EnterpriseConnector:
    """Extrait les faits de toutes les sources SI disponibles."""

    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or (_ENGINE / "data")
        self.faits: List[Tuple] = []

    # ── JSON ────────────────────────────────────────────────────

    def from_json(self, path: str, secteur: str = "GENERAL",
                  id_col: str = "id", relations: dict = None) -> List[Tuple]:
        """Extrait les faits d'un fichier JSON.

        Args:
            path: chemin vers le fichier JSON
            secteur: secteur métier (FINANCE, RH, etc.)
            id_col: colonne utilisée comme identifiant sujet
            relations: mapping {colonne_json: nom_relation}
        """
        faits = []
        full_path = Path(path)
        if not full_path.exists():
            full_path = self.data_dir / path

        if not full_path.exists():
            print(f"  ⚠ Fichier non trouvé: {path}")
            return faits

        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        items = data if isinstance(data, list) else [data]
        for item in items:
            sujet = str(item.get(id_col, f"item_{len(faits)}"))
            if relations:
                for col, rel in relations.items():
                    if col in item and item[col] is not None:
                        faits.append((sujet, rel, str(item[col]), secteur))
            else:
                # Auto-détection : toutes les colonnes → faits
                for k, v in item.items():
                    if k != id_col and v is not None:
                        faits.append((sujet, f"a_pour_{k}", str(v), secteur))

        print(f"  JSON {path}: {len(faits)} faits → {secteur}")
        self.faits.extend(faits)
        return faits

    # ── CSV ────────────────────────────────────────────────────

    def from_csv(self, path: str, secteur: str = "GENERAL",
                 id_col: int = 0) -> List[Tuple]:
        """Extrait les faits d'un fichier CSV."""
        faits = []
        full_path = Path(path)
        if not full_path.exists():
            full_path = self.data_dir / path

        if not full_path.exists():
            print(f"  ⚠ Fichier non trouvé: {path}")
            return faits

        with open(full_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            if not headers:
                return faits

            for row in reader:
                sujet = row[id_col] if id_col < len(row) else f"ligne_{len(faits)}"
                for i, val in enumerate(row):
                    if i != id_col and val and headers[i]:
                        faits.append((sujet, f"a_pour_{headers[i]}",
                                     val, secteur))

        print(f"  CSV {path}: {len(faits)} faits → {secteur}")
        self.faits.extend(faits)
        return faits

    # ── Dictionnaire / Structure Python ─────────────────────────

    def from_dict(self, data: dict, secteur: str = "GENERAL",
                  prefix: str = "ent") -> List[Tuple]:
        """Extrait les faits d'un dictionnaire Python (intégration directe)."""
        faits = []
        for key, value in data.items():
            if isinstance(value, dict):
                # Sous-objet : relations nommées
                sujet = f"{prefix}_{key}"
                for sub_key, sub_val in value.items():
                    faits.append((sujet, f"a_pour_{sub_key}",
                                 str(sub_val), secteur))
            elif isinstance(value, list):
                sujet = f"{prefix}_{key}"
                for i, item in enumerate(value):
                    faits.append((sujet, f"contient", str(item)[:100], secteur))
            else:
                faits.append((f"{prefix}_{key}", "vaut", str(value), secteur))
        self.faits.extend(faits)
        return faits

    # ── Base existante (enterprise_tenants.json) ─────────────────

    def from_existing_tenants(self) -> List[Tuple]:
        """Extrait les faits de la base existante enterprise_tenants.json."""
        path = self.data_dir / "enterprise_tenants.json"
        if not path.exists():
            return []

        with open(path, 'r', encoding='utf-8') as f:
            tenants = json.load(f)

        faits = []
        for tenant_id, tdata in tenants.items():
            secteur = tdata.get('sector', 'GENERAL')
            if 'patterns' in tdata:
                for pname, pdata in tdata['patterns'].items():
                    faits.append((f"tenant_{tenant_id}", "a_pattern",
                                 pname, secteur))
            if 'history' in tdata:
                for entry in tdata['history']:
                    faits.append((f"tenant_{tenant_id}", "a_traite",
                                 entry.get('symptom', '')[:80], secteur))

        print(f"  Tenants: {len(faits)} faits")
        self.faits.extend(faits)
        return faits

    # ── Extraction complète ─────────────────────────────────────

    def extract_all(self) -> List[Tuple]:
        """Extrait TOUS les faits de TOUTES les sources disponibles."""
        self.faits = []

        # 1. Tenants existants
        self.from_existing_tenants()

        # 2. Données d'entreprise (si présentes)
        for f in (self.data_dir / "enterprises").glob("*.json"):
            self.from_json(str(f), secteur=f.stem.upper())

        # 3. Uploads
        for tenant_dir in (self.data_dir / "enterprise_uploads").iterdir():
            if tenant_dir.is_dir():
                for f in tenant_dir.glob("*.json"):
                    self.from_json(str(f), secteur=tenant_dir.name[:20])

        return self.faits

    # ── Groupement par secteur ──────────────────────────────────

    def group_by_sector(self) -> Dict[str, List[Tuple]]:
        groups = defaultdict(list)
        for s, r, o, sec in self.faits:
            groups[sec].append((s, r, o, sec))
        return dict(groups)

    # ── Sauvegarde ──────────────────────────────────────────────

    def save(self, path: str = None):
        if path is None:
            path = self.data_dir / "faits_entreprise.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump([list(f) for f in self.faits], f, ensure_ascii=False, indent=2)
        print(f"  ✅ {len(self.faits)} faits sauvegardés → {path}")

    def stats(self) -> dict:
        groups = self.group_by_sector()
        return {
            'total_faits': len(self.faits),
            'secteurs': len(groups),
            'par_secteur': {s: len(f) for s, f in
                           sorted(groups.items(), key=lambda x: -len(x[1]))[:10]}
        }


# ════════════════════════════════════════════════════════════════
# DÉMO
# ════════════════════════════════════════════════════════════════

def demo():
    print("═" * 55)
    print("  🔌 Enterprise Connector — Démo")
    print("═" * 55)

    ec = EnterpriseConnector()

    # Simuler des données d'entreprise
    demo_finance = [
        {"id": "client_1", "nom": "Dupont SA", "ca": "450000", "secteur": "Industrie"},
        {"id": "client_2", "nom": "Martin SARL", "ca": "120000", "secteur": "Services"},
        {"id": "facture_2024_01", "client": "client_1", "montant": "15000", "date": "2024-01-15"},
        {"id": "facture_2024_02", "client": "client_2", "montant": "8000", "date": "2024-02-20"},
    ]
    demo_rh = [
        {"id": "emp_1", "nom": "Alice", "departement": "R&D", "manager": "emp_3"},
        {"id": "emp_2", "nom": "Bob", "departement": "Finance", "manager": "emp_3"},
        {"id": "emp_3", "nom": "Charlie", "departement": "Direction", "manager": None},
    ]

    # Extraction
    ec.from_dict({"demo_finance": demo_finance}, secteur="FINANCE")
    ec.from_dict({"demo_rh": demo_rh}, secteur="RH")

    # Existant
    ec.from_existing_tenants()

    # Stats
    stats = ec.stats()
    print(f"\n  Total: {stats['total_faits']} faits, {stats['secteurs']} secteurs")
    for sec, n in stats['par_secteur'].items():
        print(f"    {sec}: {n}")

    print(f"\n  ✅ Connecteur prêt.")


if __name__ == "__main__":
    demo()
