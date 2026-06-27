"""
Gestionnaire de sauvegarde local pour Harmonic AI
Sauvegarde et restauration des résultats de tests
"""

import shutil
import os
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
import hashlib

class BackupManager:
    """
    Gestionnaire de sauvegarde local avec versioning
    """
    
    def __init__(self, backup_dir: str = "backups", max_backups: int = 10):
        """
        Initialiser le gestionnaire de sauvegarde
        
        Args:
            backup_dir: Répertoire de sauvegarde
            max_backups: Nombre maximum de sauvegardes à conserver
        """
        self.backup_dir = backup_dir
        self.max_backups = max_backups
        
        # Créer le répertoire de sauvegarde
        os.makedirs(backup_dir, exist_ok=True)
        
        # Fichier de métadonnées des sauvegardes
        self.metadata_file = os.path.join(backup_dir, "backup_metadata.json")
        
        print(f"💾 Gestionnaire de sauvegarde initialisé")
        print(f"   Répertoire: {backup_dir}")
        print(f"   Sauvegardes max: {max_backups}")
    
    def create_backup(self, source_file: str, description: str = "") -> Optional[str]:
        """
        Créer une sauvegarde d'un fichier
        
        Args:
            source_file: Chemin du fichier à sauvegarder
            description: Description de la sauvegarde
            
        Returns:
            Chemin du fichier de sauvegarde ou None en cas d'erreur
        """
        if not os.path.exists(source_file):
            print(f"⚠️ Fichier source non trouvé: {source_file}")
            return None
        
        try:
            # Générer un nom de fichier unique avec horodatage
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            file_name = os.path.basename(source_file)
            backup_name = f"{file_name}_{timestamp}"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Copier le fichier
            shutil.copy2(source_file, backup_path)
            
            # Calculer le hash MD5 pour vérification
            file_hash = self.calculate_file_hash(source_file)
            
            # Enregistrer les métadonnées
            metadata = self.load_metadata()
            
            backup_info = {
                "name": backup_name,
                "source": source_file,
                "backup_path": backup_path,
                "timestamp": timestamp,
                "datetime": datetime.now().isoformat(),
                "file_size": os.path.getsize(source_file),
                "file_hash": file_hash,
                "description": description,
                "backup_type": "manual"
            }
            
            metadata["backups"].append(backup_info)
            
            # Limiter le nombre de sauvegardes
            if len(metadata["backups"]) > self.max_backups:
                # Supprimer les sauvegardes les plus anciennes
                metadata["backups"] = metadata["backups"][-self.max_backups:]
            
            # Sauvegarder les métadonnées
            self.save_metadata(metadata)
            
            print(f"✅ Sauvegarde créée: {backup_name}")
            print(f"   Source: {source_file}")
            print(f"   Taille: {backup_info['file_size']} bytes")
            print(f"   Hash: {file_hash[:16]}...")
            
            return backup_path
            
        except Exception as e:
            print(f"❌ Erreur création sauvegarde: {e}")
            return None
    
    def create_auto_backup(self, source_file: str) -> Optional[str]:
        """
        Créer une sauvegarde automatique
        
        Args:
            source_file: Chemin du fichier à sauvegarder
            
        Returns:
            Chemin du fichier de sauvegarde ou None
        """
        description = f"Auto-backup {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return self.create_backup(source_file, description)
    
    def restore_backup(self, backup_name: str, target_file: str) -> bool:
        """
        Restaurer une sauvegarde
        
        Args:
            backup_name: Nom de la sauvegarde à restaurer
            target_file: Chemin du fichier de destination
            
        Returns:
            True si la restauration a réussi, False sinon
        """
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        if not os.path.exists(backup_path):
            print(f"⚠️ Sauvegarde non trouvée: {backup_name}")
            return False
        
        try:
            # Copier la sauvegarde vers la destination
            shutil.copy2(backup_path, target_file)
            
            # Vérifier le hash
            original_hash = self.get_backup_hash(backup_name)
            restored_hash = self.calculate_file_hash(target_file)
            
            if original_hash == restored_hash:
                print(f"✅ Restauration réussie: {backup_name} -> {target_file}")
                
                # Enregistrer la restauration dans les métadonnées
                metadata = self.load_metadata()
                
                restore_info = {
                    "backup_name": backup_name,
                    "target_file": target_file,
                    "timestamp": datetime.now().isoformat(),
                    "hash_match": True,
                    "original_hash": original_hash,
                    "restored_hash": restored_hash
                }
                
                metadata["restorations"].append(restore_info)
                self.save_metadata(metadata)
                
                return True
            else:
                print(f"❌ Hash mismatch après restauration")
                print(f"   Original: {original_hash}")
                print(f"   Restored: {restored_hash}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur restauration: {e}")
            return False
    
    def restore_latest(self, target_file: str) -> bool:
        """
        Restaurer la dernière sauvegarde
        
        Args:
            target_file: Chemin du fichier de destination
            
        Returns:
            True si la restauration a réussi, False sinon
        """
        latest_backup = self.get_latest_backup()
        
        if latest_backup:
            return self.restore_backup(latest_backup["name"], target_file)
        else:
            print("⚠️ Aucune sauvegarde disponible")
            return False
    
    def get_latest_backup(self) -> Optional[Dict]:
        """
        Obtenir les informations de la dernière sauvegarde
        
        Returns:
            Dictionnaire avec les informations de la sauvegarde ou None
        """
        metadata = self.load_metadata()
        
        if metadata["backups"]:
            # Retourner la sauvegarde la plus récente
            return sorted(metadata["backups"], 
                         key=lambda x: x["timestamp"], 
                         reverse=True)[0]
        return None
    
    def list_backups(self) -> List[Dict]:
        """
        Lister toutes les sauvegardes disponibles
        
        Returns:
            Liste des informations des sauvegardes
        """
        metadata = self.load_metadata()
        return metadata["backups"]
    
    def delete_old_backups(self, keep_last: int = None):
        """
        Supprimer les anciennes sauvegardes
        
        Args:
            keep_last: Nombre de sauvegardes à conserver (par défaut: max_backups)
        """
        if keep_last is None:
            keep_last = self.max_backups
        
        metadata = self.load_metadata()
        backups = metadata["backups"]
        
        if len(backups) <= keep_last:
            print(f"ℹ️ Nombre de sauvegardes ({len(backups)}) ≤ limite ({keep_last})")
            return
        
        # Trier par date (plus anciennes en premier)
        backups_sorted = sorted(backups, key=lambda x: x["timestamp"])
        
        # Sauvegardes à supprimer
        to_delete = backups_sorted[:-keep_last]
        
        print(f"🗑️  Suppression de {len(to_delete)} anciennes sauvegardes")
        
        deleted_count = 0
        for backup in to_delete:
            try:
                backup_path = backup["backup_path"]
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                    deleted_count += 1
                    print(f"  ✓ Supprimé: {backup['name']}")
            except Exception as e:
                print(f"  ⚠️ Erreur suppression {backup['name']}: {e}")
        
        # Mettre à jour les métadonnées
        metadata["backups"] = backups_sorted[-keep_last:]
        self.save_metadata(metadata)
        
        print(f"✅ {deleted_count} sauvegardes supprimées, {keep_last} conservées")
    
    def calculate_file_hash(self, file_path: str) -> str:
        """
        Calculer le hash MD5 d'un fichier
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            Hash MD5 du fichier
        """
        hash_md5 = hashlib.md5()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        
        return hash_md5.hexdigest()
    
    def get_backup_hash(self, backup_name: str) -> Optional[str]:
        """
        Obtenir le hash d'une sauvegarde
        
        Args:
            backup_name: Nom de la sauvegarde
            
        Returns:
            Hash MD5 ou None si non trouvé
        """
        metadata = self.load_metadata()
        
        for backup in metadata["backups"]:
            if backup["name"] == backup_name:
                return backup["file_hash"]
        
        return None
    
    def verify_backup(self, backup_name: str) -> bool:
        """
        Vérifier l'intégrité d'une sauvegarde
        
        Args:
            backup_name: Nom de la sauvegarde
            
        Returns:
            True si la sauvegarde est intacte, False sinon
        """
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        if not os.path.exists(backup_path):
            print(f"⚠️ Sauvegarde non trouvée: {backup_name}")
            return False
        
        # Calculer le hash actuel
        current_hash = self.calculate_file_hash(backup_path)
        
        # Obtenir le hash original
        original_hash = self.get_backup_hash(backup_name)
        
        if original_hash and current_hash == original_hash:
            print(f"✅ Sauvegarde vérifiée: {backup_name}")
            print(f"   Hash: {current_hash[:16]}...")
            return True
        else:
            print(f"❌ Sauvegarde corrompue: {backup_name}")
            if original_hash:
                print(f"   Original: {original_hash[:16]}...")
                print(f"   Actuel:   {current_hash[:16]}...")
            return False
    
    def load_metadata(self) -> Dict:
        """
        Charger les métadonnées des sauvegardes
        
        Returns:
            Dictionnaire des métadonnées
        """
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Erreur chargement métadonnées: {e}")
        
        # Métadonnées par défaut
        return {
            "created": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "total_backups": 0,
            "backups": [],
            "restorations": [],
            "settings": {
                "max_backups": self.max_backups,
                "backup_dir": self.backup_dir
            }
        }
    
    def save_metadata(self, metadata: Dict):
        """
        Sauvegarder les métadonnées des sauvegardes
        
        Args:
            metadata: Dictionnaire des métadonnées
        """
        metadata["last_updated"] = datetime.now().isoformat()
        metadata["total_backups"] = len(metadata["backups"])
        
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            print(f"❌ Erreur sauvegarde métadonnées: {e}")
    
    def print_summary(self):
        """
        Afficher un résumé des sauvegardes
        """
        metadata = self.load_metadata()
        
        print("\n" + "📊 RÉSUMÉ DES SAUVEGARDES " + "="*40)
        print(f"   Total sauvegardes: {metadata['total_backups']}")
        print(f"   Dernière mise à jour: {metadata['last_updated']}")
        print(f"   Répertoire: {self.backup_dir}")
        print("-" * 60)
        
        if metadata["backups"]:
            print("📁 Sauvegardes disponibles:")
            for i, backup in enumerate(reversed(metadata["backups"][-5:]), 1):
                print(f"   {i}. {backup['name']}")
                print(f"      Taille: {backup['file_size']} bytes")
                print(f"      Date: {backup['datetime']}")
                if backup.get('description'):
                    print(f"      Description: {backup['description']}")
                print()
        else:
            print("ℹ️ Aucune sauvegarde disponible")
        
        print("=" * 60)

class AutoBackupScheduler:
    """
    Planificateur de sauvegarde automatique
    """
    
    def __init__(self, backup_manager: BackupManager, interval_minutes: int = 30):
        """
        Initialiser le planificateur
        
        Args:
            backup_manager: Instance de BackupManager
            interval_minutes: Intervalle entre les sauvegardes (minutes)
        """
        self.backup_manager = backup_manager
        self.interval_seconds = interval_minutes * 60
        self.running = False
        
    def start(self, files_to_backup: List[str]):
        """
        Démarrer le planificateur
        
        Args:
            files_to_backup: Liste des fichiers à sauvegarder automatiquement
        """
        self.running = True
        print(f"⏰ Planificateur démarré (intervalle: {self.interval_seconds/60} minutes)")
        
        try:
            while self.running:
                print(f"\n🕐 Prochaine sauvegarde dans {self.interval_seconds/60} minutes...")
                time.sleep(self.interval_seconds)
                
                if self.running:
                    print("🔄 Création sauvegarde automatique...")
                    
                    for file_path in files_to_backup:
                        if os.path.exists(file_path):
                            self.backup_manager.create_auto_backup(file_path)
                        else:
                            print(f"⚠️ Fichier non trouvé: {file_path}")
                    
                    # Nettoyer les anciennes sauvegardes
                    self.backup_manager.delete_old_backups()
        
        except KeyboardInterrupt:
            print("\n⏹️ Planificateur arrêté par l'utilisateur")
        except Exception as e:
            print(f"❌ Erreur planificateur: {e}")
        finally:
            self.running = False
    
    def stop(self):
        """
        Arrêter le planificateur
        """
        self.running = False
        print("⏹️ Planificateur arrêté")

def main():
    """
    Fonction principale pour démonstration
    """
    print("💾 Gestionnaire de sauvegarde Harmonic AI")
    print("=" * 60)
    
    # Initialiser le gestionnaire
    manager = BackupManager(
        backup_dir="harmonic_backups",
        max_backups=5  # Limite basse pour démonstration
    )
    
    # Fichiers à sauvegarder
    files_to_backup = [
        "lm_arena_results_partial.json",
        "verification_modele_reel_aws.md"
    ]
    
    # Créer des sauvegardes de démonstration
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            manager.create_backup(
                file_path,
                description=f"Sauvegarde initiale {datetime.now().strftime('%Y-%m-%d')}"
            )
        else:
            print(f"ℹ️ Fichier non trouvé (démo): {file_path}")
    
    # Afficher le résumé
    manager.print_summary()
    
    # Vérifier les sauvegardes
    backups = manager.list_backups()
    if backups:
        print("\n🔍 Vérification intégrité sauvegardes...")
        for backup in backups[:3]:  # Vérifier les 3 premières
            manager.verify_backup(backup["name"])
    
    # Nettoyer les anciennes sauvegardes
    print("\n🧹 Nettoyage anciennes sauvegardes...")
    manager.delete_old_backups(keep_last=3)

if __name__ == "__main__":
    main()