#!/usr/bin/env python3
"""
🚀 UPGRADE EC2 POUR VRAI MISTRAL
Passage à instance 16GB RAM pour Mistral 7B
"""

import boto3
import json

def upgrade_ec2_instance():
    """Upgrade EC2 vers instance compatible Mistral"""
    
    # Configuration
    instance_id = "i-0716d7805ca2c22e9"
    new_instance_type = "t3.xlarge"  # 4 vCPUs, 16GB RAM
    
    print("🚀 UPGRADE EC2 POUR MISTRAL RÉEL")
    print("=" * 60)
    print(f"📱 Instance actuelle: t3.medium (3.8GB RAM)")
    print(f"🚀 Nouvelle instance: {new_instance_type} (16GB RAM)")
    print(f"💰 Coût additionnel: ~$0.1664/heure ($4/jour)")
    print(f"📊 Justification: Vrai Mistral = Top 10-15 LM Arena = ROI massif")
    
    try:
        # Client EC2
        ec2 = boto3.client('ec2', region_name='us-east-1')
        
        # Arrêter l'instance
        print("\n🛑 Arrêt de l'instance actuelle...")
        ec2.stop_instances(InstanceIds=[instance_id])
        
        # Attendre arrêt
        print("⏳ Attente arrêt complet...")
        waiter = ec2.get_waiter('instance_stopped')
        waiter.wait(InstanceIds=[instance_id])
        
        # Modifier le type
        print(f"🔄 Modification vers {new_instance_type}...")
        ec2.modify_instance_attribute(
            InstanceId=instance_id,
            InstanceType={'Value': new_instance_type}
        )
        
        # Démarrer l'instance
        print("🚀 Démarrage nouvelle instance...")
        ec2.start_instances(InstanceIds=[instance_id])
        
        # Attendre démarrage
        print("⏳ Attente démarrage complet...")
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        
        print("✅ Upgrade EC2 terminé!")
        print(f"📊 Nouvelle configuration: {new_instance_type} (16GB RAM)")
        print("🔥 Prêt pour VRAI Mistral 7B!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur upgrade: {e}")
        return False

if __name__ == "__main__":
    upgrade_ec2_instance()
