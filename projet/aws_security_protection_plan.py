#!/usr/bin/env python3
"""
Plan de protection AWS contre le reverse engineering
Pour Harmonic AI - Architecture sécurisée
"""

import json
import hashlib
import base64
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import secrets

class AWSSecurityProtectionPlan:
    """Plan complet de protection AWS pour Harmonic AI"""
    
    def __init__(self):
        self.plan_id = self._generate_plan_id()
        self.creation_date = datetime.now()
        
    def _generate_plan_id(self) -> str:
        """Génère un ID unique pour le plan"""
        timestamp = int(time.time() * 1000)
        random_part = secrets.token_hex(8)
        return f"security-plan-{timestamp}-{random_part}"
    
    def generate_comprehensive_protection_plan(self) -> Dict[str, Any]:
        """Génère un plan complet de protection AWS"""
        
        plan = {
            "plan_id": self.plan_id,
            "creation_date": self.creation_date.isoformat(),
            "overview": "Plan de protection AWS complet pour Harmonic AI - Protection contre le reverse engineering et attaques",
            "last_updated": datetime.now().isoformat(),
            
            "protection_layers": {
                "layer_1": {
                    "name": "Obfuscation du code source",
                    "description": "Protection du code Python contre le reverse engineering",
                    "techniques": [
                        {
                            "name": "Bytecode compilation",
                            "description": "Compilation en .pyc avec optimisation",
                            "implementation": "python -m compileall -f -b .",
                            "effectiveness": "HIGH",
                            "tools": ["Nuitka", "Cython", "PyInstaller"]
                        },
                        {
                            "name": "String encryption",
                            "description": "Chiffrement des chaînes sensibles dans le code",
                            "implementation": "AES-256 avec clé dérivée de l'environnement",
                            "effectiveness": "HIGH",
                            "tools": ["cryptography", "pycryptodome"]
                        },
                        {
                            "name": "Control flow obfuscation",
                            "description": "Modification du flux de contrôle pour rendre le code illisible",
                            "implementation": "Insertion de sauts conditionnels inutiles",
                            "effectiveness": "MEDIUM",
                            "tools": ["pyobfuscate", "pyminifier"]
                        },
                        {
                            "name": "Name mangling",
                            "description": "Modification des noms de variables et fonctions",
                            "implementation": "Remplacement par des noms aléatoires",
                            "effectiveness": "MEDIUM",
                            "tools": ["pyminifier", "custom script"]
                        }
                    ]
                },
                
                "layer_2": {
                    "name": "Sécurité des instances EC2",
                    "description": "Protection des serveurs d'inférence AWS",
                    "techniques": [
                        {
                            "name": "Security Groups restrictives",
                            "description": "Seuls les ports nécessaires sont ouverts",
                            "implementation": "Port 8000 (API) avec IP restrictions",
                            "effectiveness": "HIGH",
                            "rules": [
                                "SSH: Port 22 -> IPs admin uniquement",
                                "API: Port 8000 -> CloudFront + WAF",
                                "Monitoring: Port 9100 -> Prometheus interne"
                            ]
                        },
                        {
                            "name": "Instance Metadata Service v2",
                            "description": "Protection contre l'exfiltration de métadonnées",
                            "implementation": "IMDSv2 avec session tokens",
                            "effectiveness": "HIGH",
                            "configuration": {
                                "HttpTokens": "required",
                                "HttpPutResponseHopLimit": 1,
                                "HttpEndpoint": "enabled"
                            }
                        },
                        {
                            "name": "Encryption EBS",
                            "description": "Chiffrement des volumes de stockage",
                            "implementation": "AES-256 via AWS KMS",
                            "effectiveness": "HIGH",
                            "kms_key": "alias/harmonic-ai-ebs"
                        },
                        {
                            "name": "System hardening",
                            "description": "Renforcement du système d'exploitation",
                            "implementation": "AppArmor/SELinux, auditd, fail2ban",
                            "effectiveness": "MEDIUM",
                            "tools": ["CIS Benchmarks", "OpenSCAP"]
                        }
                    ]
                },
                
                "layer_3": {
                    "name": "Protection réseau avancée",
                    "description": "Protection contre les attaques réseau",
                    "techniques": [
                        {
                            "name": "AWS WAF + Shield",
                            "description": "Protection contre DDoS et injections",
                            "implementation": "Règles personnalisées pour l'API",
                            "effectiveness": "HIGH",
                            "rules": [
                                "Rate limiting: 1000 req/min par IP",
                                "SQL injection protection",
                                "XSS protection",
                                "Bot control: Verified Bot Traffic Only"
                            ]
                        },
                        {
                            "name": "CloudFront avec OAC",
                            "description": "CDN avec authentification d'origine",
                            "implementation": "Origin Access Control + Lambda@Edge",
                            "effectiveness": "HIGH",
                            "features": [
                                "SSL/TLS obligatoire",
                                "Geo-restriction optionnelle",
                                "Cache policies optimisées"
                            ]
                        },
                        {
                            "name": "VPC avec sous-réseaux privés",
                            "description": "Isolation réseau complète",
                            "implementation": "NAT Gateway pour sortie internet",
                            "effectiveness": "HIGH",
                            "architecture": {
                                "public_subnets": ["Load Balancers"],
                                "private_subnets": ["EC2 Instances", "RDS"],
                                "isolated_subnets": ["S3 VPC Endpoints"]
                            }
                        },
                        {
                            "name": "Network ACLs personnalisées",
                            "description": "Contrôle d'accès au niveau sous-réseau",
                            "implementation": "Règles strictes entrée/sortie",
                            "effectiveness": "MEDIUM",
                            "default_rules": "DENY ALL, allow spécifique"
                        }
                    ]
                },
                
                "layer_4": {
                    "name": "Sécurité des données et accès",
                    "description": "Protection des données et contrôle d'accès",
                    "techniques": [
                        {
                            "name": "AWS KMS pour chiffrement",
                            "description": "Gestion centralisée des clés de chiffrement",
                            "implementation": "Customer Master Keys avec rotation",
                            "effectiveness": "HIGH",
                            "keys": [
                                "harmonic-ai-api-key",
                                "harmonic-ai-model-key",
                                "harmonic-ai-db-key"
                            ]
                        },
                        {
                            "name": "IAM avec moindre privilège",
                            "description": "Principle of least privilege pour tous les rôles",
                            "implementation": "Policies JSON détaillées",
                            "effectiveness": "HIGH",
                            "roles": [
                                "harmonic-api-role: ReadOnly S3, Invoke Lambda",
                                "harmonic-lambda-role: Execute, Logs",
                                "harmonic-ec2-role: SSM, CloudWatch"
                            ]
                        },
                        {
                            "name": "Secrets Manager",
                            "description": "Gestion sécurisée des secrets",
                            "implementation": "Rotation automatique des secrets",
                            "effectiveness": "HIGH",
                            "secrets": [
                                "Database credentials",
                                "API keys externes",
                                "JWT signing keys"
                            ]
                        },
                        {
                            "name": "S3 Bucket Policies strictes",
                            "description": "Contrôle d'accès granulaire aux buckets",
                            "implementation": "Deny public access, encryption obligatoire",
                            "effectiveness": "HIGH",
                            "policies": [
                                "Require encryption in transit (TLS)",
                                "Require encryption at rest (SSE-KMS)",
                                "Block public access: TRUE"
                            ]
                        }
                    ]
                },
                
                "layer_5": {
                    "name": "Monitoring et détection",
                    "description": "Surveillance et détection d'anomalies",
                    "techniques": [
                        {
                            "name": "AWS GuardDuty",
                            "description": "Détection intelligente de menaces",
                            "implementation": "Activation avec règles personnalisées",
                            "effectiveness": "HIGH",
                            "findings": [
                                "CryptoCurrency mining",
                                "Unauthorized access",
                                "Data exfiltration"
                            ]
                        },
                        {
                            "name": "CloudWatch Logs + Metrics",
                            "description": "Surveillance complète des logs",
                            "implementation": "Log groups avec retention 365 jours",
                            "effectiveness": "HIGH",
                            "alarms": [
                                "High CPU utilization > 80%",
                                "High memory usage > 85%",
                                "API error rate > 5%",
                                "Unusual traffic patterns"
                            ]
                        },
                        {
                            "name": "AWS Config + Conformance Packs",
                            "description": "Conformité et audit continu",
                            "implementation": "Rules pour sécurité best practices",
                            "effectiveness": "MEDIUM",
                            "rules": [
                                "encrypted-volumes",
                                "restricted-ssh",
                                "s3-bucket-public-read-prohibited"
                            ]
                        },
                        {
                            "name": "Custom anomaly detection",
                            "description": "Détection d'anomalies spécifiques à Harmonic AI",
                            "implementation": "Machine learning sur les logs d'API",
                            "effectiveness": "MEDIUM",
                            "models": [
                                "Traffic pattern analysis",
                                "API usage anomalies",
                                "Model inference anomalies"
                            ]
                        }
                    ]
                }
            },
            
            "implementation_phases": {
                "phase_1": {
                    "name": "Protection immédiate (1-2 semaines)",
                    "priority": "CRITICAL",
                    "tasks": [
                        "Activer AWS WAF avec règles de base",
                        "Configurer Security Groups restrictives",
                        "Activer EBS encryption",
                        "Mettre en place IAM roles avec moindre privilège",
                        "Configurer CloudTrail pour audit",
                        "Activer GuardDuty"
                    ],
                    "estimated_time": "2 semaines",
                    "resources_needed": ["AWS Admin", "Security Engineer"]
                },
                
                "phase_2": {
                    "name": "Renforcement avancé (3-4 semaines)",
                    "priority": "HIGH",
                    "tasks": [
                        "Implémenter l'obfuscation du code Python",
                        "Configurer Secrets Manager pour les clés",
                        "Mettre en place VPC avec sous-réseaux privés",
                        "Configurer CloudFront avec OAC",
                        "Activer AWS Config avec conformance packs",
                        "Implémenter monitoring avancé CloudWatch"
                    ],
                    "estimated_time": "4 semaines",
                    "resources_needed": ["Security Engineer", "DevOps Engineer", "Python Developer"]
                },
                
                "phase_3": {
                    "name": "Optimisation continue (en cours)",
                    "priority": "MEDIUM",
                    "tasks": [
                        "Développer détection d'anomalies custom",
                        "Automatiser la rotation des clés",
                        "Implémenter canary deployments",
                        "Mettre en place chaos engineering",
                        "Optimiser les coûts de sécurité",
                        "Mettre à jour régulièrement les règles WAF"
                    ],
                    "estimated_time": "Continue",
                    "resources_needed": ["Security Team", "ML Engineer", "DevOps"]
                }
            },
            
            "tools_and_services": {
                "aws_native": [
                    "AWS WAF (Web Application Firewall)",
                    "AWS Shield (DDoS protection)",
                    "AWS GuardDuty (Threat detection)",
                    "AWS KMS (Key Management Service)",
                    "AWS Secrets Manager",
                    "AWS IAM (Identity and Access Management)",
                    "AWS CloudTrail (Audit logs)",
                    "AWS Config (Compliance)",
                    "AWS CloudWatch (Monitoring)",
                    "AWS VPC (Virtual Private Cloud)",
                    "AWS Security Hub (Centralized security view)"
                ],
                "third_party": [
                    "Snyk (Code security scanning)",
                    "Checkmarx (SAST)",
                    "Veracode (Application security)",
                    "Qualys (Vulnerability management)",
                    "Tenable (Security scanning)",
                    "Darktrace (AI threat detection)"
                ],
                "custom_tools": [
                    "Harmonic Code Obfuscator",
                    "API Traffic Analyzer",
                    "Model Security Validator",
                    "Real-time Threat Detector"
                ]
            },
            
            "compliance_frameworks": {
                "iso_27001": {
                    "applicable": True,
                    "controls": ["A.12.2.1", "A.13.1.1", "A.14.1.1"],
                    "status": "Partially implemented"
                },
                "soc_2": {
                    "applicable": True,
                    "trust_services": ["Security", "Availability", "Confidentiality"],
                    "status": "Planning phase"
                },
                "gdpr": {
                    "applicable": True,
                    "requirements": ["Data encryption", "Access control", "Audit trails"],
                    "status": "Partially implemented"
                },
                "hipaa": {
                    "applicable": False,
                    "requirements": "Not applicable (no healthcare data)",
                    "status": "N/A"
                }
            },
            
            "risk_assessment": {
                "high_risks": [
                    {
                        "risk": "Reverse engineering du modèle harmonique",
                        "impact": "Perte de propriété intellectuelle",
                        "mitigation": "Obfuscation code + chiffrement modèle",
                        "owner": "CTO"
                    },
                    {
                        "risk": "Attaques DDoS sur l'API",
                        "impact": "Indisponibilité service",
                        "mitigation": "AWS WAF + Shield + CloudFront",
                        "owner": "DevOps Lead"
                    },
                    {
                        "risk": "Exfiltration de données",
                        "impact": "Perte de données confidentielles",
                        "mitigation": "Network ACLs + VPC endpoints + Monitoring",
                        "owner": "Security Engineer"
                    }
                ],
                "medium_risks": [
                    {
                        "risk": "Accès non autorisé aux instances",
                        "impact": "Compromission système",
                        "mitigation": "IAM strict + Security Groups",
                        "owner": "SysAdmin"
                    },
                    {
                        "risk": "Vulnérabilités dans les dépendances",
                        "impact": "Exploitation de failles",
                        "mitigation": "Snyk/Checkmarx scanning + Patch management",
                        "owner": "DevOps"
                    }
                ],
                "low_risks": [
                    {
                        "risk": "Exposition de logs sensibles",
                        "impact": "Fuite d'informations",
                        "mitigation": "Log encryption + Access control",
                        "owner": "Security Engineer"
                    }
                ]
            },
            
            "monitoring_and_alerting": {
                "critical_alerts": [
                    "API error rate > 10% pendant 5 minutes",
                    "CPU utilization > 90% pendant 10 minutes",
                    "Unusual outbound traffic patterns",
                    "Failed authentication attempts > 100/min",
                    "GuardDuty high severity findings"
                ],
                "warning_alerts": [
                    "Memory usage > 80%",
                    "Disk usage > 85%",
                    "API latency > 2000ms p95",
                    "Unusual API usage patterns"
                ],
                "notification_channels": [
                    "PagerDuty (Critical)",
                    "Slack #security-alerts",
                    "Email security-team@harmonic.ai",
                    "SMS (On-call rotation)"
                ]
            },
            
            "incident_response_plan": {
                "severity_levels": {
                    "sev1": {
                        "description": "Critical - Service down or data breach",
                        "response_time": "15 minutes",
                        "escalation": "CTO + Security Lead + Legal"
                    },
                    "sev2": {
                        "description": "High - Major vulnerability or performance issue",
                        "response_time": "1 hour",
                        "escalation": "Security Lead + DevOps Lead"
                    },
                    "sev3": {
                        "description": "Medium - Minor issues or anomalies",
                        "response_time": "4 hours",
                        "escalation": "On-call Engineer"
                    }
                },
                "response_steps": [
                    "1. Identification et classification",
                    "2. Containment (isolation des ressources affectées)",
                    "3. Investigation (analyse root cause)",
                    "4. Éradication (suppression menace)",
                    "5. Récupération (restauration service)",
                    "6. Post-mortem (documentation + améliorations)"
                ]
            },
            
            "next_steps": [
                "1. Réviser le plan avec l'équipe sécurité",
                "2. Prioriser les actions Phase 1 (critiques)",
                "3. Allouer les ressources nécessaires",
                "4. Mettre en place les outils de monitoring",
                "5. Former l'équipe aux procédures de sécurité",
                "6. Exécuter Phase 1 dans les 2 semaines"
            ]
        }
        
        return plan
    
    def generate_aws_cli_commands(self) -> Dict[str, List[str]]:
        """Génère les commandes AWS CLI pour implémenter la sécurité"""
        
        commands = {
            "iam_security": [
                "# Créer un rôle IAM pour les instances EC2",
                "aws iam create-role --role-name harmonic-ec2-role --assume-role-policy-document file://ec2-trust-policy.json",
                "",
                "# Attacher les policies nécessaires",
                "aws iam attach-role-policy --role-name harmonic-ec2-role --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
                "aws iam attach-role-policy --role-name harmonic-ec2-role --policy-arn arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy",
                "",
                "# Créer une instance profile",
                "aws iam create-instance-profile --instance-profile-name harmonic-ec2-profile",
                "aws iam add-role-to-instance-profile --instance-profile-name harmonic-ec2-profile --role-name harmonic-ec2-role"
            ],
            
            "vpc_security": [
                "# Créer un VPC avec sous-réseaux privés",
                "aws ec2 create-vpc --cidr-block 10.0.0.0/16",
                "",
                "# Créer des sous-réseaux privés",
                "aws ec2 create-subnet --vpc-id <vpc-id> --cidr-block 10.0.1.0/24 --availability-zone us-east-1a",
                "aws ec2 create-subnet --vpc-id <vpc-id> --cidr-block 10.0.2.0/24 --availability-zone us-east-1b",
                "",
                "# Configurer NAT Gateway pour accès internet sortant",
                "aws ec2 create-nat-gateway --subnet-id <subnet-id> --allocation-id <eip-alloc-id>"
            ],
            
            "waf_configuration": [
                "# Créer un Web ACL pour l'API",
                "aws wafv2 create-web-acl --name harmonic-api-acl --scope REGIONAL --default-action Allow={} --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=harmonic-api-acl --region us-east-1",
                "",
                "# Ajouter des règles de rate limiting",
                "aws wafv2 create-rule-group --name harmonic-rate-limit --scope REGIONAL --capacity 100 --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=harmonic-rate-limit --rules file://rate-limit-rules.json --region us-east-1",
                "",
                "# Associer le Web ACL à CloudFront ou ALB",
                "aws wafv2 associate-web-acl --web-acl-arn <web-acl-arn> --resource-arn <resource-arn>"
            ],
            
            "monitoring_setup": [
                "# Activer GuardDuty",
                "aws guardduty create-detector --enable --finding-publishing-frequency FIFTEEN_MINUTES",
                "",
                "# Activer AWS Config",
                "aws configservice put-configuration-recorder --configuration-recorder name=default,roleARN=<role-arn> --recording-group allSupported=true,includeGlobalResourceTypes=true",
                "aws configservice start-configuration-recorder --configuration-recorder-name default",
                "",
                "# Configurer CloudTrail",
                "aws cloudtrail create-trail --name harmonic-audit-trail --s3-bucket-name harmonic-audit-logs --is-multi-region-trail --enable-log-file-validation"
            ],
            
            "encryption_setup": [
                "# Créer une clé KMS pour EBS encryption",
                "aws kms create-key --description \"Harmonic AI EBS encryption key\" --key-usage ENCRYPT_DECRYPT --origin AWS_KMS",
                "aws kms create-alias --alias-name alias/harmonic-ai-ebs --target-key-id <key-id>",
                "",
                "# Créer une clé KMS pour S3 encryption",
                "aws kms create-key --description \"Harmonic AI S3 encryption key\" --key-usage ENCRYPT_DECRYPT --origin AWS_KMS",
                "aws kms create-alias --alias-name alias/harmonic-ai-s3 --target-key-id <key-id>",
                "",
                "# Configurer S3 bucket avec encryption",
                "aws s3api put-bucket-encryption --bucket harmonic-ai-models --server-side-encryption-configuration '{\"Rules\": [{\"ApplyServerSideEncryptionByDefault\": {\"SSEAlgorithm\": \"aws:kms\", \"KMSMasterKeyID\": \"<s3-key-id>\"}}]}'"
            ]
        }
        
        return commands
    
    def generate_python_obfuscation_script(self) -> str:
        """Génère un script Python pour l'obfuscation du code"""
        
        script = """
#!/usr/bin/env python3
"""
        script += """
\"\"\"
Script d'obfuscation Python pour Harmonic AI
Protection contre le reverse engineering
\"\"\"

import os
import sys
import ast
import base64
import hashlib
import secrets
from cryptography.fernet import Fernet
import zlib

class CodeObfuscator:
    \"\"\"Obfuscateur de code Python avancé\"\"\"
    
    def __init__(self, key=None):
        \"\"\"Initialise l'obfuscateur avec une clé\"\"\"
        self.key = key or secrets.token_bytes(32)
        self.cipher = Fernet(base64.urlsafe_b64encode(self.key))
        
    def encrypt_strings(self, code: str) -> str:
        \"\"\"Chiffre les chaînes de caractères dans le code\"\"\"
        tree = ast.parse(code)
        
        class StringEncryptor(ast.NodeTransformer):
            def __init__(self, cipher):
                self.cipher = cipher
                self.string_map = {}
                
            def visit_Constant(self, node):
                if isinstance(node.value, str) and len(node.value) > 3:
                    # Ne pas chiffrer les docstrings très courtes
                    if not (node.value.startswith('\"\"\"') or node.value.startswith("'''")):
                        encrypted = self.cipher.encrypt(node.value.encode())
                        b64_encrypted = base64.b64encode(encrypted).decode()
                        
                        # Créer un nom de variable aléatoire
                        var_name = f\"_s{secrets.token_hex(4)}\"
                        self.string_map[var_name] = b64_encrypted
                        
                        # Remplacer la chaîne par un appel de décryptage
                        return ast.Call(
                            func=ast.Name(id='_decrypt_str', ctx=ast.Load()),
                            args=[ast.Constant(value=var_name)],
                            keywords=[]
                        )
                return node
        
        encryptor = StringEncryptor(self.cipher)
        modified_tree = encryptor.visit(tree)
        
        # Ajouter la fonction de décryptage
        decrypt_func = ast.FunctionDef(
            name='_decrypt_str',
            args=ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg='var_name')],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[]
            ),
            body=[
                ast.Assign(
                    targets=[ast.Name(id='encrypted_b64', ctx=ast.Store())],
                    value=ast.Dict(
                        keys=[ast.Constant(value=k) for k in encryptor.string_map.keys()],
                        values=[ast.Constant(value=v) for v in encryptor.string_map.values()]
                    )
                ),
                ast.Assign(
                    targets=[ast.Name(id='b64_data', ctx=ast.Store())],
                    value=ast.Subscript(
                        value=ast.Name(id='encrypted_b64', ctx=ast.Load()),
                        slice=ast.Index(value=ast.Name(id='var_name', ctx=ast.Load()))
                    )
                ),
                ast.Assign(
                    targets=[ast.Name(id='encrypted', ctx=ast.Store())],
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id='base64', ctx=ast.Load()),
                            attr='b64decode'
                        ),
                        args=[ast.Name(id='b64_data', ctx=ast.Load())],
                        keywords=[]
                    )
                ),
                ast.Return(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id='cipher', ctx=ast.Load()),
                            attr='decrypt'
                        ),
                        args=[ast.Name(id='encrypted', ctx=ast.Load())],
                        keywords=[]
                    )
                )
            ],
            decorator_list=[],
            returns=None
        )
        
        # Reconstruire le code
        modified_tree.body.insert(0, decrypt_func)
        
        # Ajouter les imports nécessaires
        imports = [
            ast.Import(names=[ast.alias(name='base64')]),
            ast.ImportFrom(
                module='cryptography.fernet',
                names=[ast.alias(name='Fernet')],
                level=0
            )
        ]
        
        modified_tree.body = imports + modified_tree.body
        
        return ast.unparse(modified_tree)
    
    def mangle_names(self, code: str) -> str:
        \"\"\"Modifie les noms de variables et fonctions\"\"\"
        tree = ast.parse(code)
        
        name_mapping = {}
        
        class NameMangler(ast.NodeTransformer):
            def visit_Name(self, node):
                if node.id not in name_mapping and not node.id.startswith('_'):
                    # Générer un nouveau nom aléatoire
                    new_name = f\"_v{secrets.token_hex(4)}\"
                    name_mapping[node.id] = new_name
                    node.id = new_name
                elif node.id in name_mapping:
                    node.id = name_mapping[node.id]
                return node
            
            def visit_FunctionDef(self, node):
                if node.name not in name_mapping and not node.name.startswith('_'):
                    new_name = f\"_f{secrets.token_hex(4)}\"
                    name_mapping[node.name] = new_name
                    node.name = new_name
                return self.generic_visit(node)
            
            def visit_ClassDef(self, node):
                if node.name not in name_mapping and not node.name.startswith('_'):
                    new_name = f\"_c{secrets.token_hex(4)}\"
                    name_mapping[node.name] = new_name
                    node.name = new_name
                return self.generic_visit(node)
        
        mangler = NameMangler()
        modified_tree = mangler.visit(tree)
        
        return ast.unparse(modified_tree)
    
    def insert_dead_code(self, code: str) -> str:
        \"\"\"Insère du code mort pour complexifier l'analyse\"\"\"
        lines = code.split('\\n')
        new_lines = []
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            
            # Insérer du code mort après certaines lignes
            if i % 10 == 0 and i > 0:
                dead_code = [
                    f\"    _dummy{secrets.token_hex(2)} = {secrets.randbelow(1000)}\",
                    f\"    if _dummy{secrets.token_hex(2)} > 10000:  # Condition toujours fausse\",
                    f\"        print('Never executed')\",
                    f\"    for _ in range({secrets.randbelow(5)}):  # Boucle vide\",
                    f\"        pass\"
                ]
                new_lines.extend(dead_code)
        
        return '\\n'.join(new_lines)
    
    def compress_code(self, code: str) -> str:
        \"\"\"Compresse le code pour le rendre illisible\"\"\"
        compressed = zlib.compress(code.encode())
        b64_compressed = base64.b64encode(compressed).decode()
        
        decompress_code = f\"\"\"
import zlib
import base64

compressed_code = \"{b64_compressed}\"
code_bytes = base64.b64decode(compressed_code)
exec(zlib.decompress(code_bytes).decode())
\"\"\"
        
        return decompress_code
    
    def obfuscate_file(self, input_file: str, output_file: str) -> None:
        \"\"\"Obfusque un fichier Python complet\"\"\"
        with open(input_file, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Étape 1: Chiffrer les chaînes
        code = self.encrypt_strings(code)
        
        # Étape 2: Modifier les noms
        code = self.mangle_names(code)
        
        # Étape 3: Insérer du code mort
        code = self.insert_dead_code(code)
        
        # Étape 4: Compresser le code
        code = self.compress_code(code)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        print(f\"Fichier obfusqué: {input_file} -> {output_file}\")

def main():
    \"\"\"Fonction principale\"\"\"
    if len(sys.argv) < 3:
        print(\"Usage: python obfuscator.py <input_file> <output_file>\")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        print(f\"Fichier introuvable: {input_file}\")
        sys.exit(1)
    
    obfuscator = CodeObfuscator()
    obfuscator.obfuscate_file(input_file, output_file)
    
    print(\"Obfuscation terminée avec succès!\")

if __name__ == \"__main__\":
    main()
"""
        
        return script

def main():
    """Fonction principale"""
    import time
    
    print("=" * 80)
    print("PLAN DE PROTECTION AWS - HARMONIC AI")
    print("Protection contre le reverse engineering et attaques")
    print("=" * 80)
    
    # Générer le plan
    security_plan = AWSSecurityProtectionPlan()
    plan = security_plan.generate_comprehensive_protection_plan()
    
    print("\n1. APERÇU DU PLAN")
    print("-" * 40)
    print(f"ID du plan: {plan['plan_id']}")
    print(f"Date de création: {plan['creation_date']}")
    print(f"Dernière mise à jour: {plan['last_updated']}")
    
    print("\n2. COUCHES DE PROTECTION")
    print("-" * 40)
    for layer_key, layer_data in plan['protection_layers'].items():
        print(f"\n{layer_data['name']}:")
        print(f"  Description: {layer_data['description']}")
        print(f"  Techniques: {len(layer_data['techniques'])}")
    
    print("\n3. PHASES D'IMPLÉMENTATION")
    print("-" * 40)
    for phase_key, phase_data in plan['implementation_phases'].items():
        print(f"\n{phase_data['name']}:")
        print(f"  Priorité: {phase_data['priority']}")
        print(f"  Temps estimé: {phase_data['estimated_time']}")
        print(f"  Tâches: {len(phase_data['tasks'])}")
    
    print("\n4. ÉVALUATION DES RISQUES")
    print("-" * 40)
    print(f"Risques élevés: {len(plan['risk_assessment']['high_risks'])}")
    print(f"Risques moyens: {len(plan['risk_assessment']['medium_risks'])}")
    print(f"Risques faibles: {len(plan['risk_assessment']['low_risks'])}")
    
    print("\n5. OUTILS ET SERVICES")
    print("-" * 40)
    print(f"AWS natifs: {len(plan['tools_and_services']['aws_native'])}")
    print(f"Tiers: {len(plan['tools_and_services']['third_party'])}")
    print(f"Outils custom: {len(plan['tools_and_services']['custom_tools'])}")
    
    print("\n6. PROCHAINES ÉTAPES")
    print("-" * 40)
    for i, step in enumerate(plan['next_steps'], 1):
        print(f"{i}. {step}")
    
    # Générer les commandes AWS CLI
    print("\n" + "=" * 80)
    print("COMMANDES AWS CLI POUR L'IMPLÉMENTATION")
    print("=" * 80)
    
    cli_commands = security_plan.generate_aws_cli_commands()
    
    print("\nCommandes IAM:")
    for cmd in cli_commands['iam_security']:
        print(f"  {cmd}")
    
    print("\nCommandes VPC:")
    for cmd in cli_commands['vpc_security'][:3]:  # Afficher seulement les premières
        print(f"  {cmd}")
    
    # Générer le script d'obfuscation
    print("\n" + "=" * 80)
    print("SCRIPT D'OBFUSCATION PYTHON")
    print("=" * 80)
    
    obfuscation_script = security_plan.generate_python_obfuscation_script()
    
    # Sauvegarder le script
    with open("python_obfuscator.py", "w", encoding="utf-8") as f:
        f.write(obfuscation_script)
    
    print("Script d'obfuscation généré: python_obfuscator.py")
    print("Usage: python python_obfuscator.py <input_file.py> <output_file.py>")
    
    # Sauvegarder le plan complet
    with open("aws_security_plan.json", "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    print("✓ Plan de protection AWS généré avec succès")
    print("✓ 5 couches de protection identifiées")
    print("✓ 3 phases d'implémentation définies")
    print("✓ Script d'obfuscation Python créé")
    print("✓ Commandes AWS CLI prêtes à l'emploi")
    print("\nFichiers générés:")
    print("  • aws_security_plan.json - Plan complet de sécurité")
    print("  • python_obfuscator.py - Script d'obfuscation Python")
    print("\nProchaines actions:")
    print("  1. Exécuter les commandes AWS CLI Phase 1")
