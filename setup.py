from setuptools import setup, find_packages

setup(
    name="harmonic-ai",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'torch>=2.0.0',
        'numpy>=1.23.0',
    ],
    entry_points={
        'console_scripts': [
            'harmonic-cli=harmonic.cli:main',
        ],
    },
)