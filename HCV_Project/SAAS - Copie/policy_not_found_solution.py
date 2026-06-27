#!/usr/bin/env python3
"""
SOLUTION QUAND LA POLITIQUE N'EST PAS TROUVÉE
"Aucune correspondance" - La politique n'existe pas encore
"""

import webbrowser
import json
from pathlib import Path

def create_policy_creation_solution():
    """Crée un guide de solution complète"""
    
    solution = """# 🚨 SOLUTION: POLITIQUE NON TROUVÉE

## 📋 **DIAGNOSTIC**

Vous avez cherché `HarmonicAI-S3-Policy` et obtenu:
```
❌ Aucune correspondance
📊 0 correspondances
```

**Conclusion**: La politique n'existe pas encore - il faut la créer.

---

## 🔧 **SOLUTION IMMÉDIATE: CRÉER LA POLITIQUE**

### 🎯 **MÉTHODE 1: CRÉATION RAPIDE (RECOMMANDÉE)**

#### **Étape 1: Créer la politique**
1. **Cliquez sur** **"Créer une politique"** (bouton en haut)
2. **Sélectionnez** l'onglet **JSON**
3. **Copiez-collez** ce JSON:

```json
{
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
```

#### **Étape 2: Configuration**
4. **Cliquez sur** **Next: Tags**
5. **Cliquez sur** **Next: Review**
6. **Nom**: `HarmonicAI-S3-Policy`
7. **Description**: `Politique S3 limitée pour Harmonic AI bucket uniquement`
8. **Cliquez sur** **Create policy**

---

### 🎯 **MÉTHODE 2: LIEN DIRECT**

**Lien direct vers création**: https://console.aws.amazon.com/iam/home#/policies$new

1. **Collez le JSON** ci-dessus
2. **Nommez**: `HarmonicAI-S3-Policy`
3. **Créez** la politique

---

### 🎯 **MÉTHODE 3: AWS CLI**

```bash
# Créer le fichier politique
cat > harmonic-ai-s3-policy.json << 'EOF'
{
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
EOF

# Créer la politique
aws iam create-policy \\
    --policy-name HarmonicAI-S3-Policy \\
    --policy-document file://harmonic-ai-s3-policy.json
```

---

## ✅ **VÉRIFICATION APRÈS CRÉATION**

### **Retournez à la liste des politiques:**
1. **IAM** → **Policies**
2. **Recherchez**: `HarmonicAI-S3-Policy`
3. **Résultat attendu**:
```
┌─────────────────────────────────────────┐
│ HarmonicAI-S3-Policy                    │
│ Customer managed                        │
│ Politique S3 limitée pour Harmonic AI   │
│                                         │
│ ☑️ [ ]                                   │
│ 📝 [Modifier] 🗑️ [Supprimer]             │
└─────────────────────────────────────────┘
```

---

## 🔄 **PROCHAINES ÉTAPES**

Une fois la politique créée:

### **Étape 1: Créer l'utilisateur**
1. **IAM** → **Users** → **Create user**
2. **User name**: `harmonic-ai-user`
3. **Next: Permissions**

### **Étape 2: Attacher la politique**
4. **● Attach policies directly**
5. **Search**: `HarmonicAI-S3-Policy`
6. **☐ HarmonicAI-S3-Policy** ← **COCHEZ**
7. **Next: Tags** → **Next: Review** → **Create user**

### **Étape 3: Créer la clé d'accès**
8. **harmonic-ai-user** → **Security credentials**
9. **Create access key**
10. **● Access key - Programmatic access**
11. **Create access key**
12. **Copiez** les clés

---

## 🔗 **LIENS UTILES**

### **Création politique**
- **Direct**: https://console.aws.amazon.com/iam/home#/policies$new
- **Liste**: https://console.aws.amazon.com/iam/home#/policies

### **Création utilisateur**
- **Direct**: https://console.aws.amazon.com/iam/home#/users$new
- **Liste**: https://console.aws.amazon.com/iam/home#/users

---

## 🚨 **POINTS IMPORTANTS**

- **"Aucune correspondance"** = Normal, la politique n'existe pas encore
- **"Créer une politique"** = Bouton bleu en haut de la page
- **JSON** = Onglet à sélectionner pour coller la politique
- **Nom exact** = `HarmonicAI-S3-Policy` (sensible à la casse)

---

## 📊 **RÉSUMÉ RAPIDE**

1. **🔧 Créez** la politique avec le JSON fourni
2. **✅ Vérifiez** qu'elle apparaît dans la liste
3. **👤 Créez** l'utilisateur `harmonic-ai-user`
4. **🔗 Attachez** la politique à l'utilisateur
5. **🔑 Créez** la clé d'accès programmatique

---

**🚀 Solution complète: politique créée → utilisateur prêt → upload sécurisé !**
"""
    
    with open("POLICY_CREATION_SOLUTION.md", 'w', encoding='utf-8') as f:
        f.write(solution)
    
    print("✅ Guide solution créé: POLICY_CREATION_SOLUTION.md")

def create_policy_json_file():
    """Crée le fichier JSON prêt à copier"""
    
    policy_json = {
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
    
    with open("HarmonicAI_S3_Policy_Ready.json", 'w') as f:
        json.dump(policy_json, f, indent=2)
    
    print("✅ Fichier JSON prêt créé: HarmonAI_S3_Policy_Ready.json")

def open_policy_creation_page():
    """Ouvre directement la page de création de politique"""
    
    print("\n🌐 OUVERTURE PAGE CRÉATION POLITIQUE...")
    print("   Navigation vers: IAM → Policies → Create policy")
    
    # Ouvre la page de création de politique
    webbrowser.open("https://console.aws.amazon.com/iam/home#/policies$new")
    
    print("✅ Page de création politique ouverte")

def main():
    """Fonction principale"""
    
    print("🚨 SOLUTION: POLITIQUE NON TROUVÉE")
    print("=" * 60)
    print("❌ 'Aucune correspondance' - La politique n'existe pas")
    print("🔧 Solution: Il faut créer la politique")
    print("=" * 60)
    
    # Créer la solution
    create_policy_creation_solution()
    
    # Créer le fichier JSON
    create_policy_json_file()
    
    # Ouvrir la page de création
    open_policy_creation_page()
    
    print(f"\n🎯 DIAGNOSTIC RAPIDE:")
    print("=" * 40)
    print("❌ Résultat: 'Aucune correspondance'")
    print("📊 Cause: La politique n'existe pas encore")
    print("🔧 Solution: Créer la politique maintenant")
    print("=" * 40)
    
    print(f"\n📋 ÉTAPES IMMÉDIATES:")
    print("1. 🌐 Page création ouverte")
    print("2. 📝 Copiez le JSON depuis HarmonAI_S3_Policy_Ready.json")
    print("3. 🔧 Collez dans l'onglet JSON")
    print("4. ✅ Nommez: HarmonAI-S3-Policy")
    print("5. 🚀 Créez la politique")
    
    print(f"\n📁 Fichiers créés:")
    print("   📋 POLICY_CREATION_SOLUTION.md")
    print("   📄 HarmonAI_S3_Policy_Ready.json")
    
    print(f"\n🌐 Page ouverte:")
    print("   https://console.aws.amazon.com/iam/home#/policies$new")
    
    print(f"\n🚀 La politique sera créée en 2 minutes !")

if __name__ == "__main__":
    main()
