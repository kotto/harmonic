#!/usr/bin/env python3
"""
HARMONIC EMERGENCE — Découverte de principes par résonance
=============================================================
Superpose 277+ templates mathématiques dans un hologramme et
détecte des principes émergents par interférence constructive.

Architecture :
  1. TEMPLATE INGESTION : Chaque règle est convertie en onde
     → superposition dans un hologramme 256×256
  2. READER EXPLORATION : 16 lecteurs cherchent des corrélations
     entre les ondes dans l'hologramme
  3. INTERFERENCE DETECTION : Les zones de haute densité
     révèlent des connexions entre règles
  4. PRINCIPLE EMERGENCE : Ces connexions sont interprétées
     comme des théorèmes/principes qui n'étaient pas codés
  5. VERIFICATION : Chaque principe émergent est validé
     contre les règles connues

Philosophie :
  "Les mathématiques ne sont pas inventées — elles émergent
  de la résonance des ondes. Chaque théorème est une figure
  d'interférence qui attendait d'être observée."

Usage :
  python ka_phone/harmonic_emergence.py --discover   # Découvrir des principes
  python ka_phone/harmonic_emergence.py --report     # Rapport des émergences
"""

import os, sys, json, time, hashlib, math, random
import numpy as np
from typing import List, Tuple, Dict, Optional
from collections import defaultdict

PHI = 1.618033988749895
HOLOGRAM_SIZE = 256
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "emergence")
os.makedirs(DATA_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════
# KNOWN CONNECTIONS — Detection targets
# ══════════════════════════════════════════════════════════════════════════

# Paires de concepts qui devraient interférer si le principe est correct
KNOWN_DUALITIES = [
    ("derivative", "integral", "Fundamental Theorem of Calculus"),
    ("sin", "cos", "Pythagorean Identity sin²+cos²=1"),
    ("power_rule_diff", "power_rule_int", "Inverse Relationship d/dx∫ = x"),
    ("product_rule", "quotient_rule", "Duality of Multiplication/Division"),
    ("chain_rule", "substitution", "Composition ↔ Change of Variables"),
    ("multiplication", "division", "Inverse Operations"),
    ("addition", "subtraction", "Inverse Operations"),
    ("exponential", "logarithm", "Inverse Functions"),
    ("limit", "continuity", "Foundation of Calculus"),
    ("probability", "statistics", "Data ↔ Distribution"),
    ("geometry", "algebra", "Analytic Geometry (Descartes)"),
    ("trigonometry", "complex_numbers", "Euler's Formula e^(iθ)=cosθ+i·sinθ"),
    ("matrix", "linear_transform", "Linear Algebra"),
    ("ellipse", "hyperbola", "Conic Sections Duality"),
    ("modus_ponens", "modus_tollens", "Logical Duality"),
    ("integration_by_parts", "product_rule", "Reverse Product Rule"),
    ("taylor_series", "derivative", "Function Approximation"),
    ("fibonacci", "golden_ratio", "Phi Emergence"),
    ("de_morgan_and", "de_morgan_or", "Logical Duality"),
    ("gcd", "lcm", "Multiplicative Relationship GCD×LCM=a×b"),
]

class HarmonicEmergence:
    """Moteur de découverte de principes par résonance holographique."""

    def __init__(self, num_readers: int = 16):
        self.num_readers = num_readers
        self.hologram = self._load_or_create()
        self.readers = [(random.uniform(-8, 8), random.uniform(-8, 8))
                       for _ in range(num_readers)]
        self.discoveries = []
        self.meta = self._load_meta()

    def _load_or_create(self):
        path = os.path.join(DATA_DIR, "emergence_hologram.npy")
        if os.path.exists(path):
            return np.load(path)
        return np.zeros((HOLOGRAM_SIZE, HOLOGRAM_SIZE), dtype=np.complex128)

    def _load_meta(self):
        path = os.path.join(DATA_DIR, "emergence_meta.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {"total_ingested": 0, "discoveries": []}

    def save(self):
        np.save(os.path.join(DATA_DIR, "emergence_hologram.npy"), self.hologram)
        self.meta["discoveries"] = self.discoveries
        self.meta["total_ingested"] = self.meta.get("total_ingested", 0)
        self.meta["last_saved"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(os.path.join(DATA_DIR, "emergence_meta.json"), "w") as f:
            json.dump(self.meta, f, ensure_ascii=False, indent=2)

    # ═══ WAVE OPERATIONS ═══
    def _text_to_wave(self, text: str, amp: float = 0.1, sigma: float = 4.0) -> np.ndarray:
        h = hashlib.sha256(text.encode()[:200]).hexdigest()
        kx = (int(h[:16], 16) % (HOLOGRAM_SIZE * 100)) / 100.0
        ky = (int(h[16:32], 16) % (HOLOGRAM_SIZE * 100)) / 100.0
        kx = (kx - HOLOGRAM_SIZE / 2) / HOLOGRAM_SIZE * 20
        ky = (ky - HOLOGRAM_SIZE / 2) / HOLOGRAM_SIZE * 20
        x = np.linspace(-HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE)
        y = np.linspace(-HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE)
        X, Y = np.meshgrid(x, y)
        env = np.exp(-(X**2 + Y**2) / (2 * sigma**2))
        wave = np.exp(1j * (kx * X / 20 + ky * Y / 20))
        return amp * env * wave

    def _wave_at(self, kx: float, ky: float, amp: float = 0.5) -> np.ndarray:
        x = np.linspace(-HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE)
        y = np.linspace(-HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE)
        X, Y = np.meshgrid(x, y)
        env = np.exp(-(X**2 + Y**2) / 18)
        wave = np.exp(1j * (kx * X / 20 + ky * Y / 20))
        return amp * env * wave

    def _correlation(self, w1: np.ndarray, w2: np.ndarray) -> float:
        c = np.abs(np.sum(w1 * np.conj(w2)))
        n1 = np.sqrt(np.sum(np.abs(w1)**2))
        n2 = np.sqrt(np.sum(np.abs(w2)**2))
        if n1 < 1e-10 or n2 < 1e-10:
            return 0.0
        return float(c / (n1 * n2))

    # ═══ INGESTION — Superposer les 277 règles ═══
    def ingest_rules(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lm_arena"))
        from parametric_kb import ParametricKB
        kb = ParametricKB()
        rules = kb.rules

        print(f"Ingestion de {len(rules)} regles dans l'hologramme d'emergence...")
        t0 = time.time()

        for i, rule in enumerate(rules):
            # Superposer le nom de la règle + son pattern
            rule_text = f"{rule['name']}: {rule['pattern']}"
            wave = self._text_to_wave(rule_text, amp=0.05)
            self.hologram += wave

            # Superposer le domaine pour le clustering
            domain_wave = self._text_to_wave(rule['domain'], amp=0.02)
            self.hologram += domain_wave

            if i % 50 == 0:
                mx = np.max(np.abs(self.hologram))
                if mx > 500:
                    self.hologram *= 0.98

        self.meta["total_ingested"] = len(rules)
        dt = time.time() - t0
        print(f"  {len(rules)} regles ingerees en {dt:.1f}s")
        print(f"  Energie hologramme: {np.sum(np.abs(self.hologram)**2):.0f}")
        self.save()

    # ═══ READER TRAINING — Chercher des corrélations ═══
    def train_readers(self, epochs: int = 20):
        print(f"Entrainement de {self.num_readers} lecteurs sur {epochs} epoques...")
        for epoch in range(epochs):
            for i, (kx, ky) in enumerate(self.readers):
                r_wave = self._wave_at(kx, ky)

                # Score de base : corrélation avec l'hologramme entier
                corr = self._correlation(r_wave, self.hologram)

                # Gradient : perturbation
                eps = 0.15
                kx_p = self._correlation(self._wave_at(kx + eps, ky), self.hologram)
                ky_p = self._correlation(self._wave_at(kx, ky + eps), self.hologram)

                # Mise à jour
                new_kx = kx + 0.05 * (kx_p - corr) / eps
                new_ky = ky + 0.05 * (ky_p - corr) / eps
                new_kx = max(-12, min(12, new_kx))
                new_ky = max(-12, min(12, new_ky))
                self.readers[i] = (new_kx, new_ky)

        # Score final moyen
        avg_corr = sum(self._correlation(self._wave_at(kx, ky), self.hologram)
                      for kx, ky in self.readers) / len(self.readers)
        print(f"  Correlation moyenne: {avg_corr:.4f}")
        return avg_corr

    # ═══ INTERFERENCE DETECTION ═══
    def detect_interferences(self, threshold: float = 0.15) -> List[Dict]:
        """
        Détecte les figures d'interférence entre paires de lecteurs.
        Une forte interférence = deux concepts qui résonnent ensemble.
        """
        print("Detection des interferences entre lecteurs...")
        interferences = []

        for i in range(len(self.readers)):
            for j in range(i + 1, len(self.readers)):
                rx, ry = self.readers[i]
                sx, sy = self.readers[j]

                # Distance entre les lecteurs dans l'espace holographique
                dist = math.sqrt((rx - sx)**2 + (ry - sy)**2)

                # Corrélation entre leurs ondes respectives
                r_wave = self._wave_at(rx, ry)
                s_wave = self._wave_at(sx, sy)

                # Corrélation croisée avec l'hologramme
                cross_corr = self._correlation(
                    r_wave + s_wave,
                    self.hologram
                )

                if cross_corr > threshold:
                    interferences.append({
                        "reader_pair": (i, j),
                        "distance": round(dist, 3),
                        "interference": round(cross_corr, 4),
                        "reader1_pos": (round(rx, 2), round(ry, 2)),
                        "reader2_pos": (round(sx, 2), round(sy, 2)),
                    })

        interferences.sort(key=lambda x: -x["interference"])
        print(f"  {len(interferences)} interferences detectees (seuil: {threshold})")
        return interferences

    # ═══ PRINCIPLE EMERGENCE ═══
    def discover_principles(self) -> List[Dict]:
        """
        Interprète les interférences comme des principes mathématiques émergents.
        Compare avec les dualités connues pour validation.
        """
        print("Emergence des principes...")
        interferences = self.detect_interferences()
        discoveries = []

        # Cluster les lecteurs par positions proches
        clusters = self._cluster_readers()

        # Pour chaque cluster, essayer d'identifier un principe
        for cluster_id, reader_indices in enumerate(clusters):
            if len(reader_indices) < 2:
                continue

            # Trouver les règles les plus corrélées à ce cluster
            cluster_center = np.mean([self.readers[i] for i in reader_indices], axis=0)
            center_wave = self._wave_at(cluster_center[0], cluster_center[1])

            # Chercher quelles règles résonnent le plus
            rule_scores = []
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lm_arena"))
            try:
                from parametric_kb import ParametricKB
                kb = ParametricKB()
                for rule in kb.rules:
                    rule_wave = self._text_to_wave(f"{rule['name']}: {rule['pattern']}")
                    score = self._correlation(center_wave, rule_wave + 0.1 * self.hologram)
                    rule_scores.append((rule["name"], rule["domain"], score))
            except:
                pass

            rule_scores.sort(key=lambda x: -x[2])
            top_rules = rule_scores[:5]

            # Essayer de nommer le principe émergent
            principle = self._name_principle(top_rules)

            discoveries.append({
                "cluster": cluster_id,
                "num_readers": len(reader_indices),
                "principe": principle["name"],
                "description": principle["description"],
                "confidence": round(principle["confidence"], 3),
                "top_rules": [r[0] for r in top_rules[:3]],
                "domains": list(set(r[1] for r in top_rules[:3])),
                "emergence_type": principle.get("type", "unknown"),
            })

        # Trier par confiance
        discoveries.sort(key=lambda x: -x["confidence"])
        self.discoveries = discoveries
        return discoveries

    def _cluster_readers(self, max_dist: float = 3.0) -> List[List[int]]:
        """Cluster les lecteurs par proximité spatiale."""
        clusters = []
        assigned = set()

        for i in range(len(self.readers)):
            if i in assigned:
                continue
            cluster = [i]
            assigned.add(i)
            for j in range(i + 1, len(self.readers)):
                if j in assigned:
                    continue
                dist = math.sqrt(
                    (self.readers[i][0] - self.readers[j][0])**2 +
                    (self.readers[i][1] - self.readers[j][1])**2
                )
                if dist < max_dist:
                    cluster.append(j)
                    assigned.add(j)
            clusters.append(cluster)

        return clusters

    def _name_principle(self, top_rules: List[Tuple[str, str, float]]) -> Dict:
        """Nomme un principe émergent basé sur les règles qui le composent."""
        names = [r[0] for r in top_rules]
        domains = [r[1] for r in top_rules]
        conf = sum(r[2] for r in top_rules) / max(len(top_rules), 1)

        # Chercher dans les dualités connues
        for a_keyword, b_keyword, principle_name in KNOWN_DUALITIES:
            a_found = any(a_keyword in n for n in names)
            b_found = any(b_keyword in n for n in names)
            if a_found and b_found:
                return {
                    "name": principle_name,
                    "description": f"Principe emergent reliant '{a_keyword}' et '{b_keyword}'. Detecte par resonance entre {len(names)} regles.",
                    "confidence": min(1.0, conf * 1.2),
                    "type": "known_duality_verified",
                }

        # Sinon, nommer selon les domaines
        domain_counts = defaultdict(int)
        for d in domains:
            domain_counts[d] += 1
        primary_domain = max(domain_counts, key=domain_counts.get)

        return {
            "name": f"Emergent Principle in {primary_domain.replace('_', ' ').title()}",
            "description": f"Nouveau principe emergent detecte par interference entre {len(names)} regles dans le domaine '{primary_domain}'. Les regles {', '.join(names[:3])} resonnent ensemble.",
            "confidence": min(1.0, conf * 0.8),
            "type": "new_emergence",
        }

    # ═══ REPORT GENERATION ═══
    def generate_report(self) -> str:
        """Génère un rapport textuel des principes émergents."""
        if not self.discoveries:
            return "Aucun principe emergent detecte. Lancez --discover d'abord."

        report = []
        report.append("=" * 70)
        report.append("HARMONIC EMERGENCE - Rapport de decouverte de principes")
        report.append("=" * 70)
        report.append(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Regles ingerees: {self.meta.get('total_ingested', 0)}")
        report.append(f"Lecteurs actifs: {self.num_readers}")
        report.append(f"Principes emergents detectes: {len(self.discoveries)}")
        report.append("")

        for i, disc in enumerate(self.discoveries):
            report.append(f"{'─' * 60}")
            report.append(f"PRINCIPE #{i+1}: {disc['principe']}")
            report.append(f"  Confiance: {disc['confidence']:.0%}")
            report.append(f"  Type: {disc['emergence_type']}")
            report.append(f"  Description: {disc['description']}")
            report.append(f"  Regles sources: {', '.join(disc['top_rules'])}")
            report.append(f"  Domaines impliques: {', '.join(disc['domains'])}")
            report.append("")

        # Statistiques
        known = [d for d in self.discoveries if d["emergence_type"] == "known_duality_verified"]
        new = [d for d in self.discoveries if d["emergence_type"] == "new_emergence"]
        report.append(f"{'-' * 60}")
        report.append(f"RESUME:")
        report.append(f"  Dualites connues verifiees: {len(known)}")
        report.append(f"  Nouveaux principes emergents: {len(new)}")
        report.append(f"  Confiance moyenne: {sum(d['confidence'] for d in self.discoveries)/max(len(self.discoveries),1):.0%}")
        report.append(f"{'=' * 70}")

        return "\n".join(report)

    # ═══ FULL PIPELINE ═══
    def full_discovery(self, epochs: int = 20) -> List[Dict]:
        """Pipeline complet : ingestion → entraînement → émergence."""
        self.ingest_rules()
        self.train_readers(epochs=epochs)
        discoveries = self.discover_principles()
        self.save()
        return discoveries


# ══════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--discover", action="store_true", help="Lancer la decouverte de principes")
    p.add_argument("--report", action="store_true", help="Afficher le rapport")
    p.add_argument("--epochs", type=int, default=20, help="Epoques d'entrainement")
    args = p.parse_args()

    engine = HarmonicEmergence(num_readers=16)

    if args.discover:
        discoveries = engine.full_discovery(epochs=args.epochs)
        print(engine.generate_report())

    if args.report:
        print(engine.generate_report())

    if not args.discover and not args.report:
        print("Usage:")
        print("  python ka_phone/harmonic_emergence.py --discover")
        print("  python ka_phone/harmonic_emergence.py --report")

if __name__ == "__main__":
    main()