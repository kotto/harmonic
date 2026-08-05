# Cahier des Charges — KA Enterprise

## L'IA d'Entreprise qui n'hallucine pas, parce qu'elle n'invente rien

---

## 1. Contexte : Pourquoi le marché est mûr

### 1.1 L'impasse actuelle : RAG + LLM

Les entreprises qui déploient l'IA aujourd'hui suivent toutes le même schéma :

```
Documents internes → Vectorisation (embeddings) → Base vectorielle
Question utilisateur → Embedding → Recherche vectorielle → Top-K chunks
Top-K chunks + Question → LLM → Réponse
```

Ce schéma (RAG — Retrieval Augmented Generation) présente **trois défauts structurels** :

| Problème | Conséquence |
|---|---|
| **Le LLM peut ignorer les chunks** | Il génère une réponse qui « sonne juste » mais contredit les documents internes |
| **Le LLM peut halluciner** | Même avec les bons chunks, il invente des chiffres, des noms, des procédures |
| **Les données sortent de l'entreprise** | Appels API vers OpenAI/Anthropic/Google → les documents confidentiels transitent par des serveurs tiers |

**Résultat** : 73% des projets RAG en entreprise n'atteignent pas la production (source : Gartner 2025). La raison principale : le manque de confiance dans les réponses.

### 1.2 La promesse de KA Enterprise

KA Enterprise ne fait pas de RAG. Il ne vectorise pas. Il n'appelle pas de LLM externe.

**Il spécialise l'IA directement sur les données de l'entreprise par superposition holographique.**

```
Documents internes → HolographicEncoder → H_entreprise ∈ ℂ⁵¹²
Question utilisateur → Encodage ψ → Résonance dans H_entreprise → Réponse
```

La réponse n'est **pas générée** — elle est **retrouvée par résonance** dans l'hologramme. Si l'information n'est pas dans les documents, KA dit « je ne sais pas » au lieu d'inventer.

---

## 2. Vision du Produit

### 2.1 Principe fondateur

> **Chaque entreprise possède son propre hologramme, comme chaque utilisateur grand public possède le sien dans KA Mobile. La spécialisation est la même — seules l'échelle et la gouvernance diffèrent.**

### 2.2 Trois piliers

| Pilier | Signification |
|---|---|
| **Spécialisation holographique** | L'IA est entraînée UNIQUEMENT sur les données de l'entreprise. Pas de modèle généraliste qui « sait déjà tout ». |
| **Souveraineté totale** | Tout tourne dans l'infrastructure de l'entreprise. Zéro appel externe. Zéro fuite de données. |
| **Déterminisme absolu** | Même question + mêmes documents = même réponse. Auditabilité complète. Traçabilité SHA256. |

### 2.3 Ce que KA Enterprise n'est PAS

| N'est PAS | Parce que |
|---|---|
| Un chatbot généraliste | Il ne répond qu'à partir des documents ingérés |
| Un RAG amélioré | Il n'utilise pas de retrieval + génération |
| Un fine-tuning de LLM | Il n'y a pas de LLM — l'hologramme remplace tout |
| Une API vers OpenAI | Zéro dépendance externe |
| Un assistant « qui sait tout » | Il sait exactement ce que l'entreprise lui a appris, et rien d'autre |

---

## 3. Architecture Fonctionnelle

### 3.1 Le Cycle de Vie d'un Hologramme d'Entreprise

```
┌─────────────────────────────────────────────────────────────┐
│                     PHASE 1 : INGESTION                      │
│                                                              │
│  Documents (PDF, DOCX, XLSX, CSV, TXT, HTML, emails...)     │
│       │                                                      │
│       ▼                                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Extraction du texte + structuration                 │   │
│  │  Découpage en unités de connaissance (faits)         │   │
│  │  Nettoyage, dédoublonnage, normalisation            │   │
│  └──────────────────────────────────────────────────────┘   │
│       │                                                      │
│       ▼                                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  HolographicEncoder                                 │   │
│  │  Chaque fait → ψᵢ ∈ ℂ⁵¹² (FNV-1a + φ-spacing)      │   │
│  │  H_entreprise = Σ ψᵢ  (superposition holographique) │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  → H_entreprise est UN tenseur de 512 dimensions             │
│  → Il contient TOUTE la connaissance de l'entreprise         │
│  → Taille : ~4 Ko quel que soit le nombre de documents       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     PHASE 2 : REQUÊTE                        │
│                                                              │
│  Question utilisateur                                        │
│       │                                                      │
│       ▼                                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  HolographicEncoder : question → ψ_question          │   │
│  └──────────────────────────────────────────────────────┘   │
│       │                                                      │
│       ▼                                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Résonance holographique                            │   │
│  │  Réponse = H_entreprise ⊘ ψ_question                │   │
│  │  (corrélation circulaire — unbinding)               │   │
│  └──────────────────────────────────────────────────────┘   │
│       │                                                      │
│       ▼                                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ConsciousFilter (φ-validation)                     │   │
│  │  Si le score de résonance < seuil → "Je ne sais pas"│   │
│  │  Si le score ≥ seuil → réponse + sources            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Multi-Tenant par Conception

Chaque département, équipe, ou projet possède son **propre hologramme** :

```
┌─────────────────────────────────────────────┐
│              KA Enterprise Core              │
│                                              │
│  Tenant "Finance"     → H_finance ∈ ℂ⁵¹²    │
│  Tenant "RH"          → H_rh ∈ ℂ⁵¹²         │
│  Tenant "R&D"         → H_rd ∈ ℂ⁵¹²         │
│  Tenant "Juridique"   → H_juridique ∈ ℂ⁵¹²  │
│  ...                                         │
│                                              │
│  H_global = H_finance ⊕ H_rh ⊕ H_rd ⊕ ...  │
│  (⊕ = superposition avec isolation)         │
└─────────────────────────────────────────────┘
```

**Propriété clé** : Un employé du service Finance ne peut PAS accéder aux connaissances du service RH — les hologrammes sont isolés dans l'espace complexe (φ-orthogonalité).

### 3.3 Gouvernance des Hologrammes

| Fonction | Description |
|---|---|
| **Création** | Un administrateur crée un hologramme pour un département |
| **Ingestion** | Upload de documents → mise à jour incrémentale de H |
| **Permissions** | Qui peut interroger quel hologramme |
| **Versioning** | Chaque mise à jour de H est versionnée (H_v1, H_v2...) |
| **Audit** | Toute requête est journalisée (qui, quand, quel hologramme, quelle réponse) |
| **Expiration** | Les hologrammes peuvent avoir une date d'expiration (conformité) |
| **Fusion** | Deux hologrammes peuvent être fusionnés (H_a+b = H_a + H_b) |
| **Export** | Un hologramme peut être exporté (backup, transfert) |

---

## 4. Spécifications Techniques

### 4.1 Formats d'Ingestion Supportés

| Format | Priorité | Notes |
|---|---|---|
| PDF | P0 | Extraction texte + tableaux + métadonnées |
| DOCX | P0 | Y compris .doc (via conversion) |
| XLSX / CSV | P0 | Données structurées → faits |
| TXT / Markdown | P0 | Texte brut |
| HTML | P1 | Pages web internes (intranet, wiki) |
| Emails (.eml, .msg) | P1 | Conversations, décisions |
| Images (PNG, JPG) | P2 | OCR + extraction texte |
| Audio (WAV, MP3) | P2 | Transcription ASR → texte |
| Bases SQL | P2 | Export → faits structurés |
| APIs REST | P2 | Ingestion programmatique |

### 4.2 Performances Cibles

| Métrique | Cible | Notes |
|---|---|---|
| Ingestion | 10 000 pages / heure | Sur CPU 8 cœurs |
| Temps de réponse | < 100 ms | Après encodage de la question |
| Hologrammes simultanés | 1 000+ | Sans dégradation |
| Utilisateurs simultanés | 10 000+ | Avec load balancing |
| Taille d'un hologramme | ~4 Ko | Quel que soit le volume ingéré |
| Empreinte mémoire totale | < 2 Go | Pour 1 000 hologrammes |

### 4.3 Sécurité

| Exigence | Implémentation |
|---|---|
| **Chiffrement au repos** | AES-256-GCM sur les hologrammes stockés |
| **Chiffrement en transit** | TLS 1.3 obligatoire |
| **Authentification** | SSO (SAML 2.0, OIDC, LDAP) |
| **Autorisation** | RBAC (Admin, Manager, Reader, Auditor) |
| **Clés API** | Par tenant, avec quotas et expiration |
| **Audit trail** | Journal immuable de toutes les requêtes |
| **Anonymisation** | PII masquée dans les logs |
| **RGPD** | Droit à l'oubli = suppression d'un fait dans H |
| **Zero Trust** | Aucune confiance implicite entre tenants |

---

## 5. Interface Utilisateur

### 5.1 Dashboard Administrateur

```
┌──────────────────────────────────────────────────────────────┐
│  🏢 KA Enterprise — Admin                          [👤 Profil] │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  📊 APERÇU                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ 12       │ │ 1 247    │ │ 98.7%    │ │ 0            │   │
│  │ Tenants  │ │ Questions│ │ Précision│ │ Hallucinations│   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
│                                                              │
│  🏢 TENANTS                                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Finance      H: ████████░ (8 421 faits)  [Gérer]    │   │
│  │ RH           H: ██████░░░ (5 203 faits)  [Gérer]    │   │
│  │ R&D          H: ████████████ (14 567 faits) [Gérer] │   │
│  │ Juridique    H: ████░░░░ (3 102 faits)   [Gérer]    │   │
│  │ [+ Créer un tenant]                                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  📤 INGESTION                                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Glissez vos documents ici                            │   │
│  │  PDF, DOCX, XLSX, CSV, TXT, HTML, EML...             │   │
│  │  [Sélectionner des fichiers]  [Dossier entier]        │   │
│  │  Tenant cible: [Finance ▾]                            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  📋 DERNIÈRES REQUÊTES (filtrées par tenant)                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 14:32 | Finance    | "Quel est le budget Q3 ?"       │   │
│  │ 14:31 | RH         | "Procédure congés payés"        │   │
│  │ 14:30 | R&D        | "Spécifications API v2"         │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 Interface Utilisateur (par tenant)

L'utilisateur se connecte, sélectionne son tenant (ou y est automatiquement assigné), et pose ses questions. L'interface est simplifiée :

- **Chat** : conversation naturelle avec l'IA spécialisée
- **Sources** : pour chaque réponse, les documents sources sont cités
- **Feedback** : 👍/👎 pour améliorer la précision
- **Export** : possibilité d'exporter la réponse au format PDF

---

## 6. Déploiement

### 6.1 Modes de Déploiement

| Mode | Description | Cible |
|---|---|---|
| **On-premise** | Installation sur les serveurs de l'entreprise | Grands groupes, défense, santé |
| **VPC (Cloud privé)** | Instance dédiée chez AWS/Azure/GCP | ETI, PME |
| **Air-gapped** | Réseau complètement isolé (aucune connexion externe) | Défense, gouvernement |
| **Docker / Kubernetes** | Conteneurisation standard | Équipes techniques |

### 6.2 Prérequis Techniques

| Ressource | Minimum | Recommandé |
|---|---|---|
| CPU | 4 cœurs | 16 cœurs |
| RAM | 8 Go | 32 Go |
| Stockage | 20 Go + documents | SSD 100 Go+ |
| GPU | **Aucun** | Aucun |
| OS | Linux (Ubuntu 22.04+) | RHEL 9+ |

---

## 7. Feuille de Route

### Phase 1 — Fondation (Mois 1-2)
- [x] Moteur d'encodage holographique (HolographicEncoder)
- [x] Ingestion PDF, DOCX, TXT
- [x] Interface administrateur (tenants, ingestion)
- [ ] Authentification SSO (SAML/OIDC)
- [ ] Chiffrement AES-256 des hologrammes
- [ ] Journal d'audit immuable

### Phase 2 — Spécialisation (Mois 2-3)
- [ ] Ingestion XLSX/CSV (données structurées)
- [ ] Ingestion emails, HTML, images OCR
- [ ] Versioning des hologrammes
- [ ] Fusion/séparation d'hologrammes
- [ ] API d'ingestion programmatique
- [ ] Tableau de bord de précision par tenant

### Phase 3 — Enterprise Ready (Mois 3-4)
- [ ] Haute disponibilité (load balancing, failover)
- [ ] Déploiement Kubernetes (Helm chart)
- [ ] Intégration SIEM (Splunk, ELK)
- [ ] Certification RGPD / SOC 2
- [ ] Support multi-langue (FR, EN, DE, ES)
- [ ] Marketplace d'hologrammes pré-entraînés (sectoriels)

---

## 8. Modèle Économique

| Plan | Prix | Utilisateurs | Tenants |
|---|---|---|---|
| **Starter** | 990€ / mois | 50 | 3 |
| **Business** | 2 490€ / mois | 250 | 10 |
| **Enterprise** | 4 990€ / mois | 1 000 | 25 |
| **Unlimited** | Sur devis | Illimité | Illimité |

**Inclus dans tous les plans** :
- Installation on-premise ou cloud privé
- Mise à jour continue des hologrammes
- Support technique 8h/5j (Business: 24h/7j)
- API REST complète
- Authentification SSO
- Journal d'audit

---

## 9. Ce qui différencie KA Enterprise de TOUT ce qui existe

| | RAG + LLM | Fine-tuning LLM | **KA Enterprise** |
|---|---|---|---|
| **Base** | Recherche + génération | Poids ajustés | **Hologramme ℂ⁵¹²** |
| **Hallucinations** | 3-15% | 1-5% | **0% (déterministe)** |
| **Données externes** | Oui (API LLM) | Pendant l'entraînement | **Jamais** |
| **Explainabilité** | Boîte noire | Boîte noire | **Sources citées** |
| **Mise à jour** | Ré-indexation | Ré-entraînement | **Ingestion incrémentale** |
| **Coût par requête** | 0,01-0,06 € | 0,001-0,01 € | **0 €** |
| **GPU requis** | Oui (inférence) | Oui (entraînement) | **Non** |
| **Taille du modèle** | 7-70 Go | 7-70 Go | **4 Ko par hologramme** |
| **Multi-tenant** | Complexe | Très complexe | **Natif (φ-orthogonalité)** |

---

> **KA Enterprise ne fait pas mieux le RAG. Il le remplace.**
>
> *Un hologramme par entreprise. Zéro hallucination. Souveraineté totale.*
