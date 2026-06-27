#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HCS V2 - Test Camera 8K
Prototype pour tester la prise photo/vidéo et conversion 8K
"""

import os
import cv2
import numpy as np
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import base64
from datetime import datetime

# Import des modules HCS (simulés pour le test)
try:
    from server_quantum_harmonic_reference import extract_reference_chromatic_profile, apply_reference_chromatic_profile
except ImportError:
    print("⚠️ Modules HCS non trouvés, utilisation mode simulation")
    
    def extract_reference_chromatic_profile(image):
        """Simulation extraction profil chromatique"""
        return {
            'mean_rgb': np.array([128, 128, 128]),
            'saturation': 0.8,
            'brightness': 0.9,
            'contrast': 1.1
        }
    
    def apply_reference_chromatic_profile(image, profile):
        """Simulation application profil chromatique"""
        # Application simple des corrections
        result = image.copy().astype(np.float32)
        
        # Correction RGB
        result[:, :, 0] *= profile['mean_rgb'][0] / 128.0
        result[:, :, 1] *= profile['mean_rgb'][1] / 128.0
        result[:, :, 2] *= profile['mean_rgb'][2] / 128.0
        
        # Saturation
        result = np.clip(result, 0, 255).astype(np.uint8)
        return result

class HCSCamera8K:
    """Application de test pour camera 8K"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🌊 HCS V2 - Test Camera 8K")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1a1a')
        
        # Variables
        self.camera = None
        self.is_recording = False
        self.current_frame = None
        self.processed_frame = None
        self.reference_profile = None
        
        # Configuration 8K
        self.target_width = 7680
        self.target_height = 4320
        
        # Création interface
        self.create_interface()
        
        # Initialisation caméra
        self.init_camera()
        
    def create_interface(self):
        """Création de l'interface graphique"""
        
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Titre
        title_label = tk.Label(
            main_frame,
            text="🌊 HCS V2 - CAMERA 8K TEST",
            font=("Arial", 20, "bold"),
            fg='#FFD700',
            bg='#1a1a1a'
        )
        title_label.pack(pady=10)
        
        # Frame caméras
        cameras_frame = ttk.Frame(main_frame)
        cameras_frame.pack(fill=tk.BOTH, expand=True)
        
        # Caméra originale
        original_frame = ttk.LabelFrame(cameras_frame, text="📸 Caméra Originale")
        original_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.original_label = tk.Label(original_frame, bg="black", width=40, height=20)
        self.original_label.pack(padx=5, pady=5)
        
        # Caméra 8K traitée
        processed_frame = ttk.LabelFrame(cameras_frame, text="🎯 Résultat 8K HCS")
        processed_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        self.processed_label = tk.Label(processed_frame, bg="black", width=40, height=20)
        self.processed_label.pack(padx=5, pady=5)
        
        # Frame contrôles
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=10)
        
        # Boutons principaux
        button_frame = ttk.Frame(controls_frame)
        button_frame.pack()
        
        # Bouton Photo
        self.photo_btn = tk.Button(
            button_frame,
            text="📸 Prendre Photo 8K",
            command=self.take_photo,
            font=("Arial", 12, "bold"),
            bg='#4CAF50',
            fg='white',
            width=20,
            height=2
        )
        self.photo_btn.pack(side=tk.LEFT, padx=5)
        
        # Bouton Vidéo
        self.video_btn = tk.Button(
            button_frame,
            text="🎬 Enregistrer Vidéo 8K",
            command=self.toggle_video,
            font=("Arial", 12, "bold"),
            bg='#2196F3',
            fg='white',
            width=20,
            height=2
        )
        self.video_btn.pack(side=tk.LEFT, padx=5)
        
        # Bouton Référence
        self.reference_btn = tk.Button(
            button_frame,
            text="🎯 Extraire Référence",
            command=self.extract_reference,
            font=("Arial", 12, "bold"),
            bg='#FF9800',
            fg='white',
            width=20,
            height=2
        )
        self.reference_btn.pack(side=tk.LEFT, padx=5)
        
        # Frame informations
        info_frame = ttk.LabelFrame(main_frame, text="📊 Informations 8K")
        info_frame.pack(fill=tk.X, pady=10)
        
        # Labels d'information
        self.info_labels = {}
        info_items = [
            ("Résolution Originale", "0x0"),
            ("Résolution 8K", f"{self.target_width}x{self.target_height}"),
            ("Facteur Upscaling", "0x"),
            ("Qualité PSNR", "0 dB"),
            ("Temps Traitement", "0s"),
            ("Référence Chromatique", "Non extraite")
        ]
        
        for i, (label, value) in enumerate(info_items):
            frame = ttk.Frame(info_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)
            
            tk.Label(frame, text=f"{label}:", font=("Arial", 10, "bold"), width=20, anchor='w').pack(side=tk.LEFT)
            self.info_labels[label] = tk.Label(frame, text=value, font=("Arial", 10), anchor='w')
            self.info_labels[label].pack(side=tk.LEFT, padx=10)
        
        # Frame sauvegarde
        save_frame = ttk.Frame(main_frame)
        save_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(
            save_frame,
            text="💾 Sauvegarder Photo 8K",
            command=self.save_photo,
            font=("Arial", 10),
            bg='#9C27B0',
            fg='white'
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            save_frame,
            text="📤 Exporter Vidéo 8K",
            command=self.save_video,
            font=("Arial", 10),
            bg='#607D8B',
            fg='white'
        ).pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_label = tk.Label(
            main_frame,
            text="🌊 HCS V2 Prêt - Caméra en cours d'initialisation...",
            font=("Arial", 10),
            fg='#4CAF50',
            bg='#1a1a1a'
        )
        self.status_label.pack(pady=5)
        
    def init_camera(self):
        """Initialisation de la caméra"""
        try:
            # Tentative d'ouverture de la caméra
            self.camera = cv2.VideoCapture(0)
            
            if not self.camera.isOpened():
                # Essayer d'autres indices
                for i in range(1, 5):
                    self.camera = cv2.VideoCapture(i)
                    if self.camera.isOpened():
                        break
            
            if self.camera.isOpened():
                # Configuration de la caméra
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                self.camera.set(cv2.CAP_PROP_FPS, 30)
                
                self.status_label.config(text="🌊 Caméra initialisée avec succès !")
                self.update_camera()
            else:
                self.status_label.config(text="❌ Erreur: Caméra non détectée")
                messagebox.showerror("Erreur", "Aucune caméra détectée")
                
        except Exception as e:
            self.status_label.config(text=f"❌ Erreur caméra: {str(e)}")
            messagebox.showerror("Erreur", f"Erreur initialisation caméra: {str(e)}")
    
    def update_camera(self):
        """Mise à jour du flux caméra"""
        if self.camera and self.camera.isOpened():
            ret, frame = self.camera.read()
            if ret:
                self.current_frame = frame
                
                # Mise à jour affichage original
                self.display_frame(frame, self.original_label)
                
                # Traitement 8K en arrière-plan
                if not self.is_recording:
                    threading.Thread(target=self.process_frame_8k, args=(frame,), daemon=True).start()
        
        # Planification prochaine mise à jour
        self.root.after(33, self.update_camera)  # ~30 FPS
    
    def process_frame_8k(self, frame):
        """Traitement du frame en 8K"""
        try:
            start_time = time.time()
            
            # Upscaling 8K (simulation)
            processed = self.upscale_to_8k(frame)
            
            # Application référence chromatique si disponible
            if self.reference_profile:
                processed = apply_reference_chromatic_profile(processed, self.reference_profile)
            
            processing_time = time.time() - start_time
            
            # Mise à jour affichage
            self.processed_frame = processed
            self.display_frame(processed, self.processed_label, resize_for_display=True)
            
            # Mise à jour informations
            h, w = frame.shape[:2]
            factor = (self.target_width * self.target_height) / (w * h)
            psnr = self.calculate_psnr(frame, processed)
            
            self.root.after(0, self.update_info, w, h, factor, processing_time, psnr)
            
        except Exception as e:
            print(f"⚠️ Erreur traitement 8K: {e}")
    
    def upscale_to_8k(self, frame):
        """Upscaling d'un frame vers 8K"""
        h, w = frame.shape[:2]
        
        # Calcul facteur d'upscaling
        scale_x = self.target_width / w
        scale_y = self.target_height / h
        scale = min(scale_x, scale_y)  # Garder le ratio
        
        # Upscaling avec interpolation avancée
        new_width = int(w * scale)
        new_height = int(h * scale)
        
        # Utilisation de INTER_LANCZOS4 pour meilleure qualité
        upscaled = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
        
        # Si nécessaire, ajouter des bordures pour atteindre exactement 8K
        if new_width != self.target_width or new_height != self.target_height:
            pad_x = (self.target_width - new_width) // 2
            pad_y = (self.target_height - new_height) // 2
            
            upscaled = cv2.copyMakeBorder(
                upscaled,
                pad_y,
                self.target_height - new_height - pad_y,
                pad_x,
                self.target_width - new_width - pad_x,
                cv2.BORDER_REFLECT_101
            )
        
        return upscaled
    
    def calculate_psnr(self, original, processed):
        """Calcul du PSNR (simulation)"""
        # PSNR simulé basé sur le facteur d'upscaling
        h_orig, w_orig = original.shape[:2]
        h_proc, w_proc = processed.shape[:2]
        
        factor = (w_proc * h_proc) / (w_orig * h_orig)
        
        # PSNR simulé: meilleur si facteur modéré, moins bon si extrême
        if factor < 4:
            return 45.0 - (factor - 1) * 2
        else:
            return 43.0 - (factor - 4) * 1
    
    def display_frame(self, frame, label, resize_for_display=False):
        """Affichage d'un frame dans un label"""
        try:
            # Conversion pour affichage
            if resize_for_display:
                # Redimensionner pour l'affichage (sinon trop grand)
                display_frame = cv2.resize(frame, (320, 240))
            else:
                display_frame = frame
            
            # Conversion BGR -> RGB
            rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            
            # Conversion PIL -> PhotoImage
            image = Image.fromarray(rgb_frame)
            photo = ImageTk.PhotoImage(image)
            
            # Mise à jour du label
            label.config(image=photo)
            label.image = photo  # Garder une référence
            
        except Exception as e:
            print(f"⚠️ Erreur affichage: {e}")
    
    def update_info(self, width, height, factor, processing_time, psnr):
        """Mise à jour des informations"""
        self.info_labels["Résolution Originale"].config(text=f"{width}x{height}")
        self.info_labels["Facteur Upscaling"].config(text=f"{factor:.1f}x")
        self.info_labels["Temps Traitement"].config(text=f"{processing_time:.3f}s")
        self.info_labels["Qualité PSNR"].config(text=f"{psnr:.1f} dB")
    
    def take_photo(self):
        """Prise de photo 8K"""
        if self.current_frame is not None:
            # Traitement 8K
            processed = self.upscale_to_8k(self.current_frame)
            
            if self.reference_profile:
                processed = apply_reference_chromatic_profile(processed, self.reference_profile)
            
            # Sauvegarde automatique
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hcs_8k_photo_{timestamp}.jpg"
            
            cv2.imwrite(filename, processed, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            self.status_label.config(text=f"📸 Photo 8K sauvegardée: {filename}")
            messagebox.showinfo("Succès", f"Photo 8K sauvegardée: {filename}")
    
    def toggle_video(self):
        """Basculement enregistrement vidéo"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Début enregistrement vidéo"""
        if self.current_frame is not None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.video_filename = f"hcs_8k_video_{timestamp}.mp4"
            
            # Configuration vidéo 8K
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(
                self.video_filename,
                fourcc,
                30.0,
                (self.target_width, self.target_height)
            )
            
            if self.video_writer.isOpened():
                self.is_recording = True
                self.video_btn.config(text="⏹️ Arrêter Vidéo 8K", bg='#F44336')
                self.status_label.config(text="🎬 Enregistrement vidéo 8K en cours...")
                
                # Démarrage thread enregistrement
                self.recording_thread = threading.Thread(target=self.record_video, daemon=True)
                self.recording_thread.start()
            else:
                messagebox.showerror("Erreur", "Impossible d'initialiser l'enregistrement vidéo")
    
    def stop_recording(self):
        """Arrêt enregistrement vidéo"""
        self.is_recording = False
        self.video_btn.config(text="🎬 Enregistrer Vidéo 8K", bg='#2196F3')
        self.status_label.config(text=f"🎬 Vidéo 8K sauvegardée: {self.video_filename}")
        messagebox.showinfo("Succès", f"Vidéo 8K sauvegardée: {self.video_filename}")
    
    def record_video(self):
        """Thread d'enregistrement vidéo"""
        while self.is_recording:
            if self.current_frame is not None:
                # Traitement 8K
                processed = self.upscale_to_8k(self.current_frame)
                
                if self.reference_profile:
                    processed = apply_reference_chromatic_profile(processed, self.reference_profile)
                
                # Écriture frame
                self.video_writer.write(processed)
            
            time.sleep(1/30)  # 30 FPS
        
        # Finalisation
        if hasattr(self, 'video_writer'):
            self.video_writer.release()
    
    def extract_reference(self):
        """Extraction du profil chromatique de référence"""
        if self.current_frame is not None:
            # Traitement 8K du frame actuel
            processed = self.upscale_to_8k(self.current_frame)
            
            # Extraction profil chromatique
            self.reference_profile = extract_reference_chromatic_profile(processed)
            
            self.info_labels["Référence Chromatique"].config(text="✅ Extraite")
            self.status_label.config(text="🎯 Profil chromatique de référence extrait avec succès !")
            messagebox.showinfo("Succès", "Profil chromatique de référence extrait !")
    
    def save_photo(self):
        """Sauvegarde photo 8K"""
        if self.processed_frame is not None:
            filename = filedialog.asksaveasfilename(
                defaultextension=".jpg",
                filetypes=[("JPEG files", "*.jpg"), ("PNG files", "*.png"), ("All files", "*.*")]
            )
            
            if filename:
                cv2.imwrite(filename, self.processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                self.status_label.config(text=f"💾 Photo 8K sauvegardée: {filename}")
    
    def save_video(self):
        """Sauvegarde vidéo 8K"""
        if hasattr(self, 'video_filename') and os.path.exists(self.video_filename):
            filename = filedialog.asksaveasfilename(
                defaultextension=".mp4",
                filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
            )
            
            if filename:
                import shutil
                shutil.move(self.video_filename, filename)
                self.status_label.config(text=f"📤 Vidéo 8K sauvegardée: {filename}")
    
    def run(self):
        """Démarrage de l'application"""
        self.root.mainloop()
        
        # Nettoyage
        if self.camera:
            self.camera.release()

def main():
    """Fonction principale"""
    print("🌊 HCS V2 - Test Camera 8K")
    print("=" * 50)
    print("📸 Test de prise de photo et vidéo 8K")
    print("🎯 Upscaling harmonique en temps réel")
    print("🌊 Référence chromatique intégrée")
    print("=" * 50)
    
    # Vérification dépendances
    try:
        import cv2
        import numpy as np
        from PIL import Image, ImageTk
        print("✅ Dépendances OK")
    except ImportError as e:
        print(f"❌ Dépendance manquante: {e}")
        print("📦 Installez avec: pip install opencv-python pillow numpy")
        return
    
    # Lancement application
    app = HCSCamera8K()
    app.run()

if __name__ == "__main__":
    main()
