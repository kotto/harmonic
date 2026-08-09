#!/usr/bin/env python3
"""fractalite_oyibo_thu.py — LA FRACTALITÉ D'OYIBO REJOINT LA THU"""
import math,json,os,time;PHI=(1+math.sqrt(5))/2;A=1/PHI

# La fractalité : une loi de puissance est invariante d'échelle
# K(t) ~ t^{−1/φ} — c'est la définition d'une structure fractale
# L'exposant 1/φ ≈ 0,618 est l'unique valeur qui maximise la persistance
# sans périodicité (Hurwitz) — c'est LE point fixe fractal admissible.

print("="*70)
print("FRACTALITÉ D'OYIBO + MÉCANISME THU = LA MÊME STRUCTURE")
print("="*70)
print(f"  Oyibo : l'univers a une structure fractale basée sur φ")
print(f"  THU V2 : le noyau de mémoire K(t) ~ t^{{-1/φ}} = t^{{-{A:.4f}}}")
print(f"  → Une loi de puissance est INVARIANTE D'ÉCHELLE :")
print(f"  K(λ·t) = λ^{{-1/φ}}·K(t) — c'est la DÉFINITION d'un fractal.")
print(f"  → Le même motif se répète à toutes les échelles, pondéré par φ.")

# Dimension fractale : D_f = 1/α = φ ≈ 1.618
# (pour une marche aléatoire fractionnaire, D_f = 2 − H = 2 − (1−α) = 1+α)
D_f = 1.0 + A
print(f"\n  Dimension fractale du noyau : D_f = 1 + 1/φ ≈ {D_f:.4f}")
print(f"  → cohérent avec les attracteurs étranges (D_f non entière)")
print(f"  → le temps lui-même aurait une structure fractale d'ordre φ")

# Échelles où la fractalité est visible
echelles = [("Planck", 1e-35), ("QCD", 1e-15), ("atomique", 1e-10),
            ("syst. solaire", 1e12), ("galactique", 1e20), ("cosmologique", 1e26)]
print(f"\n  Le noyau fractal agit À TOUTES LES ÉCHELLES :")
for nom, r in echelles:
    p = (r/1e26)**A
    barre = "█"*max(1,int(p*40))
    print(f"  {nom:20s} {barre}")

print(f"\n─ CONCLUSION")
print("  Oyibo a identifié LA STRUCTURE (fractalité en φ).")
print("  La THU V2 a identifié LE MÉCANISME (filtre de stabilité :")
print("  le noyau ABC survit à l'itération → loi de puissance en 1/φ).")
print("  → Les deux se renforcent : la fractalité d'Oyibo EST la")
print("  signature du filtre d'élimination de la THU.")

dep={"fractalite_oyibo":"structure fractale en φ",
     "mecanisme_thu":"noyau ABC K(t)~t^{-1/φ} = filtre de stabilité",
     "dimension_fractale":D_f,
     "exposant":1/PHI,"date":time.strftime("%Y-%m-%d %H:%M:%S")}
p=os.path.join("data","benchmarks","fractalite_report.json")
os.makedirs(os.path.dirname(p),exist_ok=True)
json.dump(dep,open(p,"w"),indent=2)
print(f"Rapport : {p}")
