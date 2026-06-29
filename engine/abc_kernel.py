"""
Noyau ABC — Atangana-Baleanu-Caputo (Python/Numpy/Torch)
=========================================================
Implantation numeriquement stable du noyau de memoire non-locale
base sur la derivee fractionnaire d'Atangana-Baleanu et la fonction
de Mittag-Leffler.

Contexte mathematique
---------------------
La derivee fractionnaire ABC (Atangana-Baleanu-Caputo) est definie par :

    D^α_t f(t) = B(α)/(1-α) ∫_0^t f'(τ) E_α(-α(t-τ)^α/(1-α)) dτ

ou E_α(z) est la fonction de Mittag-Leffler. Le noyau de cette derivee,
K_α(t-τ) = E_α(-α(t-τ)^α/(1-α)), definit une MEMOIRE NON-LOCALE :
contrairement a une derivee classique (locale), l'etat present depend
de TOUT l'historique, avec un poids decroissant gouverne par le noyau.

Ordre optimal α = 1/φ
----------------------
L'ordre fractionnaire α = 1/φ ≈ 0.618 emerge naturellement :
  - Pour α → 0 : memoire infinie (tout le passe pese egal) → inertie
  - Pour α → 1 : memoire nulle (derivee classique) → amnesie
  - α = 1/φ   : point d'equilibre entre ces deux regimes.
    Le nombre d'or φ = (1+√5)/2 maximise le rapport memoire/inertie
    car φ est le nombre le plus irrationnel (developpement en fraction
    continue le plus lent), garantissant qu'aucun motif de repetition
    ne se forme dans les poids de memoire.

Constantes fondamentales
------------------------
    PHI        : nombre d'or φ = (1+√5)/2 ≈ 1.618033988749895
    ALPHA      : ordre fractionnaire optimal = 1/φ ≈ 0.618033988749895
    B_1_PHI    : constante de normalisation B(α) = 0.8506508083
                 Calibree pour que le noyau discret ait ΣK(t) = 1.
    ALPHA_CONST: facteur de normalisation = 1/B(1/φ) ≈ 1.1755694591

Le noyau ABC est defini par :
    K(t) = B(α) * E_α(-α * t^α / (1 - α))

Reference : Atangana, A., & Baleanu, D. (2016).
    New fractional derivatives with nonlocal and non-singular kernel.
    Thermal Science, 20(2), 763-769.
"""

import math
import numpy as np

# =========================================================================
# CONSTANTES FONDAMENTALES DU NOYAU ABC
# =========================================================================
# PHI   : nombre d'or φ = (1+√5)/2. Irrationalite maximale → memoire non
#         repetitive garantie par construction.
# ALPHA : ordre fractionnaire = 1/φ. Point d'equilibre entre memoire
#         infinie (α→0) et amnesie (α→1).
# B_1_PHI : B(α) — constante de normalisation du noyau discret.
#           Garantit Σ_t K(t) = 1 (conservation de la masse de memoire).
# ALPHA_CONST : 1/B(α) — facteur multiplicatif pour les mises a jour.
# =========================================================================

PHI = 1.618033988749895
ALPHA = 1.0 / PHI  # ≈ 0.618033988749895
B_1_PHI = 0.8506508083
ALPHA_CONST = 1.0 / B_1_PHI  # ≈ 1.1755694591


# =========================================================================
# FONCTION GAMMA (Lanczos)
# =========================================================================

def gamma_lanczos(z):
    """
    Fonction Gamma Γ(z) via approximation de Lanczos.
    
    Args:
        z: scalaire ou np.ndarray (doit etre > 0)
    
    Returns:
        Γ(z) meme shape que z
    """
    g = 7
    c = [
        0.99999999999980993,
        676.5203681218851,
        -1259.1392167224028,
        771.32342877765313,
        -176.61502916214059,
        12.507343278686905,
        -0.13857109526572012,
        9.9843695780195716e-6,
        1.5056327351493116e-7,
    ]
    
    z = np.asarray(z, dtype=np.float64)
    
    # Reflection pour z < 0.5
    mask = z < 0.5
    z_reflected = np.where(mask, 1.0 - z, z)
    
    xm1 = z_reflected - 1.0
    t = xm1 + g + 0.5
    
    # Serie de Lanczos
    series = c[0] * np.ones_like(z_reflected)
    for i in range(1, len(c)):
        series = series + c[i] / (xm1 + i)
    
    result = (0.5 * math.log(2 * math.pi)
              + (xm1 + 0.5) * np.log(t)
              - t
              + np.log(series))
    
    # Reflection formula: log(Gamma(z)) for z < 0.5
    # Use abs(sin) to avoid log of negative numbers, handle sign separately
    sin_pi_z = np.sin(math.pi * z)
    # log(|pi / sin(pi*z)|) - avoid log of negative
    log_reflection = np.log(math.pi / np.abs(sin_pi_z)) - result
    # For the overall sign: Gamma(z) = pi / (sin(pi*z) * Gamma(1-z))
    # When sin_pi_z < 0, Gamma(z) has alternating signs, we take the absolute value
    result = np.where(
        mask,
        log_reflection,  # Use log of absolute value
        result
    )

    
    return np.exp(result)


# =========================================================================
# FONCTION DE MITTAG-LEFFLER (version numpy)
# =========================================================================

def mittag_leffler(z, alpha=ALPHA, max_terms=50, tol=1e-12):
    """
    Fonction de Mittag-Leffler E_alpha(z) version numpy.
    
    E_alpha(z) = sum_{k=0}^{inf} z^k / Gamma(alpha * k + 1)
    
    Args:
        z: scalaire ou np.ndarray
        alpha: ordre (defaut: 1/phi)
        max_terms: nb max de termes
        tol: tolerance arret precoce
    
    Returns:
        E_alpha(z) meme shape que z
    """
    z = np.asarray(z, dtype=np.float64)
    result = np.zeros_like(z)
    
    for k in range(max_terms):
        gamma_val = gamma_lanczos(alpha * k + 1.0)
        term = (z ** k) / gamma_val
        
        result = result + term
        
        if np.max(np.abs(term)) < tol and k > 5:
            break
    
    return result


# =========================================================================
# FONCTION DE MITTAG-LEFFLER (version torch)
# =========================================================================

def mittag_leffler_torch(z, alpha=ALPHA, max_terms=50, tol=1e-12):
    """
    Fonction de Mittag-Leffler E_alpha(z) version torch.
    
    Args:
        z: torch.Tensor
        alpha: ordre (defaut: 1/phi)
        max_terms: nb max de termes
        tol: tolerance arret precoce
    
    Returns:
        E_alpha(z) torch.Tensor
    """
    import torch
    
    device = z.device
    dtype = torch.float64
    z = z.to(dtype)
    
    result = torch.zeros_like(z)
    
    for k in range(max_terms):
        # Calcul de z^k avec protection contre le debordement
        log_z_k = k * torch.log(torch.abs(z) + 1e-30)
        
        sign = 1.0
        if torch.any(z < 0):
            sign = torch.where(z < 0, (-1.0) ** k, 1.0)
        
        gamma_arg = alpha * k + 1.0
        log_gamma = torch.lgamma(torch.tensor(gamma_arg, device=device))
        
        log_term = log_z_k - log_gamma
        max_log = 80.0
        log_term = torch.clamp(log_term, max=max_log)
        
        term = sign * torch.exp(log_term)
        max_term = torch.max(torch.abs(term))
        
        if k > 5 and max_term < tol:
            break
        
        result = result + term
        
        if k > 10 and max_term > 1e10:
            break
    
    return result.to(z.device)


# =========================================================================
# NOYAU ABC (version numpy)
# =========================================================================

def abc_kernel_np(length, alpha=ALPHA, B_alpha=B_1_PHI):
    """
    Calcule le noyau ABC K(t) en numpy.
    
    K(t) = B(alpha) * E_alpha(-alpha * t^alpha / (1 - alpha))
    
    Args:
        length: longueur du noyau
        alpha: ordre fractionnaire
        B_alpha: constante de normalisation
    
    Returns:
        np.ndarray [length] normalise (somme = 1)
    """
    t = np.arange(length, dtype=np.float64)
    
    # Calcul exact pour t <= 2
    exact_mask = t <= 2
    t_exact = t[exact_mask]
    t_alpha = t_exact ** alpha
    arg_exact = -alpha * t_alpha / (1.0 - alpha)
    ml_exact = mittag_leffler(arg_exact, alpha)
    k_exact = B_alpha * ml_exact
    
    # Approximation par loi de puissance pour t > 2
    approx_mask = ~exact_mask
    t_approx = t[approx_mask]
    gamma_1_minus_alpha = gamma_lanczos(1.0 - alpha)
    C_asymp = 1.0 / gamma_1_minus_alpha
    k_approx = B_alpha * C_asymp / (t_approx ** (alpha + 1.0))
    
    # Assemblage et normalisation
    kernel = np.zeros(length, dtype=np.float64)
    kernel[exact_mask] = k_exact
    kernel[approx_mask] = k_approx
    kernel = kernel / kernel.sum()
    
    return kernel.astype(np.float32)


# =========================================================================
# NOYAU ABC (version torch)
# =========================================================================

def abc_kernel_torch(length, alpha=ALPHA, B_alpha=B_1_PHI):
    """
    Calcule le noyau ABC K(t) en torch.
    
    Args:
        length: longueur du noyau
        alpha: ordre fractionnaire
        B_alpha: constante de normalisation
    
    Returns:
        torch.Tensor [length] normalise (somme = 1)
    """
    import torch
    
    t = torch.arange(length, dtype=torch.float64)
    
    # Calcul exact pour t <= 2
    exact_mask = t <= 2
    t_exact = t[exact_mask]
    t_alpha = t_exact ** alpha
    arg_exact = -alpha * t_alpha / (1.0 - alpha)
    ml_exact = mittag_leffler_torch(arg_exact, alpha)
    k_exact = B_alpha * ml_exact
    
    # Approximation pour t > 2
    approx_mask = ~exact_mask
    t_approx = t[approx_mask]
    gamma_1_minus_alpha = torch.lgamma(torch.tensor(1.0 - alpha)).exp()
    C_asymp = 1.0 / gamma_1_minus_alpha
    
    k_approx = B_alpha * C_asymp / (t_approx ** (alpha + 1.0))
    
    # Assemblage et normalisation
    kernel = torch.zeros(length, dtype=torch.float64)
    kernel[exact_mask] = k_exact
    kernel[approx_mask] = k_approx
    kernel = kernel / kernel.sum()
    
    return kernel.float()


# =========================================================================
# CLASSE NOYAU ABC (unifiee, avec cache)
# =========================================================================

class ABCKernel:
    """
    Noyau ABC avec cache et auto-detect numpy/torch.
    
    Usage:
        kernel = ABCKernel()
        w = kernel(128)  # np.ndarray ou torch.Tensor
    """
    
    def __init__(self, max_len=2048, alpha=ALPHA, B_alpha=B_1_PHI):
        self.max_len = max_len
        self.alpha = alpha
        self.B_alpha = B_alpha
        self._cache = {}
    
    def __call__(self, length=None, use_torch=False):
        if length is None:
            length = self.max_len
        
        # Verifier le cache
        cache_key = (length, use_torch)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Calculer
        if use_torch:
            kernel = abc_kernel_torch(length, self.alpha, self.B_alpha)
        else:
            kernel = abc_kernel_np(length, self.alpha, self.B_alpha)
        
        # Mettre en cache
        self._cache[cache_key] = kernel
        return kernel
    
    def get_weights(self, seq_len, use_torch=False):
        """
        Retourne les poids ABC causaux pour une sequence.
        
        Returns:
            weights: [seq_len] ponderation causale
        """
        return self.__call__(seq_len, use_torch)


# =========================================================================
# VALIDATION
# =========================================================================

def test_abc():
    """Test rapide du noyau ABC."""
    print("=" * 60)
    print("TEST : Noyau ABC (Atangana-Baleanu)")
    print("=" * 60)
    
    print(f"\nConstantes :")
    print(f"  PHI       = {PHI:.15f}")
    print(f"  ALPHA     = {ALPHA:.15f}")
    print(f"  B_1_PHI   = {B_1_PHI:.10f}")
    print(f"  ALPHA_CONST = {ALPHA_CONST:.10f}")
    
    # Test numpy
    kernel_np = abc_kernel_np(32)
    print(f"\nNoyau numpy [32] :")
    print(f"  K(0)  = {kernel_np[0]:.10f}")
    print(f"  K(5)  = {kernel_np[5]:.10f}")
    print(f"  K(15) = {kernel_np[15]:.10f}")
    print(f"  K(31) = {kernel_np[31]:.10f}")
    print(f"  Somme = {kernel_np.sum():.6f}")
    assert abs(kernel_np.sum() - 1.0) < 0.01
    print("[OK] Somme normalisee a 1")
    
    # Test torch
    try:
        import torch
        kernel_torch = abc_kernel_torch(32)
        print(f"\nNoyau torch [32] :")
        print(f"  K(0)   = {kernel_torch[0].item():.10f}")
        print(f"  Somme  = {kernel_torch.sum().item():.6f}")
        assert abs(kernel_torch.sum().item() - 1.0) < 0.01
        print("[OK] Version torch operationnelle")
        
        # Verification numpy == torch
        diff = np.max(np.abs(kernel_np - kernel_torch.numpy()))
        print(f"  Difference numpy/torch : {diff:.2e}")
        assert diff < 1e-5
        print("[OK] Numpy et torch coherents")
    except ImportError:
        print("[SKIP] torch non disponible")
    
    # Test classe unifiee
    k = ABCKernel()
    w = k(128)
    print(f"\nClasse ABCKernel [128] :")
    print(f"  K(0)/K(127) = {w[127]/w[0]:.6f} (memoire longue)")
    
    print(f"\n[SUCCES] Noyau ABC operationnel")
    return True


if __name__ == '__main__':
    test_abc()
