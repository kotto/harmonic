"""
Test du dashboard SaaS local
"""

import requests
import json

print('TEST DU DASHBOARD SAAS LOCAL')
print('=' * 40)

# Test 1: Endpoint de santé du dashboard
try:
    response = requests.get('http://127.0.0.1:5000/health', timeout=5)
    print(f'1. Endpoint /health: {response.status_code}')
    if response.status_code == 200:
        print(f'   Réponse: {response.json()}')
    else:
        print(f'   Erreur: {response.text}')
except Exception as e:
    print(f'1. Endpoint /health: ERREUR - {e}')

print()

# Test 2: Création d'un utilisateur de test
try:
    print('2. Création d\'un utilisateur de test:')
    payload = {
        'email': 'demo_local@harmonica.ai',
        'tier': 'starter'
    }
    
    response = requests.post('http://127.0.0.1:5000/api/users', 
                           json=payload, 
                           timeout=5)
    
    print(f'   Status: {response.status_code}')
    if response.status_code == 201:
        user_data = response.json()
        print(f'   Utilisateur créé: {user_data.get("email", "N/A")}')
        print(f'   Tier: {user_data.get("tier", "N/A")}')
        print(f'   API Key: {user_data.get("api_key", "N/A")[:20]}...')
    else:
        print(f'   Erreur: {response.text}')
except Exception as e:
    print(f'2. Création utilisateur: ERREUR - {e}')

print()

# Test 3: Test de l'API de génération via le dashboard
try:
    print('3. Test de génération via dashboard:')
    
    # D'abord, obtenir un utilisateur existant
    response = requests.get('http://127.0.0.1:5000/api/users/demo@harmonica.ai', 
                          timeout=5)
    
    if response.status_code == 200:
        user_data = response.json()
        api_key = user_data.get('api_key')
        
        # Utiliser l'API key pour générer une réponse
        headers = {'X-API-Key': api_key}
        payload = {
            'prompt': 'Test de connexion locale avec dashboard',
            'max_tokens': 50,
            'temperature': 0.0
        }
        
        response = requests.post('http://127.0.0.1:5000/api/generate',
                               json=payload,
                               headers=headers,
                               timeout=5)
        
        print(f'   Status génération: {response.status_code}')
        if response.status_code == 200:
            result = response.json()
            print(f'   Réponse: {result.get("text", "N/A")[:60]}...')
            print(f'   Tokens utilisés: {result.get("tokens_used", "N/A")}')
            print(f'   Response ID: {result.get("response_id", "N/A")}')
        else:
            print(f'   Erreur génération: {response.text}')
    else:
        print(f'   Erreur récupération utilisateur: {response.text}')
        
except Exception as e:
    print(f'3. Test génération: ERREUR - {e}')

print()

# Test 4: Vérification des statistiques
try:
    print('4. Vérification des statistiques:')
    
    response = requests.get('http://127.0.0.1:5000/api/stats', timeout=5)
    
    print(f'   Status: {response.status_code}')
    if response.status_code == 200:
        stats = response.json()
        print(f'   Utilisateurs actifs: {stats.get("active_users", "N/A")}')
        print(f'   Requêtes totales: {stats.get("total_requests", "N/A")}')
        print(f'   Tokens totaux: {stats.get("total_tokens", "N/A")}')
    else:
        print(f'   Erreur: {response.text}')
        
except Exception as e:
    print(f'4. Statistiques: ERREUR - {e}')

print()
print('=' * 40)
print('TESTS TERMINES')
print()
print('URLs disponibles:')
print('  - Dashboard: http://127.0.0.1:5000')
print('  - API locale: http://localhost:8001')
print('  - Documentation API: http://127.0.0.1:5000/api/docs')