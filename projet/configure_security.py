#!/usr/bin/env python3
"""
Script pour configurer les règles de sécurité EC2
"""

import subprocess
import json
import sys

def check_aws_permissions():
    """Vérifier les permissions AWS"""
    print("Checking AWS permissions...")
    
    commands = [
        "aws sts get-caller-identity",
        "aws ec2 describe-regions --query 'Regions[].RegionName' --output text",
    ]
    
    for cmd in commands:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                print(f"  Command failed: {cmd}")
                print(f"  Error: {result.stderr[:200]}")
                return False
        except:
            print(f"  Error executing: {cmd}")
            return False
    
    print("  AWS credentials are valid")
    return True

def get_instance_info():
    """Obtenir les informations de l'instance"""
    print("\nGetting EC2 instance information...")
    
    # Essayer de trouver l'instance par son nom
    cmd = 'aws ec2 describe-instances --filters "Name=tag:Name,Values=qwen35-ec2-server" --query "Reservations[].Instances[]" --output json --region us-east-1'
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout.strip():
            instances = json.loads(result.stdout)
            
            if instances:
                instance = instances[0]
                instance_id = instance.get("InstanceId")
                state = instance.get("State", {}).get("Name")
                public_ip = instance.get("PublicIpAddress")
                private_ip = instance.get("PrivateIpAddress")
                security_groups = instance.get("SecurityGroups", [])
                
                print(f"  Instance ID: {instance_id}")
                print(f"  State: {state}")
                print(f"  Public IP: {public_ip}")
                print(f"  Private IP: {private_ip}")
                print(f"  Security Groups: {len(security_groups)}")
                
                for sg in security_groups:
                    print(f"    - {sg.get('GroupName')} ({sg.get('GroupId')})")
                
                return {
                    "instance_id": instance_id,
                    "state": state,
                    "public_ip": public_ip,
                    "private_ip": private_ip,
                    "security_groups": security_groups
                }
            else:
                print("  No instance found with name 'qwen35-ec2-server'")
        else:
            print(f"  Error: {result.stderr[:200]}")
            
    except Exception as e:
        print(f"  Error: {str(e)[:200]}")
    
    return None

def check_security_group_rules(group_id):
    """Vérifier les règles du groupe de sécurité"""
    print(f"\nChecking security group rules for {group_id}...")
    
    cmd = f'aws ec2 describe-security-groups --group-ids {group_id} --query "SecurityGroups[0]" --output json --region us-east-1'
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            sg = json.loads(result.stdout)
            
            inbound = sg.get("IpPermissions", [])
            outbound = sg.get("IpPermissionsEgress", [])
            
            print(f"  Inbound rules: {len(inbound)}")
            print(f"  Outbound rules: {len(outbound)}")
            
            # Vérifier les ports importants
            important_ports = [22, 80, 443, 8080, 8000]
            
            for port in important_ports:
                port_open = False
                
                for rule in inbound:
                    from_port = rule.get("FromPort")
                    to_port = rule.get("ToPort")
                    
                    if from_port and to_port:
                        if from_port <= port <= to_port:
                            port_open = True
                            cidr_ips = [ip_range.get("CidrIp", "") for ip_range in rule.get("IpRanges", [])]
                            print(f"    Port {port}: OPEN (CIDR: {', '.join(cidr_ips)})")
                            break
                
                if not port_open:
                    print(f"    Port {port}: CLOSED")
            
            return sg
            
        else:
            print(f"  Error: {result.stderr[:200]}")
            
    except Exception as e:
        print(f"  Error: {str(e)[:200]}")
    
    return None

def add_security_group_rule(group_id, port, description):
    """Ajouter une règle au groupe de sécurité"""
    print(f"\nAdding rule for port {port} to security group {group_id}...")
    
    cmd = f'aws ec2 authorize-security-group-ingress --group-id {group_id} --protocol tcp --port {port} --cidr 0.0.0.0/0 --description "{description}" --region us-east-1'
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"  Success: Port {port} opened to 0.0.0.0/0")
            return True
        else:
            print(f"  Error: {result.stderr[:200]}")
            
    except Exception as e:
        print(f"  Error: {str(e)[:200]}")
    
    return False

def main():
    """Fonction principale"""
    print("EC2 Security Configuration Tool")
    print("=" * 50)
    
    # Vérifier les permissions
    if not check_aws_permissions():
        print("\nERROR: Insufficient AWS permissions")
        print("\nRequired permissions:")
        print("  - ec2:DescribeInstances")
        print("  - ec2:DescribeSecurityGroups")
        print("  - ec2:AuthorizeSecurityGroupIngress (if adding rules)")
        print("\nPlease update IAM permissions and try again.")
        return
    
    # Obtenir les informations de l'instance
    instance_info = get_instance_info()
    
    if not instance_info:
        print("\nERROR: Could not retrieve instance information")
        return
    
    # Vérifier l'état de l'instance
    if instance_info["state"] != "running":
        print(f"\nERROR: Instance is not running (state: {instance_info['state']})")
        print("Please start the instance first.")
        return
    
    # Vérifier l'adresse IP publique
    if not instance_info["public_ip"]:
        print("\nWARNING: Instance does not have a public IP address")
        print("The instance may be in a private subnet.")
        return
    
    print(f"\nInstance is running at: {instance_info['public_ip']}")
    
    # Vérifier les groupes de sécurité
    for sg in instance_info["security_groups"]:
        group_id = sg.get("GroupId")
        group_name = sg.get("GroupName")
        
        print(f"\nAnalyzing security group: {group_name} ({group_id})")
        
        sg_info = check_security_group_rules(group_id)
        
        if sg_info:
            # Vérifier si le port 8080 est ouvert
            port_8080_open = False
            
            for rule in sg_info.get("IpPermissions", []):
                from_port = rule.get("FromPort")
                to_port = rule.get("ToPort")
                
                if from_port and to_port:
                    if from_port <= 8080 <= to_port:
                        port_8080_open = True
                        break
            
            if not port_8080_open:
                print("\nPort 8080 is not open. This is likely why the API is not accessible.")
                
                response = input("\nDo you want to open port 8080? (yes/no): ")
                
                if response.lower() == "yes":
                    success = add_security_group_rule(
                        group_id, 
                        8080, 
                        "Qwen3.5 API access"
                    )
                    
                    if success:
                        print("\nSUCCESS: Port 8080 has been opened.")
                        print(f"You can now test the API at: http://{instance_info['public_ip']}:8080/health")
                    else:
                        print("\nERROR: Failed to open port 8080")
                else:
                    print("\nPort 8080 remains closed. The API will not be accessible.")
            else:
                print("\nPort 8080 is already open.")
                
                # Tester la connectivité
                print(f"\nTesting connectivity to port 8080...")
                test_cmd = f"curl -s -o /dev/null -w '%{{http_code}}' http://{instance_info['public_ip']}:8080/health --max-time 5"
                
                try:
                    result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        http_code = result.stdout.strip()
                        print(f"  HTTP Status: {http_code}")
                        
                        if http_code == "200":
                            print("\nSUCCESS: API is accessible!")
                            print(f"  Health check: http://{instance_info['public_ip']}:8080/health")
                            print(f"  Generate endpoint: http://{instance_info['public_ip']}:8080/generate")
                        else:
                            print("\nWARNING: Port is open but API may not be responding correctly")
                            print("Check if the Qwen3.5 service is running on the instance.")
                    else:
                        print(f"  Error: {result.stderr[:200]}")
                        
                except:
                    print("  Timeout or error testing connectivity")
    
    print("\n" + "=" * 50)
    print("Configuration complete")
    print("=" * 50)

if __name__ == "__main__":
    main()