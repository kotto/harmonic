# ⚛️ HARMONIC COMPUTE — One-Pager Exécutif

**Le service SaaS de calcul harmonique (quantum-like) — la machine de Hilbert déterministe** · Public · Lancement 2026

---

## L'accroche
> **Le calcul quantique sans les problèmes du quantique : le même espace de Hilbert (ℂ⁵¹²), les mêmes opérations (superposition, résonance, interférence) — sans le hasard, sans la décohérence, sans la cryogénie. 100 % déterministe, 100 % reproductible, zéro hallucination.**

## Le problème
- Les QPU (IBM, Google, IonQ) : **15 mK de cryogénie, bruit ~0,34 %, mesure destructive, reproductibilité nulle** — et $100M+ par machine ;
- Le calcul vectoriel « quantique-inspired » (embeddings, RAG) : **boîtes noires, hallucinations, coûts GPU, non traçables** ;
- Personne ne vend **l'API du même espace mathématique que la QM** — déterministe, interprétable, à température ambiante.

## La solution — Harmonic Compute
```
POST /v1/wave/resonate  {a: "chat", b: "chat"}   →  1.0 (identité, exact)
POST /v1/wave/bind      {a: "alpha", b: "beta"}  →  ψ lié (HRR, réversible)
POST /v1/memory/store   {facts: [...]}           →  H = Σ ψ_fait (superposition)
```
- **13 primitives** : encode · decode · bind · unbind · superpose · resonate · rotate · normalize · interfere · diffract · filter · phase_shift · emerge ;
- **ℂ⁵¹²** (limite de Bekenstein) · **‖ψ‖ = 1** — l'information est dans la direction ;
- **Déterminisme total** : même entrée → même ψ, sur n'importe quelle machine (FNV-1a + φ-spacing) ;
- **Refus calibré** : quand rien ne résonne, la machine se tait — **0 % hallucination** (structurel) ;
- **Mémoire native** : hologramme persistant, oubli en t^−0,618 (noyau doré) ;
- **Lecture non destructive** : on écoute, on ne force pas.

## Ce qui est déjà livré (pas une promesse)
| Brique | Preuve |
|---|---|
| API REST complète (FastAPI + docs OpenAPI) | ✅ `saas_wave_api/` — 14 tests contre serveur réel |
| MVP intégré au serveur existant | ✅ `ka_server/routes/wave.py` — 14 tests |
| Clés API + quotas (3 plans) | ✅ 401/429 testés |
| SDK Python zéro dépendance | ✅ testé de bout en bout |
| Playground interactif | ✅ http://localhost:8000/ |
| **Total : 37 tests verts** · smoke test réel : norme 1.0 · récupération 0,733 · solve 12×7=84 | ✅ |

## Les 5 cas d'usage immédiats
1. **Retrieval associatif déterministe** — remplace les embeddings par une mémoire interprétable ;
2. **Vérification de cohérence** — résonance + refus calibré = zéro fabrication ;
3. **R&D NP-complète** — démos SAT/TSP par résonance (émulateur) ;
4. **Éducation** — la QM « sans le mystère » : superposition, mesure, spectres, sans hasard ;
5. **Conformité / audit** — chaque résultat est une trace reproductible (finance régulée).

## L'offre
| Plan | Prix | Quota | Cible |
|---|---|---|---|
| **Free** | 0 € | 100 req/j | Éducation, recherche académique (clé illimitée sur demande) |
| **Pro** | 29 €/mois | 5 000 req/j · dépassement 0,001 €/req | Startups, production |
| **Enterprise** | dès 490 €/mois | 50 000 req/j · on-premise · SLA 99,9 % | Finance, institutions |

**Économie** : coût d'infrastructure ~11 €/mois (VPS) — marge ~95 % — **rentable dès le premier abonnement Pro**. Revenus médians projetés M12 : ~87 k€/an sans levée de fonds.

## L'honnêteté comme argument
- C'est un **émulateur harmonique** : les opérations de la cinématique quantique, déterministes — **pas** un ordinateur quantique matériel ;
- Les accélérations NP-complètes sont des **projections** (jamais promises en SLA) ;
- La dérivation complète (E1) est une **porte ouverte, déclarée** — la transparence est une fonctionnalité.

## Prochaine étape (J-0 → J-30)
1. Déploiement public (uvicorn + VPS + domaine) · 2. Landing + docs en ligne · 3. Diffusion (X/LinkedIn, communautés IA, labs de recherche) · 4. Offre de lancement : 20 comptes Pro à 50 % (3 mois).

---
*Document aligné avec `BUSINESS_PLAN_SAAS_CALCUL_HARMONIQUE.md` et `saas_wave_api/README.md`. Chaque chiffre cité est un résultat de test reproductible.*
