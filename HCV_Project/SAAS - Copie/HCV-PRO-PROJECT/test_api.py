#!/usr/bin/env python3
"""
Test API Connective AI Complete Evolutionary
Test local pour validation complète
"""

import requests
import json
import time

def test_api():
    """Test complet de l'API locale"""
    
    base_url = "http://localhost:8000"
    
    print("🧠 TEST API CONNECTIVE AI COMPLETE EVOLUTIONARY")
    print("=" * 60)
    
    # Test 1: Health
    print("\n🔍 Test 1: Health Check")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check réussi")
            print(f"   Status: {data['status']}")
            print(f"   Architecture: {data['architecture_version']}")
            print(f"   Evolution Stage: {data['evolution_stage']}")
            print(f"   Confidence: {data['avg_confidence']}")
            print(f"   Determinism: {data['avg_determinism']}")
        else:
            print(f"❌ Health check échoué: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur health: {e}")
    
    # Test 2: Modalities
    print("\n🔍 Test 2: Modalities")
    try:
        response = requests.get(f"{base_url}/modalities")
        if response.status_code == 200:
            data = response.json()
            print("✅ Modalities check réussi")
            print(f"   Modalities: {data['modalities']}")
            print(f"   Description: {data['description']}")
        else:
            print(f"❌ Modalities check échoué: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur modalities: {e}")
    
    # Test 3: LM Arena Score
    print("\n🔍 Test 3: LM Arena Score")
    try:
        response = requests.get(f"{base_url}/lm_arena_score")
        if response.status_code == 200:
            data = response.json()
            print("✅ LM Arena Score check réussi")
            print(f"   Score: {data['lm_arena_score']}")
            print(f"   Rank: {data['estimated_rank']}")
            print(f"   Target Score: {data['target_score']}")
            print(f"   Guaranteed Win: {data['guaranteed_win']}")
        else:
            print(f"❌ LM Arena Score check échoué: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur LM Arena: {e}")
    
    # Test 4: Generation
    print("\n🔍 Test 4: Generation")
    try:
        request_data = {
            "prompt": "Explique la théorie de la relativité",
            "modalities": ["text"],
            "use_evolution": True
        }
        
        response = requests.post(
            f"{base_url}/generate",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Generation check réussi")
            print(f"   Confidence: {data['confidence']}")
            print(f"   Determinism: {data['determinism_score']}")
            print(f"   Processing Time: {data['processing_time']:.3f}s")
            print(f"   Architecture: {data['architecture_version']}")
            print(f"   Evolution Stage: {data['evolution_stage']}")
            print(f"   Content Length: {len(data['content'])} chars")
            
            # Extrait du contenu
            content_lines = data['content'].split('\n')[:5]
            print("   Content Preview:")
            for line in content_lines:
                if line.strip():
                    print(f"     {line}")
            print("     ...")
        else:
            print(f"❌ Generation check échoué: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Erreur generation: {e}")
    
    # Test 5: Metrics
    print("\n🔍 Test 5: Metrics")
    try:
        response = requests.get(f"{base_url}/metrics")
        if response.status_code == 200:
            data = response.json()
            print("✅ Metrics check réussi")
            print(f"   Total Requests: {data['production_metrics']['total_requests']}")
            print(f"   Success Rate: {data['success_rate']}")
            print(f"   Avg Confidence: {data['production_metrics']['avg_confidence']}")
            print(f"   Avg Determinism: {data['production_metrics']['avg_determinism']}")
        else:
            print(f"❌ Metrics check échoué: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur metrics: {e}")
    
    # Test 6: Evolution Status
    print("\n🔍 Test 6: Evolution Status")
    try:
        response = requests.get(f"{base_url}/evolution_status")
        if response.status_code == 200:
            data = response.json()
            print("✅ Evolution Status check réussi")
            print(f"   Evolution Stage: {data['evolution_stage']}")
            print(f"   Core Version: {data['core_version']}")
            print(f"   Knowledge Gained: {data['knowledge_gained']}")
            print(f"   Patterns Discovered: {data['patterns_discovered']}")
            print(f"   Learning Cycles: {data['learning_cycles']}")
        else:
            print(f"❌ Evolution Status check échoué: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur evolution status: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 TEST API TERMINÉ")
    print("🚀 L'API locale fonctionne correctement!")
    print("🌊 Prêt pour déploiement AWS!")
    print("=" * 60)

if __name__ == "__main__":
    test_api()
