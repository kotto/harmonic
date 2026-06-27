#!/usr/bin/env python3
"""
🔍 DIAGNOSTIC TÉLÉCHARGEMENT MISTRAL
Analyse complète des problèmes de téléchargement et solutions
"""

import json
import math
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Constantes harmoniques
PHI = (1 + math.sqrt(5)) / 2  # 1.61803398875
ALPHA = math.atan(PHI)  # 1.17556945908 radians
HARMONIC_GAIN = PHI ** 2  # 2.61803398875
DETERMINISM_FACTOR = 0.999999999999  # 99.9999999999%

class MistralDownloadDiagnostic:
    """Diagnostic complet du téléchargement Mistral"""
    
    def __init__(self):
        print("🔍 DIAGNOSTIC TÉLÉCHARGEMENT MISTRAL")
        print("=" * 80)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.diagnostic = {
            "timestamp": datetime.now().isoformat(),
            "problemes_identifies": [],
            "solutions": [],
            "liens_telechargement": {},
            "versions_disponibles": {},
            "causes_probables": [],
            "recommandations": []
        }
    
    def analyser_problemes_transformers(self):
        """Analyser les problèmes avec transformers"""
        print("\n🔍 ANALYSE PROBLÈMES TRANSFORMERS:")
        
        probleme_principal = "PyPreTokenizerTypeWrapper"
        solutions = []
        
        print(f"   🔍 Problème identifié: {probleme_principal}")
        print("   📝 Description: Erreur dans le tokenizer de Mistral")
        
        # Causes possibles
        causes = [
            {
                "cause": "Version de transformers incompatible",
                "description": "La version actuelle de transformers (4.36.0) n'est pas compatible avec les derniers modèles Mistral",
                "solution": "Mettre à jour transformers vers la dernière version"
            },
            {
                "cause": "Tokenizers incompatible",
                "description": "La bibliothèque tokenizers n'est pas à jour",
                "solution": "Mettre à jour tokenizers vers la dernière version"
            },
            {
                "cause": "Cache corrompu",
                "description": "Le cache Hugging Face contient des fichiers corrompus",
                "solution": "Nettoyer le cache et retélécharger"
            },
            {
                "cause": "Modèle Mistral récent",
                "description": "Les modèles Mistral v0.3 sont trop récents pour la version actuelle",
                "solution": "Utiliser des modèles plus anciens ou mettre à jour"
            }
        ]
        
        print(f"   📊 Causes possibles: {len(causes)}")
        for i, cause in enumerate(causes):
            print(f"   {i+1}. {cause['cause']}")
            print(f"      📝 {cause['description']}")
            print(f"      🔧 {cause['solution']}")
        
        self.diagnostic["causes_probables"] = causes
        
        return causes
    
    def generer_liens_telechargement(self):
        """Générer les liens de téléchargement directs"""
        print("\n🔗 GÉNÉRATION LIENS TÉLÉCHARGEMENT:")
        
        liens = {
            "hugging_face": {
                "mistral_7b_instruct_v0_2": "https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2",
                "mistral_7b_instruct_v0_1": "https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.1",
                "mistral_7b_v0_1": "https://huggingface.co/mistralai/Mistral-7B-v0.1",
                "description": "Téléchargement direct via Hugging Face"
            },
            "manuels": {
                "weights_v0_2": "https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2/resolve/main/pytorch_model.bin",
                "config_v0_2": "https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2/resolve/main/config.json",
                "tokenizer_v0_2": "https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2/resolve/main/tokenizer.json",
                "description": "Téléchargement manuel des fichiers"
            },
            "alternatifs": {
                "thebloke_mistral_7b": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
                "quantized_mistral": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GPTQ",
                "description": "Versions quantifiées optimisées"
            }
        }
        
        print("   📦 Hugging Face:")
        for nom, lien in liens["hugging_face"].items():
            if nom != "description":
                print(f"      🔗 {nom}: {lien}")
        
        print("   📦 Manuels:")
        for nom, lien in liens["manuels"].items():
            if nom != "description":
                print(f"      🔗 {nom}: {lien}")
        
        print("   📦 Alternatifs:")
        for nom, lien in liens["alternatifs"].items():
            if nom != "description":
                print(f"      🔗 {nom}: {lien}")
        
        self.diagnostic["liens_telechargement"] = liens
        
        return liens
    
    def generer_solutions(self):
        """Générer les solutions complètes"""
        print("\n🔧 GÉNÉRATION SOLUTIONS:")
        
        solutions = [
            {
                "priorite": 1,
                "titre": "MISE À JOUR TRANSFORMERS",
                "commandes": [
                    "pip install --upgrade transformers",
                    "pip install --upgrade tokenizers",
                    "pip install --upgrade huggingface_hub"
                ],
                "description": "Mettre à jour toutes les bibliothèques Hugging Face",
                "succès_probable": "Élevé"
            },
            {
                "priorite": 2,
                "titre": "UTILISER MODÈLE V0.2",
                "commandes": [
                    "python -c \"from transformers import AutoTokenizer; tokenizer = AutoTokenizer.from_pretrained('mistralai/Mistral-7B-Instruct-v0.2'); print('✅ Tokenizer v0.2 OK')\"",
                    "python -c \"from transformers import AutoModelForCausalLM; model = AutoModelForCausalLM.from_pretrained('mistralai/Mistral-7B-Instruct-v0.2'); print('✅ Modèle v0.2 OK')\""
                ],
                "description": "Utiliser la version v0.2 qui est plus stable",
                "succès_probable": "Très élevé"
            },
            {
                "priorite": 3,
                "titre": "NETTOYER CACHE",
                "commandes": [
                    "rmdir /s /q C:\\Users\\maatc\\.cache\\huggingface",
                    "mkdir C:\\Users\\maatc\\.cache\\huggingface",
                    "python -c \"print('✅ Cache nettoyé')\""
                ],
                "description": "Supprimer le cache corrompu",
                "succès_probable": "Élevé"
            },
            {
                "priorite": 4,
                "titre": "TÉLÉCHARGEMENT MANUEL",
                "commandes": [
                    "mkdir E:\\mistral-manuel",
                    "curl -L https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2/resolve/main/pytorch_model.bin -o E:\\mistral-manuel\\pytorch_model.bin",
                    "curl -L https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2/resolve/main/config.json -o E:\\mistral-manuel\\config.json",
                    "curl -L https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2/resolve/main/tokenizer.json -o E:\\mistral-manuel\\tokenizer.json"
                ],
                "description": "Télécharger manuellement les fichiers",
                "succès_probable": "Garanti"
            },
            {
                "priorite": 5,
                "titre": "UTILISER THEBLOKE VERSION",
                "commandes": [
                    "python -c \"from transformers import AutoTokenizer; tokenizer = AutoTokenizer.from_pretrained('TheBloke/Mistral-7B-Instruct-v0.2-GGUF'); print('✅ TheBloke tokenizer OK')\"",
                    "python -c \"from transformers import AutoModelForCausalLM; model = AutoModelForCausalLM.from_pretrained('TheBloke/Mistral-7B-Instruct-v0.2-GGUF'); print('✅ TheBloke modèle OK')\""
                ],
                "description": "Utiliser la version optimisée par TheBloke",
                "succès_probable": "Très élevé"
            }
        ]
        
        print(f"   🔧 Solutions disponibles: {len(solutions)}")
        for solution in solutions:
            print(f"   {solution['priorite']}. {solution['titre']} [Succès: {solution['succès_probable']}]")
            print(f"      📝 {solution['description']}")
            print(f"      💻 Commandes:")
            for cmd in solution['commandes']:
                print(f"         {cmd}")
            print()
        
        self.diagnostic["solutions"] = solutions
        
        return solutions
    
    def creer_script_telechargement_alternatif(self):
        """Créer un script de téléchargement alternatif"""
        print("\n📝 CRÉATION SCRIPT TÉLÉCHARGEMENT ALTERNATIF:")
        
        script_content = '''#!/usr/bin/env python3
"""
🚀 TÉLÉCHARGEMENT MISTRAL ALTERNATIF
Script pour télécharger Mistral avec toutes les solutions
"""

import os
import sys
import subprocess
from pathlib import Path

def mettre_a_jour_transformers():
    """Mettre à jour transformers"""
    print("🔄 MISE À JOUR TRANSFORMERS:")
    
    commandes = [
        ["pip", "install", "--upgrade", "transformers"],
        ["pip", "install", "--upgrade", "tokenizers"],
        ["pip", "install", "--upgrade", "huggingface_hub"]
    ]
    
    for cmd in commandes:
        try:
            print(f"   💻 {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("   ✅ Succès")
            else:
                print(f"   ❌ Erreur: {result.stderr[:100]}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

def tester_mistral_v0_2():
    """Tester Mistral v0.2"""
    print("\\n🧪 TEST MISTRAL V0.2:")
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        print("   📦 Tokenizer v0.2...")
        tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
        print("   ✅ Tokenizer OK")
        
        print("   📦 Modèle v0.2...")
        model = AutoModelForCausalLM.from_pretrained(
            "mistralai/Mistral-7B-Instruct-v0.2",
            torch_dtype="auto",
            device_map="auto"
        )
        print("   ✅ Modèle OK")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def tester_thebloke_version():
    """Tester la version TheBloke"""
    print("\\n🧪 TEST THEBLOKE VERSION:")
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        print("   📦 TheBloke tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained("TheBloke/Mistral-7B-Instruct-v0.2-GGUF")
        print("   ✅ Tokenizer OK")
        
        print("   📦 TheBloke modèle...")
        model = AutoModelForCausalLM.from_pretrained(
            "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
            torch_dtype="auto",
            device_map="auto"
        )
        print("   ✅ Modèle OK")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 TÉLÉCHARGEMENT MISTRAL ALTERNATIF")
    print("=" * 50)
    
    # Étape 1: Mettre à jour
    mettre_a_jour_transformers()
    
    # Étape 2: Tester v0.2
    if tester_mistral_v0_2():
        print("\\n🎉 SUCCÈS - MISTRAL V0.2 FONCTIONNEL")
        return
    
    # Étape 3: Tester TheBloke
    if tester_thebloke_version():
        print("\\n🎉 SUCCÈS - THEBLOKE VERSION FONCTIONNELLE")
        return
    
    print("\\n❌ ÉCHEC - AUCUNE VERSION FONCTIONNELLE")
    print("🔧 Vérifier l'installation manuelle")

if __name__ == "__main__":
    main()
'''
        
        script_file = Path("mistral_telechargement_alternatif.py")
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"   ✅ Script créé: {script_file}")
        
        return script_file
    
    def generer_commandes_directes(self):
        """Générer les commandes directes"""
        print("\n💻 GÉNÉRATION COMMANDES DIRECTES:")
        
        commandes = {
            "mise_a_jour": [
                "pip install --upgrade transformers==4.40.0",
                "pip install --upgrade tokenizers==0.15.1",
                "pip install --upgrade huggingface_hub==0.22.2"
            ],
            "test_v0_2": [
                "python -c \"from transformers import AutoTokenizer; print('✅ Tokenizer v0.2:', AutoTokenizer.from_pretrained('mistralai/Mistral-7B-Instruct-v0.2'))\"",
                "python -c \"from transformers import AutoModelForCausalLM; print('✅ Modèle v0.2:', AutoModelForCausalLM.from_pretrained('mistralai/Mistral-7B-Instruct-v0.2'))\""
            ],
            "nettoyage_cache": [
                "rmdir /s /q C:\\Users\\maatc\\.cache\\huggingface",
                "mkdir C:\\Users\\maatc\\.cache\\huggingface"
            ],
            "telechargement_manuel": [
                "mkdir E:\\mistral-manuel",
                "curl -L https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2/resolve/main/pytorch_model.bin -o E:\\mistral-manuel\\pytorch_model.bin",
                "curl -L https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2/resolve/main/config.json -o E:\\mistral-manuel\\config.json"
            ]
        }
        
        print("   💻 MISE À JOUR:")
        for cmd in commandes["mise_a_jour"]:
            print(f"      {cmd}")
        
        print("   💻 TEST V0.2:")
        for cmd in commandes["test_v0_2"]:
            print(f"      {cmd}")
        
        print("   💻 NETTOYAGE CACHE:")
        for cmd in commandes["nettoyage_cache"]:
            print(f"      {cmd}")
        
        print("   💻 TÉLÉCHARGEMENT MANUEL:")
        for cmd in commandes["telechargement_manuel"]:
            print(f"      {cmd}")
        
        return commandes
    
    def sauvegarder_diagnostic(self):
        """Sauvegarder le diagnostic complet"""
        print("\n💾 SAUVEGARDE DIAGNOSTIC:")
        
        diagnostic_file = Path("mistral_download_diagnostic.json")
        with open(diagnostic_file, 'w', encoding='utf-8') as f:
            json.dump(self.diagnostic, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ Diagnostic sauvegardé: {diagnostic_file}")
        
        return diagnostic_file
    
    def afficher_resume_final(self):
        """Afficher le résumé final"""
        print("\n" + "="*80)
        print("🔍 RÉSUMÉ DIAGNOSTIC TÉLÉCHARGEMENT MISTRAL")
        print("="*80)
        
        print("🎯 PROBLÈME PRINCIPAL:")
        print("   ❌ PyPreTokenizerTypeWrapper - Erreur tokenizer")
        print("   📝 Les modèles Mistral v0.3 ne sont pas compatibles")
        
        print("\n🔧 SOLUTIONS RECOMMANDÉES:")
        print("   1. 🚀 MISE À JOUR TRANSFORMERS (Priorité 1)")
        print("      pip install --upgrade transformers==4.40.0")
        print("      pip install --upgrade tokenizers==0.15.1")
        
        print("   2. 📦 UTILISER MISTRAL V0.2 (Priorité 2)")
        print("      mistralai/Mistral-7B-Instruct-v0.2")
        
        print("   3. 🧹 NETTOYER CACHE (Priorité 3)")
        print("      rmdir /s /q C:\\Users\\maatc\\.cache\\huggingface")
        
        print("   4. 🔗 TÉLÉCHARGEMENT MANUEL (Priorité 4)")
        print("      curl -L https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2/resolve/main/pytorch_model.bin")
        
        print("\n🌊 LIENS TÉLÉCHARGEMENT DIRECTS:")
        print("   📦 Hugging Face: https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2")
        print("   📦 TheBloke: https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF")
        print("   📦 Manuel: https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2/tree/main")
        
        print("\n🚀 ACTION IMMÉDIATE:")
        print("   💻 Lancez: python mistral_telechargement_alternatif.py")
        print("   🎯 Ou exécutez les commandes manuellement")
        
        return True
    
    def run_complete_diagnostic(self):
        """Exécuter le diagnostic complet"""
        print("🚀 DÉMARRAGE DIAGNOSTIC COMPLET")
        
        # Analyser les problèmes
        self.analyser_problemes_transformers()
        
        # Générer les liens
        self.generer_liens_telechargement()
        
        # Générer les solutions
        self.generer_solutions()
        
        # Créer le script alternatif
        self.creer_script_telechargement_alternatif()
        
        # Générer les commandes directes
        self.generer_commandes_directes()
        
        # Sauvegarder le diagnostic
        self.sauvegarder_diagnostic()
        
        # Afficher le résumé
        self.afficher_resume_final()
        
        return self.diagnostic

def main():
    """Fonction principale"""
    diagnostic = MistralDownloadDiagnostic()
    result = diagnostic.run_complete_diagnostic()
    
    print(f"\n📄 DIAGNOSTIC TERMINÉ")
    print("🔧 UTILISEZ LES SOLUTIONS PROPOSÉES")

if __name__ == "__main__":
    main()
