# 🔑 GUIDE DE CONFIGURATION AWS POUR HARMONIC AI

## 📋 ÉTAT ACTUEL

✅ **Structure S3 locale prête**: 114 fichiers (1.94 MB)
✅ **Scripts de configuration créés**
❌ **Credentials AWS manquants**
📋 **Upload en attente** des credentials

## 🚀 MÉTHODES DE CONFIGURATION

### 1️⃣ **MÉTHODE RAPIDE: Variables d'environnement**

**Windows PowerShell:**
```powershell
# Copiez-collez ces commandes dans PowerShell
$env:AWS_ACCESS_KEY_ID = "VOTRE_VRAIE_ACCESS_KEY"
$env:AWS_SECRET_ACCESS_KEY = "VOTRE_VRAIE_SECRET_KEY"
$env:AWS_DEFAULT_REGION = "us-east-1"
$env:AWS_REGION = "us-east-1"
$env:HARMONIC_BUCKET = "harmonic-ai-knowledge-base"

# Test immédiat
python test_aws_credentials.py
```

### 2️⃣ **MÉTHODE AUTOMATIQUE: Script PowerShell**

```powershell
# Étape 1: Modifiez le fichier set_aws_env.ps1
# Remplacez "VOTRE_ACCESS_KEY_ID" par votre vraie clé
# Remplacez "VOTRE_SECRET_ACCESS_KEY" par votre vrai secret

# Étape 2: Exécutez le script
.\set_aws_env.ps1

# Étape 3: Test
python test_aws_credentials.py
```

### 3️⃣ **MÉTHODE CLASSIQUE: AWS CLI**

```bash
# Installation AWS CLI si nécessaire
pip install awscli

# Configuration
aws configure
# Entrez vos credentials quand demandé
# Region: us-east-1
# Output format: json
```

### 4️⃣ **MÉTHODE MANUELLE: Fichiers AWS**

Modifiez `C:\Users\maatc\.aws\credentials`:
```ini
[default]
aws_access_key_id = VOTRE_VRAIE_ACCESS_KEY
aws_secret_access_key = VOTRE_VRAIE_SECRET_KEY
```

## 🧪 **VÉRIFICATION**

Après configuration, testez:
```bash
python test_aws_credentials.py
```

**Résultat attendu:**
```
✅ Connexion réussie!
✅ Bucket 'harmonic-ai-knowledge-base' accessible
🚀 Configuration AWS valide! Prêt pour l'upload S3.
```

## 🚀 **UPLOAD AUTOMATIQUE**

Une fois les credentials validés:

```bash
# Upload simple et rapide
python simple_upload_to_s3.py

# OU upload complet avec toutes les options
python upload_local_models_to_s3.py
```

## 📊 **CE QUI SERA UPLOADÉ**

```
📦 harmonic-ai-knowledge-base/
├── 📂 foundation/ (3 fichiers)
├── 📂 core/ (7 fichiers)
├── 📂 api/ (1 fichier)
├── 📂 deployment/ (5 fichiers)
├── 📂 domains/ (26 fichiers)
├── 📂 structured_data/ (24 fichiers)
├── 📂 simple_real_output/ (24 fichiers)
├── 📂 real_structured_data/ (16 fichiers)
└── 📂 reports/ (8 fichiers)
```

## 🔐 **PERMISSIONS NÉCESSAIRES**

Votre utilisateur AWS a besoin de:
- `s3:CreateBucket`
- `s3:PutObject`
- `s3:GetObject`
- `s3:ListBucket`
- `s3:DeleteObject`

## 📞 **OBTENIR VOS CREDENTIALS**

1. **Console AWS** → **IAM** → **Users** → **Votre utilisateur**
2. **Security credentials** → **Create access key**
3. **Choisir**: "Command Line Interface (CLI)"
4. **Copier** l'Access Key ID et le Secret Access Key
5. **Configurer** avec une des méthodes ci-dessus

## 🎯 **RÉSUMÉ RAPIDE**

1. ✅ Obtenez vos credentials AWS
2. ✅ Configurez-les avec une des méthodes
3. ✅ Testez avec `python test_aws_credentials.py`
4. ✅ Uploadez avec `python simple_upload_to_s3.py`

---

**🌊 Prêt pour l'upload Harmonic AI sur AWS S3 !**
