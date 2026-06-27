"""
Dashboard SaaS simplifié pour développement local
Connecté à l'API locale de démonstration
"""

from flask import Flask, render_template_string, request, jsonify
import requests
import json
from datetime import datetime

app = Flask(__name__)

# Configuration
LOCAL_API_URL = "http://localhost:8001"
DEMO_USER = {
    "email": "demo@harmonica.ai",
    "tier": "pro",
    "monthly_tokens": 100000,
    "tokens_used": 0,
    "created_at": datetime.now().isoformat()
}

# Template HTML simple
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Harmonic AI - Dashboard Local</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            color: #333;
            font-size: 28px;
            margin-bottom: 8px;
        }
        
        .header p {
            color: #666;
            font-size: 16px;
        }
        
        .user-info {
            display: flex;
            gap: 16px;
            margin-top: 16px;
            flex-wrap: wrap;
        }
        
        .user-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 16px;
            flex: 1;
            min-width: 200px;
        }
        
        .user-card h3 {
            color: #333;
            font-size: 16px;
            margin-bottom: 8px;
        }
        
        .user-card p {
            color: #666;
            font-size: 14px;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }
        
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
        }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .card h2 {
            color: #333;
            font-size: 20px;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .generator-form {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .form-group label {
            color: #333;
            font-weight: 500;
            font-size: 14px;
        }
        
        .form-group textarea {
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            resize: vertical;
            min-height: 120px;
        }
        
        .form-group input[type="number"] {
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
        }
        
        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .checkbox-group input[type="checkbox"] {
            width: 18px;
            height: 18px;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px 24px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        .btn:active {
            transform: translateY(0);
        }
        
        .response-container {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 16px;
            margin-top: 16px;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .response-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .response-id {
            font-family: monospace;
            background: #e9ecef;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            color: #495057;
        }
        
        .response-content {
            font-size: 14px;
            line-height: 1.6;
            color: #333;
            white-space: pre-wrap;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
            margin-top: 16px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 4px;
        }
        
        .stat-label {
            font-size: 12px;
            opacity: 0.9;
        }
        
        .api-status {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
        }
        
        .status-online {
            background: #d4edda;
            color: #155724;
        }
        
        .status-offline {
            background: #f8d7da;
            color: #721c24;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }
        
        .online-dot {
            background: #28a745;
        }
        
        .offline-dot {
            background: #dc3545;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            color: #666;
        }
        
        .loading.active {
            display: block;
        }
        
        .error-message {
            background: #f8d7da;
            color: #721c24;
            padding: 12px;
            border-radius: 8px;
            margin-top: 16px;
            font-size: 14px;
        }
        
        .success-message {
            background: #d4edda;
            color: #155724;
            padding: 12px;
            border-radius: 8px;
            margin-top: 16px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Harmonic AI Dashboard (Mode Local)</h1>
            <p>Développement local avec connexion internet instable</p>
            
            <div class="user-info">
                <div class="user-card">
                    <h3>Utilisateur</h3>
                    <p>{{ user.email }}</p>
                </div>
                <div class="user-card">
                    <h3>Tier</h3>
                    <p>{{ user.tier|upper }}</p>
                </div>
                <div class="user-card">
                    <h3>Statut API</h3>
                    <div class="api-status {{ 'status-online' if api_online else 'status-offline' }}">
                        <div class="status-dot {{ 'online-dot' if api_online else 'offline-dot' }}"></div>
                        {{ 'EN LIGNE' if api_online else 'HORS LIGNE' }}
                    </div>
                </div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="card">
                <h2>Générateur de texte</h2>
                <form id="generatorForm" class="generator-form">
                    <div class="form-group">
                        <label for="prompt">Prompt:</label>
                        <textarea id="prompt" name="prompt" placeholder="Entrez votre prompt ici...">Expliquez comment Harmonic AI garantit le déterminisme et zéro hallucination.</textarea>
                    </div>
                    
                    <div class="form-group">
                        <label for="max_tokens">Tokens maximum:</label>
                        <input type="number" id="max_tokens" name="max_tokens" value="200" min="10" max="1000">
                    </div>
                    
                    <div class="checkbox-group">
                        <input type="checkbox" id="verified_mode" name="verified_mode">
                        <label for="verified_mode">Mode vérifié (avec citations)</label>
                    </div>
                    
                    <button type="submit" class="btn">Générer la réponse</button>
                </form>
                
                <div id="loading" class="loading">
                    ⏳ Génération en cours...
                </div>
                
                <div id="responseContainer" class="response-container" style="display: none;">
                    <div class="response-header">
                        <span>Réponse générée</span>
                        <span class="response-id" id="responseId"></span>
                    </div>
                    <div class="response-content" id="responseContent"></div>
                    
                    <div id="responseStats" style="margin-top: 16px; font-size: 12px; color: #666;">
                        <div>Tokens générés: <span id="tokensGenerated"></span></div>
                        <div>Temps de réponse: <span id="responseTime"></span> ms</div>
                        <div>Déterministe: <span id="deterministic"></span></div>
                    </div>
                </div>
                
                <div id="errorMessage" class="error-message" style="display: none;"></div>
                <div id="successMessage" class="success-message" style="display: none;"></div>
            </div>
            
            <div class="card">
                <h2>Statistiques</h2>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{{ user.monthly_tokens|intcomma }}</div>
                        <div class="stat-label">TOKENS MENSUELS</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-value">{{ user.tokens_used|intcomma }}</div>
                        <div class="stat-label">TOKENS UTILISÉS</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-value">{{ user.tokens_remaining|intcomma }}</div>
                        <div class="stat-label">TOKENS RESTANTS</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-value">{{ user.usage_percentage|round(1) }}%</div>
                        <div class="stat-label">UTILISATION</div>
                    </div>
                </div>
                
                <div style="margin-top: 24px;">
                    <h3 style="font-size: 16px; margin-bottom: 12px;">Informations système</h3>
                    <div style="background: #f8f9fa; padding: 16px; border-radius: 8px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #666;">Mode:</span>
                            <span style="font-weight: 500;">Développement local</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span style="color: #666;">API URL:</span>
                            <span style="font-family: monospace; font-size: 12px;">{{ api_url }}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #666;">Date:</span>
                            <span style="font-size: 12px;">{{ current_date }}</span>
                        </div>
                    </div>
                </div>
                
                <div style="margin-top: 24px;">
                    <h3 style="font-size: 16px; margin-bottom: 12px;">Tests LM Arena</h3>
                    <button onclick="runLMArenaTests()" class="btn" style="width: 100%;">Exécuter les tests optimisés</button>
                    <p style="font-size: 12px; color: #666; margin-top: 8px;">
                        Tests avec gestion des erreurs de connexion et sauvegarde incrémentale
                    </p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Fonctions utilitaires
        function intcomma(value) {
            return value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        }
        
        // Gestion du formulaire
        document.getElementById('generatorForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const prompt = document.getElementById('prompt').value;
            const maxTokens = parseInt(document.getElementById('max_tokens').value);
            const verifiedMode = document.getElementById('verified_mode').checked;
            
            // Afficher le loading
            document.getElementById('loading').classList.add('active');
            document.getElementById('responseContainer').style.display = 'none';
            document.getElementById('errorMessage').style.display = 'none';
            document.getElementById('successMessage').style.display = 'none';
            
            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        prompt: prompt,
                        max_tokens: maxTokens,
                        temperature: 0.0,
                        verified_mode: verifiedMode
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    // Afficher la réponse
                    document.getElementById('responseId').textContent = data.response_id;
                    document.getElementById('responseContent').textContent = data.text;
                    document.getElementById('tokensGenerated').textContent = data.tokens_generated;
                    document.getElementById('responseTime').textContent = data.response_time_ms;
                    document.getElementById('deterministic').textContent = data.deterministic ? 'OUI' : 'NON';
                    
                    document.getElementById('responseContainer').style.display = 'block';
                    document.getElementById('successMessage').textContent = 'Réponse générée avec succès!';
                    document.getElementById('successMessage').style.display = 'block';
                    
                    // Mettre à jour les statistiques
                    updateStats();
                } else {
                    document.getElementById('errorMessage').textContent = data.error || 'Erreur lors de la génération';
                    document.getElementById('errorMessage').style.display = 'block';
                }
            } catch (error) {
                document.getElementById('errorMessage').textContent = 'Erreur de connexion: ' + error.message;
                document.getElementById('errorMessage').style.display = 'block';
            } finally {
                document.getElementById('loading').classList.remove('active');
            }
        });
        
        // Mettre à jour les statistiques
        async function updateStats() {
            try {
                const response = await fetch('/api/stats');
                if (response.ok) {
                    const data = await response.json();
                    
                    // Mettre à jour l'affichage des statistiques
                    document.querySelectorAll('.stat-value').forEach(el => {
                        const label = el.nextElementSibling.textContent;
                        if (label.includes('MENSUELS')) {
                            el.textContent = intcomma(data.user.monthly_tokens);
                        } else if (label.includes('UTILISÉS')) {
                            el.textContent = intcomma(data.user.tokens_used);
                        } else if (label.includes('RESTANTS')) {
                            el.textContent = intcomma(data.user.tokens_remaining);
                        } else if (label.includes('UTILISATION')) {
                            el.textContent = data.user.usage_percentage.toFixed(1) + '%';
                        }
                    });
                }
            } catch (error) {
                console.error('Erreur mise à jour stats:', error);
            }
        }
        
        // Exécuter les tests LM Arena
        async function runLMArenaTests() {
            const loading = document.getElementById('loading');
            const errorMessage = document.getElementById('errorMessage');
            const successMessage = document.getElementById('successMessage');
            
            loading.classList.add('active');
            errorMessage.style.display = 'none';
            successMessage.style.display = 'none';
            
            try {
                const response = await fetch('/api/run-lm-arena-tests', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    successMessage.textContent = `Tests exécutés: ${data.success}/${data.total} réussis`;
                    successMessage.style.display = 'block';
                    
                    // Afficher les détails si disponibles
                    if (data.details) {
                        console.log('Détails des tests:', data.details);
                    }
                } else {
                    errorMessage.textContent = data.error || 'Erreur lors des tests';
                    errorMessage.style.display = 'block';
                }
            } catch (error) {
                errorMessage.textContent = 'Erreur de connexion: ' + error.message;
                errorMessage.style.display = 'block';
            } finally {
                loading.classList.remove('active');
            }
        }
        
        // Vérifier le statut de l'API au chargement
        updateStats();
    </script>
</body>
</html>
"""

def check_api_status():
    """Vérifier si l'API locale est en ligne"""
    try:
        response = requests.get(f"{LOCAL_API_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

@app.route('/')
def dashboard_home():
    """Page principale du dashboard"""
    api_online = check_api_status()
    
    # Template filters
    def intcomma(value):
        return f"{value:,}"
    
    def round_filter(value, digits=0):
        return round(value, digits)
    
    return render_template_string(
        DASHBOARD_TEMPLATE,
        user=DEMO_USER,
        api_online=api_online,
        api_url=LOCAL_API_URL,
        current_date=datetime.now().strftime('%d/%m/%Y %H:%M'),
        intcomma=intcomma,
        round=round_filter
    )

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """API: Générer du texte via l'API locale"""
    try:
        data = request.get_json()
        
        # Appeler l'API locale
        response = requests.post(
            f"{LOCAL_API_URL}/generate",
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Simuler l'utilisation de tokens
            tokens_used = result.get('tokens_generated', 50)
            DEMO_USER['tokens_used'] += tokens_used
            
            return jsonify(result)
        else:
            return jsonify({
                'error': f'Erreur API locale: {response.status_code}',
                'details': response.text[:200]
            }), 500
            
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Timeout de l\'API locale'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'API locale non accessible'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """API: Obtenir les statistiques"""
    user_stats = DEMO_USER.copy()
    user_stats['tokens_remaining'] = max(0, user_stats['monthly_tokens'] - user_stats['tokens_used'])
    user_stats['usage_percentage'] = (user_stats['tokens_used'] / user_stats['monthly_tokens'] * 100) if user_stats['monthly_tokens'] > 0 else 0
    
    return jsonify({
        'user': user_stats,
        'api_status': check_api_status(),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/run-lm-arena-tests', methods=['POST'])
def run_lm_arena_tests():
    """API: Exécuter les tests LM Arena optimisés"""
    try:
        # Importer et exécuter les tests
        from lm_arena_optimise import LM_Arena_Optimise
        
        tester = LM_Arena_Optimise(base_url=LOCAL_API_URL, max_retries=3)
        
        # Exécuter un sous-ensemble de tests pour démonstration
        test_prompts = [
            "Quelle est la capitale de la France?",
            "Explique le théorème de Pythagore",
            "Écris un programme Python qui calcule la factorielle d'un nombre"
        ]
        
        results = []
        for prompt in test_prompts:
            result = tester.test_with_retry(prompt, max_tokens=100)
            results.append({
                'prompt': prompt[:50] + '...' if len(prompt) > 50 else prompt,
                'success': result['success'],
                'attempts': result.get('attempts', 1)
            })
        
        success_count = sum(1 for r in results if r['success'])
        
        return jsonify({
            'success': True,
            'total': len(results),
            'success_count': success_count,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Erreur lors des tests: {str(e)}'
        }), 500

@app.route('/health')
def health():
    """Endpoint de santé"""
    return jsonify({
        'status': 'healthy',
        'mode': 'local_dashboard',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == "__main__":
    print("=" * 50)
    print("HARMONIC AI DASHBOARD LOCAL SIMPLIFIE")
    print("=" * 50)
    print("URL: http://localhost:5001")
    print("API locale: http://localhost:8001")
    print("Mode: Développement local avec connexion instable")
    print("=" * 50)
    
    app.run(debug=True, port=5001)