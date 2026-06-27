#!/usr/bin/env python3
"""
CLARIFICATION IMPORTANTE: POLITIQUE VS CLÉ D'ACCÈS
Processus correct pour créer utilisateur IAM et clé d'accès
"""

import webbrowser
import json
from pathlib import Path

def create_clarification_guide():
    """Crée un guide de clarification du processus"""
    
    guide = """# 🔍 CLARIFICATION IMPORTANTE: POLITIQUE VS CLÉ D'ACCÈS

## ❌ **ERREUR COURANTE À ÉVITER**

Vous ne verrez **JAMAIS** "Access key - Programmatic access" dans la création de politique !

### **🚨 CE QUE VOUS FAITES MAINTENANT**
```
❌ IAM → Policies → Create policy
❌ Vous cherchez "Access key - Programmatic access" 
❌ Ça n'existe pas ici !
```

---

## ✅ **PROCESSUS CORRECT EN 2 PHASES**

### **PHASE 1: CRÉER LA POLITIQUE (SANS CLÉ D'ACCÈS)**

1. **IAM** → **Policies** → **Create policy**
2. **JSON** → Collez le JSON HarmonicAI-S3-Policy
3. **Nom**: `HarmonicAI-S3-Policy`
4. **Create policy**
5. **FIN DE LA PHASE 1** - Pas de clé d'accès ici !

### **PHASE 2: CRÉER L'UTILISATEUR (AVEC CLÉ D'ACCÈS)**

1. **IAM** → **Users** → **Create user**
2. **User name**: `harmonic-ai-user`
3. **Next: Permissions**
4. **● Attach policies directly**
5. **Search**: `HarmonicAI-S3-Policy`
6. **☐ HarmonicAI-S3-Policy`
7. **Next: Tags** → **Next: Review** → **Create user**
8. **Maintenant** → **Security credentials**
9. **Create access key**
10. **● Access key - Programmatic access** ← **ICI SEULEMENT !**

---

## 📍 **OÙ TROUVER "ACCESS KEY - PROGRAMMATIC ACCESS"**

### **🎯 UNIQUEMENT DANS CETTE SÉQUENCE:**
```
IAM → Users → harmonic-ai-user → Security credentials → Create access key
```

### **❌ PAS DANS:**
```
❌ IAM → Policies → Create policy
❌ IAM → Users → Create user
❌ IAM → Users → harmonic-ai-user → Permissions
```

---

## 🔍 **ÉTAPES VISUELLES DÉTAILLÉES**

### **ÉTAPE 1: CRÉER LA POLITIQUE**
```
📍 Page: IAM → Policies → Create policy
📝 Contenu: JSON HarmonicAI-S3-Policy
🎯 Résultat: Politique créée
❌ PAS de clé d'accès ici !
```

### **ÉTAPE 2: CRÉER L'UTILISATEUR**
```
📍 Page: IAM → Users → Create user
📝 User name: harmonic-ai-user
📋 Permissions: Attach HarmonicAI-S3-Policy
🎯 Résultat: Utilisateur créé
❌ PAS de clé d'accès ici !
```

### **ÉTAPE 3: CRÉER LA CLÉ D'ACCÈS**
```
📍 Page: IAM → Users → harmonic-ai-user → Security credentials
📝 Create access key
🔑 Type: Access key - Programmatic access ← **ICI SEULEMENT !**
🎯 Résultat: Clés générées
✅ COPIEZ LES CLÉS MAINTENANT !
```

---

## 🚨 **POINTS CRITIQUES**

### **❌ ERREURS À ÉVITER**
- Chercher "Access key" dans la création de politique
- Essayer de créer des clés avant l'utilisateur
- Oublier d'attacher la politique à l'utilisateur

### **✅ BONNES PRATIQUES**
- Créer la politique **EN PREMIER**
- Créer l'utilisateur **ENSUITE**
- Créer les clés **EN DERNIER**
- Copier les clés **IMMÉDIATEMENT**

---

## 🔧 **SCRIPT AUTOMATIQUE COMPLET**

### **Option 1: AWS CLI (PLUS SIMPLE)**
```bash
# Créer la politique
aws iam create-policy \\
    --policy-name HarmonicAI-S3-Policy \\
    --policy-document file://HarmonicAI_S3_Policy.json

# Créer l'utilisateur
aws iam create-user --user-name harmonic-ai-user

# Attacher la politique
aws iam attach-user-policy \\
    --user-name harmonic-ai-user \\
    --policy-arn arn:aws:iam::ACCOUNT_ID:policy/HarmonicAI-S3-Policy

# Créer la clé d'accès
aws iam create-access-key --user-name harmonic-ai-user
```

### **Option 2: Console AWS (VISUEL)**
Suivez les 3 phases ci-dessus dans l'ordre.

---

## 📋 **CHECKLIST DE VÉRIFICATION**

### **Phase 1: Politique**
- [ ] JSON HarmonicAI-S3-Policy créé
- [ ] Politique nommée `HarmonicAI-S3-Policy`
- [ ] Politique visible dans IAM → Policies

### **Phase 2: Utilisateur**
- [ ] Utilisateur `harmonic-ai-user` créé
- [ ] Politique `HarmonicAI-S3-Policy` attachée
- [ ] Utilisateur visible dans IAM → Users

### **Phase 3: Clé d'accès**
- [ ] Security credentials → Create access key
- [ ] "Access key - Programmatic access" sélectionné
- [ ] Clés copiées et sauvegardées

---

## 🔗 **LIENS DIRECTS DANS LE BON ORDRE**

### **1. Créer la politique**
https://console.aws.amazon.com/iam/home#/policies$new

### **2. Créer l'utilisateur**
https://console.aws.amazon.com/iam/home#/users$new

### **3. Clés d'accès (après création utilisateur)**
IAM → Users → harmonic-ai-user → Security credentials

---

## 🚨 **RÉPONSE DIRECTE À VOTRE QUESTION**

### **"il faut creer une politique? car je ne vois pas type: access key"**

**RÉPONSE:**
- ✅ **OUI**, il faut d'abord créer la politique
- ❌ **NON**, vous ne verrez jamais "Access key" dans la création de politique
- 🔑 "Access key - Programmatic access" apparaît **UNIQUEMENT** dans Security credentials de l'utilisateur

### **ORDRE CORRECT:**
1. **Politique** → 2. **Utilisateur** → 3. **Clé d'accès**

---

**🔐 Processus clarifié - Plus aucune confusion !**
"""
    
    with open("IAM_PROCESS_CLARIFICATION.md", 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print("✅ Guide de clarification créé: IAM_PROCESS_CLARIFICATION.md")

def open_policy_creation_page():
    """Ouvre la page de création de politique"""
    
    print("\n🌐 OUVERTURE PAGE CRÉATION POLITIQUE...")
    print("   ÉTAPE 1: Créer la politique HarmonicAI-S3-Policy")
    
    webbrowser.open("https://console.aws.amazon.com/iam/home#/policies$new")
    
    print("✅ Page de création politique ouverte")

def show_json_policy():
    """Affiche le JSON de la politique"""
    
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:CreateBucket",
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:ListBucket",
                    "s3:DeleteObject"
                ],
                "Resource": [
                    "arn:aws:s3:::harmonic-ai-knowledge-base",
                    "arn:aws:s3:::harmonic-ai-knowledge-base/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:ListAllMyBuckets"
                ],
                "Resource": "*"
            }
        ]
    }
    
    print(f"\n📋 JSON À COPIER DANS LA CONSOLE:")
    print("=" * 50)
    print(json.dumps(policy, indent=2))
    print("=" * 50)

def main():
    """Fonction principale"""
    
    print("🔍 CLARIFICATION IMPORTANTE: POLITIQUE VS CLÉ D'ACCÈS")
    print("=" * 60)
    print("❌ Vous ne verrez JAMAIS 'Access key' dans la création de politique")
    print("✅ Processus correct: 1. Politique → 2. Utilisateur → 3. Clé")
    print("=" * 60)
    
    # Créer le guide de clarification
    create_clarification_guide()
    
    # Afficher le JSON
    show_json_policy()
    
    # Ouvrir la bonne page
    open_policy_creation_page()
    
    print(f"\n🎯 RÉPONSE DIRECTE:")
    print("=" * 40)
    print("❌ 'Access key - Programmatic access'")
    print("   N'EXISTE PAS dans la création de politique")
    print()
    print("✅ ORDRE CORRECT:")
    print("   1. Créer la politique (sans clé)")
    print("   2. Créer l'utilisateur (avec politique)")
    print("   3. Créer la clé (dans Security credentials)")
    print("=" * 40)
    
    print(f"\n📍 OÙ TROUVER 'ACCESS KEY - PROGRAMMATIC ACCESS':")
    print("   IAM → Users → harmonic-ai-user → Security credentials → Create access key")
    print("   (UNIQUEMENT APRÈS avoir créé l'utilisateur !)")
    
    print(f"\n📋 FICHIER CRÉÉ:")
    print("   📚 IAM_PROCESS_CLARIFICATION.md")
    
    print(f"\n🌐 PAGE OUVERTE:")
    print("   https://console.aws.amazon.com/iam/home#/policies$new")
    
    print(f"\n🔐 Processus clarifié - Suivez les 3 étapes dans l'ordre !")

if __name__ == "__main__":
    main()
