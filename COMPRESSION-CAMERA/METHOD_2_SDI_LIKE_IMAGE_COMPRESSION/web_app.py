#!/usr/bin/env python3
"""
APPLICATION WEB SDI-LIKE IMAGE COMPRESSION
Interface web pour tester la compression d'images SDI-like
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import os
import json
import time
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
import base64
import io
from PIL import Image
import numpy as np
import cv2

from sdi_like_image_compression import SDILikeImageCompressor
from photorealistic_test import PhotorealisticImageGenerator
from decompression_utils import SDIImageDecompressor
from sdi_pure_image_compression import SDIPureImageCompressor
from sdi_pure_image_decompressor import SDIPureImageDecompressor

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'E:/COMPRESSION_UPLOADS'
app.config['OUTPUT_FOLDER'] = 'E:/COMPRESSION_OUTPUTS'
app.config['STATIC_FOLDER'] = 'static'

# Création des dossiers nécessaires
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
os.makedirs(app.config['STATIC_FOLDER'], exist_ok=True)

# Variables globales pour les résultats
compression_results = {}
test_sessions = {}

@app.route('/')
def index():
    """Page principale"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    """Upload d'une image"""
    if 'image' not in request.files:
        return jsonify({'error': 'Aucune image fournie'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400
    
    # Vérification de l'extension
    allowed_extensions = {'png', 'jpg', 'jpeg', 'bmp', 'tiff'}
    if not (file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        return jsonify({'error': 'Format de fichier non supporté'}), 400
    
    # Sauvegarde du fichier
    filename = secure_filename(file.filename)
    timestamp = str(int(time.time()))
    unique_filename = f"{timestamp}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(filepath)
    
    # Analyse de l'image
    try:
        image = Image.open(filepath)
        width, height = image.size
        file_size = os.path.getsize(filepath)
        
        # Conversion en base64 pour affichage
        with open(filepath, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        return jsonify({
            'success': True,
            'filename': unique_filename,
            'original_filename': filename,
            'width': width,
            'height': height,
            'file_size': file_size,
            'file_size_mb': round(file_size / (1024 * 1024), 2),
            'image_data': image_data
        })
    
    except Exception as e:
        return jsonify({'error': f'Erreur de traitement: {str(e)}'}), 500

@app.route('/compress', methods=['POST'])
def compress_image():
    """Compression d'une image"""
    # Nettoyage des fichiers anciens pour libérer de l'espace
    try:
        import glob
        old_files = glob.glob(os.path.join(app.config['OUTPUT_FOLDER'], '*.sdi-img'))
        for old_file in old_files[:-5]:  # Garder seulement les 5 derniers fichiers
            try:
                os.remove(old_file)
            except:
                pass
    except:
        pass
    
    data = request.get_json()
    
    if not data or 'filename' not in data or 'quality' not in data:
        return jsonify({'error': 'Paramètres manquants'}), 400
    
    filename = data['filename']
    quality = data['quality']
    
    if quality not in ['lossless', 'high', 'medium', 'low']:
        return jsonify({'error': 'Qualité non valide'}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'Fichier non trouvé'}), 404
    
    try:
        # Compression avec l'algorithme SDI-PURE
        start_time = time.time()
        compressor = SDIPureImageCompressor()
        
        # Génération du nom de fichier de sortie
        output_filename = f"compressed_{filename.rsplit('.', 1)[0]}.sdi-img"
        output_filepath = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        # Compression
        metrics = compressor.save_compressed_image(filepath, output_filepath)
        compression_time = time.time() - start_time
        
        # Lecture des résultats
        compressed_size = os.path.getsize(output_filepath)
        
        # Conversion du fichier compressé en base64 pour téléchargement
        with open(output_filepath, 'rb') as f:
            compressed_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Stockage des résultats
        session_id = str(uuid.uuid4())
        compression_results[session_id] = {
            'original_filename': filename,
            'compressed_filename': output_filename,
            'metrics': metrics,
            'compression_time': compression_time,
            'compressed_data': compressed_data
        }
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'metrics': metrics,
            'compression_time': compression_time,
            'compressed_size': compressed_size,
            'compressed_size_mb': round(compressed_size / (1024 * 1024), 2),
            'compression_ratio': metrics.get('compression_ratio', 0),
            'space_saving': metrics.get('space_saving', 0),
            'download_url': f'/download/{session_id}'
        })
        
    except Exception as e:
        return jsonify({'error': f'Erreur de compression: {str(e)}'}), 500

@app.route('/download/<session_id>')
def download_compressed(session_id):
    """Téléchargement du fichier compressé"""
    if session_id not in compression_results:
        return jsonify({'error': 'Session non trouvée'}), 404
    
    result = compression_results[session_id]
    output_filepath = os.path.join(app.config['OUTPUT_FOLDER'], result['compressed_filename'])
    
    if not os.path.exists(output_filepath):
        return jsonify({'error': 'Fichier compressé non trouvé'}), 404
    
    return send_file(output_filepath, 
                   as_attachment=True, 
                   download_name=result['compressed_filename'],
                   mimetype='application/octet-stream')

@app.route('/generate_test_images')
def generate_test_images():
    """Génération d'images de test photoréalistes"""
    try:
        generator = PhotorealisticImageGenerator()
        
        # Génération des images
        images = {
            'landscape_natural': generator.create_natural_landscape(),
            'portrait_photo': generator.create_portrait_photo(),
            'architecture_photo': generator.create_architecture_photo(),
            'macro_photography': generator.create_macro_photography(),
            'night_scene': generator.create_night_scene()
        }
        
        test_images = []
        
        for name, image_array in images.items():
            # Conversion numpy array vers PIL Image
            image = Image.fromarray(image_array)
            
            # Sauvegarde temporaire
            temp_filename = f"test_{name}.png"
            temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
            image.save(temp_filepath)
            
            # Conversion en base64
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            test_images.append({
                'name': name,
                'filename': temp_filename,
                'width': image.width,
                'height': image.height,
                'file_size': os.path.getsize(temp_filepath),
                'image_data': image_data
            })
        
        return jsonify({
            'success': True,
            'images': test_images
        })
        
    except Exception as e:
        return jsonify({'error': f'Erreur de génération: {str(e)}'}), 500

@app.route('/batch_test', methods=['POST'])
def batch_test():
    """Test batch sur plusieurs images"""
    data = request.get_json()
    
    if not data or 'images' not in data or 'quality' not in data:
        return jsonify({'error': 'Paramètres manquants'}), 400
    
    images = data['images']
    quality = data['quality']
    
    if quality not in ['lossless', 'high', 'medium', 'low']:
        return jsonify({'error': 'Qualité non valide'}), 400
    
    try:
        results = []
        total_start_time = time.time()
        
        for image_info in images:
            filename = image_info['filename']
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            if not os.path.exists(filepath):
                results.append({
                    'filename': filename,
                    'error': 'Fichier non trouvé'
                })
                continue
            
            try:
                # Compression
                compressor = SDILikeImageCompressor(quality)
                output_filename = f"batch_{quality}_{filename.rsplit('.', 1)[0]}.sdi-img"
                output_filepath = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
                
                metrics = compressor.save_compressed_image(filepath, output_filepath)
                
                results.append({
                    'filename': filename,
                    'success': True,
                    'metrics': metrics,
                    'compression_ratio': metrics.get('compression_ratio', 0),
                    'space_saving': metrics.get('space_saving', 0)
                })
                
            except Exception as e:
                results.append({
                    'filename': filename,
                    'error': str(e)
                })
        
        total_time = time.time() - total_start_time
        
        # Calcul des statistiques globales
        successful_results = [r for r in results if r.get('success')]
        
        if successful_results:
            total_original = sum(r['metrics']['original_size'] for r in successful_results)
            total_compressed = sum(r['metrics']['compressed_size'] for r in successful_results)
            avg_ratio = total_original / max(1, total_compressed)
            avg_saving = (total_original - total_compressed) / total_original * 100
        else:
            avg_ratio = 0
            avg_saving = 0
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total_images': len(images),
                'successful': len(successful_results),
                'failed': len(images) - len(successful_results),
                'total_time': total_time,
                'average_ratio': avg_ratio,
                'average_saving': avg_saving
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Erreur de test batch: {str(e)}'}), 500

@app.route('/compare_results')
def compare_results():
    """Comparaison des résultats de compression"""
    try:
        # Lecture des métriques existantes
        metrics_files = {
            'photorealistic': 'photorealistic_metrics_lossless.json',
            'synthetic': 'sdi_image_metrics_lossless.json'
        }
        
        comparison_data = {}
        
        for category, filename in metrics_files.items():
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    data = json.load(f)
                    comparison_data[category] = data.get('summary', {})
        
        return jsonify({
            'success': True,
            'comparison': comparison_data
        })
        
    except Exception as e:
        return jsonify({'error': f'Erreur de comparaison: {str(e)}'}), 500

@app.route('/decompress/<session_id>')
def decompress_image(session_id):
    """Décompression et visualisation d'une image compressée"""
    if session_id not in compression_results:
        return jsonify({'error': 'Session non trouvée'}), 404
    
    result = compression_results[session_id]
    output_filepath = os.path.join(app.config['OUTPUT_FOLDER'], result['compressed_filename'])
    
    if not os.path.exists(output_filepath):
        return jsonify({'error': 'Fichier compressé non trouvé'}), 404
    
    try:
        decompressor = SDIPureImageDecompressor()
        decompressed_data = decompressor.decompress_sdi_img(output_filepath)
        
        if not decompressed_data['success']:
            return jsonify({'error': f'Erreur de décompression: {decompressed_data["error"]}'}), 500
        
        # Conversion de l'image en base64 pour affichage
        image_base64 = decompressor.get_image_base64(decompressed_data['reconstructed_image'])
        
        return jsonify({
            'success': True,
            'image_data': image_base64,
            'width': decompressed_data['width'],
            'height': decompressed_data['height'],
            'bit_depth': decompressed_data['bit_depth'],
            'file_size': decompressed_data['file_size']
        })
        
    except Exception as e:
        return jsonify({'error': f'Erreur de traitement: {str(e)}'}), 500

@app.route('/file_info/<session_id>')
def get_file_info(session_id):
    """Informations détaillées sur le fichier compressé"""
    if session_id not in compression_results:
        return jsonify({'error': 'Session non trouvée'}), 404
    
    result = compression_results[session_id]
    output_filepath = os.path.join(app.config['OUTPUT_FOLDER'], result['compressed_filename'])
    
    if not os.path.exists(output_filepath):
        return jsonify({'error': 'Fichier compressé non trouvé'}), 404
    
    try:
        decompressor = SDIImageDecompressor()
        file_info = decompressor.get_file_info(output_filepath)
        
        if not file_info['success']:
            return jsonify({'error': file_info['error']}), 500
        
        # Ajout des métriques de compression
        file_info.update({
            'compression_metrics': result['metrics'],
            'compression_time': result['compression_time'],
            'original_filename': result['original_filename']
        })
        
        return jsonify({
            'success': True,
            'file_info': file_info
        })
        
    except Exception as e:
        return jsonify({'error': f'Erreur de lecture: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """Vérification de santé de l'application"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'features': [
            'upload_images',
            'compress_images',
            'generate_test_images',
            'batch_test',
            'compare_results',
            'decompress_images',
            'file_info'
        ]
    })

if __name__ == '__main__':
    # Démarrage de l'application
    print("Démarrage de l'application web SDI-Like Image Compression...")
    print("Accédez à http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
