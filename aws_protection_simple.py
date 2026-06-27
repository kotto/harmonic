#!/usr/bin/env python3
"""
Plan de protection AWS simplifié pour Harmonic AI
Actions immédiates pour protéger contre le reverse engineering
"""

import json
import os
from datetime import datetime

class SimpleAWSProtection:
    """Protection AWS simplifiée pour Harmonic AI"""
    
    def generate_quick_protection_plan(self):
        """Génère un plan de protection rapide"""
        
        plan = {
            "title": "Plan de Protection AWS Rapide - Harmonic AI",
            "date": datetime.now().isoformat(),
            "objective": "Protéger l'architecture contre le reverse engineering et les attaques",
            "priority": "HIGH",
            
            "immediate_actions": [
                {
                    "action": "Sécuriser les instances EC2",
                    "steps": [
                        "1. Configurer Security Groups: Seuls ports 8000 (API) et 22 (SSH admin) ouverts",
                        "2. Activer IMDSv2: aws ec2 modify-instance-metadata-options --instance-id <id> --http-tokens required --http-endpoint enabled",
                        "3. Chiffrer volumes EBS: Utiliser AWS KMS avec clé dédiée",
                        "4. Désactiver API metadata publique: Restreindre l'accès aux métadonnées"
                    ],
                    "time": "1 heure",
                    "owner": "DevOps"
                },
                {
                    "action": "Protéger l'API avec WAF",
                    "steps": [
                        "1. Activer AWS WAF: Créer un Web ACL pour l'API",
                        "2. Ajouter rate limiting: 1000 requêtes/minute par IP",
                        "3. Bloquer bots connus: Utiliser AWS Managed Rules",
                        "4. Activer AWS Shield: Protection DDoS standard"
                    ],
                    "time": "2 heures",
                    "owner": "Security"
                },
                {
                    "action": "Sécuriser les accès IAM",
                    "steps": [
                        "1. Créer des rôles spécifiques: harmonic-api-role, harmonic-ec2-role",
                        "2. Appliquer le moindre privilège: Seules permissions nécessaires",
                        "3. Activer MFA: Obligatoire pour tous les comptes admin",
                        "4. Configurer rotation des clés: Automatique via Secrets Manager"
                    ],
                    "time": "1 heure",
                    "owner": "IAM Admin"
                },
                {
                    "action": "Obfuscation du code Python",
                    "steps": [
                        "1. Compiler en bytecode: python -m compileall -f -b .",
                        "2. Chiffrer les chaînes sensibles: Utiliser AES-256",
                        "3. Modifier les noms de variables: Remplacer par des noms aléatoires",
                        "4. Insérer du code mort: Complexifier l'analyse statique"
                    ],
                    "time": "3 heures",
                    "owner": "Python Developer"
                },
                {
                    "action": "Monitoring et alerting",
                    "steps": [
                        "1. Activer CloudTrail: Audit de toutes les actions API",
                        "2. Configurer CloudWatch: Métriques et logs",
                        "3. Activer GuardDuty: Détection intelligente de menaces",
                        "4. Configurer alertes: CPU > 80%, erreurs API > 5%"
                    ],
                    "time": "2 heures",
                    "owner": "Monitoring"
                }
            ],
            
            "code_obfuscation_techniques": {
                "bytecode_compilation": {
                    "command": "python -m compileall -f -b .",
                    "effect": "Convertit .py en .pyc, rend le code source moins accessible",
                    "limitation": "Peut être décompilé avec des outils comme uncompyle6"
                },
                "string_encryption": {
                    "method": "AES-256 avec clé dérivée de l'environnement",
                    "effect": "Chiffre les chaînes sensibles dans le code",
                    "implementation": "Chiffrer au build, déchiffrer au runtime"
                },
                "control_flow_obfuscation": {
                    "method": "Insertion de sauts conditionnels inutiles",
                    "effect": "Rend le flux de contrôle difficile à analyser",
                    "tools": ["pyobfuscate", "pyminifier --obfuscate"]
                },
                "name_mangling": {
                    "method": "Remplacement des noms de variables/fonctions",
                    "effect": "Rend le code illisible pour les humains",
                    "tools": ["pyminifier --obfuscate-variables"]
                }
            },
            
            "aws_cli_commands": {
                "security_groups": [
                    "# Créer un Security Group restrictif",
                    "aws ec2 create-security-group --group-name harmonic-api-sg --description \"Security group for Harmonic AI API\" --vpc-id <vpc-id>",
                    "",
                    "# Autoriser uniquement le port API",
                    "aws ec2 authorize-security-group-ingress --group-id <sg-id> --protocol tcp --port 8000 --cidr 0.0.0.0/0",
                    "",
                    "# Autoriser SSH uniquement depuis IPs admin",
                    "aws ec2 authorize-security-group-ingress --group-id <sg-id> --protocol tcp --port 22 --cidr <admin-ip>/32"
                ],
                "waf_setup": [
                    "# Créer un Web ACL",
                    "aws wafv2 create-web-acl --name harmonic-api-waf --scope REGIONAL --default-action Allow={} --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=harmonic-api-waf --region us-east-1",
                    "",
                    "# Ajouter une règle de rate limiting",
                    "aws wafv2 create-rule --name rate-limit --scope REGIONAL --capacity 100 --action Block={} --statement RateBasedStatement Limit=1000,AggregateKeyType=IP --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=rate-limit --region us-east-1"
                ],
                "monitoring": [
                    "# Activer CloudTrail",
                    "aws cloudtrail create-trail --name harmonic-audit --s3-bucket-name harmonic-audit-logs --is-multi-region-trail",
                    "",
                    "# Activer GuardDuty",
                    "aws guardduty create-detector --enable --finding-publishing-frequency FIFTEEN_MINUTES"
                ]
            },
            
            "python_obfuscation_script": """
#!/usr/bin/env python3
\"\"\"
Script simple d'obfuscation Python
\"\"\"

import base64
import zlib

def obfuscate_code(input_file, output_file):
    \"\"\"Obfusque un fichier Python\"\"\"
    with open(input_file, 'r') as f:
        code = f.read()
    
    # Compresser le code
    compressed = zlib.compress(code.encode())
    b64_compressed = base64.b64encode(compressed).decode()
    
    # Générer le code obfusqué
    obfuscated = f\"\"\"
import zlib
import base64
import types

# Code compressé et encodé
compressed_code = \"{b64_compressed}\"

# Fonction de décompression
def _execute():
    code_bytes = base64.b64decode(compressed_code)
    code_str = zlib.decompress(code_bytes).decode()
    exec(code_str)

if __name__ == \"__main__\":
    _execute()
\"\"\"
    
    with open(output_file, 'w') as f:
        f.write(obfuscated)
    
    print(f\"Fichier obfusqué: {input_file} -> {output_file}\")

if __name__ == \"__main__\":
    import sys
    if len(sys.argv) < 3:
        print(\"Usage: python simple_obfuscator.py <input.py> <output.py>\")
        sys.exit(1)
    
    obfuscate_code(sys.argv[1], sys.argv[2])
""",
            
            "next_steps": [
                "1. Exécuter les actions immédiates dans les 24 heures",
                "2. Configurer AWS WAF avec rate limiting",
                "3. Obfusquer le code source Python",
                "4. Activer monitoring CloudTrail + GuardDuty",
                "5. Réviser les accès IAM régulièrement"
            ],
            
            "resources": {
                "aws_docs": [
                    "https://docs.aws.amazon.com/waf/latest/developerguide/waf-chapter.html",
                    "https://docs.aws.amazon.com/guardduty/latest/ug/what-is-guardduty.html",
                    "https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html"
                ],
                "tools": [
                    "pyminifier: pip install pyminifier",
                    "pyarmor: pip install pyarmor",
                    "Nuitka: pip install Nuitka"
                ]
            }
        }
        
        return plan
    
    def save_plan(self, plan, filename="aws_protection_plan_simple.json"):
        """Sauvegarde le plan dans un fichier JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
        
        print(f"Plan sauvegardé: {filename}")
        return filename
    
    def generate_summary(self, plan):
        """Génère un résumé du plan"""
        summary = f"""
PLAN DE PROTECTION AWS - HARMONIC AI
====================================
Date: {plan['date']}
Objectif: {plan['objective']}
Priorité: {plan['priority']}

ACTIONS IMMÉDIATES ({len(plan['immediate_actions'])}):
"""
        
        for i, action in enumerate(plan['immediate_actions'], 1):
            summary += f"\n{i}. {action['action']} ({action['time']})"
            summary += f"\n   Propriétaire: {action['owner']}"
            summary += f"\n   Étapes: {len(action['steps'])}"
        
        summary += f"""

TECHNIQUES D'OBFUSCATION ({len(plan['code_obfuscation_techniques'])}):
"""
        
        for technique, details in plan['code_obfuscation_techniques'].items():
            summary += f"\n• {technique}: {details['effect']}"
        
        summary += f"""

PROCHAINES ÉTAPES ({len(plan['next_steps'])}):
"""
        
        for i, step in enumerate(plan['next_steps'], 1):
            summary += f"\n{i}. {step}"
        
        return summary

def main():
    """Fonction principale"""
    print("=" * 70)
    print("PLAN DE PROTECTION AWS SIMPLIFIÉ - HARMONIC AI")
    print("Protection contre le reverse engineering")
    print("=" * 70)
    
    # Générer le plan
    protector = SimpleAWSProtection()
    plan = protector.generate_quick_protection_plan()
    
    # Afficher le résumé
    summary = protector.generate_summary(plan)
    print(summary)
    
    # Sauvegarder le plan
    filename = protector.save_plan(plan)
    
    # Créer le script d'obfuscation
    script_filename = "simple_python_obfuscator.py"
    with open(script_filename, 'w', encoding='utf-8') as f:
        f.write(plan['python_obfuscation_script'])
    
    print(f"\nScript d'obfuscation généré: {script_filename}")
    
    print("\n" + "=" * 70)
    print("INSTRUCTIONS RAPIDES:")
    print("=" * 70)
    print("1. Exécuter les commandes AWS CLI pour sécuriser l'infrastructure")
    print("2. Utiliser le script d'obfuscation sur le code source Python")
    print("3. Configurer AWS WAF avec rate limiting (1000 req/min par IP)")
    print("4. Activer CloudTrail et GuardDuty pour le monitoring")
    print("5. Réviser régulièrement les accès IAM")
    
    print("\n" + "=" * 70)
    print("RÉSUMÉ EXÉCUTIF:")
    print("=" * 70)
    print("SUCCES Plan de protection généré avec 5 actions immédiates")
    print("SUCCES Techniques d'obfuscation Python définies")
    print("SUCCES Commandes AWS CLI prêtes à l'emploi")
    print("SUCCES Script d'obfuscation créé")
    print("SUCCES Priorité: HAUTE - À exécuter dans les 24 heures")
    
    print("\nFichiers créés:")
    print(f"  • {filename} - Plan complet de protection")
    print(f"  • {script_filename} - Script d'obfuscation Python")
    
    print("\nActions recommandées dans l'ordre:")
    print("  1. Sécuriser les instances EC2 (Security Groups + IMDSv2)")
    print("  2. Configurer AWS WAF avec rate limiting")
    print("  3. Obfusquer le code source Python")
    print("  4. Activer CloudTrail + GuardDuty")
    print("  5. Réviser les accès IAM")

if __name__ == "__main__":
    main()