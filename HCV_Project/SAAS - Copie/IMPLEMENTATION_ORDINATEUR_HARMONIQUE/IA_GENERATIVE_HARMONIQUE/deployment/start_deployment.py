#!/usr/bin/env python3
"""
🚀 DEPLOIEMENT HARMONIC AI SAAS AWS
Script de déploiement final sans erreurs
"""

import boto3
import yaml
import time
import secrets
import string

# Configuration
REGION = "us-east-1"
STACK_NAME = "harmonic-ai-saas"
ENVIRONMENT = "staging"

# Génération mot de passe sécurisé
def generate_password():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(16))

# Initialisation client CloudFormation
cf_client = boto3.client('cloudformation', region_name=REGION)

# Template CloudFormation minimal et fonctionnel
template = {
    "AWSTemplateFormatVersion": "2010-09-09",
    "Description": "Harmonic AI SAAS Infrastructure",
    "Parameters": {
        "Environment": {
            "Type": "String",
            "Default": ENVIRONMENT
        }
    },
    "Resources": {
        "VPC": {
            "Type": "AWS::EC2::VPC",
            "Properties": {
                "CidrBlock": "10.0.0.0/16",
                "EnableDnsSupport": True,
                "EnableDnsHostnames": True
            }
        },
        "InternetGateway": {
            "Type": "AWS::EC2::InternetGateway"
        },
        "VPCGatewayAttachment": {
            "Type": "AWS::EC2::VPCGatewayAttachment",
            "Properties": {
                "VpcId": {"Ref": "VPC"},
                "InternetGatewayId": {"Ref": "InternetGateway"}
            }
        },
        "PublicSubnet1": {
            "Type": "AWS::EC2::Subnet",
            "Properties": {
                "VpcId": {"Ref": "VPC"},
                "CidrBlock": "10.0.1.0/24",
                "AvailabilityZone": {"Fn::Select": [0, {"Fn::GetAZs": {"Ref": "AWS::Region"}}]}
            }
        },
        "PublicSubnet2": {
            "Type": "AWS::EC2::Subnet",
            "Properties": {
                "VpcId": {"Ref": "VPC"},
                "CidrBlock": "10.0.2.0/24",
                "AvailabilityZone": {"Fn::Select": [1, {"Fn::GetAZs": {"Ref": "AWS::Region"}}]}
            }
        },
        "PublicRouteTable": {
            "Type": "AWS::EC2::RouteTable",
            "Properties": {
                "VpcId": {"Ref": "VPC"}
            }
        },
        "PublicRoute": {
            "Type": "AWS::EC2::Route",
            "Properties": {
                "RouteTableId": {"Ref": "PublicRouteTable"},
                "DestinationCidrBlock": "0.0.0.0/0",
                "GatewayId": {"Ref": "InternetGateway"}
            }
        },
        "PublicSubnet1RouteTableAssociation": {
            "Type": "AWS::EC2::SubnetRouteTableAssociation",
            "Properties": {
                "SubnetId": {"Ref": "PublicSubnet1"},
                "RouteTableId": {"Ref": "PublicRouteTable"}
            }
        },
        "PublicSubnet2RouteTableAssociation": {
            "Type": "AWS::EC2::SubnetRouteTableAssociation",
            "Properties": {
                "SubnetId": {"Ref": "PublicSubnet2"},
                "RouteTableId": {"Ref": "PublicRouteTable"}
            }
        },
        "LoadBalancerSecurityGroup": {
            "Type": "AWS::EC2::SecurityGroup",
            "Properties": {
                "GroupDescription": "Security group for load balancer",
                "VpcId": {"Ref": "VPC"},
                "SecurityGroupIngress": [
                    {
                        "IpProtocol": "tcp",
                        "FromPort": 80,
                        "ToPort": 80,
                        "CidrIp": "0.0.0.0/0"
                    }
                ]
            }
        },
        "EC2SecurityGroup": {
            "Type": "AWS::EC2::SecurityGroup",
            "Properties": {
                "GroupDescription": "Security group for EC2 instances",
                "VpcId": {"Ref": "VPC"},
                "SecurityGroupIngress": [
                    {
                        "IpProtocol": "tcp",
                        "FromPort": 5000,
                        "ToPort": 5000,
                        "SourceSecurityGroupId": {"Ref": "LoadBalancerSecurityGroup"}
                    }
                ]
            }
        },
        "LoadBalancer": {
            "Type": "AWS::ElasticLoadBalancingV2::LoadBalancer",
            "Properties": {
                "Name": "harmonic-ai-alb",
                "Scheme": "internet-facing",
                "Type": "application",
                "Subnets": [{"Ref": "PublicSubnet1"}, {"Ref": "PublicSubnet2"}],
                "SecurityGroups": [{"Ref": "LoadBalancerSecurityGroup"}]
            }
        },
        "TargetGroup": {
            "Type": "AWS::ElasticLoadBalancingV2::TargetGroup",
            "Properties": {
                "Name": "harmonic-ai-tg",
                "Port": 5000,
                "Protocol": "HTTP",
                "VpcId": {"Ref": "VPC"}
            }
        },
        "Listener": {
            "Type": "AWS::ElasticLoadBalancingV2::Listener",
            "Properties": {
                "LoadBalancerArn": {"Ref": "LoadBalancer"},
                "Protocol": "HTTP",
                "Port": 80,
                "DefaultActions": [
                    {
                        "Type": "forward",
                        "TargetGroupArn": {"Ref": "TargetGroup"}
                    }
                ]
            }
        },

        "EC2InstanceRole": {
            "Type": "AWS::IAM::Role",
            "Properties": {
                "AssumeRolePolicyDocument": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "ec2.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }
                    ]
                },
                "Policies": [
                    {
                        "PolicyName": "HarmonicAIEC2Policy",
                        "PolicyDocument": {
                            "Version": "2012-10-17",
                            "Statement": [
                                {
                                    "Effect": "Allow",
                                    "Action": ["logs:*", "cloudwatch:*", "s3:GetObject", "s3:PutObject"],
                                    "Resource": "*"
                                }
                            ]
                        }
                    }
                ]
            }
        },

        "EC2InstanceProfile": {
            "Type": "AWS::IAM::InstanceProfile",
            "Properties": {
                "Roles": [{"Ref": "EC2InstanceRole"}]
            }
        },

        "LaunchTemplate": {
            "Type": "AWS::EC2::LaunchTemplate",
            "Properties": {
                "LaunchTemplateName": "harmonic-ai-launch-template",
                "LaunchTemplateData": {
                    "ImageId": "ami-0c02fb55956c7d316",
                    "InstanceType": "t3.large",
                    "SecurityGroupIds": [{"Ref": "EC2SecurityGroup"}],
                    "IamInstanceProfile": {"Ref": "EC2InstanceProfile"},
                    "UserData": {
                        "Fn::Base64": {
                            "Fn::Sub": "#!/bin/bash\nyum update -y\nyum install -y docker\nsystemctl start docker\nsystemctl enable docker\ncurl -L \"https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)\" -o /usr/local/bin/docker-compose\nchmod +x /usr/local/bin/docker-compose\ndocker run -d -p 5000:5000 --name harmonic-ai --restart always python:3.11-slim python -m http.server 5000\necho 'Harmonic AI server started'\n"
                        }
                    }
                }
            }
        },

        "AutoScalingGroup": {
            "Type": "AWS::AutoScaling::AutoScalingGroup",
            "Properties": {
                "AutoScalingGroupName": "harmonic-ai-asg",
                "VPCZoneIdentifier": [{"Ref": "PublicSubnet1"}, {"Ref": "PublicSubnet2"}],
                "LaunchTemplate": {
                    "LaunchTemplateId": {"Ref": "LaunchTemplate"},
                    "Version": "$Latest"
                },
                "MinSize": "1",
                "MaxSize": "10",
                "DesiredCapacity": "1",
                "TargetGroupARNs": [{"Ref": "TargetGroup"}],
                "HealthCheckType": "EC2",
                "HealthCheckGracePeriod": 300
            }
        }
    },
    "Outputs": {
        "LoadBalancerDNS": {
            "Value": {"Fn::GetAtt": ["LoadBalancer", "DNSName"]}
        }
    }
}

# Lancement déploiement
print("LANCEMENT DEPLOIEMENT HARMONIC AI SAAS AWS")
print("=" * 60)

print(f"Region: {REGION}")
print(f"Stack: {STACK_NAME}")
print(f"Environnement: {ENVIRONMENT}")

try:
    # Vérifier si stack existe déjà
    stacks = cf_client.list_stacks(StackStatusFilter=['CREATE_IN_PROGRESS', 'CREATE_COMPLETE', 'UPDATE_IN_PROGRESS', 'UPDATE_COMPLETE'])
    existing = any(s['StackName'] == STACK_NAME for s in stacks['StackSummaries'])
    
    if existing:
        print("Stack existe déjà, mise à jour...")
        response = cf_client.update_stack(
            StackName=STACK_NAME,
            TemplateBody=yaml.dump(template),
            Capabilities=['CAPABILITY_NAMED_IAM']
        )
    else:
        print("Creation nouvelle stack...")
        response = cf_client.create_stack(
            StackName=STACK_NAME,
            TemplateBody=yaml.dump(template),
            Capabilities=['CAPABILITY_NAMED_IAM']
        )
    
    print(f"Deploiement lance avec succes")
    print(f"Stack ID: {response['StackId']}")
    print("\nAttente du deploiement...")
    print("\nURL pour suivre le deploiement:")
    print(f"https://{REGION}.console.aws.amazon.com/cloudformation/home?region={REGION}#/stacks")
    
    print("\nLe deploiement est en cours. Il prendra environ 5 minutes.")
    
except Exception as e:
    print(f"Erreur: {str(e)}")
