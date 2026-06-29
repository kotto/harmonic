"""
Harmonic Decoder Bridge — Signature 9D → Texte
===============================================
Pont entre les signatures harmoniques du moteur (engine/) et le
PhiInverseDecoder de harmonic_training/model/.

Pipeline :
  1. Signature 9D du moteur (harmonic_engine.analyze() ou contexte holographique)
  2. Adaptation 9D → 7D (projection linéaire)
  3. HarmonicPureForCausalLM → signatures par position + contexte
  4. PhiInverseDecoder → logits → échantillonnage → tokens
  5. Génération autorégressive conditionnée par la signature harmonique

Le PhiInverseDecoder est l'INVERSE du noyau ABC :
  W(v,d) = cos(v·d·φ/V) · φ / K_abc(d)
C'est l'intégrale fractionnaire qui reconstruit les tokens depuis la signature.

ZERO paramètre entraînable dans le décodeur (poids analytiques φ).
Le ConditionEncoder (11D→512D) peut être entraîné pour améliorer l'adaptation.
"""

import sys
import os
import math
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import numpy as np

# Chemins
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_HARMONIC_TRAINING = _PROJECT_ROOT / "harmonic_training"

sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_HARMONIC_TRAINING))


# ==============================================================================
# IMPORT ROBUSTE DES BRICQUES HARMONIQUES
# ==============================================================================

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# Chargement lazy du modele (pur 0-param ou entraîne 85M)
_pure_model = None
_trained_model = None
_tokenizer = None
_phi_decoder = None
_model_type = None  # 'pure' ou 'trained'


def _ensure_model(model_type: str = 'trained'):
    """Charge le modèle harmonique.

    Args:
        model_type: 'trained' (85M params, checkpoint) ou 'pure' (0 param, deterministe)
    """
    global _pure_model, _trained_model, _tokenizer, _model_type

    if model_type == 'trained' and _trained_model is not None:
        _model_type = 'trained'
        return
    if model_type == 'pure' and _pure_model is not None:
        _model_type = 'pure'
        return
    if _pure_model is not None or _trained_model is not None:
        return  # Déjà chargé

    if not TORCH_AVAILABLE:
        raise RuntimeError("PyTorch requis pour le HarmonicDecoderBridge")

    from model.tokenizer import HarmonicTokenizer

    if model_type == 'trained':
        print("[DecoderBridge] Loading HarmonicForCausalLM (85M params, trained)...")
        try:
            from model.harmonic_model import HarmonicForCausalLM, HARMONIC_CONFIGS
        except ImportError:
            print("[DecoderBridge] Trained model not available, falling back to pure")
            model_type = 'pure'

    if model_type == 'trained':
        vocab_size = 50304
        # Essayer de charger le tokenizer étendu
        extended_tok_path = _HARMONIC_TRAINING.parent / "data" / "training_output" / "tokenizer_extended.json"
        _tokenizer = HarmonicTokenizer(vocab_size=vocab_size)
        if extended_tok_path.exists():
            try:
                _tokenizer.load(str(extended_tok_path))
                print(f"  Extended tokenizer loaded: {_tokenizer.get_vocab_size()} tokens")
            except Exception:
                print(f"  Using base tokenizer ({_tokenizer.get_vocab_size()} tokens)")
        else:
            print(f"  Using base tokenizer ({_tokenizer.get_vocab_size()} tokens)")
        config = dict(HARMONIC_CONFIGS['harmonic-tiny'])
        config['vocab_size'] = vocab_size
        config['max_len'] = 64  # Match le checkpoint (RoPE cache pour 64 positions)
        _trained_model = HarmonicForCausalLM(config)

        # Charger le checkpoint (priorité: data/training_output > harmonic_training/checkpoints_test)
        ckpt_candidates = [
            _PROJECT_ROOT / "data" / "training_output" / "checkpoint_final.pt",
            _HARMONIC_TRAINING / "checkpoints_test" / "checkpoint_final.pt",
        ]
        ckpt_path = None
        for c in ckpt_candidates:
            if c.exists():
                ckpt_path = c
                break

        if ckpt_path and ckpt_path.exists():
            print(f"  Loading checkpoint: {ckpt_path}")
            ckpt = torch.load(str(ckpt_path), map_location='cpu', weights_only=False)
            state = ckpt['model_state_dict']
            state = {k.replace('model.', ''): v for k, v in state.items()}
            _trained_model.load_state_dict(state, strict=False)
            gs = ckpt.get('global_step', '?')
            bl = ckpt.get('best_loss', ckpt.get('avg_loss', '?'))
            print(f"  Checkpoint loaded (step={gs}, loss={bl})")
        else:
            print("  No checkpoint found, using random weights")

        _trained_model.eval()
        n = sum(p.numel() for p in _trained_model.parameters())
        print(f"  Vocab={_tokenizer.get_vocab_size()}, Params={n:,}")
        _model_type = 'trained'

    elif model_type == 'pure':
        from model.harmonic_pure_model import HarmonicPureForCausalLM
        print("[DecoderBridge] Loading HarmonicPureForCausalLM (0 param, deterministic)...")
        _tokenizer = HarmonicTokenizer(vocab_size=5000)
        _pure_model = HarmonicPureForCausalLM(
            vocab_size=_tokenizer.get_vocab_size(),
            hidden_size=256,
            num_layers=4,
            max_len=512,
        )
        _pure_model.eval()
        print(f"  Vocab={_tokenizer.get_vocab_size()}, Params=0")
        _model_type = 'pure'


def _ensure_phi_decoder():
    """Charge le PhiInverseDecoder."""
    global _phi_decoder
    if _phi_decoder is not None:
        return
    _ensure_model()
    from model.harmonic_signature_decoder import PhiInverseDecoder
    vocab = _tokenizer.get_vocab_size()
    dim = 7 if _model_type == 'pure' else 7  # toujours 7D pour le décodeur inverse
    _phi_decoder = PhiInverseDecoder(vocab_size=vocab, signature_dim=dim)
    print(f"  PhiInverseDecoder loaded ({vocab} tokens, {dim}D → {vocab}D logits)")


# ==============================================================================
# ADAPTATEUR SIGNATURE 9D → 7D
# ==============================================================================

class SignatureAdapter:
    """
    Adapte les signatures 9D/11D du moteur vers l'espace 7D du PhiInverseDecoder.

    La signature moteur a 9 dimensions :
      [phi_ratio, alpha_complexity, reasoning, creative, math, factual, code, emotion, temporal]

    Le PhiInverseDecoder attend 7 dimensions :
      [phi, alpha, reasoning, creativity, math, factual, code]

    Mapping :
      - phi_ratio → phi (dim 0)
      - alpha_complexity → alpha (dim 1)
      - k_reasoning, k_creative, k_mathematical, k_factual, k_code → dims 2-6
      - emotion, temporal → injectées via blending dans les 7 autres dimensions
    """

    def __init__(self):
        # Matrice de projection 9D → 7D
        # Les 5 dimensions cognitives sont mappées directement
        # emotion et temporal sont fusionnées avec la moyenne des autres
        self.projection = np.zeros((7, 9), dtype=np.float32)

        # Mapping direct pour les 5 dimensions cognitives
        self.projection[0, 0] = 0.6   # phi_ratio → phi
        self.projection[1, 1] = 0.6   # alpha_complexity → alpha

        # Dimensions cognitives: mapping weighted
        self.projection[2, 2] = 0.7   # reasoning → reasoning
        self.projection[3, 3] = 0.7   # creative → creativity
        self.projection[4, 4] = 0.7   # math → math
        self.projection[5, 5] = 0.7   # factual → factual
        self.projection[6, 6] = 0.7   # code → code

        # Emotion et temporal sont distribuées (0.15 chacune vers chaque dimension)
        for i in range(7):
            self.projection[i, 7] = 0.15  # émotion → toutes les dimensions
            self.projection[i, 8] = 0.15  # temporal → toutes les dimensions

        # Normalisation pour préserver l'énergie
        row_sums = self.projection.sum(axis=1, keepdims=True)
        self.projection = self.projection / (row_sums + 1e-8)

    def adapt(self, sig_9d: np.ndarray) -> torch.Tensor:
        """
        Projette une signature 9D [9] vers l'espace 7D [7].

        Args:
            sig_9d: [9] float32 dans [0,1]

        Returns:
            torch.Tensor [1, 7] float32
        """
        sig_7d = sig_9d @ self.projection.T  # [9] @ [9, 7] → [7]
        sig_7d = np.clip(sig_7d, 0.0, 1.0)
        return torch.from_numpy(sig_7d).float().unsqueeze(0)  # [1, 7]

    def adapt_with_style(self, sig_9d: np.ndarray, style: str = "neutre") -> torch.Tensor:
        """Adapte avec modulation de style."""
        sig = sig_9d.copy()
        if style == "creatif":
            sig[3] = min(1.0, sig[3] * 1.5)   # creativity +
            sig[2] = max(0.0, sig[2] * 0.7)   # reasoning -
        elif style == "precis":
            sig[4] = min(1.0, sig[4] * 1.5)   # math +
            sig[5] = min(1.0, sig[5] * 1.3)   # factual +
        elif style == "emotionnel":
            sig[7] = min(1.0, sig[7] * 2.0)
        elif style == "technique":
            sig[6] = min(1.0, sig[6] * 1.5)   # code +
            sig[5] = min(1.0, sig[5] * 1.3)
        return self.adapt(sig)


# ==============================================================================
# PONT PRINCIPAL : SIGNATURE → TEXTE
# ==============================================================================

class HarmonicDecoderBridge:
    """
    Pont entre les signatures harmoniques du moteur et la génération de texte.

    Deux modes :
      - 'trained' : HarmonicForCausalLM (85M params, checkpoint step 10)
      - 'pure'    : HarmonicPureForCausalLM (0 param, déterministe)

    Le PhiInverseDecoder (0 param) traduit les signatures en tokens.
    """

    def __init__(self, model_type: str = 'trained'):
        self.model_type = model_type
        _ensure_model(model_type)
        _ensure_phi_decoder()
        self.adapter = SignatureAdapter()
        self.sig_history: List[np.ndarray] = []

    @torch.no_grad()
    def generate(
        self,
        signature_9d: np.ndarray,
        prompt: str = "",
        max_new_tokens: int = 40,
        temperature: float = 0.85,
        top_k: int = 30,
        top_p: float = 0.92,
        repetition_penalty: float = 1.3,
        style: str = "neutre",
    ) -> Tuple[str, Dict]:
        """Génère du texte conditionné par une signature harmonique 9D."""
        sig_7d = self.adapter.adapt_with_style(signature_9d, style)
        self.sig_history.append(signature_9d)
        if len(self.sig_history) > 8:
            self.sig_history.pop(0)

        if prompt:
            tokens = _tokenizer.encode(prompt)
        else:
            tokens = [2]  # <BOS>

        generated = torch.tensor([tokens], dtype=torch.long)
        token_hist = []

        model = _trained_model if self.model_type == 'trained' else _pure_model
        use_phi_inverse = True  # Toujours utiliser le décodeur inverse pour le conditionnement

        for step in range(max_new_tokens):
            max_len = getattr(model, 'max_len', 512)
            if generated.shape[1] > max_len:
                generated = generated[:, -max_len:]

            if self.model_type == 'trained':
                logits_out, _, _ = model(generated)  # (logits, loss, signatures)
                logits = logits_out[:, -1, :]  # [1, V]
            else:
                _, all_signatures = model(generated)
                last_pos_sig = all_signatures[-1, 0, -1, :]
                blended = 0.7 * last_pos_sig + 0.3 * sig_7d.squeeze(0)
                logits = _phi_decoder(blended.unsqueeze(0))


            # Pénalité de répétition
            if repetition_penalty > 1.0:
                for tok in generated[0, -50:]:
                    tid = tok.item()
                    if tid < logits.shape[1]:
                        if logits[0, tid] < 0:
                            logits[0, tid] *= repetition_penalty
                        else:
                            logits[0, tid] /= repetition_penalty

            probs = F.softmax(logits / max(temperature, 0.01), dim=-1)

            if top_k > 0 and top_k < probs.shape[-1]:
                vals, idx = torch.topk(probs, top_k, dim=-1)
                probs = torch.zeros_like(probs)
                probs.scatter_(1, idx, vals)
                probs = probs / probs.sum(dim=-1, keepdim=True)

            if top_p < 1.0:
                sp, si = torch.sort(probs, descending=True, dim=-1)
                cum = torch.cumsum(sp, dim=-1)
                rmv = cum > top_p
                rmv[:, 1:] = rmv[:, :-1].clone()
                rmv[:, 0] = False
                for b in range(probs.shape[0]):
                    idx_rmv = si[b][rmv[b]]
                    probs[b, idx_rmv] = 0.0
                probs = probs / probs.sum(dim=-1, keepdim=True)

            next_t = torch.multinomial(probs, 1)
            generated = torch.cat([generated, next_t], dim=-1)
            token_hist.append(next_t.item())

            if next_t.item() == 3:  # <EOS>
                break

        text = _tokenizer.decode(generated[0].tolist())
        info = {
            'unique_tokens': len(set(token_hist)),
            'total_tokens': len(token_hist),
            'diversity': len(set(token_hist)) / max(len(token_hist), 1),
            'sig_9d_mean': float(np.mean(signature_9d)),
            'model_type': self.model_type,
        }
        return text, info

    def generate_from_engine(
        self,
        user_message: str,
        knowledge_context: Optional[str] = None,
        category: Optional[str] = None,
        max_new_tokens: int = 40,
        temperature: float = 0.85,
        style: str = "neutre",
    ) -> Tuple[str, Dict]:
        """
        Génère une réponse complète à partir d'un message utilisateur.

        Pipeline complet :
          1. Analyser le message → signature 9D
          2. Adapter → 7D
          3. Générer via HarmonicPureForCausalLM + PhiInverseDecoder

        Args:
            user_message: message utilisateur
            knowledge_context: contexte de l'hologramme (optionnel)
            category: catégorie forcée (optionnel, sinon auto-détectée)
            max_new_tokens: tokens à générer
            temperature: créativité
            style: style

        Returns:
            (réponse, infos)
        """
        # Obtenir la signature 9D du moteur
        try:
            from engine.harmonic_engine import HarmonicResonanceEngine
            engine = HarmonicResonanceEngine(use_hologram='light')
        except ImportError:
            # Fallback: utiliser une signature neutre
            sig_9d = np.full(9, 0.5, dtype=np.float32)
        else:
            sig = engine.analyze(user_message)
            sig_dict = sig.to_dict()
            sig_9d = np.array([
                sig_dict.get("phi", sig.phi_ratio),
                sig_dict.get("alpha", sig.alpha_complexity),
                sig_dict.get("reasoning", sig.k_reasoning),
                sig_dict.get("creativity", sig.k_creative),
                sig_dict.get("math", sig.k_mathematical),
                sig_dict.get("factual", sig.k_factual),
                sig_dict.get("code", sig.k_code),
                sig_dict.get("emotion", sig.k_emotional),
                sig_dict.get("temporal", sig.k_temporal),
            ], dtype=np.float32)

        # Construire le prompt à partir du contexte
        prompt = ""
        if knowledge_context:
            # Utiliser le contexte comme amorce
            prompt = knowledge_context.strip()[:100] + "\n\n"

        # Catégorie → style mapping
        if category is None:
            cat_conf = engine.classify(user_message) if engine else ("general", 0.5)
            category = cat_conf[0] if isinstance(cat_conf, tuple) else "general"

        style_map = {
            "mathematical": "precis", "code": "technique",
            "creative": "creatif", "reasoning": "precis",
            "factual": "precis", "general": style,
        }
        gen_style = style_map.get(category, style)

        return self.generate(
            signature_9d=sig_9d,
            prompt=prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            style=gen_style,
        )


# ==============================================================================
# ENTRAÎNEMENT DU CONDITION ENCODER (améliore l'adaptation 9D→texte)
# ==============================================================================

class DecoderCalibrator:
    """
    Entraîne le ConditionEncoder (11D→512D) pour améliorer la qualité
    de la génération de texte à partir des signatures.

    Utilise des paires (signature 9D, texte de référence) pour calibrer
    le mapping via backpropagation manuelle (numpy).
    """

    def __init__(self):
        _ensure_phi_decoder()

    def calibrate(
        self,
        signature_9d: np.ndarray,
        reference_text: str,
        n_steps: int = 100,
        lr: float = 0.01,
    ) -> float:
        """
        Calibre le ConditionEncoder sur un exemple de référence.

        Args:
            signature_9d: signature source [9]
            reference_text: texte cible attendu
            n_steps: nombre d'itérations
            lr: learning rate

        Returns:
            loss finale
        """
        try:
            from engine.phi_diffusion_engine import ConditionEncoder
        except ImportError:
            print("[Calibrator] ConditionEncoder non disponible")
            return 1.0

        encoder = ConditionEncoder()
        ref_tokens = _tokenizer.encode(reference_text)
        ref_tensor = torch.tensor(ref_tokens, dtype=torch.long)

        losses = []
        for step in range(n_steps):
            # Encoder la signature 9D → embedding 512D
            sig_11d = np.pad(signature_9d, (0, 2), mode='constant', constant_values=0.5)
            embedding = encoder.encode(sig_11d)

            # Cible : embedding moyen des tokens de référence
            with torch.no_grad():
                ref_emb = _pure_model.token_embedding(ref_tensor.unsqueeze(0))
                target_emb = ref_emb.mean(dim=1).squeeze(0).numpy()  # [hidden]

            # Pad/truncate to 512
            if len(target_emb) < 512:
                target_emb = np.pad(target_emb, (0, 512 - len(target_emb)))
            elif len(target_emb) > 512:
                target_emb = target_emb[:512]

            # MSE loss + train step
            loss = encoder.train_step(
                sig_11d.reshape(1, 11),
                target_emb.reshape(1, 512),
                lr=lr,
            )

            losses.append(loss)
            if step % 20 == 0 and step > 0:
                print(f"  [Calibrator] step {step}/{n_steps}: loss={loss:.6f}")

        return float(np.mean(losses[-10:]))


# ==============================================================================
# DÉMONSTRATION
# ==============================================================================

def demo():
    """Démonstration du pont signature → texte."""
    print("=" * 70)
    print("HARMONIC DECODER BRIDGE : Signature 9D → Texte")
    print("  HarmonicPureForCausalLM (0 param) + PhiInverseDecoder (0 param)")
    print("=" * 70)
    print()

    bridge = HarmonicDecoderBridge()

    # Signatures de test (simulées)
    test_cases = [
        {
            "sig": np.array([0.3, 0.5, 0.2, 0.8, 0.1, 0.4, 0.1, 0.6, 0.5], dtype=np.float32),
            "prompt": "La conscience est",
            "style": "creatif",
            "label": "créatif/poétique"
        },
        {
            "sig": np.array([0.4, 0.6, 0.8, 0.1, 0.7, 0.3, 0.1, 0.2, 0.3], dtype=np.float32),
            "prompt": "Le nombre d or",
            "style": "precis",
            "label": "mathématique/précis"
        },
        {
            "sig": np.array([0.5, 0.4, 0.5, 0.5, 0.2, 0.6, 0.1, 0.4, 0.5], dtype=np.float32),
            "prompt": "La verite est",
            "style": "neutre",
            "label": "factuel/neutre"
        },
        {
            "sig": np.array([0.3, 0.3, 0.1, 0.9, 0.1, 0.1, 0.1, 0.8, 0.6], dtype=np.float32),
            "prompt": "Dans l univers",
            "style": "emotionnel",
            "label": "émotionnel"
        },
    ]

    for tc in test_cases:
        print(f"--- {tc['label']} (sig mean={tc['sig'].mean():.2f}) ---")
        text, info = bridge.generate(
            signature_9d=tc['sig'],
            prompt=tc['prompt'],
            max_new_tokens=25,
            style=tc['style'],
            temperature=0.85,
        )
        print(f"  → {text[:120]}")
        print(f"  ({info['total_tokens']} tokens, diversity={info['diversity']:.2f})")
        print()

    print("=" * 70)
    print("Demo complete.")
    print()
    print("Pour générer depuis le moteur complet :")
    print("  bridge = HarmonicDecoderBridge()")
    print("  text, info = bridge.generate_from_engine(")
    print("      'Explique la relativite',")
    print("      knowledge_context='Einstein a publie...',")
    print("  )")
    print("=" * 70)


if __name__ == '__main__':
    demo()
