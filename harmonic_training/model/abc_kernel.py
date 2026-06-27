"""
Noyau de la derivee fractionnaire d'Atangana-Baleanu (ABC)
===========================================================
Implantation numeriquement stable du noyau de memoire non-locale
base sur la fonction de Mittag-Leffler.

Constantes fondamentales :
    PHI = 1.618033988749895  (nombre d'or)
    ALPHA = 1/PHI = 0.618033988749895  (ordre optimal de la derivee ABC)
    B_1_PHI = 0.8506508083  (constante de normalisation B(alpha) pour alpha=1/phi)
    ALPHA_CONST = 1/B_1_PHI = 1.1755694591  (facteur de normalisation optimal)

Le noyau ABC est defini par :
    K(t) = B(alpha) * E_alpha(-alpha * t^alpha / (1 - alpha))

ou E_alpha est la fonction de Mittag-Leffler a 1 parametre.

Pour la stabilite numerique, on utilise :
1. L'approximation par serie tronquee avec arret precoce
2. Pour les grands arguments, on utilise la decroissance asymptotique
3. On normalise le noyau pour qu'il soit sommable a 1
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F


# =========================================================================
# CONSTANTES HARMONIQUES FONDAMENTALES
# =========================================================================

PHI = 1.618033988749895
ALPHA = 1.0 / PHI  # = 0.618033988749895
B_1_PHI = 0.8506508083
ALPHA_CONST = 1.0 / B_1_PHI  # = 1.1755694591


# =========================================================================
# FONCTION GAMMA (approximation de Lanczos)
# =========================================================================

def lgamma_tensor(x):
    """
    Logarithme de la fonction Gamma pour tenseurs.
    Utilise l'approximation de Lanczos (valide pour Re(z) > 0).
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
    
    x = x.float()
    
    # Reflection formula pour x < 0.5
    mask = x < 0.5
    x_reflected = torch.where(mask, 1.0 - x, x)
    
    xm1 = x_reflected - 1.0
    t = xm1 + g + 0.5
    
    series = c[0] * torch.ones_like(x_reflected)
    for i in range(1, len(c)):
        series = series + c[i] / (xm1 + i)
    
    result = (0.5 * math.log(2 * math.pi) 
              + (xm1 + 0.5) * torch.log(t) 
              - t 
              + torch.log(series))
    
    result = torch.where(
        mask,
        torch.log(math.pi / torch.sin(math.pi * x)) - result,
        result
    )
    
    return result


def gamma_tensor(x):
    """Fonction Gamma pour tenseurs : Gamma(x) = exp(lgamma(x))"""
    return torch.exp(lgamma_tensor(x))


# =========================================================================
# FONCTION DE MITTAG-LEFFLER (version numeriquement stable)
# =========================================================================

def mittag_leffler_stable(z, alpha=ALPHA, max_terms=50, tol=1e-12):
    """
    Fonction de Mittag-Leffler E_alpha(z) avec stabilite numerique.
    
    E_alpha(z) = sum_{k=0}^{inf} z^k / Gamma(alpha * k + 1)
    
    Pour z negatif et |z| grand, la serie alterne.
    On utilise :
    - Arret precoce quand le terme est < tol
    - Sommation en ordre croissant pour minimiser l'erreur d'arrondi
    - Protection contre le debordement
    
    Args:
        z: Tenseur d'entree (valeurs reelles)
        alpha: Ordre de la fonction (defaut: 1/phi)
        max_terms: Nombre maximum de termes (defaut: 50)
        tol: Tolerance pour l'arret precoce (defaut: 1e-12)
    
    Returns:
        E_alpha(z) pour chaque element du tenseur
    """
    device = z.device
    dtype = torch.float64  # Utiliser float64 pour la stabilite
    z = z.to(dtype)
    
    result = torch.zeros_like(z)
    
    for k in range(max_terms):
        # Calcul de z^k avec protection contre le debordement
        log_z_k = k * torch.log(torch.abs(z) + 1e-30)
        
        # Si z est negatif, z^k alterne de signe
        sign = 1.0
        if torch.any(z < 0):
            sign = torch.where(z < 0, (-1.0) ** k, 1.0)
        
        # Gamma(alpha * k + 1)
        gamma_arg = alpha * k + 1.0
        log_gamma = lgamma_tensor(torch.tensor(gamma_arg, device=device))
        
        # log(|terme|) = log(|z|^k) - log(Gamma(...))
        log_term = log_z_k - log_gamma
        
        # Eviter le debordement
        max_log = 80.0  # exp(80) ~ 5.5e34, proche de float32 max
        log_term = torch.clamp(log_term, max=max_log)
        
        term = sign * torch.exp(log_term)
        
        # Verifier si le terme est significatif
        max_term = torch.max(torch.abs(term))
        
        if k > 5 and max_term < tol:
            break
        
        result = result + term
        
        # Si le terme redevient trop grand (divergence), arreter
        if k > 10 and max_term > 1e10:
            break
    
    return result.to(z.device)


# =========================================================================
# NOYAU ABC (version numeriquement stable)
# =========================================================================

class ABCKernel(nn.Module):
    """
    Noyau de la derivee fractionnaire d'Atangana-Baleanu.
    
    K(t) = B(alpha) * E_alpha(-alpha * t^alpha / (1 - alpha))
    
    Version numeriquement stable :
    - Pour t <= 2 : calcul exact par serie
    - Pour t > 2 : approximation par loi de puissance (decroissance lente)
    
    Le noyau est normalise pour que sum(K(t)) = 1.
    
    Usage:
        kernel = ABCKernel(max_len=2048)
        weights = kernel()  # Tenseur [max_len]
    """
    
    def __init__(self, max_len=2048, alpha=ALPHA, B_alpha=B_1_PHI):
        super().__init__()
        self.max_len = max_len
        self.alpha = alpha
        self.B_alpha = B_alpha
        
        # Pre-calcul du noyau
        kernel = self._compute_kernel_stable(max_len)
        self.register_buffer('kernel', kernel)
    
    def _compute_kernel_stable(self, length):
        """
        Calcule K(t) de maniere numeriquement stable.
        
        Pour t <= 2 : utilisation de la serie exacte
        Pour t > 2 : approximation par decroissance en loi de puissance
            K(t) ~ B(alpha) * C / t^(alpha+1)  pour t grand
        """
        t = torch.arange(length, dtype=torch.float64)
        
        # Calcul exact pour les premiers termes
        exact_mask = t <= 2
        
        # Pour t <= 2 : calcul exact
        t_exact = t[exact_mask]
        t_alpha = t_exact ** self.alpha
        arg_exact = -self.alpha * t_alpha / (1.0 - self.alpha)
        ml_exact = mittag_leffler_stable(arg_exact, self.alpha)
        k_exact = self.B_alpha * ml_exact
        
        # Pour t > 2 : approximation par loi de puissance
        # K(t) approxime par B(alpha) / (Gamma(1-alpha) * t^(alpha+1))
        # pour t grand (decroissance en loi de puissance)
        approx_mask = ~exact_mask
        t_approx = t[approx_mask]
        
        # Constante de normalisation asymptotique
        gamma_1_minus_alpha = gamma_tensor(torch.tensor(1.0 - self.alpha))
        C_asymp = 1.0 / gamma_1_minus_alpha
        
        k_approx = self.B_alpha * C_asymp / (t_approx ** (self.alpha + 1.0))
        
        # Assemblage
        kernel = torch.zeros(length, dtype=torch.float64)
        kernel[exact_mask] = k_exact
        kernel[approx_mask] = k_approx
        
        # Normalisation : somme = 1
        kernel = kernel / kernel.sum()
        
        return kernel.float()
    
    def forward(self, length=None):
        """
        Retourne le noyau ABC pour une longueur donnee.
        Le noyau est toujours recalcule et normalise pour la longueur demandee.
        
        Args:
            length: Longueur souhaitee (defaut: max_len)
        
        Returns:
            Tenseur [length] des poids du noyau (somme = 1)
        """
        if length is None:
            length = self.max_len
        
        if length == self.max_len:
            return self.kernel
        
        # Recalculer et normaliser pour la longueur exacte
        return self._compute_kernel_stable(length)
    
    def apply_to_sequence(self, x):
        """
        Applique le noyau ABC a une sequence 1D.
        
        Args:
            x: Tenseur [batch, seq_len] ou [seq_len]
        
        Returns:
            Sequence convoluee avec le noyau ABC (memoire non-locale)
        """
        if x.dim() == 1:
            x = x.unsqueeze(0).unsqueeze(0)
        elif x.dim() == 2:
            x = x.unsqueeze(1)
        
        seq_len = x.shape[-1]
        kernel = self.forward(seq_len)
        
        # Convolution causale (ne regarde que le passe)
        kernel = kernel.flip(0).unsqueeze(0).unsqueeze(0)
        
        # Padding a gauche pour causalite
        result = F.conv1d(x, kernel, padding=seq_len - 1)
        result = result[..., :seq_len]
        
        return result.squeeze()


# =========================================================================
# TEST UNITAIRE
# =========================================================================

def test_abc_kernel():
    """Teste le noyau ABC et verifie les constantes."""
    print("=" * 60)
    print("Test du Noyau ABC (Atangana-Baleanu) - Version stable")
    print("=" * 60)
    
    # Verifier les constantes
    print(f"\nConstantes fondamentales :")
    print(f"  PHI       = {PHI:.15f}")
    print(f"  ALPHA     = {ALPHA:.15f}  (1/PHI)")
    print(f"  B(1/PHI)  = {B_1_PHI:.10f}")
    print(f"  ALPHA_CONST = {ALPHA_CONST:.10f}  (1/B(1/PHI))")
    
    # Creer le noyau
    kernel = ABCKernel(max_len=32)
    
    print(f"\nNoyau ABC K(t) pour t = 0..15 :")
    print(f"  K(t) = B(alpha) * E_alpha(-alpha * t^alpha / (1 - alpha))")
    print(f"  alpha = {ALPHA:.6f}, B(alpha) = {B_1_PHI:.10f}")
    print(f"  (normalise : somme = 1)")
    print()
    
    for t in range(16):
        val = kernel.kernel[t].item()
        print(f"  K({t:2d}) = {val:.10f}")
    
    # Verifier la somme = 1
    total = kernel.kernel.sum().item()
    print(f"\n  Somme totale = {total:.6f}  (devrait etre ~1.0)")
    assert abs(total - 1.0) < 0.01, f"Somme = {total}, devrait etre ~1.0"
    print("[OK] Somme normalisee a 1")
    
    # Verifier K(0) > K(1) > K(2) > ... (decroissance)
    for t in range(1, len(kernel.kernel)):
        assert kernel.kernel[t] <= kernel.kernel[t-1] + 1e-6, \
            f"K({t}) > K({t-1}) : le noyau doit decroitre"
    print("[OK] Le noyau decroit bien avec t (memoire non-locale)")
    
    # Verifier que tous les termes sont positifs
    assert torch.all(kernel.kernel >= 0), "Tous les termes doivent etre positifs"
    print("[OK] Tous les termes sont positifs (stabilite numerique)")
    
    # Test d'application a une sequence
    x = torch.randn(2, 32)
    result = kernel.apply_to_sequence(x)
    assert result.shape == x.shape, f"Shape attendue {x.shape}, obtenue {result.shape}"
    print(f"[OK] Application a une sequence : {x.shape} -> {result.shape}")
    
    # Test avec des longueurs differentes
    for length in [8, 16, 64, 128]:
        k = kernel.forward(length)
        assert len(k) == length, f"Longueur {length} -> {len(k)}"
        # La somme doit etre ~1 car le noyau est normalise
        assert abs(k.sum().item() - 1.0) < 0.05, f"Somme pour L={length}: {k.sum().item()}"
    print("[OK] Noyau fonctionne pour toutes les longueurs (8, 16, 64, 128)")
    
    # Visualisation de la decroissance
    print(f"\nDecroissance du noyau (longueur=128) :")
    k128 = kernel.forward(128)
    print(f"  K(0)   = {k128[0].item():.6f}")
    print(f"  K(10)  = {k128[10].item():.6f}")
    print(f"  K(50)  = {k128[50].item():.6f}")
    print(f"  K(100) = {k128[100].item():.6f}")
    print(f"  K(127) = {k128[127].item():.6f}")
    print(f"  Ratio K(127)/K(0) = {k128[127].item()/k128[0].item():.6f} (memoire longue)")

    
    print(f"\n[SUCCES] Noyau ABC operationnel et numeriquement stable")
    return True


if __name__ == '__main__':
    test_abc_kernel()
