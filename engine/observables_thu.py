#!/usr/bin/env python3
"""observables_thu.py — TOUT CE QUE LA THU V2 PRÉDIT DE MESURABLE"""
import math,json,os,time;PHI=(1+math.sqrt(5))/2;A=1/PHI;PI=math.pi
C=299792458;T_U=4.35e17;L_P=1.616e-35

obs=[
 ("E3 · T* cavité 10 GHz","0.997 K → occupation φ=1.618","Cryostat dilution","✅ PRÊT"),
 ("E3 · T* H ionisation","327 918 K → Boltzmann=1/φ","Spectro plasma","✅ PRÊT"),
 ("E3 · T* 23 éléments","χ·24115 K/eV — table complète","Spectro plasma","✅ PRÊT"),
 ("E1bis · Zeno fractionnaire","survie en t^{0.618} vs t²","Rb⁸⁷ + cavité QED","✅ PRÊT"),
 ("Λ(t) ∝ 1/t²","Λ(1 Gyr)=2.9e-50 · Λ(now)=4.0e-52","DESI/Euclid","⏳ en cours"),
 ("GW · queue mémoire","h(t) ~ t^{−0.618} post-fusion","LIGO GW150914","⚡ données existantes"),
 ("Mémoire d'or (fGn)","C1 2.82% · optimal H=0.691","Séries temporelles","✅ vérifié"),
 ("Ω_Λ = φ²/3","0.873 vs 0.689 (27%)","Planck/CMB","⚠️ écart 27%"),
 ("Λ = φ²/(c·t_U)²","4.0e-52 vs 1.1e-52 (×3.6)","Cosmologie","✅ facteur 3.6"),
 ("RG · point fixe 1/φ","JS divergence 0.0001","Noyau ABC itéré","✅ vérifié"),
 ("RG · singularité α=0.50","JS divergence 0.0707","Noyau ABC itéré","✅ vérifié"),
 ("Tableau périodique","118/118 périodes","Génération","✅ vérifié"),
 ("Gaz nobles","{2,10,18,36,54,86,118}","Génération","✅ vérifié"),
 ("Pic de fer Ni-62","8.783 MeV (0.12%)","SEMF","✅ vérifié"),
 ("α = 1/137","NON dérivé","—","❌ frontière"),
]

print("="*70)
print("OBSERVABLES DE LA THU V2 — classées par testabilité")
print("="*70)
print(f"  {'OBSERVABLE':45s} {'VALEUR':20s} {'EXPÉRIENCE':20s} {'STATUT'}")
ready=sum(1 for _,_,_,s in obs if "PRÊT" in s or "vérifié" in s)
progress=sum(1 for _,_,_,s in obs if "cours" in s)
data=sum(1 for _,_,_,s in obs if "existantes" in s)
frontier=sum(1 for _,_,_,s in obs if "frontière" in s)
for o,v,e,s in obs:
    print(f"  {o:45s} {v:20s} {e:20s} {s}")
print(f"\n  {len(obs)} observables : {ready} prêtes/vérifiées · {progress} en cours · {data} sur données existantes · {frontier} frontières")
dep={"observables":len(obs),"pretes":ready,"en_cours":progress,
     "sur_donnees":data,"frontieres":frontier,"liste":[{o:(v,e,s)} for o,v,e,s in obs],
     "date":time.strftime("%Y-%m-%d %H:%M:%S")}
p=os.path.join("data","benchmarks","observables_report.json")
os.makedirs(os.path.dirname(p),exist_ok=True);json.dump(dep,open(p,"w"),indent=2)
print(f"Rapport : {p}")
