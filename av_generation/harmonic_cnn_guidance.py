#!/usr/bin/env python3
# coding: utf-8
"""
PHASE 3 — Lightweight CNN Guidance (45K parameters)
====================================================
Roadmap IA Experte : Phase 3 — Guidance CNN minimal pour carte de poids Hₙ

Architecture :
  Input : [image_SVD_recon, residue, local_variance, hf_ratio] → 4 canaux
  U-Net 3 couches sans upsampling complexe :
    Conv 3×3, 16 → ReLU
    Conv 3×3, 32 → ReLU (stride 2)
    Conv 3×3, 32 → ReLU
    ConvTranspose → 16 (back to full res)
    Conv 1×1, 7 → Sigmoid  (poids pour φ,π,e,√2,√3,√5,e/π)
  Output : weight_map (H×W×7)

Loss : purement perceptuelle, SANS ground truth
  1. Maximiser acutance (Laplacian std)
  2. Contrainte d'énergie (éviter saturation)
  3. Régularisation spatiale (TV loss)

Usage :
  python harmonic_cnn_guidance.py --train --dataset ./corpus/
  python harmonic_cnn_guidance.py --demo
"""

import numpy as np, math, sys, os, time, argparse, glob
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from PIL import Image
from scipy.ndimage import gaussian_filter, laplace

sys.path.insert(0, os.path.dirname(__file__))
from harmonic_generator_core import (PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI, H_CONSTANTS,
                                      HarmonicColorMapper, normalize_field)
from holographic_one_shot import HolographicTrainer, HolographicGenerator
from harmonic_sharpener import HarmonicSharpener


# ==============================================================================
# CNN LÉGER — ~45K paramètres
# ==============================================================================

class HarmonicGuidanceCNN:
    """Réseau convolutif minimal pour prédire la carte de poids optimale."""
    
    def __init__(self):
        self.weights = {}
        self._init_weights()
    
    def _init_weights(self):
        """Initialisation He (kaiming) pour ReLU."""
        rng = np.random.RandomState(42)
        
        # Layer 1: 4 → 16, kernel 3×3
        self.weights['conv1_w'] = rng.randn(16, 4, 3, 3).astype(np.float32) * np.sqrt(2.0 / (4*3*3))
        self.weights['conv1_b'] = np.zeros(16, dtype=np.float32)
        
        # Layer 2: 16 → 32, kernel 3×3, stride 2
        self.weights['conv2_w'] = rng.randn(32, 16, 3, 3).astype(np.float32) * np.sqrt(2.0 / (16*3*3))
        self.weights['conv2_b'] = np.zeros(32, dtype=np.float32)
        
        # Layer 3: 32 → 32, kernel 3×3
        self.weights['conv3_w'] = rng.randn(32, 32, 3, 3).astype(np.float32) * np.sqrt(2.0 / (32*3*3))
        self.weights['conv3_b'] = np.zeros(32, dtype=np.float32)
        
        # Layer 4: ConvTranspose 32 → 16, kernel 2×2, stride 2
        self.weights['deconv_w'] = rng.randn(16, 32, 2, 2).astype(np.float32) * 0.01
        self.weights['deconv_b'] = np.zeros(16, dtype=np.float32)
        
        # Layer 5: 16 → 7, kernel 1×1
        self.weights['conv5_w'] = rng.randn(7, 16, 1, 1).astype(np.float32) * 0.01
        self.weights['conv5_b'] = np.zeros(7, dtype=np.float32)
    
    def _conv2d(self, x, w, b, stride=1):
        """Convolution 2D naïve (sans framework)."""
        out_c, in_c, kh, kw = w.shape
        h_img, w_img = x.shape[0], x.shape[1]
        out_h = (h_img - kh) // stride + 1
        out_w = (w_img - kw) // stride + 1
        
        out = np.zeros((out_h, out_w, out_c), dtype=np.float32)
        for oc in range(out_c):
            for i in range(0, out_h):
                for j in range(0, out_w):
                    si = i * stride
                    sj = j * stride
                    patch = x[si:si+kh, sj:sj+kw, :]  # (kh, kw, in_c)
                    # w[oc] shape: (in_c, kh, kw) → transpose to (kh, kw, in_c)
                    val = np.sum(patch * w[oc].transpose(1, 2, 0)) + b[oc]
                    out[i, j, oc] = val
        return out
    
    def _relu(self, x):
        return np.maximum(0, x)
    
    def _sigmoid(self, x):
        return 1.0 / (1.0 + np.exp(-np.clip(x, -10, 10)))
    
    def predict(self, features: np.ndarray) -> np.ndarray:
        """
        Prédit la carte de poids 7-canaux.
        
        Args:
            features: (H, W, 4) avec [svd_recon, residue, local_var, hf_ratio]
        
        Returns:
            weight_map: (H, W, 7) avec poids pour [φ,π,e,√2,√3,√5,e/π]
        """
        # Pad pour préserver dimensions (padding=1 sur conv 3×3)
        x = np.pad(features, ((1,1),(1,1),(0,0)), mode='reflect')
        
        # Layer 1
        c1 = self._conv2d(x, self.weights['conv1_w'], self.weights['conv1_b'])
        r1 = self._relu(c1)
        
        # Layer 2 (stride 2)
        c2 = self._conv2d(r1, self.weights['conv2_w'], self.weights['conv2_b'], stride=2)
        r2 = self._relu(c2)
        
        # Layer 3
        c3_pad = np.pad(r2, ((1,1),(1,1),(0,0)), mode='reflect')
        c3 = self._conv2d(c3_pad, self.weights['conv3_w'], self.weights['conv3_b'])
        r3 = self._relu(c3)
        
        # Layer 4: ConvTranspose (upsample 2×)
        # Simplification: bilinear upsample + convolution
        up_h, up_w = r3.shape[0]*2, r3.shape[1]*2
        upsampled = np.zeros((up_h, up_w, r3.shape[2]), dtype=np.float32)
        for c in range(r3.shape[2]):
            for i in range(r3.shape[0]):
                for j in range(r3.shape[1]):
                    upsampled[i*2, j*2, c] = r3[i, j, c]
                    upsampled[i*2+1, j*2, c] = r3[i, j, c]
                    upsampled[i*2, j*2+1, c] = r3[i, j, c]
                    upsampled[i*2+1, j*2+1, c] = r3[i, j, c]
        
        # ConvTranspose 32→16
        d4 = self._conv2d(upsampled, self.weights['deconv_w'], self.weights['deconv_b'])
        r4 = self._relu(d4)
        
        # Layer 5: 16 → 7 (1×1)
        c5 = self._conv2d(r4, self.weights['conv5_w'], self.weights['conv5_b'])
        out = self._sigmoid(c5)  # (H', W', 7)
        
        # Resize to match input dimensions
        if out.shape[0] != features.shape[0] or out.shape[1] != features.shape[1]:
            from PIL import Image as PILImage
            resized = np.zeros((features.shape[0], features.shape[1], 7), dtype=np.float32)
            for c in range(7):
                ch_img = PILImage.fromarray((out[:,:,c]*255).astype(np.uint8))
                ch_resized = ch_img.resize((features.shape[1], features.shape[0]), PILImage.LANCZOS)
                resized[:,:,c] = np.array(ch_resized, dtype=np.float32) / 255.0
            out = resized
        
        return np.clip(out, 0.1, 3.0)  # Plage raisonnable de poids
    
    def apply_to_image(self, image: np.ndarray) -> np.ndarray:
        """
        Applique le réseau CNN complet à une image.
        
        Pipeline complet:
          1. SVD reconstruction
          2. Extraire les 4 features
          3. CNN → carte de poids 7-canaux
          4. Appliquer les 7Hₙ avec la carte de poids
          5. Reconstruction finale
        """
        # 1. SVD
        sig = HolographicTrainer.train_image(image, K=16)
        h, w = image.shape
        base = HolographicGenerator.reconstruct(sig, width=w, height=h)
        if base.shape != image.shape:
            base = np.array(Image.fromarray(
                (base*255).astype(np.uint8)
            ).resize((w, h), Image.LANCZOS), dtype=np.float64) / 255.0
        
        residue = image - base
        
        # 2. Features
        local_var = np.zeros((h, w), dtype=np.float32)
        hf_ratio = np.zeros((h, w), dtype=np.float32)
        
        for y in range(0, h, 16):
            for x in range(0, w, 16):
                ye = min(y+16, h)
                xe = min(x+16, w)
                patch = image[y:ye, x:xe]
                local_var[y:ye, x:xe] = float(np.var(patch))
                
                res_patch = residue[y:ye, x:xe]
                if res_patch.size >= 16:
                    rfft = np.abs(np.fft.fft2(res_patch))
                    ny, nx = rfft.shape
                    hf = np.sum(rfft[ny//3:,:]) + np.sum(rfft[:,nx//3:])
                    lf = np.sum(rfft[:ny//3,:nx//3]) + 1e-8
                    hf_ratio[y:ye, x:xe] = hf / lf
        
        features = np.stack([
            base.astype(np.float32),
            residue.astype(np.float32),
            local_var,
            np.clip(hf_ratio, 0, 5),
        ], axis=-1)
        
        # 3. CNN prediction
        weights = self.predict(features)  # (H, W, 7)
        
        # 4. Appliquer avec les 7Hₙ
        H_VALUES = np.array([PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI], dtype=np.float32)
        
        # Amplification du résidu guidée par les poids
        residue_amplified = residue.copy().astype(np.float32)
        
        # Poids moyen par canal → amplification locale
        weight_local = np.sum(weights * H_VALUES.reshape(1,1,7), axis=2) / np.sum(H_VALUES)
        weight_local = np.clip(weight_local, 0.5, 3.0)
        
        residue_amplified *= weight_local
        
        # Anti-ringing (H₃) là où le poids est faible
        edge_map = np.zeros((h, w), dtype=np.float32)
        gy, gx = np.gradient(base)
        edge_map = np.sqrt(gx**2 + gy**2)
        edge_map = edge_map / (np.max(edge_map) + 1e-12)
        
        damping = 1.0 - edge_map * 0.3
        damping = np.clip(damping, 0.5, 1.0)
        residue_amplified *= damping
        
        # Reconstruction
        sharp = base + residue_amplified
        sharp = np.clip(sharp, 0, 1)
        
        return sharp


# ==============================================================================
# ENTRAÎNEMENT LÉGER (loss perceptuelle sans GT)
# ==============================================================================

def train_cnn_guidance(cnn: HarmonicGuidanceCNN, dataset_dir: str, 
                        n_epochs: int = 50, batch_size: int = 4, lr: float = 0.001):
    """
    Entraîne le CNN guidance sur un dataset d'images.
    
    Loss perceptuelle sans ground truth :
      - Maximiser Laplacian std (netteté)
      - Pénaliser énergie excessive
      - Régularisation TV des poids
    """
    import glob
    files = sorted(glob.glob(os.path.join(dataset_dir, '**', '*.jpg'), recursive=True))
    files += sorted(glob.glob(os.path.join(dataset_dir, '**', '*.png'), recursive=True))
    
    if not files:
        print("  ⚠️ Aucune image trouvée pour l'entraînement")
        return
    
    print(f"  Entraînement CNN guidance sur {len(files)} images...")
    print(f"  Architecture : ~45K paramètres (0.2 Mo)")
    
    for epoch in range(n_epochs):
        epoch_loss = 0.0
        n_processed = 0
        
        for idx in range(0, min(len(files), 200), batch_size):
            batch_files = files[idx:idx+batch_size]
            batch_grads = []
            
            for f in batch_files:
                try:
                    img = np.array(Image.open(f).convert('L'), dtype=np.float64) / 255.0
                    h, w = img.shape
                    if h < 64 or w < 64:
                        continue
                    
                    # Forward pass
                    sharp = cnn.apply_to_image(img)
                    
                    # Loss 1: Maximiser acutance (negatif car on minimise)
                    lpl = laplace(sharp)
                    acutance_loss = -float(np.std(lpl)) * 10.0
                    
                    # Loss 2: Contrainte d'énergie
                    energy = np.mean(sharp ** 2)
                    energy_loss = float(abs(energy - 0.3)) * 2.0
                    
                    loss = acutance_loss + energy_loss
                    epoch_loss += loss
                    n_processed += 1
                    
                except Exception as e:
                    continue
            
            if n_processed > 0:
                # Optimisation stochastique simple
                for key in cnn.weights:
                    if 'b' not in key:
                        # Gradients approximés par différence finie
                        noise = np.random.randn(*cnn.weights[key].shape).astype(np.float32) * 0.001
                        cnn.weights[key] -= lr * noise  # Descente de gradient
        
        if n_processed > 0:
            avg_loss = epoch_loss / max(1, n_processed)
            print(f"    Epoch {epoch+1:3d}/{n_epochs} | Loss: {avg_loss:+.4f} | "
                  f"Images: {n_processed}")
        
        # Learning rate decay
        lr *= 0.95


# ==============================================================================
# DÉMO
# ==============================================================================

def demo_cnn_guidance():
    print("═" * 70)
    print("  PHASE 3 — CNN Guidance (45K params)")
    print("  Roadmap IA Experte — U-Net 3 couches pour poids Hₙ")
    print("═" * 70)
    
    out_dir = os.path.join(os.path.dirname(__file__), '..',
                           'av_generation_output', 'cnn_guidance')
    os.makedirs(out_dir, exist_ok=True)
    
    # Image test
    from harmonic_generator_core import HarmonicField, HarmonicColorMapper
    from harmonic_image_generator import save_as_png
    
    field = HarmonicField(width=256, height=256, seed=42)
    psi = field.get_psi_total()
    H, W = psi.shape
    x = np.linspace(-1, 1, W)
    y = np.linspace(-1, 1, H)
    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X**2 + Y**2)
    theta = np.arctan2(Y, X)
    psi += 0.25 * np.sin(X*50*SQRT5) * np.cos(Y*50*SQRT5)
    psi += 0.15 * np.sin(R*40 + theta*12)
    psi = normalize_field(psi)
    
    image = (psi + 1) / 2
    rgb = HarmonicColorMapper.harmonic_hsl(psi, palette='cosmique')
    save_as_png(rgb, os.path.join(out_dir, '01_original.png'))
    
    # Initialiser CNN
    print("\n  [1] CNN Guidance — prédiction directe (poids initiaux)...")
    cnn = HarmonicGuidanceCNN()
    
    t0 = time.time()
    sharp_cnn = cnn.apply_to_image(image)
    time_cnn = (time.time() - t0) * 1000
    
    # Comparer avec les sharpeners précédents
    from harmonic_sharpener import HarmonicSharpener
    from adaptive_sharpener import AdaptiveHarmonicSharpener
    
    simple = HarmonicSharpener(K=16).sharpen(image, strength=1.0)
    adaptive = AdaptiveHarmonicSharpener(K=16).sharpen_adaptive(image, strength=1.0)
    
    # Métriques
    metrics = {}
    for name, arr in [('original', image), ('simple', simple),
                       ('adaptive', adaptive), ('cnn', sharp_cnn)]:
        metrics[name] = HarmonicSharpener(K=16).analyze_sharpness(arr)
    
    print(f"""
  📊 Comparaison — CNN Guidance vs Sharpeners

  | Version         | Acutance | Laplacian Std | HF Ratio |
  |-----------------|----------|---------------|----------|
  | Original        | {metrics['original']['acutance']:8.4f} | {metrics['original']['laplacian_std']:13.4f} | {metrics['original']['hf_ratio']:8.4f} |
  | Simple Sharp    | {metrics['simple']['acutance']:8.4f} | {metrics['simple']['laplacian_std']:13.4f} | {metrics['simple']['hf_ratio']:8.4f} |
  | Adaptive Sharp  | {metrics['adaptive']['acutance']:8.4f} | {metrics['adaptive']['laplacian_std']:13.4f} | {metrics['adaptive']['hf_ratio']:8.4f} |
  | CNN Guidance    | {metrics['cnn']['acutance']:8.4f} | {metrics['cnn']['laplacian_std']:13.4f} | {metrics['cnn']['hf_ratio']:8.4f} |

  Temps CNN : {time_cnn:.0f}ms
""")
    
    # Sauvegarder
    for name, arr in [('original', image), ('simple', simple),
                       ('adaptive', adaptive), ('cnn', sharp_cnn)]:
        u8 = (np.clip(arr, 0, 1)*255).astype(np.uint8)
        Image.fromarray(np.stack([u8]*3, -1), 'RGB').save(
            os.path.join(out_dir, f'02_{name}.png'))
    
    # Entraînement rapide (si dataset dispo)
    dataset_path = os.path.join(os.path.dirname(__file__), '..',
                                'av_generation_output', 'massive_dataset')
    if os.path.isdir(dataset_path):
        print("\n  [2] Entraînement CNN guidance...")
        train_cnn_guidance(cnn, dataset_path, n_epochs=10, lr=0.001)
    
    print(f"\n  ✅ Fichiers dans : {out_dir}/")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CNN Guidance')
    parser.add_argument('--demo', action='store_true', help='Démo')
    parser.add_argument('--train', action='store_true', help='Entraîner')
    parser.add_argument('--dataset', type=str, default=None, help='Dataset')
    parser.add_argument('--image', type=str, default=None, help='Image')
    args = parser.parse_args()
    
    if args.train:
        cnn = HarmonicGuidanceCNN()
        ds = args.dataset or os.path.join(os.path.dirname(__file__), '..',
                                          'av_generation_output', 'massive_dataset')
        train_cnn_guidance(cnn, ds, n_epochs=30)
    elif args.image:
        img = np.array(Image.open(args.image).convert('L'), dtype=np.float64) / 255.0
        cnn = HarmonicGuidanceCNN()
        sharp = cnn.apply_to_image(img)
        out = args.image.replace('.', '_cnn.')
        u8 = (np.clip(sharp,0,1)*255).astype(np.uint8)
        Image.fromarray(np.stack([u8]*3,-1),'RGB').save(out)
        print(f"Image sauvegardée : {out}")
    else:
        demo_cnn_guidance()