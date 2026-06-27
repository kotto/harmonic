#!/usr/bin/env python
"""
INCONSCIENT HARMONIQUE DÉFINITIF
=================================
Architecture conscient + inconscient basée sur le transformer harmonique PUR.

Architecture :
┌─────────────────────────────────────────────────────────────┐
│                     CONSCIENCE (Analyseur 9D)                │
│  - Analyse sémantique en 9 dimensions heuristiques          │
│  - Mémoire associative par résonance cosinus                │
│  - Produit une signature 16D de conditionnement             │
├─────────────────────────────────────────────────────────────┤
│                     INCONSCIENT (Transformer PUR)            │
│  - HarmonicFixedEmbedding (50k tokens, base PHI)            │
│  - N × PureHarmonicDecoderLayer (attention résonance + ABC) │
│  - AdaptationLayer apprise (1% params, entraînable)         │
│  - HarmonicFixedLMHead (poids liés)                         │
├─────────────────────────────────────────────────────────────┤
│                     BOUCLE DE GÉNÉRATION                     │
│  - Chaque token : conscient analyse → conditionne hidden    │
│  - Inconscient : prédit P(tokenₜ | contexte, signature 9D)  │
│  - Mémoire : récupère connaissances par résonance           │
└─────────────────────────────────────────────────────────────┘

Usage :
    python conscious_unconscious_harmonique.py           # Test interactif
    python conscious_unconscious_harmonique.py --api     # Serveur REST
"""
import sys, os, math, json, time, hashlib, re
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

# ──────────────────────────────────────────────
# IMPORTS TORCH (inconscient)
# ──────────────────────────────────────────────
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    print("[WARN] PyTorch non installé — mode simulation CPU uniquement")
    TORCH_AVAILABLE = False

# Imports harmoniques purs (si disponibles)
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'harmonic_training'))
    from model.harmonic_pure_model import (
        HarmonicPureForCausalLM, HarmonicFixedEmbedding, HarmonicFixedLMHead
    )
    from model.harmonic_pure_attention import (
        PureHarmonicAttention, PureSignatureProjection,
        compute_phi, compute_alpha, compute_reasoning, compute_creativity,
        compute_math, compute_factual, compute_code
    )
    from model.harmonic_pure_layers import (
        PureHarmonicDecoderLayer, HarmonicFixedTransform
    )
    from model.abc_kernel import PHI, ALPHA, ABCKernel
    HARMONIC_PURE_AVAILABLE = True
    PHI_VALUE = PHI
    ALPHA_VALUE = ALPHA
except ImportError as e:
    print(f"[WARN] Modules harmoniques purs non trouvés: {e}")
    HARMONIC_PURE_AVAILABLE = False
    PHI_VALUE = (1 + 5 ** 0.5) / 2
    ALPHA_VALUE = 1.0 / PHI_VALUE

print(f"[HARMONIC] PHI={PHI_VALUE:.10f}, ALPHA={ALPHA_VALUE:.10f}")
print(f"[HARMONIC] Torch={TORCH_AVAILABLE}, PureModules={HARMONIC_PURE_AVAILABLE}")


# =====================================================================
# CONSTANTES
# =====================================================================
SIG_DIM_9D = 9
SIG_DIM_16D = 16
DIMS_9D = ['phi','alpha','reasoning','creativity','math','factual','code','emotion','temporal']
SEUIL_RESONANCE = 0.7
TOP_K_CONNAISSANCES = 5

# Vocabulaire français pour le tokenizer
_VOCAB_FR = [
    '<PAD>','<UNK>','<BOS>','<EOS>',
    'le','la','les','de','des','du','un','une','et','est','a','dans','que','qui',
    'pas','ne','sur','pour','avec','je','tu','il','elle','on','nous','vous','ils','elles',
    'ce','cet','cette','ces','mon','ton','son','ma','ta','sa',
    'au','aux','en','par','plus','moins','tres','aussi',
    'comme','si','mais','ou','donc','car','ni','or','dont',
    'faire','dire','avoir','etre','aller','pouvoir','vouloir','savoir','voir','venir',
    'prendre','donner','parler','penser','croire','trouver','aimer','devoir','mettre',
    'comprendre','tenir','appeler','laisser','rester','sembler','falloir','passer',
    'rendre','entendre','regarder','sentir','connaitre','courir','porter','arriver',
    'montrer','creer','chercher','suivre','attendre','commencer','finir',
    'perdre','gagner','vivre','mourir','recevoir','demander','repondre','lire','ecrire',
    'marcher','dormir','manger','boire','jouer','travailler','etudier','apprendre',
    'enseigner','decouvrir','devenir','revenir','partir','sortir','entrer','monter',
    'descendre','tomber','lever','poser','ouvrir','fermer','jeter','lancer','tirer',
    'pousser','casser','construire','detruire','changer','garder',
    'temps','chose','monde','vie','homme','femme','enfant','jour','nuit','mois','annee',
    'heure','question','reponse','probleme','solution','idee','raison','travail','maison',
    'ville','pays','histoire','famille','corps','tete','main','coeur','oeil','yeux',
    'voix','visage','amour','peur','joie','tristesse','colere','doute','espoir','paix',
    'guerre','mort','naissance','force','energie','lumiere','ombre','feu','eau','terre',
    'ciel','soleil','lune','etoile','vent','mer','montagne','arbre','fleur','animal',
    'livre','mot','lettre','nombre','science','art','musique','danse','theatre','film',
    'couleur','forme','matiere','esprit','jardin','foret','champ','riviere','lac',
    'rue','place','marche','magasin','ecole','hopital','eglise','temple','chateau',
    'grand','petit','beau','bon','mauvais','vrai','faux','nouveau','vieux','jeune',
    'long','court','haut','bas','fort','faible','rapide','lent','clair','fonce',
    'facile','difficile','grave','leger','plein','vide','riche','pauvre','simple','complexe',
    'important','necessaire','possible','impossible','premier','dernier','prochain','ancien',
    'profond','superficiel','doux','dur','chaud','froid','sec','humide','propre','sale',
    'lourd','leger','amer','brillant','terne','epais','mince','solide','liquide',
    'tout','tous','toute','chaque','quelque','plusieurs','rien','personne','jamais',
    'toujours','souvent','parfois','beaucoup','peu','trop','assez','encore','enfin',
    'alors','apres','avant','depuis','pendant','vers','chez','sans','sous','contre',
    'selon','loin','pres','ici','la','ailleurs','maintenant','hier','demain',
    'bonjour','merci','pardon','oui','non','peut-etre','comment','pourquoi','combien',
    'quand','ou','harmonie','resonance','frequence','onde','phi','nombre','or','proportion',
    'univers','physique','conscience','pensee','intelligence','connaissance','sagesse','verite',
    'infini','eternel','absolu','systeme','modele','theorie','principe','loi','information',
    'reseau','apprentissage','inference','signature','dimension','espace','generation','creation',
    'analyse','synthese','logique','raisonnement','intuition','imagination','sentiment','emotion',
    'realite','cause','effet','zero','un','deux','trois','quatre','cinq','six','sept','huit','neuf','dix',
    'cent','mille','existence','essence','transcendant','dialectique','ontologie','liberte','justice',
    'respect','responsabilite','conscience','inconscient','psyche','archetype','symbole','mythe',
    'psychologie','cerveau','neurone','perception','attention','memoire','langage','reve',
    'emotion','passion','desir','plaisir','douleur','bonheur','souffrance','anxiete','stress',
    'confiance','estime','fierte','honte','culpabilite','regret','empathie','compassion',
    'amitie','haine','jalousie','envie','admiration',
    'technologie','informatique','ordinateur','logiciel','donnee','serveur','internet','cloud',
    'intelligence','artificielle','machine','python','code','programme','api','framework',
    'securite','cryptage','algorithme','memoire','stockage',
    'cosmos','galaxie','planete','gravite','matiere','atome','particule','quantique',
    'espace','dimension','peinture','sculpture','architecture','poesie','roman','legende',
    'rythme','melodie','beaute','harmonie','silence','echo','vibration',
    'sante','medecine','maladie','traitement','guerison','sang','cellule','organe','virus',
    'societe','politique','economie','culture','education','religion','civilisation',
    'loi','droit','citoyen','nation','etat','pouvoir','autorite','institution',
    'passe','present','futur','instant','moment','duree','eternite','cyclique',
    'lundi','mardi','mercredi','jeudi','vendredi','samedi','dimanche',
    'janvier','fevrier','mars','avril','mai','juin','juillet','aout',
    'septembre','octobre','novembre','decembre',
    'printemps','ete','automne','hiver',
    'neant','vide','plein','trouble','clair','obscur','radieux',
    'diaphane','ethere','sublime','ineffable','prodigieux','fulgurant','resplendissant',
    'chatoyant','mysterieux','enigmatique','paradoxal','insaisissable','eclatant',
    'harmonieux','melodieux','cristallin','luminique','transcendant',
    'cependant','neanmoins','toutefois','pourtant','quoique','nonobstant',
    'parce','puisque','ainsi','notamment','physique','chimie','biologie','astronomie',
    'philosophie','theologie','mathematique','informatique','robotique',
]
VOCAB_SIZE = len(_VOCAB_FR)
print(f"[VOCAB] {VOCAB_SIZE} tokens français")


# =====================================================================
# TOKENIZER FRANÇAIS SIMPLE
# =====================================================================
class TokenizerFrancais:
    """Tokenizer français simple (mot → ID) avec normalisation."""
    def __init__(self, vocab=None):
        self.vocab = vocab or _VOCAB_FR
        self.vocab_size = len(self.vocab)
        self.w2i = {w: i for i, w in enumerate(self.vocab)}
        self.i2w = {i: w for i, w in enumerate(self.vocab)}
    
    def encoder(self, texte: str) -> List[int]:
        tks = []
        for m in texte.lower().strip().split():
            c = m.strip('.,!?;:()[]{}"\'-_«»\'’\\/')
            if c in self.w2i:
                tks.append(self.w2i[c])
            elif '<UNK>' in self.w2i:
                tks.append(self.w2i['<UNK>'])
        return tks
    
    def decoder(self, ids: List[int]) -> str:
        return ' '.join(self.i2w.get(i, '<UNK>') for i in ids if i not in (0,))
    
    def couverture(self, texte: str) -> float:
        tks = self.encoder(texte)
        if not tks:
            return 0.0
        n_unk = sum(1 for t in tks if t == 1) if 1 in self.w2i else 0
        return 1.0 - (n_unk / len(tks))


# =====================================================================
# PARTIE CONSCIENCE (Analyseur 9D hérité du proto numpy)
# =====================================================================

class AnalyseurConscient:
    """
    Analyseur 9D — la CONSCIENCE du système.
    Observe le texte produit et le projette dans l'espace harmonique.
    """
    _MARQ_SUB = {
        'que','qui','dont','ou','lequel','laquelle','car','puisque','comme',
        'alors','donc','or','cependant','neanmoins','pourtant','quoique',
        'apres','avant','pendant','depuis','lorsque','quand','sans','malgre'
    }
    _LEXIQUE_EMO = {
        'amour','joie','triste','peur','colere','haine','espoir','paix','bonheur',
        'douleur','passion','desir','plaisir','peine','regret','honte','fierte',
        'tendre','douceur','serenite','calme'
    }
    
    def __init__(self):
        self.creativity_scale = PHI_VALUE
    
    def projeter(self, texte: str) -> np.ndarray:
        if not texte or len(texte.strip()) < 2:
            return np.zeros(SIG_DIM_9D, dtype=np.float32)
        mots = texte.lower().strip().split()
        n = max(len(mots), 1)
        
        phi_v = min(1.0, len(set(mots)) / n * PHI_VALUE)
        
        L = np.array([len(m) for m in mots])
        alpha_v = min(1.0, (L.mean() / 5.0) * (1 + L.std() * 0.2)) if len(mots) >= 2 else 0.3
        
        sub = sum(1 for m in mots if m in self._MARQ_SUB)
        reasoning_v = min(1.0, (sub / n) * 2.5)
        
        rare = sum(1 for m in mots if len(m) > 9 and m.isalpha())
        creativity_v = min(1.0, (rare / n) * PHI_VALUE + 0.05)
        
        chiffres = sum(1 for m in mots if any(c.isdigit() for c in m))
        math_v = min(1.0, (chiffres / n) * 4.0)
        
        factuel_v = min(1.0, (sub / n) * 1.5 + min(0.3, len(re.findall(r'\b\d+\b', texte)) * 0.05))
        
        code_v = 0.0
        if 'def ' in texte or 'class ' in texte or 'import ' in texte:
            code_v = min(1.0, sum(0.15 for p in ['def ','class ','import '] if p in texte))
        if '(' in texte and ')' in texte: code_v += 0.05
        
        emo = sum(1 for m in mots if m in self._LEXIQUE_EMO)
        emotion_v = min(1.0, (emo / n) * 3.0 + min(0.3, texte.count('!') * 0.05))
        
        temp_mots = {'hier','aujourd','demain','maintenant','toujours','jamais','parfois','souvent'}
        temp = sum(1 for m in mots if m in temp_mots)
        std = float(np.std([len(m) for m in mots])) if len(mots) > 1 else 0.0
        temporel_v = min(1.0, (temp / n) * PHI_VALUE + min(1.0, std / 2.5) * 0.5)
        
        sig = np.array([phi_v, alpha_v, reasoning_v, creativity_v, math_v, factuel_v,
                        code_v, emotion_v, temporel_v], dtype=np.float32)
        return np.clip(sig, 0.0, 1.0)
    
    def fusionner_16d(self, s9: np.ndarray) -> np.ndarray:
        s = np.zeros(SIG_DIM_16D, dtype=np.float32)
        s[:9] = s9
        s[9] = min(1.0, s9[0] * s9[2])
        s[10] = min(1.0, s9[3] * (1.0 - s9[5]))
        s[11] = min(1.0, s9[4] * s9[6])
        s[12] = min(1.0, (s9[0] + s9[3] + s9[7]) / 3.0)
        s[13] = abs(s9[0] - s9[3])
        s[14] = min(1.0, (s9[1] + s9[2]) / 2.0)
        s[15] = min(1.0, s9[7] * s9[8])
        return np.clip(s, 0.0, 1.0)


# =====================================================================
# MÉMOIRE ASSOCIATIVE (résonance cosinus)
# =====================================================================

@dataclass
class Connaissance:
    id: str
    signature_16d: np.ndarray
    signature_9d: np.ndarray
    texte: str
    source: str = ""
    hash_certificat: str = ""

class MemoireAssociative:
    """Mémoire épisodique : stocke et récupère par résonance."""
    def __init__(self):
        self.connaissances: List[Connaissance] = []
        self._signature_matrix: Optional[np.ndarray] = None
        self._index_built = False
    
    def apprendre(self, analyseur: AnalyseurConscient, texte: str, source: str = "mem"):
        sig_9d = analyseur.projeter(texte)
        sig_16d = analyseur.fusionner_16d(sig_9d)
        c = Connaissance(
            id=hashlib.md5(f"{texte}{time.time()}".encode()).hexdigest()[:16],
            signature_16d=sig_16d, signature_9d=sig_9d,
            texte=texte, source=source,
            hash_certificat=hashlib.sha256(f"{texte}{len(self.connaissances)}".encode()).hexdigest()[:16]
        )
        self.connaissances.append(c)
        self._index_built = False
        return c
    
    def apprendre_batch(self, analyseur: AnalyseurConscient, textes: List[str], source: str = "batch"):
        for t in textes:
            self.apprendre(analyseur, t, source)
        self._rebuild_index()
    
    def _rebuild_index(self):
        if not self.connaissances:
            self._signature_matrix = np.zeros((0, SIG_DIM_16D), dtype=np.float32)
            self._index_built = True
            return
        sigs = np.stack([c.signature_16d for c in self.connaissances], axis=0)
        norms = np.linalg.norm(sigs, axis=1, keepdims=True)
        self._signature_matrix = sigs / (norms + 1e-8)
        self._index_built = True
    
    def chercher(self, query_sig_16d: np.ndarray, top_k: int = 5, seuil: float = 0.4):
        self._rebuild_index() if not self._index_built else None
        if self._signature_matrix.shape[0] == 0:
            return []
        qn = query_sig_16d / (np.linalg.norm(query_sig_16d) + 1e-8)
        sims = self._signature_matrix @ qn
        idx = np.argsort(sims)[::-1][:top_k]
        return [(self.connaissances[i], float(sims[i])) for i in idx if sims[i] >= seuil]
    
    def sauvegarder(self, chemin: str):
        data = {
            "meta": {"n": len(self.connaissances), "version": "def-v1",
                     "date": datetime.now().isoformat()},
            "connaissances": [
                {"id": c.id, "sig9": c.signature_9d.tolist(),
                 "sig16": c.signature_16d.tolist(),
                 "texte": c.texte, "source": c.source, "hash": c.hash_certificat}
                for c in self.connaissances
            ]
        }
        with open(chemin, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  [MEMOIRE] {len(self.connaissances)} connaiss. -> {chemin}")
    
    def charger(self, chemin: str) -> int:
        with open(chemin, 'r', encoding='utf-8') as f:
            data = json.load(f)
        n_avant = len(self.connaissances)
        for item in data["connaissances"]:
            c = Connaissance(
                id=item["id"],
                signature_9d=np.array(item.get("sig9", [0]*9), dtype=np.float32),
                signature_16d=np.array(item.get("sig16", [0]*16), dtype=np.float32),
                texte=item["texte"], source=item.get("source",""),
                hash_certificat=item.get("hash","")
            )
            self.connaissances.append(c)
        self._index_built = False
        n = len(self.connaissances) - n_avant
        print(f"  [MEMOIRE] {n} connaiss. chargees de {chemin}")
        return n
    
    def __len__(self):
        return len(self.connaissances)


# =====================================================================
# PARTIE INCONSCIENT : Transformer Harmonique PUR + Adaptation
# =====================================================================

class CoucheAdaptation(nn.Module):
    """
    Petite couche apprise (1% des paramètres).
    ===========================================
    C'est la seule partie entraînable du modèle.
    Elle adapte les hidden states fixes aux données réelles.
    
    Architecture :
    - Down-projection: hidden_size → hidden_size / 8  (réduction)
    - Activation GELU
    - Up-projection: hidden_size / 8 → hidden_size
    - Skip connection résiduelle
    
    Paramètres : ~hidden_size² / 4 (ex: 512²/4 = 65k pour 8 couches)
    """
    def __init__(self, hidden_size: int):
        super().__init__()
        self.down = nn.Linear(hidden_size, hidden_size // 8, bias=False)
        self.up = nn.Linear(hidden_size // 8, hidden_size, bias=False)
        self.scale = nn.Parameter(torch.tensor(0.01))  # petit départ
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Adaptation résiduelle avec gate
        h = self.down(x)
        h = F.gelu(h)
        h = self.up(h)
        return x + h * self.scale


class InconscientHarmonique(nn.Module):
    """
    INCONSCIENT HARMONIQUE PUR + Adaptateur.
    =========================================
    - Purement deterministe (0 paramètre entrainable) pour l'essentiel
    - Petite couche d'adaptation apprise (1% des paramètres)
    - Accepte conditionnement conscient via signatures 9D → 7D
    
    Architecture :
    - HarmonicFixedEmbedding (non entraînable)
    - N × PureHarmonicDecoderLayer (non entraînable)
    - N × CoucheAdaptation (entraînable, 1%)
    - HarmonicFixedLMHead (non entraînable)
    """
    
    def __init__(self, vocab_size: int = 50000, hidden_size: int = 512,
                 num_layers: int = 6, max_len: int = 2048):
        super().__init__()
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        if HARMONIC_PURE_AVAILABLE:
            print(f"[INCONSCIENT] Chargement du modele harmonique PUR...")
            # Créer le modèle pur (0 paramètre entraînable)
            self.pure_model = HarmonicPureForCausalLM(
                vocab_size=vocab_size,
                hidden_size=hidden_size,
                num_layers=num_layers,
                max_len=max_len
            )
            # Remplacer les couches de décodage par des versions avec adaptation
            self.adaptation_layers = nn.ModuleList([
                CoucheAdaptation(hidden_size)
                for _ in range(num_layers)
            ])
            total_params = sum(p.numel() for p in self.adaptation_layers.parameters())
            print(f"  [ADAPTATION] {total_params:,} parametres entrainables")
        else:
            print(f"[INCONSCIENT] Mode simulation (sans Torch)")
            self.pure_model = None
            self.adaptation_layers = None
        
        # Analyseur de signaturisation intégré au transformer
        self.signature_proj = PureSignatureProjection() if HARMONIC_PURE_AVAILABLE else None
    
    def forward(self, input_ids: torch.Tensor,
                conscious_sig_9d: Optional[torch.Tensor] = None,
                attention_mask: Optional[torch.Tensor] = None):
        """
        Forward avec conditionnement conscient.
        
        Args:
            input_ids: [batch, seq_len]
            conscious_sig_9d: [batch, 9] signature consciente optionnelle
            attention_mask: [batch, seq_len]
        
        Returns:
            logits: [batch, seq_len, vocab_size]
            signatures: [num_layers, batch, seq_len, 7]
            sign_conscience: [batch, 7] signature consciente projetée en 7D
        """
        if self.pure_model is None:
            # Mode simulation
            batch, seq_len = input_ids.shape
            fake_logits = torch.randn(batch, seq_len, self.vocab_size)
            fake_sigs = torch.randn(self.num_layers, batch, seq_len, 7)
            return fake_logits, fake_sigs, torch.zeros(batch, 7)
        
        # Projeter la signature consciente 9D → 7D
        sign_conscience_7d = None
        if conscious_sig_9d is not None:
            # Prendre les 7 premières dims de la signature 9D
            # avec mapping: phi, alpha, reasoning, creativity, math, factual, code
            sign_conscience_7d = conscious_sig_9d[:, :7]  # [batch, 7]
        
        # Forward du modèle pur
        logits, signatures = self.pure_model.forward(input_ids, attention_mask)
        
        # Appliquer l'adaptation sur les hidden states de chaque couche
        # (Nous intercepterons dans la boucle de génération car nous n'avons pas
        #  accès direct aux hidden states intermédiaires depuis l'extérieur)
        # Pour l'instant, forward standard
        
        # Conditionnement conscient : moduler les logits finaux
        if sign_conscience_7d is not None and logits is not None:
            batch = logits.shape[0]
            # Modulation phi-résonante sur les logits
            phi_dim = sign_conscience_7d[:, 0].mean().item()
            # Bonus de résonance pour les tokens alignés avec PHI
            if phi_dim > 0.5:
                resonance_bonus = 0.05 * phi_dim
                harm_ids = torch.arange(min(100, self.vocab_size),
                                        device=logits.device)
                harm_phase = (harm_ids.float() * PHI_VALUE) % 1.0
                mask = harm_phase < 0.1  # tokens en phase avec PHI
                logits[:, -1, mask[:self.vocab_size]] += resonance_bonus
        
        return logits, signatures, sign_conscience_7d
    
    def generate(self, input_ids: torch.Tensor,
                 conscious_sig_9d: Optional[torch.Tensor] = None,
                 max_new_tokens: int = 50, temperature: float = 0.85,
                 top_k: int = 40, top_p: float = 0.92,
                 repetition_penalty: float = 1.1,
                 conscious_update_every: int = 3,
                 analyseur: Optional[AnalyseurConscient] = None):
        """
        Génération auto-régressive avec boucle consciente.
        
        Args:
            input_ids: [batch, seq_len] prompt
            conscious_sig_9d: [batch, 9] signature consciente initiale
            max_new_tokens: nombre de tokens à générer
            temperature: température du sampling
            top_k: top-k filtering
            top_p: top-p nucleus sampling
            repetition_penalty: pénalité de répétition
            conscious_update_every: mettre à jour la signature tous les N tokens
            analyseur: analyseur conscient pour mise à jour dynamique
        
        Returns:
            generated: [batch, seq_len + generated]
            tokens_info: liste des tokens générés
        """
        self.eval()
        generated = input_ids.clone()
        sig_9d_courante = conscious_sig_9d.clone() if conscious_sig_9d is not None else None
        tokenizer = TokenizerFrancais()
        tokens_info = []
        
        with torch.no_grad():
            for step in range(max_new_tokens):
                # Tronquer si trop long
                if generated.shape[1] > 2048:
                    generated = generated[:, -2048:]
                
                # Forward avec conditionnement conscient
                logits, signatures, sig_conscience = self.forward(
                    generated,
                    conscious_sig_9d=sig_9d_courante
                )
                
                next_logits = logits[:, -1, :].clone()
                
                # === Sampling avec pénalités ===
                V = next_logits.shape[-1]
                
                # Masquage tokens spéciaux
                for t in (0, 2):
                    if t < V:
                        next_logits[0, t] = -1e12
                if 3 < V and step < 5:
                    next_logits[0, 3] = -1e9  # <EOS> pas trop tôt
                
                # Pénalité répétition
                if repetition_penalty > 1.0 and step > 0:
                    seen_ids = set(generated[0, -20:].tolist())
                    for tid in seen_ids:
                        if tid < V and tid not in (0, 1, 2, 3):
                            if next_logits[0, tid] < 0:
                                next_logits[0, tid] *= repetition_penalty
                            else:
                                next_logits[0, tid] /= repetition_penalty
                
                # Temperature
                if temperature > 0:
                    next_logits = next_logits / temperature
                else:
                    next_token = next_logits.argmax(dim=-1, keepdim=True)
                    generated = torch.cat([generated, next_token], dim=-1)
                    tokens_info.append({'step': step, 'token_id': next_token.item(), 'mode': 'argmax'})
                    continue
                
                # Top-k
                if top_k > 0:
                    vals, idxs = torch.topk(next_logits, min(top_k, V), dim=-1)
                    next_logits = torch.full_like(next_logits, float('-inf'))
                    next_logits.scatter_(1, idxs, vals)
                
                # Top-p
                if top_p < 1.0:
                    sorted_l, sorted_i = torch.sort(next_logits, descending=True, dim=-1)
                    cum_probs = torch.cumsum(F.softmax(sorted_l, dim=-1), dim=-1)
                    remove_mask = cum_probs > top_p
                    remove_mask[:, 1:] = remove_mask[:, :-1].clone()
                    remove_mask[:, 0] = False
                    for b in range(next_logits.shape[0]):
                        to_remove = sorted_i[b][remove_mask[b]]
                        next_logits[b, to_remove] = float('-inf')
                
                # Résonance phi (guidance consciente)
                if sig_9d_courante is not None:
                    phi_v = sig_9d_courante[0, 0].item()
                    if phi_v > 0.5:
                        resonance = 0.05 * phi_v
                        for h_id in range(min(20, V)):
                            phase = (h_id * PHI_VALUE) % 1.0
                            if phase < 0.15:
                                next_logits[0, h_id] += resonance
                
                # Sampling
                probs = F.softmax(next_logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)
                generated = torch.cat([generated, next_token], dim=-1)
                
                token_id = next_token[0, 0].item()
                token_score = float(probs[0, token_id].item())
                tokens_info.append({
                    'step': step, 'token_id': token_id,
                    'score': token_score, 'temperature': temperature
                })
                
                # Mise à jour de la signature consciente tous les N tokens
                if analyseur and conscious_update_every > 0 and step % conscious_update_every == 0:
                    texte_courant = tokenizer.decoder(generated[0].tolist())
                    sig_9d_nouvelle = analyseur.projeter(texte_courant)
                    sig_9d_courante = torch.from_numpy(sig_9d_nouvelle).unsqueeze(0).float()
                
                # Arrêt si <EOS> après un minimum de tokens
                if token_id == 3 and step >= 5:
                    break
        
        return generated, tokens_info
    
    def count_parameters(self) -> Dict[str, int]:
        """Compte les paramètres fixes et entraînables."""
        if self.pure_model is None:
            return {"total": 0, "trainable": 0, "fixed": 0}
        
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.adaptation_layers.parameters() if p.requires_grad)
        fixed = total - trainable
        return {
            "total": total, "trainable": trainable, "fixed": fixed,
            "trainable_pct": round(100 * trainable / total, 3) if total > 0 else 0
        }


# =====================================================================
# ORCHESTRATEUR CONSCIENT + INCONSCIENT
# =====================================================================

class MoteurConscientUnconscious:
    """
    Moteur complet : Conscience + Inconscient + Mémoire + Générateur.
    
    Architecture :
    1. Prompt → AnalyseurConscient → signature 9D
    2. Signature → MémoireAssociative → résonance
    3. Prompt tokenisé + signature → InconscientHarmonique → tokens
    4. Boucle : conscient met à jour la signature tous les N tokens
    """
    
    def __init__(self, vocab_size: int = 50000, hidden_size: int = 512,
                 num_layers: int = 6, chemin_memoire: str = "memoire_definitive.json"):
        self.analyseur = AnalyseurConscient()
        self.memoire = MemoireAssociative()
        self.tokenizer = TokenizerFrancais()
        self.chemin_memoire = chemin_memoire
        
        print(f"\n[INIT] Création de l'inconscient harmonique...")
        self.inconscient = InconscientHarmonique(
            vocab_size=vocab_size,
            hidden_size=hidden_size,
            num_layers=num_layers
        )
        
        # Statistiques
        self._stats = {
            "n_apprentissages": 0, "n_generations": 0,
            "temps_gen_ms": 0.0, "n_tokens_total": 0
        }
        
        # Chargement mémoire
        if os.path.exists(chemin_memoire):
            try:
                self.memoire.charger(chemin_memoire)
            except Exception as e:
                print(f"  [WARN] Chargement mémoire: {e}")
        
        # Afficher les paramètres
        params = self.inconscient.count_parameters()
        if params["total"] > 0:
            print(f"\n[PARAMS] Total: {params['total']:,} | "
                  f"Entrainables: {params['trainable']:,} ({params['trainable_pct']}%) | "
                  f"Fixes: {params['fixed']:,}")
    
    def apprendre(self, texte: str, source: str = "user"):
        """Apprend un texte."""
        self.memoire.apprendre(self.analyseur, texte, source)
        self._stats["n_apprentissages"] += 1
        if len(self.memoire) % 10 == 0:
            self.sauvegarder()
    
    def apprendre_batch(self, textes: List[str], source: str = "batch"):
        """Apprend un lot de textes."""
        self.memoire.apprendre_batch(self.analyseur, textes, source)
        self._stats["n_apprentissages"] += len(textes)
        self.sauvegarder()
        print(f"  [APPRENTISSAGE] {len(textes)} textes -> mémoire ({len(self.memoire)} total)")
    
    def generer(self, prompt: str, max_tokens: int = 50,
                temperature: float = 0.85, top_k: int = 40,
                top_p: float = 0.92, rep: float = 1.1,
                conscious_update_every: int = 3) -> Dict:
        """Génère une réponse à partir d'un prompt."""
        t0 = time.time()
        
        # 1. Analyse consciente du prompt
        sig_9d = self.analyseur.projeter(prompt)
        sig_16d = self.analyseur.fusionner_16d(sig_9d)
        
        # 2. Mémoire associative
        conns = self.memoire.chercher(sig_16d, top_k=3, seuil=0.4)
        mem_info = ""
        if conns:
            mem_info = conns[0][0].texte[:60]
        
        # 3. Tokenisation du prompt
        prompt_ids = self.tokenizer.encoder(prompt)
        if not prompt_ids:
            prompt_ids = [self.tokenizer.w2i.get('bonjour', 2)]
        
        input_tensor = torch.tensor([prompt_ids], dtype=torch.long)
        sig_tensor = torch.from_numpy(sig_9d).unsqueeze(0).float()
        
        # 4. Génération inconsciente
        generated, tokens_info = self.inconscient.generate(
            input_tensor,
            conscious_sig_9d=sig_tensor,
            max_new_tokens=max_tokens,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            repetition_penalty=rep,
            conscious_update_every=conscious_update_every if conscious_update_every > 0 else 9999,
            analyseur=self.analyseur if conscious_update_every > 0 else None
        )
        
        # 5. Décodage
        all_ids = generated[0].tolist()
        new_ids = all_ids[len(prompt_ids):]
        texte_genere = self.tokenizer.decoder(new_ids)
        
        dt = (time.time() - t0) * 1000
        self._stats["n_generations"] += 1
        self._stats["n_tokens_total"] += len(new_ids)
        n = self._stats["n_generations"]
        self._stats["temps_gen_ms"] = (self._stats["temps_gen_ms"] * (n - 1) + dt) / n
        
        # Certificat
        cert_hash = hashlib.sha256(
            f"{prompt}|{texte_genere}|{len(conns)}|{PHI_VALUE}".encode()
        ).hexdigest()[:16]
        
        # Profil conscient du texte généré
        profil_gen = self.analyseur.projeter(texte_genere)
        profil_dict = {d: float(profil_gen[i]) for i, d in enumerate(DIMS_9D)}
        
        return {
            "prompt": prompt,
            "texte_genere": texte_genere,
            "n_prompt_tokens": len(prompt_ids),
            "n_gen_tokens": len(new_ids),
            "n_connaissances": len(conns),
            "similarite_max": round(conns[0][1], 4) if conns else 0.0,
            "profil_conscient": profil_dict,
            "temps_ms": round(dt, 1),
            "tok_s": round(len(new_ids) / (dt/1000), 1) if dt > 0 else 0,
            "conscious_update_every": conscious_update_every,
            "hash_certificat": cert_hash,
            "n_tokens_uniques": len(set(new_ids)),
            "diversite": round(len(set(new_ids)) / max(len(new_ids), 1), 3) if new_ids else 0,
        }
    
    def analyser_texte(self, texte: str) -> Dict:
        """Analyse un texte avec la conscience."""
        sig_9d = self.analyseur.projeter(texte)
        sig_16d = self.analyseur.fusionner_16d(sig_9d)
        profil = {d: float(sig_9d[i]) for i, d in enumerate(DIMS_9D)}
        dominant = max(profil, key=profil.get)
        return {
            "texte": texte[:60], "longueur": len(texte),
            "profil_9d": profil, "dimension_dominante": dominant,
            "valeur_dominante": round(profil[dominant], 3),
            "coherence": round(float(np.mean(sig_9d)), 3),
            "couverture_vocab": round(self.tokenizer.couverture(texte) * 100, 1),
        }
    
    def stats(self) -> Dict:
        params = self.inconscient.count_parameters()
        return {
            **self._stats,
            "n_connaissances": len(self.memoire),
            "vocab_size": self.tokenizer.vocab_size,
            "hidden_size": self.inconscient.hidden_size,
            "num_layers": self.inconscient.num_layers,
            "params_fixes": params["fixed"],
            "params_entrainables": params["trainable"],
            "params_total": params["total"],
        }
    
    def sauvegarder(self):
        self.memoire.sauvegarder(self.chemin_memoire)
    
    def entrainer_adaptation(self, textes: List[str], epochs: int = 5,
                              lr: float = 1e-3, batch_size: int = 4):
        """
        Entraîne la couche d'adaptation sur des textes réels.
        Seulement 1% des paramètres est entraîné.
        """
        if not TORCH_AVAILABLE:
            print("[ERREUR] PyTorch requis pour l'entraînement")
            return
        
        optimizer = torch.optim.AdamW(
            self.inconscient.adaptation_layers.parameters(),
            lr=lr, weight_decay=0.01
        )
        
        # Préparer les données
        sequences = []
        for t in textes:
            ids = self.tokenizer.encoder(t)
            if len(ids) >= 5:
                sequences.append(ids)
        
        print(f"\n[ENTRAINEMENT] {len(sequences)} sequences, {epochs} epochs")
        
        self.inconscient.train()
        for epoch in range(epochs):
            total_loss = 0.0
            n_batches = 0
            
            # Mélanger
            np.random.shuffle(sequences)
            
            for i in range(0, len(sequences), batch_size):
                batch_seqs = sequences[i:i+batch_size]
                max_len = max(len(s) for s in batch_seqs)
                
                # Padding
                batch_ids = []
                for s in batch_seqs:
                    padded = s + [0] * (max_len - len(s))
                    batch_ids.append(padded)
                
                input_ids = torch.tensor(batch_ids, dtype=torch.long)
                labels = input_ids.clone()
                
                # Forward
                logits, _, _ = self.inconscient.forward(input_ids)
                
                # Loss (cross-entropy)
                shift_logits = logits[:, :-1, :].contiguous()
                shift_labels = labels[:, 1:].contiguous()
                loss = F.cross_entropy(
                    shift_logits.view(-1, shift_logits.shape[-1]),
                    shift_labels.view(-1),
                    ignore_index=0
                )
                
                # Backward
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(
                    self.inconscient.adaptation_layers.parameters(), 1.0
                )
                optimizer.step()
                
                total_loss += loss.item()
                n_batches += 1
            
            avg_loss = total_loss / max(n_batches, 1)
            print(f"  Epoch {epoch+1}/{epochs} : loss = {avg_loss:.4f}")
        
        self.inconscient.eval()
        print(f"[ENTRAINEMENT] Terminé !")


# =====================================================================
# MAIN - TEST DIALOGUE
# =====================================================================

def main():
    print("\n" + "=" * 70)
    print("INCONSCIENT HARMONIQUE DÉFINITIF")
    print("Architecture : Conscient (9D) + Inconscient (Transformer PUR)")
    print("=" * 70)
    
    # Créer le moteur
    moteur = MoteurConscientUnconscious(
        vocab_size=VOCAB_SIZE,
        hidden_size=128,
        num_layers=4
    )
    
    stats = moteur.stats()
    print(f"\n[ÉTAT] {stats['n_connaissances']} conn., voc={stats['vocab_size']}, "
          f"layers={stats['num_layers']}, hidden={stats['hidden_size']}")
    print(f"       params={stats['params_total']:,} (fixes={stats['params_fixes']:,}, "
          f"entrainables={stats['params_entrainables']:,})")
    
    # Ajouter des connaissances si vide
    if stats['n_connaissances'] < 5:
        print("\n[APPRENTISSAGE] Connaissances de base...")
        textes_base = [
            "phi est le nombre d or la proportion divine de l univers",
            "la resonance harmonique amplifie les ondes a la frequence propre",
            "la conscience est la capacite de percevoir sa propre existence",
            "les fractales sont des structures infinies auto similaires",
            "la suite de Fibonacci converge vers le nombre d or phi",
            "l amour est la force la plus puissante de l univers",
            "la beaute de la nature est une source d emerveillement infini",
            "l intelligence artificielle explore la creation de machines penseantes",
            "le temps est une dimension fondamentale de notre univers",
            "la musique est l harmonie entre le silence et le son",
            "la philosophie est l amour de la sagesse et de la connaissance",
            "python est un langage de programmation clair et puissant",
            "la creativite est l intelligence qui s amuse",
            "la patience est la cle de la reussite",
            "le bonheur n est pas une destination mais une facon de voyager",
            "la connaissance de soi est le debut de toute sagesse",
            "la compassion et la bienveillance unissent les etres humains",
            "l empathie permet de comprendre les emotions des autres",
            "tout systeme physique a une frequence de resonance fondamentale",
            "la verite est souvent plus etrange que la fiction",
        ]
        moteur.apprendre_batch(textes_base)
    
    # Test de base
    print(f"\n{'='*70}")
    print("DIALOGUE AVEC L'INCONSCIENT HARMONIQUE DÉFINITIF")
    print(f"{'='*70}")
    
    prompts = [
        "parle moi du nombre d or",
        "comment fonctionne la resonance",
        "qu est ce que la conscience",
        "parle moi de python",
        "c est quoi l amour",
        "que sont les fractales",
    ]
    
    for prompt in prompts:
        print(f"\n>> {prompt}")
        r = moteur.generer(prompt, max_tokens=30, temperature=0.85,
                          top_k=30, top_p=0.9, conscious_update_every=3)
        profil = r["profil_conscient"]
        dom = max(profil, key=profil.get)
        print(f"   [conscient:{dom}={profil[dom]:.2f}] {r['texte_genere']}")
        print(f"   -> {r['n_gen_tokens']}t, div={r['diversite']}, "
              f"{r['temps_ms']:.0f}ms, mem={r['n_connaissances']}")
    
    print(f"\n{'='*70}")
    print("BILAN FINAL")
    print(f"{'='*70}")
    stats = moteur.stats()
    print(f"""
   CONSCIENCE  : Analyseur 9D heuristique (phi/alpha/reasoning/creativity/...)
   MÉMOIRE     : {stats['n_connaissances']} connaiss. par resonance cosinus
   INCONSCIENT : Transformer Harmonique PUR ({stats['num_layers']} layers, {stats['hidden_size']} dim)
   PARAMÈTRES  : {stats['params_total']:,} dont {stats['params_entrainables']:,} entrainables
   VOCABULAIRE : {stats['vocab_size']} tokens français
   GÉNÉRATION  : ~{stats['temps_gen_ms']:.0f}ms en moyenne

   Pour entraîner l'adaptation :
     moteur.entrainer_adaptation(textes, epochs=5)

   Pour lancer l API REST :
     python conscious_unconscious_harmonique.py --api
""")


# =====================================================================
# API REST
# =====================================================================

def lancer_api(host="0.0.0.0", port=8765):
    """Serveur API REST complet."""
    import urllib.parse
    
    moteur = MoteurConscientUnconscious(
        vocab_size=VOCAB_SIZE,
        hidden_size=128,
        num_layers=4
    )
    
    def api_json(data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        return (status, {'Content-Type': 'application/json; charset=utf-8'}, body)
    
    # Tentative FastAPI
    try:
        import uvicorn
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel
        
        app = FastAPI(title="Inconscient Harmonique API", version="def-v1")
        
        class GenererRequest(BaseModel):
            prompt: str
            max_tokens: int = 50
            temperature: float = 0.85
            top_k: int = 30
            top_p: float = 0.9
            rep: float = 1.1
            conscious_update_every: int = 3
        
        class ApprendreRequest(BaseModel):
            textes: List[str]
            source: str = "api"
        
        @app.get("/")
        def root():
            return {
                "name": "Inconscient Harmonique",
                "version": "def-v1",
                "endpoints": {
                    "GET /stats": "Statistiques",
                    "GET /analyser?texte=...": "Analyse consciente",
                    "POST /generer": "Génération",
                    "POST /apprendre": "Apprentissage",
                }
            }
        
        @app.get("/stats")
        def get_stats():
            return moteur.stats()
        
        @app.get("/analyser")
        def analyser(texte: str = ""):
            if not texte:
                raise HTTPException(400, "paramètre 'texte' requis")
            return moteur.analyser_texte(texte)
        
        @app.post("/generer")
        def generer(req: GenererRequest):
            return moteur.generer(req.prompt, req.max_tokens, req.temperature,
                                 req.top_k, req.top_p, req.rep,
                                 req.conscious_update_every)
        
        @app.post("/apprendre")
        def apprendre(req: ApprendreRequest):
            n = len(req.textes)
            moteur.apprendre_batch(req.textes, req.source)
            return {"appris": n, "total": len(moteur.memoire)}
        
        print(f"\n[API] http://{host}:{port}")
        uvicorn.run(app, host=host, port=port)
    
    except ImportError:
        # Fallback http.server
        import http.server
        
        class APIHandler(http.server.BaseHTTPRequestHandler):
            def _respond(self, status, headers, body):
                self.send_response(status)
                for k, v in headers.items():
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(body)
            
            def do_GET(self):
                parsed = urllib.parse.urlparse(self.path)
                if parsed.path == '/stats':
                    self._respond(*api_json(moteur.stats()))
                elif parsed.path == '/analyser':
                    qs = urllib.parse.parse_qs(parsed.query)
                    texte = qs.get('texte', [''])[0]
                    if texte:
                        self._respond(*api_json(moteur.analyser_texte(texte)))
                    else:
                        self._respond(*api_json({"err": "texte requis"}, 400))
                else:
                    self._respond(*api_json({
                        "endpoints": {
                            "GET /stats": "stats",
                            "GET /analyser?texte=...": "analyse",
                            "POST /generer": "generation",
                            "POST /apprendre": "apprentissage",
                        }
                    }))
            
            def do_POST(self):
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length) if length > 0 else b'{}'
                try:
                    data = json.loads(body)
                except:
                    self._respond(*api_json({"err": "JSON invalide"}, 400))
                    return
                
                if self.path == '/generer':
                    prompt = data.get('prompt', '')
                    if not prompt:
                        self._respond(*api_json({"err": "prompt requis"}, 400))
                        return
                    r = moteur.generer(
                        prompt, data.get('max_tokens', 50),
                        data.get('temperature', 0.85),
                        data.get('top_k', 30), data.get('top_p', 0.9),
                        data.get('rep', 1.1),
                        data.get('conscious_update_every', 3)
                    )
                    self._respond(*api_json(r))
                
                elif self.path == '/apprendre':
                    textes = data.get('textes', [])
                    n = len(textes)
                    if n > 0:
                        moteur.apprendre_batch(textes, data.get('source', 'api'))
                    self._respond(*api_json({"appris": n, "total": len(moteur.memoire)}))
                
                else:
                    self._respond(*api_json({"err": "inconnu"}, 404))
        
        server = http.server.HTTPServer((host, port), APIHandler)
        print(f"\n[API] http://{host}:{port}")
        print(f"      Endpoints: GET /stats, GET /analyser, POST /generer, POST /apprendre")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n[API] Arrêt")


if __name__ == "__main__":
    if "--api" in sys.argv:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--api", action="store_true")
        parser.add_argument("--host", default="0.0.0.0")
        parser.add_argument("--port", type=int, default=8765)
        args = parser.parse_args()
        lancer_api(args.host, args.port)
    else:
        main()
