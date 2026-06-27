"""
🚀 HARMONIC AI - DÉPLOIEMENT SAAS AWS COMPLET
Fichier: aws_saas_deployment.py
Auteur: Équipe Harmonique
Date: 29 avril 2026
Description: Configuration complète pour déploiement SAAS sur AWS
"""

import boto3
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

@dataclass
class AWSSAASConfig:
    """Configuration pour déploiement SAAS AWS"""
    region: str = "us-east-1"
    project_name: str = "harmonic-ai-saas"
    environment: str = "production"
    
    # Compute
    instance_type: str = "t3.large"
    min_instances: int = 1
    max_instances: int = 10
    desired_capacity: int = 2
    
    # Database
    db_engine: str = "aurora-postgresql"
    db_instance_class: str = "db.serverless"
    db_name: str = "harmonic_ai_db"
    
    # Storage
    bucket_name: str = "harmonic-ai-saas-storage"
    
    # Networking
    vpc_cidr: str = "10.0.0.0/16"
    subnet_cidrs: List[str] = None
    
    # Security
    ssl_certificate_arn: str = ""
    
    def __post_init__(self):
        if self.subnet_cidrs is None:
            self.subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]

class HarmonicAISAASTemplate:
    """Template CloudFormation pour déploiement SAAS"""
    
    def __init__(self, config: AWSSAASConfig):
        self.config = config
        self.template = self.create_template()
    
    def create_template(self) -> Dict[str, Any]:
        """Création du template CloudFormation"""
        return {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": "Harmonic AI SAAS Infrastructure",
            "Parameters": self.create_parameters(),
            "Mappings": self.create_mappings(),
            "Resources": self.create_resources(),
            "Outputs": self.create_outputs()
        }
    
    def create_parameters(self) -> Dict[str, Any]:
        """Paramètres du template"""
        return {
            "Environment": {
                "Type": "String",
                "Default": self.config.environment,
                "AllowedValues": ["development", "staging", "production"],
                "Description": "Environment name"
            },
            "InstanceType": {
                "Type": "String",
                "Default": self.config.instance_type,
                "AllowedValues": ["t3.large", "t3.xlarge", "t3.2xlarge", "m5.large", "m5.xlarge"],
                "Description": "EC2 instance type"
            },
            "MinInstances": {
                "Type": "Number",
                "Default": self.config.min_instances,
                "MinValue": "1",
                "MaxValue": "10",
                "Description": "Minimum number of instances"
            },
            "MaxInstances": {
                "Type": "Number",
                "Default": self.config.max_instances,
                "MinValue": "1",
                "MaxValue": "20",
                "Description": "Maximum number of instances"
            },
            "DBPassword": {
                "Type": "String",
                "NoEcho": "true",
                "MinLength": "8",
                "Description": "Database password"
            }
        }
    
    def create_mappings(self) -> Dict[str, Any]:
        """Mappings pour les AMI et autres ressources"""
        return {
            "AWSRegionArch2AMI": {
                "us-east-1": "ami-0c02fb55956c7d316",
                "us-east-2": "ami-0d9eb5b843622c2d4",
                "us-west-1": "ami-0c02fb55956c7d316",
                "us-west-2": "ami-0c02fb55956c7d316"
            }
        }
    
    def create_resources(self) -> Dict[str, Any]:
        """Ressources AWS"""
        return {
            # VPC
            "VPC": {
                "Type": "AWS::EC2::VPC",
                "Properties": {
                    "CidrBlock": self.config.vpc_cidr,
                    "EnableDnsSupport": True,
                    "EnableDnsHostnames": True,
                    "Tags": [
                        {"Key": "Name", "Value": f"{self.config.project_name}-vpc"},
                        {"Key": "Environment", "Value": {"Ref": "Environment"}}
                    ]
                }
            },
            
            # Internet Gateway
            "InternetGateway": {
                "Type": "AWS::EC2::InternetGateway",
                "Properties": {
                    "Tags": [
                        {"Key": "Name", "Value": f"{self.config.project_name}-igw"},
                        {"Key": "Environment", "Value": {"Ref": "Environment"}}
                    ]
                }
            },
            
            "VPCGatewayAttachment": {
                "Type": "AWS::EC2::VPCGatewayAttachment",
                "Properties": {
                    "VpcId": {"Ref": "VPC"},
                    "InternetGatewayId": {"Ref": "InternetGateway"}
                }
            },
            
            # Public Subnets
            "PublicSubnet1": {
                "Type": "AWS::EC2::Subnet",
                "Properties": {
                    "VpcId": {"Ref": "VPC"},
                    "CidrBlock": self.config.subnet_cidrs[0],
                    "AvailabilityZone": {"Fn::Select": [0, {"Fn::GetAZs": {"Region": {"Ref": "AWS::Region"}}}]},
                    "MapPublicIpOnLaunch": True,
                    "Tags": [
                        {"Key": "Name", "Value": f"{self.config.project_name}-public-subnet-1"},
                        {"Key": "Type", "Value": "Public"}
                    ]
                }
            },
            
            "PublicSubnet2": {
                "Type": "AWS::EC2::Subnet",
                "Properties": {
                    "VpcId": {"Ref": "VPC"},
                    "CidrBlock": self.config.subnet_cidrs[1],
                    "AvailabilityZone": {"Fn::Select": [1, {"Fn::GetAZs": {"Region": {"Ref": "AWS::Region"}}}]},
                    "MapPublicIpOnLaunch": True,
                    "Tags": [
                        {"Key": "Name", "Value": f"{self.config.project_name}-public-subnet-2"},
                        {"Key": "Type", "Value": "Public"}
                    ]
                }
            },
            
            # Private Subnets
            "PrivateSubnet1": {
                "Type": "AWS::EC2::Subnet",
                "Properties": {
                    "VpcId": {"Ref": "VPC"},
                    "CidrBlock": self.config.subnet_cidrs[2],
                    "AvailabilityZone": {"Fn::Select": [0, {"Fn::GetAZs": {"Region": {"Ref": "AWS::Region"}}}]},
                    "MapPublicIpOnLaunch": False,
                    "Tags": [
                        {"Key": "Name", "Value": f"{self.config.project_name}-private-subnet-1"},
                        {"Key": "Type", "Value": "Private"}
                    ]
                }
            },
            
            # Route Tables
            "PublicRouteTable": {
                "Type": "AWS::EC2::RouteTable",
                "Properties": {
                    "VpcId": {"Ref": "VPC"},
                    "Tags": [
                        {"Key": "Name", "Value": f"{self.config.project_name}-public-rt"}
                    ]
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
            
            # Security Groups
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
                        },
                        {
                            "IpProtocol": "tcp",
                            "FromPort": 443,
                            "ToPort": 443,
                            "CidrIp": "0.0.0.0/0"
                        }
                    ],
                    "Tags": [
                        {"Key": "Name", "Value": f"{self.config.project_name}-lb-sg"}
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
                        },
                        {
                            "IpProtocol": "tcp",
                            "FromPort": 22,
                            "ToPort": 22,
                            "CidrIp": "0.0.0.0/0"
                        }
                    ],
                    "Tags": [
                        {"Key": "Name", "Value": f"{self.config.project_name}-ec2-sg"}
                    ]
                }
            },
            
            # IAM Role
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
                    }
                    },
                    "Policies": [
                        {
                            "PolicyName": "HarmonicAIEC2Policy",
                            "PolicyDocument": {
                                "Version": "2012-10-17",
                                "Statement": [
                                    {
                                        "Effect": "Allow",
                                        "Action": [
                                            "logs:*",
                                            "cloudwatch:*",
                                            "s3:GetObject",
                                            "s3:PutObject",
                                            "rds:*"
                                        ],
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
            
            # Launch Template
            "LaunchTemplate": {
                "Type": "AWS::EC2::LaunchTemplate",
                "Properties": {
                    "LaunchTemplateName": f"{self.config.project_name}-launch-template",
                    "LaunchTemplateData": {
                        "ImageId": {"Fn::FindInMap": ["AWSRegionArch2AMI", {"Ref": "AWS::Region"}, "AMI"]},
                        "InstanceType": {"Ref": "InstanceType"},
                        "SecurityGroupIds": [{"Ref": "EC2SecurityGroup"}],
                        "IamInstanceProfile": {"Ref": "EC2InstanceProfile"},
                        "UserData": {
                            "Fn::Base64": {
                                "Fn::Sub": "#!/bin/bash\n#!/bin/bash\n# Update system\nyum update -y\n# Install Docker\nyum install -y docker\nsystemctl start docker\nsystemctl enable docker\n# Install Docker Compose\ncurl -L \"https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)\" -o /usr/local/bin/docker-compose\nchmod +x /usr/local/bin/docker-compose\n# Pull Harmonic AI image\ndocker pull harmonic-ai/local:latest\n# Run Harmonic AI container\ndocker run -d --name harmonic-ai -p 5000:5000 harmonic-ai/local:latest\n# Setup auto-restart\ndocker update-rc.d docker defaults\n# Log completion\necho 'Harmonic AI setup complete'\n"
                            }
                        },
                        "TagSpecifications": [
                            {
                                "ResourceType": "instance",
                                "Tags": [
                                    {"Key": "Name", "Value": f"{self.config.project_name}-instance"},
                                    {"Key": "Environment", "Value": {"Ref": "Environment"}}
                                ]
                            }
                        ]
                    }
                }
            },
            
            # Auto Scaling Group
            "AutoScalingGroup": {
                "Type": "AWS::AutoScaling::AutoScalingGroup",
                "Properties": {
                    "AutoScalingGroupName": f"{self.config.project_name}-asg",
                    "VPCZoneIdentifier": [
                        {"Fn::Sub": ["subnet-", {"Ref": "AWS::Region"}, "-a"]},
                        {"Fn::Sub": ["subnet-", {"Ref": "AWS::Region"}, "-b"]}
                    ],
                    "LaunchTemplate": {
                        "LaunchTemplateId": {"Ref": "LaunchTemplate"},
                        "Version": "$Latest"
                    },
                    "MinSize": {"Ref": "MinInstances"},
                    "MaxSize": {"Ref": "MaxInstances"},
                    "DesiredCapacity": {"Ref": "MinInstances"},
                    "TargetGroupARNs": [{"Ref": "TargetGroup"}],
                    "HealthCheckType": "EC2",
                    "HealthCheckGracePeriod": 300,
                    "MetricsCollection": [
                        {
                            "Granularity": "1Minute",
                            "Metrics": ["GroupInServiceInstances", "GroupPendingInstances", "GroupTerminatingInstances"]
                        }
                    ]
                }
            },
            
            # Scaling Policies
            "ScaleUpPolicy": {
                "Type": "AWS::AutoScaling::ScalingPolicy",
                "Properties": {
                    "AutoScalingGroupName": {"Ref": "AutoScalingGroup"},
                    "PolicyType": "SimpleScaling",
                    "ScalingAdjustment": 1,
                    "AdjustmentType": "ChangeInCapacity",
                    "Cooldown": 60
                }
            },
            
            "ScaleDownPolicy": {
                "Type": "AWS::AutoScaling::ScalingPolicy",
                "Properties": {
                    "AutoScalingGroupName": {"Ref": "AutoScalingGroup"},
                    "PolicyType": "SimpleScaling",
                    "ScalingAdjustment": -1,
                    "AdjustmentType": "ChangeInCapacity",
                    "Cooldown": 60
                }
            },
            
            # CloudWatch Alarms
            "CPUHighAlarm": {
                "Type": "AWS::CloudWatch::Alarm",
                "Properties": {
                    "AlarmName": f"{self.config.project_name}-cpu-high",
                    "AlarmDescription": "CPU utilization is high",
                    "MetricName": "CPUUtilization",
                    "Namespace": "AWS/AutoScaling",
                    "Statistic": "Average",
                    "Period": 300,
                    "EvaluationPeriods": 2,
                    "Threshold": 70,
                    "ComparisonOperator": "GreaterThanThreshold",
                    "AlarmActions": [{"Ref": "ScaleUpPolicy"}]
                }
            },
            
            "CPULowAlarm": {
                "Type": "AWS::CloudWatch::Alarm",
                "Properties": {
                    "AlarmName": f"{self.config.project_name}-cpu-low",
                    "AlarmDescription": "CPU utilization is low",
                    "MetricName": "CPUUtilization",
                    "Namespace": "AWS/AutoScaling",
                    "Statistic": "Average",
                    "Period": 300,
                    "EvaluationPeriods": 2,
                    "Threshold": 20,
                    "ComparisonOperator": "LessThanThreshold",
                    "AlarmActions": [{"Ref": "ScaleDownPolicy"}]
                }
            },
            
            # Application Load Balancer
            "LoadBalancer": {
                "Type": "AWS::ElasticLoadBalancingV2::LoadBalancer",
                "Properties": {
                    "Name": f"{self.config.project_name}-alb",
                    "Scheme": "internet-facing",
                    "Type": "application",
                    "Subnets": [{"Ref": "PublicSubnet1"}, {"Ref": "PublicSubnet2"}],
                    "SecurityGroups": [{"Ref": "LoadBalancerSecurityGroup"}],
                    "IpAddressType": "ipv4",
                    "Tags": [
                        {"Key": "Name", "Value": f"{self.config.project_name}-alb"}
                    ]
                }
            },
            
            # Target Group
            "TargetGroup": {
                "Type": "AWS::ElasticLoadBalancingV2::TargetGroup",
                "Properties": {
                    "Name": f"{self.config.project_name}-tg",
                    "Port": 5000,
                    "Protocol": "HTTP",
                    "VpcId": {"Ref": "VPC"},
                    "HealthCheckProtocol": "HTTP",
                    "HealthCheckPort": "5000",
                    "HealthCheckPath": "/api/status",
                    "HealthCheckIntervalSeconds": 30,
                    "HealthCheckTimeoutSeconds": 5,
                    "HealthyThresholdCount": 3,
                    "UnhealthyThresholdCount": 3,
                    "Matcher": {
                        "HttpCode": "200"
                    },
                    "TargetType": "instance"
                }
            },
            
            # Listener
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
            
            # RDS Aurora Serverless
            "DBSubnetGroup": {
                "Type": "AWS::RDS::DBSubnetGroup",
                "Properties": {
                    "DBSubnetGroupDescription": "Subnet group for Harmonic AI database",
                    "SubnetIds": [{"Ref": "PrivateSubnet1"}],
                    "Tags": [
                        {"Key": "Name", "Value": f"{self.config.project_name}-db-subnet-group"}
                    ]
                }
            },
            
            "Database": {
                "Type": "AWS::RDS::DBCluster",
                "Properties": {
                    "DBClusterIdentifier": f"{self.config.project_name}-cluster",
                    "Engine": self.config.db_engine,
                    "EngineMode": "serverless",
                    "MasterUsername": "harmonic_ai",
                    "MasterUserPassword": {"Ref": "DBPassword"},
                    "DBSubnetGroupName": {"Ref": "DBSubnetGroup"},
                    "BackupRetentionPeriod": 7,
                    "PreferredBackupWindow": "03:00-04:00",
                    "PreferredMaintenanceWindow": "sun:04:00-sun:05:00",
                    "StorageEncrypted": True,
                    "EnableHttpEndpoint": True,
                    "ScalingConfiguration": {
                        "MinCapacity": 1,
                        "MaxCapacity": 4
                    }
                }
            },
            
            # S3 Bucket
            "S3Bucket": {
                "Type": "AWS::S3::Bucket",
                "Properties": {
                    "BucketName": self.config.bucket_name,
                    "VersioningConfiguration": {
                        "Status": "Enabled"
                    },
                    "PublicAccessBlockConfiguration": {
                        "BlockPublicAcls": True,
                        "BlockPublicPolicy": True,
                        "IgnorePublicAcls": True,
                        "RestrictPublicBuckets": True
                    },
                    "CorsConfiguration": {
                        "CorsRules": [
                            {
                                "AllowedHeaders": ["*"],
                                "AllowedMethods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                                "AllowedOrigins": ["*"],
                                "MaxAge": 3600
                            }
                        ]
                    }
                }
            },
            
            # CloudFront Distribution
            "CloudFrontDistribution": {
                "Type": "AWS::CloudFront::Distribution",
                "Properties": {
                    "DistributionConfig": {
                        "Origins": [
                            {
                                "Id": "S3Origin",
                                "DomainName": {"Fn::GetAtt": ["S3Bucket", "RegionalDomainName"]},
                                "S3OriginConfig": {
                                    "OriginAccessIdentity": "origin-access-identity/cloudfront"
                                }
                            },
                            {
                                "Id": "ALBOrigin",
                                "DomainName": {"Fn::GetAtt": ["LoadBalancer", "DNSName"]},
                                "CustomOriginConfig": {
                                    "HTTPPort": 80,
                                    "HTTPSPort": 443,
                                    "OriginProtocolPolicy": "https-only"
                                }
                            }
                        ],
                        "DefaultCacheBehavior": {
                            "TargetOriginId": "S3Origin",
                            "ViewerProtocolPolicy": "redirect-to-https",
                            "AllowedMethods": ["GET", "HEAD", "OPTIONS"],
                            "CachedMethods": ["GET", "HEAD"],
                            "ForwardedValues": {
                                "QueryString": False,
                                "Cookies": "none"
                            },
                            "MinTTL": 0,
                            "DefaultTTL": 3600,
                            "MaxTTL": 86400
                        },
                        "CacheBehaviors": [
                            {
                                "PathPattern": "/api/*",
                                "TargetOriginId": "ALBOrigin",
                                "ViewerProtocolPolicy": "https-only",
                                "AllowedMethods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                                "CachedMethods": ["GET", "HEAD", "OPTIONS"],
                                "ForwardedValues": {
                                    "QueryString": True,
                                    "Cookies": "none"
                                },
                                "MinTTL": 0,
                                "DefaultTTL": 0,
                                "MaxTTL": 300
                            }
                        ],
                        "Enabled": True,
                        "DefaultRootObject": "index.html",
                        "HttpVersion": "http2",
                        "PriceClass": "PriceClass_100"
                    }
                }
            }
        }
    
    def create_outputs(self) -> Dict[str, Any]:
        """Outputs du template"""
        return {
            "LoadBalancerDNS": {
                "Description": "DNS name of the load balancer",
                "Value": {"Fn::GetAtt": ["LoadBalancer", "DNSName"]},
                "Export": {
                    "Name": {
                        "Fn::Sub": ["${ProjectName}-${AWS::StackName}", {"ProjectName": self.config.project_name}]
                    }
                }
            },
            "DatabaseEndpoint": {
                "Description": "Database endpoint",
                "Value": {"Fn::GetAtt": ["Database", "Endpoint.Address"]},
                "Export": {
                    "Name": {
                        "Fn::Sub": ["${ProjectName}-${AWS::StackName}", {"ProjectName": self.config.project_name}]
                    }
                }
            },
            "S3BucketName": {
                "Description": "S3 bucket name",
                "Value": {"Ref": "S3Bucket"},
                "Export": {
                    "Name": {
                        "Fn::Sub": ["${ProjectName}-${AWS::StackName}", {"ProjectName": self.config.project_name}]
                    }
                }
            },
            "CloudFrontDomain": {
                "Description": "CloudFront distribution domain name",
                "Value": {"Fn::GetAtt": ["CloudFrontDistribution", "DomainName"]},
                "Export": {
                    "Name": {
                        "Fn::Sub": ["${ProjectName}-${AWS::StackName}", {"ProjectName": self.config.project_name}]
                    }
                }
            }
        }
    
    def save_template(self, filename: str):
        """Sauvegarde du template"""
        with open(filename, 'w') as f:
            yaml.dump(self.template, f, default_flow_style=False)

class AWSDeploymentManager:
    """Manager pour le déploiement AWS"""
    
    def __init__(self, config: AWSSAASConfig):
        self.config = config
        self.cf_client = boto3.client('cloudformation', region_name=config.region)
        self.ec2_client = boto3.client('ec2', region_name=config.region)
        self.s3_client = boto3.client('s3', region_name=config.region)
        
    def deploy_stack(self) -> Dict[str, Any]:
        """Déploiement de la stack CloudFormation"""
        template = HarmonicAISAASTemplate(self.config)
        template.save_template('harmonic-ai-saas-template.yaml')
        
        try:
            response = self.cf_client.create_stack(
                StackName=self.config.project_name,
                TemplateBody=yaml.dump(template.template),
                Capabilities=['CAPABILITY_NAMED_IAM'],
                Parameters={
                    'Environment': self.config.environment,
                    'InstanceType': self.config.instance_type,
                    'MinInstances': self.config.min_instances,
                    'MaxInstances': self.config.max_instances,
                    'DBPassword': self.generate_secure_password()
                },
                OnFailure='ROLLBACK',
                TimeoutInMinutes=30
            )
            
            return {
                'status': 'CREATE_IN_PROGRESS',
                'stack_id': response['StackId'],
                'message': 'Stack creation initiated'
            }
            
        except self.cf_client.exceptions.AlreadyExistsException:
            return self.update_stack()
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def update_stack(self) -> Dict[str, Any]:
        """Mise à jour de la stack"""
        template = HarmonicAISAASTemplate(self.config)
        
        try:
            response = self.cf_client.update_stack(
                StackName=self.config.project_name,
                TemplateBody=yaml.dump(template.template),
                Capabilities=['CAPABILITY_NAMED_IAM'],
                Parameters={
                    'Environment': self.config.environment,
                    'InstanceType': self.config.instance_type,
                    'MinInstances': self.config.min_instances,
                    'MaxInstances': self.config.max_instances
                }
            )
            
            return {
                'status': 'UPDATE_IN_PROGRESS',
                'stack_id': response['StackId'],
                'message': 'Stack update initiated'
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def get_stack_status(self) -> Dict[str, Any]:
        """Statut de la stack"""
        try:
            response = self.cf_client.describe_stacks(StackName=self.config.project_name)
            stack = response['Stacks'][0]
            
            return {
                'status': stack['StackStatus'],
                'creation_time': stack['CreationTime'],
                'last_updated_time': stack.get('LastUpdatedTime'),
                'outputs': stack.get('Outputs', {}),
                'parameters': stack.get('Parameters', [])
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def delete_stack(self) -> Dict[str, Any]:
        """Suppression de la stack"""
        try:
            response = self.cf_client.delete_stack(
                StackName=self.config.project_name
            )
            
            return {
                'status': 'DELETE_IN_PROGRESS',
                'message': 'Stack deletion initiated'
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def generate_secure_password(self) -> str:
        """Génération d'un mot de passe sécurisé"""
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for i in range(16))
        
        return password
    
    def create_deployment_script(self) -> str:
        """Script de déploiement"""
        return f"""
#!/bin/bash

echo "🚀 Déploiement Harmonic AI SAAS sur AWS"
echo "=========================================="

# Configuration
AWS_REGION="{self.config.region}"
STACK_NAME="{self.config.project_name}"

# Vérification AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI non installé"
    exit 1
fi

# Vérification des permissions
aws sts get-caller-identity

# Déploiement de la stack
echo "🌊 Déploiement de la stack CloudFormation..."
aws cloudformation create-stack \\
    --stack-name $STACK_NAME \\
    --template-body file://harmonic-ai-saas-template.yaml \\
    --capabilities CAPABILITY_NAMED_IAM \\
    --parameters ParameterKey=Environment,ParameterValue=production \\
    --parameters ParameterKey=InstanceType,ParameterValue={self.config.instance_type} \\
    --parameters ParameterKey=MinInstances,ParameterValue={self.config.min_instances} \\
    --parameters ParameterKey=MaxInstances,ParameterValue={self.config.max_instances} \\
    --region $AWS_REGION

# Attente du déploiement
echo "⏳ Attente du déploiement..."
aws cloudformation wait stack-create-complete \\
    --stack-name $STACK_NAME \\
    --region $AWS_REGION

# Récupération des outputs
echo "📊 Récupération des informations de déploiement..."
aws cloudformation describe-stacks \\
    --stack-name $STACK_NAME \\
    --region $AWS_REGION \\
    --query 'Stacks[0].Outputs'

echo "✅ Déploiement terminé !"
echo "🌐 Accès à l'application :"
echo "   Load Balancer DNS : $(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==LoadBalancerDNS].OutputValue' --region $AWS_REGION --output text)"
echo "   Database Endpoint : $(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==DatabaseEndpoint].OutputValue' --region $AWS_REGION --output text)"
echo "   S3 Bucket : $(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==S3BucketName].OutputValue' --region $AWS_REGION --output text)"
echo "   CloudFront Domain : $(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==CloudFrontDomain].OutputValue' --region $AWS_REGION --output text)"
"""

# Point d'entrée pour les tests
if __name__ == "__main__":
    print("🚀 HARMONIC AI - DÉPLOIEMENT SAAS AWS")
    print("=" * 50)
    
    # Configuration
    config = AWSSAASConfig(
        region="us-east-1",
        project_name="harmonic-ai-saas",
        environment="production",
        instance_type="t3.large",
        min_instances=1,
        max_instances=10
    )
    
    # Manager
    manager = AWSDeploymentManager(config)
    
    # Déploiement
    result = manager.deploy_stack()
    print(f"📊 Résultat: {result}")
    
    # Création du script
    with open('deploy_aws_saas.sh', 'w') as f:
        f.write(manager.create_deployment_script())
    
    print("✅ Script de déploiement créé: deploy_aws_saas.sh")
