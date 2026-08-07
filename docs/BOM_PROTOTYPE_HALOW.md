# Nomenclature d'Achat — Prototype Réseau Harmonique (HaLow)

**Document** : BOM-HLW-1.0  
**Date** : Juillet 2026  
**Usage** : Liste d'achat pour le prototype de validation technique (Phase 1)

---

## Résumé

Ce document liste TOUT le matériel nécessaire pour construire le premier prototype
du réseau harmonique : 2 nœuds HaLow + 1 passerelle de test.

**Budget total : ~650-850€** (selon options et frais de port)  
**Délai de livraison : 2-4 semaines** (composants distribués internationalement)

---

## 1. Modules HaLow (Critique — Commander en Premier)

### Option A : Morse Micro MM6108 (Recommandé)

| Article | Référence | Qté | Prix Unitaire | Total |
|---------|-----------|:---:|:------------:|:-----:|
| Module d'évaluation MM6108 | Morse Micro MM6108-EVK | 2 | ~150€ | ~300€ |
| OU Module mini-PCIe | MM6108-MPCIe (si disponible) | 2 | ~80€ | ~160€ |
| Antenne 900 MHz | Dipôle 3 dBi, SMA | 2 | ~8€ | ~16€ |
| Câble pigtail | u.FL → SMA female, 15cm | 2 | ~5€ | ~10€ |

**Fournisseurs :**
- Morse Micro directement (demande échantillon/devis) : https://www.morsemicro.com/
- Mouser/Digikey (rechercher « Morse Micro » ou « MM6108 »)
- **Délai typique : 2-4 semaines** (production encore limitée en 2026)

### Option B : Newracom NRC7292 (Alternative)

Si Morse Micro n'est pas disponible :

| Article | Référence | Qté | Prix Unitaire | Total |
|---------|-----------|:---:|:------------:|:-----:|
| Module NRC7292 | Newracom NRC7292-SHLD | 2 | ~60€ | ~120€ |
| Antenne 900 MHz | Dipôle 3 dBi, SMA | 2 | ~8€ | ~16€ |
| Câble pigtail | u.FL → SMA | 2 | ~5€ | ~10€ |

**Fournisseurs :**
- Newracom : https://newracom.com/
- Mouser : rechercher « NRC7292 »

### Option C : Fallback ESP32 + LoRa (Plan B minimal)

Si HaLow n'est pas disponible dans les délais, prototype sur LoRa :

| Article | Référence | Qté | Prix Unitaire | Total |
|---------|-----------|:---:|:------------:|:-----:|
| Heltec WiFi LoRa 32 V3 | ESP32-S3 + SX1262 | 2 | ~20€ | ~40€ |
| Antenne LoRa 868/915 MHz | Dipôle 3 dBi, IPEX | 2 | ~5€ | ~10€ |

**Fournisseurs :**
- AliExpress : « Heltec WiFi LoRa 32 V3 » (livraison 2-3 semaines)
- Amazon : selon région
- **Avantage : disponible immédiatement, permet d'avancer sur le code**

---

## 2. Cartes de Développement (Support)

| Article | Référence | Qté | Prix Unitaire | Total |
|---------|-----------|:---:|:------------:|:-----:|
| Raspberry Pi 4 (2 GB) | Ou Orange Pi 3 LTS | 2 | ~45€ | ~90€ |
| Carte microSD 32 GB | Sandisk Extreme / Samsung EVO | 2 | ~8€ | ~16€ |
| Alimentation USB-C 5V 3A | Officielle RPi ou équivalente | 2 | ~10€ | ~20€ |
| Câble Ethernet blindé | Cat6, 2m | 2 | ~5€ | ~10€ |

**Note :** Si vous utilisez l'Option C (ESP32), les RPi ne sont nécessaires que pour
la passerelle/supervision. L'ESP32 est autonome.

---

## 3. Audio (pour le test vocal)

| Article | Référence | Qté | Prix Unitaire | Total |
|---------|-----------|:---:|:------------:|:-----:|
| Micro USB | Mini microphone USB (type podcast) | 2 | ~15€ | ~30€ |
| OU carte son USB | Carte son USB externe + micro 3.5mm | 2 | ~12€ | ~24€ |
| Haut-parleur | Enceinte USB ou jack 3.5mm | 2 | ~15€ | ~30€ |
| Casque (optionnel) | Pour tests en environnement bruyant | 2 | ~20€ | ~40€ |

---

## 4. Énergie Solaire (pour test autonome)

| Article | Référence | Qté | Prix Unitaire | Total |
|---------|-----------|:---:|:------------:|:-----:|
| Panneau solaire 50W | Monocristallin 12V | 1 | ~50€ | ~50€ |
| Batterie 12V 20Ah | LiFePO4 recommandée (ou AGM plomb) | 1 | ~60€ | ~60€ |
| Régulateur charge | PWM 10A 12V/24V | 1 | ~15€ | ~15€ |
| Câbles + connecteurs MC4 | Kit câblage solaire | 1 | ~20€ | ~20€ |

**Note :** Pour le test initial, l'alimentation secteur suffit. Le solaire est pour
le test en conditions réelles (extérieur, pas d'accès électricité).

---

## 5. Infrastructure (mât, boîtiers)

| Article | Référence | Qté | Prix Unitaire | Total |
|---------|-----------|:---:|:------------:|:-----:|
| Mât télescopique 6m | Aluminium, haubans inclus | 1 | ~60€ | ~60€ |
| OU fixation murale | Support antenne orientable | 2 | ~15€ | ~30€ |
| Boîtier étanche IP65 | 200×150×100mm, avec presse-étoupes | 2 | ~20€ | ~40€ |
| Parafoudre RJ45 | Pour protection ethernet extérieur | 2 | ~15€ | ~30€ |
| Bride de fixation | Pour antenne sur mât | 2 | ~5€ | ~10€ |

---

## 6. Câbles et Connecteurs

| Article | Référence | Qté | Prix Unitaire | Total |
|---------|-----------|:---:|:------------:|:-----:|
| Câble Ethernet extérieur blindé | Cat6, 20m | 1 | ~25€ | ~25€ |
| Câble Ethernet court | Cat6, 1m (dans le boîtier) | 4 | ~3€ | ~12€ |
| Câble USB-A → USB-C | Alimentation, 2m | 2 | ~5€ | ~10€ |
| Connecteurs SMA | SMA male pour câble coaxial | 4 | ~3€ | ~12€ |
| Gaine thermorétractable | Kit varié | 1 | ~10€ | ~10€ |
| Serre-câbles | Lot de 100 | 1 | ~5€ | ~5€ |

---

## 7. Outillage (si pas déjà possédé)

| Article | Usage | Prix |
|---------|-------|:----:|
| Multimètre | Vérification tensions | ~20€ |
| Fer à souder + étain | Connexions antennes | ~30€ |
| Tournevis précision | Boîtiers, borniers | ~10€ |
| Pince à dénuder | Câbles électriques | ~10€ |
| Clé dynamométrique SMA | Serrage connecteurs antenne (optionnel) | ~20€ |

---

## 8. Récapitulatif Budget

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  OPTION A : HaLow Morse Micro (recommandé)                       │
│  ────────────────────────────────────────                         │
│  · 2 × module HaLow + antennes         : 326 – 350€             │
│  · 2 × Raspberry Pi 4 + SD + alim     : 126€                    │
│  · Audio (micros + HP)                 :  60 – 80€             │
│  · Infrastructure (mât, boîtiers)      : 150 – 200€             │
│  · Câbles + connecteurs                :  74€                    │
│  · Solaire (optionnel)                 : 145€                    │
│  ──────────────────────────────────────────                      │
│  TOTAL (sans outillage, sans solaire)  : ~766€                  │
│  TOTAL (avec solaire)                  : ~911€                  │
│                                                                  │
│  OPTION C : Fallback LoRa (minimal)                              │
│  ─────────────────────────────────────                            │
│  · 2 × Heltec WiFi LoRa 32 V3         :  40€                    │
│  · Antennes + câbles                   :  20€                    │
│  · Audio (micros USB)                  :  60€                    │
│  · 1 × Raspberry Pi (passerelle)      :  63€                    │
│  · Divers                              :  50€                    │
│  ──────────────────────────────────────────                      │
│  TOTAL (Option C)                      : ~233€                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 9. Instructions de Commande

### Étape 1 : Commander les modules HaLow (DÈS MAINTENANT — délai long)

1. **Contacter Morse Micro** : https://www.morsemicro.com/contact/
   - Demander 2 × module d'évaluation MM6108
   - Expliquer brièvement le projet (« réseau communautaire rural, open source, non commercial »)
   - Ils peuvent offrir un tarif réduit ou un prêt

2. **Alternative Newracom** : https://newracom.com/contact/
   - Demander 2 × NRC7292-SHLD

3. **En parallèle, commander l'Option C (LoRa)** sur AliExpress/Amazon
   - Ça permet de commencer le développement logiciel immédiatement
   - Le HVC fonctionne indépendamment de la radio

### Étape 2 : Commander le reste

- **Raspberry Pi** : Amazon, Kubii.fr, ou revendeur local
- **Audio** : Amazon (micro USB basique)
- **Solaire** : Amazon ou magasin de bricolage
- **Câbles** : Amazon Basics ou magasin électronique

### Étape 3 : Pendant l'attente → Développement logiciel

- Tester le HVC sur PC (voir `harmonic_voice_codec.py`)
- Préparer les scripts de configuration réseau
- Préparer les images SD pour les RPi

---

## 10. Checklist de Réception

```
☐ Modules HaLow (Morse Micro ou Newracom)
☐ Antennes 900 MHz + câbles pigtails
☐ Raspberry Pi 4 × 2
☐ Cartes microSD 32 GB × 2
☐ Alimentations USB-C × 2
☐ Micros USB × 2
☐ Haut-parleurs × 2
☐ Câbles Ethernet
☐ Boîtiers étanches
☐ (Optionnel) Panneau solaire + batterie + régulateur
```

---

*Nomenclature v1.0 — Projet Univers Harmonique*
