#!/usr/bin/env python3
"""
DEMONSTRATION DU GENERATEUR DE TEXTE HARMONIQUE
================================================
Charge le modele entraine et genere du texte interactivement.

Usage:
    python demo_harmonic_text_generator.py [--prompt "Votre prompt"] [--tokens 64]
"""

import os
import sys
import json
import re
import argparse

import torch
import torch.nn.functional as F

# Ajouter le repertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from harmonic_text_generator import HarmonicDecoder, HarmonicVocabulary


def load_model(model_dir: str = 'models/harmonic_text') -> tuple:
    """
    Charge le modele entraine et le vocabulaire.
    
    Args:
        model_dir: Repertoire du modele
    
    Returns:
        decoder: Decodeur harmonique entraine
        vocab: Vocabulaire harmonique
        config: Configuration d'entrainement
    """
    print(f"Chargement du modele depuis {model_dir}...")
    
    # Charger le vocabulaire
    vocab_path = os.path.join(model_dir, 'vocab.json')
    with open(vocab_path, 'r', encoding='utf-8') as f:
        vocab_data = json.load(f)
    
    # Creer le vocabulaire
    vocab = HarmonicVocabulary(
        vocab_size=vocab_data['vocab_size'],
        embed_dim=vocab_data['embed_dim']
    )
    vocab.token_to_id = vocab_data['token_to_id']
    vocab.id_to_token = {int(k): v for k, v in vocab_data['id_to_token'].items()}
    
    # Charger le checkpoint
    checkpoint_path = os.path.join(model_dir, 'decoder_best.pt')
    if not os.path.exists(checkpoint_path):
        checkpoint_path = os.path.join(model_dir, 'decoder_final.pt')
    
    checkpoint = torch.load(checkpoint_path, map_location='cpu')
    config = checkpoint['config']
    
    # Creer le decodeur
    decoder = HarmonicDecoder(
        vocab_size=config['vocab_size'],
        embed_dim=config['embed_dim'],
        hidden_dim=config['hidden_dim'],
        num_layers=config['num_layers'],
        num_heads=config['num_heads']
    )
    decoder.load_state_dict(checkpoint['model_state_dict'])
    decoder.eval()
    
    print(f"  Vocabulaire: {vocab.vocab_size} tokens")
    print(f"  Decodeur: {sum(p.numel() for p in decoder.parameters()):,} parametres")
    print(f"  Loss: {checkpoint['loss']:.4f}")
    print(f"  Epoch: {checkpoint['epoch']}")
    
    return decoder, vocab, config


def generate_text(decoder, vocab, prompt, max_tokens=64, temperature=0.8, 
                  top_k=20, repetition_penalty=1.2, device='cpu'):
    """
    Genere du texte a partir d'un prompt.
    """
    tokenizer = re.compile(r"\b\w+\b|[.,!?;:()\[\]{}'\"-]")
    
    # Encoder le prompt
    prompt_tokens = tokenizer.findall(prompt.lower())
    input_ids = [vocab.token_to_id.get(t, vocab.UNK_ID) for t in prompt_tokens]
    
    if len(input_ids) == 0:
        input_ids = [vocab.BOS_ID]
    
    generated_ids = list(input_ids)
    
    with torch.no_grad():
        for _ in range(max_tokens):
            context = generated_ids[-64:]
            input_tensor = torch.tensor([context], dtype=torch.long).to(device)
            
            logits = decoder(input_tensor)
            next_logits = logits[0, -1, :]
            
            # Temperature
            next_logits = next_logits / temperature
            
            # Repetition penalty
            for token_id in set(generated_ids[-20:]):
                next_logits[token_id] /= repetition_penalty
            
            # Top-K
            if top_k > 0:
                values, _ = torch.topk(next_logits, top_k)
                next_logits[next_logits < values[-1]] = float('-inf')
            
            # Echantillonnage
            probs = F.softmax(next_logits, dim=-1)
            next_id = torch.multinomial(probs, 1).item()
            
            if next_id == vocab.EOS_ID:
                break
            
            generated_ids.append(next_id)
    
    # Decoder
    generated_tokens = []
    for idx in generated_ids[len(input_ids):]:
        if idx == vocab.EOS_ID:
            break
        if idx == vocab.BOS_ID or idx == vocab.PAD_ID:
            continue
        token = vocab.id_to_token.get(idx, '<UNK>')
        generated_tokens.append(token)
    
    text = ' '.join(generated_tokens)
    text = re.sub(r'\s+([.,!?;:()\[\]{}"\'-])', r'\1', text)
    text = re.sub(r"\s+'\s+", "'", text)
    text = re.sub(r"\s+n't", "n't", text)
    
    return text


def interactive_mode(decoder, vocab, config):
    """Mode interactif de generation de texte."""
    device = config['device']
    
    print(f"\n{'='*60}")
    print(f"MODE INTERACTIF - GENERATEUR DE TEXTE HARMONIQUE")
    print(f"{'='*60}")
    print(f"Entrez un prompt pour generer du texte.")
    print(f"Commandes: /quit (quitter), /temp N (temperature), /topk N, /rep N")
    print(f"{'='*60}\n")
    
    temperature = 0.8
    top_k = 20
    repetition_penalty = 1.2
    max_tokens = 64
    
    while True:
        try:
            user_input = input("Prompt> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAu revoir !")
            break
        
        if not user_input:
            continue
        
        if user_input == '/quit':
            print("Au revoir !")
            break
        
        if user_input.startswith('/temp'):
            try:
                temperature = float(user_input.split()[1])
                print(f"  Temperature = {temperature}")
            except:
                print(f"  Temperature actuelle: {temperature}")
            continue
        
        if user_input.startswith('/topk'):
            try:
                top_k = int(user_input.split()[1])
                print(f"  Top-K = {top_k}")
            except:
                print(f"  Top-K actuel: {top_k}")
            continue
        
        if user_input.startswith('/rep'):
            try:
                repetition_penalty = float(user_input.split()[1])
                print(f"  Repetition penalty = {repetition_penalty}")
            except:
                print(f"  Repetition penalty actuelle: {repetition_penalty}")
            continue
        
        if user_input.startswith('/tokens'):
            try:
                max_tokens = int(user_input.split()[1])
                print(f"  Max tokens = {max_tokens}")
            except:
                print(f"  Max tokens actuel: {max_tokens}")
            continue
        
        # Generer
        generated = generate_text(
            decoder, vocab, user_input,
            max_tokens=max_tokens,
            temperature=temperature,
            top_k=top_k,
            repetition_penalty=repetition_penalty,
            device=device
        )
        
        print(f"\n  Prompt: {user_input}")
        print(f"  Genere: {generated}")
        print(f"  [temp={temperature}, topk={top_k}, rep={repetition_penalty}]\n")


def batch_demo(decoder, vocab, config):
    """Mode demo avec prompts predefinis."""
    device = config['device']
    
    print(f"\n{'='*60}")
    print(f"DEMONSTRATION - GENERATEUR DE TEXTE HARMONIQUE")
    print(f"{'='*60}")
    
    prompts = [
        "La resonance harmonique",
        "L'intelligence artificielle",
        "Le nombre d'or",
        "La mecanique quantique",
        "L'apprentissage profond",
        "La conscience",
        "Le temps",
        "La liberte",
        "L'amour",
        "La musique",
    ]
    
    for prompt in prompts:
        print(f"\nPrompt: '{prompt}'")
        
        # Generation avec temperature elevee (creativite)
        generated_creative = generate_text(
            decoder, vocab, prompt,
            max_tokens=32,
            temperature=0.9,
            top_k=25,
            repetition_penalty=1.0,
            device=device
        )
        print(f"  [Creatif]: {generated_creative}")
        
        # Generation avec temperature basse (precision)
        generated_precise = generate_text(
            decoder, vocab, prompt,
            max_tokens=32,
            temperature=0.3,
            top_k=5,
            repetition_penalty=1.5,
            device=device
        )
        print(f"  [Precis]:  {generated_precise}")


def main():
    parser = argparse.ArgumentParser(description='Demo du generateur de texte harmonique')
    parser.add_argument('--model-dir', default='models/harmonic_text',
                       help='Repertoire du modele entraine')
    parser.add_argument('--prompt', type=str, default=None,
                       help='Prompt pour la generation (mode non-interactif)')
    parser.add_argument('--tokens', type=int, default=64,
                       help='Nombre max de tokens a generer')
    parser.add_argument('--temperature', type=float, default=0.8,
                       help='Temperature d\'echantillonnage')
    parser.add_argument('--top-k', type=int, default=20,
                       help='Top-K sampling')
    parser.add_argument('--interactive', action='store_true',
                       help='Mode interactif')
    parser.add_argument('--batch', action='store_true',
                       help='Mode demo avec prompts predefinis')
    
    args = parser.parse_args()
    
    # Charger le modele
    decoder, vocab, config = load_model(args.model_dir)
    
    if args.interactive:
        interactive_mode(decoder, vocab, config)
    elif args.batch:
        batch_demo(decoder, vocab, config)
    elif args.prompt:
        generated = generate_text(
            decoder, vocab, args.prompt,
            max_tokens=args.tokens,
            temperature=args.temperature,
            top_k=args.top_k,
            device=config['device']
        )
        print(f"\nPrompt: {args.prompt}")
        print(f"Genere: {generated}")
    else:
        # Mode demo par defaut
        batch_demo(decoder, vocab, config)
        print(f"\n{'='*60}")
        print(f"Pour le mode interactif: python demo_harmonic_text_generator.py --interactive")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
