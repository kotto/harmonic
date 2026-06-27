#!/usr/bin/env python3
"""
COMPLÉTION CONFIGURATION IAM - VERSION CORRIGÉE
Guide étape par étape pour créer l'utilisateur harmonic-ai-user
"""

import webbrowser

def main():
    """Fonction principale"""
    
    print("🚀 COMPLÉTION CONFIGURATION IAM")
    print("=" * 60)
    print("✅ Politique HarmonAI-S3-Policy créée!")
    print("🔧 Création de l'utilisateur harmonic-ai-user")
    print("=" * 60)
    
    # Créer le guide simple
    guide = """# 🚀 GUIDE CRÉATION UTILISATEUR IAM

## ✅ ÉTAT ACTUEL
🎉 Politique HarmonAI-S3-Policy créée avec succès!

## 👤 ÉTAPES À EFFECTUER

### 1. CRÉATION UTILISATEUR
1. Allez sur: https://console.aws.amazon.com/iam/home#/users$new
2. User name: harmonic-ai-user
3. Cochez "Provide user permissions"
4. Next: Permissions

### 2. PERMISSIONS
5. Sélectionnez "Attach policies directly"
6. Cherchez: HarmonAI-S3-Policy
7. Cochez la politique
8. Next: Tags → Next: Review → Create user

### 3. CLÉ D'ACCÈS
9. Cliquez sur harmonic-ai-user
10. Onglet Security credentials
11. Create access key
12. Sélectionnez "Access key - Programmatic access"
13. Create access key
14. COPIEZ IMMÉDIATEMENT les deux clés!

### 4. CONFIGURATION
15. Exécutez: python configure_aws_keys.py
16. Entrez vos clés
17. Test: python test_aws_credentials.py
18. Upload: python secure_upload_to_s3.py

## 🔗 LIENS UTILES
- Création utilisateur: https://console.aws.amazon.com/iam/home#/users$new
- Liste utilisateurs: https://console.aws.amazon.com/iam/home#/users

## 🚨 POINTS CRUCIAUX
- Copiez les clés immédiatement (elles ne s'affichent qu'une fois)
- Sauvegardez les clés dans un endroit sécurisé
- Utilisez toujours l'utilisateur IAM (jamais les clés racines)
"""
    
    with open("CREATE_IAM_USER_GUIDE.md", 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print("✅ Guide créé: CREATE_IAM_USER_GUIDE.md")
    
    # Ouvrir la page de création utilisateur
    print("\n🌐 OUVERTURE PAGE CRÉATION UTILISATEUR...")
    webbrowser.open("https://console.aws.amazon.com/iam/home#/users$new")
    print("✅ Page création utilisateur ouverte")
    
    print(f"\n🎯 RÉSUMÉ RAPIDE:")
    print("=" * 40)
    print("1. 🌐 Page ouverte: Création utilisateur")
    print("2. 👤 Nom: harmonic-ai-user")
    print("3. 🔗 Politique: HarmonAI-S3-Policy")
    print("4. 🔑 Type: Programmatic access")
    print("5. 📋 Copiez les clés")
    print("6. 🔧 Configurez: python configure_aws_keys.py")
    print("7. 🧪 Testez: python test_aws_credentials.py")
    print("8. 🚀 Uploadez: python secure_upload_to_s3.py")
    print("=" * 40)
    
    print(f"\n📁 Fichier créé:")
    print("   📋 CREATE_IAM_USER_GUIDE.md")
    
    print(f"\n🌐 Liens:")
    print("   Création: https://console.aws.amazon.com/iam/home#/users$new")
    print("   Liste: https://console.aws.amazon.com/iam/home#/users")
    
    print(f"\n🎉 Suivez le guide - configuration en 8 étapes!")
    print("🔐 Utilisateur sécurisé prêt pour Harmonic AI!")

if __name__ == "__main__":
    main()
