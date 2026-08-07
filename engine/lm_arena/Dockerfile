FROM python:3.11-slim

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code
COPY . /app/engine/
COPY lm_arena/ /app/lm_arena/

WORKDIR /app/lm_arena

ENV PYTHONPATH=/app:/app/engine
ENV PORT=8000

EXPOSE 8000

CMD ["python", "api.py"]
