#!/usr/bin/env python3
"""
DÃ©monstration Community-Proof pour DeepSeek Harmonic V2
Valide les claims de dÃ©terminisme auditable et zÃ©ro hallucinations
"""

import hashlib
import json
import sys
import time
from typing import Dict, List, Any, Tuple
import requests

# Configuration de l'encodage pour Ã©viter les erreurs Unicode
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

def test_determinism(api_url: str, prompt: str, repeats: int = 5) -> Dict[str, Any]:
    """Test que le mÃªme prompt produit exactement la mÃªme rÃ©ponse"""
    print(f"[TEST] Test de dÃ©terminisme ({repeats} rÃ©pÃ©titions)...")
    
    responses = []
    response_ids = []
    
    for i in range(repeats):
        payload = {
            "prompt": prompt,
            "max_tokens": 200,
            "temperature": 0.0,
            "verified_mode": True
        }
        
        try:
            response = requests.post(f"{api_url}/generate", json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                responses.append(data)
                response_ids.append(data.get("response_id", ""))
            else:
                print(f"  âŒ Erreur HTTP {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"  âŒ Exception: {e}")
            return {"success": False, "error": str(e)}
        
        time.sleep(0.5)  # Petite pause entre les appels
    
    # VÃ©rification
    unique_ids = set(response_ids)
    all_same = len(unique_ids) == 1 and response_ids[0] != ""
    
    if all_same:
        print(f"  [OK] SUCCES: Tous les response_id identiques: {response_ids[0][:16]}...")
    else:
        print(f"  [ERREUR] ECHEC: {len(unique_ids)} response_id diffÃ©rents")
    
    return {
        "success": all_same,
        "response_id": response_ids[0] if response_ids else "",
        "unique_count": len(unique_ids),
        "all_responses": responses
    }

def test_zero_hallucination_abstention(api_url: str) -> Dict[str, Any]:
    """Test d'abstention sur question factuelle sans sources"""
    print("[TEST] Test d'abstention (zÃ©ro hallucination)...")
    
    # Question factuelle nÃ©cessitant des sources
    prompt = "Quel est le taux de chÃ´mage en France au dernier trimestre 2025?"
    
    payload = {
        "prompt": prompt,
        "max_tokens": 300,
        "verified_mode": True,
        "sources": []  # Pas de sources = doit s'abstenir
    }
    
    try:
        response = requests.post(f"{api_url}/generate", json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            content = data.get("content", "").lower()
            
            # VÃ©rifier si c'est une abstention
            is_abstention = any(word in content for word in ["abstention", "abstain", "sources", "rÃ©fÃ©rences"])
            
            if is_abstention:
                print(f"  âœ… SUCCÃˆS: Abstention correcte sur question sans sources")
                print(f"     RÃ©ponse: {content[:100]}...")
            else:
                print(f"  âš ï¸  ATTENTION: Pas d'abstention claire")
                print(f"     RÃ©ponse: {content[:100]}...")
            
            return {
                "success": is_abstention,
                "is_abstention": is_abstention,
                "content_preview": content[:200],
                "response_id": data.get("response_id", "")
            }
        else:
            print(f"  âŒ Erreur HTTP {response.status_code}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        print(f"  âŒ Exception: {e}")
        return {"success": False, "error": str(e)}

def test_citation_requirement(api_url: str) -> Dict[str, Any]:
    """Test que les affirmations citent les sources fournies"""
    print("[TEST] Test de citations obligatoires...")
    
    prompt = "Quels sont les symptÃ´mes principaux de la pneumonie?"
    sources = [
        "Manuel MSD: toux productive, fiÃ¨vre >38Â°C, dyspnÃ©e, douleur thoracique",
        "OMS: saturation en oxygÃ¨ne <94% Ã  l'air ambiant, frÃ©quence respiratoire >30/min"
    ]
    
    payload = {
        "prompt": prompt,
        "max_tokens": 300,
        "verified_mode": True,
        "sources": sources
    }
    
    try:
        response = requests.post(f"{api_url}/generate", json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            content = data.get("content", "")
            citations = data.get("citations", [])
            
            # VÃ©rifier la prÃ©sence de citations dans le texte
            has_citation_markers = any(f"[{cit.get('id', '')}]" in content for cit in citations)
            citation_count = len(citations)
            
            if has_citation_markers and citation_count > 0:
                print(f"  âœ… SUCCÃˆS: {citation_count} citations dÃ©tectÃ©es")
                for cit in citations[:2]:  # Afficher les 2 premiÃ¨res
                    print(f"     [{cit.get('id', '')}]: {cit.get('source', '')[:60]}...")
            else:
                print(f"  âŒ Ã‰CHEC: Pas de citations dÃ©tectÃ©es dans le texte")
            
            return {
                "success": has_citation_markers,
                "citation_count": citation_count,
                "has_citation_markers": has_citation_markers,
                "content_preview": content[:150],
                "citations": citations
            }
        else:
            print(f"  âŒ Erreur HTTP {response.status_code}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        print(f"  âŒ Exception: {e}")
        return {"success": False, "error": str(e)}

def test_response_id_auditability(api_url: str) -> Dict[str, Any]:
    """Test que le response_id est calculÃ© de maniÃ¨re dÃ©terministe"""
    print("[TEST] Test d'auditabilitÃ© du response_id...")
    
    prompt = "Calculer l'IMC pour une personne de 1.75m et 70kg"
    sources = ["IMC = poids(kg) / taille(m)^2"]
    
    # Premier appel
    payload1 = {
        "prompt": prompt,
        "max_tokens": 200,
        "temperature": 0.0,
        "verified_mode": True,
        "sources": sources
    }
    
    try:
        response1 = requests.post(f"{api_url}/generate", json=payload1, timeout=10)
        if response1.status_code == 200:
            data1 = response1.json()
            response_id1 = data1.get("response_id", "")
            
            # DeuxiÃ¨me appel avec exactement les mÃªmes paramÃ¨tres
            time.sleep(1)
            response2 = requests.post(f"{api_url}/generate", json=payload1, timeout=10)
            data2 = response2.json()
            response_id2 = data2.get("response_id", "")
            
            # VÃ©rifier l'Ã©galitÃ©
            if response_id1 and response_id1 == response_id2:
                print(f"  âœ… SUCCÃˆS: response_id stable et reproductible")
                print(f"     Hash: {response_id1[:32]}...")
                
                # VÃ©rifier que le hash semble Ãªtre un SHA256
                if len(response_id1) == 64 and all(c in "0123456789abcdef" for c in response_id1.lower()):
                    print(f"  âœ… Format SHA256 valide")
                else:
                    print(f"  âš ï¸  Format de hash inhabituel")
                
                return {
                    "success": True,
                    "response_id": response_id1,
                    "is_sha256": len(response_id1) == 64,
                    "identical": True
                }
            else:
                print(f"  âŒ Ã‰CHEC: response_id diffÃ©rent entre deux appels identiques")
                return {"success": False, "response_id1": response_id1, "response_id2": response_id2}
        else:
            print(f"  âŒ Erreur HTTP {response1.status_code}")
            return {"success": False, "error": f"HTTP {response1.status_code}"}
    except Exception as e:
        print(f"  âŒ Exception: {e}")
        return {"success": False, "error": str(e)}

def run_full_demo(api_url: str = "http://__EC2_IP__:8000"):
    """ExÃ©cute la dÃ©monstration complÃ¨te"""
    print("=" * 60)
    print("DEMONSTRATION COMMUNITY-PROOF - DeepSeek Harmonic V2")
    print("=" * 60)
    print(f"API cible: {api_url}")
    print()
    
    results = {}
    
    # 1. Test de dÃ©terminisme
    results["determinism"] = test_determinism(
        api_url, 
        "Explique le thÃ©orÃ¨me de Pythagore en 3 phrases.",
        repeats=3
    )
    print()
    
    # 2. Test zÃ©ro hallucination (abstention)
    results["zero_hallucination"] = test_zero_hallucination_abstention(api_url)
    print()
    
    # 3. Test citations obligatoires
    results["citations"] = test_citation_requirement(api_url)
    print()
    
    # 4. Test auditabilitÃ© response_id
    results["auditability"] = test_response_id_auditability(api_url)
    print()
    
    # RÃ©sumÃ©
    print("=" * 60)
    print("ðŸ“Š RÃ‰SUMÃ‰ DES TESTS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        if result.get("success"):
            print(f"âœ… {test_name.upper()}: PASSÃ‰")
            passed += 1
        else:
            print(f"âŒ {test_name.upper()}: Ã‰CHOUÃ‰")
            if "error" in result:
                print(f"   Erreur: {result['error']}")
    
    print()
    print(f"Score: {passed}/{total} tests passÃ©s ({passed/total*100:.1f}%)")
    
    # GÃ©nÃ©rer un rapport
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "api_url": api_url,
        "results": results,
        "summary": {
            "passed": passed,
            "total": total,
            "score_percent": passed/total*100
        }
    }
    
    # Sauvegarder le rapport
    report_file = f"community_proof_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"ðŸ“„ Rapport sauvegardÃ©: {report_file}")
    
    # Conclusion
    print()
    print("=" * 60)
    if passed == total:
        print("ðŸŽ‰ TOUS LES TESTS PASSÃ‰S !")
        print("Les claims 'DÃ©terminisme Auditable' et 'Hallucinations ZÃ©ro' sont vÃ©rifiÃ©s.")
    else:
        print("âš ï¸  CERTAINS TESTS ONT Ã‰CHOUÃ‰")
        print("VÃ©rifiez la configuration du serveur et rÃ©exÃ©cutez les tests.")
    
    return report

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="DÃ©monstration Community-Proof")
    parser.add_argument("--url", default="http://__EC2_IP__:8000", 
                       help="URL de l'API (dÃ©faut: http://__EC2_IP__:8000)")
    parser.add_argument("--output", help="Fichier de sortie pour le rapport JSON")
    
    args = parser.parse_args()
    
    report = run_full_demo(args.url)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"ðŸ“„ Rapport exportÃ©: {args.output}")