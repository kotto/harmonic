# HCV TELECOMS — Commercial Proposal

**Harmonic Compression for Operator Bandwidth — Reduce Transport Traffic by ~28 %, Payback < 1 Quarter**

| | |
|---|---|
| **Prepared for** | MTN Group / MTN Nigeria (illustrative — applicable to any mobile operator) |
| **Offer version** | 1.0 |
| **Date** | 2026-08-04 |
| **Validity** | 90 days from date |
| **Basis** | Public FY2025 data (see `HCV_TELECOMS_IMPLEMENTATION_EN.md`, §9) |
| **Confidential** | Yes — contains indicative pricing and commercial terms |

---

## 1. Executive summary (one page)

**The problem.** Video is ~70–76 % of mobile data traffic and heading to 80 % by 2028. MTN's data traffic is growing +27 %/year (2.15 EB/month at 12.5 GB/user). Every additional exabyte means backhaul, transit, energy and spectrum spend. Nigerian operators already burn > US$350 M/year of diesel; transport is one of the fastest-growing opex items.

**The solution.** HCV is a transparent transcoding layer deployed as media proxies in the operator's network (backhaul, IMS gateway, CDN, transit). It compresses the traffic crossing expensive segments **2–10×** (codec-level, statistical-lossless: signal bit-exact + deterministically regenerated grain, AV1 Film Grain / H.274 compatible), with **< 2 ms added latency**, **zero terminal modification**, and a mathematical **no-expansion guarantee** on already-compressed content.

**The numbers (illustrative, MTN Group scale).**

| Item | Value |
|---|---|
| Traffic reduction on covered segments | ≈ 28 % (conservative: 70 % video × 50 % coverage × 5×) |
| Annual savings potential | US$150–250 M (5-market rollout) · **US$150–300 M group-wide (16 markets), central ≈ 235 M** |
| Total cost of ownership (Option A, year 1, 500 nodes) | ≈ US$23 M |
| Group-wide extension (16 markets, ~1,000 nodes / ~17,000 Gbps) | software ≈ US$46 M (Option A) or ≈ US$17 M/yr (Option B) |
| **Operator payback** | **1–2 months** (5 markets) · **2–4 months group-wide** |
| **First-year ROI** | **≈ 10×** (5 markets) · **≈ 5–6× group-wide** |

**The offer.** Three commercial models (perpetual license, opex subscription, gain-share), a free-term PoC on the Lagos backhaul, and a phased rollout from pilot (Nigeria) to group (16 markets). Measurable KPIs: ≥ 25 % traffic reduction, < 2 ms latency, PSNR ≥ 40 dB.

---

## 2. What we deliver

| Deliverable | Content |
|---|---|
| **HCV Edge Proxy** | Real-time media transcoding node (voice + video), 10 Gbps/40 Gbps capacity tiers |
| **HCV CDN/Boost module** | Universal Boost for already-encoded content (VoD caches, OTA), no-expansion guaranteed |
| **HCV Orchestrator** | Policy engine: per-stream preset selection (ultra/high/balanced/compact), SDP codec negotiation, fallback to native codecs |
| **OSS/BSS integration** | SNMP/NetFlow/REST metrics, KPI dashboard (traffic, PSNR/SSIM, latency), billing records |
| **Documentation & training** | O&M manuals, 5-day administrator training per market, L3 knowledge transfer |
| **Warranty** | 12 months, unlimited software updates during term |

**Hardware** (operator-owned COTS servers, or offered via our hardware partners / lease): US$30–50 k per node (dual Xeon/EPYC, 128 GB RAM, NVMe, 2×25 GbE). Not included in license pricing.

---

## 3. Commercial models (choose one)

All prices in USD, ex-works, excluding taxes, duties and local content.

### Option A — Perpetual license (classic capex model)

| Item | Price |
|---|---|
| License fee | **US$2,000 per licensed Gbps** (one-time, perpetual per node) |
| Annual support & maintenance | 18 % of license value/year (first year included in price below) |
| Integration (NRE) per market | US$500 k (SDP/RTP integration, OSS/BSS, tuning, acceptance tests) |

### Option B — Subscription (opex-friendly, recommended for African markets)

| Item | Price |
|---|---|
| All-inclusive subscription | **US$650 per Gbps per year** (software, support, updates, no license) |
| Integration (NRE) per market | US$500 k (payable on rollout) |
| Hardware | optional vendor lease: US$8,000/node/year |

### Option C — Gain-share (aligned interest, zero-risk entry)

| Item | Price |
|---|---|
| License fees | **None** |
| Fee | **12 % of audited gross savings**, paid quarterly |
| Floor | US$2 M/year per market (covers service costs) |
| Cap | 35 % of audited savings |
| Integration (NRE) | at cost (audited), payable on rollout |

Savings are audited jointly by operator finance and our team, on the KPI methodology of §7 (traffic × unit costs, agreed in writing at PoC signature).

### Pricing illustration — 500-node group deployment (5 markets)

Capacity mix: 300 edge nodes × 10 Gbps + 120 core nodes × 40 Gbps + 80 CDN nodes × 10 Gbps = **8,600 licensed Gbps**.

| | Option A | Option B | Option C (central case) |
|---|---|---|---|
| Year 1 cost to operator | **US$22.8 M** (licenses 17.2 + support 3.1 + NRE 2.5) | **US$8.1 M** (5.6 + NRE 2.5) | **US$2.5 M** (NRE at cost) + 12 % of savings |
| Recurring (year 2+) | US$3.1 M/yr | US$5.6 M/yr | 12 % of savings (est. 18–30 M) |
| Operator net benefit, year 1 (at 200 M savings) | **~177 M** | **~192 M** | **~173 M** |
| Payback | ~1.5 months | ~2 weeks | immediate |

**Recommendation:** Option B for the pilot (lowest risk, pure opex), with a right to convert to Option A or C at rollout; or Option C for markets where savings can be audited cleanly (CDN + transit first).

### Group-wide illustration — 16 markets (extension phase)

Capacity: ~1,000 nodes / ~17,000 licensed Gbps (all 16 markets).

| | Option A | Option B | Option C (central case) |
|---|---|---|---|
| Year-1 software cost | ≈ US$46 M (licenses 34 + support 6 + NRE 6) | ≈ US$17 M (11 + NRE 6) | NRE ≈ US$6 M + 12 % of savings |
| Recurring (year 2+) | ≈ US$6 M/yr | ≈ US$11 M/yr | 12 % of savings (est. 18–36 M) |
| Central-case savings | ≈ US$235 M/yr (range 150–300 M) | | |
| Payback | ≈ 2.4 months (software only) | ≈ 2 weeks | immediate |

Note: at group level, set the Option C floor at **group level (US$10 M/year)** — a per-market floor (US$2 M) binds on small markets (12 % of a US$7 M saving = US$0.8 M < US$2 M).

---

## 4. Engagement roadmap

| Phase | Duration | Scope | Commercial terms |
|---|---|---|---|
| **0 — PoC** | 3 months | 5 nodes, Lagos backhaul + CDN; top-20 live streams + VoD cache; success criteria = §7 KPIs | **License free**; operator pays hardware at cost (~US$175 k); NRE at 50 % (US$250 k, refunded against pilot) |
| **1 — Pilot** | 6 months | 50 nodes, MTN Nigeria (Lagos + Abuja); top-100 streams; full §7 KPI dashboard | Option B on pilot capacity only, at **50 % discount** (US$325/Gbps/yr); NRE US$250 k |
| **2 — Rollout** | 18 months | 500 nodes, 5 markets (Nigeria, Ghana, Cameroon, Côte d'Ivoire, Uganda) + option SA/Zambia — ~60 % of group savings | List pricing per chosen model; NRE US$500 k/market; volume rebate ≥ 500 nodes: −10 % |
| **3 — Group extension** | months 24+ | 16 markets, ~1,000 nodes / ~17,000 Gbps — central case ≈ US$235 M/yr savings | Re-negotiated group framework, −15 % volume rebate |

**Exit rights:** at any phase boundary, operator may terminate without penalty; all hardware remains operator property; no lock-in.

---

## 5. Why now (market drivers)

1. **Video → 80 % of traffic by 2028** (Ericsson Mobility Report) — the cost curve is steepening;
2. **MTN traffic +27 %/year** — capacity opex doubles roughly every 3 years at current efficiency;
3. **Energy**: 0.24 kWh/GB in Africa vs 0.17 global; MTN Nigeria alone faces US$87–102 M annual diesel risk (Q1 2026 warning) — fewer transported bits = fewer kWh;
4. **Spectrum scarcity** in Nigeria/Ghana — freed capacity defers license capex (₦-denominated, hard-currency-sensitive);
5. **Competitive gap**: generic WAN optimizers (Riverbed, Citrix) reach 1.5–2× on protocol level; video-specific vendors (Vantrix et al.) ~2× on re-encode. HCV operates **codec-level (2–10×)**, statistical-lossless, < 2 ms — a different order of magnitude.

---

## 6. Service levels

| SLA item | Commitment |
|---|---|
| Platform availability | 99.9 % monthly (per node cluster) |
| Added latency (voice, E2E proxy pair) | < 2 ms p95 |
| Video quality (transcoded streams) | PSNR ≥ 40 dB, SSIM ≥ 0.95 vs codec-free reference |
| No-expansion guarantee | 100 % of Boost-processed files `compressed < source` |
| Incident response | P1 (outage): 2 h remote, 24 h on-site (major markets) · P2: 8 h · P3: next business day |
| Service credits | 5 % of monthly fee per missed P1 availability or latency SLA, capped 20 % |

---

## 7. KPI methodology for the pilot (contractually binding)

| KPI | Target | Measurement |
|---|---|---|
| Traffic reduction on covered links | ≥ 25 % | NetFlow/REST counters at proxy pair, weekly |
| Added latency | < 2 ms p95 | synthetic RTP probes |
| Transcode quality | PSNR ≥ 40 dB / SSIM ≥ 0.95 | codec-internal metrics (`hcv_pro_codec.py` psnr/ssim) |
| Quality incidents (MOS < 3) | < 0.5 % sessions | CDR/RTCP-XR |
| RTP compliance | 100 % | capture-based conformance tests |
| Savings audit | quarterly | operator finance + our team, per §3 Option C |

Failure to meet traffic-reduction target at PoC exit → operator may walk away with no further obligation.

---

## 8. Commercial terms

- **Payment**: NRE 30 % on signature / 40 % on delivery / 30 % on acceptance. Licenses: 100 % on delivery. Support/subscription: annually in advance. Invoicing USD, net-30/45;
- **Currency risk**: prices USD-indexed; where local law requires local invoicing (e.g., Nigeria), conversion at central-bank rate on invoice date;
- **IP**: all HCV software, bitstream formats and patents remain vendor IP; operator receives perpetual, non-exclusive, irrevocable use license on paid nodes; **source-code escrow** from month 12 (release on vendor failure/insolvency);
- **Warranty**: 12 months; liability cap = fees paid in the 12 prior months; mutual confidentiality; DPA on request;
- **Regulatory compliance**: POPIA (South Africa), NITDA Data Protection (Nigeria), GDPR where applicable — traffic content is transcoded in-country, no cross-border data movement beyond existing transit;
- **Local content**: co-development with operator engineering teams; optional **technology-transfer package** (full source access + 12-month joint development) at 1.5× license uplift — addresses national sovereignty/local-content requirements;
- **Termination**: either party 90-day notice after pilot completion; exit rights per §4.

---

## 9. Delivery team

| Role | FTE |
|---|---|
| Codec engineers (C/C++ port, real-time) | 3 |
| Integration engineers (SDP/RTP, OSS/BSS) | 2 |
| SRE / on-site support (per market) | 2 |
| Solution architect | 1 |
| Project manager | 1 |
| Trainer (per market, first 2 months) | 1 |
| **Total core team** | **8–10** (+ local operator engineers trained end-to-end) |

---

## 10. Next steps

1. **NDA + due-diligence session** (2 weeks): access to reference code, benchmarks, third-party lab validation option;
2. **PoC contract** (T0): 3-month Lagos backhaul PoC, hardware at cost, license free — operator risk ≈ US$175 k hardware only;
3. **KPI readout** at T0+3 months against §7; go/no-go for pilot;
4. **Pilot → rollout** per §4, with volume rebates.

*This proposal is indicative and subject to final due diligence, export-control review and mutual negotiation. Benchmarks quoted: 399.8× / 75 dB PSNR on test content (Strategy C); deployed expectations 2–10× depending on content mix.*

---

*Sources: MTN Group FY2025 results (BusinessDay NG, Developing Telecoms, TelecomLead, Yahoo Finance); MTN Nigeria Q1 2026; Ericsson Mobility Report / DataReportal 2025; Africa Finance Corporation — State of Africa's Infrastructure 2025; in-house measurements (B3_strategy_c_results.json).*
