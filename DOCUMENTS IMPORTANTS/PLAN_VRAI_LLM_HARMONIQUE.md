# PLAN DU VRAI LLM HARMONIQUE
## Génération Token-par-Token par Émission de Signatures

**Date :** 26 Mai 2026  
**Auteur :** Décision architecturale après analyse honnête  
**Principe :** L'inconscient harmonique ne doit PAS faire de la récupération de phrases — il doit GÉNÉRER du texte token par token, en émettant des signatures 9D à chaque pas.

---

## 1. Problème Fondamental Résolu

**L'ancien système (fusion_harmonique.py) :**
- Prend un prompt → cherche les phrases les plus similaires dans la mémoire → les fusionne
- Ce n'est PAS un LLM. C'est un moteur de recherche sémantique + concaténateur.
- Résultat : `"le chat" → "la est les dans la intelligence lumiere le"` — charabia.

**La nouvelle architecture :**
- Prend un prompt → génère TOKEN PAR TOKEN en utilisant les signatures 9D comme espace latent
- Chaque token est émis par un **décodeur harmonique** qui transforme la signature courante en logits
- Résultat attendu : des phrases grammaticalement correctes

---

## 2. Architecture du Vrai LLM Harmonique

```
┌──────────────────────────────────────────────────────────────────────┐
│                         VRAI LLM HARMONIQUE                           │
│                                                                      │
│   Token[t-1]                                                         │
│       │                                                              │
│       ▼                                                              │
│  ┌──────────┐                                                        │
│  │Projecteur│───► signature_9d[t-1]   (9 dimensions sémantiques)     │
│  │Semantique│                                                        │
│  └──────────┘                                                        │
│       │                                                              │
│       ▼                                                              │
│  ┌──────────┐                                                        │
│  │  JEPA    │───► signature_9d_prédite[t]   (prédiction dans latent) │
│  │Predictor │                                                        │
│  └──────────┘                                                        │
│       │                                                              │
│       ▼                                                              │
│  ┌──────────┐                                                        │
│  │PhiInverse│───► logits sur vocabulaire  (décodeur inverse ABC)     │
│  │ Decoder  │                                                        │
│  └──────────┘                                                        │
│       │                                                              │
│       ▼                                                              │
│  ┌──────────┐                                                        │
│  │ Sampling │───► Token[t]   (tempéré, top-k, top-p, répétition)     │
│  │Harmonique│                                                        │
│  └──────────┘                                                        │
│       │                                                              │
│       └──────────► RETOUR À LA PREMIÈRE ÉTAPE ──────────────────────►│
│                                                                      │
│  • Zéro paramètre entrainable (tout est formule fermée)              │
│  • 1 seule passe par token (pas de forward sur toute la séquence)    │
│  • 100% déterministe si températude = 0                              │
│  • Pur numpy ou torch (sans autograd)                                │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. Modules à Implémenter (Ordre Prioritaire)

### Phase 1 — Génération Token-par-Token (AUJOURD'HUI)

| # | Module | Description | Dépend de |
|---|--------|-------------|-----------|
| 1 | **ProjecteurSemantiqueToken** | Signature 9D d'UN SEUL token (pas d'une phrase entière) | harmonic_unconscious.py |
| 2 | **JEPAPredicteur** | Prédit signature_9d[t+1] à partir de signature_9d[t] + contexte | abc_kernel.py |
| 3 | **PhiInverseDecoder v2** | Transforme signature_9d en logits sur le vocabulaire | harmonic_signature_decoder.py |
| 4 | **SamplerHarmonique** | Sampling tempéré + top-k + top-p + pénalité répétition | — |
| 5 | **Boucle de Génération** | `input → [projecteur → jepa → decoder → sampler] × N → output` | 1-4 |

### Phase 2 — Contexte et Mémoire (JOUR 2)

| # | Module | Description |
|---|--------|-------------|
| 6 | **ContexteHarmonique** | Fenêtre glissante des N dernières signatures 9D |
| 7 | **JEPAMultiPas** | Prédiction à Δt = {1, 2, 4} tokens (multi-échelle) |
| 8 | **NoyauABCContextuel** | Pondération des signatures passées par mémoire non-locale |
| 9 | **GuidancePur** | Injection des signatures PUR 7D dans la décision (pont conscient↔inconscient) |

### Phase 3 — Qualité LLM (JOUR 3-5)

| # | Module | Description |
|---|--------|-------------|
| 10 | **Vocabulaire Étendu** | 5000→20000 tokens avec sous-mots BPE |
| 11 | **AttentionCroisée** | Mécanisme d'attention entre signatures passées et signature courante |
| 12 | **RésonanceMultiTête** | 4 têtes de résonance au lieu d'1 (comme multi-head attention) |
| 13 | **AlignementPhi** | Forçage des logits vers les harmoniques de φ (RLHF harmonique) |

---

## 4. Détail Technique de la Phase 1

### 4.1 ProjecteurSemantiqueToken

```python
class ProjecteurSemantiqueToken:
    """
    Signature 9D d'UN SEUL token.
    Au lieu de mesurer la diversité lexicale d'une phrase,
    on utilise les propriétés du token lui-même :
    - longueur du mot
    - présence de chiffres
    - catégorie grammaticale (stop word, émotionnel, mathématique)
    - position dans le vocabulaire ordonné
    - fréquence relative (si disponible)
    """
    
    DIMS = ['phi', 'alpha', 'reasoning', 'creativity', 'math', 
            'factual', 'code', 'emotion', 'temporal']
    
    def projeter(self, token: str, position: int = 0) -> np.ndarray:
        # phi: normalised position in vocabulary
        # alpha: word length / max_word_length
        # reasoning: 1.0 if stop word else 0.3
        # creativity: 1.0 if long word (>7 letters) else 0.2
        # math: 1.0 if has digits else 0.0
        # factual: 1.0 if in stop_words else 0.2
        # code: 1.0 if code syntax else 0.0
        # emotion: 1.0 if emotional word else 0.1
        # temporal: 0.5 (constant per token, varies across sequence)
        ...
```

### 4.2 JEPAPredicteur

```python
class JEPAPredicteur:
    """
    Prédit la signature 9D du prochain token à partir de :
    - La signature 9D du token courant
    - Les signatures 9D des tokens précédents (contexte)
    - Le noyau ABC pour la mémoire non-locale
    
    Formule : sig_pred[t+1] = f(sig[t], sig[t-1], ..., sig[t-N])
    
    Où f est une combinaison linéaire pondérée par le noyau ABC :
    sig_pred = Σ_k w_k * sig[t-k]  où w_k = K_ABC(k)
    
    Puis normalisation et clipping.
    """
    
    def predire(self, signatures_contexte: np.ndarray) -> np.ndarray:
        # signatures_contexte: [N, 9] 
        # Poids ABC décroissants
        poids = np.array([K_ABC(k) for k in range(N)])
        poids = poids / poids.sum()
        
        sig_pred = poids @ signatures_contexte  # [9]
        sig_pred = np.clip(sig_pred, 0.0, 1.0)
        return sig_pred
```

### 4.3 PhiInverseDecoder v2

Le décodeur existant (harmonic_signature_decoder.py) projette une signature 7D vers vocab_size. On l'adapte pour 9D :

```python
class PhiInverseDecoderV2:
    """
    Décodeur = Projection signature → logits.
    
    weight[d, v] = cos(v × d × φ / V) × φ / exp(-d × α / V)
    
    logits = sig @ weight  +  bias_harmonique
    """
    
    def __init__(self, vocab_size: int, sig_dim: int = 9):
        # Matrice de poids fixe basée sur PHI
        d = np.arange(sig_dim)
        v = np.arange(vocab_size)[:, None]
        phase = v * d * PHI / vocab_size
        k_abc_inv = PHI / np.exp(-d * ALPHA / sig_dim)
        self.weight = np.cos(phase) * k_abc_inv[None, :]
        # Normalisation
        self.weight = self.weight / (np.linalg.norm(self.weight, axis=0, keepdims=True) + 1e-8)
    
    def decoder(self, sig: np.ndarray) -> np.ndarray:
        """sig: [9] → logits: [vocab_size]"""
        logits = sig @ self.weight.T  # [vocab_size]
        # Bonus harmonique : les tokens dont l'ID est proche de φ^k
        # reçoivent un léger bonus (favorise la cohérence harmonique)
        logits *= PHI
        return logits
```

### 4.4 SamplerHarmonique

```python
class SamplerHarmonique:
    """
    Sampling avec :
    - Température
    - Top-k filtering
    - Top-p (nucleus) sampling
    - Pénalité de répétition
    - Guidance par résonance φ (optionnelle)
    - Masquage des tokens spéciaux (<PAD>, <UNK>, <BOS>)
    """
    
    def echantillonner(self, logits: np.ndarray, 
                       temperature=0.85, top_k=40, top_p=0.9,
                       repetition_penalty=1.2, tokens_recents=None,
                       masquer_speciaux=True) -> int:
        ...
```

### 4.5 Boucle de Génération Complète

```python
class VraiLLMHarmonique:
    """
    Le VRAI LLM Harmonique.
    
    Boucle de génération :
    for _ in range(max_tokens):
        sig_courante = projecteur.projeter(dernier_token)
        sig_predite = jepa.predire(contexte_signatures + [sig_courante])
        logits = phi_inverse.decoder(sig_predite)
        prochain_token = sampler.echantillonner(logits)
        generated.append(prochain_token)
    
    Retour : texte généré, tokens, signatures, métadonnées
    """
    
    def __init__(self, vocab_size=5000):
        self.projecteur = ProjecteurSemantiqueToken()
        self.jepa = JEPAPredicteur(fenetre_contexte=16)
        self.decoder = PhiInverseDecoderV2(vocab_size=vocab_size, sig_dim=9)
        self.sampler = SamplerHarmonique()
        self.tokenizer = HarmonicTokenizer(vocab_size=vocab_size)
        # Mémoire des signatures contextuelles
        self.contexte_signatures = []
        self.contexte_tokens = []
    
    def generer(self, prompt: str, max_tokens=100, **sampling_params) -> str:
        tokens = self.tokenizer.encode(prompt)
        generated = tokens.copy()
        self.contexte_signatures = []
        self.contexte_tokens = []
        
        # Amorcer le contexte avec le prompt
        for t in tokens:
            mot = self.tokenizer.id_to_token.get(t, '<UNK>')
            sig = self.projecteur.projeter(mot, position=len(self.contexte_tokens))
            self.contexte_signatures.append(sig)
            self.contexte_tokens.append(t)
        
        # Boucle de génération
        for step in range(max_tokens):
            # 1. Prédire la prochaine signature
            sig_pred = self.jepa.predire(np.array(self.contexte_signatures[-16:]))
            
            # 2. Décodeur : signature → logits
            logits = self.decoder.decoder(sig_pred)
            
            # 3. Masquage des tokens spéciaux
            for t_interdit in [0, 1, 2]:  # <PAD>, <UNK>, <BOS>
                logits[t_interdit] = -1e9
            
            # 4. Pénalité de répétition
            for t in set(generated[-50:]):
                if t < len(logits):
                    logits[t] /= repetition_penalty if logits[t] > 0 else repetition_penalty
            
            # 5. Sampling
            next_token = self.sampler.echantillonner(logits, **sampling_params)
            
            # 6. Token suivant
            generated.append(next_token)
            mot = self.tokenizer.id_to_token.get(next_token, '<UNK>')
            sig = self.projecteur.projeter(mot, position=len(self.contexte_tokens))
            self.contexte_signatures.append(sig)
            self.contexte_tokens.append(next_token)
            
            if next_token == 3:  # <EOS>
                break
        
        return self.tokenizer.decode(generated)
```

---

## 5. Pourquoi cette Architecture GAGNE

| Critère | Ancien système (fusion) | Vrai LLM Harmonique |
|---------|------------------------|---------------------|
| **Génération** | Fusion de phrases existantes | Token par token original |
| **Grammaire** | Aucune garantie | Apprise par co-occurrences dans JEPA |
| **Cohérence** | Limitée (concaténation) | Continue (prédiction de signature) |
| **Créativité** | Copie de connaissances | Génération de nouvelles séquences |
| **Vocabulaire** | 423 tokens | 5000+ tokens |
| **Contexte** | 1 phrase | 16+ tokens de contexte |
| **Paramètres** | 0 | 0 (tout fixe) |
| **CPU** | Oui | Oui |
| **Déterministe** | Oui (si temp=0) | Oui (si temp=0) |

---

## 6. Implémentation Immédiate

Le fichier `harmonic_training/model/vrai_llm_harmonique.py` contiendra l'implémentation complète de la Phase 1.

Structure du fichier :
1. `ProjecteurSemantiqueToken` — signature 9D d'un token
2. `NoyauABC` — mémoire non-locale (repris de abc_kernel.py)
3. `JEPAPredicteur` — prédiction de signature
4. `PhiInverseDecoderV2` — signature → logits
5. `SamplerHarmonique` — échantillonnage
6. `VraiLLMHarmonique` — boucle complète
7. `test()` — validation immédiate

**Critères de succès pour la Phase 1 :**
- `"le chat"` → `"mange la souris dans le jardin"` (phrase grammaticale)
- `"la philosophie"` → `"est l amour de la sagesse"` (cohérence sémantique)
- Zéro token `<UNK>` dans la sortie
- Diversité > 80% (pas de répétition de boucle)
- Temps de génération < 100ms par token (CPU)

---

*"Un LLM qui ne génère pas token par token n'est pas un LLM. C'est une bibliothèque."
— Leçon du 26 Mai 2026*
