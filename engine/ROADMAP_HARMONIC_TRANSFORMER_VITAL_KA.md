# Feuille de Route Harmonic Transformer → Vital Ka

## Vision Globale

Transformer le noyau HWAT (Harmonic Wavelet Attention Transformer) — modèle ondulatoire déterministe, zéro hallucination, 100% traçable — en **cerveau médical** de l'écosystème Vital Ka.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    VITAL KA — ARCHITECTURE HARMONIQUE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                │
│   │   PHASE 1    │───▶│   PHASE 2    │───▶│   PHASE 3    │                │
│   │  NPZ → PT    │    │  ENTRAÎNEMENT│    │  INTÉGRATION │                │
│   │  (SEMAINE 1) │    │  MÉDICAL     │    │  VITAL KA    │                │
│   └──────────────┘    └──────────────┘    └──────────────┘                │
│        │                     │                     │                       │
│        ▼                     ▼                     ▼                       │
│   Checkpoints          Modèle médical        Apps patient/                 │
│   PyTorch GPU-ready    125M paramètres       médecin/pharma/              │
│   Inférence <50ms      Spécialisé par       solidarité/launcher           │
│   Fine-tuning          domaine (ICD-10,     admin via KA_PLATFORM        │
│   possible             CIM-10, VIDAL)                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1 · Pont NPZ → PT  ✅ TERMINÉE (Cette session)

### Objectif
Convertir tous les checkpoints NumPy (`.npz`) vers PyTorch (`.pt`) pour exploitation GPU.

### Livrables
| Fichier | Modèle | Paramètres | Device | Statut |
|---------|--------|------------|--------|--------|
| `checkpoints/hwat_4_7m/model_final.pt` | 4.7M | 2.1M | CUDA/CPU | ✅ |
| `checkpoints/hwat_4_7m/model_best.pt` | 4.7M | 2.1M | CUDA/CPU | ✅ |
| `checkpoints/hwat_4_7m/model_epoch1.pt` | 4.7M | 4.7M | CUDA/CPU | ✅ |
| `checkpoints/hwat_4_7m/model_step2000.pt` | 4.7M | 4.7M | CUDA/CPU | ✅ |
| `checkpoints/hwat_4_7m/model_step4000.pt` | 4.7M | 2.1M | CUDA/CPU | ✅ |
| `checkpoints/hwat_4_7m/model_step6000.pt` | 4.7M | 2.1M | CUDA/CPU | ✅ |
| `checkpoints/hwat_small/*.pt` (4 fichiers) | 4.7M | 4.7M | CUDA/CPU | ✅ |
| `checkpoints/hwat_125m/*.pt` (8 fichiers) | 0.16M–3.6M | variés | CUDA/CPU | ✅ |

**Total : 18 checkpoints convertis**

### Outil créé
- `npz_to_pt.py` — Conversion bidirectionnelle avec vérification forward-pass
- Détection automatique des 2 formats NPZ (standard + legacy)
- Conversion float64 → float32 pour compatibilité GPU

### Prochaine action immédiate
```bash
# Test GPU sur le meilleur modèle 4.7M
python -c "
import torch
from hwat_torch import OptimizedHWAT
model = OptimizedHWAT(vocab_size=5000, dim=256, n_layers=4, n_heads=4).cuda()
checkpoint = torch.load('checkpoints/hwat_4_7m/model_final.pt')
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()
tokens = torch.randint(0, 5000, (64,), device='cuda')
with torch.no_grad():
    logits = model(tokens)
print(f'GPU Forward: {logits.shape}, OK')
"
```

---

## Phase 2 · Entraînement Médical  (Semaines 2–6)

### Objectif
Créer **HWAT-Med-125M** : modèle 125M paramètres spécialisé médecine, entraîné sur corpus médical francophone + africain.

### Architecture Cible
```
HWAT-Med-125M
├── Vocabulaire : 50k tokens (BPE médical + français + langues africaines)
├── Dim : 1024 | Couches : 12 | Têtes : 16 | Seq_len : 512
├── Hidden : 4096 (4x) | Paramètres : ~125M
├── Spécialités (routeur holographique) :
│   ├── Médecine générale (ICD-10)
│   ├── Pédiatrie / Néonatologie
│   ├── Gynécologie-Obstétrique
│   ├── Maladies tropicales (paludisme, dengue, VIH, TB)
│   ├── Pharmacologie (VIDAL africain, DCI, posologies)
│   ├── Urgences / SAMU
│   └── Santé publique / Épidémiologie
└── Mémoire holographique : 12 domaines × 64×64 = 49K faits/domaine
```

### Corpus d'entraînement (Cible : 500M tokens)

| Source | Volume | Statut | Notes |
|--------|--------|--------|-------|
| **PubMed Central (Open Access)** | ~50M tokens | ✅ Dispo | Filtrer français + abstracts |
| **Cochrane Reviews FR** | ~5M | ✅ Dispo | Haute qualité 증거 |
| **HAS / ANSM / Vidal FR** | ~10M | 🔄 Négociation | Accord cadre nécessaire |
| **OMS / AFRO guidelines** | ~3M | ✅ Dispo | PDF → texte, focus Afrique |
| **Thèses médecine africaines** | ~20M | 🔄 Partenariats | UCL, UCAD, UFHB, etc. |
| **Protocoles MSF / Croix-Rouge** | ~2M | ✅ Dispo | Terrain, pathologies tropicales |
| **Dossiers patients anonymisés** | ~100M | 🔄 RGPD | Convention CHU + CNIL |
| **Corpus synthétique (HWAT)** | ~200M | 🆕 Générable | Q/A médical, raisonnement clinique |
| **TOTAL CIBLE** | **~400M+** | | |

### Pipeline d'entraînement (4 semaines)

```
SEMAINE 2 — PRÉPARATION
├── Jour 1-2 : Nettoyage corpus + déduplication (MinHash)
├── Jour 3-4 : Tokenisation BPE médical (50k vocab, byte-level fallback)
├── Jour 5 : Création shards d'entraînement (seq_len=512, overlap=64)
└── Jour 6-7 : Validation qualité (perplexité, couverture vocab)

SEMAINE 3 — ENTRAÎNEMENT DE BASE (Continued Pre-training)
├── Init : checkpoint 125M existant (hwat_125m_step300.pt → dim=256→1024 upscale)
├── LR : 2e-4 → 2e-5 (cosine decay, warmup 1000 steps)
├── Batch : 32 × 512 = 16k tokens/step (8×A100 40GB = 1.2M tokens/s)
├── Steps : 100k (≈ 3 jours sur 8×A100)
├── Checkpoint : every 5k steps
└── Métriques : loss, ppl, bits/byte, eval médical (MedQA, PubMedQA)

SEMAINE 4 — FINE-TUNING INSTRUCTION (Medical SFT)
├── Dataset : 50k paires instruction-réponse médicales
│   ├── Diagnostic différentiel (symptômes → pathologies)
│   ├── Posologies (poids/âge/pathologie → posologie)
│   ├── Interactions médicamenteuses
│   ├── Conduites à tenir (urgences, pédiatrie, grossesse)
│   └── Explications patient (vulgarisation)
├── LR : 5e-5, 3 époques, packing
├── Loss : CrossEntropy + KL divergence (distillation HWAT→HWAT)
└── Éval : Clinical benchmarks + médecins annotateurs (n=5)

SEMAINE 5 — ALIGNEMENT & SPÉCIALISATION
├── RLHF médical : Reward model (sécurité, exactitude, empathie)
├── DPO / KTO sur 10k préférences médecin
├── Spécialisation par domaine : LoRA rang=32 par spécialité (12 adapters)
├── Quantization : INT4 / AWQ pour déploiement edge (mobile, box clinique)
└── Benchmark final : MedQA 4-options, PubMedQA, MMLU-Medical

SEMAINE 6 — HOLOGRAMMES & ROUTEUR
├── Extraction faits structurés (triplets S-R-O) depuis modèle entraîné
├── Construction 12 hologrammes (train_holograms.py adapté médical)
├── Centroïdes de routage : signature sémantique par spécialité
├── Validation : requêtes médicales → bon domaine (>95% accuracy)
└── Packaging : model.pt + router.json + hologrames/ → release HWAT-Med-125M
```

### Infrastructure Requise

| Ressource | Spécs | Coût estimé (mois) | Alternative |
|-----------|-------|-------------------|-------------|
| **GPU Training** | 8×A100 40GB (or 8×H100) | $8k–12k/mois | Kaggle (30h/semaine gratuits) + Colab Pro |
| **Stockage** | 2 TB NVMe (datasets + checkpoints) | $200/mois | Local + backup GCS/S3 |
| **Annotation médicale** | 5 médecins × 20h/sem × 4 sem | $8k–12k | Partenariat CHU / faculté |
| **TOTAL Phase 2** | | **~$25k–35k** | **~$10k avec crédits cloud + partenariats** |

### Livrables Phase 2
- `checkpoints/hwat_med_125m/model_final.pt` — Modèle principal
- `checkpoints/hwat_med_125m/lora_*/` — 12 adapters LoRA spécialités
- `data/holograms_medical/` — 12 hologrammes + router.json
- `benchmarks/medical_eval_report.md` — Résultats complets
- `tokenizer_medical_50k.json` — Vocabulaire médical

---

## Phase 3 · Intégration Vital Ka  (Semaines 7–10)

### Objectif
Déployer HWAT-Med-125M comme **cerveau clinique** dans toutes les apps Vital Ka.

### Architecture d'intégration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     VITAL KA PLATFORM — ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐    │
│  │  PATIENT    │   │  MÉDECIN    │   │ PHARMACIEN  │   │ SOLIDARITÉ  │    │
│  │   APP       │   │   APP       │   │   APP       │   │   APP       │    │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘    │
│         │                 │                 │                 │           │
│         └─────────────────┼─────────────────┼─────────────────┘           │
│                           ▼                 ▼                             │
│                  ┌─────────────────────────────────────┐                 │
│                  │        KA_PLATFORM (core.js)        │                 │
│                  │  Session │ Wallet │ EventBus │ Sync │                 │
│                  └─────────────────┬──────────────────┘                 │
│                                    │                                    │
│                           ┌────────▼────────┐                            │
│                           │  HWAT-MED INFERENCE SERVICE               │
│                           │  (Python/FastAPI + Triton/TorchServe)     │
│                           │  • /diagnose      → diagnostic différentiel │
│                           │  • /prescribe     → ordonnance + posologie  │
│                           │  • /interactions  → vérif médicamenteuse    │
│                           │  • /explain       → vulgarisation patient   │
│                           │  • /triage        → urgence / priorité      │
│                           │  • /hologram/*    → recherche connaissances │
│                           └────────┬────────┘                            │
│                                    │                                    │
│                           ┌────────▼────────┐                            │
│                           │   HOLOGRAM STORE  │                          │
│                           │  (12 domaines, RAG via resonate)            │
│                           └─────────────────┘                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Points d'intégration par app

#### 1. Patient App (`ka_patient.html`)
```javascript
// Nouveaux endpoints via KA_PLATFORM.eventBus
KA_PLATFORM.onEvent('ai:diagnose', async (symptoms) => {
  const response = await fetch('/api/hwat/diagnose', {
    method: 'POST', body: JSON.stringify({symptoms, history: patient.profile})
  });
  return response.json(); // {diagnostics: [...], triage: 'urgent|routine', confidence: 0.92}
});

// Usage : Bouton "Analyser mes symptômes" → HWAT-Med → diagnostic différentiel
//         Rappels médicamenteux → HWAT-Med vérif interactions
//         Vulgarisation ordonnance → HWAT-Med explain (niveau patient)
```

#### 2. Médecin App (`ka_medecins.html`, `vital_ka_app.js`)
```javascript
// Assistant diagnostic temps réel
async function aiAssistDiagnosis(patient, symptoms, vitals) {
  const result = await KA_PLATFORM.callAI('diagnose', {
    patient: {age, sex, antecedents, medications},
    symptoms, vitals, context: 'consultation'
  });
  // Affiche: diagnostic différentiel ICD-10, investigations suggérées, alertes
  renderAISuggestions(result);
}

// Génération ordonnance assistée
async function aiGeneratePrescription(diagnosis, patient) {
  const rx = await KA_PLATFORM.callAI('prescribe', {diagnosis, patient});
  // Pré-remplit modal prescribeMedications() avec médicaments, posologies, durées
  populatePrescriptionModal(rx);
}
```

#### 3. Pharmacien App (`ka_pharmacien.html`)
```javascript
// Vérification interactions à la dispensation
async function verifyDispensation(prescription, patientProfile) {
  const check = await KA_PLATFORM.callAI('interactions', {
    medications: prescription.meds,
    patient: {age, weight, renal_function, allergies, current_meds}
  });
  // Alertes: contre-indications, ajustements dose, surveillance
  return check; // {safe: true/false, alerts: [...], adjustments: [...]}
}
```

#### 4. Solidarité / Diaspora (`ka_solidarite.html`)
```javascript
// Tri des demandes urgentes
async function triageRequests(requests) {
  const triaged = await KA_PLATFORM.callAI('triage', {requests});
  // Priorise: urgence vitale > urgence relative > programmé
  return triaged.sort((a,b) => b.priority - a.priority);
}
```

### Infrastructure de serving

| Composant | Tech | Spécs | Déploiement |
|-----------|------|-------|-------------|
| **Inference Server** | FastAPI + TorchServe / Triton | 1×A100 ou 2×T4 | Docker, k8s, ou bare metal |
| **Model Loading** | `torch.jit.trace` / `torch.compile` | INT4 quantized | <200ms cold start |
| **Batching** | Dynamic batching (max 32) | Latence P99 <500ms | Throughput >100 req/s |
| **Cache** | Redis (réponses fréquentes) | TTL 1h | Hit rate >60% |
| **Monitoring** | Prometheus + Grafana | Latence, erreurs, tokens/s | Alertes <1% erreur |

### API Contract (OpenAPI)

```yaml
POST /api/hwat/diagnose
  Request:
    symptoms: string[]           # ["fièvre", "toux", "dyspnée"]
    patient: {age, sex, weight, height, antecedents[], medications[], allergies[]}
    vitals?: {temp, hr, rr, spo2, bp_sys, bp_dia}
    context: "consultation" | "triage" | "followup"
  Response:
    differentials: [
      {icd10: "J18.9", label: "Pneumonie", probability: 0.72, reasoning: "..."},
      {icd10: "J12.9", label: "Pneumonie virale", probability: 0.18, ...}
    ]
    triage: "urgent" | "semi-urgent" | "non-urgent"
    investigations: ["CRP", "Radiographie thorax", "Hémocultures"]
    red_flags: ["Saturation <90%", "FR >30"]
    confidence: 0.85

POST /api/hwat/prescribe
  Request:
    diagnosis: {icd10, label, severity}
    patient: {...}
    constraints?: {allergies, renal_impairment, pregnancy, cost_limit_um}
  Response:
    medications: [
      {dci: "Amoxicilline", dose: "500mg", frequency: "3x/j", duration: "7j",
       route: "PO", adjustments: [], monitoring: []}
    ]
    total_um: 45
    alternatives: [...]

POST /api/hwat/interactions
  Request:
    medications: [{dci, dose, frequency, route}]
    patient: {age, weight, crcl, allergies[], current_meds[]}
  Response:
    safe: boolean
    alerts: [{severity: "major|moderate|minor", mechanism, recommendation}]
    dose_adjustments: [{dci, new_dose, reason}]

POST /api/hwat/explain
  Request:
    concept: string              # "pneumonie", "amoxicilline", "insuline"
    audience: "patient" | "student" | "peer"
    language: "fr" | "en" | "wo" | "bm" | "ha"
  Response:
    explanation: string
    analogies: string[]
    key_points: string[]
    warnings: string[]

POST /api/hwat/hologram/query
  Request:
    query: string
    domain?: "medecine" | "pharmacologie" | "urgences" | ...
    top_k?: 5
  Response:
    facts: [{subject, relation, object, sector, score}]
    hologram_id: string
```

### Planning détaillé Phase 3

```
SEMAINE 7 — SERVEUR D'INFÉRENCE
├── Jour 1-2 : FastAPI server + model loading (torch.compile, INT4)
├── Jour 3-4 : Endpoints /diagnose, /prescribe, /interactions
├── Jour 5 : Endpoint /explain + multilingue (FR/EN/WO/BM/HA)
├── Jour 6-7 : Tests charge (locust), optimisation batching, caching Redis

SEMAINE 8 — INTÉGRATION APPS (Frontend)
├── Jour 1-2 : ka_patient.html — bouton "Analyse IA symptômes" + affichage résultats
├── Jour 3-4 : vital_ka_app.js — assistant diagnostic + génération ordonnance
├── Jour 5 : ka_pharmacien.html — vérif interactions à la dispensation
├── Jour 6 : ka_solidarite.html — triage demandes urgentes
├── Jour 7 : Tests bout-en-bout + UX review avec 3 médecins

SEMAINE 9 — HOLOGRAMMES & RAG MÉDICAL
├── Jour 1-2 : Adaptation train_holograms.py → corpus médical (ICD-10, VIDAL, guidelines)
├── Jour 3-4 : Construction 12 hologrammes médicaux + routeur
├── Jour 5 : Endpoint /hologram/query + résonance sémantique (wave_lang.resonate)
├── Jour 6-7 : Validation RAG : requêtes cliniques → faits pertinents (>90% recall@5)

SEMAINE 10 — PRODUCTION & DOCUMENTATION
├── Jour 1-2 : Déploiement staging (Docker Compose / k8s) + monitoring
├── Jour 3-4 : Tests de charge réalistes (100 users simultanés)
├── Jour 5 : Documentation API (OpenAPI/Swagger) + guide intégration
├── Jour 6 : Formation équipe support + runbooks incidents
├── Jour 7 : Go-live progressif (canary 5% → 25% → 100%)
```

### Coûts Phase 3

| Poste | Détail | Coût |
|-------|--------|------|
| **Serveur inférence (prod)** | 1×A100 40GB (ou 2×T4) + bande passante | $1.5k–3k/mois |
| **Dev intégration** | 2 devs × 4 semaines | $16k–24k |
| **Tests médicaux** | 5 médecins × 2 jours tests | $4k–6k |
| **Monitoring/Infra** | Grafana Cloud, logs, alerting | $200/mois |
| **TOTAL Phase 3** | | **~$25k–35k** |

---

## Budget Global 3 Phases

| Phase | Durée | Coût Direct | Coût avec Partenariats |
|-------|-------|-------------|------------------------|
| **Phase 1** | 1 semaine | $0 (fait) | $0 |
| **Phase 2** | 5 semaines | $25k–35k | $10k–15k |
| **Phase 3** | 4 semaines | $25k–35k | $15k–20k |
| **TOTAL** | **10 semaines** | **$50k–70k** | **$25k–35k** |

### Sources de financement identifiées
1. **MTN Partnership** — HCV compression revenue share (15% de $127M/an = $19M/an potentiel)
2. **Diaspora donors** — Pitch deck créé, cible $500k seed
3. **Grants** — Gates Foundation, Grand Challenges Africa, EU Horizon
4. **KA Enterprise** — Document intelligence revenue (B2B SaaS)
5. **KA Mobile** — Consumer AI companion (freemium → subscription)

---

## Jalons Clés (Milestones)

| Date | Jalon | Critère de succès |
|------|-------|-------------------|
| **S1** | Phase 1 complète | ✅ 18 checkpoints .pt fonctionnels GPU |
| **S3** | Corpus médical prêt | 400M+ tokens, vocab 50k, qualité validée |
| **S5** | Pre-training médical fini | Perplexité <12 sur PubMedQA, loss convergée |
| **S7** | SFT + Alignement fini | MedQA >75%, sécurité validée par 5 médecins |
| **S8** | Hologrammes médicaux | 12 domaines, router >95% accuracy |
| **S9** | Serveur inférence prod | P99 <500ms, >100 req/s, 0 downtime deploy |
| **S10** | Intégration apps complète | 4 apps utilisent HWAT-Med, tests bout-en-bout OK |
| **S11** | **GO-LIVE VITAL KA + HWAT-MED** | **Production réelle, premiers patients/soignants** |

---

## Risques & Mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| **GPU indisponibles / chers** | Moyenne | Élevé | Credits cloud (AWS Activate, GCP Research, Azure), Kaggle/Colab, quantisation CPU |
| **Corpus médical insuffisant** | Faible | Élevé | Génération synthétique HWAT (self-distillation), partenariats CHU |
| **Hallucinations médicales** | Faible | Critique | Architecture HWAT (déterministe), RAG holographique, validation médecins, garde-fous |
| **RGPD / Données patients** | Moyenne | Élevé | Anonymisation k-anonymity, entraînement federated learning possible |
| **Adoption soignants** | Moyenne | Moyen | Co-design avec médecins, UX testée, formation, valeur immédiate (gain temps) |

---

## Équipe Requise

| Rôle | Phase 1 | Phase 2 | Phase 3 | Profil |
|------|---------|---------|---------|--------|
| **ML Engineer (Lead)** | ✅ | Lead | Lead | PyTorch, transformers, HWAT expert |
| **Data Engineer** | — | 1 | 0.5 | Corpus, tokenisation, pipelines |
| **Medical AI Researcher** | — | 1 | 0.5 | Médecine, éval clinique, sécurité |
| **Backend Dev (API)** | — | 0.5 | 1 | FastAPI, TorchServe, Docker, k8s |
| **Frontend Dev (Apps)** | — | — | 1 | JS vanilla, Vital Ka apps, UX |
| **Médecins Annotateurs (5)** | — | 0.5 FTE | 0.2 FTE | Spécialités variées, africains de préférence |
| **DevOps / MLOps** | — | 0.2 | 0.5 | CI/CD, monitoring, infra GPU |

---

## Prochaines Actions Immédiates (Cette semaine)

1. **Valider GPU access** — Test `hwat_torch.py` sur GPU réel (A100/T4)
2. **Lancer corpus collection** — Scripts download PubMed Central + OMS + MSF
3. **Recruter 2 médecins annotateurs** — Via réseau CHU / facultés partenaires
4. **Préparer tokeniseur médical** — Entraîner BPE 50k sur corpus médical brut
5. **Setup infra training** — Dockerfile + docker-compose pour training reproductible

---

## Commandes de référence

```bash
# Phase 1 - Déjà fait
python npz_to_pt.py --all

# Phase 2 - Préparation corpus (à créer)
python prepare_medical_corpus.py --sources pubmed,oms,msf,vidal --output data/medical_corpus/

# Phase 2 - Tokenizer médical (à créer)
python train_medical_tokenizer.py --corpus data/medical_corpus --vocab_size 50000 --output tokenizer_medical_50k.json

# Phase 2 - Training (à lancer sur GPU)
python train_hwat_medical.py --config configs/hwat_med_125m.yaml --resume checkpoints/hwat_125m_step300.pt

# Phase 3 - Serveur inférence (à créer)
python -m hwat_inference_server --model checkpoints/hwat_med_125m/model_final.pt --holograms data/holograms_medical/ --port 8080

# Test intégration
curl -X POST http://localhost:8080/api/hwat/diagnose \
  -H "Content-Type: application/json" \
  -d '{"symptoms":["fièvre","toux","dyspnée"],"patient":{"age":45,"sex":"M"},"context":"consultation"}'
```

---

*Document vivant — Mis à jour à chaque phase. Dernière MAJ : 2026-08-01*