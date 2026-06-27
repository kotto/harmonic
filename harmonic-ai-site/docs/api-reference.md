# Harmonic AI - API Reference

Documentation complète de l'API Harmonic AI pour l'intégration de l'IA déterministe dans vos applications.

## 📋 Table des Matières

1. [Introduction](#introduction)
2. [Authentification](#authentification)
3. [Endpoints](#endpoints)
4. [Paramètres](#paramètres)
5. [Réponses](#réponses)
6. [Codes d'Erreur](#codes-derreur)
7. [Limitations](#limitations)
8. [Exemples](#exemples)
9. [Bonnes Pratiques](#bonnes-pratiques)

## 🎯 Introduction

L'API Harmonic AI permet d'accéder à notre technologie d'IA déterministe avec garantie de reproductibilité et auditabilité totale.

### Caractéristiques Clés
- **Déterminisme** : Même prompt ⇒ même sortie (bit-for-bit)
- **Mode Vérifié** : Citations obligatoires pour les affirmations factuelles
- **Auditabilité** : Response_ID SHA256 pour chaque réponse
- **Performance** : Latence moyenne < 250ms

### URL de Base
```
https://api.harmonic.ai/v1
```

## 🔐 Authentification

Toutes les requêtes API nécessitent une clé API valide.

### En-tête d'Authentification
```http
Authorization: Bearer YOUR_API_KEY
```

### Obtention d'une Clé API
1. Créez un compte sur [harmonic-ai.com](https://www.harmonic-ai.com)
2. Accédez à la section API dans votre tableau de bord
3. Générez une nouvelle clé API
4. Stockez-la en sécurité (jamais en clair dans le code)

### Sécurité
- Utilisez toujours HTTPS
- Ne partagez jamais votre clé API
- Régénérez régulièrement vos clés
- Utilisez des variables d'environnement

## 📡 Endpoints

### 1. Génération de Réponse
```http
POST /generate
```

Génère une réponse déterministe à partir d'un prompt.

#### Requête
```json
{
  "prompt": "Explain quantum computing",
  "max_tokens": 200,
  "temperature": 0.0,
  "verified_mode": true,
  "sources": [
    {
      "id": "S1",
      "content": "Quantum computing uses qubits...",
      "url": "https://example.com/source1"
    }
  ]
}
```

#### Réponse
```json
{
  "response": "Quantum computing uses quantum bits (qubits)...",
  "response_id": "SHA256-4a7b9c8d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4",
  "verified": true,
  "citations": [
    {
      "source_id": "S1",
      "relevance": 0.95,
      "confidence": 0.98
    }
  ],
  "cache_hit": false,
  "processing_time_ms": 245,
  "model_version": "harmonic-v2.1",
  "timestamp": "2026-05-15T10:30:45.123Z"
}
```

### 2. Vérification de Statut
```http
GET /status
```

Vérifie le statut de l'API et les quotas.

#### Requête
Aucun corps requis.

#### Réponse
```json
{
  "status": "operational",
  "version": "v2.1",
  "uptime": "99.95%",
  "rate_limit": {
    "remaining": 4950,
    "reset_in": 3600
  },
  "timestamp": "2026-05-15T10:30:45.123Z"
}
```

### 3. Historique des Requêtes
```http
GET /history
```

Récupère l'historique des requêtes récentes.

#### Paramètres de Requête
- `limit` : Nombre d'entrées à retourner (max 100)
- `offset` : Décalage pour la pagination

#### Réponse
```json
{
  "requests": [
    {
      "request_id": "req_123456",
      "prompt": "Explain quantum computing",
      "response_id": "SHA256-4a7b9c8d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4",
      "timestamp": "2026-05-15T10:30:45.123Z",
      "processing_time_ms": 245
    }
  ],
  "total": 150,
  "limit": 10,
  "offset": 0
}
```

## ⚙️ Paramètres

### Paramètres Obligatoires

#### `prompt` (string)
Le texte d'entrée pour la génération.
- **Longueur max** : 4096 caractères
- **Encodage** : UTF-8
- **Exemple** : `"Explain quantum computing"`

#### `max_tokens` (integer)
Nombre maximum de tokens à générer.
- **Min** : 1
- **Max** : 2048
- **Recommandé** : 200-500

### Paramètres Optionnels

#### `temperature` (float)
Contrôle le caractère aléatoire des réponses.
- **Min** : 0.0 (déterministe)
- **Max** : 1.0
- **Défaut** : 0.0
- **Important** : Pour le déterminisme, utilisez toujours `0.0`

#### `verified_mode` (boolean)
Active le mode vérifié avec citations obligatoires.
- **Défaut** : `true`
- **Impact** : Réduction de 99% des hallucinations

#### `sources` (array)
Liste de sources pour la vérification.
```json
{
  "sources": [
    {
      "id": "S1",
      "content": "Source content...",
      "url": "https://example.com/source1",
      "type": "article",
      "date": "2026-01-15"
    }
  ]
}
```

## 📊 Réponses

### Structure de Réponse Standard

```json
{
  "response": "Generated text...",
  "response_id": "SHA256-hash",
  "verified": true,
  "citations": [],
  "cache_hit": false,
  "processing_time_ms": 245,
  "model_version": "harmonic-v2.1",
  "timestamp": "2026-05-15T10:30:45.123Z"
}
```

### Champs de Réponse

#### `response` (string)
La réponse générée par l'IA.

#### `response_id` (string)
Identifiant unique SHA256 calculé sur :
- Prompt
- Paramètres
- Réponse générée

#### `verified` (boolean)
Indique si la réponse a été générée en mode vérifié.

#### `citations` (array)
Liste des citations utilisées.
```json
{
  "source_id": "S1",
  "relevance": 0.95,
  "confidence": 0.98,
  "text": "Relevant text from source..."
}
```

#### `cache_hit` (boolean)
Indique si la réponse provient du cache.

#### `processing_time_ms` (integer)
Temps de traitement en millisecondes.

#### `model_version` (string)
Version du modèle utilisé.

#### `timestamp` (string)
Horodatage ISO 8601 de la réponse.

## 🚨 Codes d'Erreur

### Codes HTTP

| Code | Description | Solution |
|------|-------------|----------|
| 200 | Succès | - |
| 400 | Requête invalide | Vérifiez les paramètres |
| 401 | Non autorisé | Vérifiez votre clé API |
| 403 | Interdit | Vérifiez vos permissions |
| 404 | Non trouvé | Vérifiez l'URL |
| 429 | Trop de requêtes | Respectez les limites |
| 500 | Erreur serveur | Réessayez plus tard |
| 503 | Service indisponible | Maintenance en cours |

### Erreurs d'API

```json
{
  "error": {
    "code": "invalid_prompt",
    "message": "Prompt exceeds maximum length",
    "details": {
      "max_length": 4096,
      "actual_length": 4500
    }
  }
}
```

### Codes d'Erreur Courants

| Code | Description |
|------|-------------|
| `invalid_prompt` | Prompt invalide |
| `rate_limit_exceeded` | Limite de débit dépassée |
| `insufficient_quota` | Quota insuffisant |
| `model_unavailable` | Modèle indisponible |
| `verification_failed` | Échec de vérification |

## 📈 Limitations

### Quotas

| Plan | Requêtes/min | Tokens/jour | Cache |
|------|-------------|-------------|-------|
| Démo | 10 | 10,000 | 1,024 |
| Développeur | 60 | 100,000 | 2,048 |
| Entreprise | 1,000 | 1,000,000 | 8,192 |

### Limitations Techniques

#### Longueur de Prompt
- **Max** : 4,096 caractères
- **Optimal** : 500-1,000 caractères

#### Génération de Tokens
- **Max par requête** : 2,048 tokens
- **Recommandé** : 200-500 tokens

#### Taille de Cache
- **Entries max** : Selon le plan
- **TTL** : 1 heure (configurable)

#### Latence
- **Moyenne** : < 250ms
- **P95** : < 450ms
- **P99** : < 800ms

## 💻 Exemples

### Python

```python
import requests
import os

class HarmonicAI:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('HARMONIC_API_KEY')
        self.base_url = "https://api.harmonic.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate(self, prompt, max_tokens=200, temperature=0.0, verified_mode=True):
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "verified_mode": verified_mode
        }
        
        response = requests.post(
            f"{self.base_url}/generate",
            json=payload,
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API Error: {response.status_code} - {response.text}")
    
    def get_status(self):
        response = requests.get(
            f"{self.base_url}/status",
            headers=self.headers
        )
        return response.json()

# Utilisation
client = HarmonicAI(api_key="your_api_key")

# Génération
result = client.generate(
    prompt="Explain quantum computing",
    max_tokens=200,
    temperature=0.0,
    verified_mode=True
)

print(f"Response: {result['response']}")
print(f"Response ID: {result['response_id']}")
print(f"Processing time: {result['processing_time_ms']}ms")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

class HarmonicAI {
    constructor(apiKey) {
        this.apiKey = apiKey || process.env.HARMONIC_API_KEY;
        this.baseURL = 'https://api.harmonic.ai/v1';
        this.client = axios.create({
            baseURL: this.baseURL,
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json'
            }
        });
    }

    async generate(prompt, options = {}) {
        const {
            maxTokens = 200,
            temperature = 0.0,
            verifiedMode = true,
            sources = []
        } = options;

        const payload = {
            prompt,
            max_tokens: maxTokens,
            temperature,
            verified_mode: verifiedMode,
            sources
        };

        try {
            const response = await this.client.post('/generate', payload);
            return response.data;
        } catch (error) {
            throw new Error(`API Error: ${error.response?.status} - ${error.response?.data?.error?.message}`);
        }
    }

    async getStatus() {
        try {
            const response = await this.client.get('/status');
            return response.data;
        } catch (error) {
            throw new Error(`API Error: ${error.response?.status}`);
        }
    }
}

// Utilisation
const client = new HarmonicAI('your_api_key');

async function test() {
    try {
        const result = await client.generate('Explain quantum computing', {
            maxTokens: 200,
            temperature: 0.0,
            verifiedMode: true
        });

        console.log('Response:', result.response);
        console.log('Response ID:', result.response_id);
        console.log('Processing time:', result.processing_time_ms, 'ms');
    } catch (error) {
        console.error('Error:', error.message);
    }
}

test();
```

### cURL

```bash
# Génération de réponse
curl -X POST "https://api.harmonic.ai/v1/generate" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing",
    "max_tokens": 200,
    "temperature": 0.0,
    "verified_mode": true
  }'

# Vérification de statut
curl -X GET "https://api.harmonic.ai/v1/status" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## 🏆 Bonnes Pratiques

### 1. Gestion des Erreurs
```python
try:
    result = client.generate(prompt)
except Exception as e:
    # Log l'erreur
    logger.error(f"Generation failed: {e}")
    # Fallback stratégique
    result = get_fallback_response(prompt)
```

### 2. Optimisation des Performances
```python
# Utilisez le cache
if cache.has(prompt_hash):
    return cache.get(prompt_hash)

# Limitez la taille des prompts
if len(prompt) > 1000:
    prompt = summarize_prompt(prompt)
```

### 3. Sécurité
```python
# Ne stockez jamais la clé API en clair
api_key = os.getenv('HARMONIC_API_KEY')

# Validez les entrées utilisateur
sanitized_prompt = sanitize_user_input(user_prompt)
```

### 4. Monitoring
```python
# Suivez les métriques
metrics = {
    'response_time': result['processing_time_ms'],
    'cache_hit': result['cache_hit'],
    'verified': result['verified']
}

# Alertes sur les erreurs
if result.get('error'):
    send_alert(f"API Error: {result['error']}")
```

### 5. Évolutivité
```python
# Implémentez le retry
for attempt in range(3):
    try:
        result = client.generate(prompt)
        break
    except Exception:
        if attempt == 2:
            raise
        time.sleep(2 ** attempt)
```

## 🔄 Mises à Jour

### Versioning
- **Format** : `vX.Y.Z`
- **X** : Breaking changes
- **Y** : Nouvelles fonctionnalités
- **Z** : Corrections de bugs

### Historique des Versions

| Version | Date | Changements |
|---------|------|-------------|
| v2.1 | 2026-05-15 | Améliorations de performance |
| v2.0 | 2026-04-01 | Mode vérifié, cache LRU |
| v1.0 | 2026-01-15 | Version initiale |

### Dépréciations
Les endpoints dépréciés retournent un avertissement :
```json
{
  "warning": "This endpoint is deprecated and will be removed in v3.0",
  "alternative": "/v2/generate"
}
```

## 📞 Support

### Ressources
- **Documentation** : [docs.harmonic.ai](https://docs.harmonic.ai)
- **Forum** : [community.harmonic.ai](https://community.harmonic.ai)
- **GitHub** : [github.com/harmonic-ai](https://github.com/harmonic-ai)

### Contact
- **Support technique** : support@harmonic-ai.com
- **Commercial** : sales@harmonic-ai.com
- **Urgences** : +33 1 23 45 67 89

### SLA
- **Disponibilité** : 99.95%
- **Temps de réponse** : < 4 heures
- **Support 24/7** : Pour les clients entreprise

---

**Dernière mise à jour** : 2026-05-15  
**Version du document** : 2.1.0

© 2026 Harmonic AI Corporation. Tous droits réservés.