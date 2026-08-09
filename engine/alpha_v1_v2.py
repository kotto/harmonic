#!/usr/bin/env python3
"""alpha_v1_v2.py — L'INTUITION V1, LA MÉTHODE V2"""
import math,json,os,time;PHI=(1+math.sqrt(5))/2;PI=math.pi;E=math.e

print("="*70)
print("α : L'INTUITION DE V1, LA MÉTHODE DE V2")
print("="*70)

# V1 — l'intuition
print("─ V1 · L'INTUITION (légitime)")
print("  « Les constantes fondamentales s'expriment à partir")
print("  d'un petit nombre de constantes mathématiques. »")
print("  → c'est le programme de toute la physique théorique.")
print("  → EXÉCUTION V1 : chercher une formule φ^k·π^m·e^n ≈ 1/137")
print()

# Ce que V1 a trouvé (et qui a été réfuté)
combos_v1 = [
    ("φ³·π/2", PHI**3*PI/2),("φ⁵/4π", PHI**5/(4*PI)),
    ("φ²·e/π", PHI**2*E/PI),("4π·φ⁻⁴", 4*PI*PHI**(-4)),
]
print("─ EXEMPLES V1 (réfutés par le treillis)")
for nom,val in combos_v1:
    print(f"  {nom:15s} = {val:.3f} (écart {abs(val-137):.0f})")
print("  → le treillis : TOUTE cible est approximable (poids 15).")
print("  → Bonferroni : 0/120 — aucun privilège de φ dans α.")
print()

# V2 — la méthode
print("─ V2 · LA MÉTHODE (scientifique)")
print("  Au lieu de chercher une formule, on demande :")
print("  « Comment α ÉMERGE-t-il de la dynamique du niveau n=1 ? »")
print()
print("  PISTE 1 · Le pôle de Landau fractionnaire")
print("    La THU modifie le running de α : β_frac = β_std + δβ")
print("    où δβ ∼ (μ/M_P)^{1/φ}. Le point fixe infrarouge détermine α(0).")
print("    → nécessite le calcul complet du groupe de renormalisation")
print("    fractionnaire (au-delà de l'approximation d'aujourd'hui).")
print()
print("  PISTE 2 · La constante de couplage comme survivant")
print("    α est le survivant du filtre U(1) au niveau n=1.")
print("    Le filtre = la condition de cohérence de la théorie")
print("    (anomalie nulle, liberté asymptotique/trivialité).")
print("    → la valeur de α est dictée par la cohérence du filtre.")
print()
print("  PISTE 3 · Le ratio des échelles")
print("    α ∼ 1/ln(M_P/m_e) — le logarithme du ratio des échelles")
print("    de Planck et de l'électron. La THU fournit l'échelle de")
print("    Planck (via le noyau mémoire) mais pas m_e (encore).")
print()

print("─ VERDICT")
print("  L'intuition V1 (« les constantes viennent de φ,π,e ») était")
print("  légitime. L'exécution V1 (« formule magique ») était réfutée.")
print("  La V2 garde l'intuition et change la méthode : au lieu de")
print("  DEVINER une formule, on DÉRIVE la constante depuis la dynamique")
print("  du niveau correspondant de la tour.")
print("  → Pour α (n=1, EM) : la dérivation n'est pas encore faite.")
print("  → Pour Λ (n=2, gravité) : la dérivation est faite (facteur 3,6).")
print("  → Pour φ (ordre de la mémoire) : dérivé (T1, Hurwitz).")
print("  → Le chemin est tracé — il reste à le parcourir.")

dep={"intuition_V1":"constantes = combinaisons de φ,π,e",
     "execution_V1":"réfutée (treillis, Bonferroni 0/120)",
     "methode_V2":"dériver depuis la dynamique du niveau de la tour",
     "alpha_statut":"NON DÉRIVÉ · pistes : Landau fractionnaire, filtre U(1)",
     "date":time.strftime("%Y-%m-%d %H:%M:%S")}
p=os.path.join("data","benchmarks","alpha_v1_v2_report.json")
os.makedirs(os.path.dirname(p),exist_ok=True)
json.dump(dep,open(p,"w"),indent=2)
print(f"Rapport : {p}")
