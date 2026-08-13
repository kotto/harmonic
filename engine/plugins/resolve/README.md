# HCV2 Pro — Intégration DaVinci Resolve

## Installation

### 1. Script Python (rapide, recommandé)

1. Copier `hcv2_resolve.py` dans le dossier Scripts de DaVinci Resolve :

   | Plateforme | Dossier |
   |---|---|
   | **Windows** | `%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Fusion\Scripts\` |
   | **macOS** | `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/` |
   | **Linux** | `/opt/resolve/Fusion/Scripts/` |

2. Dans Resolve : **Workspace → Scripts → hcv2_resolve.py**

3. Le script offre 3 actions :
   - **📥 Importer .hcv2** : ouvre un fichier .hcv2 et l'ajoute à la timeline
   - **📤 Exporter .hcv2** : exporte le clip courant en .hcv2
   - **📦 Batch .hcv2** : convertit tous les plans de la timeline

### 2. Plugin OpenFX (avancé)

Le plugin OFX (`hcv2_ofx.c`) s'intègre comme un node dans Fusion/Color :

```
📦 HCV2Decoder.ofx.bundle
├── Contents/
│   ├── Linux-x86_64/HCV2Decoder.ofx
│   ├── MacOS/HCV2Decoder.ofx
│   └── Windows-x86_64/HCV2Decoder.ofx
```

Dossier d'installation :
| Plateforme | Dossier |
|---|---|
| **Windows** | `%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Fusion\Plugins\` |
| **macOS** | `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Plugins/` |
| **Linux** | `~/.local/share/DaVinciResolve/Fusion/Plugins/` |

## Usage dans Resolve

### Workflow d'import (décompresser .hcv2 → projet)

```
1. Fichier source .hcv2 (213×)
        ↓
2. Workspace → Scripts → hcv2_resolve.py → 📥 Importer
        ↓
3. Le fichier est décodé en PPM temporaire
        ↓
4. Importé dans la médiathèque Resolve
        ↓
5. Ajouté à la timeline
```

### Workflow d'export (projet → .hcv2)

```
1. Clip sélectionné dans la timeline
        ↓
2. Workspace → Scripts → hcv2_resolve.py → 📤 Exporter
        ↓
3. Encodé en .hcv2 (sélecteur 3 modes, min_psnr=20)
        ↓
4. Fichier .hcv2 sauvegardé (70 Ko pour 12 MP)
```

## Commandes CLI

```bash
# Import
python hcv2_resolve.py import archive.hcv2

# Export
python hcv2_resolve.py export frame.dpx -o frame.hcv2

# Batch
python hcv2_resolve.py batch /chemin/frames/ /sortie/
```

## Prérequis

- DaVinci Resolve **18+** (scripts) ou **Studio 18+** (OpenFX)
- Le décodeur `hcv2_av` compilé (voir `plugins/BUILD.md`)
- Python 3.8+ pour le script

## Dépannage

| Problème | Solution |
|---|---|
| Script absent du menu | Vérifier le dossier Scripts, redémarrer Resolve |
| Erreur décodeur | Vérifier que `hcv2_av` est compilé dans `engine/plugins/` |
| OpenFX invisible | Vérifier le bundle, redémarrer, Resolve Studio requis |
| PPM temporaire | Supprimé après import (fonctionne sans résidu) |
