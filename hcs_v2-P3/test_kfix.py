#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

import numpy as np
from core.k_factor_engine import KFactorEngine

e = KFactorEngine(0.02)
print("Test K-factor plancher adaptatif")
print("=" * 55)
for (h, w) in [(240, 320), (480, 640), (720, 1280), (1080, 1920)]:
    img = np.random.rand(h, w, 3).astype('float32')
    comp, meta = e.compress_image(img)
    flag = "[OK]" if meta['guarantee_met'] else "[FAIL]"
    print(f"{w}x{h}: ratio={meta['actual_ratio']:.1f}:1  "
          f"compress={comp.shape}  {flag}")
print("Done")
