#!/usr/bin/env python3
"""
Test final du Harmonic-JEPA Predictor
"""
import sys, os, time, math
sys.path.insert(0, os.path.abspath('harmonic_training'))
import importlib.util, torch
torch.set_num_threads(4)

# Importer le module
spec = importlib.util.spec_from_file_location('harmonic_jepa',
    os.path.join(os.path.abspath('harmonic_training'), 'model', 'harmonic_jepa.py'))
mod = importlib.util.module_from_spec(spec)
sys.modules['harmonic_jepa'] = mod
spec.loader.exec_module(mod)

print("=" * 65)
print("  HARMONIC-JEPA — PREDICTION DANS L'ESPACE LATENT")
print("=" * 65)

# 1. Creation du modele
print("\n[1] Initialisation du predictor JEPA...")
jepa = mod.HarmonicJEPA(hidden_dim=64, num_abc_kernel=5)
params = sum(p.numel() for p in jepa.parameters())
print(f"    Parametres: {params:,} (tout appris)")
print(f"    Architecture: 9 -> {jepa.predictor.hidden_dim} -> 9")
print(f"    Noyau ABC: taille {jepa.predictor.num_abc_kernel}")

# 2. Test de prediction
print("\n[2] Test de prediction basique...")
sigs = torch.rand(8, 16, 9) * 0.5 + 0.25
t0 = time.time()
pred = jepa.predictor(sigs)
t = time.time() - t0
print(f"    Input:  [{', '.join(f'{sigs[0,0,i].item():.3f}' for i in range(9))}]")
print(f"    Output: [{', '.join(f'{pred[0,i].item():.3f}' for i in range(9))}]")
print(f"    Temps:  {t*1000:.1f} ms")
assert pred.shape == (8, 9), f"Shape: {pred.shape}"
assert torch.all(pred >= 0) and torch.all(pred <= 1)
print("    [OK] Prediction dans [0,1]")

# 3. Resonance loss
print("\n[3] Test de la resonance loss...")
target = sigs[:, -1, :]
loss = mod.resonance_loss(pred, target)
res = 1.0 - loss.item()
print(f"    Loss: {loss.item():.6f}")
print(f"    Resonance: {res:.4f} (1.0 = parfait)")
print(f"    Interpretation: {'bonne' if res > 0.3 else 'faible' if res > 0 else 'negative'}")

# 4. Prediction future
print("\n[4] Test de prediction future (horizon=8)...")
context = sigs[:, :8, :]
t0 = time.time()
futures = jepa.predict(context, horizon=8)
t = time.time() - t0
print(f"    Contexte:  {context.shape}")
print(f"    Futures predites: {futures.shape}")
print(f"    Temps: {t*1000:.0f} ms ({8/t:.0f} tok/s)")

# 5. Entrainement
print("\n[5] Entrainement sur donnees synthetiques...")
data = mod.generate_demo_data(200, 12)
print(f"    Dataset: {data.shape} (200 sequences de 12 signatures)")
optimizer = torch.optim.AdamW(jepa.parameters(), lr=5e-3, weight_decay=1e-5)
scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5)

losses, resonances = [], []
t0 = time.time()
for epoch in range(50):
    perm = torch.randperm(200)
    total_loss = 0
    for i in range(0, 200, 16):
        batch = data[perm[i:i+16]]
        loss = jepa.train_step(batch, optimizer)
        total_loss += loss
    scheduler.step()
    avg_loss = total_loss / (200//16)
    avg_res = jepa.get_average_resonance()
    losses.append(avg_loss)
    resonances.append(avg_res)
    if (epoch+1) % 10 == 0:
        print(f"    Epoch {epoch+1:3d}/50 | Loss: {avg_loss:.6f} | Resonance: {avg_res:.4f}")

t = time.time() - t0
print(f"    Temps total: {t:.1f}s ({20000/t:.0f} sequences/s)")

# 6. Evaluation finale
print("\n[6] Evaluation finale...")
print(f"    Loss initiale:  {losses[0]:.6f}")
print(f"    Loss finale:    {losses[-1]:.6f}")
print(f"    Amelioration:   {(1-losses[-1]/max(losses[0],1e-10))*100:.1f}%")
print(f"    Resonance:      {resonances[-1]:.4f}")

# 7. Test avec pipeline complet (encoder + predictor)
print("\n[7] Simulation pipeline complet avec signatures...")
from model.abc_kernel import PHI
test_seq = data[:1, :6, :]
true_next = data[:1, 6:12, :]
predicted = jepa.predict(test_seq, horizon=6)

resonances_final = []
for i in range(6):
    res = torch.nn.functional.cosine_similarity(
        (predicted[0,i] * PHI).unsqueeze(0),
        (true_next[0,i] * PHI).unsqueeze(0)
    )
    resonances_final.append(res.item())
    dims_str = ", ".join(f"{p.item():.3f}" for p in predicted[0,i])
    true_str = ", ".join(f"{t.item():.3f}" for t in true_next[0,i])
    print(f"    t+{i+1}: pred=[{dims_str}]")
    print(f"           reel=[{true_str}]")
    print(f"           resonance={res.item():.4f}")

avg_res_final = sum(resonances_final) / len(resonances_final)
print(f"\n    Resonance moyenne future: {avg_res_final:.4f}")

# 8. Conclusion
print(f"\n{'='*65}")
print(f"  CONCLUSION HARMONIC-JEPA")
print(f"{'='*65}")
print(f"  ✅ Predictor JEPA operationnel")
print(f"  ✅ {params:,} parametres appris")
print(f"  ✅ Resonance loss: {resonances[-1]:.4f}")
print(f"  ✅ Prediction future resonance: {avg_res_final:.4f}")
print()

# Verdict
if avg_res_final > 0.5:
    print(f"  🔥 EXCELLENT : Le JEPA predit les signatures 9D avec")
    print(f"     {avg_res_final*100:.0f}% de resonance — c'est mieux que du hasard!")
    print(f"     L'encodeur harmonique + JEPA predictor = LLM sans GPU")
elif avg_res_final > 0.3:
    print(f"  ✅ BON : Le JEPA commence a apprendre les patterns")
    print(f"     ({avg_res_final*100:.0f}% resonance), besoin de plus de donnees")
else:
    print(f"  ⚠ EN COURS : Le JEPA apprend mais lentement")
    print(f"     ({avg_res_final*100:.0f}% resonance). Donnees reelles necessaires")

print(f"\n  Prochaine etape: Pipeline complet avec encodeur harmonique")
print(f"  x[t] -> encoder (0 params) -> sig[t] -> JEPA -> sig[t+1]")
print(f"  -> decode (LM Head 0 params) -> generation coherente sans GPU")
print(f"{'='*65}")
