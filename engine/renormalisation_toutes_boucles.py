#!/usr/bin/env python3
"""renormalisation_toutes_boucles.py — PREUVE DE RENORMALISABILITÉ (CORRIGÉE)
Le propagateur est ANISOTROPE : G(ω,k)=1/(|ω|^{1/φ}+k²). En UV spatial (k→∞),
k² domine → la divergence spatiale est STANDARD (1/k²). La dérivée fractionnaire
temporelle n'adoucit QUE la direction ω — insuffisant pour régulariser."""
import json,math,os,time
PHI=(1.0+math.sqrt(5.0))/2.0; A=1.0/PHI

def D_standard(L,derivs_vertex=2):
    """Standard GR (α=1) : graviton 3-vertex avec 2 dérivées → D=4L−2I+2V.
    Pour le diagramme à L boucles le plus divergent : D≈2+2L (croît avec L)."""
    return 2.0+2.0*L

def D_fractionnaire_spatial(L):
    """Fractionnaire TEMPOREL seulement : le terme k² domine en UV spatial.
    Le comportement dominant est IDENTIQUE au standard. D_corr = D_std."""
    return D_standard(L)  # le terme k² domine → même divergence spatiale

def D_fractionnaire_spatio_temporel(L):
    """SI l'espace aussi était fractionnaire : D(L)=4·L−2·L·(1/α+1).
    Condition : D(L)<0 → L·(4−2·(1/α+1))<0 → L·(2−2/α)<0 → α<1 → α=1/φ=0,618
    donne D(L)=4L−2L·(1,618+1)=4L−5,236L=−1,236L<0 ∀L≥1 → SUPER-RENORMALISABLE."""
    exp_eff_spatial = 1.0/A   # laplacien fractionnaire (−Δ)^{1/φ} au lieu de −Δ
    exp_eff_temporel = 1.0/A  # les deux directions sont adoucies
    exp_total = exp_eff_spatial + exp_eff_temporel  # 2/φ ≈ 3.236
    return 4.0*L - exp_total*L  # = (4−2/φ)·L = (4−3,236)·L = 0,764·L → NON!

def D_spatio_temporel_correct(L):
    """VERSION CORRECTE : les deux directions adoucies → D = 4L − 2L·(1/α).
    Pour α=1/φ : D=4L−2L·1,618=4L−3,236L=0,764L  > 0 → NON renormalisable."""
    return 4.0*L - 2.0*L*(1.0/A)

def main():
    t0=time.time()
    print("="*70)
    print("RENORMALISABILITÉ À TOUTES LES BOUCLES — verdict corrigé")
    print("="*70)
    print("  RÉSULTAT HONNÊTE : la dérivée fractionnaire TEMPORELLE seule")
    print("  ne suffit pas — le comportement spatial reste standard (1/k²)")
    print("  et D(L) > 0 pour tout L. Le chaînon R3 est OUVERT sur ce point.")
    print()
    print("─ D(L) : standard (GR) vs fractionnaire temporel vs spatio-temporel")
    for L in [1,2,3,5,10]:
        Ds=D_standard(L); Dft=D_fractionnaire_spatial(L); Dst=D_spatio_temporel_correct(L)
        print(f"  L={L:2d} : GR={Ds:+.1f} · frac temporel={Dft:+.1f} · frac spatio-temp={Dst:+.1f}")
    print()
    print("  CONCLUSION :")
    print("  ❌ La dérivée fractionnaire TEMPORELLE seule ne rend PAS la")
    print("     gravité renormalisable à toutes les boucles (k² domine en UV).")
    print("  ⏳ Le chaînon R3 exige SOIT un Laplacien fractionnaire spatial")
    print("     (−Δ)^{1/φ} — non formulé à ce jour — SOIT la solution exacte")
    print("     de Deser fractionnaire (les vertex d'auto-interaction pourraient")
    print("     fournir la suppression spatiale manquante).")
    print("  → FRONTIÈRE CORRIGÉE. L'honnêteté du protocole l'exige.")
    print(f"  Durée : {time.time()-t0:.1f}s")
    dep={"verdict":"D(L)>0 ∀L — temporel seul insuffisant, spatial manquant",
         "solution":"(−Δ)^{1/φ} OU Deser fractionnaire complet",
         "statut":"FRONTIÈRE CORRIGÉE — le R3 précédent (D<0 à 2 boucles) était trop optimiste",
         "date":time.strftime("%Y-%m-%d %H:%M:%S")}
    p=os.path.join("data","benchmarks","renormalisation_boucles_report.json")
    os.makedirs(os.path.dirname(p),exist_ok=True)
    json.dump(dep,open(p,"w",encoding="utf-8"),indent=2,ensure_ascii=False)
    print(f"Rapport : {p}")
if __name__=="__main__":main()
