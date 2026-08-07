"""
🌊 HWAT-Med-125M — KAGGLE PACKAGE (pour upload de données)
===========================================================
Ce dossier est le PACKAGE à uploader sur Kaggle Datasets.

Contenu :
  - tokenizer_medical_50k/   → tokenizer BPE médical (50K vocab)
  - data/medical_corpus/     → corpus médical (train.txt 63.7M chars, val.txt)

Usage Kaggle :
  1. https://www.kaggle.com/datasets → New Dataset
  2. Uploader ce dossier (zip)
  3. Dans le notebook : copier train_hwat_kaggle.py
     (le script ci-dessous, auto-configuré pour Kaggle)

Fichier notebook minimal à créer (copier-coller) :

```python
# %% [markdown]
# # 🌊 HWAT-Med-125M — Entraînement Kaggle GPU
# 1. Dataset: uploader ce package → kaggle datasets upload
# 2. Accelerator: GPU P100 (2×16GB)

# %% [code]
import math, time, random, os, sys
from pathlib import Path

# ── Chemins Kaggle ──
DATA_ROOT = Path('/kaggle/input')
PKG = None
for p in DATA_ROOT.glob('*'):
    if p.is_dir() and (p / 'tokenizer_medical_50k').exists():
        PKG = p; break
assert PKG, "Package non trouvé — vérifier le nom du dataset"
print(f"📦 Package: {PKG}")

sys.path.insert(0, str(PKG))
os.chdir(PKG)
from train_hwat_kaggle import *
CONFIG.update({
    'train_file': str(PKG / 'data' / 'medical_corpus' / 'train.txt'),
    'val_file': str(PKG / 'data' / 'medical_corpus' / 'val.txt'),
    'tokenizer_path': str(PKG / 'tokenizer_medical_50k' / 'tokenizer.json'),
    'output_dir': '/kaggle/working/checkpoints/hwat_med_125m',
})
main()
```
"""

from pathlib import Path
import shutil

def build_package(target_dir: str = "kaggle_package"):
    """Construit le package Kaggle dans ./kaggle_package"""
    src = Path(__file__).resolve().parent
    dst = Path(target_dir)
    dst.mkdir(parents=True, exist_ok=True)

    # 1. Tokenizer
    print("📦 Copie tokenizer...")
    shutil.copytree(src / "tokenizer_medical_50k",
                    dst / "tokenizer_medical_50k", dirs_exist_ok=True)

    # 2. Corpus
    print("📦 Copie corpus médical...")
    (dst / "data" / "medical_corpus").mkdir(parents=True, exist_ok=True)
    for f in ["train.txt", "val.txt", "corpus_meta.json"]:
        p = src / "data" / "medical_corpus" / f
        if p.exists():
            shutil.copy2(p, dst / "data" / "medical_corpus" / f)

    # 3. Script d'entraînement (auto-configuré Kaggle)
    print("📦 Copie script d'entraînement...")
    shutil.copy2(src / "train_hwat_kaggle.py", dst / "train_hwat_kaggle.py")

    # 4. README
    readme = dst / "README.md"
    readme.write_text(open(__file__, encoding='utf-8').read().split('"""')[1]
                      if '"""' in open(__file__, encoding='utf-8').read() else "HWAT-Med package",
                      encoding='utf-8')

    # 5. Zip
    print("🗜️ Création du zip...")
    zip_name = "hwat_med_kaggle"
    shutil.make_archive(zip_name, 'zip', dst)

    size_mb = sum(f.stat().st_size for f in dst.rglob('*') if f.is_file()) / 1e6
    zip_size = (dst.parent / f"{zip_name}.zip").stat().st_size / 1e6
    print(f"\n✅ Package prêt : {dst}/ ({size_mb:.1f} MB)")
    print(f"   Zip : {zip_name}.zip ({zip_size:.1f} MB)")
    print(f"\n   Instructions :")
    print(f"   1. kaggle.com/datasets → New Dataset → uploader {zip_name}.zip")
    print(f"   2. Créer un notebook → Settings → Accelerator → GPU P100")
    print(f"   3. Ajouter le dataset + copier le script de README.md")
    print(f"   4. Run → checkpoints dans /kaggle/working/")


if __name__ == "__main__":
    build_package()