"""
🚀 HARMONIC AI - DÉPLOIEMENT SAAS AWS COMPLET
Fichier: final_deployment.py
Auteur: Équipe Harmonique
Date: 29 avril 2026
Description: Version finale corrigée et validée
"""

import boto3
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

@dataclass
class AWSSAASConfig:
    region: str = "us-east-1"
    project_name: str = "harmonic-ai-saas"
    environment: str = "staging"
    instance_type: str = "t3.large"
    min_instances: int = 1
    max_instances: int = 10
    db_engine: str = "aurora-postgresql"
    db_name: str = "harmonic_ai_db"
    bucket_name: str = "harmonic-ai-saas-storage"
    vpc_cidr: str = "10.0.0.0/16"
    subnet_cidrs: List[str] = None

    def __post_init__(self):
        if self.subnet_cidrs is None:
            self.subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]

class HarmonicAISAASTemplate:
    def __init__(self, config: AWSSAASConfig):
        self.config = config
        self.template = self.create_template()

    def create_template(self) -> Dict[str, Any]:
        return {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": "Harmonic AI SAAS Infrastructure",
            "Parameters": self.create_parameters(),
            "Mappings": self.create_mappings(),
            "Resources": self.create_resources(),
            "Outputs": self.create_outputs()
        }

    def create_parameters(self) -> Dict[str, Any]:
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
        return {
            "AWSRegionArch2AMI": {
                "us-east-1": "ami-0c02fb55956c7d316",
                "us-east-2": "ami-0d9eb5b843622c2d4",
                "us-west-1": "ami-0c02fb55956c7d316",
                "us-west-2": "ami-0c02fb55956c7d316"
            }
        }

    def create_resources(self) -> Dict[str, Any]:
        return {
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
            "PublicSubnet1": {
                "Type": "AWS::EC2::Subnet",
                "Properties": {
                    "VpcId": {"Ref": "VPC"},
                    "CidrBlock": self.config.subnet_cidrs[0],
                    "AvailabilityZone": {"Fn::Select": [0, {"Fn::GetAZs": {"Region": {"Ref": "AWS::Region"}}]},
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
                    "AvailabilityZone": {"Fn::Select": [1, {"Fn::GetAZs": {"Region": {"Ref": "AWS::Region"}}]},
                    "MapPublicIpOnLaunch": True,
                    "Tags": [
                        {"Key": "Name", "Value": f"{self.config.project_name}-public-subnet-2"},
                        {"Key": "Type", "Value": "Public"}
                    ]
                }
            },
            "PrivateSubnet1": {
                "Type": "AWS::EC2::Subnet",
                "Properties": {
                    "VpcId": {"Ref": "VPC"},
                    "CidrBlock": self.config.subnet_cidrs[2],
                    "AvailabilityZone": {"Fn::Select": [0, {"Fn::GetAZs": {"Region": {"Ref": "AWS::Region"}}]},
                    "MapPublicIpOnLaunch": False,
                    "Tags": [
                        {"Key": "Name", "Value": f"{self.config.project_name}-private-subnet-1"},
                        {"Key": "Type", "Value": "Private"}
                    ]
                }
            },
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