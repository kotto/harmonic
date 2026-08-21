"""
KA MOBILE — Service de Compression Fantôme
============================================
Pipeline transparent : capture → compression arrière-plan → stockage HCV2.
À la lecture : décompression à la volée sans que l'utilisateur ne s'en rende compte.

Architecture :
  [Capture] → fichier original (JPEG/MP4) → [Worker basse priorité]
    → compression HCV2 Mobile → suppression original → stockage .hcv2
  [Lecture] → interceptor → si .hcv2 → décompression → affichage
  [Vignettes] → stockées en JPEG à côté → instantanées
"""

import os
import sys
import time
import json
import shutil
import threading
import fnmatch
from pathlib import Path
from datetime import datetime, timedelta

# Chemin racine
_PROJECT_ROOT = str(Path(__file__).resolve().parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ka_mobile_compress import KaMobileCompressor

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Dossier surveillé (simule le stockage d'un téléphone)
WATCHED_DIR = os.path.join(_PROJECT_ROOT, 'ka_mobile_media')
# Dossier corbeille (originaux conservés 7 jours avant suppression définitive)
TRASH_DIR = os.path.join(_PROJECT_ROOT, 'ka_mobile_trash')
# Dossier thumbnails
THUMBS_DIR = os.path.join(_PROJECT_ROOT, 'ka_mobile_thumbs')
# Fichier de statistiques
STATS_FILE = os.path.join(_PROJECT_ROOT, 'ka_mobile_stats.json')
# Extensions surveillées
IMAGE_EXTS = ('*.jpg', '*.jpeg', '*.png', '*.heic', '*.webp')
VIDEO_EXTS = ('*.mp4', '*.avi', '*.mov', '*.mkv', '*.m4v')
ALL_EXTS = IMAGE_EXTS + VIDEO_EXTS
# Intervalle de polling (secondes)
POLL_INTERVAL = 5
# Conservation en corbeille (jours)
TRASH_RETENTION_DAYS = 7


# ═══════════════════════════════════════════════════════════════════════════════
# MOTEUR DE COMPRESSION FANTÔME
# ═══════════════════════════════════════════════════════════════════════════════

class GhostCompressor:
    """Compresseur fantôme : surveille un dossier et compresse en arrière-plan.

    Utilisation :
        gc = GhostCompressor()
        gc.start()           # lance le thread de fond
        gc.compress_now()    # force une passe immédiate
        gc.stats()           # dict des statistiques
        gc.stop()            # arrête le thread
    """

    def __init__(self, watch_dir=WATCHED_DIR, trash_dir=TRASH_DIR,
                 thumbs_dir=THUMBS_DIR, stats_file=STATS_FILE):
        self.watch_dir = watch_dir
        self.trash_dir = trash_dir
        self.thumbs_dir = thumbs_dir
        self.stats_file = stats_file
        self.compressor = KaMobileCompressor()
        self._thread = None
        self._running = False
        self._lock = threading.Lock()

        # Créer les dossiers si nécessaire
        for d in [watch_dir, trash_dir, thumbs_dir]:
            os.makedirs(d, exist_ok=True)

        # Charger les stats existantes
        self._stats = self._load_stats()

    # ── Démarrage / Arrêt ─────────────────────────────────────────────

    def start(self):
        """Lance le thread de compression fantôme."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True,
                                        name='GhostCompressor')
        self._thread.start()
        print(f'  👻 GhostCompressor actif — surveillance de {self.watch_dir}')

    def stop(self):
        """Arrête le thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
            self._thread = None

    # ── Boucle interne ─────────────────────────────────────────────────

    def _run(self):
        """Boucle de polling : vérifie les nouveaux fichiers toutes les N secondes."""
        while self._running:
            try:
                self._process_pending()
            except Exception as e:
                print(f'  GhostCompressor error: {e}')
            time.sleep(POLL_INTERVAL)

    def _process_pending(self):
        """Trouve et compresse les fichiers non encore traités."""
        processed = 0
        for pattern in ALL_EXTS:
            for filepath in Path(self.watch_dir).rglob(pattern):
                if not filepath.is_file():
                    continue
                if not self._should_process(str(filepath)):
                    continue
                if self._compress_file(str(filepath)):
                    processed += 1
        return processed

    def compress_now(self) -> int:
        """Force une passe de compression immédiate. Retourne le nombre de fichiers traités."""
        return self._process_pending()

    # ── Décision de traitement ─────────────────────────────────────────

    def _should_process(self, filepath: str) -> bool:
        """Vérifie si un fichier doit être compressé (pas déjà fait, pas verrouillé)."""
        relpath = os.path.relpath(filepath, self.watch_dir)
        basename = os.path.basename(filepath)
        ext = basename.rsplit('.', 1)[-1].lower() if '.' in basename else ''
        # Déjà un fichier compressé ?
        if ext in ('hcv2', 'hcvm', 'hhd'):
            return False
        # Déjà tracé dans les stats (via relpath ou legacy basename)
        with self._lock:
            if relpath in self._stats.get('compressed', {}):
                return False
            if basename in self._stats.get('compressed', {}) and relpath != basename:
                # Legacy : relpath différent, on le traite
                pass  # continue
            # Vérifier si un .hcvm correspondant existe déjà (relpath)
            for compressed_ext in ('.hcv2', '.hcvm', '.hhd'):
                if os.path.exists(filepath + compressed_ext):
                    return False
        return True

    # ── Compression d'un fichier ───────────────────────────────────────

    def _compress_file(self, filepath: str) -> bool:
        """Compresse un fichier et met à jour les stats. Retourne True si réussi."""
        relpath = os.path.relpath(filepath, self.watch_dir)
        filename = os.path.basename(filepath)
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        original_size = os.path.getsize(filepath)

        # Lire le fichier
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
        except Exception as e:
            print(f'  Erreur lecture {filename}: {e}')
            return False

        # Compresser
        try:
            video_exts = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'm4v', 'mpeg', 'mpg', 'wmv', 'flv'}
            if ext in video_exts:
                result = self.compressor.compress_video(data, filename)
            else:
                result = self.compressor.compress_image(data)
        except Exception as e:
            print(f'  Erreur compression {filename}: {e}')
            return False

        if 'error' in result:
            print(f'  Erreur compression {filename}: {result["error"]}')
            return False

        blob = result.get('blob', b'')
        compressed_size = len(blob)
        if compressed_size == 0:
            return False

        # Extension du fichier compressé
        compressed_ext = '.hcv2' if ext in video_exts else '.hcvm'
        compressed_path = filepath + compressed_ext
        thumb_path = os.path.join(self.thumbs_dir, filename + '.jpg')

        try:
            # Sauver le blob compressé
            with open(compressed_path, 'wb') as f:
                f.write(blob)

            # Générer une vignette JPEG (pour la galerie instantanée)
            self._make_thumbnail(data, ext, thumb_path)

            # Déplacer l'original vers la corbeille
            trash_path = os.path.join(self.trash_dir, filename)
            # Si le chemin relatif a des sous-dossiers, on les préserve dans la corbeille
            rel_dir = os.path.dirname(relpath)
            if rel_dir:
                trash_sub = os.path.join(self.trash_dir, rel_dir)
                os.makedirs(trash_sub, exist_ok=True)
                trash_path = os.path.join(trash_sub, filename)
            shutil.move(filepath, trash_path)

            # Mettre à jour les stats
            with self._lock:
                self._stats['compressed'][relpath] = {
                    'original_size': original_size,
                    'compressed_size': compressed_size,
                    'ratio': round(original_size / max(compressed_size, 1), 1),
                    'psnr': str(result.get('psnr', '?')),
                    'ssim': str(result.get('ssim', '?')),
                    'format': result.get('format', '?'),
                    'timestamp': datetime.now().isoformat(),
                }
                self._stats['total_original_bytes'] += original_size
                self._stats['total_compressed_bytes'] += compressed_size
                self._stats['files_count'] += 1
                self._save_stats()

            return True

        except Exception as e:
            print(f'  Erreur sauvegarde {filename}: {e}')
            return False

    # ── Vignette ───────────────────────────────────────────────────────

    def _make_thumbnail(self, data: bytes, ext: str, thumb_path: str, size: int = 320):
        """Génère une vignette JPEG à partir de l'original."""
        try:
            from PIL import Image
            import io

            if ext in ('mp4', 'avi', 'mov', 'mkv', 'webm', 'm4v'):
                # Pour les vidéos : extraire la première frame via OpenCV
                import cv2, tempfile, numpy as np
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{ext}')
                tmp.write(data)
                tmp.close()
                cap = cv2.VideoCapture(tmp.name)
                ret, frame = cap.read()
                cap.release()
                os.unlink(tmp.name)
                if ret:
                    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    thumb = Image.fromarray(img)
                else:
                    thumb = Image.new('RGB', (size, size), (30, 30, 30))
            else:
                thumb = Image.open(io.BytesIO(data)).convert('RGB')

            thumb.thumbnail((size, size), Image.LANCZOS)
            thumb.save(thumb_path, 'JPEG', quality=80)
        except Exception:
            # Vignette par défaut si échec
            try:
                from PIL import Image
                thumb = Image.new('RGB', (size, size), (50, 50, 60))
                thumb.save(thumb_path, 'JPEG', quality=60)
            except Exception:
                pass

    # ── Statistiques ───────────────────────────────────────────────────

    def _load_stats(self) -> dict:
        """Charge les stats depuis le fichier JSON."""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            'compressed': {},
            'total_original_bytes': 0,
            'total_compressed_bytes': 0,
            'files_count': 0,
            'first_run': datetime.now().isoformat(),
            'last_run': None,
        }

    def _save_stats(self):
        """Sauve les stats dans le fichier JSON."""
        self._stats['last_run'] = datetime.now().isoformat()
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self._stats, f, indent=2)
        except Exception:
            pass

    def stats(self) -> dict:
        """Retourne les statistiques actuelles."""
        with self._lock:
            s = dict(self._stats)
            s['watch_dir'] = self.watch_dir
            s['watched_patterns'] = list(ALL_EXTS)
            s['free_space_gb'] = self._free_space_gb()
            s['projection'] = self._projection()
            return s

    def _free_space_gb(self) -> float:
        """Espace libre dans le dossier surveillé (Go)."""
        try:
            usage = shutil.disk_usage(self.watch_dir)
            return round(usage.free / (1024**3), 1)
        except Exception:
            return 0

    def _projection(self) -> dict:
        """Projection du nombre de fichiers qu'on pourrait encore stocker."""
        s = self._stats
        if s['files_count'] == 0 or s['total_original_bytes'] == 0:
            return {'photos': '—', 'videos': '—', 'estimated_gb': '—'}

        avg_ratio = round(s['total_original_bytes'] / max(s['total_compressed_bytes'], 1), 1)
        free_bytes = self._free_space_gb() * (1024**3)
        # Estimer la capacité en photos (moyenne 5 Mo)
        avg_photo_original = 5 * 1024 * 1024  # 5 MB
        avg_photo_compressed = avg_photo_original / avg_ratio
        photos_fit = int(free_bytes / avg_photo_compressed) if avg_photo_compressed > 0 else 0
        return {
            'avg_ratio': avg_ratio,
            'photos_can_fit': photos_fit,
            'estimated_gb': round(free_bytes / (1024**3), 1),
        }

    # ── Nettoyage corbeille ────────────────────────────────────────────

    def clean_trash(self):
        """Supprime les fichiers en corbeille de plus de TRASH_RETENTION_DAYS jours."""
        now = time.time()
        cutoff = now - (TRASH_RETENTION_DAYS * 86400)
        for f in os.listdir(self.trash_dir):
            filepath = os.path.join(self.trash_dir, f)
            if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff:
                try:
                    os.unlink(filepath)
                except Exception:
                    pass

    def restore_file(self, filename: str) -> bool:
        """Restaure un fichier depuis la corbeille vers le dossier surveillé.
        `filename` peut être un chemin relatif (ex: DCIM/Camera/photo_001.jpg)."""
        src = os.path.join(self.trash_dir, filename)
        dst = os.path.join(self.watch_dir, filename)
        if os.path.exists(src) and not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            return True
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON GLOBAL
# ═══════════════════════════════════════════════════════════════════════════════

_ghost = None


def get_ghost() -> GhostCompressor:
    global _ghost
    if _ghost is None:
        _ghost = GhostCompressor()
    return _ghost


def start_ghost():
    g = get_ghost()
    g.start()
    return g


# ═══════════════════════════════════════════════════════════════════════════════
# AUTO-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print('╔' + '═' * 70 + '╗')
    print('║  KA MOBILE — GhostCompressor (Service de Compression Fantôme)')
    print('╚' + '═' * 70 + '╝')
    print()

    gc = GhostCompressor()

    # Créer des fichiers de démo
    demo_dir = os.path.join(gc.watch_dir, 'DCIM', 'Camera')
    os.makedirs(demo_dir, exist_ok=True)

    print(f'  Dossier surveillé : {gc.watch_dir}')
    print(f'  Dossier corbeille : {gc.trash_dir}')
    print(f'  Intervalle polling : {POLL_INTERVAL}s')
    print()

    # Créer quelques images de démo
    try:
        import numpy as np
        from PIL import Image
        for i in range(3):
            img = np.random.randint(0, 255, (400, 300, 3), dtype=np.uint8)
            Image.fromarray(img).save(os.path.join(demo_dir, f'photo_{i}.jpg'), 'JPEG', quality=90)
        print('  ✓ 3 photos de démonstration créées')
    except Exception:
        pass

    # Lancer une passe de compression
    print('  Lancement de la compression fantôme...')
    gc.compress_now()
    print()

    s = gc.stats()
    print(f'  Fichiers compressés : {s["files_count"]}')
    print(f'  Économie : {s["total_original_bytes"]//1024//1024} Mo → {s["total_compressed_bytes"]//1024//1024} Mo')
    if s['files_count'] > 0:
        avg_r = s['total_original_bytes'] / max(s['total_compressed_bytes'], 1)
        print(f'  Ratio moyen : {avg_r:.1f}×')
    print(f'  Projection photos restantes : {s["projection"]["photos_can_fit"]}')
    print()
    print('  👻 GhostCompressor prêt. Démarre avec start_ghost()')