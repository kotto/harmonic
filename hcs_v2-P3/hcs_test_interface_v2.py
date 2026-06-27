#!/usr/bin/env python3
"""
HCS TEST INTERFACE V2 - Version simplifiée et robuste
"""

from flask import Flask, render_template_string, request, jsonify
import os
import sys
import io
import base64
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>HCS Test Interface V2</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a2e; color: white; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #FFD700; text-align: center; }
        .upload-zone { border: 3px dashed #FFD700; padding: 40px; text-align: center; cursor: pointer; margin: 20px 0; }
        .upload-zone:hover { background: rgba(255,215,0,0.1); }
        .presets { display: flex; gap: 10px; margin: 20px 0; flex-wrap: wrap; }
        .preset { background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; cursor: pointer; flex: 1; min-width: 150px; }
        .preset.selected { border: 2px solid #FFD700; background: rgba(255,215,0,0.2); }
        button { background: #FFD700; color: black; border: none; padding: 15px 40px; font-size: 16px; border-radius: 30px; cursor: pointer; display: block; margin: 20px auto; }
        button:disabled { opacity: 0.5; }
        .results { display: none; margin-top: 20px; }
        .results.show { display: block; }
        .metrics { display: flex; gap: 20px; justify-content: center; margin: 20px 0; }
        .metric { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; text-align: center; min-width: 100px; }
        .metric-value { font-size: 24px; font-weight: bold; color: #FFD700; }
        .previews { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-top: 20px; }
        .preview-box { background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px; text-align: center; }
        .preview-box img { max-width: 100%; max-height: 250px; border-radius: 5px; }
        .status { text-align: center; padding: 15px; border-radius: 10px; margin: 20px 0; }
        .status.success { background: rgba(0,255,0,0.2); color: #4ade80; }
        .status.error { background: rgba(255,0,0,0.2); color: #f87171; }
    </style>
</head>
<body>
    <div class="container">
        <h1>HCS Test Interface V2</h1>
        
        <div class="upload-zone" onclick="document.getElementById('file').click()">
            <h2>📁 Cliquez pour sélectionner une image</h2>
            <p>JPG, PNG, WebP acceptés</p>
        </div>
        <input type="file" id="file" accept="image/*" style="display:none">
        
        <div class="presets">
            <div class="preset selected" data-preset="broadcast" onclick="selectPreset(this)">
                <strong>📺 BROADCAST</strong><br>
                Ratio: 100-200:1
            </div>
            <div class="preset" data-preset="master" onclick="selectPreset(this)">
                <strong>🎬 MASTER</strong><br>
                Ratio: 50-100:1
            </div>
            <div class="preset" data-preset="streaming" onclick="selectPreset(this)">
                <strong>📱 STREAMING</strong><br>
                Ratio: 200-400:1
            </div>
            <div class="preset" data-preset="archive" onclick="selectPreset(this)">
                <strong>🏛️ ARCHIVE</strong><br>
                Ratio: 30-80:1
            </div>
        </div>
        
        <button id="btn" onclick="compress()" disabled>🚀 Compresser</button>
        
        <div id="status"></div>
        
        <div class="results" id="results">
            <div class="metrics">
                <div class="metric"><div class="metric-value" id="ratio">-</div><div>Ratio</div></div>
                <div class="metric"><div class="metric-value" id="quality">-</div><div>Qualité</div></div>
                <div class="metric"><div class="metric-value" id="saved">-</div><div>% Économie</div></div>
                <div class="metric"><div class="metric-value" id="time">-</div><div>Temps (s)</div></div>
            </div>
            
            <div class="previews">
                <div class="preview-box">
                    <h4>Original</h4>
                    <div id="preview-original"></div>
                </div>
                <div class="preview-box">
                    <h4>Compressé (WebP)</h4>
                    <div id="preview-compressed"></div>
                </div>
                <div class="preview-box">
                    <h4>Décompressé + Upscale 1.5x</h4>
                    <div id="preview-decompressed"></div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let selectedFile = null;
        let preset = 'broadcast';
        
        document.getElementById('file').addEventListener('change', (e) => {
            selectedFile = e.target.files[0];
            if (selectedFile) {
                document.getElementById('btn').disabled = false;
                // Preview original
                const reader = new FileReader();
                reader.onload = (e) => {
                    document.getElementById('preview-original').innerHTML = `<img src="${e.target.result}">`;
                };
                reader.readAsDataURL(selectedFile);
            }
        });
        
        function selectPreset(el) {
            document.querySelectorAll('.preset').forEach(p => p.classList.remove('selected'));
            el.classList.add('selected');
            preset = el.dataset.preset;
        }
        
        async function compress() {
            if (!selectedFile) return;
            
            const btn = document.getElementById('btn');
            const status = document.getElementById('status');
            const results = document.getElementById('results');
            
            btn.disabled = true;
            status.className = '';
            status.textContent = 'Compression en cours...';
            results.classList.remove('show');
            
            const formData = new FormData();
            formData.append('file', selectedFile);
            formData.append('preset', preset);
            
            try {
                const response = await fetch('/compress', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('ratio').textContent = data.ratio + ':1';
                    document.getElementById('quality').textContent = data.quality;
                    document.getElementById('saved').textContent = data.saved + '%';
                    document.getElementById('time').textContent = data.time;
                    
                    if (data.compressed_preview) {
                        document.getElementById('preview-compressed').innerHTML = 
                            `<img src="${data.compressed_preview}">`;
                    }
                    if (data.decompressed_preview) {
                        document.getElementById('preview-decompressed').innerHTML = 
                            `<img src="${data.decompressed_preview}">`;
                    }
                    
                    status.className = 'status success';
                    status.textContent = '✅ Compression réussie !';
                    results.classList.add('show');
                } else {
                    throw new Error(data.error);
                }
            } catch (err) {
                status.className = 'status error';
                status.textContent = '❌ Erreur: ' + err.message;
            }
            
            btn.disabled = false;
        }
    </script>
</body>
</html>
'''

def compress_image(file_path, preset):
    """Compression avec vraie chaîne HCS"""
    from core.hybrid_compressor import HybridCompressor
    from PIL import Image
    import numpy as np
    import time
    
    # Config presets
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
    
    # Étape 1: Compression
    start = time.time()
    compressor = HybridCompressor(k_factor=config['k'], webp_quality=config['webp'])
    compressed_data, metadata = compressor.compress_image(img_array)
    
    # Étape 2: Décompression (charger WebP)
    img_webp = Image.open(io.BytesIO(compressed_data))
    
    # Étape 3: Upscale 1.5x avec Lanczos
    w, h = img_webp.size
    new_size = (int(w * 1.5), int(h * 1.5))
    upscaled = img_webp.resize(new_size, Image.LANCZOS)
    
    elapsed = time.time() - start
    
    # Convertir en base64
    # Compressed (WebP)
    compressed_b64 = base64.b64encode(compressed_data).decode('utf-8')
    compressed_preview = f'data:image/webp;base64,{compressed_b64}'
    
    # Decompressed (PNG)
    buffer = io.BytesIO()
    upscaled.save(buffer, format='PNG')
    decompressed_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    decompressed_preview = f'data:image/png;base64,{decompressed_b64}'
    
    return {
        'success': True,
        'ratio': round(metadata['hybrid_ratio'], 1),
        'quality': round(metadata.get('quality_score', 0.9), 2),
        'saved': round(metadata['space_saved_percent'], 1),
        'time': round(elapsed, 2),
        'compressed_preview': compressed_preview,
        'decompressed_preview': decompressed_preview
    }

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/compress', methods=['POST'])
def compress():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Pas de fichier'})
    
    file = request.files['file']
    preset = request.form.get('preset', 'broadcast')
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Fichier vide'})
    
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, file.filename)
    file.save(file_path)
    
    try:
        result = compress_image(file_path, preset)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        os.rmdir(temp_dir)

if __name__ == '__main__':
    print("=" * 60)
    print("HCS TEST INTERFACE V2")
    print("=" * 60)
    print("URL: http://localhost:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False)
