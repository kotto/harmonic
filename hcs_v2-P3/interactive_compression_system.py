#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SYSTEME INTERACTIF DE COMPRESSION VIDEO HCS
Configure automatiquement les parametres selon les besoins
Mode simple pour tous + Mode expert pour specialistes
"""

import sys
import os
import json
from enum import Enum
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import config UTF-8 pour Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)


class UsageType(Enum):
    """Types d'usage pour configuration automatique"""
    CINEMA_MASTER = "cinema"
    BROADCAST_TV = "broadcast"
    STREAMING_4K = "streaming"
    WEB_YOUTUBE = "web"
    ARCHIVE_MUSEUM = "archive"
    SOCIAL_MEDIA = "social"
    CUSTOM = "custom"


class PriorityType(Enum):
    """Priorites de compression"""
    QUALITY_MAX = "quality"      # Qualite avant tout
    BALANCED = "balanced"        # Equilibre qualite/taille
    SIZE_MIN = "size"           # Taille minimale


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


class InteractiveCompressionSystem:
    """
    Systeme interactif de configuration compression
    Mode assiste pour debutants + Mode expert pour professionnels
    """
    
    def __init__(self):
        self.current_profile: Optional[CompressionProfile] = None
        self.expert_mode = False
        
    def clear_screen(self):
        """Nettoie l'ecran"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title: str):
        """Affiche un titre formate"""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70 + "\n")
    
    def ask_question(self, question: str, options: list, default: int = 0) -> int:
        """Pose une question avec options numerotees"""
        print(f"{question}\n")
        for i, option in enumerate(options, 1):
            marker = " [DEFAUT]" if i-1 == default else ""
            print(f"  {i}. {option}{marker}")
        print()
        
        while True:
            try:
                response = input(f"Votre choix (1-{len(options)}, Entree={default+1}): ").strip()
                if response == "":
                    return default
                choice = int(response) - 1
                if 0 <= choice < len(options):
                    return choice
                print(f"Choix invalide. Entrez un nombre entre 1 et {len(options)}")
            except ValueError:
                print("Entree invalide. Veuillez entrer un nombre.")
    
    def ask_yes_no(self, question: str, default: bool = True) -> bool:
        """Pose une question oui/non"""
        default_str = "O" if default else "N"
        while True:
            response = input(f"{question} (O/n, Entree={default_str}): ").strip().upper()
            if response == "":
                return default
            if response in ["O", "OUI", "Y", "YES"]:
                return True
            if response in ["N", "NON", "NO"]:
                return False
            print("Repondez par O (oui) ou N (non)")
    
    def ask_float(self, question: str, min_val: float, max_val: float, 
                  default: float) -> float:
        """Demande un nombre decimal"""
        while True:
            response = input(f"{question} [{min_val}-{max_val}, defaut={default}]: ").strip()
            if response == "":
                return default
            try:
                value = float(response)
                if min_val <= value <= max_val:
                    return value
                print(f"Valeur hors plage. Entrez entre {min_val} et {max_val}")
            except ValueError:
                print("Entree invalide. Veuillez entrer un nombre.")
    
    def ask_int(self, question: str, min_val: int, max_val: int, 
                default: int) -> int:
        """Demande un nombre entier"""
        while True:
            response = input(f"{question} [{min_val}-{max_val}, defaut={default}]: ").strip()
            if response == "":
                return default
            try:
                value = int(response)
                if min_val <= value <= max_val:
                    return value
                print(f"Valeur hors plage. Entrez entre {min_val} et {max_val}")
            except ValueError:
                print("Entree invalide. Veuillez entrer un nombre entier.")
    
    def run_wizard(self) -> CompressionProfile:
        """
        Assistant interactif de configuration
        """
        self.clear_screen()
        self.print_header("ASSISTANT DE COMPRESSION VIDEO HCS")
        
        print("Bienvenue dans l'assistant de configuration!")
        print("Je vais vous aider a choisir les meilleurs parametres")
        print("pour votre compression video.\n")
        
        # Choix mode
        print("MODE DE CONFIGURATION:\n")
        mode_choice = self.ask_question(
            "Choisissez votre mode:",
            [
                "Mode Assisté (recommandé) - Je reponds a quelques questions",
                "Mode Expert - Je regle tous les parametres manuellement"
            ],
            default=0
        )
        self.expert_mode = (mode_choice == 1)
        
        if self.expert_mode:
            return self._run_expert_mode()
        else:
            return self._run_assisted_mode()
    
    def _run_assisted_mode(self) -> CompressionProfile:
        """Mode assiste avec questions simples"""
        self.clear_screen()
        self.print_header("MODE ASSISTE - QUESTIONS SIMPLES")
        
        # Question 1: Usage principal
        print("QUESTION 1/4: Usage principal de la video\n")
        usage_choice = self.ask_question(
            "A quoi servira cette video?",
            [
                "Cinema / Etalonnage / VFX (qualite maximale)",
                "TV / Broadcast / Documentaire (qualite professionnelle)",
                "Streaming Premium (Netflix, Prime Video)",
                "Web / YouTube / Reseaux sociaux",
                "Archivage / Conservation long terme",
                "Autre (personnalise)"
            ],
            default=1
        )
        
        usage_map = [
            UsageType.CINEMA_MASTER,
            UsageType.BROADCAST_TV,
            UsageType.STREAMING_4K,
            UsageType.WEB_YOUTUBE,
            UsageType.ARCHIVE_MUSEUM,
            UsageType.CUSTOM
        ]
        usage_type = usage_map[usage_choice]
        
        # Question 2: Priorite
        self.clear_screen()
        self.print_header("MODE ASSISTE - QUESTIONS SIMPLES")
        print("QUESTION 2/4: Priorite de compression\n")
        
        priority_choice = self.ask_question(
            "Quelle est votre priorite?",
            [
                "Qualite maximale (fichier plus gros mais parfait)",
                "Equilibre qualite/taille (recommande)",
                "Taille minimale (compression maximale acceptable)"
            ],
            default=1
        )
        
        priority_map = [
            PriorityType.QUALITY_MAX,
            PriorityType.BALANCED,
            PriorityType.SIZE_MIN
        ]
        priority = priority_map[priority_choice]
        
        # Question 3: Type de contenu (si pertinent)
        self.clear_screen()
        self.print_header("MODE ASSISTE - QUESTIONS SIMPLES")
        print("QUESTION 3/4: Type de contenu\n")
        
        content_choice = self.ask_question(
            "Quel type de contenu?",
            [
                "Interview / Documentaire (peu de mouvement)",
                "Film / Fiction (grain, nuances)",
                "Sport / Action (mouvement rapide)",
                "Animation / Graphisme (contenu net)",
                "Mixte / Divers"
            ],
            default=4
        )
        
        content_types = ["interview", "film", "sport", "animation", "mixed"]
        content_type = content_types[content_choice]
        
        # Question 4: Taille souhaitee
        self.clear_screen()
        self.print_header("MODE ASSISTE - QUESTIONS SIMPLES")
        print("QUESTION 4/4: Objectif de compression\n")
        
        ratio_choice = self.ask_question(
            "Quel niveau de compression souhaitez-vous?",
            [
                "Faible (20-50x plus petit) - Qualite quasi parfaite",
                "Modere (50-100x plus petit) - Excellente qualite",
                "Eleve (100-200x plus petit) - Tres bonne qualite",
                "Maximum (200-500x plus petit) - Bonne qualite",
                "Je ne sais pas (laissez l'assistant choisir)"
            ],
            default=2
        )
        
        ratio_targets = [30, 75, 150, 300, None]
        target_ratio = ratio_targets[ratio_choice]
        
        # Generation du profil
        profile = self._generate_profile(
            usage_type, priority, content_type, target_ratio
        )
        
        # Affichage resultat
        self._display_profile(profile)
        
        # Confirmation
        if self.ask_yes_no("\nUtiliser ce profil?", default=True):
            return profile
        else:
            print("\nRetour au mode expert...")
            return self._run_expert_mode()
    
    def _run_expert_mode(self) -> CompressionProfile:
        """Mode expert avec controle total"""
        self.clear_screen()
        self.print_header("MODE EXPERT - REGLAGE MANUEL")
        
        print("Mode Expert: Controle total des parametres\n")
        print("Plages recommandees:\n")
        print("  K-Factor: 0.005-0.020 (plus petit = meilleure qualite)")
        print("  WebP Quality: 75-98 (plus grand = meilleure qualite)")
        print("  Poids Temporel: 0.0-1.0 (plus grand = plus fluide)")
        print("  Seuil Qualite: 0.80-0.98 (minimum acceptable)\n")
        
        # Saisie manuelle
        k_factor = self.ask_float(
            "K-Factor", 0.001, 0.1, 0.012
        )
        
        webp_quality = self.ask_int(
            "WebP Quality", 1, 100, 88
        )
        
        temporal_weight = self.ask_float(
            "Poids coherence temporelle", 0.0, 1.0, 0.80
        )
        
        quality_threshold = self.ask_float(
            "Seuil qualite minimum", 0.5, 1.0, 0.88
        )
        
        target_psnr = self.ask_float(
            "PSNR cible (dB)", 30.0, 50.0, 42.0
        )
        
        target_ssim = self.ask_float(
            "SSIM cible", 0.8, 1.0, 0.96
        )
        
        max_ratio = self.ask_float(
            "Ratio compression max", 10.0, 1000.0, 250.0
        )
        
        # Nom du profil
        profile_name = input("\nNom du profil [Mon Profil Expert]: ").strip()
        if not profile_name:
            profile_name = "Mon Profil Expert"
        
        profile = CompressionProfile(
            name=profile_name,
            usage_type="expert",
            priority="custom",
            k_factor=k_factor,
            webp_quality=webp_quality,
            temporal_weight=temporal_weight,
            quality_threshold=quality_threshold,
            expected_ratio=f"Variable (max {max_ratio:.0f}:1)",
            description=f"Profil expert personnalise - PSNR:{target_psnr:.1f} SSIM:{target_ssim:.3f}",
            expert_mode=True
        )
        
        self._display_profile(profile)
        return profile
    
    def _generate_profile(self, usage: UsageType, priority: PriorityType,
                         content: str, target_ratio: Optional[float]) -> CompressionProfile:
        """Genere un profil automatiquement selon les reponses"""
        
        # Configuration de base selon usage
        base_configs = {
            UsageType.CINEMA_MASTER: {
                'k': 0.008, 'webp': 92, 'temp': 0.85, 'threshold': 0.92,
                'name': 'Cinema Master', 'ratio': '50-100:1'
            },
            UsageType.BROADCAST_TV: {
                'k': 0.012, 'webp': 88, 'temp': 0.80, 'threshold': 0.88,
                'name': 'Broadcast Pro', 'ratio': '100-200:1'
            },
            UsageType.STREAMING_4K: {
                'k': 0.015, 'webp': 85, 'temp': 0.75, 'threshold': 0.85,
                'name': 'Streaming 4K', 'ratio': '200-400:1'
            },
            UsageType.WEB_YOUTUBE: {
                'k': 0.018, 'webp': 82, 'temp': 0.70, 'threshold': 0.82,
                'name': 'Web Optimized', 'ratio': '300-500:1'
            },
            UsageType.ARCHIVE_MUSEUM: {
                'k': 0.010, 'webp': 95, 'temp': 0.90, 'threshold': 0.95,
                'name': 'Archive Museum', 'ratio': '30-80:1'
            },
            UsageType.CUSTOM: {
                'k': 0.012, 'webp': 88, 'temp': 0.80, 'threshold': 0.88,
                'name': 'Custom Profile', 'ratio': '100-200:1'
            }
        }
        
        config = base_configs[usage].copy()
        
        # Ajustements selon priorite
        if priority == PriorityType.QUALITY_MAX:
            config['k'] *= 0.8
            config['webp'] = min(98, config['webp'] + 3)
            config['threshold'] = min(0.98, config['threshold'] + 0.03)
            config['ratio'] = config['ratio'].replace('100-', '70-').replace('200-', '120-')
            config['name'] += ' (Qualite+)'
            
        elif priority == PriorityType.SIZE_MIN:
            config['k'] *= 1.3
            config['webp'] = max(75, config['webp'] - 5)
            config['threshold'] = max(0.80, config['threshold'] - 0.05)
            config['ratio'] = config['ratio'].replace('100-', '150-').replace('200-', '300-')
            config['name'] += ' (Compact)'
        
        # Ajustements selon contenu
        content_adjustments = {
            'interview': {'k': 1.2, 'webp': -2, 'temp': -0.05},
            'film': {'k': 0.9, 'webp': +2, 'temp': +0.05},
            'sport': {'k': 0.85, 'webp': +3, 'temp': +0.10},
            'animation': {'k': 1.3, 'webp': -3, 'temp': -0.05},
            'mixed': {'k': 1.0, 'webp': 0, 'temp': 0.0}
        }
        
        adj = content_adjustments[content]
        config['k'] = max(0.005, min(0.020, config['k'] * adj['k']))
        config['webp'] = max(75, min(98, config['webp'] + adj['webp']))
        config['temp'] = max(0.5, min(1.0, config['temp'] + adj['temp']))
        
        # Si ratio cible specifie
        if target_ratio:
            if target_ratio < 50:  # Faible compression
                config['k'] = 0.008
                config['webp'] = 92
            elif target_ratio > 200:  # Haute compression
                config['k'] = 0.016
                config['webp'] = 84
        
        # Description
        descriptions = {
            UsageType.CINEMA_MASTER: "Qualite cinematographique pour production et etalonnage",
            UsageType.BROADCAST_TV: "Standard broadcast TV professionnelle",
            UsageType.STREAMING_4K: "Optimise pour streaming premium 4K/8K",
            UsageType.WEB_YOUTUBE: "Optimise pour web et reseaux sociaux",
            UsageType.ARCHIVE_MUSEUM: "Conservation patrimoniale long terme",
            UsageType.CUSTOM: "Configuration personnalisee selon vos besoins"
        }
        
        return CompressionProfile(
            name=config['name'],
            usage_type=usage.value,
            priority=priority.value,
            k_factor=round(config['k'], 4),
            webp_quality=int(config['webp']),
            temporal_weight=round(config['temp'], 2),
            quality_threshold=round(config['threshold'], 2),
            expected_ratio=config['ratio'],
            description=descriptions[usage],
            expert_mode=False
        )
    
    def _display_profile(self, profile: CompressionProfile):
        """Affiche le profil genere"""
        self.clear_screen()
        self.print_header(f"PROFIL GENERE: {profile.name}")
        
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
    
    def save_profile(self, profile: CompressionProfile, filename: str = None):
        """Sauvegarde le profil dans un fichier JSON"""
        if filename is None:
            filename = f"profile_{profile.name.lower().replace(' ', '_')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(asdict(profile), f, indent=2, ensure_ascii=False)
        
        print(f"Profil sauvegarde dans: {filename}")
        return filename
    
    def load_profile(self, filename: str) -> CompressionProfile:
        """Charge un profil depuis un fichier JSON"""
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return CompressionProfile(**data)
    
    def apply_profile_to_strategy(self, profile: CompressionProfile):
        """Applique le profil a la strategie de compression"""
        from pro_compression_strategy import (
            ProVideoCompressionStrategy,
            ProCompressionConfig,
            ProQualityPreset
        )
        
        # Creer une config personnalisee
        custom_config = ProCompressionConfig(
            name=profile.name,
            k_factor=profile.k_factor,
            webp_quality=profile.webp_quality,
            temporal_coherence_weight=profile.temporal_weight,
            min_quality_threshold=profile.quality_threshold,
            target_psnr=42.0,
            target_ssim=0.96,
            max_compression_ratio=float(profile.expected_ratio.split('-')[1].replace(':1', '')) if '-' in profile.expected_ratio else 200.0,
            description=profile.description
        )
        
        # Injecter dans la strategie
        strategy = ProVideoCompressionStrategy(ProQualityPreset.BROADCAST)
        strategy.config = custom_config
        
        print(f"\nProfil '{profile.name}' applique avec succes!")
        print("Pret a compresser avec ces parametres.")
        
        return strategy


def main():
    """Point d'entree principal"""
    system = InteractiveCompressionSystem()
    
    try:
        # Lancer l'assistant
        profile = system.run_wizard()
        
        # Sauvegarder
        if system.ask_yes_no("\nSauvegarder ce profil?", default=True):
            filename = system.save_profile(profile)
        
        # Appliquer
        if system.ask_yes_no("\nAppliquer ce profil pour compression?", default=True):
            strategy = system.apply_profile_to_strategy(profile)
            
            # Demander video
            video_path = input("\nChemin de la video a compresser: ").strip()
            if video_path and os.path.exists(video_path):
                print("\nLancement de la compression...")
                result = strategy.compress_video_pro(video_path)
                print(f"\nCompression terminee!")
                print(f"Ratio: {result['compression']['ratio']:.1f}:1")
                print(f"Qualite: {result['compression']['quality_score']:.3f}")
            else:
                print("Video non trouvee. Vous pouvez compresser plus tard avec:")
                print(f"  strategy.compress_video_pro('chemin_video.mp4')")
        
        print("\n" + "=" * 70)
        print("Assistant termine. Merci d'avoir utilise HCS Compression!")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\nAssistant interrompu par l'utilisateur.")
    except Exception as e:
        print(f"\nErreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
