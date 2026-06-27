#!/usr/bin/env python3
"""
Test complet des fonctionnalités HCV PRO Enterprise AWS
===============================================
Test exhaustif de toutes les API et fonctionnalités
"""

import requests
import json
import time
import tempfile
import os
import sys
from pathlib import Path

class HCVEnterpriseTester:
    def __init__(self, base_url="http://localhost:8081"):
        self.base_url = base_url
        self.token = None
        self.test_results = []
        self.temp_files = []
        
    def log_test(self, test_name, success, details=""):
        """Enregistrer le résultat d'un test"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            'test': test_name,
            'status': status,
            'success': success,
            'details': details,
            'timestamp': time.time()
        }
        self.test_results.append(result)
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
    
    def create_test_file(self, content="Test content for HCV compression", filename="test.txt"):
        """Créer un fichier de test"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_file.write(content * 1000)  # Fichier de taille raisonnable
        temp_file.close()
        self.temp_files.append(temp_file.name)
        return temp_file.name
    
    def test_server_health(self):
        """Test 1: Vérifier que le serveur répond"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            success = response.status_code == 200
            data = response.json() if success else {}
            details = f"Status: {response.status_code}"
            if success:
                details += f" | Codec: {data.get('codec', 'N/A')}"
            self.log_test("Health Check", success, details)
            return success
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
            return False
    
    def test_authentication(self):
        """Test 2: Authentification"""
        # Test avec identifiants valides
        try:
            auth_data = {
                "username": "admin",
                "password": "HCV_PRO_2024_ENTERPRISE"
            }
            response = requests.post(f"{self.base_url}/api/auth", 
                                   json=auth_data, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.token = data.get('token')
                    details = f"Token reçu: {self.token[:20]}..."
                    self.log_test("Authentication (admin)", True, details)
                    return True
                else:
                    self.log_test("Authentication (admin)", False, data.get('error', 'Unknown error'))
                    return False
            else:
                self.log_test("Authentication (admin)", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Authentication (admin)", False, f"Exception: {str(e)}")
            return False
    
    def test_authentication_invalid(self):
        """Test 3: Authentification invalide"""
        try:
            auth_data = {
                "username": "invalid",
                "password": "wrong"
            }
            response = requests.post(f"{self.base_url}/api/auth", 
                                   json=auth_data, timeout=5)
            
            success = response.status_code == 401
            details = f"Status: {response.status_code}"
            self.log_test("Authentication (invalid)", success, details)
            return success
            
        except Exception as e:
            self.log_test("Authentication (invalid)", False, f"Exception: {str(e)}")
            return False
    
    def get_headers(self):
        """Obtenir les headers avec authentification"""
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def test_status_endpoint(self):
        """Test 4: Endpoint status"""
        try:
            response = requests.get(f"{self.base_url}/api/status", 
                                  headers=self.get_headers(), timeout=5)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Server: {data.get('server', 'N/A')} | Uptime: {data.get('uptime', 'N/A')}"
            else:
                details = f"HTTP {response.status_code}"
            
            self.log_test("Status Endpoint", success, details)
            return success
            
        except Exception as e:
            self.log_test("Status Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_jobs_endpoint(self):
        """Test 5: Endpoint jobs"""
        try:
            response = requests.get(f"{self.base_url}/api/jobs", 
                                  headers=self.get_headers(), timeout=5)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                jobs_count = len(data.get('jobs', []))
                details = f"Jobs trouvés: {jobs_count}"
            else:
                details = f"HTTP {response.status_code}"
            
            self.log_test("Jobs Endpoint", success, details)
            return success
            
        except Exception as e:
            self.log_test("Jobs Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_demo_compression(self):
        """Test 6: Compression demo"""
        try:
            form_data = {
                'resolution': 'HD',
                'duration': '2.0'
            }
            
            response = requests.post(f"{self.base_url}/api/demo", 
                                   data=form_data,
                                   headers={'Authorization': f'Bearer {self.token}'},
                                   timeout=10)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                job_id = data.get('job_id')
                details = f"Job créé: {job_id}"
            else:
                details = f"HTTP {response.status_code}"
            
            self.log_test("Demo Compression", success, details)
            return success, job_id if success else None
            
        except Exception as e:
            self.log_test("Demo Compression", False, f"Exception: {str(e)}")
            return False, None
    
    def test_file_compression(self):
        """Test 7: Compression de fichier"""
        try:
            # Créer un fichier de test
            test_file = self.create_test_file("HCV PRO test content for compression")
            
            with open(test_file, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                data = {'quality': 'high'}
                
                response = requests.post(f"{self.base_url}/api/android-boost", 
                                       files=files,
                                       data=data,
                                       headers={'Authorization': f'Bearer {self.token}'},
                                       timeout=10)
            
            success = response.status_code == 200
            if success:
                result = response.json()
                job_id = result.get('job_id')
                details = f"Job créé: {job_id}"
            else:
                details = f"HTTP {response.status_code}"
            
            self.log_test("File Compression (Android Boost)", success, details)
            return success, job_id if success else None
            
        except Exception as e:
            self.log_test("File Compression (Android Boost)", False, f"Exception: {str(e)}")
            return False, None
    
    def test_job_status(self, job_id):
        """Test 8: Statut d'un job"""
        if not job_id:
            self.log_test("Job Status", False, "Aucun job_id à tester")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/api/job-status/{job_id}", 
                                  headers=self.get_headers(), timeout=5)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                status = data.get('status', 'unknown')
                progress = data.get('progress', 0)
                details = f"Status: {status} | Progress: {progress}%"
            else:
                details = f"HTTP {response.status_code}"
            
            self.log_test("Job Status", success, details)
            return success
            
        except Exception as e:
            self.log_test("Job Status", False, f"Exception: {str(e)}")
            return False
    
    def test_cancel_job(self, job_id):
        """Test 9: Annulation d'un job"""
        if not job_id:
            self.log_test("Cancel Job", False, "Aucun job_id à tester")
            return False
        
        try:
            response = requests.post(f"{self.base_url}/api/job/{job_id}/cancel", 
                                   headers=self.get_headers(), timeout=5)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                message = data.get('message', 'OK')
                details = f"Message: {message}"
            else:
                details = f"HTTP {response.status_code}"
            
            self.log_test("Cancel Job", success, details)
            return success
            
        except Exception as e:
            self.log_test("Cancel Job", False, f"Exception: {str(e)}")
            return False
    
    def test_download_job(self, job_id):
        """Test 10: Téléchargement d'un job"""
        if not job_id:
            self.log_test("Download Job", False, "Aucun job_id à tester")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/api/download/{job_id}", 
                                  headers=self.get_headers(), timeout=5)
            
            success = response.status_code == 200
            if success:
                content_size = len(response.content)
                details = f"Taille: {content_size} bytes"
            else:
                details = f"HTTP {response.status_code}"
            
            self.log_test("Download Job", success, details)
            return success
            
        except Exception as e:
            self.log_test("Download Job", False, f"Exception: {str(e)}")
            return False
    
    def test_history_endpoint(self):
        """Test 11: Endpoint history"""
        try:
            response = requests.get(f"{self.base_url}/api/history", 
                                  headers=self.get_headers(), timeout=5)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                history_count = len(data.get('history', []))
                details = f"Entrées: {history_count}"
            else:
                details = f"HTTP {response.status_code}"
            
            self.log_test("History Endpoint", success, details)
            return success
            
        except Exception as e:
            self.log_test("History Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_unauthorized_access(self):
        """Test 12: Accès non autorisé"""
        try:
            response = requests.get(f"{self.base_url}/api/status", timeout=5)
            
            success = response.status_code == 401
            details = f"Status: {response.status_code}"
            
            self.log_test("Unauthorized Access", success, details)
            return success
            
        except Exception as e:
            self.log_test("Unauthorized Access", False, f"Exception: {str(e)}")
            return False
    
    def test_rate_limiting(self):
        """Test 13: Rate limiting"""
        try:
            # Faire plusieurs requêtes rapidement
            success_count = 0
            for i in range(5):
                response = requests.get(f"{self.base_url}/api/status", 
                                      headers=self.get_headers(), timeout=2)
                if response.status_code == 200:
                    success_count += 1
                time.sleep(0.1)
            
            # Le rate limiting ne devrait pas bloquer 5 requêtes
            success = success_count >= 3  # Au moins 3 devraient passer
            details = f"Requêtes réussies: {success_count}/5"
            
            self.log_test("Rate Limiting", success, details)
            return success
            
        except Exception as e:
            self.log_test("Rate Limiting", False, f"Exception: {str(e)}")
            return False
    
    def cleanup(self):
        """Nettoyer les fichiers temporaires"""
        for temp_file in self.temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🧪 DÉMARRAGE DES TESTS COMPLETS HCV PRO ENTERPRISE AWS")
        print("=" * 60)
        
        # Tests de base
        if not self.test_server_health():
            print("\n❌ Serveur inaccessible. Arrêt des tests.")
            return False
        
        # Tests d'authentification
        if not self.test_authentication():
            print("\n❌ Authentification échouée. Arrêt des tests.")
            return False
        
        self.test_authentication_invalid()
        
        # Tests des endpoints
        self.test_status_endpoint()
        self.test_jobs_endpoint()
        self.test_history_endpoint()
        self.test_unauthorized_access()
        
        # Tests de compression
        demo_success, demo_job_id = self.test_demo_compression()
        file_success, file_job_id = self.test_file_compression()
        
        # Attendre un peu pour que les jobs progressent
        time.sleep(2)
        
        # Tests de gestion des jobs
        if demo_job_id:
            self.test_job_status(demo_job_id)
            self.test_cancel_job(demo_job_id)
        
        if file_job_id:
            self.test_job_status(file_job_id)
            # Attendre que le job se termine
            time.sleep(3)
            self.test_download_job(file_job_id)
        
        # Tests avancés
        self.test_rate_limiting()
        
        # Nettoyer
        self.cleanup()
        
        # Résumé
        self.print_summary()
        return True
    
    def print_summary(self):
        """Afficher le résumé des tests"""
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📈 Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Tests échoués:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
        
        print("\n🎯 Conclusion:")
        if failed_tests == 0:
            print("✅ Tous les tests passés! L'application fonctionne parfaitement.")
        elif failed_tests <= 2:
            print("⚠️ Quelques problèmes mineurs. L'application est globalement fonctionnelle.")
        else:
            print("❌ Plusieurs problèmes détectés. Des corrections sont nécessaires.")

def main():
    """Point d'entrée principal"""
    tester = HCVEnterpriseTester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrompus par l'utilisateur.")
        tester.cleanup()
        return 1
    except Exception as e:
        print(f"\n💥 Erreur inattendue: {e}")
        tester.cleanup()
        return 1

if __name__ == "__main__":
    sys.exit(main())
