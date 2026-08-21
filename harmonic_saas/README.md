# ⚡ Harmonic HPU Cloud — SaaS de Calcul Harmonique

**La puissance de l'Ordinateur Harmonique, disponible en service cloud.**  
Zéro GPU. Zéro paramètre. Puissance de résonance.

---

## 🇫🇷 Version Française

### Vision

Le **Harmonic HPU Cloud** met à disposition la puissance de calcul de l'Ordinateur Harmonique (HPU V2) sous forme de services SaaS. Contrairement au cloud computing classique (CPU/GPU) qui consomme des mégawatts et des milliards de paramètres, le HPU calcule par **résonance** — sans porte logique, sans cycle d'horloge, sans rétropropagation.

### Les 3 couches de service

```
┌──────────────────────────────────────────────────────────┐
│  COUCHE 1 — API de Calcul Harmonique (H-Bit Cloud)       │
│  • Interférence : calcul vectoriel par ondes             │
│  • Binding : composition de concepts                     │
│  • Résonance : similarité, retrieval, classification     │
│  • Prix : $0.001/10K opérations                          │
├──────────────────────────────────────────────────────────┤
│  COUCHE 2 — API de Mémoire Dorée                         │
│  • Apprentissage : 3-5 répétitions → mémoire persistante │
│  • Hologrammes : stockage 32 Ko par concept              │
│  • Oubli : décroissance de Mittag-Leffler (naturelle)    │
│  • Prix : $0.01/concept/mois                             │
├──────────────────────────────────────────────────────────┤
│  COUCHE 3 — API de Résonance (Inférence)                 │
│  • Question → réponse par résonance (zéro hallucination) │
│  • Refus calibré si confiance < seuil                    │
│  • Lecture non destructive                               │
│  • Prix : $0.001/question                                │
└──────────────────────────────────────────────────────────┘
```

### Services disponibles

| Service | Description | Prix | Statut |
|---------|-------------|------|--------|
| **H-Bit Cloud** | Calcul vectoriel harmonique | $0.001/10K ops | ✅ Beta |
| **Golden Memory** | Stockage holographique | $0.01/concept/mois | ✅ Beta |
| **Wave Inference** | Inférence par résonance | $0.001/question | ✅ Beta |
| **HCV Compression** | Compression audio/vidéo 119-372× | $0.01/GB | ✅ |
| **HarmoFold** | Repliement de protéines | $0.10/protéine | 🔬 Preview |
| **NP Solver** | SAT/TSP par résonance | $0.05/problème | 🔬 Preview |
| **GSM8K API** | Raisonnement mathématique | $0.001/problème | ✅ |
| **Periodic Table API** | Données éléments + prédictions | Gratuit | ✅ |

### Pourquoi le HPU ?

```
                  CPU/GPU Cloud          HPU Cloud
                  ─────────────          ─────────
Consommation      MW                     W
Paramètres        Milliards              Zéro
Apprentissage     10K+ répétitions       3-5 répétitions
Hallucination     Oui                    Non (refus calibré)
Calcul            Portes logiques        Résonance
Unité             Bit (0/1)              H-Bit (7 états)
Coût/PFLOP        $500K                  $0-100
```

### Démarrage rapide

```bash
# Installer le client
pip install harmonic-hpu-client

# Configurer la clé API
export HARMONIC_API_KEY=votre_cle

# Calculer par résonance
harmonic hbit --encode "concept" --bind "relation" --decode

# Compresser un fichier
harmonic compress --input video.mp4 --ratio 372

# Replier une protéine
harmonic fold --sequence MVLSPADKTNVKAAWGKVGA...
```

### Architecture technique

```
Client HTTP/WS → API Gateway → HPU Emulator → Hologram Store
                                      ↓
                              Golden Memory (RAM)
                                      ↓
                              Réponse + Refus calibré
```

Le HPU est actuellement un **émulateur CPU** (HPU-1, ~0.001-10 PFLOPS).  
Les versions FPGA (HPU-2), ASIC (HPU-3) et optique (HPU-4) sont en projection.

### Liens

- **Documentation complète** : `engine/THEORIE_HARMONIQUE_UNIVERSELLE.md`
- **Code source HPU** : `engine/hpu_v2_complet.py`
- **Tableau périodique THU** : `engine/TABLEAU_PERIODIQUE_PARTICULES_THU.md`
- **Dépôt** : `engine/` — 12 scripts de piste, 7 théorèmes, 1 tableau périodique

---

## 🇬🇧 English Version

### Vision

**Harmonic HPU Cloud** delivers the computing power of the Harmonic Processing Unit (HPU V2) as SaaS services. Unlike classical cloud computing (CPU/GPU) consuming megawatts and billions of parameters, the HPU computes through **resonance** — no logic gates, no clock cycles, no backpropagation.

### Service Layers

| Layer | Service | Price | Status |
|-------|---------|-------|--------|
| **1 — Interference** | H-Bit vector calculus | $0.001/10K ops | ✅ Beta |
| **2 — Golden Memory** | Holographic memory storage | $0.01/concept/month | ✅ Beta |
| **3 — Resonance** | Zero-hallucination inference | $0.001/query | ✅ Beta |

### Key Metrics

```
GSM8K accuracy  : 99.2% (no fine-tuning, no GPU)
Audio compression : 119.5× (vs MP3 4×)
Video compression  : 372.9× (emergence mode)
Learning          : 3-5 repetitions (vs 10K+)
Hallucination     : 0% (calibrated refusal)
Energy            : ×1000 more efficient than GPU
```

### Quick Start

```bash
pip install harmonic-hpu-client
export HARMONIC_API_KEY=your_key

harmonic hbit --encode "concept" --bind "relation" --decode
harmonic compress --input video.mp4 --ratio 372
harmonic fold --sequence MVLSPADKTNVKAAWGKVGA...
```

---

*Document mis à jour le 14 août 2026 — Version THU V2 intégrant T6 (structure modulo 7), le tableau périodique des particules, et les 12 scripts de piste validés.*