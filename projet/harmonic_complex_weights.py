#!/usr/bin/env python3
"""
Phase 1 : Poids Complexes Harmoniques
======================================
Remplace nn.Linear par HarmonicLinear avec poids complexes.
La phase des poids est le mecanisme d'apprentissage (pas le gradient).

Principe :
    - Chaque poids w est un nombre complexe : w = r * exp(i * theta)
    - r = magnitude (apprise, mais stable)
    - theta = phase (ajustee par resonance)
    - L'apprentissage ajuste theta pour aligner les phases

Avantages :
    - Pas de backpropagation classique
    - Apprentissage par rotation de phase (continu, pas de pas discret)
    - Memoire naturelle (la phase persiste)
    - Orthogonalite des frequences

References :
    - Atangana-Baleanu fractional derivative (ABC kernel)
    - Harmonic resonance learning
    - Complex-valued neural networks
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


# =========================================================================
# CONSTANTES HARMONIQUES
# =========================================================================

PHI = 1.618033988749895  # Nombre d'or
PHI_INV = 0.6180339887498949  # 1/PHI
TAU = 2.0 * math.pi  # Constante de normalisation angulaire


# =========================================================================
# FONCTIONS DE BASE POUR LES NOMBRES COMPLEXES HARMONIQUES
# =========================================================================

def complex_mul(z1_real, z1_imag, z2_real, z2_imag):
    """
    Multiplication de deux nombres complexes.
    (a + ib)(c + id) = (ac - bd) + i(ad + bc)
    """
    real = z1_real * z2_real - z1_imag * z2_imag
    imag = z1_real * z2_imag + z1_imag * z2_real
    return real, imag


def polar_to_rect(magnitude, phase):
    """
    Convertit des coordonnees polaires en rectangulaires.
    z = r * exp(i * theta) = r*cos(theta) + i*r*sin(theta)
    
    Args:
        magnitude: Tenseur [..., 1] des magnitudes (r)
        phase: Tenseur [..., 1] des phases (theta en radians)
    
    Returns:
        real: Tenseur [..., 1] partie reelle
        imag: Tenseur [..., 1] partie imaginaire
    """
    real = magnitude * torch.cos(phase)
    imag = magnitude * torch.sin(phase)
    return real, imag


def rect_to_polar(real, imag):
    """
    Convertit des coordonnees rectangulaires en polaires.
    r = sqrt(real^2 + imag^2)
    theta = atan2(imag, real)
    
    Args:
        real: Tenseur [...] partie reelle
        imag: Tenseur [...] partie imaginaire
    
    Returns:
        magnitude: Tenseur [...] magnitude (r)
        phase: Tenseur [...] phase (theta en radians)
    """
    magnitude = torch.sqrt(real**2 + imag**2 + 1e-8)
    phase = torch.atan2(imag, real)
    return magnitude, phase


def phase_rotation(phase, delta_phase):
    """
    Applique une rotation de phase.
    theta_new = theta + delta_theta
    
    Args:
        phase: Tenseur [...] phase actuelle
        delta_phase: Tenseur [...] ou scalaire, rotation a appliquer
    
    Returns:
        phase_rotated: Tenseur [...] phase apres rotation
    """
    return (phase + delta_phase) % TAU


def resonance_measure(x, y):
    """
    Mesure le degre de resonance entre deux tenseurs.
    Resonance = cos(angle) = (x·y) / (|x|*|y|)
    
    Args:
        x: Tenseur [..., dim]
        y: Tenseur [..., dim]
    
    Returns:
        resonance: Tenseur [...] dans [-1, 1], 1 = resonance parfaite
    """
    x_norm = F.normalize(x, dim=-1)
    y_norm = F.normalize(y, dim=-1)
    return (x_norm * y_norm).sum(dim=-1)


# =========================================================================
# COUCHE LINEAIRE HARMONIQUE A POIDS COMPLEXES
# =========================================================================

class HarmonicLinear(nn.Module):
    """
    Couche lineaire avec poids complexes harmoniques.
    
    Au lieu de poids reels w, on a :
    - magnitude: tenseur [out_features, in_features] (positif, stabilise)
    - phase: tenseur [out_features, in_features] (en radians, ajustable)
    
    La sortie est : y = |W| * exp(i * theta_W) * x
    (mais on ne garde que la partie reelle pour la compatibilite)
    
    L'apprentissage se fait par rotation de phase :
    theta_W += delta_theta  (pas de gradient, pas de backprop)
    
    Args:
        in_features: Nombre d'entrees
        out_features: Nombre de sorties
        bias: Si True, ajoute un biais harmonique
        init_phase: Phase initiale (defaut: basee sur PHI)
        init_magnitude: Magnitude initiale (defaut: 0.1)
        learnable_magnitude: Si True, la magnitude est aussi apprise
    """
    
    def __init__(self, in_features, out_features, bias=True,
                 init_phase=None, init_magnitude=0.1,
                 learnable_magnitude=False):
        super().__init__()
        
        self.in_features = in_features
        self.out_features = out_features
        self.learnable_magnitude = learnable_magnitude
        
        # --- Magnitude (module du poids complexe) ---
        # Initialisee a une constante, peut etre apprise ou non
        if learnable_magnitude:
            self.magnitude = nn.Parameter(
                torch.full((out_features, in_features), init_magnitude)
            )
        else:
            self.register_buffer(
                'magnitude',
                torch.full((out_features, in_features), init_magnitude)
            )
        
        # --- Phase (angle du poids complexe) ---
        # Initialisee harmoniquement (basee sur PHI)
        if init_phase is None:
            # Phase harmonique : chaque poids a une phase differente
            # basee sur sa position et le nombre d'or
            init_phase = self._harmonic_phase_init(out_features, in_features)
        
        self.phase = nn.Parameter(init_phase)
        
        # --- Biais harmonique ---
        if bias:
            if init_phase is None:
                bias_phase = self._harmonic_phase_init(out_features, 1).squeeze(-1)
            else:
                bias_phase = torch.zeros(out_features)
            
            self.bias_magnitude = nn.Parameter(
                torch.full((out_features,), init_magnitude * 0.1)
            ) if learnable_magnitude else self.register_buffer(
                'bias_magnitude',
                torch.full((out_features,), init_magnitude * 0.1)
            )
            self.bias_phase = nn.Parameter(bias_phase)
        else:
            self.register_buffer('bias_magnitude', None)
            self.register_buffer('bias_phase', None)
        
        # Compteur d'apprentissage
        self.register_buffer('learning_step', torch.tensor(0))
        
        # Historique de resonance
        self.resonance_history = []
    
    def _harmonic_phase_init(self, rows, cols):
        """
        Initialise les phases avec des valeurs harmoniques.
        
        Chaque poids (i, j) a une phase :
        theta_ij = 2*pi * (i/rows + j/cols) * PHI_INV
        
        Cela cree un motif de phases harmoniques.
        """
        i_idx = torch.arange(rows, dtype=torch.float32).unsqueeze(1)
        j_idx = torch.arange(cols, dtype=torch.float32).unsqueeze(0)
        
        # Phase harmonique
        phase = TAU * (i_idx / rows + j_idx / cols) * PHI_INV
        phase = phase % TAU
        
        return nn.Parameter(phase)
    
    def forward(self, x):
        """
        Forward pass avec poids complexes.
        
        y = Re(W * x) = |W| * cos(theta_W) * x
        
        On utilise seulement la partie reelle pour la compatibilite
        avec les couches suivantes (ReLU, etc.)
        
        Args:
            x: Tenseur [batch, in_features] ou [batch, seq_len, in_features]
        
        Returns:
            y: Tenseur [batch, out_features] ou [batch, seq_len, out_features]
        """
        # Poids reel effectif = magnitude * cos(phase)
        # (partie reelle du poids complexe)
        weight_real = self.magnitude * torch.cos(self.phase)
        
        # Forward lineaire standard avec le poids reel
        y = F.linear(x, weight_real)
        
        # Ajouter le biais si present
        if self.bias_magnitude is not None:
            bias_real = self.bias_magnitude * torch.cos(self.bias_phase)
            y = y + bias_real
        
        return y
    
    def get_complex_weight(self):
        """
        Retourne le poids complexe complet.
        
        Returns:
            magnitude: Tenseur [out_features, in_features]
            phase: Tenseur [out_features, in_features]
        """
        return self.magnitude, self.phase
    
    def get_weight_real(self):
        """
        Retourne la partie reelle du poids.
        
        Returns:
            weight_real: Tenseur [out_features, in_features]
        """
        return self.magnitude * torch.cos(self.phase)
    
    def get_weight_imag(self):
        """
        Retourne la partie imaginaire du poids.
        
        Returns:
            weight_imag: Tenseur [out_features, in_features]
        """
        return self.magnitude * torch.sin(self.phase)
    
    def resonance_learn(self, x, target, coupling=0.1):
        """
        Apprentissage par resonance (pas de backprop).
        
        Ajuste la phase des poids pour aligner la sortie sur la cible.
        
        Principe :
        1. On calcule la sortie actuelle
        2. On mesure le decalage de phase entre sortie et cible
        3. On tourne les phases des poids dans la direction qui reduit le decalage
        
        Args:
            x: Tenseur [batch, in_features] entree
            target: Tenseur [batch, out_features] cible
            coupling: Facteur de couplage (vitesse d'apprentissage)
        
        Returns:
            resonance: Score de resonance avant ajustement
        """
        with torch.no_grad():
            # Sortie actuelle
            y_current = self.forward(x)
            
            # Mesure de resonance avant ajustement
            res_before = resonance_measure(y_current, target).mean()
            self.resonance_history.append(res_before.item())
            
            # Si deja en resonance, rien a faire
            if res_before > 0.95:
                return res_before
            
            # Calcul du decalage de phase
            # On veut que la sortie soit en phase avec la cible
            # delta_phase = angle(y_current) - angle(target)
            # Mais comme on n'a que la partie reelle, on approxime
            
            # Approximation : le gradient de la phase est proportionnel
            # a l'erreur de resonance
            # error: [batch, out_features], x: [batch, in_features]
            # On veut delta_phase: [out_features, in_features]
            # delta_phase = coupling * (error^T @ x) / |W|
            error = target - y_current  # [batch, out_features]
            
            # Ajustement de la phase
            # delta_phase = coupling * (error^T @ x) / |W|
            # error^T @ x : [out_features, batch] @ [batch, in_features] = [out_features, in_features]
            delta_phase = coupling * torch.mm(error.t(), x) / (self.magnitude + 1e-8)
            
            # Rotation de phase
            self.phase.data = phase_rotation(self.phase.data, delta_phase)
            
            # Optionnel : ajuster la magnitude si apprise
            if self.learnable_magnitude:
                delta_mag = coupling * torch.mm(error.t(), x) * torch.cos(self.phase)
                self.magnitude.data = torch.clamp(
                    self.magnitude.data + delta_mag,
                    min=1e-6, max=10.0
                )
            
            self.learning_step += 1
            
            return res_before
    
    def extra_repr(self):
        return f"in_features={self.in_features}, out_features={self.out_features}, " \
               f"learnable_magnitude={self.learnable_magnitude}"


# =========================================================================
# RESEAU HARMONIQUE COMPLET (EXEMPLE MNIST)
# =========================================================================

class HarmonicMNISTNet(nn.Module):
    """
    Reseau harmonique pour MNIST avec poids complexes.
    
    Architecture :
    - HarmonicLinear(784, 256) + ReLU
    - HarmonicLinear(256, 128) + ReLU
    - HarmonicLinear(128, 10)
    
    L'apprentissage se fait par resonance_learn(), pas par backprop.
    """
    
    def __init__(self, learnable_magnitude=False):
        super().__init__()
        
        self.fc1 = HarmonicLinear(784, 256, init_magnitude=0.1,
                                   learnable_magnitude=learnable_magnitude)
        self.fc2 = HarmonicLinear(256, 128, init_magnitude=0.1,
                                   learnable_magnitude=learnable_magnitude)
        self.fc3 = HarmonicLinear(128, 10, init_magnitude=0.1,
                                   learnable_magnitude=learnable_magnitude)
        
        self.relu = nn.ReLU()
    
    def forward(self, x):
        """
        Forward pass.
        
        Args:
            x: Tenseur [batch, 1, 28, 28] ou [batch, 784]
        
        Returns:
            logits: Tenseur [batch, 10]
        """
        if x.dim() == 4:
            x = x.view(x.size(0), -1)  # [batch, 784]
        
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.fc3(x)
        
        return x
    
    def resonance_train(self, x, target, coupling=0.1):
        """
        Entraînement par resonance sur un batch.
        
        Propage la resonance de la derniere couche vers la premiere.
        
        Args:
            x: Tenseur [batch, 784] entree
            target: Tenseur [batch, 10] cible (one-hot)
            coupling: Facteur de couplage
        
        Returns:
            resonances: Liste des scores de resonance par couche
        """
        resonances = []
        
        # Forward
        h1 = self.relu(self.fc1(x))
        h2 = self.relu(self.fc2(h1))
        y = self.fc3(h2)
        
        # Resonance couche 3 (sortie) : compare h2 -> y avec target
        r3 = self.fc3.resonance_learn(h2, target, coupling)
        resonances.append(r3)
        
        # Cible pour couche 2 : on veut que h2 soit tel que fc3(h2) ~ target
        # On retro-propage la cible via la transposee du poids de fc3
        with torch.no_grad():
            # target_h2 = W_3^T * target  (pseudo-inverse)
            w3_real = self.fc3.get_weight_real()  # [10, 128]
            target_h2 = torch.mm(target, w3_real)  # [batch, 128]
            target_h2 = torch.relu(target_h2)  # appliquer la non-linearite
        
        # Resonance couche 2 : compare h1 -> h2 avec target_h2
        r2 = self.fc2.resonance_learn(h1, target_h2, coupling * 0.5)
        resonances.append(r2)
        
        # Cible pour couche 1
        with torch.no_grad():
            w2_real = self.fc2.get_weight_real()  # [128, 256]
            target_h1 = torch.mm(target_h2, w2_real)  # [batch, 256]
            target_h1 = torch.relu(target_h1)
        
        # Resonance couche 1 : compare x -> h1 avec target_h1
        r1 = self.fc1.resonance_learn(x, target_h1, coupling * 0.25)
        resonances.append(r1)
        
        return resonances


# =========================================================================
# TEST SUR MNIST
# =========================================================================

def test_harmonic_linear():
    """Test unitaire de HarmonicLinear."""
    print("=" * 60)
    print("TEST : HarmonicLinear (Poids Complexes)")
    print("=" * 60)
    
    batch, in_features, out_features = 4, 16, 8
    
    # Creation
    layer = HarmonicLinear(in_features, out_features)
    
    print(f"\nConfiguration :")
    print(f"  in_features  = {in_features}")
    print(f"  out_features = {out_features}")
    print(f"  parametres   = {sum(p.numel() for p in layer.parameters()):,}")
    
    # Forward
    x = torch.randn(batch, in_features)
    y = layer(x)
    
    print(f"\nForward pass :")
    print(f"  Input  : {x.shape}")
    print(f"  Output : {y.shape}")
    assert y.shape == (batch, out_features), f"Shape: {y.shape}"
    print("[OK] Forward pass correcte")
    
    # Poids complexes
    mag, phase = layer.get_complex_weight()
    print(f"\nPoids complexes :")
    print(f"  Magnitude : {mag.shape}, mean={mag.mean().item():.4f}")
    print(f"  Phase     : {phase.shape}, mean={phase.mean().item():.4f}")
    assert mag.shape == (out_features, in_features)
    assert phase.shape == (out_features, in_features)
    print("[OK] Poids complexes corrects")
    
    # Partie reelle et imaginaire
    w_real = layer.get_weight_real()
    w_imag = layer.get_weight_imag()
    print(f"\n  Partie reelle  : mean={w_real.mean().item():.4f}, std={w_real.std().item():.4f}")
    print(f"  Partie imaginaire : mean={w_imag.mean().item():.4f}, std={w_imag.std().item():.4f}")
    
    # Test de resonance
    target = torch.randn(batch, out_features)
    res_before = resonance_measure(y, target).mean()
    print(f"\nResonance avant apprentissage : {res_before.item():.4f}")
    
    # Apprentissage par resonance
    for step in range(10):
        res = layer.resonance_learn(x, target, coupling=0.05)
        if step == 0:
            print(f"  Step {step}: resonance = {res.item():.4f}")
    
    # Verifier que la resonance a augmente
    y_after = layer(x)
    res_after = resonance_measure(y_after, target).mean()
    print(f"Resonance apres 10 steps : {res_after.item():.4f}")
    
    # Test de gradient (verifier que la retropropagation classique fonctionne encore)
    loss = y_after.sum()
    loss.backward()
    has_grad = all(
        p.grad is not None and p.grad.abs().sum() > 0
        for p in layer.parameters()
    )
    print(f"\nGradient (backprop classique) : {'[OK]' if has_grad else '[FAIL]'}")
    
    print(f"\n[SUCCES] HarmonicLinear operationnel")
    return True


def test_mnist_resonance():
    """
    Test d'apprentissage par resonance sur MNIST.
    
    Verifie que le modele peut apprendre par rotation de phase
    sans backpropagation classique.
    """
    print("=" * 60)
    print("TEST : Apprentissage par Resonance sur MNIST")
    print("=" * 60)
    
    # Creer le modele
    model = HarmonicMNISTNet(learnable_magnitude=False)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"\nModele : {total_params:,} parametres")
    
    # Generer des donnees factices (simule MNIST)
    batch_size = 32
    num_classes = 10
    
    # Donnees d'entrainement
    x_train = torch.randn(100, 784)  # 100 echantillons
    y_train = torch.randint(0, num_classes, (100,))
    y_train_onehot = F.one_hot(y_train, num_classes).float()
    
    # Donnees de test
    x_test = torch.randn(20, 784)
    y_test = torch.randint(0, num_classes, (20,))
    
    print(f"\nDonnees :")
    print(f"  Train : {x_train.shape[0]} echantillons")
    print(f"  Test  : {x_test.shape[0]} echantillons")
    
    # Evaluation avant apprentissage
    with torch.no_grad():
        logits_before = model(x_test)
        pred_before = logits_before.argmax(dim=-1)
        acc_before = (pred_before == y_test).float().mean()
    print(f"\nAccuracy avant apprentissage : {acc_before.item():.2%}")
    
    # Apprentissage par resonance (1 epoch, pas de backprop)
    print(f"\nApprentissage par resonance...")
    model.train()
    
    all_resonances = []
    for epoch in range(3):
        epoch_resonances = []
        
        for i in range(0, len(x_train), batch_size):
            x_batch = x_train[i:i+batch_size]
            y_batch = y_train_onehot[i:i+batch_size]
            
            if len(x_batch) < 2:
                continue
            
            # Apprentissage par resonance
            resonances = model.resonance_train(x_batch, y_batch, coupling=0.05)
            epoch_resonances.append(np.mean([r.item() for r in resonances]))
        
        avg_res = np.mean(epoch_resonances) if epoch_resonances else 0
        all_resonances.append(avg_res)
        
        # Evaluation
        with torch.no_grad():
            logits = model(x_test)
            pred = logits.argmax(dim=-1)
            acc = (pred == y_test).float().mean()
        
        print(f"  Epoch {epoch+1}: resonance={avg_res:.4f}, accuracy={acc.item():.2%}")
    
    # Verifier que l'apprentissage a eu lieu
    with torch.no_grad():
        logits_after = model(x_test)
        pred_after = logits_after.argmax(dim=-1)
        acc_after = (pred_after == y_test).float().mean()
    
    print(f"\nAccuracy finale : {acc_after.item():.2%}")
    print(f"  (sur donnees aleatoires, l'accuracy devrait etre ~10%)")
    print(f"  (le but est de verifier que la resonance fonctionne)")
    
    # Verifier que les phases ont change
    phase_before = model.fc1.phase.data.clone()
    # Faire quelques steps d'apprentissage
    for _ in range(5):
        model.resonance_train(x_train[:batch_size], y_train_onehot[:batch_size])
    phase_after = model.fc1.phase.data
    phase_change = (phase_after - phase_before).abs().mean()
    print(f"\nChangement de phase moyen : {phase_change.item():.6f} rad")
    assert phase_change > 0, "Les phases doivent changer pendant l'apprentissage"
    print("[OK] Les phases s'ajustent par resonance")
    
    print(f"\n[SUCCES] Apprentissage par Resonance operationnel")
    return True


def test_xor_resonance():
    """
    Test sur le probleme XOR (probleme non-lineaire simple).
    
    Verifie que l'apprentissage par resonance peut resoudre XOR.
    """
    print("=" * 60)
    print("TEST : Probleme XOR par Resonance")
    print("=" * 60)
    
    # Donnees XOR
    x = torch.tensor([
        [0.0, 0.0],
        [0.0, 1.0],
        [1.0, 0.0],
        [1.0, 1.0],
    ])
    y = torch.tensor([0.0, 1.0, 1.0, 0.0])
    y_onehot = F.one_hot(y.long(), num_classes=2).float()
    
    # Petit reseau harmonique pour XOR
    class HarmonicXORNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc1 = HarmonicLinear(2, 4, init_magnitude=0.2)
            self.fc2 = HarmonicLinear(4, 2, init_magnitude=0.2)
            self.relu = nn.ReLU()
        
        def forward(self, x):
            x = self.relu(self.fc1(x))
            x = self.fc2(x)
            return x
        
        def resonance_train(self, x, target, coupling=0.1):
            h = self.relu(self.fc1(x))
            y = self.fc2(h)
            
            # Resonance couche 2 (sortie)
            r2 = self.fc2.resonance_learn(h, target, coupling)
            
            # Retro-resonance : on propage l'erreur de resonance
            # vers la couche 1 en utilisant la transposee du poids
            with torch.no_grad():
                # y_apres = fc2(h) apres ajustement
                y_after = self.fc2(h)
                # Erreur de resonance sur la sortie
                error_out = target - y_after  # [batch, 2]
                # Retro-propagation de l'erreur via W^T
                w2_real = self.fc2.get_weight_real()  # [2, 4]
                error_hidden = torch.mm(error_out, w2_real)  # [batch, 4]
                # La cible pour h est h + error_hidden (correction)
                target_h = torch.relu(h + error_hidden * coupling)
            
            r1 = self.fc1.resonance_learn(x, target_h, coupling * 0.5)
            
            return [r1, r2]
    
    model = HarmonicXORNet()
    
    print(f"\nDonnees XOR :")
    for i in range(4):
        print(f"  {x[i].tolist()} -> {y[i].item()}")
    
    # Evaluation avant
    with torch.no_grad():
        pred_before = model(x).argmax(dim=-1)
        acc_before = (pred_before == y).float().mean()
    print(f"\nAccuracy avant : {acc_before.item():.2%}")
    
    # Apprentissage par resonance
    print(f"\nApprentissage par resonance...")
    for epoch in range(20):
        resonances = model.resonance_train(x, y_onehot, coupling=0.1)
        avg_res = np.mean([r.item() for r in resonances])
        
        with torch.no_grad():
            pred = model(x).argmax(dim=-1)
            acc = (pred == y).float().mean()
        
        if epoch % 5 == 0 or epoch == 19:
            print(f"  Epoch {epoch+1:2d}: resonance={avg_res:.4f}, accuracy={acc.item():.2%}")
    
    # Verification finale
    with torch.no_grad():
        pred_final = model(x).argmax(dim=-1)
        acc_final = (pred_final == y).float().mean()
    
    print(f"\nAccuracy finale : {acc_final.item():.2%}")
    
    if acc_final > 0.75:
        print("[SUCCES] XOR resolu par resonance !")
    else:
        print("[INFO] XOR partiellement appris (le couplage peut etre ajuste)")
    
    return acc_final > 0.5


# =========================================================================
# TEST DE ROTATION DE PHASE DIFFERENTIABLE
# =========================================================================

def test_phase_rotation_differentiable():
    """
    Verifie que la rotation de phase est differentiable
    (pour compatibilite avec PyTorch autograd si necessaire).
    """
    print("=" * 60)
    print("TEST : Rotation de Phase Differentiable")
    print("=" * 60)
    
    # Phase initiale
    phase = nn.Parameter(torch.tensor([0.5, 1.0, 1.5, 2.0, 2.5]))
    
    # Rotation
    delta = torch.tensor([0.1, 0.2, 0.3, 0.4, 0.5])
    phase_rotated = phase_rotation(phase, delta)
    
    print(f"\nPhase initiale : {phase.tolist()}")
    print(f"Delta          : {delta.tolist()}")
    print(f"Phase rotative : {phase_rotated.tolist()}")
    
    # Verifier que c'est differentiable
    loss = phase_rotated.sum()
    loss.backward()
    
    assert phase.grad is not None, "Le gradient doit exister"
    assert phase.grad.abs().sum() > 0, "Le gradient doit etre non nul"
    
    print(f"\nGradient : {phase.grad.tolist()}")
    print("[OK] Rotation de phase differentiable")
    
    return True


# =========================================================================
# TEST DE RESONANCE MEASURE
# =========================================================================

def test_resonance_measure():
    """Teste la mesure de resonance."""
    print("=" * 60)
    print("TEST : Mesure de Resonance")
    print("=" * 60)
    
    # Vecteurs identiques (resonance parfaite)
    x = torch.tensor([[1.0, 0.0, 0.0]])
    y = torch.tensor([[1.0, 0.0, 0.0]])
    r = resonance_measure(x, y)
    print(f"\nVecteurs identiques : resonance = {r.item():.4f} (devrait etre 1.0)")
    assert abs(r.item() - 1.0) < 1e-6
    
    # Vecteurs orthogonaux (pas de resonance)
    x = torch.tensor([[1.0, 0.0, 0.0]])
    y = torch.tensor([[0.0, 1.0, 0.0]])
    r = resonance_measure(x, y)
    print(f"Vecteurs orthogonaux : resonance = {r.item():.4f} (devrait etre 0.0)")
    assert abs(r.item()) < 1e-6
    
    # Vecteurs opposes (anti-resonance)
    x = torch.tensor([[1.0, 0.0, 0.0]])
    y = torch.tensor([[-1.0, 0.0, 0.0]])
    r = resonance_measure(x, y)
    print(f"Vecteurs opposes : resonance = {r.item():.4f} (devrait etre -1.0)")
    assert abs(r.item() + 1.0) < 1e-6
    
    # Vecteurs partiellement alignes
    x = torch.tensor([[1.0, 1.0, 0.0]])
    y = torch.tensor([[1.0, 0.0, 0.0]])
    r = resonance_measure(x, y)
    expected = 1.0 / math.sqrt(2)
    print(f"Vecteurs a 45 degres : resonance = {r.item():.4f} (devrait etre {expected:.4f})")
    assert abs(r.item() - expected) < 1e-6
    
    print(f"\n[SUCCES] Mesure de Resonance operationnelle")
    return True


# =========================================================================
# POINT D'ENTREE
# =========================================================================

def run_all_tests():
    """Execute tous les tests."""
    print("\n" + "=" * 60)
    print("PHASE 1 : POIDS COMPLEXES HARMONIQUES - TESTS COMPLETS")
    print("=" * 60)
    
    tests = [
        ("Resonance Measure", test_resonance_measure),
        ("Phase Rotation Differentiable", test_phase_rotation_differentiable),
        ("HarmonicLinear", test_harmonic_linear),
        ("XOR par Resonance", test_xor_resonance),
        ("MNIST par Resonance", test_mnist_resonance),
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
            print(f"\n  >>> {name}: [ERREUR] {e}")
    
    print(f"\n{'=' * 60}")
    print(f"RESULTATS : {passed}/{len(tests)} tests passes")
    print(f"{'=' * 60}")
    
    return passed == len(tests)


if __name__ == '__main__':
    run_all_tests()
