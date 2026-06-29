"""
Script d'apprentissage automatique — Amorçage de l'hologramme
==============================================================
Charge le corpus (50k lignes) dans l'hologramme par superposition
d'ondes, puis execute une boucle de feedback pour affiner les
motifs de resonance.

Principe (arithmetique ondulatoire) :
  Chaque phrase = superposition d'ondes ajoutees a l'hologramme.
  Pas de backpropagation. Pas de GPU. Pas de parametres.
  L'apprentissage EST l'accumulation.

Usage:
  python train_hologram.py --max_phrases 10000 --feedback_cycles 5

Etapes:
  1. Charger le corpus (50k lignes max)
  2. Amorcer l'hologramme (apprentissage additif)
  3. Boucle de feedback : generer → evaluer → re-injecter
  4. Sauvegarder l'hologramme
"""

import sys
import os
import time
import argparse
import re
from pathlib import Path
from typing import List, Dict
import numpy as np

# Chemins
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_HARMONIC_TRAINING = _PROJECT_ROOT / "harmonic_training"
_CORPUS_DIR = _PROJECT_ROOT / "data" / "corpus"
_OUTPUT_DIR = _PROJECT_ROOT / "data" / "hologram_output"
_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_HARMONIC_TRAINING))
sys.path.insert(0, str(Path(__file__).resolve().parent))


def load_corpus(max_phrases: int = 50000) -> List[str]:
    """Charge toutes les phrases du corpus."""
    all_phrases = []
    
    corpus_files = sorted(_CORPUS_DIR.glob("*.txt"))
    print(f"Corpus files found: {len(corpus_files)}")
    
    for path in corpus_files:
        if path.stat().st_size < 100:
            continue
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                # Filtrer : phrases entre 10 et 200 caracteres
                if 10 < len(line) < 200:
                    all_phrases.append(line)
                    if len(all_phrases) >= max_phrases:
                        break
        if len(all_phrases) >= max_phrases:
            break
    
    print(f"Loaded: {len(all_phrases)} phrases")
    return all_phrases


def build_vocabulary(phrases: List[str], max_words: int = 5000) -> List[str]:
    """Construit un vocabulaire a partir des phrases du corpus."""
    from harmonic_training.model.harmonic_resonance_generator import VOCABULAIRE_BASE
    
    word_counts = {}
    for phrase in phrases:
        for mot in phrase.lower().split():
            mot = mot.strip('.,!?;:()[]{}"\'-_<>/ ')
            if len(mot) >= 2:
                word_counts[mot] = word_counts.get(mot, 0) + 1
    
    # Trier par frequence
    sorted_words = sorted(word_counts.items(), key=lambda x: -x[1])
    
    # Commencer avec le vocabulaire de base
    vocab = list(VOCABULAIRE_BASE)
    existing = set(vocab)
    
    # Ajouter les mots les plus frequents du corpus
    for word, count in sorted_words:
        if word not in existing and len(vocab) < max_words:
            vocab.append(word)
            existing.add(word)
    
    print(f"Vocabulary: {len(vocab)} words (base={len(VOCABULAIRE_BASE)}, corpus={len(vocab)-len(VOCABULAIRE_BASE)})")
    return vocab


def seed_hologram(generator, phrases: List[str], batch_size: int = 500):
    """Amorce l'hologramme avec les phrases du corpus."""
    total = len(phrases)
    t0 = time.time()
    
    for i, phrase in enumerate(phrases):
        generator.apprendre(phrase, amplitude=0.5)
        
        if (i + 1) % batch_size == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            remaining = (total - i - 1) / rate
            print(f"  [{i+1}/{total}] {rate:.0f} phrases/s, "
                  f"energy={generator.energy:.0f}, "
                  f"remaining={remaining/60:.1f}min")
    
    elapsed = time.time() - t0
    print(f"Seeding complete: {total} phrases in {elapsed:.0f}s "
          f"({total/elapsed:.0f} phrases/s)")
    print(f"  Energy: {generator.energy:.0f}")


def feedback_loop(generator, phrases: List[str], n_cycles: int = 5,
                  prompts_per_cycle: int = 10):
    """
    Boucle de feedback : le systeme genere, evalue, et re-apprend.
    
    Pour chaque cycle :
      1. Selectionner des prompts aleatoires du corpus
      2. Generer une reponse par resonance
      3. Re-injecter la reponse dans l'hologramme (apprentissage)
      4. Mesurer la qualite (diversite, longueur)
    """
    print(f"\n{'='*60}")
    print(f"FEEDBACK LOOP — {n_cycles} cycles")
    print(f"{'='*60}")
    
    np.random.seed(42)
    
    for cycle in range(1, n_cycles + 1):
        t0 = time.time()
        
        # Selectionner des prompts
        indices = np.random.choice(len(phrases), min(prompts_per_cycle, len(phrases)),
                                   replace=False)
        
        total_tokens = 0
        total_diversity = 0.0
        
        for idx in indices:
            prompt = phrases[idx]
            # Utiliser la premiere moitie comme prompt
            words = prompt.split()
            if len(words) > 5:
                prompt_part = ' '.join(words[:len(words)//2])
            else:
                prompt_part = prompt
            
            try:
                result = generator.generer(prompt_part, max_tokens=15,
                                          temperature=0.8, top_k=15,
                                          n_rep_lecture=5)
                total_tokens += result.get('n_tokens', 0)
                total_diversity += result.get('diversite', 0)
                
                # Feedback : re-injecter la generation
                texte_gen = result.get('texte_genere', '')
                if len(texte_gen) > 5:
                    generator.apprendre(texte_gen, amplitude=0.3)
            except Exception as e:
                pass
        
        elapsed = time.time() - t0
        avg_tokens = total_tokens / max(prompts_per_cycle, 1)
        avg_diversity = total_diversity / max(prompts_per_cycle, 1)
        
        print(f"  Cycle {cycle}/{n_cycles}: {elapsed:.0f}s, "
              f"{avg_tokens:.1f} tok/prompt, "
              f"div={avg_diversity:.2f}, "
              f"energy={generator.energy:.0f}")
        
        # Sauvegarde intermediaire
        if cycle % 2 == 0:
            save_path = _OUTPUT_DIR / f"hologram_cycle_{cycle}.npy"
            try:
                np.save(str(save_path), generator._gen.monde.H)
                print(f"  Saved: {save_path}")
            except Exception:
                pass


def demo_generation(generator, test_prompts: List[str]):
    """Demonstration de generation apres apprentissage."""
    print(f"\n{'='*60}")
    print(f"DEMO GENERATION")
    print(f"{'='*60}")
    
    for prompt in test_prompts:
        result = generator.generer(prompt, max_tokens=20, temperature=0.8,
                                  top_k=20, n_rep_lecture=8)
        print(f"\n>> {prompt}")
        print(f"<< {result['texte_genere']}")
        print(f"   ({result['n_tokens']}t, {result['temps_ms']:.0f}ms, "
              f"div={result['diversite']:.2f})")


def main():
    parser = argparse.ArgumentParser(description="Hologram Training")
    parser.add_argument('--max_phrases', type=int, default=5000,
                       help='Max phrases to load (default: 5000)')
    parser.add_argument('--feedback_cycles', type=int, default=3,
                       help='Number of feedback cycles (default: 3)')
    parser.add_argument('--vocab_size', type=int, default=3000,
                       help='Max vocabulary size (default: 3000)')
    parser.add_argument('--hologram_size', type=int, default=256,
                       help='Hologram grid size (default: 256)')
    parser.add_argument('--skip_seeding', action='store_true',
                       help='Skip initial seeding')
    parser.add_argument('--skip_feedback', action='store_true',
                       help='Skip feedback loop')
    args = parser.parse_args()
    
    print("=" * 60)
    print("HOLOGRAM TRAINING — Apprentissage par ondes")
    print(f"  Phrases: {args.max_phrases}")
    print(f"  Feedback cycles: {args.feedback_cycles}")
    print(f"  Vocab size: {args.vocab_size}")
    print(f"  Hologram: {args.hologram_size}x{args.hologram_size}")
    print("=" * 60)
    print()
    
    # 1. Charger le corpus
    print("Loading corpus...")
    phrases = load_corpus(args.max_phrases)
    
    # 2. Construire le vocabulaire
    print("\nBuilding vocabulary...")
    vocab = build_vocabulary(phrases, args.vocab_size)
    
    # 3. Creer le generateur
    print("\nInitializing resonance generator...")
    from fast_resonance_generator import FastResonanceGenerator
    gen = FastResonanceGenerator(vocab, nx=args.hologram_size,
                                 ny=args.hologram_size, n_lecteurs=6)
    
    # 4. Amorcer l'hologramme
    if not args.skip_seeding:
        print(f"\nSeeding hologram with {len(phrases)} phrases...")
        seed_hologram(gen, phrases)
    
    # 5. Boucle de feedback
    if not args.skip_feedback and args.feedback_cycles > 0:
        feedback_loop(gen, phrases, args.feedback_cycles)
    
    # 6. Demo
    test_prompts = [
        "explique le nombre d or et la proportion divine",
        "comment fonctionne la resonance harmonique",
        "qu est ce que la conscience",
        "parle moi de l amour et de l univers",
        "quel est le sens de la vie",
    ]
    demo_generation(gen, test_prompts)
    
    # 7. Sauvegarde finale
    save_path = _OUTPUT_DIR / "hologram_final.npy"
    try:
        np.save(str(save_path), gen._gen.monde.H)
        print(f"\nFinal hologram saved: {save_path}")
    except Exception as e:
        print(f"\nSave error: {e}")
    
    # Stats finales
    stats = gen.stats() if hasattr(gen, 'stats') else {}
    print(f"\nFinal stats: {stats}")


if __name__ == '__main__':
    main()
