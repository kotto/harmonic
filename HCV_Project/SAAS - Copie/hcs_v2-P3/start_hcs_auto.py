#!/usr/bin/env python3
"""
Lancement automatique du serveur HCS Studio avec configuration PRO
"""

import sys
import os
import subprocess

# Aller dans le repertoire hcs_studio_integrated
os.chdir('hcs_studio_integrated')

print("=" * 70)
print("  DEMARRAGE HCS STUDIO - MODE AUTOMATIQUE")
print("=" * 70)
print()
print("Configuration:")
print("  - Mode: AUTO (Broadcast Pro)")
print("  - K-Factor: 0.012")
print("  - WebP Quality: 88")
print("  - Port: 8013")
print()
print("URLs d'acces:")
print("  [WEB] http://localhost:8013")
print("  [API] http://localhost:8013/docs")
print("  [HEALTH] http://localhost:8013/api/v3/health")
print()
print("Arret: Ctrl+C")
print("=" * 70)
print()

# Lancer le serveur
subprocess.run([sys.executable, "server_fixed.py"])
