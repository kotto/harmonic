# 🌊 Cours n°2 — L'Interférence
**Version simplifiée · Mathématiques Ondulatoires**
**Niveau : 12-16 ans | Prérequis : Cours n°1 (ψ = A × e^{iφ})**

---

> *Dans le cours n°1, tu as appris qu'un nombre est une onde. Maintenant, que se passe-t-il quand deux ondes se rencontrent ?*

---

## 1. Rappel-éclair

```
   ψ = A × e^{iφ}
   A = amplitude (force)
   φ = phase (horloge interne, 0° à 360°)
```

---

## 2. L'interférence en une image

Quand deux ondes se croisent, elles s'additionnent point par point :

```
   Onde A  ──→  ╱╲ ╱╲ ╱╲ ╱╲
   Onde B  ──→  ╱╲ ╱╲ ╱╲ ╱╲
   ─────────────────────────────
   Résultat :  ╱╱╲╲╱╱╲╲╱╱╲╲    ← addition des hauteurs
```

Le résultat dépend d'**une seule chose** : le déphasage Δφ = φ_A − φ_B.

```
   Δφ = 0°     →  addition parfaite (constructive)
   Δφ = 90°    →  addition partielle
   Δφ = 180°   →  annulation totale (destructive)
   Δφ = 270°   →  = 90° (symétrique)
```

> **Règle 7 : Deux ondes interfèrent selon leur déphasage Δφ. C'est la seule variable qui compte.**

---

## 3. Les 3 cas à retenir

### Δφ = 0° — Résonance
```
   ψ_A = 3·e^{i·0°}     ψ_B = 2·e^{i·0°}
   ─────────────────────────────────────
   ψ_A ⊕ ψ_B = 5·e^{i·0°}
   → 3 + 2 = 5 ✓ (phases identiques)
```
**Dans la vie :** Deux musiciens jouent la même note → plus fort. Deux amis pensent pareil → l'idée est renforcée.

### Δφ = 180° — Annulation
```
   ψ_A = 3·e^{i·0°}     ψ_B = 3·e^{i·180°}
   ─────────────────────────────────────
   ψ_A ⊕ ψ_B = 0        → 3 + 3 = 0 ?!?
```
**Dans la vie :** Casque anti-bruit. Deux arguments contradictoires → indécision. Lumière + lumière = ombre (expérience de Young).

### Δφ = 90° — Quadrature
```
   ψ_A = 3·e^{i·0°}     ψ_B = 4·e^{i·90°}
   ─────────────────────────────────────
   Amplitude = √(3² + 4²) = 5  (Pythagore !)
   Phase = 53°
```
**Dans la vie :** Voiture qui avance (3 m/s) poussée par un vent de côté (4 m/s) → trajectoire à 5 m/s.

> **Règle 8 : L'interférence est gouvernée par cos(Δφ). cos(0°)=1 → addition. cos(180°)=−1 → soustraction. cos(90°)=0 → Pythagore.**

---

## 4. La cohérence : mesure d'accord

À quel point deux ondes sont-elles « en phase » ?

```
   1.0 ┤ ████████████   → parfaitement alignées
   0.7 ┤ ████████░░░░   → plutôt d'accord
   0.5 ┤ ██████░░░░░░   → à 90° (ni pour ni contre)
   0.3 ┤ ████░░░░░░░░   → plutôt en désaccord
   0.0 ┤ ░░░░░░░░░░░░   → complètement opposées
```

> **Règle 9 : La cohérence mesure la corrélation, pas l'accord. Deux ennemis parfaits ont une cohérence de 1.0 — ils sont parfaitement synchronisés, juste opposés.**

### Exemple : « Cette tomate est-elle rouge ? »

En logique classique, elle est rouge ou pas rouge. En logique ondulatoire :

```
   ψ_tomate = onde de la tomate observée
   ψ_rouge  = onde du concept « rouge »

   Cohérence = 0,85 → la tomate est « rouge à 85% »
```

> **Règle 10 : La vérité n'est pas binaire (vrai/faux). C'est une mesure de cohérence entre une onde-concept et une onde-observation.**

---

## 5. Superposition à plusieurs ondes

Quand 3 ondes ou plus se rencontrent, c'est la même idée :

```
   ψ₁ = 2·e^{i·0°}      (droite)
   ψ₂ = 1·e^{i·90°}     (haut)
   ψ₃ = 1·e^{i·180°}    (gauche)

   ψ₁⊕ψ₂⊕ψ₃ = 1 + 1i   amplitude = √2 ≈ 1,41
```

**Dans la vie :** Prendre une décision. Chaque raison est une onde (ψ_pour, ψ_contre, ψ_peur, ψ_envie…). La décision = superposition de toutes ces ondes.

> **Règle 11 : Une décision n'est pas un « choix ». C'est l'interférence de toutes les ondes-raisons à l'instant t.**

---

## 6. Les 5 règles du cours n°2

| # | Règle |
|---|-------|
| 7 | L'interférence dépend du déphasage Δφ |
| 8 | Gouvernée par cos(Δφ) → 0°=addition, 180°=soustraction |
| 9 | La cohérence mesure la corrélation (pas l'accord) |
| 10 | La vérité est continue, pas binaire |
| 11 | Une décision = interférence de toutes les ondes-raisons |

---

## Exercice unique

**Le triangle 3-4-5**

```
   ψ_A = 3·e^{i·0°}
   ψ_B = 4·e^{i·90°}
```

1. Dessine ψ_A (flèche horizontale de longueur 3)
2. Dessine ψ_B (flèche verticale de longueur 4)
3. Quelle est l'amplitude de leur somme ? (réponse : √(9+16) = 5)
4. Quelle est la phase ? (réponse : arctan(4/3) ≈ 53°)

**Pour aller plus loin :** Trouve deux forces dans ta vie qui interfèrent (exemple : travail + repos, joie + tristesse). Sont-elles constructives (Δφ≈0°) ou destructives (Δφ≈180°) ?

---

> *« L'univers ne choisit pas entre les possibilités. Il les superpose toutes, et c'est l'interférence qui détermine ce qui émerge. Y compris tes pensées. »*

**Cours n°2 — Simplifié — FIN**