# 🌊 COURS N°1 — Qu'est-ce qu'un nombre ?

**Mathématiques Ondulatoires — Leçon inaugurale**
**Niveau : Débutant (12-16 ans)**
**Prérequis : Aucun. Juste savoir observer.**

---

> *« Avant ce cours, tu pensais que les nombres étaient des symboles sur du papier. Après ce cours, tu sauras qu'ils sont des ondes qui vibrent. Et que tout vibre. Y compris toi. »*

---

## 1. L'expérience qui change tout

Prends une corde. Attache une extrémité à un mur. Secoue l'autre extrémité.

Voici ce que tu vois :

```
       AMPLITUDE (hauteur)
          ↑
          │   ╱╲        ╱╲
          │  ╱  ╲      ╱  ╲
    ──────┼─╱────╲────╱────╲────  ← corde au repos
          │╱      ╲  ╱      ╲
          │        ╲╱        ╲╱
          │
          ├─────────┼─────────┼──→ TEMPS
              PHASE    PHASE
             (début)  (décalée)

   Une vague = une AMPLITUDE (hauteur) + une PHASE (position dans le temps)
```

Cette vague a trois propriétés :

1. **L'amplitude** — jusqu'où elle monte et descend (sa force, son énergie)
2. **La phase** — où elle commence dans son cycle (son « timing »)
3. **La fréquence** — combien de vagues par seconde (son rythme)

> **Règle n°1 : Tout dans l'univers a une amplitude, une phase, et une fréquence. Même les nombres. Même toi.**

---

## 2. L'interférence — le seul calcul de l'univers

Deux vagues sur la même corde :

```
   INTERFÉRENCE CONSTRUCTIVE (phases alignées)
   ───────────────────────────────────────────
   
   Vague A :        ╱╲   ╱╲   ╱╲     (phase 0°)
   Vague B :        ╱╲   ╱╲   ╱╲     (phase 0°)
   ─────────────────────────────────
   SOMME   :       ╱╱╲╲ ╱╱╲╲ ╱╱╲╲   (amplitude ×2 !)
   
   → Phases alignées → les ondes se RENFORCENT


   INTERFÉRENCE DESTRUCTIVE (phases opposées)
   ──────────────────────────────────────────
   
   Vague A :        ╱╲   ╱╲   ╱╲     (phase 0°)
   Vague B :        ╲╱   ╲╱   ╲╱     (phase 180°)
   ─────────────────────────────────
   SOMME   :       ─────────────────   (amplitude = 0 !)
   
   → Phases opposées → les ondes S'ANNULENT
```

> **Règle n°2 : L'univers ne calcule pas avec des + et des −. Il superpose des ondes. L'addition EST une interférence.**

---

## 3. Le nombre 5 n'existe pas

Regarde ce symbole : **5**.

Mais en réalité, « cinq » est une **onde** :

```
   LE SYMBOLE                     LA RÉALITÉ
   ─────────                      ──────────
   
   ┌──────┐                       ┌─────────────────────┐
   │  5   │  encre sur papier     │                     │
   │      │                       │   ψ = 5 * e^{iφ}   │
   └──────┘                       │                     │
                                  │   Amplitude = 5     │
   Un dessin                      │   Phase     = φ     │
   (mort, figé)                   │                     │
                                  └─────────────────────┘
                                  
                                  Une vibration
                                  (vivante, dynamique)
```

> **Règle n°3 : Un « nombre » n'est pas un symbole. C'est une onde complexe ψ = A · e^{iφ}. L'amplitude A dit « combien ». La phase φ dit « quand/où ».**

### Exercice 1.1

Deux « cinq » de même amplitude mais de phases DIFFÉRENTES :

```
   Même amplitude (5), phases DIFFÉRENTES
   ─────────────────────────────────────
   
   5*e^{i*0}           5*e^{i*π}
      ↑                   │
    5 ┤    ●              │           ●
      │                   │
   ───┼───────→      ─────┼───────────→
      │                -5 ┤
                          
   « cinq qui pousse »   « cinq qui retire »
```

*(Ces deux « cinq » ont la même amplitude mais des effets opposés. Le symbole « 5 » ne capture pas cette différence. L'onde, si.)*

---

## 4. L'onde s'écrit ψ = A · e^{iφ}

C'est la **seule formule** dont tu auras besoin.

```
   L'ONDE ψ = A * e^{iφ}
   ════════════════════

          A (amplitude)
          │
          │    ● ψ = A*e^{iφ}
          │   ╱
          │  ╱   ← le point ψ est à distance A du centre,
          │ ╱          à l'angle φ de l'horizontale
          │╱ φ
   ───────┼────────→  axe réel
          │
          │   Le cercle = toutes les phases possibles (0° à 360°)
          │   Le rayon  = l'amplitude A
          │   L'angle   = la phase φ
```

### Le cercle des phases

```
          90° (π/2)
             ↑ i
             │
    180° ────┼──── 0° (1)
     (-1)    │
             │
          270° (-i)
   
   Phase 0°   = 1       (pointe à droite)
   Phase 90°  = i       (pointe en haut)
   Phase 180° = -1      (pointe à gauche)
   Phase 270° = -i      (pointe en bas)
   Phase 360° = 1       (retour au départ)
```

> **Règle n°4 : La phase φ est une horloge. Chaque onde a sa propre horloge interne.**

### Exercice 1.2 — L'identité d'Euler

L'équation la plus célèbre des mathématiques : e^{iπ} + 1 = 0

```
   ψ₁ = 1*e^{i*0}  = 1     →  onde qui pointe à DROITE
   ψ₂ = 1*e^{i*π}  = -1    →  onde qui pointe à GAUCHE
   
   ─────────────────────────────────────
   ψ₁ ⊕ ψ₂ = 1 + (-1) = 0  → interférence destructive
   ─────────────────────────────────────
   
   Ce n'est pas des « maths ». C'est de la physique.
```

---

## 5. Additionner des ondes

Quand tu fais 2 + 3 = 5, tu supposes les phases identiques.

```
   CAS 1 : MÊME PHASE
   ──────────────────
   ψ₂ = 2*e^{i0} = 2
   ψ₃ = 3*e^{i0} = 3
   ψ₂ ⊕ ψ₃ = 5     ← 2+3=5  ✓  (le cas classique)


   CAS 2 : PHASE OPPOSÉE
   ─────────────────────
   ψ₂ = 2*e^{i0}  =  2     (pointe à droite)
   ψ₃ = 3*e^{iπ}  = -3     (pointe à gauche)
   ψ₂ ⊕ ψ₃ = -1            ← 2+3 = -1 ???
   
   → L'onde de 3 ANNULE l'onde de 2 et enlève encore 1


   CAS 3 : PHASE 90°
   ─────────────────
   ψ₂ = 2*e^{i0}    = 2     (droite)
   ψ₃ = 3*e^{iπ/2}  = 3i    (haut)
   
       ↑
     3 ┤    ● ψ₃
       │    │╲
       │    │ ╲  ψ₂⊕ψ₃ = 2 + 3i
       │    │  ╲  amplitude = √(4+9) ≈ 3.6
     0 └────┼───●──→
           0   2  ψ₂
   
   → 2 + 3 ne fait PAS 5 ! L'amplitude est ≈ 3.6
```

> **Règle n°5 : 2+3=5 n'est vrai QUE si les phases sont alignées. Sinon, c'est une interférence.**

### Exercice 1.3

Dessine ψ₄ ⊕ ψ₃ quand φ₄ = 0° et φ₃ = 180°.

*(Aide : 4*e^{i0}=4, 3*e^{iπ}=-3. La somme est 1.)*

---

## 6. La multiplication des ondes

```
   ψ₂ = 2*e^{iφ₂}
   ψ₃ = 3*e^{iφ₃}
   
   ψ₂ ⊗ ψ₃ = (2×3) * e^{i(φ₂+φ₃)}
           =   6    * e^{i(φ₂+φ₃)}
   
   L'amplitude est multipliée (2×3=6)      ← comme d'habitude
   La phase est ADDITIONNÉE (φ₂+φ₃)       ← nouveau !
```

**Visuellement :**

```
   ψ₂ = 2*e^{i*45°}   ψ₃ = 3*e^{i*45°}
   
             ↑
           6 ┤    ● ψ₂⊗ψ₃     ← pointe à 90° !
             │   ╱
             │  ╱             Phase tournée de 45°+45°=90°
             │ ╱              Amplitude devenue 2×3=6
           0 └────────→
```

> **Règle n°6 : Multiplier = amplifier l'amplitude ET additionner les phases.**

---

## 7. Le zéro n'est pas « rien »

```
   ZÉRO SYMBOLIQUE          ZÉRO PHYSIQUE
   ─────────────            ─────────────
   
   ┌───┐                    ╱╲   ╲╱
   │ 0 │   = « rien »       ╲╱ + ╱╲  = silence
   └───┘                    ──────────
   
   Un symbole               Deux ondes opposées
   (n'existe pas)           qui s'annulent
                            (existe vraiment)
```

En musique, le silence entre deux notes n'est pas « rien » — c'est l'absence de vibration. Mais dans la nature, le vrai silence est presque toujours **deux sons qui s'annulent**.

> **Règle n°7 : Le zéro n'est pas « rien » — c'est l'interférence destructive de deux ondes égales et opposées.**

---

## 8. Les 7 règles — récapitulatif

```
╔═════╤═══════════════════════════════════════════════════════╗
║  #  │ RÈGLE                                                ║
╠═════╪═══════════════════════════════════════════════════════╣
║  1  │ Tout a amplitude, phase, fréquence                   ║
║  2  │ L'univers superpose des ondes (addition=interférence)║
║  3  │ Un nombre = ψ = A*e^{iφ} (pas un symbole)           ║
║  4  │ La phase φ est une horloge interne (0°→360°)        ║
║  5  │ 2+3=5 seulement si phases alignées                  ║
║  6  │ Multiplier = amplifier ET additionner les phases     ║
║  7  │ Zéro = interférence destructive                     ║
╚═════╧═══════════════════════════════════════════════════════╝
```

---

## 9. Devoir à la maison

### Question 1 — L'onde de ton âge

Écris ton âge sous forme d'onde :

```
   Mon âge : ____ ans
   ψ = ____ * e^{i*____°}
   
   → Amplitude : ____ (mon âge)
   → Phase     : ____° (où j'en suis dans ma vie)
```

### Question 2 — L'interférence des émotions

```
   ψ_joie      = 10 * e^{i*0°}     (positive)
   ψ_tristesse = 10 * e^{i*180°}   (opposée)
   
   ψ_joie ⊕ ψ_tristesse = ???
```

Que remarques-tu ? Est-ce qu'on peut ressentir joie ET tristesse sans que l'une efface l'autre ?

### Question 3 — La corde de l'univers

Trouve un objet qui vibre. Dessine la vague. Note :
- Amplitude : ___ cm
- Nombre de vagues en 10 secondes : ___
- Où commence le cycle (phase) : ___

---

## 10. Prochain cours

```
   PROCHAIN COURS — L'INTERFÉRENCE
   ═══════════════════════════════
   
   ψ_A  ──→  ╱╲  ╱╲  ╱╲
                           ← sont-elles « d'accord » ?
   ψ_B  ──→  ╱╲  ╲╱  ╱╲
   
   Réponse : |⟨ψ_A|ψ_B⟩|²
            1.0 = parfaitement en phase (même idée)
            0.0 = complètement opposées
            0.5 = partiellement d'accord
```

> *« La physique a mis 3000 ans pour comprendre que la lumière est une onde. Les mathématiques viennent de le découvrir pour les nombres. Tu fais partie de la première génération qui apprend ça dès le début. »*

---

**Cours n°1 — Mathématiques Ondulatoires — FIN**
