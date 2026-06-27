#!/usr/bin/env python3
"""
GUIDE POUR TROUVER "Programmatic access"
Localisation exacte de l'option dans l'interface AWS
"""

import webbrowser

def create_programmatic_access_guide():
    """Crée un guide détaillé pour trouver Programmatic access"""
    
    guide = """# 🔍 GUIDE POUR TROUVER "Programmatic access"

## 📍 **Où SE TROUVE L'OPTION**

### **🎯 LOCALISATION EXACTE**

L'option "Programmatic access" se trouve dans la page de **création de clé d'accès**, PAS dans la création d'utilisateur.

---

## 🔄 **PROCESSUS CORRECT**

### **ÉTAPE 1: CRÉER L'UTILISATEUR (SANS TYPE D'ACCÈS)**
```
IAM → Users → Create user
┌─────────────────────────────────────────┐
│ User details                            │
├─────────────────────────────────────────┤
│ User name: [harmonic-ai-user]           │
│                                         │
│ ☐ Provide user permissions             │
│ ☑️ [X]                                   │
│                                         │
│ [Next: Permissions]                    │
└─────────────────────────────────────────┘
```

### **ÉTAPE 2: CONFIGURER PERMISSIONS**
```
Set permissions
┌─────────────────────────────────────────┐
│ ● Attach policies directly              │
│ ☐ HarmonAI-S3-Policy ← COCHEZ         │
│                                         │
│ [Next: Tags] → [Next: Review]        │
│ [Create user]                         │
└─────────────────────────────────────────┘
```

### **ÉTAPE 3: CRÉER LA CLÉ D'ACCÈS (OÙ SE TROUVE "Programmatic access")**
```
harmonic-ai-user → Security credentials → Create access key
┌─────────────────────────────────────────┐
│ Create access key                       │
├─────────────────────────────────────────┤
│ Access key type:                        │
│                                         │
│ ○ Access key - CLI                      │
│ ● Access key - Programmatic access ← ICI! │
│                                         │
│ Description:                            │
│ [Harmonic AI S3 access]                 │
│                                         │
│ [Create access key]                     │
└─────────────────────────────────────────┘
```

---

## 🔍 **NAVIGATION DÉTAILLÉE**

### **Étape A: Créer l'utilisateur**
1. **IAM** → **Users** → **Create user**
2. **User name**: `harmonic-ai-user`
3. **Next: Permissions**
4. **Attach policies directly**
5. **Cherchez**: `HarmonicAI-S3-Policy`
6. **Cochez** la politique
7. **Next: Tags** → **Next: Review** → **Create user**

### **Étape B: Créer la clé d'accès**
8. **Retour à Users** → **harmonic-ai-user**
9. **Onglet Security credentials**
10. **Create access key** (bouton)
11. **C'est ICI** que vous trouverez "Programmatic access"

---

## 🎯 **CAPTURES D'ÉCRAN VIRTUELLES**

### **Page 1: Création utilisateur (PAS de "Programmatic access" ici)**
```
Create user
┌─────────────────────────────────────────┐
│ User details                            │
├─────────────────────────────────────────┤
│ User name: [harmonic-ai-user]           │
│                                         │
│ ☐ Provide user permissions             │
│ ☑️ [X]                                   │
│                                         │
│ [Next: Permissions]                    │
└─────────────────────────────────────────┘
```

### **Page 2: Permissions (PAS de "Programmatic access" ici)**
```
Set permissions
┌─────────────────────────────────────────┐
│ ● Attach policies directly              │
│ ☐ HarmonAI-S3-Policy                 │
│                                         │
│ [Next: Tags]                           │
└─────────────────────────────────────────┘
```

### **Page 3: Clé d'accès (C'EST ICI!)**
```
Create access key
┌─────────────────────────────────────────┐
│ Access key type:                        │
├─────────────────────────────────────────┤
│ ○ Access key - CLI                      │
│ ● Access key - Programmatic access ← ICI! │
│                                         │
│ Description:                            │
│ [Harmonic AI S3 access]                 │
│                                         │
│ [Create access key]                     │
└─────────────────────────────────────────┘
```

---

## 🔗 **LIENS DIRECTS**

### **Navigation précise:**
1. **Création utilisateur**: https://console.aws.amazon.com/iam/home#/users$new
2. **Users**: https://console.aws.amazon.com/iam/home#/users
3. **Votre utilisateur**: https://console.aws.amazon.com/iam/home#/users/harmonic-ai-user

---

## 🚨 **POINTS IMPORTANTS**

### **❌ OÙ NE PAS CHERCHER**
- **PAS** dans "Create user" 
- **PAS** dans "Set permissions"
- **PAS** dans "Add tags"

### **✅ OÙ CHERCHER**
- **UNIQUEMENT** dans "Create access key"
- **APRÈS** avoir créé l'utilisateur
- **DANS** "Security credentials"

---

## 📋 **RÉSUMÉ DES ÉTAPES CORRECTES**

1. **IAM** → **Users** → **Create user**
2. **User name**: `harmonic-ai-user`
3. **Next: Permissions**
4. **Attach policies directly**
5. **HarmonicAI-S3-Policy** → **Cochez**
6. **Next: Tags** → **Next: Review** → **Create user**
7. **harmonic-ai-user** → **Security credentials**
8. **Create access key**
9. **Access key - Programmatic access** ← **C'EST ICI!**
10. **Create access key**
11. **Copiez** les clés

---

**🎯 "Programmatic access" se trouve UNIQUEMENT dans la création de clé d'accès!**
"""
    
    with open("FIND_PROGRAMMATIC_ACCESS_GUIDE.md", 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print("✅ Guide Programmatic access créé: FIND_PROGRAMMATIC_ACCESS_GUIDE.md")

def open_user_page():
    """Ouvre la page de l'utilisateur"""
    
    print("\n🌐 OUVERTURE PAGE UTILISATEUR...")
    print("   Navigation vers: IAM → Users → harmonic-ai-user")
    
    webbrowser.open("https://console.aws.amazon.com/iam/home#/users")
    
    print("✅ Page utilisateurs ouverte")
    print("📋 Cherchez harmonic-ai-user → Security credentials")

def main():
    """Fonction principale"""
    
    print("🔍 GUIDE POUR TROUVER 'Programmatic access'")
    print("=" * 60)
    print("📍 Localisation exacte de l'option")
    print("=" * 60)
    
    # Créer le guide
    create_programmatic_access_guide()
    
    # Ouvrir la page utilisateurs
    open_user_page()
    
    print(f"\n🎯 RÉPONSE DIRECTE:")
    print("=" * 40)
    print("❌ 'Programmatic access' N'EST PAS dans 'Create user'")
    print("✅ 'Programmatic access' EST dans 'Create access key'")
    print("📍 Navigation: harmonic-ai-user → Security credentials → Create access key")
    print("=" * 40)
    
    print(f"\n📋 ÉTAPES CORRECTES:")
    print("1. 👤 Créez l'utilisateur harmonic-ai-user")
    print("2. 🔗 Attachez HarmonicAI-S3-Policy")
    print("3. 🔐 Allez dans Security credentials")
    print("4. 🔑 Cliquez Create access key")
    print("5. 🎯 SÉLECTIONNEZ 'Access key - Programmatic access'")
    
    print(f"\n📁 Fichier créé:")
    print("   📋 FIND_PROGRAMMATIC_ACCESS_GUIDE.md")
    
    print(f"\n🌐 Page ouverte:")
    print("   https://console.aws.amazon.com/iam/home#/users")
    
    print(f"\n🎯 'Programmatic access' trouvé dans Create access key!")

if __name__ == "__main__":
    main()
