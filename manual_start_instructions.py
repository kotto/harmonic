#!/usr/bin/env python3
"""
Instructions pour démarrer manuellement l'instance EC2 depuis la console AWS
"""

import json
from datetime import datetime

def create_instructions():
    """Créer les instructions détaillées"""
    
    instructions = {
        "title": "Instructions pour démarrer l'instance EC2 DeepSeek-Harmonic-V2",
        "date": datetime.now().isoformat(),
        "instance_info": {
            "name": "DeepSeek-Harmonic-V2",
            "id": "i-0716d7805ca2c22e9",
            "current_state": "stopped",
            "region": "us-east-1"
        },
        "steps": [
            {
                "step": 1,
                "title": "Accéder à la console AWS",
                "details": [
                    "Ouvrez votre navigateur et allez sur: https://console.aws.amazon.com",
                    "Connectez-vous avec vos identifiants AWS",
                    "Assurez-vous d'être dans la région 'us-east-1' (N. Virginia)"
                ]
            },
            {
                "step": 2,
                "title": "Accéder au service EC2",
                "details": [
                    "Dans la barre de recherche en haut, tapez 'EC2'",
                    "Cliquez sur 'EC2' dans les résultats",
                    "Vous arriverez sur la page de gestion des instances EC2"
                ]
            },
            {
                "step": 3,
                "title": "Trouver l'instance DeepSeek-Harmonic-V2",
                "details": [
                    "Dans le menu de gauche, cliquez sur 'Instances'",
                    "Vous verrez la liste de vos instances EC2",
                    "Recherchez l'instance nommée 'DeepSeek-Harmonic-V2'",
                    "Son ID est: i-0716d7805ca2c22e9",
                    "Son état actuel est: 'Arrêté(e)'"
                ]
            },
            {
                "step": 4,
                "title": "Démarrer l'instance",
                "details": [
                    "Cochez la case à côté de l'instance 'DeepSeek-Harmonic-V2'",
                    "Cliquez sur le bouton 'Actions de l'instance' en haut",
                    "Dans le menu déroulant, allez dans 'État de l'instance'",
                    "Cliquez sur 'Démarrer'",
                    "Confirmez en cliquant sur 'Démarrer' dans la boîte de dialogue"
                ]
            },
            {
                "step": 5,
                "title": "Attendre le démarrage",
                "details": [
                    "L'instance va passer par les états: 'pending' → 'running'",
                    "Cela prend généralement 1-2 minutes",
                    "Rafraîchissez la page pour voir l'état mis à jour",
                    "Une fois en état 'running', notez l'adresse IP publique"
                ]
            },
            {
                "step": 6,
                "title": "Noter l'adresse IP publique",
                "details": [
                    "Dans la ligne de l'instance, regardez la colonne 'Adresse IPv4 publique'",
                    "Notez cette adresse IP (ex: 54.123.45.67)",
                    "Cette IP sera utilisée pour les tests LM Arena"
                ]
            },
            {
                "step": 7,
                "title": "Vérifier les règles de sécurité",
                "details": [
                    "Assurez-vous que le groupe de sécurité autorise le port 8000",
                    "Le nom du groupe de sécurité est: 'connective-ai-complete-sg'",
                    "Vérifiez qu'il y a une règle inbound pour TCP port 8000 depuis 0.0.0.0/0"
                ]
            }
        ],
        "troubleshooting": [
            {
                "issue": "L'instance ne démarre pas",
                "solution": "Vérifiez les limites de service EC2 dans votre compte AWS"
            },
            {
                "issue": "Pas d'adresse IP publique",
                "solution": "L'instance peut être dans un sous-réseau privé. Ajoutez une Elastic IP"
            },
            {
                "issue": "Port 8000 bloqué",
                "solution": "Modifiez le groupe de sécurité pour autoriser le port 8000"
            }
        ],
        "next_steps": [
            "Une fois l'instance démarrée et l'IP publique notée",
            "Exécutez le script de test: python test_quick.py",
            "Puis exécutez les tests LM Arena complets"
        ]
    }
    
    return instructions

def display_instructions():
    """Afficher les instructions de manière lisible"""
    
    instructions = create_instructions()
    
    print("=" * 70)
    print("INSTRUCTIONS POUR DÉMARRER L'INSTANCE EC2 MANUELLEMENT")
    print("=" * 70)
    print()
    
    print(f"Instance: {instructions['instance_info']['name']}")
    print(f"ID: {instructions['instance_info']['id']}")
    print(f"État actuel: {instructions['instance_info']['current_state']}")
    print(f"Région: {instructions['instance_info']['region']}")
    print()
    
    print("ÉTAPES DÉTAILLÉES:")
    print("-" * 70)
    
    for step in instructions['steps']:
        print(f"\nÉtape {step['step']}: {step['title']}")
        for detail in step['details']:
            print(f"  • {detail}")
    
    print("\n" + "=" * 70)
    print("DÉPANNAGE:")
    print("-" * 70)
    
    for issue in instructions['troubleshooting']:
        print(f"\nProblème: {issue['issue']}")
        print(f"Solution: {issue['solution']}")
    
    print("\n" + "=" * 70)
    print("PROCHAINES ÉTAPES APRÈS DÉMARRAGE:")
    print("-" * 70)
    
    for next_step in instructions['next_steps']:
        print(f"• {next_step}")
    
    print("\n" + "=" * 70)
    print("SCRIPT DE TEST RAPIDE APRÈS DÉMARRAGE:")
    print("-" * 70)
    
    print("""
1. Modifiez le fichier test_quick.py avec l'adresse IP publique:
   IP_LIST = ["VOTRE_IP_PUBLIQUE"]  # Remplacez par votre IP

2. Exécutez le test:
   python test_quick.py

3. Si le test réussit, exécutez les tests LM Arena complets:
   python test_ec2_real_deployed.py
    """)
    
    print("=" * 70)

def create_test_script_with_ip(ip_address):
    """Créer un script de test avec l'adresse IP spécifique"""
    
    script = f'''#!/usr/bin/env python3
"""
Test rapide pour l'instance EC2 DeepSeek-Harmonic-V2
IP: {ip_address}
"""

import requests
import time

IP_ADDRESS = "{ip_address}"
PORT = 8000
ENDPOINT = "/health"

def test_instance():
    """Tester l'instance EC2"""
    print(f"Testing EC2 Instance: DeepSeek-Harmonic-V2")
    print(f"IP Address: {ip_address}")
    print(f"Port: {PORT}")
    print("=" * 50)
    
    url = f"http://{ip_address}:{PORT}{ENDPOINT}"
    
    try:
        start = time.time()
        response = requests.get(url, timeout=5)
        elapsed = time.time() - start
        
        print(f"URL: {url}")
        print(f"Status: HTTP {response.status_code}")
        print(f"Response Time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            print(f"Response: {response.text[:100]}")
            print("\\nSUCCESS: Instance is accessible!")
            
            # Tester l'endpoint generate
            generate_url = url.replace("/health", "/generate")
            print(f"\\nTesting generate endpoint: {generate_url}")
            
            payload = {{"prompt": "Hello, test", "max_tokens": 20}}
            
            try:
                gen_response = requests.post(generate_url, json=payload, timeout=10)
                print(f"  Generate Status: HTTP {gen_response.status_code}")
                
                if gen_response.status_code == 200:
                    print(f"  Generate Response: {gen_response.text[:150]}")
                    return True
                    
            except Exception as e:
                print(f"  Generate Error: {{str(e)[:100]}}")
                
        else:
            print(f"Error: {response.text[:100]}")
            
    except requests.exceptions.Timeout:
        print("Timeout after 5 seconds")
    except requests.exceptions.ConnectionError:
        print("Connection refused")
    except Exception as e:
        print(f"Error: {{str(e)[:100]}}")
    
    return False

if __name__ == "__main__":
    success = test_instance()
    
    if success:
        print("\\n" + "=" * 50)
        print("READY FOR LM ARENA TESTS")
        print("=" * 50)
        print("\\nExecute: python test_ec2_real_deployed.py")
    else:
        print("\\n" + "=" * 50)
        print("CHECK INSTANCE CONFIGURATION")
        print("=" * 50)
        print("\\n1. Verify instance is running")
        print("2. Check security group rules for port 8000")
        print("3. Verify service is started on the instance")
'''
    
    filename = f"test_instance_{ip_address.replace('.', '_')}.py"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(script)
    
    return filename

if __name__ == "__main__":
    # Afficher les instructions
    display_instructions()
    
    # Demander l'adresse IP publique
    print("\n" + "=" * 70)
    ip_address = input("Entrez l'adresse IP publique de l'instance (après démarrage): ").strip()
    
    if ip_address:
        # Créer un script de test personnalisé
        test_script = create_test_script_with_ip(ip_address)
        print(f"\nScript de test créé: {test_script}")
        print(f"Exécutez-le avec: python {test_script}")
    else:
        print("\nAucune adresse IP fournie. Modifiez manuellement les scripts de test.")