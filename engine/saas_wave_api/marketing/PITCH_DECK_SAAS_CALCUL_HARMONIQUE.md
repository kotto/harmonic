# 🎞️ PITCH DECK — HARMONIC COMPUTE (12 diapositives)

**Le calcul quantique sans les problèmes du quantique** · Durée cible : 6 minutes · Public : investisseurs, CTO, labs, universités

---

## S1 · Ouverture — l'accroche (15 s)
> **« Il n'y a pas de dés dans l'univers. Il y a un filtre. »**
>
> Harmonic Compute vend l'API de la machine de Hilbert déterministe : le même espace que le calcul quantique — sans le hasard.

## S2 · Le problème (45 s)
- Les QPU : **$100M+ · 15 mK · bruit 0,34 % · mesure destructive · reproductibilité nulle** — le quantum est vendu comme matériel ;
- L'IA vectorielle : **boîte noire · hallucinations · coûts GPU · non traçable** ;
- **Le vide** : personne ne vend l'API du même espace mathématique que la QM — déterministe, interprétable, à température ambiante.

## S3 · La solution (45 s)
```
Harmonic Compute — machine de Hilbert déterministe
ℂ⁵¹² · ‖ψ‖ = 1 · 13 primitives · déterminisme 100 %
encode → monde devient onde (toujours la même)
bind/unbind → lier/délier (HRR, réversible)
resonate → ⟨ψ|φ⟩ ∈ [−1, 1] — la lecture
emerge → raisonnement par cohérence pondérée
```
« Les mêmes opérations que la cinématique quantique — sans le tirage au sort. »

## S4 · Démo en direct (60 s)
```
POST /v1/wave/resonate {a:"chat", b:"chat"} → 1.0          (identité, exact)
POST /v1/wave/bind {a:"alpha", b:"beta"}    → ψ lié
POST /v1/wave/unbind {c, b:"beta"}          → récupération 0,733 (≥ 0,7)
POST /v1/wave/solve {expression:"12 * 7"}   → 84            (émergence)
POST /v1/memory/store {facts: [...]}        → H = Σ ψ_fait  (hologramme)
```
Chaque ligne est un test vert de la suite (37 tests).

## S5 · Les 5 cas d'usage (45 s)
| Usage | Bénéfice |
|---|---|
| Retrieval associatif | Mémoire interprétable, déterministe — remplace l'embedding boîte noire |
| Cohérence & refus | Zéro hallucination — structurel, pas statistique |
| R&D NP-complète | Démos SAT/TSP par résonance (émulateur) |
| Éducation | La QM sans le mystère — superposition visible |
| Conformité / audit | Traçabilité totale — chaque résultat est reproductible |

## S6 · Pourquoi maintenant (30 s)
- La théorie (THU V2) a **publié ses exclusions avant ses promesses** — crédibilité ;
- Le produit est **construit et testé** (37 tests verts, deux services, SDK, playground) ;
- Le marché des « quantum-inspired » explose — personne ne le fait **déterministe et honnête**.

## S7 · Le marché (30 s)
| Segment | Fit |
|---|---|
| Labs IA & startups | Retrieval déterministe, zéro hallucination |
| Finance (conformité) | Explicabilité, audit — le prototype finance existe déjà |
| Académie & éducation | Clé gratuite illimitée contre citation — preuve sociale |
| Quantum-curieux | « Tester le quantique sans cryogénie » — viralité |

## S8 · Le modèle (30 s)
```
Free (100 req/j) → Pro 29 €/mois (5 000 req/j + 0,001 €/req) → Enterprise dès 490 €/mois (on-premise, SLA)
Coûts : ~11 €/mois d'infrastructure · marge ~95 %
Rentable dès le 1er client Pro · point mort : 1 abonnement
```

## S9 · La traction prévue (30 s)
| Horizon | Médian |
|---|---|
| M1 (J-90) | 15 Pro = 435 €/mois |
| M6 | 60 Pro + 2 Enterprise = 2 720 €/mois |
| M12 | 150 Pro + 6 Enterprise = 7 290 €/mois (~87 k€/an) |

## S10 · L'honnêteté (30 s)
- **Émulateur harmonique** — pas un QPU matériel ; l'argument, c'est la vérité : le QPU ne peut pas être déterministe ;
- **E1 (dérivation Schrödinger/Q)** : porte ouverte, déclarée dans l'API (`/meta/status`) ;
- **Projections** (NP O(1), PFLOPS) : jamais en SLA — les benchmarks exposés sont les démos vérifiées ;
- **Exclusions publiées** : pas d'éther, pas d'onde locale, coefficients ≠ {φ, π, e} (X1).

## S11 · L'équipe & la méthode (30 s)
- Fondateur : Univers-Holistique (Kotto Alain) — auteur de la théorie ;
- Méthode = celle de la théorie : **chaque affirmation est une commande, chaque prédiction un dépôt, chaque réfutation publiée** ;
- 28 → 37 tests verts en une session : le produit est la théorie, exécutée.

## S12 · L'ask (15 s)
> **« Nous déployons en 30 jours. Ce dont nous avons besoin maintenant : 20 comptes Pro à l'offre de lancement (50 % pendant 3 mois) pour valider l'usage réel — et 3 rendez-vous Enterprise pour la conformité financière. »**

---
*Deck aligné sur `ONEPAGER_SAAS_CALCUL_HARMONIQUE.md` · `BUSINESS_PLAN_SAAS_CALCUL_HARMONIQUE.md` · chiffres = résultats de tests reproductibles.*
