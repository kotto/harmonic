#!/usr/bin/env python3
"""
HCS TEST INTERFACE - Interface Web pour tester compression
Serveur Flask simple avec upload et compression
"""

from flask import Flask, render_template_string, request, jsonify, send_file
import os
import sys
import json
import tempfile
from datetime import datetime
import numpy as np
from PIL import Image
import io
import base64

# Ajouter core au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max

# Templates HTML
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HCS Test Interface - Compression Images & Videos</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 2px solid #FFD700;
            margin-bottom: 30px;
        }
        
        h1 {
            font-size: 2.5em;
            background: linear-gradient(90deg, #FFD700, #FFA500);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #888;
            font-size: 1.1em;
        }
        
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            border: 1px solid rgba(255,215,0,0.2);
        }
        
        .card-title {
            font-size: 1.3em;
            color: #FFD700;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .upload-zone {
            border: 3px dashed rgba(255,215,0,0.3);
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .upload-zone:hover {
            border-color: #FFD700;
            background: rgba(255,215,0,0.05);
        }
        
        .upload-zone.dragover {
            border-color: #FFD700;
            background: rgba(255,215,0,0.1);
        }
        
        .upload-icon {
            font-size: 3em;
            margin-bottom: 15px;
        }
        
        input[type="file"] {
            display: none;
        }
        
        .preset-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .preset-card {
            background: rgba(255,255,255,0.05);
            border: 2px solid transparent;
            border-radius: 10px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .preset-card:hover {
            border-color: rgba(255,215,0,0.5);
            transform: translateY(-3px);
        }
        
        .preset-card.selected {
            border-color: #FFD700;
            background: rgba(255,215,0,0.1);
        }
        
        .preset-name {
            font-weight: bold;
            color: #FFD700;
            margin-bottom: 8px;
        }
        
        .preset-desc {
            font-size: 0.9em;
            color: #aaa;
        }
        
        .preset-ratio {
            font-size: 0.85em;
            color: #4ade80;
            margin-top: 8px;
        }
        
        button {
            background: linear-gradient(135deg, #FFD700, #FFA500);
            color: #000;
            border: none;
            padding: 15px 40px;
            font-size: 1.1em;
            font-weight: bold;
            border-radius: 30px;
            cursor: pointer;
            transition: all 0.3s;
            display: block;
            margin: 30px auto;
        }
        
        button:hover {
            transform: scale(1.05);
            box-shadow: 0 10px 30px rgba(255,215,0,0.3);
        }
        
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .results {
            display: none;
        }
        
        .results.show {
            display: block;
        }
        
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .metric-box {
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }
        
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #FFD700;
        }
        
        .metric-label {
            color: #888;
            font-size: 0.9em;
            margin-top: 5px;
        }
        
        .preview-container {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }
        
        .preview-box {
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
        }
        
        .preview-box img {
            max-width: 100%;
            max-height: 300px;
            border-radius: 5px;
        }
        
        .preview-label {
            color: #888;
            margin-bottom: 10px;
            font-size: 0.9em;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            overflow: hidden;
            margin: 20px 0;
            display: none;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #FFD700, #FFA500);
            width: 0%;
            transition: width 0.3s;
        }
        
        .status {
            text-align: center;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            display: none;
        }
        
        .status.success {
            background: rgba(74,222,128,0.2);
            border: 1px solid #4ade80;
            color: #4ade80;
        }
        
        .status.error {
            background: rgba(248,113,113,0.2);
            border: 1px solid #f87171;
            color: #f87171;
        }
        
        .file-info {
            background: rgba(255,215,0,0.1);
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            display: none;
        }
        
        .file-info.show {
            display: block;
        }
        
        @media (max-width: 600px) {
            .preview-container {
                grid-template-columns: 1fr;
            }
            
            .preset-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>HCS Test Interface</h1>
            <p class="subtitle">Testez la compression de vos images et vidéos</p>
        </header>
        
        <!-- Upload Section -->
        <div class="card">
            <div class="card-title">
                <span>📁</span>
                <span>1. Sélectionnez votre fichier</span>
            </div>
            
            <div class="upload-zone" id="uploadZone" onclick="document.getElementById('fileInput').click()">
                <div class="upload-icon">📤</div>
                <p>Cliquez ou glissez-déposez votre fichier ici</p>
                <p style="color: #888; font-size: 0.9em; margin-top: 10px;">
                    Images: JPG, PNG, WebP | Vidéos: MP4, AVI, MOV
                </p>
            </div>
            
            <input type="file" id="fileInput" accept="image/*,video/*">
            
            <div class="file-info" id="fileInfo">
                <strong>Fichier sélectionné:</strong> <span id="fileName"></span><br>
                <span id="fileSize"></span> | <span id="fileType"></span>
            </div>
        </div>
        
        <!-- Preset Selection -->
        <div class="card">
            <div class="card-title">
                <span>⚙️</span>
                <span>2. Choisissez le preset</span>
            </div>
            
            <div class="preset-grid">
                <div class="preset-card selected" data-preset="broadcast" onclick="selectPreset(this)">
                    <div class="preset-name">📺 BROADCAST</div>
                    <div class="preset-desc">Qualité professionnelle TV</div>
                    <div class="preset-ratio">Ratio: 100-200:1</div>
                </div>
                
                <div class="preset-card" data-preset="master" onclick="selectPreset(this)">
                    <div class="preset-name">🎬 MASTER</div>
                    <div class="preset-desc">Qualité cinéma maximale</div>
                    <div class="preset-ratio">Ratio: 50-100:1</div>
                </div>
                
                <div class="preset-card" data-preset="streaming" onclick="selectPreset(this)">
                    <div class="preset-name">📱 STREAMING</div>
                    <div class="preset-desc">Optimisé pour le web</div>
                    <div class="preset-ratio">Ratio: 200-400:1</div>
                </div>
                
                <div class="preset-card" data-preset="archive" onclick="selectPreset(this)">
                    <div class="preset-name">🏛️ ARCHIVE</div>
                    <div class="preset-desc">Conservation patrimoniale</div>
                    <div class="preset-ratio">Ratio: 30-80:1</div>
                </div>
            </div>
        </div>
        
        <!-- Compress Button -->
        <button id="compressBtn" onclick="compressFile()" disabled>
            🚀 Lancer la Compression
        </button>
        
        <!-- Progress -->
        <div class="progress-bar" id="progressBar">
            <div class="progress-fill" id="progressFill"></div>
        </div>
        
        <!-- Status -->
        <div class="status" id="status"></div>
        
        <!-- Results -->
        <div class="results" id="results">
            <div class="card">
                <div class="card-title">
                    <span>📊</span>
                    <span>Résultats de la Compression</span>
                </div>
                
                <div class="metric-grid">
                    <div class="metric-box">
                        <div class="metric-value" id="ratioValue">-</div>
                        <div class="metric-label">Ratio</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-value" id="qualityValue">-</div>
                        <div class="metric-label">Qualité</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-value" id="savedValue">-</div>
                        <div class="metric-label">% Économie</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-value" id="timeValue">-</div>
                        <div class="metric-label">Temps (s)</div>
                    </div>
                </div>
                
                <div class="preview-container" id="previewContainer">
                    <div class="preview-box">
                        <div class="preview-label">Original</div>
                        <div id="originalPreview"></div>
                    </div>
                    <div class="preview-box">
                        <div class="preview-label">Compressé (WebP)</div>
                        <div id="compressedPreview"></div>
                    </div>
                    <div class="preview-box">
                        <div class="preview-label">Décompressé (HCS)</div>
                        <div id="decompressedPreview"></div>
                    </div>
                </div>
                
                <button onclick="downloadResult()" style="margin-top: 20px;">
                    💾 Télécharger le fichier compressé
                </button>
            </div>
        </div>
    </div>
    
    <script>
        let selectedFile = null;
        let selectedPreset = 'broadcast';
        let compressedData = null;
        
        // File Upload
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('fileInput');
        const fileInfo = document.getElementById('fileInfo');
        const compressBtn = document.getElementById('compressBtn');
        
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });
        
        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('dragover');
        });
        
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            handleFile(e.dataTransfer.files[0]);
        });
        
        fileInput.addEventListener('change', (e) => {
            handleFile(e.target.files[0]);
        });
        
        function handleFile(file) {
            if (!file) return;
            
            selectedFile = file;
            
            document.getElementById('fileName').textContent = file.name;
            document.getElementById('fileSize').textContent = formatSize(file.size);
            document.getElementById('fileType').textContent = file.type;
            fileInfo.classList.add('show');
            
            compressBtn.disabled = false;
            
            // Preview for images
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    document.getElementById('originalPreview').innerHTML = 
                        `<img src="${e.target.result}" alt="Original">`;
                };
                reader.readAsDataURL(file);
            }
        }
        
        function formatSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        // Preset Selection
        function selectPreset(element) {
            document.querySelectorAll('.preset-card').forEach(c => c.classList.remove('selected'));
            element.classList.add('selected');
            selectedPreset = element.dataset.preset;
        }
        
        // Compression
        async function compressFile() {
            if (!selectedFile) return;
            
            const progressBar = document.getElementById('progressBar');
            const progressFill = document.getElementById('progressFill');
            const status = document.getElementById('status');
            const results = document.getElementById('results');
            
            progressBar.style.display = 'block';
            status.style.display = 'none';
            results.classList.remove('show');
            compressBtn.disabled = true;
            
            const formData = new FormData();
            formData.append('file', selectedFile);
            formData.append('preset', selectedPreset);
            
            try {
                // Simulation de progression
                let progress = 0;
                const interval = setInterval(() => {
                    progress += 5;
                    progressFill.style.width = progress + '%';
                    if (progress >= 90) clearInterval(interval);
                }, 100);
                
                const response = await fetch('/compress', {
                    method: 'POST',
                    body: formData
                });
                
                clearInterval(interval);
                progressFill.style.width = '100%';
                
                const data = await response.json();
                
                if (data.success) {
                    compressedData = data;
                    
                    document.getElementById('ratioValue').textContent = data.ratio + ':1';
                    document.getElementById('qualityValue').textContent = data.quality;
                    document.getElementById('savedValue').textContent = data.saved + '%';
                    document.getElementById('timeValue').textContent = data.time;
                    
                    if (data.preview) {
                        document.getElementById('compressedPreview').innerHTML = 
                            `<img src="${data.preview}" alt="Compressé">`;
                    }
                    
                    if (data.decompressed_preview) {
                        document.getElementById('decompressedPreview').innerHTML = 
                            `<img src="${data.decompressed_preview}" alt="Décompressé">`;
                    }
                    
                    status.className = 'status success';
                    status.textContent = '✅ Compression réussie !';
                    results.classList.add('show');
                } else {
                    throw new Error(data.error);
                }
            } catch (error) {
                status.className = 'status error';
                status.textContent = '❌ Erreur: ' + error.message;
            }
            
            status.style.display = 'block';
            compressBtn.disabled = false;
            setTimeout(() => {
                progressBar.style.display = 'none';
                progressFill.style.width = '0%';
            }, 500);
        }
        
        function downloadResult() {
            if (!compressedData || !compressedData.download_url) return;
            window.location.href = compressedData.download_url;
        }
    </script>
</body>
</html>
'''


def compress_image_file(file_path, preset='broadcast'):
    """Compresse une image avec le preset choisi"""
    try:
        from core.hybrid_compressor import HybridCompressor
        from PIL import Image
        import numpy as np
        import time
        import io
        
        # Config selon preset
        presets = {
            'master': {'k': 0.008, 'webp': 92},
            'broadcast': {'k': 0.012, 'webp': 88},
            'streaming': {'k': 0.015, 'webp': 85},
            'archive': {'k': 0.010, 'webp': 95}
        }
        
        config = presets.get(preset, presets['broadcast'])
        
        # Charger image
        img = Image.open(file_path)
        img_array = np.array(img).astype(np.float32) / 255.0
        
        # Compresser
        start = time.time()
        compressor = HybridCompressor(k_factor=config['k'], webp_quality=config['webp'])
        compressed_data, metadata = compressor.compress_image(img_array)
        
        # VRAIE CHAINE HCS: Compression → Décompression → Upscale
        elapsed_compress = time.time() - start
        
        # Debug: sauvegarder les données compressées pour vérification
        debug_path = 'debug_compressed.bin'
        with open(debug_path, 'wb') as f:
            f.write(compressed_data)
        
        # Essayer de comprendre le format
        print(f"DEBUG: Type compressed_data: {type(compressed_data)}")
        print(f"DEBUG: Taille compressed_data: {len(compressed_data)} bytes")
        print(f"DEBUG: Premiers bytes: {compressed_data[:20]}")
        
        # Étape 2: Décompression - le HybridCompressor retourne du WebP
        try:
            # Charger directement comme WebP
            img_webp = Image.open(io.BytesIO(compressed_data))
            print(f"DEBUG: Format WebP chargé: {img_webp.size}, mode: {img_webp.mode}")
            
            decompressed_array = np.array(img_webp).astype(np.float32) / 255.0
            print(f"DEBUG: Array shape: {decompressed_array.shape}")
            
            # Étape 3: Upscale avec HarmonicUpscaler
            try:
                from core.harmonic_upscaler import HarmonicUpscalerAPI
                upscaler = HarmonicUpscalerAPI()
                upscaled_array = upscaler.upscale(decompressed_array, scale_factor=1.5)
                print(f"DEBUG: Upscale HCS réussi")
            except Exception as e:
                print(f"DEBUG: Upscale HCS échoué: {e}, fallback Lanczos")
                # Fallback: upscale avec PIL Lanczos
                h, w = decompressed_array.shape[:2]
                new_h, new_w = int(h * 1.5), int(w * 1.5)
                upscaled_img = Image.fromarray((decompressed_array * 255).astype(np.uint8)).resize((new_w, new_h), Image.LANCZOS)
                upscaled_array = np.array(upscaled_img).astype(np.float32) / 255.0
            
            # Convertir en image pour affichage
            final_img = Image.fromarray((upscaled_array * 255).astype(np.uint8))
            buffer = io.BytesIO()
            final_img.save(buffer, format='PNG')
            decompressed_data = buffer.getvalue()
            print(f"DEBUG: Image finale créée: {len(decompressed_data)} bytes")
            
        except Exception as e:
            print(f"DEBUG ERROR: {e}")
            # Si tout échoue, créer une image simple
            fallback_img = Image.new('RGB', (320, 240), color='red')
            buffer = io.BytesIO()
            fallback_img.save(buffer, format='PNG')
            decompressed_data = buffer.getvalue()
        
        elapsed = time.time() - start
        
        return {
            'success': True,
            'ratio': round(metadata['hybrid_ratio'], 1),
            'quality': round(metadata.get('quality_score', 0.9), 2),
            'saved': round(metadata['space_saved_percent'], 1),
            'time': round(elapsed, 2),
            'data': compressed_data,
            'decompressed_data': decompressed_data,
            'metadata': metadata
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


@app.route('/')
def index():
    """Page principale"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/compress', methods=['POST'])
def compress():
    """Endpoint de compression"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Aucun fichier'})
    
    file = request.files['file']
    preset = request.form.get('preset', 'broadcast')
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Fichier vide'})
    
    # Sauvegarder temporairement
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, file.filename)
    file.save(file_path)
    
    try:
        if file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif')):
            result = compress_image_file(file_path, preset)
            
            if result['success']:
                # Créer preview base64 compressé
                preview_b64 = base64.b64encode(result['data']).decode('utf-8')
                result['preview'] = f'data:image/webp;base64,{preview_b64}'
                
                # Créer preview base64 décompressé
                decompressed_b64 = base64.b64encode(result['decompressed_data']).decode('utf-8')
                result['decompressed_preview'] = f'data:image/png;base64,{decompressed_b64}'
                
                result['download_url'] = f'/download/{os.path.basename(file_path)}'
                # Supprimer données binaires avant JSON
                del result['data']
                del result['metadata']
                del result['decompressed_data']
        else:
            result = {'success': False, 'error': 'Type de fichier non supporté pour cette démo'}
        
        return jsonify(result)
        
    finally:
        # Nettoyage
        if os.path.exists(file_path):
            os.remove(file_path)
        os.rmdir(temp_dir)


@app.route('/health')
def health():
    """Health check"""
    try:
        from core.hybrid_compressor import HybridCompressor
        return jsonify({
            'status': 'ok',
            'compressor': 'available',
            'time': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})


if __name__ == '__main__':
    print("=" * 70)
    print("  HCS TEST INTERFACE")
    print("=" * 70)
    print()
    print("Démarrage du serveur web...")
    print()
    print("[WEB] Interface: http://localhost:5000")
    print("[API] Health:    http://localhost:5000/health")
    print()
    print("Ouvrez l'URL dans votre navigateur pour tester la compression!")
    print("Appuyez sur Ctrl+C pour arrêter")
    print("=" * 70)
    print()
    
    app.run(host='0.0.0.0', port=5000, debug=False)
