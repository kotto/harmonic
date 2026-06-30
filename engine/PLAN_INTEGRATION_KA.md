# Plan d'Intégration : Harmonic AI → KA Web Complete

## Résumé

**KA Web Complete** est un prototype UI/UX sublime d'un assistant personnel IA mobile (10 espaces : Messages, Mémoire, Call, Briefing, Journey, Relation, Capture, Decide…). Tout est simulé avec 8 phrases aléatoires et du contenu statique.

**Harmonic AI** est un véritable moteur d'IA ondulatoire : 217K faits, 96.8% précision, raisonnement, créativité, mémoire conversationnelle, 0 hallucination.

**L'intégration consiste à remplacer le cerveau simulé de KA par le cerveau réel de Harmonic, sans altérer l'âme visuelle de KA.**

---

## Architecture cible

```
┌─────────────────────────────────────────┐
│  ka-web-complete/index.html             │  ← UI intacte (HTML/CSS/JS)
│  ┌───────────────────────────────────┐  │
│  │ Espaces KA (Messages, Call, etc.) │  │
│  │ → fetch() vers API Harmonic       │  │
│  └───────────────────────────────────┘  │
└──────────────┬──────────────────────────┘
               │ HTTP (localhost:8765)
┌──────────────▼──────────────────────────┐
│  engine/ka_server.py                    │  ← Nouveau : serveur API léger
│  ┌───────────────────────────────────┐  │
│  │ POST /api/chat       → ask()      │  │
│  │ POST /api/reason     → reason()   │  │
│  │ POST /api/create     → create()   │  │
│  │ POST /api/haiku      → haiku()    │  │
│  │ POST /api/memory     → memory     │  │
│  │ GET  /api/stats      → stats()    │  │
│  └───────────────────────────────────┘  │
│                                         │
│  engine/harmonic_ai.py  ← moteur réel  │
│  217K faits, 96.8% précision           │
└─────────────────────────────────────────┘
```

---

## Phase 1 : Serveur API (ka_server.py) — 30 min

Créer un micro-serveur Flask/FastAPI qui expose l'IA Harmonic.

```python
# engine/ka_server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from harmonic_ai import HarmonicAI
from reasoning_engine import ReasoningEngine

app = Flask(__name__)
CORS(app)

ai = HarmonicAI()
# Charger le modèle 50K ou 217K

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    question = data.get('message', '')
    response = ai.ask(question)
    return jsonify({'response': response, 'confidence': ...})

@app.route('/api/stats', methods=['GET'])
def stats():
    return jsonify(ai.stats)

# ... autres endpoints
```

Endpoints :
| Route | Méthode | Input | Output | Utilisé par |
|-------|---------|-------|--------|------------|
| `/api/chat` | POST | `{message, context?}` | `{response, confidence}` | Messages |
| `/api/reason` | POST | `{topic}` | `{chain}` | Briefing |
| `/api/create` | POST | `{n?}` | `{ideas: [...]}` | Insight créatif |
| `/api/haiku` | GET | — | `{haiku}` | Easter egg |
| `/api/memory/context` | GET | — | `{messages: [...]}` | Mémoire conversation |
| `/api/stats` | GET | — | `{faits, autonomie, ...}` | Debug |

---

## Phase 2 : Brancher les Espaces KA — 1h

### 2.1 Espace Messages (le cœur) — remplacement le plus critique

**Avant :** 8 phrases aléatoires (`RP` array)
**Après :** Réponse réelle de Harmonic

```javascript
// AVANT
function send() {
  let txt = K.txt.trim(); if (!txt) return;
  addMsg(txt, 'out');
  K.txt = ''; updateTxt();
  let rp = RP[Math.floor(Math.random() * RP.length)];
  setTimeout(() => addMsg(rp, 'in'), 900 + Math.random() * 400);
}

// APRÈS
async function send() {
  let txt = K.txt.trim(); if (!txt) return;
  addMsg(txt, 'out');
  K.txt = ''; updateTxt();
  addThinking(); // "KA réfléchit..."
  
  try {
    let res = await fetch('http://localhost:8765/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: txt})
    });
    let data = await res.json();
    removeThinking();
    addMsg(data.response, 'in');
  } catch(e) {
    removeThinking();
    addMsg("Je rencontre un problème technique...", 'in');
  }
}
```

### 2.2 Espace Call (voix → texte → Harmonic)

**Avant :** 4 phrases simulées tapées caractère par caractère
**Après :** Web Speech API → reconnaissance vocale → Harmonic

```javascript
// Utiliser l'API Web Speech (déjà disponible dans Chrome)
const recognition = new webkitSpeechRecognition();
recognition.lang = 'fr-FR';
recognition.onresult = (e) => {
  let transcript = e.results[0][0].transcript;
  // Envoyer à Harmonic et afficher la réponse
  fetch('/api/chat', {method:'POST', body: JSON.stringify({message: transcript})})
    .then(r => r.json())
    .then(d => showCallResponse(d.response));
};
```

### 2.3 Espace Memory — données réelles

**Avant :** Photos/messages/lieu « Rome » en dur
**Après :** Stocker les vrais échanges dans localStorage + résumé par Harmonic

```javascript
// Sauvegarder chaque échange
let memory = JSON.parse(localStorage.getItem('ka_memory') || '[]');
memory.push({role: 'user', content: question, date: new Date()});
memory.push({role: 'ka', content: response, date: new Date()});
localStorage.setItem('ka_memory', JSON.stringify(memory));
```

### 2.4 Espace Prepare (Briefing) — synthèse IA

**Avant :** « Sophie a relancé deux fois… » en dur
**Après :** Harmonic résume les échanges récents

```javascript
// Récupérer les 10 derniers messages et demander un résumé
fetch('/api/reason', {
  method: 'POST',
  body: JSON.stringify({topic: 'Résume les échanges récents avec Sophie'})
}).then(r => r.json()).then(d => showBriefing(d.chain));
```

### 2.5 Espace Decide — comparaison réelle

**Avant :** Coûts Clio vs occasion en dur
**Après :** Poser la question à Harmonic qui structure la réponse

```javascript
fetch('/api/chat', {
  method: 'POST',
  body: JSON.stringify({message: 'Compare une Clio neuve à 2340€ et une occasion à 3200€. Que choisir ?'})
}).then(r => r.json()).then(d => showDecision(d.response));
```

### 2.6 Easter Eggs

- `/haiku` → afficher dans la bulle de Messages
- `/create` → afficher une connexion créative inattendue
- `/surreal` → image surréaliste dans l'espace Capture

---

## Phase 3 : Personnalité KA — 30 min

KA a une identité visuelle forte (couleurs Soul/Life/Wisdom). L'IA doit hériter de cette identité dans son ton.

Ajouter un **system prompt** au début de chaque conversation :

```python
KA_PERSONALITY = """
Tu es KA, un assistant personnel IA intégré à un OS mobile.
Ton ton est : chaleureux, concis, utile, proactif.
Tu réponds en français, en 2-3 phrases maximum.
Tu utilises des emojis avec parcimonie.
Tu es l'interface entre l'utilisateur et un moteur d'IA ondulatoire.
"""
```

Injecter ce prompt dans `ask()` quand l'appel vient de KA.

---

## Phase 4 : Déploiement — 15 min

### Option A : Local (développement)
```bash
cd engine
python ka_server.py          # API sur :8765
cd ../ka-web-complete/ka-web-complete
npx serve . -p 3000           # UI sur :3000
```

### Option B : Production légère
- Servir `index.html` via Nginx
- Lancer `ka_server.py` avec gunicorn/uvicorn
- Ajouter un service systemd pour le serveur API

---

## Résumé des modifications

| Fichier | Action | Changements |
|---------|--------|------------|
| `engine/ka_server.py` | **CRÉER** | Serveur API Flask, 6 endpoints |
| `ka-web-complete/index.html` | **MODIFIER** | `send()` → fetch API, mémoire réelle, voix Web Speech |
| `engine/harmonic_ai.py` | **LÉGER** | Ajouter `personality` param à `ask()` |
| `ka-web-complete/manifest.json` | **AUCUN** | Déjà prêt |

## Ce qui reste INTACT

- ✅ Les 10 espaces et leur design
- ✅ Le clavier AZERTY personnalisé
- ✅ Les animations (orbe, sphère, ripple, waveform)
- ✅ La navigation et les transitions
- ✅ Les couleurs sémantiques (Soul/Life/Wisdom/Rose/Sky)
- ✅ Le responsive design (mobile/desktop)
- ✅ L'identité visuelle KA

## Ce qui devient RÉEL

- ❌ 8 phrases aléatoires → ✅ IA ondulatoire 217K faits, 96.8% précision
- ❌ Voix simulée → ✅ Reconnaissance vocale Web Speech API
- ❌ Insights en dur → ✅ Générés par l'IA
- ❌ Mémoire statique → ✅ Historique réel + résumés
- ❌ Décisions fictives → ✅ Analyse comparative réelle
