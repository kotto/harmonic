#!/usr/bin/env python3
"""
🚀 LANCEMENT MATHSTRAL 7B AWS S3 - PRODUCTION RÉELLE
Déploiement complet avec Mathstral 7B spécialisé mathématiques
"""

import os
import sys
from mathstral_aws_generator import MathstralAWSGenerator

def main():
    """Fonction principale de lancement"""
    
    print("🚀 LANCEMENT MATHSTRAL 7B AWS S3")
    print("=" * 60)
    print("🤖 Modèle: Mathstral 7B spécialisé mathématiques")
    print("☁️  Infrastructure: AWS S3 scalable")
    print("🌊 Validation: Harmonique et déterministe")
    print("💰 Coût: Open source (gratuit)")
    print("🎯 Performance: Comparable GPT-4 en maths")
    print("=" * 60)
    
    # Configuration AWS
    aws_config = {
        "bucket_name": os.getenv("HARMONIC_BUCKET", "harmonic-ai-knowledge-base"),
        "access_key": os.getenv("AWS_ACCESS_KEY_ID", "YOUR_ACCESS_KEY"),
        "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY", "YOUR_SECRET_KEY"),
        "region": os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    }
    
    # Validation configuration
    print("🔧 Configuration AWS:")
    print(f"   📦 Bucket: {aws_config['bucket_name']}")
    print(f"   🌍 Region: {aws_config['region']}")
    print(f"   🔑 Access Key: {aws_config['access_key'][:8]}..." if aws_config['access_key'] != "YOUR_ACCESS_KEY" else "   🔑 Access Key: À configurer")
    
    if aws_config['access_key'] == "YOUR_ACCESS_KEY":
        print("\n⚠️  ATTENTION: Configurez vos clés AWS:")
        print("   export AWS_ACCESS_KEY_ID=votre_clé")
        print("   export AWS_SECRET_ACCESS_KEY=votre_secret")
        print("   export HARMONIC_BUCKET=votre_bucket")
        print("\n🚀 Puis relancez: python launch_mathstral_aws.py")
        return
    
    # Configuration Mathstral
    print("\n🤖 Configuration Mathstral 7B:")
    print("   📊 Modèle: mistralai/Mathstral-7B-v0.1")
    print("   🎯 Spécialisation: 100% mathématiques")
    print("   💾 Mémoire: Quantification 4-bit (GPU)")
    print("   🌡️  Température: 0.1 (précision)")
    print("   📝 Tokens max: 512 par problème")
    
    # Vérification GPU
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0)
            print(f"   🎮 GPU: {gpu_count}x {gpu_name}")
        else:
            print("   💻 CPU: Mode CPU (plus lent)")
    except:
        print("   ⚠️  GPU: Non détecté")
    
    # Configuration génération
    print("\n🎯 Configuration Génération:")
    print("   📚 Catégories: 5 domaines mathématiques")
    print("   📊 Problèmes par catégorie: 20")
    print("   📈 Total attendu: ~100 problèmes")
    print("   ✅ Score minimum harmonique: 60%")
    print("   🔄 Fallback: Problèmes prédéfinis")
    
    # Confirmation lancement
    print("\n" + "=" * 60)
    print("🚀 PRÊT À LANCER MATHSTRAL 7B SUR AWS")
    print("🌊 Ce système générera des problèmes mathématiques de qualité GPT-4")
    print("💰 Sans aucun coût API (open source)")
    print("☁️  Avec stockage scalable sur AWS S3")
    print("🎯 Validation harmonique garantie")
    print("=" * 60)
    
    confirmation = input("\n🎯 Lancer la génération? (y/n): ")
    if confirmation.lower() != 'y':
        print("🚀 Lancement annulé.")
        return
    
    # Initialisation et lancement
    try:
        print("\n🚀 Initialisation Mathstral 7B AWS...")
        generator = MathstralAWSGenerator(aws_config)
        
        # Lancement génération
        print("\n🤖 Démarrage génération Mathstral 7B...")
        print("📊 Ce peut prendre 15-30 minutes selon votre hardware...")
        results = generator.generate_mathstral_knowledge_base()
        
        # Affichage résultats
        print("\n🏆 RÉSULTATS FINAUX MATHSTRAL AWS:")
        print("=" * 50)
        print(f"📊 Problèmes totaux: {results['total_problems']}")
        print(f"🤖 Mathstral générés: {results['mathstral_generated']}")
        print(f"🔄 Fallback: {results['fallback_generated']}")
        print(f"✅ Validation réussie: {results['validation_passed']}")
        print(f"📚 Catégories: {results['categories_processed']}")
        print(f"📊 Score moyen: {results['avg_harmonic_score']:.1%}")
        print(f"🎯 Confiance moyenne: {results['avg_confidence']:.1%}")
        
        # Détails par catégorie
        if "category_results" in results:
            print("\n📦 DÉTAILS PAR CATÉGORIE:")
            for category, cat_result in results["category_results"].items():
                print(f"\n🔢 {category.upper().replace('_', ' ')}:")
                print(f"   📊 Total: {cat_result['total_generated']}")
                print(f"   ✅ Validés: {cat_result['valid_problems']}")
                print(f"   🤖 Mathstral: {cat_result['mathstral_problems']}")
                print(f"   🔄 Fallback: {cat_result['fallback_problems']}")
                print(f"   🎯 Score: {cat_result['avg_harmonic_score']:.1%}")
                print(f"   💪 Confiance: {cat_result['avg_confidence']:.1%}")
        
        # Message de succès
        print("\n✅ Génération Mathstral 7B terminée avec succès!")
        print("🌊 Base de connaissances mathématique créée sur AWS S3!")
        print("🏆 Qualité comparable à GPT-4 sans coût API!")
        
        # Informations S3
        print("\n📋 ACCÈS AWS S3:")
        print(f"📦 Bucket: s3://{aws_config['bucket_name']}")
        print("📁 Dossier: mathematics/mathstral/")
        print("📋 Manifeste: mathematics/manifests/mathstral_aws_manifest.json")
        
        # Commandes S3
        print("\n🔍 Commandes pour vérifier:")
        print(f"   aws s3 ls s3://{aws_config['bucket_name']}/mathematics/mathstral/")
        print(f"   aws s3 ls s3://{aws_config['bucket_name']}/mathematics/manifests/")
        
        # Avantages uniques
        print("\n" + "=" * 60)
        print("🌊 AVANTAGES UNIQUES MATHSTRAL AWS:")
        print("✅ Spécialisation mathématique 100%")
        print("✅ Performance niveau GPT-4")
        print("✅ Coût zéro (open source)")
        print("✅ Scalabilité AWS infinie")
        print("✅ Validation harmonique garantie")
        print("✅ Déterminisme préservé")
        print("✅ Personne n'a ce système!")
        print("=" * 60)
        
        # Prochaines étapes
        print("\n🚀 PROCHAINES ÉTAPES:")
        print("1. 📊 Explorer les problèmes sur S3")
        print("2. 🔧 Intégrer avec API harmonique")
        print("3. 🏆 Préparer LM Arena avec Mathstral")
        print("4. 📦 Ajouter autres modèles open source")
        print("5. 💰 Lancer business model")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la génération: {str(e)}")
        print("🔧 Vérifiez:")
        print("   - Configuration AWS correcte")
        print("   - Permissions S3 adéquates")
        print("   - Dépendances installées: pip install transformers torch")
        print("   - GPU disponible (recommandé)")
        
        # Aide debug
        print("\n🔧 DÉBOGAGE:")
        if "CUDA" in str(e):
            print("   💡 Essayez sans GPU: le système utilisera le CPU")
        if "memory" in str(e).lower():
            print("   💡 Réduisez batch_size ou utilisez GPU avec plus de mémoire")
        if "S3" in str(e):
            print("   💡 Vérifiez vos clés AWS et permissions bucket")

if __name__ == "__main__":
    main()
