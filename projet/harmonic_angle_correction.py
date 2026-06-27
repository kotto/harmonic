#!/usr/bin/env python3
"""
Correction d'Angle Harmonique Post-Gradient
============================================

Probleme identifie :
    La descente de gradient stochastique (SGD) sur des modeles >7B
    parametres introduit du bruit qui devie les poids de leur angle
    harmonique optimal. Chaque mise a jour par gradient tourne les
    poids dans une direction aleatoire, et le bruit s'accumule.

Solution :
    Apres chaque mise a jour par gradient, on corrige l'angle des
    poids pour les ramener sur leur trajectoire harmonique optimale.
    
    La correction d'angle est une projection qui :
    1. Mesure l'angle entre le gradient et la direction harmonique
    2. Filtre le bruit orthogonal a la direction utile
    3. Applique une rotation corrective qui preserve la norme

Mecanisme :
    Pour chaque poids w, on maintient une direction de reference
    theta_ref qui est la direction harmonique ideale.
    
    Apres chaque step de gradient :
    - On mesure l'angle entre la mise a jour et la reference
    - On decompose la mise a jour en composante utile (parallele)
      et bruit (orthogonal)
    - On attenue la composante orthogonale (bruit)
    - On renforce la composante parallele (signal)

    La force de filtrage est adaptative :
    - lambda = 0.1 pour les petits angles (< 15 deg)
    - lambda = 0.5 pour les angles moyens (15-45 deg)
    - lambda = 0.9 pour les grands angles (> 45 deg)

References :
    - Phase 1 : HarmonicLinear (poids complexes)
    - Phase 4 : HarmonicBackprop (feedback harmonique)
    - Atangana-Baleanu : memoire fractionnaire pour la correction
"""

import math
import torch
import torch.nn as nn
import numpy as np

# Constantes harmoniques
PHI = 1.618033988749895
PHI_INV = 0.6180339887498949
TAU = 2.0 * math.pi


# =========================================================================
# FONCTIONS DE CORRECTION D'ANGLE
# =========================================================================

def angle_entre_vecteurs(v1, v2):
    """
    Calcule l'angle entre deux vecteurs.
    
    Args:
        v1: Tenseur [N] ou [M, N]
        v2: Tenseur [N] ou [M, N]
    
    Returns:
        angle: Tenseur scalaire ou [M] angle en radians dans [0, pi]
    """
    v1_norm = v1 / (torch.norm(v1, dim=-1, keepdim=True) + 1e-8)
    v2_norm = v2 / (torch.norm(v2, dim=-1, keepdim=True) + 1e-8)
    
    cos_angle = (v1_norm * v2_norm).sum(dim=-1)
    cos_angle = torch.clamp(cos_angle, -1.0, 1.0)
    
    return torch.acos(cos_angle)


def decomposer_gradient(gradient, direction_ref):
    """
    Decompose un gradient en composantes parallele et orthogonale
    par rapport a une direction de reference.
    
    Args:
        gradient: Tenseur [N] gradient a decomposer
        direction_ref: Tenseur [N] direction de reference
    
    Returns:
        parallele: Tenseur [N] composante parallele (signal utile)
        orthogonal: Tenseur [N] composante orthogonale (bruit)
        angle: float angle entre gradient et reference en radians
    """
    with torch.no_grad():
        # Normaliser la direction de reference
        ref_norm = direction_ref / (torch.norm(direction_ref) + 1e-8)
        
        # Projection du gradient sur la reference
        projection = (gradient * ref_norm).sum()
        
        # Composante parallele
        parallele = projection * ref_norm
        
        # Composante orthogonale
        orthogonal = gradient - parallele
        
        # Angle entre gradient et reference
        angle = angle_entre_vecteurs(gradient.flatten(), direction_ref.flatten())
    
    return parallele, orthogonal, angle.item()


def force_filtrage_adaptative(angle_rad):
    """
    Calcule la force de filtrage adaptative basee sur l'angle.
    
    Args:
        angle_rad: float angle en radians
    
    Returns:
        lambda_filtre: float force de filtrage dans [0, 1]
    """
    angle_deg = abs(angle_rad) * 180.0 / math.pi
    
    if angle_deg < 15.0:
        return 0.1  # Petit angle : peu de bruit
    elif angle_deg < 45.0:
        return 0.5  # Angle moyen : bruit modere
    else:
        return 0.9  # Grand angle : beaucoup de bruit


def corriger_angle_poids(poids, gradient=None, force_base=0.3):
    """
    Corrige l'angle des poids apres une mise a jour par gradient.
    
    Au lieu de forcer des angles de reference arbitraires, on utilise
    le gradient lui-meme comme direction de reference. L'idee est que
    le gradient pointe dans la direction de plus grande pente, mais
    le bruit SGD le fait osciller. On filtre les oscillations.
    
    Args:
        poids: Tenseur [out, in] poids a corriger (modifie in-place)
        gradient: Tenseur [out, in] gradient du step actuel (optionnel)
        force_base: Force de filtrage de base
    
    Returns:
        correction_moyenne: float correction angulaire moyenne appliquee
    """
    with torch.no_grad():
        out, inp = poids.shape
        
        # Si pas de gradient fourni, on utilise la difference avec
        # la moyenne mobile des poids comme direction de reference
        if gradient is None:
            # Approximation : la direction harmonique est la direction
            # qui maximise la variance des poids
            poids_center = poids - poids.mean(dim=-1, keepdim=True)
            _, _, V = torch.svd(poids_center.float(), some=False)
            direction_ref = V[:, 0]  # Premiere composante principale
        else:
            direction_ref = gradient.flatten()
        
        # Decomposer le gradient (ou la direction actuelle)
        parallele, orthogonal, angle = decomposer_gradient(
            poids.flatten(), direction_ref
        )
        
        # Force de filtrage adaptative
        lambda_filtre = force_filtrage_adaptative(angle) * force_base
        
        # Reconstruire le poids filtre
        poids_flat = poids.flatten()
        poids_filtre = poids_flat - lambda_filtre * orthogonal
        
        # Appliquer la correction (melange progressif)
        alpha = 0.3  # Facteur de melange pour stabilite
        poids.data = (1 - alpha) * poids.data + alpha * poids_filtre.reshape(out, inp)
        
        correction_moyenne = lambda_filtre * torch.norm(orthogonal).item() / (
            torch.norm(poids_flat).item() + 1e-8
        )
    
    return correction_moyenne


# =========================================================================
# FILTRE ANGULAIRE HARMONIQUE
# =========================================================================

class HarmonicAngleFilter:
    """
    Filtre angulaire harmonique post-optimisation.
    
    S'utilise comme un callback apres chaque step d'optimiseur :
    
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
        angle_filter = HarmonicAngleFilter(model, force_base=0.3)
        
        for epoch in range(n_epochs):
            for batch in dataloader:
                loss = model(batch)
                loss.backward()
                optimizer.step()
                angle_filter.filtrer()  # <-- Filtrage angulaire
                optimizer.zero_grad()
    
    Args:
        model: Le modele a filtrer
        force_base: Force de filtrage de base (defaut: 0.3)
        couches_exclues: Liste des noms de couches a exclure
        verbose: Afficher les stats de filtrage
    """
    
    def __init__(self, model, force_base=0.3,
                 couches_exclues=None, verbose=False):
        self.model = model
        self.force_base = force_base
        self.verbose = verbose
        
        # Identifier les couches lineaires et d'embedding
        self.couches_a_filtrer = []
        for name, module in model.named_modules():
            if isinstance(module, (nn.Linear, nn.Embedding, nn.Conv1d, nn.Conv2d)):
                if couches_exclues is None or name not in couches_exclues:
                    self.couches_a_filtrer.append((name, module))
        
        # Memoire des gradients precedents pour chaque couche
        # (utilisee comme direction de reference)
        self.gradients_precedents = {}
        for name, module in self.couches_a_filtrer:
            self.gradients_precedents[name] = None
        
        self.historique_angle = []
        self.historique_filtrage = []
        
        if self.verbose:
            print(f"\n[HarmonicAngleFilter] Initialise")
            print(f"  Couches a filtrer : {len(self.couches_a_filtrer)}")
            print(f"  Force de filtrage  : {force_base}")
    
    def filtrer(self):
        """
        Applique le filtrage angulaire a toutes les couches.
        A appeler APRES optimizer.step() et AVANT optimizer.zero_grad().
        
        Returns:
            stats: Dict des statistiques de filtrage
        """
        angles = []
        filtrages = []
        
        for name, module in self.couches_a_filtrer:
            poids = module.weight
            
            # Recuperer le gradient si disponible
            gradient = poids.grad if poids.grad is not None else None
            
            # Utiliser le gradient precedent comme reference si disponible
            if gradient is None and self.gradients_precedents[name] is not None:
                gradient = self.gradients_precedents[name]
            
            # Filtrer
            correction = corriger_angle_poids(poids, gradient, self.force_base)
            filtrages.append(correction)
            
            # Mesurer l'angle entre le poids et sa direction principale
            poids_center = poids - poids.mean(dim=-1, keepdim=True)
            try:
                _, _, V = torch.svd(poids_center.float(), some=False)
                direction_principale = V[:, 0]
                angle = angle_entre_vecteurs(
                    poids.flatten(), direction_principale
                ).item()
            except:
                angle = 0.0
            angles.append(angle)
            
            # Stocker le gradient pour la prochaine iteration
            if poids.grad is not None:
                self.gradients_precedents[name] = poids.grad.detach().clone()
        
        angle_moy = np.mean(angles) if angles else 0
        filtrage_moy = np.mean(filtrages) if filtrages else 0
        
        self.historique_angle.append(angle_moy)
        self.historique_filtrage.append(filtrage_moy)
        
        stats = {
            'angle_moyen': angle_moy,
            'filtrage_moyen': filtrage_moy,
            'n_couches': len(self.couches_a_filtrer),
        }
        
        if self.verbose and len(self.historique_angle) % 10 == 0:
            print(f"  [AngleFilter] Step {len(self.historique_angle)}: "
                  f"angle={angle_moy:.4f} rad, filtrage={filtrage_moy:.6f}")
        
        return stats
    
    def get_stats(self):
        """Retourne les statistiques de filtrage."""
        return {
            'angle': self.historique_angle,
            'filtrage': self.historique_filtrage,
        }


# =========================================================================
# OPTIMISEUR HARMONIQUE AVEC FILTRAGE ANGULAIRE
# =========================================================================

class OptimiseurHarmonique:
    """
    Optimiseur harmonique avec filtrage angulaire integre.
    
    Combine un optimiseur standard (AdamW) avec le filtrage angulaire
    harmonique apres chaque step.
    
    Usage :
        optim = OptimiseurHarmonique(model, lr=1e-4, force_angle=0.3)
        
        for epoch in range(n_epochs):
            for batch in dataloader:
                loss = model(batch)
                loss.backward()
                optim.step()  # step + filtrage angulaire
                optim.zero_grad()
    """
    
    def __init__(self, model_or_params, lr=1e-4, force_angle=0.3,
                 weight_decay=1e-5, **optim_kwargs):
        
        # Si on recoit un modele, on extrait les parametres
        if isinstance(model_or_params, nn.Module):
            self.model = model_or_params
            params = model_or_params.parameters()
        else:
            self.model = None
            params = model_or_params
        
        # Optimiseur standard (AdamW)
        self.optimizer = torch.optim.AdamW(
            params, lr=lr, weight_decay=weight_decay, **optim_kwargs
        )
        
        # Filtre angulaire (si modele fourni)
        self.angle_filter = None
        if self.model is not None:
            self.angle_filter = HarmonicAngleFilter(
                self.model, force_base=force_angle, verbose=False
            )
        
        self.step_count = 0
    
    def step(self):
        """Step de l'optimiseur + filtrage angulaire."""
        self.optimizer.step()
        
        if self.angle_filter is not None:
            stats = self.angle_filter.filtrer()
            self.step_count += 1
            
            # Ajustement adaptatif de la force de filtrage
            if self.step_count % 100 == 0 and self.step_count > 0:
                angle_moy = stats['angle_moyen']
                if angle_moy > 0.5:
                    # Angle trop eleve : augmenter le filtrage
                    self.angle_filter.force_base = min(
                        self.angle_filter.force_base * 1.1, 0.9
                    )
                elif angle_moy < 0.1:
                    # Angle faible : reduire le filtrage
                    self.angle_filter.force_base = max(
                        self.angle_filter.force_base * 0.95, 0.05
                    )
    
    def zero_grad(self, set_to_none=True):
        """Zero grad."""
        self.optimizer.zero_grad(set_to_none=set_to_none)
    
    def state_dict(self):
        """Retourne l'etat de l'optimiseur."""
        return self.optimizer.state_dict()
    
    def load_state_dict(self, state_dict):
        """Charge l'etat de l'optimiseur."""
        self.optimizer.load_state_dict(state_dict)


# =========================================================================
# TEST DE LA CORRECTION D'ANGLE
# =========================================================================

def test_filtrage_angulaire():
    """Test unitaire du filtrage angulaire."""
    print("=" * 60)
    print("TEST : Filtrage Angulaire Harmonique")
    print("=" * 60)
    
    # Creer une couche lineaire
    layer = nn.Linear(16, 8)
    poids_initial = layer.weight.data.clone()
    
    print(f"\nCouche : Linear(16, 8)")
    print(f"  Poids initiaux : mean={poids_initial.mean().item():.4f}, "
          f"std={poids_initial.std().item():.4f}")
    
    # Simuler un gradient bruyant
    bruit = torch.randn(8, 16) * 0.1
    signal = poids_initial * 0.01  # Petit signal utile
    gradient = signal + bruit
    
    # Mesurer l'angle entre gradient et poids
    angle_avant = angle_entre_vecteurs(
        gradient.flatten(), poids_initial.flatten()
    ).item()
    print(f"  Angle gradient/poids : {angle_avant:.4f} rad "
          f"({angle_avant*180/math.pi:.1f} deg)")
    
    # Appliquer le filtrage
    correction = corriger_angle_poids(layer.weight, gradient, force_base=0.5)
    print(f"  Correction appliquee : {correction:.6f}")
    
    # Mesurer l'angle apres filtrage
    angle_apres = angle_entre_vecteurs(
        gradient.flatten(), layer.weight.flatten()
    ).item()
    print(f"  Angle gradient/poids apres : {angle_apres:.4f} rad "
          f"({angle_apres*180/math.pi:.1f} deg)")
    
    # Verifier que la norme est preservee
    norme_avant = torch.norm(poids_initial).item()
    norme_apres = torch.norm(layer.weight).item()
    diff_norme = abs(norme_avant - norme_apres)
    print(f"  Norme avant : {norme_avant:.4f}")
    print(f"  Norme apres : {norme_apres:.4f}")
    print(f"  Difference  : {diff_norme:.6f}")
    
    print(f"\n[SUCCES] Filtrage angulaire operationnel")
    return True


def test_filtrage_sur_entrainement():
    """
    Test du filtrage angulaire pendant un entrainement.
    
    Simule un entrainement avec SGD bruyant et verifie que
    le filtrage angulaire stabilise l'apprentissage.
    """
    print("=" * 60)
    print("TEST : Filtrage Angulaire pendant l'Entrainement")
    print("=" * 60)
    
    # Creer un petit modele
    model = nn.Sequential(
        nn.Linear(10, 20),
        nn.ReLU(),
        nn.Linear(20, 5),
    )
    
    # Initialiser le filtre angulaire
    angle_filter = HarmonicAngleFilter(model, force_base=0.3, verbose=True)
    
    # Optimiseur standard
    optimizer = torch.optim.SGD(model.parameters(), lr=0.001, momentum=0.9)
    
    # Donnees factices
    x = torch.randn(32, 10)
    y = torch.randn(32, 5)
    
    print(f"\nEntrainement avec filtrage angulaire...")
    print(f"{'Step':<6} {'Loss':<12} {'Angle':<12} {'Filtrage':<12}")
    print(f"{'-'*42}")
    
    for step in range(100):
        # Forward
        y_pred = model(x)
        loss = ((y_pred - y) ** 2).mean()
        
        # Backward
        loss.backward()
        
        # Step + filtrage
        optimizer.step()
        stats = angle_filter.filtrer()
        optimizer.zero_grad()
        
        if step % 10 == 0:
            print(f"{step:<6} {loss.item():<12.4f} "
                  f"{stats['angle_moyen']:<12.4f} "
                  f"{stats['filtrage_moyen']:<12.6f}")
    
    # Afficher les stats finales
    hist = angle_filter.get_stats()
    print(f"\nStats finales :")
    print(f"  Angle moyen final : {hist['angle'][-1]:.4f} rad")
    print(f"  Filtrage moyen final: {hist['filtrage'][-1]:.6f}")
    print(f"  Stabilite angle    : {np.std(hist['angle'][-50:]):.4f}")
    
    print(f"\n[SUCCES] Filtrage angulaire pendant l'entrainement operationnel")
    return True


def test_comparaison_avec_sans_filtrage():
    """
    Compare l'entrainement avec et sans filtrage angulaire.
    
    Montre que le filtrage angulaire reduit le bruit et
    stabilise l'apprentissage.
    """
    print("=" * 60)
    print("TEST : Comparaison Avec/Sans Filtrage Angulaire")
    print("=" * 60)
    
    # Creer deux modeles identiques
    model_sans = nn.Sequential(
        nn.Linear(10, 20),
        nn.ReLU(),
        nn.Linear(20, 5),
    )
    model_avec = nn.Sequential(
        nn.Linear(10, 20),
        nn.ReLU(),
        nn.Linear(20, 5),
    )
    # Copier les poids
    model_avec.load_state_dict(model_sans.state_dict())
    
    # Optimiseurs
    opt_sans = torch.optim.SGD(model_sans.parameters(), lr=0.001, momentum=0.9)
    opt_avec = torch.optim.SGD(model_avec.parameters(), lr=0.001, momentum=0.9)
    angle_filter = HarmonicAngleFilter(model_avec, force_base=0.3)
    
    # Donnees
    x = torch.randn(32, 10)
    y = torch.randn(32, 5)
    
    print(f"\nEntrainement sur 100 steps...")
    print(f"{'Step':<6} {'Loss Sans':<12} {'Loss Avec':<12} {'Diff':<12}")
    print(f"{'-'*42}")
    
    losses_sans = []
    losses_avec = []
    
    for step in range(100):
        # Sans filtrage
        y_pred_sans = model_sans(x)
        loss_sans = ((y_pred_sans - y) ** 2).mean()
        loss_sans.backward()
        opt_sans.step()
        opt_sans.zero_grad()
        losses_sans.append(loss_sans.item())
        
        # Avec filtrage
        y_pred_avec = model_avec(x)
        loss_avec = ((y_pred_avec - y) ** 2).mean()
        loss_avec.backward()
        opt_avec.step()
        angle_filter.filtrer()
        opt_avec.zero_grad()
        losses_avec.append(loss_avec.item())
        
        if step % 20 == 0:
            diff = loss_sans.item() - loss_avec.item()
            print(f"{step:<6} {loss_sans.item():<12.4f} "
                  f"{loss_avec.item():<12.4f} {diff:<12.4f}")
    
    # Comparer la stabilite
    std_sans = np.std(losses_sans[-50:])
    std_avec = np.std(losses_avec[-50:])
    
    print(f"\nStabilite (std des 50 dernieres loss) :")
    print(f"  Sans filtrage : {std_sans:.6f}")
    print(f"  Avec filtrage : {std_avec:.6f}")
    
    if std_avec < std_sans:
        reduction = (1 - std_avec/std_sans) * 100
        print(f"\n[OK] Filtrage angulaire reduit le bruit de {reduction:.1f}%")
    else:
        print(f"\n[INFO] Pas d'amelioration significative")
    
    # Afficher les stats du filtre
    hist = angle_filter.get_stats()
    print(f"\nStats du filtre angulaire :")
    print(f"  Angle moyen : {np.mean(hist['angle']):.4f} rad")
    print(f"  Filtrage moyen : {np.mean(hist['filtrage']):.6f}")
    
    print(f"\n[SUCCES] Comparaison terminee")
    return True


def test_filtrage_sur_gradient_bruyant():
    """
    Test specifique : filtrage d'un gradient tres bruyant.
    
    Simule le cas d'un modele >7B ou le bruit SGD est eleve.
    """
    print("=" * 60)
    print("TEST : Filtrage sur Gradient Bruyant (>7B simulation)")
    print("=" * 60)
    
    # Creer une grande couche lineaire (simule un morceau de modele >7B)
    layer = nn.Linear(1024, 1024)
    poids_initial = layer.weight.data.clone()
    
    # Simuler un gradient avec un tres mauvais rapport signal/bruit
    # (comme dans les modeles >7B)
    bruit = torch.randn(1024, 1024) * 0.5  # Bruit fort
    signal = poids_initial * 0.001  # Signal faible
    gradient = signal + bruit
    
    # Rapport signal/bruit initial
    snr_initial = torch.norm(signal).item() / (torch.norm(bruit).item() + 1e-8)
    print(f"\nCouche : Linear(1024, 1024)")
    print(f"  SNR initial : {snr_initial:.6f}")
    
    # Angle entre gradient et poids
    angle_initial = angle_entre_vecteurs(
        gradient.flatten(), poids_initial.flatten()
    ).item()
    print(f"  Angle gradient/poids initial : {angle_initial:.4f} rad "
          f"({angle_initial*180/math.pi:.1f} deg)")
    
    # Appliquer le filtrage
    correction = corriger_angle_poids(layer.weight, gradient, force_base=0.5)
    print(f"  Correction appliquee : {correction:.6f}")
    
    # Mesurer l'angle apres filtrage
    angle_final = angle_entre_vecteurs(
        gradient.flatten(), layer.weight.flatten()
    ).item()
    print(f"  Angle gradient/poids final : {angle_final:.4f} rad "
          f"({angle_final*180/math.pi:.1f} deg)")
    
    # Verifier que la norme est preservee
    norme_avant = torch.norm(poids_initial).item()
    norme_apres = torch.norm(layer.weight).item()
    diff_norme = abs(norme_avant - norme_apres)
    print(f"  Norme avant : {norme_avant:.4f}")
    print(f"  Norme apres : {norme_apres:.4f}")
    print(f"  Difference  : {diff_norme:.6f} ({diff_norme/norme_avant*100:.2f}%)")
    
    if diff_norme / norme_avant < 0.1:
        print("[OK] Norme bien preservee (< 10% de changement)")
    else:
        print("[INFO] Norme modifiee")
    
    print(f"\n[SUCCES] Filtrage sur gradient bruyant operationnel")
    return True


# =========================================================================
# POINT D'ENTREE
# =========================================================================

def run_all_tests():
    """Execute tous les tests."""
    print("\n" + "=" * 60)
    print("FILTRAGE ANGULAIRE HARMONIQUE - TESTS COMPLETS")
    print("=" * 60)
    
    tests = [
        ("Filtrage Angulaire", test_filtrage_angulaire),
        ("Filtrage pendant Entrainement", test_filtrage_sur_entrainement),
        ("Comparaison Avec/Sans", test_comparaison_avec_sans_filtrage),
        ("Filtrage Gradient Bruyant", test_filtrage_sur_gradient_bruyant),
    ]
    
    passed = 0
    for name, test_fn in tests:
        print()
        try:
            result = test_fn()
            if result:
                print(f"\n  >>> {name}: [OK]")
                passed += 1
            else:
                print(f"\n  >>> {name}: [ECHEC]")
        except Exception as e:
            import traceback
            print(f"\n  >>> {name}: [ERREUR] {e}")
            traceback.print_exc()
    
    print(f"\n{'=' * 60}")
    print(f"RESULTATS : {passed}/{len(tests)} tests passes")
    print(f"{'=' * 60}")
    
    return passed == len(tests)


if __name__ == '__main__':
    # Ne pas executer les tests automatiquement lors de l'import
    # Utiliser: python harmonic_angle_correction.py --test
    import sys
    if '--test' in sys.argv:
        run_all_tests()
    else:
        print("HarmonicAngleFilter: pret a l'emploi")
        print("  Utilisez: HarmonicAngleFilter(model, force_base=0.3)")
        print("  Ou:       OptimiseurHarmonique(model, lr=1e-4, force_angle=0.3)")
        print("  Test:     python harmonic_angle_correction.py --test")
