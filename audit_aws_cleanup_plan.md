# AUDIT AWS & PLAN DE NETTOYAGE - HARMONIC AI

## ðŸ“Š **RÃ‰SUMÃ‰ DE L'INFRASTRUCTURE AWS ACTUELLE**

### **1. COMPTE AWS**
- **ID Compte** : 326095712935
- **Utilisateur** : harmonic-ai-user
- **ARN** : arn:aws:iam::326095712935:user/harmonic-ai-user

### **2. RÃ‰GIONS ACTIVES**

#### **A. RÃ©gion us-east-1 (Virginie du Nord)**
**Instances EC2** :
| Instance ID | Type | Statut | IP Publique | Usage |
|-------------|------|--------|-------------|-------|
| i-040cd889e745cbedd | t3.medium | stopped | None | Ancienne instance (inutilisÃ©e) |
| i-0716d7805ca2c22e9 | t3.medium | running | __EC2_IP__ | **Instance active : DeepSeek-Harmonic-V2** |

**Buckets S3** :
| Nom du Bucket | Taille | Statut | Usage |
|---------------|--------|--------|-------|
| amazon-sagemaker-326095712935-us-east-1-3jkmqv6lj7x73b | ? | ? | SageMaker (probablement inutilisÃ©) |
| connective-ai-deploymendeepseek-models-326095712935 | ? | ? | DÃ©ploiement Connective AI |
| deepseek-models-326095712935 | **19.4 GiB** | Actif | **ModÃ¨les DeepSeek/Qwen (actif)** |
| harmonic-ai-knowledge-base | ~2.5 MB | Actif | Base de connaissances (actif) |
| hcv-compression-engine-frontend-326095712935 | ? | ? | Frontend HCV Compression |
| hcv-pro-deepseek-frontend-326095712935 | ? | ? | Frontend HCV Pro DeepSeek |
| hcv-pro-deepseek-test-326095712935 | ? | ? | Tests HCV Pro DeepSeek |
| hcv-pro-frontend-326095712935 | ? | ? | Frontend HCV Pro |

#### **B. RÃ©gion eu-west-3 (Paris)**
**Instances EC2** :
| Instance ID | Type | Statut | IP Publique | Usage |
|-------------|------|--------|-------------|-------|
| i-081dba17e2d81af47 | m5.2xlarge | running | 15.188.57.52 | Instance de production (actif) |
| i-0fc6bda21c6b144ad | c5.2xlarge | running | 13.38.251.110 | Instance de calcul (actif) |

**Buckets S3** :
| Nom du Bucket | Statut | Usage |
|---------------|--------|-------|
| elasticbeanstalk-eu-west-3-326095712935 | Actif | Elastic Beanstalk (actif) |

### **3. SERVICES AWS UTILISÃ‰S**

#### **Services Actifs** :
1. **EC2** : 3 instances running (2 en eu-west-3, 1 en us-east-1)
2. **S3** : 9 buckets (dont 1 avec 19.4 GiB de modÃ¨les)
3. **Elastic Beanstalk** : 1 environnement (eu-west-3)

#### **Services Inaccessibles (permissions manquantes)** :
1. **Lambda** : AccÃ¨s refusÃ© (pas de permission lambda:ListFunctions)
2. **S3 deepseek-models** : AccÃ¨s refusÃ© (pas de permission s3:ListBucket)

## ðŸŽ¯ **IDENTIFICATION DES RESSOURCES INUTILISÃ‰ES**

### **1. RESSOURCES Ã€ NETTOYER (PRIORITÃ‰ HAUTE)**

#### **A. us-east-1** :
| Ressource | Type | Statut | Action | Justification |
|-----------|------|--------|--------|---------------|
| i-040cd889e745cbedd | EC2 Instance | stopped | **SUPPRIMER** | Instance arrÃªtÃ©e, inutilisÃ©e |
| amazon-sagemaker-326095712935-us-east-1-3jkmqv6lj7x73b | S3 Bucket | ? | **VÃ‰RIFIER puis SUPPRIMER** | SageMaker probablement inutilisÃ© |
| connective-ai-deploymendeepseek-models-326095712935 | S3 Bucket | ? | **VÃ‰RIFIER puis SUPPRIMER** | DÃ©ploiement obsolÃ¨te |
| hcv-compression-engine-frontend-326095712935 | S3 Bucket | ? | **VÃ‰RIFIER puis SUPPRIMER** | Frontend obsolÃ¨te |
| hcv-pro-deepseek-frontend-326095712935 | S3 Bucket | ? | **VÃ‰RIFIER puis SUPPRIMER** | Frontend obsolÃ¨te |
| hcv-pro-deepseek-test-326095712935 | S3 Bucket | ? | **VÃ‰RIFIER puis SUPPRIMER** | Tests obsolÃ¨tes |
| hcv-pro-frontend-326095712935 | S3 Bucket | ? | **VÃ‰RIFIER puis SUPPRIMER** | Frontend obsolÃ¨te |

#### **B. eu-west-3** :
| Ressource | Type | Statut | Action | Justification |
|-----------|------|--------|--------|---------------|
| elasticbeanstalk-eu-west-3-326095712935 | S3 Bucket | Actif | **CONSERVER** | Elastic Beanstalk actif |

### **2. RESSOURCES Ã€ CONSERVER (CRITIQUES)**

#### **A. Essentielles** :
1. **i-0716d7805ca2c22e9** (us-east-1) : Instance DeepSeek-Harmonic-V2 active
2. **deepseek-models-326095712935** (us-east-1) : ModÃ¨les 19.4 GiB (actif)
3. **harmonic-ai-knowledge-base** (us-east-1) : Base de connaissances (actif)
4. **i-081dba17e2d81af47** (eu-west-3) : Instance production m5.2xlarge
5. **i-0fc6bda21c6b144ad** (eu-west-3) : Instance calcul c5.2xlarge

#### **B. Optionnelles (Ã  Ã©valuer)** :
1. **Lambda functions** : Inaccessibles (besoin de permissions)
2. **API Gateway** : Non listÃ© (probablement inexistant)

## ðŸš€ **PLAN DE NETTOYAGE AWS**

### **PHASE 1 : AUDIT COMPLET (Jour 1)**

#### **Ã‰tape 1.1 : Obtenir les permissions nÃ©cessaires**
```powershell
# Demander Ã  l'administrateur AWS d'ajouter les permissions suivantes :
# 1. s3:ListBucket pour deepseek-models-326095712935
# 2. lambda:ListFunctions pour toutes les fonctions
# 3. ec2:DescribeInstances pour toutes les rÃ©gions
# 4. elasticbeanstalk:DescribeEnvironments
```

#### **Ã‰tape 1.2 : Audit dÃ©taillÃ© des buckets S3**
```powershell
# Lister tous les objets dans chaque bucket suspect
aws s3 ls s3://amazon-sagemaker-326095712935-us-east-1-3jkmqv6lj7x73b/ --recursive --human-readable
aws s3 ls s3://connective-ai-deploymendeepseek-models-326095712935/ --recursive --human-readable
aws s3 ls s3://hcv-compression-engine-frontend-326095712935/ --recursive --human-readable
aws s3 ls s3://hcv-pro-deepseek-frontend-326095712935/ --recursive --human-readable
aws s3 ls s3://hcv-pro-deepseek-test-326095712935/ --recursive --human-readable
aws s3 ls s3://hcv-pro-frontend-326095712935/ --recursive --human-readable
```

#### **Ã‰tape 1.3 : Audit des instances EC2**
```powershell
# VÃ©rifier l'utilisation CPU/mÃ©moire des instances
aws cloudwatch get-metric-statistics --namespace AWS/EC2 --metric-name CPUUtilization --start-time 2026-05-10T00:00:00Z --end-time 2026-05-16T23:59:59Z --period 3600 --statistics Average --dimensions Name=InstanceId,Value=i-040cd889e745cbedd

# VÃ©rifier les tags pour comprendre l'usage
aws ec2 describe-tags --filters "Name=resource-id,Values=i-040cd889e745cbedd"
```

### **PHASE 2 : NETTOYAGE (Jour 2)**

#### **Ã‰tape 2.1 : Suppression des instances EC2 inutilisÃ©es**
```powershell
# 1. Terminer l'instance arrÃªtÃ©e
aws ec2 terminate-instances --instance-ids i-040cd889e745cbedd --region us-east-1

# 2. VÃ©rifier la suppression
aws ec2 describe-instances --instance-ids i-040cd889e745cbedd --region us-east-1
```

#### **Ã‰tape 2.2 : Nettoyage des buckets S3 obsolÃ¨tes**
```powershell
# 1. Vider les buckets inutilisÃ©s (aprÃ¨s vÃ©rification)
aws s3 rm s3://amazon-sagemaker-326095712935-us-east-1-3jkmqv6lj7x73b/ --recursive
aws s3 rm s3://connective-ai-deploymendeepseek-models-326095712935/ --recursive
aws s3 rm s3://hcv-compression-engine-frontend-326095712935/ --recursive
aws s3 rm s3://hcv-pro-deepseek-frontend-326095712935/ --recursive
aws s3 rm s3://hcv-pro-deepseek-test-326095712935/ --recursive
aws s3 rm s3://hcv-pro-frontend-326095712935/ --recursive

# 2. Supprimer les buckets vides
aws s3api delete-bucket --bucket amazon-sagemaker-326095712935-us-east-1-3jkmqv6lj7x73b --region us-east-1
aws s3api delete-bucket --bucket connective-ai-deploymendeepseek-models-326095712935 --region us-east-1
aws s3api delete-bucket --bucket hcv-compression-engine-frontend-326095712935 --region us-east-1
aws s3api delete-bucket --bucket hcv-pro-deepseek-frontend-326095712935 --region us-east-1
aws s3api delete-bucket --bucket hcv-pro-deepseek-test-326095712935 --region us-east-1
aws s3api delete-bucket --bucket hcv-pro-frontend-326095712935 --region us-east-1
```

#### **Ã‰tape 2.3 : Audit des fonctions Lambda (si permissions obtenues)**
```powershell
# 1. Lister toutes les fonctions Lambda
aws lambda list-functions --region us-east-1 --query "Functions[].{Name:FunctionName,LastModified:LastModified,Runtime:Runtime,MemorySize:MemorySize}"

# 2. VÃ©rifier les invocations rÃ©centes
aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Invocations --start-time 2026-05-01T00:00:00Z --end-time 2026-05-16T23:59:59Z --period 86400 --statistics Sum
```

### **PHASE 3 : OPTIMISATION (Jour 3)**

#### **Ã‰tape 3.1 : Optimisation des instances actives**
```powershell
# 1. VÃ©rifier les types d'instances pour optimisation coÃ»t
# Instance us-east-1 : t3.medium (2 vCPU, 4 GiB RAM) ~ $0.0416/h
# Instance eu-west-3 : m5.2xlarge (8 vCPU, 32 GiB RAM) ~ $0.384/h
# Instance eu-west-3 : c5.2xlarge (8 vCPU, 16 GiB RAM) ~ $0.34/h

# 2. Recommandations :
# - Garder t3.medium (us-east-1) : optimal pour DeepSeek-Harmonic-V2
# - Ã‰valuer m5.2xlarge (eu-west-3) : peut-Ãªtre overkill
# - Ã‰valuer c5.2xlarge (eu-west-3) : peut-Ãªtre suffisant
```

#### **Ã‰tape 3.2 : Optimisation du stockage S3**
```powershell
# 1. Analyser l'utilisation du bucket deepseek-models
aws s3 ls s3://deepseek-models-326095712935/ --recursive --human-readable --summarize

# 2. Recommandations :
# - Conserver les modÃ¨les essentiels (Qwen3.5-DeepSeek-V4)
# - Archiver les anciennes versions
# - Activer Intelligent-Tiering pour Ã©conomies
```

#### **Ã‰tape 3.3 : Mise en place du monitoring**
```powershell
# 1. CrÃ©er des dashboards CloudWatch
# 2. Configurer des alertes de coÃ»t
# 3. Mettre en place des rapports mensuels
```

## ðŸ“ˆ **ESTIMATION DES Ã‰CONOMIES**

### **1. COÃ›TS ACTUELS (ESTIMATION)**

| Service | Ressource | CoÃ»t Mensuel | Statut |
|---------|-----------|--------------|--------|
| **EC2 us-east-1** | t3.medium (running) | ~ $30 | Actif |
| **EC2 us-east-1** | t3.medium (stopped) | ~ $0 | InutilisÃ© |
| **EC2 eu-west-3** | m5.2xlarge | ~ $276 | Actif |
| **EC2 eu-west-3** | c5.2xlarge | ~ $245 | Actif |
| **S3 deepseek-models** | 19.4 GiB | ~ $0.46 | Actif |
| **S3 autres buckets** | ~ 1-5 GiB | ~ $0.15 | InutilisÃ©s |
| **Elastic Beanstalk** | Environnement | ~ $30-50 | Actif |

**Total mensuel estimÃ© : ~ $581-601**

### **2. Ã‰CONOMIES POTENTIELLES**

| Action | Ã‰conomie Mensuelle | Justification |
|--------|-------------------|---------------|
| **Supprimer instance arrÃªtÃ©e** | $0 | DÃ©jÃ  arrÃªtÃ©e, pas de coÃ»t |
| **Supprimer 7 buckets inutilisÃ©s** | ~ $0.10 | CoÃ»ts de stockage minimes |
| **Optimiser m5.2xlarge â†’ t3.large** | ~ $200 | RÃ©duction capacitÃ© |
| **Optimiser c5.2xlarge â†’ t3.large** | ~ $180 | RÃ©duction capacitÃ© |
| **Archiver anciens modÃ¨les** | ~ $0.20 | Stockage Intelligent-Tiering |

**Total Ã©conomies potentielles : ~ $380-400/mois (65-67% rÃ©duction)**

## ðŸ›¡ï¸ **PRÃ‰CAUTIONS & BACKUP**

### **1. AVANT TOUTE SUPPRESSION**

#### **Ã‰tape de vÃ©rification obligatoire** :
```powershell
# 1. CrÃ©er un snapshot de backup avant suppression
aws ec2 create-snapshot --volume-id [VOLUME_ID] --description "Backup avant nettoyage" --region us-east-1

# 2. VÃ©rifier les dÃ©pendances
# - VÃ©rifier les Security Groups utilisÃ©s
# - VÃ©rifier les Elastic IP associÃ©es
# - VÃ©rifier les Load Balancers
# - VÃ©rifier les Auto Scaling Groups
```

#### **Ã‰tape de test de restauration** :
```powershell
# 1. Tester la restauration depuis snapshot
aws ec2 restore-snapshot --snapshot-id [SNAPSHOT_ID] --region us-east-1

# 2. VÃ©rifier l'intÃ©gritÃ© des donnÃ©es
```

### **2. PLAN DE ROLLBACK**

#### **ScÃ©narios de rollback** :
1. **Suppression accidentelle** : Restaurer depuis snapshot
2. **ProblÃ¨mes de performance** : RecrÃ©er l'instance avec ancien type
3. **DonnÃ©es critiques perdues** : Restaurer depuis backup S3

#### **ProcÃ©dures de rollback** :
```powershell
# Rollback instance EC2
aws ec2 run-instances --image-id [AMI_ID] --instance-type t3.medium --key-name [KEY_NAME] --security-group-ids [SG_ID] --subnet-id [SUBNET_ID] --region us-east-1

# Rollback bucket S3 (si versioning activÃ©)
aws s3api list-object-versions --bucket [BUCKET_NAME] --prefix [OBJECT_KEY]
aws s3api restore-object --bucket [BUCKET_NAME] --key [OBJECT_KEY] --version-id [VERSION_ID]
```

## ðŸŽ¯ **RECOMMANDATIONS FINALES**

### **1. ACTIONS IMMÃ‰DIATES (Semaine 1)**

#### **PrioritÃ© 1 : Audit et sauvegarde**
1. **Obtenir les permissions** pour audit complet
2. **CrÃ©er des snapshots** de toutes les instances
3. **Exporter les configurations** (Security Groups, VPC, etc.)

#### **PrioritÃ© 2 : Nettoyage us-east-1**
1. **Supprimer l'instance arrÃªtÃ©e** (i-040cd889e745cbedd)
2. **Vider les buckets inutilisÃ©s** (aprÃ¨s vÃ©rification)
3. **Supprimer les buckets vides**

### **2. ACTIONS Ã€ MOYEN TERME (Semaine 2)**

#### **Optimisation des instances eu-west-3**
1. **Analyser l'utilisation rÃ©elle** CPU/mÃ©moire
2. **Downsizer si possible** (m5.2xlarge â†’ t3.large)
3. **Configurer Auto Scaling** pour flexibilitÃ©

#### **Optimisation du stockage**
1. **Archiver les anciens modÃ¨les** vers Glacier
2. **Activer Intelligent-Tiering** sur S3
3. **Nettoyer les donnÃ©es temporaires**

### **3. ACTIONS Ã€ LONG TERME (Mois 1)**

#### **Monitoring et gouvernance**
1. **Mettre en place Cost Explorer**
2. **Configurer des budgets AWS**
3. **CrÃ©er des politiques de tagging**

#### **SÃ©curitÃ© et conformitÃ©**
1. **Auditer les IAM roles/policies**
2. **Configurer CloudTrail**
3. **Mettre en place des alertes de sÃ©curitÃ©**

## ðŸ“‹ **CHECKLIST DE VALIDATION**

### **Avant nettoyage** :
- [ ] Snapshots de backup crÃ©Ã©s
- [ ] Permissions AWS vÃ©rifiÃ©es
- [ ] DÃ©pendances identifiÃ©es
- [ ] Plan de rollback documentÃ©
- [ ] Ã‰quipe informÃ©e (maintenance window)

### **Pendant nettoyage** :
- [ ] Instance arrÃªtÃ©e supprimÃ©e
- [ ] Buckets inutilisÃ©s vidÃ©s
- [ ] Buckets vides supprimÃ©s
- [ ] Configurations sauvegardÃ©es

### **AprÃ¨s nettoyage** :
- [ ] Services testÃ©s (DeepSeek-Harmonic-V2 actif)
- [ ] Performances vÃ©rifiÃ©es
- [ ] CoÃ»ts monitorÃ©s
- [ ] Documentation mise Ã  jour

## ðŸ **CONCLUSION**

### **RÃ©sumÃ© des actions clÃ©s** :
1. **Supprimer** : 1 instance EC2 arrÃªtÃ©e + 7 buckets S3 inutilisÃ©s
2. **Conserver** : 3 instances EC2 actives + 2 buckets S3 critiques
3. **Optimiser** : Downsizer instances eu-west-3 pour Ã©conomies
4. **Monitorer** : Mettre en place alertes coÃ»t/performance

### **BÃ©nÃ©fices attendus** :
- **RÃ©duction coÃ»ts** : ~ $380-400/mois (65-67%)
- **Simplification** : Infrastructure plus claire
- **Performance** : Monitoring amÃ©liorÃ©
- **SÃ©curitÃ©** : Surface d'attaque rÃ©duite

### **Prochaine Ã©tape** :
**Obtenir les permissions AWS nÃ©cessaires pour procÃ©der au nettoyage en toute sÃ©curitÃ©.**