#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUIDE COMPLET - Ajustement des Parametres de Compression
Tous les niveaux de reglage disponibles
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("GUIDE AJUSTEMENT PARAMETRES - Compression HCS")
print("=" * 80)
print()

# ============================================================================
# NIVEAU 1 : AJUSTEMENT SIMPLE (Presets Predefinis)
# ============================================================================
print("NIVEAU 1 : AJUSTEMENT SIMPLE - Presets Predefinis")
print("-" * 80)
print("""
Fichier: pro_compression_strategy.py

4 presets disponibles avec caracteristiques differentes:

1. ProQualityPreset.MASTER
   - K-Factor: 0.008 (tres conservateur)
   - WebP Quality: 92 (tres haute)
   - Ratio: 50-100:1
   - Usage: Cinema, etalonnage, VFX

2. ProQualityPreset.BROADCAST  [RECOMMANDE]
   - K-Factor: 0.012 (conservateur)
   - WebP Quality: 88 (haute)
   - Ratio: 100-200:1
   - Usage: TV, streaming premium

3. ProQualityPreset.STREAMING_PRO
   - K-Factor: 0.015 (modere)
   - WebP Quality: 85 (bonne)
   - Ratio: 200-400:1
   - Usage: Streaming web 4K

4. ProQualityPreset.ARCHIVE
   - K-Factor: 0.010 (conservateur)
   - WebP Quality: 95 (maximale)
   - Ratio: 30-80:1
   - Usage: Conservation patrimoniale

UTILISATION:
    from pro_compression_strategy import (
        ProVideoCompressionStrategy, 
        ProQualityPreset
    )
    
    # Choisir le preset adapte
    strategy = ProVideoCompressionStrategy(ProQualityPreset.BROADCAST)
    result = strategy.compress_video_pro('video.mp4')
""")

# ============================================================================
# NIVEAU 2 : AJUSTEMENT PAR PARAMETRE INDIVIDUEL
# ============================================================================
print()
print("NIVEAU 2 : AJUSTEMENT PAR PARAMETRE INDIVIDUEL")
print("-" * 80)
print("""
Vous pouvez modifier chaque parametre independamment dans le fichier
pro_compression_strategy.py :

class ProCompressionConfig:
    name: str                    # Nom de votre preset
    k_factor: float             # 0.005 a 0.020 (plus petit = meilleure qualite)
    webp_quality: int           # 75 a 98 (plus grand = meilleure qualite)
    temporal_coherence_weight: float  # 0.0 a 1.0 (plus grand = plus fluide)
    min_quality_threshold: float      # 0.80 a 0.98 (seuil qualite minimum)
    target_psnr: float          # 35 a 50 dB (qualite technique)
    target_ssim: float          # 0.90 a 0.99 (perception humaine)
    max_compression_ratio: float      # 50 a 500 (ratio maximum acceptable)

EXEMPLE - Preset personnalise:
    ProCompressionConfig(
        name="Mon Preset Perso",
        k_factor=0.014,          # Plus de compression que BROADCAST
        webp_quality=86,         # Qualite legerement reduite
        temporal_coherence_weight=0.82,  # Plus de fluidite
        min_quality_threshold=0.86,      # Seuil personnalise
        target_psnr=41.0,
        target_ssim=0.95,
        max_compression_ratio=300.0,
        description="Mon preset optimise pour mon usage"
    )
""")

# ============================================================================
# NIVEAU 3 : AJUSTEMENT EN TEMPS REEL (Optimisation Adatative)
# ============================================================================
print()
print("NIVEAU 3 : AJUSTEMENT EN TEMPS REEL - Optimisation Adaptative")
print("-" * 80)
print("""
La strategie PRO ajuste AUTOMATIQUEMENT les parametres si la qualite
n'est pas suffisante :

Fonction: find_optimal_parameters()

Processus:
1. Teste differentes combinaisons de parametres
2. Evalue la qualite obtenue
3. Si qualite < seuil_min:
   - Diminue K-Factor (meilleure qualite)
   - Augmente WebP Quality (meilleure qualite)
   - Re-teste jusqu'a atteindre le seuil

Vous pouvez controler ce comportement:

# DANS pro_compression_strategy.py

# Ajuster la plage de recherche K-Factor
optimizer.k_factor_range = (0.005, 0.015)  # Min, Max

# Ajuster la plage WebP
optimizer.webp_quality_range = (80, 95)    # Min, Max

# Modifier les poids d'optimisation
optimizer.weights = {
    'temporal_coherence': 0.35,   # Priorite fluidite
    'spatial_quality': 0.45,      # Priorite nettete
    'compression_ratio': 0.10,    # Priorite faible compression
    'processing_time': 0.10       # Priorite faible temps
}

# Nombre d'iterations (plus = meilleure optimisation mais plus lent)
max_iterations=20   # 10=rapide, 20=standard, 30=precis
""")

# ============================================================================
# NIVEAU 4 : AJUSTEMENT FRAME PAR FRAME (Compression Manuelle)
# ============================================================================
print()
print("NIVEAU 4 : AJUSTEMENT FRAME PAR FRAME - Compression Manuelle")
print("-" * 80)
print("""
Pour un controle total, vous pouvez compresser chaque frame avec des
parametres differents :

EXEMPLE COMPLET:
""")

code_exemple = '''
from core.hybrid_compressor import HybridCompressor
import cv2
import numpy as np

# Configuration manuelle complete
compressor = HybridCompressor(
    k_factor=0.012,          # Votre valeur K
    webp_quality=88          # Votre qualite WebP
)

# Ouvrir video
video = cv2.VideoCapture('input.mp4')
fps = video.get(cv2.CAP_PROP_FPS)
width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Parametres de sortie
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('output.mp4', fourcc, fps, (width, height))

frame_num = 0
while True:
    ret, frame = video.read()
    if not ret:
        break
    
    # AJUSTEMENT PAR FRAME POSSIBLE ICI
    # Exemple: adapter selon le contenu de la frame
    
    # Detecter si scene d'action (mouvement rapide)
    if frame_num > 0:
        movement = detect_movement(previous_frame, frame)
        if movement > 0.5:  # Beaucoup de mouvement
            # Augmenter qualite pour eviter artefacts
            compressor.k_factor = 0.010
            compressor.webp_quality = 90
        else:  # Scene statique
            # Compression plus agressive
            compressor.k_factor = 0.014
            compressor.webp_quality = 86
    
    # Compression
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_normalized = frame_rgb.astype(np.float32) / 255.0
    
    compressed_data, metadata = compressor.compress_image(frame_normalized)
    
    print(f"Frame {frame_num}: Ratio={metadata[\'hybrid_ratio\']:.1f}:1, "
          f"K={compressor.k_factor}, WebP={compressor.webp_quality}")
    
    frame_num += 1
    previous_frame = frame.copy()

video.release()
out.release()
'''

print(code_exemple)

# ============================================================================
# NIVEAU 5 : AJUSTEMENT PAR TYPE DE CONTENU
# ============================================================================
print()
print("NIVEAU 5 : AJUSTEMENT PAR TYPE DE CONTENU")
print("-" * 80)
print("""
Selon le type de contenu video, differents reglages optimaux:

1. CONTENU STATIQUE (Interview, documentaire):
   k_factor: 0.015      # Bonne compression acceptable
   webp_quality: 85     # Qualite standard suffisante
   temporal_weight: 0.70
   → Ratio: 200-300:1

2. CONTENU DYNAMIQUE (Sport, action):
   k_factor: 0.010      # Qualite prioritaire
   webp_quality: 90     # Haute qualite pour mouvement
   temporal_weight: 0.85  # FLUIDITE MAXIMALE
   → Ratio: 80-150:1

3. CONTENU GRAIN (Film argentique, texture):
   k_factor: 0.008      # Conservation texture
   webp_quality: 92     # Haute fidelite
   temporal_weight: 0.80
   → Ratio: 60-100:1

4. ANIMATION / GRAPHISME:
   k_factor: 0.018      # Compression aggressive (contenu simple)
   webp_quality: 88     # Bonne qualite
   temporal_weight: 0.75
   → Ratio: 300-500:1

5. VFX / COMPOSITING:
   k_factor: 0.008      # Qualite maximale
   webp_quality: 95     # Preservation details
   temporal_weight: 0.90  # Coherence parfaite
   → Ratio: 50-80:1
""")

# ============================================================================
# NIVEAU 6 : AJUSTEMENT API SERVEUR
# ============================================================================
print()
print("NIVEAU 6 : AJUSTEMENT VIA API SERVEUR")
print("-" * 80)
print("""
Dans HCS Studio Integrated, vous pouvez ajouter des parametres a l'API:

@app.post("/api/v3/compress/video/custom")
async def compress_video_custom(
    file: UploadFile = File(...),
    k_factor: float = Form(0.012),           # PARAMETRE AJUSTABLE
    webp_quality: int = Form(88),            # PARAMETRE AJUSTABLE
    quality_priority: str = Form("balanced") # balanced/quality/size
):
    \"\"\"Compression avec parametres personnalises\"\"\"
    
    # Ajuster selon priorite
    if quality_priority == "quality":
        k_factor = max(0.005, k_factor * 0.8)
        webp_quality = min(98, webp_quality + 5)
    elif quality_priority == "size":
        k_factor = min(0.020, k_factor * 1.3)
        webp_quality = max(75, webp_quality - 5)
    
    compressor = HybridCompressor(
        k_factor=k_factor,
        webp_quality=webp_quality
    )
    
    # ... traitement ...
    
    return {
        "k_factor_used": k_factor,
        "webp_quality_used": webp_quality,
        "compression_ratio": ratio,
        "quality_score": quality
    }

APPEL API:
    curl -X POST http://localhost:8013/api/v3/compress/video/custom \\
        -F "file=@video.mp4" \\
        -F "k_factor=0.010" \\
        -F "webp_quality=90" \\
        -F "quality_priority=quality"
""")

# ============================================================================
# TABLEAU RECAPITULATIF
# ============================================================================
print()
print("=" * 80)
print("TABLEAU RECAPITULATIF DES AJUSTEMENTS POSSIBLES")
print("=" * 80)
print()

ajustements = [
    ("Niveau", "Methode", "Complexite", "Controle", "Usage"),
    ("-" * 15, "-" * 25, "-" * 12, "-" * 12, "-" * 20),
    ("1", "Preset choix", "Tres simple", "Faible", "Rapide"),
    ("2", "Config perso", "Simple", "Moyen", "Standard"),
    ("3", "Optim auto", "Automatique", "Adaptatif", "Intelligent"),
    ("4", "Frame/frame", "Avance", "Total", "Expert"),
    ("5", "Type contenu", "Contextuel", "Intelligent", "Specialise"),
    ("6", "API params", "Interface", "Flexibile", "Integration"),
]

for row in ajustements:
    print(f"{row[0]:<15} {row[1]:<25} {row[2]:<12} {row[3]:<12} {row[4]:<20}")

print()
print("=" * 80)
print("RECOMMANDATION")
print("=" * 80)
print("""
Pour commencer simplement:
1. Utilisez les PRESETS (Niveau 1)
2. Si besoin plus precis, modifiez la CONFIG (Niveau 2)
3. Laissez l'OPTIMISATION ADAPTATIVE ajuster automatiquement (Niveau 3)

Pour besoins avances:
4. Controle frame par frame pour scenes specifiques (Niveau 4)
5. Adaptez selon le TYPE DE CONTENU (Niveau 5)
6. Integrez via API pour applications externes (Niveau 6)
""")

print()
print("=" * 80)
print("EXEMPLE PRATIQUE - Ajustement Progressif")
print("=" * 80)
print("""
# ETAPE 1: Tester avec preset standard
strategy = ProVideoCompressionStrategy(ProQualityPreset.BROADCAST)
result = strategy.compress_video_pro('video.mp4')
# Resultat: Ratio=180:1, Qualite=0.87

# ETAPE 2: Qualite insuffisante (0.87 < 0.90 souhaite)
# → Modifier le preset dans pro_compression_strategy.py:

ProCompressionConfig(
    name="Mon Broadcast+",
    k_factor=0.010,          # Diminuer (etait 0.012)
    webp_quality=90,         # Augmenter (etait 88)
    min_quality_threshold=0.90,  # Augmenter seuil
    # ... autres params
)

# ETAPE 3: Re-tester
strategy = ProVideoCompressionStrategy(ProQualityPreset.BROADCAST)
result = strategy.compress_video_pro('video.mp4')
# Resultat: Ratio=150:1, Qualite=0.91  [OK!]

# ETAPE 4: Si encore insuffisant → Passer a MASTER
strategy = ProVideoCompressionStrategy(ProQualityPreset.MASTER)
# Resultat: Ratio=80:1, Qualite=0.95  [EXCELLENT!]
""")

print()
print("=" * 80)
print("FIN DU GUIDE")
print("=" * 80)
