#!/usr/bin/env python3
"""Test rapide du sampler corrige (hologrammes apparies)."""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from coefficient_sampler import SVDCorpus, CoefficientSampler, PhotorealisticGenerator
from quality_benchmark import compute_q_hf

d = os.path.join(os.path.dirname(__file__), '..', 'av_generation_output', 'photorealistic')

corpus = SVDCorpus()
corpus.load(os.path.join(d, 'svd_corpus.npz'))
print(f"Corpus: {len(corpus)} signatures")

sampler = CoefficientSampler(corpus)
sampler.load(os.path.join(d, 'coefficient_model.pkl'))
print(f"X_latent: {sampler.X_latent.shape}")
print(f"GMM: {sampler.gmm.n_components} composantes, PCA: {sampler.pca.n_components_}d")

gen = PhotorealisticGenerator(sampler=sampler, detail_strength=1.0)

print("\nGeneration de 5 images (hologrammes apparies au corpus)...")
qhf_vals = []
for i in range(5):
    style = ['cosmique', 'solaire', 'forest', 'ocean', 'aurore'][i]
    r = gen.generate(width=512, height=512, style=style, seed=42 + i * 137)
    r['image'].save(os.path.join(d, f'gen_paired_{i+1:02d}.png'))
    q = compute_q_hf(r['grayscale'])
    qhf_vals.append(q['q_hf'])
    print(f"  [{i+1}] {style:<10s} | Q_HF={q['q_hf']:.4f} | LapStd={q['lap_std']:.4f}")

print(f"\nQ_HF moyen: {np.mean(qhf_vals):.4f}")
print(f"Fichiers dans: {d}/")