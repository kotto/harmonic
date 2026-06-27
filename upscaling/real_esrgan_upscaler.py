"""
Real-ESRGAN Upscaler - Modèle IA optimisé pour vidéo
"""
import cv2
import numpy as np
import os
import sys
from typing import Dict, Optional
from .base_upscaler import BaseUpscaler

class RealESRGANUpscaler(BaseUpscaler):
    """
    Upscaler basé sur Real-ESRGAN
    Optimisé pour les vidéos avec artefacts de compression
    """
    
    def __init__(self, model_name: str = 'RealESRGAN_x4plus'):
        super().__init__("Real-ESRGAN")
        self.model_name = model_name
        self.model = None
        self.device = None
        self.scale = 4  # Real-ESRGAN par défaut
        
        # Chemins des modèles
        self.models_dir = os.path.join(os.path.dirname(__file__), 'models')
        self.model_paths = {
            'RealESRGAN_x4plus': 'RealESRGAN_x4plus.pth',
            'RealESRGAN_x2plus': 'RealESRGAN_x2plus.pth',
            'RealESRGAN_x4plus_anime': 'RealESRGAN_x4plus_anime_6B.pth'
        }
    
    def upscale(self, frame: np.ndarray, scale_factor: float) -> np.ndarray:
        """
        Upscale avec Real-ESRGAN
        
        Args:
            frame: Frame d'entrée BGR
            scale_factor: Facteur souhaité (sera adapté au modèle)
            
        Returns:
            Frame upscalée
        """
        if not self.is_initialized:
            if not self.initialize():
                # Fallback vers Lanczos si échec
                return self._fallback_lanczos(frame, scale_factor)
        
        try:
            # Préprocessing
            img_tensor = self._preprocess_frame(frame)
            
            # Inference Real-ESRGAN
            with self._no_grad():
                output_tensor = self.model(img_tensor)
            
            # Postprocessing
            upscaled_frame = self._postprocess_tensor(output_tensor)
            
            # Ajustement si scale_factor différent du modèle
            if scale_factor != self.scale:
                upscaled_frame = self._adjust_scale(upscaled_frame, frame, scale_factor)
            
            return upscaled_frame
            
        except Exception as e:
            print(f"Erreur Real-ESRGAN: {e}")
            return self._fallback_lanczos(frame, scale_factor)
    
    def get_requirements(self) -> Dict:
        """Requirements pour Real-ESRGAN"""
        return {
            "gpu": True,  # Fortement recommandé
            "ram_mb": 2048,
            "gpu_memory_mb": 4096,
            "libs": ["torch", "torchvision", "basicsr", "facexlib", "gfpgan"],
            "python_version": ">=3.7"
        }
    
    def is_available(self) -> bool:
        """Vérifie si Real-ESRGAN peut fonctionner"""
        try:
            # Test imports
            import torch
            import torchvision
            
            # Test GPU (optionnel mais recommandé)
            gpu_available = torch.cuda.is_available()
            
            # Test modèle
            model_path = os.path.join(self.models_dir, self.model_paths[self.model_name])
            model_exists = os.path.exists(model_path)
            
            return model_exists and (gpu_available or self._cpu_fallback_ok())
            
        except ImportError as e:
            print(f"Real-ESRGAN non disponible: {e}")
            return False
    
    def get_supported_scales(self) -> list:
        """Scales supportés par Real-ESRGAN"""
        if self.model_name == 'RealESRGAN_x2plus':
            return [2.0]
        else:
            return [4.0]  # x4plus par défaut
    
    def _initialize_internal(self):
        """Initialisation Real-ESRGAN"""
        try:
            import torch
            from basicsr.archs.rrdbnet_arch import RRDBNet
            
            # Détection device
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            print(f"Real-ESRGAN utilise: {self.device}")
            
            # Configuration modèle selon le type
            if self.model_name == 'RealESRGAN_x4plus':
                model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, 
                               num_block=23, num_grow_ch=32, scale=4)
                self.scale = 4
            elif self.model_name == 'RealESRGAN_x2plus':
                model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, 
                               num_block=23, num_grow_ch=32, scale=2)
                self.scale = 2
            else:
                raise ValueError(f"Modèle non supporté: {self.model_name}")
            
            # Chargement des poids
            model_path = os.path.join(self.models_dir, self.model_paths[self.model_name])
            
            if not os.path.exists(model_path):
                print(f"Téléchargement du modèle {self.model_name}...")
                self._download_model(model_path)
            
            # Chargement et configuration
            loadnet = torch.load(model_path, map_location=self.device)
            if 'params_ema' in loadnet:
                keyname = 'params_ema'
            else:
                keyname = 'params'
            model.load_state_dict(loadnet[keyname], strict=True)
            
            model.eval()
            model = model.to(self.device)
            self.model = model
            
            print(f"Real-ESRGAN {self.model_name} initialisé avec succès")
            
        except Exception as e:
            raise RuntimeError(f"Échec initialisation Real-ESRGAN: {e}")
    
    def _preprocess_frame(self, frame: np.ndarray) -> 'torch.Tensor':
        """Préprocessing pour Real-ESRGAN"""
        import torch
        
        # BGR vers RGB
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Normalisation [0, 255] -> [0, 1]
        img_normalized = img_rgb.astype(np.float32) / 255.0
        
        # HWC vers CHW
        img_chw = np.transpose(img_normalized, (2, 0, 1))
        
        # Numpy vers Tensor
        img_tensor = torch.from_numpy(img_chw).float().unsqueeze(0).to(self.device)
        
        return img_tensor
    
    def _postprocess_tensor(self, tensor: 'torch.Tensor') -> np.ndarray:
        """Postprocessing du tensor de sortie"""
        # Tensor vers numpy
        output = tensor.data.squeeze().float().cpu().clamp_(0, 1).numpy()
        
        # CHW vers HWC
        output = np.transpose(output, (1, 2, 0))
        
        # [0, 1] vers [0, 255]
        output = (output * 255.0).round().astype(np.uint8)
        
        # RGB vers BGR
        output_bgr = cv2.cvtColor(output, cv2.COLOR_RGB2BGR)
        
        return output_bgr
    
    def _adjust_scale(self, upscaled: np.ndarray, original: np.ndarray, target_scale: float) -> np.ndarray:
        """Ajuste la taille si scale_factor différent du modèle"""
        orig_h, orig_w = original.shape[:2]
        target_w = int(orig_w * target_scale)
        target_h = int(orig_h * target_scale)
        
        # Resize vers la taille cible
        adjusted = cv2.resize(upscaled, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
        return adjusted
    
    def _fallback_lanczos(self, frame: np.ndarray, scale_factor: float) -> np.ndarray:
        """Fallback vers Lanczos en cas d'erreur"""
        print("Fallback vers Lanczos...")
        height, width = frame.shape[:2]
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        return cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
    
    def _no_grad(self):
        """Context manager pour désactiver les gradients"""
        import torch
        return torch.no_grad()
    
    def _cpu_fallback_ok(self) -> bool:
        """Vérifie si CPU fallback acceptable"""
        # Real-ESRGAN sur CPU est très lent mais possible
        return True
    
    def _download_model(self, model_path: str):
        """Télécharge le modèle depuis GitHub"""
        import urllib.request
        
        # URLs des modèles Real-ESRGAN
        model_urls = {
            'RealESRGAN_x4plus.pth': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth',
            'RealESRGAN_x2plus.pth': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x2plus.pth',
            'RealESRGAN_x4plus_anime_6B.pth': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth'
        }
        
        model_filename = os.path.basename(model_path)
        if model_filename not in model_urls:
            raise ValueError(f"URL inconnue pour {model_filename}")
        
        # Créer le dossier models si nécessaire
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # Téléchargement
        print(f"Téléchargement de {model_filename}...")
        urllib.request.urlretrieve(model_urls[model_filename], model_path)
        print(f"Modèle téléchargé: {model_path}")
    
    def get_memory_usage(self) -> int:
        """Usage mémoire Real-ESRGAN"""
        if self.model_name == 'RealESRGAN_x4plus':
            return 4096  # ~4GB GPU memory
        else:
            return 2048  # ~2GB pour x2plus
    
    def supports_batch_processing(self) -> bool:
        """Real-ESRGAN peut bénéficier du batch processing"""
        return True
    
    def cleanup(self):
        """Nettoyage des ressources GPU"""
        if self.model is not None:
            del self.model
            self.model = None
        
        # Nettoyage cache GPU si disponible
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except:
            pass