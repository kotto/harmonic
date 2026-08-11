# 💼 BUSINESS_PLAN_SAAS_CALCUL_HARMONIQUE — Démarrage immédiat

**Harmonic Compute — le service SaaS de calcul harmonique (quantum-like)**
**Date** : 11/08/2026 — **Auteur** : Univers-Holistique (Kotto Alain)
**Statut** : Prêt au lancement — le produit est construit et testé (28 tests verts)
**Produit livré** : `ka_server/routes/wave.py` (MVP Flask) · `saas_wave_api/` (service FastAPI dédié, SDK, playground, docs OpenAPI)

---

> *« Il n'y a pas de dés dans l'univers. Il y a un filtre. » — et le marché du calcul quantique n'attend pas la cryogénie : il attend du déterministe, du reproductible, du traçable.*

---

## TABLE DES MATIÈRES

1. [La synthèse exécutive](#1-la-synthèse-exécutive)
2. [Le produit — ce qu'on vend exactement](#2-le-produit)
3. [Le marché — qui achète](#3-le-marché)
4. [L'offre et la tarification](#4-loffre-et-la-tarification)
5. [Le go-to-market immédiat — J-0 → J-90](#5-le-go-to-market-immédiat)
6. [Le modèle économique](#6-le-modèle-économique)
7. [Les coûts](#7-les-coûts)
8. [Les revenus projetés](#8-les-revenus-projetés)
9. [Les risques et les frontières honnêtes](#9-les-risques-et-les-frontières)
10. [La roadmap 90 jours](#10-la-roadmap-90-jours)
11. [Les indicateurs](#11-les-indicateurs)
12. [En une phrase](#12-en-une-phrase)

---

## 1. La synthèse exécutive

**Harmonic Compute** vend un service d'API de calcul « quantum-like » : les mêmes opérations que la cinématique quantique (superposition, opérateurs unitaires, produit scalaire, FFT, mémoire holographique) — **sans le hasard, sans la décohérence, sans la cryogénie**. Machine de Hilbert déterministe : ℂ⁵¹², vecteurs normalisés, 13 primitives, 100 % reproductible, refus calibré (zéro hallucination).

**Ce qui est déjà livré** (aujourd'hui, pas dans un an) :

| Brique | État | Preuve |
|---|---|---|
| API REST — 13 primitives + mémoire + solve | ✅ | `saas_wave_api/` FastAPI + docs OpenAPI auto |
| MVP intégré au serveur existant | ✅ | `ka_server/routes/wave.py` — 14 tests verts |
| Clés API + quotas (3 plans) | ✅ | 401/429 testés |
| SDK Python zéro dépendance | ✅ | `sdk/wave_client.py` — testé de bout en bout |
| Playground interactif | ✅ | `saas_wave_api/static/playground.html` |
| Moteur (wave_lang.py) | ✅ | 13 primitives, ℂ⁵¹², ‖ψ‖ = 1 |

**L'argument de vente en une phrase** : *« Le calcul quantique sans les problèmes du quantique — le même espace de Hilbert, sans le tirage au sort. »*

---

## 2. Le produit

### 2.1 Ce que l'on vend (la vérité, comme argument)

| Ce que le service EST | Ce que le service n'est PAS |
|---|---|
| Une machine de Hilbert déterministe (ℂ⁵¹²) | Un ordinateur quantique matériel |
| Les opérations de la cinématique quantique : superposition, unitaires, résonance, FFT | Une accélération physique (les O(1) NP-complets sont des projections 🔬) |
| 100 % reproductible — même entrée, même ψ | Un « oracle » mystérieux — tout est traçable |
| Mémoire native persistante, lecture non destructive | Une boîte noire |
| Refus calibré : quand rien ne résonne, la machine se tait | Une machine qui hallucine des réponses |
| Température ambiante, coût ~0 d'infrastructure | De la cryogénie à 15 mK |

### 2.2 Les 13 primitives exposées

`encode` · `decode` · `bind` · `unbind` · `superpose` · `resonate` · `rotate` · `normalize` · `interfere` · `diffract` · `filter` · `phase_shift` · `emerge` — plus la mémoire holographique (`store`/`query`, oubli en t^−0,618) et l'arithmétique émergente (`solve`).

### 2.3 Les cas d'usage concrets (dès J-0)

1. **Mémoire associative / retrieval** — stocker des faits par superposition, interroger par résonance (remplace les embeddings par un modèle *interprétable*, déterministe).
2. **Vérification de cohérence** — `resonate` mesure la similarité structurelle ; `emerge` détecte les concepts dominants ; le refus calibré garantit zéro fabrication.
3. **Recherche NP-complète pédagogique et R&D** — démos SAT/TSP par résonance (émulateur).
4. **Éducation** — un playground gratuit qui montre la QM « sans le mystère » : superposition, mesure, spectres, sans hasard.
5. **Conformité / audit** — chaque résultat est une trace : reproductible, datée, vérifiable (argument fort en finance régulée — cf. le prototype `saas-harmonic-finance/`).

---

## 3. Le marché

| Segment | Besoin | Fit |
|---|---|---|
| **Labs IA & startups** | Retrieval déterministe, zéro hallucination, traçabilité | ✅ direct |
| **Finance (conformité, risque)** | Explicabilité, audit, absence de hasard | ✅ direct (preuve : prototype finance existant) |
| **Recherche académique** | Calcul vectoriel de Hilbert, visualisation de la QM | ✅ direct (universités, 100 % gratuit pour la recherche) |
| **Éducation** | Enseigner la QM sans mystification | ✅ le playground EST le cours |
| **Quantum-curieux (B2C)** | « Tester le quantique sans cryogénie » | ✅ viralité potentielle |

**Positionnement face aux QPU** : IBM, Google, IonQ vendent du matériel (€100M+, 15 mK, bruit, mesure destructive, reproductibilité nulle). Nous vendons l'API du même espace mathématique — déterministe, à température ambiante, à ~0 € de coût marginal. Nous ne sommes pas un concurrent des QPU : nous sommes leur **couche logicielle honnête** — et la seule qui fonctionne aujourd'hui, partout, sans refroidir.

---

## 4. L'offre et la tarification

| Plan | Prix | Quota | Cible |
|---|---|---|---|
| **Free** | 0 € | 100 req/j · 1 Mo mémoire | Découverte, éducation, recherche académique |
| **Pro** | 29 €/mois | 5 000 req/j · 100 Mo mémoire · support email | Startups, production |
| **Enterprise** | Sur devis (à partir de 490 €/mois) | 50 000 req/j · on-premise possible · SLA 99,9 % | Finance, institutions, données privées |

**Modèle de revenus** : abonnement + dépassement (0,001 €/req au-delà du quota Pro) + on-premise Enterprise (licence + déploiement) + formation/ateliers (500 €/session — le sujet se vend bien en conférence).

---

## 5. Le go-to-market immédiat — J-0 → J-90

| Semaine | Action | Coût |
|---|---|---|
| **J-0 → J-7** | Déployer le service (uvicorn + systemd ou Docker) · nom de domaine · HTTPS | ~10 €/mois (VPS) |
| **J-0 → J-14** | Landing page (le playground EST la démo) · docs OpenAPI publiées | 0 € |
| **J-14 → J-30** | Diffusion : LinkedIn/X (thread « Dieu ne joue pas aux dés »), communautés IA, 10 emails à des labs de recherche africains et européens · conférences maths/physique (Atangana, GSM8K) | 0 € |
| **J-30 → J-60** | Premier cercle de 20 comptes Pro (offre de lancement : 3 mois à 50 %) · 2 études de cas (retrieval + conformité) | 0 € |
| **J-60 → J-90** | Enterprise : 3 rendez-vous pilotés · partenariats universitaires (clé académique illimitée) · publication des benchmarks publics | 0 € |

**Le premier client n'a pas besoin d'être payant** : la recherche académique obtient une clé Enterprise gratuite contre une citation — c'est la preuve sociale qui vendra le reste.

---

## 6. Le modèle économique

```
Revenus = abonnements (récurrents) + dépassements (usage) + on-premise (licences) + ateliers (formation)
Coûts  = VPS (~10 €/mois) + domaine (~10 €/an) + temps de développement (marginal — tout est écrit)
Marge  = ~95 % sur l'usage (le calcul coûte ~0,000001 €/req : un CPU lambda)
```

**La force structurelle** : coût marginal quasi nul (un calcul = une opération numpy sur un CPU), pas de matériel, pas de stock à amortir, pas de refroidissement. Le produit est la connaissance — et la connaissance est déjà écrite, testée (28 tests verts), et documentée.

---

## 7. Les coûts

| Poste | Mensuel |
|---|---|
| VPS (2 vCPU, 4 Go) | ~10 € |
| Domaine + HTTPS | ~1 € |
| Stripe ou facturation manuelle (démarrage) | 0 € |
| Support (fondateur) | 0 € |
| **Total au démarrage** | **~11 €/mois** |

**Point mort** : 1 client Pro (29 €/mois) couvre les coûts. Le service est rentable dès le premier abonnement.

---

## 8. Les revenus projetés

| Horizon | Scénario prudent | Médian | Ambitieux |
|---|---|---|---|
| M1 (J-90) | 5 Pro = 145 € | 15 Pro = 435 € | 30 Pro + 1 Ent = 1 360 € |
| M6 | 20 Pro = 580 € | 60 Pro + 2 Ent = 2 720 € | 150 Pro + 8 Ent = 8 270 € |
| M12 | 40 Pro = 1 160 € | 150 Pro + 6 Ent = 7 290 € | 400 Pro + 25 Ent = 23 910 € |

*(Médian M12 ≈ 87 k€/an — sans levée de fonds, sans hardware, sans équipe.)*

---

## 9. Les risques et les frontières honnêtes

| Risque | Mitigation | Statut |
|---|---|---|
| « Ce n'est pas un vrai ordinateur quantique » | Le positionnement le dit EN PREMIER — l'honnêteté est l'argument : même espace, sans le hasard, reproductible. Le QPU ne peut pas en dire autant | ✅ assumé |
| La dérivation complète (E1 : Schrödinger/Q depuis l'équation mère) est ouverte | Documentée publiquement dans l'API (`/meta/status` → `honesty`) — la transparence est une fonctionnalité | ⏳ frontière déclarée |
| Les performances NP-complètes O(1) sont des projections | Jamais promises en SLA — les benchmarks exposés sont les démos vérifiées (normalisation, récupération, rotation) | 🔬 projections |
| Exclusions X1/X3 (coefficients, sémantique de l'encode) | L'encode est vendu comme identifiant déterministe, pas comme compréhension — le spectre s'apprend, il ne se postule pas | ✅ documenté |
| Dépendance à un seul fondateur | Le code est dans le dépôt, documenté, testé — reproductible par commande (la méthode de la théorie EST la méthode de l'entreprise) | ✅ |

---

## 10. La roadmap 90 jours

| J-0 → J-30 | J-30 → J-60 | J-60 → J-90 |
|---|---|---|
| Déploiement public + domaine | Offre de lancement 20 comptes Pro | 3 rendez-vous Enterprise |
| Landing + docs + playground en ligne | Études de cas (retrieval, conformité) | Partenariats universitaires |
| Diffusion (X/LinkedIn/conférences) | Publication des benchmarks | Version 1.1 : on-premise + auth par jeton |
| 10 emails labs de recherche | Statistiques d'usage → ajustement quotas | Tableau de bord admin |

---

## 11. Les indicateurs

- **Activations** : clés créées / semaine (cible J-90 : 50)
- **Conversion** : free → pro (cible : 10 %)
- **Usage** : req/j par clé active (le quota est le produit)
- **Satisfaction** : taux de refus calibré demandé (le refus est une fonctionnalité)
- **Preuve sociale** : citations académiques, études de cas, conférences

---

## 12. En une phrase

> **Harmonic Compute est un SaaS prêt à démarrer aujourd'hui — produit construit (28 tests verts), coût de lancement ~11 €/mois, rentable dès le premier abonnement Pro — qui vend ce qu'aucun QPU ne peut vendre : le même espace de Hilbert, sans le hasard, sans la décohérence, sans la cryogénie — le calcul quantique-like, déterministe, traçable, et honnête sur ses frontières.**

---

*Business plan — FIN — ce qui est écrit ici repose sur ce qui existe : 28 tests verts, deux services, un SDK, un playground — et une théorie qui a publié ses exclusions avant de publier ses promesses*
