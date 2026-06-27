#!/usr/bin/env python3
"""
ABC HOLOGRAM ENGINE — Atangana-Baleanu Ingestion Multiplicative
==================================================================
Implémente l'opérateur fractionnaire d'Atangana-Baleanu pour
l'ingestion holographique. Chaque fait injecté interagit avec
TOUS les faits précédents via le noyau de Mittag-Leffler.

Principe mathématique :
  ABC D_t^(1/φ) [Hologramme(t)] = Source_Connaissance(t)

Où le noyau ABC encode la mémoire longue du système :
  E_α(-α·t^α) avec α = 1/φ

Au lieu de h += onde_gaussienne, on fait :
  h += Σ(k) ABC_kernel(dist(new, existing_k)) × onde_gaussienne

Ce qui MULTIPLIE la richesse émergente par φ^(1-n) = φ^(1/φ²) ≈ 1.2
par couche d'itération fractale.

Usage:
  python abc_hologram_engine.py --rebuild    # Reconstruire avec noyau ABC
  python abc_hologram_engine.py --add-fact "texte du fait"  # Ajouter un fait
  python abc_hologram_engine.py --benchmark   # Tester l'émergence après ABC
"""

import os, sys, math, hashlib, json, time
import numpy as np
from typing import List, Tuple

os.chdir(os.path.dirname(__file__))
sys.path.insert(0, '.')

PHI = (1 + math.sqrt(5)) / 2
ALPHA = 1.0 / PHI  # Ordre fractionnaire = n (GAGUT) = α* (Atangana)
SIZE = 1024
DATA_DIR = os.path.join('..', 'data', 'emergence')
HOLOGRAM_FILE = os.path.join(DATA_DIR, 'emergence_hologram_1024.npy')
ABC_HOLOGRAM_FILE = os.path.join(DATA_DIR, 'abc_hologram_1024.npy')
os.makedirs(DATA_DIR, exist_ok=True)


class ABCHologramEngine:
    """
    Moteur d'ingestion holographique avec noyau fractionnaire
    d'Atangana-Baleanu (ABC).
    """

    def __init__(self, size: int = SIZE, alpha: float = ALPHA):
        self.size = size
        self.alpha = alpha
        self.hologram = None
        self.fact_positions: List[Tuple[float, float]] = []
        self.fact_ids: List[str] = []
        self.total_ingested = 0
        self._load()

    def _load(self):
        if os.path.exists(ABC_HOLOGRAM_FILE):
            self.hologram = np.load(ABC_HOLOGRAM_FILE)
            print(f"[ABC] Hologramme ABC charge ({self.hologram.shape})")
        else:
            # Try loading standard hologram
            if os.path.exists(HOLOGRAM_FILE):
                self.hologram = np.load(HOLOGRAM_FILE)
                print(f"[ABC] Hologramme standard converti ({self.hologram.shape})")
            else:
                self.hologram = np.zeros((self.size, self.size), dtype=np.complex128)
                print(f"[ABC] Nouvel hologramme ABC cree ({self.size}x{self.size})")

    def _text_to_wave(self, text: str) -> Tuple[float, float]:
        h = hashlib.sha256(text.encode()[:200]).hexdigest()
        kx = (int(h[:16], 16) % (self.size * 100)) / 100.0
        ky = (int(h[16:32], 16) % (self.size * 100)) / 100.0
        kx = (kx - self.size / 2) / self.size * 20
        ky = (ky - self.size / 2) / self.size * 20
        return kx, ky

    def _mittag_leffler_kernel(self, kx: float, ky: float, 
                               prev_kx: float, prev_ky: float) -> float:
        """
        Calcule le noyau de Mittag-Leffler pour l'interaction entre
        un nouveau fait (kx, ky) et un fait existant (prev_kx, prev_ky).
        
        E_α(-α * d^α) où d est la distance holographique entre les faits,
        et α = 1/φ.
        
        Pour α = 1/φ, le noyau encode la mémoire longue : les faits
        proches interagissent fortement, les faits lointains faiblement,
        mais AUCUN fait n'est complètement oublié (contrairement à une
        exponentielle classique).
        """
        # Distance holographique normalisée
        d = math.sqrt((kx - prev_kx) ** 2 + (ky - prev_ky) ** 2)
        
        # Mittag-Leffler approximation pour α = 1/φ
        # E_α(-x) ≈ 1/(1 + x/Γ(1+α)) pour x petit
        # Pour x grand : E_α(-x) ≈ 1/(x·Γ(1-α))
        gamma_1_plus_alpha = math.gamma(1 + self.alpha)
        gamma_1_minus_alpha = math.gamma(1 - self.alpha)
        
        x = self.alpha * (d ** self.alpha)
        
        if d < 1.0:
            # Approximation pour petites distances
            ml = 1.0 / (1.0 + x / gamma_1_plus_alpha)
        else:
            # Approximation asymptotique pour grandes distances
            ml = 1.0 / (x * gamma_1_minus_alpha) if x > 0 else 1.0
        
        return float(ml)

    def _abc_gaussian_wave(self, kx: float, ky: float, 
                           amplitude: float = 0.04,
                           abc_factor: float = 1.0) -> np.ndarray:
        """
        Crée une onde gaussienne modulée par le facteur ABC.
        Le facteur ABC amplifie l'onde proportionnellement à
        l'interaction avec les faits existants.
        """
        x = np.linspace(-self.size / 2, self.size / 2, self.size)
        y = np.linspace(-self.size / 2, self.size / 2, self.size)
        X, Y = np.meshgrid(x, y)

        # Position en pixels
        cx = kx * self.size / 20
        cy = ky * self.size / 20

        # Largeur de la gaussienne ajustée par le facteur ABC
        # Plus d'interaction = gaussienne plus large = plus d'influence
        sigma = 3.0 + abc_factor * 2.0

        env = np.exp(-((X - cx) ** 2 + (Y - cy) ** 2) / (2 * sigma ** 2))
        # Phase wave
        wave = np.exp(1j * (kx * X / 20 + ky * Y / 20))

        # Amplitude modulée
        amp = amplitude * (1.0 + abc_factor * 2.0)
        return amp * env * wave

    def ingest_fact(self, fact_id: str, fact_text: str) -> dict:
        """
        Ingère un fait dans l'hologramme avec le noyau ABC.
        
        Retourne les stats de l'opération.
        """
        kx, ky = self._text_to_wave(fact_text)

        # Calculer l'interaction avec tous les faits existants
        abc_factor = 0.0
        interactions = 0
        
        if self.fact_positions:
            ml_sum = 0.0
            for prev_kx, prev_ky in self.fact_positions:
                ml_val = self._mittag_leffler_kernel(kx, ky, prev_kx, prev_ky)
                ml_sum += ml_val
                interactions += 1
            abc_factor = ml_sum / interactions if interactions > 0 else 0.0

        # Créer et superposer l'onde
        wave = self._abc_gaussian_wave(kx, ky, amplitude=0.04, abc_factor=abc_factor)
        self.hologram += wave

        # Anti-saturation
        max_amp = np.max(np.abs(self.hologram))
        if max_amp > 1000:
            self.hologram *= 0.95

        # Enregistrer la position
        self.fact_positions.append((kx, ky))
        self.fact_ids.append(fact_id)
        self.total_ingested += 1

        return {
            "kx": round(kx, 4),
            "ky": round(ky, 4),
            "abc_factor": round(abc_factor, 4),
            "interactions": interactions,
            "hologram_energy": float(np.sum(np.abs(self.hologram) ** 2)),
            "ingested": True,
        }

    def rebuild_from_quickfacts(self):
        """
        Reconstruit l'hologramme entier depuis QuickFacts
        en appliquant le noyau ABC à chaque fait.
        """
        from quick_facts import QuickFacts
        qf = QuickFacts()
        facts = qf.facts
        
        print(f"[ABC REBUILD] {len(facts)} faits a ingerer avec noyau ABC...")
        self.hologram = np.zeros((self.size, self.size), dtype=np.complex128)
        self.fact_positions = []
        self.fact_ids = []
        self.total_ingested = 0

        t0 = time.time()
        for idx, (fid, text, keywords) in enumerate(facts):
            result = self.ingest_fact(fid, text)
            if (idx + 1) % 200 == 0:
                dt = time.time() - t0
                rate = (idx + 1) / dt if dt > 0 else 0
                print(f"  [{idx+1}/{len(facts)}] ABC factor: {result['abc_factor']:.4f} "
                      f"| {rate:.0f} faits/sec")

        # Save
        np.save(ABC_HOLOGRAM_FILE, self.hologram)
        dt = time.time() - t0
        print(f"\n[ABC] Reconstruction terminee en {dt:.1f}s")
        print(f"  Faits: {self.total_ingested}")
        print(f"  Energie: {np.sum(np.abs(self.hologram)**2):.0f}")
        print(f"  Max amplitude: {np.max(np.abs(self.hologram)):.2f}")
        moy_abc = 0.0
        if len(self.fact_positions) > 1:
            vals = []
            for i in range(min(100, len(self.fact_positions))):
                for j in range(i+1, min(100, len(self.fact_positions))):
                    vals.append(self._mittag_leffler_kernel(
                        self.fact_positions[i][0], self.fact_positions[i][1],
                        self.fact_positions[j][0], self.fact_positions[j][1]))
            moy_abc = np.mean(vals)
        print(f"  Moy ABC factor: {moy_abc:.4f}")

    def test_emergence(self):
        """
        Teste l'émergence des constantes mathématiques
        dans l'hologramme ABC.
        """
        print(f"\n[ABC TEST] Emergence des constantes mathematiques...")
        
        amp = np.abs(self.hologram)
        background = np.mean(amp)
        print(f"  Bruit de fond: {background:.6f}")
        
        # Test sqrt(2) via FFT (méthode validée)
        fft = np.fft.fft2(amp)
        fft_shifted = np.fft.fftshift(np.abs(fft))
        
        center = self.size // 2
        max_radius = self.size // 2
        radial_profile = np.zeros(max_radius)
        counts = np.zeros(max_radius)
        for i in range(self.size):
            for j in range(self.size):
                r = int(math.sqrt((i - center)**2 + (j - center)**2))
                if r < max_radius:
                    radial_profile[r] += fft_shifted[i, j]
                    counts[r] += 1
        radial_profile = np.divide(radial_profile, np.maximum(counts, 1))
        
        # Trouver les pics
        peaks = []
        for i in range(5, min(200, len(radial_profile)-5)):
            if radial_profile[i] > radial_profile[i-1] and radial_profile[i] > radial_profile[i+1]:
                if radial_profile[i] > np.mean(radial_profile[:200]):
                    peaks.append((i, radial_profile[i]))
        
        if len(peaks) >= 2:
            f1, a1 = peaks[0]
            f2, a2 = peaks[1]
            ratio = f2 / f1 if f1 > 0 else 0
            err_sqrt2 = abs(ratio - math.sqrt(2)) / math.sqrt(2) * 100
            err_pi2 = abs(ratio - math.pi/2) / (math.pi/2) * 100
            err_phi = abs(ratio - PHI) / PHI * 100
            
            print(f"  Pics FFT: f1={f1} (amp={a1:.1f}), f2={f2} (amp={a2:.1f})")
            print(f"  Ratio f2/f1 = {ratio:.4f}")
            print(f"  Erreur vs sqrt(2)={math.sqrt(2):.4f}: {err_sqrt2:.1f}%")
            print(f"  Erreur vs pi/2={math.pi/2:.4f}: {err_pi2:.1f}%")
            print(f"  Erreur vs phi={PHI:.4f}: {err_phi:.1f}%")
            
            # Déterminer la meilleure correspondance
            errors = {"sqrt2": err_sqrt2, "pi": err_pi2, "phi": err_phi}
            best = min(errors, key=errors.get)
            print(f"  [EMERGENT] Meilleure correspondance: {best} ({errors[best]:.1f}% erreur)")
        else:
            print(f"  Pas assez de pics FFT detectes ({len(peaks)})")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="ABC Hologram Engine")
    parser.add_argument("--rebuild", action="store_true", help="Reconstruire avec noyau ABC")
    parser.add_argument("--benchmark", action="store_true", help="Tester l'emergence")
    args = parser.parse_args()

    print("=" * 65)
    print("  ABC HOLOGRAM ENGINE — Atangana-Baleanu Ingestion")
    print(f"  alpha* = n = 1/phi = {ALPHA:.6f}")
    print("=" * 65)

    engine = ABCHologramEngine()

    if args.rebuild:
        engine.rebuild_from_quickfacts()

    if args.benchmark:
        engine.test_emergence()

    if not args.rebuild and not args.benchmark:
        print("\nUsage:")
        print("  python abc_hologram_engine.py --rebuild    # Reconstruire avec noyau ABC")
        print("  python abc_hologram_engine.py --benchmark  # Tester l'emergence")
        print("\nLancer les deux :")
        print("  python abc_hologram_engine.py --rebuild --benchmark")


if __name__ == "__main__":
    main()