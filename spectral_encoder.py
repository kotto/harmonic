#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ENCODEUR SPECTRAL APPRIS — Autoencodeur Contraint Harmonique
=============================================================
Remplace la projection par correlation (naive) par un autoencodeur
qui APPREND a projeter les donnees sur les 10 harmoniques fondamentales.

Principe :
  1. Encoder : donnees (ex: 784-dim MNIST) → 10 amplitudes spectrales [a1..a10]
  2. Chaque a_k est l'amplitude de l'harmonique H_k
  3. Contrainte spectrale : a_k DOIT etre lie a H_k (pas arbitraire)
  4. Decoder : 10 amplitudes → reconstruction des donnees
  5. Perte = reconstruction + contrainte spectrale + orthogonalite

Contrainte spectrale :
  - Les amplitudes a_k doivent etre proportionnelles aux H_k attendus
  - La somme des a_k * H_k doit reconstruire le signal
  - G_{ij,j}=0 impose que norme(entree) ≈ norme(sortie)

Utilisation :
  python spectral_encoder.py
"""

import numpy as np
import time, gzip, struct, os, json

# ==============================================================================
# CONSTANTES FONDAMENTALES
# ==============================================================================
PHI = (1 + np.sqrt(5)) / 2
PI  = np.pi
E   = np.e
SQ2 = np.sqrt(2)
SQ3 = np.sqrt(3)
SQ5 = np.sqrt(5)

H_BASE = np.array([PHI, PI, E, SQ2, SQ3, SQ5, E/PI, PHI*SQ2, E*PHI, PI*SQ5])
H_NAMES = ['phi', 'pi', 'e', 'sqrt2', 'sqrt3', 'sqrt5', 'e/pi', 'phi*sqrt2', 'e*phi', 'pi*sqrt5']

# ==============================================================================
# ENCODEUR SPECTRAL APPRIS
# ==============================================================================

class SpectralEncoder:
    """
    Autoencodeur qui apprend a projeter des donnees sur le spectre harmonique.
    
    Architecture:
      Encodeur:  input_dim → 256 → 64 → 10 (spectre)
      Decodeur:  10 → 64 → 256 → input_dim (reconstruction)
    
    Contraintes:
      1. Reconstruction fidèle
      2. Chaque amplitude a_k alignée avec H_k
      3. Orthogonalité des composantes spectrales
      4. G_{ij,j}=0 : conservation de l'energie du signal
    """
    
    def __init__(self, input_dim: int, seed: int = 42):
        np.random.seed(seed)
        self.input_dim = input_dim
        self.K = 10  # 10 harmoniques
        
        # === Encodeur ===
        s1 = 1.0 / np.sqrt(input_dim)
        self.W_enc1 = np.random.randn(input_dim, 256) * s1
        self.b_enc1 = np.zeros(256)
        
        s2 = 1.0 / np.sqrt(256)
        self.W_enc2 = np.random.randn(256, 64) * s2
        self.b_enc2 = np.zeros(64)
        
        s3 = 1.0 / np.sqrt(64)
        self.W_enc3 = np.random.randn(64, self.K) * s3
        self.b_enc3 = np.zeros(self.K)
        
        # === Décodeur ===
        s4 = 1.0 / np.sqrt(self.K)
        self.W_dec1 = np.random.randn(self.K, 64) * s4
        self.b_dec1 = np.zeros(64)
        
        self.W_dec2 = np.random.randn(64, 256) * s2
        self.b_dec2 = np.zeros(256)
        
        self.W_dec3 = np.random.randn(256, input_dim) * s1
        self.b_dec3 = np.zeros(input_dim)
        
        # Caches pour backward
        self.cache = {}
        
        # Statistiques
        self.epoch = 0
        self.history = {'loss_recon': [], 'loss_spectral': [], 'loss_total': [],
                        'grad_norm': []}
        
        self.num_params = (
            input_dim * 256 + 256 +
            256 * 64 + 64 +
            64 * 10 + 10 +
            10 * 64 + 64 +
            64 * 256 + 256 +
            256 * input_dim + input_dim
        )
    
    def forward(self, X: np.ndarray) -> dict:
        """
        Passe avant complete.
        
        Args:
            X: donnees d'entree (batch, input_dim)
        
        Returns:
            dict avec :
              - 'spectrum': amplitudes spectrales [a1..a10] (batch, 10)
              - 'reconstruction': donnees reconstruites (batch, input_dim)
              - 'harmonic_projection': projection modulee [a_k * H_k]
        """
        # === Encodage ===
        z1 = X @ self.W_enc1 + self.b_enc1
        h1 = np.maximum(0, z1)  # ReLU
        
        z2 = h1 @ self.W_enc2 + self.b_enc2
        h2 = np.maximum(0, z2)  # ReLU
        
        z3 = h2 @ self.W_enc3 + self.b_enc3
        
        # Activation de sortie de l'encodeur : softplus (amplitudes positives)
        # Numeriquement stable: clip z3 et utiliser softplus stable
        z3_clipped = np.clip(z3, -20, 20)
        spectrum_raw = np.where(z3 > 20, z3, np.log1p(np.exp(z3_clipped)))  # softplus stable
        
        # Normalisation du spectre (G_{ij,j}=0 au niveau spectral)
        spec_sum = spectrum_raw.sum(axis=1, keepdims=True) + 1e-8
        spectrum = spectrum_raw / spec_sum
        
        # === Décodage ===
        d1 = spectrum @ self.W_dec1 + self.b_dec1
        dh1 = np.maximum(0, d1)
        
        d2 = dh1 @ self.W_dec2 + self.b_dec2
        dh2 = np.maximum(0, d2)
        
        d3 = dh2 @ self.W_dec3 + self.b_dec3
        
        # Sortie sigmoid (pour normaliser entre 0 et 1)
        reconstruction = 1.0 / (1.0 + np.exp(-d3))
        
        # Projection harmonique (spectre module par les H_k)
        harmonic_projection = spectrum * H_BASE[np.newaxis, :]
        
        # Cache pour backward
        self.cache = {
            'X': X,
            'z1': z1, 'h1': h1,
            'z2': z2, 'h2': h2,
            'z3': z3, 'spectrum_raw': spectrum_raw, 'spectrum': spectrum,
            'd1': d1, 'dh1': dh1,
            'd2': d2, 'dh2': dh2,
            'd3': d3, 'reconstruction': reconstruction,
        }
        
        return {
            'spectrum': spectrum,
            'reconstruction': reconstruction,
            'harmonic_projection': harmonic_projection,
        }
    
    def encode(self, X: np.ndarray) -> np.ndarray:
        """Encode des donnees en spectre harmonique (utilise en inference)."""
        z1 = X @ self.W_enc1 + self.b_enc1
        h1 = np.maximum(0, z1)
        z2 = h1 @ self.W_enc2 + self.b_enc2
        h2 = np.maximum(0, z2)
        z3 = h2 @ self.W_enc3 + self.b_enc3
        spectrum_raw = np.log(1.0 + np.exp(z3))
        spec_sum = spectrum_raw.sum(axis=1, keepdims=True) + 1e-8
        return spectrum_raw / spec_sum
    
    def compute_loss(self, X: np.ndarray, output: dict) -> dict:
        """
        Calcule les pertes multiples.
        
        1. Perte de reconstruction (MSE)
        2. Perte spectrale : les amplitudes doivent refleter H_k
        3. Perte d'orthogonalite : les composantes spectrales sont independantes
        4. Perte de conservation G_{ij,j}=0
        """
        batch_size = X.shape[0]
        spectrum = output['spectrum']
        recon = output['reconstruction']
        
        # 1. Reconstruction
        loss_recon = np.mean((recon - X) ** 2)
        
        # 2. Contrainte spectrale : a_k doit etre lie a H_k
        # On penalise si les amplitudes ne suivent pas la structure harmonique
        # H_k plus grand → amplitude plus grande (en moyenne sur le batch)
        mean_amps = spectrum.mean(axis=0)  # (10,)
        # Correlation entre amplitudes moyennes et H_k
        h_norm = H_BASE / H_BASE.sum()
        amp_norm = mean_amps / (mean_amps.sum() + 1e-8)
        loss_spectral = np.mean((amp_norm - h_norm) ** 2)
        
        # 3. Orthogonalite : les colonnes de W_dec1 doivent etre decorrelees
        # (chaque harmonique reconstruit une partie independante du signal)
        WtW = self.W_dec1.T @ self.W_dec1
        np.fill_diagonal(WtW, 0)
        loss_ortho = np.mean(WtW ** 2)
        
        # 4. Conservation G_{ij,j}=0 : norme entree ≈ norme sortie
        norm_in = np.mean(np.linalg.norm(X, axis=1))
        norm_out = np.mean(np.linalg.norm(recon, axis=1))
        loss_conservation = (norm_in - norm_out) ** 2
        
        # Perte totale
        loss_total = (
            loss_recon
            + 0.1 * loss_spectral   # contrainte spectrale (poids modere)
            + 0.01 * loss_ortho     # orthogonalite (poids faible)
            + 0.05 * loss_conservation  # conservation (poids modere)
        )
        
        return {
            'loss_recon': float(loss_recon),
            'loss_spectral': float(loss_spectral),
            'loss_ortho': float(loss_ortho),
            'loss_conservation': float(loss_conservation),
            'loss_total': float(loss_total),
        }
    
    def backward(self, X: np.ndarray, output: dict, learning_rate: float = 0.01):
        """
        Backpropagation de l'autoencodeur.
        Calcule les gradients et met a jour les poids.
        """
        batch_size = X.shape[0]
        c = self.cache
        
        # === Gradient de la reconstruction (MSE) ===
        grad_recon = 2 * (c['reconstruction'] - X) / batch_size  # (batch, input_dim)
        
        # === Gradient total = reconstruction + contraintes ===
        
        # --- Backward decodeur ---
        # d3 → sigmoid
        sig = c['reconstruction']
        grad_d3 = grad_recon * sig * (1.0 - sig)  # derivee sigmoid
        
        grad_W_dec3 = c['dh2'].T @ grad_d3
        grad_b_dec3 = grad_d3.sum(axis=0)
        grad_dh2 = grad_d3 @ self.W_dec3.T
        
        # dh2 → ReLU
        grad_d2 = grad_dh2 * (c['d2'] > 0)
        
        grad_W_dec2 = c['dh1'].T @ grad_d2
        grad_b_dec2 = grad_d2.sum(axis=0)
        grad_dh1 = grad_d2 @ self.W_dec2.T
        
        # dh1 → ReLU
        grad_d1 = grad_dh1 * (c['d1'] > 0)
        
        grad_W_dec1 = c['spectrum'].T @ grad_d1
        grad_b_dec1 = grad_d1.sum(axis=0)
        grad_spectrum = grad_d1 @ self.W_dec1.T  # (batch, 10)
        
        # --- Contrainte spectrale sur l'encodeur ---
        # La contrainte spectrale pousse les amplitudes vers la distribution H_k
        mean_amps = c['spectrum'].mean(axis=0)  # (10,)
        amp_norm = mean_amps / (mean_amps.sum() + 1e-8)
        h_norm = H_BASE / H_BASE.sum()
        
        grad_spectral_loss = 0.1 * 2 * (amp_norm - h_norm) / 10
        # Distribuer ce gradient sur le batch
        grad_spectrum += grad_spectral_loss[np.newaxis, :] / batch_size
        
        # --- Contrainte d'orthogonalite ---
        # WtW = W_dec1.T @ W_dec1, on veut hors-diagonale nulle
        WtW = self.W_dec1.T @ self.W_dec1
        np.fill_diagonal(WtW, 0)
        grad_W_dec1_ortho = self.W_dec1 @ WtW * 0.01 * 2
        
        # --- Contrainte de conservation ---
        norm_in = np.mean(np.linalg.norm(X, axis=1))
        norm_out = np.mean(np.linalg.norm(c['reconstruction'], axis=1))
        # Approximation : le gradient de conservation passe par grad_recon
        grad_conservation = 0.05 * 2 * (norm_out - norm_in) * (
            c['reconstruction'] / (norm_out * batch_size + 1e-8)
        )
        # Ajouter au gradient de reconstruction
        # Note: simplification, le gradient reel est plus complexe
        
        # --- Backward encodeur ---
        # spectrum = softmax(normalisation) de spectrum_raw
        # spectrum_raw = softplus(z3)
        spec = c['spectrum']  # (batch, 10)
        grad_spec_norm = grad_spectrum
        
        # Derivee de la normalisation (simplifiee, numeriquement stable)
        spec_sum_2 = c['spectrum_raw'].sum(axis=1, keepdims=True)
        grad_raw = np.zeros_like(c['spectrum_raw'])
        for i in range(batch_size):
            s = c['spectrum_raw'][i]
            s_sum = s.sum()
            if s_sum > 1e-12:
                J = (np.eye(10) * s_sum - np.outer(s, np.ones(10))) / (s_sum * s_sum)
                grad_raw[i] = grad_spec_norm[i] @ J.T
        
        # Derivee softplus : d/dx log(1+exp(x)) = sigmoid(x) = 1/(1+exp(-x))
        sigmoid_z3 = 1.0 / (1.0 + np.exp(-c['z3']))
        grad_z3 = grad_raw * sigmoid_z3
        
        grad_W_enc3 = c['h2'].T @ grad_z3
        grad_b_enc3 = grad_z3.sum(axis=0)
        grad_h2 = grad_z3 @ self.W_enc3.T
        
        # ReLU h2
        grad_z2 = grad_h2 * (c['z2'] > 0)
        
        grad_W_enc2 = c['h1'].T @ grad_z2
        grad_b_enc2 = grad_z2.sum(axis=0)
        grad_h1 = grad_z2 @ self.W_enc2.T
        
        # ReLU h1
        grad_z1 = grad_h1 * (c['z1'] > 0)
        
        grad_W_enc1 = X.T @ grad_z1
        grad_b_enc1 = grad_z1.sum(axis=0)
        
        # === Mise a jour des poids ===
        lr = learning_rate
        
        # Decodeur
        self.W_dec3 -= lr * grad_W_dec3
        self.b_dec3 -= lr * grad_b_dec3
        self.W_dec2 -= lr * grad_W_dec2
        self.b_dec2 -= lr * grad_b_dec2
        self.W_dec1 -= lr * (grad_W_dec1 + grad_W_dec1_ortho)
        self.b_dec1 -= lr * grad_b_dec1
        
        # Encodeur
        self.W_enc3 -= lr * grad_W_enc3
        self.b_enc3 -= lr * grad_b_enc3
        self.W_enc2 -= lr * grad_W_enc2
        self.b_enc2 -= lr * grad_b_enc2
        self.W_enc1 -= lr * grad_W_enc1
        self.b_enc1 -= lr * grad_b_enc1
        
        # Tracking
        total_grad_norm = (
            np.linalg.norm(grad_W_enc1) + np.linalg.norm(grad_W_enc2) +
            np.linalg.norm(grad_W_enc3) + np.linalg.norm(grad_W_dec3)
        )
        
        return {
            'grad_norm': float(total_grad_norm),
        }


# ==============================================================================
# CHARGEMENT MNIST
# ==============================================================================

def load_mnist(data_dir='.'):
    files = {
        'train_images': 'train-images-idx3-ubyte.gz',
        'train_labels': 'train-labels-idx1-ubyte.gz',
        'test_images': 't10k-images-idx3-ubyte.gz',
        'test_labels': 't10k-labels-idx1-ubyte.gz',
    }
    urls = {k: f'https://ossci-datasets.s3.amazonaws.com/mnist/{f}' for k, f in files.items()}
    data = {}
    for key, filename in files.items():
        path = os.path.join(data_dir, filename)
        if not os.path.exists(path):
            import urllib.request
            urllib.request.urlretrieve(urls[key], path)
        with gzip.open(path, 'rb') as f:
            if 'labels' in key:
                struct.unpack('>II', f.read(8))
                data[key] = np.frombuffer(f.read(), dtype=np.uint8)
            else:
                _, num, rows, cols = struct.unpack('>IIII', f.read(16))
                img = np.frombuffer(f.read(), dtype=np.uint8).reshape(num, rows * cols)
                data[key] = img.astype(np.float64) / 255.0
    return data['train_images'], data['train_labels'], data['test_images'], data['test_labels']


# ==============================================================================
# ENTRAINEMENT DE L'ENCODEUR SPECTRAL
# ==============================================================================

def train_spectral_encoder():
    print("=" * 70)
    print("  ENTRAINEMENT DE L'ENCODEUR SPECTRAL APPRIS")
    print("  Autoencodeur contraint : 784 -> 256 -> 64 -> 10 -> 64 -> 256 -> 784")
    print("=" * 70)
    
    # Chargement
    print("\n[1] Chargement MNIST...")
    X_train, y_train, X_test, y_test = load_mnist('.')
    n_train = 10000  # sous-ensemble pour rapidite
    X_tr = X_train[:n_train]
    X_te = X_test[:2000]
    print(f"  Train: {n_train} | Test: {X_te.shape[0]} | Dim: {X_tr.shape[1]}")
    
    # Initialisation
    print("\n[2] Initialisation de l'Encodeur Spectral...")
    encoder = SpectralEncoder(input_dim=784)
    print(f"  Parametres: {encoder.num_params:,}")
    print(f"  Architecture: 784 -> 256 -> 64 -> 10 -> 64 -> 256 -> 784")
    print(f"  Les 10 dimensions du goulot = {', '.join(H_NAMES)}")
    print(f"  Contraintes: reconstruction + spectrale + orthogonalite + G=0")
    
    # Entrainement
    EPOCHS = 20
    BATCH_SIZE = 128
    LR = 0.01
    n_batches = n_train // BATCH_SIZE
    
    print(f"\n[3] Entrainement ({EPOCHS} epochs)...")
    print(f"  {'='*60}")
    
    history = {'loss_recon': [], 'loss_spectral': [], 'loss_total': []}
    t0_total = time.time()
    
    for epoch in range(EPOCHS):
        t0 = time.time()
        perm = np.random.permutation(n_train)
        Xs = X_tr[perm]
        
        total_losses = {'recon': 0, 'spectral': 0, 'total': 0}
        
        for i in range(n_batches):
            s, e = i * BATCH_SIZE, (i + 1) * BATCH_SIZE
            Xb = Xs[s:e]
            
            # Forward
            output = encoder.forward(Xb)
            losses = encoder.compute_loss(Xb, output)
            
            # Backward
            info = encoder.backward(Xb, output, LR)
            
            for k in ['recon', 'spectral', 'total']:
                total_losses[k] += losses[f'loss_{k}']
        
        avg_loss_recon = total_losses['recon'] / n_batches
        avg_loss_spec = total_losses['spectral'] / n_batches
        avg_loss_total = total_losses['total'] / n_batches
        
        history['loss_recon'].append(float(avg_loss_recon))
        history['loss_spectral'].append(float(avg_loss_spec))
        history['loss_total'].append(float(avg_loss_total))
        
        epoch_time = time.time() - t0
        
        # Evaluation sur test
        test_output = encoder.forward(X_te)
        test_losses = encoder.compute_loss(X_te, test_output)
        
        # Analyse du spectre appris
        test_spectrum = test_output['spectrum']
        mean_spectrum = test_spectrum.mean(axis=0)
        
        print(f"  Ep {epoch+1:2d}/{EPOCHS} | "
              f"Recon: {avg_loss_recon:.4f} | "
              f"Spectral: {avg_loss_spec:.4f} | "
              f"Test Recon: {test_losses['loss_recon']:.4f} | "
              f"{epoch_time:.1f}s")
        
        encoder.epoch += 1
        LR *= 0.95
    
    total_time = time.time() - t0_total
    
    # === Analyse du spectre appris ===
    print(f"\n[4] Analyse du Spectre Appris...")
    print(f"  Temps total: {total_time:.1f}s")
    
    test_output = encoder.forward(X_te[:2000])
    test_spectrum = test_output['spectrum']
    mean_spectrum = test_spectrum.mean(axis=0)
    
    print(f"\n  Distribution des amplitudes spectrales apprises :")
    print(f"  {'Harmonique':<14} | {'H_k':>8} | {'Amplitude apprise':>18} | {'H_k normalise':>14} | {'Ratio':>10}")
    print(f"  {'-'*14}+{'-'*10}+{'-'*20}+{'-'*16}+{'-'*12}")
    
    h_norm = H_BASE / H_BASE.sum()
    for k in range(10):
        amp = mean_spectrum[k]
        ratio = amp / h_norm[k] if h_norm[k] > 0 else 0
        bar = '#' * int(amp * 80)
        print(f"  H_{k+1} ({H_NAMES[k]:<8}) | {H_BASE[k]:8.3f} | "
              f"{amp:10.4f} {bar:<8} | {h_norm[k]:14.4f} | {ratio:10.4f}")
    
    # Correlation entre spectre appris et H_k
    correlation = np.corrcoef(mean_spectrum, H_BASE)[0, 1]
    print(f"\n  Correlation spectre appris <-> H_k : {correlation:.4f}")
    
    if correlation > 0.8:
        print(f"  >>> L'encodeur a APPRIS la structure harmonique ! <<<")
    elif correlation > 0.5:
        print(f"  >>> L'encodeur capture partiellement la structure harmonique <<<")
    else:
        print(f"  >>> L'encodeur n'a pas encore bien appris la structure (plus d'epochs necessaires) <<<")
    
    # === Visualisation : reconstruction ===
    print(f"\n[5] Qualite de Reconstruction...")
    
    # Prendre quelques exemples
    n_examples = 5
    indices = np.random.choice(len(X_te), n_examples, replace=False)
    examples = X_te[indices]
    ex_output = encoder.forward(examples)
    reconstructions = ex_output['reconstruction']
    spectra = ex_output['spectrum']
    
    for i in range(n_examples):
        mse = np.mean((reconstructions[i] - examples[i]) ** 2)
        # Spectre dominant
        dominant_k = np.argmax(spectra[i]) + 1
        dominant_name = H_NAMES[dominant_k - 1]
        print(f"  Exemple {i+1}: MSE={mse:.6f} | Dominant: H_{dominant_k} ({dominant_name}) "
              f"| Amplitude: {spectra[i][dominant_k-1]:.4f}")
    
    # === Sauvegarde ===
    print(f"\n[6] Sauvegarde...")
    
    model_data = {
        'input_dim': 784,
        'W_enc1': encoder.W_enc1.tolist(),
        'b_enc1': encoder.b_enc1.tolist(),
        'W_enc2': encoder.W_enc2.tolist(),
        'b_enc2': encoder.b_enc2.tolist(),
        'W_enc3': encoder.W_enc3.tolist(),
        'b_enc3': encoder.b_enc3.tolist(),
        'W_dec1': encoder.W_dec1.tolist(),
        'b_dec1': encoder.b_dec1.tolist(),
        'W_dec2': encoder.W_dec2.tolist(),
        'b_dec2': encoder.b_dec2.tolist(),
        'W_dec3': encoder.W_dec3.tolist(),
        'b_dec3': encoder.b_dec3.tolist(),
    }
    
    report = {
        'architecture': '784→256→64→10→64→256→784',
        'params': encoder.num_params,
        'epochs': EPOCHS,
        'train_time': float(total_time),
        'final_loss_recon': float(history['loss_recon'][-1]),
        'final_loss_spectral': float(history['loss_spectral'][-1]),
        'correlation_spectrum_H': float(correlation),
        'mean_spectrum': [float(x) for x in mean_spectrum],
        'H_base': [float(x) for x in H_BASE],
        'history': {k: [float(x) for x in v] for k, v in history.items()},
    }
    
    with open('spectral_encoder_weights.json', 'w') as f:
        json.dump(model_data, f)
    
    with open('spectral_encoder_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"  -> spectral_encoder_weights.json")
    print(f"  -> spectral_encoder_report.json")
    
    # === Benchmark comparatif : projection naive vs encodeur appris ===
    print(f"\n[7] Benchmark: Projection Naive vs Encodeur Appris...")
    
    # Projection naive (correlation, comme dans harmonic_computer.py)
    def naive_projection(data):
        flat = data.flatten()
        norm = np.linalg.norm(flat)
        flat_norm = flat / norm if norm > 0 else flat
        spectrum = np.zeros(10)
        for k in range(10):
            H_k = H_BASE[k]
            psi_k = H_k * (PHI ** (k + 1))
            spectrum[k] = abs(np.dot(flat_norm, np.ones_like(flat_norm) * psi_k / np.sqrt(len(flat_norm))))
        spec_sum = spectrum.sum()
        if spec_sum > 0:
            spectrum /= spec_sum
        return spectrum
    
    # Evaluer sur 500 exemples
    n_eval = min(500, len(X_te))
    X_eval = X_te[:n_eval]
    
    # Encodeur appris
    t0 = time.time()
    learned_spectra = encoder.encode(X_eval)
    t_learned = time.time() - t0
    
    # Projection naive
    t0 = time.time()
    naive_spectra = np.array([naive_projection(x) for x in X_eval])
    t_naive = time.time() - t0
    
    # Correlations avec H_k
    learned_corr = np.corrcoef(learned_spectra.mean(axis=0), H_BASE)[0, 1]
    naive_corr = np.corrcoef(naive_spectra.mean(axis=0), H_BASE)[0, 1]
    
    # Stabilite (ecart-type des amplitudes)
    learned_std = learned_spectra.std(axis=0).mean()
    naive_std = naive_spectra.std(axis=0).mean()
    
    print(f"\n  {'Metrique':<30} | {'Encodeur Appris':>16} | {'Projection Naive':>18}")
    print(f"  {'-'*30}+{'-'*18}+{'-'*20}")
    print(f"  {'Correlation avec H_k':<30} | {learned_corr:16.4f} | {naive_corr:18.4f}")
    print(f"  {'Stabilite (std)':<30} | {learned_std:16.4f} | {naive_std:18.4f}")
    print(f"  {'Temps (s) pour {n_eval} exemples':<30} | {t_learned:16.4f} | {t_naive:18.4f}")
    
    if learned_corr > naive_corr:
        print(f"\n  >>> L'encodeur appris SURPASSE la projection naive ! <<<")
    else:
        print(f"\n  >>> L'encodeur a besoin de plus d'entrainement <<<")
    
    print(f"\n{'='*70}")
    print(f"  FIN")
    print(f"{'='*70}")
    
    return encoder, report


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == '__main__':
    train_spectral_encoder()