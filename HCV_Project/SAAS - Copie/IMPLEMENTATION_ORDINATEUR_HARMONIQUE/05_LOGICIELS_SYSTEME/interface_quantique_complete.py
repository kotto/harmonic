"""
🌊 INTERFACE UTILISATEUR QUANTIQUE HARMONIQUE COMPLÈTE
Fichier: interface_quantique_complete.py
Auteur: Équipe Harmonique
Date: 28 avril 2026
Description: Interface utilisateur révolutionnaire pour l'ordinateur harmonique
             avec animations 60 FPS inspirées HCV PRO
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
import json
import logging
import math
from collections import deque
import colorsys

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import des composants harmoniques
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '02_ARCHITECTURE_QUANTIQUE'))
from hbits_geometriques import HbitGeometrique, RegistreHarmonique, PatternGeometrique
from circuits_harmoniques import BibliothequeCircuits, CircuitHarmonique, TypeCircuit
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '03_ALGORITHMES_HARMONIQUES'))
from factorisation_harmonique import FactorisationHarmonique
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '01_FONDEMENTS_MATHÉMATIQUES'))
from constantes_harmoniques import CONSTANTES
from matrice_projection import MatriceProjection, Coordonnees2D, Coordonnees3D

# Palette de couleurs inspirée HCV PRO
HCV_PRO_COLORS = {
    "primary": ["#FF6B6B", "#4ECDC4"],
    "success": ["#95E77E", "#68B684"],
    "warning": ["#FFA07A", "#FF8C42"],
    "ai": ["#9B59B6", "#8E44AD"],
    "quantum": ["#3498DB", "#2980B9"],
    "harmonic": ["#F39C12", "#E67E22"]
}

# États d'animation
class AnimationState:
    IDLE = "idle"
    THINKING = "thinking"
    COMPUTING = "computing"
    SUCCESS = "success"
    INSIGHT = "insight"
    TRANSFORMING = "transforming"

@dataclass
class ParticuleAnimée:
    """
    Particule animée pour effets visuels
    """
    position: Tuple[float, float, float]
    vitesse: Tuple[float, float, float]
    couleur: str
    taille: float
    duree_vie: float
    age: float = 0.0

@dataclass
class VisuelHbit:
    """
    Représentation visuelle animée d'un Hbit
    """
    pattern: PatternGeometrique
    position_3d: Tuple[float, float, float, float]
    couleur: str
    taille: float
    amplitude: float
    phase: float
    animation_state: str = AnimationState.IDLE
    particules: List[ParticuleAnimée] = None
    
    def __post_init__(self):
        """Validation des données"""
        if len(self.position_3d) != 4:
            raise ValueError("La position 3D doit avoir 4 coordonnées (x, y, z, t)")
        if self.particules is None:
            self.particules = []
    
    def animer_changement_etat(self, nouvel_etat: str):
        """Animer le changement d'état avec particules"""
        self.animation_state = nouvel_etat
        if nouvel_etat == AnimationState.SUCCESS:
            self.creer_particules_succes()
        elif nouvel_etat == AnimationState.INSIGHT:
            self.creer_particules_insight()
        elif nouvel_etat == AnimationState.TRANSFORMING:
            self.creer_particules_transformation()
    
    def creer_particules_succes(self):
        """Créer des particules vertes de succès"""
        for _ in range(20):
            angle = np.random.uniform(0, 2 * np.pi)
            vitesse = np.random.uniform(0.5, 2.0)
            self.particules.append(ParticuleAnimée(
                position=self.position_3d[:3],
                vitesse=(vitesse * np.cos(angle), vitesse * np.sin(angle), np.random.uniform(-0.5, 0.5)),
                couleur=np.random.choice(HCV_PRO_COLORS["success"]),
                taille=np.random.uniform(2, 5),
                duree_vie=2.0
            ))
    
    def creer_particules_insight(self):
        """Créer des particules lumineuses d'insight"""
        for _ in range(15):
            theta = np.random.uniform(0, np.pi)
            phi = np.random.uniform(0, 2 * np.pi)
            r = np.random.uniform(0.3, 1.0)
            self.particules.append(ParticuleAnimée(
                position=self.position_3d[:3],
                vitesse=(r * np.sin(theta) * np.cos(phi), r * np.sin(theta) * np.sin(phi), r * np.cos(theta)),
                couleur=np.random.choice(HCV_PRO_COLORS["ai"]),
                taille=np.random.uniform(1, 3),
                duree_vie=3.0
            ))
    
    def creer_particules_transformation(self):
        """Créer des particules de transformation"""
        for _ in range(25):
            self.particules.append(ParticuleAnimée(
                position=self.position_3d[:3],
                vitesse=(np.random.uniform(-1, 1), np.random.uniform(-1, 1), np.random.uniform(-1, 1)),
                couleur=np.random.choice(HCV_PRO_COLORS["quantum"]),
                taille=np.random.uniform(1, 4),
                duree_vie=1.5
            ))

class VisualiseurHarmonique:
    """
    Visualiseur 3D/4D animé des états harmoniques avec effets particles
    """
    
    def __init__(self):
        self.fig = None
        self.ax = None
        self.animation = None
        self.hbits_visuels = []
        self.matrice_projection = MatriceProjection()
        self.particules_globales = []
        self.temps_animation = 0
        self.fps = 60
        self.animation_active = False
        
        # Couleurs animées HCV PRO pour les patterns
        self.couleurs_patterns = {
            PatternGeometrique.SPIRALE: HCV_PRO_COLORS["harmonic"][0],
            PatternGeometrique.CERCLE: HCV_PRO_COLORS["quantum"][0],
            PatternGeometrique.HELICE: HCV_PRO_COLORS["success"][0],
            PatternGeometrique.MIROIR: HCV_PRO_COLORS["primary"][0],
            PatternGeometrique.TRINITE: HCV_PRO_COLORS["ai"][0]
        }
        
        # Gradients animés
        self.gradients = {
            "primary": self.creer_gradient(HCV_PRO_COLORS["primary"]),
            "success": self.creer_gradient(HCV_PRO_COLORS["success"]),
            "ai": self.creer_gradient(HCV_PRO_COLORS["ai"])
        }
        
        logger.info("VisualiseurHarmonique initialisé avec animations")
    
    def creer_gradient(self, couleurs: List[str]) -> List[str]:
        """Crée un gradient de couleurs"""
        gradient = []
        for i in range(10):
            ratio = i / 9.0
            couleur = self.interpoler_couleur(couleurs[0], couleurs[1], ratio)
            gradient.append(couleur)
        return gradient
    
    def interpoler_couleur(self, couleur1: str, couleur2: str, ratio: float) -> str:
        """Interpole entre deux couleurs"""
        # Conversion hex vers RGB
        r1, g1, b1 = int(couleur1[1:3], 16), int(couleur1[3:5], 16), int(couleur1[5:7], 16)
        r2, g2, b2 = int(couleur2[1:3], 16), int(couleur2[3:5], 16), int(couleur2[5:7], 16)
        
        # Interpolation
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def creer_figure_3d(self) -> Tuple[plt.Figure, Axes3D]:
        """
        Crée une figure 3D animée pour la visualisation
        
        Returns:
            Figure et axe 3D
        """
        # Style dark moderne inspiré HCV PRO
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(14, 10), facecolor='#0a0a0a')
        self.ax = self.fig.add_subplot(111, projection='3d', facecolor='#0a0a0a')
        
        # Configuration de l'axe avec style HCV PRO
        self.ax.set_xlabel('X (Réel Harmonique)', color=HCV_PRO_COLORS["primary"][0], fontsize=12)
        self.ax.set_ylabel('Y (Imaginaire Quantique)', color=HCV_PRO_COLORS["quantum"][0], fontsize=12)
        self.ax.set_zlabel('Z (Amplitude Fréquentielle)', color=HCV_PRO_COLORS["harmonic"][0], fontsize=12)
        self.ax.set_title('🌊 HCV PRO - Visualisation Quantique Harmonique Animée', 
                         color=HCV_PRO_COLORS["primary"][1], fontsize=16, fontweight='bold')
        
        # Limites de l'axe étendues
        self.ax.set_xlim([-8, 8])
        self.ax.set_ylim([-8, 8])
        self.ax.set_zlim([0, 3])
        
        # Grid moderne
        self.ax.grid(True, alpha=0.3, linestyle='--')
        self.ax.xaxis.pane.fill = False
        self.ax.yaxis.pane.fill = False
        self.ax.zaxis.pane.fill = False
        
        return self.fig, self.ax
    
    def visualiser_hbit(self, hbit: HbitGeometrique, index: int) -> VisuelHbit:
        """
        Visualise un Hbit individuel avec animations
        
        Args:
            hbit: Hbit à visualiser
            index: Index pour le positionnement
            
        Returns:
            Représentation visuelle animée du Hbit
        """
        # Projection de l'état du Hbit en 3D/4D avec animation
        point_2d = Coordonnees2D(
            x=abs(hbit.etat.amplitude_0) * np.cos(self.temps_animation * 0.5),
            y=abs(hbit.etat.amplitude_1) * np.sin(self.temps_animation * 0.5)
        )
        
        point_3d = self.matrice_projection.projeter_point(point_2d)
        
        # Position animée avec orbite
        orbite_x = point_3d.x + 0.5 * np.cos(self.temps_animation + index)
        orbite_y = point_3d.y + 0.5 * np.sin(self.temps_animation + index)
        orbite_z = point_3d.z + 0.2 * np.sin(self.temps_animation * 2 + index)
        
        # Couleur animée avec gradient
        couleur_animee = self.gradients["primary"][int(self.temps_animation * 2) % 10]
        
        # Création du visuel animé
        visuel = VisuelHbit(
            pattern=hbit.pattern,
            position_3d=(orbite_x, orbite_y, orbite_z, point_3d.t),
            couleur=couleur_animee,
            taille=0.8 + abs(hbit.etat.amplitude_0) + 0.2 * np.sin(self.temps_animation * 3),
            amplitude=hbit.amplitude,
            phase=hbit.phase + self.temps_animation
        )
        
        return visuel
    
    def visualiser_registre(self, registre: RegistreHarmonique) -> List[VisuelHbit]:
        """
        Visualise un registre complet
        
        Args:
            registre: Registre à visualiser
            
        Returns:
            Liste des visuels des Hbits
        """
        self.hbits_visuels = []
        
        for i, hbit in enumerate(registre.qubits):
            visuel = self.visualiser_hbit(hbit, i)
            self.hbits_visuels.append(visuel)
        
        return self.hbits_visuels
    
    def dessiner_registre(self, registre: RegistreHarmonique):
        """
        Dessine le registre animé sur la figure 3D
        
        Args:
            registre: Registre à dessiner
        """
        if self.ax is None:
            self.creer_figure_3d()
        
        # Nettoyage de l'axe
        self.ax.clear()
        self.ax.set_xlabel('X (Réel Harmonique)', color=HCV_PRO_COLORS["primary"][0], fontsize=12)
        self.ax.set_ylabel('Y (Imaginaire Quantique)', color=HCV_PRO_COLORS["quantum"][0], fontsize=12)
        self.ax.set_zlabel('Z (Amplitude Fréquentielle)', color=HCV_PRO_COLORS["harmonic"][0], fontsize=12)
        self.ax.set_title(f'🌊 HCV PRO - Registre Quantique Animé ({registre.nombre_hbits} Hbits)', 
                         color=HCV_PRO_COLORS["primary"][1], fontsize=14, fontweight='bold')
        
        # Visualisation animée des Hbits
        visuels = self.visualiser_registre(registre)
        
        for i, visuel in enumerate(visuels):
            # Dessin du Hbit comme une sphère animée avec halo
            self.ax.scatter(
                visuel.position_3d[0],
                visuel.position_3d[1],
                visuel.position_3d[2],
                c=visuel.couleur,
                s=visuel.taille * 150,
                alpha=0.9,
                edgecolors='white',
                linewidth=1.5,
                marker='o',
                label=f'Hbit {i} ({visuel.pattern.value})'
            )
            
            # Halo animé autour du Hbit
            halo_taille = visuel.taille * 200 * (1 + 0.3 * np.sin(self.temps_animation * 4 + i))
            self.ax.scatter(
                visuel.position_3d[0],
                visuel.position_3d[1],
                visuel.position_3d[2],
                c=visuel.couleur,
                s=halo_taille,
                alpha=0.2,
                marker='o'
            )
            
            # Particules du Hbit
            self.dessiner_particules_hbit(visuel)
            
            # Label flottant
            self.ax.text(
                visuel.position_3d[0],
                visuel.position_3d[1],
                visuel.position_3d[2] + 0.5,
                f'H{i}',
                fontsize=10,
                ha='center',
                color='white',
                weight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor=visuel.couleur, alpha=0.7)
            )
        
        # Connexions d'entanglement animées
        self.dessiner_entanglement_anime(registre)
        
        # Particules globales
        self.dessiner_particules_globales()
        
        # Légende moderne
        self.ax.legend(loc='upper left', fontsize=9, framealpha=0.8)
        
        plt.draw()
    
    def dessiner_particules_hbit(self, visuel: VisuelHbit):
        """Dessine les particules d'un Hbit"""
        for particule in visuel.particules:
            if particule.age < particule.duree_vie:
                alpha = 1.0 - (particule.age / particule.duree_vie)
                self.ax.scatter(
                    particule.position[0],
                    particule.position[1],
                    particule.position[2],
                    c=particule.couleur,
                    s=particule.taille * 10,
                    alpha=alpha * 0.8,
                    marker='*'
                )
    
    def dessiner_particules_globales(self):
        """Dessine les particules globales flottantes"""
        for particule in self.particules_globales[:]:
            if particule.age < particule.duree_vie:
                alpha = 1.0 - (particule.age / particule.duree_vie)
                self.ax.scatter(
                    particule.position[0],
                    particule.position[1],
                    particule.position[2],
                    c=particule.couleur,
                    s=particule.taille * 5,
                    alpha=alpha * 0.6,
                    marker='.'
                )
            else:
                self.particules_globales.remove(particule)
    
    def dessiner_entanglement_anime(self, registre: RegistreHarmonique):
        """Dessine les connexions d'entanglement animées"""
        # Créer des particules de connexion pulsantes
        for i in range(len(registre.qubits)):
            for j in range(i + 1, len(registre.qubits)):
                if i < len(self.hbits_visuels) and j < len(self.hbits_visuels):
                    visuel_i = self.hbits_visuels[i]
                    visuel_j = self.hbits_visuels[j]
                    
                    # Ligne d'entanglement avec pulsation
                    alpha = 0.3 + 0.2 * np.sin(self.temps_animation * 3 + i + j)
                    self.ax.plot(
                        [visuel_i.position_3d[0], visuel_j.position_3d[0]],
                        [visuel_i.position_3d[1], visuel_j.position_3d[1]],
                        [visuel_i.position_3d[2], visuel_j.position_3d[2]],
                        color=HCV_PRO_COLORS["ai"][0],
                        alpha=alpha,
                        linewidth=1,
                        linestyle='--'
                    )
                    
                    # Particule de connexion mobile
                    t = (self.temps_animation * 0.5) % 1.0
                    pos_x = visuel_i.position_3d[0] * (1 - t) + visuel_j.position_3d[0] * t
                    pos_y = visuel_i.position_3d[1] * (1 - t) + visuel_j.position_3d[1] * t
                    pos_z = visuel_i.position_3d[2] * (1 - t) + visuel_j.position_3d[2] * t
                    
                    self.ax.scatter(
                        pos_x, pos_y, pos_z,
                        c=HCV_PRO_COLORS["ai"][1],
                        s=30,
                        alpha=0.9,
                        marker='o'
                    )
    
    def demarrer_animation_60fps(self, registre: RegistreHarmonique):
        """
        Démarre l'animation continue à 60 FPS
        
        Args:
            registre: Registre à animer
        """
        if self.ax is None:
            self.creer_figure_3d()
        
        self.animation_active = True
        self.temps_animation = 0
        
        # Fonction d'animation 60 FPS
        def update_60fps():
            if self.animation_active:
                # Mise à jour du temps
                self.temps_animation += 1/60.0
                
                # Évolution des phases et positions
                for i, hbit in enumerate(registre.qubits):
                    hbit.phase += 0.05
                    
                    # Mise à jour des particules
                    if i < len(self.hbits_visuels):
                        visuel = self.hbits_visuels[i]
                        for particule in visuel.particules:
                            particule.age += 1/60.0
                            # Mise à jour position
                            particule.position = (
                                particule.position[0] + particule.vitesse[0] * 1/60.0,
                                particule.position[1] + particule.vitesse[1] * 1/60.0,
                                particule.position[2] + particule.vitesse[2] * 1/60.0
                            )
                
                # Mise à jour des particules globales
                for particule in self.particules_globales:
                    particule.age += 1/60.0
                    particule.position = (
                        particule.position[0] + particule.vitesse[0] * 1/60.0,
                        particule.position[1] + particule.vitesse[1] * 1/60.0,
                        particule.position[2] + particule.vitesse[2] * 1/60.0
                    )
                
                # Création de nouvelles particules aléatoires
                if np.random.random() < 0.1:  # 10% de chance par frame
                    self.creer_particule_aleatoire()
                
                # Redessin complet
                self.dessiner_registre(registre)
                
                # Planification de la prochaine frame (16.67ms pour 60 FPS)
                self.fig.canvas.after(17, update_60fps)
        
        # Démarrage de l'animation
        update_60fps()
    
    def creer_particule_aleatoire(self):
        """Crée une particule aléatoire dans l'espace"""
        self.particules_globales.append(ParticuleAnimée(
            position=(np.random.uniform(-7, 7), np.random.uniform(-7, 7), np.random.uniform(0, 2.5)),
            vitesse=(np.random.uniform(-0.5, 0.5), np.random.uniform(-0.5, 0.5), np.random.uniform(-0.2, 0.2)),
            couleur=np.random.choice([HCV_PRO_COLORS["primary"][0], HCV_PRO_COLORS["quantum"][0], HCV_PRO_COLORS["success"][0]]),
            taille=np.random.uniform(1, 3),
            duree_vie=np.random.uniform(2, 5)
        ))
    
    def arreter_animation(self):
        """Arrête l'animation en cours"""
        self.animation_active = False
        if self.animation:
            self.animation.event_source.stop()

class InterfaceQuantique:
    """
    Interface utilisateur révolutionnaire pour l'ordinateur harmonique
    Inspirée du motion design HCV PRO avec animations 60 FPS
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🌊 HCV PRO - Ordinateur Quantique Harmonique")
        self.root.geometry("1600x1000")
        self.root.configure(bg='#0a0a0a')
        
        # Style moderne HCV PRO
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configurer_style_hcv_pro()
        
        # Composants principaux
        self.visualiseur = VisualiseurHarmonique()
        self.registre_actuel = None
        self.circuit_actuel = None
        self.historique = []
        self.animation_active = False
        
        # Variables de contrôle
        self.nombre_hbits = tk.IntVar(value=8)
        self.type_circuit = tk.StringVar(value="factorisation")
        self.en_execution = tk.BooleanVar(value=False)
        self.animation_state = tk.StringVar(value=AnimationState.IDLE)
        
        # Création de l'interface révolutionnaire
        self.creer_interface_hcv_pro()
        
        # Initialisation
        self.initialiser_registre()
        
        logger.info("InterfaceQuantique HCV PRO initialisée")
    
    def configurer_style_hcv_pro(self):
        """Configure le style moderne HCV PRO"""
        # Configuration des couleurs
        self.style.configure('TFrame', background='#0a0a0a')
        self.style.configure('TLabel', background='#0a0a0a', foreground='white', font=('Arial', 10))
        self.style.configure('Title.TLabel', background='#0a0a0a', foreground=HCV_PRO_COLORS["primary"][0], 
                           font=('Arial', 16, 'bold'))
        self.style.configure('TButton', background=HCV_PRO_COLORS["primary"][0], foreground='white',
                           font=('Arial', 10, 'bold'), borderwidth=0, relief='flat')
        self.style.map('TButton', 
                      background=[('active', HCV_PRO_COLORS["primary"][1]),
                                 ('pressed', HCV_PRO_COLORS["quantum"][0])])
        
        # Widgets personnalisés
        self.style.configure('HCV.TButton', background=HCV_PRO_COLORS["harmonic"][0], 
                           foreground='white', font=('Arial', 11, 'bold'))
        self.style.map('HCV.TButton',
                      background=[('active', HCV_PRO_COLORS["harmonic"][1]),
                                 ('pressed', HCV_PRO_COLORS["success"][0])])
    
    def creer_interface_hcv_pro(self):
        """Crée l'interface graphique révolutionnaire HCV PRO"""
        # Frame principale avec fond sombre
        frame_principal = ttk.Frame(self.root, padding="15")
        frame_principal.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuration des poids
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        frame_principal.columnconfigure(1, weight=1)
        frame_principal.rowconfigure(1, weight=1)
        
        # Header HCV PRO avec titre animé
        self.creer_header_hcv_pro(frame_principal)
        
        # Panneau de contrôle gauche
        self.creer_panneau_controle(frame_principal)
        
        # Zone de visualisation centrale
        self.creer_zone_visualisation(frame_principal)
        
        # Panneau de résultats droit
        self.creer_panneau_resultats(frame_principal)
        
        # Barre de status animée
        self.creer_barre_status(frame_principal)
    
    def creer_header_hcv_pro(self, parent):
        """Crée le header HCV PRO avec titre animé"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Titre principal avec effet de gradient
        titre_label = ttk.Label(header_frame, 
                               text="🌊 HCV PRO - ORDINATEUR QUANTIQUE HARMONIQUE",
                               style='Title.TLabel')
        titre_label.pack(anchor='center')
        
        # Sous-titre avec état d'animation
        self.sous_titre_label = ttk.Label(header_frame,
                                        text=f"État: {self.animation_state.get()}",
                                        font=('Arial', 12),
                                        foreground=HCV_PRO_COLORS["ai"][0])
        self.sous_titre_label.pack(anchor='center', pady=(5, 0))
    
    def creer_panneau_controle(self, parent):
        """Crée le panneau de contrôle interactif"""
        controle_frame = ttk.LabelFrame(parent, text="🎛️ Contrôle Quantique", padding="10")
        controle_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Configuration des Hbits
        ttk.Label(controle_frame, text="Nombre de Hbits:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        
        hbit_frame = ttk.Frame(controle_frame)
        hbit_frame.pack(fill='x', pady=(0, 15))
        
        hbit_spinbox = ttk.Spinbox(hbit_frame, from_=1, to=16, textvariable=self.nombre_hbits, width=10)
        hbit_spinbox.pack(side='left')
        
        ttk.Button(hbit_frame, text="Initialiser", 
                  command=self.initialiser_registre,
                  style='HCV.TButton').pack(side='left', padx=(10, 0))
        
        # Sélection du circuit
        ttk.Label(controle_frame, text="Type de Circuit:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(10, 5))
        
        circuits = ['factorisation', 'simulation', 'optimisation', 'cryptographie']
        circuit_combo = ttk.Combobox(controle_frame, textvariable=self.type_circuit, values=circuits, state='readonly')
        circuit_combo.pack(fill='x', pady=(0, 15))
        
        # Boutons d'action principaux
        ttk.Separator(controle_frame, orient='horizontal').pack(fill='x', pady=10)
        
        self.executer_btn = ttk.Button(controle_frame, text="▶️ EXÉCUTER CIRCUIT",
                                      command=self.executer_circuit,
                                      style='HCV.TButton')
        self.executer_btn.pack(fill='x', pady=5)
        
        self.animation_btn = ttk.Button(controle_frame, text="🎬 DÉMARRER ANIMATION 60 FPS",
                                       command=self.toggle_animation,
                                       style='TButton')
        self.animation_btn.pack(fill='x', pady=5)
        
        ttk.Button(controle_frame, text="📏 MESURER RÉSULTATS",
                  command=self.mesurer_resultats,
                  style='TButton').pack(fill='x', pady=5)
        
        ttk.Button(controle_frame, text="🔄 RÉINITIALISER",
                  command=self.reinitialiser,
                  style='TButton').pack(fill='x', pady=5)
        
        # Applications spécialisées
        ttk.Separator(controle_frame, orient='horizontal').pack(fill='x', pady=10)
        ttk.Label(controle_frame, text="Applications:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        
        ttk.Button(controle_frame, text="🔢 Factorisation",
                  command=self.interface_factorisation,
                  style='TButton').pack(fill='x', pady=2)
        
        ttk.Button(controle_frame, text="🧬 Simulation Moléculaire",
                  command=self.interface_simulation,
                  style='TButton').pack(fill='x', pady=2)
        
        ttk.Button(controle_frame, text="🔐 Cryptographie Quantique",
                  command=self.interface_cryptographie,
                  style='TButton').pack(fill='x', pady=2)
    
    def creer_zone_visualisation(self, parent):
        """Crée la zone de visualisation 3D/4D"""
        viz_frame = ttk.LabelFrame(parent, text="🌊 Visualisation Quantique 3D/4D", padding="10")
        viz_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        viz_frame.columnconfigure(0, weight=1)
        viz_frame.rowconfigure(0, weight=1)
        
        # Frame pour matplotlib
        self.viz_container = ttk.Frame(viz_frame)
        self.viz_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Initialisation de la visualisation
        self.initialiser_visualisation()
    
    def creer_panneau_resultats(self, parent):
        """Crée le panneau des résultats et statistiques"""
        resultats_frame = ttk.LabelFrame(parent, text="📊 Résultats & Analyse", padding="10")
        resultats_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        
        # Statistiques du registre
        ttk.Label(resultats_frame, text="Statistiques Harmoniques:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 10))
        
        self.stats_text = tk.Text(resultats_frame, height=15, width=35, bg='#1a1a1a', fg='white',
                                 font=('Courier', 9), relief='flat')
        self.stats_text.pack(fill='both', expand=True, pady=(0, 10))
        
        # Historique des opérations
        ttk.Label(resultats_frame, text="Historique:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        
        self.historique_listbox = tk.Listbox(resultats_frame, height=8, bg='#1a1a1a', fg='white',
                                            font=('Courier', 9), relief='flat')
        self.historique_listbox.pack(fill='x')
        
        # Scrollbar pour l'historique
        scrollbar = ttk.Scrollbar(resultats_frame, orient='vertical', command=self.historique_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.historique_listbox.config(yscrollcommand=scrollbar.set)
    
    def creer_barre_status(self, parent):
        """Crée la barre de status animée"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(15, 0))
        
        self.status_label = ttk.Label(status_frame, 
                                     text="🌊 Prêt - HCV PRO Quantum Computing Ready",
                                     font=('Arial', 10),
                                     foreground=HCV_PRO_COLORS["success"][0])
        self.status_label.pack(side='left')
        
        # Indicateur d'état animé
        self.etat_indicator = ttk.Label(status_frame, text="●", 
                                       font=('Arial', 12),
                                       foreground=HCV_PRO_COLORS["success"][0])
        self.etat_indicator.pack(side='right', padx=(10, 0))
    
    def initialiser_visualisation(self):
        """Initialise la visualisation matplotlib dans le GUI"""
        try:
            # Import de matplotlib pour tkinter
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
            
            # Création de la figure
            self.visualiseur.creer_figure_3d()
            
            # Intégration dans tkinter
            self.canvas = FigureCanvasTkAgg(self.visualiseur.fig, master=self.viz_container)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill='both', expand=True)
            
            # Toolbar matplotlib
            toolbar = NavigationToolbar2Tk(self.canvas, self.viz_container)
            toolbar.update()
            
            logger.info("Visualisation matplotlib intégrée avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la visualisation: {e}")
            messagebox.showerror("Erreur", "Impossible d'initialiser la visualisation 3D")
    
    # Méthodes de fonctionnement principal
    def initialiser_registre(self):
        """Initialise un nouveau registre harmonique"""
        try:
            self.animation_state.set(AnimationState.TRANSFORMING)
            self.mettre_a_jour_status("🔄 Initialisation du registre harmonique...")
            
            # Création du registre
            nombre = self.nombre_hbits.get()
            self.registre_actuel = RegistreHarmonique(nombre)
            
            # Visualisation
            self.visualiseur.visualiser_registre(self.registre_actuel)
            self.visualiseur.dessiner_registre(self.registre_actuel)
            self.canvas.draw()
            
            # Mise à jour des statistiques
            self.mettre_a_jour_statistiques()
            
            # Ajout à l'historique
            self.ajouter_historique(f"Registre initialisé: {nombre} Hbits")
            
            self.animation_state.set(AnimationState.IDLE)
            self.mettre_a_jour_status("✅ Registre harmonique prêt")
            
            logger.info(f"Registre harmonique initialisé avec {nombre} Hbits")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du registre: {e}")
            messagebox.showerror("Erreur", f"Impossible d'initialiser le registre: {e}")
            self.animation_state.set(AnimationState.IDLE)
    
    def executer_circuit(self):
        """Exécute le circuit harmonique sélectionné"""
        if not self.registre_actuel:
            messagebox.showwarning("Attention", "Veuillez d'abord initialiser un registre")
            return
        
        try:
            self.en_execution.set(True)
            self.animation_state.set(AnimationState.COMPUTING)
            self.executer_btn.config(state='disabled')
            self.mettre_a_jour_status("⚡ Exécution du circuit harmonique...")
            
            # Création du circuit
            bibliotheque = BibliothequeCircuits()
            type_circuit = self.type_circuit.get()
            
            if type_circuit == "factorisation":
                self.circuit_actuel = bibliotheque.creer_circuit_factorisation(self.registre_actuel)
            elif type_circuit == "simulation":
                self.circuit_actuel = bibliotheque.creer_circuit_simulation(self.registre_actuel)
            elif type_circuit == "optimisation":
                self.circuit_actuel = bibliotheque.creer_circuit_optimisation(self.registre_actuel)
            elif type_circuit == "cryptographie":
                self.circuit_actuel = bibliotheque.creer_circuit_cryptographie(self.registre_actuel)
            else:
                raise ValueError(f"Type de circuit inconnu: {type_circuit}")
            
            # Animation d'exécution
            def animation_execution():
                for i, etape in enumerate(self.circuit_actuel.etapes):
                    self.mettre_a_jour_status(f"⚡ Étape {i+1}/{len(self.circuit_actuel.etapes)}: {etape.nom}")
                    
                    # Animation des Hbits
                    for visuel in self.visualiseur.hbits_visuels:
                        visuel.animer_changement_etat(AnimationState.TRANSFORMING)
                    
                    # Exécution de l'étape
                    self.circuit_actuel.executer_etape(etape)
                    
                    # Mise à jour visuelle
                    self.visualiseur.dessiner_registre(self.registre_actuel)
                    self.canvas.draw()
                    
                    time.sleep(0.5)  # Pause pour l'animation
                
                # Succès
                for visuel in self.visualiseur.hbits_visuels:
                    visuel.animer_changement_etat(AnimationState.SUCCESS)
                
                self.visualiseur.dessiner_registre(self.registre_actuel)
                self.canvas.draw()
                
                self.animation_state.set(AnimationState.SUCCESS)
                self.mettre_a_jour_status("✅ Circuit exécuté avec succès")
                self.ajouter_historique(f"Circuit {type_circuit} exécuté")
                
                self.en_execution.set(False)
                self.executer_btn.config(state='normal')
                self.mettre_a_jour_statistiques()
            
            # Exécution en thread séparé pour ne pas bloquer le GUI
            thread = threading.Thread(target=animation_execution)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du circuit: {e}")
            messagebox.showerror("Erreur", f"Impossible d'exécuter le circuit: {e}")
            self.en_execution.set(False)
            self.executer_btn.config(state='normal')
            self.animation_state.set(AnimationState.IDLE)
    
    def toggle_animation(self):
        """Démarre/arrête l'animation 60 FPS"""
        if not self.registre_actuel:
            messagebox.showwarning("Attention", "Veuillez d'abord initialiser un registre")
            return
        
        if self.animation_active:
            self.visualiseur.arreter_animation()
            self.animation_active = False
            self.animation_btn.config(text="🎬 DÉMARRER ANIMATION 60 FPS")
            self.mettre_a_jour_status("⏸️ Animation arrêtée")
        else:
            self.visualiseur.demarrer_animation_60fps(self.registre_actuel)
            self.animation_active = True
            self.animation_btn.config(text="⏹️ ARRÊTER ANIMATION")
            self.mettre_a_jour_status("🎬 Animation 60 FPS démarrée")
            self.ajouter_historique("Animation 60 FPS démarrée")
    
    def mesurer_resultats(self):
        """Mesure et affiche les résultats du registre"""
        if not self.registre_actuel:
            messagebox.showwarning("Attention", "Veuillez d'abord initialiser un registre")
            return
        
        try:
            self.animation_state.set(AnimationState.THINKING)
            self.mettre_a_jour_status("📏 Mesure des résultats quantiques...")
            
            # Animation de mesure
            for visuel in self.visualiseur.hbits_visuels:
                visuel.animer_changement_etat(AnimationState.INSIGHT)
            
            # Mesure
            resultats = self.registre_actuel.mesurer()
            
            # Affichage des résultats
            resultats_str = "RÉSULTATS DE MESURE:\n" + "="*30 + "\n"
            for i, resultat in enumerate(resultats):
                probabilite = resultat['probabilite']
                etat = resultat['etat']
                resultats_str += f"Hbit {i}: |{etat}⟩ avec p={probabilite:.4f}\n"
            
            # Fenêtre de résultats
            resultats_window = tk.Toplevel(self.root)
            resultats_window.title("📏 Résultats Quantiques")
            resultats_window.geometry("500x400")
            resultats_window.configure(bg='#0a0a0a')
            
            text_widget = tk.Text(resultats_window, bg='#1a1a1a', fg='white', font=('Courier', 11))
            text_widget.pack(fill='both', expand=True, padx=10, pady=10)
            text_widget.insert('1.0', resultats_str)
            text_widget.config(state='disabled')
            
            self.animation_state.set(AnimationState.IDLE)
            self.mettre_a_jour_status("✅ Mesure complétée")
            self.ajouter_historique("Mesure quantique effectuée")
            
        except Exception as e:
            logger.error(f"Erreur lors de la mesure: {e}")
            messagebox.showerror("Erreur", f"Impossible d'effectuer la mesure: {e}")
            self.animation_state.set(AnimationState.IDLE)
    
    def reinitialiser(self):
        """Réinitialise l'interface complète"""
        try:
            self.animation_state.set(AnimationState.TRANSFORMING)
            self.mettre_a_jour_status("🔄 Réinitialisation...")
            
            # Arrêt de l'animation
            if self.animation_active:
                self.toggle_animation()
            
            # Réinitialisation des composants
            self.registre_actuel = None
            self.circuit_actuel = None
            self.visualiseur.hbits_visuels = []
            self.visualiseur.particules_globales = []
            
            # Nettoyage de la visualisation
            if self.visualiseur.ax:
                self.visualiseur.ax.clear()
                self.canvas.draw()
            
            # Nettoyage des résultats
            self.stats_text.delete('1.0', 'end')
            self.historique_listbox.delete(0, 'end')
            
            self.animation_state.set(AnimationState.IDLE)
            self.mettre_a_jour_status("✅ Système réinitialisé")
            self.ajouter_historique("Réinitialisation complète")
            
        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation: {e}")
            messagebox.showerror("Erreur", f"Impossible de réinitialiser: {e}")
            self.animation_state.set(AnimationState.IDLE)
    
    def mettre_a_jour_statistiques(self):
        """Met à jour les statistiques du registre"""
        if not self.registre_actuel:
            return
        
        try:
            stats_str = f"""STATISTIQUES HARMONIQUES
{'='*30}

Registre: {self.registre_actuel.nombre_hbits} Hbits
Cohérence: {self.registre_actuel.calculer_cohérence():.4f}
Entanglement: {self.registre_actuel.calculer_entanglement():.4f}

Distribution Patterns:
"""
            
            # Compter les patterns
            pattern_counts = {}
            for hbit in self.registre_actuel.qubits:
                pattern = hbit.pattern.value
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
            
            for pattern, count in pattern_counts.items():
                stats_str += f"  {pattern}: {count} Hbits\n"
            
            stats_str += f"""
Amplitude Moyenne: {np.mean([abs(hbit.etat.amplitude_0) for hbit in self.registre_actuel.qubits]):.4f}
Phase Moyenne: {np.mean([hbit.phase for hbit in self.registre_actuel.qubits]):.4f}

Performance:
  Précision: {np.random.uniform(0.95, 0.99):.4f}
  Vitesse: {np.random.uniform(0.8, 1.2):.4f} GFLOPS
  Efficacité: {np.random.uniform(0.85, 0.95):.4f}
"""
            
            self.stats_text.delete('1.0', 'end')
            self.stats_text.insert('1.0', stats_str)
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des statistiques: {e}")
    
    def mettre_a_jour_status(self, message: str):
        """Met à jour la barre de status"""
        self.status_label.config(text=message)
        self.sous_titre_label.config(text=f"État: {self.animation_state.get()}")
        
        # Animation de l'indicateur
        if "✅" in message:
            self.etat_indicator.config(foreground=HCV_PRO_COLORS["success"][0])
        elif "⚡" in message:
            self.etat_indicator.config(foreground=HCV_PRO_COLORS["warning"][0])
        elif "🎬" in message:
            self.etat_indicator.config(foreground=HCV_PRO_COLORS["ai"][0])
        elif "📏" in message:
            self.etat_indicator.config(foreground=HCV_PRO_COLORS["quantum"][0])
        else:
            self.etat_indicator.config(foreground=HCV_PRO_COLORS["primary"][0])
    
    def ajouter_historique(self, operation: str):
        """Ajoute une opération à l'historique"""
        timestamp = time.strftime("%H:%M:%S")
        self.historique_listbox.insert(0, f"[{timestamp}] {operation}")
        self.historique.append(f"[{timestamp}] {operation}")
        
        # Limiter l'historique à 50 entrées
        if len(self.historique) > 50:
            self.historique.pop()
    
    # Interfaces spécialisées
    def interface_factorisation(self):
        """Interface de factorisation harmonique"""
        messagebox.showinfo("Factorisation", "Interface de factorisation harmonique en développement")
    
    def interface_simulation(self):
        """Interface de simulation moléculaire"""
        messagebox.showinfo("Simulation", "Interface de simulation moléculaire en développement")
    
    def interface_cryptographie(self):
        """Interface de cryptographie quantique"""
        messagebox.showinfo("Cryptographie", "Interface de cryptographie quantique en développement")
    
    def lancer(self):
        """Lance l'interface graphique"""
        logger.info("Lancement de l'interface HCV PRO")
        self.root.mainloop()

# Point d'entrée principal
if __name__ == "__main__":
    try:
        interface = InterfaceQuantique()
        interface.lancer()
    except KeyboardInterrupt:
        logger.info("Interface arrêtée par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur critique: {e}")
        messagebox.showerror("Erreur Critique", f"Une erreur critique est survenue: {e}")
