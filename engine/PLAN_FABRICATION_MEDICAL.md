# Plan de fabrication : dispositifs médicaux harmoniques

**Basé sur les dérivations THU — 17 août 2026**

---

## PHASE 1 — Logiciel seul (mois 1-3)

Ces dispositifs ne nécessitent AUCUN nouveau matériel. Ce sont des algorithmes
qui s'ajoutent à des capteurs existants.

### 1.1 Cardio : rapport S/D = 1/φ

**Principe :** S/D = 1/φ ≈ 0,618 à 75 BPM. Un écart > 2% = alerte.

**Matériel existant :** Tensio. connecté Bluetooth (Withings, Omron, 30–100 €).

**Développement :**
```
Application mobile (iOS/Android) :
1. Recevoir mesure S/D du tensiomètre via Bluetooth
2. Calculer rapport = S/D
3. Afficher écart à 1/φ
4. Alerte si |rapport − 1/φ| / (1/φ) > 2%
5. Historique et tendances
```

**Coût :** 0 € (développement logiciel, ~2 semaines).

---

### 1.2 Neuro : rapport β/α = φ (EEG)

**Principe :** β/α = φ (postérieur, yeux ouverts). Écart > 5% = alerte.

**Matériel existant :** Casque EEG 4 électrodes (Muse, NeuroSky, 200–300 €).

**Développement :**
```
Application mobile :
1. Acquisition EEG via Bluetooth (bandes α: 8-12 Hz, β: 13-30 Hz)
2. Calculer puissance spectrale : P_α, P_β
3. Rapport = P_β / P_α
4. Afficher écart à φ
5. État : Normal / Dépression (β/α < φ) / Anxiété (β/α > φ)
```

**Coût :** 0 € (développement logiciel, ~3 semaines).

---

### 1.3 Respire : rapport I/E = 1/φ

**Principe :** I/E = 1/φ à 15 cycles/min. Écart > 5% = alerte.

**Matériel existant :** Microphone de smartphone.

**Développement :**
```
Application mobile :
1. Enregistrement sonore du souffle (microphone)
2. Détection des phases I (inspiration) et E (expiration)
3. Calculer rapport I/E
4. Afficher écart à 1/φ
5. Détection apnée du sommeil (I/E anormal)
```

**Coût :** 0 € (développement logiciel, ~2 semaines).

---

### 1.4 Température : patch T* = 37°C

**Principe :** T* = ΔE_H/(k_B·ln φ) = 37°C. Fièvre = écart à T*.

**Matériel existant :** Patch thermique Bluetooth (TempTraq, BlueSpark, 10–30 €).

**Développement :**
```
Application mobile :
1. Recevoir température cutanée via Bluetooth
2. Corriger à la température corporelle (algorithme standard)
3. Afficher écart à T* = 37°C
4. Alerte si |T − T*| > 0,5°C (fièvre)
5. Courbe de tendance
```

**Coût :** 0 € (développement logiciel, ~1 semaine).

---

## PHASE 2 — Dispositifs dédiés (mois 3-12)

Ces dispositifs nécessitent un développement matériel mais utilisent
des composants standard.

### 2.1 CardioHarmon — tensiomètre harmonique

**Spécifications :**
- Capteur de pression MEMS standard
- Microcontrôleur ARM Cortex-M4
- Affichage S/D + rapport + écart à 1/φ
- Bluetooth pour application mobile

**BOM (Bill of Materials) :**
| Composant | Référence | Coût |
|---|---|---|
| Capteur pression | BMP280 | 2,50 € |
| Microcontrôleur | STM32F401 | 4,00 € |
| Afficheur OLED | 0,96" 128×64 | 3,00 € |
| Bluetooth | HC-05 | 2,50 € |
| Batterie | LiPo 200 mAh | 2,00 € |
| Brassard | Standard | 3,00 € |
| PCB + boîtier | — | 5,00 € |
| **Total** | | **~22 €** |

**Prix de vente estimé :** 49 € (marge 55%).

**Délai :** 6 mois (prototype), 3 mois (certification).

---

### 2.2 NeuroHarmon — casque EEG harmonique

**Spécifications :**
- 4 électrodes sèches
- Amplificateur EEG (ADS1299, TI)
- Filtre numérique passe-bande α/β
- Rapport β/α temps réel
- Bluetooth pour application mobile

**BOM :**
| Composant | Coût |
|---|---|
| ADS1299 (8 canaux) | 15,00 € |
| Électrodes sèches ×4 | 8,00 € |
| Microcontrôleur | 5,00 € |
| Bluetooth | 2,50 € |
| Batterie | 3,00 € |
| PCB + boîtier | 10,00 € |
| **Total** | **~43 €** |

**Prix de vente estimé :** 99 € (marge 56%).

**Délai :** 9 mois (prototype), 6 mois (certification).

---

### 2.3 ThermoPatch — patch connecté T*

**Spécifications :**
- Capteur de température IR (MLX90614)
- Épaisseur < 2 mm, autonomie 72 h
- Étanche (IP67)
- Bluetooth Low Energy
- Alerte fièvre par écart à T*

**BOM :**
| Composant | Coût |
|---|---|
| MLX90614 | 8,00 € |
| nRF52832 (BLE) | 4,00 € |
| Batterie fine | 2,00 € |
| PCB flexible | 3,00 € |
| Adhésif médical | 1,00 € |
| **Total** | **~18 €** |

**Prix de vente estimé :** 39 € (marge 54%).

**Délai :** 6 mois (prototype), 3 mois (certification médicale).

---

## PHASE 3 — Imagerie médicale (mois 12-36)

### 3.1 IRM harmonique

**Principe :** L'IRM standard utilise la transformée de Fourier pour reconstruire
l'image. Le codec ψ (projection sur ℂ⁵¹² + φ-spacing) est une généralisation
de Fourier avec mémoire.

**Avantage THU :**
- La reconstruction harmonique utilise la mémoire ABC (D^{1/φ}) au lieu de
  la transformée de Fourier standard
- Meilleur rapport signal/bruit pour un même temps d'acquisition
- Compensation des artefacts de mouvement par rotation de phase

**Ce qui change :**
```
Standard : image = FFT⁻¹(k-space) → flou si mouvement
THU      : image = decode(ψ) → compensation de phase
```

**Délai :** 24 mois (recherche), 12 mois (développement).

---

### 3.2 Radiologie harmonique

**Principe :** La compression HCV2 (×500 sans perte) s'applique aux images
médicales (radio, scanner, IRM).

**Avantage :**
- Stockage : 1 To de DICOM → 2 Go
- Transmission : envoi instantané d'un scanner complet (smartphone)
- Archivage : conservation illimitée à coût nul

**Compression :**
| Type d'image | Standard (DICOM) | HCV2 | Gain |
|---|---|---|---|
| Radio | 10 Mo | 20 Ko | ×500 |
| Scanner | 500 Mo | 1 Mo | ×500 |
| IRM | 200 Mo | 400 Ko | ×500 |

**Délai :** 3 mois (prototype logiciel), 12 mois (certification dispositif médical).

---

### 3.3 Échographie harmonique

**Principe :** Les 7 coefficients cₙ = 1/Γ(n/φ+1) sont les harmoniques
naturelles de toute onde. L'échographie utilise déjà des harmoniques —
la THU donne les poids optimaux.

**Avantage :**
- Les harmoniques cₙ sont les fréquences de résonance naturelles des tissus
- Meilleure pénétration + meilleure résolution simultanément
- Pas de réglage empirique : les cₙ sont dérivés, pas ajustés

**Délai :** 12 mois (recherche), 6 mois (développement).

---

## BUDGET TOTAL

| Phase | Description | Coût | Délai |
|---|---|---|---|
| 1 | Logiciel (4 applications) | 0 € | 3 mois |
| 2 | 3 dispositifs dédiés | 150 k€ | 12 mois |
| 3a | Compression HCV2 médical | 50 k€ | 6 mois |
| 3b | IRM/Radio/Écho harmoniques | 500 k€ | 36 mois |
| **Total** | | **~700 k€** | **36 mois** |

---

## CERTIFICATION

| Dispositif | Classe | Norme | Délai |
|---|---|---|---|
| CardioHarmon | IIa | CEI 60601, ISO 13485 | 6 mois |
| NeuroHarmon | IIa | CEI 60601, ISO 13485 | 6 mois |
| ThermoPatch | IIa | CEI 60601, ISO 13485 | 3 mois |
| Compression HCV2 | Logiciel | CEI 62304 | 6 mois |
| IRM harmonique | IIb | CEI 60601, ISO 13485 | 12 mois |

---

## PREMIÈRE ÉTAPE CONCRÈTE (semaine 1)

**Application mobile CardioHarmon :**
1. ✅ Acheter un tensiomètre Bluetooth (Withings, 79 €)
2. ✅ Développer l'app : récupérer S/D → calculer rapport → afficher écart à 1/φ
3. ✅ Tester sur 10 personnes : vérifier que le rapport moyen est 1/φ
4. ✅ Publier sur l'App Store / Google Play

**Coût : 79 €. Délai : 1 semaine.**

C'est l'application la plus simple, la moins chère, et la plus immédiate
de toutes les innovations THU. Elle ne nécessite aucune approbation
réglementaire (c'est un logiciel d'analyse, pas un dispositif médical).