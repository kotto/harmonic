# -*- coding: utf-8 -*-
"""Crée le notebook Kaggle pour l'entraînement HWAT-Med-125M."""
import json

cells = []

cells.append({
    'cell_type': 'markdown',
    'metadata': {},
    'source': [
        '# HWAT-Med-125M - Entraînement GPU Kaggle',
        '',
        'Entraînement du Harmonic Wavelet Attention Transformer (125M params) sur le corpus médical Vital Ka.',
        '',
        '**Pipeline :**',
        '1. Dataset : `alainclmentkotto/hwat-med-125m` (corpus 63.7M chars + tokenizer 50K + script)',
        '2. Entraînement : continued pre-training 100K steps, cosine LR, LoRA-ready',
        '3. Checkpoints : `/kaggle/working/checkpoints/` (auto-sauvegardés toutes les 2000 steps)',
        '',
        'Durée estimée : 60-90h sur P100/T4 - se termine en 2-3 sessions (reprise via checkpoints).'
    ]
})

cells.append({
    'cell_type': 'code',
    'metadata': {},
    'source': [
        'import math, time, random, os, sys, shutil',
        'from pathlib import Path',
        '',
        '# Detection du dataset',
        'DATA_ROOT = Path("/kaggle/input")',
        'PKG = None',
        'for p in DATA_ROOT.glob("*"):',
        '    if p.is_dir() and (p / "tokenizer_medical_50k").exists():',
        '        PKG = p; break',
        'assert PKG is not None, "Dataset hwat-med-125m non attache - verifier l onglet Data"',
        'print("Dataset:", PKG.name)',
        'corpus_size = os.path.getsize(PKG / "data" / "medical_corpus" / "train.txt") / 1e6',
        'print("Corpus: train.txt ({:.1f} MB)".format(corpus_size))',
        '',
        '# Copie du script + import',
        'sys.path.insert(0, str(PKG))',
        'from train_hwat_kaggle import HWATMed, MedicalDataset, load_tokenizer, main',
        'import train_hwat_kaggle as tk',
        '',
        '# Configuration (T4/P100 16GB)',
        'tk.CONFIG.update({',
        '    "train_file": str(PKG / "data" / "medical_corpus" / "train.txt"),',
        '    "val_file": str(PKG / "data" / "medical_corpus" / "val.txt"),',
        '    "tokenizer_path": str(PKG / "tokenizer_medical_50k" / "tokenizer.json"),',
        '    "output_dir": "/kaggle/working/checkpoints/hwat_med_125m",',
        '    "batch_size": 2,          # T4 16GB',
        '    "grad_accum": 16,          # batch effectif = 32',
        '    "seq_len": 256,',
        '    "max_steps": 100000,',
        '    "save_every": 2000,        # checkpoint toutes les 2000 steps',
        '    "eval_every": 500,',
        '    "log_every": 10,',
        '})',
        '',
        'print("Configuration chargee - lancement de l entraînement...")',
        'main()'
    ]
})

nb = {
    'metadata': {
        'kernelspec': {
            'display_name': 'Python 3',
            'language': 'python',
            'name': 'python3'
        },
        'language_info': {
            'name': 'python',
            'version': '3.11.0'
        }
    },
    'nbformat': 4,
    'nbformat_minor': 0,
    'cells': cells
}

with open('kaggle_kernel/hwat_med_125m_train.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print('OK - notebook cree: kaggle_kernel/hwat_med_125m_train.ipynb')
