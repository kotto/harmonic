#!/usr/bin/env python3
"""
Compile HCV codec files to Cython (.so) extensions for IP protection.
Usage: python setup_cython.py build_ext --inplace
"""
import sys
from pathlib import Path
from setuptools import setup
from Cython.Build import cythonize
import numpy as np

CODEC_FILES = [
    'codecs/hcv_pro_codec.py',
    'codecs/hcv_android_boost_codec.py',
    'codecs/hcv_video_boost_codec.py',
    'codecs/hcv_universal_boost_codec.py',
    'codecs/hcv_mobile_camera_codec.py',
    'enterprise/core/tile_codec.py',
]

sources = [f for f in CODEC_FILES if Path(f).exists()]
if not sources:
    print("No codec files found to compile.")
    sys.exit(0)

print(f"Compiling {len(sources)} codec files with Cython...")
for s in sources:
    print(f"  {s}")

setup(
    name='hcv-codecs',
    ext_modules=cythonize(
        sources,
        compiler_directives={
            'language_level': '3',
            'boundscheck': False,
            'wraparound': False,
            'cdivision': True,
        },
        nthreads=4,
        quiet=False,
    ),
    include_dirs=[np.get_include()],
)
