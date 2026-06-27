# 🚀 GUIDE PAS À PAS INSTANCE ON DEMAND G5.XLARGE

---

## ✅ ÉTAPE 1: Lancer l'instance
1. Ouvre la console AWS EC2
2. Clique sur **Lancer des instances**
3. Nom: `harmonic-deepseek-test`

---

## ✅ ÉTAPE 2: Choisir l'AMI
Recherche et sélectionne:
> **Deep Learning Base AMI (Amazon Linux 2023) Version 66.0**
> - AMI ID: `ami-0123456789abcdef0` (la dernière version disponible)
> - CUDA 12.1 préinstallé
> - PyTorch 2.1 préinstallé

---

## ✅ ÉTAPE 3: Type d'instance
🔹 Sélectionne: `g5.xlarge`
🔹 16 vCPU, 64 Go RAM, NVIDIA A10G 24GB VRAM
🔹 Prix: **1.21 € / heure**

---

## ✅ ÉTAPE 4: Paires de clés
🔹 Sélectionne la clé: `harmonic-ai-key`

---

## ✅ ÉTAPE 5: Paramètres réseau
🔹 Groupe de sécurité: `default` (avec SSH ouvert)

---

## ✅ ÉTAPE 6: Configuration avancée
👇 Coller **EXACTEMENT** ça dans le champ **Données utilisateur**:

```bash
#!/bin/bash
dnf update -y
dnf install -y python3.11 python3.11-pip git

# Installation dépendances
pip3.11 install transformers torch boto3 accelerate bitsandbytes s3fs tqdm

# Récupération du script
cd /home/ec2-user
wget https://raw.githubusercontent.com/your-repo/main/deepseek_harmonic_patch.py

# Execution du test
python3.11 deepseek_harmonic_patch.py > results.log 2>&1

# Upload des resultats
aws s3 cp results.log s3://deepseek-models-326095712935/
aws s3 cp harmonic_test_results.json s3://deepseek-models-326095712935/

# Upload du modèle harmonisé
aws s3 sync ./deepseek-coder-6.7b-harmonic s3://deepseek-models-326095712935/deepseek-coder-6.7b-harmonic

# 🗑️ AUTO-DESTRUCTION DE LINSTANCE
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
aws ec2 terminate-instances --instance-id $INSTANCE_ID --region eu-west-3
```

---

## ✅ ÉTAPE 7: Stockage
🔹 Augmente le volume EBS à **150 GB** (gp3)

---

## ✅ ÉTAPE 8: Lancer
✅ Clique sur **Lancer l'instance**

---

## ⏱️ Ce qui se passe ensuite AUTOMATIQUEMENT:
| Temps | Action |
|---|---|
| +2min | Instance démarrée |
| +5min | Dépendances installées |
| +7min | Modèle chargé en mémoire GPU |
| +12min | Transformation harmonique terminée |
| +18min | Benchmarks exécutés |
| +22min | Résultats uploadés sur S3 |
| +23min | ✅ INSTANCE SE DETRUIT TOUT SEULE |

---

## 📊 Récupérer les résultats
Dans ~25 minutes tu exécutes:
```bash
aws s3 cp s3://deepseek-models-326095712935/results.log . && cat results.log
```

✅ C'est tout. Pas de SSH, pas de connexion, rien à faire d'autre.