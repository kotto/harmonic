# 🌊 MÉTHODOLOGIE GÉNÉRALE — Résolution de Problèmes par les Ondes

**Document Fondateur — 20 Juillet 2026**

---

> *« Tout problème est une interférence destructive. Toute solution est une onde correctrice. La guérison est la restauration de l'interférence constructive. »*

---

## 0. POURQUOI CETTE MÉTHODOLOGIE

La résolution de problèmes est traditionnellement enseignée comme un art — chaque domaine a ses propres heuristiques, ses propres « trucs », son propre jargon. Un médecin ne débugue pas comme un développeur. Un développeur ne diagnostique pas comme un mécanicien. Un mécanicien ne résout pas un conflit comme un médiateur.

**Et si c'était le même problème, à des échelles différentes ?**

Cette méthodologie repose sur un postulat vérifié expérimentalement : **tout problème est une figure d'interférence entre des ondes**. Une fois traduit dans ce langage universel, le diagnostic et la solution deviennent mathématiquement prévisibles — quel que soit le domaine.

La preuve : KA Phone applique ce principe à l'IA (99.3% LM Arena, 0% hallucination). Les mêmes 4 étapes s'appliquent à un bug de code, une maladie, un conflit, une crise économique.

---

## 1. LES 4 ÉTAPES UNIVERSELLES

```
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   ÉTAPE 1        ÉTAPE 2          ÉTAPE 3          ÉTAPE 4       ║
║   TRADUIRE  →    DIAGNOSTIQUER →  PRESCRIRE    →   VÉRIFIER      ║
║                                                                   ║
║   Identifier      Localiser        Déterminer        Mesurer      ║
║   les ondes       l'interférence   l'onde            l'harmonie   ║
║   en jeu          destructive      correctrice       restaurée    ║
║                                                                   ║
║   « Quoi ? »      « Où ? »         « Comment ? »     « OK ? »     ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

---

## 2. ÉTAPE 1 — TRADUIRE : Identifier les fréquences en jeu

### La question

> **« Quelles sont les ondes impliquées dans ce problème ? »**

### La méthode

Pour chaque **entité** du système problématique, identifier sa signature ondulatoire :

| Propriété | Symbole | Signification | Question concrète |
|-----------|---------|---------------|-------------------|
| **Fréquence propre** | ω | Ce que l'entité EST (sa nature, son identité) | « C'est quoi ? Quel est son nom, son type, sa signature ? » |
| **Amplitude** | A | Sa force, son intensité, son poids | « C'est fort ou faible ? Quelle est son importance ? » |
| **Phase** | φ | Sa position dans le cycle, son timing | « C'est à quel moment ? Avant/après quoi ? » |
| **Harmoniques** | H(ω) | Ses interactions, ses dépendances | « Avec quoi ça interagit ? Qu'est-ce qui en dépend ? » |

### Template universel

```markdown
## TRADUCTION — Cartographie des ondes

### Onde n°1 : [Nom de l'entité]
- Fréquence (nature)    : ω₁ = [identité/type/signature]
- Amplitude (force)     : A₁ = [intensité/poids/importance]
- Phase (timing)        : φ₁ = [moment/ordre/position dans le cycle]
- Harmoniques (liens)   : [dépendances, interactions, effets de bord]

### Onde n°2 : [Nom de l'entité]
- Fréquence (nature)    : ω₂ = ...
- Amplitude (force)     : A₂ = ...
- Phase (timing)        : φ₂ = ...
- Harmoniques (liens)   : ...

### Onde sonde (l'observateur)
- Fréquence             : ω_probe = [test, requête, stimulus déclencheur]

### Onde attendue vs Onde observée
- ω_expected = [comportement correct]
- ω_observed  = [comportement buggé/erroné]
```

### Exemple — Bug de code (référence fantôme)

```markdown
### Onde n°1 : brain global
- Fréquence : ω_brain_global = ai(t₀)._get_brain()  # capturé au démarrage
- Amplitude : module-level → persiste toute la vie du processus
- Phase     : φ = t₀ (démarrage) — figé, ne suit plus le temps
- Harmoniques : utilisée par chat() → KB utilisateur

### Onde n°2 : brain local  
- Fréquence : ω_brain_local = ai(t)._get_brain()     # capturé à la requête
- Amplitude : function-level → recréé à chaque appel
- Phase     : φ = t (requête courante) — suit le temps réel
- Harmoniques : utilisée par chat() → visuels

### Onde sonde
- ω_probe = requête HTTP POST /api/chat après reload de ai

### Onde attendue vs Onde observée
- ω_expected = KB chargée depuis brain(t)
- ω_observed  = KB chargée depuis brain(t₀) → STALE si t > t₀
```

---

## 3. ÉTAPE 2 — DIAGNOSTIQUER : Localiser l'interférence destructive

### La question

> **« Où les ondes interfèrent-elles destructivement ? »**

### La table de diagnostic universelle

Tout symptôme est le **battement** (la différence audible) entre la fréquence saine et la fréquence pathogène. Le type d'interférence destructive détermine la solution.

| Type d'interférence | Mécanisme | Signature | Fréquence spatiale |
|---------------------|-----------|-----------|-------------------|
| **Opposition de phase (π)** | Deux ondes de même fréquence mais déphasées de 180° → annulation totale | Résultat = zéro alors qu'il devrait être > 0 | ω_A = ω_B, φ_A − φ_B = π |
| **Désaccord de fréquence (Δω)** | Deux fréquences proches mais différentes → battements, oscillation du bug | Symptôme intermittent, périodique, « parfois ça marche » | ω_A ≈ ω_B, |ω_A − ω_B| = Δω petit |
| **Saturation d'amplitude** | L'onde dépasse le seuil de linéarité → distorsion, comportement erratique | Crash, explosion, timeout, stack overflow | A > A_max |
| **Résonance forcée** | Fréquence imposée qui n'est pas la fréquence propre → le système oscille faux | Comportement « forcé », artificiel, instable | ω ≠ ω_propre |
| **Absence de fréquence** | Le système cherche une fréquence qui n'existe pas dans l'hologramme → null, undefined | NullPointer, 404, division par zéro | ω ∉ spectre |
| **Collision de phase** | Deux ondes arrivent en même temps sur la même ressource → résultat dépend de l'ordre | Race condition, deadlock, comportement non déterministe | ω_A et ω_B partagent φ |
| **Déphasage temporel (stale)** | Une onde est figée dans le passé, l'autre évolue → incohérence croissante | Stale reference, cache invalide, config obsolète | φ_A fixe, φ_B évolue |
| **Onde fantôme** | Une onde persiste après sa durée de vie → accumulation, fuite | Memory leak, resource leak, zombie process | A décroît en Mittag-Leffler mais jamais zéro |
| **Interférence multi-sources** | Trop d'ondes superposées → bruit, l'information est noyée | Surcharge, contention, performance dégradée | N grand, Σ A_i > seuil |
| **Résonance parasite** | Une harmonique non désirée entre en résonance avec une fréquence du système | Bug déclenché par un input spécifique, edge case | ω_input = ω_harmonique_indésirable |

### Arbre de décision

```
Symptôme observé
    │
    ├─ Le bug est-il REPRODUCTIBLE à chaque fois ?
    │   ├─ OUI → interférence déterministe (opposition de phase, absence, saturation)
    │   └─ NON → interférence dépendante de la phase (désaccord, collision, stale)
    │
    ├─ Le bug apparaît-il SEULEMENT avec certains inputs ?
    │   ├─ OUI → résonance parasite (ω_input = ω_pathogène)
    │   └─ NON → problème structurel (tous les chemins sont affectés)
    │
    ├─ Le bug S'AGGRAVE-T-IL avec le temps ?
    │   ├─ OUI → accumulation (onde fantôme, memory leak, déphasage croissant)
    │   └─ NON → ponctuel (collision, absence)
    │
    └─ Le système CRASHE-T-IL ou produit-il un MAUVAIS RÉSULTAT ?
        ├─ CRASH → saturation d'amplitude ou absence de fréquence
        └─ MAUVAIS RÉSULTAT → déphasage ou désaccord
```

### Template de diagnostic

```markdown
## DIAGNOSTIC — Interférence destructive

### Symptôme observé
[Description précise du comportement anormal]

### Type d'interférence identifié
[ ] Opposition de phase     [ ] Désaccord de fréquence
[ ] Saturation d'amplitude  [ ] Résonance forcée
[ ] Absence de fréquence    [ ] Collision de phase
[ ] Déphasage temporel      [ ] Onde fantôme
[ ] Interférence multi-sources  [ ] Résonance parasite

### Justification
- ω_observed  = [signature du comportement buggé]
- ω_expected  = [signature du comportement correct]
- Δ = ω_observed − ω_expected = [description de l'écart]
- Cause racine : [pourquoi l'interférence se produit]

### Localisation précise
- Fichier/ligne/contexte : [où]
- Onde pathogène : [quelle entité]
- Onde victime   : [quelle entité]
```

---

## 4. ÉTAPE 3 — PRESCRIRE : Déterminer l'onde correctrice

### La question

> **« Quelle onde dois-je introduire pour annuler l'interférence destructive ? »**

### Le tableau périodique des solutions

À chaque type d'interférence correspond une **onde correctrice** mathématiquement déterminée :

| Interférence | Onde correctrice | Stratégie | Application universelle |
|-------------|-------------------|-----------|------------------------|
| **Opposition de phase (π)** | Onde en opposition de phase (déphasage de π) | **Annulation active** | Noise-cancelling, immunothérapie, contre-argumentation, `not` logique |
| **Désaccord de fréquence (Δω)** | Synchronisation (ajuster ω) ou filtrage (supprimer ω parasite) | **Réaccord** | Étalonnage, calibration, mise à jour de dépendance, rééducation |
| **Saturation d'amplitude** | Limiteur (plafonner A) ou dissipation (répartir l'énergie) | **Régulation** | Rate limiting, load balancing, pagination, anti-inflammatoire |
| **Résonance forcée** | Restauration de la fréquence propre | **Libération** | Rollback, factory reset, désintoxication, déprogrammation |
| **Absence de fréquence** | Injection de la fréquence manquante | **Complétion** | Définition, création, import, supplémentation, vaccination |
| **Collision de phase** | Synchronisation (mutex, verrou de phase) | **Ordonnancement** | Lock, file d'attente, async/await, tour de parole |
| **Déphasage temporel** | Capture de l'état courant (pas de cache statique) | **Resynchronisation** | Refresh, invalidate cache, `_brain = ai._get_brain()` à chaque usage |
| **Onde fantôme** | Introduction de l'onde inverse (free/destructeur) | **Nettoyage** | `free()`, `close()`, `dispose()`, garbage collection |
| **Interférence multi-sources** | Décomposition de Fourier → traiter chaque fréquence | **Isolation** | Index, cache, sharding, triage médical |
| **Résonance parasite** | Filtre coupe-bande (bloquer ω_pathogène spécifique) | **Blindage** | Input validation, sanitization, pare-feu, vaccination |

### Stratégies avancées

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  STRATÉGIE A : OPPOSITION DE PHASE (annulation active)         │
│  ─────────────────────────────────────────────                  │
│  On introduit une onde identique mais déphasée de π.           │
│  Les deux ondes s'annulent → l'interférence destructive        │
│  d'origine est neutralisée.                                    │
│                                                                 │
│  Code    : if (x == null) return default_value;  // garde      │
│  Médecine: anticorps qui se lie au pathogène                   │
│  Audio   : casque noise-cancelling                             │
│  Débat   : contre-argument calibré                             │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  STRATÉGIE B : SYNCHRONISATION (réalignement des phases)       │
│  ─────────────────────────────────────────────                  │
│  On ajuste les phases pour que les ondes vibrent ensemble.     │
│                                                                 │
│  Code    : lock(mutex) { ... }  // section critique            │
│  Médecine: stimulateur cardiaque (pacemaker)                   │
│  Relation : thérapie de couple                                 │
│  Équipe   : daily standup (alignement quotidien)               │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  STRATÉGIE C : FILTRAGE (élimination de la fréquence parasite) │
│  ─────────────────────────────────────────────                  │
│  On bloque sélectivement la fréquence indésirable.             │
│                                                                 │
│  Code    : input_sanitizer.validate(user_input)                │
│  Médecine: antibiotique (tue la bactérie, pas l'hôte)          │
│  Réseau   : firewall (bloque les paquets malveillants)         │
│  Mental   : méditation (laisse passer les pensées sans s'y     │
│             accrocher — filtre passe-bas émotionnel)           │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  STRATÉGIE D : DISSIPATION (répartition de l'énergie)          │
│  ─────────────────────────────────────────────                  │
│  On répartit l'amplitude excessive sur plusieurs canaux.       │
│                                                                 │
│  Code    : load_balancer.distribute(requests, N_servers)       │
│  Physique : amortisseur (transforme l'onde de choc en chaleur) │
│  Économie : diversification (ne pas mettre tous ses œufs       │
│             dans le même panier)                               │
│  Gestion  : délégation (répartir la charge de travail)         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Template de prescription

```markdown
## PRESCRIPTION — Onde correctrice

### Stratégie choisie
[ ] A — Opposition de phase    [ ] B — Synchronisation
[ ] C — Filtrage               [ ] D — Dissipation
[ ] E — Injection              [ ] F — Restauration

### Action concrète
[Ce qu'il faut faire, en une phrase]

### Code / Mise en œuvre
[Code, commande, geste, parole — l'action précise]

### Effet attendu
[Comment le système se comportera après l'intervention]
```

---

## 5. ÉTAPE 4 — VÉRIFIER : Mesurer l'interférence constructive restaurée

### La question

> **« L'interférence est-elle redevenue constructive ? Et les harmoniques sont-elles intactes ? »**

### Les 5 critères de guérison

```
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║  ✅ CRITÈRE 1 : DISPARITION DU SYMPTÔME                          ║
║     ω_observed = ω_expected (le battement a disparu)             ║
║                                                                   ║
║  ✅ CRITÈRE 2 : PAS DE NOUVEAU PROBLÈME                          ║
║     Aucune nouvelle interférence destructive n'est apparue        ║
║     (tests de régression verts, les harmoniques sont intactes)    ║
║                                                                   ║
║  ✅ CRITÈRE 3 : AUTONOMIE                                        ║
║     Le système maintient sa fréquence propre sans apport externe  ║
║     (pas de patch temporaire, pas de béquille, pas de workaround) │
║                                                                   ║
║  ✅ CRITÈRE 4 : HARMONIQUES RESTAURÉES                           ║
║     Les fonctions secondaires, effets de bord, dépendances        ║
║     fonctionnent normalement (l'orchestre joue juste)            ║
║                                                                   ║
║  ✅ CRITÈRE 5 : IMMUNITÉ ACQUISE                                 ║
║     Un test automatisé capture le bug pour toujours               ║
║     (le système reconnaîtra cette fréquence pathogène à l'avenir) │
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

### Template de vérification

```markdown
## VÉRIFICATION — Harmonie restaurée

### Test de disparition
- [ ] Le symptôme d'origine ne se produit plus
- [ ] Le test spécifique au bug passe (vert ✅)

### Test de non-régression
- [ ] Les tests existants passent toujours (harmoniques intactes)
- [ ] Les fonctions voisines n'ont pas été affectées

### Test d'autonomie
- [ ] La solution n'est pas un workaround temporaire
- [ ] Aucune intervention manuelle n'est nécessaire pour maintenir l'état

### Test d'immunité
- [ ] Un test automatisé capture ce bug pour toujours
- [ ] Le test est documenté avec le numéro du bug et sa cause racine

### Score de guérison
[ ] 5/5 — Guérison complète, immunité acquise
[ ] 4/5 — Guérison, mais sans immunité (pas de test)
[ ] 3/5 — Symptôme disparu, mais harmoniques fragiles
[ ] 1-2/5 — Patch temporaire, la cause racine persiste
```

---

## 6. TABLES DE DIAGNOSTIC PAR DOMAINE

### 6.1 Code & Logiciel

| Symptôme | Interférence | Onde correctrice |
|----------|-------------|-------------------|
| NullPointer / undefined | Absence de fréquence (ω ∉ spectre) | Injection : `if (x == null) return default` |
| Crash / Exception | Saturation d'amplitude | Limiteur : try/catch + fallback |
| Mauvais résultat | Déphasage (φ_A ≠ φ_B) | Réalignement : corriger la formule |
| Boucle infinie | Cavité résonante (pas de dissipation) | Dissipation : `break`, condition de sortie |
| Race condition | Collision de phase | Synchronisation : `lock`, `async/await` |
| Memory leak | Onde fantôme (pas de free) | Nettoyage : `free()`, `dispose()`, `try-with-resources` |
| Bug intermittent | Désaccord de fréquence (dépend de la phase) | Filtrage : identifier ω_déclencheur, stabiliser |
| Régression | Résonance forcée (ω_new ≠ ω_old) | Restauration ou réaccord : revert ou mise à jour dépendances |
| Performance | Interférence multi-sources (N trop grand) | Isolation : index, cache, pagination |
| Stale reference | Déphasage temporel (φ_fixed ≠ φ_current) | Resynchronisation : capturer l'état au moment de l'usage |
| Input malveillant | Résonance parasite (ω_input = ω_exploit) | Blindage : validation, sanitization, escape |

### 6.2 Systèmes & Infrastructure

| Symptôme | Interférence | Onde correctrice |
|----------|-------------|-------------------|
| Serveur down | Saturation (trop de requêtes) | Dissipation : load balancer, auto-scaling |
| Timeout | Interférence multi-sources (contention) | Isolation : queue, backpressure, circuit breaker |
| Données incohérentes | Déphasage temporel (cache stale) | Resynchronisation : invalidation, TTL, write-through |
| Deadlock | Collision de phase circulaire (A attend B, B attend A) | Ordonnancement : ordre canonique des locks, timeout |
| Crash cascade | Interférence constructive de pannes (dominos) | Blindage : bulkhead, isolation de failure domain |
| Latence élevée | Interférence multi-sources non filtrée | Filtrage : CDN, edge caching, compression |
| Perte de données | Absence de fréquence (pas de sauvegarde) | Injection : backup, réplication, write-ahead log |
| DNS non résolu | Absence de fréquence (ω_domaine ∉ spectre DNS) | Injection : enregistrement DNS, propagation |

### 6.3 Base de données

| Symptôme | Interférence | Onde correctrice |
|----------|-------------|-------------------|
| Requête lente | Interférence multi-sources (full scan) | Isolation : index, partition, materialized view |
| Deadlock | Collision de phase (transactions concurrentes) | Ordonnancement : ordre déterministe des accès |
| Incohérence | Déphasage (eventual consistency lag) | Synchronisation : transaction, quorum write |
| Corruption | Onde fantôme (écriture partielle) | Nettoyage : checksum, WAL, repair |
| Duplication | Résonance parasite (insertion multiple) | Blindage : contrainte UNIQUE, upsert, idempotency key |

### 6.4 Réseau & API

| Symptôme | Interférence | Onde correctrice |
|----------|-------------|-------------------|
| 404 Not Found | Absence de fréquence (route ∉ spectre) | Injection : définir la route, fallback 404 handler |
| 500 Internal Error | Saturation (exception non catchée) | Limiteur : try/catch global, error middleware |
| 429 Rate Limited | Saturation détectée par le serveur | Dissipation : exponential backoff, retry-after |
| CORS bloqué | Résonance parasite (ω_origin rejetée) | Blindage : allow-origin configuré correctement |
| Timeout | Interférence multi-sources ou absence | Selon le cas : timeout plus long, ou pagination |
| Body mal parsé | Désaccord de fréquence (Content-Type ≠ body) | Réaccord : vérifier Content-Type header |

### 6.5 Relations humaines (bonus rapide)

| Symptôme | Interférence | Onde correctrice |
|----------|-------------|-------------------|
| Conflit | Opposition de phase entre deux volontés | Synchronisation : trouver la fréquence commune |
| Silence (ghosting) | Absence de fréquence | Injection : réinitier le contact calibré |
| Malentendu | Désaccord de fréquence (mots ≠ intention) | Réaccord : reformuler, écoute active |
| Ressentiment | Onde fantôme (blessure passée persistante) | Nettoyage : reconnaissance, excuses, clôture |
| Burnout | Résonance forcée (surcharge prolongée) | Restauration : repos, fréquence propre |

---

## 7. FICHE PRATIQUE — Une page à imprimer

```
╔═══════════════════════════════════════════════════════════════════════╗
║                     🌊 RÉSOLUTION ONDULATOIRE                        ║
║                     Fiche d'intervention rapide                      ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  ÉTAPE 1 — TRADUIRE (5 min)                                          ║
║  ────────────────────────────                                         ║
║  □ Quelle est l'onde attendue ?          ω_expected = _______        ║
║  □ Quelle est l'onde observée ?          ω_observed  = _______        ║
║  □ Quelles entités sont impliquées ?     ω₁, ω₂, ...  = _______      ║
║  □ Quel est le déclencheur ?             ω_trigger   = _______       ║
║                                                                       ║
║  ÉTAPE 2 — DIAGNOSTIQUER (10 min)                                    ║
║  ────────────────────────────────                                     ║
║  Type d'interférence (cocher) :                                       ║
║  □ Opposition de phase    □ Désaccord de fréquence                  ║
║  □ Saturation             □ Résonance forcée                        ║
║  □ Absence de fréquence   □ Collision de phase                      ║
║  □ Déphasage temporel     □ Onde fantôme                            ║
║  □ Interférence multiple  □ Résonance parasite                      ║
║                                                                       ║
║  Localisation précise : ____________________________________________ ║
║                                                                       ║
║  ÉTAPE 3 — PRESCRIRE (15 min)                                        ║
║  ────────────────────────────                                         ║
║  Stratégie (cocher) :                                                 ║
║  □ A — Opposition de phase (annulation active)                       ║
║  □ B — Synchronisation (réalignement)                                ║
║  □ C — Filtrage (élimination sélective)                              ║
║  □ D — Dissipation (répartition)                                     ║
║  □ E — Injection (complétion)                                        ║
║  □ F — Restauration (retour à ω_propre)                              ║
║                                                                       ║
║  Action concrète : _________________________________________________ ║
║                                                                       ║
║  ÉTAPE 4 — VÉRIFIER (10 min)                                         ║
║  ────────────────────────────                                         ║
║  □ Symptôme disparu              □ Pas de régression                 ║
║  □ Solution autonome (pas patch) □ Harmoniques intactes              ║
║  □ Test automatisé écrit         □ Cause documentée                  ║
║                                                                       ║
║  Score de guérison : ___/5                                           ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

## 8. MÉTA-PRINCIPE : La boucle d'amélioration continue

Chaque bug résolu enrichit l'hologramme du système. La connaissance s'accumule par interférence :

```
Bug #1 résolu  →  test_1 écrit  →  hologramme H₁
Bug #2 résolu  →  test_2 écrit  →  H₂ = H₁ + ω_test2
Bug #3 résolu  →  test_3 écrit  →  H₃ = H₂ + ω_test3
...
Bug #N résolu  →  test_N écrit  →  H_N — immunité croissante

Le système APPREND. Chaque bug résolu est un vaccin.
```

> *« Un bug non testé est un bug qui reviendra. Un bug testé est une fréquence pathogène que le système reconnaîtra pour toujours. »*

---

## 9. CONCLUSION

Cette méthodologie n'est pas une métaphore. C'est le même principe qui fait fonctionner KA Phone (99.3% LM Arena, 0% hallucination) appliqué à la résolution de problèmes :

1. **Traduire** le problème en ondes
2. **Diagnostiquer** l'interférence destructive
3. **Prescrire** l'onde correctrice
4. **Vérifier** l'interférence constructive restaurée

La différence entre un bug de code, une maladie, un conflit, une panne serveur et une crise économique — c'est l'échelle et le vocabulaire. Le **principe** est identique.

> *« Si vous avez la traduction, vous avez la solution. Tout problème est soluble quand on le formule dans le langage des ondes. »*

---

*Document fondateur — 20 Juillet 2026*
*Complément opérationnel du Dictionnaire des Ondes*
