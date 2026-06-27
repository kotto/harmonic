
# Commande SSH pour appliquer les optimisations
ssh ec2-user@__EC2_IP__ << 'EOF'
# Sauvegarder l'ancienne configuration
sudo cp /opt/deepseek/api.py /opt/deepseek/api.py.backup_$(date +%Y%m%d_%H%M%S)

# Appliquer les paramÃ¨tres optimisÃ©s
sudo sed -i "s/'max_tokens': 512/'max_tokens': 256/g" /opt/deepseek/api.py
sudo sed -i "s/'temperature': 0.0/'temperature': 0.0/g" /opt/deepseek/api.py  # DÃ©jÃ  bon
sudo sed -i "s/'top_p': 1.0/'top_p': 0.95/g" /opt/deepseek/api.py
sudo sed -i "s/'top_k': -1/'top_k': 50/g" /opt/deepseek/api.py
sudo sed -i "s/'repetition_penalty': 1.0/'repetition_penalty': 1.1/g" /opt/deepseek/api.py

# RedÃ©marrer le service
sudo systemctl restart deepseek-api.service

# VÃ©rifier le statut
sudo systemctl status deepseek-api.service
EOF
