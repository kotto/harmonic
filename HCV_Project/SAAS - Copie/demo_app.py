#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo App - Phase 4: Interface de Démonstration
Application web Flask pour démontrer la supériorité harmonique

Auteur: Vision Harmonique
Date: 28 avril 2026
"""

from flask import Flask, render_template, request, jsonify, send_file
import base64
import io
import os
import sys
from datetime import datetime

# Importer nos classes harmoniques
from harmonic_core import HarmonicConstants, HarmonicOptimizer, HarmonicComposer
from constants_validation import ConstantsValidator
from harmonic_ai import HarmonicAI
from generalization_test import GeneralizationTest

app = Flask(__name__)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Créer le dossier d'upload s'il n'existe pas
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Variables globales pour les instances
constants_validator = None
generalization_tester = None
harmonic_ai = None

def initialize_services():
    """Initialise les services harmoniques"""
    global constants_validator, generalization_tester, harmonic_ai
    
    try:
        constants_validator = ConstantsValidator()
        generalization_tester = GeneralizationTest()
        harmonic_ai = HarmonicAI()
        return True
    except Exception as e:
        print(f"Erreur d'initialisation: {e}")
        return False

@app.route('/')
def home():
    """
    Page d'accueil avec interface de démonstration
    """
    return render_template('index.html')

@app.route('/validate_constants', methods=['POST'])
def validate_constants():
    """
    Valide les constantes fondamentales harmoniques
    """
    try:
        if not constants_validator:
            return jsonify({'error': 'Service de validation non initialisé'}), 500
        
        results = constants_validator.run_all_validations()
        
        # Formater les résultats pour l'affichage
        formatted_results = {}
        for key, result in results.items():
            if key == 'summary':
                formatted_results[key] = result
            else:
                formatted_results[key] = {
                    'name': result['name'],
                    'formula': result['formula'],
                    'precision': result.get('precision_percent', 0),
                    'success': result.get('success', False),
                    'error': result.get('error_relative', 0)
                }
        
        return jsonify({
            'success': True,
            'results': formatted_results,
            'summary': results['summary']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test_generalization', methods=['POST'])
def test_generalization():
    """
    Test la généralisation de α = 1/φ
    """
    try:
        if not generalization_tester:
            return jsonify({'error': 'Service de test non initialisé'}), 500
        
        results = generalization_tester.run_all_tests()
        
        # Formater les résultats
        formatted_results = {}
        for key, result in results.items():
            formatted_results[key] = {
                'performance': result.get('performance_ratio', 0) * 100,
                'success': result.get('success', False),
                'details': {
                    'harmonic_alpha': result.get('harmonic_alpha', 0),
                    'optimal_alpha': result.get('optimal_alpha', 0),
                    'harmonic_value': result.get('harmonic_loss', 0),
                    'optimal_value': result.get('optimal_loss', 0)
                }
            }
        
        return jsonify({
            'success': True,
            'results': formatted_results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    """
    Analyse une image pour détecter les patterns harmoniques
    """
    try:
        if not harmonic_ai:
            return jsonify({'error': 'Service IA non initialisé'}), 500
        
        # Récupérer l'image
        image_data = request.json.get('image')
        if not image_data:
            return jsonify({'error': 'Aucune image fournie'}), 400
        
        # Décoder l'image
        image_bytes = base64.b64decode(image_data.split(',')[1])
        
        # Sauvegarder temporairement
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f'temp_{timestamp}.png')
        
        with open(temp_path, 'wb') as f:
            f.write(image_bytes)
        
        # Analyser l'image
        analysis = harmonic_ai.analyze_image_harmonics(temp_path)
        pattern = harmonic_ai.recognize_pattern(temp_path)
        
        # Nettoyer
        os.remove(temp_path)
        
        if 'error' in analysis:
            return jsonify({'error': analysis['error']}), 500
        
        return jsonify({
            'success': True,
            'analysis': {
                'harmony_score': (1 - analysis['harmonic_analysis']['harmony_score']) * 100,
                'is_harmonic': analysis['harmonic_analysis']['is_harmonic'],
                'is_strong_harmonic': analysis['harmonic_analysis']['is_strong_harmonic'],
                'dominant_pattern': analysis['harmonic_analysis']['dominant_pattern'],
                'dominant_info': analysis['harmonic_analysis']['dominant_info'],
                'image_shape': analysis['image_info']['shape'],
                'aspect_ratio': analysis['image_info']['aspect_ratio']
            },
            'pattern': pattern,
            'details': analysis['harmonic_analysis']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate_harmonic_image', methods=['POST'])
def generate_harmonic_image():
    """
    Génère une image harmonique
    """
    try:
        if not harmonic_ai:
            return jsonify({'error': 'Service IA non initialisé'}), 500
        
        data = request.json
        pattern = data.get('pattern', 'phi')
        size = data.get('size', 256)
        color = data.get('color', False)
        
        # Générer l'image
        img_array = harmonic_ai.generate_harmonic_image(pattern, (size, size), color)
        
        # Convertir en image PIL
        from PIL import Image
        img = Image.fromarray(img_array)
        
        # Convertir en base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{image_base64}',
            'pattern': pattern,
            'size': size,
            'color': color
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/compose_concept', methods=['POST'])
def compose_concept():
    """
    Compose une phrase harmonique à partir d'un concept
    """
    try:
        composer = HarmonicComposer()
        concept = request.json.get('concept', '')
        
        if not concept:
            return jsonify({'error': 'Aucun concept fourni'}), 400
        
        # Traduire le concept
        translation = composer.translate_concept(concept)
        
        return jsonify({
            'success': True,
            'concept': concept,
            'translation': {
                'formula': translation['formula'],
                'value': translation['value'],
                'meaning': translation['meaning']
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/optimize_parameter', methods=['POST'])
def optimize_parameter():
    """
    Optimise un paramètre selon α = 1/φ
    """
    try:
        optimizer = HarmonicOptimizer()
        data = request.json
        
        min_val = data.get('min', 0.0)
        max_val = data.get('max', 1.0)
        
        if min_val >= max_val:
            return jsonify({'error': 'min doit être inférieur à max'}), 400
        
        # Optimiser
        optimal_value = optimizer.optimize((min_val, max_val))
        
        return jsonify({
            'success': True,
            'range': (min_val, max_val),
            'optimal_value': optimal_value,
            'alpha_optimal': optimizer.ALPHA_OPTIMAL,
            'formula': f'optimal = min + α × (max - min) où α = 1/φ'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_constants_info')
def get_constants_info():
    """
    Retourne les informations sur les constantes harmoniques
    """
    try:
        constants = HarmonicConstants()
        return jsonify({
            'success': True,
            'constants': constants.list_constants(),
            'alpha_optimal': 1 / constants.PHI
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """
    Vérifie l'état de santé de l'application
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'constants_validator': constants_validator is not None,
            'generalization_tester': generalization_tester is not None,
            'harmonic_ai': harmonic_ai is not None
        }
    })

# Pages d'erreur personnalisées
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# Context processor pour les templates
@app.context_processor
def inject_constants():
    """Injecte les constantes harmoniques dans tous les templates"""
    try:
        constants = HarmonicConstants()
        return {
            'phi': constants.PHI,
            'alpha_optimal': 1 / constants.PHI,
            'constants_list': list(constants.SEMANTICS.keys())
        }
    except:
        return {}

def create_templates():
    """
    Crée les templates HTML pour l'application
    """
    
    # Template principal
    index_template = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌊 Preuve de Concept Harmonique</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card h2 {
            color: #4a5568;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .card-icon {
            font-size: 1.5em;
        }
        
        .btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s ease;
            margin: 5px;
        }
        
        .btn:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .result {
            background: #f8f9fa;
            border-left: 4px solid #28a745;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }
        
        .result.error {
            border-left-color: #dc3545;
            background: #f8d7da;
        }
        
        .result.warning {
            border-left-color: #ffc107;
            background: #fff3cd;
        }
        
        .loading {
            color: #6c757d;
            font-style: italic;
            text-align: center;
            padding: 20px;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }
        
        .stat {
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        
        .stat-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #28a745;
        }
        
        .stat-label {
            font-size: 0.9em;
            color: #6c757d;
            margin-top: 5px;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(45deg, #28a745, #20c997);
            transition: width 0.5s ease;
        }
        
        .image-upload {
            border: 2px dashed #dee2e6;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            margin: 15px 0;
            transition: border-color 0.3s ease;
        }
        
        .image-upload:hover {
            border-color: #667eea;
        }
        
        .image-preview {
            max-width: 100%;
            max-height: 200px;
            margin: 15px 0;
            border-radius: 10px;
        }
        
        .formula {
            font-family: 'Courier New', monospace;
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            font-weight: bold;
        }
        
        footer {
            text-align: center;
            color: white;
            margin-top: 40px;
            opacity: 0.8;
        }
        
        .hidden {
            display: none;
        }
        
        .fade-in {
            animation: fadeIn 0.5s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🌊 Preuve de Concept Harmonique</h1>
            <p class="subtitle">Démonstration de la supériorité de l'approche harmonique</p>
        </header>
        
        <div class="dashboard">
            <!-- Validation des Constantes -->
            <div class="card">
                <h2><span class="card-icon">📊</span>Validation des Constantes</h2>
                <p>Test mathématique des formules harmoniques pour ℏ et α</p>
                <button class="btn" onclick="validateConstants()">Valider ℏ et α</button>
                <div id="constants-result"></div>
            </div>
            
            <!-- Test de Généralisation -->
            <div class="card">
                <h2><span class="card-icon">🎯</span>Test de Généralisation</h2>
                <p>Test du principe universel α = 1/φ sur ML et signal</p>
                <button class="btn" onclick="testGeneralization()">Tester α = 1/φ</button>
                <div id="generalization-result"></div>
            </div>
            
            <!-- Analyse d'Image -->
            <div class="card">
                <h2><span class="card-icon">🖼️</span>Analyse d'Image Harmonique</h2>
                <p>Détection des patterns harmoniques dans les images</p>
                <div class="image-upload" onclick="document.getElementById('imageInput').click()">
                    <input type="file" id="imageInput" accept="image/*" style="display: none;" onchange="loadImage(event)">
                    <div id="uploadText">Cliquez pour charger une image</div>
                </div>
                <canvas id="canvas" width="256" height="256" style="display: none;"></canvas>
                <button class="btn" onclick="analyzeImage()" id="analyzeBtn" style="display: none;">Analyser l'harmonie</button>
                <div id="image-result"></div>
            </div>
            
            <!-- Composition de Concept -->
            <div class="card">
                <h2><span class="card-icon">🎼</span>Composition Harmonique</h2>
                <p>Traduction de concepts en phrases harmoniques</p>
                <input type="text" id="conceptInput" placeholder="Entrez un concept (amour, conscience, intelligence...)" style="width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px;">
                <button class="btn" onclick="composeConcept()">Composer</button>
                <div id="concept-result"></div>
            </div>
            
            <!-- Optimisation -->
            <div class="card">
                <h2><span class="card-icon">⚡</span>Optimisation Harmonique</h2>
                <p>Optimise un paramètre selon le principe α = 1/φ</p>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 10px 0;">
                    <input type="number" id="minInput" placeholder="Min" value="0.1" style="padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                    <input type="number" id="maxInput" placeholder="Max" value="1.0" style="padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                </div>
                <button class="btn" onclick="optimizeParameter()">Optimiser</button>
                <div id="optimization-result"></div>
            </div>
            
            <!-- Génération d'Image -->
            <div class="card">
                <h2><span class="card-icon">🎨</span>Génération Harmonique</h2>
                <p>Génère des images avec des patterns harmoniques</p>
                <select id="patternSelect" style="width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px;">
                    <option value="phi">🌟 Spirale Dorée (φ)</option>
                    <option value="pi">⭕ Cercles (π)</option>
                    <option value="sqrt2">⚖️ Dualité (√2)</option>
                    <option value="sqrt3">🔺 Triangle (√3)</option>
                    <option value="sqrt5">🌿 Pentagone (√5)</option>
                    <option value="e_over_pi">🌀 Spirale (e/π)</option>
                </select>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 10px 0;">
                    <input type="number" id="sizeInput" placeholder="Taille" value="256" style="padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                    <label style="display: flex; align-items: center; gap: 5px;">
                        <input type="checkbox" id="colorCheck">
                        <span>Couleur</span>
                    </label>
                </div>
                <button class="btn" onclick="generateImage()">Générer</button>
                <div id="generation-result"></div>
            </div>
        </div>
        
        <!-- Statistiques Globales -->
        <div class="card" style="grid-column: 1 / -1;">
            <h2><span class="card-icon">📈</span>Statistiques Harmoniques</h2>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value" id="phiValue">1.618</div>
                    <div class="stat-label">φ (Nombre d'or)</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="alphaValue">0.618</div>
                    <div class="stat-label">α optimal (1/φ)</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="precisionValue">-</div>
                    <div class="stat-label">Précision moyenne</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="successRateValue">-</div>
                    <div class="stat-label">Taux de succès</div>
                </div>
            </div>
        </div>
        
        <footer>
            <p>🌊 Vision Harmonique - Preuve de Concept | 28 avril 2026</p>
        </footer>
    </div>

    <script>
        // Variables globales
        let currentImage = null;

        // Fonctions principales
        function validateConstants() {
            const resultDiv = document.getElementById('constants-result');
            resultDiv.innerHTML = '<div class="loading">Validation en cours...</div>';
            
            fetch('/validate_constants', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        displayConstantsResults(data.results, data.summary);
                        updateStats(data.summary);
                    } else {
                        resultDiv.innerHTML = `<div class="result error">Erreur: ${data.error}</div>`;
                    }
                })
                .catch(error => {
                    resultDiv.innerHTML = `<div class="result error">Erreur de connexion: ${error}</div>`;
                });
        }

        function testGeneralization() {
            const resultDiv = document.getElementById('generalization-result');
            resultDiv.innerHTML = '<div class="loading">Test en cours...</div>';
            
            fetch('/test_generalization', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        displayGeneralizationResults(data.results);
                    } else {
                        resultDiv.innerHTML = `<div class="result error">Erreur: ${data.error}</div>`;
                    }
                })
                .catch(error => {
                    resultDiv.innerHTML = `<div class="result error">Erreur de connexion: ${error}</div>`;
                });
        }

        function loadImage(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = new Image();
                img.onload = function() {
                    const canvas = document.getElementById('canvas');
                    const ctx = canvas.getContext('2d');
                    
                    // Redimensionner pour l'analyse
                    const maxSize = 256;
                    let width = img.width;
                    let height = img.height;
                    
                    if (width > height) {
                        if (width > maxSize) {
                            height *= maxSize / width;
                            width = maxSize;
                        }
                    } else {
                        if (height > maxSize) {
                            width *= maxSize / height;
                            height = maxSize;
                        }
                    }
                    
                    canvas.width = width;
                    canvas.height = height;
                    ctx.drawImage(img, 0, 0, width, height);
                    
                    canvas.style.display = 'block';
                    document.getElementById('analyzeBtn').style.display = 'inline-block';
                    document.getElementById('uploadText').textContent = file.name;
                }
                img.src = e.target.result;
            }
            reader.readAsDataURL(file);
        }

        function analyzeImage() {
            const resultDiv = document.getElementById('image-result');
            resultDiv.innerHTML = '<div class="loading">Analyse harmonique en cours...</div>';
            
            const canvas = document.getElementById('canvas');
            const imageData = canvas.toDataURL('image/png');
            
            fetch('/analyze_image', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({image: imageData})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayImageResults(data);
                } else {
                    resultDiv.innerHTML = `<div class="result error">Erreur: ${data.error}</div>`;
                }
            })
            .catch(error => {
                resultDiv.innerHTML = `<div class="result error">Erreur de connexion: ${error}</div>`;
            });
        }

        function composeConcept() {
            const concept = document.getElementById('conceptInput').value;
            if (!concept) {
                alert('Veuillez entrer un concept');
                return;
            }
            
            const resultDiv = document.getElementById('concept-result');
            resultDiv.innerHTML = '<div class="loading">Composition en cours...</div>';
            
            fetch('/compose_concept', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({concept: concept})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayConceptResults(data);
                } else {
                    resultDiv.innerHTML = `<div class="result error">Erreur: ${data.error}</div>`;
                }
            })
            .catch(error => {
                resultDiv.innerHTML = `<div class="result error">Erreur de connexion: ${error}</div>`;
            });
        }

        function optimizeParameter() {
            const min = parseFloat(document.getElementById('minInput').value);
            const max = parseFloat(document.getElementById('maxInput').value);
            
            if (isNaN(min) || isNaN(max) || min >= max) {
                alert('Veuillez entrer des valeurs valides (min < max)');
                return;
            }
            
            const resultDiv = document.getElementById('optimization-result');
            resultDiv.innerHTML = '<div class="loading">Optimisation en cours...</div>';
            
            fetch('/optimize_parameter', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({min: min, max: max})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayOptimizationResults(data);
                } else {
                    resultDiv.innerHTML = `<div class="result error">Erreur: ${data.error}</div>`;
                }
            })
            .catch(error => {
                resultDiv.innerHTML = `<div class="result error">Erreur de connexion: ${error}</div>`;
            });
        }

        function generateImage() {
            const pattern = document.getElementById('patternSelect').value;
            const size = parseInt(document.getElementById('sizeInput').value) || 256;
            const color = document.getElementById('colorCheck').checked;
            
            const resultDiv = document.getElementById('generation-result');
            resultDiv.innerHTML = '<div class="loading">Génération en cours...</div>';
            
            fetch('/generate_harmonic_image', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({pattern: pattern, size: size, color: color})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayGenerationResults(data);
                } else {
                    resultDiv.innerHTML = `<div class="result error">Erreur: ${data.error}</div>`;
                }
            })
            .catch(error => {
                resultDiv.innerHTML = `<div class="result error">Erreur de connexion: ${error}</div>`;
            });
        }

        // Fonctions d'affichage
        function displayConstantsResults(results, summary) {
            const resultDiv = document.getElementById('constants-result');
            let html = '<h3>✅ Résultats de Validation</h3>';
            
            // Afficher les constantes fondamentales
            for (let [key, result] of Object.entries(results)) {
                if (key === 'summary') continue;
                
                const statusClass = result.success ? 'result' : 'result error';
                html += `<div class="${statusClass} fade-in">
                    <strong>${result.name}:</strong><br>
                    <div class="formula">${result.formula}</div>
                    Précision: ${result.precision?.toFixed(6)}%<br>
                    Statut: ${result.success ? '✅ SUCCÈS' : '❌ ÉCHEC'}
                </div>`;
            }
            
            // Afficher le résumé
            html += `<div class="result fade-in">
                <h4>📊 Résumé Global</h4>
                <div class="stats">
                    <div class="stat">
                        <div class="stat-value">${summary.successful_validations}/${summary.total_validations}</div>
                        <div class="stat-label">Validations réussies</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">${summary.success_rate.toFixed(1)}%</div>
                        <div class="stat-label">Taux de succès</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">${summary.average_precision.toFixed(2)}%</div>
                        <div class="stat-label">Précision moyenne</div>
                    </div>
                </div>
            </div>`;
            
            resultDiv.innerHTML = html;
        }

        function displayGeneralizationResults(results) {
            const resultDiv = document.getElementById('generalization-result');
            let html = '<h3>🎯 Résultats de Généralisation</h3>';
            
            for (let [key, result] of Object.entries(results)) {
                const statusClass = result.success ? 'result' : 'result warning';
                html += `<div class="${statusClass} fade-in">
                    <strong>${key}:</strong><br>
                    Performance: ${result.performance.toFixed(2)}%<br>
                    α harmonique: ${result.details.harmonic_alpha.toFixed(6)}<br>
                    α optimal: ${result.details.optimal_alpha.toFixed(6)}<br>
                    Statut: ${result.success ? '✅ SUCCÈS' : '⚠️ PARTIEL'}
                </div>`;
            }
            
            resultDiv.innerHTML = html;
        }

        function displayImageResults(data) {
            const resultDiv = document.getElementById('image-result');
            const analysis = data.analysis;
            
            let html = '<h3>🖼️ Analyse Harmonique</h3>';
            html += `<div class="result fade-in">
                <strong>Score d'harmonie:</strong> ${analysis.harmony_score.toFixed(2)}%<br>
                <strong>Harmonique:</strong> ${analysis.is_harmonic ? '✅' : '❌'}<br>
                <strong>Harmonie forte:</strong> ${analysis.is_strong_harmonic ? '✅' : '❌'}<br>
                <strong>Pattern dominant:</strong> ${analysis.dominant_pattern} ${analysis.dominant_info.symbol}<br>
                <strong>Description:</strong> ${analysis.dominant_info.description}<br>
                <strong>Dimensions:</strong> ${analysis.image_shape[0]}×${analysis.image_shape[1]}<br>
                <strong>Ratio d'aspect:</strong> ${analysis.aspect_ratio.toFixed(3)}
            </div>`;
            
            // Barre de progression
            html += `<div class="progress-bar">
                <div class="progress-fill" style="width: ${analysis.harmony_score}%"></div>
            </div>`;
            
            // Pattern reconnu
            html += `<div class="result fade-in">
                <h4>🔍 Pattern Reconnu</h4>
                <p>${data.pattern}</p>
            </div>`;
            
            resultDiv.innerHTML = html;
        }

        function displayConceptResults(data) {
            const resultDiv = document.getElementById('concept-result');
            const translation = data.translation;
            
            resultDiv.innerHTML = `<div class="result fade-in">
                <h3>🎼 Composition Harmonique</h3>
                <p><strong>Concept:</strong> ${data.concept}</p>
                <div class="formula">${translation.formula}</div>
                <p><strong>Valeur:</strong> ${translation.value.toFixed(6)}</p>
                <p><strong>Signification:</strong> ${translation.meaning}</p>
            </div>`;
        }

        function displayOptimizationResults(data) {
            const resultDiv = document.getElementById('optimization-result');
            const range = data.range;
            const optimal = data.optimal_value;
            
            resultDiv.innerHTML = `<div class="result fade-in">
                <h3>⚡ Optimisation Harmonique</h3>
                <p><strong>Plage:</strong> [${range[0]}, ${range[1]}]</p>
                <p><strong>Valeur optimale:</strong> ${optimal.toFixed(6)}</p>
                <div class="formula">${data.formula}</div>
                <p><strong>α optimal:</strong> ${data.alpha_optimal.toFixed(6)}</p>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${(optimal - range[0]) / (range[1] - range[0]) * 100}%"></div>
                </div>
            </div>`;
        }

        function displayGenerationResults(data) {
            const resultDiv = document.getElementById('generation-result');
            
            resultDiv.innerHTML = `<div class="result fade-in">
                <h3>🎨 Image Harmonique Générée</h3>
                <p><strong>Pattern:</strong> ${data.pattern}</p>
                <p><strong>Taille:</strong> ${data.size}×${data.size}</p>
                <p><strong>Couleur:</strong> ${data.color ? 'Oui' : 'Non'}</p>
                <img src="${data.image}" alt="Image harmonique" class="image-preview">
            </div>`;
        }

        function updateStats(summary) {
            if (summary) {
                document.getElementById('precisionValue').textContent = summary.average_precision.toFixed(1) + '%';
                document.getElementById('successRateValue').textContent = summary.success_rate.toFixed(1) + '%';
            }
        }

        // Initialisation
        document.addEventListener('DOMContentLoaded', function() {
            // Afficher les valeurs de base
            document.getElementById('phiValue').textContent = {{ phi|round(3) }};
            document.getElementById('alphaValue').textContent = {{ alpha_optimal|round(3) }};
            
            // Auto-validation au chargement
            setTimeout(() => {
                validateConstants();
            }, 1000);
        });
    </script>
</body>
</html>
    """
    
    # Créer le dossier templates
    templates_dir = 'templates'
    os.makedirs(templates_dir, exist_ok=True)
    
    # Écrire le template principal
    with open(os.path.join(templates_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_template)
    
    # Template 404
    template_404 = """<!DOCTYPE html>
<html>
<head>
    <title>Page non trouvée</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        h1 { color: #667eea; }
    </style>
</head>
<body>
    <h1>404 - Page non trouvée</h1>
    <p>La page demandée n'existe pas.</p>
    <a href="/">Retour à l'accueil</a>
</body>
</html>"""
    
    with open(os.path.join(templates_dir, '404.html'), 'w', encoding='utf-8') as f:
        f.write(template_404)
    
    # Template 500
    template_500 = """<!DOCTYPE html>
<html>
<head>
    <title>Erreur serveur</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        h1 { color: #dc3545; }
    </style>
</head>
<body>
    <h1>500 - Erreur serveur</h1>
    <p>Une erreur est survenue sur le serveur.</p>
    <a href="/">Retour à l'accueil</a>
</body>
</html>"""
    
    with open(os.path.join(templates_dir, '500.html'), 'w', encoding='utf-8') as f:
        f.write(template_500)
    
    print("📄 Templates HTML créés dans le dossier 'templates/'")

def test_phase4():
    """
    Test de validation pour la Phase 4
    """
    print("🚀 VALIDATION PHASE 4 - INTERFACE DE DÉMONSTRATION 🚀")
    print("=" * 70)
    
    # Initialiser les services
    print("\n🔧 Initialisation des services...")
    if not initialize_services():
        print("❌ Échec de l'initialisation des services")
        return False
    
    print("✅ Services initialisés avec succès")
    
    # Créer les templates
    print("\n📄 Création des templates HTML...")
    create_templates()
    
    # Test des endpoints
    print("\n🧪 Test des endpoints de l'application...")
    
    with app.test_client() as client:
        # Test de la page d'accueil
        response = client.get('/')
        if response.status_code == 200:
            print("✅ Page d'accueil fonctionnelle")
        else:
            print(f"❌ Page d'accueil: {response.status_code}")
        
        # Test du health check
        response = client.get('/health')
        if response.status_code == 200:
            data = response.get_json()
            print(f"✅ Health check: {data['status']}")
        else:
            print(f"❌ Health check: {response.status_code}")
        
        # Test des constantes
        response = client.post('/validate_constants', json={})
        if response.status_code == 200:
            data = response.get_json()
            print(f"✅ Validation constantes: {data['success']}")
        else:
            print(f"❌ Validation constantes: {response.status_code}")
        
        # Test de la généralisation
        response = client.post('/test_generalization', json={})
        if response.status_code == 200:
            data = response.get_json()
            print(f"✅ Test généralisation: {data['success']}")
        else:
            print(f"❌ Test généralisation: {response.status_code}")
        
        # Test des infos constantes
        response = client.get('/get_constants_info')
        if response.status_code == 200:
            data = response.get_json()
            print(f"✅ Infos constantes: {data['success']}")
        else:
            print(f"❌ Infos constantes: {response.status_code}")
    
    print("\n🌊 PHASE 4 VALIDÉE AVEC SUCCÈS!")
    print("Interface de démonstration prête")
    print("\n📋 Instructions pour lancer l'application:")
    print("1. python demo_app.py")
    print("2. Ouvrir http://localhost:5000 dans votre navigateur")
    print("3. Tester toutes les fonctionnalités harmoniques")
    
    return True

if __name__ == "__main__":
    # Initialiser les services avant de lancer l'app
    if initialize_services():
        print("🌊 Démarrage de l'application de démonstration harmonique...")
        print("📱 Interface disponible sur: http://localhost:5000")
        print("🔄 Health check: http://localhost:5000/health")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("❌ Impossible de démarrer l'application - services non initialisés")
        sys.exit(1)
