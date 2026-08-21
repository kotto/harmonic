# HCV TELECOMS — Proposition Commerciale

**Compression Harmonique pour la Bande Passante des Opérateurs — Réduisez le Trafic Transport de ~28 %, Payback < 1 Trimestre**

| | |
|---|---|
| **Destinataire** | MTN Group / MTN Nigeria (illustratif — applicable à tout opérateur mobile) |
| **Version de l'offre** | 1.0 |
| **Date** | 2026-08-04 |
| **Validité** | 90 jours à compter de la date |
| **Base** | Données publiques FY2025 (voir `HCV_TELECOMS_IMPLEMENTATION.md`, §9) |
| **Confidentiel** | Oui — contient des prix indicatifs et des conditions commerciales |

---

## 1. Résumé exécutif (une page)

**Le problème.** La vidéo représente ~70–76 % du trafic data mobile et atteindra 80 % d'ici 2028. Le trafic data de MTN croît de +27 %/an (2,15 EB/mois à 12,5 Go/utilisateur). Chaque exaoctet supplémentaire signifie backhaul, transit, énergie et spectre en plus. Les opérateurs nigérians dépensent déjà > US$350 M/an de diesel ; le transport est l'un des postes d'opex à la croissance la plus rapide.

**La solution.** HCV est une couche de transcodage transparente déployée en proxies média dans le réseau de l'opérateur (backhaul, gateway IMS, CDN, transit). Elle compresse le trafic traversant les segments coûteux **2–10×** (au niveau codec, lossless statistique : signal bit-exact + grain régénéré de manière déterministe, compatible AV1 Film Grain / H.274), avec **< 2 ms de latence ajoutée**, **zéro modification des terminaux**, et une garantie mathématique de **non-expansion** sur les contenus déjà compressés.

**Les chiffres (illustratifs, échelle MTN Group).**

| Élément | Valeur |
|---|---|
| Réduction de trafic sur les segments couverts | ≈ 28 % (conservateur : 70 % vidéo × 50 % de couverture × 5×) |
| Potentiel d'économies annuel | US$150–250 M (rollout 5 marchés) · **US$150–300 M groupe complet (16 marchés), central ≈ 235 M** |
| Coût total de possession (Option A, année 1, 500 nœuds) | ≈ US$23 M |
| Extension groupe (16 marchés, ~1 000 nœuds / ~17 000 Gbps) | logiciel ≈ US$46 M (Option A) ou ≈ US$17 M/an (Option B) |
| **Payback opérateur** | **1–2 mois** (5 marchés) · **2–4 mois groupe complet** |
| **ROI première année** | **≈ 10×** (5 marchés) · **≈ 5–6× groupe complet** |

**L'offre.** Trois modèles commerciaux (licence perpétuelle, abonnement opex, gain-share), un PoC à terme gratuit sur le backhaul de Lagos, et un déploiement par phases du pilote (Nigeria) au groupe (16 marchés). KPI mesurables : réduction de trafic ≥ 25 %, latence < 2 ms, PSNR ≥ 40 dB.

---

## 2. Ce que nous livrons

| Livrable | Contenu |
|---|---|
| **Proxy Edge HCV** | Nœud de transcodage média temps réel (voix + vidéo), niveaux de capacité 10 Gbps / 40 Gbps |
| **Module CDN/Boost HCV** | Universal Boost pour contenus déjà encodés (caches VoD, OTA), non-expansion garantie |
| **Orchestrateur HCV** | Moteur de politiques : sélection de preset par flux (ultra/high/balanced/compact), négociation SDP, fallback codecs natifs |
| **Intégration OSS/BSS** | Métriques SNMP/NetFlow/REST, tableau de bord KPI (trafic, PSNR/SSIM, latence), enregistrements de facturation |
| **Documentation & formation** | Manuels O&M, formation administrateurs 5 jours par marché, transfert de compétences L3 |
| **Garantie** | 12 mois, mises à jour logicielles illimitées pendant la durée |

**Matériel** (serveurs COTS appartenant à l'opérateur, ou proposés via nos partenaires matériels / en location) : US$30–50 k par nœud (dual Xeon/EPYC, 128 Go RAM, NVMe, 2×25 GbE). Non inclus dans les prix de licence.

---

## 3. Modèles commerciaux (au choix)

Tous les prix en USD, départ usine, hors taxes, droits et contenu local.

### Option A — Licence perpétuelle (modèle capex classique)

| Élément | Prix |
|---|---|
| Licence | **US$2 000 par Gbps licencié** (une fois, perpétuelle par nœud) |
| Support & maintenance annuels | 18 % de la valeur de licence/an (première année incluse dans le prix ci-dessous) |
| Intégration (NRE) par marché | US$500 k (intégration SDP/RTP, OSS/BSS, réglages, tests de recette) |

### Option B — Abonnement (opex-friendly, recommandée pour les marchés africains)

| Élément | Prix |
|---|---|
| Abonnement tout compris | **US$650 par Gbps par an** (logiciel, support, mises à jour, sans licence) |
| Intégration (NRE) par marché | US$500 k (payable au rollout) |
| Matériel | location optionnelle fournisseur : US$8 000/nœud/an |

### Option C — Gain-share (intérêts alignés, entrée sans risque)

| Élément | Prix |
|---|---|
| Licences | **Aucune** |
| Rémunération | **12 % des économies brutes auditées**, payé trimestriellement |
| Plancher | US$2 M/an par marché (couvre les coûts de service) |
| Plafond | 35 % des économies auditées |
| Intégration (NRE) | au coût (audité), payable au rollout |

Les économies sont auditées conjointement par les finances de l'opérateur et notre équipe, selon la méthodologie KPI du §7 (trafic × coûts unitaires), approuvée par écrit à la signature du PoC.

### Illustration tarifaire — déploiement groupe 500 nœuds (5 marchés)

Mix de capacité : 300 nœuds edge × 10 Gbps + 120 nœuds core × 40 Gbps + 80 nœuds CDN × 10 Gbps = **8 600 Gbps licenciés**.

| | Option A | Option B | Option C (cas central) |
|---|---|---|---|
| Coût opérateur année 1 | **US$22,8 M** (licences 17,2 + support 3,1 + NRE 2,5) | **US$8,1 M** (5,6 + NRE 2,5) | **US$2,5 M** (NRE au coût) + 12 % des économies |
| Récurrent (année 2+) | US$3,1 M/an | US$5,6 M/an | 12 % des économies (est. 18–30 M) |
| Bénéfice net opérateur, année 1 (à 200 M d'économies) | **~177 M** | **~192 M** | **~173 M** |
| Payback | ~1,5 mois | ~2 semaines | immédiat |

**Recommandation :** Option B pour le pilote (risque le plus faible, opex pur), avec droit de conversion en Option A ou C au rollout ; ou Option C pour les marchés où les économies sont auditables proprement (CDN + transit d'abord).

### Illustration groupe complet — 16 marchés (phase d'extension)

Capacité : ~1 000 nœuds / ~17 000 Gbps licenciés (les 16 marchés).

| | Option A | Option B | Option C (cas central) |
|---|---|---|---|
| Coût logiciel année 1 | ≈ US$46 M (licences 34 + support 6 + NRE 6) | ≈ US$17 M (11 + NRE 6) | NRE ≈ US$6 M + 12 % des économies |
| Récurrent (année 2+) | ≈ US$6 M/an | ≈ US$11 M/an | 12 % des économies (est. 18–36 M) |
| Économies cas central | ≈ US$235 M/an (fourchette 150–300 M) | | |
| Payback | ≈ 2,4 mois (logiciel seul) | ≈ 2 semaines | immédiat |

Note : au niveau groupe, fixer le plancher de l'Option C au **niveau groupe (US$10 M/an)** — un plancher par marché (US$2 M) devient contraignant sur les petits marchés (12 % d'une économie de 7 M = 0,8 M < 2 M).

---

## 4. Feuille de route d'engagement

| Phase | Durée | Périmètre | Conditions commerciales |
|---|---|---|---|
| **0 — PoC** | 3 mois | 5 nœuds, backhaul Lagos + CDN ; top-20 flux live + cache VoD ; critères de succès = KPI §7 | **Licence gratuite** ; l'opérateur paie le matériel au coût (~US$175 k) ; NRE à 50 % (US$250 k, remboursée contre le pilote) |
| **1 — Pilote** | 6 mois | 50 nœuds, MTN Nigeria (Lagos + Abuja) ; top-100 flux ; tableau de bord KPI §7 complet | Option B sur la capacité pilote uniquement, à **−50 %** (US$325/Gbps/an) ; NRE US$250 k |
| **2 — Rollout** | 18 mois | 500 nœuds, 5 marchés (Nigeria, Ghana, Cameroun, Côte d'Ivoire, Ouganda) + option Afrique du Sud/Zambie — ~60 % des économies groupe | Prix catalogue selon le modèle choisi ; NRE US$500 k/marché ; remise de volume ≥ 500 nœuds : −10 % |
| **3 — Extension groupe** | mois 24+ | 16 marchés, ~1 000 nœuds / ~17 000 Gbps — cas central ≈ US$235 M/an d'économies | Cadre groupe renégocié, remise de volume −15 % |

**Droits de sortie :** à chaque frontière de phase, l'opérateur peut résilier sans pénalité ; le matériel reste sa propriété ; aucun verrouillage.

---

## 5. Pourquoi maintenant (facteurs de marché)

1. **Vidéo → 80 % du trafic d'ici 2028** (Ericsson Mobility Report) — la courbe de coût s'accentue ;
2. **Trafic MTN +27 %/an** — l'opex de capacité double environ tous les 3 ans à efficacité constante ;
3. **Énergie** : 0,24 kWh/Go en Afrique vs 0,17 mondial ; MTN Nigeria seule fait face à un risque diesel de US$87–102 M/an (alerte Q1 2026) — moins de bits transportés = moins de kWh ;
4. **Pénurie de spectre** au Nigeria/Ghana — la capacité libérée reporte les capex de licences (libellées en ₦, sensibles aux devises) ;
5. **Écart concurrentiel** : les WAN optimizers génériques (Riverbed, Citrix) atteignent 1,5–2× au niveau protocole ; les vendeurs vidéo (Vantrix et al.) ~2× en ré-encodage. HCV opère **au niveau codec (2–10×)**, lossless statistique, < 2 ms — un ordre de grandeur différent.

---

## 6. Niveaux de service

| Élément SLA | Engagement |
|---|---|
| Disponibilité de la plateforme | 99,9 % mensuel (par cluster de nœuds) |
| Latence ajoutée (voix, paire de proxies E2E) | < 2 ms p95 |
| Qualité vidéo (flux transcodés) | PSNR ≥ 40 dB, SSIM ≥ 0,95 vs référence sans codec |
| Garantie de non-expansion | 100 % des fichiers traités en Boost : `compressé < source` |
| Réponse aux incidents | P1 (panne) : 2 h à distance, 24 h sur site (marchés principaux) · P2 : 8 h · P3 : jour ouvré suivant |
| Crédits de service | 5 % du montant mensuel par manquement P1 disponibilité ou latence, plafonné à 20 % |

---

## 7. Méthodologie KPI du pilote (contractuelle)

| KPI | Cible | Mesure |
|---|---|---|
| Réduction de trafic sur les liens couverts | ≥ 25 % | Compteurs NetFlow/REST à la paire de proxies, hebdomadaire |
| Latence ajoutée | < 2 ms p95 | Sondes RTP synthétiques |
| Qualité de transcodage | PSNR ≥ 40 dB / SSIM ≥ 0,95 | Métriques internes du codec (psnr/ssim, `hcv_pro_codec.py`) |
| Incidents de qualité (MOS < 3) | < 0,5 % des sessions | CDR/RTCP-XR |
| Conformité RTP | 100 % | Tests de conformité par capture |
| Audit des économies | trimestriel | finances opérateur + notre équipe, selon §3 Option C |

En cas de non-atteinte de la cible de réduction de trafic à la sortie du PoC → l'opérateur peut se retirer sans autre obligation.

---

## 8. Conditions commerciales

- **Paiement** : NRE 30 % à la signature / 40 % à la livraison / 30 % à la recette. Licences : 100 % à la livraison. Support/abonnement : annuel d'avance. Facturation USD, net-30/45 ;
- **Risque de change** : prix indexés USD ; si la législation locale impose une facturation locale (ex. Nigeria), conversion au taux de la banque centrale à la date de facture ;
- **Propriété intellectuelle** : tous les logiciels HCV, formats de bitstream et brevets restent la propriété du fournisseur ; l'opérateur reçoit une licence d'utilisation perpétuelle, non exclusive et irrévocable sur les nœuds payés ; **escrow du code source** à partir du mois 12 (libération en cas de défaillance/insolvabilité du fournisseur) ;
- **Garantie** : 12 mois ; plafond de responsabilité = montant des redevances payées au cours des 12 mois précédents ; confidentialité mutuelle ; DPA sur demande ;
- **Conformité réglementaire** : POPIA (Afrique du Sud), NITDA Data Protection (Nigeria), GDPR le cas échéant — le contenu du trafic est transcodé dans le pays, aucun déplacement transfrontalier de données au-delà du transit existant ;
- **Contenu local** : co-développement avec les équipes d'ingénierie de l'opérateur ; option **package de transfert de technologie** (accès complet au code source + 12 mois de développement conjoint) à 1,5× le prix de licence — répond aux exigences de souveraineté/contenu local nationales ;
- **Résiliation** : préavis de 90 jours par l'une ou l'autre partie après l'achèvement du pilote ; droits de sortie selon §4.

---

## 9. Équipe de livraison

| Rôle | ETP |
|---|---|
| Ingénieurs codec (portage C/C++, temps réel) | 3 |
| Ingénieurs intégration (SDP/RTP, OSS/BSS) | 2 |
| SRE / support sur site (par marché) | 2 |
| Architecte solution | 1 |
| Chef de projet | 1 |
| Formateur (par marché, 2 premiers mois) | 1 |
| **Équipe cœur totale** | **8–10** (+ ingénieurs opérateur locaux formés de bout en bout) |

---

## 10. Prochaines étapes

1. **NDA + session de due diligence** (2 semaines) : accès au code de référence, benchmarks, option de validation en laboratoire tiers ;
2. **Contrat de PoC** (T0) : PoC de 3 mois sur le backhaul de Lagos, matériel au coût, licence gratuite — risque opérateur ≈ US$175 k de matériel uniquement ;
3. **Lecture des KPI** à T0+3 mois selon §7 ; go/no-go pour le pilote ;
4. **Pilote → rollout** selon §4, avec remises de volume.

*Cette proposition est indicative et soumise à due diligence finale, revue de contrôle des exportations et négociation mutuelle. Benchmarks cités : 399,8× / 75 dB PSNR sur contenu de test (Strategy C) ; attentes déployées 2–10× selon le mix de contenu.*

---

*Sources : résultats MTN Group FY2025 (BusinessDay NG, Developing Telecoms, TelecomLead, Yahoo Finance) ; MTN Nigeria Q1 2026 ; Ericsson Mobility Report / DataReportal 2025 ; Africa Finance Corporation — State of Africa's Infrastructure 2025 ; mesures internes (B3_strategy_c_results.json).*
