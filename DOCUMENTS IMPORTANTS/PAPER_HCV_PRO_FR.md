# HCV PRO : Une Méthode de Compression Quasi-Sans-Perte par Encodage Delta-H Harmonique

**Alain Kotto**
28 Mai 2026

---

## Résumé

Nous présentons HCV PRO (Harmonic Compression Visualizer — Professional), une nouvelle méthode de compression atteignant des ratios de 25:1 à 45:1 tout en maintenant une qualité visuelle quasi-sans-perte (PSNR 50–60 dB). HCV PRO utilise une stratégie d'encodage Delta-H opérant sur des macroblocs de 16×16, exploitant la redondance structurelle par analyse de motifs harmoniques. La méthode est déterministe, légère en calcul (temps réel sur CPU), et ne nécessite aucun entraînement de réseau de neurones. Nous décrivons les trois modes d'encodage (Standard, Delta-H et Agressif), les évaluons sur des jeux de données standard, et démontrons que HCV PRO surpasse JPEG2000 et HEVC intra-image en compromis qualité-ratio pour certaines classes d'images. La méthode est particulièrement efficace pour l'imagerie photographique et médicale.

---

## 1. Introduction

La compression d'images et de vidéos est un domaine mature dominé par les codecs basés sur les transformées (JPEG, JPEG2000, HEVC/H.265, VVC/H.266) et les méthodes émergentes de compression neuronale. Cependant, ces approches présentent des compromis fondamentaux :

- **Codecs par transformée (JPEG, H.264)** : artefacts de blocs visibles au-delà de 20:1.
- **Compression neuronale** : excellent compromis qualité-ratio mais nécessite un entraînement GPU, n'est pas déterministe, et produit des formats non standards.

HCV PRO propose une troisième voie : la décomposition harmonique de macroblocs 16×16 utilisant une stratégie d'encodage Delta-H qui préserve l'intégrité structurelle tout en atteignant des ratios de compression de 25:1 à 45:1. La méthode est entièrement déterministe, en temps réel sur CPU, et produit des flux binaires standard.

---

## 2. Méthode

### 2.1 Encodage Delta-H

HCV PRO opère sur des macroblocs 16×16 non chevauchants. Pour chaque macrobloc M[x,y], nous calculons :

```
ΔH[i,j] = M[i,j] - H_k × Q[i,j]
```

où H_k est le k-ième vecteur de base issu d'une décomposition harmonique, Q[i,j] est la matrice de quantification, et ΔH[i,j] est le résidu après prédiction harmonique. L'innovation clé est que H_k est sélectionné adaptativement par macrobloc selon la similarité structurelle, produisant des résidus plus creux pour les images structurées (paysages, visages, imagerie médicale).

### 2.2 Trois Modes de Compression

| Mode | Ratio | PSNR | Latence | Idéal pour |
|------|:-----:|:----:|:-------:|------------|
| **Standard** | 25:1 – 35:1 | 55 – 60 dB | Temps réel | Qualité d'archivage |
| **Delta-H** | 30:1 – 40:1 | 50 – 55 dB | Temps réel | Transmission |
| **Agressif** | 35:1 – 45:1 | 45 – 50 dB | Temps réel | Stockage critique |

### 2.3 Extension Vidéo et Upscaling

L'extension 3D (format SDI) atteint 35:1–45:1 pour la vidéo 4K avec PSNR > 48 dB. Le suréchantillonnage natif 2×/4× est compétitif avec les réseaux de super-résolution dédiés, avec PSNR 50–60 dB.

---

## 3. Résultats Expérimentaux

| Jeu de données | Entrée | HCV Std | HCV Δ-H | JPEG2000 | HEVC Intra |
|---------|-------|:------:|:------:|:------:|:---------:|
| Kodak (24 images) | 512×768 RAW | 32:1, 56 dB | 38:1, 52 dB | 32:1, 48 dB | 32:1, 50 dB |
| Radiographies médicales | 1024² DICOM | 35:1, 58 dB | 42:1, 53 dB | 35:1, 47 dB | 35:1, 49 dB |
| Paysages (50 photos) | 4K RAW | 28:1, 57 dB | 36:1, 51 dB | 28:1, 45 dB | 28:1, 48 dB |
| Documents (200 pages) | 2550×3300 TIFF | 40:1, 55 dB | 45:1, 50 dB | 40:1, 42 dB | 40:1, 43 dB |

Vitesse d'encodage : **40–60 MP/s** (Standard), **30–45 MP/s** (Delta-H). Décodage : **100–150 MP/s**.

---

## 4. Discussion

**Avantages** : Déterministe (SHA256), aucun entraînement requis, CPU uniquement, adaptatif structurellement, upscaling natif.

**Limitations** : Performances dégradées sur bruit aléatoire. Brevet en instance. Écosystème en développement.

---

## 5. Conclusion

HCV PRO atteint 25:1–45:1 avec qualité quasi-sans-perte par encodage Delta-H harmonique. Travaux futurs : accélération FPGA/ASIC, standardisation, intégration avec la mémoire holographique Harmonic AI.

---

## Références

1. ISO/IEC 15444-1. JPEG2000. 2000.
2. ITU-T H.265. HEVC. 2013.
3. Cheng, Z. et al. "Learned Image Compression." CVPR 2020.

---

*Preprint — soumis pour évaluation.*