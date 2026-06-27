#!/usr/bin/env python3
"""
Gunicorn configuration for AWS App Runner
Optimized for long-running compression tasks
"""

import os
import multiprocessing

# Server settings
bind = '0.0.0.0:8080'
workers = 2
worker_class = 'gthread'
threads = 4  # Chaque worker gère 4 requêtes en parallèle — streaming non-bloquant

# Timeout for worker processes (seconds)
# AWS App Runner has 5min (300s) timeout for requests, set to 240s to be safe
timeout = int(os.environ.get('GUNICORN_TIMEOUT', '240'))

# Keep-alive between requests
keepalive = 30

# Max requests per worker before recycling (prevent memory leaks)
max_requests = 1000
max_requests_jitter = 100

# Server mechanics
preload_app = False
daemon = False
pidfile = None
umask = 0

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process naming
proc_name = 'hcv-pro-server'

print(f'[Gunicorn] Configured with {workers} workers x {threads} threads, timeout={timeout}s')
