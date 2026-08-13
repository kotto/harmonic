#!/usr/bin/env python3
"""
DaVinci Resolve Script — HCV2 Pro Import/Export
=================================================
Intègre le format .hcv2 dans DaVinci Resolve.

Installation :
  Copier ce fichier dans :
    Mac   : /Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/
    Win   : %PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Fusion\Scripts\
    Linux : /opt/resolve/Fusion/Scripts/

  Le script apparaît dans : Workspace → Scripts → hcv2_resolve.py

Usage :
  - Import .hcv2 : ouvre un fichier .hcv2 et l'importe dans la timeline
  - Export .hcv2 : exporte le clip courant au format .hcv2
  - Batch .hcv2  : convertit une sélection de plans en .hcv2
"""

import sys, os, subprocess, tempfile, json
from pathlib import Path

# Chimères pour Resolve (importé via le menu Scripts)
try:
    import DaVinciResolveScript as dvr
    resolve = dvr.scriptapp("Resolve")
    fusion = resolve.Fusion()
    ui = fusion.UIManager
except ImportError:
    # Mode test (hors Resolve)
    resolve = None
    fusion = None
    ui = None

# Chemin du décodeur HCV2
HCV2_DIR = Path(__file__).resolve().parent.parent.parent / "multimodal"
DECODER = HCV2_DIR / "hcv2_av"
if not DECODER.exists():
    DECODER = HCV2_DIR / "hcv2_av.exe"  # Windows


def get_current_project():
    """Retourne le projet Resolve courant."""
    if not resolve:
        return None
    return resolve.GetProjectManager().GetCurrentProject()


def get_current_timeline():
    """Retourne la timeline courante."""
    project = get_current_project()
    if not project:
        return None
    return project.GetCurrentTimeline()


def import_hcv2(filepath):
    """Importe un fichier .hcv2 dans la timeline."""
    if not os.path.exists(filepath):
        return False, "Fichier introuvable"
    
    # Décoder en PPM temporaire
    ppm_path = tempfile.mktemp(suffix='.ppm')
    try:
        result = subprocess.run(
            [str(DECODER), filepath, ppm_path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return False, f"Erreur décodeur : {result.stderr}"
        
        # Importer dans Resolve via MediaPool
        project = get_current_project()
        if not project:
            return False, "Aucun projet ouvert"
        
        media_pool = project.GetMediaPool()
        timeline = get_current_timeline()
        
        # Ajouter à la médiathèque
        media_item = media_pool.ImportMedia([ppm_path])
        if not media_item:
            return False, "Erreur import Resolve"
        
        # Ajouter à la timeline
        if timeline:
            timeline.InsertFrames(media_item[0], 0)
        
        return True, f"Importé : {os.path.basename(filepath)}"
    
    except Exception as e:
        return False, str(e)
    finally:
        if os.path.exists(ppm_path):
            os.unlink(ppm_path)


def export_hcv2(clip_path, output_path=None):
    """Exporte un clip au format .hcv2."""
    if not output_path:
        output_path = str(Path(clip_path).with_suffix('.hcv2'))
    
    # Utiliser le codec Python pour encoder
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
        import numpy as np
        from PIL import Image
        from multimodal.harmonic_codec import HarmonicCodec
        from multimodal.harmonic_database import HarmonicDatabase
        
        img = np.array(Image.open(clip_path).convert('RGB'))
        hc = HarmonicCodec(HarmonicDatabase(patch_size=32, K=8, stride=32),
                           use_hcv=True, quality=100)
        
        data, mode = hc.encode_select(img, min_psnr=20.0)
        with open(output_path, 'wb') as f:
            f.write(data)
        
        raw = img.nbytes
        ratio = raw / len(data)
        return True, f"Exporté : {ratio:.1f}× ({mode})"
    
    except Exception as e:
        return False, str(e)


def batch_convert(clip_list, output_dir):
    """Convertit une liste de clips en .hcv2."""
    results = []
    for clip in clip_list:
        output = Path(output_dir) / f"{Path(clip).stem}.hcv2"
        success, msg = export_hcv2(clip, str(output))
        results.append({'file': clip, 'success': success, 'msg': msg})
    return results


# ─── Interface utilisateur Resolve ───────────────────────────────────

def show_ui(action):
    """Affiche une boîte de dialogue Resolve."""
    if not ui:
        print("Interface Resolve non disponible (mode test)")
        return None
    
    if action == 'import':
        dlg = ui.FileDialog()
        dlg.title = "Importer un fichier .hcv2"
        dlg.filters = "Fichiers HCV2 (*.hcv2);;Tous (*.*)"
        if dlg.ShowModal():
            return dlg.GetSelectedFile()
        return None
    
    elif action == 'export':
        dlg = ui.FileDialog()
        dlg.title = "Exporter au format .hcv2"
        dlg.filters = "Fichiers HCV2 (*.hcv2)"
        dlg.defaultName = "export.hcv2"
        if dlg.ShowModal():
            return dlg.GetSelectedFile()
        return None


def main():
    """Point d'entrée du script Resolve."""
    if len(sys.argv) > 1:
        # Mode CLI
        action = sys.argv[1]
        if action == 'import' and len(sys.argv) > 2:
            success, msg = import_hcv2(sys.argv[2])
            print(msg)
            return 0 if success else 1
        
        elif action == 'export' and len(sys.argv) > 2:
            output = sys.argv[3] if len(sys.argv) > 3 else None
            success, msg = export_hcv2(sys.argv[2], output)
            print(msg)
            return 0 if success else 1
        
        elif action == 'batch':
            output_dir = sys.argv[3] if len(sys.argv) > 3 else '.'
            clips = [sys.argv[2]] if len(sys.argv) > 2 else []
            results = batch_convert(clips, output_dir)
            print(json.dumps(results, indent=2))
            return 0
    
    else:
        # Mode Resolve (interface graphique)
        if not resolve:
            print("❌ Ce script doit être exécuté depuis DaVinci Resolve")
            print("   Workspace → Scripts → hcv2_resolve.py")
            return 1
        
        # Menu
        choices = ["📥 Importer .hcv2", "📤 Exporter .hcv2", "📦 Batch .hcv2"]
        result = ui.AskUser("HCV2 Pro", choices)
        
        if result == 0:
            path = show_ui('import')
            if path:
                success, msg = import_hcv2(path)
                ui.Alert("Import HCV2", msg)
        
        elif result == 1:
            # Exporter le clip courant
            timeline = get_current_timeline()
            if timeline:
                clip = timeline.GetCurrentVideoItem()
                if clip:
                    clip_path = clip.GetClipProperty("File Path")
                    output = show_ui('export')
                    if output:
                        success, msg = export_hcv2(clip_path, output)
                        ui.Alert("Export HCV2", msg)
                else:
                    ui.Alert("Export HCV2", "Aucun clip sélectionné")
            else:
                ui.Alert("Export HCV2", "Aucune timeline ouverte")
        
        elif result == 2:
            output_dir = ui.FileDialog("Sélectionner le dossier de sortie")
            if output_dir:
                # Batch : traiter tous les clips de la timeline
                timeline = get_current_timeline()
                if timeline:
                    clips = []
                    for i in range(timeline.GetItemCountInTrack("video", 1)):
                        clip = timeline.GetItemListInTrack("video", 1)[i]
                        clip_path = clip.GetClipProperty("File Path")
                        if clip_path:
                            clips.append(clip_path)
                    results = batch_convert(clips, output_dir)
                    success = sum(1 for r in results if r['success'])
                    ui.Alert("Batch HCV2", f"{success}/{len(results)} clips exportés")


if __name__ == '__main__':
    main()