#!/bin/bash
# 🚀 USER DATA SCRIPTS - CONFIGURATION INSTANCES EC2
# Scripts pour initialiser les différentes instances

# GPU Instance User Data (g4dn.xlarge)
cat > gpu-user-data.sh << 'EOF'
#!/bin/bash
# Configuration GPU Instance pour Mathstral + WizardMath

set -e

echo "🚀 Initialisation GPU Instance pour Harmonic AI..."

# Mise à jour système
yum update -y

# Installation NVIDIA drivers et CUDA
echo "📦 Installation NVIDIA drivers..."
yum install -y gcc kernel-devel-$(uname -r) dkms

# Téléchargement NVIDIA driver
wget -P /tmp https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_520.61.05_linux.run
sh /tmp/cuda_11.8.0_520.61.05_linux.run --silent --dkms

# Installation Docker
echo "🐳 Installation Docker..."
yum install -y docker
systemctl start docker
systemctl enable docker

# Installation Python et dépendances
echo "🐍 Installation Python..."
yum install -y python3 python3-pip
pip3 install --upgrade pip

# Installation dépendances Harmonic AI
echo "📦 Installation dépendances Harmonic AI..."
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip3 install transformers accelerate bitsandbytes
pip3 install numpy scipy boto3
pip3 install flask gunicorn
pip3 install fastapi uvicorn
pip3 install jupyter notebook

# Configuration environnement
echo "🔧 Configuration environnement..."
export CUDA_HOME=/usr/local/cuda
export PATH=$PATH:$CUDA_HOME/bin
export LD_LIBRARY_PATH=$CUDA_HOME/lib64

# Création répertoires
mkdir -p /opt/harmonic-ai
cd /opt/harmonic-ai

# Clonage code Harmonic AI
echo "📥 Clonage code Harmonic AI..."
git clone https://github.com/your-org/harmonic-ai.git .

# Configuration services
echo "🔧 Configuration services..."
cat > /etc/systemd/system/harmonic-gpu.service << 'EOL'
[Unit]
Description=Harmonic AI GPU Service
After=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/harmonic-ai
ExecStart=/usr/bin/docker-compose up
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

systemctl enable harmonic-gpu.service

# Installation Docker Compose
echo "🐳 Installation Docker Compose..."
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Configuration Docker Compose
echo "🔧 Configuration Docker Compose..."
cat > /opt/harmonic-ai/docker-compose.yml << 'EOFD'
version: '3.8'

services:
  mathstral-service:
    build: .
    ports:
      - "5000:5000"
    environment:
      - CUDA_VISIBLE_DEVICES=0
    volumes:
      - ./models:/app/models
      - ./data:/app/data
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

  wizardmath-service:
    build: .
    ports:
      - "6000:6000"
    environment:
      - CUDA_VISIBLE_DEVICES=0
    volumes:
      - ./models:/app/models
      - ./data:/app/data
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

  monitoring:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring:/etc/prometheus
    restart: unless-stopped
EOFD

# Création Dockerfile
echo "🐳 Création Dockerfile..."
cat > /opt/harmonic-ai/Dockerfile << 'EOFD'
FROM nvidia/cuda:11.8-devel-ubuntu20.04

WORKDIR /app

# Installation Python et dépendances
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Installation dépendances Python
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copie code
COPY . .

# Exposition ports
EXPOSE 5000 6000

# Commande de démarrage
CMD ["python3", "launch_dual_math.py"]
EOFD

# Création requirements.txt
echo "📝 Création requirements.txt..."
cat > /opt/harmonic-ai/requirements.txt << 'EOFD'
torch>=2.0.0
torchvision>=0.15.0
transformers>=4.30.0
accelerate>=0.20.0
bitsandbytes>=0.41.0
numpy>=1.24.0
scipy>=1.10.0
boto3>=1.26.0
flask>=2.3.0
fastapi>=0.100.0
uvicorn>=0.22.0
jupyter>=1.0.0
notebook>=6.5.0
prometheus-client>=0.16.0
EOFD

# Configuration monitoring
echo "📊 Configuration monitoring..."
mkdir -p /opt/harmonic-ai/monitoring
cat > /opt/harmonic-ai/monitoring/prometheus.yml << 'EOFD'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'harmonic-gpu'
    static_configs:
      - targets: ['localhost:5000', 'localhost:6000']
    metrics_path: '/metrics'
    scrape_interval: 5s
EOFD

# Installation CloudWatch agent
echo "☁️ Installation CloudWatch agent..."
yum install -y amazon-cloudwatch-agent

# Configuration CloudWatch
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOFD'
{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "cwagent"
  },
  "metrics": {
    "namespace": "HarmonicAI",
    "metrics_collected": {
      "cpu": {
        "measurement": [
          "cpu_utilization"
        ]
      },
      "memory": {
        "measurement": [
          "memory_utilization"
        ]
      },
      "disk": {
        "measurement": [
          "used_percent"
        ]
      }
    }
  }
}
EOFD

systemctl enable amazon-cloudwatch-agent
systemctl start amazon-cloudwatch-agent

# Configuration Jupyter
echo "📓 Configuration Jupyter..."
mkdir -p /root/.jupyter
cat > /root/.jupyter/jupyter_notebook_config.py << 'EOFD'
c.NotebookApp.ip = '0.0.0.0'
c.NotebookApp.port = 8888
c.NotebookApp.open_browser = False
c.NotebookApp.notebook_dir = '/opt/harmonic-ai/notebooks'
c.NotebookApp.password = 'harmonic-ai-2024'
EOFD

# Création notebooks
mkdir -p /opt/harmonic-ai/notebooks
cat > /opt/harmonic-ai/notebooks/test_harmonic_ai.ipynb << 'EOFD'
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# 🌊 Test Harmonic AI GPU Instance\n",
    "\n",
    "Ce notebook teste les capacités GPU de l'instance Harmonic AI."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Test CUDA\n",
    "import torch\n",
    "print(f\"CUDA disponible: {torch.cuda.is_available()}\")\n",
    "print(f\"Nombre de GPU: {torch.cuda.device_count()}\")\n",
    "if torch.cuda.is_available():\n",
    "    print(f\"GPU actuel: {torch.cuda.get_device_name()}\")\n",
    "    print(f\"Mémoire GPU: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Test Mathstral\n",
    "from harmonic_ai.domains.mathematics.dual_math_generator import DualMathGenerator\n",
    "\n",
    "# Configuration\n",
    "aws_config = {\n",
    "    \"bucket_name\": \"harmonic-ai-knowledge-base\",\n",
    "    \"access_key\": os.getenv(\"AWS_ACCESS_KEY_ID\"),\n",
    "    \"secret_key\": os.getenv(\"AWS_SECRET_ACCESS_KEY\"),\n",
    "    \"region\": \"us-east-1\"\n",
    "}\n",
    "\n",
    "# Test générateur\n",
    "generator = DualMathGenerator(aws_config)\n",
    "print(\"✅ Générateur Mathstral initialisé\")"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
EOFD

# Démarrage services
echo "🚀 Démarrage services..."
systemctl start harmonic-gpu.service

# Installation terminée
echo "✅ Instance GPU configurée avec succès!"
echo "📊 Services disponibles:"
echo "   - Mathstral Service: http://localhost:5000"
echo "   - WizardMath Service: http://localhost:6000"
echo "   - Jupyter Notebook: http://localhost:8888"
echo "   - Prometheus: http://localhost:9090"
echo "🌊 Harmonic AI GPU Instance est prête!"
EOF

# Visual Instance User Data (g5.xlarge)
cat > visual-user-data.sh << 'EOF'
#!/bin/bash
# Configuration Visual Instance pour SDXL

set -e

echo "🎨 Initialisation Visual Instance pour Harmonic AI..."

# Mise à jour système
yum update -y

# Installation NVIDIA drivers et CUDA
echo "📦 Installation NVIDIA drivers..."
yum install -y gcc kernel-devel-$(uname -r) dkms

# Téléchargement NVIDIA driver
wget -P /tmp https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_520.61.05_linux.run
sh /tmp/cuda_11.8.0_520.61.05_linux.run --silent --dkms

# Installation Docker
echo "🐳 Installation Docker..."
yum install -y docker
systemctl start docker
systemctl enable docker

# Installation Python et dépendances
echo "🐍 Installation Python..."
yum install -y python3 python3-pip
pip3 install --upgrade pip

# Installation dépendances Visual
echo "📦 Installation dépendances Visual..."
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip3 install diffusers transformers accelerate
pip3 install pillow numpy scipy
pip3 install boto3 flask fastapi uvicorn
pip3 install opencv-python-headless
pip3 install matplotlib seaborn

# Configuration environnement
echo "🔧 Configuration environnement..."
export CUDA_HOME=/usr/local/cuda
export PATH=$PATH:$CUDA_HOME/bin
export LD_LIBRARY_PATH=$CUDA_HOME/lib64

# Création répertoires
mkdir -p /opt/harmonic-ai
cd /opt/harmonic-ai

# Clonage code Harmonic AI
echo "📥 Clonage code Harmonic AI..."
git clone https://github.com/your-org/harmonic-ai.git .

# Installation Stable Diffusion
echo "🎨 Installation Stable Diffusion..."
pip3 install --upgrade diffusers[torch]
pip3 install transformers accelerate
pip3 install xformers

# Configuration services
echo "🔧 Configuration services..."
cat > /etc/systemd/system/harmonic-visual.service << 'EOL'
[Unit]
Description=Harmonic AI Visual Service
After=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/harmonic-ai
ExecStart=/usr/bin/docker-compose up
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

systemctl enable harmonic-visual.service

# Installation Docker Compose
echo "🐳 Installation Docker Compose..."
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Configuration Docker Compose
echo "🔧 Configuration Docker Compose..."
cat > /opt/harmonic-ai/docker-compose.yml << 'EOFD'
version: '3.8'

services:
  sdxl-service:
    build: .
    ports:
      - "7000:7000"
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - HF_HOME=/app/models
    volumes:
      - ./models:/app/models
      - ./outputs:/app/outputs
      - ./data:/app/data
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

  visual-api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./outputs:/app/outputs
      - ./data:/app/data
    restart: unless-stopped

  monitoring:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring:/etc/prometheus
    restart: unless-stopped
EOFD

# Création Dockerfile
echo "🐳 Création Dockerfile..."
cat > /opt/harmonic-ai/Dockerfile << 'EOFD'
FROM nvidia/cuda:11.8-devel-ubuntu20.04

WORKDIR /app

# Installation Python et dépendances
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Installation dépendances Python
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copie code
COPY . .

# Exposition ports
EXPOSE 7000 8000

# Commande de démarrage
CMD ["python3", "launch_visual_generation.py"]
EOFD

# Création requirements.txt
echo "📝 Création requirements.txt..."
cat > /opt/harmonic-ai/requirements.txt << 'EOFD'
torch>=2.0.0
torchvision>=0.15.0
diffusers>=0.20.0
transformers>=4.30.0
accelerate>=0.20.0
numpy>=1.24.0
scipy>=1.10.0
pillow>=9.5.0
boto3>=1.26.0
flask>=2.3.0
fastapi>=0.100.0
uvicorn>=0.22.0
opencv-python-headless>=4.8.0
matplotlib>=3.7.0
seaborn>=0.12.0
xformers>=0.0.20
prometheus-client>=0.16.0
EOFD

# Configuration monitoring
echo "📊 Configuration monitoring..."
mkdir -p /opt/harmonic-ai/monitoring
cat > /opt/harmonic-ai/monitoring/prometheus.yml << 'EOFD'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'harmonic-visual'
    static_configs:
      - targets: ['localhost:7000', 'localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s
EOFD

# Installation CloudWatch agent
echo "☁️ Installation CloudWatch agent..."
yum install -y amazon-cloudwatch-agent

# Configuration CloudWatch
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOFD'
{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "cwagent"
  },
  "metrics": {
    "namespace": "HarmonicAI",
    "metrics_collected": {
      "cpu": {
        "measurement": [
          "cpu_utilization"
        ]
      },
      "memory": {
        "measurement": [
          "memory_utilization"
        ]
      },
      "disk": {
        "measurement": [
          "used_percent"
        ]
      }
    }
  }
}
EOFD

systemctl enable amazon-cloudwatch-agent
systemctl start amazon-cloudwatch-agent

# Création répertoires
mkdir -p /opt/harmonic-ai/models /opt/harmonic-ai/outputs /opt/harmonic-ai/data

# Téléchargement modèles SDXL
echo "🎨 Téléchargement modèles SDXL..."
mkdir -p /opt/harmonic-ai/models/sdxl
cd /opt/harmonic-ai/models/sdxl

# Création script de téléchargement
cat > download_models.py << 'EOL'
import torch
from diffusers import StableDiffusionXLImg2ImgPipeline
import os

print("🎨 Téléchargement modèles SDXL...")
try:
    pipeline = StableDiffusionXLImg2ImgPipeline.from_pretrained(
        "stabilityai/stable-diffusion-xl-refiner-1.0",
        torch_dtype=torch.float16,
        variant="fp16",
        use_safetensors=True
    )
    pipeline.save_pretrained("./sdxl-refiner")
    print("✅ SDXL Refiner téléchargé")
except Exception as e:
    print(f"❌ Erreur téléchargement SDXL: {e}")

print("🎨 Téléchargement terminé")
EOL

python3 download_models.py

# Démarrage services
echo "🚀 Démarrage services..."
systemctl start harmonic-visual.service

# Installation terminée
echo "✅ Instance Visual configurée avec succès!"
echo "📊 Services disponibles:"
echo "   - SDXL Service: http://localhost:7000"
echo "   - Visual API: http://localhost:8000"
echo "   - Prometheus: http://localhost:9090"
echo "🎨 Harmonic AI Visual Instance est prête!"
EOF

# API Instance User Data (t3.large)
cat > api-user-data.sh << 'EOF'
#!/bin/bash
# Configuration API Instance pour Prompt System

set -e

echo "🧠 Initialisation API Instance pour Harmonic AI..."

# Mise à jour système
yum update -y

# Installation Python et dépendances
echo "🐍 Installation Python..."
yum install -y python3 python3-pip
pip3 install --upgrade pip

# Installation dépendances API
echo "📦 Installation dépendances API..."
pip3 install fastapi uvicorn
pip3 install flask gunicorn
pip3 install numpy scipy
pip3 install boto3
pip3 install prometheus-client
pip3 install redis
pip3 install psycopg2-binary
pip3 install celery
pip3 install pydantic
pip3 install python-multipart

# Configuration environnement
echo "🔧 Configuration environnement..."
mkdir -p /opt/harmonic-ai
cd /opt/harmonic-ai

# Clonage code Harmonic AI
echo "📥 Clonage code Harmonic AI..."
git clone https://github.com/your-org/harmonic-ai.git .

# Configuration services
echo "🔧 Configuration services..."
cat > /etc/systemd/system/harmonic-api.service << 'EOL'
[Unit]
Description=Harmonic AI API Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/harmonic-ai
ExecStart=/usr/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

systemctl enable harmonic-api.service

# Installation Docker Compose
echo "🐳 Installation Docker Compose..."
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Configuration Docker Compose
echo "🔧 Configuration Docker Compose..."
cat > /opt/harmonic-ai/docker-compose.yml << 'EOFD'
version: '3.8'

services:
  api-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/harmonic_ai
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    restart: unless-stopped

  prompt-service:
    build: .
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/harmonic_ai
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    restart: unless-stopped

  worker:
    build: .
    command: celery -A main.celery worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/harmonic_ai
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=harmonic_ai
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  monitoring:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring:/etc/prometheus
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    restart: unless-stopped
EOFD

# Création Dockerfile
echo "🐳 Création Dockerfile..."
cat > /opt/harmonic-ai/Dockerfile << 'EOFD'
FROM python:3.9-slim

WORKDIR /app

# Installation dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie code
COPY . .

# Exposition port
EXPOSE 8000

# Commande de démarrage
CMD ["gunicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOFD

# Création requirements.txt
echo "📝 Création requirements.txt..."
cat > /opt/harmonic-ai/requirements.txt << 'EOFD'
fastapi>=0.100.0
uvicorn>=0.22.0
flask>=2.3.0
gunicorn>=20.1.0
numpy>=1.24.0
scipy>=1.10.0
boto3>=1.26.0
prometheus-client>=0.16.0
redis>=4.5.0
psycopg2-binary>=2.9.0
celery>=5.2.0
pydantic>=1.10.0
python-multipart>=0.0.6
jinja2>=3.1.0
EOFD

# Configuration monitoring
echo "📊 Configuration monitoring..."
mkdir -p /opt/harmonic-ai/monitoring
cat > /opt/harmonic-ai/monitoring/prometheus.yml << 'EOFD'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'harmonic-api'
    static_configs:
      - targets: ['localhost:8000', 'localhost:8001']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'postgres'
    static_configs:
      - targets: ['db:5432']
EOFD

# Installation CloudWatch agent
echo "☁️ Installation CloudWatch agent..."
yum install -y amazon-cloudwatch-agent

# Configuration CloudWatch
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOFD'
{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "cwagent"
  },
  "metrics": {
    "namespace": "HarmonicAI",
    "metrics_collected": {
      "cpu": {
        "measurement": [
          "cpu_utilization"
        ]
      },
      "memory": {
        "measurement": [
          "memory_utilization"
        ]
      },
      "disk": {
        "measurement": [
          "used_percent"
        ]
      }
    }
  }
}
EOFD

systemctl enable amazon-cloudwatch-agent
systemctl start amazon-cloudwatch-agent

# Configuration Nginx
echo "🌐 Installation Nginx..."
yum install -y nginx

# Configuration Nginx
cat > /etc/nginx/nginx.conf << 'EOFD'
events {
    worker_connections 1024;
}

http {
    upstream api {
        server localhost:8000;
        server localhost:8001;
    }

    server {
        listen 80;
        server_name _;

        location / {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /metrics {
            proxy_pass http://localhost:9090;
        }
    }
}
EOFD

systemctl enable nginx
systemctl start nginx

# Démarrage services
echo "🚀 Démarrage services..."
systemctl start harmonic-api.service

# Installation terminée
echo "✅ Instance API configurée avec succès!"
echo "📊 Services disponibles:"
echo "   - API Service: http://localhost:8000"
echo "   - Prompt Service: http://localhost:8001"
echo "   - Nginx: http://localhost"
echo "   - Prometheus: http://localhost:9090"
echo "   - Grafana: http://localhost:3000"
echo "🧠 Harmonic AI API Instance est prête!"
EOF

echo "✅ Scripts user data créés!"
echo "📁 Fichiers générés:"
echo "   - gpu-user-data.sh"
echo "   - visual-user-data.sh"
echo "   - api-user-data.sh"
echo "🚀 Prêts pour déploiement AWS!"
