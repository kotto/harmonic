#!/usr/bin/env python3
"""
HCV PRO - Main Entry Point
Point d'entrée principal du système complet
Démarre tous les services
"""

import asyncio
import time
import threading

from bridge_server import HCVBridgeServer
from file_watcher import HCVFileWatcher
from openclaw_integration import OpenClawService
from upscaler import start_upscaler_service, stop_upscaler_service, upscale_image
from gemma_orchestrator import gemma_init, gemma_stop, gemma_decide
from gemma_multimodal import gemma_multimodal_init, gemma_multimodal_stop, gemma_analyze
from transactional_reorganizer import reorganizer_scan

class HCVProService:
    """
    Service principal HCV PRO
    Assemble et démarre tous les modules
    """
    
    def __init__(self):
        self.running = False
        self.services = []
    
    async def start(self):
        """Démarre tous les services dans l'ordre correct"""
        
        print("🚀 HCV PRO Démarrage...")
        print("=" * 60)
        
        # 1. Démarre l'orchestrateur Gemma 4
        gemma_init()
        print("✅ Gemma 4 Orchestrateur démarré")
        
        # 2. Démarre le module multimodal
        gemma_multimodal_init()
        print("✅ Gemma 4 Multimodal démarré")
        
        # 3. Démarre l'upscaler automatique
        start_upscaler_service()
        print("✅ Upscaler Lanczos 4K démarré")
        
        # 4. Démarre OpenClaw VFS hook
        self.openclaw = OpenClawService()
        self.openclaw.start()
        print("✅ OpenClaw VFS Interception activée")
        
        # 5. Démarre la surveillance fichiers
        self.watcher = HCVFileWatcher()
        self.watcher.start(self._on_new_file)
        print("✅ Surveillance galerie activée")
        
        # 6. Démarre le bridge serveur UI
        self.bridge = HCVBridgeServer()
        await self.bridge.start()
        print("✅ Bridge serveur UI démarré")
        
        self.running = True
        
        print("\n✅ HCV PRO est maintenant actif")
        print("✅ Tous les modules sont opérationnels")
        print("✅ Tout fonctionne en arrière plan")
        print("✅ Aucune donnée ne sort du téléphone")
        print("\n👉 Interface: http://127.0.0.1:7890/ui/HarmonicPhone.html")
    
    def stop(self):
        """Arrête tous les services proprement"""
        
        print("\n🛑 Arrêt HCV PRO...")
        
        self.bridge.stop()
        self.watcher.stop()
        self.openclaw.stop()
        stop_upscaler_service()
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
