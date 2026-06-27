#!/usr/bin/env python3
"""
Script de configuration automatique des clés API pour Connective AI Multi-Modal
"""

import boto3
import json
import time

def configure_multimodal_keys():
    """Configuration des clés API sur l'instance multi-modal"""
    
    # Configuration
    instance_id = "i-0f4f670315f102d14"
    public_ip = "35.171.182.151"
    
    # Commande SSM pour configurer les clés
    ssm_client = boto3.client('ssm', region_name='us-east-1')
    
    # Script de configuration
    config_script = f'''
#!/bin/bash
cd /home/ec2-user/connective-ai-multimodal

# Création du fichier de configuration
cat > api_keys.env << 'EOF'
# Connective AI Multi-Modal - Configuration API Keys
DEEPSEEK_API_KEY="sk-votre_clé_deepseek_ici"
OPENAI_API_KEY="sk-votre_clé_openai_ici"
ANTHROPIC_API_KEY="sk-ant-votre_clé_anthropic_ici"
PERPLEXITY_API_KEY="pplx-votre_clé_perplexity_ici"
HUGGINGFACE_API_KEY="hf_votre_clé_huggingface_ici"
EOF

# Mise à jour du fichier Python
sed -i "s/YOUR_DEEPSEEK_KEY/\\$DEEPSEEK_API_KEY/g" connective_ai_multimodal.py
sed -i "s/YOUR_OPENAI_KEY/\\$OPENAI_API_KEY/g" connective_ai_multimodal.py
sed -i "s/YOUR_ANTHROPIC_KEY/\\$ANTHROPIC_API_KEY/g" connective_ai_multimodal.py
sed -i "s/YOUR_PERPLEXITY_KEY/\\$PERPLEXITY_API_KEY/g" connective_ai_multimodal.py
sed -i "s/YOUR_HUGGINGFACE_KEY/\\$HUGGINGFACE_API_KEY/g" connective_ai_multimodal.py

# Redémarrage du service
sudo systemctl restart connective-ai-multimodal

# Vérification
sleep 10
sudo systemctl status connective-ai-multimodal
'''
    
    try:
        # Exécution du script via SSM
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={'commands': [config_script]}
        )
        
        command_id = response['Command']['CommandId']
        print(f"✅ Commande SSM envoyée: {command_id}")
        
        # Attente exécution
        time.sleep(30)
        
        # Vérification statut
        output = ssm_client.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )
        
        print(f"📊 Statut: {output['Status']}")
        if 'StandardOutputContent' in output:
            print(f"📋 Output: {output['StandardOutputContent'][:500]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def create_manual_instructions():
    """Création instructions manuelles"""
    
    instructions = f'''
# 🚀 INSTRUCTIONS CONFIGURATION MANUELLE - CONNECTIVE AI MULTI-MODAL

## 📋 Connexion SSH
```bash
ssh -i ~/.ssh/deep ec2-user@35.171.182.151
```

## 📋 Configuration Clés API
```bash
cd /home/ec2-user/connective-ai-multimodal
nano connective_ai_multimodal.py
```

## 📋 Remplacer les clés:
- YOUR_DEEPSEEK_KEY → "sk-votre_clé_deepseek"
- YOUR_OPENAI_KEY → "sk-votre_clé_openai"
- YOUR_ANTHROPIC_KEY → "sk-ant-votre_clé_anthropic"
- YOUR_PERPLEXITY_KEY → "pplx-votre_clé_perplexity"
- YOUR_HUGGINGFACE_KEY → "hf_votre_clé_huggingface"

## 📋 Redémarrage service:
```bash
sudo systemctl restart connective-ai-multimodal
```

## 📋 Validation:
```bash
curl http://35.171.182.151:8000/health
curl http://35.171.182.151:8000/modalities
```

## 📋 Tests LM Arena:
```bash
python test_multimodal_lm_arena.py
```
'''
    
    with open('MANUAL_CONFIG_INSTRUCTIONS.md', 'w') as f:
        f.write(instructions)
    
    print("✅ Instructions manuelles créées: MANUAL_CONFIG_INSTRUCTIONS.md")

if __name__ == "__main__":
    print("🚀 Configuration Connective AI Multi-Modal")
    print("=" * 50)
    
    # Tentative configuration automatique
    if configure_multimodal_keys():
        print("✅ Configuration automatique réussie!")
    else:
        print("⚠️ Configuration automatique échouée, utilisation manuelle")
        create_manual_instructions()
    
    print("\n🎯 Instance déployée: 35.171.182.151")
    print("📚 Documentation: http://35.171.182.151:8000/docs")
    print("🔍 Health: http://35.171.182.151:8000/health")
    print("🎨 Modalités: http://35.171.182.151:8000/modalities")
