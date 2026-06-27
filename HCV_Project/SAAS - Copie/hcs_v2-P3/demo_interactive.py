#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEMO INTERACTIVE - Simulation du systeme de compression
Montre le fonctionnement complet avec reponses simulees
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)


def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def simulate_interactive_mode():
    """Simule une session interactive complete"""
    
    print_header("DEMO - ASSISTANT DE COMPRESSION VIDEO HCS")
    
    print("Bienvenue dans l'assistant de configuration!")
    print("Je vais vous aider a choisir les meilleurs parametres")
    print("pour votre compression video.\n")
    
    print("MODE DE CONFIGURATION:\n")
    print("Choisissez votre mode:")
    print("  1. Mode Assisté (recommande) - Je reponds a quelques questions [DEFAUT]")
    print("  2. Mode Expert - Je regle tous les parametres manuellement")
    print()
    
    # Simulation choix utilisateur
    print("Votre choix (1-2, Entree=1): 1  [UTILISATEUR CHOISIT MODE ASSISTE]")
    print()
    print(">>> Mode Assisté sélectionne\n")
    
    # Question 1
    print_header("MODE ASSISTE - QUESTION 1/4")
    print("Usage principal de la video\n")
    print("A quoi servira cette video?")
    print("  1. Cinema / Etalonnage / VFX (qualite maximale)")
    print("  2. TV / Broadcast / Documentaire (qualite professionnelle) [DEFAUT]")
    print("  3. Streaming Premium (Netflix, Prime Video)")
    print("  4. Web / YouTube / Reseaux sociaux")
    print("  5. Archivage / Conservation long terme")
    print("  6. Autre (personnalise)")
    print()
    
    print("Votre choix (1-6, Entree=2): 2  [UTILISATEUR CHOISIT TV/BROADCAST]")
    print()
    print(">>> Usage: Broadcast TV\n")
    
    # Question 2
    print_header("MODE ASSISTE - QUESTION 2/4")
    print("Priorite de compression\n")
    print("Quelle est votre priorite?")
    print("  1. Qualite maximale (fichier plus gros mais parfait)")
    print("  2. Equilibre qualite/taille (recommande) [DEFAUT]")
    print("  3. Taille minimale (compression maximale acceptable)")
    print()
    
    print("Votre choix (1-3, Entree=2): 1  [UTILISATEUR CHOISIT QUALITE MAX]")
    print()
    print(">>> Priorite: Qualite maximale\n")
    
    # Question 3
    print_header("MODE ASSISTE - QUESTION 3/4")
    print("Type de contenu\n")
    print("Quel type de contenu?")
    print("  1. Interview / Documentaire (peu de mouvement)")
    print("  2. Film / Fiction (grain, nuances)")
    print("  3. Sport / Action (mouvement rapide)")
    print("  4. Animation / Graphisme (contenu net)")
    print("  5. Mixte / Divers [DEFAUT]")
    print()
    
    print("Votre choix (1-5, Entree=5): 2  [UTILISATEUR CHOISIT FILM/FICTION]")
    print()
    print(">>> Type: Film/Fiction\n")
    
    # Question 4
    print_header("MODE ASSISTE - QUESTION 4/4")
    print("Objectif de compression\n")
    print("Quel niveau de compression souhaitez-vous?")
    print("  1. Faible (20-50x plus petit) - Qualite quasi parfaite")
    print("  2. Modere (50-100x plus petit) - Excellente qualite [DEFAUT]")
    print("  3. Eleve (100-200x plus petit) - Tres bonne qualite")
    print("  4. Maximum (200-500x plus petit) - Bonne qualite")
    print("  5. Je ne sais pas (laissez l'assistant choisir)")
    print()
    
    print("Votre choix (1-5, Entree=2): 1  [UTILISATEUR CHOISIT FAIBLE COMPRESSION]")
    print()
    print(">>> Objectif: Faible compression (qualite max)\n")
    
    # Generation profil
    print("Analyse des reponses...")
    print("Configuration de base: Broadcast TV")
    print("Ajustement priorite: Qualite+ (K*0.8, WebP+3)")
    print("Ajustement contenu: Film (K*0.9, WebP+2)")
    print("Ajustement ratio: Faible (K=0.008)")
    print()
    
    # Affichage profil
    print_header("PROFIL GENERE: Broadcast Pro (Qualite+)")
    
    print("Description: Standard broadcast TV professionnelle\n")
    print("PARAMETRES DE COMPRESSION:\n")
    print("  K-Factor:              0.0086")
    print("  WebP Quality:          93")
    print("  Poids Temporel:        0.90")
    print("  Seuil Qualite Min:     0.91")
    print()
    print("Ratio attendu: 70-120:1")
    print("Mode: Assisté")
    print()
    
    print("CONSEILS D'UTILISATION:\n")
    print("  • Qualite tres elevee - ideal pour post-production")
    print("  • WebP haute qualite - preservation excellente des details")
    print("  • Priorite fluidite - recommande pour contenu dynamique")
    print()
    
    # Confirmation
    print("Utiliser ce profil? (O/n, Entree=O): O  [UTILISATEUR CONFIRME]")
    print()
    print(">>> Profil accepte!\n")
    
    # Sauvegarde
    print("Sauvegarder ce profil? (O/n, Entree=O): O  [UTILISATEUR SAUVEGARDE]")
    print()
    print(">>> Profil sauvegarde dans: profile_broadcast_pro_qualite.json\n")
    
    # Application
    print("Appliquer ce profil pour compression? (O/n, Entree=O): O")
    print()
    print(">>> Profil 'Broadcast Pro (Qualite+)' applique avec succes!")
    print("    Pret a compresser avec ces parametres.\n")
    
    # Demande video
    print("Chemin de la video a compresser: C:/Videos/mon_film.mp4")
    print()
    print(">>> Video trouvee. Lancement de la compression...")
    print()
    
    # Simulation compression
    print("Compression en cours...")
    print("  Frame 0/5400: Ratio=85.3:1, Qualite~0.93")
    print("  Frame 30/5400: Ratio=82.1:1, Qualite~0.92")
    print("  Frame 60/5400: Ratio=88.7:1, Qualite~0.94")
    print("  ...")
    print("  Frame 5400/5400: Ratio=84.2:1, Qualite~0.93")
    print()
    
    # Resultats
    print_header("COMPRESSION TERMINEE!")
    print("Resultats:")
    print("  Ratio: 84.2:1")
    print("  Qualite: 0.93")
    print("  Standard PRO: Respecte")
    print()
    print("Fichier compresse: C:/Videos/mon_film_compressed.mp4")
    print("Taille originale: 2.4 GB")
    print("Taille compressee: 29 MB")
    print()
    
    print("=" * 70)
    print("Assistant termine. Merci d'avoir utilise HCS Compression!")
    print("=" * 70)


def simulate_expert_mode():
    """Simule une session mode expert"""
    
    print_header("DEMO - MODE EXPERT")
    
    print("Mode Expert: Controle total des parametres\n")
    print("Plages recommandees:\n")
    print("  K-Factor: 0.005-0.020 (plus petit = meilleure qualite)")
    print("  WebP Quality: 75-98 (plus grand = meilleure qualite)")
    print("  Poids Temporel: 0.0-1.0 (plus grand = plus fluide)")
    print("  Seuil Qualite: 0.80-0.98 (minimum acceptable)\n")
    
    # Saisie manuelle simulee
    print("K-Factor [0.001-0.1, defaut=0.012]: 0.009  [SPECIALISTE]")
    print("WebP Quality [1-100, defaut=88]: 91  [SPECIALISTE]")
    print("Poids coherence temporelle [0.0-1.0, defaut=0.80]: 0.88  [SPECIALISTE]")
    print("Seuil qualite minimum [0.5-1.0, defaut=0.88]: 0.92  [SPECIALISTE]")
    print("PSNR cible [30.0-50.0, defaut=42.0]: 44.0  [SPECIALISTE]")
    print("SSIM cible [0.8-1.0, defaut=0.96]: 0.97  [SPECIALISTE]")
    print("Ratio compression max [10.0-1000.0, defaut=250.0]: 150.0  [SPECIALISTE]")
    print()
    
    print("Nom du profil [Mon Profil Expert]: Config Pro Cinema 4K  [SPECIALISTE]")
    print()
    
    # Affichage profil
    print_header("PROFIL GENERE: Config Pro Cinema 4K")
    
    print("Description: Profil expert personnalise - PSNR:44.0 SSIM:0.970\n")
    print("PARAMETRES DE COMPRESSION:\n")
    print("  K-Factor:              0.009")
    print("  WebP Quality:          91")
    print("  Poids Temporel:        0.88")
    print("  Seuil Qualite Min:     0.92")
    print()
    print("Ratio attendu: Variable (max 150:1)")
    print("Mode: Expert")
    print()
    
    print("CONSEILS D'UTILISATION:\n")
    print("  • Qualite tres elevee - ideal pour post-production")
    print("  • WebP haute qualite - preservation excellente des details")
    print("  • Priorite fluidite - recommande pour contenu dynamique")
    print()
    
    print("=" * 70)
    print("Configuration expert terminee!")
    print("=" * 70)


def main():
    """Demo principale"""
    
    print_header("DEMONSTRATION DU SYSTEME INTERACTIF HCS")
    
    print("Cette demo montre le fonctionnement complet du systeme")
    print("avec des reponses simulees d'utilisateurs.\n")
    
    print("Premiere demo: Mode Assisté (utilisateur standard)")
    print("-" * 70)
    input("\nAppuyez sur Entree pour commencer la demo Mode Assisté...")
    
    simulate_interactive_mode()
    
    print("\n\n")
    print("Deuxieme demo: Mode Expert (specialiste)")
    print("-" * 70)
    input("\nAppuyez sur Entree pour voir la demo Mode Expert...")
    
    simulate_expert_mode()
    
    print("\n\n")
    print("=" * 70)
    print("DEMONSTRATION TERMINEE")
    print("=" * 70)
    print()
    print("Pour utiliser le systeme reel:")
    print("  python interactive_compression_system.py")
    print()
    print("Le systeme vous guidera avec des questions interactives")
    print("pour configurer automatiquement votre compression!")
    print()


if __name__ == "__main__":
    main()
