# PROTOCOLE EXPÉRIMENTAL — TEST T* (CAVITÉ MICRO-ONDE 10 GHz)

## Préparation à la mesure décisive de la prédiction E3

**Référence dépôt :** `DEPOT_E3_PREDICTION_TSTAR.md` (déposé 09/08/2026, avant test)
**Valeur déposée :** T* = 0,997 K · occupation moyenne n̄ = φ = 1,6180339887 · rapport p_{n+1}/p_n = 1/φ
**Objectif :** réaliser la première prédiction ex ante falsifiable de la THU, par mesure indépendante et reproductible.

---

## 0. L'ESSENTIEL EN UNE LIGNE

Le test est **une mesure de statistique d'occupation thermique** d'un mode électromagnétique unique (résonateur supraconducteur 10 GHz), thermalisé à ~1 K, dont on compte le nombre de photons par mesure de Fock. Si la distribution mesurée est la distribution géométrique de rapport 1/φ (n̄ = φ), la prédiction E3 est confirmée ; sinon elle est falsifiée.

**Point de méthode critique (hérité du dépôt E3) :** le théorème T5 est une identité algébrique : *pour tout* ΔE, $T^* = \Delta E/(k_B \ln\varphi)$ donne $e^{-\Delta E/k_B T^*} = 1/\varphi$. Le test ne vérifie donc **pas** le théorème (lui est trivial pour n'importe quel système thermalisé). Il vérifie la seule chose qui compte : **que les conditions expérimentales (fréquence 10 GHz, température) sont bien celles annoncées et reproductibles** — c'est-à-dire que la « prédiction » n'est pas un artefact de choix a posteriori de la fréquence.

> **Réécriture honnête de ce que le test démontre :**
> Confirmer n̄ = φ à T = 1/ln φ × (ℏ·2π·10 GHz)/k_B confirmerait uniquement que la statistique de Bose-Einstein et la thermométrie sont correctes — **ce qui est déjà connu et non discriminant.** La valeur scientifique du test T* repose donc sur **l'enjeu inverse** : si la THU affirme que T* est « spéciale » (et pas une simple identité), elle doit montrer une signature *au-delà* de la statistique thermique standard. À défaut, le test T* est une vérification de métrologie, pas de physique nouvelle.

Cette formulation est volontairement la plus exigeante possible : c'est la seule qui protège la théorie d'une « confirmation » triviale qui ne prouverait rien.

---

## 1. DISPOSITIF EXPÉRIMENTAL

### 1.1 Composants

| Élément | Spécification | Fournisseur type |
|---------|---------------|------------------|
| Cryostat à dilution | capacité ≤ 20 mK, stabilité ±1 mK | Bluefors / Oxford |
| Résonateur supraconducteur | cavité coplanaire λ/4, fréquence 10 GHz, Q > 10⁶ | fabrication maison (Al sur saphir) |
| Qubit transmon (détecteur de Fock) | couplé dispersivement au mode ℏω = 2π·10 GHz | fabrication maison |
| Chaîne de mesure | lecture dispersive, amplificateur paramétrique (JPA/TWPA) | standard circuit QED |
| Thermomètre | calibré vs point fixe | références NIST |

### 1.2 Principe de la mesure de Fock

Le nombre de photons n du mode est mesuré par **déplacement résonant de la fréquence du qubit** : l'état de Fock |n⟩ décale la fréquence de transition du qubit de n·χ (décalage dispersif). La lecture projective répétée construit l'histogramme des occupations p_n.

---

## 2. PROTOCOLE

### 2.1 Calibration

1. Mesurer la fréquence exacte f₀ du mode (visée 10,000 GHz, précision 1 kHz).
2. Calculer la température cible déposée :
   $$T^* = \frac{h f_0}{k_B \ln\varphi} = \frac{6{,}626\times10^{-34} \times f_0}{1{,}381\times10^{-23} \times 0{,}48121}$$
   → à f₀ = 10,000 GHz : **T* = 0,9970 K**. (à recalculer avec f₀ mesurée).
3. Régler le cryostat à T*, stabiliser ±1 mK.

### 2.2 Acquisition

1. Thermaliser le mode à T* (attente ≥ 5·τ_th, temps de thermalisation).
2. Injecter un état de Fock de référence pour calibrer la réponse dispersive (n = 0, 1, 2, 3).
3. Effectuer N = 10⁵ mesures projectives de l'occupation.
4. Construire l'histogramme p_n (n = 0…6).

### 2.3 Réduction des données

1. Ajuster p_n à une **distribution géométrique** : $p_n = (1-q)\cdot q^n$.
2. Extraire q mesuré et n̄ mesuré = q/(1−q).
3. Comparer à la valeur déposée q = 1/φ = 0,6180339887, n̄ = φ.

### 2.4 Répétition

- 3 runs indépendants, 2 réglages de température (T* ± 10 mK) pour vérifier la sensibilité.

---

## 3. CRITÈRES DE VERDICT (pré-enregistrés)

| # | Condition | Verdict |
|---|---|---|
| V1 | \|n̄_mesuré − φ\|/φ > 1×10⁻³ (au-delà de l'incertitude combinée) | **Prédiction falsifiée** |
| V2 | q mesuré ≈ 1/φ à 10⁻³ près | **confirmée (métrologie)** |
| V3 | écart systématique reproductible entre runs | **effet à investiguer** |

> **Contrôle de la sensibilité (déposé E3 §4) :** 1e-3 sur n̄ exige un contrôle de température de ±0,88 % de T* ≈ **±9 mK**. C'est atteignable mais non trivial à 1 K — c'est la principale difficulté expérimentale.

---

## 4. CE QUE LE TEST POURRA CONCLURE (et ce qu'il ne POURRA PAS)

| Résultat | Conclusion rigoureuse | Conclusion abusive à éviter |
|---|---|---|
| n̄ = φ à 10⁻³ | La statistique de Bose-Einstein + thermométrie sont correctes à T = ΔE/(k_B lnφ) | « la THU est prouvée » |
| n̄ ≠ φ | Erreur de thermométrie OU de calibration de fréquence | « la THU est réfutée » |
| écart systématique résiduel | signature physique nouvelle possible — à creuser | — |

**La seule issue scientifique réellement discriminante** pour la THU serait de découvrir un écart *au-delà* de la statistique thermique standard — par exemple une anomalie dans la **queue** de la distribution (cohérente avec un terme fractionnaire de la THU). À défaut, T* est un test de métrologie.

---

## 5. COÛT, DURÉE, FAISABILITÉ

| Poste | Estimation |
|---|---|
| Accès cryostat à dilution | collaboration ou location (coût marginal faible si existant) |
| Résonateur 10 GHz + qubit | fabrication ~ quelques semaines |
| Durée totale | 2-3 semaines (calibration + 3 runs) |
| Compétence requise | circuit QED cryogénique (groupe quantique universitaire) |

**Recommandation :** proposer ce protocole à un groupe de circuit QED (ex. LKB-ENS, ETH, Delft, Chalmers) en tant que test de métrologie de routine — l'expérience est *standard* pour un laboratoire de ce type, ce qui rend le test réaliste et indépendant.

---

## 6. PROCHAINES ÉTAPES

1. [ ] Recalculer T* exactement avec f₀ mesurée.
2. [ ] Identifier un laboratoire partenaire (email de proposition + ce protocole).
3. [ ] Signer un accord de publication du résultat, même négatif (déjà engagé dans E3 §6).
4. [ ] Horizon : 3-6 mois pour un premier résultat.

---

*Protocole préparatoire — le test ne prouvera pas la THU par lui-même, mais il en fixera la première donnée ex ante mesurée par un tiers, ce qui est exactement le seuil que la théorie doit franchir.*
