#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SYSTEME INTERACTIF HCS - Version Auto Demo
Lance le systeme reel avec valeurs par defaut pour demonstration
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dataclasses import dataclass
from typing import Optional


@dataclass
class CompressionProfile:
    """Profil de compression genere"""
    name: str
    usage_type: str
    priority: str
    k_factor: float
    webp_quality: int
    temporal_weight: float
    quality_threshold: float
    expected_ratio: str
    description: str
    expert_mode: bool = False


def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def save_profile(profile, filename):
    """Sauvegarde le profil dans un fichier JSON"""
    import json
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'name': profile.name,
            'usage_type': profile.usage_type,
            'priority': profile.priority,
            'k_factor': profile.k_factor,
            'webp_quality': profile.webp_quality,
            'temporal_weight': profile.temporal_weight,
            'quality_threshold': profile.quality_threshold,
            'expected_ratio': profile.expected_ratio,
            'description': profile.description,
            'expert_mode': profile.expert_mode
        }, f, indent=2, ensure_ascii=False)
    return filename


def display_profile(profile):
    """Affiche le profil genere"""
    print_header(f"PROFIL GENERE: {profile.name}")
    
    print(f"Description: {profile.description}\n")
    print("PARAMETRES DE COMPRESSION:\n")
    print(f"  K-Factor:              {profile.k_factor}")
    print(f"  WebP Quality:          {profile.webp_quality}")
    print(f"  Poids Temporel:        {profile.temporal_weight}")
    print(f"  Seuil Qualite Min:     {profile.quality_threshold}")
    print()
    print(f"Ratio attendu: {profile.expected_ratio}")
    print(f"Mode: {'Expert' if profile.expert_mode else 'Assiste'}")
    print()
    
    # Conseils
    print("CONSEILS D'UTILISATION:\n")
    if profile.k_factor < 0.010:
        print("  • Qualite tres elevee - ideal pour post-production")
    elif profile.k_factor > 0.015:
        print("  • Compression elevee - verifier la qualite sur echantillon")
    
    if profile.webp_quality > 90:
        print("  • WebP haute qualite - preservation excellente des details")
    
    if profile.temporal_weight > 0.85:
        print("  • Priorite fluidite - recommande pour contenu dynamique")
    
    print()


def run_auto_demo():
    """Lance le systeme avec configuration automatique"""
    
    print("=" * 70)
    print("  SYSTEME INTERACTIF HCS - MODE AUTO DEMO")
    print("=" * 70)
    print()
    print("Lancement automatique avec configuration par defaut...")
    print("(Dans la version reelle, vous repondriez aux questions interactives)")
    print()
    
    # Mode BROADCAST (valeurs par defaut recommendees)
    print("Configuration automatique selectionnee:")
    print("  Mode: BROADCAST (Qualite professionnelle)")
    print("  Usage: TV / Broadcast / Documentaire")
    print("  Priorite: Equilibre qualite/taille")
    print("  Contenu: Mixte / Divers")
    print("  Ratio cible: 100-200:1")
    print()
    
    # Configuration BROADCAST standard
    profile = CompressionProfile(
        name="Broadcast Pro Auto",
        usage_type="broadcast",
        priority="balanced",
        k_factor=0.012,
        webp_quality=88,
        temporal_weight=0.80,
        quality_threshold=0.88,
        expected_ratio="100-200:1",
        description="Standard broadcast TV professionnelle - Configuration equilibree",
        expert_mode=False
    )
    
    # Afficher le profil genere
    display_profile(profile)
    
    print("[OK] Profil genere automatiquement!")
    print()
    
    # Sauvegarder
    filename = save_profile(profile, "profile_broadcast_auto.json")
    print(f"Profil sauvegarde dans: {filename}")
    print()
    
    print("=" * 70)
    print("SYSTEME PRET!")
    print("=" * 70)
    print()
    print("Le systeme est configure et pret a compresser.")
    print()
    print("PARAMETRES ACTIFS:")
    print(f"  K-Factor: {profile.k_factor}")
    print(f"  WebP Quality: {profile.webp_quality}")
    print(f"  Poids Temporel: {profile.temporal_weight}")
    print()
    print("Pour compresser une video reelle:")
    print("  1. Mode interactif: python interactive_compression_system.py")
    print("  2. Directement:")
    print("     from pro_compression_strategy import ProVideoCompressionStrategy")
    print("     from pro_compression_strategy import ProQualityPreset")
    print("     strategy = ProVideoCompressionStrategy(ProQualityPreset.BROADCAST)")
    print("     result = strategy.compress_video_pro('votre_video.mp4')")
    print()
    print("=" * 70)


if __name__ == "__main__":
    run_auto_demo()
