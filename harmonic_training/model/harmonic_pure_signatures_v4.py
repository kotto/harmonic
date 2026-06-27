"""
Signatures Harmoniques 9D — Version 4 (Robuste)
=================================================
Version robuste adaptee aux vrais embeddings harmoniques.

Probleme identifie dans V3 :
- Les formules produisent des valeurs tres negatives sur les vrais embeddings
- La calibration ne peut pas compenser des formules inadaptees

Solution V4 :
- Chaque formule est concue pour produire naturellement des valeurs dans [0,1]
- Utilisation de normalisations internes (softmax, tanh, sigmoid integres)
- Pas de calibration externe necessaire

Les 9 dimensions :
1. phi        : entropie normalisee (toujours dans [0,1])
2. alpha      : rugosite fractale (bassee sur ratios, pas de log)
3. reasoning  : similarite cosinus moyenne (deja dans [-1,1])
4. creativity : variance de la matrice de similarite
5. math       : periodicite detectee par FFT locale
6. factual    : norme relative + confiance softmax
7. code       : ratio basse/haute frequence avec sigmoid
8. emotion    : asymetrie de la distribution des activations
9. temporal   : variation temporelle normalisee
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =========================================================================
# FONCTIONS V4 — Chaque fonction produit des valeurs dans [0,1]
# =========================================================================

def compute_phi_v4(hidden_states):
    """
    phi v4 : entropie normalisee robuste.
    
    Formule : phi = 1 - max(softmax(x))  (complement du max de probabilite)
    
    - Si un token domine → phi ~ 0 (peu de diversite)
    - Si tous les tokens sont equiprobables → phi ~ 1
    
    Garantie : phi ∈ [0, 1] car softmax produit des probabilites.
    """
    d = hidden_states.shape[-1]
    tau = math.sqrt(d)
    p = F.softmax(hidden_states / tau, dim=-1)
    max_p = p.max(dim=-1, keepdim=True)[0]
    # phi = 1 - max_p : si max_p=1 (deterministe) → phi=0
    # si max_p=1/d (uniforme) → phi ≈ 1
    phi = 1.0 - max_p
    return phi


def compute_alpha_v4(hidden_states):
    """
    alpha v4 : rugosite fractale robuste.
    
    Formule : alpha = 1 - cos(x_i, x_{i+lag}) moyenne sur plusieurs lag
    
    - Si la sequence est tres reguliere → alpha ~ 0 (faible complexite)
    - Si la sequence est chaotique → alpha ~ 1 (haute complexite)
    
    Garantie : alpha ∈ [0, 1] car cos ∈ [-1, 1] et on prend 1 - cos.
    """
    x_norm = F.normalize(hidden_states, dim=-1)
    
    # Similarite a differentes echelles
    rugosites = []
    for lag in [1, 2, 3]:
        if lag >= hidden_states.shape[1]:
            continue
        # cos(x_i, x_{i+lag})
        cos_lag = (x_norm[:, :-lag] * x_norm[:, lag:]).sum(dim=-1, keepdim=True)
        cos_lag = F.pad(cos_lag, (0, 0, 0, lag))
        # 1 - cos donne la rugosite (0 = parfaitement lisse, 2 = maximal)
        rug = 1.0 - cos_lag
        rugosites.append(rug)
    
    if rugosites:
        alpha = torch.stack(rugosites, dim=-1).mean(dim=-1)
    else:
        alpha = torch.zeros_like(hidden_states[..., :1])
    
    # Normalisation : 1 - cos ∈ [0, 2], on ramene dans [0, 1]
    alpha = alpha / 2.0
    
    return alpha


def compute_reasoning_v4(hidden_states):
    """
    reasoning v4 : coherence causale normalisee.
    
    Formule : R = (cos(x_i, x_{i+1}) + 1) / 2
    
    - Si les tokens s'enchainent logiquement → R ~ 1
    - Si les tokens sont incoherents → R ~ 0
    
    Garantie : R ∈ [0, 1] car cos ∈ [-1, 1] → (cos+1)/2 ∈ [0, 1].
    """
    x_norm = F.normalize(hidden_states, dim=-1)
    cos_sim = (x_norm[:, :-1] * x_norm[:, 1:]).sum(dim=-1, keepdim=True)
    cos_sim = F.pad(cos_sim, (0, 0, 0, 1))
    # (cos + 1) / 2 ∈ [0, 1]
    reasoning = (cos_sim + 1.0) / 2.0
    return reasoning


def compute_creativity_v4(hidden_states):
    """
    creativity v4 : divergence semantique normalisee.
    
    Formule : C = 1 - max_{j!=i} (cos(x_i, x_j) + 1) / 2
    
    - Si chaque token est unique → C ~ 1
    - Si les tokens se repetent → C ~ 0
    
    Garantie : C ∈ [0, 1] car cos ∈ [-1, 1].
    """
    batch, seq_len, _ = hidden_states.shape
    x_norm = F.normalize(hidden_states, dim=-1)
    sim_matrix = torch.bmm(x_norm, x_norm.transpose(1, 2))
    # Normaliser dans [0, 1]
    sim_matrix = (sim_matrix + 1.0) / 2.0
    # Masquer la diagonale
    mask = torch.eye(seq_len, device=hidden_states.device).unsqueeze(0)
    sim_matrix = sim_matrix * (1.0 - mask)
    # Similarite maximale avec un autre token
    max_sim = sim_matrix.max(dim=-1)[0].unsqueeze(-1)
    # Divergence
    creativity = 1.0 - max_sim
    return creativity


def compute_math_v4(hidden_states):
    """
    math v4 : precision numerique basee sur la periodicite.
    
    Formule : M = max(autocorrelation(x, lag)) pour lag > 0
    
    - Si le texte a une structure periodique → M ~ 1
    - Si le texte est aleatoire → M ~ 0
    
    Garantie : M ∈ [0, 1] car autocorrelation normalisee.
    """
    x_norm = F.normalize(hidden_states, dim=-1)
    
    # Autocorrelation a differents lags
    autocorrs = []
    for lag in [1, 2, 3, 4]:
        if lag >= hidden_states.shape[1]:
            continue
        shifted = F.pad(x_norm[:, :-lag], (0, 0, lag, 0))
        ac = (x_norm * shifted).sum(dim=-1, keepdim=True)
        autocorrs.append(ac)
    
    if autocorrs:
        # Prendre le max des autocorrelations (hors lag=0)
        math_val = torch.stack(autocorrs, dim=-1).max(dim=-1)[0]
    else:
        math_val = torch.zeros_like(hidden_states[..., :1])
    
    # Normaliser dans [0, 1]
    math_val = (math_val + 1.0) / 2.0
    
    return math_val


def compute_factual_v4(hidden_states):
    """
    factual v4 : ancrage factuel base sur la stabilite.
    
    Formule : F = 1 - variance(softmax(x)) normalisee
    
    - Si le modele est sur de lui → F ~ 1
    - Si le modele hesite → F ~ 0
    
    Garantie : F ∈ [0, 1] car base sur des probabilites.
    """
    d = hidden_states.shape[-1]
    p = F.softmax(hidden_states / math.sqrt(d), dim=-1)
    
    # Variance de la distribution de probabilite
    # Si p est concentree (sur) → variance faible → factual eleve
    # Si p est etalee (incertain) → variance elevee → factual faible
    var_p = p.var(dim=-1, keepdim=True)
    
    # Normalisation : var_max = (1 - 1/d)^2 / 4 approx 0.25 pour d grand
    var_max = 0.25
    factual = 1.0 - torch.clamp(var_p / var_max, 0.0, 1.0)
    
    return factual


def compute_code_v4(hidden_states):
    """
    code v4 : structure hierarchique par analyse frequentielle.
    
    Formule : C = sigmoid(ratio_basses_frequences - 1)
    
    - Si le texte a une structure hierarchique → C ~ 1
    - Si le texte est plat → C ~ 0
    
    Garantie : C ∈ [0, 1] car sigmoid.
    """
    hidden = hidden_states
    
    # Filtre moyenneur (basses frequences)
    low_freq = torch.zeros_like(hidden)
    if hidden.shape[1] >= 3:
        low_freq[:, 1:-1, :] = (hidden[:, :-2, :] + 2 * hidden[:, 1:-1, :] + hidden[:, 2:, :]) / 4.0
    low_freq[:, 0, :] = (2 * hidden[:, 0, :] + hidden[:, 1, :]) / 3.0 if hidden.shape[1] > 1 else hidden[:, 0, :]
    if hidden.shape[1] > 1:
        low_freq[:, -1, :] = (hidden[:, -2, :] + 2 * hidden[:, -1, :]) / 3.0
    
    high_freq = hidden - low_freq
    
    low_norm = torch.norm(low_freq, dim=-1, keepdim=True)
    high_norm = torch.norm(high_freq, dim=-1, keepdim=True)
    
    ratio = low_norm / (high_norm + 1e-8)
    
    # sigmoid(ratio - 1) : si ratio > 1 (plus de basses freq) → code eleve
    code = torch.sigmoid(ratio - 1.0)
    
    return code


def compute_emotion_v4(hidden_states):
    """
    emotion v4 : charge emotionnelle basee sur l'asymetrie.
    
    Formule : E = tanh(|skewness(x)|) * (1 - kurtosis_exces)
    
    - Si le texte est emotionnel → E ~ 1
    - Si le texte est neutre → E ~ 0
    
    Garantie : E ∈ [0, 1] car tanh ∈ [0, 1] et produit de termes dans [0,1].
    """
    # Centrer
    mean = hidden_states.mean(dim=1, keepdim=True)
    x_centre = hidden_states - mean
    
    # Skewness normalise (asymetrie)
    m2 = (x_centre ** 2).mean(dim=-1, keepdim=True)
    m3 = (x_centre ** 3).mean(dim=-1, keepdim=True)
    skewness = m3 / (m2 ** 1.5 + 1e-8)
    
    # Kurtosis (pic) - normalise
    m4 = (x_centre ** 4).mean(dim=-1, keepdim=True)
    kurtosis = m4 / (m2 ** 2 + 1e-8) - 3.0  # exces de kurtosis
    
    # Emotion = |skewness| normalise * (1 - |kurtosis| normalise)
    # skewness eleve → distribution asymetrique → emotion
    # kurtosis eleve → distribution piquee → moins d'emotion (plus technique)
    skew_norm = torch.tanh(torch.abs(skewness))
    kurt_norm = torch.sigmoid(kurtosis)  # dans [0, 1]
    
    emotion = skew_norm * (1.0 - 0.5 * kurt_norm)
    
    return emotion


def compute_temporal_v4(hidden_states):
    """
    temporal v4 : ancrage temporel base sur la variation.
    
    Formule : T = 1 - cos(x_i, x_{i+1}) moyenne
    
    - Si le texte a une direction temporelle → T ~ 1
    - Si le texte est statique → T ~ 0
    
    Garantie : T ∈ [0, 1] car 1 - cos ∈ [0, 2] et on normalise.
    """
    x_norm = F.normalize(hidden_states, dim=-1)
    
    # Gradient cosinus entre tokens consecutifs
    cos_sim = (x_norm[:, :-1] * x_norm[:, 1:]).sum(dim=-1, keepdim=True)
    cos_sim = F.pad(cos_sim, (0, 0, 0, 1))
    
    # 1 - cos : variation entre tokens
    # Si les tokens sont tres similaires → variation faible → temporal faible
    # Si les tokens changent → variation elevee → temporal eleve
    variation = 1.0 - cos_sim
    
    # Normaliser dans [0, 1]
    temporal = variation / 2.0
    
    return temporal


# =========================================================================
# PROJECTION DE SIGNATURE V4
# =========================================================================

class PureSignatureProjectionV4(nn.Module):
    """
    Projection de signature 9D — Version 4 Robuste.
    
    Caracteristiques :
    - 9 dimensions avec formules auto-normalisees dans [0,1]
    - Pas de calibration externe necessaire
    - Robuste aux vrais embeddings harmoniques
    - ZERO parametre entrainable
    """
    
    def __init__(self):
        super().__init__()
    
    def forward(self, hidden_states):
        """
        Calcule les signatures 9D.
        
        Args:
            hidden_states: [batch, seq_len, hidden_size]
        
        Returns:
            signatures: [batch, seq_len, 9]
        """
        phi = compute_phi_v4(hidden_states)
        alpha = compute_alpha_v4(hidden_states)
        reasoning = compute_reasoning_v4(hidden_states)
        creativity = compute_creativity_v4(hidden_states)
        math_val = compute_math_v4(hidden_states)
        factual = compute_factual_v4(hidden_states)
        code = compute_code_v4(hidden_states)
        emotion = compute_emotion_v4(hidden_states)
        temporal = compute_temporal_v4(hidden_states)
        
        signatures = torch.cat([
            phi, alpha, reasoning, creativity, math_val, factual, code,
            emotion, temporal
        ], dim=-1)
        
        return signatures


# =========================================================================
# VALIDATION SUR VRAIS EMBEDDINGS
# =========================================================================

def get_vrais_embeddings(phrases, hidden_size=512):
    """Genere des embeddings harmoniques fixes."""
    from model.harmonic_pure_model import HarmonicFixedEmbedding
    
    all_tokens = []
    max_len = 0
    for phrase in phrases:
        tokens = phrase.lower().split()
        all_tokens.append(tokens)
        max_len = max(max_len, len(tokens))
    
    vocab = {}
    for tokens in all_tokens:
        for t in tokens:
            if t not in vocab:
                vocab[t] = len(vocab)
    
    vocab_size = len(vocab) + 10
    embedding = HarmonicFixedEmbedding(vocab_size, hidden_size)
    
    batch = len(phrases)
    input_ids = torch.zeros(batch, max_len, dtype=torch.long)
    for i, tokens in enumerate(all_tokens):
        for j, t in enumerate(tokens):
            input_ids[i, j] = vocab.get(t, 0)
    
    with torch.no_grad():
        hidden_states = embedding(input_ids)
    
    return hidden_states, all_tokens


# =========================================================================
# DEMONSTRATION V4
# =========================================================================

def demo_v4():
    """Demonstration complete de la version 4 robuste."""
    print("=" * 70)
    print("DEMONSTRATION : Signatures Harmoniques 9D — Version 4 Robuste")
    print("=" * 70)
    
    phrases = [
        "2 + 2 = 4",
        "La Terre est ronde",
        "Imagine un dragon violet qui danse le tango",
        "if x > 0: return x + 1 else: return 0",
        "Je pense donc je suis",
        "Le chat est sur le tapis",
        "Pour tout epsilon > 0 il existe delta > 0",
        "Une licorne en tutu fait du skate sur un arc en ciel",
        "Je t aime plus que tout au monde",
        "Hier il pleuvait aujourd hui il fait beau",
        "Je deteste quand tu fais ca",
        "Dans le futur les robots danseront le tango",
    ]
    
    print("\n[1] Obtention des vrais embeddings harmoniques...")
    hidden_states, tokens = get_vrais_embeddings(phrases)
    print(f"    Embeddings: {hidden_states.shape}")
    
    proj = PureSignatureProjectionV4()
    
    print("\n[2] Calcul des signatures 9D (auto-normalisees)...")
    signatures = proj(hidden_states)
    print(f"    Signatures: {signatures.shape}")
    
    dims = ['phi', 'alpha', 'reasoning', 'creativity', 'math', 'factual', 'code', 'emotion', 'temporal']
    
    print(f"\n[3] Profils par phrase :")
    print(f"{'Phrase':<50} ", end="")
    for d in dims:
        print(f"{d[:4]:>5}", end=" ")
    print()
    print("-" * (50 + 9 * 6))
    
    for i, phrase in enumerate(phrases):
        profile = signatures[i].mean(dim=0)
        phrase_short = phrase[:48] + ".." if len(phrase) > 48 else phrase
        print(f"{phrase_short:<50} ", end="")
        for j in range(len(dims)):
            val = profile[j].item()
            print(f"{val:5.3f}", end=" ")
        print()
    
    print(f"\n[4] Analyse comparative :")
    print(f"{'Dimension':<12} {'Min':<8} {'Max':<8} {'Moy':<8} {'Ecart':<8} {'Interpretation':<40}")
    print("-" * 84)
    
    interpretations = {
        'phi': 'Diversite du vocabulaire',
        'alpha': 'Rugosite fractale',
        'reasoning': 'Coherence logique',
        'creativity': 'Originalite/divergence',
        'math': 'Periodicite numerique',
        'factual': 'Confiance factuelle',
        'code': 'Structure hierarchique',
        'emotion': 'Charge emotionnelle',
        'temporal': 'Ancrage temporel'
    }
    
    for j, dim in enumerate(dims):
        vals = signatures[:, :, j]
        ecart = vals.std().item()
        print(f"{dim:<12} {vals.min():<8.3f} {vals.max():<8.3f} {vals.mean():<8.3f} {ecart:<8.3f} {interpretations[dim]:<40}")
    
    print(f"\n[5] Phrases extremes par dimension :")
    for j, dim in enumerate(dims):
        vals = signatures[:, :, j].mean(dim=1)
        max_idx = vals.argmax().item()
        min_idx = vals.argmin().item()
        print(f"  {dim:<12}: MAX={vals[max_idx]:.3f} \"{phrases[max_idx][:40]}\"")
        print(f"  {'':12}  MIN={vals[min_idx]:.3f} \"{phrases[min_idx][:40]}\"")
    
    print(f"\n{'='*70}")
    print("RESUME V4 :")
    print("  - Formules auto-normalisees dans [0,1]")
    print("  - Pas de calibration externe")
    print("  - Robuste aux vrais embeddings harmoniques")
    print("  - 9 dimensions (7 + emotion + temporal)")
    print("  - 0 parametre entrainable")
    print(f"{'='*70}")


if __name__ == '__main__':
    demo_v4()
