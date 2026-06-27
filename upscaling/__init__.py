# Upscaling module for HCV Studio
from .base_upscaler import BaseUpscaler
from .lanczos_upscaler import LanczosUpscaler
from .real_esrgan_upscaler import RealESRGANUpscaler
from .smart_upscaler import SmartUpscaler

__all__ = ['BaseUpscaler', 'LanczosUpscaler', 'RealESRGANUpscaler', 'SmartUpscaler']