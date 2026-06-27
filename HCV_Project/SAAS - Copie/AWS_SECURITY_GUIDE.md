# 🔐 GUIDE SÉCURITÉ AWS POUR HARMONIC AI

## 🚨 **POURQUOI PAS DE CLÉS RACINES ?**

### ❌ **RISQUES DES CLÉS RACINES**
- Permissions illimitées sur TOUT votre compte AWS
- Impossible de restreindre l'accès
- Risque de sécurité maximal
- Pas d'audit possible
- Responsabilité infinie en cas de compromission

### ✅ **SOLUTION UTILISATEUR IAM**
- Permissions limitées et contrôlées
- Audit complet des actions
- Révocation instantanée possible
- Responsabilité limitée au bucket S3

## 🔐 **MÉTHODE SÉCURISÉE RECOMMANDÉE**

### 1️⃣ **CRÉATION UTILISATEUR IAM DÉDIÉ**

1. **Console AWS** → **IAM** → **Users** → **Create user**
2. **Nom**: `harmonic-ai-user`
3. **Type**: "Access key - Programmatic access"
4. **Permissions**: "Attach policies directly"

### 2️⃣ **POLITIQUE S3 LIMITÉE**

Créez cette politique personnalisée:

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

### 3️⃣ **ÉTAPES DANS LA CONSOLE**

1. **IAM** → **Policies** → **Create policy**
2. **JSON** → Collez la politique ci-dessus
3. **Nom**: `HarmonicAI-S3-Policy`
4. **Create policy**

5. **IAM** → **Users** → **harmonic-ai-user**
6. **Add permissions** → **Attach existing policies directly**
7. **Recherchez**: `HarmonicAI-S3-Policy`
8. **Attach policy**

### 4️⃣ **GÉNÉRATION SÉCURISÉE**

1. **IAM** → **Users** → **harmonic-ai-user**
2. **Security credentials** → **Create access key**
3. **Use case**: "Command Line Interface (CLI)"
4. **Acknowledge** → **Create access key**
5. **Copiez** l'Access Key ID et Secret Access Key

## 🔑 **MÉTHODES DE CONNEXION SÉCURISÉES**

### **MÉTHODE 1: AWS CLI SSO (RECOMMANDÉ)**
```bash
# Installation AWS CLI si nécessaire
pip install awscli

# Connexion SSO
aws sso login --profile harmonic-ai

# Configuration du profil
aws configure set profile.harmonic-ai.region us-east-1

# Upload sécurisé
python secure_upload_to_s3.py
```

### **MÉTHODE 2: Variables d'environnement (TEMPORAIRE)**
```powershell
# PowerShell
$env:AWS_ACCESS_KEY_ID = "VOTRE_CLÉ_IAM"
$env:AWS_SECRET_ACCESS_KEY = "VOTRE_SECRET_IAM"
$env:AWS_DEFAULT_REGION = "us-east-1"
$env:AWS_REGION = "us-east-1"

# Test
python secure_upload_to_s3.py
```

### **MÉTHODE 3: Fichier credentials (LIMITÉ)**
```ini
# ~/.aws/credentials
[harmonic-ai]
aws_access_key_id = VOTRE_CLÉ_IAM
aws_secret_access_key = VOTRE_SECRET_IAM
```

## 🛡️ **BONNES PRATIQUES DE SÉCURITÉ**

### **Rotation des clés**
- 🔄 Changez les clés tous les 90 jours maximum
- 📅 Configurez des rappels automatiques
- 🗑️ Supprimez immédiatement les anciennes clés

### **Monitoring**
- 📊 Activez AWS CloudTrail
- 🔔 Configurez des alertes CloudWatch
- 📋 Vérifiez les logs régulièrement

### **Restrictions réseau**
- 🌐 Utilisez VPC endpoints si possible
- 🔒 Limitez les adresses IP autorisées
- 🛡️ Configurez des security groups

### **Audit régulier**
- 🔍 Revoyez les permissions IAM mensuellement
- 📊 Analysez les logs d'accès S3
- 🚨 Surveillez les activités suspectes

## 🚀 **UPLOAD SÉCURISÉ**

Une fois l'utilisateur IAM configuré:

```bash
# Test de connexion
python secure_upload_to_s3.py

# Résultat attendu
✅ Session S3 sécurisée initialisée (profil: harmonic-ai)
✅ Bucket 'harmonic-ai-knowledge-base' accessible
🏆 UPLOAD SÉCURISÉ TERMINÉ!
```

## 📊 **CE QUI SERA UPLOADÉ (SÉCURISÉ)**

```
📦 harmonic-ai-knowledge-base/
├── 🏗️ foundation/ (3 fichiers)
├── ⚙️ core/ (7 fichiers)
├── 🌐 api/ (1 fichier)
├── 🚀 deployment/ (5 fichiers)
├── 🧮 domains/ (26 fichiers)
├── 📊 structured_data/ (24 fichiers)
├── 🌊 simple_real_output/ (24 fichiers)
├── 🔧 real_structured_data/ (16 fichiers)
└── 📋 reports/ (8 fichiers)
```

## 🔐 **MANIFESTE DE SÉCURITÉ**

L'upload sécurisé crée automatiquement:
```json
{
    "security_profile": "harmonic-ai",
    "permissions": [
        "s3:CreateBucket",
        "s3:PutObject", 
        "s3:GetObject",
        "s3:ListBucket",
        "s3:DeleteObject"
    ],
    "security_level": "IAM_USER_RESTRICTED",
    "root_access_denied": true
}
```

## 📞 **EN CAS DE PROBLÈME**

1. **Erreur de permissions**: Vérifiez la politique IAM
2. **Accès refusé**: Utilisez `aws sso login --profile harmonic-ai`
3. **Bucket existe déjà**: Supprimez-le manuellement ou changez de nom
4. **Clés invalides**: Régénérez les clés IAM

---

## 🎯 **RÉSUMÉ RAPIDE**

1. ❌ **JAMAIS** de clés racines
2. ✅ **TOUJOURS** utilisateur IAM dédié
3. 🔐 **LIMITER** les permissions au minimum
4. 🔄 **ROTATION** régulière des clés
5. 📊 **MONITORING** constant des accès

**🔐 Sécurité maximale garantie pour Harmonic AI !**
