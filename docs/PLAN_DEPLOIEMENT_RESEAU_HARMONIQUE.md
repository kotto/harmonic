# Plan de Déploiement — Réseau Télécom Harmonique Communautaire

**Document** : DEPLOY-RTHC-1.0  
**Date** : Juillet 2026  
**Auteur** : Alain Kotto — Projet Univers Harmonique  
**Statut** : Plan de référence (v1.0)

---

## Résumé Exécutif

Ce document présente le plan complet de déploiement du Réseau Télécom Harmonique Communautaire (RTHC), un réseau de communications souverain conçu pour les zones rurales et périurbaines des pays en développement.

**Objectif 12 mois :** 50 villages connectés, 10 000 utilisateurs, 0€ de crédit téléphonique récurrent.  
**Coût total Phase 1-4 :** ~250 000€ pour connecter 50 villages (200 familles/village).  
**Retour communautaire :** Économie de 120 000 – 360 000€/an sur les dépenses téléphoniques des utilisateurs.  
**Modèle :** Communauté propriétaire, gouvernance locale, maintenance par des techniciens formés.

---

## Table des Matières

1. [Stratégie de Déploiement](#1-stratégie-de-déploiement)
2. [Phases et Timeline](#2-phases-et-timeline)
3. [Budget Détaillé](#3-budget-détaillé)
4. [Modèle Communautaire](#4-modèle-communautaire)
5. [Formation et Transfert de Compétences](#5-formation-et-transfert-de-compétences)
6. [Stratégie de Financement](#6-stratégie-de-financement)
7. [Indicateurs de Succès (KPIs)](#7-indicateurs-de-succès-kpis)
8. [Gestion des Risques](#8-gestion-des-risques)
9. [Pays Cibles Prioritaires](#9-pays-cibles-prioritaires)
10. [Stratégie de Passage à l'Échelle](#10-stratégie-de-passage-à-léchelle)

---

## 1. Stratégie de Déploiement

### 1.1 Principe Fondateur

> **« Un village à la fois. La communauté au centre. La technologie au service. »**

Le déploiement ne suit pas une logique de conquête de marché mais une logique d'**empowerment communautaire**. Chaque village doit :
1. **Comprendre** la valeur du réseau
2. **Vouloir** le réseau (demande exprimée, pas imposée)
3. **Participer** à l'installation (main d'œuvre, hébergement des relais)
4. **Posséder** le réseau (gouvernance locale)
5. **Maintenir** le réseau (techniciens locaux formés)

### 1.2 Critères de Sélection des Villages Pilotes

| Critère | Pondération | Seuil |
|---------|:----------:|-------|
| Population (200-5000 habitants) | 25% | > 200 habitants |
| Absence de couverture 4G fiable | 30% | Aucune ou très instable |
| Coût crédit téléphonique > 5% revenu | 20% | > 5% du revenu mensuel médian |
| Présence d'un leader communautaire motivé | 15% | Identifié et engagé |
| Présence d'un centre de santé | 10% | Dans le village ou < 5 km |

### 1.3 Approche par Zone de Déploiement

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  ZONE DE DÉPLOIEMENT = 5-10 villages dans un rayon de 50 km     │
│                                                                  │
│  Pourquoi 50 km ?                                                │
│  · Distance maximale d'une liaison backhaul 5 GHz fiable        │
│  · Un administrateur technique peut couvrir la zone en 1 jour   │
│  · Les villages ont des liens économiques/sociaux existants      │
│  · Une seule passerelle Internet (Starlink) pour la zone         │
│                                                                  │
│  EXEMPLE ZONE TYPE :                                             │
│  ────────────────────                                             │
│  · 8 villages, 200-500 habitants chacun                          │
│  · Distance moyenne inter-village : 8-15 km                      │
│  · 1 village central (marché, centre de santé)                   │
│  · 1 passerelle Internet au village central                      │
│  · Coût total zone : ~35 000 – 50 000€                           │
│  · Utilisateurs zone : 1600-4000 personnes                       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Phases et Timeline

### 2.1 Vue d'Ensemble

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  MOIS 1-2      MOIS 3-4       MOIS 5-8        MOIS 9-12         │
│  ─────────     ─────────      ─────────       ─────────          │
│  PHASE 1        PHASE 2        PHASE 3          PHASE 4          │
│                                                                  │
│  Proto lab      1 village      1 zone           5 zones          │
│  Validation     Pilote réel    (8 villages)     (40 villages)    │
│  2 nœuds        200 util.      1600 util.       8000 util.       │
│  Coût: 5K€      Coût: 20K€     Coût: 50K€      Coût: 175K€     │
│                                                                  │
│  ═══════════════════════════════════════════════════════════►    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Phase 1 — Preuve de Concept Technique (Mois 1-2)

**Objectif :** Démontrer que la voix compressée passe sur HaLow avec une qualité acceptable.

```
┌──────────────────────────────────────────────────────────────────┐
│  PHASE 1 — DÉTAIL                                                │
│                                                                  │
│  SEMAINE 1-2 : PROTOTYPE VOCAL                                   │
│  ─────────────────────────────                                    │
│  □ Implémenter HVC encodeur/décodeur en Python                   │
│  □ Tester avec des échantillons vocaux réels                      │
│  □ Mesurer MOS, débit, latence                                   │
│  □ Ajuster dictionnaire phonétique (500-1000 fragments)          │
│  □ Valider : MOS > 3.5, débit < 1500 bps                        │
│                                                                  │
│  SEMAINE 3-4 : INTÉGRATION HALOW                                 │
│  ────────────────────────────────                                  │
│  □ Commander 2 modules Morse Micro MM6108                         │
│  □ Installer sur 2 Raspberry Pi 4                                │
│  □ Configurer lien HaLow point-à-point                           │
│  □ Intégrer HVC dans la chaîne : micro → encode → HaLow         │
│    → decode → haut-parleur                                       │
│  □ Test d'appel bidirectionnel                                   │
│  □ Mesurer : latence bout-en-bout, qualité, stabilité            │
│                                                                  │
│  SEMAINE 5-6 : INTÉGRATION COMPRESSION IMAGE                     │
│  ────────────────────────────────────────                          │
│  □ Portage du décodeur HHD2 en C (depuis Python)                 │
│  □ Test : photo → encode → HaLow → decode → affichage           │
│  □ Mesurer : temps de transmission, PSNR                         │
│                                                                  │
│  SEMAINE 7-8 : TEST ROBUSTESSE                                    │
│  ─────────────────────────────                                    │
│  □ Test distance : 100m → 500m → 1 km → 2 km                    │
│  □ Test interférences (autres WiFi, obstacles)                   │
│  □ Test continuité : appel de 5 minutes                          │
│  □ Rapport de validation technique                               │
│                                                                  │
│  LIVRABLES :                                                     │
│  · HVC codec Python fonctionnel                                  │
│  · 2 nœuds HaLow communicants                                    │
│  · Démonstration vidéo : appel vocal + transfert photo           │
│  · Rapport technique avec métriques                              │
│                                                                  │
│  BUDGET : 5 000€                                                 │
│  ─────────────                                                    │
│  · 2 × RPi 4 + MM6108 + accessoires : 400€                      │
│  · 2 × antennes + câbles : 100€                                  │
│  · 2 × kits solaires 50W : 240€                                  │
│  · 1 × mini-PC passerelle test : 300€                            │
│  · Matériel audio (micros, HP, carte son USB) : 200€             │
│  · Divers (câbles, connecteurs, boîtiers) : 200€                 │
│  · Ingénierie (2 mois, 1 personne) : 3 560€                      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.3 Phase 2 — Pilote Village (Mois 3-4)

**Objectif :** Déployer le réseau complet dans UN village réel et mesurer l'adoption.

```
┌──────────────────────────────────────────────────────────────────┐
│  PHASE 2 — DÉTAIL                                                │
│                                                                  │
│  VILLAGE PILOTE :                                                │
│  · Population : 200-500 habitants                                │
│  · ~50 familles équipées de boîtiers HN-1                        │
│  · 1 point d'accès HaLow                                         │
│  · 1 passerelle LoRa (capteurs agricoles/santé)                  │
│  · 1 passerelle Internet (Starlink ou 4G)                        │
│                                                                  │
│  ACTIVITÉS :                                                     │
│  ───────────                                                      │
│  SEMAINE 1 : Préparation                                         │
│  □ Sélection du village pilote (critères section 1.2)           │
│  □ Rencontre chef village + leaders communautaires               │
│  □ Présentation du projet, recueil des attentes                  │
│  □ Identification du « Gardien du réseau » local                 │
│                                                                  │
│  SEMAINE 2 : Installation infrastructure                         │
│  □ Installation mât + AP HaLow + solaire                         │
│  □ Installation passerelle LoRa                                  │
│  □ Installation passerelle Internet (Starlink)                   │
│  □ Test de couverture                                            │
│                                                                  │
│  SEMAINE 3 : Distribution boîtiers                                │
│  □ Fabrication/assemblage des 50 boîtiers HN-1                   │
│  □ Distribution aux familles                                     │
│  □ Formation utilisateurs (2h par groupe de 10)                  │
│  □ Installation application PWA sur leurs téléphones             │
│                                                                  │
│  SEMAINE 4 : Mise en service                                      │
│  □ Premier appel officiel (cérémonie communautaire)              │
│  □ Support intensif (présence quotidienne)                        │
│  □ Recueil feedback                                               │
│                                                                  │
│  SEMAINES 5-8 : Support + Mesures                                │
│  □ Support réduit (présence 2×/semaine)                         │
│  □ Mesures : appels/jour, données échangées, problèmes           │
│  □ Enquête satisfaction utilisateurs                             │
│  □ Rapport de pilote                                             │
│                                                                  │
│  LIVRABLES :                                                     │
│  · 1 village connecté et fonctionnel                             │
│  · 50 utilisateurs actifs                                        │
│  · Données d'usage réelles                                       │
│  · Rapport de pilote avec leçons apprises                        │
│  · Vidéo témoignage utilisateurs                                 │
│                                                                  │
│  BUDGET : 20 000€                                                │
│  ──────────────                                                   │
│  · Infrastructure village (AP + solaire + mât) : 600€           │
│  · Passerelle Internet (Starlink + PC) : 700€                    │
│  · Passerelle LoRa : 60€                                         │
│  · 50 boîtiers HN-1 × 30€ : 1 500€                              │
│  · Matériel divers (câbles, boîtiers) : 300€                    │
│  · Logistique pilote (déplacement, hébergement 4 sem) : 2 000€  │
│  · Ingénierie (2 mois, 2 personnes) : 14 840€                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.4 Phase 3 — Zone Pilote (Mois 5-8)

**Objectif :** Étendre à 7 villages supplémentaires, créer le premier réseau maillé inter-villages.

```
┌──────────────────────────────────────────────────────────────────┐
│  PHASE 3 — DÉTAIL                                                │
│                                                                  │
│  EXTENSION :                                                     │
│  · 7 nouveaux villages (total zone : 8 villages)                │
│  · ~200 utilisateurs/village → 1600 utilisateurs zone           │
│  · Backhaul 5 GHz entre villages                                 │
│  · 1 passerelle Internet partagée (Starlink)                     │
│  · Formation de 2 administrateurs techniques locaux              │
│                                                                  │
│  ACTIVITÉS PAR VILLAGE (répétées 7 fois) :                      │
│  ────────────────────────────────────────                         │
│  · Installation AP HaLow + solaire                               │
│  · Installation antenne backhaul 5 GHz (liaison vers hub)       │
│  · Distribution 25-50 boîtiers                                   │
│  · Formation utilisateurs                                        │
│  · Désignation Gardien du réseau                                 │
│                                                                  │
│  BACKHAUL INTER-VILLAGES :                                       │
│  □ Étude de ligne de vue (LoS) entre villages                   │
│  □ Installation liaisons 5 GHz directionnelles                   │
│  □ Configuration routage mesh (BATMAN-adv)                       │
│  □ Test redondance (coupure simulée → basculement)              │
│                                                                  │
│  FORMATION :                                                     │
│  □ 2 administrateurs techniques (formation intensive 1 semaine) │
│  □ 8 Gardiens de réseau (formation 1 jour)                      │
│  □ Manuel de maintenance en français/langue locale              │
│                                                                  │
│  LIVRABLES :                                                     │
│  · Zone de 8 villages connectés                                  │
│  · 1600+ utilisateurs                                            │
│  · Équipe technique locale autonome                              │
│  · Manuel de déploiement standardisé                             │
│                                                                  │
│  BUDGET : 50 000€                                                │
│  ──────────────                                                   │
│  · 7 × infrastructure village (AP + solaire + mât) : 4 200€    │
│  · 8 × antennes backhaul 5 GHz : 2 800€                         │
│  · 1 × passerelle Starlink zone (partagée) : 500€               │
│  · 7 × passerelle LoRa : 420€                                   │
│  · 200 boîtiers HN-1 × 28€ (volume) : 5 600€                   │
│  · Installation backhaul (mâts, haubans) : 3 500€               │
│  · Logistique zone (déplacements, hébergement) : 6 000€         │
│  · Formation (matériel, locaux) : 1 000€                         │
│  · Ingénierie (4 mois, 3 personnes) : 25 980€                   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.5 Phase 4 — Scale Régional (Mois 9-12)

**Objectif :** Répliquer le modèle sur 5 zones supplémentaires (40 villages, ~8000 utilisateurs).

```
┌──────────────────────────────────────────────────────────────────┐
│  PHASE 4 — DÉTAIL                                                │
│                                                                  │
│  SCALE :                                                         │
│  · 5 nouvelles zones × 8 villages = 40 villages                 │
│  · ~200 utilisateurs/village → 8000 utilisateurs additionnels   │
│  · Équipe de déploiement locale (les 2 admins de Phase 3)       │
│  · Partenariat avec ONG/coopération pour le financement         │
│                                                                  │
│  APPROCHE :                                                      │
│  · L'équipe technique de la Phase 3 forme les nouvelles équipes │
│  · 1 zone déployée toutes les 3 semaines                        │
│  · Production locale des boîtiers (atelier d'assemblage)        │
│  · Documentation et outils en open source                        │
│                                                                  │
│  PRODUCTION LOCALE :                                             │
│  □ Identifier un atelier d'électronique partenaire              │
│  □ Commander composants en volume (1000+ unités)                 │
│  □ Assemblage + test local                                       │
│  □ → Réduction coût boîtier : 30€ → 22€                         │
│                                                                  │
│  LIVRABLES :                                                     │
│  · 50 villages connectés au total                                │
│  · 10 000 utilisateurs                                           │
│  · 5 équipes techniques régionales                               │
│  · Capacité de production locale                                 │
│  · Étude d'impact socio-économique                               │
│                                                                  │
│  BUDGET : 175 000€                                               │
│  ───────────────                                                  │
│  · 40 × infrastructure village : 24 000€                        │
│  · 5 × passerelles Starlink zone : 2 500€                       │
│  · 40 × antennes backhaul 5 GHz : 14 000€                       │
│  · 40 × passerelles LoRa : 2 400€                               │
│  · 1000 boîtiers HN-1 × 22€ (volume) : 22 000€                 │
│  · Infrastructure backhaul inter-zone : 20 000€                  │
│  · Logistique (6 équipes, 4 mois) : 25 000€                     │
│  · Formation + documentation : 5 000€                            │
│  · Ingénierie (4 mois, 6 personnes) : 60 100€                   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Budget Détaillé

### 3.1 Budget Consolidé 12 Mois

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  BUDGET TOTAL 12 MOIS : 250 000€                                 │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  POSTE                     MONTANT     %      NOTES         │ │
│  │  ─────                     ───────    ───     ─────         │ │
│  │                                                             │ │
│  │  ÉQUIPEMENT RÉSEAU         75 000€    30%                   │ │
│  │  · AP HaLow (50 unités)    (30 000€)      600€/unité       │ │
│  │  · Backhaul 5 GHz          (20 300€)      350€/liaison     │ │
│  │  · Passerelles LoRa         (2 880€)       60€/unité       │ │
│  │  · Passerelles Internet     (3 700€)       700€/zone       │ │
│  │  · Mâts + haubans          (18 120€)                         │ │
│  │                                                             │ │
│  │  BOÎTIERS UTILISATEURS     34 500€   14%                    │ │
│  │  · 1250 unités             (34 500€)      27.60€/unité     │ │
│  │    (Phase 2: 50, Phase 3: 200, Phase 4: 1000)              │ │
│  │                                                             │ │
│  │  LOGISTIQUE                33 000€   13%                    │ │
│  │  · Déplacements            (15 000€)                        │ │
│  │  · Hébergement terrain     (12 000€)                        │ │
│  │  · Transport matériel       (6 000€)                        │ │
│  │                                                             │ │
│  │  FORMATION                  6 000€    2%                    │ │
│  │  · Sessions formation       (3 000€)                        │ │
│  │  · Manuels + documentation  (1 500€)                        │ │
│  │  · Traduction               (1 500€)                        │ │
│  │                                                             │ │
│  │  INGÉNIERIE               101 500€   41%                    │ │
│  │  · Phase 1 (2 mois)        (3 560€)    1 personne          │ │
│  │  · Phase 2 (2 mois)       (14 840€)    2 personnes         │ │
│  │  · Phase 3 (4 mois)       (25 980€)    3 personnes         │ │
│  │  · Phase 4 (4 mois)       (60 100€)    6 personnes         │ │
│  │  · Réserve technique       (-2 980€)    (ajustement)       │ │
│  │  (Note: ingénierie locale aux taux pratiqués)               │ │
│  │                                                             │ │
│  │  TOTAL                    250 000€   100%                    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 Budget par Village (Récurrent)

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  COÛT MENSUEL RÉCURRENT PAR VILLAGE (200 familles)              │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  POSTE                     MENSUEL    ANNUEL    PAR FAMILLE  │ │
│  │  ─────                     ───────    ──────    ───────────  │ │
│  │                                                             │ │
│  │  Starlink (partagé 8 vill.)  5€        60€       0.025€     │ │
│  │  Maintenance batteries       5€        60€       0.025€     │ │
│  │  Admin technique (partagé)  15€       180€       0.075€     │ │
│  │  Fonds de réserve            5€        60€       0.025€     │ │
│  │  ───────────────────────                                     │ │
│  │  TOTAL                      30€       360€       0.15€      │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  COÛT PAR FAMILLE ET PAR MOIS : 0.15€                            │
│  ─────────────────────────────────────                            │
│  (contre 5-15€ pour un opérateur classique)                      │
│                                                                  │
│  ÉCONOMIE PAR FAMILLE ET PAR AN : 58€ – 178€                     │
│  ────────────────────────────────────────────                     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 3.3 Retour sur Investissement

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  ROI POUR LA COMMUNAUTÉ (50 villages, 10 000 familles)           │
│                                                                  │
│  INVESTISSEMENT INITIAL : 250 000€ (une fois)                    │
│  ────────────────────────────────────────                         │
│                                                                  │
│  COÛT RÉCURRENT : 360€ × 50 villages / 12 mois = 18 000€/an    │
│  ─────────────────────────────────────────────────────           │
│                                                                  │
│  ÉCONOMIE VS OPÉRATEUR CLASSIQUE :                               │
│  · Scénario conservateur (5€/mois/famille) :                    │
│    10 000 × 5€ × 12 = 600 000€/an d'économies                   │
│    ROI communautaire : < 6 MOIS                                  │
│                                                                  │
│  · Scénario médian (10€/mois/famille) :                          │
│    10 000 × 10€ × 12 = 1 200 000€/an d'économies                │
│    ROI communautaire : < 3 MOIS                                  │
│                                                                  │
│  → L'investissement est récupéré par la communauté               │
│    EN MOINS DE 6 MOIS rien qu'en crédit téléphonique.            │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 3.4 Structure de Financement Recommandée

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  FINANCEMENT PHASE 1 (5 000€) : FONDS PROPRES / LOVE MONEY     │
│  ─────────────────────────────────────────────────────            │
│  · Bootstrapping : l'équipe fondatrice finance le proto          │
│  · Risque : très faible (validation technique uniquement)       │
│                                                                  │
│  FINANCEMENT PHASE 2 (20 000€) : SUBVENTION INNOVATION          │
│  ──────────────────────────────────────────────                   │
│  · Fonds innovation télécom (ITU, Banque Mondiale)              │
│  · Fondations tech (Mozilla, Open Technology Fund)              │
│  · Ambassades / Coopération décentralisée                       │
│  · Crowdfunding ciblé (diaspora, solidarité internationale)     │
│                                                                  │
│  FINANCEMENT PHASE 3 (50 000€) : PARTENARIAT ONG                │
│  ──────────────────────────────────────────                       │
│  · ONG de développement rural (AFD, GIZ, USAID, DFID)          │
│  · Fondations santé (Gates, MSF — argument KA CARE)            │
│  · Opérateurs télécoms (Orange, MTN — RSE)                     │
│                                                                  │
│  FINANCEMENT PHASE 4 (175 000€) : BLENDED FINANCE               │
│  ────────────────────────────────────────────                     │
│  · 50% subventions (agences développement)                      │
│  · 25% prêts à taux zéro (microfinance, coopération)           │
│  · 25% contributions communautaires (en nature ou cash)         │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4. Modèle Communautaire

### 4.1 Gouvernance

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  GOUVERNANCE DU RÉSEAU (par village)                             │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  ASSEMBLÉE DES UTILISATEURS                                  │ │
│  │  ─────────────────────────────                                │ │
│  │  · Tous les utilisateurs du village                          │ │
│  │  · Réunion trimestrielle                                     │ │
│  │  · Décide : tarifs, nouveaux services, réinvestissement     │ │
│  └──────────────────────────┬──────────────────────────────────┘ │
│                             │                                    │
│              ┌──────────────┼──────────────┐                    │
│              │              │              │                    │
│     ┌────────┴──────┐ ┌────┴─────┐ ┌──────┴──────┐            │
│     │  GARDIEN       │ │ TRÉSORIER│ │ ANIMATEUR   │            │
│     │  (technique)   │ │ (caisse) │ │ (social)    │            │
│     │                │ │          │ │             │            │
│     │ · Surveillance │ │ · Collecte│ │ · Formation │            │
│     │ · Redémarrage  │ │ · Paiement│ │ · Support   │            │
│     │ · Rapport      │ │ · Comptes │ │ · Inclusion │            │
│     └────────┬───────┘ └────┬─────┘ └──────┬──────┘            │
│              │              │              │                    │
│              └──────────────┼──────────────┘                    │
│                             │                                    │
│                    ┌────────┴────────┐                          │
│                    │  ADMIN TECH     │                          │
│                    │  (inter-village)│                          │
│                    │                 │                          │
│                    │ · 1 pour 10     │                          │
│                    │   villages      │                          │
│                    │ · Installation  │                          │
│                    │ · Maintenance   │                          │
│                    │ · Réparations   │                          │
│                    └─────────────────┘                          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 Modèle Économique Communautaire

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  PRINCIPE : LE RÉSEAU N'EST PAS UN BUSINESS.                     │
│            C'EST UN BIEN COMMUN.                                 │
│                                                                  │
│  COTISATION MENSUELLE (suggérée, décidée par l'assemblée) :     │
│  ───────────────────────────────────────────────────────          │
│  · 0.15 – 0.50€ par mois par famille                             │
│  · Couvre : Starlink, maintenance, admin technique              │
│  · Payable en KA PAY (monnaie communautaire), espèces, ou en nature    │
│    (ex : un poulet = 2 mois de cotisation)                      │
│                                                                  │
│  CAS PARTICULIERS :                                              │
│  · Familles sans revenu : cotisation offerte (fonds de solidarité)│
│  · Services publics (centre de santé, école) : gratuit          │
│  · Commerçants/utilisateurs intensifs : cotisation majorée      │
│    (ex : 1€/mois au lieu de 0.15€)                              │
│                                                                  │
│  PROPRIÉTÉ :                                                     │
│  · L'infrastructure (AP, mât, solaire) appartient à la          │
│    COOPÉRATIVE DU RÉSEAU, association locale à but non lucratif │
│  · Les boîtiers HN-1 appartiennent aux familles                 │
│  · Les fréquences (ISM) n'appartiennent à personne              │
│                                                                  │
│  RÉINVESTISSEMENT :                                              │
│  · 70% → Fonds de fonctionnement (Starlink, maintenance)        │
│  · 20% → Fonds de réserve (pannes, remplacement batteries)     │
│  · 10% → Fonds de solidarité (familles sans revenu)            │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 4.3 Cycle de Vie du Réseau

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  ANNÉE 1 : LANCEMENT                                             │
│  ─────────────────                                                │
│  · Installation par l'équipe projet                              │
│  · Formation intensive                                            │
│  · Support rapproché                                              │
│  · Subvention couvre 100% des coûts                              │
│                                                                  │
│  ANNÉE 2 : TRANSITION                                            │
│  ──────────────────                                               │
│  · L'équipe locale prend en charge la maintenance                │
│  · Subvention couvre 50%, cotisations 50%                        │
│  · Développement de services payants (publicité locale, etc.)   │
│                                                                  │
│  ANNÉE 3+ : AUTONOMIE                                            │
│  ────────────────────                                             │
│  · Le réseau est 100% auto-financé                               │
│  · Cotisations + services = fonctionnement                      │
│  · L'équipe projet ne fait que du support niveau 3               │
│  · Le réseau peut s'étendre par lui-même aux villages voisins   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. Formation et Transfert de Compétences

### 5.1 Programme de Formation

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  MODULE 1 : GARDIEN DU RÉSEAU (1 jour)                          │
│  ──────────────────────────────────────                           │
│  Public : 1 personne par village, niveau alphabétisé             │
│  Contenu :                                                       │
│  · Qu'est-ce que le réseau ? (concepts simples)                  │
│  · Les boîtiers : reconnaître les LEDs, redémarrer              │
│  · Le point d'accès : où est-il, comment le redémarrer           │
│  · Signaler un problème (téléphone, WhatsApp)                    │
│  · Protéger l'équipement (vol, pluie, animaux)                  │
│  Format : Pratique, en langue locale, avec images                │
│                                                                  │
│  MODULE 2 : ADMINISTRATEUR TECHNIQUE (1 semaine)                 │
│  ─────────────────────────────────────────────                    │
│  Public : 1 personne pour 10 villages, niveau secondaire+        │
│  Prérequis : savoir utiliser un smartphone et un ordinateur      │
│  Contenu :                                                       │
│  · Jour 1 : Concepts réseau (IP, WiFi, routage simples)         │
│  · Jour 2 : Installation AP HaLow + antenne backhaul            │
│  · Jour 3 : Configuration logicielle (interface web)            │
│  · Jour 4 : Diagnostic pannes (méthodologie, outils)            │
│  · Jour 5 : Pratique sur le terrain                              │
│  Format : 50% théorie, 50% pratique                              │
│                                                                  │
│  MODULE 3 : ANIMATEUR COMMUNAUTAIRE (2 jours)                    │
│  ──────────────────────────────────────────                       │
│  Public : 1 personne par village                                 │
│  Contenu :                                                       │
│  · Jour 1 : Former les utilisateurs (pédagogie)                 │
│  · Jour 2 : Gestion de communauté, inclusion                    │
│     (femmes, personnes âgées, non-alphabétisés)                 │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 5.2 Documentation

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  KIT DE DOCUMENTATION (par village)                              │
│                                                                  │
│  · MANUEL DU GARDIEN (10 pages, format A5, illustré)            │
│    → « Si la LED rouge clignote, appuyer 5 secondes sur RESET » │
│                                                                  │
│  · GUIDE DE L'UTILISATEUR (2 pages, recto-verso plastifié)      │
│    → « Pour appeler : ouvrir l'app, taper le nom, appuyer 📞 » │
│                                                                  │
│  · AFFICHE DU RÉSEAU (1 page, format A3, pour lieu public)      │
│    → Numéros d'urgence, contacts utiles                          │
│                                                                  │
│  · VIDÉO TUTORIEL (5 minutes, en langue locale)                  │
│    → Disponible hors ligne sur le réseau lui-même                │
│                                                                  │
│  TOUT EN :                                                       │
│  · Français (langue officielle)                                  │
│  · Langue locale (wolof, bambara, swahili, lingala, etc.)       │
│  · Pictogrammes universels                                       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 6. Stratégie de Financement

### 6.1 Sources de Financement par Phase

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  PHASE 1 (5 000€) — AMORÇAGE                                     │
│  ─────────────────────────────                                    │
│  · Auto-financement fondateur : 3 000€                           │
│  · Dons personnel (friends & family) : 2 000€                    │
│  · Alternative : bourse innovation (ex : Prototype Fund)         │
│                                                                  │
│  PHASE 2 (20 000€) — SUBVENTIONS INNOVATION                      │
│  ──────────────────────────────────────                           │
│  · Mozilla Technology Fund : 10 000 – 50 000€                    │
│    → Thématique : « Alternatives décentralisées »               │
│  · Open Technology Fund : 10 000 – 100 000€                     │
│    → Thématique : « Internet freedom, connectivity »            │
│  · NLnet Foundation : 5 000 – 50 000€                           │
│    → Thématique : « Next Generation Internet »                  │
│  · ITU Innovation Challenge : 5 000 – 25 000€                   │
│    → Thématique : « Connecter les non-connectés »               │
│  · Ambassade de France / Affaires étrangères : 10 000 – 30 000€ │
│    → Programme : Fonds de solidarité pour projets innovants     │
│                                                                  │
│  PHASE 3 (50 000€) — PARTENARIATS DÉVELOPPEMENT                  │
│  ──────────────────────────────────────────                       │
│  · AFD (Agence Française de Développement) : 50 000 – 200 000€  │
│  · GIZ (Coopération allemande) : via programme Digital Africa   │
│  · USAID Digital Strategy : 50 000 – 500 000€                   │
│  · Fondation Gates : via programme « Connectivity »             │
│  · GSMA Mobile for Development : soutien technique + financier  │
│                                                                  │
│  PHASE 4 (175 000€) — BLENDED FINANCE                            │
│  ─────────────────────────────────────                            │
│  · Banque Mondiale (IDA — guichet pays pauvres)                 │
│    → Programme : Digital Development Partnership                │
│  · Fonds d'infrastructure numérique africain (UE/UA)            │
│  · Crowdfunding diaspora : 20 000 – 50 000€                     │
│    → « Connecte ton village natal »                             │
│  · Micro-crédit communautaire (coopératives villageoises)       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 6.2 Budget Prévisionnel Détaillé (Tableur)

Voir le fichier `BUDGET_RESEAU_HARMONIQUE.ods` (à créer — tableur avec formules de calcul automatique selon nombre de villages, utilisateurs, etc.)

---

## 7. Indicateurs de Succès (KPIs)

### 7.1 Métriques Techniques

| KPI | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|-----|:-------:|:-------:|:-------:|:-------:|
| Disponibilité réseau | > 95% | > 90% | > 90% | > 95% |
| Latence appel intra-village | < 50 ms | < 50 ms | < 50 ms | < 50 ms |
| Latence appel inter-villages | — | — | < 100 ms | < 100 ms |
| Qualité voix (MOS) | > 3.5 | > 3.5 | > 3.5 | > 3.5 |
| Taux de perte paquets | < 2% | < 5% | < 3% | < 2% |
| Temps transfert photo | < 1s | < 2s | < 1s | < 1s |

### 7.2 Métriques d'Adoption

| KPI | Phase 2 | Phase 3 | Phase 4 |
|-----|:-------:|:-------:|:-------:|
| Utilisateurs actifs/jour | > 60% équipés | > 50% équipés | > 50% équipés |
| Appels/jour/utilisateur | > 1 | > 1.5 | > 2 |
| Messages/jour/utilisateur | > 3 | > 5 | > 7 |
| Réduction achat crédit opérateur | > 50% | > 70% | > 80% |
| Satisfaction utilisateur (1-5) | > 4.0 | > 4.0 | > 4.0 |
| Taux de panne boîtier | < 5% | < 5% | < 3% |

### 7.3 Métriques d'Impact

| KPI | Cible 12 mois |
|-----|:------------:|
| Argent économisé par les utilisateurs | > 500 000€ cumulé |
| Appels d'urgence sanitaire facilités | > 500 appels |
| Emplois locaux créés (techniciens, gardiens) | > 50 emplois |
| Villages autonomes (sans subvention) | 0 → cible Année 3 |
| Temps moyen de résolution panne | < 24h |
| Taux de rétention utilisateurs à 6 mois | > 90% |

---

## 8. Gestion des Risques

### 8.1 Matrice des Risques

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  RISQUE                    PROB.   IMPACT   MITIGATION           │
│  ─────                     ─────   ──────   ──────────           │
│                                                                  │
│  TECHNIQUES                                                     │
│  ─────────                                                       │
│  HVC qualité insuffisante   Moyen   Élevé    · Fallback Codec2  │
│                                              · Itérations        │
│  HaLow portée < prévu       Bas     Moyen    · Ajouter répéteur │
│                                              · Passer en 1 MHz   │
│  Backhaul 5 GHz pas de LoS  Moyen   Élevé    · Relais TVWS      │
│                                              · Mât plus haut     │
│  Panne solaire (saison      Élevé   Faible   · Surdimensionner  │
│    des pluies)                               · Batterie 3 jours  │
│                                                                  │
│  HUMAINS                                                        │
│  ───────                                                         │
│  Faible adoption             Élevé  Critique  · Implication      │
│    utilisateurs                               leaders locaux     │
│                                              · Période gratuite  │
│  Vol/vandalisme équipement   Moyen   Élevé    · Installation     │
│                                              sécurisée (toit)    │
│                                              · Gardien local     │
│  Départ admin technique      Moyen   Élevé    · Former 2 par zone│
│                                              · Documentation     │
│                                                                  │
│  RÉGLEMENTAIRES                                                  │
│  ──────────────                                                   │
│  Blocage régulateur télécom  Faible  Critique  · Bande ISM =     │
│                                              libre partout       │
│                                              · Dialogue anticipé │
│  Starlink indisponible pays  Bas     Élevé    · 4G fallback      │
│                                              · TVWS alternatif   │
│                                                                  │
│  FINANCIERS                                                      │
│  ──────────                                                       │
│  Subvention refusée          Élevé   Variable  · Candidatures    │
│                                              multiples            │
│                                              · Bootstrapping     │
│  Inflation composants         Bas     Moyen    · Stock avance    │
│                                              · Alternatives      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 8.2 Plan de Continuité

En cas d'échec d'une phase :
- **Phase 1 échoue** → Itération technique, extension timeline +2 mois
- **Phase 2 échoue** → Changement de village pilote, ajustement du modèle
- **Phase 3 échoue** → Réduction scope (4 villages au lieu de 8), focus qualité
- **Phase 4 échoue** → Pause scale, consolidation, recherche financement additionnel

---

## 9. Pays Cibles Prioritaires

### 9.1 Critères de Priorisation

| Critère | Pondération |
|---------|:-----------:|
| Pénétration mobile mais coût élevé (> 5% revenu) | 30% |
| Stabilité politique et sécurité | 20% |
| Cadre réglementaire favorable (ISM libre, pas de blocage) | 20% |
| Présence de partenaires locaux (ONG, universités) | 15% |
| Langue française (facilite équipe projet) | 10% |
| Diaspora active (potentiel crowdfunding) | 5% |

### 9.2 Classement

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  🥇 BÉNIN                                                        │
│  · Cadre réglementaire favorable (ARCEP Bénin ouverte)          │
│  · Coût data élevé (1 Go = 3-5% revenu mensuel)                 │
│  · Stabilité politique                                           │
│  · Diaspora active                                               │
│  · Présence ONG françaises fortes                                │
│                                                                  │
│  🥈 SÉNÉGAL                                                      │
│  · Écosystème tech émergent (Dakar)                              │
│  · Stabilité politique                                           │
│  · Cadre réglementaire OK                                        │
│  · Coût data modéré mais inégalités fortes                       │
│                                                                  │
│  🥉 CÔTE D'IVOIRE                                                │
│  · Coût crédit élevé                                             │
│  · Bonne pénétration mobile                                      │
│  · Présence partenaires francophones                             │
│                                                                  │
│  4. MADAGASCAR                                                   │
│  · Zones rurales très isolées                                    │
│  · Coût data prohibitif                                          │
│  · Stabilité politique OK                                        │
│  · Faible densité → portée HaLow critique                        │
│                                                                  │
│  5. RÉPUBLIQUE DÉMOCRATIQUE DU CONGO                              │
│  · Besoins immenses (connectivité quasi nulle en rural)          │
│  · Défis logistiques et sécuritaires                             │
│  · Potentiel d'impact maximal                                    │
│  · Mais risque élevé → phase pilote ailleurs d'abord             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 9.3 Partenaires Potentiels par Pays

| Pays | Partenaire | Rôle |
|------|-----------|------|
| Bénin | Campus Numérique Francophone (AUF) | Formation, locaux |
| Sénégal | Sonatel (RSE), CTIC Dakar | Support tech |
| Côte d'Ivoire | Fonds NSIA, Fondation Orange CI | Financement |
| Madagascar | Telma (RSE), ONG locales | Logistique |
| RDC | MSF, UNICEF | Usage santé |

---

## 10. Stratégie de Passage à l'Échelle

### 10.1 Après l'Année 1

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  ANNÉE 2 : 100 VILLAGES (20 000 utilisateurs)                    │
│  ─────────────────────────────────────────                        │
│  · Modèle éprouvé, documentation complète                         │
│  · Formation de formateurs (cascade)                              │
│  · Production locale de boîtiers à l'échelle                     │
│  · Partenariat avec gouvernement pour reconnaissance légale     │
│                                                                  │
│  ANNÉE 3 : 500 VILLAGES (100 000 utilisateurs)                   │
│  ──────────────────────────────────────────                       │
│  · Réseau inter-États (villages frontaliers connectés)           │
│  · Plateforme de gestion cloud pour agrégation données           │
│  · Licence d'opérateur communautaire (si nécessaire)             │
│                                                                  │
│  ANNÉE 5 : 5000 VILLAGES (1 MILLION d'utilisateurs)              │
│  ────────────────────────────────────────────────                 │
│  · Standard de facto pour le rural en Afrique                    │
│  · Interconnexion avec réseaux nationaux (peering)              │
│  · Modèle économique mature : cotisations + services             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 10.2 Leviers de Scale

| Levier | Description |
|--------|-------------|
| **Franchise sociale** | Un village formé peut former le village voisin |
| **Open source** | Le code, les schémas, les manuels sont libres |
| **Production locale** | Assemblage boîtiers dans le pays (emploi local) |
| **Micro-crédit** | Les familles achètent le boîtier via micro-crédit |
| **KA PAY** | Monnaie communautaire autonome — cotisations, échanges, services (0% frais) |
| **Plaidoyer** | Reconnaissance par les régulateurs comme « réseau communautaire » |

### 10.3 Organisation Cible à l'Échelle

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  ORGANISATION À MATURITÉ (ANNÉE 3+)                              │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  HARMONIC NETWORK FOUNDATION (entité à but non lucratif)    │ │
│  │  ───────────────────────────────────────────────────────    │ │
│  │  · Développement logiciel (HVC, HHD2, PWA)                  │ │
│  │  · R&D (nouvelles fonctionnalités)                           │ │
│  │  · Certification des administrateurs techniques              │ │
│  │  · Plaidoyer international                                   │ │
│  │  · Financement : subventions + dons                          │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                             │                                    │
│     ┌───────────────────────┼───────────────────────┐           │
│     │                       │                       │           │
│  ┌──┴────────────────┐ ┌───┴──────────────┐ ┌──────┴─────────┐ │
│  │  COOPÉRATIVE      │ │  COOPÉRATIVE     │ │  COOPÉRATIVE   │ │
│  │  RÉGION NORD      │ │  RÉGION CENTRE   │ │  RÉGION SUD    │ │
│  │  ─────────────    │ │  ──────────────  │ │  ────────────  │ │
│  │  · 20 villages    │ │  · 15 villages   │ │  · 18 villages  │ │
│  │  · 2 admins tech  │ │  · 2 admins tech │ │  · 2 admins     │ │
│  │  · 1 passerelle   │ │  · 1 passerelle  │ │  · 1 passerelle │ │
│  │    Starlink       │ │    Starlink      │ │    Starlink     │ │
│  │  · Cotisations    │ │  · Cotisations   │ │  · Cotisations  │ │
│  └───────────────────┘ └──────────────────┘ └─────────────────┘ │
│                                                                  │
│  CHAQUE COOPÉRATIVE EST AUTONOME FINANCIÈREMENT.                 │
│  LA FONDATION FOURNIT LE LOGICIEL, LA FORMATION, LE SUPPORT.    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Annexes

### A. Check-liste de Déploiement (par village)

```
☐ Sélection du village (critères validés)
☐ Rencontre chef du village + leaders
☐ Accord communautaire signé
☐ Identification du Gardien
☐ Identification de l'Animateur
☐ Étude de ligne de vue (backhaul 5 GHz)
☐ Commande matériel
☐ Installation mât + panneau solaire + batterie
☐ Installation AP HaLow
☐ Installation antenne backhaul
☐ Installation passerelle LoRa
☐ Test de couverture
☐ Distribution boîtiers + formation utilisateurs
☐ Premier appel officiel
☐ Remise manuel du Gardien
☐ Support intensif (1 semaine)
☐ Passage en mode normal
```

### B. Contacts et Ressources

| Ressource | URL / Contact |
|-----------|--------------|
| Spécification technique | SPEC_TECHNIQUE_RESEAU_HARMONIQUE.md |
| Code source HVC | À créer |
| Code source HHD2 | engine/multimodal/harmonic_codec.py |
| Module HaLow Morse Micro | https://www.morsemicro.com/ |
| Antennes Ubiquiti | https://www.ui.com/ |
| Projet LibreRouter | https://librerouter.org/ |
| Codec2 | https://github.com/drowe67/codec2 |
| Meshtastic | https://meshtastic.org/ |
| Starlink | https://www.starlink.com/ |

### C. Acronymes

| Acronyme | Signification |
|----------|---------------|
| RTHC | Réseau Télécom Harmonique Communautaire |
| HVC | Harmonic Voice Codec |
| HHD2 | Harmonic-HCV Dictionary Codec v2 |
| HaLow | IEEE 802.11ah |
| LoS | Line of Sight |
| KPI | Key Performance Indicator |
| PWA | Progressive Web App |
| RSE | Responsabilité Sociétale des Entreprises |
| AFD | Agence Française de Développement |
| GIZ | Deutsche Gesellschaft für Internationale Zusammenarbeit |

---

*Plan de déploiement v1.0 — Juillet 2026 — Projet Univers Harmonique*
