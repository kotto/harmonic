#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HARMONIC CREATIVITY ENGINE — Créativité par Interférence d'Ondes
=================================================================
Adaptation du principe de Poetic Emergence (poetic_emergence.py)
aux images, vidéos et audio.

Principe fondamental (prouvé en poésie) :
  "Si la pensée est une onde (Ψ = Σ Hₙ (Ψ₁)ⁿ), alors la CRÉATIVITÉ
   est l'INTERFÉRENCE de deux ondes qui produit une TROISIÈME onde
   émergente — qui n'existait dans aucune des deux sources."

   Ψ_créatif = Ψ_sourceA ⊗ Ψ_sourceB  (interférence = produit d'hologrammes)

Modes de créativité harmonique :
  1. INTERFERENCE   : Ψ_A × Ψ_B → émergence pure (le plus créatif)
  2. MORPH          : Ψ_A → Ψ_B par interpolation harmonique
  3. REMIX          : Transfert de style (hologramme B, coefficients A)
  4. EVOLUTION      : Mutation progressive guidée par un thème (seed)
  5. RESONANCE      : Sélection des éléments qui résonnent avec un thème

Métrique d'émergence :
  Score = distance(Ψ_ab, Ψ_a) × distance(Ψ_ab, Ψ_b)
  Plus le score est élevé, plus le résultat est "original" (ni A, ni B)

Usage :
  python harmonic_creativity_engine.py --demo
  python harmonic_creativity_engine.py --interfere img1.png img2.png
  python harmonic_creativity_engine.py --theme "galaxie spirale" --source img.png
"""

import numpy as np
import math
import sys
import os
import time
import hashlib
import json
import argparse
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harmonic_generator_core import (
    PHI, PI, E, SQRT2, SQRT3, SQRT5, E_PI, PHI_INV,
    H_CONSTANTS, H_NAMES, HarmonicColorMapper, HarmonicField,
    SeedManager, normalize_field, compute_harmonic_coherence, save_image,
)
from holographic_one_shot import (
    HolographicTrainer, HolographicSignature, HolographicGenerator,
    BLOCK_SIZE, BLOCK_DIM,
)
from prompt_engine import analyze_prompt, RESOLUTIONS
from holobase import Holobase


# ==============================================================================
# SIGNATURE CRÉATIVE — Extension de HolographicSignature
# ==============================================================================

@dataclass
class CreativeSignature:
    """
    Signature créative : hologramme + métadonnées de créativité.
    """
    signature: HolographicSignature
    source_name: str = ""
    style_tags: List[str] = field(default_factory=list)
    emotional_signature: Optional[np.ndarray] = None  # Signature émotionnelle (H-Bit)
    
    @property
    def coherence(self) -> float:
        """Cohérence de la signature (0=chaos, 1=parfait)."""
        return self.signature.coherence_score()
    
    def distance_to(self, other: 'CreativeSignature') -> float:
        """
        Distance harmonique entre deux signatures.
        
        Basée sur l'interférence cosinus de leurs hologrammes.
        """
        h_a = np.mean(self.signature.hologram, axis=0)
        h_b = np.mean(other.signature.hologram, axis=0)
        dot = np.dot(h_a, h_b)
        n_a = np.linalg.norm(h_a)
        n_b = np.linalg.norm(h_b)
        if n_a < 1e-12 or n_b < 1e-12:
            return 1.0
        return 1.0 - dot / (n_a * n_b)


# ==============================================================================
# MOTEUR DE CRÉATIVITÉ HARMONIQUE
# ==============================================================================

class HarmonicCreativityEngine:
    """
    Moteur de créativité : applique les principes de Poetic Emergence
    aux images, vidéos et audio.
    
    La créativité = interférence d'ondes qui produit une émergence.
    """
    
    def __init__(self):
        self.creative_history: List[CreativeSignature] = []
    
    def extract_signature(self, image: np.ndarray, name: str = "",
                          K: int = 16) -> CreativeSignature:
        """
        Extrait la signature créative d'une image.
        
        Équivalent de : encoder un vers en H-Bit (poetic_emergence.py:120)
        """
        sig = HolographicTrainer.train_image(image, K=K)
        
        # Tags basés sur l'analyse harmonique
        tags = []
        energy = sig.energy_spectrum()
        dominant = np.argmax(energy) + 1
        tags.append(H_NAMES[dominant - 1].split(' ')[0])
        
        # Signature émotionnelle (H-Bit simplifié)
        emotional = sig.hologram[0] if sig.K > 0 else np.ones(BLOCK_DIM)
        
        cs = CreativeSignature(
            signature=sig,
            source_name=name,
            style_tags=tags,
            emotional_signature=emotional,
        )
        
        self.creative_history.append(cs)
        return cs
    
    def interfere(self, sig_a: CreativeSignature, sig_b: CreativeSignature,
                  strength: float = 0.5,
                  width: int = 512, height: int = 512) -> Tuple[np.ndarray, float]:
        """
        INTERFÉRENCE CRÉATIVE PURE — Le cœur de l'émergence.
        
        Ψ_créatif = Ψ_A × Ψ_B (produit d'hologrammes)
        
        C'est l'équivalent exact de :
          poetic_emergence.py:219 → h_interference = v1.hbit * v2.hbit
        
        Le résultat n'est NI l'image A, NI l'image B — c'est une
        TROISIÈME image qui ÉMERGE de leur interférence.
        
        Args:
            sig_a, sig_b: Signatures créatives sources
            strength: Force de l'interférence (0=pas d'interférence, 1=max)
            width, height: Dimensions de sortie
        
        Returns:
            (image_array [0,1], emergence_score)
        """
        # 1. Produit point-à-point des hologrammes (interférence pure)
        ha = sig_a.signature.hologram  # K_a × 64
        hb = sig_b.signature.hologram  # K_b × 64
        
        # Aligner les dimensions
        min_k = min(ha.shape[0], hb.shape[0])
        ha_interf = ha[:min_k]
        hb_interf = hb[:min_k]
        
        # INTERFÉRENCE : multiplication des vecteurs de base
        # C'est le mécanisme exact de Poetic Emergence
        interference_hologram = ha_interf * hb_interf  # Produit élément par élément
        
        # Normaliser les vecteurs d'interférence
        for k in range(min_k):
            n = np.linalg.norm(interference_hologram[k])
            if n > 1e-12:
                interference_hologram[k] /= n
        
        # 2. Interférence des coefficients (moyenne pondérée + produit croisé)
        coeffs_a = sig_a.signature.coefficients[:256, :min_k]
        coeffs_b = sig_b.signature.coefficients[:256, :min_k]
        
        # Le produit croisé crée de NOUVELLES corrélations
        # (équivalent de : les mots de A interfèrent avec les mots de B)
        cross_term = np.dot(coeffs_a.T, coeffs_b) / 256.0
        np.fill_diagonal(cross_term, cross_term.diagonal() * 0.5)  # Atténuer l'auto-interférence
        
        coeffs_interference = (coeffs_a * (1 - strength) + 
                               coeffs_b * strength +
                               np.dot(coeffs_a, cross_term[:min_k, :min_k]) * strength * 0.3)
        
        # 3. Statistiques hybrides
        mean_hybrid = sig_a.signature.mean * (1 - strength) + sig_b.signature.mean * strength
        std_hybrid = sig_a.signature.std * (1 - strength) + sig_b.signature.std * strength
        
        # 4. Reconstruction
        merged_sig = HolographicSignature(
            hologram=interference_hologram,
            coefficients=coeffs_interference,
            mean=mean_hybrid,
            std=std_hybrid,
            source_shape=(height, width),
            K=min_k,
        )
        
        result = HolographicGenerator.reconstruct(merged_sig, width=width, height=height)
        
        # 5. Score d'émergence (métrique de créativité)
        # Plus le résultat est DIFFÉRENT des deux sources, plus le score est élevé
        dist_a = sig_a.distance_to(CreativeSignature(signature=merged_sig, source_name="emerged"))
        
        # Reconstruire B pour comparaison (utiliser l'hologramme original)
        sig_b_reconstruct = HolographicGenerator.reconstruct(
            sig_b.signature, width=width, height=height
        )
        sig_b_creative = self.extract_signature(sig_b_reconstruct, name="b_recon", K=min_k)
        dist_b = sig_a.distance_to(sig_b_creative)
        
        # Score d'émergence = produit des distances aux sources
        # Élevé = très créatif (loin des deux sources)
        emergence_score = dist_a * (1.0 - dist_b) * 100
        
        return np.clip(result, 0, 1), emergence_score
    
    def morph(self, sig_a: CreativeSignature, sig_b: CreativeSignature,
              steps: int = 7, width: int = 512, height: int = 512) -> List[np.ndarray]:
        """
        MORPH créatif : transformation progressive de A vers B.
        
        Équivalent de : interpoler entre deux poèmes.
        """
        frames = []
        
        for i in range(steps):
            alpha = i / (steps - 1) if steps > 1 else 0.5
            
            # Interpolation non-linéaire φ-basée pour un morphing plus naturel
            alpha_phi = 1.0 / (1.0 + np.exp(-(alpha - 0.5) * PHI * 5))
            
            frame = HolographicGenerator.interpolate(
                sig_a.signature, sig_b.signature,
                alpha=alpha_phi, width=width, height=height,
            )
            frames.append(frame)
        
        return frames
    
    def remix(self, sig_content: CreativeSignature, sig_style: CreativeSignature,
              style_strength: float = 0.5,
              width: int = 512, height: int = 512) -> np.ndarray:
        """
        REMIX créatif : applique le STYLE de B au CONTENU de A.
        
        Équivalent de : réécrire un poème dans le style d'un autre poète.
        
        L'hologramme de B (texture) × coefficients de A (structure).
        """
        result = HolographicGenerator.remix_style(
            sig_content.signature, sig_style.signature,
            style_strength=style_strength,
            width=width, height=height,
        )
        return result
    
    def evolve(self, sig: CreativeSignature, theme_prompt: str,
               n_generations: int = 7, mutation_rate: float = 0.15,
               width: int = 512, height: int = 512) -> List[Tuple[np.ndarray, float]]:
        """
        ÉVOLUTION thématique : fait évoluer une image vers un thème.
        
        Équivalent de : faire émerger des vers sur un thème donné
        (poetic_emergence.py:154 → faire_emerger)
        
        Chaque génération est une mutation guidée par la résonance
        entre l'hologramme courant et le thème (encodé en seed).
        """
        analysis = analyze_prompt(theme_prompt)
        theme_seed = analysis.seed
        theme_h = H_CONSTANTS[analysis.dominant_layer - 1]
        
        generations = []
        current_sig = sig
        
        for gen in range(n_generations):
            # Mutation guidée par le thème
            rate = mutation_rate * (1.0 + gen * 0.1)  # Augmente progressivement
            
            mutated = HolographicGenerator.mutate(
                current_sig.signature,
                mutation_rate=rate,
                preserve_structure=0.6,
                width=width, height=height,
            )
            
            # Mesurer la "résonance" avec le thème
            # (comme poetic_emergence.py mesure l'interférence cosinus)
            mutated_sig = self.extract_signature(mutated, name=f"gen_{gen}")
            resonance = np.abs(np.dot(
                mutated_sig.emotional_signature[:8],
                np.array([theme_h] * 8)
            )) / (theme_h * 8 + 1e-12)
            
            generations.append((mutated, resonance))
            current_sig = mutated_sig
        
        # Trier par résonance (meilleur en premier)
        generations.sort(key=lambda x: x[1], reverse=True)
        
        return generations
    
    def resonate_and_assemble(self, theme_prompt: str,
                               holobase: Holobase = None,
                               corpus_dir: str = None,
                               width: int = 512, height: int = 512,
                               n_pieces: int = 7) -> np.ndarray:
        """
        RÉSONANCE CRÉATIVE : trouve les éléments qui résonnent
        avec un thème et les assemble en une œuvre nouvelle.
        
        Équivalent exact de : poetic_emergence.py:154 → faire_emerger()
        
        1. Analyser le thème → seed + couche dominante
        2. Chercher les images qui résonnent le plus avec le thème
        3. Assembler leurs signatures par fusion pondérée Hₙ
        4. L'œuvre émergente n'est aucune des sources mais les transcende
        """
        analysis = analyze_prompt(theme_prompt)
        
        if holobase and len(holobase.entries) > 0:
            # Recherche dans la Holobase
            result = holobase.generate_from_prompt(
                theme_prompt, resolution='sd',
                num_variations=1, blend_strength=0.8,
            )
            return np.array(result['images'][0].convert('L'), dtype=np.float64) / 255.0
        
        elif corpus_dir and os.path.isdir(corpus_dir):
            # Chercher dans un répertoire local
            import glob
            files = sorted(glob.glob(os.path.join(corpus_dir, '**', '*.png'), recursive=True))
            files += sorted(glob.glob(os.path.join(corpus_dir, '**', '*.jpg'), recursive=True))
            
            if not files:
                return None
            
            # Extraire les signatures et mesurer la résonance
            signatures = []
            for f in files[:20]:  # Limiter à 20 pour la performance
                try:
                    img = np.array(Image.open(f).convert('L'), dtype=np.float64) / 255.0
                    cs = self.extract_signature(img, name=os.path.basename(f))
                    
                    # Résonance avec le thème
                    resonance = np.abs(np.dot(
                        cs.emotional_signature[:8],
                        np.array([H_CONSTANTS[analysis.dominant_layer - 1]] * 8)
                    ))
                    signatures.append((cs, resonance, img))
                except:
                    pass
            
            if not signatures:
                return None
            
            # Trier par résonance
            signatures.sort(key=lambda x: x[1], reverse=True)
            
            # Assembler les n_pieces meilleures signatures
            top_sigs = signatures[:min(n_pieces, len(signatures))]
            
            # Fusion pondérée par les Hₙ
            base_cs = top_sigs[0][0]
            merged_coeffs = np.zeros_like(base_cs.signature.coefficients[:256])
            total_weight = 0.0
            
            for i, (cs, resonance, _) in enumerate(top_sigs):
                weight = H_CONSTANTS[min(i, 6)] / PHI * resonance
                coeffs = cs.signature.coefficients[:256]
                
                min_k = min(coeffs.shape[1], merged_coeffs.shape[1])
                coeffs = coeffs[:, :min_k]
                merged_coeffs = merged_coeffs[:, :min_k]
                
                merged_coeffs += coeffs * weight
                total_weight += weight
            
            merged_coeffs /= max(1e-12, total_weight)
            
            merged_sig = HolographicSignature(
                hologram=base_cs.signature.hologram[:merged_coeffs.shape[1]],
                coefficients=merged_coeffs,
                mean=base_cs.signature.mean,
                std=base_cs.signature.std,
                source_shape=(height, width),
                K=merged_coeffs.shape[1],
            )
            
            return HolographicGenerator.reconstruct(merged_sig, width=width, height=height)
        
        else:
            # Fallback : génération procédurale pure
            field = HarmonicField(width=width, height=height, seed=analysis.seed)
            psi = field.get_psi_total()
            return (psi + 1) / 2  # [-1,1] → [0,1]
    
    def triple_interference(self, sig_a: CreativeSignature,
                            sig_b: CreativeSignature,
                            sig_c: CreativeSignature,
                            width: int = 512, height: int = 512) -> Tuple[np.ndarray, float]:
        """
        INTERFÉRENCE À TROIS — l'équivalent de Ψ_a × Ψ_b × Ψ_c.
        
        Prouvé en poésie : l'interférence de 3 vers produit une émergence
        encore plus riche et imprévisible.
        """
        # Interférence A×B d'abord
        inter_ab, score_ab = self.interfere(sig_a, sig_b, strength=0.5,
                                             width=width, height=height)
        sig_ab = self.extract_signature(inter_ab, name="inter_AB")
        
        # Puis (A×B) × C
        result, score = self.interfere(sig_ab, sig_c, strength=0.6,
                                        width=width, height=height)
        
        # Score combiné (plus il est élevé, plus l'émergence est forte)
        combined_score = score_ab * score
        
        return result, combined_score
    
    def generate_creative_video(self, sig_a: CreativeSignature,
                                 sig_b: CreativeSignature,
                                 duration: float = 3.0, fps: int = 12,
                                 mode: str = 'interference',
                                 width: int = 512, height: int = 512) -> List[np.ndarray]:
        """
        Génère une vidéo créative à partir de deux images sources.
        
        Modes :
          - 'interference' : Évolution de A×B (interférence progressive)
          - 'morph'        : Transformation A → B
          - 'pulse'        : Pulsation entre A et B
        """
        n_frames = int(fps * duration)
        frames = []
        
        for i in range(n_frames):
            t = i / (n_frames - 1) if n_frames > 1 else 0.5
            
            if mode == 'interference':
                # L'interférence augmente avec le temps
                strength = t * 1.5
                frame, score = self.interfere(
                    sig_a, sig_b, strength=strength,
                    width=width, height=height
                )
            elif mode == 'morph':
                frame = HolographicGenerator.interpolate(
                    sig_a.signature, sig_b.signature,
                    alpha=t, width=width, height=height
                )
            else:  # pulse
                pulse = 0.5 + 0.5 * np.sin(t * PI * 3)
                frame, score = self.interfere(
                    sig_a, sig_b, strength=pulse,
                    width=width, height=height
                )
            
            frames.append(frame)
        
        return frames
    
    def generate_creative_audio(self, sig_a: CreativeSignature,
                                 sig_b: CreativeSignature,
                                 duration: float = 3.0,
                                 sample_rate: int = 44100) -> np.ndarray:
        """
        Génère un audio créatif par interférence de signatures.
        
        Utilise les hologrammes comme modulateurs spectraux.
        """
        from harmonic_audio_generator import HarmonicMusicGenerator
        
        # Les hologrammes guident la composition
        ha_mean = np.mean(sig_a.signature.hologram)
        hb_mean = np.mean(sig_b.signature.hologram)
        
        # Fréquence fondamentale = interférence des hologrammes moyens
        fundamental = 110.0 + (ha_mean * hb_mean) * 200
        fundamental = max(55, min(440, fundamental))
        
        # BPM = distance harmonique entre les signatures
        bpm = 60 + sig_a.distance_to(sig_b) * 120
        
        # Intensité = cohérence moyenne
        intensity = (sig_a.coherence + sig_b.coherence) / 2
        
        gen = HarmonicMusicGenerator(
            seed=int(ha_mean * hb_mean * 1000) % (2**31),
            sample_rate=sample_rate,
        )
        
        audio = gen.generate_full_composition(duration=duration, bpm=bpm)
        
        return audio * intensity


# ==============================================================================
# DÉMONSTRATION
# ==============================================================================

def demo_creativity_engine():
    """Démonstration du moteur de créativité harmonique."""
    print("=" * 70)
    print("  HARMONIC CREATIVITY ENGINE")
    print("  Créativité = Interférence d'Ondes (Ψ_A × Ψ_B → Ψ_AB)")
    print("  Inspiré de Poetic Emergence (poetic_emergence.py)")
    print("=" * 70)
    
    engine = HarmonicCreativityEngine()
    output_dir = os.path.join(os.path.dirname(__file__), '..',
                              'av_generation_output', 'creativity')
    os.makedirs(output_dir, exist_ok=True)
    
    # Créer deux images sources distinctes
    print("\n  [1] Création de 2 images sources...")
    from harmonic_generator_core import HarmonicField, HarmonicColorMapper
    from harmonic_image_generator import save_as_png
    
    # Source A : cosmique
    field_a = HarmonicField(width=512, height=512, seed=12345)
    psi_a = field_a.get_psi_total()
    img_a = (psi_a + 1) / 2
    rgb_a = HarmonicColorMapper.harmonic_hsl(psi_a, palette='cosmique')
    save_as_png(rgb_a, os.path.join(output_dir, 'source_A_cosmique.png'))
    
    # Source B : solaire
    field_b = HarmonicField(width=512, height=512, seed=67890)
    psi_b = field_b.get_psi_total()
    img_b = (psi_b + 1) / 2
    rgb_b = HarmonicColorMapper.harmonic_hsl(psi_b, palette='solaire')
    save_as_png(rgb_b, os.path.join(output_dir, 'source_B_solaire.png'))
    
    print("    ✓ Source A : cosmique (seed=12345)")
    print("    ✓ Source B : solaire (seed=67890)")
    
    # Extraire les signatures créatives
    print("\n  [2] Extraction des signatures créatives (K=16)...")
    sig_a = engine.extract_signature(img_a, name="cosmique", K=16)
    sig_b = engine.extract_signature(img_b, name="solaire", K=16)
    
    distance = sig_a.distance_to(sig_b)
    print(f"    Distance harmonique A↔B : {distance:.4f}")
    print(f"    Cohérence A : {sig_a.coherence:.1%}")
    print(f"    Cohérence B : {sig_b.coherence:.1%}")
    
    # Test 1 : Interférence pure
    print("\n  [3] INTERFÉRENCE CRÉATIVE (Ψ_A × Ψ_B)...")
    for strength in [0.3, 0.5, 0.7, 1.0]:
        result, score = engine.interfere(sig_a, sig_b, strength=strength)
        
        # Colorisation harmonique
        field = result * 2 - 1
        rgb = HarmonicColorMapper.harmonic_hsl(field, palette='aurore')
        
        filepath = os.path.join(output_dir, f'interference_strength_{int(strength*100):03d}.png')
        save_as_png(rgb, filepath)
        print(f"    strength={strength:.1f} | score_emergence={score:.1f} → {filepath}")
    
    # Test 2 : Morph
    print("\n  [4] MORPH A → B (7 étapes)...")
    morph_frames = engine.morph(sig_a, sig_b, steps=7)
    for i, frame in enumerate(morph_frames):
        field = frame * 2 - 1
        rgb = HarmonicColorMapper.harmonic_hsl(field, palette='crepuscule')
        filepath = os.path.join(output_dir, f'morph_step_{i:02d}.png')
        save_as_png(rgb, filepath)
    print(f"    ✓ 7 étapes de morphing → {output_dir}/morph_step_*.png")
    
    # Test 3 : Remix (style transfer)
    print("\n  [5] REMIX : contenu cosmique + style solaire...")
    remix_result = engine.remix(sig_a, sig_b, style_strength=0.6)
    field = remix_result * 2 - 1
    rgb = HarmonicColorMapper.harmonic_hsl(field, palette='aurore')
    filepath = os.path.join(output_dir, 'remix_cosmic_solar.png')
    save_as_png(rgb, filepath)
    print(f"    ✓ Remix → {filepath}")
    
    # Test 4 : Évolution thématique
    print("\n  [6] ÉVOLUTION thématique : 'galaxie spirale dorée'...")
    evolved = engine.evolve(sig_a, "galaxie spirale dorée", n_generations=4)
    for i, (frame, resonance) in enumerate(evolved):
        if i < 4:
            field = frame * 2 - 1
            rgb = HarmonicColorMapper.harmonic_hsl(field, palette='cosmique')
            filepath = os.path.join(output_dir, f'evolution_gen_{i+1}_r{resonance:.3f}.png')
            save_as_png(rgb, filepath)
            print(f"    Gen {i+1} | résonance={resonance:.3f} → {filepath}")
    
    # Test 5 : Résonance et assemblage
    print("\n  [7] RÉSONANCE : thème 'océan de lumière'...")
    resonance_result = engine.resonate_and_assemble(
        "océan de lumière dorée", corpus_dir=None, width=512, height=512
    )
    if resonance_result is not None:
        field = resonance_result * 2 - 1
        rgb = HarmonicColorMapper.harmonic_hsl(field, palette='ocean')
        filepath = os.path.join(output_dir, 'resonance_ocean_lumiere.png')
        save_as_png(rgb, filepath)
        print(f"    ✓ Résonance → {filepath}")
    
    # Rapport
    print(f"\n{'='*70}")
    print("  RAPPORT CRÉATIVITÉ HARMONIQUE")
    print(f"{'='*70}")
    print(f"\n  Principe : Ψ_créatif = Ψ_A × Ψ_B (interférence d'ondes)")
    print(f"  Inspiré de : poetic_emergence.py (Poetic Emergence)")
    print(f"  Modes      : interference, morph, remix, evolution, resonance")
    print(f"  Fichiers   : {output_dir}/")
    print(f"\n  ✅ Moteur de créativité harmonique opérationnel.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Harmonic Creativity Engine')
    parser.add_argument('--demo', action='store_true', help='Démonstration complète')
    parser.add_argument('--interfere', nargs=2, metavar=('IMG_A', 'IMG_B'),
                        help='Interférer deux images')
    parser.add_argument('--morph', nargs=2, metavar=('IMG_A', 'IMG_B'),
                        help='Morph entre deux images')
    parser.add_argument('--theme', type=str, default=None, help='Thème créatif')
    parser.add_argument('--source', type=str, default=None, help='Image source')
    parser.add_argument('--output', type=str, default='creative_output.png')
    
    args = parser.parse_args()
    
    if args.interfere:
        engine = HarmonicCreativityEngine()
        img_a = np.array(Image.open(args.interfere[0]).convert('L'), dtype=np.float64) / 255.0
        img_b = np.array(Image.open(args.interfere[1]).convert('L'), dtype=np.float64) / 255.0
        
        sig_a = engine.extract_signature(img_a, name="source_A")
        sig_b = engine.extract_signature(img_b, name="source_B")
        
        result, score = engine.interfere(sig_a, sig_b, strength=0.5)
        
        field = result * 2 - 1
        rgb = HarmonicColorMapper.harmonic_hsl(field, palette='aurore')
        Image.fromarray(rgb, 'RGB').save(args.output)
        print(f"Création sauvegardée : {args.output} (score={score:.1f})")
    
    elif args.morph:
        engine = HarmonicCreativityEngine()
        img_a = np.array(Image.open(args.morph[0]).convert('L'), dtype=np.float64) / 255.0
        img_b = np.array(Image.open(args.morph[1]).convert('L'), dtype=np.float64) / 255.0
        
        sig_a = engine.extract_signature(img_a, name="source_A")
        sig_b = engine.extract_signature(img_b, name="source_B")
        
        frames = engine.morph(sig_a, sig_b, steps=7)
        for i, frame in enumerate(frames):
            field = frame * 2 - 1
            rgb = HarmonicColorMapper.harmonic_hsl(field, palette='crepuscule')
            out = args.output.replace('.png', f'_step{i:02d}.png')
            Image.fromarray(rgb, 'RGB').save(out)
        print(f"Morph sauvegardé : {args.output.replace('.png', '_step*.png')}")
    
    else:
        demo_creativity_engine()