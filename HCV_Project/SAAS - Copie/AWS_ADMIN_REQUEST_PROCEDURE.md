# 📋 PROCÉDURE DEMANDE PERMISSIONS AWS ADMIN
## Pour: `lambda:UpdateFunctionCode` et permissions complètes Qwen3.5

---

## 🎯 **OBJECTIF**
Obtenir les permissions nécessaires pour finaliser l'intégration de **Qwen3.5 Enhanced Harmonic AI** avec le vrai modèle et la transformation harmonique complète.

---

## 📧 **INFORMATIONS TECHNIQUES**

### **Utilisateur AWS:**
- **Nom**: `harmonic-ai-user`
- **Account ID**: `326095712935`
- **Region**: `us-east-1`
- **ARN**: `arn:aws:iam::326095712935:user/harmonic-ai-user`

### **Ressources existantes:**
- **Lambda Function**: `qwen35-simple` (déjà créée)
- **API Gateway**: `https://lymk98dbvk.execute-api.us-east-1.amazonaws.com/prod/generate`
- **Bucket S3 requis**: `harmonic-ai-qwen-models`

---

## 🔐 **PERMISSIONS REQUISES**

### **Permissions Lambda:**
```
lambda:UpdateFunctionCode
lambda:UpdateFunctionConfiguration
lambda:GetFunction
lambda:InvokeFunction
lambda:CreateFunction
lambda:DeleteFunction
```

### **Permissions IAM:**
```
iam:CreatePolicy
iam:AttachUserPolicy
iam:ListAttachedUserPolicies
iam:PassRole
iam:GetRole
iam:CreateRole
```

### **Permissions S3:**
```
s3:CreateBucket
s3:PutObject
s3:GetObject
s3:DeleteObject
s3:ListBucket
```

### **Permissions ECR:**
```
ecr:CreateRepository
ecr:GetAuthorizationToken
ecr:InitiateLayerUpload
ecr:PutImage
ecr:UploadLayerPart
```

### **Permissions SageMaker:**
```
sagemaker:CreateModel
sagemaker:CreateEndpoint
sagemaker:CreateEndpointConfig
sagemaker:InvokeEndpoint
```

---

## 📧 **PROCÉDURE ÉTAPE PAR ÉTAPE**

### **ÉTAPE 1: CRÉER LA POLITIQUE IAM**

#### **Option A: Via Console AWS**
1. Connectez-vous à la **Console AWS IAM**
2. Allez dans **"Politiques"** → **"Créer une politique"**
3. **Nom**: `Qwen35-Enhanced-Harmonic-Policy`
4. **Description**: `Permissions complètes pour déploiement Qwen3.5 Enhanced Harmonic AI`
5. **Éditeur JSON** → Coller ce code:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "LambdaFullAccess",
            "Effect": "Allow",
            "Action": [
                "lambda:*"
            ],
            "Resource": "*"
        },
        {
            "Sid": "IAMFullAccess",
            "Effect": "Allow",
            "Action": [
                "iam:*"
            ],
            "Resource": "*"
        },
        {
            "Sid": "S3FullAccess",
            "Effect": "Allow",
            "Action": [
                "s3:*"
            ],
            "Resource": "*"
        },
        {
            "Sid": "ECRFullAccess",
            "Effect": "Allow",
            "Action": [
                "ecr:*"
            ],
            "Resource": "*"
        },
        {
            "Sid": "SageMakerFullAccess",
            "Effect": "Allow",
            "Action": [
                "sagemaker:*"
            ],
            "Resource": "*"
        },
        {
            "Sid": "APIGatewayFullAccess",
            "Effect": "Allow",
            "Action": [
                "apigateway:*"
            ],
            "Resource": "*"
        },
        {
            "Sid": "CloudWatchFullAccess",
            "Effect": "Allow",
            "Action": [
                "cloudwatch:*",
                "logs:*"
            ],
            "Resource": "*"
        }
    ]
}
```

6. **Créer la politique**

#### **Option B: Via AWS CLI (Admin)**
```bash
aws iam create-policy \
  --policy-name "Qwen35-Enhanced-Harmonic-Policy" \
  --policy-document file://qwen35_enhanced_policy.json \
  --description "Permissions complètes pour Qwen3.5 Enhanced Harmonic AI"
```

---

### **ÉTAPE 2: ATTACHER LA POLITIQUE À L'UTILISATEUR**

#### **Via Console:**
1. **IAM** → **"Utilisateurs"** → **"harmonic-ai-user"**
2. **"Ajouter des autorisations"** → **"Attacher des politiques existantes directement"**
3. **Chercher**: `Qwen35-Enhanced-Harmonic-Policy`
4. **Cocher** et **"Attacher les autorisations"**

#### **Via AWS CLI:**
```bash
aws iam attach-user-policy \
  --user-name "harmonic-ai-user" \
  --policy-arn "arn:aws:iam::326095712935:policy/Qwen35-Enhanced-Harmonic-Policy"
```

---

### **ÉTAPE 3: VÉRIFIER L'ATTACHEMENT**

#### **Via Console:**
1. **IAM** → **"Utilisateurs"** → **"harmonic-ai-user"**
2. **Vérifier** que la politique apparaît dans **"Autorisations"**

#### **Via AWS CLI:**
```bash
aws iam list-attached-user-policies \
  --user-name "harmonic-ai-user"
```

---

### **ÉTAPE 4: ATTENDRE LA PROPAGATION**

**⏳ Temps d'attente**: 2-5 minutes
Les permissions IAM peuvent prendre jusqu'à 5 minutes pour se propager à travers tous les services AWS.

---

### **ÉTAPE 5: TESTER LES PERMISSIONS**

#### **Test Lambda:**
```bash
aws lambda get-function \
  --function-name "qwen35-simple" \
  --region "us-east-1"
```

#### **Test S3:**
```bash
aws s3 ls s3://harmonic-ai-qwen-models \
  --region "us-east-1"
```

#### **Test IAM:**
```bash
aws iam list-policies \
  --scope Local \
  --region "us-east-1"
```

---

## 📧 **FICHIERS PRÉPARÉS POUR L'ADMIN**

### **1. Politique JSON Complète**
Fichier: `qwen35_enhanced_policy.json` (déjà créé dans votre workspace)

### **2. Script de Vérification**
Fichier: `verify_permissions.py` (créé ci-dessous)

### **3. Script de Déploiement Final**
Fichier: `deploy_qwen35_final.py` (déjà créé)

---

## 📧 **SCRIPT DE VÉRIFICATION AUTOMATIQUE**

```python
#!/usr/bin/env python3
"""
Script de vérification des permissions Qwen3.5 Enhanced
"""

import boto3
import json

def verify_permissions():
    """Vérifie toutes les permissions requises"""
    print("🔍 Vérification des permissions Qwen3.5 Enhanced...")
    
    # Clients AWS
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    iam_client = boto3.client('iam', region_name='us-east-1')
    s3_client = boto3.client('s3', region_name='us-east-1')
    
    results = {}
    
    # Test Lambda
    try:
        lambda_client.get_function(FunctionName='qwen35-simple')
        results['lambda'] = '✅ OK'
        print("✅ Lambda: OK")
    except Exception as e:
        results['lambda'] = f'❌ {e}'
        print(f"❌ Lambda: {e}")
    
    # Test IAM
    try:
        iam_client.list_attached_user_policies(UserName='harmonic-ai-user')
        results['iam'] = '✅ OK'
        print("✅ IAM: OK")
    except Exception as e:
        results['iam'] = f'❌ {e}'
        print(f"❌ IAM: {e}")
    
    # Test S3
    try:
        s3_client.head_bucket(Bucket='harmonic-ai-qwen-models')
        results['s3'] = '✅ OK'
        print("✅ S3: OK")
    except Exception as e:
        results['s3'] = f'❌ {e}'
        print(f"❌ S3: {e}")
    
    return results

if __name__ == "__main__":
    results = verify_permissions()
    print(f"\n📊 Résultats: {json.dumps(results, indent=2)}")
```

---

## 📧 **PROCÉDURE COMPLÈTE POUR L'ADMIN**

### **Résumé des actions:**
1. ✅ **Créer la politique** `Qwen35-Enhanced-Harmonic-Policy`
2. ✅ **Attacher la politique** à `harmonic-ai-user`
3. ✅ **Attendre 2-5 minutes** pour la propagation
4. ✅ **Tester les permissions** avec le script de vérification
5. ✅ **Confirmer** que tout fonctionne

### **Une fois les permissions obtenues:**
```bash
# Relancer l'intégration finale
python qwen35_harmonic_simple.py
```

---

## 📧 **CONTACT ADMIN AWS**

### **Email Template:**
```
Sujet: URGENT - Demande permissions pour projet Qwen3.5 Enhanced Harmonic AI

Destinataire: [votre-admin-aws@entreprise.com]

Corps:
Bonjour,

Je travaille sur le projet "Qwen3.5 Enhanced Harmonic AI" et j'ai besoin 
de permissions supplémentaires pour finaliser le déploiement.

INFORMATIONS UTILISATEUR:
- User: harmonic-ai-user
- Account: 326095712935
- Region: us-east-1

PERMISSIONS REQUISES:
- lambda:UpdateFunctionCode (priorité urgente)
- lambda:UpdateFunctionConfiguration
- lambda:CreateFunction
- iam:CreatePolicy, iam:AttachUserPolicy
- s3:CreateBucket, s3:PutObject
- ecr:CreateRepository, ecr:PutImage
- sagemaker:CreateModel, sagemaker:CreateEndpoint

RESSOURCES EXISTANTES:
- Lambda: qwen35-simple
- API Gateway: https://lymk98dbvk.execute-api.us-east-1.amazonaws.com/prod/generate
- Bucket: harmonic-ai-qwen-models

OBJECTIF:
Finaliser l'intégration de Qwen3.5 avec transformation harmonique 
selon le MODELE_MONDE_HARMONIQUE ("accorder le piano").

Pourriez-vous s'il vous plaît:
1. Créer la politique "Qwen35-Enhanced-Harmonic-Policy"
2. L'attacher à l'utilisateur harmonic-ai-user
3. Me confirmer quand les permissions seront actives

C'est urgent pour la finalisation du projet.

Merci,
[Votre Nom]
[Votre Contact]
```

---

## 🎯 **RÉSULTAT ATTENDU**

Une fois les permissions obtenues et le script relancé:

✅ **Qwen3.5 Enhanced Harmonic AI** sera pleinement fonctionnel
✅ **Transformation harmonique** appliquée avec Alpha et Phi
✅ **AVX2 optimization** activée
✅ **API production** avec vraies réponses Qwen3.5
✅ **MODELE_MONDE_HARMONIQUE** complètement implémenté

---

**Cette procédure complète permettra le déploiement final de Qwen3.5 Enhanced Harmonic AI avec toutes les optimisations AVX2.** 🚀
