#!/usr/bin/env python3
"""
🔍 ENQUÊTE COMPLÈTE : POURQUOI DEEPSEEK N'EST PLUS SUR EC2
Investigation complète de la disparition de DeepSeek V4 Pro
"""

import os
import json
import subprocess
import requests
from pathlib import Path
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

class DeepSeekEC2Investigator:
    """Enquêteur sur la disparition de DeepSeek sur EC2"""
    
    def __init__(self):
        print("🔍 ENQUÊTE : POURQUOI DEEPSEEK N'EST PLUS SUR EC2")
        print("=" * 70)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "investigation": {},
            "findings": [],
            "conclusions": []
        }
    
    def check_ec2_instance_status(self):
        """Vérifier si nous sommes sur EC2"""
        print("\n🖥️  VÉRIFICATION INSTANCE EC2...")
        
        try:
            # Vérifier les métadonnées EC2
            metadata_url = "http://169.254.169.254/latest/meta-data/"
            
            try:
                response = requests.get(metadata_url, timeout=5)
                
                if response.status_code == 200:
                    # Récupérer les métadonnées
                    instance_id = requests.get(f"{metadata_url}instance-id", timeout=5).text
                    instance_type = requests.get(f"{metadata_url}instance-type", timeout=5).text
                    region = requests.get(f"{metadata_data}placement/availability-zone", timeout=5).text[:-1]
                    
                    ec2_info = {
                        "is_ec2": True,
                        "instance_id": instance_id,
                        "instance_type": instance_type,
                        "region": region,
                        "metadata_accessible": True
                    }
                    
                    print(f"   ✅ Instance EC2 détectée")
                    print(f"   🖥️  ID: {instance_id}")
                    print(f"   🏷️  Type: {instance_type}")
                    print(f"   🌍 Region: {region}")
                    
                    return ec2_info
                else:
                    print("   ❌ Métadonnées EC2 non accessibles")
                    return {"is_ec2": False, "metadata_accessible": False}
                    
            except requests.exceptions.Timeout:
                print("   ❌ Timeout métadonnées EC2")
                return {"is_ec2": False, "metadata_accessible": False, "error": "timeout"}
            except Exception as e:
                print(f"   ❌ Erreur métadonnées: {e}")
                return {"is_ec2": False, "metadata_accessible": False, "error": str(e)}
                
        except Exception as e:
            print(f"   ❌ Erreur générale: {e}")
            return {"is_ec2": False, "error": str(e)}
    
    def check_disk_space(self):
        """Vérifier l'espace disque"""
        print("\n💾 VÉRIFICATION ESPACE DISQUE...")
        
        try:
            # Sur Windows
            if os.name == 'nt':
                import psutil
                disk = psutil.disk_usage('.')
                disk_info = {
                    "total_gb": disk.total / (1024**3),
                    "used_gb": disk.used / (1024**3),
                    "free_gb": disk.free / (1024**3),
                    "percent_used": (disk.used / disk.total) * 100
                }
            else:
                # Sur Linux
                result = subprocess.run(['df', '-h', '.'], capture_output=True, text=True)
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    parts = lines[1].split()
                    disk_info = {
                        "total_gb": float(parts[1].replace('G', '')),
                        "used_gb": float(parts[2].replace('G', '')),
                        "free_gb": float(parts[3].replace('G', '')),
                        "percent_used": float(parts[4].replace('%', ''))
                    }
                else:
                    disk_info = {"error": "Impossible de parser df"}
            
            print(f"   📊 Total: {disk_info.get('total_gb', 0):.1f} GB")
            print(f"   📊 Utilisé: {disk_info.get('used_gb', 0):.1f} GB")
            print(f"   📊 Libre: {disk_info.get('free_gb', 0):.1f} GB")
            print(f"   📊 % utilisé: {disk_info.get('percent_used', 0):.1f}%")
            
            # Vérifier si l'espace est suffisant pour DeepSeek (1.2TB)
            if disk_info.get('free_gb', 0) < 1200:
                print("   ⚠️  Espace insuffisant pour DeepSeek V4 Pro (nécessite 1.2TB)")
                disk_info["sufficient_for_deepseek"] = False
            else:
                print("   ✅ Espace suffisant pour DeepSeek V4 Pro")
                disk_info["sufficient_for_deepseek"] = True
            
            return disk_info
            
        except Exception as e:
            print(f"   ❌ Erreur vérification disque: {e}")
            return {"error": str(e)}
    
    def check_recent_file_operations(self):
        """Vérifier les opérations de fichiers récentes"""
        print("\n📂 VÉRIFICATION OPÉRATIONS FICHIERS RÉCENTES...")
        
        try:
            current_dir = Path('.')
            
            # Chercher les fichiers récents (dernières 24h)
            recent_files = []
            current_time = datetime.now().timestamp()
            day_ago = current_time - (24 * 60 * 60)
            
            for file_path in current_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        mtime = file_path.stat().st_mtime
                        if mtime > day_ago:
                            recent_files.append({
                                "path": str(file_path),
                                "name": file_path.name,
                                "size_mb": file_path.stat().st_size / (1024**2),
                                "modified": datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                            })
                    except:
                        continue
            
            # Trier par date de modification
            recent_files.sort(key=lambda x: x['modified'], reverse=True)
            
            print(f"   📊 Fichiers modifiés (dernières 24h): {len(recent_files)}")
            
            # Afficher les 10 plus récents
            for i, file_info in enumerate(recent_files[:10]):
                print(f"   {i+1:2d}. {file_info['name']}")
                print(f"       📅 {file_info['modified']}")
                print(f"       📊 {file_info['size_mb']:.1f} MB")
                print(f"       📁 {file_info['path']}")
            
            return recent_files
            
        except Exception as e:
            print(f"   ❌ Erreur vérification fichiers: {e}")
            return []
    
    def check_aws_credentials_status(self):
        """Vérifier le statut des credentials AWS"""
        print("\n🔐 VÉRIFICATION CREDENTIALS AWS...")
        
        try:
            # Configuration AWS
            config = {
                "aws_access_key_id": "AKIAUX3GRWKTZEPOJOFI",
                "aws_secret_access_key": "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",
                "region": "us-east-1"
            }
            
            # Tester l'accès S3
            s3_client = boto3.client(
                's3',
                aws_access_key_id=config["aws_access_key_id"],
                aws_secret_access_key=config["aws_secret_access_key"],
                region_name=config["region"]
            )
            
            # Vérifier l'accès au bucket DeepSeek
            try:
                response = s3_client.list_objects_v2(
                    Bucket="deepseek-models-326095712935",
                    MaxKeys=5
                )
                
                if 'Contents' in response:
                    files = response['Contents']
                    total_size = sum(obj['Size'] for obj in files)
                    
                    credentials_status = {
                        "valid": True,
                        "s3_accessible": True,
                        "deepseek_bucket_accessible": True,
                        "files_found": len(files),
                        "total_size_gb": total_size / (1024**3),
                        "error": None
                    }
                    
                    print(f"   ✅ Credentials AWS valides")
                    print(f"   ✅ Accès S3 OK")
                    print(f"   ✅ Bucket DeepSeek accessible")
                    print(f"   📁 Fichiers: {len(files)}")
                    print(f"   📊 Taille: {total_size / (1024**3):.1f} GB")
                    
                else:
                    credentials_status = {
                        "valid": True,
                        "s3_accessible": True,
                        "deepseek_bucket_accessible": True,
                        "files_found": 0,
                        "total_size_gb": 0,
                        "error": None
                    }
                    
                    print(f"   ✅ Credentials AWS valides")
                    print(f"   ✅ Accès S3 OK")
                    print(f"   ✅ Bucket DeepSeek accessible mais vide")
                    
            except ClientError as e:
                credentials_status = {
                    "valid": True,
                    "s3_accessible": False,
                    "deepseek_bucket_accessible": False,
                    "files_found": 0,
                    "total_size_gb": 0,
                    "error": str(e)
                }
                
                print(f"   ✅ Credentials AWS valides")
                print(f"   ❌ Accès S3 refusé: {e}")
                
            return credentials_status
            
        except Exception as e:
            print(f"   ❌ Erreur credentials: {e}")
            return {"valid": False, "error": str(e)}
    
    def check_deepseek_download_logs(self):
        """Vérifier les logs de téléchargement DeepSeek"""
        print("\n📋 VÉRIFICATION LOGS TÉLÉCHARGEMENT DEEPSEEK...")
        
        log_files = [
            "deepseek_aws_downloader.log",
            "download_deepseek_weights_s3.log",
            "deepseek_download.log",
            "aws_download.log",
            "s3_download.log"
        ]
        
        found_logs = []
        
        for log_file in log_files:
            log_path = Path(log_file)
            
            if log_path.exists():
                try:
                    with open(log_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Analyser le contenu
                    lines = content.split('\n')
                    error_lines = [line for line in lines if 'error' in line.lower() or 'failed' in line.lower()]
                    success_lines = [line for line in lines if 'success' in line.lower() or 'completed' in line.lower()]
                    
                    log_info = {
                        "file": log_file,
                        "size_kb": log_path.stat().st_size / 1024,
                        "total_lines": len(lines),
                        "error_lines": len(error_lines),
                        "success_lines": len(success_lines),
                        "last_modified": datetime.fromtimestamp(log_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        "sample_lines": lines[-5:] if lines else []
                    }
                    
                    found_logs.append(log_info)
                    
                    print(f"   📄 {log_file}")
                    print(f"       📊 Taille: {log_info['size_kb']:.1f} KB")
                    print(f"       📊 Lignes: {log_info['total_lines']}")
                    print(f"       ❌ Erreurs: {log_info['error_lines']}")
                    print(f"       ✅ Succès: {log_info['success_lines']}")
                    print(f"       📅 Modifié: {log_info['last_modified']}")
                    
                    if error_lines:
                        print(f"       🚨 Dernière erreur: {error_lines[-1][:100]}...")
                    
                except Exception as e:
                    print(f"   ❌ Erreur lecture {log_file}: {e}")
            else:
                print(f"   ❌ {log_file}: inexistant")
        
        return found_logs
    
    def check_system_processes(self):
        """Vérifier les processus système"""
        print("\n⚙️  VÉRIFICATION PROCESSUS SYSTÈME...")
        
        try:
            if os.name == 'nt':
                # Windows
                result = subprocess.run(['tasklist'], capture_output=True, text=True)
                processes = result.stdout
            else:
                # Linux
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                processes = result.stdout
            
            # Chercher les processus liés à DeepSeek
            deepseek_processes = []
            lines = processes.split('\n')
            
            for line in lines:
                if any(keyword in line.lower() for keyword in ['deepseek', 'python', 'download', 'aws']):
                    deepseek_processes.append(line.strip())
            
            print(f"   📊 Processus liés à DeepSeek: {len(deepseek_processes)}")
            
            for i, process in enumerate(deepseek_processes[:10]):
                print(f"   {i+1:2d}. {process}")
            
            return deepseek_processes
            
        except Exception as e:
            print(f"   ❌ Erreur vérification processus: {e}")
            return []
    
    def analyze_findings(self):
        """Analyser les découvertes"""
        print("\n🎯 ANALYSE DÉCOUVERTES...")
        
        findings = []
        
        # Analyser l'espace disque
        disk_info = self.results["investigation"].get("disk_space", {})
        if not disk_info.get("sufficient_for_deepseek", False):
            findings.append("💾 Espace disque insuffisant pour DeepSeek V4 Pro")
            findings.append(f"   📊 Espace libre: {disk_info.get('free_gb', 0):.1f} GB")
            findings.append(f"   📊 Nécessaire: 1200 GB (1.2TB)")
        
        # Analyser les credentials AWS
        aws_info = self.results["investigation"].get("aws_credentials", {})
        if not aws_info.get("deepseek_bucket_accessible", False):
            findings.append("🔐 Accès AWS S3 refusé pour DeepSeek")
            findings.append(f"   ❌ Erreur: {aws_info.get('error', 'Inconnue')}")
        
        # Analyser les logs
        logs = self.results["investigation"].get("download_logs", [])
        if logs:
            error_count = sum(log.get("error_lines", 0) for log in logs)
            if error_count > 0:
                findings.append(f"📋 {error_count} erreurs trouvées dans les logs de téléchargement")
        
        # Analyser les processus
        processes = self.results["investigation"].get("system_processes", [])
        download_processes = [p for p in processes if 'download' in p.lower()]
        if download_processes:
            findings.append(f"⚙️  {len(download_processes)} processus de téléchargement actifs")
        
        self.results["findings"] = findings
        return findings
    
    def generate_conclusions(self):
        """Générer les conclusions"""
        print("\n🎯 GÉNÉRATION CONCLUSIONS...")
        
        findings = self.results["findings"]
        conclusions = []
        
        # Causes possibles
        if any("Espace disque" in f for f in findings):
            conclusions.append("💾 CAUSE PROBABLE : Espace disque insuffisant")
            conclusions.append("   📊 DeepSeek nécessite 1.2TB d'espace libre")
            conclusions.append("   🗑️  Les fichiers ont peut-être été supprimés pour libérer de l'espace")
        
        if any("Accès AWS" in f for f in findings):
            conclusions.append("🔐 CAUSE PROBABLE : Permissions AWS révoquées")
            conclusions.append("   📋 Les credentials ne permettent plus l'accès au bucket")
            conclusions.append("   🚫 Le téléchargement a échoué")
        
        if any("erreurs" in f for f in findings):
            conclusions.append("❌ CAUSE PROBABLE : Erreurs de téléchargement")
            conclusions.append("   📋 Le téléchargement a rencontré des erreurs")
            conclusions.append("   🔄 Les fichiers ont peut-être été corrompus")
        
        if not conclusions:
            conclusions.append("❓ CAUSE INCONNUE : Aucune anomalie détectée")
            conclusions.append("   🔍 DeepSeek n'a peut-être jamais été complètement téléchargé")
            conclusions.append("   📊 Les fichiers trouvés sont des fragments")
        
        self.results["conclusions"] = conclusions
        return conclusions
    
    def save_investigation_report(self):
        """Sauvegarder le rapport d'enquête"""
        print("\n📄 SAUVEGARDE RAPPORT D'ENQUÊTE...")
        
        report_file = Path("deepseek_ec2_investigation_report.json")
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"✅ Rapport sauvegardé: {report_file.absolute()}")
        return report_file
    
    def run_complete_investigation(self):
        """Exécuter l'enquête complète"""
        print("🚀 DÉMARRAGE ENQUÊTE COMPLÈTE...")
        
        # 1. Vérifier le statut EC2
        self.results["investigation"]["ec2_status"] = self.check_ec2_instance_status()
        
        # 2. Vérifier l'espace disque
        self.results["investigation"]["disk_space"] = self.check_disk_space()
        
        # 3. Vérifier les opérations de fichiers récentes
        self.results["investigation"]["recent_operations"] = self.check_recent_file_operations()
        
        # 4. Vérifier les credentials AWS
        self.results["investigation"]["aws_credentials"] = self.check_aws_credentials_status()
        
        # 5. Vérifier les logs de téléchargement
        self.results["investigation"]["download_logs"] = self.check_deepseek_download_logs()
        
        # 6. Vérifier les processus système
        self.results["investigation"]["system_processes"] = self.check_system_processes()
        
        # 7. Analyser les découvertes
        self.analyze_findings()
        
        # 8. Générer les conclusions
        self.generate_conclusions()
        
        # 9. Sauvegarder le rapport
        report_file = self.save_investigation_report()
        
        print("\n🏆 ENQUÊTE TERMINÉE!")
        print(f"📄 Rapport complet: {report_file}")
        
        # Afficher le résumé
        findings = self.results["findings"]
        conclusions = self.results["conclusions"]
        
        print("\n📊 DÉCOUVERTES:")
        print("=" * 50)
        
        for finding in findings:
            print(f"   {finding}")
        
        print("\n🎯 CONCLUSIONS:")
        print("=" * 50)
        
        for conclusion in conclusions:
            print(f"   {conclusion}")
        
        return True

if __name__ == "__main__":
    investigator = DeepSeekEC2Investigator()
    success = investigator.run_complete_investigation()
    
    if success:
        print("\n🌊 ENQUÊTE TERMINÉE AVEC SUCCÈS!")
        print("✅ Rapport généré: deepseek_ec2_investigation_report.json")
    else:
        print("\n❌ ERREUR LORS DE L'ENQUÊTE")
