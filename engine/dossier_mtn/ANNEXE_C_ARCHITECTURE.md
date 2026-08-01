# ANNEXE C — Architecture HWAT (référence technique)

## C.1 Vue d'ensemble

```
┌────────────────────────────────────────────────────────────┐
│                     HWAT (wavelet attention)                │
│                                                            │
│  token_ids ──▶ ψ = A·e^{iφ} ──▶ [Bloc Attention]×N ──▶ logits │
│                     │                     │                │
│                     │                     │                │
│  A : FNV-1a hash    │      cos(φi-φj)     │                │
│  φ : φ-spaced pos   │      + amplitude    │                │
└────────────────────────────────────────────────────────────┘
```

## C.2 Implémentation de référence

**Fichier :** `hwat_torch.py` (458 lignes) — modèle PyTorch

### Embedding déterministe (aucun stockage)
```python
def _fnv1a(s: str) -> int:
    h = 2166136261
    for ch in s.encode('utf-8'):
        h ^= ch; h = (h * 16777619) & 0xFFFFFFFF
    return h

# À la construction : A_tab[token] et phi_tok[token] calculés par hash
# À l'inférence : regenerés par la même formule → 0 octet stocké
def embed(self, token_ids):
    A = self.A_table[token_ids]          # amplitude (hash déterministe)
    phi_t = self.phi_token[token_ids]    # phase lexicale
    phi_p = self.phi_pos[:L]             # phase positionnelle (φ-spacée)
    return A * (cos(phi) + i·sin(phi))   # onde complexe
```

### Attention par cohérence de phase (pas de QK^T appris)
```python
def phase_attention_fast(psi, n_heads, causal=True):
    # Amplitude & phase
    A = heads.abs(); phi = heads.angle()
    cos_phi, sin_phi = cos(phi), sin(phi)
    # Phase coherence : cos(φᵢ−φⱼ) = cosφᵢcosφⱼ + sinφᵢsinφⱼ
    phase_scores = (cos_phi @ cos_phi.T + sin_phi @ sin_phi.T) / head_dim
    # Modulation d'amplitude
    amp_scores = sqrt(A_norm_sq[:, None] * A_norm_sq[None, :])
    scores = phase_scores * amp_scores
    # Causality mask + softmax
    return attn @ heads
```

### MLP sur l'amplitude (phase préservée)
```python
def mlp_fast(psi, W1, W2):
    A = psi.abs(); phase = psi.angle()
    h = relu(A @ W1 + b1)
    A_new = h @ W2 + b2
    return A_new · e^{i·phase}   # la phase traverse intacte
```

## C.3 Configurations implémentées

| Modèle | Dim | Couches | Têtes | Vocab | Paramètres | Fichier |
|--------|-----|---------|-------|-------|-----------|---------|
| HWAT small | 256 | 4 | 4 | 5K | 4.7M | `train_hwat_small.py` |
| HWAT scaled | 512 | 8 | 8 | 32K | 22.4M | `train_hwat_scaled.py` |
| HWAT 125M (cible) | 1024 | 12 | 16 | 50K | ~125M | `train_hwat_kaggle.py` |
| Hologrammes | 32 | 1 | 2 | ~2.5K | ~100K | `train_medical_holograms.py` |
| Holographic Trainer | 384 | — | — | — | — | `holographic_trainer.py` |

## C.4 Le routeur spectral

```python
class HologramRouter:
    def route(query, top_k):
        # Similarité cosinus entre tokens de la requête
        # et vocabulaire de chaque domaine
        scores = {domaine: match(requête, vocab_domaine)}
        return top_k domaines

    def retrieve_facts(domaine, requête, top_k):
        # Retrieval par index inversé sur les faits du domaine
        return faits avec score
```

**Résultat :** une requête → top domaines → faits pertinents en <12 ms, sans GPU.

## C.5 Pipeline d'entraînement (état actuel)

| Étape | Script | État |
|-------|--------|------|
| Conversion NPZ→PT | `npz_to_pt.py` | ✅ 18 checkpoints |
| Tokenizer médical BPE 50K | `train_medical_tokenizer.py` | ✅ 50K vocab |
| Corpus médical 63.7M chars | `prepare_medical_corpus.py` | ✅ 132K segments |
| Hologrammes médicaux | `train_medical_holograms.py` | ✅ 15 domaines, 2.6 min |
| HWAT-Med-125M GPU | `train_hwat_kaggle.py` | 🟢 en cours (Kaggle GPU) |
| API inférence | `inference_server.py` | ✅ FastAPI 6 endpoints |

---

*Annexe C — DOSSIER TECHNIQUE MTN v1.0 — 2026-08-01*
