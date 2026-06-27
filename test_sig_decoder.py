#!/usr/bin/env python3
"""Test du SignatureDecoder avec import direct."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'harmonic_training'))
import warnings
warnings.filterwarnings('ignore')

import importlib.util as iu
import torch
torch.set_num_threads(4)

def main():
    print("=" * 60)
    print("TEST SIGNATURE DECODER")
    print("=" * 60)

    # Charger modules avec importlib
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

    # Pure model (attention, layers, model)
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

    # Signature Decoder
    spec = iu.spec_from_file_location('harmonic_signature_decoder', os.path.join(mdl, 'harmonic_signature_decoder.py'))
    sd = iu.module_from_spec(spec)
    sys.modules['harmonic_signature_decoder'] = sd
    spec.loader.exec_module(sd)

    print("\nModules charges avec succes.")

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

    decoder = sd.SignatureDecoder(vocab_size=tokenizer.get_vocab_size(), hidden_dim=64)
    print(f"Decoder: {sum(p.numel() for p in decoder.parameters()):,} params")

    # ========= 1. BASELINE : LM HEAD FIXE =========
    print("\n" + "-" * 60)
    print("[1] BASELINE : Generation avec LM Head fixe")
    print("-" * 60)

    all_new_raw = []
    for prompt in ["Le nombre d or", "La conscience est", "Dans l univers"]:
        tokens = tokenizer.encode(prompt)
        inp = torch.tensor([tokens], dtype=torch.long)
        generated = inp.clone()
        with torch.no_grad():
            for _ in range(25):
                logits, _ = model(generated)
                probs = torch.softmax(logits[:, -1, :] / 0.85, dim=-1)
                # top-k 40
                vals, idx = torch.topk(probs, 40, dim=-1)
                probs = torch.zeros_like(probs)
                probs.scatter_(1, idx, vals)
                probs = probs / probs.sum(dim=-1, keepdim=True)
                next_t = torch.multinomial(probs, 1)
                generated = torch.cat([generated, next_t], dim=-1)
                if next_t.item() == 3:
                    break
        text = tokenizer.decode(generated[0].tolist())
        new_ids = generated[0].tolist()[len(tokens):]
        all_new_raw.extend(new_ids)
        print(f"  [{prompt:<20s}] -> {text[:90]}")
        print(f"    {len(new_ids)} tokens, {len(set(new_ids))} uniques ({len(set(new_ids))/len(new_ids):.2f})")
    r1 = len(set(all_new_raw)) / max(len(all_new_raw), 1)
    print(f"  => LM Head Total: {len(set(all_new_raw))}/{len(all_new_raw)} ratio={r1:.3f}")

    # ========= 2. ENTRAINEMENT DECODER =========
    print("\n" + "-" * 60)
    print("[2] ENTRAINEMENT DU SIGNATURE DECODER")
    print("-" * 60)

    num_seqs = 300
    seq_len = 16
    all_sigs, all_tgts = [], []

    t0 = time.time()
    with torch.no_grad():
        for _ in range(num_seqs):
            tokens = torch.randint(1, tokenizer.get_vocab_size() - 1, (1, seq_len))
            _, signatures = model(tokens)
            sigs = signatures[-1, 0]  # [S, 7]
            for pos in range(seq_len - 1):
                all_sigs.append(sigs[pos])
                all_tgts.append(tokens[0, pos + 1])

    X = torch.stack(all_sigs)  # [N, 7]
    Y = torch.tensor(all_tgts)  # [N]
    print(f"Dataset: {X.shape} -> {Y.shape} ({time.time()-t0:.1f}s)")

    opt = torch.optim.AdamW(decoder.parameters(), lr=1e-2, weight_decay=1e-4)
    n = X.shape[0]
    bs = 32

    for ep in range(30):
        total_loss = 0.0
        correct = 0
        perm = torch.randperm(n)
        for i in range(0, n, bs):
            idx = perm[i:i + bs]
            bx, by = X[idx], Y[idx]
            opt.zero_grad()
            logits = decoder(bx)
            loss = torch.nn.functional.cross_entropy(logits, by)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(decoder.parameters(), 1.0)
            opt.step()
            total_loss += loss.item()
            correct += (logits.argmax(dim=-1) == by).sum().item()
        avg_loss = total_loss / (n // bs + 1)
        acc = correct / n
        if (ep + 1) % 10 == 0:
            print(f"  Epoch {ep+1:2d}/30 | Loss: {avg_loss:.4f} | Acc: {acc:.4f} ({acc*100:.1f}%)")

    # ========= 3. GENERATION AVEC DECODER =========
    print("\n" + "-" * 60)
    print("[3] GENERATION AVEC SIGNATURE DECODER")
    print("-" * 60)

    all_new_sd = []
    for prompt in ["Le nombre d or", "La conscience est", "Dans l univers"]:
        tokens = tokenizer.encode(prompt)
        inp = torch.tensor([tokens], dtype=torch.long)
        generated = inp.clone()

        with torch.no_grad():
            for _ in range(25):
                _, signatures = model(generated)
                last_sig = signatures[-1, 0, -1, :]  # [7]
                logits = decoder(last_sig.unsqueeze(0))  # [1, V]
                probs = torch.softmax(logits / 0.85, dim=-1)

                # top-k 40
                vals, idx = torch.topk(probs, 40, dim=-1)
                probs = torch.zeros_like(probs)
                probs.scatter_(1, idx, vals)
                probs = probs / probs.sum(dim=-1, keepdim=True)

                next_t = torch.multinomial(probs, 1)
                generated = torch.cat([generated, next_t], dim=-1)
                if next_t.item() == 3:
                    break

        text = tokenizer.decode(generated[0].tolist())
        new_ids = generated[0].tolist()[len(tokens):]
        all_new_sd.extend(new_ids)
        print(f"  [{prompt:<20s}] -> {text[:90]}")
        print(f"    {len(new_ids)} tokens, {len(set(new_ids))} uniques ({len(set(new_ids))/len(new_ids):.2f})")
    r2 = len(set(all_new_sd)) / max(len(all_new_sd), 1)
    print(f"  => SigDecoder Total: {len(set(all_new_sd))}/{len(all_new_sd)} ratio={r2:.3f}")

    # ========= RESULTATS =========
    print("\n" + "=" * 60)
    print("RESULTATS FINAUX")
    print("=" * 60)
    print(f"  LM Head fixe:        {len(set(all_new_raw))} uniques / {len(all_new_raw)} = {r1:.3f}")
    print(f"  Signature Decoder:   {len(set(all_new_sd))} uniques / {len(all_new_sd)} = {r2:.3f}")
    print(f"  Gain: {r2-r1:+.3f} ({len(set(all_new_sd))-len(set(all_new_raw)):+d} tokens)")
    print(f"\n  Decoder params: {sum(p.numel() for p in decoder.parameters()):,}")
    print(f"  Accuracy finale: {acc*100:.1f}%")
    print("\n[OK] Test termine")

if __name__ == '__main__':
    main()
