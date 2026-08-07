# Spécification Technique — KA PAY : Monnaie Communautaire Autonome

**Document** : SPEC-KAPAY-1.0  
**Date** : Juillet 2026  
**Auteur** : Alain Kotto — Projet Univers Harmonique  
**Statut** : Spécification de référence (v1.0)
**Dépendances** : SPEC-RTC-HV1.0 (Réseau Télécom Harmonique Communautaire), HTP v1 (Harmonic Transport Protocol), SPEC-IAH-ECOSYSTEM-1.0 (IA Harmonique)

---

## Résumé Exécutif

KA PAY est une **monnaie numérique communautaire autonome** fonctionnant exclusivement sur le Réseau Télécom Harmonique Communautaire (RTHC). Contrairement aux solutions de paiement mobile existantes (Orange Money, M-Pesa, MTN Mobile Money), KA PAY **ne dépend d'aucun opérateur télécom, d'aucune banque, d'aucune API externe**. La monnaie est émise, validée et régulée par la communauté elle-même, via l'infrastructure du RTHC.

**Coût par transaction : 0€** (pas de frais opérateur, pas de frais de réseau).  
**Latence intra-village : < 500 ms**.  
**Latence inter-villages : < 5 secondes**.  
**Fonctionne 100% hors ligne** (transactions signées localement, propagées dès que le mesh est disponible).  

**Aucun compte bancaire requis. Aucune SIM requise. Aucun KYC externe. Juste un téléphone et le réseau harmonique.**

> *« Pendant que le monde attend la bancarisation de l'Afrique, l'Afrique harmonique crée sa propre monnaie — sans demander la permission. »*

---

## Table des Matières

1. [Principes Fondateurs](#1-principes-fondateurs)
2. [Architecture Générale](#2-architecture-générale)
3. [Le Protocole HPP — Harmonic Payment Protocol](#3-le-protocole-hpp--harmonic-payment-protocol)
4. [Le Portefeuille Local](#4-le-portefeuille-local)
5. [Le Registre Comptable Villageois](#5-le-registre-comptable-villageois)
6. [Création Monétaire — Comment l'argent entre dans le système](#6-création-monétaire--comment-largent-entre-dans-le-système)
7. [Consensus et Validation](#7-consensus-et-validation)
8. [Gouvernance Monétaire](#8-gouvernance-monétaire)
9. [Sécurité et Résilience](#9-sécurité-et-résilience)
10. [Intégration avec l'Écosystème KA](#10-intégration-avec-lécosystème-ka)
11. [Spécifications Techniques Détaillées](#11-spécifications-techniques-détaillées)
12. [Plan de Déploiement](#12-plan-de-déploiement)
13. [Projections et Passage à l'Échelle](#13-projections-et-passage-à-léchelle)

---

## 1. Principes Fondateurs

### 1.1 Les 7 Commandements de KA PAY

| Principe | Description |
|----------|-------------|
| **Souveraineté** | La monnaie appartient à la communauté, pas à un opérateur, une banque ou un État |
| **Zéro frais** | Aucun prélèvement sur les transactions intra-réseau. Le réseau est un bien commun |
| **Autonomie** | Aucune dépendance à Orange, MTN, Wave, Visa, Mastercard, Swift, ou toute API externe |
| **Création par le travail** | La monnaie est créée par le travail utile à la communauté, pas par la dette |
| **Transparence** | Le registre comptable est public (anonymisé) et accessible à tous les membres |
| **Résilience** | Fonctionne même si Internet mondial est coupé. Fonctionne même si le pays est en crise |
| **Inclusion** | Pas de KYC, pas de compte bancaire, pas de justificatif de revenus. Un téléphone suffit |

### 1.2 Pourquoi pas les opérateurs existants ?

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   Mobile Money (Orange, MTN, M-Pesa, Wave) :                             │
│   ─────────────────────────────────────────                               │
│   ❌ Frais de 1-3% par transaction → l'argent quitte la communauté        │
│   ❌ Dépendance à une API propriétaire → si Orange coupe, tout s'arrête   │
│   ❌ KYC obligatoire → exclusion des plus pauvres (pas de pièce d'identité)│
│   ❌ SIM obligatoire → exclusion des zones sans couverture GSM            │
│   ❌ Données chez l'opérateur → zero vie privée, profilage commercial     │
│   ❌ Latence 5-30s → dépend du réseau GSM/USSD saturé                    │
│   ❌ Pas interopérable → Orange Money → MTN Money = complexe et coûteux  │
│                                                                          │
│   KA PAY :                                                               │
│   ────────                                                                │
│   ✅ 0% de frais intra-réseau                                             │
│   ✅ Protocole ouvert, exécuté sur le RTHC communautaire                  │
│   ✅ Pas de KYC — l'identité est la clé publique Ed25519                  │
│   ✅ Pas de SIM — le réseau HaLow n'appartient à aucun opérateur          │
│   ✅ Données dans le village — le registre est local                      │
│   ✅ Latence < 500ms intra-village, < 5s inter-villages                  │
│   ✅ Interopérable par conception — un seul protocole pour tout le réseau │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 1.3 KA PAY n'est pas une cryptomonnaie

| | Bitcoin/Ethereum | KA PAY |
|---|---|---|
| **Consensus** | Proof-of-Work (énergie) / Proof-of-Stake (capital) | Proof-of-Authority communautaire (confiance) |
| **Création monétaire** | Mining (compétition) / Staking (richesse) | Travail communautaire (contribution) |
| **Énergie** | 100-900 kWh par transaction (Bitcoin) | < 0.001 Wh (un ESP32 en veille) |
| **Décentralisation** | Globale, anonyme, sans gouvernance | Locale, identifiée, avec gouvernance |
| **Registre** | Blockchain publique mondiale | Registre local par village, réconcilié en P2P |
| **Latence** | 10-60 minutes (confirmations) | < 5 secondes (confirmation unique) |
| **Taille transaction** | 200-500 octets | 86 octets (HPP) |
| **Fraude** | 51% attack, double-spend via réorganisations | Double-dépense impossible (autorité unique par village) |
| **Philosophie** | « Don't trust, verify » (anonyme, global) | « Trust your village, verify the math » (communautaire, local) |

KA PAY est conçu pour des communautés de 200 à 5000 personnes qui **se connaissent**. La confiance est le fondement — la cryptographie est la garantie.

---

## 2. Architecture Générale

### 2.1 Topologie : Un Village, Un Registre, Une Monnaie

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│                    KA PAY — ARCHITECTURE PAR VILLAGE                       │
│                                                                          │
│   ┌───────────────────────────────────────────────────────────────────┐ │
│   │  UTILISATEURS (téléphones, boîtiers HN-1)                          │ │
│   │  ────────────────────────────────────────                           │ │
│   │  · Portefeuille local (IndexedDB + AES-256-GCM)                    │ │
│   │  · Clé privée Ed25519                                              │ │
│   │  · Peut signer des transactions hors ligne                         │ │
│   │  · Se connecte au mesh via WiFi → boîtier HN-1 → HaLow 900 MHz    │ │
│   └───────────────────────────┬───────────────────────────────────────┘ │
│                               │                                          │
│                               │ WiFi (2.4 GHz) → Boîtier HN-1            │
│                               │ Boîtier HN-1 → HaLow (900 MHz)           │
│                               ▼                                          │
│   ┌───────────────────────────────────────────────────────────────────┐ │
│   │  POINT D'ACCÈS VILLAGE (Raspberry Pi 4)                            │ │
│   │  ───────────────────────────────────────                            │ │
│   │  ┌─────────────────────────────────────────────────────────────┐  │ │
│   │  │  REGISTRE COMPTABLE (registry.db — SQLite)                    │  │ │
│   │  │  ─────────────────────────────────────                        │  │ │
│   │  │  · Table accounts : user_id, pubkey, balance, created_at      │  │ │
│   │  │  · Table transactions : id, from, to, amount, signature,     │  │ │
│   │  │      timestamp_harmonic, status, block_hash                   │  │ │
│   │  │  · Table creation_events : id, user_id, work_type, amount,   │  │ │
│   │  │      approved_by_gardien, approved_by_tresorier               │  │ │
│   │  │  · Table exchange_events : external_tx_id, amount_eur,       │  │ │
│   │  │      amount_kapay, user_id, direction (IN/OUT)                │  │ │
│   │  └─────────────────────────────────────────────────────────────┘  │ │
│   │                                                                   │ │
│   │  ┌─────────────────────────────────────────────────────────────┐  │ │
│   │  │  VALIDATEUR DE TRANSACTIONS (validator.py)                    │  │ │
│   │  │  · Vérifie signature Ed25519                                  │  │ │
│   │  │  · Vérifie solde suffisant                                    │  │ │
│   │  │  · Vérifie non-double-dépense (cache des tx récentes)         │  │ │
│   │  │  · Horodate avec l'horloge harmonique (φ-based)              │  │ │
│   │  │  · Signe la confirmation avec la clé de l'AP                  │  │ │
│   │  └─────────────────────────────────────────────────────────────┘  │ │
│   │                                                                   │ │
│   │  ┌─────────────────────────────────────────────────────────────┐  │ │
│   │  │  SYNCHRONISEUR INTER-VILLAGES (sync.py)                       │ │ │
│   │  │  · Toutes les 15 minutes, envoie le delta au village voisin  │ │ │
│   │  │  · Reçoit les deltas des villages voisins                     │ │ │
│   │  │  · Valide les transactions entrantes (signature AP source)    │ │ │
│   │  │  · Met à jour la table des soldes inter-villages              │ │ │
│   │  └─────────────────────────────────────────────────────────────┘  │ │
│   └───────────────────────────┬───────────────────────────────────────┘ │
│                               │                                          │
│                               │ Backhaul 5 GHz directionnel               │
│                               ▼                                          │
│   ┌───────────────────────────────────────────────────────────────────┐ │
│   │  PASSERELLE INTERNET (Mini-PC N100 — point d'entrée/sortie unique) │ │
│   │  ────────────────────────────────────────────────────────────────  │ │
│   │  · Compte Wise/PayPal UNIQUE pour toute la zone (8-20 villages)   │ │
│   │  · Géré par le Trésorier de zone + double signature Gardien        │ │
│   │  · Entrée : subventions ONG, dons diaspora → crédités en KA PAY   │ │
│   │  · Sortie : achat Starlink, pièces détachées → débités en euros   │ │
│   │  · Taux de change fixe : 1 KA PAY = 1 EUR (ancrage communautaire) │ │
│   │  · Dashboard Grafana public : réserves, volume, création monétaire │ │ │
│   └───────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Flux d'une Transaction Type

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   ALICE ENVOIE 50 KA PAY À BOB — MÊME VILLAGE                             │
│                                                                          │
│   ÉTAPE 1 — ALICE (téléphone)                                            │
│   ─────────────────────────                                               │
│   a. Alice ouvre KA Phone → onglet « 💰 Payer »                          │
│   b. Elle scanne le QR code de Bob (ou sélectionne dans ses contacts)    │
│   c. Elle saisit : 50 KA PAY, motif : « Achat de tissu »                 │
│   d. Elle valide avec son code PIN (6 chiffres)                          │
│   e. Le téléphone construit la trame HPP, la signe avec sa clé privée   │
│   f. Le téléphone envoie la trame signée au boîtier HN-1 (WiFi)         │
│                                                                          │
│   ÉTAPE 2 — BOÎTIER HN-1 → AP VILLAGE (HaLow 900 MHz)                    │
│   ──────────────────────────────────────────────────                       │
│   a. Le boîtier relaie la trame HPP signée vers l'AP du village         │
│   b. Latence de transmission : < 50 ms (HaLow, 2 Mbps, trame 86 o)     │
│                                                                          │
│   ÉTAPE 3 — AP VILLAGE (Validation)                                       │
│   ────────────────────────────────                                         │
│   a. L'AP vérifie la signature Ed25519 d'Alice                           │
│   b. L'AP vérifie le solde d'Alice : 120 KA PAY ≥ 50 → OK               │
│   c. L'AP vérifie l'absence de double-dépense (cache)                    │
│   d. L'AP horodate avec l'horloge harmonique                             │
│   e. L'AP signe la confirmation avec sa clé d'autorité                   │
│   f. L'AP met à jour le registre : Alice -50, Bob +50                   │
│   g. Latence totale (étapes 2+3) : < 500 ms                              │
│                                                                          │
│   ÉTAPE 4 — CONFIRMATION AUX UTILISATEURS                                 │
│   ───────────────────────────────────────                                   │
│   a. L'AP envoie la confirmation à Alice et Bob                          │
│   b. Le téléphone d'Alice met à jour son solde : 70 KA PAY               │
│   c. Le téléphone de Bob met à jour son solde : +50 KA PAY               │
│   d. Bob reçoit une notification : « Alice vous a envoyé 50 KA PAY »    │
│                                                                          │
│   TEMPS TOTAL : < 1 SECONDE                                               │
│   FRAIS : 0 KA PAY                                                        │
│   INTERMÉDIAIRES : AUCUN                                                  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Flux d'une Transaction Inter-Village

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   ALICE (Village A) ENVOIE 100 KA PAY À CHARLES (Village C)               │
│                                                                          │
│   ÉTAPE 1-3 : Identique au flux intra-village                            │
│   ─────────────────────────────────────────                               │
│   · Alice signe, l'AP du Village A valide                                │
│   · MAIS : Charles n'est pas dans le registre du Village A               │
│                                                                          │
│   ÉTAPE 4 : ROUTAGE INTER-VILLAGES                                        │
│   ───────────────────────────────────                                      │
│   a. L'AP-A identifie que Charles appartient au Village C                │
│      (via l'annuaire LDAP du réseau : user_id → village_id)              │
│   b. L'AP-A déduit 100 KA PAY du solde « pont inter-villages » de A     │
│   c. L'AP-A propage la transaction vers l'AP-C via le backhaul 5 GHz    │
│   d. L'AP-C reçoit la transaction, vérifie la signature de l'AP-A       │
│   e. L'AP-C crédite 100 KA PAY au solde de Charles                       │
│   f. L'AP-C crédite 100 KA PAY au solde « pont inter-villages » de C    │
│   g. L'AP-C envoie la confirmation à Charles                             │
│                                                                          │
│   RÉCONCILIATION PÉRIODIQUE (toutes les 15 minutes) :                     │
│   ───────────────────────────────────────────────                          │
│   · Chaque village calcule son solde net avec chaque voisin              │
│   · Village A doit 100 KA PAY à Village C                                │
│   · Si A et C ont des transactions croisées, seul le solde net est réglé│
│   · Le règlement se fait par ajustement des « soldes pont »              │
│   · Aucun transfert physique d'argent n'est nécessaire                   │
│                                                                          │
│   TEMPS TOTAL : < 5 SECONDES                                              │
│   FRAIS : 0 KA PAY                                                        │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Le Protocole HPP — Harmonic Payment Protocol

### 3.1 Format de Trame Binaire

Le HPP s'appuie sur le HTP (Harmonic Transport Protocol) défini dans la spécification RTHC. Il ajoute un sous-type applicatif dédié aux transactions de paiement.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   TRAME HPP v1 — 86 OCTETS                                               │
│                                                                          │
│   ┌──────────┬──────────┬──────────┬──────────┬──────────┬────────────┐ │
│   │  MAGIC   │ VERSION  │   TYPE   │  FLAGS   │ MONTANT  │   HORODA-  │ │
│   │  4 B     │   1 B    │   1 B    │   2 B    │   8 B    │   TAGE     │ │
│   │ 'KPAY'   │   0x01   │          │          │ (int64)  │   8 B      │ │
│   └──────────┴──────────┴──────────┴──────────┴──────────┴────────────┘ │
│                                                                          │
│   ┌──────────┬──────────┬──────────┬──────────┬────────────────────────┐ │
│   │   DE     │    À     │ MOTIF    │  SIG     │     SIGNATURE          │ │
│   │  4 B     │   4 B    │   LEN    │  TYPE    │     Ed25519            │ │
│   │(user_id) │(user_id) │   2 B    │   1 B    │     64 B               │ │
│   └──────────┴──────────┴──────────┴──────────┴────────────────────────┘ │
│                                                                          │
│   DÉTAIL DES CHAMPS :                                                    │
│   ────────────────────                                                    │
│                                                                          │
│   MAGIC (4 B)       : 'KPAY' (0x4B504159) — identifie une trame KA PAY  │
│                                                                          │
│   VERSION (1 B)     : 0x01 — version 1 du protocole                      │
│                                                                          │
│   TYPE (1 B)        :                                                     │
│       0x00 = TRANSFERT       — envoi d'argent entre utilisateurs         │
│       0x01 = PAIEMENT        — achat chez un commerçant                  │
│       0x02 = CREATION        — création monétaire (travail communautaire) │
│       0x03 = DESTRUCTION     — destruction monétaire (sortie du système) │
│       0x04 = COTISATION      — paiement de la cotisation réseau          │
│       0x05 = ABONNEMENT      — abonnement KA TV Premium                 │
│       0x06 = CONSULTATION    — paiement consultation KA CARE             │
│       0x07 = DON             — don à la caisse de solidarité             │
│       0x08 = RECONCILIATION  — ajustement inter-villages                 │
│                                                                          │
│   FLAGS (2 B)        : bitfield (Little Endian)                          │
│       bit 0  = OFFLINE        — transaction signée hors ligne            │
│       bit 1  = URGENT         — priorité sanitaire (KA CARE)             │
│       bit 2  = GRATUIT        — transaction sans frais (toujours le cas) │
│       bit 3  = CONFIRMATION   — l'expéditeur demande une confirmation    │
│       bit 4  = RECURRENT      — prélèvement automatique mensuel          │
│       bit 5  = ANONYME        — ne pas afficher le nom dans le registre  │
│       bit 6  = MICRO          — micro-paiement (< 1 KA PAY)              │
│       bit 7  = LEGACY         — compatible v0 (réservé)                  │
│       bits 8-15 = RESERVED    — usage futur                              │
│                                                                          │
│   MONTANT (8 B)      : int64, en centièmes de KA PAY                     │
│       Exemple : 50.00 KA PAY = 5000 (0x0000000000001388)                 │
│       Valeur max : 9.22 × 10^16 KA PAY (~92 trillions)                  │
│                                                                          │
│   HORODATAGE (8 B)   : int64, microsecondes depuis l'époque harmonique   │
│       Époque harmonique : 2026-01-01T00:00:00Z                           │
│       Format inspiré de l'horloge φ (timestamp × φ pour l'ordre total)   │
│                                                                          │
│   DE (4 B)           : uint32, identifiant utilisateur émetteur          │
│   À (4 B)            : uint32, identifiant utilisateur destinataire       │
│       0x00000000 = réserve de création monétaire                         │
│       0xFFFFFFFF = caisse de solidarité                                  │
│       0xFFFFFFFE = réserve de destruction monétaire                      │
│       0xFFFFFFFD = trésorerie coopérative                                │
│                                                                          │
│   MOTIF LEN (2 B)    : uint16, longueur du champ motif (0 à 255)         │
│   MOTIF (0-255 B)    : UTF-8, texte libre décrivant la transaction       │
│       Exemple : "Achat de 5 kg de manioc au marché"                      │
│                                                                          │
│   SIG TYPE (1 B)     : 0x00 = Ed25519 (seul type supporté en v1)        │
│                                                                          │
│   SIGNATURE (64 B)   : Signature Ed25519 de tous les champs précédents   │
│       sign(concat(magic, version, type, flags, montant, horodatage,      │
│                   de, à, motif_len, motif, sig_type))                    │
│                                                                          │
│   TAILLE TOTALE MINIMALE (motif vide) : 86 OCTETS                        │
│   TAILLE TOTALE MAXIMALE (motif 255 B) : 341 OCTETS                     │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Comparaison de Taille avec d'Autres Systèmes

| Système | Taille par transaction | Sur canal 2 Mbps |
|---------|----------------------|-------------------|
| **KA PAY (HPP)** | **86 octets** | 0.34 ms |
| Bitcoin (P2PKH) | ~220 octets | 0.88 ms |
| Ethereum (simple ETH) | ~110 octets | 0.44 ms |
| Carte bancaire (ISO 8583) | ~500-1000 octets | 2-4 ms |
| SMS USSD (Orange Money) | ~160 octets + overhead GSM | 500-2000 ms |

**Avec la compression HTP (déjà intégrée au RTHC), la trame HPP peut encore être réduite de 10-30× via le dictionnaire harmonique, descendant jusqu'à ~3 octets pour les transactions fréquentes (mêmes paires émetteur/destinataire).**

### 3.3 Exemple de Trame Hexadécimale

```
Transaction : Alice (user_id=42) envoie 50.00 KA PAY à Bob (user_id=1001)
Motif : "Achat tissu"

Hex: 4B504159 01 00 0000 8813000000000000 0000003B9A6A8000
     0000002A 000003E9 000C 4163686174207469737375 00
     [64 octets signature Ed25519]

Total : 86 + 12 (motif) = 98 octets
```

### 3.4 Intégration dans le HTP (Harmonic Transport Protocol)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   ENCAPSULATION HTP → HPP                                                 │
│                                                                          │
│   ┌──────┬──────┬──────┬──────────┬──────────────────────────────────┐  │
│   │Vers. │Type  │Flags │  App ID  │     PAYLOAD (trame HPP)          │  │
│   │ 4b   │ 4b   │ 8b   │  16b     │     86-341 octets               │  │
│   │ 0x1  │ 0x6  │      │ 0x0003   │                                  │  │
│   └──────┴──────┴──────┴──────────┴──────────────────────────────────┘  │
│                                                                          │
│   HTP Type = 0x6 → « HPP Payment »                                       │
│   HTP App ID = 0x0003 → « KA PAY »                                       │
│                                                                          │
│   OVERHEAD HTP : 4 octets supplémentaires                                │
│   TAILLE TOTALE SUR LE RÉSEAU : 90-345 octets                           │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Le Portefeuille Local

### 4.1 Architecture du Wallet

Le portefeuille KA PAY est une bibliothèque JavaScript intégrée à la PWA KA Phone. Il fonctionne entièrement dans le navigateur, sans backend.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   WALLET.JS — PORTEFEUILLE LOCAL (PWA)                                    │
│                                                                          │
│   ┌───────────────────────────────────────────────────────────────────┐ │
│   │  API PUBLIQUE                                                      │ │
│   │  ────────────                                                      │ │
│   │  wallet.init(pin)              → Initialise le wallet              │ │
│   │  wallet.unlock(pin)            → Déverrouille pour la session       │ │
│   │  wallet.getBalance()           → Solde actuel                      │ │
│   │  wallet.getTransactions(n)     → N dernières transactions          │ │
│   │  wallet.send(to, amount, memo)→ Crée et signe une transaction      │ │
│   │  wallet.receive(tx)            → Vérifie et enregistre une tx reçue │ │
│   │  wallet.export()               → Exporte le wallet (backup)         │ │
│   │  wallet.import(data)           → Importe un wallet (restauration)   │ │
│   │  wallet.getPublicKey()         → Clé publique Ed25519              │ │
│   │  wallet.getUserId()            → ID utilisateur réseau             │ │
│   │  wallet.getQRCode()            → QR code pour recevoir             │ │
│   └───────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│   ┌───────────────────────────────────────────────────────────────────┐ │
│   │  STOCKAGE INTERNE (IndexedDB)                                       │ │
│   │  ─────────────────────────────                                      │ │
│   │  · Clé privée Ed25519 — chiffrée AES-256-GCM avec le PIN            │ │
│   │  · Clé publique Ed25519 — en clair                                  │ │
│   │  · user_id — en clair                                               │ │
│   │  · transactions[] — chiffrées AES-256-GCM                           │ │
│   │  · soldes_cache[] — solde local + soldes des contacts fréquents    │ │
│   │  · contacts[] — noms locaux associés aux user_id                   │ │
│   └───────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│   ┌───────────────────────────────────────────────────────────────────┐ │
│   │  SÉCURITÉ                                                          │ │
│   │  ────────                                                          │ │
│   │  · PIN 6 chiffres → dérivé en clé AES-256 via PBKDF2 (100K iter)  │ │
│   │  · Verrouillage après 5 tentatives erronées (30 min)               │ │
│   │  · La clé privée n'est JAMAIS en clair dans la RAM                 │ │
│   │  · Les transactions signées sont mises en file d'attente si offline │ │
│   │  · La file d'attente est flushée dès que le mesh est disponible    │ │
│   └───────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Mode Offline

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   TRANSACTION HORS LIGNE                                                 │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  ALICE (hors ligne — son boîtier HN-1 est éteint)                │   │
│   │                                                                  │   │
│   │  1. Alice ouvre KA Phone → Wallet                                 │   │
│   │  2. Elle saisit : Bob, 50 KA PAY                                  │   │
│   │  3. Elle valide avec son PIN                                      │   │
│   │  4. Le wallet :                                                   │   │
│   │     a. Vérifie le solde local (cache)                              │   │
│   │     b. Construit la trame HPP                                     │   │
│   │     c. Signe avec la clé privée                                   │   │
│   │     d. Stocke dans la file d'attente (IndexedDB)                  │   │
│   │     e. Affiche : « Transaction en attente — sera envoyée          │   │
│   │        dès la reconnexion au réseau »                             │   │
│   │  5. Dès qu'Alice rallume son HN-1 ou entre dans la zone HaLow :   │   │
│   │     → Le wallet flushe automatiquement la file d'attente          │   │
│   │     → Chaque transaction est envoyée à l'AP du village            │   │
│   │     → L'AP valide et confirme                                     │   │
│   │     → Le wallet met à jour le solde local                         │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   PROTECTION ANTI-DOUBLE-DÉPENSE OFFLINE :                               │
│   ─────────────────────────────────────────                               │
│   · Le wallet maintient un numéro de séquence par transaction            │
│   · L'AP vérifie que les séquences sont strictement croissantes          │
│   · Si deux transactions ont le même numéro de séquence, seule la       │
│     première arrivée est acceptée — l'autre est rejetée                  │
│   · L'horodatage harmonique (φ-based) garantit l'ordre total             │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Le Registre Comptable Villageois

### 5.1 Schéma de la Base de Données

```sql
-- Exécuté sur le SQLite du Raspberry Pi de l'AP Village

-- Table des comptes utilisateurs
CREATE TABLE accounts (
    user_id       INTEGER PRIMARY KEY,       -- 32-bit user ID
    pubkey        BLOB NOT NULL UNIQUE,      -- Ed25519 public key (32 bytes)
    village_id    INTEGER NOT NULL,          -- ID du village d'appartenance
    balance       INTEGER NOT NULL DEFAULT 0,-- Solde en centièmes de KA PAY
    created_at    INTEGER NOT NULL,          -- Timestamp harmonique
    last_tx_at    INTEGER,                   -- Dernière transaction
    is_merchant   BOOLEAN DEFAULT 0,         -- Compte commerçant (peut recevoir des paiements)
    is_treasury   BOOLEAN DEFAULT 0,         -- Compte trésorerie (création monétaire)
    is_solidarity BOOLEAN DEFAULT 0,         -- Compte caisse de solidarité
    is_active     BOOLEAN DEFAULT 1          -- Compte actif ou gelé
);

-- Table des transactions
CREATE TABLE transactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tx_hash         BLOB NOT NULL UNIQUE,       -- SHA-256 de la trame HPP
    tx_type         INTEGER NOT NULL,           -- 0=transfert, 1=paiement, 2=création, etc.
    from_user       INTEGER NOT NULL,           -- user_id émetteur (0 = création)
    to_user         INTEGER NOT NULL,           -- user_id destinataire
    amount          INTEGER NOT NULL,           -- Montant en centièmes
    memo            TEXT,                        -- Motif (UTF-8)
    timestamp_harm  INTEGER NOT NULL,           -- Horodatage harmonique
    signature       BLOB NOT NULL,              -- Signature Ed25519 (64 bytes)
    village_id      INTEGER NOT NULL,           -- Village où la tx a été validée
    status          INTEGER NOT NULL DEFAULT 0, -- 0=pending, 1=confirmed, 2=rejected
    block_hash      BLOB,                       -- Hash du bloc de 15 minutes
    confirmed_at    INTEGER,                    -- Timestamp de confirmation
    confirmed_by    BLOB,                       -- Signature de l'AP validateur
    FOREIGN KEY (from_user) REFERENCES accounts(user_id),
    FOREIGN KEY (to_user) REFERENCES accounts(user_id)
);

-- Table des événements de création monétaire
CREATE TABLE creation_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    work_type       TEXT NOT NULL,              -- "maintenance", "formation", "sante", etc.
    work_detail     TEXT,                       -- Description du travail effectué
    amount          INTEGER NOT NULL,           -- Montant créé (centièmes)
    approved_by_gardien  INTEGER,               -- user_id du Gardien
    approved_by_tresorier INTEGER,             -- user_id du Trésorier
    tx_hash         BLOB,                       -- Hash de la transaction de création
    created_at      INTEGER NOT NULL,
    status          INTEGER DEFAULT 0,          -- 0=en_attente, 1=approuvé, 2=rejeté
    FOREIGN KEY (user_id) REFERENCES accounts(user_id)
);

-- Table des blocs de réconciliation (1 bloc = 15 minutes)
CREATE TABLE reconciliation_blocks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    block_hash      BLOB NOT NULL UNIQUE,       -- SHA-256 du bloc
    village_id      INTEGER NOT NULL,
    start_time      INTEGER NOT NULL,           -- Début de la période
    end_time        INTEGER NOT NULL,           -- Fin de la période
    tx_count        INTEGER NOT NULL,           -- Nombre de transactions dans le bloc
    total_volume    INTEGER NOT NULL,           -- Volume total en centièmes
    prev_block_hash BLOB,                       -- Hash du bloc précédent
    merkle_root     BLOB,                       -- Racine de Merkle des transactions
    created_at      INTEGER NOT NULL,
    signature       BLOB NOT NULL               -- Signature de l'AP
);

-- Index pour les recherches rapides
CREATE INDEX idx_tx_from ON transactions(from_user, timestamp_harm);
CREATE INDEX idx_tx_to ON transactions(to_user, timestamp_harm);
CREATE INDEX idx_tx_village ON transactions(village_id, timestamp_harm);
CREATE INDEX idx_tx_status ON transactions(status);
CREATE INDEX idx_tx_hash ON transactions(tx_hash);
CREATE INDEX idx_creation_status ON creation_events(status);
```

### 5.2 Format du Bloc de Réconciliation

Toutes les 15 minutes, l'AP du village compile les transactions confirmées en un « bloc de réconciliation ». Ce bloc est signé et propagé aux villages voisins.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   BLOC DE RÉCONCILIATION — VILLAGE A, PÉRIODE 14:00-14:15                │
│                                                                          │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  HEADER (128 octets)                                              │  │
│   │  ───────────────────                                               │  │
│   │  · magic         : 'KBLK' (4 B)                                   │  │
│   │  · version       : 0x01 (1 B)                                     │  │
│   │  · village_id    : uint32 (4 B)                                    │  │
│   │  · start_time    : int64 (8 B) — timestamp φ                       │  │
│   │  · end_time      : int64 (8 B)                                     │  │
│   │  · tx_count      : uint32 (4 B)                                    │  │
│   │  · total_volume  : int64 (8 B) — somme des montants du bloc        │  │
│   │  · prev_block    : SHA-256 (32 B)                                  │  │
│   │  · merkle_root   : SHA-256 (32 B)                                  │  │
│   │  · reserve       : 27 B (padding)                                  │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  BODY (variable)                                                  │  │
│   │  ───────────────                                                   │  │
│   │  · transaction_1 : trame HPP complète (86-341 B)                  │  │
│   │  · transaction_2 : trame HPP complète                              │  │
│   │  · ...                                                             │  │
│   │  · transaction_N : trame HPP complète                              │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  SIGNATURE (64 octets)                                             │  │
│   │  ───────────────────────                                            │  │
│   │  · Signature Ed25519 de l'AP du village sur (header + merkle_root)│  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│   TAILLE TOTALE (20 transactions, motif moyen 20 B) :                   │
│   = 128 + (20 × 106) + 64 = ~2 312 octets                               │
│                                                                          │
│   PROPAGATION :                                                          │
│   · Le bloc est envoyé à tous les villages voisins (backhaul 5 GHz)     │
│   · Chaque village voisin vérifie la signature de l'AP-A                │
│   · Chaque village voisin met à jour sa table des soldes inter-villages │
│   · Les transactions marquées inter-village sont exécutées              │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Création Monétaire — Comment l'argent entre dans le système

### 6.1 Principes de Création

KA PAY n'est pas miné, n'est pas acheté, n'est pas adossé à une dette. **La monnaie est créée par le travail utile à la communauté.** C'est le principe de la « monnaie-travail » ou « monnaie fondante communautaire ».

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   TYPES DE TRAVAIL GÉNÉRATEUR DE KA PAY                                   │
│                                                                          │
│   ┌──────────────────────────┬────────────────┬──────────────────────┐  │
│   │ TRAVAIL                  │ KA PAY CRÉÉS   │ FRÉQUENCE            │  │
│   ├──────────────────────────┼────────────────┼──────────────────────┤  │
│   │ Gardien du réseau        │ 20 KA PAY/mois │ Mensuelle            │  │
│   │ (surveillance, reboot)   │                │                      │  │
│   ├──────────────────────────┼────────────────┼──────────────────────┤  │
│   │ Animateur communautaire  │ 15 KA PAY/mois │ Mensuelle            │  │
│   │ (formation, support)     │                │                      │  │
│   ├──────────────────────────┼────────────────┼──────────────────────┤  │
│   │ Agent de santé communau- │ 25 KA PAY/mois │ Mensuelle            │  │
│   │ taire (dépistages KA CARE)│               │                      │  │
│   ├──────────────────────────┼────────────────┼──────────────────────┤  │
│   │ Maintenance solaire      │ 5 KA PAY/heure │ À la tâche           │  │
│   │ (nettoyage panneaux)     │                │                      │  │
│   ├──────────────────────────┼────────────────┼──────────────────────┤  │
│   │ Travaux collectifs       │ 3 KA PAY/heure │ À la tâche           │  │
│   │ (réfection route, citerne)│               │ /participant         │  │
│   ├──────────────────────────┼────────────────┼──────────────────────┤  │
│   │ Contenu éducatif         │ 2-10 KA PAY    │ À la pièce           │  │
│   │ (cours, tutos, radio)    │ par contenu    │                      │  │
│   ├──────────────────────────┼────────────────┼──────────────────────┤  │
│   │ Création contenu KA TV   │ 2-50 KA PAY    │ À la pièce           │  │
│   │ (vidéos, reportages)     │ par vidéo      │ (selon audience)     │  │
│   ├──────────────────────────┼────────────────┼──────────────────────┤  │
│   │ Dépistages KA CARE       │ 1 KA PAY       │ Par dépistage        │  │
│   │ (incitation santé)       │ par dépistage  │ effectué             │  │
│   └──────────────────────────┴────────────────┴──────────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Processus de Validation d'une Création Monétaire

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   CRÉATION MONÉTAIRE — DOUBLE SIGNATURE OBLIGATOIRE                       │
│                                                                          │
│   ÉTAPE 1 — L'UTILISATEUR EFFECTUE LE TRAVAIL                            │
│   ─────────────────────────────────────────                               │
│   · Exemple : Mariam nettoie les 3 panneaux solaires du village          │
│   · Durée : 2 heures → 2 × 5 = 10 KA PAY à créer                        │
│                                                                          │
│   ÉTAPE 2 — LE GARDIEN CONSTATE                                           │
│   ───────────────────────────────                                          │
│   · Le Gardien vérifie que le travail est fait                           │
│   · Il ouvre l'interface « Création monétaire » sur sa tablette          │
│   · Il sélectionne : Mariam, « maintenance solaire », 10 KA PAY          │
│   · Il signe avec sa clé privée (1ère signature)                         │
│                                                                          │
│   ÉTAPE 3 — LE TRÉSORIER VALIDE                                           │
│   ────────────────────────────                                             │
│   · Le Trésorier reçoit la demande de création                           │
│   · Il vérifie que le montant correspond au barème                       │
│   · Il vérifie que la création ne dépasse pas le plafond mensuel         │
│   · Il signe avec sa clé privée (2ème signature)                         │
│                                                                          │
│   ÉTAPE 4 — L'AP EXÉCUTE LA CRÉATION                                      │
│   ──────────────────────────────────                                       │
│   · L'AP vérifie les deux signatures                                     │
│   · L'AP crée la transaction de type CREATION (from=0x00000000)          │
│   · L'AP crédite le compte de Mariam de 10 KA PAY                        │
│   · L'AP enregistre l'événement dans creation_events                     │
│   · L'AP notifie Mariam : « +10 KA PAY — Maintenance solaire »          │
│                                                                          │
│   DOUBLE SIGNATURE = GARDIEN (technique) + TRÉSORIER (financier)         │
│   LES DEUX SONT NÉCESSAIRES. AUCUN NE PEUT CRÉER SEUL.                   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Plafond de Création Monétaire

Pour éviter l'inflation, la création monétaire est plafonnée :

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   RÈGLES DE CRÉATION MONÉTAIRE                                            │
│                                                                          │
│   1. PLAFOND MENSUEL PAR VILLAGE :                                       │
│      · Maximum 500 KA PAY créés par mois pour un village de 200 familles │
│      · Soit 2.5 KA PAY/famille/mois de création monétaire                │
│      · Révisable par l'Assemblée des utilisateurs (trimestrielle)        │
│                                                                          │
│   2. PLAFOND ANNUEL :                                                    │
│      · La masse monétaire totale ne peut croître de plus de 15% par an   │
│      · Si le plafond est atteint, la création est suspendue              │
│                                                                          │
│   3. DESTRUCTION MONÉTAIRE (sortie d'argent vers l'extérieur) :          │
│      · Quand la coopérative paie une facture en euros (Starlink),        │
│        les KA PAY correspondants sont DÉTRUITS, pas transférés           │
│      · Type de transaction : DESTRUCTION (0x03)                          │
│      · Cela compense la création et maintient l'équilibre                │
│                                                                          │
│   4. MASSE MONÉTAIRE CIBLE :                                             │
│      · ~2 500 KA PAY en circulation par village de 200 familles          │
│      · Soit ~12.5 KA PAY/famille de pouvoir d'achat local                │
│      · La monnaie est « fondante » si thésaurisée (optionnel,            │
│        configurable par village) : -2%/an sur les soldes inactifs        │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 6.4 Entrée de Fonds Externes (Diaspora, ONG, Subventions)

C'est le SEUL point de contact avec le système financier mondial :

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   FLUX ENTRANT : EURO → KA PAY                                             │
│   ───────────────────────────                                              │
│                                                                          │
│   1. La diaspora ou l'ONG envoie 1000 € sur le compte Wise/PayPal        │
│      de la coopérative (UN compte pour 8-20 villages)                    │
│                                                                          │
│   2. Le Trésorier constate le virement                                   │
│                                                                          │
│   3. Le Trésorier crée un événement d'échange :                          │
│      · external_tx_id : référence du virement Wise                       │
│      · amount_eur : 1000.00 €                                            │
│      · amount_kapay : 1000.00 KA PAY (taux 1:1)                          │
│                                                                          │
│   4. Le Trésorier + Gardien signent une création monétaire de 1000 KA PAY │
│      → La masse monétaire augmente de 1000 KA PAY                        │
│      → La réserve en euros augmente de 1000 €                            │
│                                                                          │
│   5. Le Trésorier ventile les 1000 KA PAY selon les instructions :       │
│      · 700 KA PAY → 14 familles destinataires (50 KA PAY/famille)        │
│      · 300 KA PAY → caisse de solidarité du village                      │
│                                                                          │
│   FLUX SORTANT : KA PAY → EURO                                            │
│   ───────────────────────────                                              │
│                                                                          │
│   1. La coopérative doit payer la facture Starlink : 50 €/mois           │
│                                                                          │
│   2. Le Trésorier initie une destruction monétaire de 50 KA PAY          │
│      → La masse monétaire diminue de 50 KA PAY                           │
│      → Le paiement de 50 € est effectué depuis le compte Wise            │
│                                                                          │
│   3. Double signature Trésorier + Gardien obligatoire                    │
│                                                                          │
│   RÈGLE D'OR :                                                            │
│   KA PAY EN CIRCULATION ≤ RÉSERVE EN EUROS + TRAVAIL CRÉÉ                │
│   (La monnaie est intégralement adossée : 1 KA PAY = 1 € de réserve      │
│    OU 1 € de travail communautaire validé)                                │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Consensus et Validation

### 7.1 Modèle de Consensus : Proof-of-Authority Communautaire (PoAC)

Contrairement aux blockchains globales, KA PAY n'a pas besoin d'un consensus distribué coûteux. Le village est une communauté de confiance.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   PROOF-OF-AUTHORITY COMMUNAUTAIRE (PoAC)                                 │
│                                                                          │
│   PRINCIPE :                                                              │
│   ─────────                                                               │
│   · Chaque village a UNE autorité de validation : le nœud AP             │
│   · Cette autorité est DÉSIGNÉE par l'Assemblée du village               │
│   · Elle est CONTRÔLÉE par le registre public (tout le monde peut lire)  │
│   · Elle est RÉVOCABLE par l'Assemblée à tout moment                      │
│   · Elle est DOUBLÉE par une redondance (2ème AP optionnel)              │
│                                                                          │
│   POURQUOI ÇA MARCHE :                                                    │
│   ─────────────────────                                                   │
│   · Dans un village de 200-2000 personnes, tout le monde se connaît      │
│   · Si l'AP triche, tout le village le voit immédiatement                │
│   · Le registre est public — n'importe quel utilisateur peut auditer     │
│   · La fraude est socialement impossible (honte + exclusion)              │
│   · La double signature Gardien + Trésorier empêche la collusion         │
│                                                                          │
│   VALIDATION TECHNIQUE :                                                  │
│   ───────────────────────                                                  │
│   Pour chaque transaction, l'AP vérifie :                                │
│   1. Signature Ed25519 valide (preuve que l'émetteur a autorisé)         │
│   2. Solde suffisant (pas de découvert)                                   │
│   3. Numéro de séquence valide (pas de double-dépense)                   │
│   4. Horodatage cohérent (pas dans le futur, pas trop dans le passé)    │
│   5. Pour les créations monétaires : double signature Gardien+Trésorier  │
│                                                                          │
│   Si TOUT est valide → transaction confirmée en < 500 ms                  │
│   Si NON → transaction rejetée avec code d'erreur                        │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Résolution des Conflits Inter-Villages

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   RÉCONCILIATION INTER-VILLAGES                                           │
│                                                                          │
│   PROBLÈME :                                                              │
│   · Le Village A envoie un bloc où Alice (Village A) paie Charles        │
│     (Village C) 100 KA PAY                                                │
│   · Mais le Village C ne reçoit pas le bloc (panne backhaul)             │
│   · Alice a été débitée, Charles n'a pas été crédité                     │
│                                                                          │
│   SOLUTION : PROTOCOLE DE RÉCONCILIATION EN 3 ÉTAPES                      │
│   ─────────────────────────────────────────────                            │
│                                                                          │
│   1. DÉTECTION (automatique) :                                            │
│      · Toutes les 15 minutes, chaque village envoie son bloc au voisin  │
│      · Le village voisin accuse réception (ACK signé)                    │
│      · Si pas d'ACK après 3 tentatives → le bloc est marqué « pending »  │
│                                                                          │
│   2. RATTRAPAGE (automatique) :                                           │
│      · Le Village C, une fois reconnecté, demande les blocs manquants    │
│      · Le Village A renvoie les blocs pending                            │
│      · Le Village C vérifie et applique les transactions                 │
│                                                                          │
│   3. ARBITRAGE (humain, si conflit) :                                     │
│      · Si un désaccord persiste (ex : A dit avoir envoyé, C dit n'avoir │
│        rien reçu), les Trésoriers des 2 villages examinent les logs      │
│      · Si pas de consensus, l'Admin technique régional tranche           │
│      · Recours ultime : l'Assemblée des utilisateurs                     │
│                                                                          │
│   GARANTIE :                                                              │
│   · Aucune transaction n'est PERDUE (le bloc est stocké des 2 côtés)     │
│   · Aucune transaction n'est DUPLIQUÉE (hash unique)                     │
│   · Le délai MAX de résolution est de 24h (pire cas)                     │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Gouvernance Monétaire

### 8.1 Rôles et Responsabilités

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  ASSEMBLÉE DES UTILISATEURS (tous les membres du village)         │  │
│   │  ─────────────────────────────────────────────────────────────    │  │
│   │  · Se réunit tous les 3 mois                                     │  │
│   │  · Décide du plafond de création monétaire                        │  │
│   │  · Décide des barèmes de travail (combien de KA PAY par tâche)    │  │
│   │  · Décide du taux de « fonte » (optionnel, -2%/an par défaut)     │  │
│   │  · Peut révoquer le Gardien ou le Trésorier                       │  │
│   │  · Peut geler un compte (consensus 2/3)                            │  │
│   └──────────────────────────┬───────────────────────────────────────┘  │
│                              │                                          │
│              ┌───────────────┼───────────────┐                          │
│              │               │               │                          │
│   ┌──────────┴──────┐ ┌──────┴──────┐ ┌──────┴──────────┐              │
│   │  GARDIEN        │ │  TRÉSORIER  │ │  ADMIN TECH     │              │
│   │  (technique)    │ │ (financier) │ │  (inter-village)│              │
│   │                 │ │             │ │                 │              │
│   │ · Signe les     │ │ · Gère le   │ │ · Maintient le  │              │
│   │   créations     │ │   compte    │ │   backhaul 5 GHz│              │
│   │   monétaires    │ │   Wise      │ │ · Résout les    │              │
│   │ · Surveille     │ │ · Signe les │ │   conflits      │              │
│   │   l'intégrité   │ │   créations │ │   inter-villages│              │
│   │   du registre   │ │   monétaires│ │ · Forme les     │              │
│   │ · Redémarre     │ │ · Publie le │ │   nouveaux      │              │
│   │   l'AP si       │ │   rapport   │ │   Gardiens      │              │
│   │   nécessaire    │ │   mensuel   │ │                 │              │
│   └─────────────────┘ └────────────┘ └─────────────────┘              │
│                                                                          │
│   SÉPARATION DES POUVOIRS :                                              │
│   · Le Gardien constate le travail (technique)                           │
│   · Le Trésorier valide la création (financier)                          │
│   · L'Admin technique arbitre les conflits (indépendant)                 │
│   · L'Assemblée contrôle tout le monde (démocratique)                    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Transparence et Audit

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   REGISTRE PUBLIC (accessible à tous les utilisateurs du village)         │
│                                                                          │
│   http://harmonic.local:8700/registry                                     │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  DASHBOARD PUBLIC DU VILLAGE                                      │   │
│   │  ─────────────────────────────                                    │   │
│   │                                                                   │   │
│   │  📊 MASSE MONÉTAIRE : 2 847 KA PAY                                │   │
│   │     └─ Créée par travail : 1 200 KA PAY                           │   │
│   │     └─ Entrée externe (ONG/diaspora) : 1 800 KA PAY               │   │
│   │     └─ Détruite (sorties) : -153 KA PAY                           │   │
│   │                                                                   │   │
│   │  💰 RÉSERVE EN EUROS : 1 800 € (compte Wise)                      │   │
│   │                                                                   │   │
│   │  📈 TRANSACTIONS DU MOIS : 342                                     │   │
│   │     └─ Volume : 1 847 KA PAY                                      │   │
│   │     └─ Moyenne par tx : 5.4 KA PAY                                │   │
│   │                                                                   │   │
│   │  🔍 DERNIÈRES TRANSACTIONS :                                       │   │
│   │     ┌────────┬──────────┬────────┬────────┬──────────────────┐   │   │
│   │     │   De   │    À     │ Montant│ Motif  │ Horodatage       │   │   │
│   │     ├────────┼──────────┼────────┼────────┼──────────────────┤   │   │
│   │     │ #42    │ #1001    │ 50.00  │ Tissu  │ 14:32:15.423     │   │   │
│   │     │ #108   │ #55      │ 3.50   │ Légumes│ 14:31:02.118     │   │   │
│   │     │ #0     │ #42      │ 10.00  │ CRÉAT° │ 14:30:00.000     │   │   │
│   │     └────────┴──────────┴────────┴────────┴──────────────────┘   │   │
│   │                                                                   │   │
│   │  ⚠ AUDIT AUTOMATIQUE :                                             │   │
│   │     · Somme(soldes) = Masse monétaire ✅                           │   │
│   │     · Créations = Travail + Entrées ✅                             │   │
│   │     · Aucune double-dépense détectée ✅                            │   │
│   │     · Dernier audit : il y a 2 minutes                             │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   Les noms réels sont REMPLACÉS par les user_id.                         │
│   Seuls l'émetteur et le destinataire voient leurs propres noms.         │
│   Le Trésorier voit tout (pour l'audit).                                  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Sécurité et Résilience

### 9.1 Matrice des Menaces

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   MENACE                    PROB.   IMPACT   DÉFENSE                     │
│   ──────                    ─────   ──────   ───────                     │
│                                                                          │
│   Vol de téléphone          Élevée  Moyen    · PIN 6 chiffres            │
│   (accès au wallet)                          · Verrouillage 5 essais     │
│                                              · Backup papier (12 mots)   │
│                                              · Le solde est reconstruc-  │
│                                                tible depuis le registre  │
│                                                                          │
│   Double-dépense            Faible  Critique · Numéro de séquence unique │
│   (utilisateur malveillant)                  · Horodatage harmonique φ   │
│                                              · Cache des tx récentes     │
│                                              · Détection automatique     │
│                                                                          │
│   Collusion Gardien+Trésorier Très   Critique · Registre public          │
│   (création monétaire     faible           · Audit par l'Assemblée       │
│    frauduleuse)                              · Admin technique extérieur │
│                                              · Alerte si écart > seuil   │
│                                                                          │
│   Panne AP village          Moyen   Élevé    · AP secondaire (option)    │
│   (plus de validation)                       · Mode offline (files       │
│                                                d'attente utilisateurs)   │
│                                              · Redémarrage automatique   │
│                                                                          │
│   Corruption base SQLite    Faible  Critique · Sauvegarde automatique    │
│   (fichier registry.db)                      toutes les heures sur clé   │
│                                              USB + backup cloud (Starlink)│
│                                              · Checksum SHA-256 par bloc │
│                                                                          │
│   Attaque Sybil             Très    Élevé    · Chaque compte est créé    │
│   (faux utilisateurs)       faible           par le Gardien (pas auto)   │
│                                              · Vérification physique     │
│                                              · Limite de comptes par     │
│                                                boîtier HN-1 (1 compte)   │
│                                                                          │
│   Coupure du backhaul       Moyen   Faible   · Mode dégradé : les        │
│   (isolement du village)                     transactions intra-village  │
│                                              continuent normalement      │
│                                              · Rattrapage automatique    │
│                                              à la reconnexion            │
│                                                                          │
│   Vol physique de l'AP      Faible  Élevé    · L'AP est dans un boîtier  │
│                                              verrouillé, sur un toit     │
│                                              · Chiffrement complet du    │
│                                              disque (LUKS)               │
│                                              · La clé privée de l'AP     │
│                                              est dans un TPM/HSM         │
│                                                                          │
│   Inflation non contrôlée   Moyen   Critique · Plafond de création       │
│   (création monétaire                        · Ancrage 1:1 avec l'euro   │
│    excessive)                                · Destruction automatique   │
│                                              à la sortie                 │
│                                              · Audit trimestriel public  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Plan de Reprise Après Sinistre

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   SCÉNARIO CATASTROPHE : L'AP DU VILLAGE BRÛLE                            │
│   ─────────────────────────────────────────                                │
│                                                                          │
│   1. Le Gardien constate la panne                                        │
│                                                                          │
│   2. Il installe un nouveau Raspberry Pi avec l'image SD de secours      │
│      (stockée chez le Gardien + chez l'Admin technique)                  │
│                                                                          │
│   3. Il restaure la base de données depuis la dernière sauvegarde :      │
│      · Sauvegarde horaire sur clé USB (branchée sur l'AP)               │
│      · Sauvegarde quotidienne sur le cloud (Starlink)                    │
│      · Sauvegarde hebdomadaire chez l'Admin technique                    │
│                                                                          │
│   4. Il contacte les villages voisins pour récupérer les blocs           │
│      de réconciliation post-sauvegarde (max 1 heure de données perdues)  │
│                                                                          │
│   5. Les utilisateurs resynchronisent leurs wallets :                    │
│      · Le wallet interroge l'AP : « Quel est mon solde ? »              │
│      · Le wallet met à jour le solde local                               │
│      · Les transactions en file d'attente sont renvoyées                │
│                                                                          │
│   TEMPS DE RÉTABLISSEMENT : < 4 heures                                    │
│   PERTE MAXIMALE DE DONNÉES : < 1 heure de transactions                  │
│   PERTE FINANCIÈRE : 0 KA PAY (les soldes sont reconstituables)          │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 9.3 Chiffrement des Communications

Toutes les transactions KA PAY transitent sur des canaux déjà sécurisés par le RTHC :

| Couche | Protocole | Ce qu'il protège |
|--------|-----------|-----------------|
| **Radio** | WPA3-SAE (HaLow), WPA2-AES (5 GHz) | La trame HPP ne peut pas être interceptée sur le lien radio |
| **Réseau** | WireGuard VPN (backhaul inter-villages) | Les blocs de réconciliation sont chiffrés de bout en bout |
| **Application** | Signature Ed25519 (chaque transaction) | Même si le réseau est compromis, une transaction ne peut pas être forgée |
| **Stockage** | AES-256-GCM (wallet local + registry.db) | Les données au repos sont chiffrées |

---

## 10. Intégration avec l'Écosystème KA

### 10.1 KA PAY × KA PHONE

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   INTÉGRATION DANS L'APPLICATION KA PHONE (PWA)                           │
│                                                                          │
│   ÉCRAN D'ACCUEIL KA PHONE :                                              │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  🔵 KA PHONE                                    📶 ▮▮▮ 🔋 85%   │  │
│   │                                                                   │  │
│   │  ┌─────────────────────────────────────────────────────────────┐ │  │
│   │  │                                                             │ │  │
│   │  │              SOLDE : 127.50 KA PAY                           │ │  │
│   │  │                                                             │ │  │
│   │  └─────────────────────────────────────────────────────────────┘ │  │
│   │                                                                   │  │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │  │
│   │  │ 📞       │ │ 💬       │ │ 💰       │ │ 🫀               │   │  │
│   │  │ Appeler  │ │ Messages │ │  Payer   │ │ KA CARE          │   │  │
│   │  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │  │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │  │
│   │  │ 📺       │ │ 📻       │ │ 🧠       │ │ ⚙️               │   │  │
│   │  │ KA TV   │ │  Radio   │ │ IA Harm. │ │ Paramètres       │   │  │
│   │  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │  │
│   │                                                                   │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│   ÉCRAN « 💰 PAYER » :                                                    │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  ← Retour                                                         │  │
│   │                                                                   │  │
│   │  ENVOYER DE L'ARGENT                                              │  │
│   │  ┌─────────────────────────────────────────────────────────────┐ │  │
│   │  │ 📷 Scanner le QR code                                        │ │  │
│   │  │ ── ou ──                                                     │ │  │
│   │  │ 👤 Choisir un contact                                         │ │  │
│   │  └─────────────────────────────────────────────────────────────┘ │  │
│   │                                                                   │  │
│   │  MONTANT : [____] KA PAY                                          │  │
│   │                                                                   │  │
│   │  MOTIF : [________________________]                               │  │
│   │                                                                   │  │
│   │  ┌─────────────────────────────────────────────────────────────┐ │  │
│   │  │                     [ ENVOYER ]                              │ │  │
│   │  └─────────────────────────────────────────────────────────────┘ │  │
│   │                                                                   │  │
│   │  ─── DERNIÈRES TRANSACTIONS ───                                   │  │
│   │  14:32  → Bob       -50.00  Achat tissu                          │  │
│   │  12:15  → Coop      -0.15   Cotisation réseau                    │  │
│   │  09:00  ← Travail   +10.00  Maintenance solaire                  │  │
│   │  Hier   ← Alice     +5.00   Remboursement repas                  │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 10.2 KA PAY × KA CARE (Santé)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   SCÉNARIO 1 : CONSULTATION MÉDICALE PAYABLE EN KA PAY                     │
│                                                                          │
│   1. L'agent de santé utilise KA CARE pour dépister un enfant            │
│   2. KA CARE détecte une pneumonie → recommande un référencement         │
│   3. L'agent dit à la mère : « La consultation au centre de santé        │
│      coûte 50 KA PAY »                                                   │
│   4. La mère ouvre KA Phone → Wallet → scanne le QR code du centre       │
│   5. Elle envoie 50 KA PAY avec le motif : « Consultation pédiatrique »  │
│   6. Le centre reçoit instantanément le paiement                         │
│   7. Le registre de santé KA CARE se met à jour automatiquement          │
│   8. Si la mère n'a pas assez de KA PAY :                                │
│      → La caisse de solidarité couvre (automatique si solde < 20)       │
│      → Ou le centre accepte un paiement différé (crédit communautaire)   │
│                                                                          │
│   SCÉNARIO 2 : MICRO-ASSURANCE SANTÉ                                      │
│                                                                          │
│   1. Les familles paient 2 KA PAY/mois dans la caisse de solidarité      │
│   2. En cas de maladie grave, la caisse couvre jusqu'à 200 KA PAY        │
│   3. Décision par le Trésorier + Agent de santé (double signature)       │
│   4. Tout est tracé dans le registre public                              │
│                                                                          │
│   SCÉNARIO 3 : INCITATION AU DÉPISTAGE                                    │
│                                                                          │
│   1. Chaque dépistage KA CARE effectué = +1 KA PAY pour l'agent         │
│   2. Chaque enfant dépisté = +0.5 KA PAY pour la famille                │
│   3. Financement par subvention ONG → entrée externe → création          │
│   4. Résultat : plus de dépistages, plus de vies sauvées                 │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 10.3 KA PAY × KA TV (Télévision)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   SCÉNARIO : ABONNEMENT KA TV PREMIUM EN 1 CLIC                           │
│                                                                          │
│   1. L'utilisateur regarde KA TV gratuit (qualité 480p, pubs)            │
│   2. Un match de football important arrive → popup :                      │
│      « CAN 2027 — Sénégal vs Nigeria — LIVE 1080p — 2 KA PAY »          │
│   3. L'utilisateur clique « Regarder »                                   │
│   4. KA TV appelle wallet.pay(2, 'CAN 2027 — Sénégal vs Nigeria')       │
│   5. Le wallet signe la transaction, l'envoie à l'AP                    │
│   6. L'AP confirme en < 500 ms                                           │
│   7. Le flux 1080p se déverrouille instantanément                        │
│                                                                          │
│   SCÉNARIO : ABONNEMENT MENSUEL                                           │
│                                                                          │
│   1. L'utilisateur s'abonne à KA TV Premium : 15 KA PAY/mois             │
│   2. Le flag RECURRENT est activé dans la transaction HPP                │
│   3. Chaque mois, le wallet crée automatiquement une transaction         │
│   4. L'utilisateur reçoit une notification : « Prélèvement KA TV OK »   │
│   5. L'utilisateur peut annuler à tout moment                             │
│                                                                          │
│   SCÉNARIO : RÉMUNÉRATION DES CRÉATEURS DE CONTENU                        │
│                                                                          │
│   1. Amar, créateur local, upload une vidéo sur KA TV                    │
│   2. La vidéo est vue 500 fois (0.01 KA PAY par vue)                     │
│   3. KA TV crée automatiquement une transaction :                        │
│      → from : compte contenu KA TV                                       │
│      → to : Amar (user_id #555)                                          │
│      → amount : 5.00 KA PAY (500 vues × 0.01)                           │
│      → motif : « Revenus vidéo — Les techniques de pêche »              │
│   4. Amar est payé pour son contenu, sans intermédiaire, sans délai      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 10.4 KA PAY × RTHC (Télécoms)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   SCÉNARIO : COTISATION RÉSEAU AUTOMATIQUE                                 │
│                                                                          │
│   1. Chaque famille doit 0.15 KA PAY/mois pour le réseau                 │
│   2. Le 1er de chaque mois, le Trésorier déclenche la collecte            │
│   3. Pour chaque famille, une transaction de type COTISATION est créée   │
│   4. Les familles reçoivent une notification                              │
│   5. Si une famille n'a pas assez, la caisse de solidarité couvre        │
│   6. Le total collecté est détruit (type DESTRUCTION) et les euros       │
│      correspondants sont utilisés pour payer Starlink                    │
│                                                                          │
│   SCÉNARIO : RECHARGE DATA                                                │
│                                                                          │
│   1. L'utilisateur veut 500 Mo de data Internet supplémentaire           │
│   2. Tarif : 1 KA PAY = 100 Mo                                            │
│   3. L'utilisateur paie 5 KA PAY via wallet                               │
│   4. Le quota data est augmenté automatiquement                           │
│   5. Les KA PAY sont détruits (compensation)                              │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 10.5 KA PAY × IA HARMONIQUE (Finance Intelligente)

> **Spécification détaillée** : voir `SPEC_IA_HARMONIQUE_ECOSYSTEM.md`, Section 3 — IA × KA PAY.

L'IA Harmonique est intégrée au registre KA PAY pour quatre fonctions critiques :

| Fonction IA | Déclencheur | Action |
|------------|-------------|--------|
| **Détection de fraude** | Chaque transaction entrante | Analyse du pattern de dépense, graphe social, vélocité, horodatage → score de suspicion (0-100%) |
| **Scoring de crédit communautaire** | Sur demande (demande de micro-crédit) | Analyse de l'ancienneté, régularité, solde, graphe social, cotisations → score 0-100 |
| **Audit automatique quotidien** | Tous les jours à 03:00 UTC | Vérifie Σ(soldes) = masse_monétaire, cohérence des blocs, signatures, plafonds de création |
| **Prédiction de trésorerie** | Hebdomadaire | Projette les entrées/sorties à 3 mois, alerte si réserve < seuil |

Toutes ces fonctions s'exécutent **sur l'AP du village** (CPU local), pour **0 €/mois**, en **< 50 ms** par analyse.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   EXEMPLE : L'IA DÉTECTE UNE TRANSACTION SUSPECTE                          │
│                                                                          │
│   Transaction : user_id=42 → user_id=999, montant=200 KA PAY             │
│                                                                          │
│   ANALYSE IA (< 10 ms) :                                                  │
│   ──────────────────────                                                  │
│   ✅ Signature Ed25519 valide                                             │
│   ✅ Solde suffisant (250 > 200)                                          │
│   ⚠️  Pattern de dépense : user_id=42 dépense habituellement 2-15 KA PAY │
│       → 200 KA PAY = 13× l'écart-type → ANOMALIE                         │
│   ⚠️  Graphe social : 1ère transaction entre #42 et #999                 │
│   ⚠️  Vélocité : #42 a fait 3 transactions en 5 minutes                  │
│   → SCORE DE FRAUDE : 72% (ÉLEVÉ)                                        │
│                                                                          │
│   ACTION AUTOMATIQUE :                                                    │
│   · Transaction BLOQUÉE temporairement                                    │
│   · Notification au Gardien : « Transaction suspecte #42 → #999 »        │
│   · Le Gardien contacte l'utilisateur #42 pour vérifier                  │
│   · Si légitime → Gardien débloque la transaction                        │
│   · Si fraude → compte gelé, enquête communautaire                       │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Spécifications Techniques Détaillées

### 11.1 Pile Technologique

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   TÉLÉPHONE UTILISATEUR (PWA JavaScript)                                  │
│   ──────────────────────────────────────                                   │
│   · wallet.js          — Portefeuille, signing, sync (vanilla JS)        │
│   · hpp_encoder.js     — Encodeur/décodeur HPP binaire                  │
│   · ed25519.js         — Implémentation Ed25519 légère                   │
│   · aes-gcm.js         — Web Crypto API (navigator.subtle)               │
│   · qrcode.js          — Génération QR code pour recevoir                │
│   · Stockage           — IndexedDB (chiffré AES-256-GCM)                 │
│   · Communication      — fetch() vers l'API locale de l'AP               │
│                                                                          │
│   AP VILLAGE (Python 3.11+ sur Raspberry Pi OS Lite)                     │
│   ──────────────────────────────────────────────────                      │
│   · registry.py        — Gestion du registre SQLite                      │
│   · validator.py       — Validation des transactions                    │
│   · sync.py            — Synchronisation inter-villages                  │
│   · api.py             — API REST pour les wallets utilisateurs          │
│   · treasury.py        — Gestion des entrées/sorties externes            │
│   · auditor.py         — Audit automatique quotidien                     │
│   · dashboard.py       — Dashboard web Grafana                           │
│   · Base de données    — SQLite 3.42+ avec WAL mode + chiffrement        │
│   · Serveur web        — nginx + uWSGI (ou FastAPI standalone)           │
│   · Clés              — Stockées dans TPM (si dispo) ou fichier chiffré │
│                                                                          │
│   PASSERELLE INTERNET (Python 3.11+ sur Mini-PC Debian 12)               │
│   ────────────────────────────────────────────────────────                │
│   · exchange.py        — Bridge Wise/PayPal (manuel, assisté)            │
│   · reports.py         — Génération rapports mensuels PDF                │
│   · federation.py      — Fédération inter-zone (optionnel)               │
│   · backup.py          — Backup automatique cloud (S3 compatible)        │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 11.2 API REST du Nœud AP

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   API ENDPOINTS (accessibles depuis le réseau HaLow)                      │
│                                                                          │
│   ─── TRANSACTIONS ───                                                    │
│                                                                          │
│   POST /api/pay/send                                                      │
│   ──────────────────                                                      │
│   Body : trame HPP signée (binaire, Content-Type: application/hpp)       │
│   Response : { "status": "confirmed", "tx_hash": "...", "timestamp": ... }│
│   Errors  : 400 (trame invalide), 402 (solde insuffisant),                │
│             409 (double-dépense), 422 (signature invalide)               │
│                                                                          │
│   POST /api/pay/send_batch                                                │
│   ─────────────────────────                                               │
│   Body : tableau de trames HPP signées (max 100)                         │
│   Response : [{ tx_hash, status }, ...]                                  │
│                                                                          │
│   ─── SOLDE ───                                                           │
│                                                                          │
│   GET /api/pay/balance/{user_id}                                          │
│   ───────────────────────────────                                          │
│   Response : { "user_id": 42, "balance": 12750, "pending_out": 0,        │
│                "pending_in": 500, "last_tx_at": 1721145600 }             │
│   Note : balance est en centièmes (12750 = 127.50 KA PAY)                │
│                                                                          │
│   ─── HISTORIQUE ───                                                      │
│                                                                          │
│   GET /api/pay/transactions/{user_id}?limit=50&offset=0&dir=all           │
│   ──────────────────────────────────────────────────────────────           │
│   Response : { "transactions": [{ tx_hash, type, from, to, amount,       │
│                memo, timestamp, status }, ...], "total": 342 }           │
│                                                                          │
│   ─── REGISTRE PUBLIC ───                                                 │
│                                                                          │
│   GET /api/pay/registry?limit=100                                         │
│   ─────────────────────────────────                                       │
│   Response : { "mass_monetaire": 284700, "reserve_eur": 180000,          │
│                "tx_count_24h": 87, "volume_24h": 42300,                  │
│                "last_block": { "hash": "...", "time": ..., "tx_count": 12}│
│              }                                                            │
│                                                                          │
│   GET /api/pay/registry/blocks?from={time}&to={time}                     │
│   ───────────────────────────────────────────────────────                 │
│   Response : [{ block_hash, start_time, end_time, tx_count,              │
│                total_volume, merkle_root, signature }, ...]              │
│                                                                          │
│   ─── GOUVERNANCE ───                                                     │
│                                                                          │
│   POST /api/pay/create_money                                              │
│   ────────────────────────────                                             │
│   Auth : Double signature Gardien + Trésorier requise                     │
│   Body : { "user_id": 42, "work_type": "maintenance", "amount": 1000,    │
│            "signature_gardien": "...", "signature_tresorier": "..." }    │
│   Response : { "status": "created", "tx_hash": "..." }                   │
│                                                                          │
│   POST /api/pay/propose_creation                                          │
│   ─────────────────────────────────                                       │
│   Auth : Signature Gardien requise                                        │
│   Body : { "user_id": 42, "work_type": "maintenance", "amount": 1000 }   │
│   Response : { "status": "pending_treasury_approval", "proposal_id": 7 } │
│                                                                          │
│   GET /api/pay/proposals?status=pending                                   │
│   ──────────────────────────────────────                                   │
│   Response : [{ proposal_id, user_id, work_type, amount, approved_by,    │
│                status, created_at }, ...]                                │
│                                                                          │
│   ─── SYNCHRONISATION ───                                                 │
│                                                                          │
│   POST /api/pay/sync/push_block                                           │
│   ───────────────────────────────                                          │
│   Body : Bloc de réconciliation signé (binaire)                           │
│   Response : { "status": "accepted", "block_hash": "..." }               │
│                                                                          │
│   GET /api/pay/sync/pull_blocks?since={block_hash}                        │
│   ────────────────────────────────────────────────                         │
│   Response : [{ block complet }, ...]                                    │
│                                                                          │
│   GET /api/pay/sync/status                                                │
│   ───────────────────────────                                              │
│   Response : { "latest_block": "...", "pending_blocks": 2,               │
│                "connected_villages": [3, 7, 12], "sync_lag_ms": 1234 }   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 11.3 Horloge Harmonique (φ-Timestamp)

Pour éviter les conflits d'horodatage entre villages (horloges désynchronisées), KA PAY utilise une horloge harmonique basée sur φ :

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   HORLOGE HARMONIQUE (φ-TIMESTAMP)                                        │
│                                                                          │
│   Principe : L'ordre total des transactions est déterminé par :          │
│                                                                          │
│   T_φ = T_unix × φ + H(village_id) × φ²                                  │
│                                                                          │
│   Où :                                                                    │
│   · T_unix = timestamp Unix en microsecondes                             │
│   · φ = (1 + √5) / 2 ≈ 1.618033988749895                                │
│   · H(village_id) = hash du village_id (déterministe, entre 0 et 1)     │
│                                                                          │
│   Propriété : Deux transactions au même T_unix dans deux villages        │
│   différents auront des T_φ différents (grâce au φ² × H(village_id)).   │
│   L'ordre est DÉTERMINISTE et ne dépend pas d'une horloge centrale.      │
│                                                                          │
│   En pratique :                                                           │
│   · Chaque AP maintient son T_unix via NTP (Starlink ou GPS)            │
│   · Si NTP est indisponible, l'horloge interne du RPi est utilisée       │
│   · La dérive max entre deux villages est < 100 ms (NTP)                 │
│   · Le H(village_id) garantit qu'aucune collision n'est possible         │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 12. Plan de Déploiement

### 12.1 Phases et Budget

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   PHASE 1 — PORTEFEUILLE LOCAL (Mois 1-2) — 10 000 €                     │
│   ─────────────────────────────────────────────                            │
│   □ Module wallet.js (IndexedDB + AES-256-GCM + Ed25519)                 │
│   □ Module hpp_encoder.js (encodage/décodage binaire HPP)                │
│   □ Interface UI dans KA Phone (écran Wallet, envoi, réception, QR)     │
│   □ Mode offline complet (file d'attente, flush automatique)             │
│   □ Tests unitaires + tests d'intégration                                │
│   □ Simulation de 1000 transactions sur 2 téléphones                     │
│   │                                                                      │
│   │  Équipe : 1 développeur PWA senior (2 mois)                          │
│   │  Livrable : PWA wallet fonctionnelle sur un téléphone Android        │
│                                                                          │
│   PHASE 2 — REGISTRE VILLAGEOIS (Mois 3-4) — 15 000 €                    │
│   ─────────────────────────────────────────────                            │
│   □ Module registry.py (SQLite, schéma complet)                          │
│   □ Module validator.py (vérification signatures, soldes, séquences)    │
│   □ Module api.py (endpoints REST pour les wallets)                      │
│   □ Module auditor.py (audit automatique quotidien)                      │
│   □ Dashboard Grafana (masse monétaire, transactions, alertes)          │
│   □ Déploiement sur Raspberry Pi 4 (l'AP du village)                    │
│   □ Test pilote : 2 villages RTHC, 20 utilisateurs, transactions réelles │
│   │                                                                      │
│   │  Équipe : 1 développeur backend Python + 1 intégrateur RTHC          │
│   │  Livrable : Registre fonctionnel sur 2 AP, 20 wallets actifs        │
│                                                                          │
│   PHASE 3 — CRÉATION MONÉTAIRE ET GOUVERNANCE (Mois 5-6) — 10 000 €     │
│   ────────────────────────────────────────────────────────────            │
│   □ Module treasury.py (entrées/sorties externes, double signature)      │
│   □ Interface de gouvernance (Trésorier, Gardien, Assemblée)            │
│   □ Module creation_events (proposition, approbation, exécution)        │
│   □ Module reports.py (rapports financiers mensuels PDF)                │
│   □ Module exchange.py (bridge Wise/PayPal pour la coopérative)         │
│   □ Test pilote : création monétaire réelle (travail communautaire)      │
│   │                                                                      │
│   │  Équipe : 1 développeur backend + 1 designer UI/UX                   │
│   │  Livrable : Cycle complet création → circulation → destruction      │
│                                                                          │
│   PHASE 4 — SYNC INTER-VILLAGES ET SCALE (Mois 7-9) — 15 000 €          │
│   ──────────────────────────────────────────────────────────              │
│   □ Module sync.py (push/pull blocs, rattrapage, résolution conflits)   │
│   □ Module federation.py (fédération inter-zone, agrégation)            │
│   □ Tests de résilience (panne backhaul, isolation village, reprise)    │
│   □ Déploiement sur 8 villages RTHC (Phase 3 RTHC)                      │
│   □ Intégration KA PAY × KA CARE × KA TV × KA PHONE                     │
│   □ Formation Trésoriers et Gardiens (8 villages)                        │
│   │                                                                      │
│   │  Équipe : 1 développeur Rust/C + 1 formateur terrain                 │
│   │  Livrable : 8 villages interconnectés, 200+ utilisateurs KA PAY     │
│                                                                          │
│   PHASE 5 — SCALE RÉGIONAL (Mois 10-12) — Inclus dans budget RTHC       │
│   ─────────────────────────────────────────────────────                   │
│   □ Déploiement sur 50 villages (Phase 4 RTHC)                           │
│   □ 10 000 utilisateurs KA PAY                                           │
│   □ Optimisation performances (HaLow, backhaul, SQLite)                  │
│   □ Audit de sécurité externe                                            │
│   □ Documentation et manuels en langues locales                          │
│   │                                                                      │
│   │  Équipe : Intégrée à l'équipe RTHC                                    │
│   │  Livrable : KA PAY opérationnel sur l'ensemble du réseau            │
│                                                                          │
│   ────────────────────────────────────────────────────────────            │
│   BUDGET TOTAL KA PAY : 50 000 € (12 mois)                                │
│   ─────────────────────────────────────────                                │
│   (À comparer au budget RTHC global : 250 000 €)                          │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 12.2 Indicateurs de Succès (KPIs)

| KPI | Phase 2 (Mois 4) | Phase 4 (Mois 9) | Phase 5 (Mois 12) |
|-----|:----------------:|:----------------:|:-----------------:|
| Utilisateurs actifs KA PAY | 20 | 200 | 10 000 |
| Transactions/jour | 10 | 200 | 5 000 |
| Volume journalier (KA PAY) | 50 | 1 000 | 25 000 |
| Masse monétaire en circulation | 500 | 5 000 | 50 000 |
| Latence intra-village | < 500 ms | < 500 ms | < 500 ms |
| Latence inter-villages | — | < 5 s | < 5 s |
| Taux d'erreur transactions | < 1% | < 0.5% | < 0.1% |
| Disponibilité registre | > 99% | > 99.5% | > 99.9% |
| Temps de reprise après panne | < 4 h | < 2 h | < 1 h |
| Frais moyens par transaction | 0 KA PAY | 0 KA PAY | 0 KA PAY |

---

## 13. Projections et Passage à l'Échelle

### 13.1 Évolution de la Masse Monétaire

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   PROJECTION — 50 VILLAGES, 10 000 FAMILLES (FIN ANNÉE 1)                 │
│                                                                          │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  MASSE MONÉTAIRE TOTALE : ~125 000 KA PAY                         │  │
│   │                                                                   │  │
│   │  Provenance :                                                     │  │
│   │  · Travail communautaire validé  :   25 000 KA PAY (20%)          │  │
│   │  · Entrées externes (ONG/diaspora):  100 000 KA PAY (80%)          │  │
│   │  · Détruites (sorties)            :   -0 KA PAY (pas de sortie   │  │
│   │                                           individuelle possible)  │  │
│   │                                                                   │  │
│   │  CIRCULATION :                                                    │  │
│   │  · Volume mensuel estimé          :   75 000 KA PAY               │  │
│   │  · Transactions mensuelles        :   ~15 000                     │  │
│   │  · Moyenne par transaction        :   5 KA PAY                    │  │
│   │  · Vélocité de la monnaie         :   0.6/mois                    │  │
│   │                                                                   │  │
│   │  ÉQUIVALENT EN EUROS : 125 000 €                                   │  │
│   │  (ancrage 1:1, intégralement adossé aux réserves + travail)       │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│   PROJECTION — 500 VILLAGES, 100 000 FAMILLES (FIN ANNÉE 3)              │
│                                                                          │
│   · Masse monétaire : ~2 500 000 KA PAY                                  │
│   · Volume mensuel : ~1 500 000 KA PAY                                   │
│   · Transactions mensuelles : ~300 000                                   │
│   · KA PAY devient la monnaie principale des échanges locaux            │
│                                                                          │
│   PROJECTION — 5 000 VILLAGES, 1 MILLION DE FAMILLES (FIN ANNÉE 5)       │
│                                                                          │
│   · Masse monétaire : ~50 000 000 KA PAY                                 │
│   · Volume mensuel : ~30 000 000 KA PAY                                  │
│   · Transactions mensuelles : ~6 000 000                                 │
│   · KA PAY = première monnaie numérique panafricaine                    │
│   · Les opérateurs télécom demandent à s'interconnecter                  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 13.2 Interopérabilité Future (Année 5+)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   QUAND LE RÉSEAU SERA ASSEZ GRAND (10M+ UTILISATEURS) :                  │
│                                                                          │
│   Ce n'est pas KA PAY qui s'adaptera aux opérateurs.                     │
│   Ce sont les opérateurs qui voudront se connecter à KA PAY.             │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  ORANGE : « Nous souhaitons que nos 80M utilisateurs Orange       │   │
│   │            Money puissent échanger avec le réseau KA PAY. »       │   │
│   │                                                                   │   │
│   │  KA PAY : « Voici notre API de bridge ouverte.                     │   │
│   │             Frais d'interconnexion : 0.1% (vs vos 2-3%).          │   │
│   │             Pas de KYC supplémentaire (le réseau a déjà            │   │
│   │             vérifié l'identité de nos membres).                    │   │
│   │             Pas de données utilisateur exportées.                  │   │
│   │             Vous vous connectez à NOTRE protocole. »               │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   C'EST LE RÉSEAU COMMUNAUTAIRE QUI DICTE LES CONDITIONS.                │
│   PAS L'OPÉRATEUR.                                                       │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Annexes

### A. Acronymes

| Acronyme | Signification |
|----------|---------------|
| HPP | Harmonic Payment Protocol |
| HTP | Harmonic Transport Protocol |
| PoAC | Proof-of-Authority Communautaire |
| RTHC | Réseau Télécom Harmonique Communautaire |
| HVC | Harmonic Voice Codec |
| HHD2 | Harmonic-HCV Dictionary Codec v2 |
| KA PAY | KA Paiement — Monnaie Communautaire Autonome |
| TPM | Trusted Platform Module |
| WAL | Write-Ahead Logging (SQLite) |

### B. Références aux Documents Existants

| Document | Contenu |
|----------|---------|
| SPEC_TECHNIQUE_RESEAU_HARMONIQUE.md | Architecture RTHC, protocoles HTP, adressage, sécurité |
| PLAN_DEPLOIEMENT_RESEAU_HARMONIQUE.md | Déploiement RTHC en 4 phases sur 12 mois |
| STRATEGIE_KA_TV.md | Plateforme OTT avec paiement mobile money |
| BLE_INTEGRATION.md | Intégration dispositifs médicaux BLE via Web Bluetooth |
| DONATEURS.md | Stratégie de financement KA CARE |
| SPEC_IA_HARMONIQUE_ECOSYSTEM.md | IA Harmonique — couche transversale (fraude, diagnostic, éducation, agriculture) |

### C. Licence

Le protocole HPP est publié sous licence ouverte (MIT). Les implémentations de référence (wallet.js, registry.py, sync.py) sont open source. Le réseau KA PAY est un bien commun, gouverné par les communautés qui l'utilisent.

---

*Spécification technique v1.0 — Juillet 2026 — Projet Univers Harmonique*

> *« Un village qui communique sans opérateur, se soigne sans médecin, regarde la TV sans parabole, et paie sans banque — n'a plus besoin de demander la permission pour exister. »*
