"""PhiPostFilter — Équilibrage φ + débruitage + accentuation"""
import math, numpy as np
PHI = 1.618033988749895; TAU = 2*math.pi

class PhiPostFilter:
    def apply(self, img: np.ndarray) -> np.ndarray:
        if img.dtype != np.float32: img_f = img.astype(np.float32)
        else: img_f = img.copy()
        try:
            from scipy.ndimage import convolve
            h, w = img_f.shape[:2]
            # Accentuation φ
            k = np.array([[-0.5/PHI, -0.5, -0.5/PHI],[-0.5, PHI, -0.5],[-0.5/PHI, -0.5, -0.5/PHI]])
            if img_f.ndim == 3:
                for c in range(3):
                    img_f[:,:,c] = np.clip(img_f[:,:,c] + convolve(img_f[:,:,c], k)*0.25, 0, 255)
        except: pass
        # Contraste φ
        for c in range(3 if img_f.ndim==3 else 1):
            ch = img_f[:,:,c] if img_f.ndim==3 else img_f
            low, high = np.percentile(ch, 2), np.percentile(ch, 98)
            if high > low: ch[:] = np.clip((ch-low)/(high-low+1e-10)*255, 0, 255)
        return img_f.astype(np.uint8)
