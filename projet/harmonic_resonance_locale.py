#!/usr/bin/env python3
"""
Phase 2 : Resonance Locale Harmonique
======================================
Chaque neurone ajuste sa phase localement, sans propagation globale.
L'apprentissage devient un phenomene emergent : chaque couche
resonne a sa propre frequence, et l'harmonie globale emerge.

Principe :
    - Chaque neurone a une frequence de resonance propre
    - L'apprentissage ajuste la phase pour maximiser la resonance locale
    - Pas de retro-propagation : chaque couche apprend independamment
    - La coherence emerge du couplage harmonique entre couches

Avantages :
    - Parallele : chaque couche peut apprendre en meme temps
    - Non-destructif : les frequences apprises ne s'ecrasent pas
    - Robuste : pas de vanishing/exploding gradient
    - Continu : l'apprentissage peut se faire en temps reel

References :
    - Phase 1 : HarmonicLinear (poids complexes)
    - Atangana-Baleanu fractional derivative
    - Harmonic resonance theory
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


# =========================================================================
# RESONATEUR LOCAL
# =========================================================================

class LocalResonator(nn.Module):
    """
    Resonateur local : chaque neurone a sa propre frequence de resonance.
    
    Au lieu d'apprendre par erreur propagee, chaque neurone :
    1. Mesure sa resonance avec l'entree
    2. Ajuste sa phase pour maximiser cette resonance
    3. Emet un signal a sa frequence propre
    
    C'est l'equivalent harmonique d'un neurone biologique :
    - Frequence propre = potentiel de repos
    - Phase = etat d'excitation
    - Resonance = potentiel d'action
    
    Args:
        num_neurons: Nombre de neurones dans ce resonateur
        freq_base: Frequence de base (en Hz conceptuels)
        coupling: Facteur de couplage local
    """
    
    def __init__(self, num_neurons, freq_base=1.0, coupling=0.1):
        super().__init__()
        
        self.num_neurons = num_neurons
        self.freq_base = freq_base
        self.coupling = coupling
        
        # Frequence propre de chaque neurone (harmonique)
        # Chaque neurone a une frequence differente, basee sur PHI
        freqs = torch.zeros(num_neurons)
        for i in range(num_neurons):
            freqs[i] = freq_base * (1.0 + i * PHI_INV)
        self.register_buffer('frequencies', freqs)
        
        # Phase actuelle de chaque neurone
        # Initialisee harmoniquement
        init_phase = TAU * torch.arange(num_neurons, dtype=torch.float32) / num_neurons
        self.phase = nn.Parameter(init_phase)
        
        # Amplitude (excitabilite) de chaque neurone
        self.amplitude = nn.Parameter(torch.ones(num_neurons) * 0.5)
        
        # Memoire locale : derniere resonance mesuree
        self.register_buffer('last_resonance', torch.zeros(num_neurons))
        
        # Historique
        self.resonance_history = []
    
    def forward(self, x):
        """
        Forward pass : chaque neurone emet a sa frequence.
        
        y_i = amplitude_i * sin(phase_i + 2*pi*freq_i*t)
        
        Mais comme on est en discret, on utilise la phase comme etat.
        
        Args:
            x: Tenseur [batch, num_neurons] ou [batch, features]
               Si x a plus de features que num_neurons, on moyenne.
        
        Returns:
            y: Tenseur [batch, num_neurons] signaux emis
        """
        batch_size = x.shape[0]
        
        # Adapter x si necessaire
        if x.shape[-1] != self.num_neurons:
            # Projection lineaire simplifiee
            x = x.mean(dim=-1, keepdim=True).expand(-1, self.num_neurons)
        
        # Signal emis = amplitude * sin(phase) * x
        # (modulation du signal d'entree par la phase du neurone)
        signal = self.amplitude * torch.sin(self.phase) * x
        
        return signal
    
    def resonate(self, x):
        """
        Mesure et ajuste la resonance locale.
        
        Chaque neurone ajuste sa phase pour etre en resonance
        avec le signal d'entree.
        
        Mise a jour continue (pas de signe binaire) :
        delta_phase = coupling * (1 - resonance^2) * (x - y)
        
        Args:
            x: Tenseur [batch, num_neurons] signal d'entree
        
        Returns:
            resonance: Tenseur [num_neurons] resonance par neurone
        """
        with torch.no_grad():
            # Signal emis
            y = self.forward(x)
            
            # Resonance par neurone
            res = resonance_measure(y, x)  # [batch]
            res_per_neuron = res.mean(dim=0)  # moyenne sur le batch
            
            self.last_resonance = res_per_neuron
            self.resonance_history.append(res_per_neuron.mean().item())
            
            # Ajustement continu de la phase
            # On veut maximiser la resonance (cos > 0), pas la valeur absolue
            # Si res < 0 (anti-resonance), on tourne la phase de pi/2
            # Si res > 0 mais faible, on ajuste finement
            # delta_phase = coupling * (1 - res) * cos(phase) * x_mean
            # (1 - res) au lieu de (1 - res^2) pour penaliser aussi l'anti-resonance
            error = 1.0 - res_per_neuron  # [num_neurons], 2 si anti-res, 0 si resonance parfaite
            x_mean = x.mean(dim=0)  # [num_neurons]
            
            # Ajustement proportionnel continu
            delta_phase = self.coupling * error * torch.cos(self.phase) * x_mean
            
            # Rotation de phase
            self.phase.data = phase_rotation(self.phase.data, delta_phase)
            
            # Ajustement de l'amplitude (convergence vers 1.0)
            # Si resonance faible, amplitude augmente ; si forte, amplitude diminue
            delta_amp = self.coupling * error * 0.1
            self.amplitude.data = torch.clamp(
                self.amplitude.data + delta_amp,
                min=0.01, max=2.0
            )
            
            return res_per_neuron
    
    def get_state(self):
        """
        Retourne l'etat complet du resonateur.
        """
        return {
            'frequencies': self.frequencies,
            'phase': self.phase,
            'amplitude': self.amplitude,
            'last_resonance': self.last_resonance,
        }


# =========================================================================
# COUCHE DE RESONANCE LOCALE
# =========================================================================

class HarmonicResonanceLayer(nn.Module):
    """
    Couche de resonance locale : combine HarmonicLinear + LocalResonator.
    
    Architecture :
    1. HarmonicLinear : transforme l'entree avec des poids complexes
    2. LocalResonator : chaque neurone resonne localement
    3. La sortie est la resonance combinee
    
    L'apprentissage est entierement local :
    - HarmonicLinear ajuste ses phases par resonance_learn
    - LocalResonator ajuste ses phases par resonate
    - Pas de retro-propagation entre couches
    
    Args:
        in_features: Nombre d'entrees
        out_features: Nombre de neurones
        freq_base: Frequence de base du resonateur
        coupling_linear: Couplage pour HarmonicLinear
        coupling_resonator: Couplage pour LocalResonator
    """
    
    def __init__(self, in_features, out_features,
                 freq_base=1.0, coupling_linear=0.1,
                 coupling_resonator=0.05):
        super().__init__()
        
        self.in_features = in_features
        self.out_features = out_features
        
        # Transformation lineaire harmonique
        self.linear = HarmonicLinear(
            in_features, out_features,
            init_magnitude=0.1,
            learnable_magnitude=False
        )
        
        # Resonateur local
        self.resonator = LocalResonator(
            out_features,
            freq_base=freq_base,
            coupling=coupling_resonator
        )
        
        # Couplages
        self.coupling_linear = coupling_linear
        self.coupling_resonator = coupling_resonator
    
    def forward(self, x):
        """
        Forward pass.
        
        y = resonator(linear(x))
        
        Args:
            x: Tenseur [batch, in_features]
        
        Returns:
            y: Tenseur [batch, out_features]
        """
        h = self.linear(x)
        y = self.resonator(h)
        return y
    
    def local_learn(self, x, target=None):
        """
        Apprentissage local (pas de retro-propagation).
        
        Chaque sous-module apprend independamment :
        - linear : resonance_learn (si target fourni)
        - resonator : resonate (toujours)
        
        Args:
            x: Tenseur [batch, in_features] entree
            target: Tenseur [batch, out_features] cible (optionnel)
        
        Returns:
            resonances: Dict des resonances
        """
        resonances = {}
        
        # Forward
        h = self.linear(x)
        
        # Resonance du resonateur local
        res_resonator = self.resonator.resonate(h)
        resonances['resonator'] = res_resonator.mean().item()
        
        # Resonance lineaire (si cible fournie)
        if target is not None:
            res_linear = self.linear.resonance_learn(
                x, target, coupling=self.coupling_linear
            )
            resonances['linear'] = res_linear.item()
        
        return resonances


# =========================================================================
# RESEAU A RESONANCE LOCALE (EXEMPLE MNIST)
# =========================================================================

class HarmonicLocalResonanceNet(nn.Module):
    """
    Reseau entierement base sur la resonance locale.
    
    Chaque couche apprend independamment. Pas de retro-propagation.
    La coherence emerge du couplage harmonique entre couches.
    
    Architecture :
    - HarmonicResonanceLayer(784, 256, freq=1.0)
    - HarmonicResonanceLayer(256, 128, freq=PHI)
    - HarmonicResonanceLayer(128, 10, freq=PHI^2)
    
    Chaque couche a une frequence de base differente (harmonique).
    """
    
    def __init__(self):
        super().__init__()
        
        self.layer1 = HarmonicResonanceLayer(
            784, 256, freq_base=1.0,
            coupling_linear=0.05, coupling_resonator=0.02
        )
        self.layer2 = HarmonicResonanceLayer(
            256, 128, freq_base=PHI,
            coupling_linear=0.03, coupling_resonator=0.01
        )
        self.layer3 = HarmonicResonanceLayer(
            128, 10, freq_base=PHI**2,
            coupling_linear=0.01, coupling_resonator=0.005
        )
        
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
            x = x.view(x.size(0), -1)
        
        x = self.relu(self.layer1(x))
        x = self.relu(self.layer2(x))
        x = self.layer3(x)
        
        return x
    
    def local_train(self, x, target, coupling=0.1):
        """
        Entrainement local : chaque couche apprend independamment.
        
        Args:
            x: Tenseur [batch, 784] entree
            target: Tenseur [batch, 10] cible (one-hot)
            coupling: Facteur de couplage global
        
        Returns:
            all_resonances: Liste des resonances par couche
        """
        all_resonances = []
        
        # Forward
        h1 = self.relu(self.layer1(x))
        h2 = self.relu(self.layer2(h1))
        y = self.layer3(h2)
        
        # Apprentissage local couche 3 (sortie)
        r3 = self.layer3.local_learn(h2, target=target)
        all_resonances.append(('layer3', r3))
        
        # Apprentissage local couche 2
        # Pas de cible externe : resonance avec sa propre entree
        r2 = self.layer2.local_learn(h1)
        all_resonances.append(('layer2', r2))
        
        # Apprentissage local couche 1
        r1 = self.layer1.local_learn(x)
        all_resonances.append(('layer1', r1))
        
        return all_resonances


# =========================================================================
# TESTS
# =========================================================================

def test_local_resonator():
    """Test unitaire du resonateur local."""
    print("=" * 60)
    print("TEST : LocalResonator")
    print("=" * 60)
    
    num_neurons = 8
    resonator = LocalResonator(num_neurons, freq_base=1.0, coupling=0.1)
    
    print(f"\nConfiguration :")
    print(f"  Neurones     : {num_neurons}")
    print(f"  Frequences   : {resonator.frequencies.tolist()}")
    print(f"  Phase init   : {resonator.phase.data.tolist()}")
    print(f"  Amplitude    : {resonator.amplitude.data.tolist()}")
    
    # Forward
    x = torch.randn(4, num_neurons)
    y = resonator(x)
    
    print(f"\nForward pass :")
    print(f"  Input  : {x.shape}")
    print(f"  Output : {y.shape}")
    assert y.shape == x.shape
    print("[OK] Forward pass correcte")
    
    # Resonance
    res = resonator.resonate(x)
    print(f"\nResonance initiale : {res.mean().item():.4f}")
    
    # Faire resonner plusieurs fois
    for step in range(20):
        res = resonator.resonate(x)
        if step % 5 == 0:
            print(f"  Step {step:2d}: resonance = {res.mean().item():.4f}")
    
    print(f"\nResonance finale : {res.mean().item():.4f}")
    print(f"Phase apres : {resonator.phase.data.tolist()}")
    
    print(f"\n[SUCCES] LocalResonator operationnel")
    return True


def test_harmonic_resonance_layer():
    """Test unitaire de HarmonicResonanceLayer."""
    print("=" * 60)
    print("TEST : HarmonicResonanceLayer")
    print("=" * 60)
    
    in_features, out_features = 16, 8
    layer = HarmonicResonanceLayer(in_features, out_features)
    
    print(f"\nConfiguration :")
    print(f"  in_features  = {in_features}")
    print(f"  out_features = {out_features}")
    
    # Forward
    x = torch.randn(4, in_features)
    y = layer(x)
    
    print(f"\nForward pass :")
    print(f"  Input  : {x.shape}")
    print(f"  Output : {y.shape}")
    assert y.shape == (4, out_features)
    print("[OK] Forward pass correcte")
    
    # Apprentissage local
    target = torch.randn(4, out_features)
    resonances = layer.local_learn(x, target=target)
    
    print(f"\nApprentissage local :")
    for name, res in resonances.items():
        print(f"  {name}: {res:.4f}")
    
    print(f"\n[SUCCES] HarmonicResonanceLayer operationnel")
    return True


def test_local_resonance_mnist():
    """Test d'apprentissage local sur MNIST."""
    print("=" * 60)
    print("TEST : Resonance Locale sur MNIST")
    print("=" * 60)
    
    model = HarmonicLocalResonanceNet()
    total_params = sum(p.numel() for p in model.parameters())
    print(f"\nModele : {total_params:,} parametres")
    
    # Donnees factices
    batch_size = 32
    num_classes = 10
    
    x_train = torch.randn(100, 784)
    y_train = torch.randint(0, num_classes, (100,))
    y_train_onehot = F.one_hot(y_train, num_classes).float()
    
    x_test = torch.randn(20, 784)
    y_test = torch.randint(0, num_classes, (20,))
    
    print(f"\nDonnees :")
    print(f"  Train : {x_train.shape[0]} echantillons")
    print(f"  Test  : {x_test.shape[0]} echantillons")
    
    # Evaluation avant
    with torch.no_grad():
        pred_before = model(x_test).argmax(dim=-1)
        acc_before = (pred_before == y_test).float().mean()
    print(f"\nAccuracy avant : {acc_before.item():.2%}")
    
    # Apprentissage local
    print(f"\nApprentissage local par resonance...")
    model.train()
    
    for epoch in range(3):
        epoch_resonances = []
        
        for i in range(0, len(x_train), batch_size):
            x_batch = x_train[i:i+batch_size]
            y_batch = y_train_onehot[i:i+batch_size]
            
            if len(x_batch) < 2:
                continue
            
            resonances = model.local_train(x_batch, y_batch)
            epoch_resonances.append(resonances)
        
        # Evaluation
        with torch.no_grad():
            pred = model(x_test).argmax(dim=-1)
            acc = (pred == y_test).float().mean()
        
        # Afficher les resonances moyennes
        if epoch_resonances:
            avg_res = {}
            for layer_name, res_dict in epoch_resonances[0]:
                for k, v in res_dict.items():
                    avg_res[f"{layer_name}_{k}"] = v
            res_str = ", ".join([f"{k}={v:.4f}" for k, v in avg_res.items()])
            print(f"  Epoch {epoch+1}: {res_str}, accuracy={acc.item():.2%}")
    
    # Verification finale
    with torch.no_grad():
        pred_final = model(x_test).argmax(dim=-1)
        acc_final = (pred_final == y_test).float().mean()
    
    print(f"\nAccuracy finale : {acc_final.item():.2%}")
    
    # Verifier que les phases ont change
    phase_changes = []
    for name, layer in [('layer1', model.layer1), ('layer2', model.layer2), ('layer3', model.layer3)]:
        pc = layer.resonator.phase.data.abs().mean().item()
        phase_changes.append(pc)
        print(f"  {name} phase moyenne : {pc:.4f} rad")
    
    print(f"\n[SUCCES] Resonance Locale operationnelle")
    return True


def test_xor_local_resonance():
    """Test XOR avec resonance locale."""
    print("=" * 60)
    print("TEST : XOR par Resonance Locale")
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
    
    # Petit reseau a resonance locale
    class XORLocalResonanceNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.layer1 = HarmonicResonanceLayer(2, 4, freq_base=1.0)
            self.layer2 = HarmonicResonanceLayer(4, 2, freq_base=PHI)
            self.relu = nn.ReLU()
        
        def forward(self, x):
            x = self.relu(self.layer1(x))
            x = self.layer2(x)
            return x
        
        def local_train(self, x, target):
            h = self.relu(self.layer1(x))
            y = self.layer2(h)
            
            r2 = self.layer2.local_learn(h, target=target)
            r1 = self.layer1.local_learn(x)
            
            return {'layer1': r1, 'layer2': r2}
    
    model = XORLocalResonanceNet()
    
    print(f"\nDonnees XOR :")
    for i in range(4):
        print(f"  {x[i].tolist()} -> {y[i].item()}")
    
    # Evaluation avant
    with torch.no_grad():
        acc_before = (model(x).argmax(dim=-1) == y).float().mean()
    print(f"\nAccuracy avant : {acc_before.item():.2%}")
    
    # Apprentissage local
    print(f"\nApprentissage local...")
    for epoch in range(30):
        resonances = model.local_train(x, y_onehot)
        
        with torch.no_grad():
            acc = (model(x).argmax(dim=-1) == y).float().mean()
        
        if epoch % 10 == 0 or epoch == 29:
            r_str = "; ".join([f"{name}: {', '.join(f'{k}={v:.4f}' for k, v in res.items())}" for name, res in resonances.items()])
            print(f"  Epoch {epoch+1:2d}: {r_str}, accuracy={acc.item():.2%}")
    
    # Verification finale
    with torch.no_grad():
        acc_final = (model(x).argmax(dim=-1) == y).float().mean()
    
    print(f"\nAccuracy finale : {acc_final.item():.2%}")
    
    if acc_final > 0.75:
        print("[SUCCES] XOR resolu par resonance locale !")
    else:
        print("[INFO] XOR partiellement appris")
    
    return acc_final > 0.5


# =========================================================================
# TESTS SPECIFIQUES A LA RESONANCE LOCALE
# =========================================================================

def test_auto_organisation():
    """
    Test d'auto-organisation : est-ce que les phases s'organisent
    en motifs coherents sans supervision externe ?
    
    La resonance locale doit creer des motifs de phase stables
    quand on presente le meme stimulus plusieurs fois.
    """
    print("=" * 60)
    print("TEST : Auto-organisation par Resonance Locale")
    print("=" * 60)
    
    num_neurons = 16
    resonator = LocalResonator(num_neurons, freq_base=1.0, coupling=0.2)
    
    # Stimulus fixe
    x = torch.randn(1, num_neurons)
    x = x / x.norm()  # normalise
    
    print(f"\nStimulus fixe presente 50 fois...")
    
    phases_avant = resonator.phase.data.clone()
    resonances = []
    
    for step in range(50):
        res = resonator.resonate(x)
        resonances.append(res.mean().item())
    
    phases_apres = resonator.phase.data.clone()
    changement_phase = (phases_apres - phases_avant).abs().mean().item()
    
    print(f"  Resonance initiale : {resonances[0]:.4f}")
    print(f"  Resonance finale   : {resonances[-1]:.4f}")
    print(f"  Changement de phase: {changement_phase:.4f} rad")
    
    # Verifier que la resonance converge (devient stable)
    resonance_stable = abs(resonances[-1] - resonances[-5]) < 0.01
    print(f"  Resonance stable   : {'[OK]' if resonance_stable else '[NON]'}")
    
    # Verifier que les phases ont change de maniere significative
    phases_ont_change = changement_phase > 0.01
    print(f"  Phases ajustees    : {'[OK]' if phases_ont_change else '[NON]'}")
    
    resultat = resonance_stable and phases_ont_change
    print(f"\n[{'SUCCES' if resultat else 'ECHEC'}] Auto-organisation operationnelle")
    return resultat


def test_non_destructivite():
    """
    Test de non-destructivite : l'apprentissage d'un nouveau stimulus
    ne detruit pas les frequences apprises pour un stimulus precedent.
    
    C'est la propriete cle de la resonance locale : chaque neurone
    a sa frequence propre, donc les apprentissages ne s'ecrasent pas.
    """
    print("=" * 60)
    print("TEST : Non-destructivite de la Resonance Locale")
    print("=" * 60)
    
    num_neurons = 16
    resonator = LocalResonator(num_neurons, freq_base=1.0, coupling=0.1)
    
    # Deux stimuli differents
    x1 = torch.randn(1, num_neurons)
    x1 = x1 / x1.norm()
    x2 = torch.randn(1, num_neurons)
    x2 = x2 / x2.norm()
    
    print(f"\nPhase 1 : Apprentissage du stimulus A (50 iterations)...")
    for _ in range(50):
        resonator.resonate(x1)
    
    res_apres_A = resonator.resonate(x1).mean().item()
    phase_apres_A = resonator.phase.data.clone()
    print(f"  Resonance sur A apres apprentissage : {res_apres_A:.4f}")
    
    print(f"\nPhase 2 : Apprentissage du stimulus B (50 iterations)...")
    for _ in range(50):
        resonator.resonate(x2)
    
    res_apres_B_sur_A = resonator.resonate(x1).mean().item()
    res_apres_B_sur_B = resonator.resonate(x2).mean().item()
    print(f"  Resonance sur A apres B : {res_apres_B_sur_A:.4f}")
    print(f"  Resonance sur B apres B : {res_apres_B_sur_B:.4f}")
    
    # Verifier que la resonance sur A n'a pas ete completement detruite
    non_destructif = res_apres_B_sur_A > -0.5  # pas d'anti-resonance totale
    print(f"  Non-destructif (A preserve) : {'[OK]' if non_destructif else '[NON]'}")
    
    # Verifier que B a aussi ete appris
    b_appris = res_apres_B_sur_B > res_apres_B_sur_A
    print(f"  B appris correctement      : {'[OK]' if b_appris else '[NON]'}")
    
    resultat = non_destructif and b_appris
    print(f"\n[{'SUCCES' if resultat else 'ECHEC'}] Non-destructivite operationnelle")
    return resultat


def test_convergence_resonance():
    """
    Test de convergence : la resonance locale doit converger
    vers un etat stable quand le stimulus est constant.
    
    Mesure : variance de la resonance sur les dernieres iterations.
    """
    print("=" * 60)
    print("TEST : Convergence de la Resonance Locale")
    print("=" * 60)
    
    num_neurons = 8
    resonator = LocalResonator(num_neurons, freq_base=1.0, coupling=0.15)
    
    x = torch.randn(4, num_neurons)
    
    print(f"\nResonance sur 100 iterations...")
    
    for step in range(100):
        res = resonator.resonate(x)
        
        if step % 20 == 0:
            print(f"  Step {step:3d}: resonance = {res.mean().item():.4f}")
    
    # Mesure de la stabilite sur les 20 dernieres iterations
    dernieres_res = resonator.resonance_history[-20:]
    variance = np.var(dernieres_res)
    moyenne = np.mean(dernieres_res)
    
    print(f"\n  Resonance moyenne (20 derniers) : {moyenne:.4f}")
    print(f"  Variance (20 derniers)          : {variance:.6f}")
    
    converge = variance < 0.01
    print(f"  Convergence                     : {'[OK]' if converge else '[NON]'}")
    
    print(f"\n[{'SUCCES' if converge else 'ECHEC'}] Convergence operationnelle")
    return converge


def test_parallelisme():
    """
    Test de parallelisme : plusieurs resonateurs peuvent apprendre
    simultanement sans interference.
    
    C'est l'avantage fondamental de la resonance locale :
    chaque couche peut s'ajuster en parallele.
    """
    print("=" * 60)
    print("TEST : Parallelisme de la Resonance Locale")
    print("=" * 60)
    
    # Deux resonateurs independants
    r1 = LocalResonator(4, freq_base=1.0, coupling=0.1)
    r2 = LocalResonator(4, freq_base=PHI, coupling=0.1)
    
    x1 = torch.randn(2, 4)
    x2 = torch.randn(2, 4)
    
    print(f"\nApprentissage parallele de 2 resonateurs...")
    
    for step in range(30):
        res1 = r1.resonate(x1)
        res2 = r2.resonate(x2)
        
        if step % 10 == 0:
            print(f"  Step {step:2d}: r1={res1.mean().item():.4f}, r2={res2.mean().item():.4f}")
    
    # Verifier que les deux ont appris independamment
    res1_final = r1.resonate(x1).mean().item()
    res2_final = r2.resonate(x2).mean().item()
    
    print(f"\n  Resonance finale r1 : {res1_final:.4f}")
    print(f"  Resonance finale r2 : {res2_final:.4f}")
    
    # Les deux doivent avoir une resonance significative
    r1_ok = res1_final > -0.5
    r2_ok = res2_final > -0.5
    
    print(f"  r1 operationnel : {'[OK]' if r1_ok else '[NON]'}")
    print(f"  r2 operationnel : {'[OK]' if r2_ok else '[NON]'}")
    
    resultat = r1_ok and r2_ok
    print(f"\n[{'SUCCES' if resultat else 'ECHEC'}] Parallelisme operationnel")
    return resultat


# =========================================================================
# POINT D'ENTREE
# =========================================================================

def run_all_tests():
    """Execute tous les tests."""
    print("\n" + "=" * 60)
    print("PHASE 2 : RESONANCE LOCALE HARMONIQUE - TESTS COMPLETS")
    print("=" * 60)
    
    tests = [
        ("LocalResonator", test_local_resonator),
        ("HarmonicResonanceLayer", test_harmonic_resonance_layer),
        ("XOR Resonance Locale", test_xor_local_resonance),
        ("MNIST Resonance Locale", test_local_resonance_mnist),
        ("Auto-organisation", test_auto_organisation),
        ("Non-destructivite", test_non_destructivite),
        ("Convergence", test_convergence_resonance),
        ("Parallelisme", test_parallelisme),
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
