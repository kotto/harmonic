#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de démarrage automatique du serveur HCS V2
Gestion automatique des ports et configuration du frontend
"""

import os
import sys
import time
import socket
import subprocess
import requests
import threading
from pathlib import Path

# Configuration
DEFAULT_PORT = 8009
ALTERNATIVE_PORT = 8010
FRONTEND_FILE = "frontend/quantum_upscaler.html"
SERVER_FILE = "api/server_simple.py"

class PortManager:
    """Gestionnaire de ports automatique"""
    
    def __init__(self):
        self.default_port = DEFAULT_PORT
        self.alternative_port = ALTERNATIVE_PORT
        self.current_port = None
        
    def is_port_available(self, port):
        """Vérifie si un port est disponible"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                return result != 0
        except:
            return False
    
    def find_available_port(self):
        """Trouve un port disponible"""
        if self.is_port_available(self.default_port):
            self.current_port = self.default_port
            print(f"✅ Port {self.default_port} disponible")
        elif self.is_port_available(self.alternative_port):
            self.current_port = self.alternative_port
            print(f"⚠️ Port {self.default_port} occupé, utilisation du port {self.alternative_port}")
        else:
            # Trouver un port libre automatiquement
            for port in range(8020, 8100):
                if self.is_port_available(port):
                    self.current_port = port
                    print(f"🔍 Port trouvé automatiquement: {port}")
                    break
            else:
                raise Exception("❌ Aucun port disponible trouvé")
        
        return self.current_port
    
    def kill_processes_on_port(self, port):
        """Tue les processus utilisant un port spécifique"""
        try:
            if sys.platform == "win32":
                # Windows
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
                                print(f"🔪 Processus {pid} tué sur port {port}")
            else:
                # Linux/Mac
                subprocess.run(f'lsof -ti:{port} | xargs kill -9', shell=True)
                print(f"🔪 Processus tués sur port {port}")
                
        except Exception as e:
            print(f"⚠️ Erreur en tuant les processus: {e}")

class FrontendUpdater:
    """Gestionnaire de mise à jour du frontend"""
    
    def __init__(self, frontend_file):
        self.frontend_file = frontend_file
        
    def update_frontend_urls(self, port):
        """Met à jour les URLs dans le frontend"""
        try:
            if not os.path.exists(self.frontend_file):
                print(f"⚠️ Fichier frontend non trouvé: {self.frontend_file}")
                return False
            
            # Lire le fichier
            with open(self.frontend_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remplacer toutes les occurrences de localhost:8009 ou localhost:8010
            old_urls = [
                'http://localhost:8009',
                'http://localhost:8010'
            ]
            new_url = f'http://localhost:{port}'
            
            updated = False
            for old_url in old_urls:
                if old_url in content:
                    content = content.replace(old_url, new_url)
                    updated = True
                    print(f"🔄 URL mise à jour: {old_url} → {new_url}")
            
            if updated:
                # Écrire le fichier mis à jour
                with open(self.frontend_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Frontend mis à jour pour le port {port}")
                return True
            else:
                print(f"ℹ️ Aucune URL à mettre à jour dans le frontend")
                return True
                
        except Exception as e:
            print(f"❌ Erreur mise à jour frontend: {e}")
            return False

class ServerManager:
    """Gestionnaire du serveur"""
    
    def __init__(self, server_file, port):
        self.server_file = server_file
        self.port = port
        self.process = None
        
    def start_server(self):
        """Démarre le serveur"""
        try:
            if not os.path.exists(self.server_file):
                print(f"❌ Fichier serveur non trouvé: {self.server_file}")
                return False
            
            # Mettre à jour le port dans le serveur si nécessaire
            self.update_server_port()
            
            # Démarrer le serveur
            print(f"🚀 Démarrage du serveur sur le port {self.port}...")
            
            # Utiliser subprocess pour démarrer le serveur
            self.process = subprocess.Popen(
                [sys.executable, self.server_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Lire la sortie en arrière-plan
            def read_output():
                for line in iter(self.process.stdout.readline, ''):
                    if line.strip():
                        print(f"🖥️  {line.strip()}")
            
            output_thread = threading.Thread(target=read_output, daemon=True)
            output_thread.start()
            
            # Attendre que le serveur démarre
            time.sleep(3)
            
            # Vérifier que le serveur fonctionne
            if self.is_server_running():
                print(f"✅ Serveur démarré avec succès sur http://localhost:{self.port}")
                return True
            else:
                print(f"❌ Le serveur ne répond pas sur http://localhost:{self.port}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur démarrage serveur: {e}")
            return False
    
    def update_server_port(self):
        """Met à jour le port dans le fichier serveur"""
        try:
            with open(self.server_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remplacer le port dans le fichier serveur
            if 'port=8010' in content and self.port != 8010:
                content = content.replace('port=8010', f'port={self.port}')
                with open(self.server_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"🔄 Port serveur mis à jour: {self.port}")
                
        except Exception as e:
            print(f"⚠️ Erreur mise à jour port serveur: {e}")
    
    def is_server_running(self):
        """Vérifie si le serveur fonctionne"""
        try:
            response = requests.get(f'http://localhost:{self.port}/', timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def stop_server(self):
        """Arrête le serveur"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            print("🛑 Serveur arrêté")

class AutoStarter:
    """Classe principale de démarrage automatique"""
    
    def __init__(self):
        self.port_manager = PortManager()
        self.frontend_updater = FrontendUpdater(FRONTEND_FILE)
        self.server_manager = None
        
    def start(self, kill_existing=False):
        """Démarre le système complet"""
        print("🌊 HCS V2 - Démarrage Automatique")
        print("=" * 50)
        
        # Tuer les processus existants si demandé
        if kill_existing:
            print("🔪 Arrêt des processus existants...")
            self.port_manager.kill_processes_on_port(DEFAULT_PORT)
            self.port_manager.kill_processes_on_port(ALTERNATIVE_PORT)
            time.sleep(2)
        
        # Trouver un port disponible
        port = self.port_manager.find_available_port()
        
        # Mettre à jour le frontend
        if not self.frontend_updater.update_frontend_urls(port):
            print("❌ Échec mise à jour frontend")
            return False
        
        # Démarrer le serveur
        self.server_manager = ServerManager(SERVER_FILE, port)
        if not self.server_manager.start_server():
            print("❌ Échec démarrage serveur")
            return False
        
        # Afficher les informations
        self.show_info(port)
        
        return True
    
    def show_info(self, port):
        """Affiche les informations de connexion"""
        print("\n" + "=" * 50)
        print("🎯 INFORMATIONS DE CONNEXION")
        print("=" * 50)
        print(f"🌐 URL du serveur: http://localhost:{port}")
        print(f"📁 Frontend: frontend/quantum_upscaler.html")
        print(f"🎨 Approche: Référence Chromatique (votre idée !)")
        print(f"🔧 Endpoint: /api/v2/upscale/video-reference")
        print("=" * 50)
        print("✅ Système prêt à utiliser !")
        print("🚀 Testez votre vidéo maintenant !")
        print("=" * 50)
    
    def stop(self):
        """Arrête le système"""
        if self.server_manager:
            self.server_manager.stop_server()

def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Démarrage automatique HCS V2')
    parser.add_argument('--kill', action='store_true', help='Tuer les processus existants')
    parser.add_argument('--port', type=int, help='Port spécifique à utiliser')
    
    args = parser.parse_args()
    
    starter = AutoStarter()
    
    try:
        if args.port:
            # Utiliser un port spécifique
            starter.port_manager.current_port = args.port
            if not starter.port_manager.is_port_available(args.port):
                print(f"❌ Port {args.port} non disponible")
                return
            
            if not starter.frontend_updater.update_frontend_urls(args.port):
                print("❌ Échec mise à jour frontend")
                return
            
            starter.server_manager = ServerManager(SERVER_FILE, args.port)
            if starter.server_manager.start_server():
                starter.show_info(args.port)
                
                # Garder le script en cours d'exécution
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n🛑 Arrêt demandé...")
                    starter.stop()
            else:
                print("❌ Échec démarrage serveur")
        else:
            # Mode automatique
            if starter.start(kill_existing=args.kill):
                try:
                    # Garder le script en cours d'exécution
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n🛑 Arrêt demandé...")
                    starter.stop()
            else:
                print("❌ Échec démarrage système")
    
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé...")
        starter.stop()
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()
