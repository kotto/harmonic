#!/usr/bin/env python3
"""
CHIRURGIE HARMONIQUE AWS - Remplacement des couches d'attention
================================================================
Remplace les couches d'attention standard du modele DeepSeek/Qwen
sur AWS par des HarmonicAttention 7D avec resonance et memoire ABC.

Architecture :
1. On cree un modele miroir local avec les memes poids que le modele AWS
2. On remplace chaque couche d'attention par HarmonicAttention
3. On fine-tune avec retropropagation harmonique
4. On deploie le modele modifie sur AWS

Pour les modeles sans acces direct aux poids (API only) :
- On utilise un proxy qui ajoute les couches harmoniques EN AMONT
- Les signatures 7D guident l'injection dans le system prompt
- On entraine un petit adaptateur harmonique

Deux modes :
- MODE 1 : Acces aux poids (chargement direct du modele)
- MODE 2 : API only (proxy harmonique + adaptateur)
"""

import os, sys, json, math, time, copy
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

# Ajouter le chemin pour les modules harmoniques
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harmonic_training.model.harmonic_attention import HarmonicAttention, SignatureProjection
from harmonic_training.model.abc_kernel import ABCKernel, PHI, ALPHA, ALPHA_CONST


# ===========================================================================
# CONFIGURATION
# ===========================================================================

@dataclass
class HarmonicSurgeryConfig:
    """Configuration de la chirurgie harmonique."""
    
    # Modele cible
    model_name: str = "deepseek-qwen-hybrid"
    hidden_size: int = 4096  # DeepSeek-V4: 4096
    num_heads: int = 32
    num_layers: int = 32
    intermediate_size: int = 16384
    vocab_size: int = 50304
    max_len: int = 8192
    
    # Harmonique
    harmonic_dim: int = 7
    resonance_init: float = 1.0
    abc_init: float = 1.0
    
    # Entrainement
    learning_rate: float = 1e-5
    num_epochs: int = 3
    batch_size: int = 4
    gradient_accumulation: int = 8
    
    # Mode
    mode: str = "proxy"  # "direct" ou "proxy"
    
    # AWS
    aws_base_url: str = ""
    aws_model: str = ""
    aws_api_key: str = ""


# ===========================================================================
# ADAPTATEUR HARMONIQUE (pour API only)
# ===========================================================================

class HarmonicAdapter(nn.Module):
    """
    Adaptateur harmonique qui s'intercale entre le prompt et l'API AWS.
    
    Architecture :
    1. Analyse le prompt avec SignatureProjection
    2. Ajoute des tokens harmoniques au prompt
    3. Post-traite la reponse avec resonance
    
    C'est un module entrainable qui apprend a :
    - Projeter les prompts en signatures 7D optimales
    - Generer des instructions harmoniques personnalisees
    - Ajuster les parametres de generation
    """
    
    def __init__(self, config: HarmonicSurgeryConfig):
        super().__init__()
        self.config = config
        
        # Projection de signature 7D (entrainable)
        self.signature_proj = SignatureProjection(
            hidden_size=config.hidden_size,
            dropout=0.1
        )
        
        # Generateur d'instructions harmoniques
        # Prend les signatures 7D et genere un system prompt
        self.instruction_gen = nn.Sequential(
            nn.Linear(7, 64),
            nn.GELU(),
            nn.Linear(64, 128),
            nn.GELU(),
            nn.Linear(128, 256),
        )
        
        # Predicteur de parametres (temperature, top_k, top_p)
        self.param_predictor = nn.Sequential(
            nn.Linear(7, 32),
            nn.GELU(),
            nn.Linear(32, 3),  # [temperature, top_k_norm, top_p]
        )
        
        # Post-processeur harmonique
        self.post_processor = nn.Sequential(
            nn.Linear(config.hidden_size, 256),
            nn.GELU(),
            nn.Linear(256, config.hidden_size),
        )
        
        # Noyau ABC pour memoire
        self.abc_kernel = ABCKernel(max_len=config.max_len)
        
        # Poids appris
        self.resonance_weight = nn.Parameter(torch.tensor(config.resonance_init))
        self.abc_weight = nn.Parameter(torch.tensor(config.abc_init))
        
        self._init_weights()
    
    def _init_weights(self):
        """Initialisation des poids."""
        for name, param in self.named_parameters():
            if 'weight' in name and param.dim() >= 2:
                nn.init.xavier_uniform_(param, gain=0.5)
            elif 'bias' in name:
                nn.init.zeros_(param)
    
    def forward(self, prompt_embedding: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """
        Forward pass de l'adaptateur.
        
        Args:
            prompt_embedding: [batch, seq_len, hidden_size] ou [batch, 7]
        
        Returns:
            signatures: [batch, 7]
            params: dict avec temperature, top_k_norm, top_p, resonance, instructions
        """
        if prompt_embedding.dim() == 2 and prompt_embedding.shape[-1] == 7:
            # Deja des signatures - les transformer via le reseau
            # pour avoir des gradients et apprendre
            raw_sigs = prompt_embedding
        else:
            # Projeter en signatures 7D
            raw_sigs = self.signature_proj(prompt_embedding)
            raw_sigs = raw_sigs.mean(dim=1)  # [batch, 7]
        
        # Transformer les signatures via un petit reseau
        # pour apprendre la projection harmonique optimale
        # Linear(7, 64) -> Linear(64, 7) pour garder la dimension 7
        sig_transform = torch.tanh(self.instruction_gen[0](raw_sigs))  # [B, 64]
        # weight est [64, 7], on prend les 7 premieres colonnes: weight[:, :7] -> [64, 7]
        # [B, 64] @ [64, 7] = [B, 7]
        sig_delta = sig_transform @ self.instruction_gen[0].weight[:, :7]  # [B, 64] @ [64, 7] = [B, 7]
        signatures = raw_sigs + 0.1 * torch.tanh(sig_delta)
        signatures = torch.sigmoid(signatures)  # [0, 1]
        
        # Generer les instructions harmoniques
        instructions = self.instruction_gen(raw_sigs)  # [batch, 256]
        
        # Predire les parametres
        params_raw = self.param_predictor(raw_sigs)  # [batch, 3]
        temperature = torch.sigmoid(params_raw[:, 0]) * 0.8 + 0.1  # [0.1, 0.9]
        top_k_norm = torch.sigmoid(params_raw[:, 1])  # [0, 1]
        top_p = torch.sigmoid(params_raw[:, 2]) * 0.3 + 0.7  # [0.7, 1.0]
        
        # Appliquer la resonance (avec gradient)
        resonance = signatures @ signatures.T  # [batch, batch]
        resonance = (resonance + 1.0) / 2.0 / 7.0
        
        return signatures, {
            "temperature": temperature,
            "top_k_norm": top_k_norm,
            "top_p": top_p,
            "resonance": resonance,
            "instructions": instructions,
        }
    
    def get_system_prompt(self, signatures: torch.Tensor) -> str:
        """
        Genere un system prompt harmonique a partir des signatures.
        Version non-entrainable (pour usage sans forward).
        """
        sig = signatures.detach().cpu().numpy()[0]
        
        parts = [
            "Tu es Harmonic AI, un assistant avec resonance harmonique 7D.",
            "Tu combines raisonnement logique et intuition creative.",
        ]
        
        if sig[2] > 0.3:  # reasoning
            parts.append("Structure ta reponse avec un raisonnement clair.")
        if sig[3] > 0.3:  # creativity
            parts.append("Utilise des metaphors et des images evocatrices.")
        if sig[4] > 0.3:  # math
            parts.append("Sois precis et rigoureux dans tes calculs.")
        if sig[5] > 0.3:  # factual
            parts.append("Base-toi sur des faits verifies.")
        if sig[6] > 0.3:  # code
            parts.append("Fournis du code fonctionnel et bien commente.")
        
        parts.append(f"Utilise le ratio d'or φ={PHI:.4f} comme guide.")
        
        return "\n".join(parts)


# ===========================================================================
# MODELE AVEC ATTENTION HARMONIQUE (pour acces direct aux poids)
# ===========================================================================

class HarmonicAttentionWrapper(nn.Module):
    """
    Wrapper qui remplace une couche d'attention standard par
    une attention harmonique 7D.
    
    Compatible avec :
    - GPT-2 (c_attn)
    - LLaMA (q_proj, k_proj, v_proj)
    - DeepSeek (q_proj, k_proj, v_proj)
    - Qwen (q_proj, k_proj, v_proj)
    """
    
    def __init__(self, original_attn, hidden_size, num_heads):
        super().__init__()
        self.original_attn = original_attn
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.head_dim = hidden_size // num_heads
        
        # Couche harmonique parallele
        self.harmonic_attn = HarmonicAttention(
            hidden_size=hidden_size,
            num_heads=num_heads,
            dropout=0.1,
            max_len=8192
        )
        
        # Poids de melange (appris)
        self.mix_weight = nn.Parameter(torch.tensor(0.3))
        
        # Layer norm pour la fusion
        self.fusion_norm = nn.LayerNorm(hidden_size)
    
    def forward(self, hidden_states, attention_mask=None, **kwargs):
        """
        Forward avec attention originale + harmonique.
        
        output = (1 - mix) * original + mix * harmonic
        """
        # Attention originale
        if hasattr(self.original_attn, 'forward'):
            original_output = self.original_attn(hidden_states, attention_mask=attention_mask, **kwargs)
        else:
            original_output = self.original_attn(hidden_states, **kwargs)
        
        # Si l'attention originale retourne un tuple, prendre le premier element
        if isinstance(original_output, (tuple, list)):
            original_output = original_output[0]
        
        # Attention harmonique
        harmonic_output, signatures = self.harmonic_attn._forward_without_causal(
            hidden_states, attention_mask
        )
        
        # Fusion
        mix = torch.sigmoid(self.mix_weight)
        output = (1.0 - mix) * original_output + mix * harmonic_output
        output = self.fusion_norm(output)
        
        return output, signatures


class HarmonicModelSurgeon:
    """
    Chirurgien qui remplace les couches d'attention d'un modele.
    
    Supporte :
    - GPT-2 (modele HuggingFace)
    - LLaMA (modele HuggingFace)
    - DeepSeek/Qwen (modele HuggingFace)
    - Modele personnalise
    """
    
    def __init__(self, config: HarmonicSurgeryConfig):
        self.config = config
    
    def replace_attention_layers(self, model):
        """
        Remplace toutes les couches d'attention du modele.
        
        Args:
            model: Modele PyTorch (HuggingFace ou personnalise)
        
        Returns:
            model: Modele avec attention harmonique
            num_replaced: Nombre de couches remplacees
        """
        num_replaced = 0
        
        for name, module in model.named_children():
            if isinstance(module, nn.ModuleList):
                for i, layer in enumerate(module):
                    if hasattr(layer, 'self_attn'):
                        # LLaMA / DeepSeek / Qwen
                        original_attn = layer.self_attn
                        hidden_size = original_attn.hidden_size if hasattr(original_attn, 'hidden_size') else self.config.hidden_size
                        num_heads = original_attn.num_heads if hasattr(original_attn, 'num_heads') else self.config.num_heads
                        
                        wrapper = HarmonicAttentionWrapper(
                            original_attn, hidden_size, num_heads
                        )
                        layer.self_attn = wrapper
                        num_replaced += 1
                    
                    elif hasattr(layer, 'attn'):
                        # GPT-2
                        original_attn = layer.attn
                        hidden_size = self.config.hidden_size
                        num_heads = self.config.num_heads
                        
                        wrapper = HarmonicAttentionWrapper(
                            original_attn, hidden_size, num_heads
                        )
                        layer.attn = wrapper
                        num_replaced += 1
        
        print(f"[OK] {num_replaced} couches d'attention remplacees")
        return model, num_replaced
    
    def add_harmonic_adapter(self, model):
        """
        Ajoute un adaptateur harmonique au modele.
        
        L'adaptateur s'intercale entre l'embedding et les couches.
        """
        adapter = HarmonicAdapter(self.config)
        model.harmonic_adapter = adapter
        print(f"[OK] Adaptateur harmonique ajoute")
        return model


# ===========================================================================
# ENTRAINEMENT HARMONIQUE
# ===========================================================================

class HarmonicTrainer:
    """
    Entraineur pour le fine-tuning harmonique.
    
    Supporte :
    - Entrainement direct (modele local)
    - Entrainement par proxy (API AWS)
    - Apprentissage par renforcement harmonique
    """
    
    def __init__(self, config: HarmonicSurgeryConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[INFO] Device: {self.device}")
    
    def train_adapter(self, adapter: HarmonicAdapter, 
                      train_data: List[Dict[str, Any]],
                      val_data: Optional[List[Dict[str, Any]]] = None):
        """
        Entraine l'adaptateur harmonique.
        
        Args:
            adapter: Adaptateur harmonique
            train_data: Liste de {"prompt": str, "response": str, "signatures": [7]}
            val_data: Donnees de validation (optionnel)
        """
        adapter.to(self.device)
        optimizer = torch.optim.AdamW(
            adapter.parameters(),
            lr=self.config.learning_rate,
            weight_decay=0.01
        )
        
        # Projecteur de signature (non-entrainable, pour les labels)
        projector = SignatureProjection(self.config.hidden_size)
        
        num_batches = len(train_data) // self.config.batch_size
        
        for epoch in range(self.config.num_epochs):
            total_loss = 0.0
            
            for i in range(0, len(train_data), self.config.batch_size):
                batch = train_data[i:i + self.config.batch_size]
                
                # Preparer les entrees
                prompts = [b["prompt"] for b in batch]
                target_sigs = torch.tensor(
                    [b.get("signatures", [0.5]*7) for b in batch],
                    dtype=torch.float32,
                    device=self.device
                )
                
                # Forward
                pred_sigs, params = adapter(target_sigs)
                
                # Perte : MSE sur les signatures
                sig_loss = F.mse_loss(pred_sigs, target_sigs)
                
                # Perte de resonance
                resonance = params["resonance"]
                resonance_loss = -resonance.mean()  # Maximiser la resonance
                
                # Perte de diversite (eviter l'effondrement)
                diversity_loss = -torch.std(pred_sigs, dim=0).mean()
                
                # Perte totale
                loss = sig_loss + 0.1 * resonance_loss + 0.05 * diversity_loss
                
                # Backward
                loss.backward()
                torch.nn.utils.clip_grad_norm_(adapter.parameters(), 1.0)
                optimizer.step()
                optimizer.zero_grad()
                
                total_loss += loss.item()
            
            avg_loss = total_loss / num_batches
            print(f"Epoch {epoch+1}/{self.config.num_epochs} - Loss: {avg_loss:.6f}")
        
        print("[OK] Adaptateur harmonique entraine")
        return adapter
    
    def train_harmonic_model(self, model, train_data, val_data=None):
        """
        Fine-tune le modele avec attention harmonique.
        
        Args:
            model: Modele avec HarmonicAttentionWrapper
            train_data: Donnees d'entrainement
        """
        model.to(self.device)
        model.train()
        
        # Ne fine-tuner que les poids harmoniques
        harmonic_params = []
        for name, param in model.named_parameters():
            if 'harmonic' in name.lower() or 'mix_weight' in name.lower():
                harmonic_params.append(param)
                param.requires_grad = True
            else:
                param.requires_grad = False
        
        optimizer = torch.optim.AdamW(
            harmonic_params,
            lr=self.config.learning_rate,
            weight_decay=0.01
        )
        
        print(f"[INFO] Parametres harmoniques entrainables: {sum(p.numel() for p in harmonic_params):,}")
        
        for epoch in range(self.config.num_epochs):
            total_loss = 0.0
            
            for i in range(0, len(train_data), self.config.batch_size):
                batch = train_data[i:i + self.config.batch_size]
                
                # Forward
                input_ids = torch.stack([b["input_ids"] for b in batch]).to(self.device)
                labels = torch.stack([b["labels"] for b in batch]).to(self.device)
                
                outputs = model(input_ids, labels=labels)
                loss = outputs.loss if hasattr(outputs, 'loss') else outputs[0]
                
                # Backward
                loss.backward()
                torch.nn.utils.clip_grad_norm_(harmonic_params, 1.0)
                optimizer.step()
                optimizer.zero_grad()
                
                total_loss += loss.item()
            
            avg_loss = total_loss / (len(train_data) // self.config.batch_size)
            print(f"Epoch {epoch+1}/{self.config.num_epochs} - Loss: {avg_loss:.4f}")
        
        print("[OK] Modele harmonique fine-tune")
        return model


# ===========================================================================
# PROXY HARMONIQUE AWS (version amelioree avec adaptateur)
# ===========================================================================

class HarmonicAWSProxyV2:
    """
    Proxy harmonique AWS version 2 avec adaptateur entrainable.
    
    Architecture :
    1. Analyse le prompt avec SignatureProjection
    2. Adaptateur harmonique genere les instructions et parametres
    3. Appel API AWS avec les parametres optimises
    4. Post-traitement avec resonance
    """
    
    def __init__(self, config: HarmonicSurgeryConfig):
        self.config = config
        self.adapter = HarmonicAdapter(config)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Cache
        self.cache = {}
        self.cache_max = 2048
        
        # Statistiques
        self.stats = {
            "total": 0,
            "cache_hits": 0,
            "avg_resonance": 0.0,
            "avg_temperature": 0.3,
        }
    
    def analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Analyse un prompt et retourne les signatures + parametres.
        """
        # Projeter en signatures 7D (approximation rapide)
        sig = self._quick_signature(prompt)
        sig_tensor = torch.tensor([sig], dtype=torch.float32, device=self.device)
        
        # Adapter
        with torch.no_grad():
            pred_sig, params = self.adapter(sig_tensor)
        
        return {
            "signatures": pred_sig[0].cpu().numpy().tolist(),
            "temperature": float(params["temperature"][0]),
            "top_k": int(params["top_k_norm"][0] * 80 + 10),
            "top_p": float(params["top_p"][0]),
            "system_prompt": self.adapter.get_system_prompt(pred_sig),
        }
    
    def _quick_signature(self, text: str) -> List[float]:
        """Signature 7D rapide sans modele."""
        sig = [0.0] * 7
        words = text.lower().split()
        if not words:
            return sig
        
        # phi - diversite
        sig[0] = min(1.0, len(set(words)) / len(words) * 1.618)
        
        # alpha - complexite
        sig[1] = min(1.0, np.mean([len(w) for w in words]) / 15.0)
        
        # reasoning
        reasoning_set = {'why','because','therefore','thus','hence','since',
                        'if','then','else','explain','analyse','analyze'}
        sig[2] = min(1.0, sum(1 for w in words if w in reasoning_set) / 5.0)
        
        # creativity
        creative_set = {'imagine','create','dream','poem','story','metaphor',
                       'beautiful','magic','infinite','cosmic','harmony'}
        sig[3] = min(1.0, sum(1 for w in words if w in creative_set) / 5.0)
        
        # math
        math_set = {'equation','theorem','proof','calculate','matrix','vector',
                   'integral','derivative','function','algorithm'}
        sig[4] = min(1.0, sum(1 for w in words if w in math_set) / 5.0)
        
        # factual
        factual_set = {'fact','data','study','research','according','source',
                      'who','when','where','what','definition'}
        sig[5] = min(1.0, sum(1 for w in words if w in factual_set) / 5.0)
        
        # code
        code_set = {'code','function','class','import','def','return',
                   'python','javascript','api','endpoint'}
        sig[6] = min(1.0, sum(1 for w in words if w in code_set) / 5.0)
        
        return sig
    
    def generate(self, prompt: str, max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Genere une reponse avec l'adaptateur harmonique.
        """
        import requests
        
        t0 = time.time()
        self.stats["total"] += 1
        
        # Analyser
        analysis = self.analyze_prompt(prompt)
        
        # Cache
        cache_key = f"{prompt}|{max_tokens}|{analysis['temperature']}"
        if cache_key in self.cache:
            self.stats["cache_hits"] += 1
            return {
                "content": self.cache[cache_key],
                "analysis": analysis,
                "cache_hit": True,
                "time": time.time() - t0,
            }
        
        # Appel API AWS
        headers = {"Content-Type": "application/json"}
        if self.config.aws_api_key:
            headers["Authorization"] = f"Bearer {self.config.aws_api_key}"
        
        payload = {
            "model": self.config.aws_model,
            "messages": [
                {"role": "system", "content": analysis["system_prompt"]},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": analysis["temperature"],
            "top_p": analysis["top_p"],
        }
        
        try:
            r = requests.post(
                f"{self.config.aws_base_url}/v1/chat/completions",
                headers=headers, json=payload, timeout=120
            )
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            content = f"[Erreur] {str(e)}"
        
        # Cache
        self.cache[cache_key] = content
        if len(self.cache) > self.cache_max:
            self.cache.popitem(last=False)
        
        # Stats
        self.stats["avg_resonance"] = (
            self.stats["avg_resonance"] * (self.stats["total"] - 1) + 
            np.mean(analysis["signatures"])
        ) / self.stats["total"]
        
        return {
            "content": content,
            "analysis": analysis,
            "cache_hit": False,
            "time": time.time() - t0,
        }


# ===========================================================================
# TEST
# ===========================================================================

def test_harmonic_surgery():
    """Teste la chirurgie harmonique."""
    print("=" * 60)
    print("TEST : Chirurgie Harmonique AWS")
    print("=" * 60)
    
    config = HarmonicSurgeryConfig(
        hidden_size=512,
        num_heads=8,
        num_layers=4,
        mode="proxy"
    )
    
    # 1. Tester l'adaptateur
    print("\n1. Test de l'adaptateur harmonique...")
    adapter = HarmonicAdapter(config)
    
    # Forward avec signatures
    test_sigs = torch.randn(4, 7)
    pred_sig, params = adapter(test_sigs)
    
    print(f"  Signatures input:  {test_sigs.shape}")
    print(f"  Signatures output: {pred_sig.shape}")
    print(f"  Temperature: {params['temperature'][0]:.3f}")
    print(f"  Top-K norm:  {params['top_k_norm'][0]:.3f}")
    print(f"  Top-P:       {params['top_p'][0]:.3f}")
    print(f"  Resonance:   {params['resonance'][0,0]:.3f}")
    
    assert pred_sig.shape == (4, 7)
    assert params["temperature"].shape == (4,)
    print("[OK] Adaptateur fonctionnel")
    
    # 2. Tester le proxy V2
    print("\n2. Test du proxy harmonique V2...")
    proxy = HarmonicAWSProxyV2(config)
    
    test_prompts = [
        "Calculate the integral of x^2 from 0 to 1",
        "Write a poem about the ocean",
        "Explain quantum computing",
        "Write Python code to sort a list",
    ]
    
    for prompt in test_prompts:
        analysis = proxy.analyze_prompt(prompt)
        sig = analysis["signatures"]
        dims = ['phi','alpha','reasoning','creativity','math','factual','code']
        
        print(f"\n  Prompt: {prompt[:40]}...")
        for name, val in zip(dims, sig):
            print(f"    {name:12s} = {val:.3f}")
        print(f"    temperature={analysis['temperature']:.3f}, "
              f"top_k={analysis['top_k']}, top_p={analysis['top_p']:.3f}")
    
    # 3. Tester l'entrainement
    print("\n3. Test d'entrainement de l'adaptateur...")
    train_data = [
        {"prompt": "math question", "signatures": [0.5, 0.3, 0.2, 0.1, 0.8, 0.3, 0.1]},
        {"prompt": "creative writing", "signatures": [0.6, 0.4, 0.3, 0.9, 0.1, 0.2, 0.1]},
        {"prompt": "code review", "signatures": [0.4, 0.3, 0.2, 0.1, 0.2, 0.2, 0.9]},
        {"prompt": "explain physics", "signatures": [0.5, 0.4, 0.7, 0.2, 0.5, 0.3, 0.1]},
    ] * 10  # Multiplier pour plus de donnees
    
    trainer = HarmonicTrainer(config)
    trained_adapter = trainer.train_adapter(adapter, train_data)
    
    print("\n[SUCCES] Chirurgie harmonique operationnelle")
    print("\nPour utiliser sur AWS:")
    print("  python harmonic_aws_surgery.py --mode proxy --prompt '...'")
    print("  python harmonic_aws_surgery.py --mode train --data train.json")


# ===========================================================================
# SERVEUR API REST HARMONIQUE (mode serve)
# ===========================================================================
# Compatible OpenAI API : /v1/chat/completions
# S'intercale entre le client et l'API AWS DeepSeek/Qwen
# Injecte les signatures 7D et la resonance harmonique
# ===========================================================================

class HarmonicAPIServer:
    """
    Serveur API REST compatible OpenAI.
    
    Endpoints :
    - POST /v1/chat/completions : chat avec resonance harmonique
    - GET  /v1/models : liste les modeles disponibles
    - GET  /health : sante du serveur
    - GET  /stats : statistiques harmoniques
    
    Utilisation :
        python harmonic_aws_surgery.py --mode serve --port 8080
    """
    
    def __init__(self, config: HarmonicSurgeryConfig):
        self.config = config
        self.proxy = HarmonicAWSProxyV2(config)
        self.start_time = time.time()
        
        # Stats globales
        self.total_requests = 0
        self.total_tokens = 0
        self.errors = 0
        
        print(f"[OK] Serveur harmonique initialise")
        print(f"     Backend: {config.aws_base_url or 'NON CONFIGURE (mode demo)'}")
        print(f"     Modele:  {config.aws_model or 'NON CONFIGURE (mode demo)'}")
    
    def _build_response(self, content: str, model: str, 
                        analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Construit une reponse compatible OpenAI."""
        return {
            "id": f"chatcmpl-{int(time.time()*1000)}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": len(content.split()),
                "total_tokens": len(content.split())
            },
            "harmonic_analysis": {
                "signatures": analysis.get("signatures", []),
                "temperature": analysis.get("temperature", 0.5),
                "top_p": analysis.get("top_p", 0.85),
                "top_k": analysis.get("top_k", 50),
                "resonance": float(np.mean(analysis.get("signatures", [0.5]*7)))
            }
        }
    
    def _extract_prompt(self, body: Dict[str, Any]) -> str:
        """Extrait le dernier message utilisateur du body OpenAI."""
        messages = body.get("messages", [])
        for msg in reversed(messages):
            if msg.get("role") == "user":
                return msg.get("content", "")
        return ""
    
    def chat_completion(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Endpoint /v1/chat/completions.
        
        Si le backend AWS est configure, appelle l'API reelle.
        Sinon, genere une reponse simulee avec les signatures.
        """
        self.total_requests += 1
        t0 = time.time()
        
        prompt = self._extract_prompt(body)
        model = body.get("model", self.config.aws_model or "harmonic-proxy")
        
        if not prompt:
            return self._build_response(
                "Prompt vide.", model,
                {"signatures": [0.5]*7, "temperature": 0.5, "top_p": 0.85, "top_k": 50}
            )
        
        # Analyser avec le proxy harmonique
        analysis = self.proxy.analyze_prompt(prompt)
        
        # Si backend AWS configure, appel API
        if self.config.aws_base_url:
            result = self.proxy.generate(prompt)
            content = result["content"]
        else:
            # Mode demo : generer une reponse harmonique
            sig = analysis["signatures"]
            dims = ['phi','alpha','raisonnement','creativite','math','factuel','code']
            active = [d for d, v in zip(dims, sig) if v > 0.5]
            
            content = (
                f"✨ **Reponse Harmonique** ✨\n\n"
                f"Analyse 7D de votre prompt :\n"
                f"- Dimensions actives : {', '.join(active) if active else 'aucune'}\n"
                f"- Resonance : {np.mean(sig):.3f}\n"
                f"- Temperature harmonique : {analysis['temperature']:.3f}\n\n"
                f"*[Mode demo - Configurez BACKEND_BASE_URL pour utiliser l'API AWS]*"
            )
        
        elapsed = time.time() - t0
        self.total_tokens += len(content.split())
        
        response = self._build_response(content, model, analysis)
        response["usage"]["prompt_tokens"] = len(prompt.split())
        response["harmonic_analysis"]["latency_ms"] = int(elapsed * 1000)
        
        return response
    
    def get_models(self) -> Dict[str, Any]:
        """Endpoint /v1/models."""
        models = [
            {
                "id": self.config.aws_model or "harmonic-proxy",
                "object": "model",
                "created": int(self.start_time),
                "owned_by": "harmonic-ai",
                "harmonic": True,
                "resonance_7d": True
            }
        ]
        return {"object": "list", "data": models}
    
    def get_health(self) -> Dict[str, Any]:
        """Endpoint /health."""
        uptime = time.time() - self.start_time
        return {
            "status": "healthy",
            "harmonic": True,
            "uptime_seconds": int(uptime),
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "errors": self.errors,
            "backend_configured": bool(self.config.aws_base_url),
            "resonance_active": True
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Endpoint /stats."""
        return {
            "harmonic_stats": {
                "total_requests": self.total_requests,
                "total_tokens": self.total_tokens,
                "errors": self.errors,
                "avg_resonance": self.proxy.stats["avg_resonance"],
                "cache_hits": self.proxy.stats["cache_hits"],
                "cache_size": len(self.proxy.cache),
                "uptime_seconds": int(time.time() - self.start_time)
            },
            "config": {
                "model": self.config.aws_model or "harmonic-proxy",
                "backend": self.config.aws_base_url or "demo",
                "harmonic_dim": 7,
                "max_len": self.config.max_len
            }
        }


def run_server():
    """Lance le serveur API REST harmonique."""
    try:
        from fastapi import FastAPI, Request
        from fastapi.responses import JSONResponse
        import uvicorn
    except ImportError:
        print("[ERREUR] fastapi/uvicorn requis: pip install fastapi uvicorn")
        sys.exit(1)
    
    config = HarmonicSurgeryConfig(
        aws_base_url=os.getenv("BACKEND_BASE_URL", ""),
        aws_model=os.getenv("BACKEND_MODEL", ""),
        aws_api_key=os.getenv("BACKEND_API_KEY", ""),
    )
    
    server = HarmonicAPIServer(config)
    app = FastAPI(title="Harmonic AWS Proxy", version="2.0.0")
    
    @app.post("/v1/chat/completions")
    async def chat_completions(request: Request):
        body = await request.json()
        try:
            result = server.chat_completion(body)
            return JSONResponse(content=result)
        except Exception as e:
            server.errors += 1
            return JSONResponse(
                content={"error": str(e), "harmonic": True},
                status_code=500
            )
    
    @app.get("/v1/models")
    async def list_models():
        return JSONResponse(content=server.get_models())
    
    @app.get("/health")
    async def health():
        return JSONResponse(content=server.get_health())
    
    @app.get("/stats")
    async def stats():
        return JSONResponse(content=server.get_stats())
    
    @app.get("/")
    async def root():
        return {
            "service": "Harmonic AWS Proxy",
            "version": "2.0.0",
            "endpoints": {
                "POST /v1/chat/completions": "Chat avec resonance harmonique",
                "GET /v1/models": "Modeles disponibles",
                "GET /health": "Sante du serveur",
                "GET /stats": "Statistiques harmoniques"
            },
            "harmonic_7d": True,
            "resonance": True
        }
    
    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"\n{'='*60}")
    print(f"SERVEUR HARMONIQUE AWS")
    print(f"{'='*60}")
    print(f"  API:     http://{host}:{port}/v1/chat/completions")
    print(f"  Health:  http://{host}:{port}/health")
    print(f"  Models:  http://{host}:{port}/v1/models")
    print(f"  Stats:   http://{host}:{port}/stats")
    print(f"{'='*60}\n")
    
    uvicorn.run(app, host=host, port=port, log_level="info")


def main():
    """Point d'entree principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Chirurgie Harmonique AWS")
    parser.add_argument("--mode", choices=["test", "proxy", "train", "deploy", "serve"],
                       default="test", help="Mode d'execution")
    parser.add_argument("--prompt", type=str, default="", help="Prompt")
    parser.add_argument("--data", type=str, default="", help="Fichier de donnees")
    parser.add_argument("--port", type=int, default=8080, help="Port du serveur")
    
    args = parser.parse_args()
    
    if args.mode == "test":
        test_harmonic_surgery()
        return
    
    if args.mode == "serve":
        os.environ["PORT"] = str(args.port)
        run_server()
        return
    
    config = HarmonicSurgeryConfig(
        aws_base_url=os.getenv("BACKEND_BASE_URL", ""),
        aws_model=os.getenv("BACKEND_MODEL", ""),
        aws_api_key=os.getenv("BACKEND_API_KEY", ""),
    )
    
    if args.mode == "proxy":
        proxy = HarmonicAWSProxyV2(config)
        if not args.prompt:
            args.prompt = input("Prompt: ")
        result = proxy.generate(args.prompt)
        print(f"\nAnalyse harmonique:")
        for k, v in result["analysis"].items():
            if k != "system_prompt":
                print(f"  {k}: {v}")
        print(f"\nReponse:\n{result['content'][:1000]}")
    
    elif args.mode == "train":
        if not args.data:
            print("Erreur: --data requis pour le mode train")
            return
        with open(args.data) as f:
            data = json.load(f)
        adapter = HarmonicAdapter(config)
        trainer = HarmonicTrainer(config)
        trainer.train_adapter(adapter, data)
        torch.save(adapter.state_dict(), "harmonic_adapter.pt")
        print("[OK] Adaptateur sauvegarde: harmonic_adapter.pt")
    
    elif args.mode == "deploy":
        print("Deploiement sur AWS...")
        print("1. Entrainer l'adaptateur (--mode train)")
        print("2. Tester le proxy (--mode proxy)")
        print("3. Lancer le serveur (--mode serve --port 8080)")


if __name__ == "__main__":
    main()
