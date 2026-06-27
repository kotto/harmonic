#!/bin/bash
# Script de migration instance AWS pour Harmonic AI

set -e

echo "PLAN DE MIGRATION INSTANCE AWS"
echo "=================================="

# Variables
OLD_INSTANCE_ID="i-xxxxxxxxxxxxx"  # À remplacer
NEW_INSTANCE_TYPE="g5.8xlarge"
KEY_NAME="harmonic-ai-key"
SECURITY_GROUP="sg-xxxxxxxx"
SUBNET_ID="subnet-xxxxxxxx"
AMI_ID="ami-0c55b159cbfafe1f0"  # Ubuntu 22.04 LTS

echo "CONFIGURATION ACTUELLE:"
echo "   Instance ID: $OLD_INSTANCE_ID"
echo "   Type actuel: g5.2xlarge (estimé)"
echo "   GPU: NVIDIA A10G (24GB VRAM)"
echo "   vCPU: 8, RAM: 32GB"

echo ""
echo "CONFIGURATION CIBLE:"
echo "   Nouveau type: $NEW_INSTANCE_TYPE"
echo "   GPU: 4x NVIDIA A10G (96GB VRAM)"
echo "   vCPU: 32, RAM: 128GB"
echo "   Coût additionnel: ~$1,900/mois"
echo "   Gain performance: 50-60%"

echo ""
echo "📋 ÉTAPES DE MIGRATION:"

cat << 'MIGRATION_STEPS'
1. 📸 CRÉER SNAPSHOT
   - Snapshot EBS volumes
   - Vérifier intégrité snapshot

2. 🚀 LANCER NOUVELLE INSTANCE
   - Instance type: g5.8xlarge
   - AMI: Ubuntu 22.04 LTS
   - Storage: 600GB (100GB système + 500GB données)

3. ⚙️ CONFIGURER ENVIRONNEMENT
   - Docker + NVIDIA container toolkit
   - Python 3.11 + dépendances
   - Harmonic AI codebase

4. 📁 COPIER DONNÉES
   - Modèle GGUF (17GB → 9GB avec quantisation)
   - Configuration API
   - Cache déterministe

5. 🧪 TESTER NOUVELLE INSTANCE
   - Health check endpoint
   - Performance benchmark
   - Déterminisme vérification

6. 🔄 MISE À JOUR INFRASTRUCTURE
   - DNS records (si applicable)
   - Load balancer target group
   - Monitoring CloudWatch

7. 🛑 ARRÊTER ANCIENNE INSTANCE
   - Vérifier nouvelle instance stable
   - Sauvegarder logs ancienne instance
   - Terminer instance
MIGRATION_STEPS

echo ""
echo "⚠️  RISQUES IDENTIFIÉS:"
echo "   - Problèmes compatibilité GPU drivers"
echo "   - Performance inférieure aux attentes"
echo "   - Downtime plus long que prévu"

echo ""
echo "🛡️  MITIGATIONS:"
echo "   - Tester sur instance dev d'abord"
echo "   - Backup complet avant migration"
echo "   - Plan de rollback préparé"

echo ""
echo "🎯 RECOMMANDATION:"
echo "   Exécuter migration pendant fenêtre maintenance (ex: 02:00-04:00)"
echo "   Tester intensivement avant coupure production"
echo "   Monitorer étroitement post-migration"
