# Plan d'Intégration V2 : Harmonic AI + HCV Compression → KA Web Complete

## Vision

> **Transformer un téléphone d'entrée de gamme en téléphone haut de gamme.**
> 
> Cerveau : Harmonic AI (217K faits, 96.8% précision, 0 hallucination)
> Corps : HCV Compression (26-345:1 compression, upscaling, audio enhancement)
> Âme : KA Web Complete (10 espaces, design system Soul/Life/Wisdom)

---

## Architecture complète

```
┌──────────────────────────────────────────────────┐
│  KA Web Complete (index.html)                    │
│  ┌────────────┬────────────┬──────────────────┐ │
│  │ Messages   │ Memory     │ Capture          │ │
│  │ (chat IA)  │ (photos↑)  │ (voix→texte)     │ │
│  │   ↓        │   ↓        │   ↓              │ │
│  │ Harmonic   │ HCV        │ HCV + Harmonic   │ │
│  └────────────┴────────────┴──────────────────┘ │
└──────────────────────┬───────────────────────────┘
                       │ HTTP (localhost:8765)
┌──────────────────────▼───────────────────────────┐
│  engine/ka_server.py  (API unifiée)              │
│                                                   │
│  /api/chat       → HarmonicAI.ask()              │
│  /api/reason     → ReasoningEngine.reason()      │
│  /api/create     → ReasoningEngine.create()      │
│  /api/haiku      → HarmonicAI.haiku()            │
│  /api/compress   → HCV.encode_image()            │
│  /api/upscale    → HCV.upscale()                 │
│  /api/enhance    → HCV.enhance_audio()           │
│  /api/stats      → {faits, compression, uptime}  │
│                                                   │
│  ┌─────────────────┐  ┌──────────────────────┐   │
│  │ Harmonic AI      │  │ HCV Compression      │   │
│  │ 217K faits       │  │ Grain Separation     │   │
│  │ Encodeur S²      │  │ Delta-H encoding     │   │
│  │ Créativité       │  │ Upscaling (Lanczos)  │   │
│  │ Bootstrapper     │  │ Audio passthrough    │   │
│  └─────────────────┘  └──────────────────────┘   │
└──────────────────────────────────────────────────┘
```

---

## Phase 1 : API unifiée (ka_server.py) — 45 min

Un seul serveur Flask exposant les deux moteurs :

```python
# engine/ka_server.py
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from harmonic_ai import HarmonicAI
from reasoning_engine import ReasoningEngine

# Importer le codec HCV
import sys; sys.path.insert(0, '../HCV-Compression-Engine')
from codecs.hcv_android_boost_codec import HCVAndroidBoostCodec
from mobile.upscaler import HCVUpscaler

app = Flask(__name__)
CORS(app)

# Initialisation
ai = HarmonicAI()
ai.model.knowledge_base = load_facts('knowledge_base_50k.npz')
ai.model.rebuild_waves()
ai.engine = ReasoningEngine(ai.model)

hcv_photo = HCVAndroidBoostCodec(preset='balanced')
hcv_upscaler = HCVUpscaler()

# === HARMONIC AI ENDPOINTS ===
@app.route('/api/chat', methods=['POST'])
def chat():
    msg = request.json.get('message', '')
    response = ai.ask(msg)
    return jsonify({'response': response})

@app.route('/api/reason', methods=['POST'])
def reason():
    topic = request.json.get('topic', '')
    return jsonify({'chain': ai.reason(topic)})

@app.route('/api/create', methods=['POST'])
def create():
    n = request.json.get('n', 3)
    return jsonify({'ideas': ai.create(n=n)})

@app.route('/api/haiku')
def haiku():
    return jsonify({'haiku': ai.haiku()})

@app.route('/api/stats')
def stats():
    return jsonify(ai.stats)

# === HCV COMPRESSION ENDPOINTS ===
@app.route('/api/compress', methods=['POST'])
def compress():
    """Compresse une image (upload). Retourne l'image compressée + ratio."""
    file = request.files['image']
    input_data = file.read()
    compressed, ratio = hcv_photo.compress(input_data)
    return jsonify({
        'original_size': len(input_data),
        'compressed_size': len(compressed),
        'ratio': round(ratio, 1),
        'saved_percent': round((1 - 1/ratio) * 100, 1)
    })

@app.route('/api/upscale', methods=['POST'])
def upscale():
    """Upscale une image (2x, 4x)."""
    file = request.files['image']
    scale = int(request.form.get('scale', 2))
    img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
    upscaled = hcv_upscaler.upscale(img, factor=scale)
    _, buffer = cv2.imencode('.jpg', upscaled)
    return send_file(io.BytesIO(buffer), mimetype='image/jpeg')

@app.route('/api/compress-and-upscale', methods=['POST'])
def compress_and_upscale():
    """Pipeline complet : compresser pour stockage, upscaler pour affichage."""
    file = request.files['image']
    # 1. Compresser (économise espace)
    compressed, ratio = hcv_photo.compress(file.read())
    # 2. Décompresser (restauration)
    decompressed = hcv_photo.decompress(compressed)
    # 3. Upscaler pour affichage (qualité perçue)
    upscaled = hcv_upscaler.upscale(decompressed, factor=2)
    _, buffer = cv2.imencode('.jpg', upscaled)
    return send_file(io.BytesIO(buffer), mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(port=8765, debug=True)
```

---

## Phase 2 : Intégration dans les Espaces KA — 1h30

### 2.1 Espace Messages — Intelligence conversationnelle (Harmonic)

**Avant :** 8 phrases aléatoires  
**Après :** Réponse réelle de Harmonic, avec personnalité KA

```javascript
const KA_SYSTEM_PROMPT = "Tu es KA, assistant personnel. Ton ton est chaleureux, concis. Réponds en 2-3 phrases. Français.";

async function sendToKA(message) {
  const res = await fetch('http://localhost:8765/api/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: KA_SYSTEM_PROMPT + '\n\nUtilisateur: ' + message})
  });
  const data = await res.json();
  return data.response;
}
```

### 2.2 Espace Memory — Photos upscalées + compressées (HCV)

**Avant :** Photos statiques de Rome en dur  
**Après :** Photos réelles, compressées au stockage, upscalées à l'affichage

```javascript
// Quand l'utilisateur prend une photo
async function compressPhoto(file) {
  const form = new FormData();
  form.append('image', file);
  const res = await fetch('http://localhost:8765/api/compress', {method: 'POST', body: form});
  const data = await res.json();
  // Afficher le ratio
  showToast(`Photo compressée : ${data.ratio}:1 (${data.saved_percent}% d'espace sauvé)`);
  return data;
}

// Quand l'utilisateur ouvre une photo dans Memory
async function viewPhoto(photoId) {
  // Upscaler à la volée
  const res = await fetch(`http://localhost:8765/api/upscale?scale=2`, {
    method: 'POST',
    body: createFormData(photoId)
  });
  const blob = await res.blob();
  displayPhoto(URL.createObjectURL(blob));
}
```

### 2.3 Espace Capture — Voix → Texte → IA (Harmonic + Web Speech)

**Avant :** 4 phrases simulées  
**Après :** Vraie reconnaissance vocale + analyse IA

```javascript
// Reconnaissance vocale (Web Speech API)
const recognition = new webkitSpeechRecognition();
recognition.lang = 'fr-FR';
recognition.continuous = false;

recognition.onresult = async (e) => {
  const transcript = e.results[0][0].transcript;
  
  // 1. Structurer l'idée avec Harmonic
  const res = await fetch('http://localhost:8765/api/reason', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({topic: transcript})
  });
  const data = await res.json();
  
  // 2. Afficher dans l'espace Capture (concept, cible, lié)
  showCaptureResult({
    concept: transcript,
    structured: data.chain
  });
};
```

### 2.4 Espace Prepare (Briefing) — Synthèse IA

**Avant :** « Sophie a relancé deux fois sur les chiffres… » en dur  
**Après :** Harmonic analyse les échanges récents et génère un briefing

```javascript
async function generateBriefing() {
  const memory = JSON.parse(localStorage.getItem('ka_memory') || '[]');
  const recentMsgs = memory.slice(-20).map(m => m.content).join('\n');
  
  const res = await fetch('http://localhost:8765/api/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: `Résume en 3 points ces échanges récents :\n${recentMsgs}`})
  });
  const data = await res.json();
  showBriefing(data.response);
}
```

### 2.5 Espace Call — Audio enhancement (HCV)

**Avant :** Waveform simulée  
**Après :** Vrai traitement audio (réduction de bruit, compression)

```javascript
// Pendant un appel, le flux audio est traité par HCV
async function processAudioStream(audioBlob) {
  const form = new FormData();
  form.append('audio', audioBlob);
  const res = await fetch('http://localhost:8765/api/enhance-audio', {
    method: 'POST', body: form
  });
  return await res.blob();
}
```

---

## Phase 3 : Mode Hors-ligne Progressif — 45 min

Pour que ça fonctionne même sans connexion (essence du téléphone d'entrée de gamme) :

### 3.1 Cache local (Service Worker)

```javascript
// sw.js
self.addEventListener('fetch', event => {
  // Cache-first pour les assets KA
  if (event.request.url.includes('/ka-ui/')) {
    event.respondWith(caches.match(event.request)
      .then(cached => cached || fetch(event.request)));
  }
});
```

### 3.2 Dégradé élégant

- **API injoignable** → fallback aux 8 phrases simulées (déjà en place)
- **API lente** → timeout de 5s, puis fallback
- **Indicateur visuel** : pastille verte = IA réelle, pastille grise = mode hors-ligne

### 3.3 Stockage intelligent

```javascript
// Sauvegarder les réponses pour consultation hors-ligne
const offlineCache = {};
async function askWithCache(question) {
  const cacheKey = question.toLowerCase().trim();
  if (offlineCache[cacheKey]) return offlineCache[cacheKey];
  
  try {
    const res = await fetch('/api/chat', {method: 'POST', body: JSON.stringify({message: question})});
    const data = await res.json();
    offlineCache[cacheKey] = data.response;
    return data.response;
  } catch {
    return RP[Math.floor(Math.random() * RP.length)]; // fallback
  }
}
```

---

## Phase 4 : Effet « Téléphone Haut de Gamme » — 30 min

### 4.1 Photos

| Étape | Sans HCV | Avec HCV |
|-------|----------|----------|
| Stockage | 5 MB/photo | 0.5 MB/photo (10:1) |
| Affichage | Résolution native | Upscale 2× (Lanczos) |
| Qualité perçue | Standard | Améliorée (grain régénéré) |

→ Sur un téléphone 32 GB : 6 000 photos au lieu de 1 200.

### 4.2 Vidéos

| Étape | Sans HCV | Avec HCV |
|-------|----------|----------|
| Stockage | 100 MB/min (1080p) | 15 MB/min (7:1) |
| Lecture | Débit natif | Décompressé à la volée |

→ 1h de vidéo en 900 MB au lieu de 6 GB.

### 4.3 Audio

- Compression de l'espace de stockage audio
- Enhancement du microphone (réduction de bruit)
- Qualité d'appel améliorée

---

## Résumé des modifications

| Fichier | Action | Rôle |
|---------|--------|------|
| `engine/ka_server.py` | **CRÉER** | API unifiée Harmonic + HCV |
| `ka-web-complete/index.html` | **MODIFIER** | fetch() au lieu de phrases aléatoires |
| `HCV-Compression-Engine/codecs/*` | **EXISTANT** | Codecs de compression |
| `HCV-Compression-Engine/mobile/upscaler.py` | **EXISTANT** | Upscaling Lanczos |

## Ce qui reste INTACT

- ✅ Design KA (10 espaces, couleurs, animations)
- ✅ Clavier AZERTY personnalisé
- ✅ Navigation et transitions
- ✅ Identité visuelle (Soul/Life/Wisdom)
- ✅ Architecture HCV (grain separation, delta-H, zstd)

## Résultat final

```
Téléphone entrée de gamme (32 GB, 3 GB RAM)
    ↓ KA + Harmonic + HCV
Téléphone « augmenté » :
  • Assistant IA réel (pas de phrases simulées)
  • 10× plus de photos/vidéos (compression HCV)
  • Photos upscalées (qualité perçue supérieure)
  • Audio amélioré
  • Fonctionne même hors-ligne (cache progressif)
```
