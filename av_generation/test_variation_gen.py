#!/usr/bin/env python3
"""Test rapide de generate_variation() — 3 variations + retrieval."""
import sys,os,numpy as np;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8',errors='replace')

from harmonic_photo_retrieval import HarmonicPhotoIndex,HarmonicPhotoRetrieval
from quality_benchmark import compute_q_hf
import hashlib

d=os.path.join(os.path.dirname(__file__),'..','av_generation_output','retrieval')
index=HarmonicPhotoIndex()
data=np.load(os.path.join(d,'photo_index.npz'),allow_pickle=True)
index.entries=list(data['entries']);index.embeddings=list(data['embeddings'])
index._build_faiss()
print(f'Index: {len(index)} photos\n')

engine=HarmonicPhotoRetrieval(index=index)
prompts=['sunset over mountains','forest with river','ocean storm waves','city at night','desert dunes']

for prompt in prompts:
    print(f'Prompt: "{prompt}"')
    
    # Retrieval
    r=engine.retrieve(prompt,top_k=1,style='cosmique')
    img_id=hashlib.sha256(prompt.encode()).hexdigest()[:6]
    r['results'][0]['image'].save(os.path.join(d,f'ret_{img_id}.png'))
    desc=r['results'][0]['description'][:35]
    score=r['results'][0]['score']
    print(f'  Retrieval: score={score:.4f} | {desc}')
    
    # Generation (interférence harmonique)
    g=engine.generate_variation(prompt,n_sources=7,width=512,height=512,
                                 style='cosmique',upscale=None)
    if 'error' not in g:
        g['image'].save(os.path.join(d,f'gen_{img_id}.png'))
        q=compute_q_hf(g['grayscale'])
        print(f'  Generated: emergence={g["emergence_score"]:.1f} | Q_HF={q["q_hf"]:.4f} | LapStd={q["lap_std"]:.4f}')
        print(f'    Sources: {g["sources"][:3]}')
    print()

print('Done. Fichiers dans retrieval/')