#!/usr/bin/env python3
"""
SUPPRESSION ANCIENNE INSTANCE EC2 - DEEPSEEK-V4-PRO
===================================================

Script pour supprimer proprement l'ancienne instance EC2
i-0569cad6646c9c0f9 et libérer les ressources
"""

import boto3
import json
import time
from datetime import datetime

class EC2InstanceDeleter:
    """Suppresseur d'instance EC2 pour Deepseek-V4-Pro"""
    
    def __init__(self):
        self.ec2_client = boto3.client('ec2', region_name='eu-west-3')
        self.old_instance_id = 'i-0569cad6646c9c0f9'
        self.new_instance_id = 'i-081dba17e2d81af47'
        
        print("🗑️ SUPPRESSION ANCIENNE INSTANCE EC2")
        print("=" * 80)
        print(f"🗑️ Ancienne instance: {self.old_instance_id}")
        print(f"🆕 Nouvelle instance: {self.new_instance_id}")
        print("=" * 80)
    
    def check_instance_status(self, instance_id):
        """Vérifier le statut d'une instance"""
        try:
            response = self.ec2_client.describe_instances(InstanceIds=[instance_id])
            instance = response['Reservations'][0]['Instances'][0]
            status = instance['State']['Name']
            return status, instance
        except Exception as e:
            return None, str(e)
    
    def stop_instance(self, instance_id):
        """Arrêter une instance si elle est en cours d'exécution"""
        print(f"\n🔥 ÉTAPE 1: ARRÊT INSTANCE {instance_id}")
        print("=" * 60)
        
        try:
            status, instance = self.check_instance_status(instance_id)
            
            if status == 'running':
                print(f"⏳ Arrêt de l'instance {instance_id}...")
                
                response = self.ec2_client.stop_instances(InstanceIds=[instance_id])
                
                # Attendre l'arrêt
                waiter = self.ec2_client.get_waiter('instance_stopped')
                waiter.wait(
                    InstanceIds=[instance_id],
                    WaiterConfig={'Delay': 15, 'MaxAttempts': 20}
                )
                
                print(f"✅ Instance {instance_id} arrêtée")
                return True
                
            elif status == 'stopped':
                print(f"✅ Instance {instance_id} déjà arrêtée")
                return True
                
            else:
                print(f"⚠️ Instance {instance_id} statut: {status}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur arrêt instance: {e}")
            return False
    
    def detach_security_groups(self, instance_id):
        """Détacher les security groups de l'instance"""
        print(f"\n🔥 ÉTAPE 2: VÉRIFICATION SECURITY GROUPS")
        print("=" * 60)
        
        try:
            status, instance = self.check_instance_status(instance_id)
            
            if status == 'stopped':
                sg_ids = [sg['GroupId'] for sg in instance['SecurityGroups']]
                print(f"🔍 Security groups attachés: {sg_ids}")
                
                # Ne pas supprimer les security groups utilisés par la nouvelle instance
                new_status, new_instance = self.check_instance_status(self.new_instance_id)
                if new_status:
                    new_sg_ids = [sg['GroupId'] for sg in new_instance['SecurityGroups']]
                    print(f"🆕 Security groups nouvelle instance: {new_sg_ids}")
                    
                    # Identifier les security groups à supprimer
                    sgs_to_delete = [sg for sg in sg_ids if sg not in new_sg_ids]
                    
                    if sgs_to_delete:
                        print(f"🗑️ Security groups à supprimer: {sgs_to_delete}")
                        return sgs_to_delete
                    else:
                        print("✅ Aucun security group à supprimer (utilisés par nouvelle instance)")
                        return []
                else:
                    print("⚠️ Impossible de vérifier la nouvelle instance")
                    return []
            else:
                print("⚠️ Instance doit être arrêtée pour vérifier les security groups")
                return []
                
        except Exception as e:
            print(f"❌ Erreur vérification security groups: {e}")
            return []
    
    def delete_instance(self, instance_id):
        """Supprimer l'instance EC2"""
        print(f"\n🔥 ÉTAPE 3: SUPPRESSION INSTANCE {instance_id}")
        print("=" * 60)
        
        try:
            status, instance = self.check_instance_status(instance_id)
            
            if status == 'stopped':
                print(f"🗑️ Suppression de l'instance {instance_id}...")
                
                response = self.ec2_client.terminate_instances(InstanceIds=[instance_id])
                
                # Attendre la suppression
                waiter = self.ec2_client.get_waiter('instance_terminated')
                waiter.wait(
                    InstanceIds=[instance_id],
                    WaiterConfig={'Delay': 15, 'MaxAttempts': 20}
                )
                
                print(f"✅ Instance {instance_id} supprimée")
                return True
                
            else:
                print(f"⚠️ Instance doit être arrêtée pour être supprimée (statut: {status})")
                return False
                
        except Exception as e:
            print(f"❌ Erreur suppression instance: {e}")
            return False
    
    def cleanup_resources(self):
        """Nettoyer les ressources associées"""
        print(f"\n🔥 ÉTAPE 4: NETTOYAGE RESSOURCES")
        print("=" * 60)
        
        # Vérifier les volumes
        try:
            response = self.ec2_client.describe_volumes(
                Filters=[
                    {'Name': 'attachment.instance-id', 'Values': [self.old_instance_id]}
                ]
            )
            
            volumes = response['Volumes']
            if volumes:
                print(f"📀 Volumes à nettoyer: {len(volumes)}")
                
                for volume in volumes:
                    volume_id = volume['VolumeId']
                    print(f"🗑️ Suppression volume: {volume_id}")
                    
                    try:
                        self.ec2_client.delete_volume(VolumeId=volume_id)
                        print(f"✅ Volume {volume_id} supprimé")
                    except Exception as e:
                        print(f"❌ Erreur suppression volume {volume_id}: {e}")
            else:
                print("✅ Aucun volume à nettoyer")
                
        except Exception as e:
            print(f"❌ Erreur vérification volumes: {e}")
    
    def verify_new_instance(self):
        """Vérifier que la nouvelle instance fonctionne bien"""
        print(f"\n🔥 ÉTAPE 5: VÉRIFICATION NOUVELLE INSTANCE")
        print("=" * 60)
        
        try:
            status, instance = self.check_instance_status(self.new_instance_id)
            
            if status == 'running':
                public_ip = instance.get('PublicIpAddress', 'N/A')
                print(f"✅ Nouvelle instance opérationnelle: {self.new_instance_id}")
                print(f"🌐 IP Publique: {public_ip}")
                
                # Test de connexion SSH possible
                print(f"🔑 Connexion SSH possible:")
                print(f"C:\\Windows\\System32\\OpenSSH\\ssh.exe -i \"C:\\Users\\maatc\\.ssh\\deepseek_ec2\" ec2-user@{public_ip}")
                
                return True
            else:
                print(f"⚠️ Nouvelle instance statut: {status}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur vérification nouvelle instance: {e}")
            return False
    
    def delete_old_instance_complete(self):
        """Suppression complète de l'ancienne instance"""
        print("🚀 DÉMARRAGE SUPPRESSION ANCIENNE INSTANCE")
        print("=" * 80)
        
        # Étape 1: Vérifier la nouvelle instance
        if not self.verify_new_instance():
            print("❌ La nouvelle instance n'est pas opérationnelle - annulation")
            return False
        
        # Étape 2: Arrêter l'ancienne instance
        if not self.stop_instance(self.old_instance_id):
            print("❌ Impossible d'arrêter l'ancienne instance")
            return False
        
        # Étape 3: Vérifier les security groups
        sgs_to_check = self.detach_security_groups(self.old_instance_id)
        
        # Étape 4: Supprimer l'ancienne instance
        if not self.delete_instance(self.old_instance_id):
            print("❌ Impossible de supprimer l'ancienne instance")
            return False
        
        # Étape 5: Nettoyer les ressources
        self.cleanup_resources()
        
        # Afficher le résumé
        print("\n🎉 SUPPRESSION TERMINÉE AVEC SUCCÈS!")
        print("=" * 80)
        print(f"🗑️ Ancienne instance supprimée: {self.old_instance_id}")
        print(f"🆕 Nouvelle instance active: {self.new_instance_id}")
        print("=" * 80)
        
        # Afficher les informations de la nouvelle instance
        print("\n🌊 CONNECTIVE AI - NOUVELLE INSTANCE:")
        print("=" * 50)
        
        status, instance = self.check_instance_status(self.new_instance_id)
        if status == 'running':
            public_ip = instance.get('PublicIpAddress', 'N/A')
            public_dns = instance.get('PublicDnsName', 'N/A')
            
            print(f"🖥️ Instance ID: {self.new_instance_id}")
            print(f"🌐 IP Publique: {public_ip}")
            print(f"🌐 DNS Public: {public_dns}")
            print(f"🔑 Clé SSH: deepseek_ec2_key")
            
            print(f"\n🔑 COMMANDES DE CONNEXION:")
            print(f"C:\\Windows\\System32\\OpenSSH\\ssh.exe -i \"C:\\Users\\maatc\\.ssh\\deepseek_ec2\" ec2-user@{public_dns}")
            print(f"C:\\Windows\\System32\\OpenSSH\\ssh.exe -i \"C:\\Users\\maatc\\.ssh\\deepseek_ec2\" ec2-user@{public_ip}")
            
            print(f"\n🌊 ENDPOINTS CONNECTIVE AI:")
            print(f"🏠 http://{public_ip}:8000/")
            print(f"❤️ http://{public_ip}:8000/health")
            print(f"🧠 http://{public_ip}:8000/generate")
        
        return True

def main():
    """Fonction principale"""
    print("🗑️ SUPPRESSION ANCIENNE INSTANCE EC2")
    print("=" * 80)
    print("🤖 DEEPSEEK-V4-PRO PHASE 1")
    print("🌊 CONNECTIVE AI")
    print("=" * 80)
    
    # Supprimer l'ancienne instance
    deleter = EC2InstanceDeleter()
    success = deleter.delete_old_instance_complete()
    
    if success:
        print("\n🎉 SUCCÈS TOTAL!")
        print("🗑️ Ancienne instance supprimée")
        print("🌊 Connective AI sur nouvelle instance")
        print("🏆 Prête pour LM Arena domination!")
    else:
        print("\n❌ ÉCHEC SUPPRESSION")
        print("🔧 Vérifiez les logs et réessayez")

if __name__ == "__main__":
    main()
