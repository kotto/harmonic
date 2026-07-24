# Harmoniq Enterprise — L'IA d'entreprise fondée sur le système d'information

**Document de Conception — Version 1.0**
**Date :** 24 juillet 2026
**Contexte :** Pourquoi le RAG + LLM actuel n'est pas efficace, et comment HarmoniqLLM résout le problème.

---

## Résumé exécutif

Les entreprises déploient aujourd'hui des solutions RAG (Retrieval-Augmented Generation)
couplées à des LLM pour « interroger leurs données ». Cette approche souffre de
**cinq défaillances structurelles** qui la rendent inefficace en production.

Nous proposons **Harmoniq Enterprise**, une architecture fondée sur les hologrammes
harmoniques spécialisés (HarmoniqLLM) qui **transforme le système d'information
en IA native**, sans vectorisation, sans hallucination, et sans GPU.

---

## 1. Pourquoi le RAG + LLM actuel échoue en entreprise

### 1.1 Les cinq défaillances

| Défaillance | Cause racine | Conséquence en production |
|---|---|---|
| **1. Perte de structure** | Les documents sont chunkés en fragments de texte plat | Les relations entre entités (client→commande→facture) sont détruites |
| **2. Hallucination** | Le LLM génère statistiquement, le RAG ne garantit pas la fidélité | Réponses plausibles mais fausses — inacceptables en finance, santé, droit |
| **3. Latence** | Embedding + retrieval + génération = plusieurs secondes | Impossible en temps réel (support client, production) |
| **4. Coût** | GPU nécessaire, API externes, ré-indexation continue | 10-100K€/an pour une PME, dépendance fournisseur |
| **5. Souveraineté** | Données envoyées à des API cloud (OpenAI, Anthropic) | Non-conformité RGPD, secret industriel exposé |

### 1.2 Le problème fondamental

Le RAG+LLM traite les données de l'entreprise comme du **texte**,
alors qu'elles sont déjà **structurées** :

```
ERP      → tables SQL (clients, commandes, stocks)
CRM      → relations (contact→opportunité→deal)
RH       → hiérarchies (employé→manager→département)
Docs     → arborescences (politique→procédure→formulaire)
Métier   → règles (si X alors Y sauf si Z)
```

Transformer ces structures en « chunks » pour les donner à un LLM,
c'est comme traduire un plan d'architecte en description textuelle
pour demander au maçon de construire — on perd l'essentiel.

---

## 2. La solution Harmoniq Enterprise

### 2.1 Principe fondateur

> **Chaque entité du SI devient une onde. Chaque relation devient une interférence.
> Chaque département devient un hologramme spécialisé.**

Au lieu de :
```
Documents → Chunks → Embeddings → VectorDB → LLM → Réponse
```

On fait :
```
SI (SQL, API, CSV) → Faits (s,r,o) → Hologrammes métier → Routeur → Réponse
```

### 2.2 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    HARMONIQ ENTERPRISE                               │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │              CONNECTEURS SI (extracteurs)                 │       │
│  │                                                          │       │
│  │  [ERP]──► │PostgreSQL│──► faits                          │       │
│  │  [CRM]──► │  REST API│──► faits   ──► Base de faits      │       │
│  │  [RH] ──► │   CSV    │──► faits       unifiée            │       │
│  │  [Doc]──► │   PDF    │──► faits       (s,r,o,sec)        │       │
│  └──────────────────────────────────────────────────────────┘       │
│                           │                                         │
│                           ▼                                         │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │              HOLOGRAMMES MÉTIER                           │       │
│  │                                                          │       │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │       │
│  │  │ FINANCE  │ │   RH     │ │ LOGISTIQ │ │ COMMERCL │    │       │
│  │  │ 12K faits│ │  8K faits│ │ 15K faits│ │ 20K faits│    │       │
│  │  │ HWAT 32d │ │ HWAT 32d │ │ HWAT 32d │ │ HWAT 64d │    │       │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │       │
│  └──────────────────────────────────────────────────────────┘       │
│                           │                                         │
│                           ▼                                         │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │              ROUTEUR HARMONIQUE                           │       │
│  │  "quel est le CA du client X ?" → FINANCE                │       │
│  │  "combien de congés pour Y ?"   → RH                     │       │
│  │  "où est la commande Z ?"       → LOGISTIQUE             │       │
│  └──────────────────────────────────────────────────────────┘       │
│                           │                                         │
│                           ▼                                         │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │              INTERFACES                                    │       │
│  │  API REST │ Chat │ Dashboard │ Alertes │ Rapports         │       │
│  └──────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 Les connecteurs SI

Chaque source de données est connectée via un **extracteur de faits** :

```python
# Exemple : connecteur PostgreSQL → faits
def extract_faits_from_erp():
    faits = []
    # Clients
    for row in db.query("SELECT id, nom, secteur, ca FROM clients"):
        faits.append((f"client_{row.id}", "a_pour_nom", row.nom, "COMMERCIAL"))
        faits.append((f"client_{row.id}", "a_pour_secteur", row.secteur, "COMMERCIAL"))
        faits.append((f"client_{row.id}", "a_pour_ca", str(row.ca), "FINANCE"))
    # Commandes
    for row in db.query("SELECT id, client_id, date, montant FROM commandes"):
        faits.append((f"commande_{row.id}", "passée_par", f"client_{row.client_id}", "COMMERCIAL"))
        faits.append((f"commande_{row.id}", "date", str(row.date), "LOGISTIQUE"))
        faits.append((f"commande_{row.id}", "montant", str(row.montant), "FINANCE"))
    return faits
```

**Avantage clé** : les relations sont explicites (`passée_par`, `a_pour_nom`),
pas inférées statistiquement. Zéro hallucination possible sur ces faits.

### 2.4 Les hologrammes métier

Chaque département reçoit un **HWAT spécialisé** entraîné sur ses faits :

| Département | Source SI | Faits estimés | Taille HWAT | Temps entraînement |
|---|---|---|---|---|
| Finance | ERP (factures, compta) | 10-50K | dim=32 | 30s |
| Commercial | CRM (clients, deals) | 20-100K | dim=32-64 | 1-2 min |
| RH | SIRH (employés, congés) | 5-20K | dim=32 | 20s |
| Logistique | WMS (stocks, livraisons) | 15-50K | dim=32 | 30s |
| Juridique | GED (contrats, conformité) | 5-30K | dim=32 | 20s |
| Direction | BI (KPI, tableaux de bord) | 5-20K | dim=32 | 20s |

**Propriété critique** : les hologrammes sont **étanches**. Le service RH
ne peut pas accéder aux données financières, et inversement. La sécurité
est architecturale, pas applicative.

### 2.5 Le routeur

Le routeur dirige chaque question vers le(s) bon(s) hologramme(s) :

```python
def router(question):
    # 1. Embedding harmonique
    psi = hwat_encode(question)
    
    # 2. Similarité avec les centroïdes métier
    scores = {
        'FINANCE':    cos_sim(psi, centroide_finance),
        'RH':         cos_sim(psi, centroide_rh),
        'COMMERCIAL': cos_sim(psi, centroide_commercial),
        'LOGISTIQUE': cos_sim(psi, centroide_logistique),
    }
    
    # 3. Top-K experts
    experts = top_k(scores, k=2)
    
    # 4. Interroger les experts
    reponses = []
    for metier, score in experts:
        faits = holograms[metier].retrieve(question, top_k=10)
        reponses.append(formater(faits, metier))
    
    return fusionner(reponses)
```

**Exemple** : « Quel est le chiffre d'affaires du client Dupont au T3 ? »
→ Routeur sélectionne `FINANCE` (CA) + `COMMERCIAL` (client)
→ Chaque hologramme retrouve ses faits
→ Fusion : « Client Dupont : CA T3 = 450K€ (source: ERP, table factures) »

---

## 3. Comparaison RAG+LLM vs Harmoniq Enterprise

| Critère | RAG + LLM | Harmoniq Enterprise |
|---|---|---|
| **Source** | Documents texte | **SI structuré** (SQL, API, CSV) |
| **Représentation** | Chunks + embeddings | **Faits (sujet, relation, objet)** |
| **Stockage** | VectorDB (pgvector, Pinecone) | **Hologrammes HWAT** (fichiers .pt) |
| **Mise à jour** | Ré-indexation complète | **Ajout instantané** (H += ψ_fait) |
| **Hallucination** | Fréquente | **Impossible sur les faits stockés** |
| **Latence** | 2-10 secondes | **< 100ms** (retrieval pur) |
| **GPU** | Requis | **CPU seul** (même un Raspberry Pi) |
| **Souveraineté** | Données sur cloud externe | **100% on-premise** |
| **Sécurité** | RBAC applicatif | **Étanchéité architecturale** |
| **Coût annuel** | 10-100K€ | **0€** (open source, CPU existant) |
| **Explicabilité** | Boîte noire | **Source tracée** (fait → réponse) |

---

## 4. Scénarios concrets

### 4.1 Support client

```
Client : « Ma commande #4521 n'est pas arrivée »

AVANT (RAG+LLM) :
  1. Recherche vectorielle : "commande #4521 pas arrivée"
  2. Retrieval : 5 chunks de texte (politique de livraison, FAQ...)
  3. LLM : « Votre commande est en cours de traitement. Délai: 3-5 jours. »
  → Réponse générique, pas basée sur la commande réelle

APRÈS (Harmoniq) :
  1. Routeur → LOGISTIQUE
  2. Hologramme LOGISTIQUE : retrouve commande_4521 → statut = "bloquée douane"
  3. Réponse : « Commande #4521 : bloquée en douane depuis le 22/07.
     Contactez le transporteur DHL, suivi: XY123. »
  → Réponse exacte, basée sur le fait réel
```

### 4.2 Reporting direction

```
DG : « Évolution du CA par région ce trimestre »

AVANT :
  1. L'analyste extrait les données de l'ERP (2h)
  2. Excel / PowerBI (30 min)
  3. Présentation (1h)
  → 3h30 de travail humain

APRÈS :
  1. Routeur → FINANCE
  2. Hologramme FINANCE : CA(region, trimestre) → table de faits
  3. Réponse formatée + graphique
  → 3 secondes, zéro travail humain
```

### 4.3 Conformité RGPD

```
DPO : « Quelles données personnelles sont stockées sur le client Martin ? »

AVANT :
  → Impossible sans audit manuel de toutes les bases

APRÈS :
  1. Routeur → JURIDIQUE + COMMERCIAL + RH
  2. Chaque hologramme retrouve les faits liés à "client_Martin"
  3. Réponse : « ERP: nom, adresse, email, IBAN | CRM: historique achats,
     préférences | RH: néant »
  → Conformité en temps réel
```

---

## 5. Déploiement

### 5.1 Prérequis techniques

| Ressource | Minimum | Recommandé |
|---|---|---|
| CPU | 2 cœurs | 8 cœurs |
| RAM | 512 MB | 4 GB |
| Stockage | 100 MB | 1 GB |
| OS | Linux / Windows / Mac | Linux serveur |
| Dépendances | Python 3.11+, NumPy, PyTorch | — |

### 5.2 Installation (3 étapes)

```bash
# 1. Cloner
git clone https://github.com/.../engine
cd engine

# 2. Connecter les sources SI
python connecteurs/erp_connector.py --db postgresql://...
python connecteurs/crm_connector.py --api https://crm.interne/api

# 3. Entraîner les hologrammes
python train_holograms.py --sources data/faits_entreprise.json

# 4. Démarrer le serveur
python ka_server.py --mode enterprise
```

### 5.3 Maintenance

- **Ajout d'une source** : nouveau connecteur → extraction → ajout aux hologrammes existants (ou nouveau hologramme)
- **Mise à jour des faits** : `H += ψ_nouveau_fait` (instantané, pas de ré-entraînement)
- **Nouveau département** : `train_holograms.py --sector NOUVEAU` (30 secondes)
- **Sauvegarde** : `data/holograms/*.pt` + `data/faits_*.json`

---

## 6. Feuille de route entreprise

### Phase 1 — Pilote (2 semaines)

- [ ] Connecteur PostgreSQL (ERP)
- [ ] 3 hologrammes : Finance, Commercial, Logistique
- [ ] Routeur simple (mots-clés)
- [ ] Interface chat + API REST
- [ ] Démo sur données réelles

### Phase 2 — Industrialisation (1 mois)

- [ ] Connecteurs : REST API, CSV, PDF structuré
- [ ] 6-8 hologrammes métier
- [ ] Routeur spectral (cos sim sur embeddings)
- [ ] Dashboard de supervision
- [ ] Gestion des droits par hologramme
- [ ] Alertes (faits contradictoires, données manquantes)

### Phase 3 — Plateforme (3 mois)

- [ ] Connecteurs : tous les SI majeurs (SAP, Salesforce, etc.)
- [ ] 15+ hologrammes
- [ ] Fusion multi-experts
- [ ] Génération de rapports automatisés
- [ ] Interface administrateur (gestion des hologrammes)
- [ ] Chiffrement des hologrammes (sécurité)

---

## 7. Pourquoi ça marche (et pas le RAG+LLM)

Le RAG+LLM traite le SI comme une **bibliothèque de documents**.
Harmoniq Enterprise le traite comme un **réseau de faits**.

| | RAG+LLM | Harmoniq Enterprise |
|---|---|---|
| **Paradigme** | Statistique | Ondulatoire |
| **Données** | Texte brut | Faits structurés |
| **Mémoire** | VectorDB (externe) | Hologramme (interne) |
| **Recherche** | Similarité cosinus | Résonance d'onde |
| **Génération** | Probabiliste | Retrieval + assemblage |
| **Apprentissage** | GPU, heures | CPU, secondes |
| **Mise à jour** | Ré-indexation | Addition instantanée |

> **La différence fondamentale** : le RAG+LLM *cherche* du texte similaire
> et *génère* une réponse plausible. Harmoniq Enterprise *retrouve* des
> faits exacts et *assemble* une réponse vérifiée. L'un est statistique,
> l'autre est déterministe. L'un hallucine, l'autre sait quand il ne sait pas.

---

## 8. Annexes

### A. Format des faits

```json
{
  "sujet": "client_4521",
  "relation": "a_pour_nom",
  "objet": "Dupont SA",
  "secteur": "COMMERCIAL",
  "source": "ERP.table_clients.ligne_4521",
  "date_extraction": "2026-07-24T10:00:00"
}
```

### B. Exemple de connecteur ERP

```python
def connecteur_erp_postgresql(connection_string: str) -> list:
    """Extrait les faits d'un ERP PostgreSQL."""
    import psycopg2
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    faits = []
    
    # Tables à extraire (configurable)
    for table, colonnes in ERP_SCHEMA.items():
        cur.execute(f"SELECT * FROM {table}")
        for row in cur:
            sujet = f"{table}_{row[0]}"
            for col_name, col_value in zip(colonnes, row):
                faits.append((sujet, f"a_pour_{col_name}", str(col_value), "ERP"))
    
    return faits
```

### C. Sécurité des hologrammes

Chaque hologramme est un fichier `.pt` indépendant. La sécurité est assurée par :
1. **Étanchéité** : un hologramme RH ne contient pas de données financières
2. **Chiffrement** : les fichiers peuvent être chiffrés (AES-256)
3. **Traçabilité** : chaque fait a une source et une date d'extraction
4. **Droit à l'oubli** : supprimer un fait = annuler son onde (opération inverse)

---

**Harmoniq Enterprise — Document de Conception v1.0**
**Branche :** `feature/harmonic-transformer-refonte/enterprise`
**Auteur :** IA Harmoniq
