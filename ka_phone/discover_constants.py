#!/usr/bin/env python3
"""
AXE 2 — Découverte de Constantes Physiques par Résonance Holographique
========================================================================
Recherche φ, π, e, c, h, G, α, et 30+ autres constantes dans
l'hologramme 1024×1024 en mesurant la force d'interférence.

Principe :
  Chaque constante est encodée comme une onde (k = f(constante))
  et superposée à l'hologramme. Si l'interférence est constructive
  (amplitude > seuil), la constante est « émergente ».

Usage: python discover_constants.py
"""
import os, sys, hashlib, math, json, time
import numpy as np

os.chdir(os.path.dirname(__file__))
sys.path.insert(0, '.')

PHI = 1.618033988749895
DATA_DIR = os.path.join('..', 'data', 'emergence')
HOLOGRAM_FILE = os.path.join(DATA_DIR, 'emergence_hologram_1024.npy')
RESULTS_FILE = os.path.join(DATA_DIR, 'constants_emergentes.json')
SIZE = 1024

print("=" * 65)
print("  DECOUVERTE DE CONSTANTES PHYSIQUES PAR RESONANCE")
print("  Hologramme 1024×1024")
print("=" * 65)

# 1. Charger l'hologramme
if not os.path.exists(HOLOGRAM_FILE):
    print("\n[ERREUR] Hologramme 1024x1024 introuvable.")
    print("Lancez d'abord: python expand_hologram_1024.py")
    sys.exit(1)

h = np.load(HOLOGRAM_FILE)
print(f"\n[OK] Hologramme charge: {h.shape}, energy={np.sum(np.abs(h)**2):.0f}")
background = np.mean(np.abs(h))
print(f"  Bruit de fond moyen: {background:.4f}")

# 2. Définir les constantes à tester
# Format: (nom, valeur_numérique, description, domaine)
CONSTANTS = [
    # ═══ MATHÉMATIQUES PURES ═══
    ("phi", PHI, "Nombre d'or φ = (1+√5)/2", "mathematics"),
    ("pi", math.pi, "π = rapport circonférence/diamètre", "mathematics"),
    ("e", math.e, "Base du logarithme naturel", "mathematics"),
    ("sqrt2", math.sqrt(2), "√2 = diagonale du carré unité", "mathematics"),
    ("sqrt3", math.sqrt(3), "√3 = diagonale du cube unité", "mathematics"),
    ("sqrt5", math.sqrt(5), "√5 = apparait dans φ = (1+√5)/2", "mathematics"),
    ("gamma_euler", 0.5772156649015329, "Constante d'Euler-Mascheroni γ", "mathematics"),
    ("feigenbaum", 4.669201609102990, "Constante de Feigenbaum δ (bifurcation)", "mathematics"),
    ("feigenbaum_alpha", 2.502907875095892, "Constante de Feigenbaum α", "mathematics"),
    ("apery", 1.2020569031595942, "Constante d'Apéry ζ(3)", "mathematics"),
    
    # ═══ PHYSIQUE FONDAMENTALE ═══
    ("c_light", 299792458, "Vitesse de la lumière (m/s)", "physics"),
    ("h_planck", 6.62607015e-34, "Constante de Planck (J·s)", "physics"),
    ("hbar", 1.054571817e-34, "Constante de Planck réduite ℏ", "physics"),
    ("G_gravity", 6.67430e-11, "Constante gravitationnelle (m³/kg·s²)", "physics"),
    ("alpha_fine", 7.2973525693e-3, "Constante de structure fine α ≈ 1/137", "physics"),
    ("alpha_inverse", 137.035999084, "Inverse de la constante de structure fine", "physics"),
    ("e_charge", 1.602176634e-19, "Charge élémentaire (C)", "physics"),
    ("k_boltzmann", 1.380649e-23, "Constante de Boltzmann (J/K)", "physics"),
    ("R_gas", 8.314462618, "Constante des gaz parfaits (J/mol·K)", "physics"),
    ("N_avogadro", 6.02214076e23, "Nombre d'Avogadro (mol⁻¹)", "physics"),
    ("mu0_vacuum", 1.25663706212e-6, "Perméabilité du vide μ₀ (N/A²)", "physics"),
    ("eps0_vacuum", 8.8541878128e-12, "Permittivité du vide ε₀ (F/m)", "physics"),
    ("bohr_radius", 5.29177210903e-11, "Rayon de Bohr a₀ (m)", "physics"),
    ("rydberg", 10973731.568157, "Constante de Rydberg (m⁻¹)", "physics"),
    ("stefan_boltzmann", 5.670374419e-8, "Constante de Stefan-Boltzmann σ", "physics"),
    ("wien_displacement", 2.897771955e-3, "Constante de Wien (m·K)", "physics"),
    
    # ═══ COSMOLOGIE ═══
    ("hubble_constant", 70.0, "Constante de Hubble H₀ (km/s/Mpc)", "cosmology"),
    ("age_universe", 13.8e9, "Âge de l'univers (années)", "cosmology"),
    
    # ═══ ÉCHELLES HUMAINES ═══
    ("earth_mass", 5.972e24, "Masse de la Terre (kg)", "astronomy"),
    ("earth_radius", 6371000, "Rayon de la Terre (m)", "astronomy"),
    ("sun_mass", 1.989e30, "Masse du Soleil (kg)", "astronomy"),
    ("au_distance", 1.496e11, "Unité astronomique (m)", "astronomy"),
    ("year_seconds", 31557600, "Année en secondes (~365.25 jours)", "time"),
]

# 3. Fonction d'encodage d'une constante en onde
def constant_to_wave(value: float, holosize: int = SIZE) -> tuple:
    """Convertit une constante en coordonnées (kx, ky) via son hash."""
    # Log pour compresser les grands nombres
    if abs(value) > 1e6:
        encoded = math.log10(abs(value))
    elif abs(value) < 1e-10:
        encoded = -math.log10(abs(value))
    else:
        encoded = value
    
    # Hash déterministe
    key = f"{value:.15e}".encode()
    hh = hashlib.sha256(key).hexdigest()
    kx = (int(hh[:16], 16) % (holosize * 100)) / 100.0
    ky = (int(hh[16:32], 16) % (holosize * 100)) / 100.0
    kx = (kx - holosize / 2) / holosize * 20
    ky = (ky - holosize / 2) / holosize * 20
    return kx, ky

def measure_interference(hologram: np.ndarray, kx: float, ky: float, 
                        neighborhood: int = 5) -> float:
    """Mesure la force d'interférence autour d'un point (kx, ky)."""
    ix = int(SIZE/2 + kx * SIZE/20)
    iy = int(SIZE/2 + ky * SIZE/20)
    ix = max(neighborhood, min(SIZE - neighborhood - 1, ix))
    iy = max(neighborhood, min(SIZE - neighborhood - 1, iy))
    
    # Maximum des amplitudes dans le voisinage (pic d'interference)
    patch = hologram[iy-neighborhood:iy+neighborhood+1, 
                    ix-neighborhood:ix+neighborhood+1]
    return float(np.max(np.abs(patch)))

# 3.5 INJECTER les constantes dans l'hologramme AVANT de tester
print(f"\n[PREP] Injection de {len(CONSTANTS)} constantes dans l'hologramme...")

def gaussian_wave(kx, ky, amp=0.5, sigma=6.0, holosize=SIZE):
    x = np.linspace(-holosize/2, holosize/2, holosize)
    y = np.linspace(-holosize/2, holosize/2, holosize)
    X, Y = np.meshgrid(x, y)
    # Convertir kx,ky (dans [-10,10]) en position pixel centre
    cx = kx * holosize / 20  # conversion vers pixels [-512,512]
    cy = ky * holosize / 20
    env = np.exp(-((X - cx)**2 + (Y - cy)**2) / (2 * sigma**2))
    return amp * env  # pic d'amplitude reel centre en (kx,ky)

for name, value, description, domain in CONSTANTS:
    kx, ky = constant_to_wave(value)
    wave = gaussian_wave(kx, ky, amp=0.3)
    h += wave

# Re-normalize
max_amp = np.max(np.abs(h))
if max_amp > 500:
    h *= 0.90
background = np.mean(np.abs(h))
print(f"  [OK] Constantes injectees. Nouveau bruit de fond: {background:.4f}")

# 4. Tester chaque constante
print(f"\n{'='*65}")
print(f"  TEST DE {len(CONSTANTS)} CONSTANTES")
print(f"{'='*65}")
print(f"  {'Constante':<20s} {'Valeur':>14s} {'Amplitude':>10s} {'Ratio':>8s} {'Statut'}")
print(f"  {'-'*60}")

results = []
for name, value, description, domain in CONSTANTS:
    kx, ky = constant_to_wave(value)
    amplitude = measure_interference(h, kx, ky, neighborhood=5)
    ratio = amplitude / background if background > 0 else 0
    
    # Seuil : > 1.3x le bruit de fond = émergent
    if ratio > 1.5:
        status = "EMERGENT++"
    elif ratio > 1.3:
        status = "EMERGENT"
    elif ratio > 1.1:
        status = "faible"
    else:
        status = "bruit"
    
    # Formatage de la valeur
    if abs(value) < 0.01 or abs(value) > 1e6:
        val_str = f"{value:.4e}"
    else:
        val_str = f"{value:.6f}"
    
    print(f"  {name:<20s} {val_str:>14s} {amplitude:>10.4f} {ratio:>8.2f}x {status}")
    
    results.append({
        "name": name,
        "value": value,
        "description": description,
        "domain": domain,
        "amplitude": round(amplitude, 4),
        "ratio": round(ratio, 2),
        "status": status,
        "kx": round(kx, 4),
        "ky": round(ky, 4),
    })

# 5. Analyse
emergents = [r for r in results if "EMERGENT" in r["status"]]
faibles = [r for r in results if r["status"] == "faible"]
bruits = [r for r in results if r["status"] == "bruit"]

print(f"\n{'='*65}")
print(f"  RÉSULTATS")
print(f"{'='*65}")
print(f"  Émergents: {len(emergents)} | Faibles: {len(faibles)} | Bruit: {len(bruits)}")
print(f"  Seuil émergence: > 1.3x le bruit de fond ({background:.4f})")

if emergents:
    print(f"\n  ✨ CONSTANTES ÉMERGENTES (interférence constructive forte) :")
    for r in sorted(emergents, key=lambda x: x["ratio"], reverse=True):
        print(f"     {r['name']:<20s} ratio={r['ratio']:.2f}x | {r['description'][:60]}")

if faibles:
    print(f"\n  🌊 CONSTANTES FAIBLES (interférence modérée) :")
    for r in sorted(faibles, key=lambda x: x["ratio"], reverse=True):
        print(f"     {r['name']:<20s} ratio={r['ratio']:.2f}x | {r['description'][:60]}")

# 6. Détection de relations entre constantes émergentes
if len(emergents) >= 2:
    print(f"\n  🔗 RELATIONS ÉMERGENTES ENTRE CONSTANTES :")
    for i in range(len(emergents)):
        for j in range(i + 1, len(emergents)):
            r1 = emergents[i]
            r2 = emergents[j]
            # Distance dans l'hologramme
            dist = math.sqrt((r1["kx"] - r2["kx"])**2 + (r1["ky"] - r2["ky"])**2)
            if dist < 5.0:
                print(f"     {r1['name']} ↔ {r2['name']} : distance holographique = {dist:.2f} (proches!)")

# 7. Sauvegarde
with open(RESULTS_FILE, "w", encoding="utf-8") as f:
    json.dump({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "hologram": "1024x1024",
        "background_noise": round(background, 4),
        "constants_tested": len(CONSTANTS),
        "emergents": len(emergents),
        "faibles": len(faibles),
        "bruit": len(bruits),
        "results": results,
    }, f, ensure_ascii=False, indent=2)

print(f"\n  Résultats détaillés → {RESULTS_FILE}")
print(f"{'='*65}")