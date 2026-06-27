#!/usr/bin/env python3
"""Corriger les triples quotes échappées dans harmonic_code_generator.py"""
import re

with open('harmonic_saas/app/services/harmonic_code_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remplacer les \"\"\" échappés dans les templates par '''
# On ne touche qu'aux \"\"\" qui sont dans les chaînes de template
content = content.replace('\\"\\"\\"', "'''")

with open('harmonic_saas/app/services/harmonic_code_generator.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Correction effectuée: toutes les \\\"\\\"\\\" ont été remplacées par '''")
