# 📸 DATASETS D'IMAGES PHOTORÉALISTES — GRATUITS & OPEN SOURCE
## Pour l'entraînement holographique one-pass
### Alain Kotto — 27 Mai 2026

---

## 🌍 Sources gratuites et légales d'images photoréalistes

### Datasets majeurs (1M+ images)

| Dataset | Volume | Description | Licence | Lien |
|---------|:------:|-------------|---------|------|
| **LAION-5B** | 5.85 milliards | Images + légendes (paires texte-image) | CC-BY 4.0 | https://laion.ai |
| **LAION-Aesthetics** | 600M | Sous-ensemble filtré par qualité esthétique | CC-BY 4.0 | https://laion.ai |
| **LAION-High-Resolution** | 170M | Images ≥ 1024px | CC-BY 4.0 | https://laion.ai |
| **COCO** | 330K | Objets du quotidien, scènes complexes | CC-BY 4.0 | https://cocodataset.org |
| **OpenImages V7** | 9M | Google — multi-labels, boîtes | CC-BY 4.0 | https://storage.googleapis.com/openimages |
| **Conceptual Captions** | 3.3M | Google — paires image-description | Custom | https://ai.google.com/research/ConceptualCaptions |
| **YFCC100M** | 100M | Flickr — géolocalisées, métadonnées riches | CC | https://multimediacommons.wordpress.com |

### Portraits & Visages

| Dataset | Volume | Description | Licence |
|---------|:------:|-------------|---------|
| **FFHQ** (NVIDIA) | 70 000 | Visages 1024×1024, diversité ethnique/âge | CC BY-NC-SA 4.0 |
| **CelebA** | 200 000 | Célébrités avec attributs (lunettes, sourire...) | Non-commercial |
| **Faces-HQ** (Flickr-Faces-HQ) | 70 000 | Haute qualité 1024² | CC BY-NC 4.0 |

### Paysages & Architecture

| Dataset | Volume | Description | Licence |
|---------|:------:|-------------|---------|
| **Places365** | 1.8M | Scènes : 365 catégories (plages, forêts, villes...) | CC-BY |
| **LSUN** | 10M | Scènes : chambres, églises, tours... | MIT |
| **SUN Database** | 130K | Scènes avec annotations riches | MIT |
| **MIT Places** | 2.4M | Scènes en contexte | MIT |

### Nature & Animaux

| Dataset | Volume | Description | Licence |
|---------|:------:|-------------|---------|
| **iNaturalist** | 2.7M | Faune et flore — 5000+ espèces | CC |
| **CUB-200** | 12K | Oiseaux — 200 espèces | MIT |
| **Stanford Dogs** | 20K | 120 races de chiens | MIT |
| **Oxford Pets** | 7.3K | 37 races chiens/chats | CC |

### Art & Design

| Dataset | Volume | Description | Licence |
|---------|:------:|-------------|---------|
| **WikiArt** | 80K | Œuvres d'art classées par artiste/style | Public domain |
| **Met Open Access** | 400K | Musée Met — art mondial | CC0 |
| **Rijksmuseum** | 600K | Musée d'Amsterdam — haute résolution | Public domain |
| **Google Arts & Culture** | API | Milliers d'œuvres | Variable |
| **Behance/Adobe Stock** (gratuit) | 100K+ | Design contemporain | Gratuit via API |

### Textures & Matériaux

| Dataset | Volume | Description | Licence |
|---------|:------:|-------------|---------|
| **Describable Textures (DTD)** | 5.6K | 47 catégories de textures | CC |
| **Texture Library** | 1K+ | Textures PBR, normals, roughness | Gratuit |
| **Poliigon Free** | 300+ | Textures photoréalistes HD | Gratuit |

### Téléchargement rapide (subsets prêts à l'emploi)

```bash
# LAION-Aesthetics (subset 100K images) — filtrage par score > 6.5
wget https://huggingface.co/datasets/laion/laion-aesthetics-6.5/resolve/main/urls.txt
head -n 100000 urls.txt | xargs -P 8 -I {} wget -q {} -P images/

# COCO 2017 (train + val) — 123K images annotées
wget http://images.cocodataset.org/zips/train2017.zip
wget http://images.cocodataset.org/zips/val2017.zip

# Places365 (standard) — 1.8M images
wget http://data.csail.mit.edu/places/places365/places365standard_easyformat.tar

# FFHQ (70K visages) — via NVIDIA
wget https://github.com/NVlabs/ffhq-dataset/releases/download/v1.0/ffhq-dataset-v1.0.zip

# WikiArt
git clone https://github.com/cs-chan/ArtGAN.git
cd ArtGAN/WikiArt\ Dataset/
```

---

## 🎯 Priorité d'ingestion pour entraînement rapide

```
Priorité 1 (J+1, ~12h CPU) :
  ✅ LAION-Aesthetics 100K (qualité filtrée)
  ✅ FFHQ 70K (visages)
  ✅ Places365 100K subset (scènes)

Priorité 2 (J+2, ~12h CPU) :
  ✅ COCO 123K (objets quotidiens)
  ✅ WikiArt 80K (styles artistiques)
  ✅ Textures DTD 5.6K (matériaux)

Priorité 3 (J+3, ~10h CPU) :
  ✅ iNaturalist 100K subset (nature)
  ✅ LSUN 100K subset (intérieurs)

TOTAL : ~34h CPU, 0€, ~650K images → Hologramme 32 Ko
Qualité photoréaliste pour la génération par résonance.
```

---

## 🔄 Pipeline complet

```
1. TÉLÉCHARGER les datasets (wget/curl)
2. PRÉTRAITER : resize 128×128, conversion niveaux de gris
3. INGÉRER one-pass : FFT 2D → fréquences dominantes → onde → hologramme
4. TESTER : prompt texte → résonance → IFFT → image générée
5. UPSCALER : image 128×128 → HCV upscale → 4K photoréaliste
```

---

## 📦 Commande d'ingestion avec ces datasets

```bash
# Télécharger et ingérer automatiquement
python ka_studio_ingest.py --images --dir ./datasets/ffhq/
python ka_studio_ingest.py --images --dir ./datasets/coco/
python ka_studio_ingest.py --images --dir ./datasets/places365/

# Ou tout en une fois avec images synthétiques + réelles
python ka_studio_ingest.py --all --n 5000
```

---

*Document établi le 27 mai 2026 — Alain Kotto*