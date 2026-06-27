# Documentation commerciale & technique — IA fiable (déterminisme + mode vérifié)
Date: 2026-05-14

## 1) Positionnement
### Proposition de valeur
- **Fiabilité mesurable**: mêmes entrées ⇒ mêmes sorties (déterminisme) + empreinte reproductible (`response_id`).
- **Mode vérifié**: aucune affirmation “externe” sans source; **citations** quand sources fournies; **abstention structurée** sinon.
- **Traçabilité**: politique de réponse + métriques (cache_hit, policy, sources_count, etc.) exploitables pour audit et RCA.

### Promesse formulable (sans surpromesse)
- À éviter: “0 hallucination universel”.
- À revendiquer: **“0 assertion non sourcée en mode vérifié”** + “déterminisme auditable”.

## 2) Capacités clés (communes à tous les secteurs)
- **Modes**
  - *Standard*: meilleure utilité générale (sans contrainte de sources).
  - *Vérifié*: réponse uniquement à partir de sources; sinon abstention structurée.
- **Artefacts**
  - `response_id` reproductible (hash stable entrée+params+sources+version).
  - `citations[]` structurées.
  - `metrics{}`: `policy`, `cache_hit`, `deterministic_lock`, `sources_count`, etc.
- **Contrôles**
  - Verrou déterministe (température forcée à 0 côté serveur).
  - Cache déterministe (prompt+params ⇒ sortie identique).

## 3) Grille transversale — cas d’usage typiques (fiabilité)
Chaque cas d’usage est proposé en 2 variantes: *Standard* (productivité) et *Vérifié* (conformité).

### A. Synthèse & extraction (documents)
- Entrées: PDF/notes/rapports + annexes.
- Sorties attendues: résumé structuré + extraction champs + anomalies + citations.
- Métriques: taux de champs extraits corrects, taux d’assertions sourcées, temps de traitement.

### B. QA sur référentiels internes (policies, procédures)
- Entrées: procédures internes, directives, manuel qualité.
- Sorties attendues: réponse + références aux sections + checklist d’exécution.
- Métriques: taux de réponses avec citations valides; taux d’abstentions utiles (quand doc manque).

### C. Aide à la décision “assistée, pas automatique”
- Entrées: dossier + contraintes + sources.
- Sorties attendues: options + risques + critères + recommandations conditionnelles.
- Métriques: couverture des critères, cohérence, absence d’éléments non sourcés.

## 4) Santé — grille de cas d’usage
### Objectif secteur
Réduire le risque clinique et administratif via **réponses traçables** et **non-inventives**.

#### Cas d’usage S1 — Synthèse de dossier (administratif / RCP)
- Entrées: compte-rendu, biologie, imagerie (texte), lettres.
- Mode vérifié: synthèse + champs structurés + citations vers sources.
- Démo: fournir 3 documents; demander une synthèse + “drapeaux rouges”.
- KPI: 100% des affirmations cliniques citées; 0 élément ajouté hors sources.

#### Cas d’usage S2 — Conformité protocole (procédure interne)
- Entrées: protocole établissement + checklists.
- Mode vérifié: réponse sous forme de checklist + références.
- KPI: taux de correspondance section→réponse; 0 recommandation hors protocole.

#### Cas d’usage S3 — Préparation consentement / information patient
- Entrées: procédure + fiche HAS/établissement.
- Mode vérifié: reformulation en langage patient + citations + avertissements “non médical”.
- KPI: lisibilité, conformité, absence d’invention (dosages/chiffres).

#### Cas d’usage S4 — Codage PMSI / facturation (selon corpus fourni)
- Entrées: règles internes + exemples.
- Mode vérifié: suggestions + incertitudes + citations.
- KPI: précision des codes proposés sur dataset de référence.

## 5) Finance — grille de cas d’usage
### Objectif secteur
Réduire risque réglementaire (AMF/ACPR/SEC…), risque modèle, et risque opérationnel.

#### Cas d’usage F1 — Analyse KYC/KYB (dossier client)
- Entrées: dossier client + politique KYC interne.
- Mode vérifié: résumé + points manquants + citations vers docs internes.
- KPI: taux de “missing items” corrects; 0 affirmation non sourcée.

#### Cas d’usage F2 — Revue de politiques (ex: AML)
- Entrées: politique + procédures + logs/audit.
- Mode vérifié: gap analysis + recommandations limitées au référentiel.
- KPI: couverture des exigences, traçabilité par section.

#### Cas d’usage F3 — Contrôle 1st line / 2nd line (RCSA)
- Entrées: contrôles + risques + incidents.
- Mode vérifié: matrice risques/contrôles + citations.
- KPI: cohérence et complétude; 0 “contrôle inventé”.

#### Cas d’usage F4 — Analyse rapports (10-K/URD) (si sources fournies)
- Entrées: extraits, sections, chiffres.
- Mode vérifié: synthèse + citations + identification d’incertitudes.
- KPI: 0 chiffre inventé; 100% des chiffres cités.

## 6) Juridique — grille de cas d’usage
### Objectif secteur
Assistance fiable: **pas de jurisprudence inventée**, citations obligatoires.

#### Cas d’usage J1 — Revue de contrat (clauses & risques)
- Entrées: contrat + playbook interne.
- Mode vérifié: extraction clauses + risques + recommandations alignées playbook + citations.
- KPI: taux de clauses détectées, réduction du temps de revue.

#### Cas d’usage J2 — Recherche guidée (avec corpus interne)
- Entrées: doctrine interne, modèles, mémos.
- Mode vérifié: réponse = uniquement corpus; sinon abstention + questions de cadrage.
- KPI: 0 référence inventée; pertinence.

#### Cas d’usage J3 — Préparation note / courrier
- Entrées: faits + sources + modèle.
- Mode vérifié: rédaction structurée + citations + zones “à confirmer”.
- KPI: conformité style/format, absence d’assertions sans preuve.

## 7) Industrie — grille de cas d’usage
### Objectif secteur
Réduire erreurs opérationnelles, standardiser l’exécution, améliorer qualité.

#### Cas d’usage I1 — Maintenance (procédures & interventions)
- Entrées: SOP, manuels, historiques.
- Mode vérifié: pas à pas + références + prérequis + sécurité.
- KPI: réduction incidents, conformité SOP.

#### Cas d’usage I2 — Qualité (non-conformités / 8D)
- Entrées: rapports NC, exigences, lots.
- Mode vérifié: classification + causes potentielles + actions seulement si supportées.
- KPI: cohérence 8D, traçabilité.

#### Cas d’usage I3 — HSE (sécurité)
- Entrées: consignes, fiches sécurité.
- Mode vérifié: réponses limitées aux consignes + abstention si info manquante.
- KPI: 0 consigne inventée.

## 8) Protocole de démonstration (standardisé)
### Préparation
1. Constituer un **mini-corpus** (10–30 documents) par vertical (PDF/texte).
2. Préparer 20 questions:
   - 10 “répondables” (sources contiennent explicitement),
   - 5 “incomplètes” (sources insuffisantes),
   - 5 “pièges” (questions incitant à inventer: fausses citations, chiffres non présents).
3. Activer:
   - `DETERMINISTIC_LOCK=true`
   - `VERIFIED_MODE_DEFAULT=false` (ou `true` si tu veux une démo “full compliance”)

### Script de démo (15–25 min)
1. Montrer la **reproductibilité**
   - même prompt × 3 ⇒ même `response_id` et même `content`.
2. Montrer le **mode vérifié avec sources**
   - fournir sources/extraits,
   - exiger citations,
   - vérifier que chaque point clé pointe vers une source.
3. Montrer l’**abstention structurée**
   - poser une question factuelle sans source ⇒ abstention + liste des infos nécessaires.
4. Montrer la **résilience**
   - démontrer cache_hit sur une requête répétée (latence baisse, sortie identique).

### Grille d’évaluation (scorecard)
- **Fiabilité**
  - % d’assertions sourcées (mode vérifié) — cible: 100%
  - # d’assertions non sourcées — cible: 0
  - taux d’abstention utile — cible: > 80% (abstention avec questions actionnables)
- **Reproductibilité**
  - stabilité du `response_id` — cible: 100%
  - stabilité du contenu — cible: 100%
- **Utilité**
  - temps gagné vs process actuel
  - satisfaction experts métier

## 9) Plateformes à privilégier (davantage que LM Arena)
LM Arena est utile pour visibilité “grand public LLM”, mais pour **entreprises/institutions**, le levier principal est là où elles achètent/intègrent:

### Priorité 1 — Marketplaces & plateformes cloud (go-to-market B2B)
- **AWS Marketplace / AWS Bedrock (si packaging compatible)**: achat simplifié, procurement, facturation.
- **Azure Marketplace / Azure AI Foundry**: très fort pour institutions/entreprises, gouvernance, RBAC.
- **Google Cloud Marketplace / Vertex AI**: similaire pour GCP-first.

### Priorité 2 — Plateformes data/AI entreprise (là où vivent les données)
- **Databricks** (Marketplace + Model Serving/Unity Catalog) — traction forte en industrie/finance.
- **Snowflake** (Marketplace + apps/data products) — traction forte finance/secteurs régulés.

### Priorité 3 — Distribution dev & crédibilité technique
- **Hugging Face** (présence, démos, endpoints) — visibilité technique et intégrations, même si pas “institutionnel” en procurement.

### Priorité 4 — Confiance & conformité (souvent décisif)
- Certifs/process: SOC2, ISO 27001, DPIA, journalisation, contrôles d’accès, politiques de rétention.
- Alignement “mode vérifié” + audit trail = argument central.

## 10) Recommandation pratique de positionnement
- Conserver LM Arena comme vitrine.
- Se positionner “fiabilité” via:
  - **Azure (institutions/secteur public/entreprises)** + **AWS Marketplace (entreprises)** en priorité,
  - puis Databricks/Snowflake si vous visez les équipes data.

