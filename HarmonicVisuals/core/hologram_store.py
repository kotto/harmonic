"""ImageHologramStore — Stockage holographique d'images"""
import math, time, uuid, numpy as np

class ImageHologramStore:
    def __init__(self, dim=512): self.dim=dim; self.H=np.zeros(dim,dtype=np.complex128); self.count=0
    def add(self, img: np.ndarray, prompt: str) -> str:
        psi = self._img_to_psi(img); self.H += psi; self.count += 1
        hid = str(uuid.uuid4())[:8]; return hid
    def _img_to_psi(self, img: np.ndarray) -> np.ndarray:
        gray = np.mean(img, axis=2) if img.ndim==3 else img
        small = gray[::max(1,gray.shape[0]//32), ::max(1,gray.shape[1]//32)]
        psi = np.zeros(self.dim, dtype=np.complex128)
        for i in range(min(small.size, self.dim)):
            psi[i] = complex(small.flat[i]/255.0, 0.0)
        n=np.sqrt(np.sum(np.abs(psi)**2)); return psi/(n+1e-10) if n>1e-10 else psi
