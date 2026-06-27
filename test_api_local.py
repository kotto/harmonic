"""
Test de l'API locale de démonstration
"""

import requests
import json

print('TEST DE L\'API LOCALE DE DEMONSTRATION')
print('=' * 40)

# Test 1: Endpoint de santé
try:
    response = requests.get('http://localhost:8001/health', timeout=5)
    print(f'1. Endpoint /health: {response.status_code}')
    if response.status_code == 200:
        print(f'   Réponse: {response.json()}')
    else:
        print(f'   Erreur: {response.text}')
except Exception as e:
    print(f'1. Endpoint /health: ERREUR - {e}')

print()

# Test 2: Génération simple
try:
    test_prompt = 'Quelle est la capitale de la France?'
    payload = {
        'prompt': test_prompt,
        'max_tokens': 50,
        'temperature': 0.0,
        'verified_mode': True
    }
    
    response = requests.post('http://localhost:8001/generate', 
                           json=payload, 
                           timeout=5)
    print(f'2. Endpoint /generate: {response.status_code}')
    if response.status_code == 200:
        result = response.json()
        print(f'   Prompt: {test_prompt}')
        print(f'   Réponse: {result.get("text", "N/A")[:80]}...')
        print(f'   Response ID: {result.get("response_id", "N/A")}')
        print(f'   Déterministe: {result.get("deterministic", "N/A")}')
    else:
        print(f'   Erreur: {response.text}')
except Exception as e:
    print(f'2. Endpoint /generate: ERREUR - {e}')

print()

# Test 3: Test de déterminisme (même prompt = même réponse)
try:
    print('3. Test de déterminisme:')
    responses = []
    for i in range(3):
        payload = {
            'prompt': '2 + 2 = ?',
            'max_tokens': 30,
            'temperature': 0.0
        }
        response = requests.post('http://localhost:8001/generate', 
                               json=payload, 
                               timeout=5)
        if response.status_code == 200:
            result = response.json()
            responses.append(result.get('response_id', ''))
            print(f'   Tentative {i+1}: Response ID = {result.get("response_id", "N/A")}')
    
    # Vérifier si tous les Response ID sont identiques
    if len(set(responses)) == 1 and responses[0]:
        print(f'   DETERMINISME CONFIRME (tous les Response ID identiques)')
    else:
        print(f'   DETERMINISME NON RESPECTE')
        
except Exception as e:
    print(f'3. Test de déterminisme: ERREUR - {e}')

print()

# Test 4: Test du mode vérifié avec citations
try:
    print('4. Test du mode vérifié:')
    payload = {
        'prompt': 'Quand a été fondée la NASA?',
        'max_tokens': 100,
        'temperature': 0.0,
        'verified_mode': True,
        'sources': ['NASA History Office', 'Encyclopedia Britannica']
    }
    
    response = requests.post('http://localhost:8001/generate', 
                           json=payload, 
                           timeout=5)
    if response.status_code == 200:
        result = response.json()
        print(f'   Prompt: {payload["prompt"]}')
        print(f'   Mode vérifié: {result.get("verified_mode", "N/A")}')
        print(f'   Citations: {result.get("citations", [])}')
    else:
        print(f'   Erreur: {response.text}')
except Exception as e:
    print(f'4. Test du mode vérifié: ERREUR - {e}')

print()
print('=' * 40)
print('TESTS TERMINES')