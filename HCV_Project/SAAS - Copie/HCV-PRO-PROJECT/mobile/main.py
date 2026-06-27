#!/usr/bin/env python3
"""
HCV PRO - Main Entry Point
Point d'entrée principal du système complet
"""

import asyncio
import time
import threading

# Processeur Harmonique Universel
from harmonic_constants import get_harmonic_processor

from bridge_server import HCVBridgeServer
from file_watcher import HCVFileWatcher
from openclaw_integration import OpenClawService
from upscaler_harmonic import start_upscaler_service, stop_upscaler_service, upscale_image
from gemma_orchestrator import gemma_init, gemma_stop, gemma_decide
from gemma_multimodal import gemma_multimodal_init, gemma_multimodal_stop, gemma_analyze
from audio_tunnel import audio_tunnel_init, audio_tunnel_stop
from virtual_display_layer import virtual_display_init, virtual_display_stop

class HCVProService:
    """
    Service principal HCV PRO
    """
    
    def __init__(self):
        self.running = False
        self.services = []
    
    async def start(self):
        """Démarre tous les services dans l'ordre correct"""
        
        print("🚀 HCV PRO Démarrage...")
        print("=" * 60)
        
        # 1. Démarre le bridge serveur UI EN PREMIER
        self.bridge = HCVBridgeServer()
        await self.bridge.start()
        print("✅ Bridge serveur UI démarré")
        print("👉 Interface: http://127.0.0.1:7890/ui/HarmonicPhone.html")
        
        # 2. Démarre l'orchestrateur Gemma 4
        try:
            gemma_init()
            print("✅ Gemma 4 Orchestrateur démarré")
        except Exception as e:
            print(f"ℹ️ Gemma 4 non disponible: {e}")
        
        # 3. Démarre le module multimodal
        try:
            gemma_multimodal_init()
            print("✅ Gemma 4 Multimodal démarré")
        except Exception as e:
            print(f"ℹ️ Gemma Multimodal non disponible: {e}")
        
        # 4. Initialise le processeur harmonique universel
        try:
            self.harmonic = get_harmonic_processor()
            print("✅ Processeur Harmonique Universel initialisé")
        except Exception as e:
            print(f"ℹ️ Processeur harmonique non disponible: {e}")
        
        # 5. Démarre l'upscaler harmonique PI/PHI
        try:
            start_upscaler_service()
            print("✅ Upscaler Harmonique PI/PHI 4K démarré")
        except Exception as e:
            print(f"ℹ️ Upscaler non disponible: {e}")
        
        # 6. Démarre OpenClaw VFS hook
        try:
            self.openclaw = OpenClawService()
            self.openclaw.start()
            print("✅ OpenClaw VFS Interception activée")
        except Exception:
            print("ℹ️ OpenClaw VFS disponible uniquement sur Linux/Android - Mode simulation activé")
        
        # 7. Démarre la surveillance fichiers
        try:
            self.watcher = HCVFileWatcher()
            self.watcher.start(self._on_new_file)
            print("✅ Surveillance galerie activée")
        except Exception as e:
            print(f"ℹ️ Surveillance fichiers non disponible: {e}")
        
        # 8. Démarre le Tunnel Audio HD
        try:
            audio_tunnel_init()
            print("✅ Tunnel Audio HD activé")
        except Exception as e:
            print(f"ℹ️ Audio tunnel non disponible: {e}")
        
        # 9. Démarre la couche d'affichage virtuelle 16K
        try:
            virtual_display_init()
            print("✅ Ecran virtuel 16K OLED activé")
        except Exception as e:
            print(f"ℹ️ Ecran virtuel non disponible: {e}")
        
        gemma_multimodal_stop()
        gemma_stop()
        
        self.running = False
        print("✅ Tous les services arrêtés")
    
    def _on_new_file(self, path: str):
        """Appelé automatiquement quand un nouveau fichier est détecté"""
        
        # 1. Gemma décide quoi faire avec ce fichier
        decision = gemma_decide(path)
        
        # 2. Upscale automatique si décidé
        if decision['should_upscale']:
            upscale_image(path)
        
        # 3. Analyse sémantique multimodale
        gemma_analyze(path)
        
        # 4. L'interface se met à jour automatiquement en 60fps


if __name__ == "__main__":
    
    service = HCVProService()
    
    try:
        asyncio.run(service.start())
        
        # Main loop
        while True:
            time.sleep(3600)
            
    except KeyboardInterrupt:
        service.stop()
