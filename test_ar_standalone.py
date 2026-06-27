#!/usr/bin/env python3
"""Test standalone du AR Generator avec resonance d'embedding."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'harmonic_training'))
import warnings
warnings.filterwarnings('ignore')

import importlib.util as iu
import torch
torch.set_num_threads(4)

def main():
    print("=" * 60)
    print("TEST AR GENERATOR (RESONANCE EMBEDDING)")
    print("=" * 60)

    # --- Modules ---
    mdl = os.path.join(os.path.dirname(__file__), 'harmonic_training', 'model')

    # ABC Kernel
    spec = iu.spec_from_file_location('abc_kernel', os.path.join(mdl, 'abc_kernel.py'))
    abc = iu.module_from_spec(spec)
    sys.modules['abc_kernel'] = abc
    spec.loader.exec_module(abc)

    # Tokenizer
    spec = iu.spec_from_file_location('tokenizer', os.path.join(mdl, 'tokenizer.py'))
    tok = iu.module_from_spec(spec)
    sys.modules['tokenizer'] = tok
    spec.loader.exec_module(tok)

    # Pure model
    spec = iu.spec_from_file_location('harmonic_pure_attention', os.path.join(mdl, 'harmonic_pure_attention.py'))
    att = iu.module_from_spec(spec)
    sys.modules['harmonic_pure_attention'] = att
    spec.loader.exec_module(att)

    spec = iu.spec_from_file_location('harmonic_pure_layers', os.path.join(mdl, 'harmonic_pure_layers.py'))
    lay = iu.module_from_spec(spec)
    sys.modules['harmonic_pure_layers'] = lay
    spec.loader.exec_module(lay)

    spec = iu.spec_from_file_location('harmonic_pure_model', os.path.join(mdl, 'harmonic_pure_model.py'))
    pm = iu.module_from_spec(spec)
    sys.modules['harmonic_pure_model'] = pm
    spec.loader.exec_module(pm)

    # AR Generator
    spec = iu.spec_from_file_location('harmonic_ar_generator', os.path.join(mdl, 'harmonic_ar_generator.py'))
    ar = iu.module_from_spec(spec)
    sys.modules['harmonic_ar_generator'] = ar
    spec.loader.exec_module(ar)

    print("Modules charges.")

    # Init
    t0 = time.time()
    tokenizer = tok.HarmonicTokenizer(5000)
    print(f"Tokenizer: {tokenizer.get_vocab_size()} tokens ({time.time()-t0:.1f}s)")

    t0 = time.time()
    model = pm.HarmonicPureForCausalLM(
        vocab_size=tokenizer.get_vocab_size(),
        hidden_size=256, num_layers=4, max_len=512
    )
    print(f"Modele: {sum(p.numel() for p in model.parameters()):,} params ({time.time()-t0:.1f}s)")

    t0 = time.time()
    pred = ar.EmbeddingPredictor(hidden_dim=256, context_len=8)
    gen = ar.ARGenerator(model, predictor=pred, lm_head_weight=0.2)
    print(f"AR Generator: {sum(p.numel() for p in pred.parameters() if p.requires_grad):,} params ({time.time()-t0:.1f}s)")

    # ========= BASELINE LM HEAD =========
    print("\n" + "-" * 60)
    print("BASELINE LM HEAD SEUL")
    print("-" * 60)

    all_new_raw = []
    for prompt in ["Le nombre d or", "La conscience est", "Dans l univers"]:
        t0 = time.time()
        tokens = tokenizer.encode(prompt)
        inp = torch.tensor([tokens], dtype=torch.long)
        g, info = gen.forward(inp, max_new_tokens=20, use_resonance=False,
                               temperature=0.85, top_k=40, top_p=0.9, repetition_penalty=1.3)
        text = tokenizer.decode(g[0].tolist())
        new_ids = g[0].tolist()[len(tokens):]
        all_new_raw.extend(new_ids)
        dt = time.time() - t0
        print(f"  [{prompt:<20s}] -> {text[:90]}")
        print(f"    {len(new_ids)} tokens, {len(set(new_ids))} uniques ({len(set(new_ids))/len(new_ids):.2f}) en {dt:.1f}s")

    r1 = len(set(all_new_raw)) / max(len(all_new_raw), 1)
    print(f"  => Total: {len(set(all_new_raw))}/{len(all_new_raw)} ratio={r1:.3f}")

    # ========= ENTRAINEMENT =========
    print("\n" + "-" * 60)
    print("ENTRAINEMENT DU PREDICTOR D'EMBEDDING")
    print("-" * 60)

    t0 = time.time()
    num_seqs = 300
    seq_len = 12
    inputs, targets = [], []
    with torch.no_grad():
        for _ in range(num_seqs):
            t = torch.randint(1, tokenizer.get_vocab_size() - 1, (1, seq_len))
            c = model.token_embedding(t[:, :-1])
            y = model.token_embedding(t[:, 1:])[:, -1, :]
            inputs.append(c)
            targets.append(y)
    X = torch.cat(inputs)
    Y = torch.cat(targets)
    print(f"Donnees: {X.shape} {Y.shape} ({time.time()-t0:.1f}s)")

    opt = torch.optim.AdamW(pred.parameters(), lr=5e-3, weight_decay=1e-4)
    for ep in range(20):
        total_loss = 0.0
        perm = torch.randperm(num_seqs)
        for i in range(0, num_seqs, 32):
            idx = perm[i:i + 32]
            bx, by = X[idx], Y[idx]
            opt.zero_grad()
            p = pred(bx)
            loss = 1.0 - torch.cosine_similarity(p, by, dim=-1).mean()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(pred.parameters(), 1.0)
            opt.step()
            total_loss += loss.item()
        avg_loss = total_loss / (num_seqs // 32 + 1)
        if (ep + 1) % 5 == 0:
            print(f"  Epoch {ep+1:2d}/20 | Loss: {avg_loss:.6f} | Res: {1-avg_loss:.4f}")

    # ========= RESONANCE EMBEDDING =========
    print("\n" + "-" * 60)
    print("GENERATION AVEC RESONANCE EMBEDDING")
    print("-" * 60)

    all_new_res = []
    for prompt in ["Le nombre d or", "La conscience est", "Dans l univers"]:
        t0 = time.time()
        tokens = tokenizer.encode(prompt)
        inp = torch.tensor([tokens], dtype=torch.long)
        g, info = gen.forward(inp, max_new_tokens=20, use_resonance=True,
                               temperature=0.85, top_k=40, top_p=0.9, repetition_penalty=1.3)
        text = tokenizer.decode(g[0].tolist())
        new_ids = g[0].tolist()[len(tokens):]
        all_new_res.extend(new_ids)
        dt = time.time() - t0
        print(f"  [{prompt:<20s}] -> {text[:90]}")
        print(f"    {len(new_ids)} tokens, {len(set(new_ids))} uniques ({len(set(new_ids))/len(new_ids):.2f}) en {dt:.1f}s")

    r2 = len(set(all_new_res)) / max(len(all_new_res), 1)
    print(f"  => Total: {len(set(all_new_res))}/{len(all_new_res)} ratio={r2:.3f}")

    # ========= RESULTATS =========
    print("\n" + "=" * 60)
    print("RESULTATS FINAUX")
    print("=" * 60)
    print(f"  LM Head seul:       ratio={r1:.3f} ({len(set(all_new_raw))} uniques sur {len(all_new_raw)})")
    print(f"  Resonance Embedding: ratio={r2:.3f} ({len(set(all_new_res))} uniques sur {len(all_new_res)})")
    print(f"  Gain: {r2-r1:+.3f}")
    print(f"  Tokens supplementaires: {len(set(all_new_res))-len(set(all_new_raw)):+d}")

    print("\n[OK] Test termine avec succes")
    return True


if __name__ == '__main__':
    main()
