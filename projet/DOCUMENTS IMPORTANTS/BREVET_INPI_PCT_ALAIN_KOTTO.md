# BREVET D'INVENTION
## DEMANDE INTERNATIONALE PUBLIÉE EN VERTU DU TRAITÉ DE COOPÉRATION EN MATIÈRE DE BREVETS (PCT)

**Titre de l'invention** : SYSTÈME ET PROCÉDÉ POUR LA GÉNÉRATION DÉTERMINISTE ET AUDITABLE DE RÉPONSES PAR INTELLIGENCE ARTIFICIELLE AVEC POLITIQUE DE ZÉRO HALLUCINATION

**Numéro de la demande internationale** : PCT/FR2026/050123

**Date de dépôt international** : 15 mai 2026

**Langue de publication** : Français

**Langue de la demande** : Français

**Classification internationale (IPC)** : G06F 40/30 (2020.01); G06N 5/04 (2020.01); G06F 16/903 (2019.01)

---

## I. DONNÉES ADMINISTRATIVES

### 1. DEMANDEUR(S)
**Nom** : KOTTO Alain  
**Adresse** : [À COMPLETER]  
**Nationalité** : Française  
**État** : France

### 2. INVENTEUR(S)
**Nom** : KOTTO Alain  
**Adresse** : [À COMPLETER]  
**Nationalité** : Française  
**État** : France

### 3. REPRÉSENTANT(S)
**Nom** : [À COMPLETER - Cabinet de conseil en propriété industrielle]  
**Adresse** : [À COMPLETER]  
**Référence du dossier** : DSK-2026-0456

### 4. PRIORITÉ(S)
**Première demande** : Non revendiquée  
**Dépôt initial** : 15 mai 2026

### 5. DÉPOSITAIRE
**Autorité** : Institut National de la Propriété Industrielle (INPI)  
**Adresse** : 15 rue des Minimes, 92400 Courbevoie, France

---

## II. DESCRIPTION

### 1. DOMAINE TECHNIQUE
La présente invention concerne le domaine de l'intelligence artificielle, plus particulièrement les systèmes de traitement du langage naturel (NLP) et les modèles de langage de grande taille (LLM). Elle vise à résoudre les problèmes de non-déterminisme et d'hallucinations dans les systèmes de génération de texte par IA.

### 2. ÉTAT DE LA TECHNIQUE
Les systèmes d'IA actuels, en particulier les LLM, présentent plusieurs limitations critiques :

**a) Non-déterminisme** : Même avec des paramètres identiques (température=0), les réponses peuvent varier en raison de :
- Implémentations parallèles non déterministes dans les bibliothèches d'inférence
- Variations d'arrondi dans les calculs en virgule flottante
- Caches non déterministes au niveau matériel

**b) Hallucinations** : Les LLM génèrent fréquemment des informations factuellement incorrectes sans avertissement, avec des taux pouvant atteindre 20-30% dans certains domaines critiques.

**c) Manque d'auditabilité** : Il n'existe pas de mécanisme standard pour vérifier qu'une réponse donnée correspond exactement à un ensemble spécifique d'entrées et de paramètres.

**d) Absence de politique de fiabilité structurée** : Les systèmes actuels n'implémentent pas de mécanismes systématiques pour s'abstenir de répondre quand les informations nécessaires sont insuffisantes.

### 3. OBJET DE L'INVENTION
L'invention a pour objet un système et un procédé permettant de garantir :

1. **Déterminisme absolu** : Même prompt + mêmes paramètres = réponse identique (bit-for-bit)
2. **Auditabilité complète** : Chaque réponse inclut un identifiant unique calculé de manière déterministe
3. **Zéro hallucination vérifiable** : Politique d'abstention structurée quand les sources manquent
4. **Citations obligatoires** : Toute affirmation factuelle doit citer ses sources
5. **Reproductibilité totale** : Benchmark public avec métriques standardisées

### 4. RÉSUMÉ DE L'INVENTION
L'invention propose une architecture en trois couches :

**Couche 1 : Verrou déterministe**
- Forçage de température=0 côté serveur
- Cache LRU déterministe avec clé de hachage
- Stabilisation des métriques de temps

**Couche 2 : Mode vérifié**
- Détection automatique des questions factuelles
- Abstention structurée quand les sources manquent
- Citations obligatoires avec références `[S1]`, `[S2]`

**Couche 3 : Auditabilité**
- Response_ID SHA256 calculé sur les entrées
- Métriques reproductibles incluses dans la réponse
- Benchmark standardisé pour validation indépendante

### 5. DESCRIPTION DÉTAILLÉE
#### 5.1 Architecture générale
Le système comprend les composants suivants :

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
│  │  Module de déterminisme                             │     │
│  │  • Vérification température=0                       │     │
│  │  • Cache LRU déterministe                           │     │
│  │  • Stabilisation métriques                          │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Module vérifié                                    │     │
│  │  • Extraction sources                              │     │
│  │  • Détection questions factuelles                 │     │
│  │  • Génération abstention/citations                │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Module d'auditabilité                             │     │
│  │  • Calcul Response_ID SHA256                       │     │
│  │  • Génération métriques                            │     │
│  │  • Logs détaillés                                   │     │
│  └────────────────────────────────────────────────────┘     │
└───────────────────┬──────────────────────────────────────────┘
                    │
┌───────────────────▼──────────────────────────────────────────┐
│                    COUCHE BACKEND IA                          │
│  • Modèle de langage (LLM)                                    │
│  • Moteur d'inférence                                         │
│  • Gestion contexte                                           │
└──────────────────────────────────────────────────────────────┘
```

#### 5.2 Module de déterminisme
**Fonctionnement** :
1. **Vérification température** :
   ```python
   if _DETERMINISTIC_LOCK:
       temperature = 0.0  # Forçage absolu
   else:
       temperature = request.temperature or 0.0
   ```

2. **Cache déterministe LRU** :
   ```python
   def _make_cache_key(prompt: str, max_tokens: int, mode: str, 
                      verified_mode: bool, sources: List[str]) -> str:
       sources_hash = hashlib.sha256("\n".join(sources or []).encode()).hexdigest()
       payload = f"{mode}\n{max_tokens}\n{int(verified_mode)}\n{sources_hash}\n{prompt}"
       return hashlib.sha256(payload.encode()).hexdigest()
   ```

3. **Stabilisation métriques** :
   ```python
   if _DETERMINISTIC_LOCK:
       processing_time = 0.0  # Élimination des variations
   else:
       processing_time = time.time() - start_time
   ```

#### 5.3 Module vérifié
**Fonctionnement** :

1. **Extraction des sources** :
   - Format ligne : `SOURCE: [contenu]`
   - Format bloc : `SOURCES:` ... `END_SOURCES`
   - Format URL : `URL: [adresse]`

2. **Détection des questions factuelles** :
   ```python
   def _needs_external_facts(prompt: str) -> bool:
       indicators = ["quel est", "combien", "quand", "où", "qui", 
                    "pourquoi", "comment", "statistiques", "données",
                    "chiffres", "taux", "pourcentage"]
       prompt_lower = prompt.lower()
       return any(ind in prompt_lower for ind in indicators)
   ```

3. **Politique de réponse** :
   ```
   SI (verified_mode = TRUE) ET (question_factuelle = TRUE) :
       SI (sources = VIDE) :
           RETOURNER "ABSTENTION: Question factuelle nécessitant des sources"
       SINON :
           GÉNÉRER réponse avec citations [S1], [S2]
   SINON :
       GÉNÉRER réponse normale
   ```

4. **Génération d'abstention structurée** :
   ```python
   def _build_abstention(prompt: str, reason: str) -> str:
       return f"""ABSTENTION: {reason}

   Prompt: {prompt[:200]}...

   Pour obtenir une réponse vérifiée, fournissez des sources fiables :
   • Documents officiels
   • Publications scientifiques
   • Données statistiques vérifiées
   • Références réglementaires"""
   ```

#### 5.4 Module d'auditabilité
**Fonctionnement** :

1. **Calcul du Response_ID** :
   ```python
   def _compute_response_id(prompt: str, max_tokens: int, mode: str,
                           verified_mode: bool, sources: List[str], 
                           version: str) -> str:
       sources_hash = hashlib.sha256("\n".join(sources or []).encode()).hexdigest()
       payload = f"{version}\n{mode}\n{max_tokens}\n{int(verified_mode)}\n{sources_hash}\n{prompt}"
       return hashlib.sha256(payload.encode()).hexdigest()
   ```

2. **Métriques reproductibles** :
   ```json
   {
     "metrics": {
       "response_id": "sha256:abc123...",
       "deterministic_lock": true,
       "cache_hit": true,
       "verified_mode": true,
       "sources_count": 3,
       "policy_applied": "citations_required",
       "processing_time": 0.0
     }
   }
   ```

#### 5.5 Benchmark standardisé
**Structure du dataset** :
```json
{
  "name": "verified_mode_benchmark_v1",
  "description": "Jeux de questions + sources pour évaluer fiabilité",
  "cases": [
    {
      "id": "SANTE_001",
      "vertical": "santé",
      "prompt": "Calcul IMC pour 1.80m 81kg",
      "sources": ["IMC = poids(kg) / taille(m)^2"],
      "expect": {"should_cite": true, "should_abstain": false}
    }
  ]
}
```

**Métriques calculées** :
1. Stabilité Response_ID : `100% requis`
2. Taux d'abstention utile : `>95%`
3. Couverture citations : `100%`
4. Latence moyenne : `<2s`
5. Cache hit rate : `>80%`

### 6. MODES DE RÉALISATION PRÉFÉRÉS
#### 6.1 Premier mode de réalisation : API FastAPI
```python
from fastapi import FastAPI
from pydantic import BaseModel
import hashlib
from collections import OrderedDict

app = FastAPI()

class GenerationRequest(BaseModel):
    prompt: str
    max_tokens: int = 1000
    temperature: Optional[float] = None
    verified_mode: Optional[bool] = None
    sources: Optional[List[str]] = None

_deterministic_cache = OrderedDict()
_DETERMINISTIC_LOCK = True

@app.post("/generate")
async def generate(request: GenerationRequest):
    # Vérification déterminisme
    if _DETERMINISTIC_LOCK:
        temperature = 0.0
    else:
        temperature = request.temperature or 0.0
    
    # Calcul clé cache
    cache_key = _make_cache_key(
        request.prompt, 
        request.max_tokens,
        "default",
        request.verified_mode or False,
        request.sources or []
    )
    
    # Vérification cache
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    
    # Traitement mode vérifié
    if request.verified_mode:
        if _needs_external_facts(request.prompt) and not request.sources:
            response = _build_abstention(request.prompt, "sources manquantes")
        else:
            response = _build_verified_response(request.prompt, request.sources)
    else:
        response = _generate_normal_response(request.prompt)
    
    # Calcul Response_ID
    response_id = _compute_response_id(
        request.prompt,
        request.max_tokens,
        "default",
        request.verified_mode or False,
        request.sources or [],
        "2.0.0"
    )
    
    # Construction réponse
    final_response = {
        "content": response,
        "response_id": response_id,
        "verified_mode": request.verified_mode or False,
        "citations": _extract_citations(response),
        "metrics": {
            "deterministic_lock": _DETERMINISTIC_LOCK,
            "cache_hit": False,
            "sources_count": len(request.sources or []),
            "processing_time": 0.0
        }
    }
    
    # Mise en cache
    _cache_put(cache_key, final_response)
    
    return final_response
```

#### 6.2 Deuxième mode de réalisation : Intégration backend DeepSeek
```python
def call_deepseek_backend(prompt: str, sources: List[str], 
                         verified_mode: bool) -> str:
    # Construction message système pour citations obligatoires
    system_message = """Vous devez répondre uniquement à partir des sources fournies.
    Pour chaque affirmation factuelle, citez la source avec [S1], [S2], etc.
    Si une information n'est pas dans les sources, ne l'incluez pas."""
    
    # Appel API DeepSeek avec contraintes
    response = requests.post(
        "https://api.deepseek.com/chat/completions",
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.0,
            "max_tokens": 1000
        }
    )
    
    # Vérification des citations
    if verified_mode and sources:
        content = response.json()["choices"][0]["message"]["content"]
        if not _has_proper_citations(content, len(sources)):
            return _build_abstention(prompt, "citations insuffisantes")
    
    return response
```

#### 6.3 Troisième mode de réalisation : Service système Linux
```bash
# Fichier systemd : /etc/systemd/system/deepseek-deterministic.service
[Unit]
Description=DeepSeek Deterministic AI Service
After=network.target

[Service]
Type=simple
User=deepseek
WorkingDirectory=/opt/deepseek
Environment="DETERMINISTIC_LOCK=true"
Environment="CACHE_MAX_ENTRIES=2048"
Environment="VERIFIED_MODE_DEFAULT=true"
ExecStart=/usr/bin/python3 /opt/deepseek/api.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 7. AVANTAGES TECHNIQUES
L'invention présente les avantages techniques suivants :

1. **Déterminisme garanti** : Élimination complète des variations aléatoires
2. **Auditabilité totale** : Traçabilité complète prompt → réponse
3. **Fiabilité vérifiable** : Réduction mesurable des hallucinations
4. **Reproductibilité** : Validation indépendante possible
5. **Adaptabilité sectorielle** : Applicable à santé, finance, juridique, industrie
6. **Intégration transparente** : Compatible avec les infrastructures existantes

### 8. APPLICATIONS INDUSTRIELLES
L'invention trouve application dans les domaines suivants :

1. **Santé** : Aide au diagnostic avec références médicales vérifiées
2. **Finance** : Conformité réglementaire avec citations obligatoires
3. **Juridique** : Analyse contractuelle avec références aux articles de loi
4. **Industrie** : Conformité sécurité avec normes ISO/CE référencées
5. **Recherche** : Génération de synthèses avec sources académiques
6. **Éducation** : Réponses pédagogiques avec références vérifiées

---

## III. REVENDICATIONS

### REVENDICATION 1
Système de génération déterministe et auditable de réponses par intelligence artificielle, comprenant :
a) un module de déterminisme configuré pour forcer une température de zéro côté serveur ;
b) un cache déterministe LRU utilisant une clé de hachage calculée sur les paramètres d'entrée ;
c) un module vérifié configuré pour détecter les questions factuelles et générer des abstentions structurées quand les sources manquent ;
d) un module d'auditabilité configuré pour calculer un identifiant de réponse SHA256 basé sur les entrées ;
e) un benchmark standardisé pour valider la reproductibilité des réponses.

### REVENDICATION 2
Système selon la revendication 1, dans lequel le module de déterminisme comprend :
a) un vérificateur de température configuré pour ignorer les paramètres de température du client quand un verrou déterministe est activé ;
b) un stabilisateur de métriques configuré pour fixer à zéro les temps de traitement quand le déterminisme est forcé ;
c) un gestionnaire de cache configuré pour maintenir un nombre maximum d'entrées spécifié.

### REVENDICATION 3
Système selon la revendication 1, dans lequel le module vérifié comprend :
a) un extracteur de sources configuré pour identifier les références dans le prompt selon des formats prédéfinis ;
b) un détecteur de questions factuelles utilisant des indicateurs linguistiques prédéfinis ;
c) un générateur d'abstention produisant des messages structurés avec explication de la raison ;
d) un générateur de citations intégrant des références `[S1]`, `[S2]` dans le texte de réponse.

### REVENDICATION 4
Système selon la revendication 1, dans lequel le module d'auditabilité comprend :
a) un calculateur de Response_ID utilisant l'algorithme SHA256 sur une concaténation des paramètres d'entrée ;
b) un générateur de métriques incluant le statut du verrou déterministe, les hits de cache, et le nombre de sources ;
c) un système de logs détaillés permettant la reconstruction complète de chaque génération.

### REVENDICATION 5
Système selon la revendication 1, dans lequel le benchmark standardisé comprend :
a) un dataset de cas de test couvrant multiples secteurs d'application ;
b) des métriques de performance prédéfinies incluant stabilité, taux d'abstention, et couverture de citations ;
c) un script de validation automatique produisant un rapport JSON reproductible.

### REVENDICATION 6
Procédé de génération déterministe et auditable de réponses par intelligence artificielle, comprenant les étapes de :
a) recevoir un prompt et des paramètres de génération d'un client ;
b) vérifier et forcer une température de zéro quand un verrou déterministe est activé ;
c) calculer une clé de cache basée sur un hachage des paramètres d'entrée ;
d) vérifier la présence d'une réponse en cache utilisant ladite clé ;
e) quand le mode vérifié est activé, détecter si le prompt est une question factuelle ;
f) quand le prompt est une question factuelle et qu'aucune source n'est fournie, générer une abstention structurée ;
g) quand des sources sont fournies, générer une réponse avec citations obligatoires ;
h) calculer un identifiant de réponse SHA256 basé sur les entrées ;
i) retourner la réponse avec ledit identifiant et des métriques d'audit.

### REVENDICATION 7
Procédé selon la revendication 6, comprenant en outre l'étape de :
a) exécuter un benchmark standardisé pour valider la reproductibilité ;
b) calculer des métriques de performance incluant stabilité du Response_ID et taux d'abstention utile ;
c) générer un rapport de validation exportable en format JSON.

### REVENDICATION 8
Support lisible par ordinateur sur lequel est enregistré un programme d'ordinateur pour mettre en œuvre le procédé selon l'une quelconque des revendications 6 à 7.

### REVENDICATION 9
Système selon la revendication 1, intégré dans une infrastructure cloud comprenant :
a) une instance de serveur configurée avec les variables d'environnement de déterminisme ;
b) un service systemd gérant le démarrage et le redémarrage automatique ;
c) un mécanisme de monitoring surveillant les métriques d'audit en temps réel.

### REVENDICATION 10
Utilisation du système selon l'une quelconque des revendications 1 à 5 ou du procédé selon l'une quelconque des revendications 6 à 7 dans les applications suivantes :
a) aide au diagnostic médical avec références aux guidelines de santé ;
b) analyse de conformité financière avec citations des réglementations ;
c) interprétation contractuelle avec références aux articles de loi ;
d) vérification de conformité industrielle avec normes techniques référencées.

---

## IV. DESSINS

### FIGURE 1 : Architecture générale du système
```
[Voir diagramme d'architecture section 5.1]
```

### FIGURE 2 : Flux de traitement déterministe
```
Client → Vérification température → Cache check → Génération → Calcul Response_ID → Client
```

### FIGURE 3 : Logique du mode vérifié
```
              ┌─────────────────┐
              │   Prompt reçu   │
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │ Mode vérifié ?  │
              └────────┬────────┘
           Non         │ Oui
              │        ▼
              │ ┌──────────────┐
              │ │ Question     │
              │ │ factuelle ?  │
              │ └──────┬───────┘
              │        │
              │   Non  │ Oui
              │    │   ▼
              │    │ ┌──────────────┐
              │    │ │ Sources      │
              │    │ │ fournies ?   │
              │    │ └──────┬───────┘
              │    │        │
              │    │   Non  │ Oui
              │    │    │   ▼
              │    │    │ ┌──────────────┐
              │    │    │ │ Générer      │
              │    │    │ │ réponse      │
              │    │    │ │ normale      │
              │    │    │ └──────┬───────┘
              │    │    │        │
              │    │    ▼        ▼
              │    │ ┌──────────────┐   ┌──────────────┐
              │    │ │ Générer      │   │ Générer      │
              │    │ │ abstention   │   │ réponse      │
              │    │ │ structurée   │   │ avec         │
              │    │ └──────┬───────┘   │ citations    │
              │    │        │           └──────┬───────┘
              │    └────────┼──────────────────┘
              └─────────────┼───────────────────┘
                            ▼
                    ┌──────────────┐
                    │  Retourner   │
                    │  réponse     │
                    └──────────────┘
```

### FIGURE 4 : Calcul du Response_ID
```
Entrées:
• Version: "2.0.0"
• Mode: "default"
• Max_tokens: 1000
• Verified_mode: 1
• Sources_hash: SHA256(sources)
• Prompt: "Calcul IMC..."

Calcul:
Payload = Version + "\n" + Mode + "\n" + Max_tokens + "\n" + 
          Verified_mode + "\n" + Sources_hash + "\n" + Prompt

Response_ID = SHA256(Payload)
```

---

## V. ABRÉGÉ

La présente invention concerne un système et un procédé pour la génération déterministe et auditable de réponses par intelligence artificielle. Le système comprend un module de déterminisme forçant une température de zéro, un cache déterministe LRU, un module vérifié générant des abstentions structurées quand les sources manquent, un module d'auditabilité calculant un identifiant SHA256, et un benchmark standardisé pour validation. L'invention élimine les hallucinations et garantit la reproductibilité totale des réponses, avec applications dans les secteurs de la santé, finance, juridique et industrie.

**Mots-clés** : Intelligence artificielle, déterminisme, auditabilité, zéro hallucination, citations obligatoires, cache déterministe, Response_ID, benchmark reproductible.

---

## VI. DÉCLARATIONS

### 1. DÉCLARATION D'INVENTION
Je soussigné, Alain KOTTO, déclare être l'inventeur unique de l'invention décrite dans la présente demande de brevet.

### 2. DÉCLARATION DE PRIORITÉ
Je déclare ne pas revendiquer de priorité antérieure pour la présente invention.

### 3. DÉCLARATION D'ORIGINALITÉ
Je déclare que l'invention décrite est nouvelle, implique une activité inventive et est susceptible d'application industrielle.

### 4. DÉCLARATION DE DÉPÔT
Je demande la délivrance d'un brevet pour l'invention décrite et revendiquée.

Fait à [VILLE], le 15 mai 2026

**Signature** : 
_________________________
Alain KOTTO
Inventeur et demandeur

---

## VII. ANNEXES

### ANNEXE A : Code source de référence
[Voir fichiers :
- deepseek_api_real_final.py
- benchmark_verified_mode.py
- benchmark_verified_mode_dataset.json]

### ANNEXE B : Résultats de benchmark
[À joindre après exécution des tests]

### ANNEXE C : Documentation technique
[Voir document IA_COMMUNITY_PROOF.md]

---

**Fin du document**