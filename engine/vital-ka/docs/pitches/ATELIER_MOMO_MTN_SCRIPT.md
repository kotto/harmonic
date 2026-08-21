# Script d'Atelier — 60 minutes · Direction MoMo MTN Cameroun

**Objectif de l'atelier** : obtenir (1) l'accord technique sur l'architecture UM sur MoMo, et (2) l'engagement de signer le **MoU pilote** (avec exclusivité Cameroun) sous 3 semaines.

| | |
|---|---|
| **Durée** | 60 min (atelier technique : prévoir la Direction MoMo + 1 ingénieur API + 1 compliance/AML) |
| **Prérequis** | La réunion Fondation a eu lieu · l'introduction MoMo est faite · NDA signé |
| **Matériel** | Démo smartphone (mode avion) · deck HTML slides 4-5-8 · architecture UM imprimée (schéma) · brouillon de MoU (6 clauses) en 2 pages |
| **Règle d'or** | Cette réunion ne vend PAS la santé (déjà fait) — elle vend la **machine à cash-flow MoMo** : change 1–2 % + commission + wallets. |

---

## Déroulé minute par minute

### 0:00–0:05 — Ouverture : le contexte (5 min)
**Message d'ouverture (à dire mot pour mot, ou presque) :**
> *« La Fondation vous a remis le projet que nous venons de lancer avec elle. Aujourd'hui, on ne parle pas santé — on parle du meilleur levier que MTN MoMo ait pour consolider ses 60 % de part de marché face à Orange Money : le wallet santé. On vous montre comment ça s'encaisse, et on vous laisse le schéma d'architecture. »*

**Pourquoi ça marche** : vous parlez à un directeur de P&L, pas à un philanthrope. Le premier mot doit être « parts de marché », pas « ODD 3 ».

### 0:05–0:12 — La démo courte (7 min) + les chiffres MoMo
**Version courte de la démo** (même séquence que la Fondation, 4 étapes seulement) :
1. Mode avion → diagnostic → ordonnance QR (30 secondes) ;
2. Wallet UM : *« La diaspora envoie 3 000 UM. »* ;
3. QR pharmacien : *« La pharmacie encaisse en UM. »* ;
4. **Rallumer le réseau → synchronisation → conversion UM → FCFA côté MoMo.** La phrase :
   > *« Chaque cycle de ce schéma = 1 transaction MoMo. Chaque patient = 1 wallet MoMo. C'est votre volume, pas le nôtre. »*

**Les 3 chiffres qui comptent pour eux** :
- 60 % de part de marché MoMo vs Orange ~40 % → le wallet santé est une arme de fidélisation ;
- 15 M+ de comptes mobile money au Cameroun → le gisement de conversion existe déjà ;
- 1–2 % de frais de change + commission 1 % sur la conversion UM → la machine à revenus.

### 0:12–0:30 — Architecture UM sur MoMo (18 min) ⭐ LE CŒUR TECHNIQUE
**Présentez le schéma imprimé (le laisser sur la table) :**

```
┌────────────────────────────────────────────────────────────────────┐
│                    MTN MoMo Cameroun (émetteur e-money BEAC)       │
│                                                                    │
│  💝 Diaspora (EUR/USD) ──change 1-2%──► UM wallet (valeur santé)   │
│        ▲                                         │                 │
│        │ plateforme VITAL KA (1%)                │ 0% entre proches│
│        │                                         ▼                 │
│  📱 App Solidarité  ────────────────► 👤 Patient (wallet UM)       │
│                                             │                      │
│                                             │ soins               │
│                                             ▼                      │
│  🏪 Pharmacie (QR) ── conversion standard ──► 💰 FCFA (compte)     │
│                                             │ commission 1% MoMo  │
│                                             ▼                      │
│                        📊 Réconciliation T+0/T+1 (API MoMo)        │
└────────────────────────────────────────────────────────────────────┘
```

**Les 6 points techniques à valider un par un :**

1. **Structure de compte** : l'UM = un **sous-compte à usage restreint** sur MoMo (type « earmarked balance »), pas une émission monétaire — MTN reste l'émetteur e-money agréé BEAC ;
2. **Non-convertibilité patient** : le patient ne peut convertir ses UM qu'en **soins** (acheter de la santé), jamais en cash — c'est ce qui garantit le caractère non spéculatif et l'acceptation réglementaire ;
3. **Conversion pharmacie** : la pharmacie seule convertit UM → FCFA, via le flux standard MoMo (frais normaux + commission 1 %) ;
4. **Conformité AML** : plafond 5 000 UM/mois, KYC hérité du compte MoMo existant (pas de nouveau KYC), traçabilité totale du don au médicament ;
5. **Intégration** : API MTN MoMo Developer (sandbox → production), webhooks de réconciliation, settlement T+0/T+1 ;
6. **Privacy by design** : aucun dossier médical ne transite par MoMo — les données santé restent chiffrées (AES-GCM) sur le téléphone du patient ; MoMo ne voit que des UM. *« On protège votre réputation avant la nôtre. »*

**Point de vigilance à déclarer vous-même (crédibilité) :**
> *« La qualification réglementaire exacte de l'UM (valeur à usage restreint) sera validée avec BEAC/COBAC pendant le pilote. C'est un des livrables — et c'est plus simple que vous ne le pensez : c'est le modèle des bons d'achat à usage limité, déjà connu. »*

### 0:30–0:45 — Le modèle économique (15 min)
**Tableau à présenter (et à laisser) :**

| Flux | MTN MoMo gagne | VITAL KA gagne |
|---|---|---|
| Achat UM (diaspora) | Frais de change **1–2 %** | Frais plateforme **1 %** |
| Paiement prestataire (UM) | Gratuit (fidélisation wallet) | Gratuit |
| Conversion UM → FCFA (pharmacie) | Frais standard MoMo + **commission 1 %** | Gratuit |
| Abonnement médecins | Canal de distribution 100 % VITAL KA | Revenu récurrent |

**Projection pilote Cameroun (année 1, à valider ensemble) :**
- 50 000 patients actifs · 500 médecins · 200 pharmacies ;
- ~2 M$ de volume UM échangé → **~40 000 $ de frais de change + ~20 000 $ de commission** pour MoMo, pour un investissement pilote de 150 K$ ;
- **Le vrai gain n'est pas là** : c'est la **conquête de 50 000 wallets santé** — et l'image « MTN = la santé des Camerounais » avant Orange.

**La phrase de cadrage :**
> *« Le pilote ne change pas votre P&L. Il change votre position de marché. On construit ça ensemble, et vous gardez 100 % de vos frais standards. »*

### 0:45–0:55 — Le MoU : les 6 clauses (10 min)
**Présentez le brouillon (2 pages) et lisez les 6 titres :**

| Clause | Contenu | Pourquoi (argument à dire) |
|---|---|---|
| **1. Exclusivité** | MTN Cameroun s'interdit de lancer/financer un produit concurrent (wallet santé/paiement santé) pendant le pilote + 12 mois | *« Vous protège contre Orange — et nous protège contre vous. C'est une clause de confiance mutuelle. »* |
| **2. Propriété intellectuelle** | Tout reste VITAL KA ; MTN reçoit une licence d'usage limitée au périmètre pilote ; pas de cession, pas de work-for-hire | *« Vous n'avez pas besoin de posséder la technologie pour gagner le marché. La preuve : vous ne possédez pas MoMo Advance non plus. »* |
| **3. Non-solicitation** | MTN ne recrute pas les pharmaciens/médecins/agents du réseau VITAL KA pendant 24 mois | *« Le réseau terrain est notre investissement. On ne vous demande pas le vôtre. »* |
| **4. Périmètre limité** | 1 pays, 6 mois, données agrégées uniquement ; pas de transfert de source ni de bundle | *« Le pilote est un laboratoire, pas une cession. Les données patients restent à l'hôpital du patient. »* |
| **5. Données & conformité** | AES-GCM, POPIA/NITDA, consentement explicite, anonymisation des agrégats ; validation BEAC/COBAC de l'UM en livrable pilote | *« La conformité est notre argument de vente, pas notre problème. »* |
| **6. Sortie** | Résiliation sans pénalité à chaque jalon ; période de non-concurrence 12 mois post-sortie ; arbitrage CCI Cameroun (OHADA) | *« On veut que ce soit facile de sortir. C'est comme ça qu'on sait qu'on restera. »* |

### 0:55–1:00 — Décision et prochaines étapes (5 min)
**La demande exacte :**
> *« Deux engagements aujourd'hui : un, vous validez le schéma d'architecture UM sur MoMo avec votre ingénieur API pour retour technique sous 10 jours. Deux, votre équipe juridique reçoit le brouillon de MoU pour finalisation sous 3 semaines. On lance le pilote à T0 + 45 jours. »*

**Ne partez jamais sans :** un nom (l'ingénieur référent API), une date (retour technique), une date (signature MoU).

---

## Les 5 messages clés de l'atelier MoMo

1. **« C'est votre volume, pas le nôtre »** — chaque UM circulante est une transaction MoMo ;
2. **« Le patient ne touche jamais de cash »** — non-convertibilité = conformité AML et acceptation BEAC ;
3. **« MoMo ne voit jamais de données santé »** — privacy by design, dossiers chiffrés sur le téléphone ;
4. **« 50 000 wallets santé contre Orange Money »** — le pilote est une arme de parts de marché ;
5. **« L'UM, c'est un bon d'achat à usage restreint, pas une monnaie »** — la qualification BEAC est un livrable, pas un obstacle.

---

## Objections spécifiques MoMo et réponses

| Objection | Réponse |
|---|---|
| **« Une monnaie UM, c'est illégal. »** | *« C'est exactement pourquoi on ne crée pas une monnaie. L'UM est un solde à usage restreint (comme un bon d'achat), émis et réglé par MTN MoMo, émetteur agréé BEAC. La qualification formelle est un livrable du pilote avec la COBAC. »* |
| **« Pourquoi pas directement via MTN Group Fintech ? »** | *« Parce que le Cameroun est le meilleur terrain de preuve : MoMo y est n°1, la CSU avance. On prouve ici en 6 mois, on remonte au groupe avec des résultats. Vous avez le projet pilote, le groupe aura le modèle. »* |
| **« La diaspora, c'est des corridors internationaux — c'est compliqué. »** | *« Pour le pilote, la diaspora passe par le corridor MoMo existant ou un partenaire de change agréé. On ne crée aucun corridor : on utilise les vôtres. »* |
| **« On a déjà MoMo Advance, des prêts, etc. »** | *« Exactement — le wallet santé est un usage, pas un concurrent de vos produits financiers. Il alimente MoMo Advanced, pas l'inverse. »* |
| **« Comment on sait que vous ne disparaissez pas ? »** | *« Le code source est en escrow dès le MoU, et l'application tourne déjà sans serveur central — votre risque d'exécution est nul : si on disparaît, le système continue chez vous. »* |
| **« Les frais de change sont régulés par la BEAC. »** | *« Justement : la commission 1 % sur la conversion UM → FCFA est un frais de service MoMo standard, déjà dans votre grille. Rien de nouveau pour la BEAC. »* |
| **« Votre 1 % de plateforme, c'est sur quoi ? »** | *« Sur l'émission UM (l'achat diaspora) uniquement — c'est la rémunération du logiciel, le change reste intégralement vôtre. »* |

---

## Checklist avant l'atelier

- [ ] Schéma d'architecture UM imprimé en A3 (×2)
- [ ] Brouillon MoU 6 clauses en 2 pages (×3 exemplaires)
- [ ] Noms vérifiés : Direction MoMo, responsable API MoMo Developer, responsable compliance
- [ ] Démo re-testée en mode avion le matin même
- [ ] Les 3 chiffres MoMo (60 %, 15 M+, 1–2 %) relus
- [ ] Scénario de repli si l'ingénieur API demande des détails : proposer un atelier technique séparé d'1 h sous 2 semaines (sandbox API MoMo)

## Après l'atelier (T+2 h max)

1. **Email de synthèse** : schéma joint, les 3 décisions demandées rappelées (retour technique 10 jours, MoU 3 semaines, pilote T0+45 j) ;
2. **Faire suivre le MoU aux juristes** avec les 6 clauses annotées (le « pourquoi » de chaque clause pour faciliter la négociation) ;
3. **Réserver la date du lancement pilote** et commencer la signature des 200 pharmacies — la course au réseau commence maintenant, pas après la signature.

---
*Préparé pour l'atelier Direction MoMo MTN Cameroun. Déroulé aligné sur le one-pager Cameroun et le deck HTML (slides 4, 5, 8). Les montants (1-2 %, 1 %, ~40 K$/20 K$) sont des hypothèses de négociation à valider avec la grille tarifaire réelle de MTN MoMo.*
