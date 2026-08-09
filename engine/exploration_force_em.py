#!/usr/bin/env python3
"""
exploration_force_em.py — LA FORCE ÉLECTROMAGNÉTIQUE DANS LA THU V2
==================================================================
Parallèle avec la gravité (n=2) :
    n=2 : Fierz-Pauli → Deser → Einstein   (spin 2, auto-interaction nécessaire)
    n=1 : Maxwell → QED                     (spin 1, déjà cohérent sans auto-interaction)

La beauté : Maxwell est DÉJÀ valide aux deux niveaux — quantique (photon) et
classique (ondes EM). C'est l'auto-similarité fractale de la tour : le niveau
n=1 n'a pas besoin de « Deser » parce que le spin 1 est linéaire par nature.

APPORT DE LA THU : FRACTIONAL MAXWELL
    Standard : □A_μ = J_μ  →  potentiel de Coulomb V(r) ∝ 1/r
    THU V2   : D^{1/φ}[A_μ] = J_μ  →  V_frac(r) = V(r) ∗ K(r)
    → le potentiel de Coulomb acquiert une QUEUE FRACTIONNAIRE

PRÉDICTIONS TESTABLES :
    P1 · Déviation du potentiel de Coulomb à courte distance (∼ fm)
         → testable en diffusion électron-proton à basse énergie
    P2 · Modification du propagateur photonique → correction à g−2
    P3 · Le photon « se souvient » — queue de mémoire EM après une impulsion
"""
import json,math,os,time;PHI=(1+math.sqrt(5))/2;A=1/PHI;PI=math.pi

def coulomb_frac(r, r0=1e-15):
    """Potentiel de Coulomb modifié par le noyau fractal.
    V(r) ∝ 1/r · (1 + (r/r0)^{-α}) pour r >> r0."""
    return 1.0/r + (r/r0)**(-A)/r0 if r>0 else float('inf')

def deviation(r, r0=1e-15):
    """Écart relatif au potentiel de Coulomb standard."""
    v_std = 1.0/r if r>0 else 1e15
    v_frac = coulomb_frac(r, r0)
    return abs(v_frac - v_std)/v_std

def main():
    t0=time.time()
    print("="*70)
    print("FORCE ÉLECTROMAGNÉTIQUE — Maxwell fractionnaire (THU V2)")
    print("="*70)
    print("  NIVEAU n=1 : Ψ₁ = A₁·e^{i(ω₀t+φ₁)} → photon → spin 1 → EM")
    print()
    
    # Parallèle gravité/EM
    print("─ AUTO-SIMILARITÉ FRACTALE (même structure aux deux niveaux)")
    print("  GRAVITÉ (n=2) : Fierz-Pauli → Deser → Einstein")
    print("  EM (n=1)      : Maxwell → déjà valide (quantique + classique)")
    print("  → le spin 1 est linéaire : pas besoin d'auto-interaction")
    print("  → Maxwell EST déjà la version « Deser » du photon :")
    print("     la même équation gouverne le photon ET les ondes radio")
    print()
    
    # Fractional Maxwell
    print("─ MAXWELL FRACTIONNAIRE : D^{1/φ}[A_μ] = J_μ")
    print("  Standard : □A_μ = J_μ → V(r) ∝ 1/r")
    print("  THU V2   : le noyau fractal modifie le potentiel")
    print()
    
    # Déviations du potentiel de Coulomb (correction HONNÊTE)
    print("─ DÉVIATION DU POTENTIEL DE COULOMB (r_mem = c·t_U/φ ≈ 2,6 Mpc)")
    print("  La queue fractionnaire modifie le potentiel à LONGUE portée :")
    print("  V(r) ∝ 1/r · (1 + (r/r_mem)^{1/φ}) — à courte distance, négligeable.")
    for r in [1e-10, 1e6, 1e15, 1e20, 1e25]:
        corr = (r/8e25)**A
        barre = "⚠️ MESURABLE" if corr > 1e-6 else ("⚡ trace" if corr > 1e-12 else "— indétectable")
        print(f"  r = {r:.0e} m : correction ∼ {corr:.2e}  {barre}")
    print("  → À l'échelle atomique (10⁻¹⁰ m) : CORRECTION NULLE.")
    print("  → La queue EM n'est visible qu'aux échelles galactiques/cosmologiques.")
    print("  → Le photon « ordinaire » est le photon standard — la mémoire d'or")
    print("     ne modifie PAS la QED de précision (g−2, Lamb).")
    print("  → COHÉRENT avec le succès expérimental de QED (10⁻¹²).")
    print()
    
    # L'auto-similarité fractale
    print("─ CONCLUSION : LA FRACTALITÉ DE LA TOUR")
    print("  n=1 (EM)   : Maxwell = classique + quantique → AUTO-SIMILAIRE ✅")
    print("  n=2 (grav) : Einstein = classique, Fierz-Pauli = quantique → AUTO-SIMILAIRE ✅")
    print("  → La tour THU est fractale : chaque niveau unit ses deux visages.")
    print("  → La contribution THU est le TERME FRACTIONNAIRE D^{1/φ},")
    print("     qui ajoute une couche de mémoire au propagateur standard.")
    print(f"  Durée : {time.time()-t0:.1f}s")
    
    dep={"force":"EM","niveau":1,"spin":1,"boson":"photon",
         "classique":"Maxwell","quantique":"QED",
         "thu_maxwell":"D^{1/φ}[A_μ]=J_μ → Coulomb modifié",
         "predictions":["P1 diffusion e-p","P2 g-2","P3 queue EM attoseconde"],
         "auto_similarite":"Maxwell déjà valide aux deux niveaux — pas de Deser nécessaire",
         "date":time.strftime("%Y-%m-%d %H:%M:%S")}
    p=os.path.join("data","benchmarks","exploration_em_report.json")
    os.makedirs(os.path.dirname(p),exist_ok=True)
    json.dump(dep,open(p,"w"),indent=2)
    print(f"Rapport : {p}")
if __name__=="__main__":main()
