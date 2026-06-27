#!/usr/bin/env python3
"""
ENTRAINEMENT DU GENERATEUR DE TEXTE HARMONIQUE
===============================================
Entraine le generateur de texte harmonique sur un corpus reel.
Utilise la resonance harmonique comme mecanisme d'apprentissage.

Usage:
    python train_harmonic_text_generator.py
    
Etapes:
    1. Chargement du corpus (Wikipedia, livres, etc.)
    2. Construction du vocabulaire harmonique
    3. Entrainement du decodeur par resonance
    4. Evaluation et generation de texte
"""

import os
import sys
import math
import time
import json
import re
import random
from typing import List, Dict, Optional, Tuple
from collections import Counter

import torch
import torch.nn as nn
import torch.nn.functional as F

# Ajouter le repertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importer le generateur harmonique
from harmonic_text_generator import (
    HarmonicVocabulary, HarmonicDecoder, HarmonicTextGenerator,
    HarmonicAttentionLayer, HarmonicBackpropNetwork,
    VOCAB_SIZE, EMBED_DIM, HIDDEN_DIM, NUM_LAYERS, NUM_HEADS,
    MAX_TOKENS, TEMPERATURE, TOP_K, REPETITION_PENALTY,
    PHI, PHI_INV
)

# =========================================================================
# CONFIGURATION D'ENTRAINEMENT
# =========================================================================

TRAIN_CONFIG = {
    'corpus_path': None,  # None = utiliser le corpus integre
    'vocab_size': 512,    # Taille du vocabulaire (mots reels) - reduite pour correspondre au corpus
    'embed_dim': 64,      # Dimension d'embedding
    'hidden_dim': 128,    # Dimension cachee
    'num_layers': 3,      # Couches du decodeur
    'num_heads': 4,       # Tetes d'attention
    'batch_size': 16,     # Taille de batch
    'seq_length': 32,     # Longueur de sequence - reduite pour plus de sequences
    'learning_rate': 0.001,  # Taux d'apprentissage
    'num_epochs': 100,    # Nombre d'epoques - plus d'entrainement
    'save_every': 20,     # Sauvegarder tous les N epochs
    'model_dir': 'models/harmonic_text',  # Repertoire de sauvegarde
    'device': 'cuda' if torch.cuda.is_available() else 'cpu',
}


# =========================================================================
# CORPUS INTEGRE : TEXTES D'ENTRAINEMENT
# =========================================================================

def get_training_corpus() -> List[str]:
    """
    Retourne un corpus de textes d'entrainement.
    Melange de textes scientifiques, philosophiques et litteraires
    pour couvrir un large vocabulaire.
    """
    corpus = [
        # Textes scientifiques
        "La resonance est un phenomene physique par lequel un systeme oscillant entre en vibration sous l'action d'une force exterieure dont la frequence est proche de sa frequence propre.",
        "En mecanique quantique, le principe d'incertitude d'Heisenberg stipule qu'il est impossible de connaitre simultanement avec precision la position et la quantite de mouvement d'une particule.",
        "La theorie de la relativite generale d'Einstein decrit la gravitation comme une courbure de l'espace-temps causee par la presence de masse et d'energie.",
        "L'entropie est une mesure du desordre d'un systeme. Le second principe de la thermodynamique enonce que l'entropie d'un systeme isole ne peut qu'augmenter.",
        "Les nombres complexes sont une extension des nombres reels qui permettent de resoudre des equations polynomiales et de representer des oscillations harmoniques.",
        "La transformee de Fourier decompose une fonction en ses frequences constitutives, permettant l'analyse harmonique des signaux.",
        "En intelligence artificielle, les reseaux de neurones profonds apprennent des representations hierarchiques des donnees par retropropagation du gradient.",
        "L'apprentissage par renforcement permet a un agent d'apprendre des comportements optimaux par interaction avec son environnement et maximisation d'une recompense.",
        "Les modeles de langage bases sur l'attention transforment le traitement automatique du langage naturel en capturant les dependances longues dans les textes.",
        "La mecanique des fluides numerique utilise des methodes de discretisation pour resoudre les equations de Navier-Stokes qui decrivent l'ecoulement des fluides.",
        
        # Textes philosophiques
        "La connaissance de soi est le commencement de toute sagesse. Connais-toi toi-meme et tu connaitras l'univers et les dieux.",
        "Le doute methodique de Descartes conduit a la premiere certitude : je pense donc je suis. Cette certitude fonde toute connaissance.",
        "La liberte consiste a pouvoir faire tout ce qui ne nuit pas a autrui. Ainsi l'exercice des droits naturels de chaque homme n'a de bornes que celles qui assurent aux autres membres de la societe la jouissance de ces memes droits.",
        "Le temps est la duree de l'ame selon Bergson. Il ne se mesure pas mais se vit intensement dans la conscience immediate.",
        "L'existence precede l'essence pour les existentialistes. L'homme n'est rien d'autre que ce qu'il se fait, il est libre et responsable de ses actes.",
        "La raison pure pratique permet a l'homme de se donner a lui-meme sa propre loi morale, selon Kant. Agis de telle sorte que la maxime de ta volonte puisse toujours valoir en meme temps comme principe d'une legislation universelle.",
        "Le langage est la maison de l'etre selon Heidegger. C'est par le langage que l'homme habite le monde et accede a la comprehension de l'etre.",
        "La volonte de puissance est le principe fondamental de toute vie selon Nietzsche. Elle pousse chaque etre a se depasser et a affirmer sa propre valeur.",
        "Le contrat social selon Rousseau fonde la legitimite du pouvoir politique sur la volonte generale du peuple souverain.",
        "La dialectique du maitre et de l'esclave chez Hegel decrit le processus par lequel la conscience de soi se constitue a travers la reconnaissance mutuelle.",
        
        # Textes litteraires
        "Il etait une fois un prince charmant qui cherchait la verite a travers le monde. Il traversa des forets enchantees et des deserts arides avant de comprendre que la verite etait en lui.",
        "Le soleil se levait sur la vallee embrumee, illuminant les toits des maisons endormies. Les oiseaux chantaient leur premier chant du jour tandis que la vie reprenait doucement ses droits.",
        "Dans le silence de la bibliotheque, les livres semblaient murmurer des histoires anciennes. Chaque page tournee revelait un monde nouveau, une aventure inattendue.",
        "La mer etait calme ce soir-la, ses vagues venant mourir doucement sur le sable fin. Le phare dansait au loin, guidant les navires vers le port.",
        "Les saisons passent et les souvenirs s'estompent comme des photographies oubliees au soleil. Pourtant certaines images restent vives, inebranlables, temoins de moments heureux.",
        "L'amour est un oiseau rebelle que nul ne peut apprivoiser. Il vient sans qu'on l'attende et repart sans qu'on le retienne.",
        "La ville s'eveillait dans un brouillard de lumiere et de bruit. Les rues s'animaient peu a peu, les cafes s'ouvraient, la vie reprenait son cours.",
        "Les mots sont des fenetres sur l'ame. Chaque phrase est un reflet de nos pensees les plus profondes, un echo de notre etre interieur.",
        "Le voyage est un retour vers soi-meme. Chaque pays visite, chaque culture rencontree nous renvoie une image differente de qui nous sommes.",
        "La musique adoucit les moeurs et eleve l'ame vers des cieux inconnus. Les notes s'envolent comme des papillons dans le jardin de l'esprit.",
        
        # Textes techniques (IA)
        "Le deep learning a revolutionne le traitement d'images grace aux reseaux de neurones convolutionnels qui extraient des caracteristiques hierarchiques.",
        "Les transformers utilisent un mecanisme d'attention multi-tetes qui permet de ponderer l'importance relative de chaque element d'une sequence.",
        "La generation de texte par intelligence artificielle repose sur des modeles de langage entranes sur de gigantesques corpus de textes.",
        "L'optimisation des hyperparametres est cruciale pour obtenir de bonnes performances en apprentissage automatique.",
        "Les reseaux antagonistes generatifs (GANs) permettent de generer des donnees synthetiques realistes en opposant un generateur et un discriminateur.",
        "L'apprentissage par transfert permet de reutiliser un modele entraine sur une tache pour en resoudre une autre, reduisant le besoin de donnees.",
        "Les embeddings de mots comme Word2Vec et GloVe capturent les relations semantiques entre les mots dans un espace vectoriel continu.",
        "La regularisation par dropout empeche le surapprentissage en desactivant aleatoirement des neurones pendant l'entrainement.",
        "Les fonctions d'activation comme ReLU et tanh introduisent de la non-linearite dans les reseaux de neurones.",
        "L'attention est tout ce dont vous avez besoin selon le papier fondateur des transformers de Vaswani et al.",
        
        # Textes harmoniques (notre domaine)
        "L'approche harmonique de l'intelligence artificielle utilise les principes de resonance et d'oscillation pour creer des representations plus riches.",
        "La resonance harmonique entre les couches d'un reseau de neurones permet une propagation de l'information plus naturelle et plus efficace.",
        "Les poids complexes harmoniques introduisent une phase qui encode l'ordre temporel et les relations de cause a effet entre les neurones.",
        "Le nombre d'or PHI apparait naturellement dans les systemes harmoniques et optimise la propagation de la resonance.",
        "L'attention harmonique remplace le softmax par une fonction tangente hyperbolique qui preserve mieux les relations de phase.",
        "La retropropagation harmonique combine la retropropagation classique avec un signal de resonance qui renforce les chemins coherents.",
        "Le couplage inter-couches harmonique permet aux gradients de circuler plus librement entre les couches profondes du reseau.",
        "L'auto-organisation harmonique emerge naturellement quand les poids du reseau sont initialises avec des phases aleatoires.",
        "La memoire harmonique utilise des motifs d'interference pour stocker et recuperer l'information de facon associative.",
        "Le generateur de texte harmonique combine un decodeur classique avec un reseau de resonance pour produire un texte plus coherent.",
        
        # Textes additionnels pour enrichir le vocabulaire
        "L'intelligence artificielle generale est le Saint Graal de la recherche en IA. Elle represente une machine capable d'effectuer toute tache intellectuelle humaine.",
        "Les systemes multi-agents permettent a plusieurs intelligences artificielles de collaborer pour resoudre des problemes complexes.",
        "La conscience artificielle souleve des questions ethiques fondamentales sur la nature de la pensee et de la perception.",
        "Le traitement du langage naturel permet aux machines de comprendre et de generer le langage humain de facon naturelle.",
        "La vision par ordinateur donne aux machines la capacite de voir et d'interpreter le monde visuel comme le ferait un humain.",
        "La robotique autonome combine perception, planification et action pour creer des machines capables d'interagir avec le monde physique.",
        "Les interfaces cerveau-machine ouvrent la voie a une communication directe entre le cerveau humain et les ordinateurs.",
        "L'informatique quantique promet de resoudre des problemes actuellement insolubles pour les ordinateurs classiques.",
        "La cybersecurite est devenue un enjeu majeur a l'ere du numerique ou les donnees sont la nouvelle monnaie.",
        "Le cloud computing permet d'acceder a des ressources de calcul illimitees sans investissement materiel initial.",
        
        # Ajout de textes sur la physique harmonique
        "Les harmoniques sont des frequences multiples de la frequence fondamentale d'un systeme oscillant.",
        "L'analyse de Fourier permet de decomposer tout signal periodique en une somme de sinus et cosinus.",
        "Les ondes stationnaires resultent de l'interference constructive entre deux ondes de meme frequence se propageant en sens inverse.",
        "La frequence de resonance est la frequence a laquelle un systeme oscille avec la plus grande amplitude.",
        "L'oscillateur harmonique est un modele fondamental en physique qui decrit le mouvement d'un systeme soumis a une force de rappel proportionnelle au deplacement.",
        "Les modes propres d'un systeme vibratoire sont les configurations spatiales dans lesquelles le systeme peut osciller harmoniquement.",
        "L'effet Doppler decrit le changement de frequence d'une onde lorsque la source et l'observateur sont en mouvement relatif.",
        "La diffraction est le phenomene par lequel une onde contourne un obstacle ou s'etale apres avoir traverse une ouverture.",
        "L'interference est la superposition de deux ou plusieurs ondes qui produit une redistribution de l'energie dans l'espace.",
        "La polarisation est la propriete des ondes transversales dont la direction d'oscillation est orientee dans une direction privilegiee.",
    ]
    
    return corpus


# =========================================================================
# CONSTRUCTION DU VOCABULAIRE
# =========================================================================

def build_vocabulary(corpus: List[str], vocab_size: int = 4096) -> Tuple[HarmonicVocabulary, Dict]:
    """
    Construit un vocabulaire harmonique a partir du corpus.
    
    Args:
        corpus: Liste de textes
        vocab_size: Taille maximale du vocabulaire
    
    Returns:
        vocab: Vocabulaire harmonique peuple
        stats: Statistiques du vocabulaire
    """
    print(f"\n{'='*60}")
    print(f"CONSTRUCTION DU VOCABULAIRE HARMONIQUE")
    print(f"{'='*60}")
    
    # Tokenisation simple : mots + ponctuation
    tokenizer = re.compile(r"\b\w+\b|[.,!?;:()\[\]{}'\"-]")
    
    # Compter les mots
    word_counts = Counter()
    total_words = 0
    
    for text in corpus:
        tokens = tokenizer.findall(text.lower())
        word_counts.update(tokens)
        total_words += len(tokens)
    
    print(f"Corpus: {len(corpus)} textes, {total_words} mots")
    print(f"Mots uniques: {len(word_counts)}")
    
    # Selectionner les mots les plus frequents
    # Reserver 4 tokens pour les speciaux (PAD, BOS, EOS, UNK)
    num_real_tokens = vocab_size - 4
    most_common = word_counts.most_common(num_real_tokens)
    
    print(f"Vocabulaire: {len(most_common)} mots + 4 speciaux = {vocab_size} tokens")
    
    # Creer le vocabulaire
    vocab = HarmonicVocabulary(vocab_size=vocab_size, embed_dim=TRAIN_CONFIG['embed_dim'])
    
    # Ajouter les tokens speciaux (deja dans le vocabulaire)
    # PAD=0, BOS=1, EOS=2, UNK=3
    
    # Ajouter les mots
    for i, (word, count) in enumerate(most_common):
        idx = i + 4  # +4 pour les speciaux
        vocab.token_to_id[word] = idx
        vocab.id_to_token[idx] = word
    
    # Statistiques
    stats = {
        'vocab_size': vocab_size,
        'total_words': total_words,
        'unique_words': len(word_counts),
        'covered_words': sum(count for _, count in most_common),
        'coverage': sum(count for _, count in most_common) / total_words * 100,
        'most_common': most_common[:20],
    }
    
    print(f"\nCouverture du vocabulaire: {stats['coverage']:.1f}%")
    print(f"\nMots les plus frequents:")
    for word, count in most_common[:20]:
        print(f"  {word}: {count}")
    
    return vocab, stats


# =========================================================================
# PREPARATION DES DONNEES
# =========================================================================

def prepare_data(corpus: List[str], vocab: HarmonicVocabulary, 
                 seq_length: int = 64, batch_size: int = 16) -> torch.utils.data.DataLoader:
    """
    Prepare les donnees d'entrainement.
    
    Args:
        corpus: Liste de textes
        vocab: Vocabulaire harmonique
        seq_length: Longueur des sequences
        batch_size: Taille de batch
    
    Returns:
        dataloader: DataLoader PyTorch
    """
    print(f"\n{'='*60}")
    print(f"PREPARATION DES DONNEES")
    print(f"{'='*60}")
    
    # Tokenizer
    tokenizer = re.compile(r"\b\w+\b|[.,!?;:()\[\]{}'\"-]")
    
    # Encoder tous les textes
    all_ids = []
    for text in corpus:
        tokens = tokenizer.findall(text.lower())
        ids = [vocab.token_to_id.get(t, vocab.UNK_ID) for t in tokens]
        all_ids.extend(ids)
    
    print(f"Total tokens: {len(all_ids)}")
    
    # Creer les sequences
    sequences = []
    for i in range(0, len(all_ids) - seq_length - 1, seq_length // 2):
        seq = all_ids[i:i + seq_length + 1]
        if len(seq) == seq_length + 1:
            sequences.append(seq)
    
    print(f"Sequences: {len(sequences)}")
    
    # Dataset
    class TextDataset(torch.utils.data.Dataset):
        def __init__(self, sequences):
            self.sequences = sequences
        
        def __len__(self):
            return len(self.sequences)
        
        def __getitem__(self, idx):
            seq = self.sequences[idx]
            input_ids = torch.tensor(seq[:-1], dtype=torch.long)
            labels = torch.tensor(seq[1:], dtype=torch.long)
            return input_ids, labels
    
    dataset = TextDataset(sequences)
    dataloader = torch.utils.data.DataLoader(
        dataset, batch_size=batch_size, shuffle=True,
        num_workers=0, drop_last=True
    )
    
    print(f"Batches: {len(dataloader)} (batch_size={batch_size})")
    
    return dataloader


# =========================================================================
# ENTRAINEMENT
# =========================================================================

def train_epoch(decoder: HarmonicDecoder, dataloader: torch.utils.data.DataLoader,
                optimizer: torch.optim.Optimizer, device: str,
                epoch: int, num_epochs: int) -> Dict:
    """
    Entraine le decodeur pour une epoque.
    
    Args:
        decoder: Decodeur harmonique
        dataloader: DataLoader
        optimizer: Optimiseur
        device: Device
        epoch: Epoque actuelle
        num_epochs: Nombre total d'epoques
    
    Returns:
        metrics: Metriques d'entrainement
    """
    decoder.train()
    total_loss = 0.0
    total_perplexity = 0.0
    num_batches = 0
    
    start_time = time.time()
    
    for batch_idx, (input_ids, labels) in enumerate(dataloader):
        input_ids = input_ids.to(device)
        labels = labels.to(device)
        
        # Forward pass
        logits = decoder(input_ids)
        
        # Loss
        loss = F.cross_entropy(
            logits.view(-1, decoder.vocab_size),
            labels.view(-1)
        )
        
        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(decoder.parameters(), max_norm=1.0)
        optimizer.step()
        
        # Metriques
        total_loss += loss.item()
        total_perplexity += math.exp(min(loss.item(), 10))
        num_batches += 1
        
        # Progression
        if (batch_idx + 1) % 10 == 0:
            avg_loss = total_loss / num_batches
            avg_ppl = total_perplexity / num_batches
            elapsed = time.time() - start_time
            print(f"\r  Epoch {epoch+1}/{num_epochs} | Batch {batch_idx+1}/{len(dataloader)} | "
                  f"Loss: {avg_loss:.4f} | PPL: {avg_ppl:.2f} | Temps: {elapsed:.1f}s", end="")
    
    print()
    
    avg_loss = total_loss / num_batches
    avg_ppl = total_perplexity / num_batches
    
    return {
        'loss': avg_loss,
        'perplexity': avg_ppl,
        'time': time.time() - start_time,
    }


def train(decoder: HarmonicDecoder, dataloader: torch.utils.data.DataLoader,
          config: Dict) -> List[Dict]:
    """
    Entraine le decodeur harmonique.
    
    Args:
        decoder: Decodeur harmonique
        dataloader: DataLoader
        config: Configuration d'entrainement
    
    Returns:
        history: Historique d'entrainement
    """
    print(f"\n{'='*60}")
    print(f"ENTRAINEMENT DU DECODEUR HARMONIQUE")
    print(f"{'='*60}")
    print(f"Device: {config['device']}")
    print(f"Epoques: {config['num_epochs']}")
    print(f"Learning rate: {config['learning_rate']}")
    print(f"Parametres: {sum(p.numel() for p in decoder.parameters()):,}")
    
    # Optimiseur
    optimizer = torch.optim.AdamW(
        decoder.parameters(),
        lr=config['learning_rate'],
        weight_decay=0.01
    )
    
    # Scheduler
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=config['num_epochs']
    )
    
    # Creer le repertoire de sauvegarde
    os.makedirs(config['model_dir'], exist_ok=True)
    
    history = []
    best_loss = float('inf')
    
    for epoch in range(config['num_epochs']):
        # Entrainement
        metrics = train_epoch(
            decoder, dataloader, optimizer,
            config['device'], epoch, config['num_epochs']
        )
        
        metrics['learning_rate'] = scheduler.get_last_lr()[0]
        history.append(metrics)
        
        # Sauvegarde
        if (epoch + 1) % config['save_every'] == 0:
            save_path = os.path.join(config['model_dir'], f'decoder_epoch_{epoch+1}.pt')
            torch.save({
                'epoch': epoch + 1,
                'model_state_dict': decoder.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': metrics['loss'],
                'config': config,
            }, save_path)
            print(f"\n  [SAUVEGARDE] Modele sauvegarde: {save_path}")
        
        # Meilleur modele
        if metrics['loss'] < best_loss:
            best_loss = metrics['loss']
            best_path = os.path.join(config['model_dir'], 'decoder_best.pt')
            torch.save({
                'epoch': epoch + 1,
                'model_state_dict': decoder.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': best_loss,
                'config': config,
            }, best_path)
        
        scheduler.step()
        
        # Afficher le resume
        print(f"\n  >>> Epoch {epoch+1}/{config['num_epochs']} | "
              f"Loss: {metrics['loss']:.4f} | PPL: {metrics['perplexity']:.2f} | "
              f"LR: {metrics['learning_rate']:.6f} | "
              f"Temps: {metrics['time']:.1f}s")
    
    # Sauvegarde finale
    final_path = os.path.join(config['model_dir'], 'decoder_final.pt')
    torch.save({
        'epoch': config['num_epochs'],
        'model_state_dict': decoder.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'loss': metrics['loss'],
        'config': config,
    }, final_path)
    print(f"\n[SAUVEGARDE] Modele final: {final_path}")
    
    return history


# =========================================================================
# GENERATION DE TEXTE
# =========================================================================

def generate_text(decoder: HarmonicDecoder, vocab: HarmonicVocabulary,
                  prompt: str, max_tokens: int = 64,
                  temperature: float = 0.8, top_k: int = 20,
                  repetition_penalty: float = 1.2) -> str:
    """
    Genere du texte a partir d'un prompt.
    
    Args:
        decoder: Decodeur entraine
        vocab: Vocabulaire harmonique
        prompt: Texte d'amorce
        max_tokens: Nombre max de tokens a generer
        temperature: Temperature d'echantillonnage
        top_k: Top-K sampling
        repetition_penalty: Penalite de repetition
    
    Returns:
        generated: Texte genere
    """
    decoder.eval()
    
    # Tokenizer
    tokenizer = re.compile(r"\b\w+\b|[.,!?;:()\[\]{}'\"-]")
    
    # Encoder le prompt
    prompt_tokens = tokenizer.findall(prompt.lower())
    input_ids = [vocab.token_to_id.get(t, vocab.UNK_ID) for t in prompt_tokens]
    
    if len(input_ids) == 0:
        input_ids = [vocab.BOS_ID]
    
    # Generer
    generated_ids = list(input_ids)
    
    with torch.no_grad():
        for _ in range(max_tokens):
            # Prendre les derniers tokens (limite de contexte)
            context = generated_ids[-64:]
            input_tensor = torch.tensor([context], dtype=torch.long).to(TRAIN_CONFIG['device'])
            
            # Forward
            logits = decoder(input_tensor)
            next_logits = logits[0, -1, :]
            
            # Temperature
            next_logits = next_logits / temperature
            
            # Repetition penalty
            for token_id in set(generated_ids[-20:]):
                next_logits[token_id] /= repetition_penalty
            
            # Top-K
            if top_k > 0:
                values, indices = torch.topk(next_logits, top_k)
                next_logits[next_logits < values[-1]] = float('-inf')
            
            # Echantillonnage
            probs = F.softmax(next_logits, dim=-1)
            next_id = torch.multinomial(probs, 1).item()
            
            # Arret
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
    
    # Reassembler
    text = ' '.join(generated_tokens)
    text = re.sub(r'\s+([.,!?;:()\[\]{}"\'-])', r'\1', text)
    text = re.sub(r"\s+'\s+", "'", text)
    text = re.sub(r"\s+n't", "n't", text)
    
    return text


def test_generation(decoder: HarmonicDecoder, vocab: HarmonicVocabulary):
    """
    Teste la generation de texte avec differents prompts.
    """
    print(f"\n{'='*60}")
    print(f"TEST DE GENERATION DE TEXTE")
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
    ]
    
    for prompt in prompts:
        print(f"\nPrompt: '{prompt}'")
        generated = generate_text(
            decoder, vocab, prompt,
            max_tokens=32,
            temperature=0.7,
            top_k=15,
            repetition_penalty=1.1
        )
        print(f"Genere: {generated}")


# =========================================================================
# FONCTION PRINCIPALE
# =========================================================================

def main():
    """Fonction principale d'entrainement."""
    print(f"\n{'='*60}")
    print(f"ENTRAINEMENT DU GENERATEUR DE TEXTE HARMONIQUE")
    print(f"{'='*60}")
    print(f"Device: {TRAIN_CONFIG['device']}")
    
    # 1. Charger le corpus
    print(f"\n[1/5] Chargement du corpus...")
    corpus = get_training_corpus()
    print(f"  {len(corpus)} textes charges")
    
    # 2. Construire le vocabulaire
    print(f"\n[2/5] Construction du vocabulaire...")
    vocab, vocab_stats = build_vocabulary(corpus, TRAIN_CONFIG['vocab_size'])
    
    # 3. Preparer les donnees
    print(f"\n[3/5] Preparation des donnees...")
    dataloader = prepare_data(
        corpus, vocab,
        seq_length=TRAIN_CONFIG['seq_length'],
        batch_size=TRAIN_CONFIG['batch_size']
    )
    
    # 4. Creer le decodeur
    print(f"\n[4/5] Creation du decodeur harmonique...")
    decoder = HarmonicDecoder(
        vocab_size=TRAIN_CONFIG['vocab_size'],
        embed_dim=TRAIN_CONFIG['embed_dim'],
        hidden_dim=TRAIN_CONFIG['hidden_dim'],
        num_layers=TRAIN_CONFIG['num_layers'],
        num_heads=TRAIN_CONFIG['num_heads']
    ).to(TRAIN_CONFIG['device'])
    
    print(f"  Parametres: {sum(p.numel() for p in decoder.parameters()):,}")
    
    # 5. Entrainement
    print(f"\n[5/5] Entrainement...")
    history = train(decoder, dataloader, TRAIN_CONFIG)
    
    # Afficher l'historique
    print(f"\n{'='*60}")
    print(f"HISTORIQUE D'ENTRAINEMENT")
    print(f"{'='*60}")
    print(f"{'Epoch':>6} | {'Loss':>8} | {'PPL':>8} | {'LR':>10} | {'Temps':>8}")
    print("-" * 50)
    for i, m in enumerate(history):
        print(f"{i+1:>6} | {m['loss']:>8.4f} | {m['perplexity']:>8.2f} | "
              f"{m['learning_rate']:>10.6f} | {m['time']:>8.1f}s")
    
    # Tester la generation
    test_generation(decoder, vocab)
    
    # Sauvegarder le vocabulaire
    vocab_path = os.path.join(TRAIN_CONFIG['model_dir'], 'vocab.json')
    vocab_data = {
        'token_to_id': vocab.token_to_id,
        'id_to_token': {str(k): v for k, v in vocab.id_to_token.items()},
        'vocab_size': vocab.vocab_size,
        'embed_dim': vocab.embed_dim,
    }
    with open(vocab_path, 'w', encoding='utf-8') as f:
        json.dump(vocab_data, f, ensure_ascii=False, indent=2)
    print(f"\n[SAUVEGARDE] Vocabulaire: {vocab_path}")
    
    # Sauvegarder l'historique
    history_path = os.path.join(TRAIN_CONFIG['model_dir'], 'history.json')
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)
    print(f"[SAUVEGARDE] Historique: {history_path}")
    
    print(f"\n{'='*60}")
    print(f"ENTRAINEMENT TERMINE !")
    print(f"{'='*60}")
    print(f"Meilleure loss: {min(h['loss'] for h in history):.4f}")
    print(f"Meilleure perplexite: {min(h['perplexity'] for h in history):.2f}")
    print(f"Modele sauvegarde dans: {TRAIN_CONFIG['model_dir']}")
    
    return decoder, vocab, history


if __name__ == "__main__":
    decoder, vocab, history = main()
