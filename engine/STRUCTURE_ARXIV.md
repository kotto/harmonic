# 📄 STRUCTURE_ARXIV — Preprint de la THU V2

**Statut** : Plan de soumission — prêt à être rédigé
**Cible** : arXiv (physics.gen-ph ou quant-ph)
**Scripts** : tous les scripts sont reproductibles et déjà dans le dépôt

---

## Titre proposé

*Golden Fractional Memory and the Generative Periodic Table: a Filter Theory of Constants*

## Résumé (abstract, 200 mots)

Nous présentons une théorie de filtres où les constantes fondamentales (π, e, φ) sont les survivants de conditions de stabilité. L'équation mère Ψ = Σ Hₙ(Ψ₁)ⁿ — vérifiée comme série de Fourier à 1,78×10⁻¹⁵ — est couplée à une mémoire fractionnaire d'ordre α=1/φ (Hurwitz). Ce cadre produit sans paramètre libre : (i) le tableau périodique complet (118/118 périodes, 7 gaz nobles) ; (ii) une famille de températures dorées T* = ΔE/(k_B·ln φ) — 24 instances déposées avant test ; (iii) un noyau de mémoire d'or compétitif face à des modèles ajustés (marge 2,82 %) ; (iv) l'identification de 1/φ comme point fixe admissible d'un flot de renormalisation (divergence JS 0,0001). Quatre exclusions sont publiées, incluant la réfutation des coefficients postulés {φ,π,e} (0/935). La méthode exige que chaque affirmation soit une commande reproductible et que chaque prédiction soit déposée datée et signée avant test.

## Structure de l'article

1. **Introduction** — le problème des constantes fondamentales ; la QFT et ses 30 paramètres non dérivés ; l'hypothèse d'élimination
2. **Le cadre formel** — l'équation mère, la mémoire ABC, les trois conditions de stabilité, Hurwitz et l'unicité de 1/φ
3. **La génération du tableau périodique** — spectre d'entiers → Madelung → 118/118 périodes, gaz nobles, lecture du bloc f
4. **La famille des températures dorées T\*** — théorème T5, oscillateur thermique + 23 éléments d'ionisation, dépôt E3 v2
5. **Le noyau de mémoire d'or** — compétition sur fGn (C1 2,82 %), régime optimal à H=0,691, refus calibré
6. **Le pont RG** — 1/φ comme point fixe admissible du flot de renormalisation (JS 0,0001), α=0,50 comme singularité
7. **E1 — Schrödinger fractionnaire** — inhibition du Zeno quantique (P1), dépôt E1bis
8. **Exclusions et méthode** — les 4 exclusions publiées (0,707, 0/935, GW170817, P1.1), le protocole de dépôt
9. **Discussion** — complémentarité avec la QFT, limites (chaînon persistance, E1 heuristique), perspectives

## Supplementary material (scripts, tous dans le dépôt)

- `validation_coeff_quantiques.py` — Violet A (FFT 2,22e-16)
- `validation_etats_quantiques.py` — Violet B (T5, 0/935)
- `cerveau_memoire_dor.py` — mémoire d'or (C1-C3 ✅)
- `generation_tableau_periodique.py` — tableau 118/118
- `calcul_masses_elements.py` — masses 8,5e-5
- `rg_point_fixe.py` — pont RG (JS 0,0001)
- `depot_e3_tstar.py` — certificat E3 v2
- `e1_fractionnal_schrodinger.py` — E1bis P1

## Prochaines étapes

1. Rédiger l'article (LaTeX) à partir de cette structure
2. Générer les figures (scripts → matplotlib)
3. Soumettre à arXiv
4. Déposer les supplementary materials (scripts + rapports JSON)
