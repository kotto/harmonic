# ═══════════════════════════════════════════════════════════════════════════════
# KA Enterprise — Image Docker (CPU uniquement, aucun GPU requis)
#
# Build (depuis le dossier backend/enterprise) :
#   docker build -f deploy_vps/Dockerfile -t ka-enterprise:latest .
#
# ═══════════════════════════════════════════════════════════════════════════════
FROM python:3.11-slim

# Pas d'interactivité pip, logs visibles immédiatement
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dépendances (légères : numpy + flask uniquement)
COPY deploy_vps/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Code de l'application (moteur enterprise + cœur ondulatoire)
COPY . /app

# Volume des données persistantes : tenants, hologrammes, clés API, audit
VOLUME /app/data

EXPOSE 8767

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8767/api/enterprise/info', timeout=4)" || exit 1

CMD ["python", "ka_enterprise_server.py", "--port", "8767", "--host", "0.0.0.0"]
