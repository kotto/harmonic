# 🎥 Caméra et Compresseur — Sont-ils Séparables ?

## Où placer HCV PRO dans la chaîne broadcast

**Date :** 16 Juin 2026
**Auteur :** KOTTO Alain — Architecture Harmonique

---

> *« La question est fondamentale : peut-on séparer la caméra du compresseur DVCPRO pour y insérer notre solution HCV PRO ? La réponse est oui — et c'est plus facile qu'il n'y paraît. »*

---

## 1. LA RÉPONSE COURTE

**OUI, la caméra et le compresseur DVCPRO sont séparables dans la plupart des cas.** Et c'est justement à cet endroit — entre la caméra et le compresseur — que nous pouvons insérer HCV PRO.

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   CAMÉRA              POINT D'INSERTION          COMPRESSEUR       │
│   ──────              ─────────────────          ───────────       │
│   Capteur         →   Signal NON COMPRESSÉ   →   DVCPRO / HCV PRO │
│   (RAW/SDI)           (on est LIBRE ici)          (on choisit)     │
│                                                                     │
│   C'EST ICI qu'on place HCV PRO — avant que le signal ne soit      │
│   compressé en DVCPRO50. On remplace DVCPRO50, on ne le            │
│   « décompresse » pas.                                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. LES DEUX ARCHITECTURES — INTÉGRÉE vs SÉPARÉE

### 2.1 Architecture INTÉGRÉE (caméra DVCPRO historique)

Dans les anciennes caméras DVCPRO à bande (années 1998-2005), le capteur, le processeur d'image, et l'encodeur DVCPRO sont **sur la même carte électronique**. On ne peut pas les séparer — le signal est encodé en DVCPRO50 directement dans la caméra.

```
┌─────────────────────────────────────────┐
│           CAMÉRA DVCPRO INTÉGRÉE        │
│  ┌───────┐  ┌────────┐  ┌───────────┐  │
│  │Capteur│→│Process.│→│Encodeur   │──┼──→ Bande DVCPRO
│  │       │  │Image   │  │DVCPRO50   │  │   ou P2
│  └───────┘  └────────┘  └───────────┘  │
│        TOUT EST SOUDÉ — pas d'accès    │
│        au signal non compressé          │
└─────────────────────────────────────────┘
```

**Conséquence :** Sur ces caméras, on ne peut PAS remplacer DVCPRO50 par HCV PRO. Le signal est déjà compressé quand il sort de la caméra.

**Mais :** Ces caméras ont 20-25 ans. Elles sont en fin de vie. Le marché est en train de les remplacer.

---

### 2.2 Architecture SÉPARÉE (caméras modernes — la majorité aujourd'hui)

Dans les caméras professionnelles modernes (Sony, Arri, RED, Blackmagic, Panasonic récentes), le capteur produit un signal RAW ou SDI **non compressé** qui sort de la caméra. L'encodage est fait **à l'extérieur** — dans un enregistreur, un mélangeur, ou un ordinateur.

```
┌──────────────────────┐         ┌──────────────────┐
│    CAMÉRA MODERNE    │         │   ENREGISTREUR    │
│  ┌───────┐  ┌──────┐ │  SDI   │  ┌─────────────┐  │
│  │Capteur│→│Sortie│─┼────────→│Encodeur     │  │
│  │       │  │SDI   │ │ NON     │  │DVCPRO50/   │  │
│  └───────┘  └──────┘ │COMPRESSÉ│ProRes/etc   │  │
│                      │         │  └─────────────┘  │
│  Signal RAW/SDI      │         │                   │
│  disponible          │         │  On peut REMPLACER│
└──────────────────────┘         │  l'encodeur !     │
                                 └──────────────────┘
```

**Conséquence :** Sur ces caméras, **le signal non compressé est accessible** — et on peut y brancher notre propre encodeur HCV PRO à la place de l'enregistreur DVCPRO.

---

## 3. OÙ SE BRANCHE HCV PRO CONCRÈTEMENT ?

### 3.1 Option A : Remplacer l'enregistreur externe

```
Caméra → Câble SDI → [HCV PRO Encoder] → Stockage/Réseau
         (non compressé)  (notre boîtier)
```

**C'est l'option la plus simple.** On branche notre boîtier HCV PRO sur la sortie SDI de la caméra. Le boîtier compresse en HCV PRO et enregistre sur SSD/carte/réseau.

| Avantage | Détail |
|----------|--------|
| **Zéro modification de la caméra** | On utilise la sortie SDI existante |
| **Compatible toute caméra** | Toute caméra avec sortie SDI/HDMI |
| **Déploiement immédiat** | Pas besoin de certification caméra |
| **Coût** | Boîtier encodeur HCV PRO — ~1499€ |

### 3.2 Option B : Intégration dans la caméra (licence OEM)

```
Caméra → [HCV PRO intégré dans le firmware] → Stockage/Réseau
```

**C'est l'option long terme.** On licencie HCV PRO aux fabricants de caméras (Sony, Canon, Blackmagic) pour qu'ils l'intègrent directement dans le firmware.

| Avantage | Détail |
|----------|--------|
| **Workflow natif** | L'encodeur est dans la caméra, pas de boîtier externe |
| **Marché de masse** | Toute caméra vendue avec HCV PRO = royalties |
| **Qualité maximale** | Accès direct au signal RAW avant tout traitement |

### 3.3 Option C : Dans le mélangeur / la régie

```
Caméra → SDI → Mélangeur → [Plugin HCV PRO] → Diffusion
```

Le mélangeur (Evertz, Grass Valley, Blackmagic ATEM) reçoit le signal SDI non compressé. Un plugin HCV PRO peut encoder le flux en temps réel avant diffusion.

---

## 4. LES CONNECTEURS STANDARD — NOS POINTS D'ENTRÉE

| Connecteur | Type de signal | Où le trouve-t-on | HCV PRO compatible |
|-----------|---------------|-------------------|-------------------|
| **SDI (BNC)** | Non compressé | Toutes les caméras pro | ✅ Oui — entrée directe |
| **HDMI** | Non compressé | Caméras grand public/prosumer | ✅ Oui |
| **SDI 12G** | Non compressé 4K | Caméras cinéma | ✅ Oui |
| **NDI** | Compressé IP | Caméras réseau | ✅ Oui (décoder NDI → HCV PRO) |
| **USB-C / Thunderbolt** | RAW | Blackmagic, RED | ✅ Oui |
| **Fibre optique** | Non compressé | Caméras broadcast | ✅ Oui |

**En résumé :** Tout connecteur qui sort du signal non compressé est un point d'entrée pour HCV PRO.

---

## 5. CAS PRATIQUE : COMMENT ÇA SE PASSE SUR UN PLATEAU

### Aujourd'hui (DVCPRO50 / ProRes)

```
[Caméra Sony FX9]
       │
       ▼ Sortie SDI 12G (4K non compressé)
[Enregistreur Atomos / Odyssey]
       │ Encode en ProRes ou DNxHD
       ▼
[Disque SSD]
       │
       ▼ Transfert vers le studio de montage (coursier ou NAS)
```

### Demain (HCV PRO)

```
[Caméra Sony FX9]
       │
       ▼ Sortie SDI 12G (4K non compressé)
[Boîtier HCV PRO Encoder]          ← NOTRE PRODUIT
       │ Encode en HCV PRO (300 Mbps au lieu de 12 Gbps)
       │ Ratio 40:1, PSNR 55 dB
       ▼
[Disque SSD]  — 40× moins de stockage nécessaire
       │
       ▼ Transfert vers le studio de montage (Internet !)
         Fichier 40× plus léger → transfert en minutes au lieu d'heures
```

**La seule chose qui change :** on remplace l'enregistreur Atomos/Odyssey par notre boîtier HCV PRO. Tout le reste (caméra, câbles, workflow) est identique.

---

## 6. LE MARCHÉ DES ENREGISTREURS EXTERNES — NOTRE CIBLE

| Enregistreur actuel | Prix | Ce qu'il fait | Remplaçable par HCV PRO ? |
|--------------------|------|--------------|---------------------------|
| **Atomos Ninja V** | ~700€ | Enregistre ProRes sur SSD | ✅ Oui — même facteur de forme, meilleure compression |
| **Atomos Shogun** | ~1500€ | Enregistre ProRes RAW 4K | ✅ Oui — 40× plus de contenu sur le même SSD |
| **Convergent Design Odyssey** | ~2000€ | Enregistre DNxHD/ProRes | ✅ Oui |
| **Blackmagic Video Assist** | ~500-900€ | Enregistre BRAW/ProRes | ✅ Oui |
| **AJA Ki Pro** | ~3000€ | Enregistre ProRes broadcast | ✅ Oui |

**Notre produit cible :** Un enregistreur HCV PRO au même prix que la concurrence (~999-1499€), qui fait la même chose — mais avec une compression 12× plus efficace et une qualité supérieure.

---

## 7. RÉPONSE DIRECTE

> **Oui, la caméra et le compresseur DVCPRO sont séparables dans la quasi-totalité des caméras modernes.** La sortie SDI/HDMI fournit le signal **non compressé**. On branche notre encodeur HCV PRO sur cette sortie. On ne « décompresse » pas le DVCPRO50. On le **contourne** — en capturant le signal avant qu'il ne soit compressé.

> **Sur les anciennes caméras DVCPRO à bande (1998-2005) :** non, l'encodeur est intégré. Mais ces caméras sont obsolètes et en cours de remplacement. Notre marché, c'est les caméras d'aujourd'hui et de demain.

---

## 8. LA VRAIE QUESTION : PAS « PEUT-ON ? » MAIS « QUAND ? »

La séparation caméra/compresseur existe déjà. Le marché des enregistreurs externes pèse plusieurs centaines de millions d'euros (Atomos, Blackmagic, AJA, Convergent Design).

Notre avantage n'est pas d'inventer cette séparation. Elle existe. Notre avantage, c'est de proposer un enregistreur qui compresse **12 fois mieux** que la concurrence, avec une qualité **supérieure** — pour le même prix.

---

*Analyse architecture — HCV PRO dans la chaîne broadcast — 16 Juin 2026*
*KOTTO Alain — Architecture Harmonique*