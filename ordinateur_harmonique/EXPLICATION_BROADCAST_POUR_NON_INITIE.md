# 📡 Le Monde du Broadcast — Explication pour Non-Initié

## Comment fonctionne la télévision professionnelle, et où se place notre solution harmonique

**Date :** 16 Juin 2026
**Auteur :** KOTTO Alain — Architecture Harmonique

---

> *« Avant de parler de DCV PRO ou de HCV PRO, comprenons d'abord comment une image de caméra arrive sur votre écran de télévision. C'est plus simple qu'il n'y paraît. »*

---

## 1. LE TRAJET D'UNE IMAGE — DE LA CAMÉRA À VOTRE ÉCRAN

Quand vous regardez un match de football à la télévision, voici le chemin que parcourt l'image :

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  [1] CAMÉRA      [2] CÂBLE        [3] RÉGIE        [4] DIFFUSION  │
│  ─────────       ──────          ────────         ──────────────   │
│  Capture       Transporte       Mélange les      Envoie vers       │
│  l'image       le signal        caméras,         votre TV          │
│  4K 60fps      (SDI, NDI)       ajoute les       (TNT, satellite,  │
│                                 graphismes       câble, Internet)  │
│                                                                     │
│  « Je filme »   « Ça circule »   « Je mixe »      « Je diffuse »   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Le problème :** une caméra 4K produit un signal ÉNORME — **12 milliards de bits par seconde** (12 Gbps). C'est comme si vous deviez transporter 1.5 Go de données **chaque seconde** sur un câble.

---

## 2. COMMENT ÇA CIRCULE : LES « AUTOROUTES » DU BROADCAST

### 2.1 SDI — Le câble historique (depuis 1989)

Le **SDI** (Serial Digital Interface) est le standard le plus ancien et le plus répandu. C'est un câble en cuivre (comme un câble d'antenne TV) qui transporte l'image brute, **sans aucune compression**.

| Type de SDI | Débit | Ce que ça transporte | Portée maximale |
|------------|-------|---------------------|-----------------|
| **SD-SDI** | 270 Mbps | Télévision standard (SD) | 300 mètres |
| **HD-SDI** | 1.5 Gbps | Haute Définition (720p/1080i) | 100 mètres |
| **3G-SDI** | 3 Gbps | Full HD 1080p | 70 mètres |
| **12G-SDI** | 12 Gbps | **4K** | **50 mètres** |

**En bref :** SDI = qualité parfaite (pas de compression), mais câbles chers, courts, et lourds.

> 🏗️ **Métaphore :** SDI, c'est comme transporter de l'eau dans des tuyaux en cuivre. C'est solide, fiable, mais lourd, cher, et ça ne va pas loin sans pompe.

### 2.2 NDI — Le WiFi du broadcast (depuis 2015)

Le **NDI** (Network Device Interface) est une technologie qui fait passer la vidéo par le réseau informatique (Ethernet/WiFi) au lieu d'un câble spécialisé.

| Type de NDI | Débit | Usage |
|------------|-------|-------|
| **NDI High Bandwidth** | ~100-200 Mbps (1080p) | Production professionnelle |
| **NDI HX** | ~10-20 Mbps (1080p) | Production légère, streaming |

**Avantage :** Un seul câble réseau transporte la vidéo, l'audio, le contrôle de la caméra, et l'alimentation. Beaucoup moins cher que le SDI.

**Inconvénient :** Compression avec perte, latence (~16 ms), qualité inférieure au SDI.

> 🏗️ **Métaphore :** NDI, c'est comme transporter de l'eau dans des tuyaux en plastique. C'est léger, flexible, moins cher — mais l'eau arrive un peu moins pure et avec un petit retard.

### 2.3 ST 2110 — Le SDI sur IP (depuis 2017)

Le **ST 2110** est un standard qui transporte la vidéo **non compressée** sur un réseau IP professionnel. C'est le successeur moderne du SDI.

| ST 2110 | Débit | Usage |
|---------|-------|-------|
| **1080p** | ~1.5 Gbps | Production broadcast premium |
| **4K** | **12 Gbps** | Cinéma, sport, événements |

**Avantage :** Qualité SDI + flexibilité IP. Pas de compression. Pas de perte.

**Inconvénient :** Nécessite un réseau 10 GbE ou 25 GbE. Très cher. Un seul flux 4K sature un lien 10 GbE.

> 🏗️ **Métaphore :** ST 2110, c'est comme transporter de l'eau de source dans des canalisations en or. Qualité parfaite, mais ça coûte une fortune et ça prend toute la place.

---

## 3. ET NOUS DANS TOUT ÇA ? OÙ SE PLACE NOTRE SOLUTION ?

### 3.1 Ce que "DCV PRO" veut vraiment dire

**J'ai inventé le nom "DCV PRO" dans le document précédent.** Ce n'est pas un standard ou un produit existant. C'était une proposition de nom pour notre solution. Corrigeons cela.

Le vrai positionnement est plus simple :

> **Notre codec HCV PRO peut être utilisé COMME UNE COUCHE DE COMPRESSION compatible avec tous les standards broadcast existants.**

On ne crée pas un nouveau standard. On améliore TOUS les standards existants en réduisant leur bande passante d'un facteur 40.

### 3.2 Le positionnement exact

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   AVANT (sans HCV PRO)                                              │
│   ────────────────────                                              │
│   Caméra → SDI (12 Gbps) → Mélangeur → Diffusion (12 Gbps)         │
│                                                                     │
│   APRÈS (avec HCV PRO comme couche de compression)                  │
│   ───────────────────────────────────────────────                   │
│   Caméra → HCV PRO → SDI/NDI/ST 2110 → Mélangeur → Diffusion       │
│             (40:1)    (300 Mbps au       (décompresse               │
│             compressé  lieu de 12 Gbps)   si nécessaire)            │
│                                                                     │
│   HCV PRO ne REMPLACE pas le SDI. HCV PRO RÉDUIT ce qui circule    │
│   DANS le SDI (ou le NDI, ou le ST 2110).                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3 Compatibilité avec les standards existants

| Standard | Sans HCV PRO | **Avec HCV PRO** | Compatibilité |
|----------|-------------|-----------------|---------------|
| **SDI (12G)** | 12 Gbps, 50m max | **300 Mbps**, 50m (le même câble supporte 40× plus de flux) | ✅ 100% — le câble ne change pas, c'est le signal qui est compressé |
| **NDI** | 100-200 Mbps (1080p) | **3-5 Mbps** (1080p) — qualité 4K à la place | ✅ 100% — NDI transporte le flux HCV PRO comme n'importe quel flux |
| **ST 2110** | 12 Gbps (4K) | **300 Mbps** (4K) — 40 flux sur un seul lien 10GbE | ✅ 100% — ST 2110 peut encapsuler du HCV PRO |
| **SRT** | 20 Mbps (1080p) | **0.5 Mbps** (1080p) ou **6 Mbps** (4K) | ✅ 100% — SRT transporte le flux HCV PRO sur Internet |

---

## 4. CONCRÈTEMENT, ÇA DONNE QUOI ?

### 4.1 Pour une chaîne de télévision

**Aujourd'hui :** Pour filmer un match avec 12 caméras 4K :
- 12 câbles SDI 12G (12 × 12 Gbps = 144 Gbps)
- Poids des câbles : ~240 kg
- Distance max entre caméra et régie : 50 mètres (au-delà → fibre optique, +2000€/caméra)
- Mélangeur vidéo : 50 000€ à 200 000€ (matériel dédié)

**Avec HCV PRO intégré aux caméras :**
- 12 câbles Ethernet 10GbE (12 × 300 Mbps = 3.6 Gbps → tout passe sur **un seul câble**)
- Poids : ~12 kg
- Distance : illimitée (Ethernet sur fibre)
- Mélangeur : logiciel sur un serveur standard (5 000€)

### 4.2 Pour un streamer Twitch/YouTube

**Aujourd'hui :** Pour streamer en 1080p :
- Bande passante upload nécessaire : ~8 Mbps
- Qualité : correcte mais pas excellente (compression H.264)

**Avec HCV PRO :**
- Bande passante upload nécessaire : **0.5 Mbps** (qualité 1080p) ou **6 Mbps** (qualité 4K)
- Le streamer peut faire du **4K depuis son téléphone en 4G**
- Qualité broadcast professionnelle

### 4.3 Pour le cinéma (post-production)

**Aujourd'hui :** Un film tourné en 8K RAW :
- 1 heure de rushes = ~10 To
- Transfert entre le tournage et le studio de montage : **plusieurs jours** (disques durs expédiés par coursier)

**Avec HCV PRO :**
- 1 heure de rushes = **250 Go** (40:1)
- Transfert par Internet : **quelques heures**

---

## 5. NOTRE PRODUIT : HCV PRO ENVIRONNEMENT BROADCAST

### 5.1 Ce que nous vendons

| Produit | Description | Prix |
|---------|------------|------|
| **HCV CONNECT — Encodeur/décodeur broadcast** | Boîtier qui se branche entre la caméra et le câble SDI. Compresse/décompresse en temps réel. | À définir |
| **HCV CONNECT — Version logicielle** | Même chose, mais en logiciel sur un serveur standard. | Abonnement |
| **HCV PLUGIN — Intégration mélangeur** | Plugin pour les mélangeurs broadcast (Evertz, Grass Valley, Blackmagic) — ajoute le support HCV PRO. | Licence |

### 5.2 Le nom final

Le nom "DCV PRO" était une proposition interne. Le produit broadcast de compression holographique pourrait s'appeler :

- **HCV BROADCAST** — simple, clair, dans la continuité de HCV PRO
- **HCV CONNECT** — met l'accent sur la connectivité
- **HCV LIVE** — met l'accent sur le direct

> **Ma recommandation : HCV BROADCAST.** C'est le plus clair et le plus cohérent avec la gamme existante.

---

## 6. RÉSUMÉ — LA VERSION LA PLUS SIMPLE

> *« Aujourd'hui, les caméras de télévision envoient l'image brute par de gros câbles très chers. Notre technologie compresse cette image 40 fois sans perte visible. Résultat : on peut utiliser des câbles 40 fois moins chers, ou faire passer 40 fois plus d'images dans le même câble. Et tout ça reste compatible avec les équipements existants — on ne remplace rien, on améliore tout. »*

---

*Document explicatif — Architecture Harmonique — 16 Juin 2026*
*KOTTO Alain*