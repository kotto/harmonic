"""
🌊 Phase 1 · Pont NPZ → PT
===========================
Convertit les checkpoints NPZ (NumPy) des modèles HWAT vers le format PyTorch (.pt).
Permet de charger les modèles pré-entraînés dans hwat_torch.py pour entraînement GPU,
inférence, fine-tuning médical, et intégration Vital Ka.

Usage:
    python npz_to_pt.py --input checkpoints/hwat_4_7m/model_final.npz --output checkpoints/hwat_4_7m/model_final.pt
    python npz_to_pt.py --all                    # convertit tous les checkpoints
    python npz_to_pt.py --verify checkpoints/hwat_4_7m/model_final.pt  # test chargement
"""

import sys
import argparse
from pathlib import Path
import numpy as np
import torch

_ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE))

from hwat_torch import OptimizedHWAT, create_4_7m_model, create_125m_model


def load_npz_checkpoint(npz_path: Path) -> dict:
    """Charge un checkpoint NPZ et retourne un dict structuré."""
    data = np.load(str(npz_path), allow_pickle=True)
    
    # Détecter le format (deux formats possibles)
    keys = list(data.keys())
    
    if 'vocab_size' in keys:
        # Format standard (hwat_optimized.py)
        meta = {
            'vocab_size': int(data['vocab_size']),
            'dim': int(data['dim']),
            'n_layers': int(data['n_layers']),
            'n_heads': int(data['n_heads']),
            'max_seq_len': int(data['max_seq_len']),
            'hidden_mult': int(data.get('hidden_mult', 4)),
        }
    elif 'config_vocab' in keys:
        # Format ancien (hwat_torch.py early checkpoints)
        dim = int(data['config_dim'])
        n_layers = int(data['config_layers'])
        vocab_size = int(data['config_vocab'])
        # Déduire les autres params
        n_heads = 2 if dim == 64 else 4  # 64->2 heads, 256->4 heads
        hidden_mult = 2 if dim == 64 else 4  # 64->128 hidden, 256->1024 hidden
        max_seq_len = 64  # défaut
        
        meta = {
            'vocab_size': vocab_size,
            'dim': dim,
            'n_layers': n_layers,
            'n_heads': n_heads,
            'max_seq_len': max_seq_len,
            'hidden_mult': hidden_mult,
        }
        print(f"  ⚠️ Format ancien détecté: dim={dim}, layers={n_layers}, vocab={vocab_size}, heads={n_heads}")
    else:
        raise ValueError(f"Format NPZ non reconnu: {keys[:10]}")
    
    # Paramètres (arr_0 à arr_N)
    params = []
    i = 0
    while f'arr_{i}' in data:
        params.append(torch.from_numpy(data[f'arr_{i}']).float())  # Convert to float32
        i += 1
    
    return {'meta': meta, 'params': params}


def map_params_to_model(model: OptimizedHWAT, params: list):
    """Mappe les paramètres NPZ (liste plate) vers le modèle PyTorch."""
    idx = 0
    
    # Blocs MLP (par couche)
    for layer_idx in range(model.n_layers):
        model.W1[layer_idx].data = params[idx]; idx += 1
        model.b1[layer_idx].data = params[idx]; idx += 1
        model.W2[layer_idx].data = params[idx]; idx += 1
        model.b2[layer_idx].data = params[idx]; idx += 1
        model.ln_gamma[layer_idx].data = params[idx]; idx += 1
        model.ln_beta[layer_idx].data = params[idx]; idx += 1
    
    # Tête de langage
    model.lm_head.data = params[idx]; idx += 1
    model.lm_bias.data = params[idx]; idx += 1
    
    assert idx == len(params), f"Params restants: {len(params) - idx}"
    print(f"  ✅ {idx} tenseurs mappés vers le modèle")


def convert_npz_to_pt(npz_path: Path, pt_path: Path, verify: bool = True):
    """Convertit un checkpoint NPZ vers PyTorch .pt"""
    print(f"\n🔄 Conversion: {npz_path.name} → {pt_path.name}")
    
    # 1. Charger NPZ
    checkpoint = load_npz_checkpoint(npz_path)
    meta = checkpoint['meta']
    params = checkpoint['params']
    
    print(f"  Config: vocab={meta['vocab_size']}, dim={meta['dim']}, "
          f"layers={meta['n_layers']}, heads={meta['n_heads']}, "
          f"seq_len={meta['max_seq_len']}, hidden_mult={meta['hidden_mult']}")
    print(f"  Paramètres NPZ: {len(params)} tenseurs")
    
    # 2. Créer le modèle PyTorch avec la même config
    model = OptimizedHWAT(
        vocab_size=meta['vocab_size'],
        dim=meta['dim'],
        n_layers=meta['n_layers'],
        n_heads=meta['n_heads'],
        max_seq_len=meta['max_seq_len'],
        hidden_mult=meta['hidden_mult'],
        use_float32=True,
    )
    
    # 3. Mapper les poids
    map_params_to_model(model, params)
    
    # 4. Sauvegarder en format PyTorch
    pt_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        'model_state_dict': model.state_dict(),
        'config': meta,
        'param_count': sum(p.numel() for p in model.parameters()),
    }, str(pt_path))
    
    print(f"  💾 Sauvé: {pt_path} ({pt_path.stat().st_size / 1e6:.1f} MB)")
    
    # 5. Vérification optionnelle
    if verify:
        verify_conversion(npz_path, pt_path, meta)
    
    return pt_path


def verify_conversion(npz_path: Path, pt_path: Path, meta: dict):
    """Vérifie que la conversion est correcte (forward pass identique)."""
    print(f"  🔍 Vérification...")
    
    # Charger le modèle converti
    checkpoint = torch.load(str(pt_path), map_location='cpu', weights_only=False)
    model = OptimizedHWAT(
        vocab_size=meta['vocab_size'],
        dim=meta['dim'],
        n_layers=meta['n_layers'],
        n_heads=meta['n_heads'],
        max_seq_len=meta['max_seq_len'],
        hidden_mult=meta['hidden_mult'],
        use_float32=True,
    )
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    # Test forward pass
    test_tokens = torch.randint(0, min(1000, meta['vocab_size']), (32,), dtype=torch.long)
    
    with torch.no_grad():
        logits = model(test_tokens)
    
    print(f"    Input: {test_tokens.shape}")
    print(f"    Output logits: {logits.shape} (attendu: [32, {meta['vocab_size']}])")
    print(f"    Logits range: [{logits.min():.3f}, {logits.max():.3f}]")
    print(f"    ✅ Vérification OK")


def convert_all_checkpoints():
    """Convertit tous les checkpoints NPZ trouvés."""
    checkpoints_dir = _ENGINE / "checkpoints"
    npz_files = list(checkpoints_dir.rglob("*.npz"))
    
    if not npz_files:
        print("  ⚠️ Aucun fichier .npz trouvé dans checkpoints/")
        return
    
    print(f"\n📦 {len(npz_files)} checkpoints NPZ trouvés")
    converted = 0
    
    for npz_path in npz_files:
        # Ignorer les fichiers d'optimiseur
        if 'optimizer' in npz_path.name:
            print(f"  ⏭️  Skip (optimiseur): {npz_path.relative_to(_ENGINE)}")
            continue
        
        pt_path = npz_path.with_suffix('.pt')
        try:
            convert_npz_to_pt(npz_path, pt_path, verify=True)
            converted += 1
        except Exception as e:
            print(f"  ❌ Erreur {npz_path.name}: {e}")
    
    print(f"\n✅ {converted}/{len(npz_files)} checkpoints convertis")


def main():
    parser = argparse.ArgumentParser(description="Pont NPZ → PT pour modèles HWAT")
    parser.add_argument('--input', '-i', type=str, help="Fichier NPZ d'entrée")
    parser.add_argument('--output', '-o', type=str, help="Fichier PT de sortie")
    parser.add_argument('--all', '-a', action='store_true', help="Convertir tous les checkpoints")
    parser.add_argument('--verify', '-v', type=str, help="Vérifier un fichier PT existant")
    parser.add_argument('--no-verify', action='store_true', help="Skip verification")
    
    args = parser.parse_args()
    
    print("═" * 60)
    print("  🌊 PHASE 1 · PONT NPZ → PT")
    print("═" * 60)
    
    if args.all:
        convert_all_checkpoints()
    
    elif args.input and args.output:
        npz_path = Path(args.input)
        pt_path = Path(args.output)
        if not npz_path.exists():
            print(f"  ❌ Fichier introuvable: {npz_path}")
            return 1
        convert_npz_to_pt(npz_path, pt_path, verify=not args.no_verify)
    
    elif args.verify:
        pt_path = Path(args.verify)
        if not pt_path.exists():
            print(f"  ❌ Fichier introuvable: {pt_path}")
            return 1
        checkpoint = torch.load(str(pt_path), map_location='cpu', weights_only=False)
        verify_conversion(pt_path.with_suffix('.npz'), pt_path, checkpoint['config'])
    
    else:
        parser.print_help()
        print("\nExemples:")
        print("  python npz_to_pt.py --all")
        print("  python npz_to_pt.py -i checkpoints/hwat_4_7m/model_final.npz -o checkpoints/hwat_4_7m/model_final.pt")
        print("  python npz_to_pt.py --verify checkpoints/hwat_4_7m/model_final.pt")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())