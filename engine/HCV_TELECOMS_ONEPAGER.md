# HCV TELECOMS — One-Pager Exécutif

**Compression Harmonique pour Opérateurs Téléphoniques** · Réduisez le trafic transport de ~28 % · Payback < 1 trimestre · Confidential

---

## Le problème
- **Vidéo = ~70–76 % du trafic data mobile** → 80 % d'ici 2028 (Ericsson). Trafic MTN : **+27 %/an** (2,15 EB/mois, 12,5 Go/utilisateur).
- Chaque exaoctet supplémentaire = backhaul, transit, énergie, spectre. Diesel nigérian déjà **> US$350 M/an** ; MTN Nigeria : risque diesel **US$87–102 M/an** (Q1 2026).
- Les codecs actuels (H.264/AV1) sont **déjà au plancher** : les optimiseurs de WAN classiques plafonnent à 1,5–2×.

## La solution — HCV, couche de transcodage transparente
Proxies média insérés dans le réseau (backhaul, IMS, CDN, transit) : **aucun terminal modifié, < 2 ms de latence ajoutée, fallback transparent** sur les codecs natifs.

| Mécanisme | Gain |
|---|---|
| Séparation signal/grain : signal bit-exact (Delta-H + zstd), **grain régénéré déterministe, 0 octet transmis** (seed dérivée) | **2–10×** codec-level, lossless statistique (compatible AV1 Film Grain / H.274) |
| Universal Boost : `compressé < source` **garanti** sur contenus déjà encodés (H.264, MP4, JPEG) | 1,5–4× là où ZIP/GZIP échouent (1,0007×) |
| Upscale Lanczos4 + sharpening adaptatif au décodage | restitution HD sans surcoût |

**Mesuré : 399,8× / PSNR 75 dB** (Strategy C, labo) · 63 ms/frame encode · décodage bit-exact et idempotent.

## L'étude de cas — MTN (données publiques FY2025)
307 M clients · 172 M data · capex R38 Md (~US$2,3 Md) · EBITDA 44,5 %.

| Levier | Économie annuelle |
|---|---|
| Opex transport (backhaul) | US$80–140 M |
| Transit international | US$20–30 M |
| Report de capex capacité | US$30–60 M |
| Énergie (part transport) | US$11–17 M |
| CDN stockage/peering | US$5–10 M |
| **Total** | **≈ US$150–300 M/an** (central ≈ 235 M) |

*Modèle conservateur : −28 % de trafic · Extension 16 marchés : ≈ US$235 M/an (central) · ≈ +3,8 % d'EBITDA.*

## L'offre — 3 modèles au choix (5 marchés : 8 600 Gbps / 500 nœuds · groupe : 17 000 Gbps / 1 000 nœuds)

| Modèle | Coût année 1 | Bénéfice net opérateur (à 200 M d'économies) | Payback |
|---|---|---|---|
| **A. Licence perpétuelle** — US$2 000/Gbps + support 18 %/an | US$22,8 M | ~US$177 M | ~1,5 mois |
| **B. Abonnement opex** — US$650/Gbps/an tout compris | US$8,1 M | ~US$192 M | ~2 semaines |
| **C. Gain-share** — 12 % des économies auditées (plancher 2 M, plafond 35 %) | US$2,5 M (NRE) | ~US$173 M | immédiat |

**Extension groupe 16 marchés :** Option B ≈ US$17 M/an vs 235 M d'économies (central) — payback ~2 semaines.

## Parcours sans risque
**PoC 3 mois — licence gratuite** (risque opérateur ≈ US$175 k de matériel) → **Pilote 50 nœuds Nigeria à −50 %** → **Rollout 500 nœuds, 5 marchés** → Extension 16 marchés. Droits de sortie sans pénalité à chaque phase.

**KPI contractuels :** trafic −25 % · latence < 2 ms · PSNR ≥ 40 dB / SSIM ≥ 0,95 · conformité RTP 100 % · SLA 99,9 % · crédits de service 5 %.

## Pourquoi maintenant
Vidéo → 80 % d'ici 2028 · trafic +27 %/an · énergie 0,24 kWh/Go (vs 0,17 mondial) · spectre rare → chaque bit économisé = capex, diesel et licence en moins, bande en plus pour vos clients. ROI ≈ **5–10× en année 1**.

## Prochaine étape
**NDA + due diligence (2 semaines)** → **Contrat PoC backhaul Lagos (T0)** → **Lecture des KPI à T0+3 mois**.

---
*Sources : MTN Group FY2025 (BusinessDay NG, Developing Telecoms, TelecomLead, Yahoo Finance) · MTN Nigeria Q1 2026 · Ericsson Mobility Report / DataReportal 2025 · AFC 2025 · mesures internes (B3_strategy_c_results.json). Chiffres financiers : modèle illustratif, à auditer sur comptes réels.*
