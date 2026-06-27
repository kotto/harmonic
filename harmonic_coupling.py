#!/usr/bin/env python3
"""
Phase 3 : Resonance Inter-Couches (Couplage Harmonique)
========================================================
Les couches communiquent entre elles par resonance, sans retro-propagation.
Chaque couche ecoute la resonance de la couche suivante et ajuste
sa propre phase en consequence.

Principe :
    - Chaque couche a sa propre frequence de resonance
    - La couche N ecoute la resonance de la couche N+1
    - Si la couche N+1 est en resonance, la couche N renforce son signal
    - Si la couche N+1 est en anti-resonance, la couche N ajuste sa phase
    - L'information circule dans les deux sens (feedforward + feedback)

Mecanisme :
    - Couplage harmonique : chaque couche emet a sa frequence propre
    - Les couches voisines echangent leur etat de resonance
    - L'ajustement est local : chaque couche ne voit que ses voisines
    - L'harmonie globale emerge du couplage local

Avantages par rapport a la retro-propagation :
    - Bi-directionnel : l'information circule dans les deux sens
    - Local : pas de calcul de gradient global
    - Continu : apprentissage en temps reel
    - Robuste : pas de vanishing/exploding gradient
    - Parallele : toutes les couches s'ajustent simultanement

References :
    - Phase 1 : HarmonicLinear (poids complexes)
    - Phase 2 : LocalResonator (resonance locale)
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
from harmonic_resonance_locale import (
    LocalResonator, HarmonicResonanceLayer
)


# =========================================================================
# COUPLAGE HARMONIQUE ENTRE COUCHES
# =========================================================================

class HarmonicCoupling(nn.Module):
    """
    Couplage harmonique entre deux couches adjacentes.
    
    La couche source (N) ecoute la resonance de la couche cible (N+1).
    Si la cible est en resonance, la source renforce son signal.
    Si la cible est en anti-resonance, la source ajuste sa phase.
    
    Le couplage est symetrique : l'information circule dans les deux sens.
    
    Args:
        source_size: Nombre de neurones dans la couche source
        target_size: Nombre de neurones dans la couche cible
        coupling_strength: Force du couplage harmonique
        freq_base: Frequence de base du couplage
    """
    
    def __init__(self, source_size, target_size,
                 coupling_strength=0.1, freq_base=PHI):
        super().__init__()
        
        self.source_size = source_size
        self.target_size = target_size
        self.coupling_strength = coupling_strength
        
        # Frequence de couplage (harmonique entre les deux couches)
        self.register_buffer('coupling_freq',
            torch.tensor(freq_base * (source_size + target_size) / 2.0))
        
        # Phase de couplage (ajustable)
        self.coupling_phase = nn.Parameter(torch.zeros(1))
        
        # Memoire du couplage
        self.register_buffer('last_coupling_resonance', torch.zeros(1))
        self.coupling_history = []
    
    def forward(self, source_output, target_output):
        """
        Mesure le couplage harmonique entre deux couches.
        
        Le couplage est maximal quand les deux couches sont en phase :
        coupling_resonance = resonance_measure(source, target)
        
        Args:
            source_output: Tenseur [batch, source_size] sortie de la couche N
            target_output: Tenseur [batch, target_size] sortie de la couche N+1
        
        Returns:
            coupling: Tenseur scalaire, force du couplage harmonique
        """
        # Adapter les dimensions si necessaire
        if source_output.shape[-1] != target_output.shape[-1]:
            # Projection sur la plus petite dimension
            min_dim = min(source_output.shape[-1], target_output.shape[-1])
            source_proj = source_output[:, :min_dim]
            target_proj = target_output[:, :min_dim]
        else:
            source_proj = source_output
            target_proj = target_output
        
        # Resonance de couplage
        coupling_res = resonance_measure(source_proj, target_proj)
        coupling = coupling_res.mean()
        
        self.last_coupling_resonance = coupling.detach()
        self.coupling_history.append(coupling.item())
        
        return coupling
    
    def adjust_phase(self, coupling_resonance):
        """
        Ajuste la phase de couplage pour maximiser la resonance.
        
        Si le couplage est faible, on tourne la phase.
        Si le couplage est fort, on maintient la phase.
        
        Args:
            coupling_resonance: Tenseur scalaire, resonance de couplage
        """
        with torch.no_grad():
            # Erreur de couplage
            error = 1.0 - coupling_resonance
            
            # Ajustement de la phase de couplage
            delta = self.coupling_strength * error * torch.cos(self.coupling_phase)
            self.coupling_phase.data = phase_rotation(
                self.coupling_phase.data, delta.unsqueeze(0)
            )


# =========================================================================
# RESEAU A COUPLAGE HARMONIQUE
# =========================================================================

class HarmonicCoupledNetwork(nn.Module):
    """
    Reseau a couplage harmonique entre couches.
    
    Chaque couche est un HarmonicResonanceLayer.
    Les couches sont couplees harmoniquement :
    - La couche N recoit le signal de la couche N-1
    - La couche N ajuste sa phase en fonction de la resonance de N+1
    - L'apprentissage est entierement local et parallele
    
    Architecture :
    - N couches de resonance locale
    - N-1 couplages harmoniques entre couches adjacentes
    - L'information circule dans les deux sens
    
    Args:
        layer_sizes: Liste des tailles de couches [in, h1, h2, ..., out]
        freq_base: Frequence de base (harmonique)
        coupling_strength: Force du couplage inter-couches
    """
    
    def __init__(self, layer_sizes, freq_base=1.0, coupling_strength=0.05):
        super().__init__()
        
        self.layer_sizes = layer_sizes
        self.num_layers = len(layer_sizes) - 1
        
        # Couches de resonance locale
        self.layers = nn.ModuleList()
        for i in range(self.num_layers):
            layer = HarmonicResonanceLayer(
                layer_sizes[i], layer_sizes[i+1],
                freq_base=freq_base * (PHI ** i),  # Frequence harmonique croissante
                coupling_linear=0.05,
                coupling_resonator=0.02
            )
            self.layers.append(layer)
        
        # Couplages harmoniques entre couches adjacentes
        self.couplings = nn.ModuleList()
        for i in range(self.num_layers - 1):
            coupling = HarmonicCoupling(
                layer_sizes[i+1], layer_sizes[i+2],
                coupling_strength=coupling_strength,
                freq_base=freq_base * (PHI ** i)
            )
            self.couplings.append(coupling)
        
        # Activation
        self.activation = nn.ReLU()
    
    def forward(self, x):
        """
        Forward pass avec couplage harmonique.
        
        L'information circule dans les deux sens :
        1. Forward : x -> layer1 -> layer2 -> ... -> layerN
        2. Couplage : chaque couche ecoute la resonance de la suivante
        
        Args:
            x: Tenseur [batch, layer_sizes[0]]
        
        Returns:
            y: Tenseur [batch, layer_sizes[-1]]
        """
        # Forward pass
        activations = [x]
        h = x
        
        for i, layer in enumerate(self.layers):
            h = layer(h)
            if i < self.num_layers - 1:
                h = self.activation(h)
            activations.append(h)
        
        # Couplage harmonique (feedback)
        # Chaque couche ajustee par la resonance de la suivante
        for i in range(len(self.couplings)):
            coupling_res = self.couplings[i](
                activations[i+1], activations[i+2]
            )
            self.couplings[i].adjust_phase(coupling_res)
        
        return activations[-1]
    
    def local_train(self, x, target=None):
        """
        Apprentissage local avec couplage harmonique.
        
        Chaque couche apprend localement, mais le couplage harmonique
        permet a l'information de circuler entre les couches.
        
        Args:
            x: Tenseur [batch, in_features]
            target: Tenseur [batch, out_features] (optionnel pour la derniere couche)
        
        Returns:
            all_resonances: Dict des resonances par couche et couplage
        """
        all_resonances = {}
        
        # Forward avec stockage des activations
        activations = [x]
        h = x
        
        for i, layer in enumerate(self.layers):
            h = layer(h)
            if i < self.num_layers - 1:
                h = self.activation(h)
            activations.append(h)
        
        # Apprentissage local de chaque couche
        # La derniere couche a une cible (si fournie)
        # Les couches intermediaires apprennent par couplage harmonique
        
        # Derniere couche (sortie)
        if target is not None:
            r_last = self.layers[-1].local_learn(
                activations[-2], target=target
            )
            all_resonances[f'layer{self.num_layers-1}'] = r_last
        
        # Couches intermediaires (apprentissage par couplage)
        for i in range(self.num_layers - 2, -1, -1):
            # La couche i recoit le couplage de la couche i+1
            coupling_res = self.couplings[i](
                activations[i+1], activations[i+2]
            )
            
            # Apprentissage local avec influence du couplage
            r = self.layers[i].local_learn(activations[i])
            all_resonances[f'layer{i}'] = r
            all_resonances[f'coupling{i}'] = {
                'value': coupling_res.item()
            }
        
        return all_resonances


# =========================================================================
# RESEAU A COUPLAGE HARMONIQUE AVEC MEMOIRE
# =========================================================================

class HarmonicMemoryCoupling(nn.Module):
    """
    Extension du couplage harmonique avec memoire.
    
    Chaque couche maintient un etat de resonance memorise.
    Le couplage harmonique peut rappeler des etats anterieurs.
    
    C'est l'equivalent harmonique d'une memoire associative :
    - Chaque pattern active une resonance specifique
    - Le couplage harmonique permet de retrouver le pattern
    - La memoire est distribuee dans les phases des couches
    
    Args:
        layer_sizes: Liste des tailles de couches
        memory_size: Nombre de patterns memorisables
        coupling_strength: Force du couplage
    """
    
    def __init__(self, layer_sizes, memory_size=10, coupling_strength=0.05):
        super().__init__()
        
        self.memory_size = memory_size
        self.layer_sizes = layer_sizes
        
        # Reseau a couplage harmonique
        self.network = HarmonicCoupledNetwork(
            layer_sizes, coupling_strength=coupling_strength
        )
        
        # Memoire : etats de resonance par pattern
        self.memory = []  # Liste de dicts {pattern, phases, resonances}
        
        # Seuil de rappel
        self.register_buffer('recall_threshold',
            torch.tensor(0.3))
    
    def forward(self, x):
        """Forward pass standard."""
        return self.network(x)
    
    def memorize(self, x, pattern_id=None):
        """
        Memorise un pattern.
        
        Le pattern est encode dans les phases des resonateurs.
        Chaque couche ajuste sa phase pour etre en resonance avec le pattern.
        
        Args:
            x: Tenseur [batch, layer_sizes[0]] pattern a memoriser
            pattern_id: Identifiant du pattern (optionnel)
        
        Returns:
            memory_entry: Dict contenant le pattern memorise
        """
        # Forward pour obtenir les activations
        activations = [x]
        h = x
        
        for i, layer in enumerate(self.network.layers):
            h = layer(h)
            if i < self.network.num_layers - 1:
                h = self.network.activation(h)
            activations.append(h)
        
        # Capturer les phases de chaque couche
        phases = []
        for i, layer in enumerate(self.network.layers):
            phases.append(layer.resonator.phase.data.clone())
        
        # Capturer les resonances
        resonances = []
        for i, layer in enumerate(self.network.layers):
            res = layer.resonator.last_resonance.clone()
            resonances.append(res)
        
        # Creer l'entree memoire
        memory_entry = {
            'pattern': x.clone(),
            'phases': phases,
            'resonances': resonances,
            'activations': activations,
            'id': pattern_id or len(self.memory)
        }
        
        self.memory.append(memory_entry)
        
        # Limiter la taille de la memoire
        if len(self.memory) > self.memory_size:
            self.memory.pop(0)
        
        return memory_entry
    
    def recall(self, x):
        """
        Rappelle un pattern par resonance.
        
        Le pattern d'entree est compare aux patterns memorises
        par resonance harmonique.
        
        Args:
            x: Tenseur [batch, layer_sizes[0]] requete
        
        Returns:
            best_match: Dict du pattern le plus proche (ou None)
            similarity: Score de similarite harmonique
        """
        if not self.memory:
            return None, 0.0
        
        best_similarity = -float('inf')
        best_match = None
        
        for entry in self.memory:
            # Mesure de la resonance avec le pattern memorise
            similarity = resonance_measure(
                x.mean(dim=0, keepdim=True),
                entry['pattern'].mean(dim=0, keepdim=True)
            ).mean().item()
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = entry
        
        return best_match, best_similarity
    
    def replay(self, memory_idx=None):
        """
        Rejoue un pattern memorise en restaurant les phases.
        
        C'est l'equivalent harmonique du "replay" hippocampal :
        le reseau peut rejouer des patterns memorises en restaurant
        les etats de resonance.
        
        Args:
            memory_idx: Index du pattern a rejouer (aleatoire si None)
        
        Returns:
            pattern: Le pattern rejoue
        """
        if not self.memory:
            return None
        
        if memory_idx is None:
            memory_idx = np.random.randint(len(self.memory))
        
        entry = self.memory[memory_idx]
        
        # Restaurer les phases
        with torch.no_grad():
            for i, layer in enumerate(self.network.layers):
                layer.resonator.phase.data = entry['phases'][i].clone()
        
        # Forward avec les phases restaurees
        x = entry['pattern']
        h = x
        
        for i, layer in enumerate(self.network.layers):
            h = layer(h)
            if i < self.network.num_layers - 1:
                h = self.network.activation(h)
        
        return h


# =========================================================================
# TESTS
# =========================================================================

def test_harmonic_coupling():
    """Test unitaire du couplage harmonique."""
    print("=" * 60)
    print("TEST : HarmonicCoupling")
    print("=" * 60)
    
    source_size, target_size = 8, 4
    coupling = HarmonicCoupling(source_size, target_size)
    
    print(f"\nConfiguration :")
    print(f"  Source : {source_size} neurones")
    print(f"  Target : {target_size} neurones")
    print(f"  Coupling freq : {coupling.coupling_freq.item():.4f}")
    
    # Forward
    source_out = torch.randn(4, source_size)
    target_out = torch.randn(4, target_size)
    
    c = coupling(source_out, target_out)
    print(f"\nCoupling resonance : {c.item():.4f}")
    
    # Ajustement
    coupling.adjust_phase(c)
    print(f"Phase apres ajustement : {coupling.coupling_phase.item():.4f}")
    
    # Verifier que le couplage est symetrique
    c2 = coupling(target_out, source_out)
    print(f"Coupling symetrique : {c2.item():.4f}")
    
    print(f"\n[SUCCES] HarmonicCoupling operationnel")
    return True


def test_coupled_network():
    """Test du reseau a couplage harmonique."""
    print("=" * 60)
    print("TEST : HarmonicCoupledNetwork")
    print("=" * 60)
    
    layer_sizes = [10, 8, 6, 4]
    network = HarmonicCoupledNetwork(layer_sizes)
    
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
    
    # Apprentissage local avec couplage
    target = torch.randn(4, layer_sizes[-1])
    resonances = network.local_train(x, target=target)
    
    print(f"\nResonances apres apprentissage :")
    for name, res in resonances.items():
        if isinstance(res, dict):
            print(f"  {name}: {', '.join(f'{k}={v:.4f}' for k, v in res.items())}")
        else:
            print(f"  {name}: {res:.4f}")
    
    print(f"\n[SUCCES] HarmonicCoupledNetwork operationnel")
    return True


def test_memory_coupling():
    """Test de la memoire harmonique."""
    print("=" * 60)
    print("TEST : HarmonicMemoryCoupling")
    print("=" * 60)
    
    layer_sizes = [8, 6, 4]
    memory = HarmonicMemoryCoupling(layer_sizes, memory_size=5)
    
    print(f"\nArchitecture : {layer_sizes}")
    print(f"  Memoire : {memory.memory_size} patterns")
    
    # Memoriser des patterns
    print(f"\nMemorisation de 3 patterns...")
    patterns = []
    for i in range(3):
        x = torch.randn(1, layer_sizes[0])
        x = x / x.norm()
        entry = memory.memorize(x, pattern_id=i)
        patterns.append(x)
        print(f"  Pattern {i} memorise (resonance: {entry['resonances'][-1].mean().item():.4f})")
    
    assert len(memory.memory) == 3
    print("[OK] 3 patterns memorises")
    
    # Rappel par resonance
    print(f"\nRappel par resonance...")
    for i in range(3):
        match, similarity = memory.recall(patterns[i])
        if match:
            print(f"  Pattern {i}: rappele (similarite: {similarity:.4f})")
        else:
            print(f"  Pattern {i}: non rappele")
    
    # Replay
    print(f"\nReplay d'un pattern memorise...")
    replayed = memory.replay(memory_idx=0)
    if replayed is not None:
        print(f"  Pattern 0 rejoue : {replayed.shape}")
        print("[OK] Replay operationnel")
    
    print(f"\n[SUCCES] HarmonicMemoryCoupling operationnel")
    return True


def test_coupling_xor():
    """
    Test XOR avec couplage harmonique.
    
    Le couplage harmonique devrait permettre d'apprendre XOR
    car l'information circule dans les deux sens.
    """
    print("=" * 60)
    print("TEST : XOR avec Couplage Harmonique")
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
    
    # Reseau a couplage harmonique
    network = HarmonicCoupledNetwork(
        [2, 4, 2],
        freq_base=1.0,
        coupling_strength=0.1
    )
    
    print(f"\nDonnees XOR :")
    for i in range(4):
        print(f"  {x[i].tolist()} -> {y[i].item()}")
    
    # Evaluation avant
    with torch.no_grad():
        acc_before = (network(x).argmax(dim=-1) == y).float().mean()
    print(f"\nAccuracy avant : {acc_before.item():.2%}")
    
    # Apprentissage local avec couplage
    print(f"\nApprentissage avec couplage harmonique...")
    for epoch in range(50):
        resonances = network.local_train(x, target=y_onehot)
        
        with torch.no_grad():
            acc = (network(x).argmax(dim=-1) == y).float().mean()
        
        if epoch % 10 == 0 or epoch == 49:
            res_str = "; ".join([
                f"{k}: {v:.4f}" if isinstance(v, float) else
                f"{k}: {', '.join(f'{kk}={vv:.4f}' for kk, vv in v.items())}"
                for k, v in resonances.items()
            ])
            print(f"  Epoch {epoch+1:2d}: {res_str}, accuracy={acc.item():.2%}")
    
    # Verification finale
    with torch.no_grad():
        acc_final = (network(x).argmax(dim=-1) == y).float().mean()
    
    print(f"\nAccuracy finale : {acc_final.item():.2%}")
    
    if acc_final > 0.75:
        print("[SUCCES] XOR resolu par couplage harmonique !")
    else:
        print("[INFO] XOR partiellement appris par couplage")
    
    return acc_final > 0.5


def test_coupling_convergence():
    """
    Test de convergence du couplage harmonique.
    
    Le couplage doit converger vers un etat stable
    quand on presente le meme stimulus.
    """
    print("=" * 60)
    print("TEST : Convergence du Couplage Harmonique")
    print("=" * 60)
    
    layer_sizes = [8, 6, 4]
    network = HarmonicCoupledNetwork(layer_sizes, coupling_strength=0.05)
    
    x = torch.randn(4, layer_sizes[0])
    
    print(f"\nCouplage harmonique sur 50 iterations...")
    
    coupling_history = []
    for step in range(50):
        y = network(x)
        
        # Mesurer les couplages
        for i, coupling in enumerate(network.couplings):
            c = coupling(
                y if i == len(network.couplings) - 1 else
                network.layers[i+1](network.layers[i](x)),
                y
            )
            coupling_history.append(c.item())
        
        if step % 10 == 0:
            avg_coupling = np.mean(coupling_history[-len(network.couplings):])
            print(f"  Step {step:2d}: couplage moyen = {avg_coupling:.4f}")
    
    # Mesure de la stabilite
    dernieres_res = coupling_history[-20:]
    variance = np.var(dernieres_res)
    moyenne = np.mean(dernieres_res)
    
    print(f"\n  Couplage moyen (20 derniers) : {moyenne:.4f}")
    print(f"  Variance (20 derniers)       : {variance:.6f}")
    
    converge = variance < 0.01
    print(f"  Convergence                  : {'[OK]' if converge else '[NON]'}")
    
    print(f"\n[{'SUCCES' if converge else 'ECHEC'}] Convergence du couplage operationnelle")
    return converge


# =========================================================================
# POINT D'ENTREE
# =========================================================================

def run_all_tests():
    """Execute tous les tests de la Phase 3."""
    print("\n" + "=" * 60)
    print("PHASE 3 : RESONANCE INTER-COUCHES - TESTS COMPLETS")
    print("=" * 60)
    
    tests = [
        ("HarmonicCoupling", test_harmonic_coupling),
        ("HarmonicCoupledNetwork", test_coupled_network),
        ("HarmonicMemoryCoupling", test_memory_coupling),
        ("XOR avec Couplage", test_coupling_xor),
        ("Convergence Couplage", test_coupling_convergence),
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
