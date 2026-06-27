#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HCS V2 - Script de Démarrage Automatique pour IA Générative Hybride SDXL + HCS
Gestion complète des ports et services
"""

import os
import sys
import time
import socket
import subprocess
import threading
from pathlib import Path

# Configuration
HYBRID_PORT = 8011
VIDEO_PORT = 8009
FRONTEND_FILE = "frontend/hybrid_sdxl_interface.html"
HYBRID_SERVER_FILE = "api/hybrid_sdxl_server.py"

class PortManager:
    """Gestionnaire de ports pour services multiples"""
    
    def __init__(self):
        self.hybrid_port = HYBRID_PORT
        self.video_port = VIDEO_PORT
        
    def is_port_available(self, port):
        """Vérifie si un port est disponible"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                return result != 0
        except:
            return False
    
    def check_all_ports(self):
        """Vérifie tous les ports nécessaires"""
        ports_status = {}
        
        ports_status['hybrid'] = {
            'port': self.hybrid_port,
            'available': self.is_port_available(self.hybrid_port),
            'service': 'IA Générative Hybride SDXL + HCS'
        }
        
        ports_status['video'] = {
            'port': self.video_port,
            'available': self.is_port_available(self.video_port),
            'service': 'Video Upscaling Harmonique'
        }
        
        return ports_status

class HybridServiceManager:
    """Gestionnaire des services HCS"""
    
    def __init__(self):
        self.processes = {}
        self.port_manager = PortManager()
        self.video_port = VIDEO_PORT
        self.hybrid_port = HYBRID_PORT
        
    def start_all_services(self):
        """Démarre tous les services HCS"""
        print("🌊 HCS V2 - Démarrage Complet des Services")
        print("=" * 60)
        
        # Vérification des ports
        ports_status = self.port_manager.check_all_ports()
        
        print("🔍 Vérification des ports:")
        all_available = True
        for service, status in ports_status.items():
            available = status['available']
            port = status['port']
            name = status['service']
            
            status_icon = "✅" if available else "❌"
            print(f"   {status_icon} {name} (port {port}): {'Disponible' if available else 'Occupé'}")
            
            if not available:
                all_available = False
        
        if not all_available:
            print("\n⚠️ Certains ports sont occupés. Tentative de libération...")
            self.free_ports()
        
        print("\n🚀 Démarrage des services:")
        
        # Démarrage du serveur vidéo (si nécessaire)
        if self.port_manager.is_port_available(self.video_port):
            self.start_video_service()
        else:
            print("ℹ️ Serveur vidéo déjà en cours d'exécution")
        
        # Démarrage du serveur hybride
        self.start_hybrid_service()
        
        # Attendre démarrage complet
        time.sleep(3)
        
        # Lancement des tests si demandé
        if '--test' in sys.argv:
            print("\n🧪 Lancement des tests automatiques...")
            time.sleep(2)
            
            try:
                import test_hybrid_sdxl
                tester = test_hybrid_sdxl.HybridSDXLTester()
                tester.run_all_tests()
            except Exception as e:
                print(f"❌ Erreur tests: {e}")
        
        # Affichage des informations
        self.show_service_info()
        
        return True
    
    def free_ports(self):
        """Libère les ports occupés"""
        try:
            if sys.platform == "win32":
                # Windows
                for port in [self.video_port, self.hybrid_port]:
                    result = subprocess.run(
                        f'netstat -ano | findstr :{port}',
                        shell=True,
                        capture_output=True,
                        text=True
                    )
                    
                    if result.stdout:
                        lines = result.stdout.strip().split('\n')
                        for line in lines:
                            if f':{port}' in line and 'LISTENING' in line:
                                parts = line.split()
                                if len(parts) >= 5:
                                    pid = parts[-1]
                                    subprocess.run(f'taskkill /F /PID {pid}', shell=True)
                                    print(f"🔪 Processus {pid} arrêté (port {port})")
            else:
                # Linux/Mac
                for port in [self.video_port, self.hybrid_port]:
                    subprocess.run(f'lsof -ti:{port} | xargs kill -9', shell=True)
                    print(f"🔪 Processus arrêtés (port {port})")
                    
        except Exception as e:
            print(f"⚠️ Erreur libération ports: {e}")
    
    def start_video_service(self):
        """Démarre le service vidéo"""
        try:
            print("   🎬 Démarrage du service vidéo...")
            
            # Vérification si le fichier existe
            if not os.path.exists("api/server_simple.py"):
                print("   ⚠️ Fichier serveur vidéo non trouvé")
                return False
            
            # Démarrage en arrière-plan
            process = subprocess.Popen([
                sys.executable, "api/server_simple.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            
            self.processes['video'] = process
            
            # Attendre démarrage
            time.sleep(3)
            
            if self.port_manager.is_port_available(self.video_port):
                print("   ❌ Échec démarrage service vidéo")
                return False
            else:
                print("   ✅ Service vidéo démarré")
                return True
                
        except Exception as e:
            print(f"   ❌ Erreur démarrage vidéo: {e}")
            return False
    
    def start_hybrid_service(self):
        """Démarre le service hybride"""
        try:
            print("   🎨 Démarrage du service hybride SDXL + HCS...")
            
            # Vérification si le fichier existe
            if not os.path.exists(HYBRID_SERVER_FILE):
                print(f"   ❌ Fichier serveur hybride non trouvé: {HYBRID_SERVER_FILE}")
                return False
            
            # Démarrage en arrière-plan
            process = subprocess.Popen([
                sys.executable, HYBRID_SERVER_FILE
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            
            self.processes['hybrid'] = process
            
            # Attendre démarrage
            time.sleep(5)
            
            if self.port_manager.is_port_available(self.hybrid_port):
                print("   ❌ Échec démarrage service hybride")
                return False
            else:
                print("   ✅ Service hybride démarré")
                return True
                
        except Exception as e:
            print(f"   ❌ Erreur démarrage hybride: {e}")
            return False
    
    def show_service_info(self):
        """Affiche les informations des services"""
        print("\n" + "=" * 60)
        print("🌊 HCS V2 - SERVICES ACTIFS")
        print("=" * 60)
        
        print("🎬 Service Vidéo (Upscaling Harmonique):")
        print(f"   🌐 URL: http://localhost:{self.video_port}")
        print(f"   📁 Frontend: frontend/quantum_upscaler.html")
        print(f"   🎯 Endpoint: /api/v2/upscale/video-reference")
        print(f"   🌊 Approche: Référence Chromatique")
        
        print("\n🎨 Service Hybride (IA Générative SDXL + HCS):")
        print(f"   🌐 URL: http://localhost:{self.hybrid_port}")
        print(f"   📁 Frontend: frontend/hybrid_sdxl_interface.html")
        print(f"   🎯 Endpoint: /api/v2/hybrid/generate")
        print(f"   🌊 Approche: SDXL + Théorie Harmonique")
        
        print("\n🚀 CAPACITÉS COMPLÈTES:")
        print("   📸 Video Upscaling 4K→8K avec référence chromatique")
        print("   🎨 Text-to-Image avec principes harmoniques")
        print("   🖼️ Image-to-Image avec optimisation HCS")
        print("   🌊 Génération 8K native avec constantes φ²")
        print("   🎯 Profils chromatiques personnalisés")
        print("   ⚡ Métriques harmoniques avancées")
        
        print("\n🌊 UTILISATION:")
        print("   1. Video: http://localhost:8009/frontend/quantum_upscaler.html")
        print("   2. Hybrid: http://localhost:8011/frontend/hybrid_sdxl_interface.html")
        print("   3. Tests: python test_hybrid_sdxl.py")
        
        print("\n🏆 VOTRE RÉVOLUTION EST PRÊTE !")
        print("   🌊 IA Générative + Théorie Harmonique = Innovation Unique")
        print("   🎨 SDXL + HCS = Qualité Inégalée")
        print("   🚀 8K Natif + Référence Chromatique = Révolution")
        
        print("=" * 60)
    
    def stop_all_services(self):
        """Arrête tous les services"""
        print("\n🛑 Arrêt des services HCS...")
        
        for service, process in self.processes.items():
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                    print(f"   ✅ Service {service} arrêté")
                except subprocess.TimeoutExpired:
                    process.kill()
                    print(f"   🔪 Service {service} forcé")
        
        print("🛑 Tous les services arrêtés")

def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Démarrage HCS V2 - Services Complets')
    parser.add_argument('--stop', action='store_true', help='Arrêter tous les services')
    parser.add_argument('--test', action='store_true', help='Lancer les tests après démarrage')
    
    args = parser.parse_args()
    
    manager = HybridServiceManager()
    
    try:
        if args.stop:
            manager.stop_all_services()
        else:
            # Démarrage des services
            if manager.start_all_services():
                print("\n🌊 Services HCS V2 démarrés avec succès !")
                
                # Garder les services en cours d'exécution
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n🛑 Arrêt demandé par l'utilisateur")
                    manager.stop_all_services()
            else:
                print("❌ Échec démarrage des services")
    
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé")
        manager.stop_all_services()
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()
