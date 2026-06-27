#!/bin/bash
# 🚀 DÉMARRAGE UPGRADE 5 JOURS - DEEPSEEK V4 PRO

echo "🚀 DÉMARRAGE UPGRADE 5 JOURS - DEEPSEEK V4 PRO"
echo "=================================================="
echo "⏰ Durée: 5 jours (120 heures)"
echo "💰 Coût total: $384.00"
echo "🎯 Objectif: TOP 5 LM Arena"

echo ""
echo "📅 JOUR 1: UPGRADE INFRASTRUCTURE"
echo "🔄 Arrêt instance actuelle..."

# Arrêt instance
aws ec2 stop-instances --instance-ids i-0716d7805ca2c22e9 --region us-east-1

# Attendre arrêt complet
echo "⏳ Attente arrêt complet..."
aws ec2 wait instance-stopped --instance-ids i-0716d7805ca2c22e9 --region us-east-1

echo "✅ Instance arrêtée"
echo "🔄 Upgrade vers x2iezn.8xlarge..."

# Upgrade type
aws ec2 modify-instance-attribute --instance-id i-0716d7805ca2c22e9 --instance-type x2iezn.8xlarge --region us-east-1

echo "✅ Type d'instance modifié"
echo "🚀 Redémarrage instance..."

# Redémarrage
aws ec2 start-instances --instance-ids i-0716d7805ca2c22e9 --region us-east-1

# Attendre démarrage
echo "⏳ Attente démarrage complet..."
aws ec2 wait instance-running --instance-ids i-0716d7805ca2c22e9 --region us-east-1

echo "✅ Instance démarrée"
echo "🔥 Instance x2iezn.8xlarge prête pour DeepSeek V4 Pro!"

# Vérification
echo "📊 Vérification configuration..."
aws ec2 describe-instances --instance-ids i-0716d7805ca2c22e9 --region us-east-1 --query 'Reservations[0].Instances[0].[InstanceType,State.Name]' --output table

echo ""
echo "🎯 ÉTAPE 1 TERMINÉE - INFRASTRUCTURE PRÊTE"
echo "📦 Prochaine étape: Téléchargement DeepSeek V4 Pro"
