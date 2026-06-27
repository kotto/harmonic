#!/usr/bin/env python3
"""
🚀 LANCEMENT GÉNÉRATION VISUELLE HARMONIQUE
Script de lancement pour déploiement AWS S3
"""

import os
import sys
from harmonic_s3_visual_system import HarmonicS3VisualSystem

def main():
    """Fonction principale de lancement"""
    
    print("🌊 LANCEMENT GÉNÉRATION VISUELLE HARMONIQUE")
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
        return
    
    # Initialisation système
    try:
        print("\n🚀 Initialisation système S3 harmonique...")
        system = HarmonicS3VisualSystem(aws_config)
        
        # Lancement génération
        print("\n🎨 Démarrage génération base visuelle...")
        results = system.create_complete_visual_knowledge_base()
        
        # Affichage résultats
        print("\n🏆 RÉSULTATS FINAUX:")
        print("=" * 40)
        print(f"📊 Assets créés: {results['total_assets']}")
        print(f"🗄️ Objets S3: {results['s3_objects_created']}")
        print(f"📦 Batches: {results['batches_processed']}")
        
        # Détails par batch
        if "batch_results" in results:
            for batch_name, batch_result in results["batch_results"].items():
                print(f"\n📦 {batch_name.upper()}:")
                print(f"   📊 Assets: {batch_result['assets_created']}")
        
        print("\n✅ Génération visuelle terminée avec succès!")
        print("🌊 Base de connaissances harmonique disponible sur S3")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la génération: {str(e)}")
        print("🔧 Vérifiez votre configuration AWS et les permissions S3")

if __name__ == "__main__":
    main()
