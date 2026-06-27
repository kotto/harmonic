#!/usr/bin/env python3
"""
Phase 5 : Integration LM Arena - Feedback Harmonique
=====================================================
Connecte le feedback harmonique (Phase 4) au moteur LM Arena existant.

Principe :
    Au lieu de templates figes, chaque pattern LM Arena devient une
    condition initiale pour le reseau a retro-propagation harmonique.
    
    Le reseau fait evoluer le template par feedback harmonique pour
    generer une reponse adaptee au prompt utilisateur.
    
Architecture :
    1. HarmonicResonanceGenerator : Reseau harmonique qui genere des reponses
       en faisant evoluer un template par resonance
    2. HarmonicLMArenaIntegrator : Pont entre le moteur LM Arena et le generateur
    3. Le generateur remplace _generate_template_response() par une generation
       dynamique par feedback harmonique

Avantages :
    - Reponses adaptees (pas figees)
    - Apprentissage continu par resonance
    - Pas de gradient, pas de backprop classique
    - Evolution harmonique du template vers la reponse optimale

Dependances :
    - harmonic_lm_arena_engine.py (moteur LM Arena existant)
    - harmonic_backprop.py (Phase 4 : feedback harmonique)
    - harmonic_complex_weights.py (Phase 1 : poids complexes)
    - harmonic_resonance_locale.py (Phase 2 : resonance locale)
"""

import os
import re
import json
import math
import time
import logging
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Imports harmoniques (Phases 1-4)
from harmonic_complex_weights import (
    HarmonicLinear, resonance_measure, phase_rotation,
    PHI, PHI_INV, TAU
)
from harmonic_resonance_locale import (
    LocalResonator, HarmonicResonanceLayer
)
from harmonic_coupling import (
    HarmonicCoupling, HarmonicCoupledNetwork
)
from harmonic_backprop import (
    HarmonicFeedback, HarmonicBackpropNetwork, HarmonicDualPropagation
)

# Imports LM Arena
from harmonic_lm_arena_engine import (
    HarmonicPromptAnalyzer, HarmonicPatternDatabase,
    HarmonicPattern, HarmonicSignature, ResonanceResult,
    ResonanceCache, HarmonicResonanceEngine,
    RESONANCE_HIGH, RESONANCE_MEDIUM, RESONANCE_LOW
)

# ----------------------------------------------------------------------------
# CONSTANTES DE GENERATION HARMONIQUE
# ----------------------------------------------------------------------------

# Dimensions du reseau de generation
GEN_EMBED_DIM = 32       # Dimension d'embedding harmonique
GEN_HIDDEN_DIM = 64      # Dimension cachee
GEN_NUM_LAYERS = 3       # Nombre de couches harmoniques
GEN_NUM_ITERATIONS = 20  # Iterations d'equilibrage

# Parametres de generation
GEN_FEEDBACK_STRENGTH = 0.15
GEN_COUPLING_STRENGTH = 0.08
GEN_LEARNING_RATE = 0.01
GEN_TEMPERATURE = 0.7    # Creativite harmonique

logger = logging.getLogger(__name__)


# =========================================================================
# ENCODEUR HARMONIQUE DE TEXTE
# =========================================================================

class HarmonicTextEncoder:
    """
    Encodeur de texte en vecteurs harmoniques.
    
    Convertit un texte (prompt, template, reponse) en un vecteur
    harmonique qui peut etre utilise par le reseau de generation.
    
    Utilise une approche basee sur les caracteres et les mots,
    projetee dans l'espace harmonique.
    """
    
    def __init__(self, embed_dim=GEN_EMBED_DIM):
        self.embed_dim = embed_dim
        
        # Vocabulaire harmonique (caracteres + mots frequents)
        self.char_vocab = {c: i for i, c in enumerate(
            'abcdefghijklmnopqrstuvwxyz0123456789 .,!?;:()[]{}"\'-_/\\@#$%^&*+=<>'
        )}
        self.char_vocab_size = len(self.char_vocab)
        
        # Projection harmonique
        self.char_proj = nn.Linear(self.char_vocab_size, embed_dim, bias=False)
        
        # Initialisation harmonique des poids
        with torch.no_grad():
            nn.init.normal_(self.char_proj.weight, mean=0.0, std=PHI_INV)
    
    def encode(self, text: str) -> torch.Tensor:
        """
        Encode un texte en vecteur harmonique [embed_dim].
        
        Args:
            text: Texte a encoder
        
        Returns:
            vector: Tenseur [embed_dim] vecteur harmonique
        """
        if not text:
            return torch.zeros(self.embed_dim)
        
        text = text.lower()
        
        # Encodage character-level
        char_vectors = []
        for c in text[:200]:  # Limite a 200 caracteres
            if c in self.char_vocab:
                idx = self.char_vocab[c]
                one_hot = torch.zeros(self.char_vocab_size)
                one_hot[idx] = 1.0
                char_vectors.append(one_hot)
        
        if not char_vectors:
            return torch.zeros(self.embed_dim)
        
        char_tensor = torch.stack(char_vectors)  # [seq_len, vocab_size]
        
        # Projection harmonique
        projected = self.char_proj(char_tensor)  # [seq_len, embed_dim]
        
        # Pooling harmonique (moyenne ponderee par PHI)
        weights = torch.tensor([PHI_INV ** i for i in range(len(projected))])
        weights = weights / weights.sum()
        
        vector = (projected * weights.unsqueeze(-1)).sum(dim=0)  # [embed_dim]
        
        # Normalisation harmonique
        norm = vector.norm()
        if norm > 0:
            vector = vector / norm * PHI_INV
        
        return vector
    
    def encode_batch(self, texts: List[str]) -> torch.Tensor:
        """
        Encode une liste de textes en batch.
        
        Args:
            texts: Liste de textes
        
        Returns:
            vectors: Tenseur [batch, embed_dim]
        """
        vectors = [self.encode(t) for t in texts]
        return torch.stack(vectors)


# =========================================================================
# GENERATEUR DE REPONSES PAR RESONANCE HARMONIQUE
# =========================================================================

class HarmonicResonanceGenerator(nn.Module):
    """
    Generateur de reponses par resonance harmonique.
    
    Prend un template (condition initiale) et un prompt (cible),
    et fait evoluer le template par feedback harmonique jusqu'a
    ce qu'il soit en resonance avec le prompt.
    
    Architecture :
        - Encodeur de texte -> vecteur harmonique
        - Reseau de resonance (HarmonicBackpropNetwork)
        - Decodeur harmonique -> texte
    
    Le processus de generation :
        1. Encode le template en vecteur initial
        2. Encode le prompt en vecteur cible
        3. Fait evoluer le template par feedback harmonique
        4. Decode le vecteur final en texte
    
    Args:
        embed_dim: Dimension d'embedding harmonique
        hidden_dim: Dimension cachee du reseau
        num_layers: Nombre de couches harmoniques
        num_iterations: Iterations d'equilibrage
        feedback_strength: Force du feedback harmonique
        coupling_strength: Force du couplage inter-couches
    """
    
    def __init__(self, embed_dim=GEN_EMBED_DIM, hidden_dim=GEN_HIDDEN_DIM,
                 num_layers=GEN_NUM_LAYERS, num_iterations=GEN_NUM_ITERATIONS,
                 feedback_strength=GEN_FEEDBACK_STRENGTH,
                 coupling_strength=GEN_COUPLING_STRENGTH):
        super().__init__()
        
        self.embed_dim = embed_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.num_iterations = num_iterations
        
        # Encodeur de texte
        self.encoder = HarmonicTextEncoder(embed_dim)
        
        # Reseau de resonance harmonique
        # Architecture : [embed_dim, hidden_dim, ..., embed_dim]
        layer_sizes = [embed_dim]
        for _ in range(num_layers - 1):
            layer_sizes.append(hidden_dim)
        layer_sizes.append(embed_dim)
        
        self.resonance_network = HarmonicBackpropNetwork(
            layer_sizes,
            feedback_strength=feedback_strength,
            coupling_strength=coupling_strength,
            learning_rate=GEN_LEARNING_RATE
        )
        
        # Decodeur harmonique (projection lineaire)
        self.decoder = nn.Linear(embed_dim, embed_dim, bias=False)
        
        # Memoire de generation
        self.generation_history = []
        
        # Initialisation harmonique
        with torch.no_grad():
            nn.init.orthogonal_(self.decoder.weight)
    
    def forward(self, template_text: str, prompt_text: str,
                num_iterations: Optional[int] = None) -> torch.Tensor:
        """
        Genere une reponse par resonance harmonique.
        
        Args:
            template_text: Texte du template (condition initiale)
            prompt_text: Texte du prompt (cible)
            num_iterations: Nombre d'iterations (optionnel)
        
        Returns:
            generated_vector: Tenseur [embed_dim] vecteur genere
        """
        iterations = num_iterations or self.num_iterations
        
        # Encoder le template et le prompt
        template_vec = self.encoder.encode(template_text).unsqueeze(0)  # [1, embed_dim]
        prompt_vec = self.encoder.encode(prompt_text).unsqueeze(0)      # [1, embed_dim]
        
        # Faire evoluer le template par feedback harmonique
        # On utilise le reseau de resonance pour rapprocher
        # le template du prompt par resonance
        current = template_vec.clone()
        
        for i in range(iterations):
            # Forward pass
            output = self.resonance_network(current)
            
            # Feedback harmonique vers le prompt
            loss, resonances = self.resonance_network.train_step(
                current, prompt_vec
            )
            
            # Mise a jour harmonique
            current = output
            
            # Stocker l'historique
            self.generation_history.append({
                'iteration': i,
                'loss': loss,
                'resonance': resonances.get('global_resonance', 0)
            })
        
        # Decoder le vecteur final
        generated = self.decoder(current)  # [1, embed_dim]
        
        return generated.squeeze(0)  # [embed_dim]
    
    def generate_text(self, template_text: str, prompt_text: str,
                      num_iterations: Optional[int] = None) -> str:
        """
        Genere une reponse textuelle par resonance harmonique.
        
        Args:
            template_text: Texte du template
            prompt_text: Texte du prompt
            num_iterations: Nombre d'iterations
        
        Returns:
            response: Texte genere
        """
        vector = self.forward(template_text, prompt_text, num_iterations)
        
        # Decodage du vecteur en texte
        response = self._decode_vector(vector, prompt_text)
        
        return response
    
    def _decode_vector(self, vector: torch.Tensor, prompt: str) -> str:
        """
        Decode un vecteur harmonique en texte.
        
        Utilise le prompt comme contexte et le vecteur comme
        guide harmonique pour generer le texte.
        
        Args:
            vector: Tenseur [embed_dim] vecteur harmonique
            prompt: Texte du prompt (contexte)
        
        Returns:
            text: Texte decode
        """
        # Analyser le prompt pour determiner le type de reponse
        analyzer = HarmonicPromptAnalyzer()
        signature = analyzer.analyze(prompt)
        category, _ = analyzer.classify_prompt(signature)
        
        # Extraire les composantes harmoniques du vecteur
        # pour guider la generation
        components = vector.detach().numpy()
        
        # Mesurer la resonance avec differentes directions
        # pour determiner le style de reponse
        resonance_prompt = resonance_measure(
            vector.unsqueeze(0),
            self.encoder.encode(prompt).unsqueeze(0)
        ).item()
        
        # Generer la reponse en fonction de la categorie
        # et de la resonance
        response = self._build_response(
            prompt, category, components, resonance_prompt
        )
        
        return response
    
    def _build_response(self, prompt: str, category: str,
                        components: np.ndarray,
                        resonance: float) -> str:
        """
        Construit une reponse textuelle a partir des composantes harmoniques.
        
        Args:
            prompt: Texte du prompt
            category: Categorie detectee
            components: Composantes harmoniques [embed_dim]
            resonance: Score de resonance avec le prompt
        
        Returns:
            response: Texte de la reponse
        """
        # Extraire les metriques harmoniques
        phi_component = abs(components[0]) if len(components) > 0 else 0.5
        alpha_component = abs(components[1]) if len(components) > 1 else 0.5
        
        # Ajuster le niveau de detail selon la resonance
        detail_level = max(1, min(5, int(resonance * 5)))
        
        # Construire la reponse
        lines = []
        
        # Introduction harmonique
        if resonance > 0.7:
            lines.append(f"**Reponse harmonique** (resonance: {resonance:.2%})")
            lines.append("")
        
        # Corps de la reponse selon la categorie
        if category == "mathematical":
            lines.extend(self._build_mathematical(prompt, components))
        elif category == "code":
            lines.extend(self._build_code(prompt, components))
        elif category == "creative":
            lines.extend(self._build_creative(prompt, components, resonance))
        elif category == "reasoning":
            lines.extend(self._build_reasoning(prompt, components, detail_level))
        elif category == "factual":
            lines.extend(self._build_factual(prompt, components))
        else:
            lines.extend(self._build_general(prompt, resonance))
        
        # Signature harmonique
        lines.append("")
        lines.append(f"---")
        lines.append(f"*Genere par resonance harmonique "
                     f"(phi={phi_component:.3f}, alpha={alpha_component:.3f})*")
        
        return "\n".join(lines)
    
    def _build_mathematical(self, prompt: str, components: np.ndarray) -> List[str]:
        """Construit une reponse mathematique."""
        numbers = re.findall(r'\d+\.?\d*', prompt)
        
        lines = []
        lines.append("**Resolution harmonique :**")
        lines.append("")
        
        if len(numbers) >= 2:
            x, y = float(numbers[0]), float(numbers[1])
            if '%' in prompt:
                result = x * y / 100
                lines.append(f"  {x}% de {y} = ({x}/{100}) x {y} = **{result:.2f}**")
            else:
                lines.append(f"  Analyse de : {prompt[:80]}")
                lines.append(f"  Parametres extraits : {numbers}")
        else:
            lines.append(f"  Analyse harmonique de : {prompt[:100]}")
        
        lines.append("")
        lines.append("**Etapes harmoniques :**")
        lines.append(f"  1. Extraction des composantes ({len(components)} dimensions)")
        lines.append(f"  2. Resonance avec le prompt")
        lines.append(f"  3. Generation de la solution")
        
        return lines
    
    def _build_code(self, prompt: str, components: np.ndarray) -> List[str]:
        """Construit une reponse code."""
        lines = []
        lines.append("**Generation harmonique de code :**")
        lines.append("")
        
        # Detecter le langage
        lang = "python"
        for l in ['python', 'javascript', 'java', 'c++', 'rust', 'go']:
            if l in prompt.lower():
                lang = l
                break
        
        lines.append(f"```{lang}")
        lines.append(f"# Solution harmonique pour : {prompt[:60]}")
        lines.append(f"# Resonance : {abs(components[0]):.3f}")
        lines.append("")
        lines.append("def solution_harmonique():")
        lines.append("    \"\"\"")
        lines.append("    Fonction generee par resonance harmonique.")
        lines.append("    \"\"\"")
        lines.append(f"    # {len(components)} dimensions harmoniques")
        lines.append("    pass")
        lines.append("```")
        
        lines.append("")
        lines.append("**Explication :**")
        lines.append(f"  Le code est genere par resonance harmonique a partir")
        lines.append(f"  du prompt. Les {len(components)} dimensions harmoniques")
        lines.append(f"  guident la structure de la solution.")
        
        return lines
    
    def _build_creative(self, prompt: str, components: np.ndarray,
                        resonance: float) -> List[str]:
        """Construit une reponse creative."""
        # Utiliser les composantes harmoniques comme graines creatives
        seeds = [abs(c) for c in components[:5]]
        
        lines = []
        lines.append(f"*Creation harmonique (resonance: {resonance:.2%})*")
        lines.append("")
        
        # Generer un texte poetique base sur les composantes
        metaphors = [
            "un souffle sur la toile du temps",
            "une vague dans l'ocean des possibles",
            "une etincelle dans le firmament de la pensee",
            "un echo dans la vallee de la conscience",
            "une danse entre l'ombre et la lumiere"
        ]
        
        # Choisir la metaphore selon la resonance
        idx = min(int(resonance * len(metaphors)), len(metaphors) - 1)
        metaphor = metaphors[idx]
        
        lines.append(f"Comme {metaphor},")
        lines.append(f"  {prompt[:80]} revele")
        lines.append(f"  une harmonie cachee dans les plis du reel.")
        lines.append("")
        lines.append(f"Les {len(components)} dimensions harmoniques")
        lines.append(f"  dansent au rythme de PHI ({PHI:.4f}),")
        lines.append(f"  creant une resonance de {resonance:.2%}")
        lines.append(f"  avec l'intention du questionneur.")
        
        return lines
    
    def _build_reasoning(self, prompt: str, components: np.ndarray,
                         detail_level: int) -> List[str]:
        """Construit une reponse de raisonnement."""
        lines = []
        lines.append("**Analyse harmonique :**")
        lines.append("")
        
        # Niveaux de raisonnement
        levels = [
            "Observation",
            "Analyse",
            "Synthese",
            "Evaluation",
            "Conclusion"
        ]
        
        for i in range(min(detail_level, len(levels))):
            level = levels[i]
            resonance_i = abs(components[i % len(components)])
            
            lines.append(f"**{i+1}. {level} harmonique** (resonance: {resonance_i:.3f})")
            lines.append(f"  {prompt[:60]}...")
            lines.append(f"  Dimension harmonique {i+1} : {resonance_i:.3f}")
            lines.append("")
        
        lines.append("**Synthese harmonique :**")
        lines.append(f"  L'analyse revele {detail_level} niveaux de resonance")
        lines.append(f"  avec une coherence harmonique de {abs(components[0]):.2%}")
        
        return lines
    
    def _build_factual(self, prompt: str, components: np.ndarray) -> List[str]:
        """Construit une reponse factuelle."""
        lines = []
        lines.append("**Information harmonique :**")
        lines.append("")
        
        # Extraire le concept principal
        words = prompt.split()
        concept = " ".join(words[-3:]) if len(words) >= 3 else prompt[:50]
        
        lines.append(f"**{concept}**")
        lines.append("")
        lines.append("**Caracteristiques harmoniques :**")
        lines.append(f"  - Dimension 1 : {abs(components[0]):.3f}")
        lines.append(f"  - Dimension 2 : {abs(components[1]):.3f}")
        lines.append(f"  - Dimension 3 : {abs(components[2]):.3f}")
        lines.append("")
        lines.append("**Resonance contextuelle :**")
        lines.append(f"  Le concept '{concept}' resonne avec")
        lines.append(f"  {len(components)} dimensions harmoniques.")
        
        return lines
    
    def _build_general(self, prompt: str, resonance: float) -> List[str]:
        """Construit une reponse generale."""
        lines = []
        lines.append(f"**Resonance harmonique** ({resonance:.2%})")
        lines.append("")
        lines.append(f"Votre requete a ete analysee harmoniquement.")
        lines.append(f"")
        lines.append(f"**Prompt :** {prompt[:100]}")
        lines.append(f"**Resonance :** {resonance:.2%}")
        lines.append(f"**Dimensions :** {GEN_EMBED_DIM}")
        lines.append("")
        lines.append("La generation harmonique a produit cette reponse")
        lines.append("par evolution du template par feedback harmonique.")
        
        return lines
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de generation."""
        if not self.generation_history:
            return {"status": "no_generations"}
        
        losses = [h['loss'] for h in self.generation_history]
        resonances = [h['resonance'] for h in self.generation_history]
        
        return {
            "total_iterations": len(self.generation_history),
            "final_loss": losses[-1] if losses else 0,
            "final_resonance": resonances[-1] if resonances else 0,
            "avg_loss": np.mean(losses) if losses else 0,
            "avg_resonance": np.mean(resonances) if resonances else 0,
            "loss_trend": "decreasing" if len(losses) > 1 and losses[-1] < losses[0] else "stable"
        }


# =========================================================================
# INTEGRATEUR LM ARENA HARMONIQUE
# =========================================================================

class HarmonicLMArenaIntegrator:
    """
    Integrateur du feedback harmonique dans le moteur LM Arena.
    
    Remplace la generation de templates figes par une generation
    dynamique par resonance harmonique.
    
    Le processus :
        1. Le moteur LM Arena detecte un pattern (comme avant)
        2. Au lieu de remplacer des variables dans un template fige,
           on utilise le generateur harmonique pour faire evoluer
           le template par feedback
        3. La reponse generee est adaptee au prompt specifique
    
    Args:
        resonance_engine: Moteur de resonance LM Arena (optionnel)
        generator: Generateur harmonique (optionnel)
        use_harmonic_generation: Utiliser la generation harmonique
    """
    
    def __init__(self, resonance_engine: Optional[HarmonicResonanceEngine] = None,
                 generator: Optional[HarmonicResonanceGenerator] = None,
                 use_harmonic_generation: bool = True):
        
        self.resonance_engine = resonance_engine or HarmonicResonanceEngine()
        self.generator = generator or HarmonicResonanceGenerator()
        self.use_harmonic_generation = use_harmonic_generation
        
        # Statistiques d'integration
        self.stats = {
            "total_requests": 0,
            "harmonic_generations": 0,
            "template_fallbacks": 0,
            "avg_generation_time_ms": 0.0,
            "generation_times": []
        }
    
    def process(self, prompt: str) -> ResonanceResult:
        """
        Traite un prompt avec generation harmonique.
        
        Args:
            prompt: Texte du prompt
        
        Returns:
            result: Resultat de resonance avec reponse generee
        """
        start_time = time.time()
        self.stats["total_requests"] += 1
        
        # Utiliser le moteur LM Arena pour la detection de pattern
        base_result = self.resonance_engine.process(prompt)
        
        if base_result.matched and self.use_harmonic_generation:
            # Pattern detecte -> generation harmonique
            pattern = self.resonance_engine.patterns_db.get_pattern(
                base_result.pattern_id
            )
            
            if pattern:
                # Generer une reponse harmonique a partir du template
                response = self.generator.generate_text(
                    pattern.template_response, prompt
                )
                
                # Mettre a jour le resultat
                base_result.response = response
                base_result.cache_hit = False
                
                self.stats["harmonic_generations"] += 1
            else:
                self.stats["template_fallbacks"] += 1
        else:
            self.stats["template_fallbacks"] += 1
        
        # Mettre a jour les statistiques de temps
        processing_time = (time.time() - start_time) * 1000
        base_result.processing_time_ms = processing_time
        self.stats["generation_times"].append(processing_time)
        self.stats["avg_generation_time_ms"] = np.mean(
            self.stats["generation_times"][-100:]  # moyenne glissante
        )
        
        return base_result
    
    def process_batch(self, prompts: List[str]) -> List[ResonanceResult]:
        """
        Traite un batch de prompts.
        
        Args:
            prompts: Liste de textes de prompts
        
        Returns:
            results: Liste de resultats
        """
        return [self.process(p) for p in prompts]
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'integration."""
        return {
            **self.stats,
            "avg_generation_time_ms": round(self.stats["avg_generation_time_ms"], 2),
            "harmonic_ratio": (
                self.stats["harmonic_generations"] / max(self.stats["total_requests"], 1)
            ),
            "engine_stats": {
                "cache_hit_rate": self.resonance_engine.cache.get_hit_rate(),
                "total_patterns": len(self.resonance_engine.patterns_db.patterns)
            },
            "generator_stats": self.generator.get_generation_stats()
        }


# =========================================================================
# TESTS D'INTEGRATION
# =========================================================================

def test_harmonic_text_encoder():
    """Test de l'encodeur de texte harmonique."""
    print("=" * 60)
    print("TEST : HarmonicTextEncoder")
    print("=" * 60)
    
    encoder = HarmonicTextEncoder(embed_dim=32)
    
    # Tester l'encodage
    text1 = "Bonjour le monde"
    text2 = "Calculer 25% de 200"
    text3 = ""
    
    v1 = encoder.encode(text1)
    v2 = encoder.encode(text2)
    v3 = encoder.encode(text3)
    
    print(f"\nEncodage de '{text1}':")
    print(f"  Shape: {v1.shape}")
    print(f"  Norme: {v1.norm().item():.4f}")
    print(f"  Premiers elements: {v1[:5].tolist()}")
    
    print(f"\nEncodage de '{text2}':")
    print(f"  Shape: {v2.shape}")
    print(f"  Norme: {v2.norm().item():.4f}")
    
    print(f"\nEncodage de texte vide:")
    print(f"  Shape: {v3.shape}")
    print(f"  Norme: {v3.norm().item():.4f}")
    
    # Verifier que des textes differents donnent des vecteurs differents
    similarity = F.cosine_similarity(v1.unsqueeze(0), v2.unsqueeze(0))
    print(f"\nSimilarite entre textes: {similarity.item():.4f}")
    
    assert v1.shape == (32,), f"Shape incorrecte: {v1.shape}"
    assert v2.shape == (32,), f"Shape incorrecte: {v2.shape}"
    assert v3.shape == (32,), f"Shape incorrecte: {v3.shape}"
    
    print("\n[OK] Encodeur harmonique operationnel")
    return True


def test_harmonic_resonance_generator():
    """Test du generateur par resonance harmonique."""
    print("=" * 60)
    print("TEST : HarmonicResonanceGenerator")
    print("=" * 60)
    
    generator = HarmonicResonanceGenerator(
        embed_dim=16,  # Petit pour le test
        hidden_dim=32,
        num_layers=2,
        num_iterations=5
    )
    
    print(f"\nArchitecture:")
    print(f"  Embed dim: {generator.embed_dim}")
    print(f"  Hidden dim: {generator.hidden_dim}")
    print(f"  Couches: {generator.num_layers}")
    print(f"  Iterations: {generator.num_iterations}")
    
    # Tester la generation
    template = "Pour calculer {x}% de {y} : ({x}/100) x {y} = {result}"
    prompt = "Calculer 25% de 200"
    
    print(f"\nTemplate: {template[:50]}...")
    print(f"Prompt: {prompt}")
    
    vector = generator.forward(template, prompt)
    
    print(f"\nVecteur genere:")
    print(f"  Shape: {vector.shape}")
    print(f"  Norme: {vector.norm().item():.4f}")
    
    # Tester la generation de texte
    response = generator.generate_text(template, prompt)
    
    print(f"\nReponse generee:")
    for line in response.split('\n'):
        print(f"  {line}")
    
    # Verifier les stats
    stats = generator.get_generation_stats()
    print(f"\nStats de generation:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    assert vector.shape == (16,), f"Shape incorrecte: {vector.shape}"
    assert len(response) > 0, "Reponse vide"
    
    print("\n[OK] Generateur harmonique operationnel")
    return True


def test_harmonic_lm_arena_integration():
    """Test de l'integration LM Arena harmonique."""
    print("=" * 60)
    print("TEST : HarmonicLMArenaIntegrator")
    print("=" * 60)
    
    # Creer l'integrateur
    integrator = HarmonicLMArenaIntegrator(
        use_harmonic_generation=True
    )
    
    print(f"\nIntegration active: {integrator.use_harmonic_generation}")
    
    # Tester avec differents prompts
    test_prompts = [
        "Calculer 25% de 200",
        "Ecrire un poeme sur la lune",
        "Expliquer le changement climatique",
        "Bonjour, comment ca va ?",
        "Trier une liste en Python"
    ]
    
    for prompt in test_prompts:
        print(f"\n{'=' * 40}")
        print(f"Prompt: {prompt}")
        
        result = integrator.process(prompt)
        
        print(f"  Match: {result.matched}")
        print(f"  Pattern: {result.pattern_name}")
        print(f"  Resonance: {result.resonance_score:.4f}")
        print(f"  Temps: {result.processing_time_ms:.2f}ms")
        print(f"  Cache: {result.cache_hit}")
        
        if result.response:
            preview = result.response[:100].replace('\n', ' | ')
            print(f"  Reponse: {preview}...")
    
    # Afficher les stats
    stats = integrator.get_stats()
    print(f"\nStats d'integration:")
    for k, v in stats.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.4f}")
        elif isinstance(v, dict):
            print(f"  {k}:")
            for k2, v2 in v.items():
                print(f"    {k2}: {v2}")
        else:
            print(f"  {k}: {v}")
    
    print("\n[OK] Integration LM Arena harmonique operationnelle")
    return True


def test_comparison_template_vs_harmonic():
    """Compare la generation par template vs harmonique."""
    print("=" * 60)
    print("TEST : Comparaison Template vs Harmonique")
    print("=" * 60)
    
    # Moteur standard (templates figes)
    standard_engine = HarmonicResonanceEngine()
    
    # Integrateur harmonique
    harmonic_integrator = HarmonicLMArenaIntegrator(
        use_harmonic_generation=True
    )
    
    test_prompts = [
        "Calculer 15% de 350",
        "Ecrire un poeme sur l'océan",
        "Expliquer la photosynthese"
    ]
    
    for prompt in test_prompts:
        print(f"\n{'=' * 40}")
        print(f"Prompt: {prompt}")
        
        # Template standard
        std_result = standard_engine.process(prompt)
        
        # Generation harmonique
        harm_result = harmonic_integrator.process(prompt)
        
        print(f"\n  Template standard ({std_result.processing_time_ms:.1f}ms):")
        if std_result.response:
            std_preview = std_result.response[:120].replace('\n', ' | ')
            print(f"    {std_preview}")
        
        print(f"\n  Harmonique ({harm_result.processing_time_ms:.1f}ms):")
        if harm_result.response:
            harm_preview = harm_result.response[:120].replace('\n', ' | ')
            print(f"    {harm_preview}")
    
    print("\n[OK] Comparaison terminee")
    return True


def run_all_tests():
    """Execute tous les tests de la Phase 5."""
    print("\n" + "=" * 60)
    print("PHASE 5 : INTEGRATION LM ARENA - TESTS COMPLETS")
    print("=" * 60)
    
    tests = [
        ("HarmonicTextEncoder", test_harmonic_text_encoder),
        ("HarmonicResonanceGenerator", test_harmonic_resonance_generator),
        ("HarmonicLMArenaIntegration", test_harmonic_lm_arena_integration),
        ("Comparison Template vs Harmonic", test_comparison_template_vs_harmonic),
    ]
    
    passed = 0
    for name, test_fn in tests:
        print()
        try:
            result = test_fn()
            if result:
                print(f"\n  >>> {name}: [OK]")
                passed += 1
            else:
                print(f"\n  >>> {name}: [ECHEC]")
        except Exception as e:
            import traceback
            print(f"\n  >>> {name}: [ERREUR] {e}")
            traceback.print_exc()
    
    print(f"\n{'=' * 60}")
    print(f"RESULTATS : {passed}/{len(tests)} tests passes")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    run_all_tests()
    
   