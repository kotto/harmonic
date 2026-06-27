#!/usr/bin/env python3
"""
🔍 VÉRIFICATION COMPLÈTE : IMPORTATION DEEPSEEK V4 PRO
Vérification manuelle de tous les chemins possibles pour DeepSeek
"""

import os
import json
from pathlib import Path
from datetime import datetime

class DeepSeekImportationVerifier:
    """Vérificateur complet d'importation DeepSeek"""
    
    def __init__(self):
        print("🔍 VÉRIFICATION COMPLÈTE IMPORTATION DEEPSEEK V4 PRO")
        print("=" * 70)
        
        # Chemins possibles pour DeepSeek
        self.search_paths = [
            "./deepseek-model",
            "./deepseek-v4-pro-complete",
            "./deepseek-v4-pro-direct",
            "./deepseek-v4-pro-root",
            "./deepseek-direct-bypass",
            "./deepseek-harmonic-complete",
            "./downloaded_models",
            "./models",
            "./model",
            "./deepseek",
            "./deepseek_v4_pro",
            "./deepseek_v4",
            "./deepseek_coder",
            "./deepseek-coder",
            "./huggingface",
            "./hf_models",
            "./transformers_cache",
            "./cache",
            "./.cache",
            "./temp",
            "./tmp"
        ]
        
        # Extensions de fichiers de modèle
        self.model_extensions = [
            '.bin', '.safetensors', '.pth', '.pt', '.gguf', '.ckpt', '.model',
            '.h5', '.onnx', '.tflite', '.trt', '.engine'
        ]
        
        # Fichiers de configuration
        self.config_files = [
            'config.json', 'tokenizer.json', 'tokenizer_config.json',
            'special_tokens_map.json', 'vocab.json', 'merges.txt',
            'generation_config.json', 'model_index.json'
        ]
        
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "search_results": {},
            "model_files_found": [],
            "config_files_found": [],
            "total_size_bytes": 0,
            "conclusions": []
        }
    
    def search_all_paths(self):
        """Rechercher dans tous les chemins possibles"""
        print("\n🔍 RECHERCHE DANS TOUS LES CHEMINS...")
        
        search_results = {}
        
        for path in self.search_paths:
            path_obj = Path(path)
            
            print(f"\n   📁 Vérification: {path}")
            
            if path_obj.exists():
                files = list(path_obj.rglob("*"))
                files = [f for f in files if f.is_file()]
                
                model_files = []
                config_files = []
                other_files = []
                
                total_size = 0
                
                for file_path in files:
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    
                    # Vérifier si c'est un fichier de modèle
                    if file_path.suffix.lower() in self.model_extensions or 'model' in file_path.name.lower():
                        model_files.append(file_path)
                    # Vérifier si c'est un fichier de configuration
                    elif file_path.name in self.config_files:
                        config_files.append(file_path)
                    else:
                        other_files.append(file_path)
                
                search_results[path] = {
                    "exists": True,
                    "total_files": len(files),
                    "model_files": len(model_files),
                    "config_files": len(config_files),
                    "other_files": len(other_files),
                    "total_size_bytes": total_size,
                    "total_size_gb": total_size / (1024**3),
                    "model_files_list": [str(f.relative_to(path_obj)) for f in model_files],
                    "config_files_list": [str(f.relative_to(path_obj)) for f in config_files],
                    "sample_files": [str(f.relative_to(path_obj)) for f in files[:10]]
                }
                
                print(f"      ✅ Existe")
                print(f"      📊 Fichiers: {len(files)}")
                print(f"      🎯 Modèles: {len(model_files)}")
                print(f"      ⚙️  Config: {len(config_files)}")
                print(f"      📊 Taille: {total_size / (1024**3):.2f} GB")
                
                if model_files:
                    print(f"      📋 Modèles: {', '.join([f.name for f in model_files[:3]])}")
                
                if config_files:
                    print(f"      ⚙️  Config: {', '.join([f.name for f in config_files[:3]])}")
                
                # Ajouter aux résultats globaux
                self.results["model_files_found"].extend(model_files)
                self.results["config_files_found"].extend(config_files)
                self.results["total_size_bytes"] += total_size
                
            else:
                search_results[path] = {
                    "exists": False,
                    "total_files": 0,
                    "model_files": 0,
                    "config_files": 0,
                    "other_files": 0,
                    "total_size_bytes": 0,
                    "total_size_gb": 0
                }
                
                print(f"      ❌ N'existe pas")
        
        self.results["search_results"] = search_results
        return search_results
    
    def analyze_model_files(self):
        """Analyser les fichiers de modèle trouvés"""
        print("\n🔍 ANALYSE FICHIERS MODÈLE...")
        
        model_files = self.results["model_files_found"]
        
        if not model_files:
            print("   ❌ Aucun fichier de modèle trouvé")
            return False
        
        print(f"   📊 {len(model_files)} fichiers de modèle trouvés")
        
        # Analyser les fichiers par type
        file_types = {}
        large_files = []
        
        for file_path in model_files:
            file_size = file_path.stat().st_size
            file_ext = file_path.suffix.lower()
            
            file_types[file_ext] = file_types.get(file_ext, 0) + 1
            
            if file_size > 1024**3:  # > 1GB
                large_files.append({
                    "path": str(file_path),
                    "name": file_path.name,
                    "size_gb": file_size / (1024**3)
                })
        
        print(f"   📋 Types de fichiers: {dict(file_types)}")
        print(f"   🎯 Fichiers > 1GB: {len(large_files)}")
        
        # Afficher les plus gros fichiers
        large_files.sort(key=lambda x: x["size_gb"], reverse=True)
        for i, file_info in enumerate(large_files[:5]):
            print(f"      {i+1}. {file_info['name']} ({file_info['size_gb']:.1f} GB)")
        
        # Vérifier si on a les poids principaux
        has_main_weights = any(
            any(keyword in f.name.lower() for keyword in ['model', 'weights', 'pytorch_model'])
            for f in model_files
        )
        
        if has_main_weights:
            print("   ✅ Poids principaux détectés")
            return True
        else:
            print("   ⚠️  Poids principaux non détectés")
            return False
    
    def analyze_config_files(self):
        """Analyser les fichiers de configuration"""
        print("\n🔍 ANALYSE FICHIERS CONFIGURATION...")
        
        config_files = self.results["config_files_found"]
        
        if not config_files:
            print("   ❌ Aucun fichier de configuration trouvé")
            return False
        
        print(f"   📊 {len(config_files)} fichiers de configuration trouvés")
        
        # Analyser les fichiers de configuration
        config_types = {}
        
        for file_path in config_files:
            file_name = file_path.name
            config_types[file_name] = config_types.get(file_name, 0) + 1
        
        print(f"   📋 Types de configuration: {dict(config_types)}")
        
        # Vérifier si on a les fichiers essentiels
        essential_configs = ['config.json', 'tokenizer.json']
        has_essential = any(
            any(essential in f.name for essential in essential_configs)
            for f in config_files
        )
        
        if has_essential:
            print("   ✅ Fichiers de configuration essentiels détectés")
            return True
        else:
            print("   ⚠️  Fichiers de configuration essentiels manquants")
            return False
    
    def check_model_completeness(self):
        """Vérifier si le modèle est complet"""
        print("\n🔍 VÉRIFICATION COMPLÉTUDE MODÈLE...")
        
        model_files = self.results["model_files_found"]
        config_files = self.results["config_files_found"]
        total_size = self.results["total_size_bytes"]
        
        # Critères de complétude
        has_weights = len(model_files) > 0
        has_config = len(config_files) > 0
        has_large_files = any(f.stat().st_size > 1024**3 for f in model_files)
        
        # Taille attendue pour DeepSeek V4 Pro (~1.2TB)
        expected_size = 1.2 * 1024**4  # 1.2TB
        size_percentage = (total_size / expected_size) * 100
        
        print(f"   📊 Taille totale: {total_size / (1024**4):.3f} TB")
        print(f"   📊 Pourcentage attendu: {size_percentage:.1f}%")
        print(f"   🎯 Fichiers poids: {len(model_files)}")
        print(f"   ⚙️  Fichiers config: {len(config_files)}")
        
        # Évaluer la complétude
        if has_weights and has_config and size_percentage > 90:
            print("   🎉 MODÈLE COMPLET DÉTECTÉ!")
            print("   ✅ DeepSeek V4 Pro est complètement importé")
            return "complete"
        elif has_weights and has_config and size_percentage > 50:
            print("   ⚠️  MODÈLE PARTIEL DÉTECTÉ")
            print("   📊 DeepSeek V4 Pro est partiellement importé")
            return "partial"
        elif has_weights or has_config:
            print("   ⚠️  FRAGMENTS DE MODÈLE DÉTECTÉS")
            print("   📊 Seuls des fragments de DeepSeek sont présents")
            return "fragments"
        else:
            print("   ❌ AUCUN MODÈLE DÉTECTÉ")
            print("   📊 DeepSeek V4 Pro n'est pas importé")
            return "none"
    
    def generate_conclusions(self):
        """Générer les conclusions"""
        print("\n🎯 GÉNÉRATION CONCLUSIONS...")
        
        completeness = self.check_model_completeness()
        
        conclusions = []
        
        if completeness == "complete":
            conclusions.append("🎉 SUCCÈS TOTAL : DeepSeek V4 Pro est complètement importé")
            conclusions.append("   📊 Taille complète: ~1.2TB")
            conclusions.append("   🎯 Poids et configuration disponibles")
            conclusions.append("   🚀 Prêt pour transformation harmonique immédiate")
            conclusions.append("   📋 Prochaine étape: python apply_harmonic_transformation.py")
        
        elif completeness == "partial":
            conclusions.append("⚠️  SUCCÈS PARTIEL : DeepSeek V4 Pro est partiellement importé")
            conclusions.append("   📊 Taille partielle: < 1.2TB")
            conclusions.append("   🎯 Certains poids disponibles")
            conclusions.append("   🚀 Peut nécessiter téléchargement supplémentaire")
            conclusions.append("   📋 Prochaine étape: Compléter le téléchargement")
        
        elif completeness == "fragments":
            conclusions.append("⚠️  FRAGMENTS : Seuls des fragments de DeepSeek sont présents")
            conclusions.append("   📊 Taille minimale: < 100GB")
            conclusions.append("   🎯 Poids incomplets")
            conclusions.append("   🚀 Nécessite téléchargement complet")
            conclusions.append("   📋 Prochaine étape: Téléchargement depuis S3 ou Hugging Face")
        
        else:
            conclusions.append("❌ ÉCHEC : DeepSeek V4 Pro n'est pas importé")
            conclusions.append("   📊 Aucun poids détecté")
            conclusions.append("   🎯 Configuration manquante")
            conclusions.append("   🚀 Nécessite importation complète")
            conclusions.append("   📋 Prochaine étape: Importation depuis Hugging Face")
        
        self.results["conclusions"] = conclusions
        return conclusions
    
    def save_verification_report(self):
        """Sauvegarder le rapport de vérification"""
        print("\n📄 SAUVEGARDE RAPPORT...")
        
        report_file = Path("deepseek_verification_report.json")
        
        # Préparer le rapport final
        final_report = {
            "timestamp": self.results["timestamp"],
            "summary": {
                "total_paths_searched": len(self.search_paths),
                "paths_found": sum(1 for p in self.search_paths if Path(p).exists()),
                "model_files_found": len(self.results["model_files_found"]),
                "config_files_found": len(self.results["config_files_found"]),
                "total_size_gb": self.results["total_size_bytes"] / (1024**3),
                "total_size_tb": self.results["total_size_bytes"] / (1024**4)
            },
            "search_results": self.results["search_results"],
            "model_files": [str(f) for f in self.results["model_files_found"]],
            "config_files": [str(f) for f in self.results["config_files_found"]],
            "conclusions": self.results["conclusions"]
        }
        
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        print(f"✅ Rapport sauvegardé: {report_file.absolute()}")
        return report_file
    
    def run_complete_verification(self):
        """Exécuter la vérification complète"""
        print("🚀 DÉMARRAGE VÉRIFICATION COMPLÈTE...")
        
        # 1. Rechercher dans tous les chemins
        self.search_all_paths()
        
        # 2. Analyser les fichiers de modèle
        self.analyze_model_files()
        
        # 3. Analyser les fichiers de configuration
        self.analyze_config_files()
        
        # 4. Vérifier la complétude
        completeness = self.check_model_completeness()
        
        # 5. Générer les conclusions
        self.generate_conclusions()
        
        # 6. Sauvegarder le rapport
        report_file = self.save_verification_report()
        
        print("\n🏆 VÉRIFICATION TERMINÉE!")
        print(f"📄 Rapport complet: {report_file}")
        
        # Afficher le résumé final
        conclusions = self.results["conclusions"]
        
        print("\n🎯 RÉSUMÉ FINAL:")
        print("=" * 50)
        
        for conclusion in conclusions:
            print(f"   {conclusion}")
        
        return completeness

if __name__ == "__main__":
    verifier = DeepSeekImportationVerifier()
    completeness = verifier.run_complete_verification()
    
    if completeness == "complete":
        print("\n🌊 DEEPSEEK V4 PRO EST COMPLÈTEMENT IMPORTÉ!")
        print("✅ Prêt pour transformation harmonique")
        print("🚀 Exécuter: python apply_harmonic_transformation.py")
    elif completeness == "partial":
        print("\n⚠️  DEEPSEEK V4 PRO EST PARTIELLEMENT IMPORTÉ!")
        print("📊 Compléter le téléchargement")
    elif completeness == "fragments":
        print("\n⚠️  SEULS DES FRAGMENTS SONT PRÉSENTS!")
        print("📊 Téléchargement complet nécessaire")
    else:
        print("\n❌ DEEPSEEK V4 PRO N'EST PAS IMPORTÉ!")
        print("📊 Importation depuis Hugging Face nécessaire")
        print("🚀 Exécuter: python deepseek_aws_downloader.py")
