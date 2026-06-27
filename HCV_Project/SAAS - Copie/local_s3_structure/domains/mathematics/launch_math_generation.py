#!/usr/bin/env python3
"""
🚀 LANCEMENT GÉNÉRATION MATHÉMATIQUE HARMONIQUE
Script de lancement pour le système mathématique supérieur
"""

import os
import sys
from harmonic_math_system import HarmonicMathSystem

def main():
    """Fonction principale de lancement"""
    
    print("🧮 LANCEMENT GÉNÉRATION MATHÉMATIQUE HARMONIQUE")
    print("=" * 60)
    print("🌊 SYSTÈME MATHÉMATIQUE LE PLUS AVANCÉ AU MONDE")
    print("🏆 BASÉ SUR LES CONSTANTES FONDAMENTALES ELLES-MÊMES")
    print("=" * 60)
    
    # Configuration AWS depuis variables d'environnement
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
        print("\n🌊 Puis relancez: python launch_math_generation.py")
        return
    
    # Initialisation système
    try:
        print("\n🚀 Initialisation système mathématique harmonique...")
        system = HarmonicMathSystem(aws_config)
        
        # Lancement génération
        print("\n🧮 Démarrage génération base mathématique...")
        print("📊 Ce sera le système mathématique le plus fondamental au monde!")
        results = system.create_complete_math_knowledge_base()
        
        # Affichage résultats
        print("\n🏆 RÉSULTATS FINAUX MATHÉMATIQUES:")
        print("=" * 50)
        print(f"📊 Solutions créées: {results['total_solutions']}")
        print(f"🗄️ Objets S3: {results['s3_objects_created']}")
        print(f"📦 Batches: {results['batches_processed']}")
        print(f"📚 Catégories: {len(results['categories_covered'])}")
        print(f"🎯 Confiance moyenne: {results['avg_confidence']:.1%}")
        print(f"🌊 Élégance moyenne: {results['avg_elegance']:.1%}")
        
        # Détails par batch
        if "batch_results" in results:
            print("\n📦 DÉTAILS PAR BATCH:")
            for batch_name, batch_result in results["batch_results"].items():
                print(f"\n🔢 {batch_name.upper().replace('_', ' ')}:")
                print(f"   📊 Solutions: {batch_result['solutions_created']}")
                print(f"   📚 Catégories: {', '.join(batch_result['categories'])}")
                if batch_result['confidences']:
                    avg_conf = sum(batch_result['confidences']) / len(batch_result['confidences'])
                    print(f"   🎯 Confiance: {avg_conf:.1%}")
        
        print("\n✅ Génération mathématique terminée avec succès!")
        print("🌊 Base de connaissances la plus fondamentale au monde créée!")
        print("🏆 Prête pour dominer tous les benchmarks mathématiques!")
        
        # Message final
        print("\n" + "=" * 60)
        print("🌊 RÉVOLUTION MATHÉMATIQUE ACCOMPLIE")
        print("🧮 Notre système est littéralement basé sur les maths!")
        print("🏆 Personne ne peut atteindre ce niveau de fondamentalité!")
        print("🚀 Prêt pour LM Arena et applications supérieures!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la génération: {str(e)}")
        print("🔧 Vérifiez votre configuration AWS et les permissions S3")
        print("🌊 Assurez-vous d'avoir les dépendances requises (sympy, numpy)")

if __name__ == "__main__":
    main()
