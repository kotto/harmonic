# 🔐 GUIDE UTILISATEUR IAM SÉCURISÉ POUR HARMONIC AI

## 🚨 POURQUOI PAS DE CLÉS RACINES ?

Les clés d'accès racines ont:
- ❌ Permissions illimitées
- ❌ Impossible de restreindre
- ❌ Risque de sécurité élevé
- ❌ Pas d'audit possible

## ✅ SOLUTION UTILISATEUR IAM

### 1️⃣ CRÉATION UTILISATEUR IAM

1. **Console AWS** → **IAM** → **Users** → **Create user**
2. **Nom**: `harmonic-ai-user`
3. **Type**: "Access key - Programmatic access"
4. **Permissions**: "Attach policies directly"

### 2️⃣ POLITIQUES RECOMMANDÉES

Créez une politique personnalisée:

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

### 3️⃣ ÉTAPES DANS LA CONSOLE

1. **IAM** → **Policies** → **Create policy**
2. **JSON** → Collez la politique ci-dessus
3. **Nom**: `HarmonicAI-S3-Policy`
4. **Create policy**

5. **IAM** → **Users** → **harmonic-ai-user**
6. **Add permissions** → **Attach existing policies directly**
7. **Recherchez**: `HarmonicAI-S3-Policy`
8. **Attach policy**

### 4️⃣ GÉNÉRATION DES CLÉS

1. **IAM** → **Users** → **harmonic-ai-user**
2. **Security credentials** → **Create access key**
3. **Use case**: "Command Line Interface (CLI)"
4. **Acknowledge** → **Create access key**
5. **Copiez** l'Access Key ID et Secret Access Key

## 🔐 SÉCURITÉ ADDITIONNELLE

### Rotation des clés
- 🔄 Changez les clés tous les 90 jours
- 📅 Configurez des rappels
- 🗑️ Supprimez les anciennes clés

### Monitoring
- 📊 Activez CloudTrail
- 🔔 Configurez des alertes
- 📋 Vérifiez les logs régulièrement

### Restrictions réseau
- 🌐 Configurez des VPC endpoints
- 🔒 Limitez les adresses IP
- 🛡️ Utilisez des security groups
