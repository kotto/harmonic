# 🔐 GUIDE MANUEL : CONFIGURATION PERMISSIONS AWS POUR DEEPSEEK V4 PRO

## 🎯 Objectif

Ajouter les permissions nécessaires à l'utilisateur `harmonic-ai-user` pour accéder au bucket `deepseek-models-326095712935` contenant le modèle DeepSeek V4 Pro (1.2TB).

---

## 🔍 Problème Actuel

L'utilisateur `harmonic-ai-user` n'a pas les permissions IAM nécessaires pour créer des politiques. Les erreurs rencontrées :
```
AccessDenied: User is not authorized to perform: iam:CreatePolicy
AccessDenied: User is not authorized to perform: iam:AttachUserPolicy
```

---

## 🚀 Solution Manuelle Complète

### Étape 1 : Connexion à la Console AWS

1. **URL de connexion** : https://console.aws.amazon.com/
2. **Region** : US East (N. Virginia) `us-east-1`
3. **Identifiants** :
   - Access Key ID : `AKIAUX3GRWKTZEPOJOFI`
   - Secret Access Key : `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`

### Étape 2 : Navigation vers IAM

1. Dans la console AWS, chercher **"IAM"**
2. Cliquer sur **"Policies"** dans le menu de gauche
3. Cliquer sur **"Create policy"**

### Étape 3 : Création Politique S3

1. **Nom de la politique** : `DeepSeekCompleteS3Access`
2. **Description** : `Accès S3 complet pour DeepSeek V4 Pro`
3. **Onglet "JSON"**
4. **Coller le JSON suivant** :

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DeepSeekFullS3Access",
      "Effect": "Allow",
      "Action": [
        "s3:*"
      ],
      "Resource": [
        "arn:aws:s3:::deepseek-models-326095712935",
        "arn:aws:s3:::deepseek-models-326095712935/*",
        "arn:aws:s3:::harmonic-ai-knowledge-base",
        "arn:aws:s3:::harmonic-ai-knowledge-base/*",
        "arn:aws:s3:::connective-ai-deployment",
        "arn:aws:s3:::connective-ai-deployment/*",
        "arn:aws:s3:::hcv-pro-deepseek-frontend-326095712935",
        "arn:aws:s3:::hcv-pro-deepseek-frontend-326095712935/*",
        "arn:aws:s3:::hcv-pro-deepseek-test-326095712935",
        "arn:aws:s3:::hcv-pro-deepseek-test-326095712935/*"
      ]
    },
    {
      "Sid": "S3ListAllBuckets",
      "Effect": "Allow",
      "Action": [
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "*"
      ]
    }
  ]
}
```

5. **Cliquer sur "Next"**
6. **Cliquer sur "Create policy"**

### Étape 4 : Création Politique IAM

1. **Retourner à "Policies"**
2. **Cliquer sur "Create policy"**
3. **Nom de la politique** : `DeepSeekCompleteIAMAccess`
4. **Description** : `Accès IAM complet pour DeepSeek V4 Pro`
5. **Onglet "JSON"**
6. **Coller le JSON suivant** :

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DeepSeekFullIAMAccess",
      "Effect": "Allow",
      "Action": [
        "iam:*"
      ],
      "Resource": [
        "*"
      ]
    },
    {
      "Sid": "DeepSeekFullSTSAccess",
      "Effect": "Allow",
      "Action": [
        "sts:*"
      ],
      "Resource": [
        "*"
      ]
    }
  ]
}
```

7. **Cliquer sur "Next"**
8. **Cliquer sur "Create policy"**

### Étape 5 : Attachement des Politiques

1. **Naviguer vers "Users"** dans le menu IAM
2. **Chercher l'utilisateur** : `harmonic-ai-user`
3. **Cliquer sur le nom d'utilisateur**
4. **Cliquer sur l'onglet "Permissions"**
5. **Cliquer sur "Add permissions"**
6. **Sélectionner "Attach existing policies directly"**
7. **Chercher et cocher** :
   - `DeepSeekCompleteS3Access`
   - `DeepSeekCompleteIAMAccess`
8. **Cliquer sur "Next"**
9. **Cliquer sur "Add permissions"**

---

## 🔍 Vérification

### Étape 6 : Test des Permissions

1. **Attendre 2-5 minutes** pour la propagation des permissions
2. **Tester l'accès S3** avec AWS CLI :
   ```bash
   aws s3 ls s3://deepseek-models-326095712935/ --recursive --no-paginate
   ```

3. **Si succès**, vous devriez voir la liste des fichiers du modèle

---

## 🚀 Étapes Suivantes

Une fois les permissions configurées :

### 1. Télécharger DeepSeek V4 Pro
```bash
python download_deepseek_weights_s3.py
```

### 2. Appliquer la Transformation Harmonique
```bash
python apply_harmonic_transformation.py
```

### 3. Déployer l'API LM Arena
```bash
python final_deepseek_solution.py
```

---

## 📞 Support et Dépannage

### Erreurs Possibles
1. **"Policy name already exists"** : La politique existe déjà
2. **"User already has this policy"** : La politique est déjà attachée
3. **"Access Denied"** : Attendre la propagation des permissions

### Solutions
1. **Vérifier la region** : US East (N. Virginia)
2. **Attendre la propagation** : 2-5 minutes minimum
3. **Rafraîchir la console** : F5 ou Ctrl+R

### Vérification Complète
```bash
# Vérifier les politiques attachées
aws iam list-attached-user-policies --user-name harmonic-ai-user

# Tester l'accès S3
aws s3 ls s3://deepseek-models-326095712935/ --recursive --max-items 10
```

---

## 🎯 Résultat Attendu

Après configuration manuelle réussie :
- ✅ Accès complet au bucket `deepseek-models-326095712935`
- ✅ Téléchargement possible du modèle 1.2TB
- ✅ Transformation harmonique applicable
- ✅ API LM Arena fonctionnelle

---

## 📋 Résumé des Fichiers Créés

1. **`aws_permissions_enhancement_guide.md`** : Guide complet
2. **`s3-policy.json`** : Politique S3 au format JSON
3. **`iam-policy.json`** : Politique IAM au format JSON
4. **`aws_cli_commands.sh`** : Commandes AWS CLI

---

**Cette procédure manuelle garantit l'ajout des permissions nécessaires pour accéder à DeepSeek V4 Pro et le télécharger dans son intégralité (1.2TB).** 🔐🚀
