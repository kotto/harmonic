#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BENCHMARK AVANCE: Harmonic ConvNet vs CNN Classique sur MNIST
===============================================================
Etapes suivantes:
  P0: Ajout couche convolutionnelle avant projection spectrale
  P2: Pre-processing FFT/DCT avant projection spectrale
  Comparaison: HarmonicConv vs CNN Classique vs MLP de base

Objectif: Depasser 95% avec l'architecture harmonique.
"""

import numpy as np
import time, sys, os, gzip, struct, json

# ==============================================================================
# CONSTANTES HARMONIQUES
# ==============================================================================
PHI = (1 + np.sqrt(5))/2     # 1.618
PI  = np.pi                  # 3.142
E   = np.e                   # 2.718
SQ2 = np.sqrt(2)             # 1.414
SQ3 = np.sqrt(3)             # 1.732
SQ5 = np.sqrt(5)             # 2.236

H_BASE = np.array([PHI, PI, E, SQ2, SQ3, SQ5, E/PI, PHI*SQ2, E*PHI, PI*SQ5])

# ==============================================================================
# CHARGEMENT MNIST
# ==============================================================================

def load_mnist(data_dir='.'):
    files = {
        'train_images': 'train-images-idx3-ubyte.gz',
        'train_labels': 'train-labels-idx1-ubyte.gz',
        'test_images':  't10k-images-idx3-ubyte.gz',
        'test_labels':  't10k-labels-idx1-ubyte.gz',
    }
    urls = {k: f'https://ossci-datasets.s3.amazonaws.com/mnist/{f}' for k, f in files.items()}
    data = {}
    for key, filename in files.items():
        path = os.path.join(data_dir, filename)
        if not os.path.exists(path):
            print(f"  Telechargement {filename}...")
            import urllib.request
            urllib.request.urlretrieve(urls[key], path)
        with gzip.open(path, 'rb') as f:
            if 'labels' in key:
                magic, num = struct.unpack('>II', f.read(8))
                data[key] = np.frombuffer(f.read(), dtype=np.uint8)
            else:
                magic, num, rows, cols = struct.unpack('>IIII', f.read(16))
                img = np.frombuffer(f.read(), dtype=np.uint8).reshape(num, rows, cols)
                data[key] = img.astype(np.float64) / 255.0
    return data['train_images'], data['train_labels'], data['test_images'], data['test_labels']

def one_hot(labels, n=10):
    oh = np.zeros((len(labels), n), dtype=np.float64)
    oh[np.arange(len(labels)), labels] = 1.0
    return oh

# ==============================================================================
# CONVOLUTION NAIVE (im2col) - sans dependance externe
# ==============================================================================

def im2col(X, k_h, k_w, stride=1, pad=0):
    """Convertit une image batch en matrice pour convolution rapide."""
    N, H, W = X.shape
    if pad > 0:
        X = np.pad(X, ((0,0),(pad,pad),(pad,pad)), mode='constant')
    H_out = (H + 2*pad - k_h)//stride + 1
    W_out = (W + 2*pad - k_w)//stride + 1
    cols = np.zeros((N, k_h, k_w, H_out, W_out))
    for i in range(k_h):
        ii = i*stride
        for j in range(k_w):
            jj = j*stride
            cols[:, i, j, :, :] = X[:, ii:ii+H_out*stride:stride, jj:jj+W_out*stride:stride]
    cols = cols.transpose(0,3,4,1,2).reshape(-1, k_h*k_w)
    return cols, H_out, W_out

def conv2d(X, weight, bias, stride=1, pad=0):
    """Convolution 2D naive mais vectorisee."""
    N, H, W = X.shape
    out_ch, in_ch, k_h, k_w = weight.shape
    assert in_ch == 1, "Une seule couche d'entree supportee pour l'instant"
    cols, H_out, W_out = im2col(X, k_h, k_w, stride, pad)
    out = cols @ weight.reshape(out_ch, -1).T + bias
    return out.reshape(N, H_out, W_out, out_ch).transpose(0,3,1,2), (cols, H_out, W_out, X)

def conv2d_backward(dout, cache, weight, X_input, stride=1, pad=0):
    """Backward convolution pour mise a jour."""
    cols, H_out, W_out, X_pad = cache
    N, out_ch, H_o, W_o = dout.shape
    dout_flat = dout.transpose(0,2,3,1).reshape(-1, out_ch)
    dW = dout_flat.T @ cols
    dW = dW.reshape(weight.shape)
    db = dout_flat.sum(axis=0)
    return dW, db

def relu(x):
    return np.maximum(0, x)

def relu_backward(dout, x):
    return dout * (x > 0)

def maxpool2d(X, size=2, stride=2):
    N, C, H, W = X.shape
    H_out = (H-size)//stride + 1
    W_out = (W-size)//stride + 1
    out = np.zeros((N, C, H_out, W_out))
    for i in range(H_out):
        for j in range(W_out):
            patch = X[:,:,i*stride:i*stride+size,j*stride:j*stride+size]
            out[:,:,i,j] = patch.max(axis=(2,3))
    return out

# ==============================================================================
# PRE-PROCESSING FFT
# ==============================================================================

def fft_preprocess(X):
    """Transforme des images en leur spectre de magnitude FFT."""
    N, H, W = X.shape
    X_fft = np.zeros_like(X)
    for i in range(N):
        fft = np.fft.fft2(X[i])
        fft_shift = np.fft.fftshift(fft)
        mag = np.abs(fft_shift)
        # log scale
        mag = np.log1p(mag)
        mag = (mag - mag.min()) / (mag.max() - mag.min() + 1e-8)
        X_fft[i] = mag
    return X_fft

def dct_preprocess(X, block_size=8):
    """Transforme des images par DCT par blocs (comme JPEG)."""
    N, H, W = X.shape
    X_dct = np.zeros_like(X)
    for i in range(N):
        img = X[i]
        for y in range(0, H, block_size):
            for x in range(0, W, block_size):
                block = img[y:y+block_size, x:x+block_size]
                if block.shape[0] == block_size and block.shape[1] == block_size:
                    # DCT 2D manuelle
                    dct_block = np.zeros_like(block)
                    for u in range(block_size):
                        for v in range(block_size):
                            cu = 1/np.sqrt(2) if u==0 else 1
                            cv = 1/np.sqrt(2) if v==0 else 1
                            s = 0.0
                            for p in range(block_size):
                                for q in range(block_size):
                                    s += block[p,q] * \
                                         np.cos((2*p+1)*u*np.pi/(2*block_size)) * \
                                         np.cos((2*q+1)*v*np.pi/(2*block_size))
                            dct_block[u,v] = 0.25*cu*cv*s
                    X_dct[i, y:y+block_size, x:x+block_size] = np.abs(dct_block)
    # Normaliser
    for i in range(N):
        m = X_dct[i]
        X_dct[i] = (m - m.min()) / (m.max() - m.min() + 1e-8)
    return X_dct


# ==============================================================================
# MODELE HARMONIQUE AVANCE (Conv + Projection Spectrale + Reinjection)
# ==============================================================================

class HarmonicConvNet:
    """
    CNN Harmonique: convolution + pooling + projection spectrale + reinjection.
    
    Architecture:
      1. Conv2D 1->16 (5x5) + ReLU + MaxPool 2x2
      2. Flatten -> 16*12*12 = 2304
      3. Couche lineaire 2304 -> hidden avec activation spectrale H_k
      4. Couche lineaire hidden -> 10
      
    L'apprentissage utilise la reinjection spectrale avec G_{ij,j}=0.
    """
    
    def __init__(self, hidden_dim=128, num_classes=10, seed=42):
        np.random.seed(seed)
        
        self.hidden_dim = hidden_dim
        self.num_classes = num_classes
        self.K = 10
        
        # Conv layer
        self.conv_W = np.random.randn(16, 1, 5, 5) * 0.1
        self.conv_b = np.zeros(16)
        
        # Conv output size: (28-5+1)=24, pool -> 12, flat = 16*12*12 = 2304
        self.conv_out_dim = 16 * 12 * 12
        
        # Harmonic hidden layer
        scale1 = 1.0/np.sqrt(self.conv_out_dim)
        self.W1 = np.random.randn(self.conv_out_dim, hidden_dim) * scale1
        self.b1 = np.zeros(hidden_dim)
        
        # Assignation harmonique par neurone
        self.neuron_harmonic = np.array([(i%self.K)+1 for i in range(hidden_dim)])
        self.harmonic_values = np.array([H_BASE[k-1] for k in self.neuron_harmonic])
        
        # Output layer
        scale2 = 1.0/np.sqrt(hidden_dim)
        self.W2 = np.random.randn(hidden_dim, num_classes) * scale2
        self.b2 = np.zeros(num_classes)
        
        # Caches
        self.cache = {}
        
        self.num_params = (16*5*5 + 16 + self.conv_out_dim*hidden_dim + hidden_dim
                          + hidden_dim*num_classes + num_classes)
    
    def forward(self, X_raw):
        """X_raw: (N, 28, 28) images normalisees."""
        # Conv
        conv_out, conv_cache = conv2d(X_raw, self.conv_W, self.conv_b)
        conv_relu = relu(conv_out)
        pool_out = maxpool2d(conv_relu, size=2, stride=2)
        
        # Flatten
        N = X_raw.shape[0]
        flat = pool_out.reshape(N, -1)
        
        # Harmonic dense
        z1 = flat @ self.W1 + self.b1
        h1 = relu(z1) * self.harmonic_values[np.newaxis, :]
        
        # Output
        logits = h1 @ self.W2 + self.b2
        exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
        probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
        
        # Cache pour backward
        self.cache = {
            'conv_cache': conv_cache,
            'conv_relu': conv_relu,
            'pool_out': pool_out,
            'flat': flat,
            'z1': z1,
            'h1': h1,
            'X_raw': X_raw,
        }
        
        return probs
    
    def predict(self, X):
        return np.argmax(self.forward(X), axis=1)
    
    def harmonic_update(self, X_raw, y_true, probs, learning_rate=0.01):
        """Mise a jour avec reinjection spectrale."""
        batch_size = X_raw.shape[0]
        
        # Erreur sortie
        error_output = probs - y_true
        
        # Retroinjection harmonique sur la couche dense
        error_hidden = error_output @ self.W2.T
        h_inv = 1.0/(self.harmonic_values + 1e-8)
        error_hidden_corrected = error_hidden * h_inv[np.newaxis, :]
        error_hidden_corrected *= (self.cache['z1'] > 0)
        
        # Gradients couche output
        grad_W2 = self.cache['h1'].T @ error_output / batch_size
        grad_b2 = np.mean(error_output, axis=0)
        
        # Gradients couche hidden (reinjection modulee)
        rf = 1.0/(1.0 + self.harmonic_values)
        grad_W1 = self.cache['flat'].T @ (error_hidden_corrected * rf[np.newaxis, :]) / batch_size
        grad_b1 = np.mean(error_hidden_corrected * rf, axis=0)
        
        # Erreur retropropagee au flatten
        error_flat = (error_hidden_corrected * rf[np.newaxis, :]) @ self.W1.T
        
        # Erreur sur le pooling (reshape inverse)
        error_pool = error_flat.reshape(self.cache['pool_out'].shape)
        
        # Erreur sur conv (upsample maxpool inverse - approximation naive)
        error_conv_relu = np.zeros_like(self.cache['conv_relu'])
        for i in range(batch_size):
            for c in range(error_conv_relu.shape[1]):
                for h in range(error_pool.shape[2]):
                    for w in range(error_pool.shape[3]):
                        hh, ww = h*2, w*2
                        patch = self.cache['conv_relu'][i,c,hh:hh+2,ww:ww+2]
                        max_idx = np.unravel_index(patch.argmax(), patch.shape)
                        error_conv_relu[i,c,hh+max_idx[0],ww+max_idx[1]] = error_pool[i,c,h,w]
        
        error_conv = relu_backward(error_conv_relu, self.cache['conv_relu'])
        
        # Gradient convolution
        grad_conv_W, grad_conv_b = conv2d_backward(
            error_conv, self.cache['conv_cache'],
            self.conv_W, self.cache['X_raw']
        )
        
        # Conservation check
        error_norm_before = np.mean(np.abs(error_output))
        
        # Apply updates
        self.W2 -= learning_rate * grad_W2
        self.b2 -= learning_rate * grad_b2
        self.W1 -= learning_rate * grad_W1
        self.b1 -= learning_rate * grad_b1
        self.conv_W -= learning_rate * grad_conv_W
        self.conv_b -= learning_rate * grad_conv_b
        
        new_probs = self.forward(X_raw)
        error_norm_after = np.mean(np.abs(new_probs - y_true))
        
        return {
            'error_before': error_norm_before,
            'error_after': error_norm_after,
            'conserved': error_norm_after <= error_norm_before * 1.1,
        }


# ==============================================================================
# CNN CLASSIQUE (Backprop Standard)
# ==============================================================================

class ClassicCNN:
    """CNN classique pour comparaison equitable."""
    
    def __init__(self, hidden_dim=128, num_classes=10, seed=42):
        np.random.seed(seed)
        
        self.conv_W = np.random.randn(16, 1, 5, 5) * 0.1
        self.conv_b = np.zeros(16)
        self.conv_out_dim = 16 * 12 * 12
        
        scale1 = 1.0/np.sqrt(self.conv_out_dim)
        self.W1 = np.random.randn(self.conv_out_dim, hidden_dim) * scale1
        self.b1 = np.zeros(hidden_dim)
        
        scale2 = 1.0/np.sqrt(hidden_dim)
        self.W2 = np.random.randn(hidden_dim, num_classes) * scale2
        self.b2 = np.zeros(num_classes)
        
        self.cache = {}
        self.num_params = (16*5*5+16 + self.conv_out_dim*hidden_dim+hidden_dim
                          + hidden_dim*num_classes+num_classes)
    
    def forward(self, X_raw):
        conv_out, conv_cache = conv2d(X_raw, self.conv_W, self.conv_b)
        conv_relu = relu(conv_out)
        pool_out = maxpool2d(conv_relu, size=2, stride=2)
        
        N = X_raw.shape[0]
        flat = pool_out.reshape(N, -1)
        
        z1 = flat @ self.W1 + self.b1
        h1 = relu(z1)
        logits = h1 @ self.W2 + self.b2
        
        exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
        probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
        
        self.cache = {
            'conv_cache': conv_cache, 'conv_relu': conv_relu,
            'pool_out': pool_out, 'flat': flat, 'z1': z1, 'h1': h1,
            'X_raw': X_raw,
        }
        return probs
    
    def predict(self, X):
        return np.argmax(self.forward(X), axis=1)
    
    def backprop_update(self, X_raw, y_true, probs, learning_rate=0.01):
        batch_size = X_raw.shape[0]
        error_output = probs - y_true
        
        # Backprop through dense layers
        grad_W2 = self.cache['h1'].T @ error_output / batch_size
        grad_b2 = np.mean(error_output, axis=0)
        
        error_hidden = error_output @ self.W2.T
        error_hidden *= (self.cache['z1'] > 0)
        
        grad_W1 = self.cache['flat'].T @ error_hidden / batch_size
        grad_b1 = np.mean(error_hidden, axis=0)
        
        error_flat = error_hidden @ self.W1.T
        error_pool = error_flat.reshape(self.cache['pool_out'].shape)
        
        # Unpool (naive)
        error_conv_relu = np.zeros_like(self.cache['conv_relu'])
        for i in range(batch_size):
            for c in range(error_conv_relu.shape[1]):
                for h in range(error_pool.shape[2]):
                    for w in range(error_pool.shape[3]):
                        hh, ww = h*2, w*2
                        patch = self.cache['conv_relu'][i,c,hh:hh+2,ww:ww+2]
                        max_idx = np.unravel_index(patch.argmax(), patch.shape)
                        error_conv_relu[i,c,hh+max_idx[0],ww+max_idx[1]] = error_pool[i,c,h,w]
        
        error_conv = relu_backward(error_conv_relu, self.cache['conv_relu'])
        grad_conv_W, grad_conv_b = conv2d_backward(
            error_conv, self.cache['conv_cache'], self.conv_W, self.cache['X_raw']
        )
        
        self.W2 -= learning_rate * grad_W2
        self.b2 -= learning_rate * grad_b2
        self.W1 -= learning_rate * grad_W1
        self.b1 -= learning_rate * grad_b1
        self.conv_W -= learning_rate * grad_conv_W
        self.conv_b -= learning_rate * grad_conv_b
        
        return np.mean(np.abs(error_output))


# ==============================================================================
# BOUCLE D'ENTRAINEMENT
# ==============================================================================

def cross_entropy_loss(probs, y_true):
    eps = 1e-12
    return -np.mean(np.log(np.maximum(np.sum(probs*y_true, axis=1), eps)))

def train_model(model, X_train, y_train, X_test, y_test,
                epochs=20, batch_size=128, learning_rate=0.01,
                is_harmonic=False, preprocess=None):
    """
    Entraine un modele.
    preprocess: None, 'fft', ou 'dct'
    """
    # Appliquer preprocessing si demande
    if preprocess == 'fft':
        X_train = fft_preprocess(X_train)
        X_test = fft_preprocess(X_test)
    elif preprocess == 'dct':
        X_train = dct_preprocess(X_train)
        X_test = dct_preprocess(X_test)
    
    n_train = X_train.shape[0]
    n_batches = n_train // batch_size
    
    history = {'train_loss':[], 'test_loss':[], 'train_acc':[], 'test_acc':[],
               'conservation_rate':[], 'epoch_times':[]}
    
    name = 'Harmonique' if is_harmonic else 'Classique'
    pp_name = f' [{preprocess.upper()}]' if preprocess else ''
    print(f"\n  {'='*55}")
    print(f"  {name}{pp_name} | {model.num_params:,} params | Epochs: {epochs}")
    print(f"  {'='*55}")
    
    for epoch in range(epochs):
        t0 = time.time()
        perm = np.random.permutation(n_train)
        Xs, ys = X_train[perm], y_train[perm]
        
        total_loss, total_acc, cons_oks = 0.0, 0.0, 0
        
        for i in range(n_batches):
            start, end = i*batch_size, (i+1)*batch_size
            Xb, yb = Xs[start:end], ys[start:end]
            
            probs = model.forward(Xb)
            total_loss += cross_entropy_loss(probs, yb)
            total_acc += np.mean(np.argmax(probs,1) == np.argmax(yb,1))
            
            if is_harmonic:
                info = model.harmonic_update(Xb, yb, probs, learning_rate)
                if info['conserved']: cons_oks += 1
            else:
                model.backprop_update(Xb, yb, probs, learning_rate)
        
        avg_train_loss = total_loss/n_batches
        avg_train_acc = total_acc/n_batches
        
        test_probs = model.forward(X_test)
        test_loss = cross_entropy_loss(test_probs, y_test)
        test_acc = np.mean(np.argmax(test_probs,1) == np.argmax(y_test,1))
        ep_time = time.time()-t0
        
        history['train_loss'].append(avg_train_loss)
        history['test_loss'].append(test_loss)
        history['train_acc'].append(avg_train_acc)
        history['test_acc'].append(test_acc)
        history['epoch_times'].append(ep_time)
        
        if is_harmonic:
            cr = cons_oks/n_batches
            history['conservation_rate'].append(cr)
            print(f"  Ep {epoch+1:2d}/{epochs} | Loss: {avg_train_loss:.4f}->{test_loss:.4f} | "
                  f"Acc: {avg_train_acc:.4f}->{test_acc:.4f} | G=0: {cr:.2f} | {ep_time:.1f}s")
        else:
            print(f"  Ep {epoch+1:2d}/{epochs} | Loss: {avg_train_loss:.4f}->{test_loss:.4f} | "
                  f"Acc: {avg_train_acc:.4f}->{test_acc:.4f} | {ep_time:.1f}s")
        
        learning_rate *= 0.95
    
    return history


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("="*70)
    print("  BENCHMARK AVANCE: HarmonicConv vs CNN vs FFT/DCT (MNIST)")
    print("  P0: Conv + Projection Spectrale + Reinjection")
    print("="*70)
    
    # Chargement
    print("\n[1/6] Chargement MNIST...")
    X_train, y_train_raw, X_test, y_test_raw = load_mnist('.')
    y_train = one_hot(y_train_raw)
    y_test = one_hot(y_test_raw)
    print(f"  Train: {X_train.shape[0]} | Test: {X_test.shape[0]} | Shape: {X_train.shape[1:]}")

    # Config
    HIDDEN = 128
    EPOCHS = 15
    BATCH = 128
    LR = 0.02
    
    results = {}
    
    # === CNN Classique (baseline) ===
    print("\n[2/6] CNN Classique (baseline)...")
    cnn = ClassicCNN(hidden_dim=HIDDEN, seed=42)
    print(f"  Params: {cnn.num_params:,}")
    results['CNN'] = train_model(cnn, X_train, y_train, X_test, y_test,
                                 epochs=EPOCHS, batch_size=BATCH, learning_rate=LR,
                                 is_harmonic=False)
    
    # === HarmonicConv (P0) ===
    print("\n[3/6] HarmonicConv (P0: Conv + Projection Spectrale)...")
    hcn = HarmonicConvNet(hidden_dim=HIDDEN, seed=42)
    print(f"  Params: {hcn.num_params:,}")
    results['HarmonicConv'] = train_model(hcn, X_train, y_train, X_test, y_test,
                                           epochs=EPOCHS, batch_size=BATCH, learning_rate=LR,
                                           is_harmonic=True)
    
    # === FFT + CNN ===
    print("\n[4/6] CNN + FFT Pre-processing...")
    cnn_fft = ClassicCNN(hidden_dim=HIDDEN, seed=42)
    results['CNN_FFT'] = train_model(cnn_fft, X_train.copy(), y_train, X_test.copy(), y_test,
                                      epochs=EPOCHS, batch_size=BATCH, learning_rate=LR,
                                      is_harmonic=False, preprocess='fft')
    
    # === FFT + HarmonicConv ===
    print("\n[5/6] HarmonicConv + FFT Pre-processing (P2)...")
    hcn_fft = HarmonicConvNet(hidden_dim=HIDDEN, seed=42)
    results['HarmonicConv_FFT'] = train_model(hcn_fft, X_train.copy(), y_train, X_test.copy(), y_test,
                                               epochs=EPOCHS, batch_size=BATCH, learning_rate=LR,
                                               is_harmonic=True, preprocess='fft')
    
    # === Comparaison finale ===
    print("\n[6/6] Comparaison finale...")
    print(f"\n  {'='*65}")
    print(f"  RESULTATS COMPARATIFS")
    print(f"  {'='*65}")
    print(f"  {'Modele':<22} | {'Parametres':>10} | {'Acc Test':>10} | {'Loss Test':>10}")
    print(f"  {'-'*22}+{'-'*12}+{'-'*12}+{'-'*12}")
    
    best_acc = 0
    best_name = ''
    for name, hist in results.items():
        acc = hist['test_acc'][-1]
        loss = hist['test_loss'][-1]
        params = hist.get('num_params', '?')
        print(f"  {name:<22} | {params:>10} | {acc:10.4f} | {loss:10.4f}")
        if acc > best_acc:
            best_acc = acc
            best_name = name
    
    print(f"\n  Meilleur modele: {best_name} ({best_acc:.4f})")
    
    # Analyse de l'ecart HarmonicConv vs CNN
    cnn_acc = results['CNN']['test_acc'][-1]
    hcn_acc = results['HarmonicConv']['test_acc'][-1]
    ratio = hcn_acc / cnn_acc
    print(f"\n  Ratio HarmonicConv/CNN: {ratio:.2%}")
    
    if hcn_acc > cnn_acc:
        print(f"  >>> L'architecture harmonique SURPASSE le CNN classique! <<<")
    elif ratio >= 0.98:
        print(f"  >>> L'architecture harmonique est COMPETITIVE (ratio >= 98%) <<<")
    else:
        print(f"  Ecart: {cnn_acc - hcn_acc:.4f}")
    
    # Impact du FFT
    if 'CNN_FFT' in results:
        print(f"\n  Impact FFT:")
        print(f"  CNN:       {results['CNN']['test_acc'][-1]:.4f}")
        print(f"  CNN+FFT:   {results['CNN_FFT']['test_acc'][-1]:.4f}")
        print(f"  HConv:     {results['HarmonicConv']['test_acc'][-1]:.4f}")
        print(f"  HConv+FFT: {results['HarmonicConv_FFT']['test_acc'][-1]:.4f}")

    # Conservation rate pour les modeles harmoniques
    if 'conservation_rate' in results['HarmonicConv']:
        cr = np.mean(results['HarmonicConv']['conservation_rate'])
        print(f"\n  G=0 HarmonicConv: {cr:.2%}")
    if 'conservation_rate' in results['HarmonicConv_FFT']:
        cr = np.mean(results['HarmonicConv_FFT']['conservation_rate'])
        print(f"  G=0 HarmonicConv+FFT: {cr:.2%}")

    # Sauvegarde rapport
    report = {}
    for name, hist in results.items():
        report[name] = {
            'final_acc': float(hist['test_acc'][-1]),
            'final_loss': float(hist['test_loss'][-1]),
            'test_acc': [float(x) for x in hist['test_acc']],
            'test_loss': [float(x) for x in hist['test_loss']],
        }
    
    with open('benchmark_avance_mnist.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n  Rapport: benchmark_avance_mnist.json")
    print(f"\n{'='*70}")
    print(f"  FIN")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()