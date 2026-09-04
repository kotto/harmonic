# DOSSIER DE PARTENARIAT — KARE x ORABANK
## Émission d'Unités Médicales (UM) — Santé Digitale en Afrique

---

**Version** : 1.0 — Septembre 2026  
**Contact** : [À remplir]  
**Classification** : Confidentiel

---

## Résumé exécutif

KARE (ex-Vital KA) est une plateforme de santé digitale panafricaine qui permet aux patients, médecins, pharmaciens et laboratoires d'échanger des soins via une **Unité Médicale (UM)**, une monnaie de santé non spéculative adossée 1:1 à l'EUR et au CFA (1 UM = 1 EUR = 655 FCFA).

Orabank, en tant que partenaire bancaire agréé pour l'émission de monnaie électronique (licence BCEAO), apporte l'infrastructure de **collecte** (Mobile Money, cartes) et de **règlement** (conversion UM → CFA) qui permet à l'UM de circuler dans l'économie réelle.

Ce document détaille l'architecture, le modèle économique, les flux financiers, et les bénéfices pour Orabank.

---

## 1. Le problème

### 1.1 La santé en Afrique : une crise de circulation

- **60%** des paiements de santé en Afrique sont encore en espèces
- **< 5%** des transactions de santé sont digitalisées en zone UEMOA
- **Aucune** monnaie de santé dédiée ne circule à l'échelle panafricaine
- Les patients de la diaspora n'ont pas de moyen simple de payer les soins des proches à distance
- Les médecins et pharmaciens perdent du temps à gérer le cash, sans traçabilité

### 1.2 La solution UM

L'Unité Médicale (UM) est une monnaie privée adossée, non spéculative, conçue pour un seul usage : **la santé**.

| Propriété | Valeur |
|---|---|
| Taux fixe | 1 UM = 1 EUR = 655 FCFA |
| Convertibilité patient | **Non** — ne peut servir qu'à payer des soins |
| Convertibilité prestataire | **Oui** — avec plafond AML (5 000 UM/mois) |
| Émission | Uniquement via collecte fiat (Mobile Money, carte) |
| Traçabilité | Ledger append-only, signé, idempotent |
| Émission | Adossée 1:1 à la monnaie fiduciaire déposée chez Orabank |

---

## 2. L'architecture

### 2.1 Schéma des flux

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                        KARE (interface)                             │
 │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
 │  │ Patients │  │ Médecins │  │Pharmacies│  │   Diaspora       │   │
 │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬──────────┘   │
 │       │             │             │               │               │
 │       ▼             ▼             ▼               ▼               │
 │  ┌──────────────────────────────────────────────────────────────┐  │
 │  │               KARE Ledger (source de vérité)                  │  │
 │  │  • Comptes wallets (patients, prestataires)                   │  │
 │  │  • Transactions UM (crédit, débit, conversion)               │  │
 │  │  • Rapprochement 1:1 avec le compte fiduciaire               │  │
 │  │  • Plafonds AML, traçabilité, audit                          │  │
 │  └────────────────────────┬─────────────────────────────────────┘  │
 │                           │ UM → CFA / CFA → UM                    │
 └───────────────────────────┼─────────────────────────────────────────┘
                             │
                             ▼
 ┌─────────────────────────────────────────────────────────────────────┐
 │                     ORABANK (settlement)                            │
 │                                                                     │
 │  ┌──────────────────────────────────────────────────────────────┐  │
 │  │              COMPTE FIDUCIAIRE GLOBAL                         │  │
 │  │  « FIDUCIE_KARE »                                             │  │
 │  │  • Toutes les collectes fiat sont déposées ici                │  │
 │  │  • Tous les règlements CFA sont débités d'ici                 │  │
 │  │  • Solde = Σ(UM en circulation) × 655                        │  │
 │  └──────────────────────────────────────────────────────────────┘  │
 │              │                        │                            │
 │              ▼                        ▼                            │
 │  ┌──────────────────┐     ┌──────────────────────┐                │
 │  │  Collecte        │     │  Règlement           │                │
 │  │  • Mobile Money  │     │  • Virement CFA      │                │
 │  │  • Carte         │     │  • Vers comptes      │                │
 │  │  • Agrégation    │     │    prestataires      │                │
 │  │    MoMo / Wave   │     │  • J+1              │                │
 │  └──────────────────┘     └──────────────────────┘                │
 │                                                                     │
 └─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Rôle de chaque partie

| Composant | KARE | Orabank |
|---|---|---|
| Interface client (app, web) | ✅ Développe et maintient | — |
| Ledger UM (comptes, transactions) | ✅ Source de vérité | — |
| Wallet patients | ✅ Gère les soldes UM | — |
| Wallet prestataires | ✅ Gère les soldes UM | — |
| Conversion UM → CFA | ✅ Traite la demande | ✅ Exécute le règlement |
| Collecte Mobile Money | ✅ Initie | ✅ Agrège et acquitte |
| Collecte carte | ✅ Initie | ✅ Traite |
| Compte fiduciaire | — | ✅ Héberge et sécurise |
| Licence e-money | — | ✅ Met à disposition |
| Conformité BCEAO | — | ✅ Garantit |
| Rapprochement | ✅ Calcule les écarts | ✅ Fournit les relevés |
| Relation client | ✅ **Le client nous appartient** | — |
| Marketing et acquisition | ✅ | — |

### 2.3 Le client appartient à KARE

**Orabank ne voit jamais le client final.** Les seules informations qu'Orabank reçoit sont :

1. **Collecte** : « KARE a collecté X CFA par Mobile Money (opérateur Y) »
2. **Règlement** : « KARE demande un virement de X CFA vers le compte bancaire Z »

Orabank n'a pas accès :
- Aux identités des patients
- À l'historique médical
- Aux wallets UM
- Aux transactions entre patients et prestataires

---

## 3. Les flux financiers détaillés

### 3.1 Achat d'UM (diaspora → patient)

```
1. Diaspora ouvre l'app KARE
2. Sélectionne 100 UM (65 500 CFA)
3. Paie par Mobile Money
4. Orabank collecte 65 500 CFA sur le compte fiduciaire
5. KARE crédite 100 UM dans le wallet du patient
6. Le patient voit « +100 UM » dans son app
```

**Commission KARE** : 1.5% = 983 CFA  
**Frais Orabank** : Négociable (0.5%–1% du volume)

### 3.2 Paiement de soin (patient → médecin)

```
1. Patient consulte un médecin (30 UM)
2. KARE débite le patient, crédite le médecin
3. **0 appel Orabank** — transaction interne UM
4. Le médecin voit « +30 UM » dans son app
```

**Commission KARE** : 0% (les UM restent dans le circuit)  
**Frais Orabank** : 0% (aucun mouvement bancaire)

### 3.3 Conversion (prestataire → CFA)

```
1. Médecin demande la conversion de 30 UM → CFA
2. KARE gèle les 30 UM (sortis de la circulation)
3. KARE appelle Orabank → virement de 19 650 CFA
4. Orabank débite le compte fiduciaire
5. Orabank crédite le compte bancaire du médecin
6. Médecin reçoit 19 650 CFA sur son compte Orabank (ou autre banque)
```

**Commission KARE** : 0% (la conversion est un service au prestataire)  
**Frais Orabank** : 0 — le médecin est un nouveau client Orabank

---

## 4. Ce qu'Orabank gagne avec ce projet

### 4.1 Bénéfices financiers directs

| Source de revenu | Estimation Année 1 | Estimation Année 3 | Mécanisme |
|---|---|---|---|
| **Frais de collecte** | 15–30 M FCFA | 150–300 M FCFA | 0.5%–1% sur le volume collecté |
| **Float du compte fiduciaire** | 10–50 M FCFA | 100–500 M FCFA | Fonds disponibles avant règlement des prestataires |
| **Nouveaux comptes prestataires** | 500–1 000 | 5 000–10 000 | Chaque médecin/pharmacien doit avoir un compte bancaire pour le règlement |
| **Nouveaux clients particuliers** | 5 000–10 000 | 50 000–100 000 | Patients et diaspora qui ouvrent des comptes Orabank |
| **Volume annuel transactionnel** | 2–5 Mds FCFA | 20–50 Mds FCFA | Toutes les collectes + règlements passent par Orabank |

### 4.2 Bénéfices stratégiques

| Bénéfice | Impact |
|---|---|
| **Pionnier de la santé digitale** | Orabank est la première banque UEMOA à proposer une monnaie de santé dédiée |
| **Acquisition massive de clients** | Chaque patient, médecin, pharmacien devient un client Orabank (pour le règlement CFA) |
| **Fidélisation** | Le compte fiduciaire est chez Orabank — difficile à transférer |
| **Différenciation concurrentielle** | Aucune autre banque UEMOA n'a ce produit |
| **Données de transaction** | Visibilité sur le volume de santé en zone UEMOA |
| **CSR / ESG** | Impact social mesurable : accès aux soins, traçabilité, réduction du cash |
| **Expansion géographique** | Le modèle s'étend aux 13 pays Orabank |

### 4.3 Projection de croissance

```
Année 1 (pilote Côte d'Ivoire) :
  • 10 000 patients
  • 500 prestataires
  • 2 Mds FCFA de volume
  • Compte fiduciaire : 200 M FCFA de solde moyen

Année 2 (extension Sénégal, Mali) :
  • 50 000 patients
  • 2 000 prestataires
  • 10 Mds FCFA de volume
  • Compte fiduciaire : 1 Md FCFA de solde moyen

Année 3 (13 pays Orabank) :
  • 200 000 patients
  • 10 000 prestataires
  • 50 Mds FCFA de volume
  • Compte fiduciaire : 5 Mds FCFA de solde moyen
```

### 4.4 Positionnement concurrentiel

| Banque | Produit santé digital | Statut |
|---|---|---|
| **Orabank** | **KARE (UM)** | **En cours — premier sur le marché** |
| Ecobank | Ecobank Health (crédit santé) | Pas de monnaie dédiée |
| Orange Bank | Pas de verticale santé | — |
| Wave | Transfert d'argent uniquement | Pas de santé |
| MTN MoMo | Paiement marchand | Pas d'émission de monnaie |

---

## 5. Aspects techniques

### 5.1 Intégration API

Orabank expose (ou configure) les endpoints suivants :

| Endpoint | Rôle | Fréquence |
|---|---|---|
| `POST /v1/collections/momo` | Collecte Mobile Money | Temps réel |
| `POST /v1/collections/card` | Collecte carte bancaire | Temps réel |
| `POST /v1/settlements` | Règlement CFA vers un prestataire | Temps réel |
| `GET /v1/statements?date=` | Relevé journalier pour rapprochement | Quotidien |
| `GET /v1/accounts/balance` | Solde du compte fiduciaire | Temps réel |
| `POST /v1/webhook` | Callback de statut de paiement | Temps réel |

### 5.2 Sécurité

- Authentification OAuth2 (client_credentials)
- Signature HMAC-SHA256 de chaque requête
- Idempotence (clé unique, pas de double collecte/règlement)
- Chiffrement AES-GCM-256 au repos
- Journal d'audit complet

### 5.3 Prérequis techniques

- Environnement sandbox (bac à sable) pour les tests
- Comptes de test Mobile Money (Orange Money, MTN, Wave)
- Cartes de test Visa/Mastercard
- Un compte fiduciaire dédié « FIDUCIE_KARE »

---

## 6. Modèle de contrat proposé

### 6.1 Principes

1. **KARE** développe l'interface, possède le ledger, gère la relation client
2. **Orabank** fournit la licence e-money, le compte fiduciaire, l'agrégation des paiements
3. **Le client appartient à KARE** — Orabank ne sollicite pas les clients de KARE
4. **Exclusivité** sur le marché de la santé digitale en zone UEMOA (à négocier)

### 6.2 Part des revenus

| Flux | Proposition KARE |
|---|---|
| Frais de collecte Mobile Money (1.5%) | Orabank : 0.5% — KARE : 1.0% |
| Frais de collecte carte (2.5%) | Orabank : 0.5% — KARE : 2.0% |
| Float du compte fiduciaire | Orabank : 100% (c'est leur liquidité) |
| Comptes prestataires | Orabank : 100% (nouveaux clients) |
| Conversion UM → CFA | Gratuit pour le prestataire, sans frais |

### 6.3 Durée

Proposition : 3 ans renouvelables, avec clause de sortie à 12 mois.

---

## 7. Prochaines étapes

| Étape | Délai | Responsable |
|---|---|---|
| 1. Réunion de cadrage (ce document) | S1 | Orabank + KARE |
| 2. Obtention de l'accès sandbox | S2 | Orabank |
| 3. Intégration technique (OrabankClient) | S3 | KARE |
| 4. Tests de bout en bout (T1–T10) | S4 | KARE + Orabank |
| 5. Pilote Côte d'Ivoire (1 000 patients) | S5 | Orabank + KARE |
| 6. Déploiement production | S6 | Orabank + KARE |

---

## Annexes

- **A1** : Architecture technique détaillée (banking_gateway.py, settlement.py)
- **A2** : Plan de tests sandbox (T1–T10)
- **A3** : Modèle de données (ledger, conversions, collections)
- **A4** : Spécification API Orabank attendue
- **A5** : Analyse de conformité BCEAO / UEMOA