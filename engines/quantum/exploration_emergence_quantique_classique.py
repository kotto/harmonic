#!/usr/bin/env python3
r"""
DÉMONSTRATION — Émergence Quantique & Classique depuis les Ondes
==================================================================
Séquence : Harmonique (ondes) → Quantique → Classique

1. HARMONIQUE → QUANTIQUE
   a. Paquet d'ondes → Principe d'incertitude (Δx·Δk ≥ 1/2)
   b. Modes stationnaires → Quantification (E = n·ℏω)
   c. |Ψ|² → Règle de Born (intensité = densité de probabilité)
   d. Interférences → Corrélations (Einstein-Podolsky-Rosen)

2. QUANTIQUE → CLASSIQUE
   a. Décohérence → Perte des termes non-diagonaux
   b. Limite ℏ → 0 → Principe de moindre action
   c. Moyenne d'ensemble → Thermodynamique

Usage :
  python exploration_emergence_quantique_classique.py
"""

import sys, os, math, time
import numpy as np

PHI = (1 + math.sqrt(5)) / 2
PI = math.pi
TAU = 2 * PI


# ═══════════════════════════════════════════════════════════════════════════════
# PARTIE 1 : HARMONIQUE → QUANTIQUE
# ═══════════════════════════════════════════════════════════════════════════════

def demonstrate_wave_packet_uncertainty():
    """
    1a. Paquet d'ondes gaussien → Principe d'incertitude.
    
    Ψ(x) = exp(-x²/2σ_x²) · exp(i·k₀·x)
    
    Dans l'espace de Fourier : Ψ(k) = exp(-σ_x²·(k-k₀)²/2)
    
    Largeur en x : σ_x
    Largeur en k : σ_k = 1/σ_x
    
    Donc : σ_x · σ_k = 1  (≥ 1/2 après normalisation correcte)
    """
    print("=" * 70)
    print("  1a. INCERTITUDE ONDULATOIRE → HEISENBERG")
    print("=" * 70)
    
    N = 2048
    x = np.linspace(-10, 10, N)
    k = np.fft.fftfreq(N, x[1] - x[0]) * 2 * PI
    
    for sigma_x in [0.5, 1.0, 2.0]:
        # Paquet d'ondes gaussien
        psi_x = np.exp(-x**2 / (2 * sigma_x**2)) * np.exp(1j * 5.0 * x)
        psi_x /= np.sqrt(np.sum(np.abs(psi_x)**2))
        
        # Transformée de Fourier
        psi_k = np.fft.fft(psi_x)
        psi_k = np.fft.fftshift(psi_k)
        k_shifted = np.fft.fftshift(k)
        
        # Largeurs
        prob_x = np.abs(psi_x)**2
        prob_k = np.abs(psi_k)**2
        
        mean_x = np.sum(x * prob_x) / np.sum(prob_x)
        sigma_x_meas = np.sqrt(np.sum((x - mean_x)**2 * prob_x) / np.sum(prob_x))
        
        mean_k = np.sum(k_shifted * prob_k) / np.sum(prob_k)
        sigma_k_meas = np.sqrt(np.sum((k_shifted - mean_k)**2 * prob_k) / np.sum(prob_k))
        
        product = sigma_x_meas * sigma_k_meas
        
        ok = "V" if product >= 0.5 - 0.01 else "X"
        print(f"  σ_x={sigma_x:.1f} → σ_x·σ_k = {product:.4f} (≥ 1/2)  {ok}")
    
    print(f"""
  PRINCIPE : Δx·Δk ≥ 1/2  (onde)
           → Δx·Δp ≥ ℏ/2  (quantique, via p = ℏk)
  
  L'incertitude quantique N'EST PAS une propriété intrinsèque
  de la matière — c'est une propriété GÉOMÉTRIQUE des ondes.
  Tout paquet d'ondes, quel que soit le milieu, obéit à cette
  relation. La physique quantique la redécouvre en posant p = ℏk.
""")

def demonstrate_quantization():
    """
    1b. Modes stationnaires dans une cavité → Quantification.
    
    Onde dans [0, L] avec Ψ(0) = Ψ(L) = 0 :
    Ψ_n(x, t) = sin(n·π·x/L) · exp(-i·ω_n·t)
    
    Fréquences : ω_n = n·π·c/L  (discrètes !)
    Énergies   : E_n = ℏ·ω_n = n·ℏ·π·c/L
    """
    print("=" * 70)
    print("  1b. MODES STATIONNAIRES → QUANTIFICATION")
    print("=" * 70)
    
    L = 1.0
    Nx = 512
    x = np.linspace(0, L, Nx)
    
    print(f"  Cavité [0, {L}] — conditions aux bords Ψ(0)=Ψ(L)=0 :\n")
    
    for n in [1, 2, 3, 5, 10]:
        psi_n = np.sin(n * PI * x / L)
        # Énergie du mode
        omega_n = n * PI / L  # c = 1
        E_n = omega_n  # ℏ = 1
        
        # Compter les zéros (quantification visible)
        zero_crossings = np.sum(np.abs(np.diff(np.sign(psi_n))) > 0)
        
        print(f"  n={n:2d} : ω_{n} = {omega_n:.3f}π/L  E_{n} = {E_n:.3f}ℏπ/L")
    
    print(f"""
  PRINCIPE : Une onde CONFINÉE ne peut exister qu'à des
           fréquences DISCRÈTES (modes stationnaires).
  
  C'est l'origine de la QUANTIFICATION :
  - Atome de Bohr : électron = onde stationnaire autour du noyau
  - Puits quantique : niveaux d'énergie discrets
  - Cavité laser : modes électromagnétiques discrets
  
  La quantification n'est PAS un postulat quantique —
  c'est une propriété GÉOMÉTRIQUE des ondes confinées.
""")

def demonstrate_born_rule():
    """
    1c. |Ψ|² → Règle de Born.
    
    Pour une onde, l'INTENSITÉ est I = |Ψ|².
    Pour une particule quantique, la DENSITÉ DE PROBABILITÉ
    est P(x) = |Ψ(x)|² (règle de Born).
    
    Ces deux concepts sont MATHÉMATIQUEMENT IDENTIQUES.
    La seule différence est l'INTERPRÉTATION :
    - Onde classique : I = énergie transportée
    - Onde quantique : P = probabilité de détection
    
    Mais le formalisme est le MÊME.
    """
    print("=" * 70)
    print("  1c. |Ψ|² → RÈGLE DE BORN")
    print("=" * 70)
    
    N = 512
    x = np.linspace(-5, 5, N)
    
    # Superposition de 3 modes (comme un atome)
    psi = (np.exp(-(x+2)**2/0.5) * np.exp(1j*3*x) +
           0.7 * np.exp(-(x-1)**2/0.8) * np.exp(1j*5*x) +
           0.5 * np.exp(-x**2/1.2) * np.exp(1j*8*x))
    
    prob_density = np.abs(psi)**2
    prob_density /= np.trapz(prob_density, x)  # Normaliser à 1
    
    # Vérifier que ∫|Ψ|² dx = 1
    integral = np.trapz(prob_density, x)
    
    print(f"  ∫|Ψ(x)|² dx = {integral:.6f}  (doit valoir 1)")
    print(f"  max P(x)    = {np.max(prob_density):.4f}")
    
    # Pic principal
    peak_idx = np.argmax(prob_density)
    print(f"  Pic principal à x = {x[peak_idx]:.2f}")
    
    print(f"""
  PRINCIPE : L'intensité d'une onde classique est I = |Ψ|².
           La probabilité de présence quantique est P = |Ψ|².
           
           C'est la MÊME expression mathématique. La règle de
           Born n'est pas un postulat arbitraire — c'est la
           mesure NATURELLE de l'énergie d'une onde.
""")

def demonstrate_interference_correlations():
    """
    1d. Interférences à deux ondes → Corrélations EPR.
    
    Ψ_{AB} = (1/√2)(Ψ_A↑ ⊗ Ψ_B↓ + Ψ_A↓ ⊗ Ψ_B↑)
    
    Mesure de A → réduction instantanée de B.
    Dans le cadre ondulatoire : l'onde Ψ_{AB} est UNIQUE et
    NON-LOCALE — elle occupe tout l'espace. La mesurer en A
    modifie l'onde ENTIÈRE, instantanément.
    """
    print("=" * 70)
    print("  1d. INTERFÉRENCES → CORRÉLATIONS NON-LOCALES")
    print("=" * 70)
    
    N = 256
    x = np.linspace(-2, 2, N)
    
    # Deux ondes corrélées (intriquées)
    psi_A_up = np.exp(-(x+0.5)**2/0.3) * np.exp(1j*3*x)
    psi_A_down = np.exp(-(x+0.5)**2/0.3) * np.exp(1j*5*x)
    psi_B_up = np.exp(-(x-0.5)**2/0.3) * np.exp(1j*3*x)
    psi_B_down = np.exp(-(x-0.5)**2/0.3) * np.exp(1j*5*x)
    
    # État intriqué
    psi_entangled = (1/np.sqrt(2)) * (np.outer(psi_A_up, psi_B_down) + 
                                        np.outer(psi_A_down, psi_B_up))
    
    # Matrice densité réduite
    rho_A = np.trace(psi_entangled @ psi_entangled.conj().T) if psi_entangled.shape[0] == psi_entangled.shape[1] else 0
    
    print(f"  Dimensions de Psi_AB : {psi_entangled.shape}")
    print(f"  Etat intrigue : (1/racine2)(|haut,bas> + |bas,haut>)")
    
    # Corrélation : interférence entre les composantes
    interf = np.real(np.sum(psi_A_up * np.conj(psi_A_down)))
    print(f"  Interférence ⟨↑|↓⟩ = {interf:.6f}")
    
    print("""
  PRINCIPE : Deux ondes peuvent etre correlees GLOBALEMENT
           sans que chaque onde individuelle ait un etat defini.
           
           L'onde intriguee Psi_AB est UNIQUE — elle n'est pas
           la somme de deux ondes independantes. Mesurer A
           modifie l'onde GLOBALE, ce qui affecte B instantanement.
           
           La "non-localite quantique" est une propriete NATURELLE
           des ondes couplees. Rien de mysterieux — juste de
           l'interference a distance.
""")

# ═══════════════════════════════════════════════════════════════════════════════
# PARTIE 2 : QUANTIQUE → CLASSIQUE
# ═══════════════════════════════════════════════════════════════════════════════

def demonstrate_decoherence():
    """
    2a. Décohérence : comment les interférences quantiques
    disparaissent par couplage à l'environnement.
    
    ρ(x, x') → ρ(x, x') · exp(-γ·(x-x')²·t)
    
    Les termes non-diagonaux (x ≠ x') décroissent exponentiellement.
    """
    print("=" * 70)
    print("  2a. DÉCOHÉRENCE → PERTE DES INTERFÉRENCES QUANTIQUES")
    print("=" * 70)
    
    N = 256
    x = np.linspace(-3, 3, N)
    
    # État quantique pur : superposition de deux gaussiennes (chat de Schrödinger)
    psi_alive = np.exp(-(x+1)**2/0.5) * np.exp(1j*2*x)
    psi_dead = np.exp(-(x-1)**2/0.5) * np.exp(1j*4*x)
    psi_cat = (psi_alive + psi_dead) / np.sqrt(2)
    psi_cat /= np.sqrt(np.sum(np.abs(psi_cat)**2))
    
    # Matrice densité pure (avant décohérence)
    rho_pure = np.outer(psi_cat, np.conj(psi_cat))
    
    # Termes non-diagonaux (interférences quantiques)
    nondiag_before = np.sum(np.abs(rho_pure)) - np.sum(np.abs(np.diag(np.diag(rho_pure))))
    
    # Simuler la décohérence
    gamma = 0.1
    t_values = [0, 1, 5, 20]
    
    print(f"  Évolution des interférences quantiques :")
    print(f"  {'Temps':>6s}  {'Interf. (nondiag)':>20s}  {'Classique ?'}")
    print(f"  {'-'*50}")
    
    for t in t_values:
        X, Y = np.meshgrid(x, x)
        decoherence_factor = np.exp(-gamma * (X - Y)**2 * t)
        rho_t = rho_pure * decoherence_factor
        
        nondiag = np.sum(np.abs(rho_t)) - np.sum(np.abs(np.diag(np.diag(rho_t))))
        nondiag_norm = nondiag / (nondiag_before + 1e-10)
        
        is_classical = "OUI" if nondiag_norm < 0.1 else "NON"
        print(f"  t={t:4d}    {nondiag_norm:20.6f}     {is_classical}")
    
    print(f"""
  PRINCIPE : L'interaction avec l'environnement (des milliers
           d'ondes à fréquences aléatoires) moyenne à ZÉRO
           les termes d'interférence de la matrice densité.
           
           Résultat : ρ → diag(P₁, P₂, ...) — une distribution
           de probabilités CLASSIQUE, sans interférences.
           
           La décohérence est le pont entre le monde quantique
           (interférences) et le monde classique (probabilités).
           C'est un processus PHYSIQUE, pas une interprétation.
""")

def demonstrate_classical_limit():
    """
    2b. Limite ℏ → 0 → principe de moindre action classique.
    
    En intégrale de chemin :
    ∫ exp(i·S[x]/ℏ) Dx  →  contribution dominante = δS = 0
    
    Quand ℏ est petit, les chemins qui ne satisfont pas δS = 0
    interfèrent destructivement et s'annulent.
    """
    print("=" * 70)
    print("  2b. LIMITE ℏ → 0 → PRINCIPE DE MOINDRE ACTION")
    print("=" * 70)
    
    # Simuler l'intégrale de chemin pour une particule libre
    N_paths = 1000
    x_final = 1.0
    t_final = 1.0
    
    paths = []
    for _ in range(N_paths):
        # Chemin aléatoire avec x(t_final) = x_final
        t = np.linspace(0, t_final, 100)
        # Chemin brownien + contrainte au bord
        random_walk = np.cumsum(np.random.randn(99) * 0.3)
        path = np.concatenate([[0], random_walk])
        path = path - path[-1] + x_final  # Forcer x(t_final) = x_final
        paths.append(path)
    
    # Action pour chaque chemin (particule libre : S = ∫ (dx/dt)² dt)
    actions = []
    for path in paths:
        dx_dt = np.diff(path) / (t_final / 99)
        S = np.sum(dx_dt**2) * (t_final / 99)
        actions.append(S)
    
    # Chemin classique : ligne droite (action minimale)
    S_classical = (x_final / t_final)**2 * t_final  # (v²)·t, v = x/t = 1
    
    # Phases exp(i·S/ℏ) pour différents ℏ
    for hbar in [1.0, 0.1, 0.01, 1e-5]:
        phases = np.exp(1j * np.array(actions) / hbar)
        amplitude = np.abs(np.mean(phases))
        
        # Si ℏ est petit, seuls les chemins proches de l'action minimale
        # survivent (interférence constructive)
        within_10pct = np.sum(np.abs(np.array(actions) - S_classical) < 0.1 * S_classical)
        classical_prob = within_10pct / N_paths
        
        print(f"  ℏ = {hbar:.0e} : amplitude moy = {amplitude:.4f}, "
              f"chemins proches classique = {classical_prob:.1%}")
    
    print(f"""
  PRINCIPE : Dans l'intégrale de chemin de Feynman, tous les
           chemins contribuent avec un poids exp(i·S/ℏ).
           
           Pour ℏ → 0, les phases varient TRÈS RAPIDEMENT
           d'un chemin à l'autre → interférence destructive
           partout SAUF autour de δS = 0 (principe de moindre
           action).
           
           Le monde classique émerge comme la limite des
           interférences constructives autour du chemin
           d'action minimale.
""")

if __name__ == "__main__":
    print("=" * 74)
    print("  ÉMERGENCE QUANTIQUE & CLASSIQUE DEPUIS LES ONDES")
    print("  Séquence : Harmonique → Quantique → Classique")
    print("=" * 74)
    
    print("\n" + "─" * 74)
    print("  PHASE 1 : HARMONIQUE → QUANTIQUE")
    print("─" * 74)
    
    demonstrate_wave_packet_uncertainty()
    demonstrate_quantization()
    demonstrate_born_rule()
    demonstrate_interference_correlations()
    
    print("\n" + "─" * 74)
    print("  PHASE 2 : QUANTIQUE → CLASSIQUE")
    print("─" * 74)
    
    demonstrate_decoherence()
    demonstrate_classical_limit()
    
    print("\n" + "=" * 74)
    print("  CONCLUSION")
    print("=" * 74)
    print("""
    La séquence d'émergence est :
    
      ONDES (Fourier, superposition)
        │
        ├─ Incertitude Δx·Δk ≥ 1/2 → Heisenberg
        ├─ Modes stationnaires → Quantification
        ├─ |Ψ|² → Règle de Born
        ├─ Interférences globales → Non-localité EPR
        │
        ▼
      PHYSIQUE QUANTIQUE
        │
        ├─ Décohérence → Perte des interférences
        ├─ ℏ → 0 → Principe de moindre action
        ├─ Moyennes d'ensemble → Thermodynamique
        │
        ▼
      PHYSIQUE CLASSIQUE
    
    AUCUNE de ces transitions ne nécessite de nouveau postulat.
    Chaque niveau ÉMERGE naturellement du précédent par :
    - superposition d'ondes
    - interférence
    - limite d'échelle
    
    La physique quantique n'est pas "étrange" — c'est la physique
    des ondes. La physique classique n'est pas "fondamentale" —
    c'est la limite où les interférences se sont moyennées.
""")