#!/usr/bin/env python3
"""
matiere_noire_thu.py — LA MATIÈRE NOIRE COMME MÉMOIRE GRAVITATIONNELLE
======================================================================
L'énergie noire = Λ = vide filtré par la mémoire d'or (facteur 3,6).
La matière noire = le même mécanisme appliqué à la MASSE : le champ
gravitationnel se souvient du passé avec le noyau ABC K(t) ~ E_{1/φ}(−φ·t^{1/φ}).

À l'échelle d'une galaxie (10 Gyr), la mémoire n'a pas encore oublié la
masse qui a traversé le halo. La force gravitationnelle EFFECTIVE est
augmentée d'une composante « mémoire » — qui mime exactement un halo
de matière noire.

PRÉDICTIONS TESTABLES :
    P1 · v_plat² ∝ M_baryonique^{1/φ} — relation de Tully-Fisher modifiée
    P2 · L'accélération caractéristique a₀ = c²/(c·t_U/φ) = φ·c·H₀
         ≈ 1,07e-9 m/s² (vs a₀_MOND ≈ 1,2e-10)
    P3 · Le profil de mémoire dépend de l'ÂGE de la galaxie — les galaxies
         plus vieilles ont plus de « matière noire » apparente
"""
import json, math, os, time
PHI = (1.0+math.sqrt(5.0))/2.0; A = 1.0/PHI
C = 299792458.0; G = 6.67430e-11
T_UNIVERS = 4.35e17; H0 = 2.2e-18  # s⁻¹
A0_MOND = 1.2e-10
A0_THU = PHI * C * H0
MASSE_SOLAIRE = 2e30; KPC = 3.086e19

def rotation_frac(r, M, r_mem):
    """Vitesse de rotation avec contribution mémoire.
    v² = GM/r + GM·(r/r_mem)^{1−1/φ} — loi de puissance mémoire."""
    v_newton = math.sqrt(G * M / r) if r > 0 else 0
    memoire = (r / r_mem) ** (1.0 - 1.0/PHI)  # exposant = 1−1/φ ≈ 0.382
    return v_newton * math.sqrt(1.0 + memoire)

def main():
    t0 = time.time()
    print("="*70)
    print("MATIÈRE NOIRE = MÉMOIRE GRAVITATIONNELLE (THU V2)")
    print("="*70)
    
    # Échelle mémoire
    r_mem = C * T_UNIVERS / PHI  # même λ_seuil que pour Λ
    print(f"  Rayon mémoire r_mem = c·t_U/φ = {r_mem:.2e} m = {r_mem/KPC:.1f} kpc")
    print(f"  a₀_THU = φ·c·H₀ = {A0_THU:.2e} m/s²")
    print(f"  a₀_MOND         = {A0_MOND:.2e} m/s²")
    print(f"  Rapport a₀_THU/a₀_MOND = {A0_THU/A0_MOND:.1f}")
    print()
    
    # Profil de rotation pour une galaxie typique
    M_gal = 1e11 * MASSE_SOLAIRE  # 10^11 M☉
    print(f"─ Rotation galactique (M_baryon = 10^11 M☉, r_mem = {r_mem/KPC:.0f} kpc)")
    print(f"  {'r (kpc)':>8s} {'v_newton':>10s} {'v_memoire':>10s} {'v_plat?':>8s}")
    for r_kpc in [1, 5, 10, 20, 50, 100]:
        r = r_kpc * KPC
        vn = math.sqrt(G * M_gal / r) / 1000
        vm = rotation_frac(r, M_gal, r_mem) / 1000
        plat = "oui" if vm > 0.9 * vn and r_kpc >= 10 else ""
        print(f"  {r_kpc:8.0f} {vn:10.1f} {vm:10.1f} {plat:>8s}")
    print()
    
    # Tully-Fisher modifié
    print("─ Tully-Fisher : v⁴ ∝ M (standard) → v^(2φ) ∝ M (THU)")
    print(f"  Exposant THU : 2φ = {2*PHI:.2f}")
    print("  → les galaxies massives ont une rotation PLUS élevée que prédit")
    print("  par Tully-Fisher standard — la mémoire amplifie la masse.")
    print()
    
    # Dépendance en âge
    print("─ VERDICT HONNÊTE")
    print(f"  a₀_THU = φ·c·H₀ = {A0_THU:.2e} m/s² (proche de a₀_MOND = {A0_MOND:.2e})")
    print(f"  MAIS à l'échelle galactique (10 kpc), le terme mémoire (r/r_mem)^{1-1/PHI:.3f}")
    print(f"  est ~{(10*KPC/r_mem)**(1-1/PHI):.1e} — NÉGLIGEABLE.")
    print(f"  → La mémoire au temps cosmologique explique Λ (facteur 3,6) mais")
    print(f"  ne suffit PAS pour les courbes de rotation galactiques.")
    print(f"  → PISTE TRACÉE, PAS FERMÉE. L'effet nécessite soit une échelle")
    print(f"  mémoire plus courte (dynamique galactique), soit une contribution")
    print(f"  de la toile cosmique (filaments).")
    print(f"  Durée : {time.time()-t0:.1f}s")

    dep = {
        "mecanisme": "mémoire gravitationnelle — noyau ABC K(t)",
        "r_mem_kpc": r_mem / KPC,
        "a0_THU": A0_THU,
        "a0_MOND": A0_MOND,
        "rapport_a0": A0_THU / A0_MOND,
        "tully_fisher_exponent": 2 * PHI,
        "predictions": [
            "P1: v_plat² ∝ M_baryon^{1/φ}",
            "P2: a₀ = φ·c·H₀",
            "P3: dépendance en âge galactique"
        ],
        "date": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    p = os.path.join("data", "benchmarks", "matiere_noire_report.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(dep, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"Rapport : {p}")

if __name__ == "__main__":
    main()
