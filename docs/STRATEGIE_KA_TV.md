# KA TV — L'Alternative Harmonique à la Télévision par Satellite en Afrique

**Document** : STRAT-KATV-1.0  
**Date** : Juillet 2026  
**Auteur** : Alain Kotto — Projet Univers Harmonique  
**Statut** : Proposition stratégique (v1.0)
**Dépendances** : SPEC_IA_HARMONIQUE_ECOSYSTEM.md (IA Harmonique), SPEC_TECHNIQUE_KA_PAY.md (KA PAY)

---

## Résumé Exécutif

**KA TV** est une offre de télévision over-the-top (OTT) pour le continent africain, exploitant la compression harmonique HCV (119,5× sur les images → 30-50× sur la vidéo) pour diffuser de la télévision en qualité HD sur des réseaux 2G/3G, sans parabole, sans décodeur, sans abonnement coûteux.

**Le constat** : Canal+ et ses 23 millions d'abonnés africains (post-rachat de MultiChoice) ne couvrent que **3%** de la population du continent. Le ticket d'entrée (parabole + décodeur = 13-38€) et l'abonnement mensuel (5-45€) excluent 97% des Africains. Pourtant, **91,8%** des Africains connectés regardent déjà des vidéos chaque semaine — sur leur téléphone.

**La solution** : La compression harmonique HCV réduit la bande passante vidéo d'un facteur 30-50× par rapport au H.265 standard. Un film 1080p de 2h passe de 4,5 Go à 90-150 Mo. À 0,42$/Go (prix data Nigeria), cela représente **0,04$ le film**. Diffusé via une application mobile légère, KA TV peut offrir une expérience de télévision complète (direct + VOD) pour **1,50-3€/mois** — soit 10 à 50 fois moins cher que Canal+.

**L'ambition** : 100 millions d'utilisateurs africains d'ici 2030, en commençant par un pilote dans un pays francophone (Bénin ou Sénégal) avec 50K€ d'investissement initial.

> *« Canal+ a besoin d'une parabole. KA TV a besoin d'un téléphone. 97% des Africains ont déjà le téléphone. »*

---

## Table des Matières

1. [Analyse du Marché](#1-analyse-du-marché)
2. [L'Arme Technologique : La Compression Harmonique](#2-larme-technologique--la-compression-harmonique)
3. [Architecture du Produit KA TV](#3-architecture-du-produit-ka-tv)
4. [Infrastructure de Diffusion](#4-infrastructure-de-diffusion)
5. [Modèle Économique](#5-modèle-économique)
6. [Analyse Concurrentielle](#6-analyse-concurrentielle)
7. [Stratégie de Mise sur le Marché](#7-stratégie-de-mise-sur-le-marché)
8. [Roadmap Technique](#8-roadmap-technique)
9. [Spécifications Techniques Détaillées](#9-spécifications-techniques-détaillées)
10. [Projections Financières](#10-projections-financières)
11. [Risques et Mitigations](#11-risques-et-mitigations)
12. [Prochaines Actions](#12-prochaines-actions)

---

## 1. Analyse du Marché

### 1.1 Le marché africain de la TV payante aujourd'hui

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   MARCHÉ TOTAL PAY-TV AFRIQUE : ~43 millions d'abonnés           │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  Canal+ / MultiChoice  ████████████████████████  23M     │  │
│   │  StarTimes             ██████████                  10M     │  │
│   │  Autres (TNT, locaux)  ██████████                  10M     │  │
│   │  Netflix/Showmax/Prime █                            1M     │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│   POPULATION TOTALE AFRIQUE : 1,4 milliard                       │
│   TAUX DE PÉNÉTRATION PAY-TV : ~3%                               │
│                                                                  │
│   97% DES AFRICAINS N'ONT PAS ACCÈS À LA TV PAYANTE              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 1.2 Pourquoi si peu d'abonnés ?

| Barrière | Détail |
|----------|--------|
| **Ticket d'entrée** | Parabole + décodeur + installation = 13-38€ (1-3 semaines de salaire moyen) |
| **Abonnement** | 5-45€/mois, payable par carte bancaire (pénétration bancaire < 20%) |
| **Électricité** | 600M d'Africains sans accès à l'électricité fiable |
| **Mobilité** | La TV satellite est fixe. Les Africains sont mobiles. |
| **Maintenance** | Parabole désalignée = plus de signal. Décodeur en panne = pas de SAV. |

### 1.3 Le vrai marché : la vidéo sur mobile

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   COMPORTEMENT RÉEL DES AFRICAINS CONNECTÉS                      │
│                                                                  │
│   · 91,8% regardent des vidéos chaque semaine                    │
│   · 75% consomment le contenu sur smartphone                     │
│   · La data mobile coûte 0,42-2$/Go (en baisse constante)        │
│   · YouTube est la « télévision nationale » de facto             │
│   · Le marché CTV (Connected TV) vaudra 16 milliards $ en 2034   │
│                                                                  │
│   LE BESOIN EXISTE. LE RÉSEAU EXISTE. L'APPAREIL EXISTE.         │
│   IL MANQUE JUSTE LA BONNE COMPRESSION.                          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 1.4 L'érosion de Canal+

MultiChoice a perdu **4 millions d'abonnés en 18 mois** avant son rachat par Canal+. Raisons :

- Crise des devises (naira, cedi, shilling) qui rend l'abonnement impayable
- Concurrence du streaming (YouTube gratuit, Netflix à 3€/mois)
- Piratage massif des décodeurs satellite
- Coupures d'électricité qui rendent la TV inutilisable

**David Mignot, DG Canal+ Afrique** : *« Le ticket d'entrée est trop élevé, il dissuade les nouveaux abonnés. »* — Et pourtant, même avec des décodeurs à -40%, ils restent hors de portée du marché de masse.

---

## 2. L'Arme Technologique : La Compression Harmonique

### 2.1 Le principe

La compression harmonique (HCV) ne compresse pas les pixels comme H.264/H.265 (DCT + motion estimation). Elle calcule une **signature harmonique DFT** pour chaque fragment de l'image, puis cherche cette signature dans un **dictionnaire spectral partagé** de 1,2 million de patches naturels. Quand elle trouve un match, elle transmet seulement **6 octets** (shard_id + patch_id) au lieu des données brutes.

```
ENCODE :
  Frame → Patches 13×13 → [DFT → Signature 512D]
       → KD-Tree → Dictionnaire (1,2M patches)
       → Si match : 6 octets (lossless)
       → Si non : Delta-H + zstd → résiduel compressé

DECODE :
  Bitstream → Pour chaque patch :
       → Si ID seul : lookup dictionnaire → patch exact
       → Si résiduel : lookup + décompresser → reconstruction
  → Assemblage → Frame
```

### 2.2 Les chiffres qui changent tout

| Métrique | Valeur HCV | Comparaison |
|----------|-----------|-------------|
| **Compression image (lossless)** | **119,5×** | PNG = 3,3×. JPEG lossless = 2-4× |
| **PSNR** | **100 dB** | Qualité parfaite, SSIM = 1,000 |
| **Temps d'encodage** | 300 ms (400×400) | Optimisable en C/Rust (10-50× plus rapide) |
| **Temps de décodage** | 60 ms (400×400) | Décodeur mobile = ~200 lignes Python |
| **RAM décodeur** | ~90 Mo constant | Indépendant de la taille du dictionnaire |

### 2.3 Projection vidéo

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│   ESTIMATION CONSERVATRICE DE LA COMPRESSION VIDÉO HCV            │
│                                                                    │
│   Hypothèses :                                                     │
│   · Patches 13×13, I-frame tous les 30 frames                      │
│   · 70% des patches P-frame = skip (inchangés)                     │
│   · 20% = dict match (6 octets), 10% = résiduel compressé          │
│   · Taille moyenne par patch P-frame : ~25 octets                  │
│                                                                    │
│   RÉSULTATS PAR RÉSOLUTION :                                       │
│                                                                    │
│   ┌──────────┬──────────────┬──────────────┬──────────────────┐   │
│   │ Résolution│ H.265 standard│ HCV harmonique│ Ratio compression│  │
│   ├──────────┼──────────────┼──────────────┼──────────────────┤   │
│   │ 4K       │ 25 Mbps      │ 0,5-0,8 Mbps │ 30-50×          │   │
│   │ 1080p    │ 5 Mbps       │ 100-170 kbps │ 30-50×          │   │
│   │ 720p     │ 2,5 Mbps     │ 50-80 kbps   │ 30-50×          │   │
│   │ 480p     │ 1 Mbps       │ 25-40 kbps   │ 25-40×          │   │
│   │ 360p     │ 0,5 Mbps     │ 12-20 kbps   │ 25-40×          │   │
│   └──────────┴──────────────┴──────────────┴──────────────────┘   │
│                                                                    │
│   CONSÉQUENCE DIRECTE :                                            │
│   · 1080p en 3G (384 kbps théorique)                              │
│   · 720p en EDGE/2G (236 kbps)                                    │
│   · 480p en GPRS (85 kbps)                                         │
│   · Un film 2h 1080p = 90-150 Mo (vs 4,5 Go en H.265)             │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### 2.4 Impact sur le coût data

| Pays | Prix data/Go | Coût film 2h (HCV 1080p) | Coût film 2h (H.265) | Économie |
|------|-------------|--------------------------|---------------------|----------|
| Nigeria | 0,42 $ | **0,04-0,06 $** | 1,89 $ | **97%** |
| Côte d'Ivoire | 1,50 $ | **0,14-0,23 $** | 6,75 $ | **97%** |
| Sénégal | 2,00 $ | **0,18-0,30 $** | 9,00 $ | **97%** |
| Afrique du Sud | 1,20 $ | **0,11-0,18 $** | 5,40 $ | **97%** |

---

## 3. Architecture du Produit KA TV

### 3.1 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                        KA TV — ARCHITECTURE                         │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     COUCHE CONTENU                            │  │
│  │  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌───────┐ │  │
│  │  │ Chaînes │ │   VOD   │ │  Contenu │ │  Éduca- │ │Religi-│ │  │
│  │  │  Live   │ │ Nollywood│ │ Communauté│ │  tion   │ │ eux   │ │  │
│  │  └─────────┘ └─────────┘ └──────────┘ └─────────┘ └───────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                   COUCHE COMPRESSION                          │  │
│  │  ┌────────────────────────────────────────────────────────┐  │  │
│  │  │  Encodeur HCV Vidéo (I/P frames, dict 1,2M patches)    │  │  │
│  │  │  · Qualités : 144p → 4K                                │  │  │
│  │  │  · Bitrates : 12 kbps → 800 kbps                       │  │  │
│  │  │  · Profils : Éco / Standard / Fidèle / Parfaite         │  │  │
│  │  └────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  COUCHE DISTRIBUTION                          │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │  │
│  │  │  CDN     │ │  RTHC    │ │  P2P     │ │  Satellite   │   │  │
│  │  │ Cloudflare│ │ Mesh     │ │ Device   │ │  Backhaul    │   │  │
│  │  │ (global) │ │ Village  │ │ Sharing  │ │  (injection) │   │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  COUCHE CLIENT                                 │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │  │
│  │  │ Android  │ │ iOS      │ │ PWA      │ │ Feature      │   │  │
│  │  │ App      │ │ App      │ │ (KaiOS)  │ │ Phone (USSD) │   │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Fonctionnalités clés

| Fonctionnalité | Description | Priorité |
|---------------|-------------|----------|
| **TV en direct** | 20-50 chaînes linéaires (info, sport, divertissement, musique, religion) | P0 |
| **VOD** | Bibliothèque de films/séries Nollywood, africains, internationaux | P0 |
| **Téléchargement offline** | Télécharger pour regarder plus tard sans connexion | P0 |
| **Contenu communautaire** | Upload et partage par les créateurs locaux | P1 |
| **Live streaming** | Tout utilisateur peut diffuser en direct | P1 |
| **Radio** | Streaming audio HCV (1 kbps) : 100+ radios communautaires | P1 |
| **KA Care intégré** | Vidéos éducatives santé, dépistages visuels | P1 |
| **Cast TV** | Envoyer vers une TV via Chromecast/Miracast/WiFi Direct | P2 |
| **Paiement mobile money** | M-Pesa, Orange Money, MTN Mobile Money, Wave | P0 |
| **Multi-langues** | Interface en 20+ langues africaines | P1 |
| **Sous-titres** | Générés automatiquement en langues locales | P2 |

### 3.3 Profils de qualité adaptative

| Profil | Résolution max | Bitrate | Utilisation data/heure | Réseau minimum |
|--------|---------------|---------|----------------------|----------------|
| **Éco** | 360p | 12-20 kbps | 5-9 Mo | GPRS |
| **Standard** | 480p | 25-40 kbps | 11-18 Mo | EDGE |
| **HD** | 720p | 50-80 kbps | 22-36 Mo | 3G |
| **Full HD** | 1080p | 100-170 kbps | 45-76 Mo | 3G+ |
| **4K** | 2160p | 500-800 kbps | 225-360 Mo | 4G/WiFi |

---

## 4. Infrastructure de Diffusion

### 4.1 Les 4 piliers de distribution

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                 STRATÉGIE DE DISTRIBUTION MULTI-COUCHES              │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  TIER 1 : CDN MONDIAL (Cloudflare / BunnyCDN)                 │ │
│  │  ─────────────────────────────────────────                     │ │
│  │  · Pour les utilisateurs urbains avec 3G/4G                   │ │
│  │  · Contenu HCV pré-encodé, stocké en edge cache               │ │
│  │  · Coût CDN : ~0,01$/Go (vs 0,05-0,10$ standard)             │ │
│  │  · Latence : < 50 ms dans les grandes villes africaines        │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  TIER 2 : RTHC — RÉSEAU COMMUNAUTAIRE (Zones rurales)        │ │
│  │  ─────────────────────────────────────────                     │ │
│  │  · Wi-Fi HaLow (900 MHz) : portée 1-3 km par point d'accès   │ │
│  │  · Backhaul 5 GHz directionnel : inter-villages 5-30 km       │ │
│  │  · Nœud de cache local : 1 To de contenu pré-chargé           │ │
│  │  · Coût marginal : 0,15€/mois/famille (déjà prévu RTHC)      │ │
│  │  · Indépendant des opérateurs télécom                         │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  TIER 3 : P2P — PARTAGE ENTRE APPAREILS                       │ │
│  │  ─────────────────────────────────────────                     │ │
│  │  · Protocole inspiré de BitTorrent + IPFS                      │ │
│  │  · Contenu populaire = distribué localement, zéro data mobile │ │
│  │  · Partage via WiFi Direct / Bluetooth / HaLow                │ │
│  │  · Chaque appareil = cache + relais                           │ │
│  │  · Incitation : partager = crédits data gagnés                │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  TIER 4 : SATELLITE BACKHAUL (Injection de contenu)           │ │
│  │  ─────────────────────────────────────────                     │ │
│  │  · Contenu live injecté via Starlink ou Eutelsat              │ │
│  │  · Distribué localement via RTHC + P2P                        │ │
│  │  · 1 point d'injection pour 5-20 villages                     │ │
│  │  · Évite de saturer le backhaul internet du village           │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Flux de diffusion d'un match de football en direct

```
                    STADE (Caméras)
                         │
                         ▼
               ┌─────────────────┐
               │  RÉGIE CENTRALE │
               │  Encodeur HCV   │
               │  Temps réel     │
               └────────┬────────┘
                        │
           ┌────────────┼────────────┐
           ▼            ▼            ▼
     Starlink      Fibre optique  4G/5G
     (zones        (capitales)    (backup)
      rurales)
           │            │            │
           └────────────┼────────────┘
                        │
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
  ┌─────────┐    ┌──────────┐    ┌──────────┐
  │  CDN    │    │ Nœud RTHC│    │ Nœud RTHC│
  │ Global  │    │ Village A│    │ Village B│
  └────┬────┘    └────┬─────┘    └────┬─────┘
       │              │               │
       ▼              ▼               ▼
  ┌─────────┐   ┌──────────┐   ┌──────────┐
  │Urbains  │   │ HaLow AP │   │ HaLow AP │
  │3G/4G    │   │ 900 MHz  │   │ 900 MHz  │
  └────┬────┘   └────┬─────┘   └────┬─────┘
       │              │               │
       ▼              ▼               ▼
    📱📱📱         📱📱📱          📱📱📱
  (et P2P entre téléphones dans le même village)
```

---

## 5. Modèle Économique

### 5.1 Structure Freemium

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   GRATUIT                      PREMIUM                              │
│   ────────                     ────────                              │
│                                                                     │
│   ✓ 10 chaînes live            ✓ 50+ chaînes live                   │
│   ✓ Qualité max 480p           ✓ Jusqu'à 1080p/4K                   │
│   ✓ VOD limité (10h/mois)      ✓ VOD illimité                       │
│   ✓ Publicités (3 min/h)       ✓ Zéro publicité                     │
│   ✓ 1 appareil                 ✓ Jusqu'à 5 appareils (famille)     │
│   ✓ Contenu communauté         ✓ Contenu exclusif                   │
│   ✗ Sports live                ✓ Sports live (SuperSport-like)      │
│   ✗ Téléchargement offline     ✓ Téléchargement offline illimité    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Grille tarifaire

| Formule | Prix/jour | Prix/semaine | Prix/mois | Prix/an |
|---------|-----------|-------------|-----------|---------|
| **Gratuit** | Gratuit | Gratuit | Gratuit | Gratuit |
| **Premium** | 0,10 $ | 0,50 $ | **1,50 $** | **15 $** |
| **Famille** (5 appareils) | — | 1,00 $ | **3,00 $** | **30 $** |
| **Sport** (add-on) | 0,20 $ | 1,00 $ | 3,00 $ | 30 $ |

Comparaison Canal+ : 5-45€/mois (5-50$). **KA TV est 3 à 30 fois moins cher.**

### 5.3 Paiement Mobile Money

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   PAS DE CARTE BANCAIRE NÉCESSAIRE                                  │
│                                                                     │
│   · M-Pesa (Afrique de l'Est — 50M+ utilisateurs)                   │
│   · Orange Money (Afrique de l'Ouest — 80M+ utilisateurs)           │
│   · MTN Mobile Money (15 pays africains — 60M+ utilisateurs)        │
│   · Wave (Sénégal, Côte d'Ivoire — 15M+ utilisateurs)               │
│   · Airtel Money (14 pays africains)                                │
│   · FreeMoney / Moov Money                                          │
│                                                                     │
│   Paiement par :                                                    │
│   · Code USSD (*123#) — compatible avec tous les téléphones        │
│   · QR Code chez les revendeurs locaux                              │
│   · Carte prépayée KA TV vendue chez les kiosques                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.4 Flux de revenus

| Source | Description | Part estimée du CA |
|--------|-------------|-------------------|
| **Abonnements Premium** | 1,50-3$/mois/utilisateur | 60% |
| **Publicité** | Spots locaux ciblés, non-intrusifs | 20% |
| **Partenariats télécom** | Zero-rating, partage de revenu data | 10% |
| **Contenu exclusif** | Pay-per-view (matches, concerts) | 5% |
| **Licence HCV** | Licence du codec à d'autres plateformes | 5% |

### 5.5 Économie unitaire (par utilisateur)

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   UTILISATEUR GRATUIT :                                             │
│   · Revenu pub : 0,15-0,30$/mois                                   │
│   · Coût CDN : 0,02$/mois (10h visionnage, 480p)                   │
│   · MARGE : 0,13-0,28$/mois                                        │
│                                                                     │
│   UTILISATEUR PREMIUM :                                             │
│   · Revenu abonnement : 1,50$/mois                                 │
│   · Revenu pub : 0$ (pas de pubs)                                  │
│   · Coût CDN : 0,05$/mois (30h visionnage, 720p)                   │
│   · Coût contenu : 0,30$/mois (licences)                           │
│   · Coût paiement : 0,05$/mois (frais mobile money)                │
│   · MARGE : 1,10$/mois                                              │
│                                                                     │
│   À l'échelle de 10M d'utilisateurs (5% convertis en Premium) :     │
│   · CA annuel : 103M$                                               │
│   · Marge brute : 75M$                                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Analyse Concurrentielle

### 6.1 Comparatif direct : KA TV vs Canal+

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   FACTEUR              CANAL+                  KA TV                │
│   ───────              ───────                  ─────                │
│                                                                     │
│   Installation         Parabole+décodeur        Téléchargement app  │
│                        (13-38€, technicien)     (0€, 30 secondes)   │
│                                                                     │
│   Matériel requis      TV + décodeur            Smartphone seul     │
│                        + parabole + électricité (85% en ont déjà)   │
│                                                                     │
│   Abonnement mensuel   5-45€                    0-3€                │
│                                                                     │
│   Paiement             Carte bancaire            Mobile money       │
│                        (<20% de pénétration)     (>50% de pénétration)│
│                                                                     │
│   Mobilité             Fixe (un seul téléviseur) Partout, tout le temps│
│                                                                     │
│   Data consommée       Aucune (satellite)       30-150 Mo/film HD   │
│                                                                     │
│   Fonctionne sans      NON (décodeur + TV)      OUI (batterie tel) │
│   électricité          ───                      ───                 │
│                                                                     │
│   Contenu local        Limité (Canal+ Original) Massif (communauté) │
│                                                                     │
│   Marché adressable    3% de la population       97% de la population│
│                                                                     │
│   Barrière à l'entrée  TRÈS ÉLEVÉE               NULLE              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Positionnement dans l'écosystème

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                        QUALITÉ VIDÉO                                │
│                             ↑                                       │
│                     4K ─    │    ┌─────────┐                       │
│                             │    │  CANAL+ │                        │
│                   1080p ─   │    │  DSTV   │    ┌─────────┐        │
│                             │    └─────────┘    │  KA TV  │        │
│                    720p ─   │                   │ PREMIUM │        │
│                             │    ┌─────────┐    └─────────┘        │
│                    480p ─   │    │ NETFLIX │                       │
│                             │    │ MOBILE  │    ┌─────────┐        │
│                    360p ─   │    └─────────┘    │  KA TV  │        │
│                             │                   │ GRATUIT │        │
│                    144p ─   │                   └─────────┘        │
│                             │                                       │
│                             │    ┌─────────┐                       │
│                             │    │ YOUTUBE │                        │
│                             │    │ (gratuit│                       │
│                             │    │ mais pub)│                       │
│                             │    └─────────┘                       │
│                             └─────────────────────────→ PRIX       │
│                             0$    3$     10$     30$     50$       │
│                                                                     │
│   KA TV occupe le quadrant INOCCUPÉ : haute qualité, prix nul/faible│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.3 Avantages compétitifs défendables (moat)

| Avantage | Type | Durabilité |
|----------|------|-----------|
| **Compression HCV** | Technologique | 5-10 ans (brevet Soleau + avance algorithmique) |
| **Dictionnaire harmonique** | Données | Permanent (1,2M patches optimisés) |
| **Réseau RTHC** | Infrastructure | Très difficile à répliquer (communautaire) |
| **Paiement mobile money** | Distribution | Difficile (accords multi-opérateurs) |
| **Contenu communautaire** | Effet réseau | Croît avec la base utilisateurs |
| **Marque « KA »** | Confiance | Construite via KA Phone + KA Care |

---

## 7. Stratégie de Mise sur le Marché

### 7.1 Phase 1 : PILOTE — « La Preuve » (Mois 1-6)

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   PAYS CIBLE : Bénin ou Sénégal (francophone, stable, connecté)    │
│                                                                     │
│   OBJECTIFS :                                                       │
│   · Valider le codec HCV en conditions réelles                      │
│   · Mesurer la rétention et l'engagement                            │
│   · Prouver le paiement mobile money                                │
│   · 10 000 utilisateurs                                             │
│                                                                     │
│   ACTIONS CLÉS :                                                    │
│   · Développer l'app Android MVP + PWA                              │
│   · Intégrer le décodeur HCV mobile                                 │
│   · Licence 50 films Nollywood + 20 chaînes locales                 │
│   · Accord zero-rating avec 1 opérateur (Orange ou MTN)             │
│   · Recruter 20 créateurs de contenu locaux                         │
│   · Campagne WhatsApp + Facebook + influenceurs locaux              │
│                                                                     │
│   BUDGET : 50 000€                                                  │
│   · Développement app : 20 000€                                     │
│   · Licences contenu : 10 000€                                      │
│   · Marketing : 10 000€                                             │
│   · Infrastructure : 5 000€                                         │
│   · Équipe locale : 5 000€                                          │
│                                                                     │
│   KPI CLÉ :                                                         │
│   · Rétention Jour 30 > 40%                                         │
│   · Temps de visionnage > 45 min/jour                               │
│   · Taux de conversion Gratuit → Premium > 3%                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 Phase 2 : EXPANSION — « La Vague Francophone » (Mois 7-18)

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   PAYS : 5 pays Afrique francophone (Bénin, Sénégal, Côte d'Ivoire,│
│          Cameroun, Burkina Faso)                                    │
│                                                                     │
│   OBJECTIFS :                                                       │
│   · 500 000 utilisateurs                                            │
│   · Déploiement RTHC dans 10 villages pilotes                       │
│   · 500 créateurs de contenu                                        │
│                                                                     │
│   ACTIONS CLÉS :                                                    │
│   · Portage Android natif (Kotlin) + SDK iOS                        │
│   · Encodeur HCV temps réel (C/Rust)                                │
│   · Intégration StarTimes / chaînes TNT pour contenu live           │
│   · Partenariats avec 3 opérateurs télécom                          │
│   · Lancement P2P sharing                                           │
│                                                                     │
│   BUDGET : 500 000€                                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.3 Phase 3 : PANAFRICAINE — « Le Raz-de-Marée » (Mois 19-36)

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   PAYS : 25 pays africains (francophones, anglophones, lusophones) │
│                                                                     │
│   OBJECTIFS :                                                       │
│   · 10 millions d'utilisateurs                                      │
│   · RTHC dans 500 villages                                          │
│   · 5 000 créateurs de contenu                                      │
│   · Licence HCV vendue à 3 opérateurs télécom                       │
│                                                                     │
│   BUDGET : 5 000 000€                                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.4 Phase 4 : GLOBAL SOUTH — « Le Standard » (Année 4+)

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   EXPANSION : Asie du Sud, Amérique Latine, Asie du Sud-Est         │
│                                                                     │
│   OBJECTIF : 100 millions d'utilisateurs                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Roadmap Technique

### 8.1 Ce qui existe déjà (Juillet 2026)

```
✅ FINALISÉ :
   ├── Codec I/P-frames vidéo (harmonic_codec.py)
   ├── Décodeur mobile HHD2 (mobile_decoder.py, ~200 lignes)
   ├── Dictionnaire harmonique 1,2M patches (119,5×)
   ├── Encodeur vidéo offline (encode_video / decode_video)
   ├── Serveur streaming (ka_server.py : /api/media/video)
   ├── BackgroundCompressor (compression asynchrone)
   ├── Codec vocal 1200 bps (harmonic_voice_codec.py)
   ├── Réseau RTHC (spécification complète, BOM prototype)
   └── Paiement mobile money (intégrable)
```

### 8.2 Ce qu'il faut construire

```
🔧 PHASE 1 (Mois 1-3) — MVP :
   ├── App Android PWA avec lecteur HCV intégré
   ├── Adaptive bitrate selector (détection réseau automatique)
   ├── Intégration mobile money (Orange Money, MTN, Wave)
   ├── Backend de gestion des abonnements
   ├── Pipeline d'encodage par lot (bibliothèque VOD)
   └── Dashboard analytics (rétention, engagement, revenus)

🔧 PHASE 2 (Mois 4-12) — Passage à l'échelle :
   ├── Encodeur HCV temps réel en C/Rust (10-50× plus rapide)
   ├── Protocole streaming adaptatif (HLS-like avec segments HCV)
   ├── SDK Android natif (Kotlin) + iOS (Swift)
   ├── P2P distribution protocol (BitTorrent-like, WiFi Direct)
   ├── Intégration RTHC (cache local + distribution HaLow)
   ├── Pipeline live streaming (ingest → encode HCV → distribute)
   └── CDN multi-POP africain (Cloudflare + edge nodes locaux)

🔧 PHASE 3 (Mois 13-24) — Industrialisation :
   ├── DRM / watermarking (protection contenu premium)
   ├── Recommendation engine (IA Harmonique, pas deep learning — voir SPEC_IA_HARMONIQUE_ECOSYSTEM.md)
   ├── Syndication API (chaînes tierces peuvent utiliser HCV)
   ├── SDK Set-top box (Android TV, Raspberry Pi)
   ├── Intégration satellite DTH hybride (broadcast + HCV unicast)
   └── Portage KaiOS (150M feature phones en Afrique)
```

### 8.3 Stack technique cible

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   BACKEND :                                                         │
│   · API : FastAPI (existant) → Go/Rust pour haute performance       │
│   · Base de données : PostgreSQL + Redis cache                      │
│   · Stockage : S3-compatible (Wasabi/Cloudflare R2)                 │
│   · CDN : Cloudflare + BunnyCDN + nœuds RTHC                        │
│   · Encodage : Workers GPU/CUDA pour batch, C/Rust pour temps réel  │
│                                                                     │
│   FRONTEND :                                                        │
│   · Android : Kotlin natif + décodeur C via JNI                     │
│   · iOS : Swift natif + décodeur C via FFI                          │
│   · PWA : React + Service Worker (fallback tous appareils)          │
│   · Feature phones : USSD menu + streaming audio uniquement         │
│                                                                     │
│   DÉCODEUR HCV :                                                    │
│   · Core : C library (libhcv) avec bindings Python/Java/Swift       │
│   · Dictionnaire : fichier .hhdm compact (~200 Mo JPEG, ~977 Mo RGB565)│
│   · RAM : < 100 Mo constant                                        │
│   · CPU : < 5% sur un processeur mobile récent                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 9. Spécifications Techniques Détaillées

### 9.1 Format de bitstream vidéo HCV

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   BITSTREAM VIDÉO HCV (HHDV - Harmonic Dictionary Video)            │
│                                                                     │
│   ┌─────────┬────────┬──────────┬────────────────────────────────┐ │
│   │ Magic   │Version │  Flags   │         GOP Data               │ │
│   │ 'HHDV'  │   1    │  1 byte  │      (variable length)         │ │
│   │  4 B    │  1 B   │          │                                │ │
│   └─────────┴────────┴──────────┴────────────────────────────────┘ │
│                                                                     │
│   GOP Data = [I-FRAME] [P-FRAME] [P-FRAME] ... [P-FRAME]           │
│                                                                     │
│   I-FRAME :                                                         │
│   ┌──────┬──────┬──────┬──────────────────────────────────────┐   │
│   │ Type │  n_h │  n_w │  Patch Data [0..N]                    │   │
│   │ 0x01 │ 2 B  │ 2 B  │  (tous les patches)                   │   │
│   └──────┴──────┴──────┴──────────────────────────────────────┘   │
│                                                                     │
│   P-FRAME :                                                         │
│   ┌──────┬──────┬──────┬──────────────────────────────────────┐   │
│   │ Type │  n_h │  n_w │  Changed Patches [0..M] + END_MARKER  │   │
│   │ 0x02 │ 2 B  │ 2 B  │                                      │   │
│   └──────┴──────┴──────┴──────────────────────────────────────┘   │
│                                                                     │
│   Changed Patch Payload (3 types) :                                 │
│                                                                     │
│   Type 1 — Dictionary Match (meilleur cas, 10 octets) :            │
│   ┌──────────┬──────┬────────┬──────────┬──────────────┬────────┐ │
│   │Grid Index│ 0x01 │ Shard  │Patch ID  │ Residual Len │Residual│ │
│   │   4 B    │ 1 B  │  2 B   │   4 B    │     4 B      │ N B    │ │
│   └──────────┴──────┴────────┴──────────┴──────────────┴────────┘ │
│   Si Residual Len = 0 → match exact, pas de données résiduelles     │
│                                                                     │
│   Type 2 — Raw Fallback (pire cas) :                                │
│   ┌──────────┬──────┬──────────┬──────────────────────────┐       │
│   │Grid Index│ 0x00 │ Raw Len  │   Raw Delta-H + zstd      │       │
│   │   4 B    │ 1 B  │   4 B    │         N B                │       │
│   └──────────┴──────┴──────────┴──────────────────────────┘       │
│                                                                     │
│   Type 3 — Skip (patch inchangé) : 0 octet (implicite)              │
│                                                                     │
│   END_MARKER : 0xFFFFFFFF (4 octets)                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.2 Protocole de streaming adaptatif

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   HHS — Harmonic HTTP Streaming                                     │
│                                                                     │
│   Principe : Similaire à HLS/DASH mais avec segments HCV            │
│                                                                     │
│   MANIFESTE (hhs.m3u) :                                             │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │ #EXTM3U                                                      │  │
│   │ #EXT-X-STREAM-INF:BANDWIDTH=20000,RESOLUTION=360p            │  │
│   │ eco/manifest.m3u                                              │  │
│   │ #EXT-X-STREAM-INF:BANDWIDTH=40000,RESOLUTION=480p            │  │
│   │ standard/manifest.m3u                                         │  │
│   │ #EXT-X-STREAM-INF:BANDWIDTH=80000,RESOLUTION=720p            │  │
│   │ hd/manifest.m3u                                               │  │
│   │ #EXT-X-STREAM-INF:BANDWIDTH=170000,RESOLUTION=1080p          │  │
│   │ fullhd/manifest.m3u                                           │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│   SEGMENTS :                                                        │
│   · Durée : 2 secondes                                              │
│   · Format : HHDV bitstream standalone (auto-suffisant)            │
│   · Taille typique (1080p, 2s) : 25-42 Ko                         │
│   · Taille typique (480p, 2s) : 6-10 Ko                            │
│   · Un segment 480p HCV = ~taille d'une image JPEG standard        │
│                                                                     │
│   ADAPTATION CLIENT :                                               │
│   · Mesure le débit effectif toutes les 2 secondes                  │
│   · Monte/descend d'un profil si débit > 1.5× ou < 0.5× target    │
│   · Buffer de 6 secondes pour absorber les variations               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.3 Décodeur mobile — Spécifications cibles

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   Librairie : libhcv.so / HCV.framework                             │
│   Langage : C (avec bindings Kotlin/Swift/Python)                   │
│   Taille binaire : < 500 Ko                                         │
│   Dictionnaire : 200-977 Mo (téléchargé une fois, stockage externe)│
│                                                                     │
│   PERFORMANCE (cible, estimation C vs Python actuel) :              │
│   ┌────────────────────┬────────────┬────────────┐                 │
│   │ Opération          │ Python     │ C (cible)  │                 │
│   ├────────────────────┼────────────┼────────────┤                 │
│   │ Décode 1080p/frame │ ~60 ms     │ ~3 ms      │                 │
│   │ Décode 1080p/30fps │ 1800 ms/s  │ 90 ms/s    │                 │
│   │ Temps réel 30fps   │ ❌ (1,8s)  │ ✅ (90ms)  │                 │
│   │ RAM                │ ~90 Mo     │ ~50 Mo     │                 │
│   │ CPU (mobile)       │ 30-40%     │ 2-5%       │                 │
│   └────────────────────┴────────────┴────────────┘                 │
│                                                                     │
│   Le portage C/Rust est le PRÉREQUIS au streaming temps réel.       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 10. Projections Financières

### 10.1 Scénario conservateur

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   ANNÉE 1 (Pilote) :                                                │
│   · Utilisateurs : 50 000                                           │
│   · Premium (3%) : 1 500                                            │
│   · CA : 50 000€ (subventions + dons principalement)                │
│   · Charges : 50 000€                                               │
│   · Résultat : 0€ (break-even visé)                                 │
│                                                                     │
│   ANNÉE 2 (Expansion francophone) :                                 │
│   · Utilisateurs : 500 000                                          │
│   · Premium (4%) : 20 000                                           │
│   · CA : 450 000€ (180K abonnements + 150K pub + 120K licences)    │
│   · Charges : 500 000€                                              │
│   · Résultat : -50 000€                                             │
│                                                                     │
│   ANNÉE 3 (Panafricain) :                                           │
│   · Utilisateurs : 5 000 000                                        │
│   · Premium (5%) : 250 000                                          │
│   · CA : 6 200 000€                                                 │
│   · Charges : 5 000 000€                                            │
│   · Résultat : +1 200 000€ ✅                                       │
│                                                                     │
│   ANNÉE 5 (Consolidation) :                                         │
│   · Utilisateurs : 50 000 000                                       │
│   · Premium (5%) : 2 500 000                                        │
│   · CA : 75 000 000€                                                │
│   · Résultat net : 25 000 000€                                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 10.2 Besoins de financement

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   AMORÇAGE (0-12 mois) : 250 000€                                   │
│   · Développement MVP + pilote : 150 000€                           │
│   · Licences contenu initial : 50 000€                              │
│   · Marketing pilote : 30 000€                                      │
│   · Frais juridiques/structure : 20 000€                            │
│                                                                     │
│   SÉRIE A (12-24 mois) : 5 000 000€                                 │
│   · Expansion 5 pays : 2 500 000€                                   │
│   · R&D (encodeur C, SDK, P2P, RTHC) : 1 500 000€                  │
│   · Contenu (droits sportifs, productions) : 1 000 000€             │
│                                                                     │
│   SÉRIE B (24-36 mois) : 20 000 000€                                │
│   · Expansion 25 pays : 10 000 000€                                 │
│   · RTHC 500 villages : 5 000 000€                                  │
│   · Contenu + marketing : 5 000 000€                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 11. Risques et Mitigations

| # | Risque | Probabilité | Impact | Mitigation |
|---|--------|------------|--------|------------|
| 1 | **HCV non prouvé en vidéo temps réel** | Moyenne | Critique | Pilote rapide (Phase 1, mois 1-3) pour valider ou pivoter. Le codec offline fonctionne déjà. |
| 2 | **Opérateurs télécom bloquent/throttlent** | Élevée | Élevé | Accords zero-rating gagnant-gagnant. RTHC + P2P comme alternatives hors réseau télécom. |
| 3 | **Canal+ verrouille les droits sportifs** | Élevée | Moyen | Contournement : produire du contenu local original. Le sport africain (CAN, ligues locales) n'est pas exclusif. |
| 4 | **Coût de la data encore trop élevé** | Moyenne | Élevé | P2P + RTHC = distribution locale à coût zéro. Offline download. Négociation zero-rating. |
| 5 | **Pénétration smartphone < 50%** | Moyenne | Moyen | PWA + KaiOS pour feature phones. Audio-only mode. RTHC + appareils low-cost. |
| 6 | **Piratage des flux HCV** | Moyenne | Élevé | Chiffrement du bitstream. Watermarking par appareil. Rotation des clés de dictionnaire. |
| 7 | **Instabilité politique/économique** | Élevée | Moyen | Diversification multi-pays. Mobile money = pas de risque de change. Structure locale par pays. |
| 8 | **Complexité des licences de contenu** | Élevée | Moyen | Commencer par contenu original + créateurs locaux. Pas besoin des catalogues Hollywood au début. |
| 9 | **Concurrence d'un géant (Google/Netflix)** | Faible | Élevé | Ils n'ont pas HCV. Ils visent le haut de marché. Notre compression est notre fossé — ils ne peuvent pas copier sans le dictionnaire harmonique. |
| 10 | **Adoption utilisateurs lente** | Moyenne | Élevé | Freemium + viralité (WhatsApp, P2P). Un utilisateur qui partage un film avec 5 amis = 5 nouveaux utilisateurs gratuits. |

---

## 12. Prochaines Actions

### 12.1 Immédiat (Juillet-Août 2026)

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   ACTION 1 : Prototype technique — 2 semaines                       │
│   ───────────────────────────────────                                │
│   · Prendre l'encodeur vidéo HCV existant (harmonic_codec.py)       │
│   · Encoder 10 films Nollywood (libres de droits ou licences pas    │
│     chères) en HCV 480p/720p/1080p                                  │
│   · Mesurer les vrais ratios de compression sur du contenu réel     │
│   · Servir les fichiers via HTTP Range requests (simuler streaming) │
│   · Tester la lecture sur un vrai téléphone Android                 │
│                                                                     │
│   Livrable : Rapport de benchmark vidéo réel + échantillons         │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ACTION 2 : Maquette produit — 2 semaines                          │
│   ─────────────────────────────────                                  │
│   · PWA minimaliste avec lecteur vidéo                              │
│   · Interface : grille de contenu + lecteur plein écran             │
│   · Sélecteur de qualité automatique                                │
│   · Page d'abonnement (mockup mobile money)                         │
│                                                                     │
│   Livrable : PWA testable sur ka.tv ou sous-domaine                 │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ACTION 3 : Validation marché — En parallèle                       │
│   ─────────────────────────────────────                              │
│   · 20 entretiens utilisateurs au Bénin/Sénégal (WhatsApp)          │
│   · Questions : Que regardez-vous ? Combien payez-vous ?            │
│     Utiliseriez-vous une app à 1 500 FCFA/mois ?                    │
│   · Identifier 5 créateurs de contenu locaux prêts à tester         │
│                                                                     │
│   Livrable : Rapport de validation marché                           │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ACTION 4 : Montage du dossier — 1 semaine                         │
│   ─────────────────────────────────────                              │
│   · Synthèse des 3 actions précédentes                              │
│   · Pitch deck pour investisseurs (10 slides)                       │
│   · Budget détaillé Phase 1                                         │
│   · Identification des 5 premiers investisseurs cibles              │
│                                                                     │
│   Livrable : Dossier d'investissement complet                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 12.2 Les 90 premiers jours

| Semaine | Action | Livrable |
|---------|--------|----------|
| 1-2 | Benchmark vidéo HCV réel | Rapport technique |
| 3-4 | PWA prototype | App testable |
| 5-6 | Entretiens utilisateurs | Rapport marché |
| 7-8 | Partenariats contenu (5 créateurs, 20 films) | Contrats signés |
| 9-10 | Intégration mobile money | Paiement fonctionnel |
| 11-12 | Lancement beta fermé (100 utilisateurs) | Beta live |
| 13 | Analyse beta, itération, pitch deck final | Dossier investissement |

---

## Annexe A : Paysage Concurrentiel Détaillé

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   ACTEUR            FORCES                  FAIBLESSES              │
│   ──────            ──────                  ──────────              │
│                                                                     │
│   Canal+/DSTV       Droits sportifs         Prix (5-45€/mois)       │
│   23M abonnés       Contenu premium          Infrastructure lourde   │
│                     Marque historique        Perte d'abonnés         │
│                                              Complexité offre        │
│                                                                     │
│   StarTimes         Prix bas (3-8€/mois)    Qualité médiocre        │
│   10M abonnés       Présence rurale (TNT)    Réputation « cheap »    │
│                     Partenariats gouvern.    Dépendance chinoise     │
│                                                                     │
│   Netflix           Catalogue mondial       Data intensive (H.265)  │
│   200K Afrique      Marque aspirationnelle  Prix (3-8€/mois)        │
│                     Recommendation IA        Paiement carte bancaire │
│                                              Pas de contenu local    │
│                                                                     │
│   YouTube           Gratuit                 Data intensive           │
│   Dominant          Tout le contenu          Pubs envahissantes      │
│                     Aucune friction          Pas de direct TV        │
│                                                                     │
│   Showmax           Contenu africain         Seulement 476K abonnés │
│   (MultiChoice)     Sports (SuperSport)      Cannibalisé par DSTV   │
│                     Intégration DSTV         Arrêté avril 2026       │
│                                                                     │
│   KA TV (NOUS)      Compression 30-50×      Nouvel entrant          │
│   À construire      Prix 0-3€/mois           Pas de droits sports   │
│                     Mobile money             Marque inconnue         │
│                     RTHC + P2P               Codec non standard      │
│                     Contenu communautaire                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Annexe B : Comparaison des Codecs Vidéo

| Codec | Année | Base technique | Compression type (1080p) | Standardisé |
|-------|-------|---------------|-------------------------|-------------|
| H.264/AVC | 2003 | DCT + motion estimation | 8-12 Mbps | Oui (MPEG) |
| H.265/HEVC | 2013 | DCT + améliorations | 4-8 Mbps | Oui (MPEG) |
| AV1 | 2018 | DCT + ML tools | 3-6 Mbps | Oui (AOM) |
| H.266/VVC | 2020 | DCT + ML + affinements | 2-4 Mbps | Oui (MPEG) |
| **HCV (Harmonic)** | 2026 | **DFT + dictionnaire spectral** | **0,1-0,17 Mbps** | Non (propriétaire) |

**Le différentiel HCV** : Tous les codecs traditionnels sont basés sur la DCT (transformée cosinus discrète) — une approximation fréquentielle locale. HCV utilise la DFT (transformée de Fourier discrète) avec un dictionnaire global — il « reconnaît » les patches au lieu de les approximer. C'est un changement de paradigme, pas une amélioration incrémentale.

---

## Annexe C : Le « Pourquoi maintenant ? »

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   5 FORCES CONVERGENTES QUI RENDENT KA TV INÉVITABLE               │
│                                                                     │
│   1. LA TECHNOLOGIE EST PRÊTE                                       │
│      HCV 119.5× est finalisé (Phase 6 benchmark).                    │
│      Le décodeur mobile tient en 200 lignes de Python.               │
│      Le portage C/Rust est le seul verrou restant.                   │
│                                                                     │
│   2. LE MARCHÉ EST MÛR                                              │
│      Data mobile à 0,42$/Go et en baisse.                           │
│      600M de smartphones en Afrique (2025).                          │
│      Mobile money ubiquitaire (500M+ comptes).                       │
│                                                                     │
│   3. L'INCUMBENT S'AFFAIBLIT                                        │
│      Canal+/MultiChoice perd 4M d'abonnés en 18 mois.               │
│      Endettement post-acquisition (1,9 milliards €).                │
│      Incapable de baisser les prix assez bas.                        │
│                                                                     │
│   4. LE BESOIN EST IMMENSE                                           │
│      97% des Africains n'ont pas de TV payante.                     │
│      La demande de contenu africain explose.                         │
│      Nollywood = 2 500 films/an, pas de plateforme dédiée.          │
│                                                                     │
│   5. L'INFRASTRUCTURE ALTERNATIVE EXISTE                             │
│      RTHC : réseau communautaire prêt à déployer.                   │
│      Starlink : backhaul satellite disponible partout.              │
│      P2P : chaque téléphone est un nœud de distribution.            │
│                                                                     │
│   TOUTES LES CONDITIONS SONT RÉUNIES. LE MOMENT EST MAINTENANT.     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

> *« L'Afrique ne regarde pas la télévision parce que la télévision n'a jamais été pensée pour l'Afrique. KA TV change cela. Avec la compression harmonique, un téléphone à 50$ devient un cinéma. Un village sans électricité devient une salle de concert. Un jeune à Cotonou devient une chaîne de télévision. Ce n'est pas une alternative à Canal+. C'est la télévision que l'Afrique aurait dû avoir depuis le début. »*
>
> — Projet Univers Harmonique, Juillet 2026

---

**Prochaine étape** : Prototype technique de benchmark vidéo HCV réel → Validation des ratios de compression sur du contenu Nollywood.
