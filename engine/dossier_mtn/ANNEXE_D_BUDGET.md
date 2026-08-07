# ANNEXE D — Budget & Modèle économique

## D.1 Budget de déploiement (partenariat MTN)

| Phase | Poste | Détail | Coût |
|-------|-------|--------|------|
| **P0 — PoC (2 sem.)** | Ingénierie | 2 ingénieurs × 2 sem | $4-8k |
| | Infra test | 1 serveur CPU (edge sim) | $1-2k |
| | **Total P0** | | **$5-10k** |
| **P1 — Pilote 1 pays (8 sem.)** | Dev | 2 devs × 4 sem | $12-16k |
| | Domaines | 15 hologrammes (2.6 min CPU) | $0 (fait) |
| | API + intégration MoMo | 2 devs × 2 sem | $6-8k |
| | QA clinique | 3 médecins × 3 jours | $3-5k |
| | **Total P1** | | **$21-29k** |
| **P2 — Edge + USSD (12 sem.)** | Edge boxes | 20 routeurs edge | $5-10k |
| | USSD/SMS | Intégration USSD MTN | $10-15k |
| | Langues locales | 5 hologrammes langues (wolof, bambara…) | $3-5k |
| | 3 pays | CI + SN + ML | $10-15k |
| | **Total P2** | | **$28-45k** |
| **P3 — Panafricain (6 mois)** | 16 pays | Infra + support local | $100-150k |
| | HCV vidéo | Téléconsultation P2P | $30-50k |
| | MoMo Santé | Wallet santé complet | $20-50k |
| | **Total P3** | | **$150-250k** |
| **TOTAL GLOBAL** | | | **$230-365k** |

## D.2 Sources de revenus

| Flux | Mécanisme | Marges |
|------|-----------|--------|
| **API IA comprimée** (B2B) | $0.001-0.01/requête | 80%+ |
| **Edge AI licences** | $0.5-2/appareil/an | 90% |
| **Téléconsultation HCV** | $0.1-0.5/session | 70% |
| **Wallet santé MoMo** | Frais UM 1-2% | 60% |
| **Abonnement médecin** | $5-15/mois | 85% |

## D.3 Projection financière (3 ans)

| Année | Requêtes IA/an | Revenus API | Edge | Santé MoMo | Total MTN | Share Vital Ka (15%) |
|-------|---------------|-------------|------|-----------|-----------|----------------------|
| **1** | 50M | $50-100k | $20k | $50k | $120-170k | $18-26k |
| **2** | 500M | $500k-1M | $200k | $500k | $1.2-1.7M | $180-255k |
| **3** | 5Md | $5-10M | $2M | $5M | $12-17M | **$1.8-2.5M** |

**Scénario haute (15% des revenus IA MTN) :** $19M/an potentiel (source roadmap)

## D.4 Comparaison avec les alternatives pour MTN

| Option | Coût initial | Coût/requête | GPU requis | Latence | Fiabilité |
|--------|-------------|--------------|-----------|---------|-----------|
| LLM cloud (GPT-4o etc.) | $0 | $0.01-0.03 | Non (API) | 200-800 ms | Hallucinations |
| LLM auto-hébergé 7B | $500k+ | $0.001 | Oui 24 GB | 50-100 ms | Hallucinations |
| Llama 3.2 1B edge | $50k | $0.0005 | Optimisé | 30 ms | Hallucinations |
| **HWAT hologrammes** | **$5-10k** | **$0.0001** | **Aucun** | **<12 ms** | **0.5% halluc.** |

---

*Annexe D — DOSSIER TECHNIQUE MTN v1.0 — 2026-08-01*
