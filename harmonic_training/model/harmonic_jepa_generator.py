"""
Harmonic JEPA Generator
=======================
Pipeline de generation base sur JEPA : prediction dans l'espace des signatures 9D.

Au lieu de predire le prochain token (biais du LM head fixe),
on predit la PROCHAINE SIGNATURE 9D avec JEPA, puis on selectionne
le token dont l'embedding resonne le mieux avec cette signature.

Architecture :
    x[t-n:t] -> HarmonicPureForCausalLM -> Signatures 7D + embeddings
    -> JEPA Predictor (appris) -> Signature predite [t+1]
    -> Resonance avec chaque token du vocabulaire
    -> Selection du token le plus resonant

Le LM Head fixe devient un GUIDE, et JEPA est le veritable generateur.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Optional, Tuple
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.harmonic_pure_model import HarmonicPureForCausalLM, HarmonicFixedEmbedding
from model.harmonic_jepa import HarmonicJEPA, resonance_loss, JEPAPredictor
from model.abc_kernel import PHI, ALPHA


class JEPAGenerator(nn.Module):
    """
    Generateur harmonique guide par JEPA.

    Args:
        base_model: HarmonicPureForCausalLM (encodeur fixe)
        jepa_model: HarmonicJEPA (predictor appris)
        resonance_weight: Poids de la resonance vs logits (0-1)
        top_k_resonance: Nombre de tokens candidats par resonance
    """

    def __init__(self,
                 base_model: HarmonicPureForCausalLM,
                 jepa_model: Optional[HarmonicJEPA] = None,
                 resonance_weight: float = 0.6,
                 top_k_resonance: int = 50):
        super().__init__()

        self.base_model = base_model
        self.jepa = jepa_model or HarmonicJEPA(hidden_dim=64, num_abc_kernel=5)
        self.resonance_weight = resonance_weight
        self.top_k_resonance = top_k_resonance

        # Embedding fixe pour reference
        self.embedding = base_model.token_embedding

        # Pre-calculer les signatures de tous les tokens du vocabulaire
        print("[JEPAGenerator] Calcul des signatures du vocabulaire...")
        self.register_buffer('vocab_signatures', self._compute_vocab_signatures())
        print(f"  Signatures: {self.vocab_signatures.shape}")

    def _compute_vocab_signatures(self) -> torch.Tensor:
        """
        Calcule les signatures 7D de tous les tokens du vocabulaire
        en utilisant la premiere couche du modele de base.

        Returns: [vocab_size, 7]
        """
        vocab_size = self.embedding.vocab_size
        hidden_size = self.embedding.hidden_size

        # Traiter par lots pour economiser la memoire
        batch_size = 256
        all_sigs = []

        with torch.no_grad():
            for start in range(0, vocab_size, batch_size):
                end = min(start + batch_size, vocab_size)
                token_ids = torch.arange(start, end, dtype=torch.long).unsqueeze(0)
                embeddings = self.embedding(token_ids)  # [1, B, D]

                # Extraire signature via la premiere couche
                first_layer = self.base_model.layers[0]
                _, signatures = first_layer(embeddings, None)  # [1, B, 7]
                all_sigs.append(signatures[0])  # [B, 7]

        return torch.cat(all_sigs, dim=0)  # [V, 7]

    def _resonance_scores(self, pred_sig_7d: torch.Tensor) -> torch.Tensor:
        """
        Calcule le score de resonance entre une signature 7D predite
        et les signatures pre-calculees de TOUS les tokens.

        resonance = cosine_similarity(sig_pred * PHI, sig_vocab * PHI)

        Args:
            pred_sig_7d: [1, 7] signature predite

        Returns:
            scores: [V] scores de resonance normalises dans [0, 1]
        """
        pred_norm = F.normalize(pred_sig_7d * PHI, dim=-1)  # [1, 7]
        vocab_norm = F.normalize(self.vocab_signatures * PHI, dim=-1)  # [V, 7]

        # Similarite cosinus avec tous les tokens
        similarity = torch.mm(pred_norm, vocab_norm.T)[0]  # [V]

        # Normaliser dans [0, 1]
        scores = (similarity + 1.0) / 2.0

        return scores

    def forward(self,
                input_ids: torch.Tensor,
                max_new_tokens: int = 50,
                temperature: float = 0.85,
                top_k: int = 30,
                top_p: float = 0.92,
                repetition_penalty: float = 1.3,
                use_jepa: bool = True) -> Tuple[torch.Tensor, List[Dict]]:
        """
        Generation avec guidance JEPA.

        Args:
            input_ids: [batch, seq_len]
            max_new_tokens: Nombre max de tokens a generer
            temperature: Temperature du sampling
            top_k: Top-k filtering
            top_p: Top-p nucleus sampling
            repetition_penalty: Repetition penalty (>1.0 penalise)
            use_jepa: Utiliser JEPA comme guide

        Returns:
            generated: [batch, seq_len + max_new_tokens]
            tokens_info: Liste des tokens generes avec scores
        """
        self.eval()
        generated = input_ids.clone()
        tokens_info = []

        # Compter les tokens generes pour afficher la diversite
        generated_set = set()

        with torch.no_grad():
            for step in range(max_new_tokens):
                # Tronquer si trop long
                if generated.shape[1] > self.base_model.max_len:
                    generated = generated[:, -self.base_model.max_len:]

                # 1. Forward pass du modele de base
                logits, signatures = self.base_model(generated)
                # signatures: [L, B, S, 7]

                # 2. Predire la prochaine signature avec JEPA
                if use_jepa and generated.shape[1] >= 3:
                    # Signatures de la derniere couche
                    last_sigs = signatures[-1, 0]  # [S, 7]

                    # Etendre en 9D pour JEPA
                    S = last_sigs.shape[0]
                    sig_9d = torch.zeros(S, 9, device=last_sigs.device)
                    sig_9d[:, :7] = last_sigs
                    # Dimension 7 = emotion (oscillation)
                    sig_9d[:, 7] = 0.3 + 0.3 * torch.sin(
                        torch.arange(S, device=last_sigs.device) * PHI
                    )
                    # Dimension 8 = temporal (meme que phi par defaut)
                    sig_9d[:, 8] = last_sigs[:, 0]

                    # Ajouter dimension batch
                    sig_9d_batch = sig_9d.unsqueeze(0)  # [1, S, 9]

                    # Predire la prochaine signature
                    pred_sig_9d = self.jepa.predictor(sig_9d_batch)  # [1, 9]

                    # Extraire les 7 premieres dimensions
                    pred_sig = pred_sig_9d[:, :7]  # [1, 7]

                    # 3. Scores de resonance avec le vocabulaire
                    resonance_scores = self._resonance_scores(pred_sig)  # [V]
                else:
                    # Fallback: pas de JEPA
                    resonance_scores = torch.ones(
                        logits.shape[-1], device=logits.device
                    ) / logits.shape[-1]

                # 4. Combiner logits du LM Head + resonance JEPA
                next_logits = logits[:, -1, :].clone()  # [1, V]

                # Repetition penalty sur les logits
                if repetition_penalty > 1.0:
                    for batch_idx in range(generated.shape[0]):
                        for token_id in generated[batch_idx, -50:]:
                            if next_logits[batch_idx, token_id] < 0:
                                next_logits[batch_idx, token_id] *= repetition_penalty
                            else:
                                next_logits[batch_idx, token_id] /= repetition_penalty

                # Probabilites du LM Head
                lm_probs = F.softmax(next_logits / temperature, dim=-1)  # [1, V]

                # Normaliser les scores de resonance
                res_probs = resonance_scores / (resonance_scores.sum() + 1e-8)
                res_probs = res_probs.unsqueeze(0)  # [1, V]

                # Combinaison ponderee
                combined = (1 - self.resonance_weight) * lm_probs + \
                    self.resonance_weight * res_probs
                combined = combined / combined.sum(dim=-1, keepdim=True)

                # Top-k filtering
                if top_k > 0:
                    vals, idx = torch.topk(combined, min(top_k, combined.shape[-1]), dim=-1)
                    combined = torch.zeros_like(combined)
                    combined.scatter_(1, idx, vals)
                    combined = combined / combined.sum(dim=-1, keepdim=True)

                # Top-p filtering
                if top_p < 1.0:
                    sorted_probs, sorted_idx = torch.sort(combined, descending=True, dim=-1)
                    cumulative = torch.cumsum(sorted_probs, dim=-1)
                    remove = cumulative > top_p
                    remove[:, 1:] = remove[:, :-1].clone()
                    remove[:, 0] = False
                    for b in range(combined.shape[0]):
                        idx_to_remove = sorted_idx[b][remove[b]]
                        combined[b, idx_to_remove] = 0.0
                    combined = combined / combined.sum(dim=-1, keepdim=True)

                # Sampling
                next_token = torch.multinomial(combined, num_samples=1)

                # Concatener
                generated = torch.cat([generated, next_token], dim=-1)
                generated_set.add(next_token.item())

                # Infos
                token_score = float(combined[0, next_token[0, 0]].item())
                tokens_info.append({
                    'step': step,
                    'token_id': next_token.item(),
                    'score': token_score,
                    'lm_weight': 1 - self.resonance_weight,
                    'jepa_weight': self.resonance_weight,
                })

                # Arret si EOS
                if next_token.item() == 3:
                    break

        tokens_info.append({
            'unique_tokens': len(generated_set),
            'total_new_tokens': len(tokens_info),
            'diversity': len(generated_set) / max(len(tokens_info), 1),
        })

        return generated, tokens_info


# =========================================================================
# PIPELINE COMPLET
# =========================================================================

class HarmonicJEPAPipeline:
    """
    Pipeline complet : Tokenizer + Modele PUR + JEPA Generator.

    Usage:
        pipe = HarmonicJEPAPipeline()
        texte = pipe.generate("Le nombre d'or phi")
    """

    def __init__(self,
                 vocab_size: int = 5000,
                 hidden_size: int = 256,
                 num_layers: int = 4,
                 max_len: int = 512,
                 jepa_hidden: int = 64,
                 resonance_weight: float = 0.6):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from model.tokenizer import HarmonicTokenizer

        print("=" * 60)
        print("[HarmonicJEPAPipeline] Initialisation")
        print("=" * 60)

        # Tokenizer
        self.tokenizer = HarmonicTokenizer(vocab_size=vocab_size)
        actual_vocab = self.tokenizer.get_vocab_size()
        print(f"  Tokenizer: {actual_vocab} tokens")

        # Modele de base PUR
        self.model = HarmonicPureForCausalLM(
            vocab_size=actual_vocab,
            hidden_size=hidden_size,
            num_layers=num_layers,
            max_len=max_len,
        )
        model_params = sum(p.numel() for p in self.model.parameters())
        print(f"  Modele PUR: {model_params:,} params (0 entrainables)")

        # JEPA
        self.jepa = HarmonicJEPA(hidden_dim=jepa_hidden, num_abc_kernel=5)
        jepa_params = sum(p.numel() for p in self.jepa.parameters() if p.requires_grad)
        print(f"  JEPA predictor: {jepa_params:,} params (tout appris)")

        # Generator
        self.generator = JEPAGenerator(
            base_model=self.model,
            jepa_model=self.jepa,
            resonance_weight=resonance_weight,
        )
        total = sum(p.numel() for p in self.generator.parameters())
        trainable = sum(p.numel() for p in self.generator.parameters() if p.requires_grad)
        print(f"  Total: {total:,} params ({trainable:,} entrainables)")
        print(f"  Resonance weight: {resonance_weight}")

    def train_jepa(self, num_epochs: int = 30, batch_size: int = 16,
                   lr: float = 1e-3, verbose: bool = True) -> List[float]:
        """
        Entraine le predictor JEPA sur des signatures generees par le modele PUR.

        Les donnees d'entrainement sont produites en faisant forward
        sur le modele PUR avec des sequences aleatoires.

        Args:
            num_epochs: Nombre d'epochs
            batch_size: Taille du batch
            lr: Learning rate
            verbose: Afficher la progression

        Returns:
            losses: Historique des losses
        """
        # Generer des donnees d'entrainement : signatures 9D du modele PUR
        if verbose:
            print("\n[Entrainement JEPA] Generation des donnees...")

        num_seqs = 200
        seq_len = 16
        data = []

        with torch.no_grad():
            for _ in range(num_seqs):
                # Sequence de tokens aleatoires
                tokens = torch.randint(1, self.model.vocab_size - 1, (1, seq_len))
                _, signatures = self.model(tokens)  # [L, 1, S, 7]
                sig_7d = signatures[-1, 0]  # [S, 7]

                # Etendre en 9D
                S = sig_7d.shape[0]
                sig_9d = torch.zeros(S, 9)
                sig_9d[:, :7] = sig_7d
                sig_9d[:, 7] = 0.3 + 0.3 * torch.sin(torch.arange(S) * PHI)
                sig_9d[:, 8] = sig_7d[:, 0]

                data.append(sig_9d.unsqueeze(0))

        data = torch.cat(data, dim=0)  # [N, seq, 9]

        if verbose:
            print(f"  Dataset: {data.shape} ({num_seqs} sequences de {seq_len} signatures 9D)")

        # Optimiseur
        optimizer = torch.optim.AdamW(self.jepa.parameters(), lr=lr, weight_decay=1e-5)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs)

        # Entrainement
        losses = []

        for epoch in range(num_epochs):
            total_loss = 0.0
            num_batches = 0

            perm = torch.randperm(num_seqs)

            for i in range(0, num_seqs, batch_size):
                idx = perm[i:i + batch_size]
                batch = data[idx]
                loss = self.jepa.train_step(batch, optimizer)
                total_loss += loss
                num_batches += 1

            scheduler.step()
            avg_loss = total_loss / num_batches
            avg_res = self.jepa.get_average_resonance()
            losses.append(avg_loss)

            if verbose and (epoch + 1) % 10 == 0:
                print(f"  Epoch {epoch+1:3d}/{num_epochs} | "
                      f"Loss: {avg_loss:.6f} | Resonance: {avg_res:.4f} | "
                      f"LR: {scheduler.get_last_lr()[0]:.2e}")

        if verbose:
            final_res = self.jepa.get_average_resonance()
            print(f"\n  Final: Loss={losses[-1]:.6f} | Resonance={final_res:.4f}")
            print(f"  Amelioration: {(1-losses[-1]/losses[0])*100:.1f}%")

        return losses

    def generate(self,
                 prompt: str,
                 max_new_tokens: int = 40,
                 temperature: float = 0.85,
                 top_k: int = 30,
                 top_p: float = 0.92,
                 repetition_penalty: float = 1.3,
                 use_jepa: bool = True) -> str:
        """
        Genere du texte a partir d'un prompt.

        Args:
            prompt: Texte d'entree
            max_new_tokens: Nombre de tokens a generer
            temperature: Temperature du sampling
            top_k: Top-k filtering
            top_p: Top-p nucleus sampling
            repetition_penalty: Penalite de repetition
            use_jepa: Utiliser JEPA (True) ou LM Head seul (False)

        Returns:
            Texte genere
        """
        # Encoder
        tokens = self.tokenizer.encode(prompt)
        input_ids = torch.tensor([tokens], dtype=torch.long)

        # Generer
        generated, info = self.generator.forward(
            input_ids,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            use_jepa=use_jepa
        )

        # Decoder
        full_text = self.tokenizer.decode(generated[0].tolist())

        return full_text

    def benchmark(self, prompts: List[str] = None, verbose: bool = True) -> Dict:
        """
        Benchmark du pipeline complet.

        Teste la generation avec et sans JEPA, et compare la diversite.

        Args:
            prompts: Liste de prompts a tester (utilise des defauts si None)

        Returns:
            results: Dictionnaire des resultats
        """
        if prompts is None:
            prompts = [
                "Le nombre d or",
                "La conscience est",
                "Dans l univers",
                "La verite est",
                "Le sens de la",
            ]

        results = {}

        for mode, use_jepa in [('LM Head seul', False), ('JEPA guide', True)]:
            if verbose:
                print(f"\n--- Mode: {mode} ---")

            all_tokens = []
            all_unique = []

            for prompt in prompts:
                text = self.generate(
                    prompt,
                    max_new_tokens=30,
                    temperature=0.85,
                    top_k=30,
                    top_p=0.92,
                    repetition_penalty=1.3,
                    use_jepa=use_jepa
                )

                # Compter la diversite
                tokens = self.tokenizer.encode(text)
                new_tokens = tokens[len(self.tokenizer.encode(prompt)):]
                unique_ratio = len(set(new_tokens)) / max(len(new_tokens), 1)

                all_tokens.extend(new_tokens)
                all_unique.append(unique_ratio)

                if verbose:
                    n_tokens = min(len(text), 100)
                    print(f"  [{prompt:25s}] -> {text[:n_tokens]:.80s}")
                    print(f"    Tokens: {len(new_tokens)}, Uniques: {len(set(new_tokens))}, "
                          f"Ratio: {unique_ratio:.2f}")

            avg_diversity = sum(all_unique) / len(all_unique)
            global_unique = len(set(all_tokens)) / max(len(all_tokens), 1)

            results[mode] = {
                'avg_diversity': avg_diversity,
                'global_unique_ratio': global_unique,
                'total_tokens': len(all_tokens),
                'unique_tokens': len(set(all_tokens)),
            }

            if verbose:
                print(f"\n  [{mode}] Diversite moyenne: {avg_diversity:.3f}")
                print(f"  [{mode}] Ratio unique global: {global_unique:.3f}")

        if verbose:
            if 'JEPA guide' in results and 'LM Head seul' in results:
                improvement = (
                    (results['JEPA guide']['global_unique_ratio'] -
                     results['LM Head seul']['global_unique_ratio']) /
                    max(results['LM Head seul']['global_unique_ratio'], 0.01) * 100
                )
                print(f"\n  => Amelioration JEPA: {improvement:+.1f}% diversite")

        return results


# =========================================================================
# TEST UNIQUE
# =========================================================================

def test_jepa_generator():
    """Test complet du pipeline JEPA Generator."""
    print("=" * 70)
    print("TEST DU JEPA GENERATOR + PIPELINE COMPLET")
    print("=" * 70)

    # 1. Initialisation
    print("\n[1] Initialisation du pipeline...")
    pipe = HarmonicJEPAPipeline(
        vocab_size=5000,
        hidden_size=256,
        num_layers=4,
        max_len=512,
        jepa_hidden=64,
        resonance_weight=0.6
    )

    # 2. Test sans JEPA (baseline)
    print("\n[2] Test SANS JEPA (LM Head seul)...")
    for prompt in ["Le nombre d or", "La conscience"]:
        text = pipe.generate(prompt, max_new_tokens=20, use_jepa=False)
        print(f"  [{prompt}] -> {text[:90]}")
        tokens = pipe.tokenizer.encode(text)
        new_t = tokens[len(pipe.tokenizer.encode(prompt)):]
        print(f"    Tokens: {len(new_t)}, Uniques: {len(set(new_t))}")

    # 3. Entrainement JEPA
    print("\n[3] Entrainement du predictor JEPA...")
    losses = pipe.train_jepa(num_epochs=15, batch_size=16, lr=5e-3)
    print(f"  Loss initiale: {losses[0]:.6f} -> Finale: {losses[-1]:.6f}")

    # 4. Test AVEC JEPA
    print("\n[4] Test AVEC JEPA (resonance guide)...")
    for prompt in ["Le nombre d or", "La conscience"]:
        text = pipe.generate(prompt, max_new_tokens=20, use_jepa=True)
        print(f"  [{prompt}] -> {text[:90]}")
        tokens = pipe.tokenizer.encode(text)
        new_t = tokens[len(pipe.tokenizer.encode(prompt)):]
        print(f"    Tokens: {len(new_t)}, Uniques: {len(set(new_t))}")

    # 5. Benchmark
    print("\n[5] Benchmark SANS JEPA...")
    pipe.benchmark(verbose=True)

    print(f"\n{'='*70}")
    print("TEST TERMINE")
    print("=" * 70)

    return pipe


if __name__ == '__main__':
    test_jepa_generator()
