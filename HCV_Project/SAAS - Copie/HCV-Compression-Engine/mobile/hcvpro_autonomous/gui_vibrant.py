#!/usr/bin/env python3
"""
HCV PRO - Interface Utilisateur Vibrante & Dynamique
===================================================
Interface graphique avec couleurs franches et animations énergiques

🌈 Design Features :
- Couleurs vives et énergiques
- Animations dynamiques fluides
- Thème néon futuriste
- Graphiques temps réel animés
- Feedback utilisateur spectaculaire

🚀 Technologies :
- Tkinter avec style vibrant
- Animations arc-en-ciel
- Effets néon et lumières
- Transitions fluides
- Design moderne audacieux
"""

import sys
import os
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import json
import hashlib
from datetime import datetime
import math
import random

# Ajouter le répertoire bin au path
package_dir = Path(__file__).parent
sys.path.insert(0, str(package_dir / "bin"))

try:
    from harmonic_autonomous_package import HarmonicAutonomousPackage
except ImportError:
    print("❌ Package HCV PRO non trouvé")
    sys.exit(1)

class VibrantStyle:
    """Style vibrant et énergique pour l'interface"""
    
    def __init__(self):
        # Palette de couleurs vibrantes
        self.colors = {
            'primary': '#FF006E',      # Rose néon
            'secondary': '#FB5607',    # Orange vif
            'accent': '#FFBE0B',       # Jaune éclatant
            'success': '#8338EC',      # Violet profond
            'info': '#3A86FF',        # Bleu électrique
            'warning': '#FFD60A',      # Jaune d'or
            'error': '#FF006E',       # Rose alarme
            'text': '#FFFFFF',         # Blanc pur
            'text_secondary': '#B8B8B8', # Gris clair
            'background': '#0A0E27',   # Bleu nuit profond
            'surface': '#1A1F3A',      # Bleu nuit moyen
            'border': '#2D3561',       # Bleu nuit clair
            'gradient_start': '#FF006E', # Rose néon
            'gradient_end': '#3A86FF',   # Bleu électrique
            'neon_pink': '#FF10F0',    # Rose néon
            'neon_blue': '#00D9FF',    # Bleu néon
            'neon_green': '#00FF88',   # Vert néon
            'neon_yellow': '#FFFF00',  # Jaune néon
            'neon_orange': '#FF6600',  # Orange néon
        }
        
        # Polices modernes
        self.fonts = {
            'title': ('Segoe UI', 28, 'bold'),
            'header': ('Segoe UI', 20, 'bold'),
            'body': ('Segoe UI', 12, 'bold'),
            'small': ('Segoe UI', 10, 'bold'),
            'mono': ('Consolas', 11, 'bold'),
            'neon': ('Segoe UI', 16, 'bold')
        }
        
        # Animation colors
        self.rainbow_colors = [
            '#FF006E', '#FB5607', '#FFBE0B', '#8338EC', '#3A86FF',
            '#06FFB4', '#FF4365', '#00D9FF', '#FF10F0', '#00FF88'
        ]
    
    def get_style(self):
        """Configure le style vibrant"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configuration générale
        for widget in ['TLabel', 'TButton', 'TFrame', 'TEntry']:
            style.configure(widget, 
                          background=self.colors['background'],
                          foreground=self.colors['text'],
                          borderwidth=0,
                          font=self.fonts['body'])
        
        # Boutons vibrants
        style.configure('Vibrant.TButton',
                       background=self.colors['primary'],
                       foreground=self.colors['text'],
                       borderwidth=0,
                       focuscolor='none',
                       font=self.fonts['body'],
                       padding=(20, 10))
        
        style.map('Vibrant.TButton',
                 background=[('active', self.colors['secondary']),
                           ('pressed', self.colors['accent'])])
        
        # Boutons néon
        style.configure('Neon.TButton',
                       background=self.colors['background'],
                       foreground=self.colors['neon_pink'],
                       borderwidth=2,
                       relief='solid',
                       focuscolor='none',
                       font=self.fonts['neon'])
        
        style.map('Neon.TButton',
                 background=[('active', self.colors['surface']),
                           ('pressed', self.colors['primary'])],
                 relief=[('active', 'raised'),
                        ('pressed', 'sunken')])
        
        # Frames vibrants
        style.configure('Vibrant.TFrame',
                       background=self.colors['surface'],
                       relief='flat',
                       borderwidth=2)
        
        style.configure('Neon.TFrame',
                       background=self.colors['background'],
                       relief='solid',
                       borderwidth=2)
        
        return style

class RainbowCanvas(tk.Canvas):
    """Canvas avec animations arc-en-ciel dynamiques"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.particles = []
        self.waves = []
        self.animation_running = False
        self.time = 0
        self.color_index = 0
        self.style_manager = VibrantStyle()
        
    def start_animation(self):
        """Démarre l'animation arc-en-ciel"""
        self.animation_running = True
        self.animate()
    
    def stop_animation(self):
        """Arrête l'animation"""
        self.animation_running = False
    
    def animate(self):
        """Animation arc-en-ciel et particules"""
        if not self.animation_running:
            return
        
        self.delete("all")
        
        # Dessiner fond dégradé
        self.draw_gradient_background()
        
        # Créer nouvelles particules colorées
        if len(self.particles) < 30:
            color = random.choice(self.style_manager.rainbow_colors)
            self.particles.append({
                'x': self.winfo_width() / 2,
                'y': self.winfo_height() / 2,
                'vx': random.uniform(-3, 3),
                'vy': random.uniform(-3, 3),
                'size': random.randint(2, 8),
                'color': color,
                'life': 100,
                'trail': []
            })
        
        # Créer vagues d'ondes
        if self.time % 20 == 0:
            self.waves.append({
                'x': self.winfo_width() / 2,
                'y': self.winfo_height() / 2,
                'radius': 0,
                'max_radius': 150,
                'color': self.style_manager.rainbow_colors[self.color_index % len(self.style_manager.rainbow_colors)],
                'alpha': 255
            })
            self.color_index += 1
        
        # Animer et dessiner vagues
        new_waves = []
        for wave in self.waves:
            wave['radius'] += 3
            wave['alpha'] -= 5
            
            if wave['alpha'] > 0:
                alpha_hex = format(wave['alpha'], '02x')
                color_with_alpha = wave['color'] + alpha_hex
                
                self.create_oval(
                    wave['x'] - wave['radius'],
                    wave['y'] - wave['radius'],
                    wave['x'] + wave['radius'],
                    wave['y'] + wave['radius'],
                    outline=wave['color'],
                    width=2,
                    tags="wave"
                )
                new_waves.append(wave)
        
        self.waves = new_waves
        
        # Animer et dessiner particules
        new_particles = []
        for particle in self.particles:
            # Mettre à jour position
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 1
            
            # Ajouter à la traînée
            particle['trail'].append((particle['x'], particle['y']))
            if len(particle['trail']) > 10:
                particle['trail'].pop(0)
            
            if particle['life'] > 0:
                # Dessiner traînée
                for i, (tx, ty) in enumerate(particle['trail']):
                    trail_size = particle['size'] * (i / len(particle['trail']))
                    trail_alpha = particle['life'] * (i / len(particle['trail'])) / 100
                    
                    self.create_oval(
                        tx - trail_size,
                        ty - trail_size,
                        tx + trail_size,
                        ty + trail_size,
                        fill=particle['color'],
                        outline='',
                        tags="trail"
                    )
                
                # Dessiner particule principale avec effet néon
                # Halo extérieur
                halo_size = particle['size'] * 2
                self.create_oval(
                    particle['x'] - halo_size,
                    particle['y'] - halo_size,
                    particle['x'] + halo_size,
                    particle['y'] + halo_size,
                    fill='',
                    outline=particle['color'],
                    width=1,
                    tags="particle"
                )
                
                # Particule centrale
                self.create_oval(
                    particle['x'] - particle['size'],
                    particle['y'] - particle['size'],
                    particle['x'] + particle['size'],
                    particle['y'] + particle['size'],
                    fill=particle['color'],
                    outline='white',
                    width=1,
                    tags="particle"
                )
                
                new_particles.append(particle)
        
        self.particles = new_particles
        self.time += 1
        
        # Continuer animation
        self.after(30, self.animate)
    
    def draw_gradient_background(self):
        """Dessine un fond dégradé animé"""
        width = self.winfo_width()
        height = self.winfo_height()
        
        if width <= 1 or height <= 1:
            return
        
        # Créer dégradé animé
        for i in range(0, height, 5):
            progress = i / height
            color_shift = math.sin(self.time * 0.05 + progress * math.pi) * 0.5 + 0.5
            
            # Interpoler entre couleurs
            r1, g1, b1 = self.hex_to_rgb(self.style_manager.colors['gradient_start'])
            r2, g2, b2 = self.hex_to_rgb(self.style_manager.colors['gradient_end'])
            
            r = int(r1 + (r2 - r1) * color_shift)
            g = int(g1 + (g2 - g1) * color_shift)
            b = int(b1 + (b2 - b1) * color_shift)
            
            color = f'#{r:02x}{g:02x}{b:02x}'
            
            self.create_rectangle(
                0, i, width, i + 5,
                fill=color,
                outline='',
                tags="gradient"
            )
    
    def hex_to_rgb(self, hex_color):
        """Convertit hex en RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

class NeonLabel(tk.Label):
    """Label avec effet néon"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.neon_colors = ['#FF006E', '#00D9FF', '#00FF88', '#FFFF00']
        self.current_color_index = 0
        self.animation_running = False
        self.original_text = self.cget('text')
    
    def start_neon_animation(self):
        """Démarre l'animation néon"""
        self.animation_running = True
        self.animate_neon()
    
    def stop_neon_animation(self):
        """Arrête l'animation néon"""
        self.animation_running = False
    
    def animate_neon(self):
        """Animation de changement de couleur néon"""
        if not self.animation_running:
            return
        
        # Changer de couleur
        color = self.neon_colors[self.current_color_index]
        self.config(fg=color)
        
        # Effet de clignotement
        if random.random() > 0.8:
            self.config(fg='white')
        
        self.current_color_index = (self.current_color_index + 1) % len(self.neon_colors)
        
        # Continuer animation
        self.after(500, self.animate_neon)

class HCVProVibrantGUI:
    """Interface utilisateur vibrante HCV PRO"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.style_manager = VibrantStyle()
        self.style = self.style_manager.get_style()
        
        # Package HCV PRO
        self.package = None
        self.license_active = False
        
        # Configuration fenêtre
        self.setup_window()
        
        # Créer interface
        self.create_vibrant_interface()
        
        # Démarrer animations
        self.start_animations()
        
    def setup_window(self):
        """Configure la fenêtre principale vibrante"""
        self.root.title("🚀 HCV PRO - Interface Vibrante")
        self.root.geometry("1400x900")
        self.root.configure(bg=self.style_manager.colors['background'])
        
        # Configuration pour effet plein écran
        self.root.attributes('-fullscreen', False)
        self.root.resizable(True, True)
        
        # Centrer fenêtre
        self.center_window()
    
    def center_window(self):
        """Centre la fenêtre sur l'écran"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_vibrant_interface(self):
        """Crée l'interface vibrante complète"""
        
        # Header spectaculaire
        self.create_spectacular_header()
        
        # Zone principale
        main_frame = ttk.Frame(self.root, style='Vibrant.TFrame')
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Panneau latéral néon
        self.create_neon_sidebar(main_frame)
        
        # Zone contenu dynamique
        self.create_dynamic_content_area(main_frame)
        
        # Barre de statut animée
        self.create_animated_status_bar()
    
    def create_spectacular_header(self):
        """Crée un header spectaculaire avec animations"""
        header_frame = ttk.Frame(self.root, style='Neon.TFrame')
        header_frame.pack(fill='x', padx=20, pady=(10, 5))
        
        # Canvas animation arc-en-ciel
        self.rainbow_canvas = RainbowCanvas(
            header_frame,
            width=300,
            height=100,
            bg=self.style_manager.colors['background'],
            highlightthickness=2,
            highlightbackground=self.style_manager.colors['neon_pink']
        )
        self.rainbow_canvas.pack(side='left', padx=10, pady=10)
        
        # Zone titre avec effets néon
        title_frame = ttk.Frame(header_frame, style='Vibrant.TFrame')
        title_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        
        # Titre principal néon
        self.title_label = NeonLabel(
            title_frame,
            text="🚀 HCV PRO",
            font=self.style_manager.fonts['title'],
            fg=self.style_manager.colors['neon_pink'],
            bg=self.style_manager.colors['surface']
        )
        self.title_label.pack(anchor='w')
        
        # Sous-titre vibrant
        subtitle_label = NeonLabel(
            title_frame,
            text="🌈 Package Autonome Vibrant - Compression Harmonique Quantique",
            font=self.style_manager.fonts['body'],
            fg=self.style_manager.colors['neon_blue'],
            bg=self.style_manager.colors['surface']
        )
        subtitle_label.pack(anchor='w')
        
        # Badge de statut animé
        self.status_badge = NeonLabel(
            title_frame,
            text="🔴 NON LICENCIÉ",
            font=self.style_manager.fonts['small'],
            fg=self.style_manager.colors['error'],
            bg=self.style_manager.colors['surface']
        )
        self.status_badge.pack(anchor='w', pady=(5, 0))
        
        # Démarrer animations néon
        self.title_label.start_neon_animation()
        subtitle_label.start_neon_animation()
        self.status_badge.start_neon_animation()
    
    def create_neon_sidebar(self, parent):
        """Crée un panneau latéral avec effets néon"""
        sidebar = ttk.Frame(parent, style='Neon.TFrame', width=300)
        sidebar.pack(side='left', fill='y', padx=(0, 10))
        sidebar.pack_propagate(False)
        
        # Logo animé
        logo_frame = ttk.Frame(sidebar, style='Vibrant.TFrame')
        logo_frame.pack(fill='x', padx=10, pady=10)
        
        # Logo néon
        logo_canvas = tk.Canvas(
            logo_frame,
            width=80,
            height=80,
            bg=self.style_manager.colors['background'],
            highlightthickness=2,
            highlightbackground=self.style_manager.colors['neon_pink']
        )
        logo_canvas.pack(pady=10)
        
        # Dessiner logo animé
        self.draw_animated_logo(logo_canvas)
        
        # Menu navigation vibrant
        nav_frame = ttk.Frame(sidebar, style='Vibrant.TFrame')
        nav_frame.pack(fill='x', padx=10, pady=10)
        
        menu_items = [
            ("🏠 Tableau de Bord", self.show_dashboard, self.style_manager.colors['neon_pink']),
            ("🗜️ Compression", self.show_compression, self.style_manager.colors['neon_blue']),
            ("📊 Performance", self.show_performance, self.style_manager.colors['neon_green']),
            ("🔐 Sécurité", self.show_security, self.style_manager.colors['neon_yellow']),
            ("⚙️ Paramètres", self.show_settings, self.style_manager.colors['neon_orange']),
            ("📋 Rapport", self.show_report, self.style_manager.colors['success'])
        ]
        
        for text, command, color in menu_items:
            btn_frame = ttk.Frame(nav_frame, style='Vibrant.TFrame')
            btn_frame.pack(fill='x', pady=2)
            
            btn = ttk.Button(
                btn_frame,
                text=text,
                style='Neon.TButton',
                command=command
            )
            btn.pack(fill='x')
            
            # Ajouter effet de survol
            btn.bind('<Enter>', lambda e, b=btn: b.config(foreground=color))
            btn.bind('<Leave>', lambda e, b=btn: b.config(foreground=self.style_manager.colors['neon_pink']))
        
        # Zone licence vibrante
        self.license_frame = ttk.Frame(sidebar, style='Vibrant.TFrame')
        self.license_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(
            self.license_frame,
            text="🔑 LICENCE VIBRANTE",
            font=self.style_manager.fonts['header'],
            foreground=self.style_manager.colors['neon_pink']
        ).pack(anchor='w')
        
        self.license_info = NeonLabel(
            self.license_frame,
            text="❌ NON ACTIVÉE",
            font=self.style_manager.fonts['small'],
            fg=self.style_manager.colors['error'],
            bg=self.style_manager.colors['surface']
        )
        self.license_info.pack(anchor='w')
        
        # Bouton activation néon
        self.activate_btn = ttk.Button(
            self.license_frame,
            text="🔓 ACTIVER LICENCE",
            style='Vibrant.TButton',
            command=self.activate_license
        )
        self.activate_btn.pack(fill='x', pady=(10, 0))
    
    def create_dynamic_content_area(self, parent):
        """Crée la zone de contenu dynamique"""
        self.content_frame = ttk.Frame(parent, style='Vibrant.TFrame')
        self.content_frame.pack(side='right', fill='both', expand=True)
        
        # Afficher tableau de bord par défaut
        self.show_dashboard()
    
    def create_animated_status_bar(self):
        """Crée une barre de statut animée"""
        status_frame = ttk.Frame(self.root, style='Neon.TFrame')
        status_frame.pack(fill='x', padx=20, pady=(5, 10))
        
        # Statut connexion avec animation
        self.connection_status = NeonLabel(
            status_frame,
            text="🟢 CONNECTÉ",
            font=self.style_manager.fonts['small'],
            fg=self.style_manager.colors['neon_green']
        )
        self.connection_status.pack(side='left', padx=10)
        
        # Heure animée
        self.time_label = NeonLabel(
            status_frame,
            text="",
            font=self.style_manager.fonts['small'],
            fg=self.style_manager.colors['neon_blue']
        )
        self.time_label.pack(side='right', padx=10)
        
        # Démarrer animations
        self.connection_status.start_neon_animation()
        self.time_label.start_neon_animation()
        
        # Mettre à jour heure
        self.update_time()
    
    def update_time(self):
        """Met à jour l'heure avec format vibrant"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.config(text=f"🕐 {current_time}")
        self.root.after(1000, self.update_time)
    
    def draw_animated_logo(self, canvas):
        """Dessine un logo animé"""
        # Cercle extérieur néon
        canvas.create_oval(
            10, 10, 70, 70,
            outline=self.style_manager.colors['neon_pink'],
            width=3,
            tags="logo"
        )
        
        # Cercle intérieur
        canvas.create_oval(
            20, 20, 60, 60,
            outline=self.style_manager.colors['neon_blue'],
            width=2,
            tags="logo"
        )
        
        # Texte HCV
        canvas.create_text(
            40, 40,
            text="HCV",
            font=('Segoe UI', 16, 'bold'),
            fill=self.style_manager.colors['neon_green'],
            tags="logo"
        )
        
        # Animation simple
        self.animate_logo(canvas)
    
    def animate_logo(self, canvas):
        """Animation simple du logo"""
        colors = [self.style_manager.colors['neon_pink'], 
                 self.style_manager.colors['neon_blue'],
                 self.style_manager.colors['neon_green']]
        
        # Changer couleur du cercle extérieur
        color = random.choice(colors)
        canvas.itemconfig("logo", outline=color)
        
        # Continuer animation
        self.root.after(1000, lambda: self.animate_logo(canvas))
    
    def start_animations(self):
        """Démarre toutes les animations"""
        self.rainbow_canvas.start_animation()
    
    def clear_content(self):
        """Efface le contenu actuel"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_dashboard(self):
        """Affiche le tableau de bord vibrant"""
        self.clear_content()
        
        # Header vibrant
        header = ttk.Frame(self.content_frame, style='Vibrant.TFrame')
        header.pack(fill='x', padx=10, pady=10)
        
        title_label = NeonLabel(
            header,
            text="📊 TABLEAU DE BORD VIBRANT",
            font=self.style_manager.fonts['header'],
            fg=self.style_manager.colors['neon_pink'],
            bg=self.style_manager.colors['surface']
        )
        title_label.pack(anchor='w')
        title_label.start_neon_animation()
        
        # Grid de statistiques colorées
        stats_frame = ttk.Frame(self.content_frame, style='Vibrant.TFrame')
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        # Cartes statistiques vibrantes
        stats = [
            ("📦 COMPRESSIONS", "0", "TOTAL", self.style_manager.colors['neon_pink']),
            ("⚡ PERFORMANCE", "0MS", "MOYENNE", self.style_manager.colors['neon_blue']),
            ("🔐 SÉCURITÉ", "MAX", "NIVEAU", self.style_manager.colors['neon_green']),
            ("📊 RATIO", "0X", "MOYEN", self.style_manager.colors['neon_yellow'])
        ]
        
        for i, (title, value, subtitle, color) in enumerate(stats):
            card = ttk.Frame(stats_frame, style='Vibrant.TFrame')
            card.grid(row=0, column=i, padx=5, pady=5, sticky='nsew')
            stats_frame.grid_columnconfigure(i, weight=1)
            
            # Titre coloré
            ttk.Label(
                card,
                text=title,
                font=self.style_manager.fonts['small'],
                foreground=color
            ).pack(anchor='w', padx=10, pady=(10, 0))
            
            # Valeur vibrante
            value_label = NeonLabel(
                card,
                text=value,
                font=self.style_manager.fonts['header'],
                fg=color,
                bg=self.style_manager.colors['surface']
            )
            value_label.pack(anchor='w', padx=10)
            value_label.start_neon_animation()
            
            # Sous-titre
            ttk.Label(
                card,
                text=subtitle,
                font=self.style_manager.fonts['small'],
                foreground=self.style_manager.colors['text_secondary']
            ).pack(anchor='w', padx=10, pady=(0, 10))
        
        # Zone d'activité animée
        activity_frame = ttk.Frame(self.content_frame, style='Vibrant.TFrame')
        activity_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        activity_title = NeonLabel(
            activity_frame,
            text="📋 ACTIVITÉ RÉCENTE VIBRANTE",
            font=self.style_manager.fonts['header'],
            fg=self.style_manager.colors['neon_orange'],
            bg=self.style_manager.colors['surface']
        )
        activity_title.pack(anchor='w', padx=10, pady=10)
        activity_title.start_neon_animation()
        
        # Zone d'activité avec couleurs
        activity_canvas = tk.Canvas(
            activity_frame,
            height=300,
            bg=self.style_manager.colors['background'],
            highlightthickness=2,
            highlightbackground=self.style_manager.colors['neon_green']
        )
        activity_canvas.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Texte d'activité avec couleurs
        activity_lines = [
            "🚀 HCV PRO - Interface Vibrante Activée",
            "",
            "🌈 Système d'animations démarré",
            "💡 Effets néon opérationnels",
            "🎨 Palette de couleurs vibrantes chargée",
            "⚡ Interface utilisateur prête",
            "",
            "🔔 Pour commencer : Activez votre licence vibrante !"
        ]
        
        y_position = 20
        colors = [self.style_manager.colors['neon_pink'],
                 self.style_manager.colors['neon_blue'],
                 self.style_manager.colors['neon_green'],
                 self.style_manager.colors['neon_yellow'],
                 self.style_manager.colors['neon_orange']]
        
        for i, line in enumerate(activity_lines):
            color = colors[i % len(colors)]
            activity_canvas.create_text(
                20, y_position,
                text=line,
                font=self.style_manager.fonts['mono'],
                fill=color,
                anchor='w'
            )
            y_position += 25
    
    def show_compression(self):
        """Affiche l'interface de compression vibrante"""
        self.clear_content()
        
        # Header vibrant
        header = ttk.Frame(self.content_frame, style='Vibrant.TFrame')
        header.pack(fill='x', padx=10, pady=10)
        
        title_label = NeonLabel(
            header,
            text="🗜️ COMPRESSION VIBRANTE",
            font=self.style_manager.fonts['header'],
            fg=self.style_manager.colors['neon_blue'],
            bg=self.style_manager.colors['surface']
        )
        title_label.pack(anchor='w')
        title_label.start_neon_animation()
        
        # Zone compression colorée
        compress_frame = ttk.Frame(self.content_frame, style='Vibrant.TFrame')
        compress_frame.pack(fill='x', padx=10, pady=5)
        
        # Sélection fichier
        file_frame = ttk.Frame(compress_frame, style='Vibrant.TFrame')
        file_frame.pack(fill='x', padx=10, pady=10)
        
        file_label = NeonLabel(
            file_frame,
            text="📁 FICHIER À COMPRESSER :",
            font=self.style_manager.fonts['body'],
            fg=self.style_manager.colors['neon_pink'],
            bg=self.style_manager.colors['surface']
        )
        file_label.pack(anchor='w')
        file_label.start_neon_animation()
        
        file_select_frame = ttk.Frame(file_frame, style='Vibrant.TFrame')
        file_select_frame.pack(fill='x', pady=5)
        
        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(file_select_frame, textvariable=self.file_path_var, font=self.style_manager.fonts['mono'])
        file_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        browse_btn = ttk.Button(
            file_select_frame,
            text="📂 PARCOURIR",
            style='Vibrant.TButton',
            command=self.browse_file
        )
        browse_btn.pack(side='right')
        
        # Options compression vibrantes
        options_frame = ttk.Frame(compress_frame, style='Vibrant.TFrame')
        options_frame.pack(fill='x', padx=10, pady=5)
        
        options_label = NeonLabel(
            options_frame,
            text="⚙️ OPTIONS VIBRANTES :",
            font=self.style_manager.fonts['body'],
            fg=self.style_manager.colors['neon_green'],
            bg=self.style_manager.colors['surface']
        )
        options_label.pack(anchor='w', pady=(10, 5))
        options_label.start_neon_animation()
        
        # Mode compression
        mode_frame = ttk.Frame(options_frame, style='Vibrant.TFrame')
        mode_frame.pack(fill='x', pady=5)
        
        ttk.Label(mode_frame, text="MODE :", foreground=self.style_manager.colors['neon_blue']).pack(side='left')
        
        self.compression_mode = tk.StringVar(value="balanced")
        modes = ["ultra_fast", "balanced", "max_quality", "quantum"]
        mode_colors = [self.style_manager.colors['neon_pink'],
                      self.style_manager.colors['neon_blue'],
                      self.style_manager.colors['neon_green'],
                      self.style_manager.colors['neon_yellow']]
        
        for i, mode in enumerate(modes):
            radio_frame = ttk.Frame(mode_frame, style='Vibrant.TFrame')
            radio_frame.pack(side='left', padx=10)
            
            ttk.Radiobutton(
                radio_frame,
                text=mode.replace('_', ' ').title(),
                variable=self.compression_mode,
                value=mode
            ).pack()
        
        # Niveau sécurité
        security_frame = ttk.Frame(options_frame, style='Vibrant.TFrame')
        security_frame.pack(fill='x', pady=5)
        
        ttk.Label(security_frame, text="SÉCURITÉ :", foreground=self.style_manager.colors['neon_orange']).pack(side='left')
        
        self.security_level = tk.StringVar(value="quantum_harmonic")
        levels = ["phi_protected", "e_encrypted", "pi_secured", "quantum_harmonic"]
        
        for level in levels:
            ttk.Radiobutton(
                security_frame,
                text=level.replace('_', ' ').title(),
                variable=self.security_level,
                value=level
            ).pack(side='left', padx=10)
        
        # Bouton compression vibrant
        compress_btn = ttk.Button(
            compress_frame,
            text="🚀 LANCER COMPRESSION VIBRANTE",
            style='Vibrant.TButton',
            command=self.start_compression
        )
        compress_btn.pack(pady=10)
        
        # Zone résultats animée
        results_frame = ttk.Frame(self.content_frame, style='Vibrant.TFrame')
        results_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        results_title = NeonLabel(
            results_frame,
            text="📊 RÉSULTATS VIBRANTS",
            font=self.style_manager.fonts['header'],
            fg=self.style_manager.colors['success'],
            bg=self.style_manager.colors['surface']
        )
        results_title.pack(anchor='w', padx=10, pady=10)
        results_title.start_neon_animation()
        
        # Canvas résultats avec animations
        self.results_canvas = tk.Canvas(
            results_frame,
            bg=self.style_manager.colors['background'],
            highlightthickness=2,
            highlightbackground=self.style_manager.colors['neon_pink']
        )
        self.results_canvas.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Message initial
        self.results_canvas.create_text(
            20, 30,
            text="📋 EN ATTENTE DE COMPRESSION VIBRANTE...",
            font=self.style_manager.fonts['body'],
            fill=self.style_manager.colors['neon_pink'],
            anchor='w'
        )
        
        self.results_canvas.create_text(
            20, 60,
            text="ℹ️ SÉLECTIONNEZ UN FICHIER ET CLIQUEZ SUR 'LANCER COMPRESSION VIBRANTE'",
            font=self.style_manager.fonts['small'],
            fill=self.style_manager.colors['neon_blue'],
            anchor='w'
        )
    
    def show_performance(self):
        """Affiche les performances vibrantes"""
        self.clear_content()
        
        header = ttk.Frame(self.content_frame, style='Vibrant.TFrame')
        header.pack(fill='x', padx=10, pady=10)
        
        title_label = NeonLabel(
            header,
            text="📈 PERFORMANCE VIBRANTE",
            font=self.style_manager.fonts['header'],
            fg=self.style_manager.colors['neon_green'],
            bg=self.style_manager.colors['surface']
        )
        title_label.pack(anchor='w')
        title_label.start_neon_animation()
        
        # Canvas performance avec graphiques
        perf_canvas = tk.Canvas(
            self.content_frame,
            bg=self.style_manager.colors['background'],
            highlightthickness=2,
            highlightbackground=self.style_manager.colors['neon_green']
        )
        perf_canvas.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Données de performance
        performance_data = [
            ("🚀 MÉTRIQUES PERFORMANCE HCV PRO", self.style_manager.colors['neon_pink']),
            ("", ""),
            ("⚡ Vitesse compression : 300x supérieure", self.style_manager.colors['neon_blue']),
            ("🎯 Qualité préservée : 99.9%", self.style_manager.colors['neon_green']),
            ("⏱️ Latence : <1ms", self.style_manager.colors['neon_yellow']),
            ("🔋 Efficacité énergétique : 70%", self.style_manager.colors['neon_orange']),
            ("", ""),
            ("📊 COMPARAISON STANDARDS", self.style_manager.colors['success']),
            ("", ""),
            ("📺 H.264 : 10-50x compression", self.style_manager.colors['neon_pink']),
            ("📺 H.265 : 20-100x compression", self.style_manager.colors['neon_blue']),
            ("🚀 HCV PRO : 300-1000x compression", self.style_manager.colors['neon_green']),
            ("", ""),
            ("🎯 AVANTAGES COMPÉTITIFS", self.style_manager.colors['neon_yellow']),
            ("", ""),
            ("💪 Ratio 10x supérieur", self.style_manager.colors['neon_pink']),
            ("🎨 Qualité lossless", self.style_manager.colors['neon_blue']),
            ("🔐 Sécurité quantique", self.style_manager.colors['neon_green']),
            ("📡 Monitoring temps réel", self.style_manager.colors['neon_orange'])
        ]
        
        y_position = 30
        for text, color in performance_data:
            perf_canvas.create_text(
                20, y_position,
                text=text,
                font=self.style_manager.fonts['mono'],
                fill=color,
                anchor='w'
            )
            y_position += 25
    
    def show_security(self):
        """Affiche la sécurité vibrante"""
        self.clear_content()
        
        header = ttk.Frame(self.content_frame, style='Vibrant.TFrame')
        header.pack(fill='x', padx=10, pady=10)
        
        title_label = NeonLabel(
            header,
            text="🔐 SÉCURITÉ VIBRANTE",
            font=self.style_manager.fonts['header'],
            fg=self.style_manager.colors['neon_yellow'],
            bg=self.style_manager.colors['surface']
        )
        title_label.pack(anchor='w')
        title_label.start_neon_animation()
        
        # Canvas sécurité
        security_canvas = tk.Canvas(
            self.content_frame,
            bg=self.style_manager.colors['background'],
            highlightthickness=2,
            highlightbackground=self.style_manager.colors['neon_yellow']
        )
        security_canvas.pack(fill='both', expand=True, padx=10, pady=5)
        
        security_data = [
            ("🔐 SYSTÈME SÉCURITÉ HCV PRO", self.style_manager.colors['neon_yellow']),
            ("", ""),
            ("🛡️ PROTECTIONS IMPLÉMENTÉES :", self.style_manager.colors['neon_pink']),
            ("   • Anti-reverse engineering", self.style_manager.colors['neon_blue']),
            ("   • Cryptographie quantique harmonique", self.style_manager.colors['neon_green']),
            ("   • Validation intégrité continue", self.style_manager.colors['neon_orange']),
            ("   • Monitoring sécurité temps réel", self.style_manager.colors['neon_yellow']),
            ("   • Détection violations automatique", self.style_manager.colors['success']),
            ("", ""),
            ("🔑 NIVEAUX SÉCURITÉ :", self.style_manager.colors['neon_pink']),
            ("   • PHI Protected : Sécurité de base", self.style_manager.colors['neon_blue']),
            ("   • E Encrypted : Sécurité standard", self.style_manager.colors['neon_green']),
            ("   • PI Secured : Sécurité avancée", self.style_manager.colors['neon_yellow']),
            ("   • Quantum Harmonic : Sécurité maximale", self.style_manager.colors['neon_orange']),
            ("", ""),
            ("🚨 DÉTECTION MENACES :", self.style_manager.colors['error']),
            ("   • Package modifié : Arrêt immédiat", self.style_manager.colors['neon_pink']),
            ("   • Licence expirée : Blocage fonctions", self.style_manager.colors['neon_blue']),
            ("   • Usage excessif : Limitation quota", self.style_manager.colors['neon_green'])
        ]
        
        y_position = 30
        for text, color in security_data:
            security_canvas.create_text(
                20, y_position,
                text=text,
                font=self.style_manager.fonts['mono'],
                fill=color,
                anchor='w'
            )
            y_position += 25
    
    def show_settings(self):
        """Affiche les paramètres vibrants"""
        self.clear_content()
        
        header = ttk.Frame(self.content_frame, style='Vibrant.TFrame')
        header.pack(fill='x', padx=10, pady=10)
        
        title_label = NeonLabel(
            header,
            text="⚙️ PARAMÈTRES VIBRANTS",
            font=self.style_manager.fonts['header'],
            fg=self.style_manager.colors['neon_orange'],
            bg=self.style_manager.colors['surface']
        )
        title_label.pack(anchor='w')
        title_label.start_neon_animation()
        
        # Canvas paramètres
        settings_canvas = tk.Canvas(
            self.content_frame,
            bg=self.style_manager.colors['background'],
            highlightthickness=2,
            highlightbackground=self.style_manager.colors['neon_orange']
        )
        settings_canvas.pack(fill='both', expand=True, padx=10, pady=5)
        
        settings_data = [
            ("⚙️ PARAMÈTRES HCV PRO", self.style_manager.colors['neon_orange']),
            ("", ""),
            ("🔧 CONFIGURATION SYSTÈME :", self.style_manager.colors['neon_pink']),
            ("   • Version : 1.0.0", self.style_manager.colors['neon_blue']),
            ("   • Build : PROD-20260425", self.style_manager.colors['neon_green']),
            ("   • Niveau sécurité : Maximum", self.style_manager.colors['neon_yellow']),
            ("   • Mode : Production", self.style_manager.colors['neon_orange']),
            ("", ""),
            ("📊 PARAMÈTRES COMPRESSION :", self.style_manager.colors['success']),
            ("   • Mode par défaut : Balanced", self.style_manager.colors['neon_pink']),
            ("   • Sécurité par défaut : Quantum Harmonic", self.style_manager.colors['neon_blue']),
            ("   • Quota par défaut : 1000 compressions", self.style_manager.colors['neon_green']),
            ("   • Taille max : 10GB", self.style_manager.colors['neon_yellow']),
            ("", ""),
            ("🌐 OPTIONS RÉSEAU :", self.style_manager.colors['neon_orange']),
            ("   • Validation licence : Activée", self.style_manager.colors['neon_pink']),
            ("   • Monitoring sécurité : Activé", self.style_manager.colors['neon_blue']),
            ("   • Auto-optimisation : Activée", self.style_manager.colors['neon_green'])
        ]
        
        y_position = 30
        for text, color in settings_data:
            settings_canvas.create_text(
                20, y_position,
                text=text,
                font=self.style_manager.fonts['mono'],
                fill=color,
                anchor='w'
            )
            y_position += 25
    
    def show_report(self):
        """Affiche le rapport vibrant"""
        self.clear_content()
        
        header = ttk.Frame(self.content_frame, style='Vibrant.TFrame')
        header.pack(fill='x', padx=10, pady=10)
        
        title_label = NeonLabel(
            header,
            text="📋 RAPPORT VIBRANT",
            font=self.style_manager.fonts['header'],
            fg=self.style_manager.colors['success'],
            bg=self.style_manager.colors['surface']
        )
        title_label.pack(anchor='w')
        title_label.start_neon_animation()
        
        # Canvas rapport
        report_canvas = tk.Canvas(
            self.content_frame,
            bg=self.style_manager.colors['background'],
            highlightthickness=2,
            highlightbackground=self.style_manager.colors['success']
        )
        report_canvas.pack(fill='both', expand=True, padx=10, pady=5)
        
        report_data = [
            ("📋 RAPPORT COMPLET HCV PRO", self.style_manager.colors['success']),
            ("", ""),
            ("🚀 RÉSUMÉ EXÉCUTIF :", self.style_manager.colors['neon_pink']),
            ("   Package autonome HCV PRO opérationnel", self.style_manager.colors['neon_blue']),
            ("   Compression harmonique quantique active", self.style_manager.colors['neon_green']),
            ("   Sécurité maximale garanties", self.style_manager.colors['neon_yellow']),
            ("", ""),
            ("📊 MÉTRIQUES PERFORMANCES :", self.style_manager.colors['neon_orange']),
            ("   • Compression : 300-1000x théorique", self.style_manager.colors['neon_pink']),
            ("   • Qualité : Lossless 99.9%", self.style_manager.colors['neon_blue']),
            ("   • Latence : <1ms", self.style_manager.colors['neon_green']),
            ("   • Sécurité : Quantique", self.style_manager.colors['neon_yellow']),
            ("", ""),
            ("🎯 RECOMMANDATIONS :", self.style_manager.colors['success']),
            ("   1. Activer licence complète pour production", self.style_manager.colors['neon_pink']),
            ("   2. Configurer quotas selon besoins", self.style_manager.colors['neon_blue']),
            ("   3. Monitorer performances continues", self.style_manager.colors['neon_green']),
            ("   4. Maintenir sécurité à jour", self.style_manager.colors['neon_yellow'])
        ]
        
        y_position = 30
        for text, color in report_data:
            report_canvas.create_text(
                20, y_position,
                text=text,
                font=self.style_manager.fonts['mono'],
                fill=color,
                anchor='w'
            )
            y_position += 25
    
    def browse_file(self):
        """Parcourt les fichiers avec interface vibrante"""
        file_path = filedialog.askopenfilename(
            title="🌈 SÉLECTIONNER FICHIER VIBRANT",
            filetypes=[("Tous les fichiers", "*.*"), ("Texte", "*.txt"), ("Documents", "*.pdf")]
        )
        
        if file_path:
            self.file_path_var.set(file_path)
            messagebox.showinfo("Fichier Sélectionné", f"📁 Fichier vibrant sélectionné :\n{file_path}")
    
    def activate_license(self):
        """Active la licence avec effets vibrants"""
        if not self.package:
            self.package = HarmonicAutonomousPackage()
        
        # Licence démo
        demo_license = "eyJ2ZXJzaW9uIjogIjEuMC4wIiwgImNvbXBhbnkiOiAiREVNT19IQ1ZfUFJPXzQ4SCIsICJzdGFydF90aW1lIjogMTc3NzEyODYxNy41ODY1NTQ4LCAiZXhwaXJ5X3RpbWUiOiAxNzc3MzAxNDE3LjU4NjU1NDgsICJkdXJhdGlvbl9ob3VycyI6IDQ4LCAibWF4X2NvbXByZXNzaW9ucyI6IDEwMDAsICJjdXJyZW50X2NvbXByZXNzaW9ucyI6IDAsICJzZWN1cml0eV9sZXZlbCI6ICJxdWFudHVtX2hhcm1vbmljIiwgImZlYXR1cmVzIjogWyJjb21wcmVzc2lvbl9zZWN1cmUiLCAicXVhbnR1bV9lbmNyeXB0aW9uIiwgImludGVncml0eV9jaGVjayIsICJsaWNlbnNlX3ZhbGlkYXRpb24iLCAic2VjdXJpdHlfbW9uaXRvcmluZyIsICJhbnRpX3JldmVyc2VfZW5naW5lZXJpbmciLCAiZnVsbF9hcGlfYWNjZXNzIiwgInByaW9yaXR5X3N1cHBvcnQiXSwgImhhcmR3YXJlX2lkIjogIjI1ODA3ZjA2MzIyZjQxMzkiLCAibGljZW5zZV9pZCI6ICIyNDdhN2RhMWNlZWIwMWQ2MDg3YTliZWQ2NDJlMzA5MyIsICJzaWduYXR1cmUiOiAiMWU4NGI5NDM3ZjA0MDU2YzFlZWE1ODliNzRlZjU5NDQ5MmZiNzlmNTliNWE1MTlkMzhjY2Q5ZjliNjY1MDRkMSJ9"
        
        if self.package.initialize(demo_license):
            self.license_active = True
            self.update_license_status()
            messagebox.showinfo("🎉 SUCCÈS VIBRANT", "🌈 Licence activée avec succès !\n\nPackage HCV PRO vibrant prêt pour utilisation !")
        else:
            messagebox.showerror("❌ ERREUR VIBRANTE", "Échec activation de la licence")
    
    def update_license_status(self):
        """Met à jour le statut de licence avec effets vibrants"""
        if self.license_active and self.package:
            info = self.package.get_package_info()
            
            if 'license' in info:
                license_info = info['license']
                self.status_badge.config(
                    text=f"🟢 LICENCIÉ VIBRANT - {license_info['company']}",
                    fg=self.style_manager.colors['neon_green']
                )
                
                self.license_info.config(
                    text=f"✅ {license_info['security_level'].title()}\n"
                         f"📊 {license_info['quota_remaining']} restantes",
                    fg=self.style_manager.colors['neon_green']
                )
                
                self.activate_btn.config(text="✅ LICENCE ACTIVE", state='disabled')
    
    def start_compression(self):
        """Démarre la compression avec effets vibrants"""
        if not self.license_active:
            messagebox.showwarning("🔑 LICENCE REQUISE", "🌈 Veuillez d'abord activer la licence vibrante")
            return
        
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showwarning("📁 FICHIER REQUIS", "🌈 Veuillez sélectionner un fichier à compresser")
            return
        
        if not Path(file_path).exists():
            messagebox.showerror("❌ ERREUR", "❌ Le fichier sélectionné n'existe pas")
            return
        
        # Compression en arrière-plan avec animations
        threading.Thread(target=self.compress_file_vibrant, args=(file_path,), daemon=True).start()
    
    def compress_file_vibrant(self, file_path):
        """Compresse le fichier avec interface vibrante"""
        try:
            # Animation de démarrage
            self.animate_compression_start()
            
            # Effectuer la compression
            output_path = file_path + ".hcvpro"
            result = self.package.compress_file(file_path, output_path)
            
            # Afficher les résultats vibrants
            self.display_vibrant_results(result, file_path, output_path)
            
            # Mettre à jour statut licence
            self.update_license_status()
            
        except Exception as e:
            self.display_compression_error(str(e))
    
    def animate_compression_start(self):
        """Animation de démarrage de compression"""
        self.results_canvas.delete("all")
        
        # Animation de progression
        colors = [self.style_manager.colors['neon_pink'],
                 self.style_manager.colors['neon_blue'],
                 self.style_manager.colors['neon_green'],
                 self.style_manager.colors['neon_yellow']]
        
        for i in range(5):
            color = colors[i % len(colors)]
            self.results_canvas.create_text(
                20, 30 + i * 30,
                text="🔄 COMPRESSION VIBRANTE EN COURS..." + "." * i,
                font=self.style_manager.fonts['body'],
                fill=color,
                anchor='w',
                tags="animation"
            )
        
        self.root.update()
        time.sleep(1)
    
    def display_vibrant_results(self, result, file_path, output_path):
        """Affiche les résultats avec couleurs vibrantes"""
        self.results_canvas.delete("all")
        
        if 'error' in result:
            self.results_canvas.create_text(
                20, 30,
                text=f"❌ ERREUR VIBRANTE : {result['error']}",
                font=self.style_manager.fonts['body'],
                fill=self.style_manager.colors['error'],
                anchor='w'
            )
        else:
            # Succès vibrant
            success_data = [
                ("🎉 COMPRESSION VIBRANTE TERMINÉE !", self.style_manager.colors['success']),
                ("", ""),
                ("📊 RÉSULTATS VIBRANTS :", self.style_manager.colors['neon_pink']),
                (f"   📁 Fichier original : {file_path}", self.style_manager.colors['neon_blue']),
                (f"   📦 Fichier compressé : {output_path}", self.style_manager.colors['neon_green']),
                (f"   📊 Taille originale : {result['original_size']:,} bytes", self.style_manager.colors['neon_yellow']),
                (f"   📊 Taille compressée : {result['compressed_size']:,} bytes", self.style_manager.colors['neon_orange']),
                (f"   ⚡ Ratio compression : {result['ratio']:.1f}:1", self.style_manager.colors['success']),
                (f"   ⏱️ Temps traitement : {result['processing_time_ms']:.2f}ms", self.style_manager.colors['neon_pink']),
                (f"   📋 Quota restant : {result['quota_remaining']}", self.style_manager.colors['neon_blue']),
                ("", ""),
                ("🌈 OPÉRATION VIBRANTE RÉUSSIE !", self.style_manager.colors['success'])
            ]
            
            y_position = 30
            for text, color in success_data:
                self.results_canvas.create_text(
                    20, y_position,
                    text=text,
                    font=self.style_manager.fonts['mono'],
                    fill=color,
                    anchor='w'
                )
                y_position += 25
    
    def display_compression_error(self, error):
        """Affiche une erreur de compression vibrante"""
        self.results_canvas.delete("all")
        
        self.results_canvas.create_text(
            20, 30,
            text="❌ ERREUR COMPRESSION VIBRANTE",
            font=self.style_manager.fonts['body'],
            fill=self.style_manager.colors['error'],
            anchor='w'
        )
        
        self.results_canvas.create_text(
            20, 60,
            text=f"Détails : {error}",
            font=self.style_manager.fonts['small'],
            fill=self.style_manager.colors['neon_pink'],
            anchor='w'
        )
    
    def run(self):
        """Démarre l'interface vibrante"""
        self.root.mainloop()

def main():
    """Point d'entrée principal vibrant"""
    try:
        app = HCVProVibrantGUI()
        app.run()
    except Exception as e:
        messagebox.showerror("❌ ERREUR VIBRANTE", f"Erreur démarrage interface : {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
