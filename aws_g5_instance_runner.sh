#!/bin/bash
# ==============================================
# LANCEUR AUTOMATIQUE INSTANCE AWS G5.XLARGE
# ==============================================
# Execution automatique de la transformation harmonique
# L'instance se termine TOUT SEULE apres le test
# ==============================================

INSTANCE_TYPE="g5.xlarge"
AMI_ID="ami-08b4d587ef98c47c1" # Deep Learning AMI GPU PyTorch 2.1
SECURITY_GROUP="default"
KEY_NAME="harmonic-ai-key"
SPOT_PRICE="0.70"

echo "🚀 Lancement instance AWS g5.xlarge Spot..."

# Lancer instance Spot
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SECURITY_GROUP \
    --instance-market-options '{"MarketType":"spot","SpotOptions":{"MaxPrice":"'$SPOT_PRICE'","SpotInstanceType":"one-time","InstanceInterruptionBehavior":"terminate"}}' \
    --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":100}}]' \
    --user-data '#!/bin/bash
cd /home/ubuntu
git clone https://github.com/your-repo/harmonic-ai.git
cd harmonic-ai
pip install -r requirements.txt
python deepseek_harmonic_patch.py > results.log
aws s3 cp results.log s3://deepseek-models-326095712935/
# AUTO-DESTRUCTION DE LINSTANCE APRES TEST
aws ec2 terminate-instances --instance-id $(curl http://169.254.169.254/latest/meta-data/instance-id)
' \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "✅ Instance lancée: $INSTANCE_ID"
echo "⏱️  Le test se lance automatiquement au démarrage"
echo "🗑️  L'instance se détruit TOUT SEULE à la fin du test"
echo "📊 Les résultats seront disponible sur S3"