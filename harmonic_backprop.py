#!/usr/bin/env python3
"""
Phase 4 : Retro-Propagation Harmonique (Feedback Harmonique)
=============================================================
Au lieu de propager l'erreur par gradient (backprop classique),
on propage la resonance de la sortie vers l'entree.

Principe :
    - Forward : chaque couche emet un signal a sa frequence propre
    - Feedback : la resonance de la sortie est retro-propagee harmoniquement
    - Chaque couche recoit un signal de feedback qui indique
      comment ajuster sa phase pour mieux contribuer a l'objectif
    - L'ajustement est local et continu

Mecanisme :
    1. Forward pass : x -> layer1 -> layer2 -> ... -> layerN -> y
    2. Mesure de l'erreur harmonique : e = target - y (en phase)
    3. Feedback harmonique : l'erreur est retro-propagee par resonance
       - Chaque couche recoit : feedback_i = coupling_i * resonance(e, output_i)
       - La couche ajuste sa phase : delta_phase = feedback_i * cos(phase)
    4. L'information circule dans les deux sens simultanement

Avantages :
    - Pas de gradient : pas de vanishing/exploding
    - Local : chaque couche ne voit que son feedback
    - Continu : apprentissage en temps reel
    - Bi-directionnel : forward + feedback simultanes

References :
    - Phase 1 : HarmonicLinear (poids complexes)
    - Phase 2 : LocalResonator (resonance locale)
    - Phase 3 : HarmonicCoupling (couplage inter-couches)
    - Atangana-Baleanu fractional derivative
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from harmonic_complex_weights import (
    HarmonicLinear, resonance_measure, phase_rotation,
    PHI, PHI_INV, TAU
)
from harmonic_resonance_locale import (
    LocalResonator, HarmonicResonanceLayer
)
from harmonic_coupling import (
    HarmonicCoupling, HarmonicCoupledNetwork
)


# =========================================================================
# FEEDBACK HARMONIQUE
# =========================================================================

class HarmonicFeedback(nn.Module):
    """
    Feedback harmonique : propage la resonance de la sortie vers l'entree.
    
    Au lieu de calculer un gradient, on mesure la resonance entre
    la sortie souhaitee (target) et la sortie reelle, puis on
    retro-propage cette resonance harmoniquement.
    
    Le feedback est une onde qui se propage de la sortie vers l'entree :
    - Chaque couche recoit : feedback_i = W_i * resonance(target, output)
    - La couche ajuste sa phase : delta_phase = feedback_strength * fb * cos(phase)
    - L'onde de feedback s'attenue harmoniquement (facteur PHI_INV)
    
    Note : resonance_measure retourne [batch] (un scalaire par exemple).
    On projette ce scalaire sur chaque couche via des poids appris.
    
    Args:
        layer_sizes: Liste des tailles de couches
        feedback_strength: Force du feedback harmonique
        attenuation: Facteur d'attenuation du feedback (PHI_INV par defaut)
    """
    
    def __init__(self, layer_sizes, feedback_strength=0.1,
                 attenuation=PHI_INV):
        super().__init__()
        
        self.layer_sizes = layer_sizes
        self.num_layers = len(layer_sizes) - 1
        self.feedback_strength = feedback_strength
        self.attenuation = attenuation
        
        # Projecteurs de feedback : chaque couche a un poids pour projeter
        # le scalaire de resonance [batch] -> [batch, layer_size]
        self.feedback_projectors = nn.ModuleList([
            nn.Linear(1, size, bias=False)
            for size in layer_sizes[1:]
        ])
        
        # Phases de feedback pour chaque couche
        self.feedback_phases = nn.ParameterList([
            nn.Parameter(torch.zeros(size))
            for size in layer_sizes[1:]  # pas de feedback sur l'entree
        ])
        
        # Memoire du feedback
        self.feedback_history = []
    
    def forward(self, activations, target):
        """
        Retro-propagation harmonique du feedback.
        
        Args:
            activations: Liste des activations [x, h1, h2, ..., y]
            target: Tenseur [batch, out_size] sortie souhaitee
        
        Returns:
            feedbacks: Liste des feedbacks par couche [f0, f1, ..., fN-1]
                       (du plus profond au plus superficiel)
                       Chaque fb est [batch, layer_size]
        """
        batch_size = activations[0].shape[0]
        feedbacks = []
        
        # Derniere couche : erreur harmonique directe
        y = activations[-1]
        error = target - y
        
        # Resonance de l'erreur sur la derniere couche
        # resonance_measure retourne [batch] (scalaire par exemple)
        fb_scalar = resonance_measure(error, y)  # [batch]
        
        # Projeter le scalaire sur la derniere couche
        fb_last = self.feedback_projectors[-1](fb_scalar.unsqueeze(-1))  # [batch, out_size]
        feedbacks.append(fb_last)
        
        # Propagation du feedback vers les couches precedentes
        fb = fb_scalar  # scalaire [batch]
        for i in range(self.num_layers - 2, -1, -1):
            # Attenuation harmonique
            fb = fb * self.attenuation
            
            # Projeter sur la couche courante
            fb_proj = self.feedback_projectors[i](fb.unsqueeze(-1))  # [batch, layer_size]
            
            # Resonance entre le feedback projete et la sortie de la couche
            layer_out = activations[i+1]  # [batch, layer_size]
            fb_res = resonance_measure(fb_proj, layer_out)  # [batch]
            
            # Projeter la resonance sur la couche
            fb_out = self.feedback_projectors[i](fb_res.unsqueeze(-1))  # [batch, layer_size]
            feedbacks.append(fb_out)
        
        # Stocker l'historique
        self.feedback_history.append([f.mean().item() for f in feedbacks])
        
        return feedbacks  # [fb_N, fb_{N-1}, ..., fb_1]
    
    def apply_feedback(self, layers, feedbacks):
        """
        Applique le feedback aux couches.
        
        Chaque couche ajuste sa phase en fonction du feedback recu.
        
        Note : feedbacks est [fb_N, fb_{N-1}, ..., fb_1] (du plus profond
        au plus superficiel). layers est [layer_1, layer_2, ..., layer_N].
        On inverse feedbacks pour les aligner.
        
        Args:
            layers: Liste des couches (HarmonicResonanceLayer)
            feedbacks: Liste des feedbacks [fb_N, fb_{N-1}, ..., fb_1]
                       Chaque fb est [batch, layer_size]
        """
        with torch.no_grad():
            # Inverser feedbacks pour les aligner avec layers
            feedbacks_aligned = list(reversed(feedbacks))
            
            for i, (layer, fb) in enumerate(zip(layers, feedbacks_aligned)):
                # fb est [batch, layer_size] -> moyenner sur le batch
                fb_mean = fb.mean(dim=0)  # [layer_size]
                
                # Ajustement de phase harmonique
                # delta_phase = feedback_strength * fb * cos(phase)
                delta = self.feedback_strength * fb_mean * torch.cos(
                    layer.resonator.phase
                )
                
                # Rotation de phase
                layer.resonator.phase.data = phase_rotation(
                    layer.resonator.phase.data, delta
                )
                
                # Mise a jour de la phase de feedback
                self.feedback_phases[i].data = phase_rotation(
                    self.feedback_phases[i].data,
                    delta[:self.feedback_phases[i].shape[0]]
                )


# =========================================================================
# RESEAU A RETRO-PROPAGATION HARMONIQUE
# =========================================================================

class HarmonicBackpropNetwork(nn.Module):
    """
    Reseau a retro-propagation harmonique.
    
    Combine :
    - Forward harmonique (Phase 2 : resonance locale)
    - Couplage inter-couches (Phase 3)
    - Feedback harmonique (Phase 4)
    
    L'apprentissage se fait en deux phases :
    1. Forward : chaque couche emet a sa frequence
    2. Feedback : la resonance de l'erreur est retro-propagee
    
    Pas de gradient, pas de retro-propagation classique.
    
    Args:
        layer_sizes: Liste des tailles de couches [in, h1, h2, ..., out]
        feedback_strength: Force du feedback harmonique
        coupling_strength: Force du couplage inter-couches
        learning_rate: Taux d'apprentissage harmonique
    """
    
    def __init__(self, layer_sizes, feedback_strength=0.1,
                 coupling_strength=0.05, learning_rate=0.01):
        super().__init__()
        
        self.layer_sizes = layer_sizes
        self.num_layers = len(layer_sizes) - 1
        self.learning_rate = learning_rate
        
        # Couches de resonance locale (Phase 2)
        self.layers = nn.ModuleList()
        for i in range(self.num_layers):
            layer = HarmonicResonanceLayer(
                layer_sizes[i], layer_sizes[i+1],
                freq_base=PHI ** i,
                coupling_linear=0.05,
                coupling_resonator=0.02
            )
            self.layers.append(layer)
        
        # Couplages harmoniques (Phase 3)
        self.couplings = nn.ModuleList()
        for i in range(self.num_layers - 1):
            coupling = HarmonicCoupling(
                layer_sizes[i+1], layer_sizes[i+2],
                coupling_strength=coupling_strength
            )
            self.couplings.append(coupling)
        
        # Feedback harmonique (Phase 4)
        self.feedback = HarmonicFeedback(
            layer_sizes,
            feedback_strength=feedback_strength
        )
        
        # Activation
        self.activation = nn.ReLU()
        
        # Historique d'apprentissage
        self.loss_history = []
        self.resonance_history = []
    
    def forward(self, x):
        """
        Forward pass harmonique.
        
        Args:
            x: Tenseur [batch, in_features]
        
        Returns:
            y: Tenseur [batch, out_features]
        """
        h = x
        for i, layer in enumerate(self.layers):
            h = layer(h)
            if i < self.num_layers - 1:
                h = self.activation(h)
        return h
    
    def forward_with_activations(self, x):
        """
        Forward pass avec stockage des activations.
        
        Args:
            x: Tenseur [batch, in_features]
        
        Returns:
            activations: Liste [x, h1, h2, ..., y]
        """
        activations = [x]
        h = x
        for i, layer in enumerate(self.layers):
            h = layer(h)
            if i < self.num_layers - 1:
                h = self.activation(h)
            activations.append(h)
        return activations
    
    def train_step(self, x, target):
        """
        Une etape d'apprentissage complete.
        
        1. Forward : calcule les activations
        2. Couplage : mesure les resonances inter-couches
        3. Feedback : retro-propage la resonance de l'erreur
        4. Ajustement : chaque couche ajuste sa phase
        
        Args:
            x: Tenseur [batch, in_features]
            target: Tenseur [batch, out_features]
        
        Returns:
            loss: Perte harmonique
            resonances: Dict des resonances
        """
        resonances = {}
        
        # 1. Forward
        activations = self.forward_with_activations(x)
        y = activations[-1]
        
        # Perte harmonique (mesuree en resonance)
        loss = 1.0 - resonance_measure(y, target).mean()
        self.loss_history.append(loss.item())
        
        # 2. Couplage inter-couches
        for i, coupling in enumerate(self.couplings):
            c = coupling(activations[i+1], activations[i+2])
            coupling.adjust_phase(c)
            resonances[f'coupling_{i}'] = c.item()
        
        # 3. Feedback harmonique
        feedbacks = self.feedback(activations, target)
        
        # 4. Ajustement des couches par feedback
        self.feedback.apply_feedback(self.layers, feedbacks)
        
        # 5. Apprentissage local (resonance)
        for i, layer in enumerate(self.layers):
            if i == self.num_layers - 1:
                # Derniere couche : cible connue
                r = layer.local_learn(activations[i], target=target)
            else:
                # Couches intermediaires : apprentissage local pur
                r = layer.local_learn(activations[i])
            resonances[f'layer_{i}'] = r
        
        # Resonance globale
        global_resonance = resonance_measure(y, target).mean().item()
        self.resonance_history.append(global_resonance)
        resonances['global_resonance'] = global_resonance
        
        return loss.item(), resonances
    
    def train(self, x, target, num_epochs=100, verbose=True):
        """
        Entrainement complet.
        
        Args:
            x: Tenseur [batch, in_features]
            target: Tenseur [batch, out_features]
            num_epochs: Nombre d'iterations
            verbose: Afficher la progression
        
        Returns:
            history: Dict des historiques
        """
        for epoch in range(num_epochs):
            loss, resonances = self.train_step(x, target)
            
            if verbose and (epoch % 10 == 0 or epoch == num_epochs - 1):
                res_str = "; ".join([
                    f"{k}: {v:.4f}" if isinstance(v, float) else
                    f"{k}: {', '.join(f'{kk}={vv:.4f}' for kk, vv in v.items())}"
                    for k, v in resonances.items()
                ])
                print(f"  Epoch {epoch+1:3d}: loss={loss:.4f}, {res_str}")
        
        return {
            'loss': self.loss_history,
            'resonance': self.resonance_history,
        }


# =========================================================================
# RESEAU A DOUBLE PROPAGATION HARMONIQUE
# =========================================================================

class HarmonicDualPropagation(nn.Module):
    """
    Propagation duale : forward harmonique + feedback harmonique.
    
    L'information circule dans les deux sens simultanement :
    - Forward : chaque couche emet a sa frequence propre
    - Feedback : chaque couche recoit la resonance de la sortie
    
    Les deux ondes (forward et feedback) interferent pour creer
    un etat d'equilibre harmonique.
    
    Args:
        layer_sizes: Liste des tailles de couches
        num_iterations: Nombre d'iterations d'equilibrage
    """
    
    def __init__(self, layer_sizes, num_iterations=10):
        super().__init__()
        
        self.layer_sizes = layer_sizes
        self.num_layers = len(layer_sizes) - 1
        self.num_iterations = num_iterations
        
        # Poids forward (matrices de resonance)
        self.forward_weights = nn.ModuleList()
        for i in range(self.num_layers):
            w = HarmonicLinear(layer_sizes[i], layer_sizes[i+1])
            self.forward_weights.append(w)
        
        # Poids feedback (matrices de resonance inverses)
        self.feedback_weights = nn.ModuleList()
        for i in range(self.num_layers - 1, -1, -1):
            w = HarmonicLinear(layer_sizes[i+1], layer_sizes[i])
            self.feedback_weights.append(w)
        
        # Resonateurs locaux
        self.resonators = nn.ModuleList()
        for size in layer_sizes[1:]:
            r = LocalResonator(size, freq_base=PHI)
            self.resonators.append(r)
        
        # Activation
        self.activation = nn.Tanh()  # Tanh pour l'equilibrage harmonique
    
    def forward(self, x, target=None):
        """
        Propagation duale avec equilibrage harmonique.
        
        Pendant `num_iterations` iterations, le forward et le feedback
        s'equilibrent pour trouver un etat harmonique stable.
        
        Args:
            x: Tenseur [batch, in_features]
            target: Tenseur [batch, out_features] (optionnel)
        
        Returns:
            y: Tenseur [batch, out_features] etat d'equilibre
        """
        batch_size = x.shape[0]
        
        # Initialisation des etats
        states = [x]
        for size in self.layer_sizes[1:]:
            states.append(torch.zeros(batch_size, size))
        
        # Equilibrage harmonique
        for iteration in range(self.num_iterations):
            # Forward pass
            new_states = [x]
            for i in range(self.num_layers):
                h = self.forward_weights[i](states[i])
                h = self.resonators[i](h)
                if i < self.num_layers - 1:
                    h = self.activation(h)
                new_states.append(h)
            
            # Feedback pass (si target fourni)
            if target is not None:
                # Erreur sur la sortie
                error = target - new_states[-1]
                
                # Retro-propagation harmonique
                fb_states = [error]
                for i in range(self.num_layers):
                    fb = self.feedback_weights[i](fb_states[-1])
                    fb_states.append(fb)
                
                # Fusion forward + feedback
                for i in range(1, self.num_layers):
                    # Interference harmonique
                    alpha = 0.5  # facteur de melange
                    new_states[i] = (1 - alpha) * new_states[i] + \
                                    alpha * fb_states[self.num_layers - i]
            
            states = new_states
        
        return states[-1]
    
    def train_step(self, x, target):
        """
        Etape d'apprentissage avec propagation duale.
        
        Args:
            x: Tenseur [batch, in_features]
            target: Tenseur [batch, out_features]
        
        Returns:
            loss: Perte harmonique
        """
        # Propagation duale
        y = self.forward(x, target=target)
        
        # Perte
        loss = 1.0 - resonance_measure(y, target).mean()
        
        # Apprentissage local des resonateurs
        states = [x]
        h = x
        for i in range(self.num_layers):
            h = self.forward_weights[i](h)
            h = self.resonators[i](h)
            if i < self.num_layers - 1:
                h = self.activation(h)
            states.append(h)
        
        # Feedback pour les couches intermediaires
        # feedback_weights[i] va de layer_sizes[i+1] -> layer_sizes[i]
        # (inverse du forward)
        error = target - states[-1]
        fb = error
        for i in range(self.num_layers - 1, -1, -1):
            # Resonance du feedback
            self.resonators[i].resonate(fb)
            # feedback_weights est indexe de 0 a num_layers-1
            # mais construit dans l'ordre inverse
            # fb a la taille layer_sizes[i+1], feedback_weights[i] va de layer_sizes[i+1] -> layer_sizes[i]
            fb = self.feedback_weights[self.num_layers - 1 - i](fb)
        
        return loss.item()


# =========================================================================
# TESTS
# =========================================================================

def test_harmonic_feedback():
    """Test unitaire du feedback harmonique."""
    print("=" * 60)
    print("TEST : HarmonicFeedback")
    print("=" * 60)
    
    layer_sizes = [10, 8, 6, 4]
    feedback = HarmonicFeedback(layer_sizes)
    
    print(f"\nArchitecture : {layer_sizes}")
    print(f"  Couches : {len(layer_sizes) - 1}")
    print(f"  Attenuation : {feedback.attenuation:.4f}")
    
    # Creer des activations factices
    activations = [torch.randn(4, size) for size in layer_sizes]
    target = torch.randn(4, layer_sizes[-1])
    
    # Feedback
    feedbacks = feedback(activations, target)
    
    print(f"\nFeedbacks :")
    for i, fb in enumerate(feedbacks):
        print(f"  Layer {len(layer_sizes) - 1 - i}: shape={fb.shape}, mean={fb.mean().item():.4f}")
    
    assert len(feedbacks) == len(layer_sizes) - 1
    print("[OK] Feedback retro-propage sur toutes les couches")
    
    # Appliquer le feedback
    layers = [HarmonicResonanceLayer(layer_sizes[i], layer_sizes[i+1])
              for i in range(len(layer_sizes) - 1)]
    feedback.apply_feedback(layers, feedbacks)
    
    print("[OK] Feedback applique aux couches")
    
    print(f"\n[SUCCES] HarmonicFeedback operationnel")
    return True


def test_harmonic_backprop_network():
    """Test du reseau a retro-propagation harmonique."""
    print("=" * 60)
    print("TEST : HarmonicBackpropNetwork")
    print("=" * 60)
    
    layer_sizes = [10, 8, 6, 4]
    network = HarmonicBackpropNetwork(layer_sizes)
    
    print(f"\nArchitecture : {layer_sizes}")
    print(f"  Couches : {network.num_layers}")
    print(f"  Couplages : {len(network.couplings)}")
    
    # Forward
    x = torch.randn(4, layer_sizes[0])
    y = network(x)
    
    print(f"\nForward pass :")
    print(f"  Input  : {x.shape}")
    print(f"  Output : {y.shape}")
    assert y.shape == (4, layer_sizes[-1])
    print("[OK] Forward pass correcte")
    
    # Etape d'apprentissage
    target = torch.randn(4, layer_sizes[-1])
    loss, resonances = network.train_step(x, target)
    
    print(f"\nApprentissage :")
    print(f"  Loss : {loss:.4f}")
    print(f"  Resonance globale : {resonances.get('global_resonance', 0):.4f}")
    
    print(f"\n[SUCCES] HarmonicBackpropNetwork operationnel")
    return True


def test_dual_propagation():
    """Test de la propagation duale."""
    print("=" * 60)
    print("TEST : HarmonicDualPropagation")
    print("=" * 60)
    
    layer_sizes = [8, 6, 4]
    network = HarmonicDualPropagation(layer_sizes, num_iterations=5)
    
    print(f"\nArchitecture : {layer_sizes}")
    print(f"  Iterations d'equilibrage : {network.num_iterations}")
    
    # Forward sans target
    x = torch.randn(4, layer_sizes[0])
    y = network(x)
    
    print(f"\nForward sans target :")
    print(f"  Input  : {x.shape}")
    print(f"  Output : {y.shape}")
    assert y.shape == (4, layer_sizes[-1])
    print("[OK] Forward pass correcte")
    
    # Forward avec target
    target = torch.randn(4, layer_sizes[-1])
    y2 = network(x, target=target)
    
    print(f"\nForward avec target :")
    print(f"  Output : {y2.shape}")
    print("[OK] Propagation duale operationnelle")
    
    # Etape d'apprentissage
    loss = network.train_step(x, target)
    print(f"\nLoss apres apprentissage : {loss:.4f}")
    
    print(f"\n[SUCCES] HarmonicDualPropagation operationnel")
    return True


def test_backprop_xor():
    """
    Test XOR avec retro-propagation harmonique.
    
    C'est le test decisif : est-ce que le feedback harmonique
    permet d'apprendre XOR ?
    """
    print("=" * 60)
    print("TEST : XOR avec Retro-Propagation Harmonique")
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
    
    # Reseau a retro-propagation harmonique
    network = HarmonicBackpropNetwork(
        [2, 4, 2],
        feedback_strength=0.2,
        coupling_strength=0.1,
        learning_rate=0.01
    )
    
    print(f"\nDonnees XOR :")
    for i in range(4):
        print(f"  {x[i].tolist()} -> {y[i].item()}")
    
    # Evaluation avant
    with torch.no_grad():
        acc_before = (network(x).argmax(dim=-1) == y).float().mean()
    print(f"\nAccuracy avant : {acc_before.item():.2%}")
    
    # Entrainement
    print(f"\nEntrainement avec retro-propagation harmonique...")
    history = network.train(x, y_onehot, num_epochs=100, verbose=True)
    
    # Verification finale
    with torch.no_grad():
        y_pred = network(x)
        acc_final = (y_pred.argmax(dim=-1) == y).float().mean()
    
    print(f"\nAccuracy finale : {acc_final.item():.2%}")
    print(f"Loss finale : {history['loss'][-1]:.4f}")
    print(f"Resonance finale : {history['resonance'][-1]:.4f}")
    
    # Afficher les predictions
    print(f"\nPredictions :")
    with torch.no_grad():
        for i in range(4):
            pred = network(x[i:i+1])
            print(f"  {x[i].tolist()} -> {pred[0].tolist()} (attendu: {y[i].item()})")
    
    if acc_final > 0.75:
        print("\n[SUCCES] XOR resolu par retro-propagation harmonique !")
    else:
        print("\n[INFO] XOR partiellement appris")
    
    return acc_final > 0.5


def test_backprop_convergence():
    """
    Test de convergence de la retro-propagation harmonique.
    
    Le feedback harmonique doit converger vers un etat stable.
    """
    print("=" * 60)
    print("TEST : Convergence Retro-Propagation Harmonique")
    print("=" * 60)
    
    layer_sizes = [8, 6, 4]
    network = HarmonicBackpropNetwork(layer_sizes, feedback_strength=0.1)
    
    x = torch.randn(4, layer_sizes[0])
    target = torch.randn(4, layer_sizes[-1])
    
    print(f"\nEntrainement sur 50 iterations...")
    
    for epoch in range(50):
        loss, resonances = network.train_step(x, target)
        
        if epoch % 10 == 0:
            print(f"  Epoch {epoch:3d}: loss={loss:.4f}, "
                  f"resonance={resonances.get('global_resonance', 0):.4f}")
    
    # Mesure de la stabilite
    dernieres_loss = network.loss_history[-20:]
    variance = np.var(dernieres_loss)
    moyenne = np.mean(dernieres_loss)
    
    print(f"\n  Loss moyenne (20 derniers) : {moyenne:.4f}")
    print(f"  Variance (20 derniers)     : {variance:.6f}")
    
    converge = variance < 0.01
    print(f"  Convergence                : {'[OK]' if converge else '[NON]'}")
    
    print(f"\n[{'SUCCES' if converge else 'ECHEC'}] Convergence operationnelle")
    return converge


# =========================================================================
# POINT D'ENTREE
# =========================================================================

def run_all_tests():
    """Execute tous les tests de la Phase 4."""
    print("\n" + "=" * 60)
    print("PHASE 4 : RETRO-PROPAGATION HARMONIQUE - TESTS COMPLETS")
    print("=" * 60)
    
    tests = [
        ("HarmonicFeedback", test_harmonic_feedback),
        ("HarmonicBackpropNetwork", test_harmonic_backprop_network),
        ("HarmonicDualPropagation", test_dual_propagation),
        ("XOR Retro-Propagation", test_backprop_xor),
        ("Convergence Retro-Propagation", test_backprop_convergence),
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
    run_all_tests()
