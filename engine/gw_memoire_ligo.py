#!/usr/bin/env python3
"""
gw_memoire_ligo.py — QUEUE DE MÉMOIRE GW : testable sur données existantes
==========================================================================
Prédiction THU V2 : après une fusion de trous noirs, la décroissance
de l'onde gravitationnelle suit une enveloppe de Mittag-Leffler :
    h(t) ~ E_{1/φ}(−Γ·t^{1/φ}) · cos(2πf_R·t + φ₀)

Standard GR : h(t) ~ e^{−Γt} · cos(2πf_R·t + φ₀)

DIFFÉRENCE MESURABLE : à t ∼ 1/Γ (temps caractéristique de l'amortissement),
l'écart entre les deux enveloppes atteint ∼20%. Pour GW150914,
f_R ∼ 250 Hz, Q ∼ 4-12 → Γ = πf_R/Q ∼ 65-200 s⁻¹ → τ ∼ 5-15 ms.
La queue de mémoire domine après ∼2-3 τ (10-50 ms post-fusion).

PROTOCOLE D'ANALYSE :
1. Sélectionner le signal ringdown (t > t_merger + 5 ms)
2. Ajuster un modèle standard : h(t) = A·e^{−Γt}·cos(2πf_R t + φ₀)
3. Ajuster le modèle THU : h(t) = A·E_{1/φ}(−Γ·t^{1/φ})·cos(2πf_R t + φ₀)
4. Comparer les résidus et le facteur de Bayes
5. Si le modèle THU est favorisé (BF > 3) → indication positive
   Si le modèle standard est favorisé → contrainte sur la THU
"""
import json,math,os,time,numpy as np
PHI=(1+math.sqrt(5))/2;A=1/PHI;PI=math.pi
from validation_coeff_quantiques import E_alpha

# Paramètres GW150914 (LIGO)
F_R=250.0       # Hz — fréquence du mode quasi-normal dominant
Q=8.0           # facteur de qualité
GAMMA=PI*F_R/Q  # taux d'amortissement standard (s⁻¹)
TAU=1.0/GAMMA   # temps caractéristique (s)
T_MAX=6*TAU     # durée d'analyse
FS=4096         # fréquence d'échantillonnage LIGO
N=int(T_MAX*FS)

def enveloppe_std(t,gamma):
    return np.exp(-gamma*t)
def enveloppe_thu(t,gamma):
    return np.array([abs(E_alpha(-gamma*ti**A,A)) for ti in t])

def ecart_relatif(t):
    e_std=enveloppe_std(t,GAMMA)
    e_thu=enveloppe_thu(t,GAMMA)
    return np.abs(e_thu-e_std)/np.maximum(e_std,1e-15)

def main():
    t0=time.time()
    print("="*70)
    print("GW MÉMOIRE THU — testable sur données LIGO existantes")
    print("="*70)
    print(f"  GW150914 : f_R={F_R:.0f} Hz · Q={Q:.0f} · Γ={GAMMA:.1f} s⁻¹ · τ={TAU*1e3:.1f} ms")
    print(f"  Modèle THU : h(t) ~ E_{{1/φ}}(−Γ·t^{{1/φ}})·cos(2πf_R t)")
    print(f"  Modèle std : h(t) ~ exp(−Γt)·cos(2πf_R t)")
    print()
    
    t_vals=np.linspace(0,T_MAX,N)
    
    # Écart aux temps caractéristiques
    print("─ ÉCART THU vs STANDARD (enveloppe) :")
    for mult in [0.5,1,2,3,5]:
        t_val=mult*TAU
        ecart=ecart_relatif(np.array([t_val]))[0]
        barre="⚠️ MESURABLE" if ecart>0.05 else ("⚡ détectable" if ecart>0.01 else "— faible")
        print(f"  t={mult:.0f}τ = {t_val*1e3:.1f} ms : Δh/h = {ecart*100:.1f}%  {barre}")
    print()
    
    # SNR requis
    ecart_2tau=ecart_relatif(np.array([2*TAU]))[0]
    SNR_min=3.0/ecart_2tau  # besoin de SNR suffisant pour distinguer à 3σ
    print(f"─ FAISABILITÉ")
    print(f"  Écart à 2τ = {ecart_2tau*100:.1f}%")
    print(f"  SNR minimum requis (3σ) ≈ {SNR_min:.0f}")
    print(f"  SNR GW150914 ≈ 24 (LIGO) → {'✅ FAISABLE' if SNR_min<24 else '⚠️ LIMITE'}")
    print()
    
    print("─ PROTOCOLE D'ANALYSE (prêt à être exécuté) :")
    print("  1. Extraire les données ringdown de GW150914 (t > t_merger + 5 ms)")
    print("  2. Ajuster h(t)=A·exp(−Γt)·cos(2πf_R t+φ₀) → résidus std")
    print("  3. Ajuster h(t)=A·E_{1/φ}(−Γ·t^{1/φ})·cos(2πf_R t+φ₀) → résidus THU")
    print("  4. Calculer le facteur de Bayes BF = P(data|THU)/P(data|std)")
    print("  5. BF > 3 → indication THU · BF < 1/3 → contrainte · sinon → indéterminé")
    print(f"  Durée : {time.time()-t0:.1f}s")
    
    dep={"evenement":"GW150914","f_R_Hz":F_R,"Q":Q,"gamma":GAMMA,
         "ecart_2tau_pct":float(ecart_2tau*100),"SNR_min":float(SNR_min),
         "SNR_GW150914":24,"faisable":bool(SNR_min<24),
         "protocole":"facteur de Bayes Mittag-Leffler vs exponentielle",
         "statut":"PRÊT — données LIGO publiques (GWOSC)",
         "date":time.strftime("%Y-%m-%d %H:%M:%S")}
    p=os.path.join("data","benchmarks","gw_memoire_ligo_report.json")
    os.makedirs(os.path.dirname(p),exist_ok=True)
    json.dump(dep,open(p,"w"),indent=2);print(f"Rapport : {p}")
if __name__=="__main__":main()
