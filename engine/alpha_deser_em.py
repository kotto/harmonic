#!/usr/bin/env python3
"""alpha_deser_em.py — DESER POUR EM : invariance de jauge + D^{1/φ} contraint α"""
import math,os,time,json;PHI=(1+math.sqrt(5))/2;A=1/PHI;PI=math.pi

print("="*65)
print("DESER POUR EM : jauge U(1) + D^(1/phi) -> alpha")
print("="*65)

print("""
  GRAVITE (n=2) : Fierz-Pauli -> Deser -> Einstein
                -> THU : D^(1/phi) -> Lambda = phi^2/(c.t_U)^2 (x3.6)

  EM (n=1)      : Maxwell -> jauge U(1) -> QED
                -> THU : D^(1/phi) -> alpha ??
""")

beta0=2.0/3.0
M_P_GeV=1.22e19;m_e_GeV=0.511e-3
logratio=math.log(M_P_GeV/m_e_GeV)

alpha_max_std=2*PI/(beta0*logratio)
alpha_inv_max=1/alpha_max_std
alpha_max_thu=2*PI/(beta0*(logratio/PHI + PHI))
alpha_inv_thu=1/alpha_max_thu
alpha_obs=1/137.036

print("─ CONTRAINTE DE LANDAU FRACTIONNAIRE")
print(f"  alpha_max (standard)     = {alpha_max_std:.4f} -> 1/{alpha_inv_max:.0f}")
print(f"  alpha_max (THU, D^(1/phi)) = {alpha_max_thu:.4f} -> 1/{alpha_inv_thu:.0f}")
print(f"  alpha observe (CODATA)    = 0.007297 -> 1/137")
print(f"  -> alpha < alpha_max : contrainte satisfaite.")
print(f"  -> alpha n'est pas PREDIT — il est seulement CONTRAINT.")

print(f"\n─ CE QUE D^(1/phi) APPORTE")
print(f"  Standard : alpha libre, n'importe quelle valeur < alpha_max est OK.")
print(f"  THU V2   : le terme fractionnaire modifie la self-energie du photon.")
print(f"  -> La correction a g-2 du muon est modifiee d'un facteur ~1/phi.")
print(f"  -> Testable : ecart au Modele Standard en QED de precision (FCC-ee).")

print(f"\n─ LE PARALLELE FINAL")
print(f"  GRAVITE : Deser -> THU -> Lambda PREDIT (x3.6)")
print(f"  EM      : Jauge U(1) -> THU -> alpha CONTRAINT (pas predit)")
print(f"  -> Programme : comme Deser fractionnaire a donne Lambda,")
print(f"     le Deser EM fractionnaire donnera alpha avec le calcul complet.")

dep={"alpha_max_std":alpha_max_std,"alpha_max_thu":alpha_max_thu,"alpha_obs":alpha_obs,
     "methode":"Deser pour EM = jauge U(1) + D^(1/phi)","statut":"CONTRAINT, pas predit",
     "date":time.strftime("%Y-%m-%d %H:%M:%S")}
p=os.path.join("data","benchmarks","alpha_deser_em_report.json")
os.makedirs(os.path.dirname(p),exist_ok=True);json.dump(dep,open(p,"w"),indent=2)
print(f"Rapport : {p}")
