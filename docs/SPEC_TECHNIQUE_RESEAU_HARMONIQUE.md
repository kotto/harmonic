# Spécification Technique — Réseau Télécom Harmonique Communautaire

**Document** : SPEC-RTC-HV1.0  
**Date** : Juillet 2026  
**Auteur** : Alain Kotto — Projet Univers Harmonique  
**Statut** : Spécification de référence (v1.0)

---

## Résumé Exécutif

Le Réseau Télécom Harmonique Communautaire (RTHC) est un réseau de communications **souverain, sans licence, sans abonnement**, conçu pour les zones rurales et périurbaines des pays en développement. Il combine trois technologies radio complémentaires avec une couche de compression harmonique (119.5× – 480×) qui multiplie la capacité effective du réseau par un facteur 50-150×.

**Coût par famille : 11€ une fois + 0.15€/mois** (vs 5-15€/mois chez un opérateur).  
**Services : voix HD, messagerie, photos, données légères, alertes sanitaires, radio communautaire.**

---

## Table des Matières

1. [Architecture Générale](#1-architecture-générale)
2. [Couche Accès : Wi-Fi HaLow (802.11ah)](#2-couche-accès--wi-fi-halow-80211ah)
3. [Couche Backhaul : Mesh 5 GHz Directionnel](#3-couche-backhaul--mesh-5-ghz-directionnel)
4. [Couche IoT : LoRa](#4-couche-iot--lora)
5. [Couche Compression Harmonique](#5-couche-compression-harmonique)
6. [Codec Vocal Harmonique](#6-codec-vocal-harmonique)
7. [Protocoles et Adressage](#7-protocoles-et-adressage)
8. [Sécurité et Chiffrement](#8-sécurité-et-chiffrement)
9. [Interconnexion Externe](#9-interconnexion-externe)
10. [Spécifications Matérielles](#10-spécifications-matérielles)
11. [Pile Logicielle](#11-pile-logicielle)
12. [Gestion du Réseau](#12-gestion-du-réseau)

---

## 1. Architecture Générale

### 1.1 Topologie à 3 Couches Radio + 1 Couche Logique

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│                      INTERNET MONDIAL                            │
│                            │                                     │
│              ┌─────────────┴─────────────┐                      │
│              │   PASSERELLE INTERNET     │                      │
│              │   (Starlink / 4G / Fibre) │                      │
│              │   Une pour 5-20 villages  │                      │
│              └─────────────┬─────────────┘                      │
│                            │                                     │
│  ╔══════════════════════════════════════════════════════════════╗ │
│  ║  COUCHE 3 — BACKHAUL INTER-VILLAGES (5 GHz directionnel)    ║ │
│  ║  ───────────────────────────────────────────────────────    ║ │
│  ║  · Liaisons point-à-point : 5-30 km                         ║ │
│  ║  · Débit : 50-500 Mbps                                      ║ │
│  ║  · Équipement : Ubiquiti AirMax / MikroTik / LibreRouter    ║ │
│  ║  · Alimentation : Solaire 50W par relais                    ║ │
│  ║  · Topologie : Arbre/Anneau redondant                       ║ │
│  ╚══════════════════════════════════════════════════════════════╝ │
│                            │                                     │
│  ╔══════════════════════════════════════════════════════════════╗ │
│  ║  COUCHE 2 — ACCÈS VILLAGE (Wi-Fi HaLow 900 MHz)             ║ │
│  ║  ───────────────────────────────────────────────────────    ║ │
│  ║  · Point d'accès HaLow par village (1-3 selon taille)       ║ │
│  ║  · Portée : 1-3 km autour du point d'accès                  ║ │
│  ║  · Débit : 2-8 Mbps partagé                                 ║ │
│  ║  · Jusqu'à 2000 clients par AP                              ║ │
│  ║  · VoIP native (QoS intégré 802.11ah)                       ║ │
│  ╚══════════════════════════════════════════════════════════════╝ │
│                            │                                     │
│  ╔══════════════════════════════════════════════════════════════╗ │
│  ║  COUCHE 1 — IoT/CAPTEURS (LoRa 868/915 MHz)                 ║ │
│  ║  ───────────────────────────────────────────────────────    ║ │
│  ║  · Capteurs agricoles, météo, environnement                 ║ │
│  ║  · Portée : 5-15 km                                         ║ │
│  ║  · Très basse consommation (1+ an sur batterie)             ║ │
│  ║  · Données compressées via dictionnaire harmonique          ║ │
│  ╚══════════════════════════════════════════════════════════════╝ │
│                            │                                     │
│  ╔══════════════════════════════════════════════════════════════╗ │
│  ║  COUCHE 0 — COMPRESSION HARMONIQUE (transversale)           ║ │
│  ║  ───────────────────────────────────────────────────────    ║ │
│  ║  · Toute donnée est compressée avant émission               ║ │
│  ║  · Dictionnaires partagés à tous les niveaux                ║ │
│  ║  · Voix : 32 kbps → 1 kbps (32×)                           ║ │
│  ║  · Images : 480 KB → 3.3 KB (145×)                         ║ │
│  ║  · Texte/Données : 10-100× via dictionnaire sémantique     ║ │
│  ╚══════════════════════════════════════════════════════════════╝ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 1.2 Flux de Données Type

```
UTILISATEUR                    RÉSEAU                          MONDE
──────────                   ──────────                       ─────

Téléphone ──WiFi──► Boîtier ──HaLow──► AP Village ──5GHz──► Passerelle ── Internet
  │                                     │                    │
  │  1. Compression harmonique          │                    │
  │     (sur le boîtier ou              │                    │
  │      sur le téléphone)              │                    │
  │                                     │                    │
  │  2. Données ultra-compactes         │                    │
  │     traversent le réseau            │                    │
  │                                     │                    │
  │  3. Reconstruction au point         │                    │
  │     de sortie (passerelle           │                    │
  │     ou destinataire local)          │                    │
```

### 1.3 Principes Fondateurs

| Principe | Description |
|----------|-------------|
| **Souveraineté** | Le réseau appartient à la communauté, pas à un opérateur |
| **Zéro coût récurrent** | Pas de licence spectre, pas d'abonnement opérateur |
| **Compression d'abord** | Toute donnée est compressée avant transmission |
| **Dégradation gracieuse** | Si une couche tombe, les autres continuent |
| **Auto-réparation** | Mesh auto-configurable, pas d'ingénieur requis |
| **Ouvert** | Standards IEEE/ETSI, logiciel open source |
| **Faible consommation** | Fonctionne sur solaire, pas de climatisation |

---

## 2. Couche Accès : Wi-Fi HaLow (802.11ah)

### 2.1 Justification du Choix

HaLow est le seul standard qui combine :
- **Bande ISM 900 MHz** (pas de licence, comme LoRa)
- **Portée kilométrique** (1-3 km en zone rurale avec antenne basique)
- **Débit « vrai WiFi »** (150 kbps à 86.7 Mbps selon configuration)
- **QoS native** (priorisation voix/vidéo/données)
- **Full duplex** (contrairement à LoRa)
- **Très basse consommation** (mode cible < 100 µW en veille, comparable LoRa)
- **Standard IEEE ouvert** (pas de royalties Semtech)

### 2.2 Paramètres Radio

| Paramètre | Valeur | Notes |
|-----------|:------:|-------|
| Fréquence centrale | 868 MHz (EU/Afrique), 915 MHz (Amériques/Asie) | Bande ISM |
| Largeur canal | 1 MHz, 2 MHz (recommandé) | 4/8/16 MHz disponibles |
| Modulation | BPSK, QPSK, 16-QAM, 64-QAM, 256-QAM | Adaptative |
| MCS (Modulation Coding Scheme) | MCS0 (150 kbps) à MCS10 (86.7 Mbps) | Négociation automatique |
| Puissance TX max | 14 dBm (25 mW) — réglementation EU | Jusqu'à 27 dBm US |
| Sensibilité RX | -110 dBm (MCS0), -85 dBm (MCS7) | Excellent |
| Débit utile MCS0 | ~150 kbps | Portée maximale |
| Débit utile MCS7 (16-QAM) | ~2 Mbps | Bon compromis portée/débit |
| Débit utile MCS10 (256-QAM) | ~8 Mbps | Portée réduite (< 500m) |
| Antenne | Dipôle omnidirectionnelle 3 dBi | Par défaut |
| Portée MCS0 (champ libre) | 3-5 km | Avec antenne 3 dBi |
| Portée MCS7 (champ libre) | 1-2 km | Couverture village typique |

### 2.3 Configuration du Point d'Accès Village

```
┌──────────────────────────────────────────────────────────────────┐
│  POINT D'ACCÈS HALOW VILLAGE (AP-HLW-1)                          │
│                                                                  │
│  Matériel :                                                      │
│  · Carte mère : Raspberry Pi 4 (ou Orange Pi 3 LTS)              │
│  · Module HaLow : Morse Micro MM6108 (mini-PCIe)                 │
│  · Antenne : Omnidirectionnelle 5 dBi, 900 MHz                  │
│  · Boîtier : Étanche IP65 + parasurtenseur                       │
│  · Alimentation : Panneau solaire 50W + batterie 12V 20Ah        │
│                                                                  │
│  Configuration réseau :                                          │
│  · Mode : AP (Access Point)                                      │
│  · SSID : HARMONIC-VILLAGE-XX (caché ou visible selon politique) │
│  · Canal : 2 MHz (configurable)                                  │
│  · Sécurité : WPA3-SAE (Simultaneous Authentication of Equals)   │
│  · QoS : WMM (priorité voix > vidéo > données)                   │
│  · VLAN : Voix (VLAN 10), Données (VLAN 20), Gestion (VLAN 99)   │
│  · DHCP : Plage 10.XX.YY.100-200 (YY = ID village)               │
│                                                                  │
│  Supervision :                                                   │
│  · Interface web locale (http://harmonic.local)                  │
│  · SNMP pour monitoring centralisé                               │
│  · Redémarrage automatique si perte de connectivité              │
│                                                                  │
│  Coût unitaire : 150-200€ (hors installation)                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.4 Boîtier Utilisateur (« Harmonic Node »)

```
┌──────────────────────────────────────────────────────────────────┐
│  BOÎTIER UTILISATEUR (HN-1)                                      │
│                                                                  │
│  Fonction : Pont entre le téléphone de l'utilisateur             │
│             et le réseau HaLow du village.                        │
│                                                                  │
│  Matériel :                                                      │
│  · MCU : ESP32-S3 (double core, WiFi 2.4 GHz + BLE 5)           │
│  · Module HaLow : Morse Micro MM6108 (SPI)                       │
│  · Antenne WiFi : Intégrée (PCB trace)                           │
│  · Antenne HaLow : Externe, fouet 3 dBi                          │
│  · Batterie : Li-Ion 18650 × 2 (6000 mAh)                       │
│  · Autonomie : 24-48h en usage normal                            │
│  · Recharge : Micro-USB / USB-C (5V)                             │
│  · Boutons : Power, Appairage                                    │
│  · LEDs : WiFi, HaLow, Batterie                                  │
│  · Boîtier : Plastique recyclé, 80 × 50 × 25 mm                 │
│                                                                  │
│  Fonctionnalités :                                               │
│  · Mode routeur : WiFi AP local → pont HaLow                    │
│  · Compression harmonique embarquée (optionnelle)                │
│  · Mode économie d'énergie : WiFi off si inactif                 │
│  · Mise à jour OTA via HaLow                                     │
│                                                                  │
│  Interface utilisateur :                                         │
│  · Application PWA (KA Phone modifiée)                           │
│  · Ou application native Android (F-Droid)                       │
│  · Configuration via page web locale (captive portal)            │
│                                                                  │
│  Coût unitaire (composants, volume 1000) : 18-25€                │
│  Prix de vente cible : 25-35€                                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.5 Densité de Déploiement

| Environnement | Portée utile | AP par km² | Utilisateurs par AP |
|---------------|:------------:|:----------:|:-------------------:|
| Rural dispersé | 2-3 km | 0.1 | 50-200 |
| Village dense | 1-1.5 km | 0.5 | 200-1000 |
| Petite ville | 500-800 m | 2 | 500-2000 |
| Marché/centre | 300-500 m | 5 | 1000-5000 |

---

## 3. Couche Backhaul : Mesh 5 GHz Directionnel

### 3.1 Justification

Le backhaul 5 GHz relie les villages entre eux et les connecte au point Internet. Le choix du 5 GHz avec antennes directionnelles permet :
- Des **liaisons stables** de 5-30 km (ligne de vue)
- Un **débit élevé** (50-500 Mbps) qui agrège tout le trafic d'un village
- Une utilisation en **bande ISM** (pas de licence)
- Un **coût modéré** (200-400€ par liaison)
- Une **maturité** éprouvée (WISP du monde entier)

### 3.2 Topologie

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  TOPOLOGIE BACKHAUL RECOMMANDÉE : ARBRE REDONDANT                │
│                                                                  │
│                    ┌─────────┐                                   │
│                    │Passerelle│                                   │
│                    │Internet  │                                   │
│                    └────┬────┘                                   │
│                         │                                        │
│            ┌────────────┼────────────┐                          │
│            │            │            │                          │
│         ┌──┴──┐      ┌──┴──┐      ┌──┴──┐                      │
│         │Vill.│      │Vill.│      │Vill.│    ← Niveau 1         │
│         │  A  │      │  B  │      │  C  │                      │
│         └──┬──┘      └──┬──┘      └──┬──┘                      │
│            │            │            │                          │
│       ┌────┼────┐  ┌────┼────┐  ┌────┼────┐                    │
│       │    │    │  │    │    │  │    │    │                    │
│     ┌┴┐  ┌┴┐  ┌┴┐┌┴┐  ┌┴┐  ┌┴┐┌┴┐  ┌┴┐  ┌┴┐                  │
│     │D│  │E│  │F││G│  │H│  │I││J│  │K│  │L│  ← Niveau 2       │
│     └─┘  └─┘  └─┘└─┘  └─┘  └─┘└─┘  └─┘  └─┘                  │
│                                                                  │
│  REDONDANCE :                                                    │
│  · Chaque niveau 2 a AU MOINS 2 chemins vers le niveau 1        │
│  · Protocole de routage : OSPF ou BATMAN-adv                     │
│  · Basculement automatique en cas de perte de liaison            │
│  · Les liaisons critiques (A, B, C) sont doublées si budget     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 3.3 Spécifications des Liaisons

| Paramètre | Valeur | Notes |
|-----------|:------:|-------|
| Fréquence | 5.180 – 5.875 GHz | Bande ISM, canaux 20/40/80 MHz |
| Équipement recommandé | Ubiquiti PowerBeam 5AC Gen2 | 25 dBi, ~100€ |
| Alternative économique | MikroTik SXTsq 5 ac | 16 dBi, ~60€ |
| Alternative open source | LibreRouter + antenne externe | 100% libre |
| Portée max (25 dBi) | 30 km | Ligne de vue dégagée |
| Portée typique | 10-15 km | Avec marge pour la pluie |
| Débit TCP (20 MHz) | 50-150 Mbps | Selon distance |
| Débit TCP (80 MHz) | 200-500 Mbps | Courte distance |
| Latence | 2-5 ms par saut | Excellent |
| Alimentation | PoE 24V passif | Depuis le boîtier solaire |
| Consommation | 5-8 W | Acceptable pour solaire |

### 3.4 Relais Backhaul

```
┌──────────────────────────────────────────────────────────────────┐
│  RELAIS BACKHAUL (BH-1)                                          │
│                                                                  │
│  Matériel :                                                      │
│  · 2 × Radio 5 GHz (une par direction)                           │
│  · Switch PoE 3 ports (alimente les radios)                      │
│  · Raspberry Pi (contrôleur + routage)                           │
│  · Parafoudre + mise à la terre                                  │
│  · Mât télescopique 6-12m ou fixation toit                      │
│  · Alimentation : Panneau solaire 100W + batterie 12V 50Ah      │
│  · Boîtier étanche IP66                                          │
│                                                                  │
│  Logiciel :                                                      │
│  · OpenWRT / LibreRouter OS                                      │
│  · Routage dynamique (BATMAN-adv ou OSPF)                        │
│  · Monitoring : Zabbix agent / Prometheus node_exporter          │
│  · VPN mesh (WireGuard) pour le trafic inter-villages            │
│                                                                  │
│  Coût unitaire : 300-500€ (selon hauteur du mât)                 │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4. Couche IoT : LoRa

### 4.1 Rôle dans l'Architecture

LoRa est conservé pour la couche capteurs, où ses avantages sont imbattables :
- **Consommation :** 1+ an sur une pile AA
- **Portée :** 5-15 km sans ligne de vue
- **Pénétration :** Traverse la végétation et les murs légers
- **Coût :** Module à 5€

### 4.2 Cas d'Usage Ciblés

| Usage | Capteur | Fréquence TX | Taille donnée brute | Taille après harmonique |
|-------|---------|:------------:|:-------------------:|:----------------------:|
| Météo agricole | BME280 (T°, H%, P) | 15 min | 12 B | 2 B (dict. météo) |
| Humidité du sol | Capacitif | 1 h | 4 B | 2 B |
| Niveau d'eau (puits) | Ultrason | 1 h | 4 B | 2 B |
| GPS troupeau | GNSS | 30 min | 16 B | 2 B (dict. pâturage) |
| Alerte feu | Détecteur fumée | Événement | 4 B | 2 B |
| Photo animal | Caméra basse rés | 1/jour | 50 KB | 400 B (128×128 harmonique) |
| Alerte inondation | Niveau eau rivière | 10 min (si critique) | 4 B | 2 B |

### 4.3 Architecture LoRa

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  CAPTEURS LoRa ──► Passerelle LoRa du village ──► AP HaLow      │
│                                                    │             │
│                                                    ▼             │
│                                              Dashboard local     │
│                                              + Alerte SMS/WhatsApp│
│                                                                  │
│  PASSERELLE LoRa VILLAGE :                                       │
│  · ESP32 + SX1278/SX1262 (moins de 25€)                         │
│  · Ou module RAKwireless WisGate (60€, plus robuste)             │
│  · Connectée au Raspberry Pi du AP HaLow en USB/série            │
│  · Décode les trames LoRa → formate en JSON → pousse vers MQTT  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. Couche Compression Harmonique

### 5.1 Positionnement

La couche compression est **transversale** : elle intervient à chaque point d'entrée du réseau, quelle que soit la technologie radio sous-jacente.

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  POINTS D'APPLICATION DE LA COMPRESSION HARMONIQUE :             │
│                                                                  │
│  1. BOÎTIER UTILISATEUR (encode)                                 │
│     · Voix entrante → Harmonic Voice Codec → trames 1 kbps      │
│     · Photo/vidéo → Harmonic Dictionary → bitstream HHD2        │
│     · Texte → Dictionnaire sémantique → IDs de fragments        │
│                                                                  │
│  2. AP VILLAGE (transcode si nécessaire)                         │
│     · Reçoit déjà compressé → relaye tel quel                   │
│     · Si donnée externe entrante → compresse avant diffusion    │
│                                                                  │
│  3. PASSERELLE INTERNET (transcode)                              │
│     · Reçoit compressé du mesh → décompresse → Internet standard│
│     · Reçoit d'Internet → compresse → injecte dans le mesh      │
│                                                                  │
│  4. CAPTEURS IoT (encode léger)                                  │
│     · Données télémétrie → dictionnaire de patterns → 2B/trame │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 5.2 Dictionnaires Partagés

| Dictionnaire | Contenu | Taille | Déploiement |
|-------------|---------|:------:|-------------|
| **Harmonic Voice** | 500-1000 fragments phonétiques | 5-10 MB | Pré-chargé sur le boîtier |
| **Harmonic Image** | Dictionnaire visuel compact | 50-120 MB | AP village + passerelle |
| **Harmonic Text** | Dictionnaire sémantique multilingue | 10-50 MB | AP village |
| **Harmonic Telemetry** | Patterns de données capteurs | 1-5 MB | Passerelle LoRa + dashboard |

### 5.3 Impact sur la Capacité Réseau

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  SANS COMPRESSION HARMONIQUE :                                   │
│  ────────────────────────────                                     │
│  · Canal HaLow 2 Mbps                                            │
│  · Voix 32 kbps → 62 appels simultanés                          │
│  · Photo 400×400 (480 KB) → 1.9s de transmission                │
│  · Vidéo 1 min 240p (5 MB) → 20s de transmission                │
│                                                                  │
│  AVEC COMPRESSION HARMONIQUE :                                    │
│  ─────────────────────────────                                    │
│  · Canal HaLow 2 Mbps                                            │
│  · Voix 1 kbps → 2000 appels simultanés (32× plus !)            │
│  · Photo 400×400 (3.3 KB) → 0.013s de transmission (146× plus)  │
│  · Vidéo I/P frames (estimé 50 KB/min) → 0.2s (100× plus)      │
│                                                                  │
│  → LA COMPRESSION TRANSFORME UN RÉSEAU « OK »                    │
│    EN RÉSEAU « SURPUISSANT »                                     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 6. Codec Vocal Harmonique

### 6.1 Spécification

Le Harmonic Voice Codec (HVC) est un codec vocal basé sur un dictionnaire partagé de fragments phonétiques compressés par l'approche harmonique.

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  ENCODEUR HVC (côté émetteur)                                    │
│  ─────────────────────────────                                    │
│                                                                  │
│  MICRO ──► Buffer 40ms (16 kHz, 16-bit = 640 échantillons)      │
│    │                                                             │
│    ├─► Étape 1 : FFT 1024 points → spectre de magnitude         │
│    │                                                             │
│    ├─► Étape 2 : Extraction caractéristiques harmoniques        │
│    │   · Fréquence fondamentale f0 (pitch) : 8 bits             │
│    │   · Énergie : 5 bits                                      │
│    │   · Enveloppe spectrale (10 coefficients LPC) : 30 bits    │
│    │   · Signature 9D harmonique : 18 bits                      │
│    │   → Total descripteur : 61 bits                            │
│    │                                                             │
│    ├─► Étape 3 : Recherche dictionnaire                         │
│    │   · KD-tree dans l'espace des signatures 9D               │
│    │   · Distance de résonance harmonique                       │
│    │   · Si dist < seuil → [dict_id: 10 bits]                   │
│    │   · Sinon → [dict_id + residual compressé]                 │
│    │                                                             │
│    └─► Étape 4 : Format trame                                   │
│        · Trame standard (exact match) : 71 bits = ~9 octets     │
│        · Trame avec résiduel : 120-200 bits = 15-25 octets     │
│        · Débit moyen (90% hit rate) : ~1000 bps                │
│        · Débit pire cas : ~2000 bps                             │
│                                                                  │
│  DÉCODEUR HVC (côté récepteur)                                   │
│  ─────────────────────────────                                    │
│                                                                  │
│  TRAME ──► Extraction [dict_id] + [residual optionnel]          │
│    │                                                             │
│    ├─► Lookup dictionnaire → fragment temporel                  │
│    │                                                             │
│    ├─► Ajout residual → reconstruction fine                     │
│    │                                                             │
│    ├─► Overlap-add 50% → continuité inter-trames                 │
│    │                                                             │
│    └─► Filtre post-processing → HAUT-PARLEUR                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 6.2 Spécifications de Performance

| Métrique | Cible | Mesure |
|----------|:-----:|:------:|
| Débit moyen | **< 1500 bps** | Avec hit rate 85-90% |
| Débit pire cas | **< 2500 bps** | Avec 0% hit rate |
| MOS (Mean Opinion Score) | **> 3.5/5** | Équivalent GSM-FR |
| Latence algorithme | **< 30 ms** | Encodage + décodage |
| Complexité encodeur | **< 50 MOPS** | Tient sur ESP32-S3 |
| Complexité décodeur | **< 20 MOPS** | Tient sur ESP32 |
| Taille dictionnaire | **< 10 MB** | Stocké en flash SPI |
| Robustesse bruit fond | **Bonne** | Test en conditions réelles |
| Langues supportées | **Multilingue** | Dictionnaire par langue |

### 6.3 Comparaison avec Codecs Existants

| Codec | Débit (bps) | MOS | Open Source | Complexité |
|-------|:-----------:|:---:|:-----------:|:----------:|
| GSM Full Rate | 13 000 | 3.5 | Oui (libgsm) | Faible |
| AMR 4.75 | 4 750 | 3.0 | Oui (OpenCORE) | Moyenne |
| Codec2 700C | 700 | 2.5 | Oui | Faible |
| Codec2 3200 | 3 200 | 3.2 | Oui | Faible |
| Opus 6 kbps | 6 000 | 3.0 | Oui | Moyenne |
| **HVC (cible)** | **1 000** | **3.5** | **Oui** | **Faible** |

---

## 7. Protocoles et Adressage

### 7.1 Plan d'Adressage

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  ADRESSAGE IPv6 (ULA — Unique Local Address)                     │
│  ─────────────────────────────────────────                        │
│                                                                  │
│  Préfixe : fd00:abcd::/48 (réseau harmonique)                    │
│                                                                  │
│  Structure : fd00:abcd:RRVV:UUUU:UUUU:UUUU:UUUU:UUUU            │
│              ─────┬───── ─┬─ ───────────────┬───────────────    │
│                   │       │                  │                   │
│                   │       │                  └─ ID utilisateur   │
│                   │       └─ ID village (16 bits, 65535 villages)│
│                   └─ ID région (8 bits, 256 régions)            │
│                                                                  │
│  EXEMPLE :                                                       │
│  · Région 1 (Nord), Village 42, Utilisateur 1001                │
│  · → fd00:abcd:0100:2a00:0000:0000:0000:03e9                    │
│                                                                  │
│  ADRESSAGE LOCAL (sans IPv6, mode minimal) :                     │
│  · Numéro de village (2 digits) + Numéro utilisateur (4 digits) │
│  · Exemple : 42-1001 → « appelle le 42-1001 »                   │
│  · Traduction DNS locale : harmonic.local → IP                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 7.2 Protocoles de Communication

| Service | Protocole | Port | Notes |
|---------|-----------|:----:|-------|
| VoIP | SIP (ou protocole custom HCP) | 5060 | SIP proxy local sur AP village |
| Messagerie | Matrix (ou XMPP) | 8448 | Serveur Matrix local |
| Transfert fichiers | HTTP/2 sur TLS | 443 | Avec compression harmonique intégrée |
| Photos médicales | DICOM-web over HHD2 | 8042 | Format médical standard |
| Alertes urgentes | MQTT | 1883 | QoS 1, priorité maximale |
| Mise à jour OTA | HTTP Range Requests | 80 | Téléchargement progressif |
| VoIP vers extérieur | SIP trunk via passerelle | 5060 | Avec transcodage si nécessaire |
| Synchronisation dictionnaire | rsync over SSH | 22 | Différentiel, périodique |
| Supervision | SNMP v3 | 161 | Monitoring du réseau |
| Annuaire | LDAP | 389 | Annuaire des utilisateurs du réseau |

### 7.3 Protocole de Transport Harmonique (HTP)

Au-dessus de TCP/UDP, un protocole léger indique le type de compression utilisé :

```
┌──────────────────────────────────────────────────────────────────┐
│  TRAME HTP (Harmonic Transport Protocol)                          │
│                                                                  │
│  ┌──────┬──────┬──────┬──────┬────────────────────────────────┐ │
│  │Vers. │Type  │Flags │App ID│  PAYLOAD (compressé ou non)    │ │
│  │ 4b   │ 4b   │ 8b   │ 16b  │  variable                      │ │
│  └──────┴──────┴──────┴──────┴────────────────────────────────┘ │
│                                                                  │
│  Vers : version du protocole (actuellement 1)                    │
│  Type : 0=raw, 1=HHD2 image, 2=HVC voix, 3=HTX texte,          │
│         4=HTL telemetry, 5=HVD video, 6=dict_update             │
│  Flags : bit0=compressed, bit1=fragmented, bit2=encrypted,      │
│          bit3=priority, bit4-7=reserved                          │
│  App ID : identifiant application (VoIP=1, Messenger=2, etc.)   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 8. Sécurité et Chiffrement

### 8.1 Architecture de Sécurité par Couche

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  COUCHE RADIO :                                                  │
│  · HaLow : WPA3-SAE (authentification par mot de passe partagé) │
│  · 5 GHz : WPA2-AES + clé pré-partagée par liaison             │
│  · LoRa : AES-128 (clé pré-partagée par application)            │
│                                                                  │
│  COUCHE RÉSEAU :                                                 │
│  · WireGuard VPN entre tous les nœuds du backhaul (obligatoire) │
│  · IPsec possible en alternative plus légère                     │
│  · VLAN séparés : Voix, Données, Gestion, Invités               │
│                                                                  │
│  COUCHE APPLICATION :                                            │
│  · VoIP : SRTP (Secure RTP) avec ZRTP pour l'échange de clés   │
│  · Messagerie : E2E encryption (Matrix/Olm ou Signal Protocol)  │
│  · Fichiers : Chiffrement AES-256-GCM avant stockage            │
│                                                                  │
│  GESTION DES CLÉS :                                              │
│  · Clé maître réseau → dérivée par village via HKDF             │
│  · Rotation automatique des clés tous les 30 jours               │
│  · Révocation possible si un nœud est compromis                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 8.2 Authentification des Utilisateurs

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  IDENTITÉ HARMONIQUE                                             │
│                                                                  │
│  Chaque utilisateur a une identité composée de :                 │
│  · Numéro réseau : 42-1001 (village-utilisateur)                │
│  · Clé publique Ed25519 (stockée dans l'annuaire LDAP)          │
│  · Empreinte de voix (optionnelle, pour appels)                  │
│                                                                  │
│  PROVISIONING :                                                  │
│  · L'administrateur du village crée le compte                    │
│  · L'utilisateur reçoit un QR code à scanner                     │
│  · Le boîtier/app est automatiquement configuré                  │
│  · L'utilisateur définit un code PIN local (6 chiffres)          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 9. Interconnexion Externe

### 9.1 Passerelle Internet

```
┌──────────────────────────────────────────────────────────────────┐
│  PASSERELLE INTERNET PRINCIPALE (GW-1)                            │
│                                                                  │
│  Matériel :                                                      │
│  · Mini-PC fanless (Intel N100, 8 GB RAM, 256 GB SSD)           │
│  · Connexion WAN : Starlink standard (prioritaire)              │
│    OU modem 4G avec forfait données mutualisé                    │
│  · Connexion LAN : Backhaul 5 GHz                                │
│                                                                  │
│  Logiciel :                                                      │
│  · Debian 12 + Docker                                            │
│  · Firewall : nftables avec QoS (limit rate par utilisateur)    │
│  · Proxy cache : Squid (réduit conso données Starlink)           │
│  · DNS local : Unbound (avec cache + blocage pubs)              │
│  · VoIP Gateway : Asterisk (SIP trunk vers le monde)            │
│  · WhatsApp Gateway : whatsapp-web.js (messages automatiques)    │
│  · Monitoring : Netdata + Grafana                                │
│                                                                  │
│  POLITIQUE D'ACCÈS INTERNET :                                    │
│  · Services gratuits locaux (via cache) : Wikipedia, météo,     │
│    prix des marchés, annonces locales                             │
│  · Accès Internet complet : quota équitable par utilisateur      │
│  · Priorité : Urgences médicales > Voix externe > Messagerie    │
│    > Navigation web > Streaming                                  │
│                                                                  │
│  Coût unitaire : 300-500€ + 30-50€/mois (Starlink)              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 9.2 Interconnexion GSM/PSTN

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  PASSERELLE GSM (optionnelle, pour appels vers réseau classique) │
│                                                                  │
│  · Raspberry Pi + dongle GSM (Huawei E3372 ou SIM7600)          │
│  · Carte SIM prépayée économique (voix uniquement)               │
│  · Asterisk avec chan_dongle → pont SIP ↔ GSM                   │
│  · Règle de routage :                                            │
│    · Appel vers numéro local → dongle GSM (coût local)          │
│    · Appel vers international → SIP trunk VoIP (moins cher)     │
│    · Appel depuis extérieur → le réseau est joignable !          │
│                                                                  │
│  NUMÉROTATION DEPUIS L'EXTÉRIEUR :                               │
│  · Un numéro GSM « point d'entrée » est attribué au réseau      │
│  · L'appelant compose ce numéro, puis le code du destinataire   │
│  · « Tapez 1 pour le village A, 2 pour le village B... »        │
│  · Ou reconnaissance vocale du nom du destinataire               │
│                                                                  │
│  Coût : 50€ + crédit prépayé (5-10€/mois)                       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 9.3 Intégration Messageries Existantes

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  BRIDGE WHATSAPP / TELEGRAM / SIGNAL                             │
│  ──────────────────────────────────────                           │
│                                                                  │
│  La passerelle peut héberger des bridges vers :                  │
│  · WhatsApp : via whatsapp-web.js (API non officielle)           │
│    → Le médecin reçoit les alertes dans WhatsApp                 │
│  · Telegram : API officielle, bot simple à créer                │
│    → Canal d'alerte + dashboard automatique                     │
│  · Signal : signal-cli (API non officielle)                     │
│    → Communications ultra-sécurisées                             │
│                                                                  │
│  EXEMPLE FLUX ALERTE SANITAIRE :                                 │
│  Agent santé → photo via réseau → AP village                    │
│  → Gateway détecte « alerte médicale »                          │
│  → Compression HHD2 → envoi via WhatsApp au médecin             │
│  → Médecin répond sur WhatsApp → Gateway → réseau → Agent       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 10. Spécifications Matérielles

### 10.1 Tableau Récapitulatif des Équipements

| Équipement | Modèle de Référence | Qté/Village | Prix Unitaire | Total/Village |
|-----------|---------------------|:-----------:|:------------:|:------------:|
| **Point d'accès HaLow** | RPi 4 + Morse Micro MM6108 | 1-3 | 175€ | 175-525€ |
| **Relais Backhaul 5 GHz** | Ubiquiti PowerBeam 5AC × 2 | 1 | 350€ | 350€ |
| **Passerelle LoRa** | RAKwireless WisGate ou ESP32+SX1278 | 1 | 60€ | 60€ |
| **Passerelle Internet** | Mini-PC N100 + Starlink | 0.1/village* | 500€ | 50€ |
| **Mât + installation** | Mât 6-12m + haubans | 2 | 150€ | 300€ |
| **Solaire AP** | 50W + batterie 20Ah | 1-3 | 120€ | 120-360€ |
| **Solaire Backhaul** | 100W + batterie 50Ah | 1 | 250€ | 250€ |
| **Boîtiers utilisateurs** | ESP32-S3 + MM6108 | 50-200 | 25€ | 1250-5000€ |
| **Câbles, connecteurs** | Ethernet blindé, PoE | — | — | 100€ |
| **Boîtiers étanches** | IP65/IP66 | — | — | 150€ |
| | | | **TOTAL (200 familles)** | **~2810-7160€** |
| | | | **TOTAL par famille** | **14-36€ une fois** |

*\* Une passerelle Internet dessert 5-20 villages (coût partagé)*

### 10.2 Consommation Énergétique

| Équipement | Conso (W) | Solaire requis | Autonomie sans soleil |
|-----------|:---------:|:--------------:|:---------------------:|
| AP HaLow (RPi + HaLow) | 8-12 W | 50W | 2-3 jours |
| Relais Backhaul (2 radios) | 10-15 W | 100W | 2-3 jours |
| Passerelle LoRa | 1-2 W | 5W | 5+ jours |
| Passerelle Internet (Starlink) | 40-60 W | 200W | 1 jour (ou groupe électrogène) |
| Boîtier utilisateur (veille) | 0.2 W | — (batterie interne) | 24-48h |
| Boîtier utilisateur (actif) | 1-2 W | — | 8-12h |

---

## 11. Pile Logicielle

### 11.1 Carte des Logiciels

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  BOÎTIER UTILISATEUR (ESP32-S3)                                  │
│  ──────────────────────────────                                   │
│  · RTOS : FreeRTOS (inclus ESP-IDF)                              │
│  · WiFi AP : ESP-NETIF                                           │
│  · HaLow driver : Morse Micro SDK (C)                            │
│  · Compression voix : HVC encoder (C, à développer)              │
│  · Compression image : Delta-H + zstd (C, portage depuis Python) │
│  · Interface : Serveur web local (captive portal)                │
│  · OTA : Via HaLow (protocole custom)                            │
│                                                                  │
│  POINT D'ACCÈS VILLAGE (Raspberry Pi / Linux)                    │
│  ──────────────────────────────────────────                       │
│  · OS : Raspberry Pi OS Lite (Debian 12)                         │
│  · AP HaLow : hostapd (patché 802.11ah)                          │
│  · Routage : bird / frr (BGP/OSPF)                               │
│  · VoIP : Asterisk 20 (SIP proxy local)                          │
│  · Messagerie : Synapse (Matrix) ou Prosody (XMPP)              │
│  · DNS : Unbound + blocage pubs                                  │
│  · DHCP : Kea DHCP                                               │
│  · Firewall : nftables                                           │
│  · VPN : WireGuard                                               │
│  · Supervision : Prometheus node_exporter                        │
│  · Conteneurisation : Docker (pour isolation services)           │
│                                                                  │
│  PASSERELLE INTERNET (Mini-PC Linux)                             │
│  ────────────────────────────────────                             │
│  · OS : Debian 12                                                │
│  · Proxy cache : Squid (économise 30-50% data Starlink)         │
│  · DNS : Unbound avec overrides locaux                           │
│  · VoIP Gateway : Asterisk + chan_sip + chan_dongle (GSM)       │
│  · WhatsApp bridge : whatsapp-web.js (Docker)                   │
│  · Telegram bot : python-telegram-bot                            │
│  · Dashboard : Grafana + Prometheus + Loki (logs)               │
│  · Mise à jour dict : rsync depuis serveur central              │
│  · Gestion utilisateurs : FreeIPA ou LDAP                       │
│                                                                  │
│  SERVEUR CENTRAL (Cloud, optionnel pour fédération)              │
│  ────────────────────────────────────────────                     │
│  · Fédération Matrix entre réseaux village                      │
│  · Distribution mises à jour OTA                                 │
│  · Backup des dictionnaires harmoniques                          │
│  · Portail web de gestion (pour admin régional)                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 11.2 Applications Utilisateur

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  APPLICATION MOBILE (basée sur KA Phone PWA)                     │
│  ────────────────────────────────────────────                     │
│                                                                  │
│  · Framework : PWA (HTML5 + Service Worker)                      │
│  · Fonctionne sur : Tout navigateur moderne                      │
│    (Android 5+, iOS 11+, KaiOS 3+)                               │
│  · Installation : URL → « Ajouter à l'écran d'accueil »         │
│  · Taille : < 5 MB (chargée une fois, puis hors ligne)           │
│                                                                  │
│  FONCTIONS :                                                     │
│  ───────────                                                      │
│  📞 APPELS :                                                     │
│     · Numérotation par nom ou numéro village-utilisateur         │
│     · Historique des appels                                      │
│     · Appels de groupe (conférence)                              │
│                                                                  │
│  💬 MESSAGES :                                                   │
│     · Texte, notes vocales, photos                               │
│     · Groupes de discussion                                      │
│     · Statut « vu » / « livré »                                  │
│                                                                  │
│  📷 PHOTOS :                                                     │
│     · Prise de vue → compression automatique harmonique          │
│     · Envoi vers contact ou groupe                               │
│     · Album local                                                │
│                                                                  │
│  🚨 ALERTES :                                                    │
│     · Urgence médicale (KA CARE intégré)                         │
│     · Alerte météo/agricole                                      │
│     · Notification push locale                                   │
│                                                                  │
│  📻 RADIO :                                                      │
│     · Radio communautaire en streaming                           │
│     · Annonces du village                                        │
│     · Programme éducatif harmonique                              │
│                                                                  │
│  💰 KA PAY — PAIEMENTS :                                          │
│     · Portefeuille local chiffré (AES-256-GCM + Ed25519)        │
│     · Transfert entre utilisateurs (< 500 ms)                    │
│     · Paiement commerçants locaux (QR code)                      │
│     · Monnaie communautaire autonome — zéro opérateur            │
│     → Voir SPEC_TECHNIQUE_KA_PAY.md                              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 12. Gestion du Réseau

### 12.1 Rôles Communautaires

| Rôle | Responsabilité | Formation requise |
|------|---------------|:-----------------:|
| **Gardien du réseau** (1 par village) | Vérifie que tout fonctionne, redémarre si besoin | 1 jour |
| **Administrateur technique** (1 pour 10 villages) | Installe, configure, dépanne | 1 semaine |
| **Animateur communautaire** | Forme les utilisateurs, gère les comptes | 2 jours |
| **Trésorier** | Gère la caisse commune (Starlink, maintenance) | Aucune (existant) |

### 12.2 Supervision Technique

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  DASHBOARD DE SUPERVISION (Grafana)                               │
│                                                                  │
│  MÉTRIQUES SURVEILLÉES :                                         │
│  · État des liaisons (up/down, latence, débit, perte paquets)   │
│  · Charge CPU/RAM/disque de chaque nœud                          │
│  · Nombre d'utilisateurs connectés                               │
│  · Appels actifs, qualité (MOS, jitter, perte)                   │
│  · Consommation data Starlink                                    │
│  · Niveau batterie solaire                                       │
│  · Alertes automatiques (SMS/WhatsApp si panne)                  │
│                                                                  │
│  ACCÈS :                                                         │
│  · Local : http://harmonic.local:3000                            │
│  · Distant : via VPN WireGuard                                   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 12.3 Maintenance et Support

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  PLAN DE MAINTENANCE                                             │
│                                                                  │
│  QUOTIDIEN (Gardien) :                                           │
│  · Vérifier LEDs des équipements                                 │
│  · Redémarrer si problème (1 bouton)                             │
│                                                                  │
│  HEBDOMADAIRE (Gardien) :                                        │
│  · Nettoyer panneaux solaires                                    │
│  · Vérifier niveaux batterie                                     │
│  · Rapporter anomalies à l'admin technique                       │
│                                                                  │
│  MENSUEL (Admin technique) :                                     │
│  · Visite de maintenance (ou supervision distante)               │
│  · Mise à jour logicielle                                        │
│  · Vérification physique (câbles, corrosion, fixation mât)      │
│                                                                  │
│  TRIMESTRIEL (Admin technique) :                                 │
│  · Rotation des clés de sécurité                                 │
│  · Mise à jour dictionnaires harmoniques                         │
│  · Test de dégradation batterie                                  │
│                                                                  │
│  ANNUEL :                                                        │
│  · Remplacement batteries (coût ~30€ par site solaire)          │
│  · Inspection complète                                           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Annexes

### A. Acronymes

| Acronyme | Signification |
|----------|---------------|
| RTHC | Réseau Télécom Harmonique Communautaire |
| HVC | Harmonic Voice Codec |
| HHD2 | Harmonic-HCV Dictionary Codec v2 |
| HTP | Harmonic Transport Protocol |
| HaLow | IEEE 802.11ah (Wi-Fi en bande 900 MHz) |
| AP | Access Point (Point d'accès) |
| BH | Backhaul (liaison inter-site) |
| GW | Gateway (Passerelle) |
| HN | Harmonic Node (boîtier utilisateur) |
| PWA | Progressive Web App |
| OTA | Over-The-Air (mise à jour sans fil) |
| LOS | Line of Sight (ligne de vue) |
| QoS | Quality of Service |
| MOS | Mean Opinion Score (qualité vocale perçue) |

### B. Références aux Documents Existants

| Document | Contenu |
|----------|---------|
| BENCHMARK_PHASE6.md | Performances du Harmonic Dictionary (119.5× lossless) |
| BENCHMARK_MOBILE.md | Décodeur mobile, dictionnaires compacts |
| HCV_VS_KA_PHONE.md | Stratégie de déploiement mobile |
| STRATEGIE_DEPLOIEMENT_KA_PHONE.md | Canaux de distribution PWA |
| STRATEGIE_FINANCEMENT.md | Sources de financement |
| KA_CARE/ | Application santé communautaire (modèle d'interface) |
| SPEC_TECHNIQUE_KA_PAY.md | Monnaie communautaire autonome — protocole HPP |
| SPEC_IA_HARMONIQUE_ECOSYSTEM.md | IA Harmonique — couche transversale (fraude, diagnostic, éducation, agriculture) |

---

*Document technique de référence v1.0 — Juillet 2026 — Projet Univers Harmonique*
