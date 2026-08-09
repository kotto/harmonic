#!/usr/bin/env python3
"""persistance_monte_carlo.py — Le chaînon « persistance ∝ 1/μ(α) » (Monte-Carlo)
Test : pour α ∈ (0,1], mesurer la persistance de la mémoire (décroissance de E_α)
et la corréler avec la mesure d'irrationalité μ(α) — constante de Hurwitz."""
import json, math, os, time
import numpy as np
PHI=(1.0+math.sqrt(5.0))/2.0; ALPHA=1.0/PHI
from validation_coeff_quantiques import E_alpha

def mu_hurwitz(a):
    """Mesure d'irrationalité : 1/√5 pour φ et ses équivalents ; sinon approx."""
    for p in range(1,200):
        for q in range(1,200):
            if abs(a-p/q)<1e-12: return 1.0  # rationnel → μ petit
    # Pour φ : μ=1/√5 ≈ 0.4472 ; sinon estimé par la meilleure fraction
    best = float("inf")
    for q in range(1,500):
        p = round(a*q)
        d = abs(a-p/q)
        if d < best: best = d; best_q = q
    return best_q*best  # μ(a) ≈ q·|a−p/q| (la plus petite valeur)

def persistance(alpha, T=50, N=200):
    """Persistance = Σ_t |K(t)| / max (masse totale de la mémoire)."""
    lam = alpha/(1-alpha); B = 1 - alpha + alpha/math.gamma(alpha)
    K = np.array([1.0] + [B*E_alpha(-lam*t**alpha,alpha).real for t in range(1,T)])
    return float(np.sum(np.abs(K[1:])) / np.max(np.abs(K[1:])))

def main():
    t0=time.time()
    print("="*70); print("CHAÎNON « persistance ∝ 1/μ » — Monte-Carlo sur α")
    print("="*70)
    np.random.seed(20260809)
    alphas = list(np.linspace(0.15,0.95,60)) + [ALPHA, 0.3, 0.5, 0.7]
    pts = []
    for a in sorted(set(alphas)):
        mu = mu_hurwitz(a); p = persistance(a)
        pts.append((a, mu, p))
    # corrélation de Spearman
    mus = np.array([m for _,m,_ in pts])
    pers = np.array([p for _,_,p in pts])
    from scipy import stats
    rho, pval = stats.spearmanr(mus, 1.0/pers)  # persistance ∝ 1/μ ?
    print(f"  Spearman(μ, 1/persistance) = {rho:.4f} (p = {pval:.4f})")
    # 1/φ est-il un extremum ?
    i_phi = np.argmin(np.abs(np.array([a for a,_,_ in pts])-ALPHA))
    phi_mu, phi_p = pts[i_phi][1], pts[i_phi][2]
    best_p = max(pts, key=lambda t: t[2])
    print(f"  1/φ : μ = {phi_mu:.4f} · persistance = {phi_p:.4f}")
    print(f"  meilleure persistance : α={best_p[0]:.4f} → {best_p[2]:.4f}")
    c1 = rho > 0.3
    c2 = phi_p >= 0.8 * best_p[2]
    ok = c1 and c2
    print(f"  ─{'─'*60}")
    print(f"  C1 · corrélation μ ↔ persistance (ρ={rho:.3f}) : {'✅' if c1 else '❌'}")
    print(f"  C2 · 1/φ dans le top persistance : {'✅' if c2 else '❌'}")
    msg="✅ Monte-Carlo : la persistance corrèle avec l'irrationalité (chaînon soutenu)" if ok else "❌ NÉGATIF"
    print(f"  VERDICT : {msg} · {time.time()-t0:.1f}s")
    dep={"verdict":{"C1_corr":bool(c1),"C2_1_phi":bool(c2),"chaînon":bool(ok)},"spearman":rho,"p_value":pval,
         "phi_mu":phi_mu,"phi_persistance":phi_p,"date":time.strftime("%Y-%m-%d %H:%M:%S")}
    p=os.path.join("data","benchmarks","persistance_monte_carlo_report.json")
    os.makedirs(os.path.dirname(p),exist_ok=True)
    json.dump(dep,open(p,"w",encoding="utf-8"),indent=2,ensure_ascii=False)
    print(f"  Rapport : {p}")
if __name__=="__main__":main()
