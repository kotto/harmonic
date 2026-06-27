#!/usr/bin/env python3
"""
Script de test final pour valider la correction des URLs dynamiques
"""

import requests
import json
import os
import tempfile
import logging
import webbrowser
import time

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_server_port():
    """Trouve le port du serveur HCS V2 en cours d'exécution"""
    for port in range(8008, 8100):
        try:
            response = requests.get(f"http://localhost:{port}/api/v2/health", timeout=2)
            if response.status_code == 200:
                logger.info(f"Serveur trouvé sur le port {port}")
                return port
        except requests.exceptions.ConnectionError:
            continue
    return None

def test_frontend_backend_compatibility():
    """Test la compatibilité frontend/backend avec URLs dynamiques"""
    server_port = find_server_port()
    
    if not server_port:
        logger.error("❌ Serveur HCS V2 non trouvé")
        return False
    
    API_BASE_URL = f"http://localhost:{server_port}"
    
    logger.info("🧪 Test de compatibilité Frontend/Backend")
    logger.info(f"   Port détecté: {server_port}")
    logger.info(f"   API Base: {API_BASE_URL}")
    
    # 1. Tester l'endpoint de santé
    try:
        response = requests.get(f"{API_BASE_URL}/api/v2/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Endpoint santé fonctionnel")
        else:
            logger.error(f"❌ Endpoint santé erreur: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Erreur endpoint santé: {e}")
        return False
    
    # 2. Créer une image de test simple
    from PIL import Image
    import numpy as np
    
    # Créer une image simple
    width, height = 200, 200
    image = Image.new('RGB', (width, height), color='red')
    
    # Sauvegarder temporairement
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        image.save(f.name, 'PNG')
        test_image_path = f.name
    
    try:
        # 3. Compresser l'image
        with open(test_image_path, 'rb') as f:
            files = {'file': ('test_image.png', f, 'image/png')}
            
            logger.info("📤 Test compression image...")
            response = requests.post(f"{API_BASE_URL}/api/v2/compress/image", files=files, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"❌ Erreur compression: {response.status_code}")
            return False
        
        result = response.json()
        result_id = result['result_id']
        logger.info(f"✅ Image compressée - ID: {result_id}")
        
        # 4. Tester les URLs générées
        decompress_url = result.get('decompress_url', '')
        download_url = result.get('download_url', '')
        
        logger.info(f"   Decompress URL: {decompress_url}")
        logger.info(f"   Download URL: {download_url}")
        
        # 5. Tester l'URL de décompression
        full_decompress_url = f"{API_BASE_URL}{decompress_url}"
        try:
            decompress_response = requests.get(full_decompress_url, timeout=10)
            if decompress_response.status_code == 200:
                logger.info("✅ URL décompression fonctionnelle")
                
                # Vérifier le content-type
                content_type = decompress_response.headers.get('content-type', '')
                logger.info(f"   Content-Type: {content_type}")
                
                # Sauvegarder pour test
                with open(f"test_decompressed_{result_id}.png", 'wb') as f:
                    f.write(decompress_response.content)
                logger.info(f"   Fichier sauvegardé: test_decompressed_{result_id}.png")
                
            else:
                logger.error(f"❌ URL décompression erreur: {decompress_response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur test décompression: {e}")
            return False
        
        # 6. Tester l'URL de téléchargement
        full_download_url = f"{API_BASE_URL}{download_url}"
        try:
            download_response = requests.get(full_download_url, timeout=10)
            if download_response.status_code == 200:
                logger.info("✅ URL téléchargement fonctionnelle")
                
                # Sauvegarder pour test
                with open(f"test_compressed_{result_id}.webp", 'wb') as f:
                    f.write(download_response.content)
                logger.info(f"   Fichier sauvegardé: test_compressed_{result_id}.webp")
                
            else:
                logger.error(f"❌ URL téléchargement erreur: {download_response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur test téléchargement: {e}")
            return False
        
        # 7. Créer une page de test HTML
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test URLs Dynamiques HCS V2</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .test-section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
        .url {{ background: #f5f5f5; padding: 10px; margin: 5px 0; font-family: monospace; }}
        .success {{ color: green; }}
        .error {{ color: red; }}
        img, video {{ max-width: 300px; margin: 10px 0; }}
    </style>
</head>
<body>
    <h1>🧪 Test URLs Dynamiques HCS V2</h1>
    
    <div class="test-section">
        <h2>📊 Configuration</h2>
        <p><strong>Port serveur:</strong> {server_port}</p>
        <p><strong>API Base:</strong> {API_BASE_URL}</p>
        <p><strong>Result ID:</strong> {result_id}</p>
    </div>
    
    <div class="test-section">
        <h2>🔗 URLs Générées</h2>
        <p><strong>Décompression:</strong></p>
        <div class="url">{full_decompress_url}</div>
        
        <p><strong>Téléchargement:</strong></p>
        <div class="url">{full_download_url}</div>
    </div>
    
    <div class="test-section">
        <h2>🖼️ Test Décompression</h2>
        <p>Test via balise img:</p>
        <img src="{full_decompress_url}" alt="Image décompressée" onerror="this.style.border='2px solid red'" onload="this.style.border='2px solid green'">
        
        <p>Test via JavaScript:</p>
        <button onclick="testDecompression()">Tester décompression JS</button>
        <div id="js-result"></div>
    </div>
    
    <div class="test-section">
        <h2>📥 Test Téléchargement</h2>
        <a href="{full_download_url}" download="test_compressed.webp">Télécharger fichier compressé</a>
    </div>
    
    <script>
        async function testDecompression() {{
            const resultDiv = document.getElementById('js-result');
            resultDiv.innerHTML = 'Test en cours...';
            
            try {{
                const response = await fetch('{full_decompress_url}');
                if (response.ok) {{
                    const blob = await response.blob();
                    const url = URL.createObjectURL(blob);
                    
                    const img = document.createElement('img');
                    img.src = url;
                    img.onload = () => {{
                        resultDiv.innerHTML = '<span class="success">✅ Succès JavaScript!</span>';
                    }};
                    img.onerror = () => {{
                        resultDiv.innerHTML = '<span class="error">❌ Erreur JavaScript!</span>';
                    }};
                    resultDiv.appendChild(img);
                }} else {{
                    resultDiv.innerHTML = '<span class="error">❌ Erreur fetch!</span>';
                }}
            }} catch (error) {{
                resultDiv.innerHTML = '<span class="error">❌ Exception: ' + error.message + '</span>';
            }}
        }}
        
        // Log automatique
        console.log('API Base:', '{API_BASE_URL}');
        console.log('Decompress URL:', '{full_decompress_url}');
        console.log('Download URL:', '{full_download_url}');
    </script>
</body>
</html>
        """
        
        html_path = f"test_urls_{result_id}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"🌐 Page HTML créée: {html_path}")
        
        # Ouvrir la page HTML
        file_url = f"file://{os.path.abspath(html_path)}"
        logger.info(f"🌐 Ouverture: {file_url}")
        webbrowser.open(file_url)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test: {e}")
        return False
    finally:
        if os.path.exists(test_image_path):
            os.unlink(test_image_path)

if __name__ == "__main__":
    print("🧪 Test de compatibilité Frontend/Backend HCS V2")
    print("=" * 60)
    
    success = test_frontend_backend_compatibility()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Test de compatibilité réussi!")
        print("📁 Fichiers créés:")
        print("   - Image décompressée: test_decompressed_*.png")
        print("   - Fichier compressé: test_compressed_*.webp")
        print("   - Page test HTML: test_urls_*.html")
        print("\n🌐 La page HTML s'ouvrira automatiquement")
        print("   Vérifiez que les images s'affichent correctement")
    else:
        print("❌ Le test de compatibilité a échoué")
        print("Vérifiez les logs pour plus de détails")
