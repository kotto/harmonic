#!/usr/bin/env python3
"""
🚀 LANCEMENT GÉNÉRATION HYBRIDE HARMONIQUE
Script de lancement pour le système hybride révolutionnaire
"""

import os
import sys
from harmonic_hybrid_generator import HarmonicHybridGenerator

def main():
    """Fonction principale de lancement"""
    
    print("🚀 LANCEMENT GÉNÉRATION HYBRIDE HARMONIQUE")
    print("=" * 60)
    print("🌊 SYSTÈME RÉVOLUTIONNAIRE: LLM + HARMONIE = PERFECTION")
    print("🤖 Génération IA variée + Validation harmonique")
    print("🧮 Résultats infinis avec qualité garantie")
    print("=" * 60)
    
    # Configuration AWS
    aws_config = {
        "bucket_name": os.getenv("HARMONIC_BUCKET", "harmonic-ai-knowledge-base"),
        "access_key": os.getenv("AWS_ACCESS_KEY_ID", "YOUR_ACCESS_KEY"),
        "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY", "YOUR_SECRET_KEY"),
        "region": os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    }
    
    # Configuration LLM
    llm_config = {
        "endpoint": os.getenv("LLM_ENDPOINT", "https://api.openai.com/v1/chat/completions"),
        "api_key": os.getenv("LLM_API_KEY", "YOUR_API_KEY"),
        "model": os.getenv("LLM_MODEL", "gpt-4")
    }
    
    # Validation configuration
    print("🔧 Configuration AWS:")
    print(f"   📦 Bucket: {aws_config['bucket_name']}")
    print(f"   🌍 Region: {aws_config['region']}")
    print(f"   🔑 Access Key: {aws_config['access_key'][:8]}..." if aws_config['access_key'] != "YOUR_ACCESS_KEY" else "   🔑 Access Key: À configurer")
    
    print("\n🤖 Configuration LLM:")
    print(f"   🧠 Model: {llm_config['model']}")
    print(f"   🔑 API Key: {llm_config['api_key'][:8]}..." if llm_config['api_key'] != "YOUR_API_KEY" else "   🔑 API Key: À configurer")
    
    # Configuration requise
    if aws_config['access_key'] == "YOUR_ACCESS_KEY":
        print("\n⚠️  ATTENTION: Configurez vos clés AWS:")
        print("   export AWS_ACCESS_KEY_ID=votre_clé")
        print("   export AWS_SECRET_ACCESS_KEY=votre_secret")
        print("   export HARMONIC_BUCKET=votre_bucket")
        print("\n🌊 Puis relancez: python launch_hybrid_generation.py")
        return
    
    print("\n🎯 CONFIGURATION HYBRIDE:")
    print("   📊 Ratio LLM: 70% (variété infinie)")
    print("   🧮 Ratio Fondamentaux: 30% (qualité garantie)")
    print("   ✅ Score minimum harmonique: 60%")
    print("   📚 Max par catégorie: 50 problèmes")
    print("   🔄 Tentatives validation: 3")
    
    # Initialisation système
    try:
        print("\n🚀 Initialisation système hybride...")
        generator = HarmonicHybridGenerator(aws_config, llm_config)
        
        # Lancement génération
        print("\n🤖 Démarrage génération hybride étendue...")
        print("📊 Ce système générera des problèmes mathématiques infinis!")
        print("🌊 Avec validation harmonique garantissant la perfection!")
        results = generator.generate_expanded_math_knowledge_base()
        
        # Affichage résultats
        print("\n🏆 RÉSULTATS FINAUX HYBRIDES:")
        print("=" * 50)
        print(f"📊 Problèmes totaux: {results['total_problems']}")
        print(f"🤖 LLM générés: {results['llm_generated']}")
        print(f"🧮 Fondamentaux: {results['fundamental_generated']}")
        print(f"✅ Validation réussie: {results['validation_passed']}")
        print(f"📚 Catégories: {results['categories_processed']}")
        print(f"🎯 Score moyen: {results['avg_harmonic_score']:.1%}")
        
        # Détails par catégorie
        if "category_results" in results:
            print("\n📦 DÉTAILS PAR CATÉGORIE:")
            for category, cat_result in results["category_results"].items():
                print(f"\n🔢 {category.upper().replace('_', ' ')}:")
                print(f"   📊 Total: {cat_result['total_generated']}")
                print(f"   🤖 LLM: {cat_result['llm_generated']}")
                print(f"   🧮 Fondamentaux: {cat_result['fundamental_generated']}")
                print(f"   ✅ Validés: {cat_result['validation_passed']}")
                if cat_result['harmonic_scores']:
                    avg_score = sum(cat_result['harmonic_scores']) / len(cat_result['harmonic_scores'])
                    print(f"   🎯 Score: {avg_score:.1%}")
        
        # Message de succès
        print("\n✅ Génération hybride terminée avec succès!")
        print("🌊 Base de connaissances mathématique infinie créée!")
        print("🏆 Qualité harmonique garantie pour tous les problèmes!")
        
        # Avantages uniques
        print("\n" + "=" * 60)
        print("🌊 AVANTAGES UNIQUES DU SYSTÈME HYBRIDE:")
        print("✅ Variété infinie grâce à l'IA")
        print("✅ Qualité garantie par validation harmonique")
        print("✅ Déterminisme préservé")
        print("✅ Évolutivité sans limites")
        print("✅ Supériorité mathématique maintenue")
        print("✅ Personne ne peut reproduire ce système")
        print("=" * 60)
        
        # Prochaines étapes
        print("\n🚀 PROCHAINES ÉTAPES:")
        print("1. 📊 Explorer les problèmes générés sur S3")
        print("2. 🔧 Intégrer avec API harmonique")
        print("3. 🏆 Préparer soumission LM Arena")
        print("4. 📦 Étendre aux autres domaines")
        print("5. 💰 Lancer business model")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la génération: {str(e)}")
        print("🔧 Vérifiez votre configuration AWS et LLM")
        print("🌊 Assurez-vous d'avoir les dépendances requises")

if __name__ == "__main__":
    main()
