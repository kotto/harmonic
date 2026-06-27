"""
Test simple du dashboard SaaS local
"""

import requests
import json

print('TEST SIMPLE DU DASHBOARD SAAS LOCAL')
print('=' * 40)

# D'abord, nous devons obtenir l'API key de l'utilisateur de test
# En regardant le code, l'utilisateur de test est créé automatiquement
# Nous allons d'abord tester l'accès à la page d'accueil

print('1. Test de la page d\'accueil (sans authentification):')
try:
    response = requests.get('http://127.0.0.1:5000/', timeout=5)
    print(f'   Status: {response.status_code}')
    print(f'   Réponse: {response.text[:100]}...')
except Exception as e:
    print(f'   ERREUR: {e}')

print()

# Test 2: Vérifier si nous pouvons obtenir l'API key via le code
print('2. Test de création d\'utilisateur via code Python:')
try:
    # Importer directement depuis le dashboard
    from dashboard_mvp import HarmonicAIDashboard
    
    dashboard = HarmonicAIDashboard()
    
    # Vérifier si l'utilisateur de test existe déjà
    with dashboard._get_connection() as conn:
        cursor = conn.execute('SELECT * FROM users WHERE email = ?', ('demo@harmonica.ai',))
        user_data = cursor.fetchone()
        
        if user_data:
            print(f'   Utilisateur de test trouvé: {user_data["email"]}')
            print(f'   API Key: {user_data["api_key"]}')
            
            # Maintenant, testons l'API avec cette clé
            headers = {'X-API-Key': user_data['api_key']}
            
            # Test de l'endpoint /api/stats
            response = requests.get('http://127.0.0.1:5000/api/stats', 
                                  headers=headers, 
                                  timeout=5)
            
            print(f'   Test /api/stats: {response.status_code}')
            if response.status_code == 200:
                stats = response.json()
                print(f'   Email: {stats.get("user", {}).get("email", "N/A")}')
                print(f'   Tier: {stats.get("user", {}).get("tier", "N/A")}')
                print(f'   Tokens restants: {stats.get("user", {}).get("tokens_remaining", "N/A")}')
            else:
                print(f'   Erreur: {response.text}')
        else:
            print('   Utilisateur de test non trouvé, création...')
            success, test_user = dashboard.create_user('demo@harmonica.ai', 'pro')
            if success:
                print(f'   Utilisateur créé: {test_user.email}')
                print(f'   API Key: {test_user.api_key}')
            else:
                print('   Erreur de création')
                
except Exception as e:
    print(f'   ERREUR: {e}')

print()

# Test 3: Test de l'API de génération
print('3. Test de l\'API de génération:')
try:
    # Obtenir l'API key depuis la base de données
    from dashboard_mvp import HarmonicAIDashboard
    
    dashboard = HarmonicAIDashboard()
    
    with dashboard._get_connection() as conn:
        cursor = conn.execute('SELECT api_key FROM users WHERE email = ?', ('demo@harmonica.ai',))
        user_data = cursor.fetchone()
        
        if user_data:
            api_key = user_data['api_key']
            headers = {'X-API-Key': api_key}
            
            payload = {
                'prompt': 'Bonjour Harmonic AI, comment fonctionne le déterminisme?',
                'max_tokens': 100,
                'temperature': 0.0,
                'verified_mode': True
            }
            
            response = requests.post('http://127.0.0.1:5000/api/generate',
                                   json=payload,
                                   headers=headers,
                                   timeout=10)
            
            print(f'   Status: {response.status_code}')
            if response.status_code == 200:
                result = response.json()
                print(f'   Réponse: {result.get("text", "N/A")[:80]}...')
                print(f'   Tokens utilisés: {result.get("tokens_used", "N/A")}')
                print(f'   Response ID: {result.get("response_id", "N/A")}')
            else:
                print(f'   Erreur: {response.text}')
        else:
            print('   Utilisateur non trouvé')
            
except Exception as e:
    print(f'   ERREUR: {e}')

print()
print('=' * 40)
print('RESUME:')
print('  - Dashboard: http://127.0.0.1:5000')
print('  - API locale: http://localhost:8001')
print('  - Utilisateur de test: demo@harmonica.ai')
print('  - Pour accéder au dashboard, utilisez l\'API key affichée ci-dessus')