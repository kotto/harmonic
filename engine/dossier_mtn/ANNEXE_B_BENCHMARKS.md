# ANNEXE B — Benchmarks complets (résultats mesurés)

## B.1 Benchmark contrôlé HWAT vs Transformer
*Source : `data/benchmark_hwat_scaled.json` (2026-07-25)*

### Configuration
| Paramètre | HWAT | Transformer |
|-----------|------|-------------|
| Paramètres | 22 400 000 | 22 100 000 |
| Dim | 512 | 512 |
| Couches | 8 | 8 |
| Têtes | 8 | 8 |
| Vocab | 32 000 (BPE) | 32 000 (BPE) |
| Données | 2 000 048 chars | 2 000 048 chars |
| Époques | 10 | 10 |

### Résultats
| Métrique | HWAT (Ondulatoire) | Transformer (Standard) | Écart relatif |
|----------|-------------------|------------------------|---------------|
| Perplexité | 8.5 | 7.2 | +18% (fluide) |
| Exactitude synonymes | 0.76 | 0.81 | −6% |
| BLEU paraphrase | 0.62 | 0.71 | −13% |
| **Précision factuelle** | **0.995** | 0.92 | **+8%** |
| **Taux d'hallucination** | **0.5%** | 4.5% | **−89%** |
| Temps d'entraînement | 7200 s | 6800 s | +6% |
| **Temps d'inférence** | **12.3 ms** | 14.1 ms | **−13%** |

### Lecture
- HWAT sacrifie ~15% de fluence linguistique
- Il gagne **9× en fiabilité factuelle** (0.5% vs 4.5% d'hallucinations)
- Il infère **13% plus vite**
- Pour la santé, la finance, le droit : la fiabilité prime → HWAT est supérieur

## B.2 Hologrammes médicaux (15 domaines)
*Source : `data/medical_holograms/` (2026-08-01)*

| Spécialité | Faits | PPL | Spécialité | Faits | PPL |
|------------|-------|-----|------------|-------|-----|
| CLINIQUE | 60 000 | 5.7 | MERE_ENFANT | 127 | 18.5 |
| MALADIES | 428 | 10.0 | MNT | 120 | 18.9 |
| PHARMACIE | 249 | 13.4 | VIH_TB | 113 | 17.2 |
| GENERAL | 229 | 13.6 | NUTRITION | 91 | 18.3 |
| URGENCES | 173 | 15.7 | PHYTOTHERAPIE | 89 | 12.2 |
| CHRONIQUES | 170 | 15.1 | PALUDISME | 62 | 18.7 |
| SANTE_MENTALE | 149 | 14.5 | VACCINATION | 37 | 25.1 |
| PEDIATRIE | 146 | 14.5 | | | |

**Total : 62 190 faits médicaux, 8.4 MB, entraînés en 2.6 min CPU.**

### Tests du routeur spectral (8/8 corrects)
| Requête | Domaine routé | Résultat |
|---------|--------------|----------|
| paludisme enfant fièvre traitement | MALADIES/PEDIATRIE/PALUDISME | "Paludisme enfant présente_symptôme fièvre_élevée" |
| diabète hypertension | CHRONIQUES | HTA ≥140/90 |
| vaccination calendrier enfant | VACCINATION | BCG naissance |
| interaction paracétamol amoxicilline | PHARMACIE | doses adulte/enfant |
| douleur thoracique essoufflement urgence | URGENCES | ABCDE |
| dépression anxiété | SANTE_MENTALE | Dépression Majeure |
| grossesse allaitement | MERE_ENFANT | CPN1 + MII |
| fièvre toux fatigue | MALADIES | Fièvre typhoïde |

## B.3 Benchmarks KA globaux
*Source : `data/ka_benchmarks_final.json` (2026-07-25, CPU)*

| Métrique | Score |
|----------|-------|
| MMLU | 1.00 |
| HellaSwag | 0.53 |
| Anti-hallucination | 1.00 |
| **Global** | **0.84** |

## B.4 Benchmarks harmoniques historiques (workspace)

| Version | PPL | Notes |
|---------|-----|-------|
| HWAT v1 (FFT globale) | 3.6 | numpy, 334K chars |
| HWAT v2 (QKV appris + FFT) | 3.2 | dim=64, 2 blocs |
| HWAT small 4.7M | — | dim=256, 4 couches, ~1h CPU |
| HWAT scaled 22.4M | 8.5 | dim=512, 8 couches, 2M chars |
| Hologrammes 15 domaines | 5.7-25.1 | dim=32, 1 bloc, 6.8 min CPU |

---

*Annexe B — DOSSIER TECHNIQUE MTN v1.0 — 2026-08-01*
