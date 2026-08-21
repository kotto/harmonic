# Fabrication additive (3D) vs traditionnelle pour les dispositifs médicaux harmoniques

---

## Analyse par dispositif

### 1. CardioHarmon (tensiomètre harmonique)

| Composant | Fabrication | Méthode |
|---|---|---|
| Circuit imprimé PCB | Standard | Chine/JLCPCB (2 €) |
| Microcontrôleur STM32 | Standard | Achat (4 €) |
| Capteur pression BMP280 | Standard | Achat (2,50 €) |
| Bluetooth HC-05 | Standard | Achat (2,50 €) |
| Batterie LiPo | Standard | Achat (2 €) |
| **Boîtier** | **3D** | **PLA/PETG, 2h, 0,20 €** |
| **Brassard** | 3D (tissu) | Impression textile ou standard |
| Assemblage | Manuel | 15 min |

**Verdict :** Boîtier 3D, reste standard. Le coût total du boîtier passe de 5 € (injection plastique, moule 5 000 €) à 0,20 € (3D, sans moule).

---

### 2. NeuroHarmon (casque EEG)

| Composant | Fabrication | Méthode |
|---|---|---|
| ADS1299 (ampli EEG) | Standard | Achat (15 €) |
| Microcontrôleur nRF52 | Standard | Achat (5 €) |
| Électrodes sèches | Standard | Achat (8 €/4) |
| Batterie | Standard | Achat (3 €) |
| **Arceau casque** | **3D** | **PLA flexible, 4h, 0,50 €** |
| **Connecteurs électrodes** | **3D** | **PLA, 30 min, 0,05 €** |
| PCB | Standard | JLCPCB (2 €) |

**Verdict :** Arceau et supports d'électrodes en 3D. Le casque peut être personnalisé pour chaque patient (taille, forme du crâne) — impossible avec un moule plastique standard.

---

### 3. ThermoPatch (patch T*)

| Composant | Fabrication | Méthode |
|---|---|---|
| MLX90614 (capteur IR) | Standard | Achat (8 €) |
| nRF52832 (BLE) | Standard | Achat (4 €) |
| Batterie fine | Standard | Achat (2 €) |
| **PCB flexible** | **Standard** | **PCB flexible Chine (5 €)** |
| **Adhésif médical** | **Standard** | **Achat (1 €)** |
| **Boîtier souple** | **3D TPU** | **Filament flexible, 0,30 €** |

**Verdict :** Le PCB flexible nécessite une fabrication standard (PCB pliable). Le boîtier souple peut être imprimé en TPU (filament flexible). Le patch est le plus difficile à 3D-riser à cause du PCB flexible, mais le boîtier et le prototype sont faisables.

---

### 4. Échographe harmonique

| Composant | Fabrication | Méthode |
|---|---|---|
| Sonde piézo | Standard | Achat (500-1000 €) |
| Tablette Android | Standard | Achat (200 €) |
| Module USB/hôte | Standard | Achat (10 €) |
| **Boîtier sonde** | **3D** | **Résine, 3h, 0,50 €** |
| **Support tablette** | **3D** | **PLA, 2h, 0,20 €** |
| **Gel de couplage** | Standard | Achat (5 €/litre) |

**Verdict :** Le boîtier de la sonde et le support tablette sont 3D. La sonde elle-même est standard. C'est le dispositif le plus facile à fabriquer localement.

---

### 5. Scanner harmonique

| Composant | Fabrication | Méthode |
|---|---|---|
| Tube X 5 kW | Standard | Achat (5 000 €) |
| Détecteurs photodiodes | Standard | Achat (3 000 €) |
| Alimentation HT | Standard | Achat (2 000 €) |
| **Gantry (structure tournante)** | **3D** | **PLA/grand format, 5 kg, 50 €** |
| **Capotage blindé** | **Standard** | **Tôle acier 1 mm (100 €)** |
| **Support patient** | **Mixte** | **Alu + 3D (200 €)** |
| GPU | Standard | Achat (300 €) |

**Verdict :** Le gantry (structure mécanique tournante) peut être imprimé en 3D grand format sur une imprimante 1m³ (type Modix Big-1800, 3 000 €). Le blindage est en tôle (pas de 3D). Le tube X et les détecteurs restent standard.

---

### 6. IRM bas champ 0.05T

| Composant | Fabrication | Méthode |
|---|---|---|
| Aimant NdFeB 0.05T | Standard | Achat (5 000 €) |
| Bobines de gradient | **3D + cuivre** | **Support 3D + fil cuivre bobiné** |
| Bobine RF | **3D + cuivre** | **Support 3D + fil cuivre** |
| Amplificateur RF | Standard | Achat (1 500 €) |
| Générateur gradient | Standard | Achat (1 500 €) |
| GPU | Standard | Achat (300 €) |
| **Structure porteuse** | **3D** | **PLA grand format, 10 kg, 100 €** |
| **Lit patient** | **Mixte** | **Alu + 3D (200 €)** |
| **Blindage RF** | Standard | Tôle acier + cuivre (500 €) |

**Verdict :** Les supports de bobines de gradient et RF sont imprimés en 3D, puis le fil de cuivre est bobiné manuellement. C'est une approche classique dans les IRM open-source (projet OpenMRI). La structure porteuse est 3D grand format.

---

## Récapitulatif : ce qui peut être 3D vs standard

| Composant | 3D possible | Standard nécessaire |
|---|---|---|
| Boîtiers, capots, arceaux | ✅ **Oui** | |
| Supports de bobines | ✅ **Oui** | |
| Connecteurs, adaptateurs | ✅ **Oui** | |
| Pièces mécaniques (gantry, lit) | ✅ **Oui** | |
| PCB, circuits imprimés | ❌ | ✅ Standard |
| Capteurs, puces, aimants | ❌ | ✅ Achat |
| Tubes X, détecteurs | ❌ | ✅ Achat |
| Blindage RF/rayons X | ❌ | ✅ Tôle/cuivre |
| Câbles, connecteurs électriques | ❌ | ✅ Standard |
| Sondes piézoélectriques | ❌ | ✅ Achat |

---

## Coût d'une imprimante 3D adaptée

| Type | Modèle | Volume | Prix | Usage |
|---|---|---|---|---|
| Desktop | Bambu Lab A1 mini | 18×18×18 cm | 300 € | Prototypes, boîtiers |
| Desktop | Prusa MK4 | 25×21×22 cm | 800 € | Pièces qualité médicale |
| Grand format | Creality CR-10 S5 | 50×50×50 cm | 600 € | Gantry, lit patient |
| Très grand format | Modix Big-1800 | 180×180×180 cm | 3 000 € | Structure IRM complète |
| Flexible | Bambu Lab X1C + AMS | 25×25×26 cm | 1 500 € | TPU, pièces souples |

**Investissement total recommandé :** ~3 000 € pour une imprimante grand format (Modix) + 1 500 € pour une imprimante multi-matériaux (X1C) = **4 500 €**.

---

## Avantages de la 3D pour les pays en développement

| Avantage | Explication |
|---|---|
| **Pas de moule** | L'injection plastique nécessite un moule à 5 000-50 000 €. La 3D n'a pas ce coût |
| **Pas de stock** | On imprime à la demande, pièce par pièce |
| **Réparation locale** | Une pièce cassée est réimprimée en 24h, pas importée en 3 mois |
| **Personnalisation** | Chaque casque EEG peut être adapté à la morphologie du patient |
| **Évolution** | Le design peut être amélioré en continu, pas figé par un moule |
| **Transfert de technologie** | Le fichier STL se télécharge, la machine produit la pièce |

---

## Conclusion

**Approche mixte recommandée :**

```
Pièces 3D (40% du dispositif en valeur) :
  → Boîtiers, supports, structures mécaniques
  → Imprimé localement, à la demande

Pièces standard (60% du dispositif en valeur) :
  → Capteurs, puces, PCB, aimants, tubes X
  → Acheté en ligne, importé

Assemblage final :
  → Local, par technicien formé
  → Test et calibration sur place
```

**Pour un pays en développement :**
- Investissement initial : **4 500 €** (imprimantes 3D)
- Coût par échographe harmonique : **~5 500 €** (500 € de pièces 3D + 5 000 € de composants standards)
- Délai d'installation : **1 semaine** (impression 3D + assemblage + test)
- Maintenance : **0 €** (pièces de rechange imprimées localement)

**L'impression 3D ne remplace pas tout, mais elle EST le facteur clé qui rend la fabrication locale possible.** Sans elle, chaque pièce cassée nécessite une importation depuis l'étranger. Avec elle, un hôpital peut produire ses propres pièces de rechange en 24h.