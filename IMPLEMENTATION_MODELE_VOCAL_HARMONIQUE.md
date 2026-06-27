# Implémentation du Modèle Vocal Harmonique de Haute Qualité — Résumé Exécutif

*Document de continuité — 26 Juin 2026 — à reprendre en section séparée*

---

## 1. Contexte

Ce document résume les décisions architecturales et spécifications techniques pour la création d'un **modèle vocal harmonique de haute qualité**, extraites de l'analyse prospective complète (`ANALYSE_PROSPECTIVE_PHYSIQUE_HARMONIQUE.md`, Annexe N).

**Objectif :** Disposer d'une synthèse vocale pilotée par le moteur harmonique (SpectralMessage → audio), sans dépendance à un LLM externe, avec une qualité audio de niveau professionnel.

---

## 2. Architecture Cible

```
SpectralMessage (du moteur harmonique)
       │
       ├──→ Décodeur Texte → TEXTE AFFICHÉ
       │
       └──→ Décodeur Vocal  → AUDIO (WAV/MP3)
                │
                ├── Signature vocale extraite des corpus de référence
                ├── Pilotage direct des paramètres prosodiques
                └── Synthèse par harmoniques φ-spaced (futur)
```

**Principe clé :** Le SpectralMessage contient déjà TOUS les paramètres prosodiques (ton émotionnel, registre, urgence, complexité). Le décodeur vocal n'a pas à les deviner — il les reçoit directement.

---

## 3. Décisions Techniques

| Composant | Choix | Justification |
|-----------|-------|---------------|
| **Vocodeur** | HiFi-GAN v2 ou BigVGAN | Meilleure qualité audio actuelle |
| **Analyse prosodique** | Parselmouth (wrapper Praat) | Standard académique f₀, formants |
| **Embedding locuteur** | SpeechBrain ECAPA-TDNN | SOTA reconnaissance locuteur |
| **Fine-tuning** | LoRA sur modèle pré-entraîné | ~500 €, quelques heures A100 |
| **Évaluation** | MOS (> 4.0/5) + MCD | Standards industriels |

---

## 4. Corpus de Référence (8 sources)

| Source | Volume | Qualité | Usage |
|--------|--------|---------|-------|
| **Common Voice** (Mozilla) | 20 000h+, 100+ langues | Variable | Masse multilingue |
| **LibriSpeech** | 1 000h anglais | Haute | Base propre |
| **VCTK** | 110 locuteurs anglais | Studio | Diversité timbres |
| **LJSpeech** | 24h, 1 voix féminine | Excellente | Référence mono-locuteur |
| **CSS10** | 10 langues | Bonne | Base multilingue |
| **LibriTTS** | 585h anglais | Très haute | **Entraînement principal** |
| **Fleurs** (Google) | 100+ langues | Bonne à très bonne | Couverture linguistique |
| **TED-LIUM** | Conférences TED | Très haute | Prosodie naturelle |

**Total : ~22 000 heures téléchargeables librement.**

---

## 5. Extraction des Signatures Vocales

Chaque voix est caractérisée par **11 dimensions harmoniques** :

| Dimension | Mesure | Paramètre TTS piloté |
|-----------|--------|---------------------|
| H_pitch_mean | f₀ moyen | Pitch de base |
| H_pitch_range | Écart-type f₀ | Variation de hauteur |
| H_speed | Débit syllabique | Speaking rate |
| H_timbre | Centroïde spectral | Formant shift |
| H_breathiness | Ratio bruit/harmonique | Mix voiced/unvoiced |
| H_resonance | Alignement φ des formants | Espacement harmonique |
| H_emotion_range | Plage expressive | Pitch variability (jitter) |
| H_clarity | Netteté articulatoire | Réduction de bruit |
| H_pause_pattern | Pattern de pauses | Pause insertion |
| H_phi_alignment | Score φ global | Qualité harmonique |
| H_naturalness | Score MOS-like | Qualité perçue |

---

## 6. Banque de Profils Vocaux de Référence (Top 6)

| Profil | Source | f₀ | Plage φ | Style |
|--------|--------|-----|---------|-------|
| Femme narrative US | LJSpeech | 220 Hz | 0.72 | Chaleureuse, pédagogique |
| Homme neutre UK | VCTK p225 | 110 Hz | 0.68 | Posée, académique |
| Femme dynamique UK | VCTK p227 | 200 Hz | 0.74 | Expressive, média |
| Conférencière US | TED speaker 1 | 130 Hz | 0.81 | Autorité, conviction |
| 10 profils divers | LibriTTS best | 100-250 Hz | 0.65-0.82 | Polyvalence |
| Français natif | CSS10 FR | 180 Hz | 0.70 | Langue cible |

---

## 7. Feuille de Route d'Implémentation

| Étape | Durée | Livrable | Dépendances |
|-------|-------|----------|-------------|
| **1. Téléchargement corpus** | 1 jour | ~2 TB données audio | Stockage |
| **2. Extraction signatures** | 3 jours | 50 000 signatures 11D + métadonnées | Parselmouth, Python |
| **3. Sélection Top 20 voix** | 1 jour | 20 profils de référence | Étape 2 |
| **4. Entraînement décodeur** | 1 semaine | Modèle mapping SpectralMessage → paramètres vocaux (CPU, < 50 MB) | Étape 3 |
| **5. Fine-tuning vocodeur** | 3 jours | HiFi-GAN φ-spaced (~200 € GPU) | Étape 4 |
| **6. Évaluation MOS** | 2 jours | Test ABX 30 auditeurs, cible MOS > 4.0 | Étape 5 |
| **TOTAL** | **~3 semaines** | **Décodeur vocal harmonique opérationnel** | |

---

## 8. Code à Implémenter (Classes clés)

### 8.1 VoiceSignatureExtractor
```python
class VoiceSignatureExtractor:
    def extract(self, audio_path) -> dict  # 11 dimensions
    def extract_harmonics(self, audio_path) -> Tuple[f0, harmonics]
    def measure_phi_spacing(self, harmonics) -> float
    def measure_speed(self) -> float
    def measure_timbre(self) -> float
    def measure_breath(self) -> float
    def emotion_range(self) -> float
    def measure_clarity(self) -> float
    def pause_analysis(self) -> float
    def phi_alignment(self) -> float
    def naturalness(self) -> float  # MOS estimate
```

### 8.2 HarmonicVoiceTrainer
```python
class HarmonicVoiceTrainer:
    def train(self, dataset) -> None
    def synthesize(self, spectral_message, voice_profile='default') -> np.ndarray
    def apply_voice_profile(self, voice_params, profile) -> dict
    # Utilise vocodeur HiFi-GAN φ-spaced en interne
```

### 8.3 SpectralVoicePipeline (intégration avec tts_server.py existant)
```python
class SpectralVoicePipeline:
    """
    Interface : tts_server.synthesize(spectral_message=msg, voice="default")
    Remplace l'interface actuelle : tts_server.synthesize(text="...", voice="default")
    """
    def __init__(self, trainer: HarmonicVoiceTrainer)
    def synthesize(self, spectral_message, voice_profile='default') -> bytes  # WAV
```

---

## 9. Synergie avec le Projet Existant

- **`tts_server.py`** — à étendre avec l'interface `synthesize(spectral_message=msg)`
- **`engine/signatures_11d.py`** — fournit les signatures 11D des SpectralMessages
- **`engine/harmonic_resonator.py`** — produit les SpectralMessages (Couche 0)
- **`engine/recursive_learner.py`** — peut optimiser les paramètres vocaux par résonance

---

## 10. Prochaines Actions Immédiates

1. **Télécharger les corpus** (Common Voice, LibriTTS, VCTK, TED-LIUM)
2. **Implémenter `VoiceSignatureExtractor`** avec Parselmouth
3. **Extraire et sauvegarder** les signatures 11D des 6 profils de référence
4. **Fine-tuner HiFi-GAN** sur le corpus (ou utiliser un modèle pré-entraîné)
5. **Intégrer** la sortie audio dans `tts_server.py`
6. **Évaluer** avec MOS (> 4.0 cible)

---

*Résumé pour continuité — Analyse Prospective Physique Harmonique — 26 Juin 2026*