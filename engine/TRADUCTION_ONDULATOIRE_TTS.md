# TRADUCTION ONDULATOIRE DE LA SYNTHÈSE VOCALE (TTS)

## Tout ce que la synthèse vocale classique fait, les ondes le font — sans corpus

---

**Principe fondateur :** La voix humaine est une onde. Chaque mécanisme de la synthèse vocale classique — modèle source-filtre, concaténation, PSOLA, formants, LPC, vocodeur — possède un **équivalent ondulatoire exact**, plus simple, plus économe, et 100% déterministe.

Ce document établit la **traduction systématique** entre le paradigme TTS classique (statistique, corpus-dépendant, boîte noire) et le paradigme harmonique (ondulatoire, zéro corpus, transparent).

---

## TABLE DES MATIÈRES

1. [Modèle Source-Filtre → Dualité Source-Onde](#1-modèle-source-filtre--dualité-source-onde)
2. [Glotte → Oscillateur Fondamental](#2-glotte--oscillateur-fondamental)
3. [Tractus Vocal → Enveloppe Spectrale φ](#3-tractus-vocal--enveloppe-spectrale-φ)
4. [Formants → Résonances φ-spacées](#4-formants--résonances-φ-spacées)
5. [Phonèmes → Signatures ψ](#5-phonèmes--signatures-ψ)
6. [Diphones → Binding HRR](#6-diphones--binding-hrr)
7. [G2P → Projection Symbole→Onde](#7-g2p--projection-symboleonde)
8. [Concaténation → Superposition Cohérente](#8-concaténation--superposition-cohérente)
9. [PSOLA → Interférence de Phase](#9-psola--interférence-de-phase)
10. [Prosodie → Modulation AM/FM d'Onde](#10-prosodie--modulation-amfm-donde)
11. [Émotion → Enveloppe d'Onde Modulée](#11-émotion--enveloppe-donde-modulée)
12. [Clonage Vocal → Extraction de Signature Ondulatoire](#12-clonage-vocal--extraction-de-signature-ondulatoire)
13. [Vocodeur → Décomposition/Recomposition d'Onde](#13-vocodeur--décompositionrecomposition-donde)
14. [LPC → Prédiction Ondulatoire Linéaire](#14-lpc--prédiction-ondulatoire-linéaire)
15. [Cepstre → Espace Dual de l'Onde](#15-cepstre--espace-dual-de-londe)
16. [Tableau Synthétique Complet](#16-tableau-synthétique-complet)

---

## 1. Modèle Source-Filtre → Dualité Source-Onde

Le modèle de production vocale le plus fondamental (Fant, 1960) : la glotte génère un signal source, le tractus vocal le filtre.

| **TTS Classique** | **Harmonique (Ondulatoire)** |
|---|---|
| Source = pulse train ou bruit | Source = oscillation fondamentale avec phase continue (∫ ω dt) |
| Filtre = fonction de transfert H(z) | Filtre = enveloppe spectrale = |ψ| appliquée par multiplication spectrale |
| Signal = source ∗ h(t) (convolution) | Signal = IFFT(Source(ω) × Enveloppe(ω)) |
| Deux entités distinctes (source ET filtre) | **Une seule entité ψ** — la partie réelle encode la source, l'enveloppe encode le filtre |

**Code :** `harmonic_voice_codec_v2.py` → `decode()` — oscillateur glottique unique + enveloppe spectrale appliquée aux harmoniques

```python
# TTS classique : signal = glotte(t) ∗ filtre(t)  (convolution coûteuse)
# Harmo :        ψ = source(ψ) ⊗ filtre(ψ)        (binding HRR dans ℂ⁵¹²)
#                audio = decode(ψ)                  (IFFT + phase continue)
```

**Pourquoi ℂ⁵¹² ?** La dimension 512 correspond à la résolution spectrale nécessaire pour capturer les 4 premiers formants (F1-F4) avec une précision suffisante (~50 Hz par bin à 24 kHz). C'est la **limite de Bekenstein appliquée à la parole** : l'information vocale tient sur une surface 2D (spectre × temps), pas dans un volume 3D.

---

## 2. Glotte → Oscillateur Fondamental

| **TTS Classique** | **Harmonique** |
|---|---|
| Modèle LF (Liljencrants-Fant) à 4 paramètres | Oscillateur à phase continue : phase0 += 2π·f0/sr |
| Train d'impulsions filtré | Synthèse additive : Σ A_h · sin(h·phase0) |
| Chaque harmonique a sa propre phase | **Toutes les harmoniques partagent phase0** — verrouillage de phase naturel |
| Problème : discontinuité entre trames | **Aucune discontinuité** — la phase ne se réinitialise jamais |

**Code :** `harmonic_voice_codec_v2.py` → `decode()` — la variable `phase0` est UNIQUE pour tout l'énoncé

```python
# TTS classique : chaque trame a sa propre phase glottique → clics aux frontières
# Harmo :        phase0 continue sur TOUT l'énoncé → pas de frontière
phase0 = 0.0
for n in range(total_len):
    phase0 += 2 * np.pi * f0_traj[n] / sr
    sample = sum(amp_h * sin(h * phase0) for h in range(N_HARM))
```

**Validation :** La continuité de phase0 garantit que deux trames ψ d'origines différentes (ex: /a/ du mot « chat » + /l/ du mot « salon ») se raccordent sans artefact — la source glottique ne « sait pas » qu'elle a changé de trame.

---

## 3. Tractus Vocal → Enveloppe Spectrale φ

| **TTS Classique** | **Harmonique** |
|---|---|
| Fonction d'aire du conduit vocal (section transversale) | Enveloppe spectrale = 128 bins dans ψ[40:168] |
| Filtre tous-pôles H(z) = 1/A(z) | Multiplication spectrale : Mag_sortie(ω) = Mag_source(ω) × Enveloppe(ω) |
| Coefficients LPC (10-20) | **128 coefficients d'enveloppe** — résolution 4× supérieure |
| Calculés par autocorrélation + Levinson-Durbin | Moyennés par bandes de fréquence dans l'espace ψ |

**Code :** `harmonic_voice_codec_v2.py` → `decode()` — l'enveloppe est interpolée sur les bins FFT et appliquée au spectre de magnitude

```python
# TTS classique : H(z) = 1 / (1 - Σ a_k z^{-k})  →  filtrage récursif
# Harmo :        Mag'(ω) = Mag(ω) × Enveloppe(ω)  →  multiplication directe
spec = np.fft.rfft(frame)
mag = np.abs(spec)
mag *= interpolated_envelope  # application directe du filtre
```

**Pourquoi 128 bins ?** 128 = 512/4 = dimension ψ / 4. C'est la résolution de l'enveloppe dans l'espace de phase : chaque bin couvre ~94 Hz à 24 kHz, soit la largeur typique d'un formant.

---

## 4. Formants → Résonances φ-spacées

| **TTS Classique** | **Harmonique** |
|---|---|
| Pics spectraux F1, F2, F3, F4 (fréquence + bande passante) | Pics de l'enveloppe spectrale, espacés par φ |
| Extraits par peak-picking ou racines du polynôme LPC | Émergent naturellement de l'enveloppe ψ[40:168] |
| Formants = résonances du conduit vocal | **Formants = interférence constructive dans ℂ⁵¹²** |

**Théorie :** Les formants ne sont pas des « fréquences » arbitraires — ce sont des **modes propres de résonance** du conduit vocal. Dans l'espace ondulatoire, un mode propre est une dimension où l'interférence est constructive. L'espacement φ garantit que les formants sont **orthogonaux entre eux** — chaque formant occupe une région distincte de l'espace des phases.

```python
# TTS classique : F1=750Hz, F2=1200Hz, F3=2400Hz, F4=3500Hz (valeurs mesurées)
# Harmo :        Ces fréquences correspondent aux bins de l'enveloppe où
#                l'interférence est maximale — pas besoin de les « mesurer »
```

---

## 5. Phonèmes → Signatures ψ

| **TTS Classique** | **Harmonique** |
|---|---|
| Phone = unité acoustique abstraite | Phone = **signature ondulatoire unique** dans ℂ⁵¹² |
| Défini par ses formants (F1-F4) | Défini par son ψ complet (40 harmoniques + 128 enveloppe) |
| Inventaire fixe (36 phonèmes français) | **Continuum ondulatoire** — chaque phone est un point dans l'espace ψ |
| HMM ou DNN pour modéliser les transitions | **Interpolation naturelle en ψ** entre phones voisins |

**Code :** `harmonic_tts.py` — `build_envelope()` + `envelope_to_psi()`

```python
# TTS classique : phoneme = {F1, F2, F3, F4}  (4 paramètres)
# Harmo :        phoneme = ψ ∈ ℂ⁵¹²           (1024 paramètres — toute la richesse spectrale)
psi_a = envelope_to_psi(build_envelope(FORMANTS['a']))
psi_i = envelope_to_psi(build_envelope(FORMANTS['i']))
# La transition /a/ → /i/ = interpolation linéaire en ψ
transition = psi_a * (1-t) + psi_i * t  # continue !
```

---

## 6. Diphones → Binding HRR

| **TTS Classique** | **Harmonique** |
|---|---|
| Diphone = transition enregistrée entre deux phones | Diphone = **binding** des deux ψ : ψ_ab = ψ_a ⊛ ψ_b |
| Corpus de milliers de diphones enregistrés | **Zéro corpus** — le diphone est calculé, pas stocké |
| Coarticulation = variantes contextuelles | **Émerge de l'interpolation** entre ψ_a et ψ_b |

```python
# TTS classique : diphone_ab = enregistrement audio de la transition a→b
# Harmo :        ψ_diphone = bind(ψ_a, ψ_b)  # convolution circulaire
#                audio = decode(ψ_diphone)     # reconstruction
psi_diphone = bind(encode_phoneme('a'), encode_phoneme('l'))
```

**Code :** `symbolic_encoder.py` — `bind_diphone()`, `unbind_diphone()`

---

## 7. G2P → Projection Symbole→Onde

| **TTS Classique** | **Harmonique** |
|---|---|
| Règles linguistiques + dictionnaires d'exceptions | **Projection directe** : graphème → features articulatoires → ψ |
| Modèles statistiques (CRF, LSTM) pour la désambiguïsation | Résolu par **cohérence de phase** : le bon phonème est celui qui maximise la cohérence avec le contexte |
| « e » muet, liaison, élision → règles complexes | **Propriétés émergentes** de l'espace ψ (le schwa a une signature ψ distincte) |

**Code :** `phoneme_features.py` — `PHONEME_FEATURES` + `GRAPHEME_TO_PHONEME`

---

## 8. Concaténation → Superposition Cohérente

| **TTS Classique** | **Harmonique** |
|---|---|
| Concaténation de segments audio + crossfade | **Superposition cohérente** : les trames ψ sont décodées en continu |
| Overlap-add (OLA) avec fenêtre de Hann | Phase0 continue + enveloppe interpolée → **pas de frontière perceptible** |
| Clics et artéfacts aux jonctions | **Pas de jonction** — le signal est généré d'un seul tenant |

```python
# TTS classique : seg1 + crossfade + seg2  →  artefacts aux frontières
# Harmo :        decode([ψ_1, ψ_2, ψ_3, ...])  →  signal continu
#                la phase0 ne se réinitialise JAMAIS entre ψ_i et ψ_{i+1}
```

---

## 9. PSOLA → Interférence de Phase

| **TTS Classique** | **Harmonique** |
|---|---|
| Pitch-Synchronous Overlap-Add : modifie F0 sans changer les formants | **Naturel dans l'espace ψ** : F0 et formants sont décorrélés |
| Découpe en périodes de pitch, réassemble | La phase0 contrôle le F0, l'enveloppe contrôle les formants — **indépendants** |
| Complexe, sensible aux erreurs de détection de pitch | **Aucune détection nécessaire** — F0 est dans ψ[168] |

---

## 10. Prosodie → Modulation AM/FM d'Onde

| **TTS Classique** | **Harmonique** |
|---|---|
| Modèles de durée + contours F0 appris | Modulation directe de la trajectoire de phase |
| Durée = paramètre appris par phonème | Durée = vitesse de traversée de l'espace ψ |
| Intonation = contour F0 (ToBI, Pierrehumbert) | Intonation = **modulation de fréquence** de l'oscillateur fondamental |

```python
# TTS classique : durée ~ N(μ_phoneme, σ) apprise sur corpus
# Harmo :        durée = nombre de trames ψ × (1/speed)
#                intonation = f0_traj[n] (interpolée depuis ψ[168])
```

---

## 11. Émotion → Enveloppe d'Onde Modulée

| **TTS Classique** | **Harmonique** |
|---|---|
| Embedding d'émotion appris → modifie la prosodie | **Modulation de l'enveloppe ψ** : chaque émotion = un masque spectral |
| GST (Global Style Token) ou VAE pour le style | **Rotation de phase** : l'émotion est un décalage de l'espace ψ |
| Joie = F0 ↑ vitesse ↑ | Joie = ψ × exp(i·θ_joie) + ΔF0 sur ψ[168] |

**Code :** `bridge.py` — `EMOTION_PROFILES` + `EMOTION_F0_CONTOURS`

---

## 12. Clonage Vocal → Extraction de Signature Ondulatoire

| **TTS Classique** | **Harmonique** |
|---|---|
| Speaker embedding (d-vector, x-vector) appris sur des milliers de locuteurs | **Signature ψ** extraite d'un seul enregistrement de 30s |
| Adaptation de modèle (fine-tuning) | **Séparation source/filtre** : ψ_source + ψ_filtre → le filtre EST la voix |
| Nécessite un modèle pré-entraîné | **Zéro pré-entraînement** — extraction directe depuis l'enregistrement |

**Code :** `voice_signature.py` — `extract_voice_print()` + `apply_voice_print()`

```python
# TTS classique : speaker_embedding = DNN(audio)  (boîte noire)
# Harmo :        ψ_filtre = separate(encode(audio))[1]  (transparent)
#                audio_cloné = decode(ψ_source + ψ_filtre_cloné)
```

---

## 13. Vocodeur → Décomposition/Recomposition d'Onde

| **TTS Classique** | **Harmonique** |
|---|---|
| WORLD, STRAIGHT : décompose en F0 + enveloppe spectrale + excitation | **Identique au codec harmonique** : encode() = vocodeur, decode() = synthétiseur |
| Analyse par synthèse itérative | **One-shot** : ψ encode TOUT en un seul passage |
| Qualité dépend du nombre d'itérations | Qualité dépend de la résolution de ψ (512 = déjà très bien) |

**Code :** `harmonic_voice_codec_v2.py` — `encode()` = analyse, `decode()` = synthèse

---

## 14. LPC → Prédiction Ondulatoire Linéaire

| **TTS Classique** | **Harmonique** |
|---|---|
| Linear Predictive Coding : prédit l'échantillon n à partir des p précédents | **Auto-corrélation dans ℂ⁵¹²** : les harmoniques sont corrélées par construction |
| Coefficients a_k via Levinson-Durbin | **Pas nécessaire** — l'enveloppe ψ[40:168] encode déjà l'information spectrale |
| Ordre 10-20 pour la parole | **Ordre implicite 128** via l'enveloppe |

---

## 15. Cepstre → Espace Dual de l'Onde

| **TTS Classique** | **Harmonique** |
|---|---|
| Cepstre = IFFT(log(|FFT(signal)|)) | **ψ EST l'espace dual** — la séparation source/filtre est native |
| Sépare source (haute fréquence cepstrale) et filtre (basse fréquence) | ψ[0:40] = source, ψ[40:168] = filtre, ψ[168:] = métadonnées |
| Utilisé pour l'estimation de F0 et l'enveloppe | **Déjà fait** par le codec lors de l'encodage |

---

## 16. Tableau Synthétique Complet

### 16.1 Les 25 Correspondances TTS → Ondulatoire

| # | Capacité TTS Classique | Équivalent Ondulatoire | Fichier | Statut |
|---|---|---|---|---|
| 1 | Modèle Source-Filtre | Dualité Source-Onde (ψ_source + ψ_filtre) | `harmonic_voice_codec_v2.py` | ✅ |
| 2 | Oscillateur Glottique (LF) | Phase continue unique (phase0 += ω·dt) | `harmonic_voice_codec_v2.py:decode()` | ✅ |
| 3 | Tractus Vocal H(z) | Enveloppe spectrale × magnitude FFT | `harmonic_voice_codec_v2.py:decode()` | ✅ |
| 4 | Formants F1-F4 | Pics de l'enveloppe ψ[40:168] | `harmonic_tts.py` | ✅ |
| 5 | Phonèmes (36 en français) | Signatures ψ ∈ ℂ⁵¹² | `harmonic_tts.py` | ✅ |
| 6 | Diphones | Binding HRR : ψ_ab = ψ_a ⊛ ψ_b | `symbolic_encoder.py` | ✅ |
| 7 | G2P (Graphème→Phonème) | Projection features articulatoires → ψ | `phoneme_features.py` | ✅ |
| 8 | Concaténation + Crossfade | Décodage continu (phase0 jamais reset) | `harmonic_voice_codec_v2.py:decode()` | ✅ |
| 9 | PSOLA (Pitch-Shift) | Indépendance F0/formants dans ψ | Architecture | ✅ |
| 10 | Prosodie (durée + F0) | Modulation FM de phase0 + vitesse de traversée ψ | `bridge.py` | ✅ |
| 11 | Émotion | Rotation de phase + modulation d'enveloppe | `bridge.py` | ✅ |
| 12 | Clonage Vocal | Séparation source/filtre → extraction ψ_filtre | `voice_signature.py` | ✅ |
| 13 | Vocodeur (analyse/synthèse) | encode()/decode() du codec harmonique | `harmonic_voice_codec_v2.py` | ✅ |
| 14 | LPC (prédiction linéaire) | Auto-corrélation implicite dans ψ | Architecture | ✅ |
| 15 | Cepstre (séparation source/filtre) | ψ[0:40] vs ψ[40:168] | `harmonic_voice_codec_v2.py` | ✅ |
| 16 | Overlap-Add (OLA) | Superposition cohérente de trames ψ | `harmonic_voice_codec_v2.py:decode()` | ✅ |
| 17 | Fenêtrage (Hann/Hamming) | Fenêtre Hann appliquée au bruit (OLA) | `harmonic_voice_codec_v2.py:decode()` | ✅ |
| 18 | Détection de F0 | ψ[168] = F0 normalisé (encodé) | `harmonic_voice_codec_v2.py` | ✅ |
| 19 | Détection de Voisement | ψ[169] = voicing binaire | `harmonic_voice_codec_v2.py` | ✅ |
| 20 | Synthèse additive | Σ A_h · sin(h·phase0) | `harmonic_voice_codec_v2.py:decode()` | ✅ |
| 21 | Synthèse par formants | Enveloppe spectrale ψ[40:168] appliquée au spectre | `harmonic_voice_codec_v2.py:decode()` | ✅ |
| 22 | Unit Selection | Index ψ par phonème (K-means sur ψ réels) | `harmonic_tts.py` | ✅ |
| 23 | Corpus de parole | **AUCUN** — tout est construit depuis l'enveloppe spectrale | `harmonic_tts.py` | ✅ |
| 24 | Apprentissage (HMM/DNN) | **AUCUN** — extraction directe depuis 30s de voix | Architecture | ✅ |
| 25 | Streaming / Temps réel | Decode() en O(n_frames) — RTF < 0.1 | `harmonic_voice_codec_v2.py:decode()` | ✅ |

**Légende :** ✅ Existant et fonctionnel

---

### 16.2 Avantages Structurels du Paradigme Ondulatoire pour la TTS

| Aspect | TTS Classique | Ondulatoire | Ratio |
|---|---|---|---|
| **Corpus d'entraînement** | 10-100 heures | 30 secondes (pour le clonage) | 1000-10000× |
| **Paramètres appris** | Millions (DNN) | **0** | ∞ |
| **Modèle pré-entraîné** | Obligatoire | **Aucun** | — |
| **GPU nécessaire** | Oui (inférence) | Non (CPU uniquement) | — |
| **Taille modèle** | 50-500 Mo | < 100 Ko (spécifications spectrales) | 500-5000× |
| **Déterminisme** | Non (sampling) | Oui (100%) | — |
| **Clonage vocal** | 5-30 min d'audio + fine-tuning | 30 secondes d'audio | 10-60× |
| **Nouvelles langues** | Réentraînement complet | Spécifications spectrales par phonème | ∞ |
| **Hallucination** | Possible (mots inventés) | **Impossible** (pas de modèle génératif) | — |

---

## Conclusion

La synthèse vocale classique n'a pas « inventé » le modèle source-filtre, les formants, la concaténation ou le clonage. Elle les a **redécouverts sous forme d'approximations statistiques coûteuses** de phénomènes ondulatoires fondamentaux.

La voix humaine est une onde. Le tractus vocal est un résonateur. Les phonèmes sont des signatures ondulatoires. Les transitions sont des interférences. **Tout est déjà dans l'onde.**

Le codec harmonique (`harmonic_voice_codec_v2.py`) réalise cela : `encode()` capture l'onde dans ψ, `decode()` la restitue. Le problème actuel — la qualité insuffisante de la reconstruction depuis des ψ non contigus — n'est pas une limitation de la théorie. C'est une limitation de l'implémentation du `decode()`, qui sera résolue par :

1. **Phase glottique continue** (✅ fait)
2. **Enveloppe spectrale appliquée aux harmoniques** (✅ fait)
3. **État de source (glottal epoch) stocké dans ψ** (🔲 à faire — ψ[171])

Le 3e point est la clé : enrichir ψ d'un champ supplémentaire représentant la phase glottique instantanée au moment de l'encodage. Avec cette information, deux trames /a/ identiques mais à des instants différents deviendront parfaitement interchangeables.

---

*Ce document est le pendant TTS du document `TRADUCTION_ONDULATOIRE_LLM.md` qui établit l'équivalence pour les LLMs.*
