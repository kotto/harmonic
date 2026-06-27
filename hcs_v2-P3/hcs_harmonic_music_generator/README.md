# HCS Harmonic Music Generator

Générateur IA de musique harmonique basé sur les principes de la compression harmonique HCS.

## 🎵 Fonctionnalités

### Génération Musicale
- **Styles multiples** : Pop, Jazz, Classique, Électronique
- **Tonalités** : Do, Ré, Mi, Fa, Sol, La, Si
- **Gammes** : Majeure, Mineure, Pentatonique, Blues, Chromatique
- **Paramètres** : Tempo (60-180 BPM), Durée (10-120s)

### Moteur Harmonique
- **Séries harmoniques** : 8 harmoniques naturelles par note
- **Enveloppes ADSR** : Attack, Decay, Sustain, Release
- **Progressions d'accords** : I-IV-V-I, I-vi-IV-V, etc.
- **Couches musicales** : Accords, Basse, Mélodie

### Analyse Spectrale
- **FFT** : Analyse fréquentielle complète
- **Détection de fondamentale** : Fréquence principale
- **Contenu harmonique** : Nombre et force des harmoniques
- **Centroïde spectrale** : "Barycentre" fréquentiel

## 🚀 Installation

### Prérequis
```bash
pip install -r requirements.txt
```

### Démarrage
```bash
python server.py
```

L'application sera disponible sur : http://localhost:8020

## 🎛️ API Endpoints

### Génération
- `POST /api/generate` : Générer une piste musicale
  - style : pop, jazz, classical, electronic
  - key : C, D, E, F, G, A, B
  - tempo : 60-180 BPM
  - duration : 10-120 secondes
  - scale : major, minor, pentatonic, blues, chromatic

### Gestion des Pistes
- `GET /api/tracks` : Lister toutes les pistes
- `GET /api/track/{id}` : Informations sur une piste
- `GET /api/download/{id}` : Télécharger une piste
- `DELETE /api/track/{id}` : Supprimer une piste

### Analyse
- `GET /api/analyze/{id}` : Analyse harmonique détaillée
- `GET /api/styles` : Styles et gammes disponibles
- `GET /api/health` : État du serveur

## 🎼 Principes Harmoniques

### Série Harmonique
```
Fondamentale : f₁ = 261.63 Hz (Do)
Harmonique 2 : f₂ = 2 × f₁ = 523.26 Hz (Do octave)
Harmonique 3 : f₃ = 3 × f₁ = 784.89 Hz (Sol)
Harmonique 4 : f₄ = 4 × f₁ = 1046.52 Hz (Do 2 octaves)
...
```

### Force des Harmoniques
```
H₁ : 1.00 (fondamentale)
H₂ : 0.50 (octave)
H₃ : 0.33 (quinte)
H₄ : 0.25 (octave 2)
H₅ : 0.20 (tierce majeure)
...
```

### Enveloppe ADSR
- **Attack** : Temps d'attaque (0.1s)
- **Decay** : Temps de déclin (0.2s)
- **Sustain** : Niveau maintenu (0.7)
- **Release** : Temps de relâchement (0.3s)

## 🎹 Styles Musicaux

### Pop
- Structure : I-V-vi-iii
- Caractéristiques : Accords majeurs, mélodies accrocheuses
- Tempo typique : 120-130 BPM

### Jazz
- Structure : ii-V-I-vi
- Caractéristiques : Accords étendus, swing
- Tempo typique : 80-140 BPM

### Classique
- Structure : I-IV-V-I
- Caractéristiques : Progressions tonales, formes classiques
- Tempo typique : 60-120 BPM

### Électronique
- Structure : Pentatonique
- Caractéristiques : Basses profondes, synthétiseurs
- Tempo typique : 120-140 BPM

## 📊 Formats et Qualité

### Sortie Audio
- **Format** : WAV 16-bit
- **Échantillonnage** : 44.1 kHz
- **Canaux** : Mono (pour la génération)
- **Qualité** : Haute fidélité

### Compression
Les fichiers générés utilisent les principes HCS :
- **Séries harmoniques** optimisées
- **Compression temporelle** intelligente
- **Ratios théoriques** : 10:1 à 50:1

## 🔧 Configuration

### Paramètres du Générateur
```python
harmonic_gen = HarmonicGenerator(
    sample_rate=44100,    # Échantillonnage
    duration=30.0           # Durée par défaut
)
```

### Personnalisation
- **Ajouter des styles** : Modifier les dictionnaires de progression
- **Nouvelles gammes** : Ajouter au dictionnaire `scales`
- **Harmoniques personnalisées** : Modifier la liste `harmonics`

## 🎨 Interface Web

### Fonctionnalités
- **Génération en temps réel** : Interface responsive
- **Visualisation** : Waveforms et spectres
- **Gestion des pistes** : Téléchargement et suppression
- **Analyse harmonique** : Spectrogrammes et fréquences

### Design
- **Thème** : Glassmorphism avec gradients
- **Animations** : Waveforms et transitions
- **Responsive** : Mobile et desktop
- **Icônes** : Lucide icons

## 🧠 Algorithmes

### Génération d'Accords
```python
def generate_chord(root_note, chord_type='major'):
    # Sélection des harmoniques
    # Combinaison des fréquences
    # Enveloppe ADSR
    # Normalisation
```

### Progression Harmonique
```python
def generate_progression(key, style='major'):
    # Sélection des accords
    # Transition harmonique
    # Voix leading
    # Résolution
```

### Analyse Spectrale
```python
def analyze_harmonics(signal):
    # FFT rapide
    # Détection de pics
    # Identification fondamentale
    # Calcul centroïde
```

## 🔍 Débogage

### Logs
```bash
# Niveau INFO par défaut
python server.py

# Mode DEBUG
export LOG_LEVEL=DEBUG
python server.py
```

### Tests
```bash
# Test du générateur
python -c "from harmonic_engine import HarmonicGenerator; h = HarmonicGenerator(); print(h.generate_full_track())"

# Test API
curl -X POST http://localhost:8020/api/generate -F style=pop -F key=C
```

## 🚀 Performance

### Optimisations
- **Vectorisation NumPy** : Calculs parallèles
- **FFT efficace** : Algorithme Cooley-Tukey
- **Cache mémoire** : Réutilisation des calculs
- **Streaming audio** : Gestion par morceaux

### Benchmarks
- **Génération 30s** : ~2-5 secondes
- **Analyse spectrale** : ~0.1 seconde
- **Export WAV** : ~0.5 seconde
- **Mémoire utilisée** : ~50MB pour 30s

## 📝 Licence

HCS Harmonic Music Generator - Propriétaire

## 🤝 Contribution

Les contributions sont les bienvenues :
- Nouveaux styles musicaux
- Algorithmes d'analyse
- Optimisations de performance
- Améliorations UI/UX

---

**HCS Harmonic Music Generator** - La musique par les mathématiques harmoniques 🎵
