"""
Distillation Harmonique V2 : BERT -> Embedding avec cibles pre-calculees
=======================================================================

Probleme identifie :
  PureSignatureProjectionV4 est deterministe et ne depend que de la
  structure geometrique de l'embedding. Les cibles simulees ne sont
  pas assez informatives pour entrainer l'embedding.

Solution V2 :
  1. Pre-calculer les cibles BERT hors-ligne (une seule fois)
  2. Les sauvegarder dans un fichier .pt
  3. Entrainer l'embedding par dessus avec une loss qui compare
     DIRECTEMENT les signatures 9D de l'embedding aux cibles BERT
  4. Apres entrainement, l'embedding produit des signatures qui
     ressemblent a celles de BERT

Architecture :
  Phase 0 : Pre-calcul BERT (hors-ligne, GPU si disponible)
  Phase 1 : Entrainement embedding (rapide, CPU)
  Phase 2 : Validation (comparaison avant/apres)
  Phase 3 : Integration dans le routeur hybride
"""

import os
os.environ['HF_HOME'] = 'C:\\Users\\maatc\\hf_cache'
os.environ['XDG_CACHE_HOME'] = 'C:\\Users\\maatc\\hf_cache'
os.environ['TRANSFORMERS_CACHE'] = 'C:\\Users\\maatc\\hf_cache\\transformers'
os.environ['HUGGINGFACE_HUB_CACHE'] = 'C:\\Users\\maatc\\hf_cache\\hub'

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import time
import json
from torch.utils.data import Dataset, DataLoader

from model.harmonic_pure_signatures_v4 import PureSignatureProjectionV4


# =========================================================================
# GENERATEUR DE CIBLES BERT (hors-ligne)
# =========================================================================

class BertTargetGenerator:
    """
    Genere les signatures 9D cibles via BERT.
    S'execute une seule fois, sauvegarde les resultats.
    """
    
    def __init__(self, device='cpu'):
        self.device = device
        self.bert = None
        self.tokenizer = None
    
    def load_bert(self):
        """Charge BERT (lazy loading)."""
        if self.bert is None:
            try:
                from transformers import BertModel, BertTokenizer
                self.tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
                self.bert = BertModel.from_pretrained(
                    'bert-base-uncased', output_hidden_states=True
                ).to(self.device)
                self.bert.eval()
                print(f"  [BERT charge: 109M params sur {self.device}]")
                return True
            except Exception as e:
                print(f"  [ERREUR chargement BERT: {e}]")
                return False
        return True
    
    def signature_from_bert(self, hidden_states):
        """
        Extrait une signature 9D depuis les hidden states de BERT.
        
        Args:
            hidden_states: [1, seq_len, 768] - derniere couche BERT
        
        Returns:
            torch.Tensor [9] - signature harmonique
        """
        h = hidden_states.mean(dim=1)  # [1, 768]
        h = h.squeeze(0)  # [768]
        
        # 1. phi : entropie normalisee
        h_norm = torch.softmax(h, dim=-1)
        entropy = -(h_norm * torch.log(h_norm + 1e-8)).sum()
        phi = entropy / np.log(h.size(-1))
        
        # 2. alpha : rugosite fractale (FFT)
        h_fft = torch.fft.rfft(h, norm='ortho')
        freqs = torch.abs(h_fft)
        alpha = 1.0 - (freqs[-1] / (freqs[0] + 1e-8))
        
        # 3. reasoning : coherence interne (auto-similarite)
        h_2d = h.unsqueeze(0).unsqueeze(0)  # [1, 1, 768]
        cos_sim = torch.cosine_similarity(h_2d, h_2d.transpose(1, 2), dim=-1)
        reasoning = cos_sim.mean()
        
        # 4. creativity : variance de similarite
        creativity = cos_sim.std()
        
        # 5. math : periodicite FFT
        fft_mag = torch.abs(torch.fft.rfft(h, norm='ortho'))
        math = fft_mag[1:].max() / (fft_mag[0] + 1e-8)
        
        # 6. factual : norme relative
        factual = torch.norm(h) / np.sqrt(h.size(-1))
        
        # 7. code : ratio basse/haute frequence
        half = fft_mag.size(-1) // 2
        low = fft_mag[:half].sum()
        high = fft_mag[half:].sum()
        code = low / (high + 1e-8)
        
        # 8. emotion : asymetrie de distribution
        emotion = torch.abs(h.mean())
        
        # 9. temporal : variation normalisee
        temporal = torch.std(h)
        
        sig = torch.stack([phi, alpha, reasoning, creativity, math,
                          factual, code, emotion, temporal])
        
        # Normalisation dans [0, 1]
        sig = torch.sigmoid(sig - sig.mean())
        
        return sig
    
    def generate_targets(self, phrases, batch_size=8):
        """
        Genere les cibles BERT pour une liste de phrases.
        
        Args:
            phrases: list[str]
            batch_size: int
        
        Returns:
            torch.Tensor [len(phrases), 9]
        """
        if not self.load_bert():
            return None
        
        all_signatures = []
        
        with torch.no_grad():
            for i in range(0, len(phrases), batch_size):
                batch = phrases[i:i+batch_size]
                
                inputs = self.tokenizer(
                    batch, return_tensors='pt',
                    padding=True, truncation=True, max_length=64
                ).to(self.device)
                
                outputs = self.bert(**inputs)
                hidden = outputs.hidden_states[-1]  # [batch, seq_len, 768]
                
                for j in range(len(batch)):
                    sig = self.signature_from_bert(hidden[j:j+1])
                    all_signatures.append(sig.cpu())
                
                if (i + batch_size) % 32 == 0 or i + batch_size >= len(phrases):
                    print(f"    [{i+len(batch)}/{len(phrases)}] signatures generees")
        
        return torch.stack(all_signatures)
    
    def generate_and_save(self, phrases, output_path='bert_targets.pt'):
        """Genere et sauvegarde les cibles."""
        print(f"\n  Generation des cibles BERT pour {len(phrases)} phrases...")
        targets = self.generate_targets(phrases)
        
        if targets is None:
            print("  [ECHEC] Generation impossible")
            return None
        
        torch.save({
            'targets': targets,
            'phrases': phrases,
            'timestamp': time.time(),
        }, output_path)
        
        print(f"  [OK] {len(targets)} cibles sauvegardees dans {output_path}")
        
        # Stats
        print(f"\n  Stats des cibles BERT :")
        dims = ['phi', 'alpha', 'reasoning', 'creativity', 'math',
                'factual', 'code', 'emotion', 'temporal']
        for i, name in enumerate(dims):
            vals = targets[:, i]
            print(f"    {name:<12} mean={vals.mean():.4f} std={vals.std():.4f} "
                  f"min={vals.min():.4f} max={vals.max():.4f}")
        
        return targets


# =========================================================================
# MODELE DE DISTILLATION V2
# =========================================================================

class DistillationModelV2(nn.Module):
    """
    Modele de distillation V2.
    
    Au lieu d'utiliser PureSignatureProjectionV4 (deterministe),
    on utilise un petit reseau qui apprend a mapper l'embedding
    vers les signatures 9D cibles.
    
    Architecture :
      Embedding (vocab_size, 512) -> Linear(512, 256) -> ReLU -> Linear(256, 9)
    
    Loss : L2 + Cosinus entre prediction et cible BERT
    """
    
    def __init__(self, vocab_size=2000, hidden_size=512):
        super().__init__()
        
        # Embedding initialise harmoniquement
        self.embedding = nn.Embedding(vocab_size, hidden_size)
        with torch.no_grad():
            token_ids = torch.arange(vocab_size, dtype=torch.float32).unsqueeze(1)
            dims = torch.arange(hidden_size, dtype=torch.float32).unsqueeze(0)
            phase = token_ids * dims * 1.618033988749895 / hidden_size
            amplitude = torch.exp(-dims * 0.618033988749895 / hidden_size)
            init_weights = torch.cos(phase) * amplitude
            init_weights = init_weights / (torch.sqrt(torch.mean(init_weights ** 2) + 1e-8))
            self.embedding.weight.data = init_weights
        
        # Petit reseau de projection (entrainable)
        self.projection = nn.Sequential(
            nn.Linear(hidden_size, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 9),
        )
        
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
    
    def forward(self, input_ids):
        """
        Args:
            input_ids: [batch, seq_len]
        Returns:
            signatures: [batch, 9]
        """
        # Embedding
        emb = self.embedding(input_ids)  # [batch, seq_len, hidden]
        
        # Moyenne sur la sequence
        emb_mean = emb.mean(dim=1)  # [batch, hidden]
        
        # Projection vers signature 9D
        signatures = self.projection(emb_mean)  # [batch, 9]
        
        # Normalisation sigmoid pour [0, 1]
        signatures = torch.sigmoid(signatures)
        
        return signatures


class DistillationLossV2(nn.Module):
    """
    Loss composee V2 :
    - L2 : proximite numerique
    - Cosinus : alignement directionnel
    - KL : divergence de distribution
    """
    
    def __init__(self, lambda_cos=0.3, lambda_kl=0.1):
        super().__init__()
        self.lambda_cos = lambda_cos
        self.lambda_kl = lambda_kl
        self.mse = nn.MSELoss()
    
    def forward(self, pred, target):
        # L2 loss
        loss_l2 = self.mse(pred, target)
        
        # Cosinus loss
        cos_sim = torch.sum(pred * target, dim=1) / (
            torch.norm(pred, dim=1) * torch.norm(target, dim=1) + 1e-8
        )
        loss_cos = (1.0 - cos_sim).mean()
        
        # KL divergence (distribution des dimensions)
        pred_dist = torch.softmax(pred, dim=1)
        target_dist = torch.softmax(target, dim=1)
        loss_kl = torch.sum(target_dist * torch.log(target_dist / (pred_dist + 1e-8) + 1e-8), dim=1).mean()
        
        return loss_l2 + self.lambda_cos * loss_cos + self.lambda_kl * loss_kl


# =========================================================================
# DATASET AVEC CIBLES PRE-CALCULEES
# =========================================================================

class DistillationDataset(Dataset):
    """
    Dataset qui charge les phrases ET leurs cibles BERT pre-calculees.
    """
    
    def __init__(self, phrases, targets, vocab_size=2000):
        self.phrases = phrases
        self.targets = targets
        
        # Construction du vocabulaire
        self.vocab = {'<PAD>': 0, '<UNK>': 1}
        next_id = 2
        for phrase in phrases:
            for mot in phrase.lower().split():
                if mot not in self.vocab and next_id < vocab_size - 1:
                    self.vocab[mot] = next_id
                    next_id += 1
    
    def __len__(self):
        return len(self.phrases)
    
    def __getitem__(self, idx):
        phrase = self.phrases[idx]
        tokens = phrase.lower().split()
        input_ids = torch.tensor(
            [self.vocab.get(t, self.vocab['<UNK>']) for t in tokens],
            dtype=torch.long
        )
        target = self.targets[idx]
        return input_ids, target, phrase


def collate_distillation(batch):
    """Collate function pour le DataLoader."""
    input_ids_list = [b[0] for b in batch]
    targets = torch.stack([b[1] for b in batch])
    phrases = [b[2] for b in batch]
    
    # Padding
    max_len = max(ids.size(0) for ids in input_ids_list)
    padded = torch.zeros(len(input_ids_list), max_len, dtype=torch.long)
    for i, ids in enumerate(input_ids_list):
        padded[i, :ids.size(0)] = ids
    
    return padded, targets, phrases


# =========================================================================
# ENTRAINEMENT V2
# =========================================================================

class DistillationTrainerV2:
    """
    Entraineur V2 avec cibles BERT pre-calculees.
    """
    
    def __init__(self, vocab_size=2000, hidden_size=512, device='cpu'):
        self.device = device
        self.model = DistillationModelV2(vocab_size, hidden_size).to(device)
        self.loss_fn = DistillationLossV2(lambda_cos=0.3, lambda_kl=0.1)
        self.optimizer = optim.AdamW(self.model.parameters(), lr=5e-4, weight_decay=1e-5)
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(self.optimizer, T_max=50)
        
        self.loss_history = []
        self.cos_history = []
    
    def train_epoch(self, dataloader):
        """Entraine une epoque."""
        self.model.train()
        total_loss = 0
        total_cos = 0
        n_batches = 0
        
        for input_ids, targets, _ in dataloader:
            input_ids = input_ids.to(self.device)
            targets = targets.to(self.device)
            
            self.optimizer.zero_grad()
            
            predictions = self.model(input_ids)
            loss = self.loss_fn(predictions, targets)
            
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.optimizer.step()
            
            cos_val = torch.cosine_similarity(predictions, targets, dim=1).mean().item()
            
            total_loss += loss.item()
            total_cos += cos_val
            n_batches += 1
        
        avg_loss = total_loss / n_batches
        avg_cos = total_cos / n_batches
        
        self.loss_history.append(avg_loss)
        self.cos_history.append(avg_cos)
        
        return avg_loss, avg_cos
    
    def train(self, dataset, n_epochs=50, batch_size=16):
        """Entrainement complet."""
        dataloader = DataLoader(
            dataset, batch_size=batch_size, shuffle=True,
            collate_fn=collate_distillation
        )
        
        print(f"\n{'='*60}")
        print(f"ENTRAINEMENT DISTILLATION V2")
        print(f"{'='*60}")
        print(f"  Device  : {self.device}")
        print(f"  Epochs  : {n_epochs}")
        print(f"  Batch   : {batch_size}")
        print(f"  Dataset : {len(dataset)} echantillons")
        print(f"  Vocab   : {len(dataset.vocab)} mots")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        for epoch in range(n_epochs):
            loss, cos = self.train_epoch(dataloader)
            self.scheduler.step()
            
            if (epoch + 1) % 5 == 0 or epoch == 0:
                lr = self.optimizer.param_groups[0]['lr']
                elapsed = time.time() - start_time
                print(f"  Epoch {epoch+1:3d}/{n_epochs} | Loss: {loss:.6f} | Cos: {cos:.4f} | LR: {lr:.2e} | {elapsed:.1f}s")
        
        total_time = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"ENTRAINEMENT TERMINE en {total_time:.1f}s")
        print(f"  Loss finale : {self.loss_history[-1]:.6f}")
        print(f"  Cos finale   : {self.cos_history[-1]:.4f}")
        print(f"{'='*60}")
        
        return self.loss_history, self.cos_history
    
    def evaluate(self, dataset, phrases_test=None):
        """Evalue la qualite des signatures."""
        self.model.eval()
        
        if phrases_test is None:
            phrases_test = dataset.phrases[:5]
        
        print(f"\n{'='*60}")
        print(f"EVALUATION DES SIGNATURES DISTILLEES")
        print(f"{'='*60}")
        print(f"\n  {'Phrase':<45} {'Phi':<8} {'Reasoning':<10} {'Creativite':<12} {'Emotion':<10}")
        print(f"  {'-'*45} {'-'*8} {'-'*10} {'-'*12} {'-'*10}")
        
        with torch.no_grad():
            for phrase in phrases_test:
                tokens = phrase.lower().split()
                input_ids = torch.zeros(1, len(tokens), dtype=torch.long)
                for j, t in enumerate(tokens):
                    input_ids[0, j] = dataset.vocab.get(t, dataset.vocab['<UNK>'])
                
                input_ids = input_ids.to(self.device)
                sig = self.model(input_ids)[0].cpu().numpy()
                
                desc = phrase[:42] + '..' if len(phrase) > 42 else phrase
                print(f"  {desc:<45} {sig[0]:<8.3f} {sig[2]:<10.3f} {sig[3]:<12.3f} {sig[7]:<10.3f}")
        
        print(f"\n{'='*60}")
    
    def compare_with_bert(self, dataset, phrases_test, bert_targets):
        """Compare les signatures distillees avec les cibles BERT."""
        self.model.eval()
        
        print(f"\n{'='*70}")
        print(f"COMPARAISON DISTILLE vs BERT")
        print(f"{'='*70}")
        print(f"\n  {'Phrase':<40} {'D_Phi':<8} {'D_Reas':<8} {'D_Crea':<8} {'D_Emo':<8} {'Cos':<8}")
        print(f"  {'-'*40} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
        
        with torch.no_grad():
            for i, phrase in enumerate(phrases_test):
                tokens = phrase.lower().split()
                input_ids = torch.zeros(1, len(tokens), dtype=torch.long)
                for j, t in enumerate(tokens):
                    input_ids[0, j] = dataset.vocab.get(t, dataset.vocab['<UNK>'])
                
                input_ids = input_ids.to(self.device)
                sig_pred = self.model(input_ids)[0].cpu()
                sig_target = bert_targets[i].cpu()
                
                diff = torch.abs(sig_pred - sig_target)
                cos = torch.cosine_similarity(sig_pred.unsqueeze(0), sig_target.unsqueeze(0), dim=1)[0]
                
                desc = phrase[:37] + '..' if len(phrase) > 37 else phrase
                print(f"  {desc:<40} {diff[0]:<8.4f} {diff[2]:<8.4f} {diff[3]:<8.4f} {diff[7]:<8.4f} {cos:<8.4f}")
        
        # Stats globales
        all_diffs = []
        all_cos = []
        with torch.no_grad():
            for i in range(len(phrases_test)):
                phrase = phrases_test[i]
                tokens = phrase.lower().split()
                input_ids = torch.zeros(1, len(tokens), dtype=torch.long)
                for j, t in enumerate(tokens):
                    input_ids[0, j] = dataset.vocab.get(t, dataset.vocab['<UNK>'])
                
                input_ids = input_ids.to(self.device)
                sig_pred = self.model(input_ids)[0].cpu()
                sig_target = bert_targets[i].cpu()
                
                all_diffs.append(torch.abs(sig_pred - sig_target).mean().item())
                all_cos.append(torch.cosine_similarity(
                    sig_pred.unsqueeze(0), sig_target.unsqueeze(0), dim=1
                )[0].item())
        
        print(f"\n  Stats globales ({len(phrases_test)} phrases):")
        print(f"    Erreur moyenne : {np.mean(all_diffs):.4f}")
        print(f"    Cosinus moyen  : {np.mean(all_cos):.4f}")
        print(f"{'='*70}")
    
    def save(self, path='harmonic_distilled_v2.pt'):
        """Sauvegarde le modele entraine."""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'loss_history': self.loss_history,
            'cos_history': self.cos_history,
            'vocab_size': self.model.vocab_size,
            'hidden_size': self.model.hidden_size,
        }, path)
        print(f"\n  Modele distille sauvegarde dans : {path}")
        return path
    
    def load(self, path='harmonic_distilled_v2.pt'):
        """Charge le modele entraine."""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.loss_history = checkpoint['loss_history']
        self.cos_history = checkpoint['cos_history']
        print(f"\n  Modele distille charge depuis : {path}")
        return self


# =========================================================================
# CORPUS D'ENTRAINEMENT
# =========================================================================

def generer_corpus_entrainement(taille=200):
    """Genere un corpus equilibre pour l'entrainement."""
    corpus = []
    
    # 1. Mathematiques (20%)
    maths = [
        "2 + 2 = 4", "3 * 5 = 15", "10 / 2 = 5", "E = mc^2",
        "La derivee de x^2 est 2x", "Le theoreme de Pythagore",
        "Pi est approximativement 3.14159", "Les nombres premiers sont infinis",
        "Le determinant d'une matrice", "La transformee de Fourier",
        "sin(x)^2 + cos(x)^2 = 1", "log(a*b) = log(a) + log(b)",
        "La somme des angles d'un triangle est 180", "F = ma",
        "a^2 + b^2 = c^2", "x^2 + y^2 = z^2",
    ]
    corpus.extend(maths)
    
    # 2. Poetique / Creatif (20%)
    poetique = [
        "Le soleil couchant embrase l'horizon de ses derniers feux pourpres",
        "La lune se leve doucement sur la mer endormie",
        "Les etoiles dansent dans le ciel infini",
        "Le vent murmure des secrets aux feuilles des arbres",
        "Une larme glisse sur la joue du temps qui passe",
        "L'amour est un oiseau qui chante meme dans la tempete",
        "Les reves sont les fenetres de l'ame vers l'infini",
        "La pluie tombe comme des perles de cristal",
        "Un sourire peut changer le monde",
        "La beaute est dans les yeux de celui qui regarde",
        "Les mots sont des ponts entre les coeurs",
        "La musique adoucit les moeurs",
        "L'art est le miroir de l'ame",
        "La poesie est la langue de l'indicible",
        "Les couleurs du couchant peignent le ciel",
    ]
    corpus.extend(poetique)
    
    # 3. Code / Technique (15%)
    code = [
        "if x > 0: return x + 1", "for i in range(10): print(i)",
        "while True: break", "class Animal: def __init__(self): pass",
        "import numpy as np", "def fibonacci(n): return n if n < 2 else fibonacci(n-1) + fibonacci(n-2)",
        "try: except Exception as e: pass", "with open('file.txt') as f: content = f.read()",
        "lambda x: x * 2", "map(lambda x: x**2, range(10))",
        "Le protocole TCP/IP garantit la livraison des paquets",
        "L'algorithme de tri rapide a une complexite O(n log n)",
        "La base de donnees est indexee par B-tree",
        "Le cache LRU evince les entrees les moins recentes",
        "L'API REST utilise les methodes HTTP GET POST PUT DELETE",
    ]
    corpus.extend(code)
    
    # 4. Emotionnel (15%)
    emotion = [
        "Je t'aime plus que tout au monde",
        "Mon coeur est brise en mille morceaux",
        "La joie de te revoir est indescriptible",
        "La tristesse m'envahit comme une vague",
        "Je suis si heureux que tu sois la",
        "La peur me paralyse quand je pense a demain",
        "La colere monte en moi comme un volcan",
        "La douceur de ta voix m'apaise",
        "L'espoir renait comme le printemps",
        "La nostalgie du temps passe me serre le coeur",
        "L'excitation du voyage me transporte",
        "La serenite du matin m'emplit de paix",
    ]
    corpus.extend(emotion)
    
    # 5. Factuel / Scientifique (15%)
    factuel = [
        "La Terre tourne autour du Soleil en 365 jours",
        "L'eau bout a 100 degres Celsius au niveau de la mer",
        "Le corps humain contient environ 60% d'eau",
        "La vitesse de la lumiere est de 300 000 km/s",
        "L'ADN est compose de quatre bases nucleiques",
        "Le cerveau humain a environ 86 milliards de neurones",
        "La photosynthese convertit le CO2 en oxygene",
        "La gravite est proportionnelle a la masse",
        "Les electrons tournent autour du noyau atomique",
        "La pression atmospherique diminue avec l'altitude",
        "Le pH mesure l'acidite d'une solution",
        "Les bacteries sont des organismes unicellulaires",
    ]
    corpus.extend(factuel)
    
    # 6. Finance / Transactionnel (10%)
    finance = [
        "Achat de 100 actions Apple a 150 dollars",
        "Virement de 5000 euros vers compte epargne",
        "Paiement loyer mensuel 1200 euros",
        "Achat supermarche 85 euros",
        "TRANSFERT URGENT 50000$ VERS COMPTE INCONNU PANAMA",
        "VIREMENT MASSIF FONDS NON JUSTIFIE ORIGINE DOUTEUSE",
        "Depot especes 10000 euros sans justificatif",
        "Transaction multiple petits montants 24h",
    ]
    corpus.extend(finance)
    
    # 7. Medical (5%)
    medical = [
        "Toux grasse avec fievre moderee depuis 3 jours",
        "Douleur a la poitrine apres effort",
        "Douleur au ventre apres les repas",
        "Fievre elevee superieure a 38.5 degres",
        "Maux de tete violents avec sensibilite a la lumiere",
        "INJECTER 10ML SOLUTION MYSTERE INTRAVEINEUSE",
        "Administrer 500mg paracetamol toutes les 6h",
    ]
    corpus.extend(medical)
    
    return corpus[:taille]


# =========================================================================
# PIPELINE COMPLET
# =========================================================================

def pipeline_complet(use_bert=True, n_epochs=50):
    """
    Pipeline complet de distillation.
    
    Args:
        use_bert: Si True, utilise BERT pour generer les cibles
        n_epochs: Nombre d'epochs d'entrainement
    """
    print("\n" + "=" * 70)
    print("PIPELINE COMPLET : DISTILLATION HARMONIQUE V2")
    print("=" * 70)
    
    # 1. Generer le corpus
    print("\n[1] Generation du corpus d'entrainement...")
    corpus = generer_corpus_entrainement(taille=200)
    print(f"    {len(corpus)} phrases generees")
    
    # 2. Generer les cibles BERT (ou simulees)
    print("\n[2] Generation des cibles...")
    if use_bert:
        generator = BertTargetGenerator(device='cpu')
        targets = generator.generate_and_save(corpus, 'bert_targets.pt')
    else:
        print("    [Mode simule] Generation de cibles heuristiques...")
        targets = torch.rand(len(corpus), 9) * 0.5 + 0.25
        torch.save({'targets': targets, 'phrases': corpus}, 'bert_targets.pt')
        print(f"    [OK] {len(targets)} cibles simulees sauvegardees")
    
    if targets is None:
        print("    [ECHEC] Utilisation de cibles simulees...")
        targets = torch.rand(len(corpus), 9) * 0.5 + 0.25
    
    # 3. Creer le dataset
    print("\n[3] Creation du dataset de distillation...")
    dataset = DistillationDataset(corpus, targets)
    print(f"    {len(dataset)} echantillons, {len(dataset.vocab)} mots uniques")
    
    # 4. Initialiser l'entraineur
    print("\n[4] Initialisation du modele de distillation...")
    trainer = DistillationTrainerV2(vocab_size=2000, hidden_size=512, device='cpu')
    
    # 5. Evaluation avant entrainement
    print("\n[5] Evaluation AVANT entrainement :")
    phrases_test = [
        "2 + 2 = 4",
        "Le soleil couchant embrase l'horizon",
        "Je t'aime plus que tout au monde",
        "if x > 0: return x + 1",
        "TRANSFERT URGENT 50000$ PANAMA",
    ]
    trainer.evaluate(dataset, phrases_test)
    
    # 6. Entrainement
    print("\n[6] Entrainement de la distillation...")
    trainer.train(dataset, n_epochs=n_epochs, batch_size=16)
    
    # 7. Evaluation apres entrainement
    print("\n[7] Evaluation APRES entrainement :")
    trainer.evaluate(dataset, phrases_test)
    
    # 8. Comparaison avec BERT
    print("\n[8] Comparaison distille vs BERT :")
    trainer.compare_with_bert(dataset, phrases_test, targets)
    
    # 9. Sauvegarde
    trainer.save('harmonic_distilled_v2.pt')
    
    # 10. Bilan
    print("\n" + "=" * 70)
    print("BILAN DE LA DISTILLATION V2")
    print("=" * 70)
    print("""
  Ce qui a change :
    - PureSignatureProjectionV4 (deterministe) -> Reseau de projection (entrainable)
    - Cibles simulees -> Cibles BERT pre-calculees
    - Loss L2 + Cosinus + KL divergence
    - 50 epochs d'entrainement

  Resultats attendus :
    - Les signatures distillees se rapprochent des signatures BERT
    - Cosinus de similarite > 0.9 entre distille et BERT
    - L'embedding a appris a capturer le sens semantique
    - Inference en ~1ms (0 GPU) avec la qualite de BERT

  Boucle de retroaction continue :
    Phase 1 : BERT genere les cibles sur nouveau corpus
    Phase 2 : Embedding s'ajuste par descente de gradient
    Phase 3 : L'embedding remplace l'ancienne version
    Phase 4 : Repeat avec un corpus different
    -> L'embedding s'ameliorE continuellement
    -> Convergence vers la qualite BERT sans le cout BERT
""")
    
    return trainer


if __name__ == '__main__':
    import sys
    
    use_bert = '--no-bert' not in sys.argv
    n_epochs = 50
    
    for i, arg in enumerate(sys.argv):
        if arg.startswith('--epochs='):
            n_epochs = int(arg.split('=')[1])
    
    trainer = pipeline_complet(use_bert=use_bert, n_epochs=n_epochs)
