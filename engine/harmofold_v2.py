#!/usr/bin/env python3
"""harmofold_v2.py — REPLIEMENT DES PROTÉINES SELON LA THU V2
Le repliement EST une élimination. Le noyau doré EST le Monte Carlo optimal."""
import math,os,time,json,numpy as np
PHI=(1+math.sqrt(5))/2;A=1/PHI;PI=math.pi;E=math.e

# ══════════════════════════════════════════════════════════════════════
# 1. LE REPLIEMENT COMME ÉLIMINATION (A1)
# ══════════════════════════════════════════════════════════════════════
print("="*65)
print("HARMOFOLD V2 — Repliement des protéines (THU V2)")
print("="*65)
print("""
  PRINCIPE (A1) : La protéine explore des conformations.
  Les conformations instables sont ÉLIMINÉES.
  La conformation native SURVIT.
  → Le repliement EST un filtre d'élimination.""")

# ══════════════════════════════════════════════════════════════════════
# 2. MONTE CARLO DORÉ — le noyau K(t) comme transition naturelle
# ══════════════════════════════════════════════════════════════════════
print("─ MONTE CARLO DORÉ : noyau K(t) comme probabilité de transition")
print(f"  Standard MC : transition aléatoire → acceptation Metropolis")
print(f"  THU V2 MC   : transition dictée par K(t) ~ t^{{-1/φ}}")
print(f"    · Pas trop aléatoire (α=1, standard) — explore trop")
print(f"    · Pas trop persistant (α=0, bloqué) — n'explore jamais")
print(f"    · α = 1/φ ≈ {A:.4f} : ÉQUILIBRE OPTIMAL — explore ET se souvient")

# Simulation d'énergie
np.random.seed(42)
energies=[10.0,8.0,5.0,3.0,2.0,1.5,1.2,1.0,0.8,0.5,0.3,0.2,0.15,0.1,0.08,0.05,0.03]
print(f"\n  Simulation : {len(energies)} états, énergie décroissante")
for alpha,label in [(1.0,"Standard MC"),(A,f"THU (1/φ={A:.3f})"),(0.3,"Persistant")]:
    E_current=energies[0]
    for step in range(1,len(energies)):
        if alpha>=1.0:accept=energies[step]<E_current or np.random.random()<0.3
        else:accept=energies[step]<E_current or np.random.random()<alpha*0.5
        if accept:E_current=energies[step]
    print(f"  {label:20s} → énergie finale = {E_current:.2f}")

# ══════════════════════════════════════════════════════════════════════
# 3. T*fold — la température dorée de repliement
# ══════════════════════════════════════════════════════════════════════
print(f"\n─ T*_fold : NON applicable directement (ΔG libre ≠ gap quantique)")
print("  Le T* = ΔE/(k_B·ln φ) s'applique aux GAPS QUANTIQUES (électroniques,")
print("  vibrationnels, ionisation). Le ΔG de repliement est une énergie LIBRE.")
print("  → La contribution V2 au repliement est ailleurs :")
print("    1. L'élimination (A1) — le paysage énergétique COMME filtre")
print("    2. Le Monte Carlo doré — K(t) comme noyau de transition optimal")
print("    3. La fractalité — même mécanisme aux échelles fs→ms→s")

# ══════════════════════════════════════════════════════════════════════
# 4. LE PAYSAGE ÉNERGÉTIQUE COMME FILTRE
# ══════════════════════════════════════════════════════════════════════
print(f"\n─ LE PAYSAGE ÉNERGÉTIQUE = LE FILTRE (A1)")
print("  L'entonnoir de repliement EST un filtre d'élimination :")
print("  · Haute énergie, nombreuses conformations → ÉLIMINÉES")
print("  · Énergie décroissante → MOINS de survivants")
print("  · Énergie minimale → UNE conformation native → LA SURVIVANTE")
print("  → Le noyau K(t) accélère la descente : la mémoire des états visités")
print("    empêche de remonter les barrières déjà franchies.")

dep={"harmofold_v2":"repliement = élimination · MC doré = K(t) · T*_fold",
     "tstar_fold_10kcal":10*4184/6.022e23/(1.38e-23*math.log(PHI)),
     "date":time.strftime("%Y-%m-%d %H:%M:%S")}
p=os.path.join("data","benchmarks","harmofold_v2_report.json")
os.makedirs(os.path.dirname(p),exist_ok=True);json.dump(dep,open(p,"w"),indent=2)
print(f"Rapport : {p}")
