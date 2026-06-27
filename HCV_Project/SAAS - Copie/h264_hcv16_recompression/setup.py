#!/usr/bin/env python3
"""
Setup script pour POC H.264 → HCV16 Recompression
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="h264-hcv16-recompression",
    version="0.1.0",
    author="HCV16 Team",
    author_email="team@hcv16.com",
    description="POC recompression H.264 avec breakthrough HCV16",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hcv16/h264-recompression-poc",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Video :: Conversion",
        "Topic :: Scientific/Engineering :: Image Processing",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=0.5",
        ],
    },
    entry_points={
        "console_scripts": [
            "h264-hcv16-recompress=h264_recompressor:main",
            "h264-analyze=h264_analyzer:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)