#!/usr/bin/env python
"""
FUSION HARMONIQUE COMPLÈTE
===========================
Combine les 3 correctifs :
1. Ordonnancement harmonique du vocabulaire (embedding ↔ sémantique)
2. Apprentissage par résonance (remplace backprop)
3. Guidance mémoire pour la génération (remplace sampling aléatoire)

Le tout SANS GPU, 100% CPU.

Usage :
    python fusion_harmonique.py                  # Test avec phrases par défaut
    python fusion_harmonique.py --train data.txt  # Entraînement depuis fichier
    python fusion_harmonique.py --api             # API REST
"""
import numpy as np
import json, os, sys, time, math, hashlib
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

PHI = (1 + 5 ** 0.5) / 2
ALPHA = 1.0 / PHI

# =====================================================================
# 1. VOCABULAIRE ORDONNÉ HARMONIQUEMENT
# =====================================================================

VOCAB_ORDONNE = [
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
    'couleur','forme','matiere','esprit',
    'grand','petit','beau','bon','mauvais','vrai','faux','nouveau','vieux','jeune',
    'long','court','haut','bas','fort','faible','rapide','lent','clair','fonce',
    'facile','difficile','grave','leger','plein','vide','riche','pauvre','simple','complexe',
    'important','necessaire','possible','impossible','premier','dernier','prochain','ancien',
    'tout','tous','toute','chaque','quelque','plusieurs','rien','personne','jamais',
    'toujours','souvent','parfois','beaucoup','peu','trop','assez','encore','enfin',
    'alors','apres','avant','depuis','pendant','vers','chez','sans','sous','contre',
    'selon','loin','pres','ici','la','ailleurs','maintenant','hier','demain',
    'bonjour','merci','pardon','oui','non','peut-etre','comment','pourquoi','combien',
    'quand','ou','harmonie','resonance','frequence','onde','phi','nombre','or',
    'conscience','pensee','intelligence','connaissance','sagesse','verite',
    'systeme','modele','theorie','principe','loi','information',
    'reseau','apprentissage','inference','signature','dimension','espace',
    'analyse','synthese','logique','raisonnement','intuition','imagination',
    'realite','cause','effet',
    'philosophie','psychologie','cerveau','neurone','perception','attention',
    'memoire','langage','reve','emotion','passion','desir','bonheur',
    'sentiment','confiance','empathie','compassion',
    'technologie','informatique','ordinateur','logiciel','donnee','python','code',
    'intelligence','artificielle','machine','programme','api',
    'algorithme','securite',
    'sante','medecine','maladie','traitement','soin','corps','esprit',
    'societe','politique','economie','culture','education','religion',
    'loi','droit','justice','liberte','citoyen','paix','guerre',
    'passe','present','futur','instant','moment','temps','eternite',
    'nature','cosmos','univers','planete','vie','mort',
    'beau','art','poesie','musique','couleur','forme','lumiere',
    'silence','echo','vibration','rythme','cristal','harmonie',
    'abstrait','concret','profond','eternel','absolu','relatif',
    'zephyr','nebuleuse','diaphane','fulgurant','resplendissant',
]

VOCAB_SIZE = len(VOCAB_ORDONNE)
W2I = {w: i for i, w in enumerate(VOCAB_ORDONNE)}
I2W = {i: w for i, w in enumerate(VOCAB_ORDONNE)}


class EmbeddingOrdonne:
    """
    Embedding harmonique avec vocabulaire ordonné.
    Maintenant : mots sémantiquement proches → IDs proches → embeddings proches.
    """
    def __init__(self, hidden_size: int = 256):
        self.vocab = VOCAB_ORDONNE
        self.n = VOCAB_SIZE
        self.d = hidden_size
        self.idx = W2I
        
        # Pré-calcul
        ids = np.arange(self.n, dtype=np.float32).reshape(-1, 1)
        dims = np.arange(self.d, dtype=np.float32).reshape(1, -1)
        
        # cos(ID × dim × φ / d) × exp(-dim × α / d)
        self.matrix = np.cos(ids * dims * PHI / self.d) * np.exp(-dims * ALPHA / self.d)
        norms = np.linalg.norm(self.matrix, axis=1, keepdims=True)
        self.matrix = self.matrix / (norms + 1e-8)
    
    def __call__(self, mot: str) -> np.ndarray:
        return self.matrix[self.idx.get(mot, 1)]
    
    def similarite(self, a: str, b: str) -> float:
        ea, eb = self(a), self(b)
        return float(ea @ eb / (np.linalg.norm(ea) * np.linalg.norm(eb) + 1e-8))


# =====================================================================
# 2. MATRICE DE RÉSONANCE (apprentissage hebbien)
# =====================================================================

class MatriceResonance:
    """Matrice N×N de co-occurrence apprise sans backprop."""
    def __init__(self):
        self.R = np.zeros((VOCAB_SIZE, VOCAB_SIZE), dtype=np.float32)
        self.freq = np.zeros(VOCAB_SIZE, dtype=np.float32)
        self.n_phrases = 0
    
    def apprendre(self, ids: List[int], fenetre: int = 5):
        n = len(ids)
        for i in range(n):
            ti = ids[i]
            if ti >= VOCAB_SIZE: continue
            self.freq[ti] += 1.0
            debut, fin = max(0, i-fenetre), min(n, i+fenetre+1)
            for j in range(debut, fin):
                if i == j: continue
                tj = ids[j]
                if tj >= VOCAB_SIZE: continue
                poids = 1.0 / (abs(i-j) ** ALPHA)
                self.R[ti, tj] += poids
                self.R[tj, ti] += poids
        self.n_phrases += 1
    
    def resonner(self, contexte: List[int]) -> np.ndarray:
        if not contexte: return np.zeros(VOCAB_SIZE)
        scores = np.zeros(VOCAB_SIZE)
        nv = 0
        for t in contexte:
            if t < VOCAB_SIZE: scores += self.R[t]; nv += 1
        if nv > 0: scores /= nv
        for t in set(contexte[-10:]):
            if t < VOCAB_SIZE: scores[t] *= 0.5
        # Masquer tokens spéciaux (<PAD>=0, <UNK>=1, <BOS>=2)
        scores[0] = -1e9
        scores[1] = -1e9
        scores[2] = -1e9
        return scores
    
    def top_k(self, contexte: List[int], k: int = 10) -> List[Tuple[int, float]]:
        scores = self.resonner(contexte)
        idx = np.argsort(scores)[::-1]
        return [(int(i), float(scores[i])) for i in idx[:k] if scores[i] > 0.01]


# =====================================================================
# 3. TOKENIZER
# =====================================================================

class Tokenizer:
    def encoder(self, texte: str) -> List[int]:
        tks = []
        for m in texte.lower().strip().split():
            c = m.strip('.,!?;:()[]{}"\'-_«»\'’\\/')
            tks.append(W2I.get(c, 1))
        return tks
    
    def decoder(self, ids: List[int]) -> str:
        return ' '.join(I2W.get(i, '<UNK>') for i in ids if i not in (0,))
    
    def texte_ids(self, texte: str) -> List[int]:
        return self.encoder(texte)


# =====================================================================
# 4. SYSTÈME COMPLET
# =====================================================================

class SystemeHarmonique:
    """
    Système harmonique complet avec :
    - Embedding sémantique par ordonnancement
    - Apprentissage par résonance (sans backprop)
    - Guidance mémoire pour la génération
    
    Utilisation :
        sys = SystemeHarmonique()
        sys.apprendre("le chat mange la souris")
        print(sys.generer("le chat"))
    """
    
    def __init__(self):
        self.emb = EmbeddingOrdonne()
        self.resonance = MatriceResonance()
        self.tokenizer = Tokenizer()
        
        # Mémoire épisodique : liste de (signature_9d, ids, texte)
        self.memoire: List[Tuple[np.ndarray, List[int], str]] = []
        self._index_memoire: Optional[np.ndarray] = None
    
    def apprendre(self, texte: str):
        """Apprend un texte par résonance."""
        ids = self.tokenizer.encoder(texte)
        if len(ids) < 2: return
        
        # Matrice de résonance
        self.resonance.apprendre(ids)
        
        # Mémoire épisodique
        sig = self._signature_9d(texte)
        self.memoire.append((sig, ids, texte))
        self._index_memoire = None
    
    def apprendre_batch(self, textes: List[str]):
        for t in textes: self.apprendre(t)
        self._build_index()
        print(f"[SYSTEME] {len(textes)} phrases apprises")
        print(f"  Connexions: {int(np.sum(self.resonance.R > 0))}")
        print(f"  Mémoire: {len(self.memoire)} traces")
    
    def _signature_9d(self, texte: str) -> np.ndarray:
        """Signature 9D rapide."""
        if not texte or len(texte.strip()) < 2: return np.zeros(9)
        mots = texte.lower().strip().split()
        n = max(len(mots), 1)
        s = np.zeros(9)
        s[0] = min(1.0, len(set(mots))/n * PHI)
        if len(mots) >= 2:
            L = np.array([len(m) for m in mots])
            s[1] = min(1.0, (L.mean()/5.0) * (1+L.std()*0.2))
        else: s[1] = 0.3
        subs = {'que','qui','dont','ou','car','comme','alors','donc'}
        sub_c = sum(1 for m in mots if m in subs)
        s[2] = min(1.0, (sub_c/n) * 2.5)
        rares = sum(1 for m in mots if len(m) > 9 and m.isalpha())
        s[3] = min(1.0, (rares/n) * PHI + 0.05)
        s[5] = s[2] * 0.6
        emos = {'amour','joie','triste','peur','colere','haine','espoir','paix'}
        s[7] = min(1.0, sum(1 for m in mots if m in emos)/n * 3.0)
        return np.clip(s, 0.0, 1.0)
    
    def _build_index(self):
        if not self.memoire: return
        sigs = np.stack([m[0] for m in self.memoire])
        norms = np.linalg.norm(sigs, axis=1, keepdims=True)
        self._index_memoire = sigs / (norms + 1e-8)
    
    def _resonner_memoire(self, sig: np.ndarray) -> np.ndarray:
        """Bonus de guidage par la mémoire épisodique."""
        scores = np.zeros(VOCAB_SIZE)
        if self._index_memoire is None or len(self.memoire) < 2: return scores
        q = sig / (np.linalg.norm(sig) + 1e-8)
        sims = self._index_memoire @ q
        top_idx = np.argsort(sims)[::-1][:3]
        for idx in top_idx:
            if sims[idx] < 0.2: continue
            _, ids, _ = self.memoire[idx]
            for t in ids:
                if t < VOCAB_SIZE: scores[t] += sims[idx] * 0.15
        return scores
    
    def generer(self, prompt: str, max_tokens: int = 15,
                temperature: float = 0.8, repetition: float = 0.4) -> str:
        """
        Génération complète guidée par :
        1. Résonance (co-occurrences apprises)
        2. Mémoire épisodique (phrases similaires)
        3. Embedding sémantique (mots proches)
        4. Pénalité de répétition
        """
        ids = self.tokenizer.encoder(prompt)
        if not ids: return ""
        
        generated = ids.copy()
        sig_prompt = self._signature_9d(prompt)
        
        for _ in range(max_tokens):
            # 1. Score de résonance (co-occurrences)
            scores = self.resonance.resonner(generated)
            
            # 2. Guidance mémoire
            scores += self._resonner_memoire(sig_prompt)
            
            # 3. Guidance embedding : les mots proches du dernier token
            if generated:
                dernier_mot = I2W.get(generated[-1], '')
                if dernier_mot in W2I:
                    emb_dernier = self.emb(dernier_mot)
                    # Bonus pour les tokens dont l'embedding est proche
                    sims = self.emb.matrix @ emb_dernier
                    scores += sims * 0.05
            
            # 4. Pénalité de répétition
            for t in set(generated[-8:]):
                if t < VOCAB_SIZE: scores[t] *= repetition
            
            # Masquer spéciaux
            for t in [0, 1, 2]: scores[t] = -1e9
            
            # Température + softmax
            if temperature > 0: scores = scores / temperature
            scores = scores.astype(np.float64)
            scores -= scores.max()
            exp_s = np.exp(scores)
            probs = exp_s / (exp_s.sum() + 1e-10)
            
            next_id = np.random.choice(VOCAB_SIZE, p=probs)
            if next_id == 3: break
            generated.append(next_id)
        
        return self.tokenizer.decoder(generated[len(ids):])
    
    def interagir(self):
        """Dialogue interactif."""
        print("\n" + "="*60)
        print("  SYSTÈME HARMONIQUE - Dialogue")
        print("  'quit' pour quitter")
        print("="*60)
        while True:
            prompt = input("\n  Vous: ").strip()
            if prompt.lower() in ('quit', 'exit', 'q'): break
            if prompt:
                reponse = self.generer(prompt, max_tokens=12)
                print(f"  IA: {reponse}")
    
    def sauvegarder(self, prefix: str = "harmonique_complet"):
        np.savez_compressed(f"{prefix}_resonance.npz",
            R=self.resonance.R, freq=self.resonance.freq)
        data = {
            "phrases": [m[2] for m in self.memoire],
            "signatures": [m[0].tolist() for m in self.memoire]
        }
        with open(f"{prefix}_memoire.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"[SAVE] Système sauvegardé dans {prefix}_*.npz/json")
    
    def charger(self, prefix: str = "harmonique_complet"):
        if os.path.exists(f"{prefix}_resonance.npz"):
            data = np.load(f"{prefix}_resonance.npz", allow_pickle=True)
            self.resonance.R = data['R']
            self.resonance.freq = data['freq']
        if os.path.exists(f"{prefix}_memoire.json"):
            with open(f"{prefix}_memoire.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
            for sig, phrase in zip(data["signatures"], data["phrases"]):
                sig_np = np.array(sig, dtype=np.float32)
                ids = self.tokenizer.encoder(phrase)
                self.memoire.append((sig_np, ids, phrase))
            self._index_memoire = None
            self._build_index()
        print(f"[LOAD] Système chargé: {len(self.memoire)} phrases")


# =====================================================================
# API REST LÉGÈRE
# =====================================================================

class APILegere:
    """Serveur API minimaliste."""
    def __init__(self, systeme: SystemeHarmonique, port: int = 8080):
        self.sys = systeme
        self.port = port
    
    def demarrer(self):
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import urllib.parse
        
        class Handler(BaseHTTPRequestHandler):
            sys = self.sys
            def do_GET(self):
                parsed = urllib.parse.urlparse(self.path)
                params = urllib.parse.parse_qs(parsed.query)
                
                if parsed.path == '/':
                    self._json({"status": "ok", "message": "IA Harmonique",
                               "phrases_apprises": len(self.sys.memoire)})
                elif parsed.path == '/generer':
                    prompt = params.get('prompt', [''])[0]
                    temp = float(params.get('temperature', ['0.8'])[0])
                    max_tk = int(params.get('max_tokens', ['15'])[0])
                    if not prompt:
                        self._json({"error": "paramètre 'prompt' requis"}, 400)
                    else:
                        reponse = self.sys.generer(prompt, max_tokens=max_tk, temperature=temp)
                        self._json({"prompt": prompt, "reponse": reponse})
                elif parsed.path == '/apprendre':
                    texte = params.get('texte', [''])[0]
                    if texte:
                        self.sys.apprendre(texte)
                        self._json({"appris": True, "texte": texte,
                                   "total": len(self.sys.memoire)})
                    else:
                        self._json({"error": "paramètre 'texte' requis"}, 400)
                elif parsed.path == '/stats':
                    self._json({
                        "phrases": len(self.sys.memoire),
                        "connexions": int(np.sum(self.sys.resonance.R > 0)),
                        "vocabulaire": VOCAB_SIZE,
                        "embedding_dim": self.sys.emb.d,
                    })
                else:
                    self._json({"error": "route inconnue"}, 404)
            
            def _json(self, data, code=200):
                self.send_response(code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
        
        server = HTTPServer(('0.0.0.0', self.port), Handler)
        print(f"[API] Serveur démarré sur http://0.0.0.0:{self.port}")
        print(f"[API]   GET /generer?prompt=...&temperature=0.8&max_tokens=15")
        print(f"[API]   GET /apprendre?texte=...")
        print(f"[API]   GET /stats")
        print(f"[API]   Ctrl+C pour arrêter")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n[API] Arrêt")
            server.server_close()


# =====================================================================
# MAIN
# =====================================================================

def main():
    print("=" * 70)
    print("  SYSTÈME HARMONIQUE COMPLET")
    print("  Embedding sémantique + Résonance + Guidance mémoire")
    print("  CPU only, 0 GPU, 0 backprop")
    print("=" * 70)
    
    sys = SystemeHarmonique()
    
    # Phrases d'entraînement
    phrases = [
        # Base
        "le chat mange la souris",
        "le chien mange la viande",
        "le chat dort sur le lit",
        "le chien court dans le jardin",
        "la souris est petite et rapide",
        "le soleil brille dans le ciel",
        "la lune eclaire la nuit noire",
        "les etoiles brillent dans le ciel",
        "le vent souffle sur la mer",
        "la pluie tombe sur la terre",
        "l eau coule dans la riviere",
        "le feu brule dans la cheminee",
        # Philosophie et science
        "la philosophie est l amour de la sagesse",
        "le nombre d or est la proportion divine",
        "la resonance harmonique amplifie les ondes",
        "la conscience est la capacite de percevoir",
        "l intelligence artificielle explore la creation",
        "la creativite est l intelligence qui s amuse",
        # Vie quotidienne
        "le temps passe vite quand on s amuse",
        "la vie est belle malgre les difficultes",
        "l espoir fait vivre les jours sombres",
        "la paix est le chemin vers la lumiere",
        "le silence parle plus que les mots",
        "la musique adoucit les coeurs blesses",
        "le travail est la cle de la reussite",
        "la famille est un tresor precieux",
        "l amitie est une fleur qui ne fane jamais",
        "la liberte est un droit fondamental",
        "la connaissance est la lumiere de l esprit",
        "le bonheur se trouve dans les petites choses",
        # Technique
        "python est un langage de programmation",
        "l algorithme est une suite d instructions",
        "la donnee est stockee dans la memoire",
        "le code est compile par le compilateur",
        "l api permet la communication entre services",
    ]
    
    print(f"\n[ENTRAINEMENT] {len(phrases)} phrases...")
    t0 = time.time()
    sys.apprendre_batch(phrases)
    t = time.time() - t0
    print(f"  Temps: {t:.3f}s")
    
    # Test
    print("\n[TEST] Prédiction par résonance :")
    tests = [
        ("le", 5), ("la", 5), ("dans", 5), ("est", 5),
        ("le soleil", 5), ("la philosophie", 5),
    ]
    for ctx, k in tests:
        ids = sys.tokenizer.encoder(ctx)
        top = sys.resonance.top_k(ids, k)
        mots = [I2W.get(i, '?') for i, _ in top]
        scores = [f"{s:.3f}" for _, s in top]
        print(f"  '{ctx}' -> {mots} ({scores})")
    
    # Test embedding sémantique
    print("\n[EMBEDDING] Similarités sémantiques :")
    paires = [('maison','appartement'), ('amour','passion'), ('guerre','paix'),
              ('soleil','lune'), ('philosophie','sagesse'),
              ('maison','guerre'), ('amour','haine'),
              ('python','code')]
    for a, b in paires:
        sim = sys.emb.similarite(a, b)
        print(f"  {a:15s} <-> {b:15s} : {sim:.4f}")
    
    # Test génération
    print("\n[GENERATION] Guidée par résonance + mémoire + embedding :")
    prompts = [
        "le chat", "la philosophie", "le nombre",
        "la vie", "l intelligence", "le silence",
    ]
    for prompt in prompts:
        gen = sys.generer(prompt, max_tokens=8, temperature=0.85)
        print(f"  '{prompt}' -> '{gen}'")
    
    # Stats
    print(f"\n[STATS]")
    print(f"  Phrases apprises: {len(sys.memoire)}")
    print(f"  Connexions résonance: {int(np.sum(sys.resonance.R > 0))}")
    print(f"  Vocabulaire: {VOCAB_SIZE} tokens")
    print(f"  Embedding dim: {sys.emb.d}")
    print(f"  Temps: {t:.3f}s")
    print(f"[OK] Système harmonique complet opérationnel")
    
    # Sauvegarde
    sys.sauvegarder()
    
    # API ou dialogue
    if '--api' in sys.argv:
        api = APILegere(sys, port=8080)
        api.demarrer()
    elif '--interactif' in sys.argv or '--i' in sys.argv:
        sys.interagir()
    
    return sys


if __name__ == '__main__':
    import sys as _sys
    # Entraînement depuis fichier
    if '--train' in _sys.argv:
        sys_sys = SystemeHarmonique()
        fichier = _sys.argv[_sys.argv.index('--train') + 1]
        with open(fichier, 'r', encoding='utf-8') as f:
            textes = [l.strip() for l in f if l.strip()]
        sys_sys.apprendre_batch(textes)
        sys_sys.sauvegarder()
        if '--api' in _sys.argv:
            APILegere(sys_sys, port=8080).demarrer()
    else:
        main()
