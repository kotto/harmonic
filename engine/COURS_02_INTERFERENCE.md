# 🌊 COURS N°2 — L'Interférence, ou comment deux idées s'additionnent

**Mathématiques Ondulatoires — Leçon n°2**
**Niveau : Débutant (12-16 ans)**
**Prérequis : Cours n°1 (ψ = A·e^{iφ})**

---

> *« Dans le cours précédent, tu as appris qu'un nombre est une onde. Dans ce cours, tu vas apprendre ce qui se passe quand deux ondes se rencontrent. Spoiler : c'est la base de tout — de la logique à l'amour. »*

---

## 1. Rappel : ce qu'est une onde

```
   ψ = A · e^{iφ}
   
   A  = amplitude (combien d'énergie)
   φ  = phase     (où dans le cycle, 0° à 360°)
   
   ═══════════════════════════════════
   
   Exemples :
   
   ψ₁ = 5 · e^{i·0°}    →  « 5 qui commence à monter »
   ψ₂ = 5 · e^{i·180°}  →  « 5 qui commence à descendre »
   ψ₃ = 3 · e^{i·90°}   →  « 3 qui pointe vers le haut »
```

---

## 2. L'interférence : la rencontre de deux mondes

Quand deux ondes se croisent, elles ne s'ignorent pas. Elles **interfèrent**.

```
   L'INTERFÉRENCE EN UNE IMAGE
   ═══════════════════════════
   
   Onde A  ──→  ╱╲ ╱╲ ╱╲ ╱╲
                                ↓  elles se croisent
   Onde B  ──→  ╱╲ ╱╲ ╱╲ ╱╲
   
   Résultat :  ╱╱╲╲╱╱╲╲╱╱╲╲╱╱╲╲   ← addition des hauteurs
   
   → À chaque point, la hauteur de A + la hauteur de B = la nouvelle vague.
```

Le résultat dépend d'UNE seule chose : **le déphasage** Δφ = φ_A − φ_B.

```
   Δφ = 0°     →  addition parfaite       (constructive)
   Δφ = 90°    →  addition partielle      
   Δφ = 180°   →  annulation parfaite     (destructive)
   Δφ = 270°   →  = 90° (symétrique)
```

> **Règle n°8 : Deux ondes interfèrent selon leur déphasage Δφ. C'est la seule variable qui compte.**

---

## 3. Les 4 cas fondamentaux

### Cas 1 — Δφ = 0° : la résonance parfaite

```
   ψ_A = 3·e^{i·0°}     ψ_B = 2·e^{i·0°}
   
       ↑                   ↑
     3 ┤ ●               2 ┤ ●
       │                   │
   ────┼────→         ────┼────→
       │                   │
       
       ─────────────────────────────────
       ψ_A ⊕ ψ_B = 5·e^{i·0°}
       ─────────────────────────────────
       
       ↑
     5 ┤ ●     ← les deux flèches s'additionnent
       │        (3+2=5, phases identiques)
   ────┼────→
       │
   
   → C'est le SEUL cas où 3+2=5 est « vrai » au sens classique.
```

**Dans la vraie vie :** Deux musiciens qui jouent la même note au même moment. Le son est plus fort. Deux amis qui pensent exactement la même chose. L'idée est renforcée.

### Cas 2 — Δφ = 180° : l'annulation parfaite

```
   ψ_A = 3·e^{i·0°}      ψ_B = 3·e^{i·180°}
   
       ↑                       │
     3 ┤ ●                      │
       │                   ─────┼────→
   ────┼────→                 3 ┤ ●
       │                        │
       
       ─────────────────────────────────
       ψ_A ⊕ ψ_B = 0     ← silence total
       ─────────────────────────────────
       
       Les deux flèches sont égales et opposées.
       Elles s'annulent exactement.
   
   → 3 + 3 = 0 ? Oui, si les phases sont opposées.
```

**Dans la vraie vie :** Le casque anti-bruit : il émet l'onde sonore EXACTEMENT opposée au bruit ambiant → silence. Deux arguments parfaitement contradictoires → indécision totale. La lumière qui traverse deux fentes et crée des zones d'ombre (expérience de Young).

### Cas 3 — Δφ = 90° : la quadrature

```
   ψ_A = 3·e^{i·0°}      ψ_B = 4·e^{i·90°}
   
       ↑                   ↑
       │                 4 ┤ ●
     3 ┤ ●                 │ │
       │                   │ │  ψ_A⊕ψ_B = 3 + 4i
   ────┼────→         ─────┼─┼──→    amplitude = 5
       │                   │
       
       ─────────────────────────────────
       
       ↑
     5 ┤    ●  ← résultante (hypoténuse du triangle 3-4-5)
       │   ╱
     4 ┤  ╱
       │ ╱
       │╱ 53°
   ────┼────→
          3
   
   → 3² + 4² = 5²  (Pythagore !)
   → La phase a tourné de 53° (arctan(4/3))
```

**Dans la vraie vie :** Une voiture qui avance (3 m/s vers l'est) poussée par un vent latéral (4 m/s vers le nord) → trajectoire à 5 m/s vers le nord-est. Deux objectifs partiellement compatibles → compromis à 53°.

### Cas 4 — Δφ quelconque : le cas général

```
   ψ_A = A·e^{i·φ_A}     ψ_B = B·e^{i·φ_B}
   
   Formule générale :
   
   Amplitude résultante = √(A² + B² + 2AB·cos(Δφ))
   Phase résultante     = arctan2(A·sin φ_A + B·sin φ_B,
                                  A·cos φ_A + B·cos φ_B)
```

> **Règle n°9 : L'interférence de deux ondes est gouvernée par cos(Δφ). cos(0°)=1 → addition. cos(180°)=−1 → soustraction. cos(90°)=0 → Pythagore.**

---

## 4. La mesure de cohérence

À quel point deux ondes sont-elles « d'accord » ? On mesure la **cohérence** :

```
   COHÉRENCE ENTRE ψ_A ET ψ_B
   ═══════════════════════════
   
   C(ψ_A, ψ_B) = |⟨ψ_A | ψ_B⟩|² / (||ψ_A|| · ||ψ_B||)
   
   ═══════════════════════════════════════════════
   
   LA JAUGE DE COHÉRENCE
   
   1.0 ┤ ████████████   → parfaitement en phase (même idée)
   0.8 ┤ ██████████░░   → très en accord
   0.5 ┤ ██████░░░░░░   → partiellement d'accord (90°)
   0.3 ┤ ████░░░░░░░░   → plutôt en désaccord
   0.0 ┤ ░░░░░░░░░░░░   → complètement opposées (180°)
   
   → La cohérence n'est jamais négative.
   → Elle varie CONTINÛMENT de 0 à 1.
   → Il n'y a pas de « vrai/faux » — juste des degrés de résonance.
```

### Exercice 2.1

Calcule la cohérence entre :

a) ψ₁ = 1·e^{i·0°} et ψ₂ = 1·e^{i·0°}
b) ψ₁ = 1·e^{i·0°} et ψ₂ = 1·e^{i·180°}
c) ψ₁ = 1·e^{i·0°} et ψ₂ = 1·e^{i·90°}

*(Réponses : a) 1.0, b) 1.0 — oui, 1.0 ! Deux ondes opposées ont une cohérence de 1 car elles sont PARFAITEMENT corrélées, juste inversées. c) 0.0 — une onde horizontale et une verticale n'ont aucun rapport.)*

> **Règle n°10 : La cohérence mesure la corrélation, pas l'accord. Deux ennemis parfaits ont une cohérence de 1.0 — ils sont parfaitement synchronisés, juste opposés.**

---

## 5. La logique ondulatoire

Si la cohérence remplace la vérité, alors la LOGIQUE devient continue :

```
   LOGIQUE CLASSIQUE (binaire)    LOGIQUE ONDULATOIRE (continue)
   ════════════════════════       ═════════════════════════════
   
   A est VRAI ou FAUX             A a une cohérence C avec la réalité
   
   ┌────┬───────┐                 ┌──────────┬──────────────────┐
   │ A  │ NON A │                 │ Cohérence│ Signification    │
   ├────┼───────┤                 ├──────────┼──────────────────┤
   │ V  │   F   │                 │  0.9-1.0 │ quasi certain    │
   │ F  │   V   │                 │  0.7-0.9 │ probable         │
   └────┴───────┘                 │  0.5-0.7 │ plausible        │
                                  │  0.3-0.5 │ incertain        │
   Deux valeurs seulement         │  0.0-0.3 │ improbable       │
   (oui ou non)                   └──────────┴──────────────────┘
                                  
                                  Une infinité de degrés
                                  (continuum de résonance)
```

### Exemple : « Cette tomate est rouge »

```
   ψ_tomate = onde encodant la tomate observée
   ψ_rouge  = onde encodant le concept « rouge »
   
   C(ψ_tomate, ψ_rouge) = 0.85
   
   → La tomate est « rouge à 85% » (plutôt rouge, mais pas parfaitement)
   
   En logique classique : elle est soit rouge, soit pas rouge.
   En logique ondulatoire : elle est rouge à 85%, orange à 60%, mûre à 90%.
   TOUTES ces affirmations sont partiellement vraies.
```

> **Règle n°11 : La vérité n'est pas binaire. C'est une mesure de cohérence entre une onde-concept et une onde-observation.**

---

## 6. L'interférence à N ondes : la superposition

Quand PLUS de deux ondes se rencontrent :

```
   SUPERPOSITION DE 3 ONDES
   ════════════════════════
   
   ψ₁ = 2·e^{i·0°}      (droite)
   ψ₂ = 1·e^{i·90°}     (haut)
   ψ₃ = 1·e^{i·180°}    (gauche)
   
       ↑
     1 ┤ ● ψ₂
       │ │
       │ │    ψ₁⊕ψ₂⊕ψ₃ = 1 + 1i
   ──●─┼─●──→            │
   ψ₃ 1│    2 ψ₁         │  amplitude = √2 ≈ 1.41
       │                  │  phase = 45°
   
   → L'onde résultante est la SOMME VECTORIELLE de toutes les ondes.
   → Chaque onde contribue, aucune n'est « perdue ».
```

**Dans la vraie vie :** Un cerveau qui prend une décision. Chaque raison est une onde (ψ_pour, ψ_contre, ψ_peur, ψ_envie...). La décision finale est la superposition de toutes ces ondes. Tu ne « choisis » pas — tu **interfères**.

> **Règle n°12 : Une décision n'est pas un choix. C'est l'interférence de toutes les ondes-raisons présentes dans ton esprit à l'instant t.**

---

## 7. L'expérience des fentes de Young

C'est l'expérience la plus importante de toute la physique. La voici :

```
   EXPÉRIENCE DES FENTES DE YOUNG
   ══════════════════════════════
   
   SOURCE     BARRIER      ÉCRAN
   (lumière)  (2 fentes)   (mur)
   
     💡          ┃
                 ┃    ╱     ██ ← interférence constructive (lumière)
                 ┣━━━╋━━━━  ── ← interférence destructive (ombre)
     ──→         ┃    ╲     ██ ← constructive
                 ┃          ── ← destructive
                 ┃          ██
   
   → La lumière passe par DEUX fentes en même temps.
   → Sur l'écran, on voit des bandes claires et sombres.
   → Les bandes claires = Δφ = 0° (ondes en phase)
   → Les bandes sombres = Δφ = 180° (ondes opposées)
   
   C'est la PREUVE que la lumière est une onde.
   Une particule ne pourrait pas « passer par deux fentes à la fois »
   et interférer avec elle-même.
```

### Exercice 2.2 — L'expérience de Young avec les nombres

Si on envoyait des « nombres-ondes » au lieu de la lumière à travers deux fentes, quel motif verrait-on sur l'écran pour ψ = 5·e^{i·0°} et ψ = 5·e^{i·180°} ?

*(Réponse : des bandes sombres partout — interférence destructive totale. 5 + (−5) = 0.)*

---

## 8. Tableau récapitulatif des 5 nouvelles règles

```
╔══════╤══════════════════════════════════════════════════════════════╗
║  #   │ RÈGLE                                                       ║
╠══════╪══════════════════════════════════════════════════════════════╣
║  8   │ Deux ondes interfèrent selon Δφ (la seule variable)         ║
║  9   │ L'interférence est gouvernée par cos(Δφ)                    ║
║ 10   │ La cohérence mesure la corrélation (pas l'accord)           ║
║ 11   │ La vérité est continue : une mesure de cohérence            ║
║ 12   │ Une décision = interférence de toutes les ondes-raisons     ║
╚══════╧══════════════════════════════════════════════════════════════╝
```

---

## 9. Devoir à la maison

### Question 1 — Le triangle 3-4-5

```
   ψ_A = 3·e^{i·0°}
   ψ_B = 4·e^{i·90°}
   
   1. Dessine les deux ondes
   2. Dessine leur somme
   3. Mesure l'amplitude résultante (aide : théorème de Pythagore)
   4. Mesure la phase résultante (aide : tan(φ) = opposé/adjacent)
```

### Question 2 — La cohérence des idées

Prends deux idées auxquelles tu crois :

```
   Idée A : « ___________________________________ »
   Idée B : « ___________________________________ »
```

Attribue-leur une phase (0° = complètement d'accord avec toi, 180° = tu penses le contraire).

Calcule leur cohérence. Sont-elles plutôt en phase ou en opposition ?

### Question 3 — L'interférence dans ta vie

Trouve UN exemple dans ta vie où deux « forces » interfèrent :

```
   Force 1 (onde A) : _________________________
   Force 2 (onde B) : _________________________
   
   Sont-elles constructives (même direction) ou destructives (opposées) ?
   Quel est le Δφ approximatif ?
   Quel est le résultat de leur interférence dans ta vie ?
```

---

## 10. Prochain cours

```
   COURS N°3 — LA SUPERPOSITION
   ════════════════════════════
   
   Quand une onde EST plusieurs ondes à la fois.
   
   ψ_chat = ψ_vivant ⊕ ψ_mort
   
   → Oui, le fameux chat de Schrödinger.
   → Mais appliqué aux nombres, aux idées, et à toi.
```

> *« L'univers ne choisit pas entre les possibilités. Il les superpose toutes, et c'est l'interférence qui détermine ce qui émerge. Y compris tes pensées. »*

---

**Cours n°2 — Mathématiques Ondulatoires — FIN**
