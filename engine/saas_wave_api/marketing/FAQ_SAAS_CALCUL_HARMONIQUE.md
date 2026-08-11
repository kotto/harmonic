# ❓ FAQ — HARMONIC COMPUTE

**Les questions qu'on nous posera — et les réponses qu'on doit donner** · Chaque réponse est alignée sur les documents fondateurs

---

## 1 · LE PRODUIT

**Q : C'est un ordinateur quantique ?**
R : Non. C'est un **émulateur harmonique** : les opérations de la cinématique quantique (superposition, opérateurs unitaires, produit scalaire, FFT, mesure par résonance), exécutées de façon **déterministe** sur du matériel classique. Même espace mathématique (ℂ⁵¹², vecteurs normalisés) — sans le hasard, sans la décohérence, sans la cryogénie.

**Q : Pourquoi « quantum-like » alors ?**
R : Parce que la structure est celle de la QM : l'état est une onde normalisée dans un espace de Hilbert, la lecture est un produit scalaire, l'évolution est unitaire. La physique harmonique démontre ce que la QM postule (voir `DOCUMENT_FONDATEUR_EMERGENCE_QUANTIQUE.md`). Nous vendons cette structure — sans le tirage.

**Q : C'est quoi les 13 primitives ?**
R : encode · decode · bind · unbind · superpose · resonate · rotate · normalize · interfere · diffract · filter · phase_shift · emerge — plus la mémoire holographique (store/query) et l'arithmétique émergente (solve). Implémentées dans `wave_lang.py`, exposées en REST.

**Q : Le déterminisme, concrètement ?**
R : Même entrée → même ψ, sur n'importe quelle machine (hash FNV-1a déterministe + φ-spacing). Un résultat d'hier se rejoue demain, à l'identique. C'est le contrat qui manque au QPU (reproductibilité nulle) et au LLM (stochasticité).

**Q : La mémoire est persistante ?**
R : Oui. La mémoire holographique H = Σ ψ_fait est une superposition — rien n'est écrasé, l'ajout coûte O(1), et l'oubli suit le noyau doré (t^−0,618). Persistance JSON, restauration déterministe.

## 2 · PERFORMANCES

**Q : Et les accélérations NP-complètes (O(1), 10⁶ PFLOPS) ?**
R : Ce sont des **projections de recherche** (simulateur HPU), documentées comme telles dans la théorie. Elles ne sont **jamais** promises en SLA. Les benchmarks exposés par le service sont les démos vérifiées : normalisation 1,0 · résonance identité 1,0 · récupération ≥ 0,7 · rotation π → −1 · solve 12×7 = 84. 37 tests verts.

**Q : C'est lent ?**
R : Une primitive = quelques microsecondes sur un CPU lambda (opérations numpy sur 512 dimensions). Le service tourne sur un VPS à ~11 €/mois.

## 3 · SECURITÉ & CONFIDENTIALITÉ

**Q : Mes données restent-elles privées ?**
R : Plan cloud : les faits stockés en mémoire sont chiffrés au repos (JSON, accès contrôlé par clé). Plan **Enterprise : on-premise** — vos données ne quittent pas votre infrastructure.

**Q : Qui voit mes requêtes ?**
R : Personne. La clé API est personnelle ; les quotas sont anonymes (usage agrégé). Pas de tracking, pas de revente de données.

**Q : Et si je dépasse mon quota ?**
R : Le service répond 429 avec la date de réinitialisation. Vous pouvez changer de plan à tout moment ; le dépassement Pro coûte 0,001 €/req.

## 4 · LA SCIENCE (les questions difficiles)

**Q : Le hasard quantique n'est-il pas prouvé ?**
R : Les corrélations de Bell sont mesurées et **non-locales** — la THU l'assume pleinement (le substrat est non-local, une onde l'est par nature). Ce que la THU conteste, c'est que le hasard soit **fondamental** : le probabilisme est la statistique d'un filtre appliqué à une onde déterministe (illustration : `theorie-harmonique/probabilisme-filtre.html`). C'est une position falsifiable, avec ses exigences E1/E2/E3.

**Q : Schrödinger est-il dérivé de l'équation mère ?**
R : Pas encore — c'est la **porte E1, ouverte et déclarée** (dans l'API elle-même, `/meta/status`). La cinématique (l'espace de Hilbert) est démontrée ; la dynamique complète reste une frontière assumée.

**Q : Les coefficients de l'équation mère sont {φ, π, e} ?**
R : Non — cette hypothèse a été **réfutée et publiée** (X1 : écart 0,707 · 0/935). Les coefficients dérivés sont cₙ = 1/Γ(n/φ+1). L'encode utilise φ pour la non-répétition (spacing), pas comme coefficient sémantique (X3 : le φ-spacing ne porte pas la sémantique — le spectre s'apprend).

**Q : C'est une secte ?**
R : C'est l'inverse d'une secte : **tout est public, reproductible, réfutable**. Chaque affirmation est une commande, chaque prédiction un dépôt daté, chaque réfutation publiée. La transparence est le produit.

## 5 · PRATIQUE

**Q : Comment je commence ?**
R : 1) `POST /v1/auth/register` avec votre email → clé `hwu_…` (plan free, 100 req/j). 2) Playground : http://localhost:8000/ . 3) SDK Python en 10 lignes. 4) Docs OpenAPI : `/docs`.

**Q : Il y a un SDK ?**
R : Oui — Python, zéro dépendance (`saas_wave_api/sdk/wave_client.py`). JS/TS : le playground contient le client fetch de référence.

**Q : La recherche académique est vraiment gratuite ?**
R : Oui — clé Enterprise (50 000 req/j) gratuite pour les universités et laboratoires, contre une citation dans les publications et les cours.

**Q : Quels sont vos tarifs ?**
R : Free 0 € (100 req/j) · Pro 29 €/mois (5 000 req/j, dépassement 0,001 €/req) · Enterprise dès 490 €/mois (50 000 req/j, on-premise, SLA 99,9 %).

**Q : Le service est-il déjà déployé ?**
R : Le produit est construit et testé (37 tests verts, smoke test de bout en bout). Le déploiement public est l'étape J-0 du plan de lancement — il se fait en une commande (`uvicorn saas_wave_api.main:app`).

---
*FAQ vivante — chaque réponse technique pointe vers un test ou un document reproductible.*
