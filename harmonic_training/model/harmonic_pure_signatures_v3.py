"""
Signatures Harmoniques 7D — Version 3 Complete
================================================
Ameliorations :
1. Validation sur de VRAIS embeddings (modele harmonique pur)
2. Ajout de 2 dimensions : emotion (8e) et temporalite (9e)
3. Calibration automatique des seuils par analyse statistique

Architecture :
- Les signatures sont calculees sur les hidden states du modele harmonique pur
- Chaque dimension a une formule analytique avec des parametres calibres
- Les seuils sigmoid sont ajustes automatiquement

Les 9 dimensions :
1. phi        : entropie/diversite du vocabulaire
2. alpha      : complexite fractale du raisonnement
3. reasoning  : coherence logique (cause → effet)
4. creativity : divergence creative (originalite)
5. math       : precision numerique et logique formelle
6. factual    : ancrage factuel (confiance)
7. code       : structure hierarchique (programmation)
8. emotion    : charge emotionnelle et tonalite
9. temporal   : ancrage temporel (passe/futur/conditionnel)
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.abc_kernel import PHI, ALPHA


# =========================================================================
# CALIBRATEUR AUTOMATIQUE DE SEUILS
# =========================================================================

class SeuilCalibrator:
    """
    Calibre automatiquement les seuils des sigmoids.
    
    Principe :
    Pour chaque dimension, on analyse la distribution des valeurs brutes
    sur un echantillon de texte, puis on ajuste mu et sigma pour que
    sigmoid(k * (x - mu)) donne une distribution uniforme dans [0, 1].
    
    Usage :
        cal = SeuilCalibrator()
        cal.fit(hidden_states)  # analyse la distribution
        x_cal = cal.transform(x, dim='reasoning')  # applique le seuil calibre
    """
    
    def __init__(self):
        self.stats = {}  # {dim: {'mean': float, 'std': float, 'k': float}}
    
    def fit(self, hidden_states):
        """
        Calibre les seuils a partir d'un echantillon de hidden states.
        
        Args:
            hidden_states: [batch, seq_len, hidden_size]
        """
        # On calcule les valeurs brutes pour chaque dimension
        with torch.no_grad():
            raw = self._compute_all_raw(hidden_states)
        
        dims = ['phi', 'alpha', 'reasoning', 'creativity', 'math', 'factual', 'code', 'emotion', 'temporal']
        
        for i, dim in enumerate(dims):
            vals = raw[..., i].flatten()
            # Enlever les inf et nan
            vals = vals[torch.isfinite(vals)]
            if vals.numel() == 0:
                self.stats[dim] = {'mean': 0.0, 'std': 1.0, 'k': 1.0}
                continue
            mean = vals.mean().item()
            std = max(vals.std().item(), 0.1)  # std minimum de 0.1
            
            # k est choisi pour que sigmoid(k * (x - mean)) couvre [0.05, 0.95]
            # quand x est dans [mean - 2*std, mean + 2*std]
            # On borne k pour eviter les explosions
            k = min(2.0 / std, 10.0)
            
            self.stats[dim] = {'mean': mean, 'std': std, 'k': k}
    
    def _compute_all_raw(self, hidden_states):
        """Calcule les valeurs brutes pour toutes les dimensions."""
        return torch.cat([
            compute_phi_raw(hidden_states),
            compute_alpha_raw(hidden_states),
            compute_reasoning_raw(hidden_states),
            compute_creativity_raw(hidden_states),
            compute_math_raw(hidden_states),
            compute_factual_raw(hidden_states),
            compute_code_raw(hidden_states),
            compute_emotion_raw(hidden_states),
            compute_temporal_raw(hidden_states),
        ], dim=-1)
    
    def transform(self, raw_values, dim):
        """
        Applique le seuil calibre.
        
        Args:
            raw_values: tenseur de valeurs brutes
            dim: nom de la dimension
        
        Returns:
            valeurs calibrees dans [0, 1]
        """
        stats = self.stats.get(dim, {'mean': 0.0, 'k': 1.0})
        return torch.sigmoid(stats['k'] * (raw_values - stats['mean']))


# =========================================================================
# FONCTIONS RAW (valeurs brutes avant sigmoid)
# =========================================================================

def compute_phi_raw(hidden_states):
    """phi raw : entropie de Renyi."""
    d = hidden_states.shape[-1]
    tau = math.sqrt(d)
    p = F.softmax(hidden_states / tau, dim=-1)
    q = 0.5
    p_q = torch.sum(p ** q, dim=-1)
    renyi = torch.log(p_q + 1e-10) / (1 - q)
    renyi = renyi / math.log(d)
    return renyi.unsqueeze(-1)


def compute_alpha_raw(hidden_states):
    """alpha raw : exposant de Hurst."""
    var_total = hidden_states.var(dim=-1, keepdim=True)
    min_len = hidden_states.shape[1]
    scales = []
    for s in [1, 2, 4]:
        if s >= min_len:
            continue
        diff = hidden_states[:, s:] - hidden_states[:, :-s]
        var_scale = diff.var(dim=1, keepdim=True)
        var_scale = var_scale.mean(dim=1, keepdim=True)
        scales.append(var_scale)
    
    if scales:
        var_scales = torch.stack(scales, dim=-1).mean(dim=-1)
        var_scales = var_scales.expand(-1, min_len, -1)
    else:
        var_scales = var_total.expand(-1, min_len, -1)
    
    ratio = var_scales / (var_total + 1e-8)
    ratio = torch.clamp(ratio, min=1e-8, max=1e8)
    H = 0.5 * torch.log2(ratio) + 0.5
    H = torch.nan_to_num(H, nan=0.5)
    return H


def compute_reasoning_raw(hidden_states):
    """reasoning raw : coherence causale."""
    x_norm = F.normalize(hidden_states, dim=-1)
    cos_sim = (x_norm[:, :-1] * x_norm[:, 1:]).sum(dim=-1)
    cos_sim = F.pad(cos_sim.unsqueeze(-1), (0, 0, 0, 1))
    var_local = hidden_states[:, 1:] - hidden_states[:, :-1]
    var_local = var_local.var(dim=-1, keepdim=True)
    var_local = F.pad(var_local, (0, 0, 0, 1))
    coherence = cos_sim * (1.0 - torch.sigmoid(var_local - 0.5))
    return coherence


def compute_creativity_raw(hidden_states):
    """creativity raw : divergence semantique."""
    batch, seq_len, _ = hidden_states.shape
    x_norm = F.normalize(hidden_states, dim=-1)
    sim_matrix = torch.bmm(x_norm, x_norm.transpose(1, 2))
    mask = torch.eye(seq_len, device=hidden_states.device).unsqueeze(0)
    sim_matrix = sim_matrix * (1.0 - mask) - mask * 10.0
    max_sim = sim_matrix.max(dim=-1)[0].unsqueeze(-1)
    diversity = 1.0 - max_sim
    return diversity


def compute_math_raw(hidden_states):
    """math raw : precision numerique."""
    x_norm = F.normalize(hidden_states, dim=-1)
    shifted = F.pad(x_norm[:, :-1], (0, 0, 1, 0))
    autocorr = (x_norm * shifted).sum(dim=-1, keepdim=True)
    if hidden_states.shape[1] > 2:
        shifted2 = F.pad(x_norm[:, :-2], (0, 0, 2, 0))
        periodic = (x_norm * shifted2).sum(dim=-1, keepdim=True)
    else:
        periodic = torch.zeros_like(autocorr)
    return 0.7 * autocorr + 0.3 * periodic


def compute_factual_raw(hidden_states):
    """factual raw : ancrage factuel."""
    norm = torch.norm(hidden_states, dim=-1, keepdim=True)
    norm_max = norm.max(dim=1, keepdim=True)[0]
    norm_ratio = norm / (norm_max + 1e-8)
    d = hidden_states.shape[-1]
    p = F.softmax(hidden_states / math.sqrt(d), dim=-1)
    log_p = torch.log(p + 1e-10)
    entropy = -torch.sum(p * log_p, dim=-1, keepdim=True)
    entropy = entropy / math.log(d)
    return norm_ratio * (1.0 - entropy)


def compute_code_raw(hidden_states):
    """code raw : structure hierarchique."""
    hidden = hidden_states
    low_freq = torch.zeros_like(hidden)
    low_freq[:, 1:-1, :] = (hidden[:, :-2, :] + 2 * hidden[:, 1:-1, :] + hidden[:, 2:, :]) / 4.0
    low_freq[:, 0, :] = (2 * hidden[:, 0, :] + hidden[:, 1, :]) / 3.0
    low_freq[:, -1, :] = (hidden[:, -2, :] + 2 * hidden[:, -1, :]) / 3.0
    high_freq = hidden - low_freq
    low_norm = torch.norm(low_freq, dim=-1, keepdim=True)
    high_norm = torch.norm(high_freq, dim=-1, keepdim=True)
    ratio = low_norm / (high_norm + 1e-8)
    norm_var = hidden_states.norm(dim=-1).var(dim=-1, keepdim=True)
    structure = torch.sigmoid(3.0 * (norm_var - 0.3))
    return ratio * (0.7 + 0.3 * structure)


# =========================================================================
# NOUVELLES DIMENSIONS : EMOTION (8e) ET TEMPORALITE (9e)
# =========================================================================

def compute_emotion_raw(hidden_states):
    """
    emotion raw : charge emotionnelle et tonalite.
    
    Formule : E = ||x_centre|| * (1 - symetrie)
    
    Mesure la charge emotionnelle :
    - Eleve : representation polarisee (emotion forte)
    - Faible : representation neutre (factuel)
    
    Principe :
    Les representations emotionnelles sont caracterisees par :
    1. Une norme elevee (activation forte)
    2. Une asymetrie dans la distribution des activations
       (les emotions positives/negatives polarisent le vecteur)
    
    Exemple :
    - "Je t'aime" → emotion eleve
    - "Le resultat est 42" → emotion faible
    """
    # Centre les donnees
    mean = hidden_states.mean(dim=1, keepdim=True)
    x_centre = hidden_states - mean
    
    # Norme de la deviation (activation emotionnelle)
    norm_dev = torch.norm(x_centre, dim=-1, keepdim=True)
    norm_dev = norm_dev / (norm_dev.max(dim=1, keepdim=True)[0] + 1e-8)
    
    # Asymetrie (skewness) de la distribution
    # Les emotions polarisent le vecteur → skewness eleve
    skew = torch.mean(x_centre ** 3, dim=-1, keepdim=True)
    skew = skew / (torch.mean(x_centre ** 2, dim=-1, keepdim=True) ** 1.5 + 1e-8)
    skew = torch.abs(skew)  # valeur absolue (peu importe le signe)
    
    # Combinaison : norme * asymetrie
    emotion = norm_dev * skew
    
    return emotion


def compute_temporal_raw(hidden_states):
    """
    temporal raw : ancrage temporel.
    
    Formule : T = gradient(x) * courbure(x)
    
    Mesure l'ancrage temporel :
    - Eleve : le texte a une direction temporelle (passe→futur)
    - Faible : le texte est intemporel (description, definition)
    
    Principe :
    Les textes temporels ont :
    1. Un gradient non nul (changement entre tokens)
    2. Une courbure (acceleration/deceleration)
    
    Exemple :
    - "Hier j'ai mange, aujourd'hui je digere" → temporal eleve
    - "Le ciel est bleu" → temporal faible
    """
    # Gradient (difference entre tokens consecutifs)
    grad = hidden_states[:, 1:] - hidden_states[:, :-1]
    grad = F.pad(grad, (0, 0, 0, 1))
    grad_norm = torch.norm(grad, dim=-1, keepdim=True)
    
    # Courbure (difference des gradients)
    # grad est [B, S, D] avec S = seq_len
    # courb doit etre [B, S, D] aussi
    if hidden_states.shape[1] > 2:
        # courb[t] = grad[t+1] - grad[t], donc courb a S-1 elements
        courb = grad[:, 1:, :] - grad[:, :-1, :]  # [B, S-1, D]
        # On pad pour retrouver S elements
        courb = F.pad(courb, (0, 0, 0, 1))  # [B, S, D]
        courb_norm = torch.norm(courb, dim=-1, keepdim=True)
    else:
        courb_norm = torch.zeros_like(grad_norm)
    
    # Normalisation
    grad_norm = grad_norm / (grad_norm.max(dim=1, keepdim=True)[0] + 1e-8)
    courb_norm = courb_norm / (courb_norm.max(dim=1, keepdim=True)[0] + 1e-8)
    
    # Temporalite = gradient * courbure
    temporal = grad_norm * (1.0 + courb_norm)
    
    return temporal


# =========================================================================
# PROJECTION DE SIGNATURE V3 (avec calibration)
# =========================================================================

class PureSignatureProjectionV3(nn.Module):
    """
    Projection de signature 9D — Version 3.
    
    Caracteristiques :
    - 9 dimensions (7 originales + emotion + temporal)
    - Calibration automatique des seuils
    - Validation sur vrais embeddings
    
    ZERO parametre entrainable.
    """
    
    def __init__(self, calibrate=True):
        super().__init__()
        self.calibrate = calibrate
        self.calibrator = SeuilCalibrator() if calibrate else None
        self._calibrated = False
    
    def fit_calibration(self, hidden_states):
        """Calibre les seuils sur un echantillon."""
        if self.calibrate:
            self.calibrator.fit(hidden_states)
            self._calibrated = True
    
    def forward(self, hidden_states):
        """
        Calcule les signatures 9D.
        
        Args:
            hidden_states: [batch, seq_len, hidden_size]
        
        Returns:
            signatures: [batch, seq_len, 9]
        """
        # Valeurs brutes
        phi = compute_phi_raw(hidden_states)
        alpha = compute_alpha_raw(hidden_states)
        reasoning = compute_reasoning_raw(hidden_states)
        creativity = compute_creativity_raw(hidden_states)
        math_val = compute_math_raw(hidden_states)
        factual = compute_factual_raw(hidden_states)
        code = compute_code_raw(hidden_states)
        emotion = compute_emotion_raw(hidden_states)
        temporal = compute_temporal_raw(hidden_states)
        
        if self.calibrate and self._calibrated:
            # Appliquer les seuils calibres
            phi = self.calibrator.transform(phi, 'phi')
            alpha = self.calibrator.transform(alpha, 'alpha')
            reasoning = self.calibrator.transform(reasoning, 'reasoning')
            creativity = self.calibrator.transform(creativity, 'creativity')
            math_val = self.calibrator.transform(math_val, 'math')
            factual = self.calibrator.transform(factual, 'factual')
            code = self.calibrator.transform(code, 'code')
            emotion = self.calibrator.transform(emotion, 'emotion')
            temporal = self.calibrator.transform(temporal, 'temporal')
        else:
            # Seuils par defaut (sigmoid standard)
            phi = torch.sigmoid(3.0 * (phi - 0.5))
            alpha = torch.sigmoid(3.0 * (alpha - 0.5))
            reasoning = torch.sigmoid(3.0 * (reasoning - 0.3))
            creativity = torch.sigmoid(3.0 * (creativity - 0.5))
            math_val = torch.sigmoid(3.0 * (math_val - 0.3))
            factual = torch.sigmoid(3.0 * (factual - 0.5))
            code = torch.sigmoid(code - 1.0)
            emotion = torch.sigmoid(3.0 * (emotion - 0.3))
            temporal = torch.sigmoid(3.0 * (temporal - 0.5))
        
        signatures = torch.cat([
            phi, alpha, reasoning, creativity, math_val, factual, code,
            emotion, temporal
        ], dim=-1)
        
        return signatures


# =========================================================================
# VALIDATION SUR VRAIS EMBEDDINGS
# =========================================================================

def get_vrais_embeddings(phrases, hidden_size=512):
    """
    Genere des embeddings REALISTES en utilisant l'embedding harmonique fixe.
    
    Contrairement a la version precedente qui utilisait torch.randn seede,
    cette fonction utilise le veritable HarmonicFixedEmbedding du modele.
    
    Args:
        phrases: liste de phrases
        hidden_size: taille de l'embedding
    
    Returns:
        hidden_states: [batch, max_len, hidden_size]
        tokens: liste des tokens
    """
    from model.harmonic_pure_model import HarmonicFixedEmbedding
    
    # Tokenisation simple (split)
    all_tokens = []
    max_len = 0
    for phrase in phrases:
        tokens = phrase.lower().split()
        all_tokens.append(tokens)
        max_len = max(max_len, len(tokens))
    
    # Creer un vocabulaire a la volee
    vocab = {}
    for tokens in all_tokens:
        for t in tokens:
            if t not in vocab:
                vocab[t] = len(vocab)
    
    vocab_size = len(vocab) + 10  # +10 pour les tokens inconnus
    
    # Embedding harmonique fixe
    embedding = HarmonicFixedEmbedding(vocab_size, hidden_size)
    
    # Convertir en IDs
    batch = len(phrases)
    input_ids = torch.zeros(batch, max_len, dtype=torch.long)
    for i, tokens in enumerate(all_tokens):
        for j, t in enumerate(tokens):
            input_ids[i, j] = vocab.get(t, 0)
    
    # Obtenir les vrais embeddings
    with torch.no_grad():
        hidden_states = embedding(input_ids)
    
    return hidden_states, all_tokens


# =========================================================================
# DEMONSTRATION COMPLETE V3
# =========================================================================

def demo_v3():
    """
    Demonstration complete de la version 3.
    
    Inclut :
    1. Validation sur vrais embeddings harmoniques
    2. 9 dimensions (7 + emotion + temporal)
    3. Calibration automatique des seuils
    """
    print("=" * 70)
    print("DEMONSTRATION : Signatures Harmoniques 9D — Version 3")
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
    
    # 1. Obtenir les VRAIS embeddings
    print("\n[1] Obtention des vrais embeddings harmoniques...")
    hidden_states, tokens = get_vrais_embeddings(phrases)
    print(f"    Embeddings: {hidden_states.shape}")
    print(f"    Phrases: {len(phrases)}")
    
    # 2. Initialiser la projection V3
    proj = PureSignatureProjectionV3(calibrate=True)
    
    # 3. Calibrer les seuils
    print("\n[2] Calibration automatique des seuils...")
    proj.fit_calibration(hidden_states)
    for dim, stats in proj.calibrator.stats.items():
        print(f"    {dim:<12} mean={stats['mean']:.4f}, std={stats['std']:.4f}, k={stats['k']:.2f}")
    
    # 4. Calculer les signatures
    print("\n[3] Calcul des signatures 9D...")
    signatures = proj(hidden_states)
    print(f"    Signatures: {signatures.shape}")
    
    # 5. Afficher les profils
    dims = ['phi', 'alpha', 'reasoning', 'creativity', 'math', 'factual', 'code', 'emotion', 'temporal']
    
    print(f"\n[4] Profils par phrase :")
    print(f"{'Phrase':<50} ", end="")
    for d in dims:
        print(f"{d[:4]:>5}", end=" ")
    print()
    print("-" * (50 + 9 * 6))
    
    for i, phrase in enumerate(phrases):
        profile = signatures[i].mean(dim=0)
        phrase_short = phrase[:48] + ".." if len(phrase) > 48 else phrase
        print(f"{phrase_short:<50} ", end="")
        for j, dim in enumerate(dims):
            val = profile[j].item()
            print(f"{val:5.3f}", end=" ")
        print()
    
    # 6. Analyse comparative
    print(f"\n[5] Analyse comparative :")
    print(f"{'Dimension':<12} {'Min':<8} {'Max':<8} {'Moy':<8} {'Interpretation':<40}")
    print("-" * 76)
    
    interpretations = {
        'phi': 'Diversite du vocabulaire',
        'alpha': 'Complexite du raisonnement',
        'reasoning': 'Coherence logique',
        'creativity': 'Originalite/divergence',
        'math': 'Precision numerique',
        'factual': 'Ancrage factuel',
        'code': 'Structure hierarchique',
        'emotion': 'Charge emotionnelle',
        'temporal': 'Ancrage temporel'
    }
    
    for j, dim in enumerate(dims):
        vals = signatures[:, :, j]
        print(f"{dim:<12} {vals.min():<8.3f} {vals.max():<8.3f} {vals.mean():<8.3f} {interpretations[dim]:<40}")
    
    # 7. Exemples extremes
    print(f"\n[6] Phrases extremes par dimension :")
    for j, dim in enumerate(dims):
        vals = signatures[:, :, j].mean(dim=1)
        max_idx = vals.argmax().item()
        min_idx = vals.argmin().item()
        print(f"  {dim:<12}: MAX={vals[max_idx]:.3f} \"{phrases[max_idx][:40]}\"")
        print(f"  {'':12}  MIN={vals[min_idx]:.3f} \"{phrases[min_idx][:40]}\"")
    
    print(f"\n{'='*70}")
    print("RESUME V3 :")
    print("  - Embeddings : VRAIS (HarmonicFixedEmbedding)")
    print("  - Dimensions : 9 (7 + emotion + temporal)")
    print("  - Seuils : Calibration automatique")
    print("  - Parametres : 0 entrainable")
    print(f"{'='*70}")


if __name__ == '__main__':
    demo_v3()
