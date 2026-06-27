"""
Harmonic AR Generator
=====================
Generation Autoregressive harmonique par resonance d'embedding directe.

Probleme resolu :
    Le LM Head fixe (embedding.T @ hidden * PHI) crée un biais
    systematique vers les memes tokens a chaque generation car
    les embeddings harmoniques ont des normes differentes.

Solution :
    Au lieu de predire un ID de token, on predit l'EMBEDDING 256D
    du prochain token dans l'espace latent harmonique.
    
    x[t-n:t] -> HarmonicPure -> Embedding predit [256D]
    -> Cosine similarity avec TOUS les embeddings du vocabulaire
    -> Le token le plus "resonant" est selectionne

    Le LM Head devient inutile pour la selection finale.
    Le predictor d'embedding (50K params) remplace le LM Head.

Resonance d'embedding :
    Pour chaque token du vocabulaire, on a son embedding harmonique.
    "resonance(pred, tok_i) = cos(pred, embedding_i)"
    On choisit le token avec la plus haute resonance.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Optional, Tuple
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.harmonic_pure_model import HarmonicPureForCausalLM
from model.abc_kernel import PHI, ALPHA


class EmbeddingPredictor(nn.Module):
    """
    Predicteur d'embedding 256D pour le prochain token.
    
    Prend des embeddings contextuels et predit l'embedding du prochain.
    
    Args:
        hidden_dim: Dimension des embeddings (256)
        context_len: Fenetre de contexte (8 tokens)
    """
    
    def __init__(self, hidden_dim: int = 256, context_len: int = 8):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.context_len = context_len
        
        # Poids ABC temporels fixes
        t = torch.arange(context_len, dtype=torch.float32)
        abc_w = torch.exp(-ALPHA * t) * torch.cos(PHI * t / context_len)
        abc_w = abc_w / (abc_w.sum() + 1e-8)
        self.register_buffer('abc_weights', abc_w)
        
        # MLP leger (seule partie apprise)
        self.mlp = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2, bias=False),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, hidden_dim, bias=False),
        )
        self.norm = nn.LayerNorm(hidden_dim)
        
        self._init_weights()
    
    def _init_weights(self):
        with torch.no_grad():
            for p in self.parameters():
                if p.ndim >= 2:
                    nn.init.normal_(p, std=PHI / math.sqrt(p.shape[1]))
    
    def forward(self, embeddings: torch.Tensor) -> torch.Tensor:
        """
        Predire l'embedding du prochain token.
        
        Args:
            embeddings: [batch, seq_len, hidden_dim]
        
        Returns:
            pred: [batch, hidden_dim] embedding predit
        """
        B, S, D = embeddings.shape
        
        # Moyenne ponderee temporelle ABC
        ctx = min(self.context_len, S)
        last_embs = embeddings[:, -ctx:, :]
        w = self.abc_weights[:ctx].view(1, ctx, 1)
        weighted = (last_embs * w).sum(dim=1)  # [B, D]
        
        # MLP
        pred = self.mlp(weighted)
        pred = self.norm(pred)
        
        return pred


class ARGenerator(nn.Module):
    """
    Generateur Autoregressif Harmonique.
    
    Selectionne le token par resonance d'embedding.
    
    Args:
        base_model: HarmonicPureForCausalLM
        predictor: EmbeddingPredictor (optionnel)
        lm_head_weight: Poids residuel du LM Head (0-1)
    """
    
    def __init__(self,
                 base_model: HarmonicPureForCausalLM,
                 predictor: Optional[EmbeddingPredictor] = None,
                 lm_head_weight: float = 0.2):
        super().__init__()
        
        self.base_model = base_model
        self.embedding = base_model.token_embedding
        self.lm_head = base_model.lm_head
        self.lm_head_weight = lm_head_weight
        
        self.predictor = predictor or EmbeddingPredictor(
            hidden_dim=base_model.hidden_size, context_len=8
        )
        
        # Pre-calculer les embeddings normalises du vocabulaire
        with torch.no_grad():
            V = self.embedding.vocab_size
            all_ids = torch.arange(V, dtype=torch.long)
            all_embs = self.embedding(all_ids.unsqueeze(0))[0]
            self.register_buffer('vocab_emb', F.normalize(all_embs, dim=-1))
    
    @torch.no_grad()
    def forward(self,
                input_ids: torch.Tensor,
                max_new_tokens: int = 50,
                temperature: float = 0.85,
                top_k: int = 40,
                top_p: float = 0.92,
                repetition_penalty: float = 1.3,
                use_resonance: bool = True) -> Tuple[torch.Tensor, List]:
        """
        Generation.
        
        Args:
            input_ids: [batch, seq_len]
            max_new_tokens: max tokens
            temperature: sampling temperature
            top_k: top-k filtering
            top_p: nucleus sampling
            repetition_penalty: >1.0 penalise repetition
            use_resonance: resonance embedding vs LM Head
        
        Returns:
            generated, tokens_info
        """
        generated = input_ids.clone()
        info = []
        token_hist = []
        
        for step in range(max_new_tokens):
            if generated.shape[1] > self.base_model.max_len:
                generated = generated[:, -self.base_model.max_len:]
            
            # Forward
            logits, signatures = self.base_model(generated)
            next_logits = logits[:, -1, :].clone()  # [1, V]
            
            # Repetition penalty
            if repetition_penalty > 1.0:
                for tok in generated[0, -50:]:
                    if next_logits[0, tok] < 0:
                        next_logits[0, tok] *= repetition_penalty
                    else:
                        next_logits[0, tok] /= repetition_penalty
            
            # Resonance embedding
            if use_resonance and generated.shape[1] >= 3:
                # Embedding predit
                ctx_embs = self.embedding(generated[:, -8:])  # [1, ctx, D]
                pred_emb = self.predictor(ctx_embs)  # [1, D]
                pred_norm = F.normalize(pred_emb, dim=-1)
                
                # Scores de resonance avec tout le vocabulaire
                resonance = torch.mm(pred_norm, self.vocab_emb.T)[0]  # [V]
                res_probs = (resonance + 1.0) / 2.0  # normalise [0, 1]
                res_probs = res_probs / res_probs.sum()
                
                # Penaliser les tokens deja choisis (diversite)
                for tok in token_hist[-15:]:
                    res_probs[tok] *= 0.85
                res_probs = res_probs / res_probs.sum()
            else:
                res_probs = torch.ones(next_logits.shape[-1]) / next_logits.shape[-1]
            
            # Combinaison
            lm_probs = F.softmax(next_logits / temperature, dim=-1)
            
            if use_resonance:
                combined = (1 - self.lm_head_weight) * res_probs.unsqueeze(0) + \
                           self.lm_head_weight * lm_probs
            else:
                combined = lm_probs
            
            combined = combined / combined.sum(dim=-1, keepdim=True)
            
            # Top-k
            if top_k > 0:
                vals, idx = torch.topk(combined, min(top_k, combined.shape[-1]), dim=-1)
                combined = torch.zeros_like(combined)
                combined.scatter_(1, idx, vals)
                combined = combined / combined.sum(dim=-1, keepdim=True)
            
            # Top-p
            if top_p < 1.0:
                sp, si = torch.sort(combined, descending=True, dim=-1)
                cum = torch.cumsum(sp, dim=-1)
                rmv = cum > top_p
                rmv[:, 1:] = rmv[:, :-1].clone()
                rmv[:, 0] = False
                for b in range(combined.shape[0]):
                    idx_rmv = si[b][rmv[b]]
                    combined[b, idx_rmv] = 0.0
                combined = combined / combined.sum(dim=-1, keepdim=True)
            
            # Sampling
            next_tok = torch.multinomial(combined, num_samples=1)
            generated = torch.cat([generated, next_tok], dim=-1)
            token_hist.append(next_tok.item())
            
            info.append({
                'step': step,
                'token_id': next_tok.item(),
                'prob': float(combined[0, next_tok.item()]),
                'use_resonance': use_resonance,
            })
            
            if next_tok.item() == 3:
                break
        
        info.append({
            'unique': len(set(token_hist)),
            'total': len(token_hist),
            'diversity': len(set(token_hist)) / max(len(token_hist), 1),
        })
        
        return generated, info


class HarmonicARGeneratorPipeline:
    """
    Pipeline complet Tokenizer + Modele PUR + AR Generator.
    """
    
    def __init__(self, vocab_size=5000, hidden_size=256, num_layers=4, max_len=512, lr=5e-3):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from model.tokenizer import HarmonicTokenizer
        
        self.tokenizer = HarmonicTokenizer(vocab_size=vocab_size)
        actual_vocab = self.tokenizer.get_vocab_size()
        
        self.model = HarmonicPureForCausalLM(
            vocab_size=actual_vocab, hidden_size=hidden_size,
            num_layers=num_layers, max_len=max_len,
        )
        
        self.generator = ARGenerator(self.model, lm_head_weight=0.2)
        self.lr = lr
        
        n_p = sum(p.numel() for p in self.generator.predictor.parameters() if p.requires_grad)
        print(f"[AR] Vocab={actual_vocab} Predictor={n_p:,} params")
    
    def train(self, num_epochs=30, verbose=True):
        """Entraine le predictor d'embedding."""
        num_seqs = 300
        seq_len = 16
        
        inputs, targets = [], []
        with torch.no_grad():
            for _ in range(num_seqs):
                tokens = torch.randint(1, self.model.vocab_size - 1, (1, seq_len))
                ctx_embs = self.model.token_embedding(tokens[:, :-1])
                tgt_embs = self.model.token_embedding(tokens[:, 1:])
                inputs.append(ctx_embs)
                targets.append(tgt_embs[:, -1, :])
        
        X = torch.cat(inputs, dim=0)
        Y = torch.cat(targets, dim=0)
        
        opt = torch.optim.AdamW(self.generator.predictor.parameters(), lr=self.lr, weight_decay=1e-4)
        losses = []
        bs = 32
        n = X.shape[0]
        
        for ep in range(num_epochs):
            total = 0.0
            nb = 0
            perm = torch.randperm(n)
            for i in range(0, n, bs):
                idx = perm[i:i+bs]
                bx, by = X[idx], Y[idx]
                opt.zero_grad()
                pred = self.generator.predictor(bx)
                loss = 1.0 - F.cosine_similarity(pred, by, dim=-1).mean()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.generator.predictor.parameters(), 1.0)
                opt.step()
                total += loss.item()
                nb += 1
            avg = total / nb
            losses.append(avg)
            if verbose and (ep+1) % 10 == 0:
                print(f"  Epoch {ep+1:3d}/{num_epochs} | Loss: {avg:.6f} | Res: {1-avg:.4f}")
        
        if verbose:
            print(f"  Final: Loss={losses[-1]:.6f} Improve={(1-losses[-1]/losses[0])*100:.1f}%")
        return losses
    
    def generate(self, prompt, max_new=40, temp=0.85, top_k=30, top_p=0.92, rep=1.3, use_res=True):
        tokens = self.tokenizer.encode(prompt)
        inp = torch.tensor([tokens], dtype=torch.long)
        gen, info = self.generator.forward(inp, max_new_tokens=max_new, temperature=temp,
                                            top_k=top_k, top_p=top_p, repetition_penalty=rep,
                                            use_resonance=use_res)
        text = self.tokenizer.decode(gen[0].tolist())
        return text, info
    
    def benchmark(self):
        """Benchmark comparatif."""
        prompts = [
            "Le nombre d or", "La conscience est", "Dans l univers",
            "La verite est", "Le sens de la", "Harmonic resonance",
        ]
        
        for mode, use_res in [("LM Head", False), ("Resonance", True)]:
            print(f"\n--- {mode} ---")
            all_new = []
            for p in prompts:
                text, info = self.generate(p, max_new=25, use_res=use_res)
                new_ids = self.tokenizer.encode(text)[len(self.tokenizer.encode(p)):]
                unique = len(set(new_ids))
                ratio = unique / max(len(new_ids), 1)
                all_new.extend(new_ids)
                print(f"  [{p}] {text[:80]:.80s}")
                print(f"    {len(new_ids)} tokens, {unique} uniques ({ratio:.2f})")
            total_u = len(set(all_new))
            total_n = len(all_new)
            print(f"  [{mode}] Total: {total_u}/{total_n} uniques = {total_u/max(total_n,1):.3f}")


def test():
    """Test complet."""
    pipe = HarmonicARGeneratorPipeline()
    
    print("\n[1] Baseline LM Head...")
    pipe.benchmark()
    
    print("\n[2] Entrainement...")
    pipe.train(num_epochs=20)
    
    print("\n[3] Resonance Embedding...")
    pipe.benchmark()
    
    return pipe


if __name__ == '__main__':
    test()
