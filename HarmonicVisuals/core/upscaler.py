"""PhiUpscaler — Upscaling ×2/×4 sans perte de qualité"""
import math, numpy as np
PHI = 1.618033988749895

class PhiUpscaler:
    def upscale(self, img: np.ndarray, factor: int = 2) -> tuple:
        try:
            from PIL import Image
            h, w = img.shape[:2]
            pil = Image.fromarray(img)
            up = pil.resize((w*factor, h*factor), Image.LANCZOS)
            up_arr = np.array(up)
            # Accentuation φ des contours
            from scipy.ndimage import convolve
            kernel = np.array([[-1/PHI, -1, -1/PHI], [-1, 2*PHI, -1], [-1/PHI, -1, -1/PHI]])
            if up_arr.ndim == 3:
                for c in range(3):
                    up_arr[:,:,c] = np.clip(up_arr[:,:,c] + convolve(up_arr[:,:,c].astype(float), kernel) * 0.3, 0, 255)
            return up_arr.astype(np.uint8), factor
        except ImportError:
            h, w = img.shape[:2]
            new_h, new_w = h*factor, w*factor
            y = np.linspace(0, h-1, new_h); x = np.linspace(0, w-1, new_w)
            y0 = np.floor(y).astype(int); x0 = np.floor(x).astype(int)
            y1 = np.minimum(y0+1, h-1); x1 = np.minimum(x0+1, w-1)
            dy, dx = y-y0, x-x0
            if img.ndim == 3:
                result = np.zeros((new_h, new_w, 3), dtype=img.dtype)
                for c in range(3):
                    for i in range(new_h):
                        wy = dy[i]
                        row = ((1-wy)*((1-dx)*img[y0[i],x0,c]+dx*img[y0[i],x1,c]) +
                                wy*((1-dx)*img[y1[i],x0,c]+dx*img[y1[i],x1,c]))
                        result[i,:,c] = row.astype(img.dtype)
                return result, factor
            return np.repeat(np.repeat(img, factor, axis=0), factor, axis=1), factor
