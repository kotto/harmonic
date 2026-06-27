#!/usr/bin/env python3
"""
Vérifier le statut de l'instance EC2 qwen35-ec2-server
"""

import subprocess
import json
import sys

def check_ec2_status():
    """Vérifier le statut de l'instance EC2"""
    print("Verification du statut de l'instance EC2...")
    
    # Essayer différentes requêtes pour trouver l'instance
    commands = [
        'aws ec2 describe-instances --filters "Name=tag:Name,Values=qwen35-ec2-server" --query "Reservations[].Instances[]" --output json --region us-east-1',
        'aws ec2 describe-instances --filters "Name=tag:Name,Values=qwen35-production-instance" --query "Reservations[].Instances[]" --output json --region us-east-1',
        'aws ec2 describe-instances --filters "Name=instance-state-name,Values=running" --query "Reservations[].Instances[]" --output json --region us-east-1'
    ]
    
    for cmd in commands:
        try:
            print(f"\nExecution: {cmd}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                if result.stdout.strip() and result.stdout.strip() != '[]':
                    instances = json.loads(result.stdout)
                    
                    if isinstance(instances, list) and len(instances) > 0:
                        print("\n=== INSTANCE(S) TROUVEE(S) ===")
                        
                        for i, instance in enumerate(instances):
                            print(f"\nInstance {i+1}:")
                            print(f"  ID: {instance.get('InstanceId', 'N/A')}")
                            print(f"  Type: {instance.get('InstanceType', 'N/A')}")
                            print(f"  Statut: {instance.get('State', {}).get('Name', 'N/A')}")
                            print(f"  IP Publique: {instance.get('PublicIpAddress', 'N/A')}")
                            print(f"  IP Privee: {instance.get('PrivateIpAddress', 'N/A')}")
                            
                            # Afficher les tags
                            tags = instance.get('Tags', [])
                            if tags:
                                print(f"  Tags:")
                                for tag in tags:
                                    print(f"    {tag.get('Key')}: {tag.get('Value')}")
                            
                            # Afficher le security group
                            security_groups = instance.get('SecurityGroups', [])
                            if security_groups:
                                print(f"  Security Groups:")
                                for sg in security_groups:
                                    print(f"    - {sg.get('GroupName')} (ID: {sg.get('GroupId')})")
                        
                        return instances
                    else:
                        print("  Aucune instance dans la reponse")
                else:
                    print("  Reponse vide")
            else:
                print(f"  Erreur: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("  Timeout")
        except Exception as e:
            print(f"  Exception: {e}")
    
    print("\n❌ Aucune instance trouvee avec les filtres utilises")
    return []

def check_security_group(instance):
    """Verifier les regles du security group"""
    if not instance.get('SecurityGroups'):
        print("\n⚠️  Aucun security group associe a l'instance")
        return
    
    print("\n=== REGLES DE SECURITE ===")
    
    for sg in instance.get('SecurityGroups', []):
        sg_id = sg.get('GroupId')
        sg_name = sg.get('GroupName')
        
        print(f"\nSecurity Group: {sg_name} (ID: {sg_id})")
        
        # Obtenir les details du security group
        cmd = f'aws ec2 describe-security-groups --group-ids {sg_id} --query "SecurityGroups[0]" --output json --region us-east-1'
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                sg_details = json.loads(result.stdout)
                
                # Regles entrantes
                ingress = sg_details.get('IpPermissions', [])
                if ingress:
                    print("  Regles entrantes (Ingress):")
                    for rule in ingress:
                        from_port = rule.get('FromPort', 'all')
                        to_port = rule.get('ToPort', 'all')
                        ip_protocol = rule.get('IpProtocol', 'all')
                        
                        ip_ranges = rule.get('IpRanges', [])
                        for ip_range in ip_ranges:
                            cidr = ip_range.get('CidrIp', '0.0.0.0/0')
                            print(f"    - {ip_protocol}:{from_port}-{to_port} from {cidr}")
                else:
                    print("  Aucune regle entrante")
                
                # Regles sortantes
                egress = sg_details.get('IpPermissionsEgress', [])
                if egress:
                    print("  Regles sortantes (Egress):")
                    for rule in egress:
                        from_port = rule.get('FromPort', 'all')
                        to_port = rule.get('ToPort', 'all')
                        ip_protocol = rule.get('IpProtocol', 'all')
                        
                        ip_ranges = rule.get('IpRanges', [])
                        for ip_range in ip_ranges:
                            cidr = ip_range.get('CidrIp', '0.0.0.0/0')
                            print(f"    - {ip_protocol}:{from_port}-{to_port} to {cidr}")
                else:
                    print("  Aucune regle sortante")
                    
            else:
                print(f"  Erreur: {result.stderr}")
                
        except Exception as e:
            print(f"  Exception: {e}")

def main():
    """Fonction principale"""
    print("=== VERIFICATION INSTANCE EC2 ===")
    print("Instance: qwen35-ec2-server")
    print("Region: us-east-1")
    print("=" * 40)
    
    # Verifier le statut de l'instance
    instances = check_ec2_status()
    
    if not instances:
        print("\n💡 Recommendations:")
        print("1. Verifiez que l'instance est en cours d'execution")
        print("2. Verifiez les permissions AWS (IAM)")
        print("3. L'instance peut ne pas avoir d'IP publique")
        print("4. Les tags peuvent etre differents")
        return
    
    # Pour chaque instance, verifier le security group
    for instance in instances:
        check_security_group(instance)
        
        # Verifier si l'instance a une IP publique
        public_ip = instance.get('PublicIpAddress')
        if not public_ip:
            print("\n⚠️  ATTENTION: Cette instance n'a pas d'adresse IP publique")
            print("   Elle ne peut pas etre accessible depuis Internet")
            print("   Solutions:")
            print("   - Associer une Elastic IP")
            print("   - Utiliser un bastion host")
            print("   - Configurer un VPN/VPC Peering")
        else:
            print(f"\n✅ Instance accessible a l'adresse: {public_ip}")
            print("   Ports a tester: 8080, 8000, 80")
    
    print("\n" + "=" * 40)
    print("Pour tester l'API, utilisez:")
    print("curl http://<IP_PUBLIQUE>:8080/health")
    print("curl -X POST http://<IP_PUBLIQUE>:8080/generate \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{\"prompt\": \"Test\", \"max_length\": 100}'")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\nErreur: {e}")
        sys.exit(1)