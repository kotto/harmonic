# ──────────────────────────────────────────────
# Dockerfile — KA Server (Flask)
# Port : 8765
# Services : Banking KARE, Simulation multi-agents,
#            Sonic ID, Harmonic AI, Chat, Wave Compute
# ──────────────────────────────────────────────
FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash appuser
WORKDIR /app

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ──────────────────────────────────────────────
# Builder
# ──────────────────────────────────────────────
FROM base AS builder

COPY requirements_server.txt .
RUN pip install --no-cache-dir -r requirements_server.txt

# ──────────────────────────────────────────────
# Runtime
# ──────────────────────────────────────────────
FROM base AS runtime

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Structure du projet
COPY --chown=appuser:appuser ka_server/           ./ka_server/
COPY --chown=appuser:appuser ka_config.py          .
COPY --chown=appuser:appuser vital-ka/core/python/ ./vital-ka/core/python/
COPY --chown=appuser:appuser data/                 ./data/

# Fichiers de configuration
COPY --chown=appuser:appuser .env.production       .env
COPY --chown=appuser:appuser ka_launcher.py        .

USER appuser

# Dossier de données persistant (banking ledger, simulation results)
VOLUME /app/data

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8765/api/banking/health || curl -f http://localhost:8765/api/health || exit 1

EXPOSE 8765

CMD ["python", "ka_launcher.py", "--product", "enterprise", "--port", "8765"]