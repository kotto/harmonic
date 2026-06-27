# KA Phone — Dockerfile (Serveur Canonique)
# ===========================================
# Multi-stage build for minimal image size
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (gcc + cmake pour llama-cpp-python, curl pour healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    g++ \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (llama-cpp-python se compile avec gcc/cmake sur Ubuntu)
COPY ka_phone/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (sans les modèles GGUF — montés en volume)
COPY ka_phone/ /app/ka_phone/

# Create data directories
RUN mkdir -p /app/data/memory /app/data/hcv /app/data/notes /app/data/reminders

# Expose port (canonical: 8420)
EXPOSE 8420

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8420/')" || exit 1

# Run the canonical unified server
WORKDIR /app/ka_phone
CMD ["python", "unified_server.py"]
