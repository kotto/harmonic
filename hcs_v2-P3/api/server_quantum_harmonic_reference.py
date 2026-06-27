# APPROCHE DE RÉFÉRENCE CHROMATIQUE - IDÉE UTILISATEUR

def extract_reference_chromatic_profile(video_path, sample_frame=0):
    """Extraire une frame et l'upscale comme image pour profil chromatique"""
    try:
        import cv2
        import numpy as np
        import logging
        logger = logging.getLogger(__name__)
        
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, sample_frame)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            logger.warning("⚠️ Impossible d'extraire la frame de référence")
            return None
        
        # Convertir en RGB si nécessaire
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            r_mean = np.mean(frame[:, :, 0])
            b_mean = np.mean(frame[:, :, 2])
            
            if b_mean > r_mean + 15:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                frame_rgb = frame
        else:
            frame_rgb = frame
        
        # Utiliser notre pipeline d'upscale d'image qui fonctionne
        from core.harmonic_upscaler import HarmonicUpscaler
        upscaler = HarmonicUpscaler()
        
        # Upscaler comme une image (pipeline qui fonctionne)
        upscaled_image = upscaler.upscale_image(
            frame_rgb, 
            scale_factor=2.0,
            energy_level="standard"
        )
        
        # Analyser les caractéristiques chromatiques de l'image upscalée
        if upscaled_image is not None:
            profile = {
                'r_mean': np.mean(upscaled_image[:, :, 0]),
                'g_mean': np.mean(upscaled_image[:, :, 1]),
                'b_mean': np.mean(upscaled_image[:, :, 2]),
                'saturation_mean': np.mean(cv2.cvtColor(upscaled_image, cv2.COLOR_RGB2HSV)[:, :, 1]),
                'brightness_mean': np.mean(cv2.cvtColor(upscaled_image, cv2.COLOR_RGB2LAB)[:, :, 0])
            }
            
            logger.info(f"🎨 Profil chromatique de référence extrait:")
            logger.info(f"   RGB moyens: [{profile['r_mean']:.1f}, {profile['g_mean']:.1f}, {profile['b_mean']:.1f}]")
            logger.info(f"   Saturation moyenne: {profile['saturation_mean']:.1f}")
            logger.info(f"   Luminosité moyenne: {profile['brightness_mean']:.1f}")
            
            return profile
        
        return None
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"⚠️ Erreur extraction profil chromatique: {e}")
        return None

def apply_reference_chromatic_profile(frame, reference_profile):
    """Appliquer le profil chromatique de référence à une frame vidéo"""
    try:
        if reference_profile is None:
            return frame
        
        import cv2
        import numpy as np
        import logging
        logger = logging.getLogger(__name__)
        
        # Analyser la frame actuelle
        current_r_mean = np.mean(frame[:, :, 0])
        current_g_mean = np.mean(frame[:, :, 1])
        current_b_mean = np.mean(frame[:, :, 2])
        
        # Calculer les facteurs de correction basés sur la référence
        r_factor = reference_profile['r_mean'] / current_r_mean if current_r_mean > 0 else 1.0
        g_factor = reference_profile['g_mean'] / current_g_mean if current_g_mean > 0 else 1.0
        b_factor = reference_profile['b_mean'] / current_b_mean if current_b_mean > 0 else 1.0
        
        # Limiter les facteurs pour éviter les extrêmes
        r_factor = np.clip(r_factor, 0.7, 1.3)
        g_factor = np.clip(g_factor, 0.7, 1.3)
        b_factor = np.clip(b_factor, 0.7, 1.3)
        
        # Appliquer les corrections
        corrected = frame.copy().astype(np.float32)
        corrected[:, :, 0] *= r_factor
        corrected[:, :, 1] *= g_factor
        corrected[:, :, 2] *= b_factor
        
        # Ajuster la saturation pour correspondre à la référence
        frame_hsv = cv2.cvtColor(corrected.astype(np.uint8), cv2.COLOR_RGB2HSV)
        current_sat = np.mean(frame_hsv[:, :, 1])
        target_sat = reference_profile['saturation_mean']
        sat_factor = target_sat / current_sat if current_sat > 0 else 1.0
        sat_factor = np.clip(sat_factor, 0.8, 1.2)
        
        frame_hsv[:, :, 1] = np.clip(frame_hsv[:, :, 1] * sat_factor, 0, 255)
        corrected = cv2.cvtColor(frame_hsv, cv2.COLOR_HSV2RGB)
        
        logger.info(f"🎨 Profil référence appliqué: RGB×[{r_factor:.2f}, {g_factor:.2f}, {b_factor:.2f}], Sat×{sat_factor:.2f}")
        
        return corrected.astype(np.uint8)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"⚠️ Erreur application profil référence: {e}")
        return frame
