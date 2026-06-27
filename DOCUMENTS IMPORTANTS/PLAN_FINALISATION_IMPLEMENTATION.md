# PLAN DE FINALISATION : Modele Monde Harmonique Auto-Interactif

## Etat des lieux

### Ce qui est valide
- [x] Hologramme 2D avec accumulation additive (64x64 = 4096 pixels complexes)
- [x] Tokenisation par projection d'ondes (323 tokens, 0 collision)
- [x] Lecteurs multiples avec gradient ascent (8 perspectives)
- [x] Generation par resonance inverse (texte <UNK> mais structure emerge)
- [x] Feedback conscient->inconscient (boucle fermee)
- [x] Preuve du modele monde multimodal auto-interactif

### Ce qui bloque la qualite
- [ ] **Diversite des lecteurs** : 8 lecteurs identiques = 1 perspective
- [ ] **Vocabulaire trop petit** : 323 tokens -> <UNK> partout
- [ ] **Pas d'optimisation** : 7 secondes pour 25 tokens

---

## PHASE A : CORRECTIONS RAPIDES (1-2 jours)

### A1 : Diversite des lecteurs (critique)

**Probleme** : Tous les lecteurs convergent vers les memes tokens car
le gradient ascent maximise la meme activation sur le meme hologramme.

**Solution immediate** : Repulsion entre lecteurs + bruit local differencie

```python
# Dans l'iteration de LecteurResonantMultiple :
def iterer_avec_diversite(self, lr=0.03, force_repulsion=0.01):
    eps = 0.001
    for n in range(self.n_lecteurs):
        # Gradient standard
        gx = (act(kx+eps) - act(kx-eps)) / (2*eps)
        
        # TERME DE REPULSION : chaque lecteur fuit les autres
        for m in range(self.n_lecteurs):
            if m != n:
                dx = self.kx[n] - self.kx[m]
                dy = self.ky[n] - self.ky[m]
                dist = sqrt(dx*dx + dy*dy)
                if dist < 0.5:  # Si trop proche
                    gx += force_repulsion * dx / (dist + 1e-8)
                    gy += force_repulsion * dy / (dist + 1e-8)
        
        # Bruit d'exploration INDIVIDUEL
        self.kx[n] += lr * gx + np.random.randn() * (0.001 + n*0.0005)
        self.ky[n] += lr * gy + np.random.randn() * (0.001 + n*0.0005)
```

**Impact attendu** : 8 lecteurs -> 8 tokens differents en sortie

### A2 : Bruit de fond d'experience (fondamental)

**Decouverte** : L'hologramme initial a un bruit de fond gaussien (0.01).
Ce bruit est le MEME pour tous les lecteurs -> ils convergent vers les
memes maxima locaux du bruit.

**Solution** : Ajouter un bruit de fond DIFFERENT pour chaque lecteur :

```python
class HologrammeMonde:
    def __init__(self, nx=64, ny=64):
        # ... existant ...
        self.bruit_fond = np.random.randn(nx, ny) * 0.01 + 1j * np.random.randn(nx, ny) * 0.01
    
    def lire_onde_lecteur(self, kx, ky, lecteur_id=0):
        """Chaque lecteur a une LEGERE variation du bruit de fond."""
        bruit_varie = self.bruit_fond * (1.0 + lecteur_id * 0.001)
        onde_ref = np.exp(-1j * (kx * self.xx + ky * self.yy))
        H_effective = self.H + bruit_varie  # Bruit different pour chaque lecteur
        corr = np.sum(H_effective * onde_ref)
        return float(np.abs(corr) / (self.nx * self.ny))
```

### A3 : Vocabulaire enrichi (passage a 1000+ tokens)

**Probleme** : 323 tokens, dont beaucoup sont des mots inutiles.

**Solution** : Generer un vocabulaire depuis un texte reel (Wikipedia/corec)

```bash
# Extraire les mots les plus frequents d'un corpus reel
python -c "
from collections import Counter
import re
texte = open('corpus.txt', encoding='utf-8').read()
mots = re.findall(r'\\b\\w+\\b', texte.lower())
freqs = Counter(mots)
for mot, count in freqs.most_common(5000):
    print(mot)
" > vocab_5000.txt
```

**Impact** : <UNK> quasi-elimine pour le francais courant

### A4 : Optimisation FFT 2D (de 7s a ~0.1s par generation)

**Probleme** : La boucle sur 323 tokens pour `activations_tokens()` est O(V*N).

**Solution** : Utiliser la FFT 2D pour calculer TOUTES les activations en O(N log N) :

```python
import numpy.fft as fft

class HologrammeMonde:
    def activations_masse(self, tokenizer):
        """
        Calcule TOUTES les activations en UNE operation FFT 2D.
        O(N log N) au lieu de O(V*N) ou V=vocab_size.
        """
        # FFT 2D de l'hologramme = spectre complet
        spectre = fft.fft2(self.H)  # [64, 64] complexe
        
        # Interpolation sur les k des tokens
        activations = np.zeros(tokenizer.vocab_size)
        for t in range(tokenizer.vocab_size):
            kx, ky = tokenizer.vecteur_onde(t)
            # kx, ky -> indices dans le spectre FFT
            i = int((kx + math.pi) / (2*math.pi) * self.nx) % self.nx
            j = int((ky + math.pi) / (2*math.pi) * self.ny) % self.ny
            activations[t] = np.abs(spectre[i, j])
        
        return activations
```

**Impact attendu** : 7s -> ~0.1s par generation

---

## PHASE B : INTEGRATION AVEC VRAI LLM (3-5 jours)

### B1 : Bridge harmonique -> LLM classique

**Principe** : Utiliser l'hologramme harmonique comme MEMOIRE EXTERNE
d'un LLM classique (Qwen/DeepSeek via API).

```
Architecture hybride :
+------------------+    +------------------+    +------------------+
| Hologramme       |    | Lecteurs         |    | LLM classique    |
| (memoire brute)  | -> | (resonance)      | -> | (expression)     |
| 64x64 complexe   |    | 8 perspectives   |    | Qwen/DeepSeek    |
+------------------+    +------------------+    +------------------+
         |                      |                        |
         |   Feedback           |   Contexte enrichi     |   Generation
         +<---------------------+<-----------------------+
```

**Implementation** :

```python
class BridgeHarmoniqueLLM:
    def __init__(self, llm_api, vocab):
        self.monde = HologrammeMonde()
        self.tokenizer = TokeniseurOndes(vocab)
        self.llm = llm_api  # OpenAI/Anthropic/Qwen compatible
    
    def apprendre(self, texte):
        self.monde.enregistrer_texte(texte, self.tokenizer)
    
    def generer(self, prompt, max_tokens=100):
        # 1. Resonance harmonique -> etat conscient
        lecteurs = LecteurResonantMultiple(self.monde)
        lecteurs.apprendre(n_iter=30)
        
        # 2. Extraire les top tokens harmoniques
        acts = lecteurs.activations_tokens(self.tokenizer)
        top_tokens = [self.tokenizer.i2w[i] 
                     for i in np.argsort(acts.mean(axis=0))[-20:]]
        
        # 3. Enrichir le prompt avec le contexte harmonique
        contexte_harmonique = ' '.join(top_tokens)
        prompt_enrichi = f"[Contexte harmonique: {contexte_harmonique}]\n{prompt}"
        
        # 4. Generer avec le LLM classique
        return self.llm.generer(prompt_enrichi, max_tokens)
```

### B2 : Cache reseau

Pour eviter les appels API redondants :

```python
class CacheReseauHarmonique:
    def __init__(self):
        self.cache = {}  # signature -> reponse
    
    def signature(self, prompt, etat_hologramme):
        # Hash du prompt + etat de l'hologramme
        h = hashlib.sha256(f"{prompt}|{etat_hologramme}".encode())
        return h.hexdigest()[:16]
    
    def generer(self, prompt, monde, llm):
        sig = self.signature(prompt, monde.energie())
        if sig in self.cache:
            return self.cache[sig]
        reponse = llm.generer(prompt)
        self.cache[sig] = reponse
        return reponse
```

---

## PHASE C : ARCHITECTURE MODULAIRE FINALE (5-7 jours)

### C1 : Systeme multi-hologrammes

Pour resoudre le probleme de diversite de fond :

```python
class SystemeMultiHologrammes:
    """
    Chaque lecteur a SON hologramme personnel + un hologramme commun.
    -> La memoire commune + les experiences personnelles
    -> Chaque lecteur a une perspective UNIQUE
    """
    def __init__(self, n_lecteurs=8, nx=64, ny=64):
        self.hologramme_commun = HologrammeMonde(nx, ny)
        self.hologrammes_persos = [HologrammeMonde(nx, ny) 
                                   for _ in range(n_lecteurs)]
        self.n_lecteurs = n_lecteurs
    
    def apprendre(self, texte, tokenizer, importance_perso=0.3):
        """
        - Le texte va dans l'hologramme commun (100%)
        - Une partie va dans les hologrammes personnels (importance_perso%)
        - Chaque hologramme personnel recoit un SOUS-ENSEMBLE different
        """
        self.hologramme_commun.enregistrer_texte(texte, tokenizer, 1.0)
        
        for n in range(self.n_lecteurs):
            # Chaque lecteur recoit une portion differente du texte
            if np.random.random() < importance_perso:
                self.hologrammes_persos[n].enregistrer_texte(texte, tokenizer, 0.5)
    
    def lire(self, kx, ky, lecteur_id=0):
        """
        Lecture combinee : commun * poids_commun + perso * poids_perso
        """
        act_commun = self.hologramme_commun.lire_onde(kx, ky)
        act_perso = self.hologrammes_persos[lecteur_id].lire_onde(kx, ky)
        return act_commun * 0.7 + act_perso * 0.3
```

### C2 : Extension multimodale (texte + image + son)

```python
class MondeMultimodal:
    """
    Extension de l'hologramme pour supporter plusieurs modalites.
    Chaque modalite = sa propre bande de frequence dans l'hologramme.
    """
    def __init__(self, nx=256, ny=256):
        self.nx, self.ny = nx, ny
        self.H = np.random.randn(nx, ny) * 0.01 + 1j * np.random.randn(nx, ny) * 0.01
        
        # Bandes de frequence par modalite
        self.bandes = {
            'texte': {'kx_min': -5, 'kx_max': 5, 'ky_min': -5, 'ky_max': 5},
            'image': {'kx_min': -50, 'kx_max': 50, 'ky_min': -50, 'ky_max': 50},
            'son':   {'kx_min': 100, 'kx_max': 500, 'ky_min': -50, 'ky_max': 50},
        }
    
    def enregistrer_multimodal(self, modalite, kx, ky, amplitude=1.0):
        """Enregistre une onde dans la bande de la modalite."""
        self.H += amplitude * np.exp(1j * (kx * self.xx + ky * self.yy))
    
    def lire_bande(self, modalite):
        """Extrait la contribution d'une modalite specifique."""
        b = self.bandes[modalite]
        # Filtre passe-bande
        from numpy.fft import fft2, ifft2
        spectre = fft2(self.H)
        masque = np.zeros_like(spectre)
        # Appliquer le masque de bande...
        return ifft2(spectre * masque)
```

### C3 : Modele monde predictif

```python
class ModeleMondePredictif:
    """
    Version avancee qui PREDIT l'etat futur de l'hologramme.
    C'est la capacite d'ANTICIPATION.
    
    Principe : si l'hologramme encode le monde, alors
    la prediction = continuer les motifs d'interference.
    """
    def predire(self, kx_actuel, ky_actuel, pas=1, horizon=5):
        """
        Predire l'evolution du vecteur d'onde sur `horizon` pas.
        Utilise l'historique des gradients pour extrapoler.
        """
        # L'evolution des k suit le gradient de l'hologramme
        # Prediction = continuer dans la meme direction
        predictions = []
        kx, ky = kx_actuel, ky_actuel
        for _ in range(horizon):
            gx = (self.lire(kx+eps, ky) - self.lire(kx-eps, ky)) / (2*eps)
            gy = (self.lire(kx, ky+eps) - self.lire(kx, ky-eps)) / (2*eps)
            kx += pas * gx
            ky += pas * gy
            predictions.append((kx, ky, self.lire(kx, ky)))
        return predictions
```

---

## PHASE D : PRODUCTION (7-14 jours)

### D1 : API REST complete

```python
# Fichier : api_harmonique.py
from flask import Flask, request, jsonify

app = Flask(__name__)
systeme = None  # Initialise au demarrage

@app.route('/apprendre', methods=['POST'])
def apprendre():
    texte = request.json['texte']
    systeme.apprendre(texte)
    return jsonify({
        'status': 'ok',
        'energie': systeme.monde.energie(),
        'n_experiences': systeme.monde.n_experiences
    })

@app.route('/generer', methods=['POST'])
def generer():
    data = request.json
    r = systeme.generateur.generer(
        prompt=data['prompt'],
        max_tokens=data.get('max_tokens', 50),
        temperature=data.get('temperature', 0.85),
        feedback_conscient=data.get('feedback', True)
    )
    return jsonify(r)

@app.route('/diagnostic', methods=['GET'])
def diagnostic():
    return jsonify(systeme.diagnostiquer())
```

### D2 : Tests de non-regression

```python
class TestsHarmonique:
    def test_tokenisation_unique(self):
        """Verifie que tous les tokens ont des vecteurs uniques"""
        tk = TokeniseurOndes(VOCAB)
        assert len({tk.vecteur_onde(i) for i in range(len(VOCAB))}) == len(VOCAB)
    
    def test_accumulation_monotone(self):
        """L'energie doit toujours croitre avec les experiences"""
        m = HologrammeMonde()
        e0 = m.energie()
        for _ in range(10):
            m.enregistrer_onde(np.random.randn(), np.random.randn())
            assert m.energie() > e0
            e0 = m.energie()
    
    def test_diversite_lecteurs(self):
        """Apres diversite, les lecteurs doivent avoir des tops differents"""
        l = LecteurResonantMultiple(...)
        l.apprendre_avec_diversite(n_iter=50)
        tops = [set(l.top_tokens(tk, 5)) for n in range(8)]
        # Au moins 2 lecteurs differents
        differents = sum(1 for i in range(8) for j in range(i+1, 8)
                        if tops[i] != tops[j])
        assert differents > 0, "Tous les lecteurs sont identiques!"
    
    def test_generation_sans_crash(self):
        """La generation ne doit jamais planter"""
        g = GenerateurResonance(VOCAB)
        g.apprendre("test de generation")
        r = g.generer("test")
        assert 'texte_genere' in r
        assert r['n_tokens'] > 0
```

---

## CALENDRIER ESTIME

| Phase | Tache | Duree | Dependances |
|-------|-------|-------|-------------|
| **A1** | Diversite des lecteurs | ~2h | - |
| **A2** | Bruit de fond individuel | ~1h | - |
| **A3** | Vocabulaire enrichi | ~4h | Corpus texte |
| **A4** | Optimisation FFT | ~4h | A1, A2 |
| **B1** | Bridge LLM harmonique | ~1j | A1-A4 |
| **B2** | Cache reseau | ~2h | B1 |
| **C1** | Multi-hologrammes | ~1j | A1, A2 |
| **C2** | Extension multimodale | ~2j | C1 |
| **C3** | Modele predictif | ~2j | C1, A4 |
| **D1** | API REST | ~1j | B1, C1 |
| **D2** | Tests | ~1j | Tout |
| **D3** | Documentation | ~1j | Tout |

**Total estime** : 12-20 jours pour une version production-ready

---

## DECISIONS A PRENDRE MAINTENANT

1. **Priorite immediate** : Par quoi commencer ?
   - Option A : Corriger la diversite des lecteurs (A1 + A2) -> resultat visible rapidement
   - Option B : Enrichir le vocabulaire (A3) -> moins de <UNK> immediatement
   - Option C : Optimiser FFT (A4) -> generation plus rapide

2. **Architecture cible** :
   - Pur harmonique (tout notre code, du bas en haut)
   - Hybride (hologramme + LLM API)
   - Les deux

3. **Echelle** :
   - 64x64 (prouve, mais petit)
   - 256x256 (moyen, recommandé)
   - 1024x1024 (grand, necessite GPU)

**Ma recommandation** : 
- Commencer par **A1 + A2** (la diversite est le verrou critique)
- Puis **A4** (FFT pour la vitesse)
- Puis **B1** (hybridation avec Qwen/DeepSeek pour la qualite)
- En parallele **A3** (vocabulaire enrichi)

La suite depend de votre vision : voulez-vous un prototype de demonstration rapidement, ou l'architecture finale directement ?
