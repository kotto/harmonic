"""
HCV PRO File Watcher - Phase 2
Détection automatique nouveaux fichiers dans DCIM/Camera
"""

import os
import time
from pathlib import Path
from typing import Callable, List
import threading

class HCVFileWatcher:
    """Surveille les nouveaux fichiers dans la galerie photo"""
    
    def __init__(self, watch_paths: List[str] = None):
        self.watch_paths = watch_paths or [
            '/sdcard/DCIM/Camera',
            '/sdcard/Pictures',
            '/sdcard/DCIM'
        ]
        self.running = False
        self.known_files = set()
        self.callback: Callable[[str], None] = None
        self.thread: threading.Thread = None
        
        # Initialiser la liste des fichiers connus
        self._scan_existing_files()
    
    def _scan_existing_files(self) -> None:
        """Scan initial des fichiers existants"""
        for path in self.watch_paths:
            p = Path(path)
            if not p.exists():
                continue
            
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.mp4', '*.mov']:
                for f in p.rglob(ext):
                    self.known_files.add(f.resolve())
    
    def start(self, new_file_callback: Callable[[str], None]) -> None:
        """Démarre la surveillance en arrière plan"""
        self.callback = new_file_callback
        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
    
    def stop(self) -> None:
        """Arrête la surveillance"""
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _watch_loop(self) -> None:
        """Boucle principale de surveillance"""
        while self.running:
            new_files = []
            
            for path in self.watch_paths:
                p = Path(path)
                if not p.exists():
                    continue
                
                for ext in ['*.jpg', '*.jpeg', '*.png', '*.mp4', '*.mov']:
                    for f in p.rglob(ext):
                        abs_path = f.resolve()
                        if abs_path not in self.known_files:
                            # Attendre que le fichier soit complètement écrit
                            try:
                                size1 = f.stat().st_size
                                time.sleep(0.5)
                                size2 = f.stat().st_size
                                
                                if size1 == size2 and size1 > 0:
                                    new_files.append(abs_path)
                                    self.known_files.add(abs_path)
                            except:
                                pass
            
            # Notifier les nouveaux fichiers
            for f in new_files:
                if self.callback:
                    try:
                        self.callback(str(f))
                    except:
                        pass
            
            time.sleep(2.0)
    
    def get_stats(self) -> dict:
        """Retourne les statistiques de surveillance"""
        return {
            'known_files': len(self.known_files),
            'watching_paths': self.watch_paths,
            'running': self.running
        }


if __name__ == "__main__":
    # Test du watcher
    print("✅ HCV File Watcher Test")
    
    def on_new_file(path: str):
        print(f"✅ Nouveau fichier détecté: {path}")
    
    watcher = HCVFileWatcher()
    watcher.start(on_new_file)
    
    try:
        while True:
            stats = watcher.get_stats()
            print(f"\r✅ Fichiers connus: {stats['known_files']}", end='')
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n✅ Arrêt...")
        watcher.stop()
