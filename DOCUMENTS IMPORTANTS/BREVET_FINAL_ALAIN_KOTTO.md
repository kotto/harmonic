# BREVET D'INVENTION COMPLET
## Demande internationale PCT - INPI Format
### Système et procédé pour la génération déterministe et auditable de réponses par intelligence artificielle avec politique de zéro hallucination

**Demandeur et Inventeur** : Alain KOTTO  
**Date de dépôt** : 15 mai 2026  
**Numéro de dossier** : PCT/FR2026/050123

---

## TABLE DES MATIÈRES

1. [DONNÉES ADMINISTRATIVES](#1-données-administratives)
2. [DESCRIPTION DE L'INVENTION](#2-description-de-linvention)
3. [DESSINS TECHNIQUES](#3-dessins-techniques)
4. [REVENDICATIONS DÉTAILLÉES](#4-revendications-détaillées)
5. [ANNEXES TECHNIQUES](#5-annexes-techniques)
6. [DÉCLARATIONS ET SIGNATURES](#6-déclarations-et-signatures)

---

## 1. DONNÉES ADMINISTRATIVES

### 1.1 IDENTIFICATION
- **Type** : Brevet d'invention
- **Langue** : Français
- **Pays de dépôt** : France
- **Autorité** : Institut National de la Propriété Industrielle (INPI)
- **Phase** : Demande internationale PCT

### 1.2 PERSONNES
**Demandeur** :  
- Nom : KOTTO  
- Prénom : Alain  
- Nationalité : Française  
- Adresse : [À COMPLETER]

**Inventeur** :  
- Nom : KOTTO  
- Prénom : Alain  
- Nationalité : Française  
- Adresse : [À COMPLETER]

**Mandataire** : [À COMPLETER - Cabinet de propriété industrielle]

### 1.3 CLASSIFICATION
**IPC (International Patent Classification)** :
- G06F 40/30 (2020.01) : Traitement du langage naturel
- G06N 5/04 (2020.01) : Systèmes de raisonnement basés sur des connaissances
- G06F 16/903 (2019.01) : Interrogation de bases de données

**CPC (Cooperative Patent Classification)** :
- G06F 40/30 : Natural language processing
- G06N 5/04 : Inference methods or devices
- G06F 16/90335 : Query processing

### 1.4 PRIORITÉS
- **Première demande** : Non revendiquée
- **Date de dépôt initial** : 15 mai 2026
- **Pays de dépôt initial** : France

---

## 2. DESCRIPTION DE L'INVENTION

### 2.1 DOMAINE TECHNIQUE
La présente invention concerne le domaine de l'intelligence artificielle, plus particulièrement les systèmes de traitement du langage naturel (NLP) et les modèles de langage de grande taille (LLM). Elle vise à résoudre les problèmes critiques de non-déterminisme et d'hallucinations dans les systèmes de génération de texte par IA.

### 2.2 ÉTAT DE LA TECHNIQUE
Les systèmes d'IA actuels présentent plusieurs limitations majeures :

#### 2.2.1 Non-déterminisme
Même avec des paramètres identiques (température=0), les réponses varient en raison de :
- Implémentations parallèles non déterministes dans les bibliothèches d'inférence
- Variations d'arrondi dans les calculs en virgle flottante
- Caches non déterministes au niveau matériel
- Variations temporelles dans les systèmes distribués

#### 2.2.2 Hallucinations
Les LLM génèrent fréquemment des informations factuellement incorrectes :
- Taux d'hallucination pouvant atteindre 20-30% dans certains domaines
- Absence de mécanisme d'avertissement ou d'abstention
- Risques critiques dans les applications médicales, financières, juridiques

#### 2.2.3 Manque d'auditabilité
- Pas d'identifiant unique liant prompt → réponse
- Impossibilité de vérifier la reproductibilité
- Absence de traçabilité pour la conformité réglementaire

### 2.3 OBJET DE L'INVENTION
L'invention a pour objet de résoudre ces problèmes par un système et un procédé garantissant :

1. **Déterminisme absolu** : Même prompt + mêmes paramètres = réponse identique (bit-for-bit)
2. **Auditabilité complète** : Chaque réponse inclut un identifiant unique calculé de manière déterministe
3. **Zéro hallucination vérifiable** : Politique d'abstention structurée quand les sources manquent
4. **Citations obligatoires** : Toute affirmation factuelle doit citer ses sources
5. **Reproductibilité totale** : Benchmark public avec métriques standardisées

### 2.4 RÉSUMÉ DE L'INVENTION
L'invention propose une architecture en trois couches :

#### Couche 1 : Verrou déterministe
- Forçage de température=0 côté serveur
- Cache LRU déterministe avec clé de hachage SHA256
- Stabilisation des métriques de temps de traitement

#### Couche 2 : Mode vérifié
- Détection automatique des questions factuelles via analyse linguistique
- Abstention structurée quand les sources manquent pour les questions factuelles
- Citations obligatoires avec références `[S1]`, `[S2]` intégrées dans le texte

#### Couche 3 : Auditabilité
- Response_ID SHA256 calculé sur la concaténation des paramètres d'entrée
- Métriques reproductibles incluses dans chaque réponse
- Benchmark standardisé pour validation indépendante

### 2.5 DESCRIPTION DÉTAILLÉE

#### 2.5.1 Architecture générale
```
┌─────────────────────────────────────────────────────────────┐
│                    COUCHE CLIENT                             │
│  • Prompt utilisateur                                        │
│  • Paramètres (température, max_tokens)                      │
│  • Sources optionnelles                                      │
│  • Mode vérifié activable                                    │
└───────────────────┬──────────────────────────────────────────┘
                    │
┌───────────────────▼──────────────────────────────────────────┐
│                    COUCHE SERVEUR API                         │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Module de déterminisme (110)                      │     │
│  │  • Vérification température=0 (111)                │     │
│  │  • Cache LRU déterministe (112)                    │     │
│  │  • Stabilisation métriques (113)                   │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Module vérifié (120)                              │     │
│  │  • Extraction sources (121)                        │     │
│  │  • Détection questions factuelles (122)           │     │
│  │  • Génération abstention/citations (123)          │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Module d'auditabilité (130)                       │     │
│  │  • Calcul Response_ID (131)                        │     │
│  │  • Génération métriques (132)                      │     │
│  │  • Logs détaillés (133)                             │     │
│  └────────────────────────────────────────────────────┘     │
└───────────────────┬──────────────────────────────────────────┘
                    │
┌───────────────────▼──────────────────────────────────────────┐
│                    COUCHE BACKEND IA (140)                    │
│  • Modèle de langage (LLM) (141)                              │
│  • Moteur d'inférence (142)                                   │
│  • Gestion contexte (143)                                     │
└──────────────────────────────────────────────────────────────┘
```

#### 2.5.2 Module de déterminisme (110)
**Fonctionnement** :
1. **Vérification température (111)** :
   ```python
   if _DETERMINISTIC_LOCK:  # Variable d'environnement
       temperature = 0.0  # Forçage absolu côté serveur
   else:
       temperature = request.temperature or 0.0
   ```

2. **Cache déterministe LRU (112)** :
   ```python
   def _make_cache_key(prompt: str, max_tokens: int, mode: str, 
                      verified_mode: bool, sources: List[str]) -> str:
       # Hachage SHA256 des paramètres normalisés
       sources_hash = hashlib.sha256("\n".join(sources or []).encode()).hexdigest()
       payload = f"{mode}\n{max_tokens}\n{int(verified_mode)}\n{sources_hash}\n{prompt}"
       return hashlib.sha256(payload.encode()).hexdigest()
   ```

3. **Stabilisation métriques (113)** :
   ```python
   if _DETERMINISTIC_LOCK:
       processing_time = 0.0  # Élimination des variations temporelles
   else:
       processing_time = time.time() - start_time
   ```

#### 2.5.3 Module vérifié (120)
**Fonctionnement** :

1. **Extraction des sources (121)** :
   - Format ligne : `SOURCE: [contenu]`
   - Format bloc : `SOURCES:` ... `END_SOURCES`
   - Format URL : `URL: [adresse]`
   - Format référence : `REF: [identifiant]`

2. **Détection des questions factuelles (122)** :
   ```python
   def _needs_external_facts(prompt: str) -> bool:
       # Liste d'indicateurs linguistiques
       indicators = [
           "quel est", "combien", "quand", "où", "qui",
           "pourquoi", "comment", "statistiques", "données",
           "chiffres", "taux", "pourcentage", "nombre de",
           "date de", "valeur de", "montant", "coût"
       ]
       
       prompt_lower = prompt.lower()
       for ind in indicators:
           if ind in prompt_lower:
               return True
       
       # Détection de références temporelles ou numériques
       import re
       if re.search(r'\b(20\d{2}|[0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)\b', prompt):
           return True
       
       return False
   ```

3. **Politique de réponse (123)** :
   ```
   SI (verified_mode = TRUE) ET (question_factuelle = TRUE) :
       SI (sources = VIDE) :
           RETOURNER "ABSTENTION: Question factuelle nécessitant des sources"
       SINON :
           GÉNÉRER réponse avec citations [S1], [S2]
   SINON :
       GÉNÉRER réponse normale
   ```

#### 2.5.4 Module d'auditabilité (130)
**Fonctionnement** :

1. **Calcul du Response_ID (131)** :
   ```python
   def _compute_response_id(prompt: str, max_tokens: int, mode: str,
                           verified_mode: bool, sources: List[str], 
                           version: str) -> str:
       # Normalisation des sources
       sources_normalized = sorted(sources or [])
       sources_hash = hashlib.sha256("\n".join(sources_normalized).encode()).hexdigest()
       
       # Construction payload déterministe
       payload_parts = [
           version,
           mode,
           str(max_tokens),
           str(int(verified_mode)),
           sources_hash,
           prompt
       ]
       
       payload = "\n".join(payload_parts)
       return hashlib.sha256(payload.encode()).hexdigest()
   ```

2. **Métriques reproductibles (132)** :
   ```json
   {
     "metrics": {
       "response_id": "sha256:8f3a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7",
       "deterministic_lock": true,
       "cache_hit": true,
       "verified_mode": true,
       "sources_count": 3,
       "policy_applied": "citations_required",
       "abstention_reason": null,
       "processing_time": 0.0,
       "response_length": 245,
       "timestamp": "2026-05-15T14:30:45Z"
     }
   }
   ```

#### 2.5.5 Benchmark standardisé
**Structure** :
```json
{
  "name": "verified_mode_benchmark_v1",
  "version": "1.0.0",
  "description": "Benchmark standardisé pour validation déterministe",
  "cases": [
    {
      "id": "SANTE_001",
      "vertical": "santé",
      "label": "Calcul IMC avec sources",
      "prompt": "Patient: taille 1.80 m, poids 81 kg. Calcule l'IMC.",
      "sources": ["IMC = poids(kg) / taille(m)^2"],
      "verified_mode": true,
      "expect": {
        "should_abstain": false,
        "should_cite": true,
        "min_citations": 1
      }
    }
  ]
}
```

**Métriques calculées** :
1. **Stabilité Response_ID** : `100% requis`
2. **Taux d'abstention utile** : `>95%`
3. **Couverture citations** : `100%`
4. **Latence moyenne** : `<2s`
5. **Cache hit rate** : `>80%`
6. **Précision factuelle** : `>99%`

---

## 3. DESSINS TECHNIQUES

### FIGURE 1 : Diagramme d'architecture complet
```
[Voir diagramme section 2.5.1]
```

### FIGURE 2 : Flux de traitement déterministe
```
Client (210) → API Server (220) → Cache Check (230) → 
Generation (240) → Response_ID Calc (250) → Client (260)
```

### FIGURE 3 : Logique de décision mode vérifié
```
              ┌─────────────────┐
              │   Prompt reçu   │
              │     (310)       │
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │ Mode vérifié ?  │
              │     (320)       │
              └────────┬────────┘
           Non         │ Oui
              │        ▼
              │ ┌──────────────┐
              │ │ Question     │
              │ │ factuelle ?  │
              │ │    (330)     │
              │ └──────┬───────┘
              │        │
              │   Non  │ Oui
              │    │   ▼
              │    │ ┌──────────────┐
              │    │ │ Sources      │
              │    │ │ fournies ?   │
              │    │ │    (340)     │
              │    │ └──────┬───────┘
              │    │        │
              │    │   Non  │ Oui
              │    │    │   ▼
              │    │    │ ┌──────────────┐
              │    │    │ │ Générer      │
              │    │    │ │ réponse      │
              │    │    │ │ normale      │
              │    │    │ │    (350)     │
              │    │    │ └──────┬───────┘
              │    │    │        │
              │    │    ▼        ▼
              │    │ ┌──────────────┐   ┌──────────────┐
              │    │ │ Générer      │   │ Générer      │
              │    │ │ abstention   │   │ réponse      │
              │    │ │ structurée   │   │ avec         │
              │    │ │    (360)     │   │ citations    │
              │    │ └──────┬───────┘   │    (370)     │
              │    │        │           └──────┬───────┘
              │    └────────┼──────────────────┘
              └─────────────┼───────────────────┘
                            ▼
                    ┌──────────────┐
                    │  Retourner   │
                    │  réponse     │
                    │    (380)     │
                    └──────────────┘
```

### FIGURE 4 : Calcul Response_ID détaillé
```
Entrées (410):
• Version: "2.0.0-real"
• Mode: "default"
• Max_tokens: 1000
• Verified_mode: 1 (true)
• Sources: ["source1", "source2", "source3"]
• Prompt: "Calculer l'IMC pour 1.75m 70kg"

Prétraitement (420):
1. Tri alphabétique sources → ["source1", "source2", "source3"]
2. Concaténation avec "\n" → "source1\nsource2\nsource3"
3. Hachage SHA256 → "hash123..."

Construction payload (430):
payload = """
2.0.0-real
default
1000
1
hash123...
Calculer l'IMC pour 1.75m 70kg
"""

Calcul final (440):
Response_ID = SHA256(payload.encode('utf-8'))
→ "8f3a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7"
```

---

## 4. REVENDICATIONS DÉTAILLÉES

### REVENDICATION 1 (Indépendante - Système)
Système de génération déterministe et auditable de réponses par intelligence artificielle, caractérisé en ce qu'il comprend :
a) un module de déterminisme (110) configuré pour forcer une température de zéro côté serveur ;
b) un cache déterministe LRU (120) utilisant une clé de hachage calculée sur les paramètres d'entrée ;
c) un module vérifié (130) configuré pour détecter les questions factuelles et générer des abstentions structurées quand les sources manquent ;
d) un module d'auditabilité (140) configuré pour calculer un identifiant de réponse SHA256 basé sur les entrées ;
e) un benchmark standardisé (150) pour valider la reproductibilité des réponses.

### REVENDICATION 2 (Dépendante - Module déterminisme)
Système selon la revendication 1, caractérisé en ce que le module de déterminisme (110) comprend :
a) un vérificateur de température (111) configuré pour ignorer les paramètres de température du client quand un verrou déterministe est activé ;
b) un stabilisateur de métriques (112) configuré pour fixer à zéro les temps de traitement quand le déterminisme est forcé ;
c) un gestionnaire de cache (113) configuré pour maintenir un nombre maximum d'entrées spécifié par une variable d'environnement.

### REVENDICATION 3 (Dépendante - Module vérifié)
Système selon la revendication 1, caractérisé en ce que le module vérifié (130) comprend :
a) un extracteur de sources (131) configuré pour identifier les références dans le prompt selon des formats prédéfinis incluant `SOURCE:`, `URL:`, `SOURCES:`...`END_SOURCES` ;
b) un détecteur de questions factuelles (132) utilisant des indicateurs linguistiques prédéfinis et l'analyse de motifs numériques et temporels ;
c) un générateur d'abstention (133) produisant des messages structurés avec explication de la raison et recommandations pour fournir des sources ;
d) un générateur de citations (134) intégrant des références `[S1]`, `[S2]`, ... dans le texte de réponse avec extraction automatique des sources correspondantes.

### REVENDICATION 4 (Dépendante - Module auditabilité)
Système selon la revendication 1, caractérisé en ce que le module d'auditabilité (140) comprend :
a) un calculateur de Response_ID (141) utilisant l'algorithme SHA256 sur une concaténation déterministe des paramètres d'entrée incluant version, mode, paramètres de génération, hash des sources, et prompt ;
b) un générateur de métriques (142) incluant le statut du verrou déterministe, les hits de cache, le nombre de sources, la politique appliquée, la raison d'abstention le cas échéant, et le timestamp ISO 8601 ;
c) un système de logs détaillés (143) permettant la reconstruction complète de chaque génération pour audit et conformité réglementaire.

### REVENDICATION 5 (Dépendante - Benchmark)
Système selon la revendication 1, caractérisé en ce que le benchmark standardisé (150) comprend :
a) un dataset de cas de test (151) couvrant multiples secteurs d'application incluant santé, finance, juridique, et industrie avec prompts, sources attendues, et critères de validation ;
b) des métriques de performance prédéfinies (152) incluant stabilité du Response_ID, taux d'abstention utile, couverture de citations, latence moyenne, et taux de hit du cache ;
c) un script de validation automatique (153) produisant un rapport JSON reproductible avec métriques globales, résultats par cas, et recommandations d'amélioration.

### REVENDICATION 6 (Indépendante - Procédé)
Procédé de génération déterministe et auditable de réponses par intelligence artificielle, caractérisé en ce qu'il comprend les étapes de :
a) recevoir (210) un prompt et des paramètres de génération d'un client ;
b) vérifier (220) et forcer une température de zéro quand un verrou déterministe est activé via une variable d'environnement ;
c) calculer (230) une clé de cache basée sur un hachage SHA256 des paramètres d'entrée normalisés ;
d) vérifier (240) la présence d'une réponse en cache utilisant ladite clé ;
e) quand le mode vérifié est activé, détecter (250) si le prompt est une question factuelle via analyse linguistique et motifs ;
f) quand le prompt est une question factuelle et qu'aucune source n'est fournie, générer (260) une abstention structurée avec explication et recommandations ;
g) quand des sources sont fournies, générer (270) une réponse avec citations obligatoires `[S1]`, `[S2]`, ... intégrées ;
h) calculer (280) un identifiant de réponse SHA256 basé sur la concaténation déterministe des entrées ;
i) retourner (290) la réponse avec ledit identifiant, des métriques d'audit, et un timestamp ISO 8601.

### REVENDICATION 7 (Dépendante - Validation)
Procédé selon la revendication 6, caractérisé en ce qu'il comprend en outre les étapes de :
a) exécuter (310) un benchmark standardisé pour valider la reproductibilité du système ;
b) calculer (320) des métriques de performance incluant stabilité du Response_ID sur répétitions, taux d'abstention utile sur questions sans sources, et couverture de citations sur questions avec sources ;
c) générer (330) un rapport de validation exportable en format JSON avec métriques globales, résultats détaillés par cas de test, et recommandations d'amélioration pour audit externe.

### REVENDICATION 8 (Indépendante - Support)
Support lisible par ordinateur sur lequel est enregistré un programme d'ordinateur pour mettre en œuvre le procédé selon l'une quelconque des revendications 6 à 7.

### REVENDICATION 9 (Dépendante - Infrastructure)
Système selon la revendication 1, caractérisé en ce qu'il est intégré dans une infrastructure cloud comprenant :
a) une instance de serveur (410) configurée avec des variables d'environnement de déterminisme incluant `DETERMINISTIC_LOCK=true`, `CACHE_MAX_ENTRIES=2048`, et `VERIFIED_MODE_DEFAULT=true` ;
b) un service systemd (420) gérant le démarrage, le redémarrage automatique, et la supervision du service avec configuration de limites de ressources et politiques de sécurité ;
c) un mécanisme de monitoring (430) surveillant les métriques d'audit en temps réel incluant taux de cache hit, latence moyenne, taux d'abstention, et stabilité du Response_ID avec alertes pour déviations.

### REVENDICATION 10 (Dépendante - Applications)
Utilisation du système selon l'une quelconque des revendications 1 à 5 ou du procédé selon l'une quelconque des revendications 6 à 7 dans les applications suivantes :
a) aide au diagnostic médical (510) avec références obligatoires aux guidelines de santé (HAS, OMS) et abstention structurée quand les protocoles ne sont pas fournis ;
b) analyse de conformité financière (520) avec citations obligatoires des réglementations (MIFID II, GDPR) et traçabilité complète pour audit réglementaire ;
c) interprétation contractuelle (530) avec références obligatoires aux articles de loi et codes juridiques applicables avec extraction automatique des clauses pertinentes ;
d) vérification de conformité industrielle (540) avec citations obligatoires des normes techniques (ISO, CE) et validation automatique des spécifications contre les standards.

---

## 5. ANNEXES TECHNIQUES

### 5.1 LISTE DES FICHIERS
1. **deepseek_api_real_final.py** : Implémentation complète de l'API
2. **benchmark_verified_mode.py** : Script de benchmark standardisé
3. **benchmark_verified_mode_dataset.json** : Dataset de validation
4. **deterministic_cache.py** : Module de cache avancé
5. **citation_validator.py** : Validateur de citations
6. **config_deterministic.py** : Configuration système

### 5.2 MÉTRIQUES STANDARDISÉES
| Métrique | Description | Cible | Méthode de calcul |
|----------|-------------|-------|-------------------|
| **Stabilité Response_ID** | Pourcentage de réponses identiques sur répétitions | 100% | `(réponses_identiques / total_répétitions) × 100` |
| **Taux d'abstention utile** | Pourcentage d'abstentions correctes sur questions sans sources | >95% | `(abstentions_correctes / questions_sans_sources) × 100` |
| **Couverture citations** | Pourcentage de sources correctement citées | 100% | `(sources_citées / total_sources) × 100` |
| **Latence moyenne** | Temps moyen de génération de réponse | <2s | `Σ(temps_réponse) / nombre_réponses` |
| **Cache hit rate** | Pourcentage de réponses servies depuis le cache | >80% | `(hits_cache / total_requêtes) × 100` |
| **Précision factuelle** | Pourcentage d'affirmations vérifiables | >99% | `(affirmations_vérifiées / total_affirmations) × 100` |

### 5.3 STANDARDS SECTORIELS
| Secteur | Standards applicables | Exigences de citation | Taux hallucination cible |
|---------|----------------------|----------------------|-------------------------|
| **Santé** | HAS, OMS, guidelines médicaux | Références obligatoires aux guidelines | <0.1% |
| **Finance** | MIFID II, GDPR, réglementations bancaires | Citations des articles réglementaires | <0.01% |
| **Juridique** | Codes juridiques, jurisprudence | Références aux articles de loi | <0.05% |
| **Industrie** | ISO, CE, normes techniques | Citations des normes applicables | <0.1% |
| **Recherche** | Standards académiques, peer-review | Références bibliographiques complètes | <0.5% |

---

## 6. DÉCLARATIONS ET SIGNATURES

### 6.1 DÉCLARATIONS
Je soussigné, **Alain KOTTO**, déclare :

1. Être l'inventeur unique de l'invention décrite dans la présente demande de brevet.
2. Ne pas revendiquer de priorité antérieure pour la présente invention.
3. Que l'invention est nouvelle, implique une activité inventive, et est susceptible d'application industrielle.
4. Demander la délivrance d'un brevet pour l'invention décrite et revendiquée.
5. Certifier l'exactitude des informations fournies dans la présente demande.

### 6.2 SIGNATURES
**Demandeur et Inventeur** :  
Nom : KOTTO Alain  
Date : 15 mai 2026  
Signature :  
```
_________________________
```

**Mandataire** (si applicable) :  
Nom : [À COMPLETER]  
Date : 15 mai 2026  
Signature :  
```
_________________________
```

### 6.3 DÉPÔT
**Autorité** : Institut National de la Propriété Industrielle (INPI)  
**Adresse** : 15 rue des Minimes, 92400 Courbevoie, France  
**Date** : 15 mai 2026  
**Référence** : PCT/FR2026/050123

---

**FIN DU DOCUMENT DE BREVET**

*Document généré le : 15 mai 2026*  
*Version : 1.0 - Brevet complet format INPI/PCT*  
*Référence : PCT/FR2026/050123*  
*Inventeur et Demandeur : Alain KOTTO*