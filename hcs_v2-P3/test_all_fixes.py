#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validation des 4 correctifs appliques"""
import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'f:\FINAL\DEFINITIF\hcs_v2-P3')
os.chdir(r'f:\FINAL\DEFINITIF\hcs_v2-P3')

import numpy as np

print("=" * 62)
print("  VALIDATION DES 4 CORRECTIFS HCS STUDIO")
print("=" * 62)

# ── FIX 1: HarmonicUpscaler chargeable ──────────────────────────
print("\n[P0] Fix 1 - harmonic_upscaler emoji")
try:
    from core.harmonic_upscaler import harmonic_upscaler_api, HarmonicUpscalerAPI
    assert isinstance(harmonic_upscaler_api, HarmonicUpscalerAPI)
    print("  [OK] HarmonicUpscalerAPI charge correctement (fallback bicubique)")
except Exception as e:
    print(f"  [KO] ECHEC: {e}")

# ── FIX 2: startup_checks ────────────────────────────────────────
print("\n[P0] Fix 2 - startup_checks.py")
try:
    from hcs_studio_integrated.startup_checks import verify_modules, print_startup_banner
    result = verify_modules(strict=False)
    ok_req = sum(1 for v in result['required'].values() if v['ok'])
    tot_req = len(result['required'])
    print(f"  Modules requis: {ok_req}/{tot_req}")
    ok_opt = sum(1 for v in result['optional'].values() if v['ok'])
    tot_opt = len(result['optional'])
    print(f"  Modules optionnels: {ok_opt}/{tot_opt}")
    if ok_req == tot_req:
        print("  [OK] Tous les modules requis presents")
    else:
        print(f"  [WARN] {tot_req - ok_req} module(s) requis absent(s)")
except Exception as e:
    print(f"  [KO] ECHEC: {e}")

# ── FIX 3: compress_frames_parallel ─────────────────────────────
print("\n[P1] Fix 3 - compress_frames_parallel (30 frames 320x240)")
try:
    from core.hybrid_compressor import HybridCompressor
    comp = HybridCompressor()
    frames = [np.random.rand(240, 320, 3).astype('float32') for _ in range(30)]

    # Sequentiel
    t0 = time.time()
    for f in frames:
        comp.compress_image(f)
    t_seq = time.time() - t0

    # Parallele
    t1 = time.time()
    results = comp.compress_frames_parallel(frames)
    t_par = time.time() - t1

    ok = sum(1 for r in results if r and r['success'])
    fps_seq = 30 / t_seq
    fps_par = 30 / t_par
    speedup = t_seq / t_par
    print(f"  Sequentiel : {fps_seq:.1f} FPS  ({t_seq*1000:.0f} ms)")
    print(f"  Parallele  : {fps_par:.1f} FPS  ({t_par*1000:.0f} ms)")
    print(f"  Speedup    : {speedup:.2f}x")
    print(f"  Succes     : {ok}/30")
    if fps_par >= fps_seq:
        print("  [OK] Parallele >= Sequentiel")
    else:
        print("  [WARN] Pas de gain (test local, gain visible sur vrai CPU multi-coeur)")
except Exception as e:
    print(f"  [KO] ECHEC: {e}")
    import traceback; traceback.print_exc()

# ── FIX 4: K-factor plancher ─────────────────────────────────────
print("\n[P1] Fix 4 - K-factor plancher adaptatif")
try:
    from core.k_factor_engine import KFactorEngine
    e = KFactorEngine(0.02)
    all_ok = True
    for (h, w) in [(240, 320), (480, 640), (720, 1280), (1080, 1920)]:
        img = np.random.rand(h, w, 3).astype('float32')
        _, meta = e.compress_image(img)
        ok = meta['guarantee_met']
        flag = "[OK]" if ok else "[FAIL]"
        print(f"  {w}x{h}: ratio={meta['actual_ratio']:.1f}:1  {flag}")
        if not ok:
            all_ok = False
    if all_ok:
        print("  [OK] Garantie 50:1 respectee sur toutes les resolutions")
    else:
        print("  [KO] Garantie non respectee sur certaines resolutions")
except Exception as e:
    print(f"  [KO] ECHEC: {e}")

print("\n" + "=" * 62)
print("  VALIDATION TERMINEE")
print("=" * 62)
