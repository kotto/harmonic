#!/usr/bin/env python3
"""e4_lambda_evolutif.py + gw_memoire.py + cmb_pics_phi.py — TROIS DÉMONSTRATIONS RAPIDES"""
import json,math,os,time;PHI=(1+math.sqrt(5))/2;A=1/PHI;C=299792458;G=6.6743e-11;H0=2.2e-18;T_U=4.35e17;L_P=1.616e-35

def e4():
    """Λ(t) = φ²/(c·t)² — la constante cosmologique DÉCROÎT avec le temps."""
    tt=[1e9*365.25*86400,4.35e17,T_U*2]
    print("─ E4 · Λ(t) = φ²/(c·t)² — dépôt pré-enregistré")
    for t in tt:
        lt=PHI**2/(C*t)**2;print(f"  t={t/3.156e16:.1f} Gyr : Λ={lt:.2e} m⁻²")
    print("  → Λ diminue en 1/t² — TESTABLE par DESI/Euclid (évolution énergie noire)")
    return {"t_Gyr":[t/3.156e16 for t in tt],"Lambda_t":[PHI**2/(C*t)**2 for t in tt]}

def gw():
    """Queue de mémoire gravitationnelle : h(t) ~ t^{−1/φ} après la fusion."""
    tt=[1e-3,1e-2,1e-1,1,10]
    print("─ GW · queue de mémoire : h(t) ~ t^{−1/φ} après fusion LIGO")
    for t in tt: print(f"  t={t:.0e}s : h(t)/h(0) ~ t^(−{A:.3f}) = {t**(-A):.2e}")
    print("  → testable : analyser le post-merger de GW150914 pour une queue en t^{−0,618}")
    return {"queue_exponent":-A,"temps_s":tt,"amplitude":[t**(-A) for t in tt]}

def cmb():
    """Pics acoustiques CMB : ratio θ₁/θ₂. Prédiction : lié à φ."""
    r1,r2=220.0,540.0  # positions approx ℓ₁,ℓ₂ (Planck 2018: ~220, ~537)
    ratio=r2/r1
    phi_pred=1+1/PHI;phi_pred2=PHI
    print(f"─ CMB · ratio ℓ₂/ℓ₁ = {ratio:.3f} (Planck ~2,44)")
    print(f"  φ² = {PHI**2:.3f} · 1+1/φ = {phi_pred:.3f} · √φ = {math.sqrt(PHI):.3f}")
    print("  → pas de correspondance évidente à ce stade — piste à creuser")
    return {"ratio_CMB":ratio,"phi_carres":PHI**2,"un_plus_un_sur_phi":phi_pred}

r={"E4_lambda":e4(),"GW_memoire":gw(),"CMB":cmb(),"date":time.strftime("%Y-%m-%d %H:%M:%S")}
p=os.path.join("data","benchmarks","trois_demos_report.json")
os.makedirs(os.path.dirname(p),exist_ok=True);json.dump(r,open(p,"w"),indent=2)
print(f"Rapport : {p}")
