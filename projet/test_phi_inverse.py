#!/usr/bin/env python3
"""Test du PhiInverseDecoder (inverse de la derivee ABC) avec import lib direct."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'harmonic_training'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'harmonic_training', 'model'))
import warnings
warnings.filterwarnings('ignore')
import torch
torch.set_num_threads(4)

# Creer le package model proprement
import types
mdl = os.path.join(os.path.dirname(__file__), 'harmonic_training', 'model')
mp = types.ModuleType('model')
mp.__path__ = [mdl]; mp.__package__ = 'model'; mp.__name__ = 'model'
sys.modules['model'] = mp

import importlib.util as iu

def load_mod(name, fn):
    spec = iu.spec_from_file_location(f'model.{name}', os.path.join(mdl, fn))
    mod = iu.module_from_spec(spec)
    mod.__package__ = 'model'
    sys.modules[f'model.{name}'] = mod
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    # Exposer les imports internes
    for k in list(mod.__dict__.keys()):
        if not k.startswith('_'):
            setattr(mp, k, getattr(mod, k))
    return mod

load_mod('abc_kernel', 'abc_kernel.py')
load_mod('tokenizer', 'tokenizer.py')
load_mod('harmonic_pure_attention', 'harmonic_pure_attention.py')
load_mod('harmonic_pure_layers', 'harmonic_pure_layers.py')
load_mod('harmonic_pure_model', 'harmonic_pure_model.py')
load_mod('harmonic_signature_decoder', 'harmonic_signature_decoder.py')

del mp  # nettoyage

print("Modules charges.")

# Maintenant utiliser l'import standard
from model.harmonic_signature_decoder import PhiInversePipeline

pipe = PhiInversePipeline()

print("\n" + "-" * 60)
print("BENCHMARK : LM Head vs PhiInverse")
print("-" * 60)

prompts = ["Le nombre d or", "La conscience est", "Dans l univers",
           "La verite est", "Le sens de la vie"]

for use_inv, label in [(False, "LM Head fixe"), (True, "PhiInverse (inverse ABC)")]:
    all_new = []
    print(f"\n--- {label} ---")
    for p in prompts:
        t0 = time.time()
        text, info = pipe.generate(p, max_new=20, use_inverse=use_inv,
                                    temperature=0.85, top_k=30)
        dt = time.time() - t0
        new_ids = pipe.tokenizer.encode(text)[len(pipe.tokenizer.encode(p)):]
        uniq = len(set(new_ids))
        all_new.extend(new_ids)
        print(f"  [{p:<20s}] -> {text[:80]:.80s}")
        print(f"    {len(new_ids)} t, {uniq} u ({uniq/max(len(new_ids),1):.2f}) en {dt:.1f}s")
    tu = len(set(all_new)); tn = len(all_new)
    print(f"  [{label}] {tu}/{tn} = {tu/max(tn,1):.3f}")

print("\n[OK] Test termine")
