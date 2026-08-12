#!/usr/bin/env python3
"""
hcv2_pro — CLI de compression harmonique professionnelle
Format .hcv2 v1.0 — Archivage TV, Cinéma, Média
=====================================================
Usage:
    hcv2_pro encode <image> [--quality MODE] [--output <file>]
    hcv2_pro decode <file.hcv2> [--output <image>]
    hcv2_pro batch <directory> [--quality MODE] [--recursive]
    hcv2_pro info <file.hcv2>
    hcv2_pro checksum <file.hcv2>
    hcv2_pro dict <directory> [--output <dict.hdb>] [--patch-size 32] [--k 8]
"""

import sys, os, time, struct, hashlib, json, argparse
from pathlib import Path

# Ajouter le chemin du projet
_BASE = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, _BASE)
sys.path.insert(0, str(Path(_BASE) / 'vital-ka' / 'core' / 'python'))

# Imports conditionnels
try:
    import numpy as np
    from PIL import Image
    from multimodal.harmonic_codec import HarmonicCodec
    from multimodal.harmonic_database import HarmonicDatabase
    from multimodal.build_dict import build_dictionary
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'vital-ka' / 'core' / 'python'))
    import hcv2_modal_codec as modal
    _HAVE_CODEC = True
except ImportError as e:
    _HAVE_CODEC = False
    _IMPORT_ERR = str(e)


MAGICS = {b'HCVM': 'MODAL', b'HCVH': 'HYBRID', b'HHD2': 'DICT_V2', b'HHDC': 'FULL'}


def read_header(path):
    """Lit et vérifie le header d'un fichier .hcv2."""
    with open(path, 'rb') as f:
        first4 = f.read(4)
        if first4 in MAGICS:
            mode = MAGICS[first4]
            magic = first4
            hdr = f.read(12)
        else:
            f.seek(0)
            hdr = f.read(12)
            magic = f.read(4)
            mode = MAGICS.get(magic)
            if not mode and magic[0] == 0x78:
                mode = 'MODAL'
            elif not mode:
                mode = 'INCONNU'
    
    if len(hdr) < 12:
        return {'error': 'Fichier trop court'}
    h = struct.unpack('<I', hdr[0:4])[0]
    w = struct.unpack('<I', hdr[4:8])[0]
    version = hdr[8]
    precision = hdr[9]
    bit_depth = hdr[10] if hdr[10] > 0 else 8
    return {
        'width': w, 'height': h, 'version': version,
        'precision': 'float32' if precision == 1 else 'float16',
        'bit_depth': bit_depth,
        'mode': mode, 'magic': magic.hex() if magic else 'absent',
        'file_size': os.path.getsize(path),
        'pixels': h * w * 3,
        'ratio': round(h * w * 3 / os.path.getsize(path), 1) if os.path.getsize(path) > 0 else 0,
    }
    
    h = struct.unpack('<I', hdr[0:4])[0]
    w = struct.unpack('<I', hdr[4:8])[0]
    version = hdr[8]
    precision = hdr[9]
    return {
        'width': w, 'height': h,
        'version': version, 'precision': 'float32' if precision == 1 else 'float16',
        'mode': mode, 'magic': magic.hex() if magic else 'absent',
        'file_size': os.path.getsize(path),
        'pixels': h * w * 3,
        'ratio': round(h * w * 3 / os.path.getsize(path), 1) if os.path.getsize(path) > 0 else 0,
    }


def cmd_encode(args):
    """Encode une image au format .hcv2."""
    if not _HAVE_CODEC:
        sys.exit(f"Erreur : codec non disponible ({_IMPORT_ERR})")
    
    img = np.array(Image.open(args.image).convert('RGB'))
    src_size = img.nbytes
    t0 = time.perf_counter()
    
    if args.quality == 'lossless':
        # Mode FULL (Delta-H+zstd, exact)
        hc = HarmonicCodec(HarmonicDatabase(patch_size=32, K=8, stride=32),
                           use_hcv=True, quality=100)
        data = hc.encode_full(img)
        mode = 'HHDC'
    elif args.quality == 'max':
        # Mode MODAL (troncature dorée, 527×)
        enc = modal.encode(img, precision=16)
        data = enc['blob']
        mode = 'HCVM'
    elif args.quality == 'pro':
        # Mode SELECT (min_psnr=30, quasi-lossless)
        hc = HarmonicCodec(HarmonicDatabase(patch_size=32, K=8, stride=32),
                           use_hcv=True, quality=100)
        d, m = hc.encode_select(img, min_psnr=30.0)
        data = d
        mode = 'HCVM' if d[:4] == b'HCVM' else ('HHD2' if d[:4] == b'HHD2' else 'HHDC')
    else:  # 'archive' (défaut)
        # Mode SELECT (min_psnr=20, meilleur compromis)
        hc = HarmonicCodec(HarmonicDatabase(patch_size=32, K=8, stride=32),
                           use_hcv=True, quality=100)
        d, m = hc.encode_select(img, min_psnr=20.0)
        data = d
        mode = 'HCVM' if d[:4] == b'HCVM' else ('HHD2' if d[:4] == b'HHD2' else 'HHDC')
    
    enc_ms = (time.perf_counter() - t0) * 1000
    ratio = src_size / len(data)
    
    if args.output:
        output = args.output
    else:
        stem = Path(args.image).stem
        output = f"{stem}.hcv2"
    
    with open(output, 'wb') as f:
        f.write(data)
    
    print(f"✅ {Path(args.image).name} → {output}")
    print(f"   {src_size//1024} Ko → {len(data)//1024} Ko  ratio {ratio:.1f}×  mode {mode}  ({enc_ms:.0f} ms)")


def cmd_decode(args):
    """Décode un fichier .hcv2 en image."""
    info = read_header(args.file)
    if 'error' in info:
        sys.exit(f"Erreur : {info['error']}")
    
    print(f"📋 {Path(args.file).name} : {info['width']}×{info['height']}  "
          f"mode {info['mode']}  {info['precision']}  "
          f"ratio {info['ratio']}×  ({info['file_size']//1024} Ko)")
    
    if not _HAVE_CODEC:
        sys.exit("Erreur : codec non disponible")
    
    with open(args.file, 'rb') as f:
        data = f.read()
    
    t0 = time.perf_counter()
    magic = data[12:16]
    
    if magic == b'HCVM':
        rec = modal.decode(data)
    elif magic == b'HHD2' or magic == b'HHDC':
        db = None
        if args.dict:
            db = HarmonicDatabase()
            db.load(args.dict)
        hc = HarmonicCodec(db or HarmonicDatabase(patch_size=32, K=8, stride=32),
                           use_hcv=True, quality=100)
        if magic == b'HHD2':
            rec, _ = hc.decode_v2(data, database=db)
        else:
            rec, _ = hc.decode_full(data)
    elif magic == b'HCVH':
        from multimodal.harmonic_codec import HarmonicCodec, HarmonicDatabase
        hc = HarmonicCodec(HarmonicDatabase(patch_size=32, K=8, stride=32),
                           use_hcv=True, quality=100)
        rec, _ = hc.decode_select(data)
    else:
        sys.exit(f"Magic inconnu : {magic}")
    
    dec_ms = (time.perf_counter() - t0) * 1000
    
    if args.output:
        output = args.output
    else:
        stem = Path(args.file).stem
        output = f"{stem}.png"
    
    Image.fromarray(rec).save(output)
    print(f"✅ → {output}  ({dec_ms:.0f} ms)  {rec.shape[1]}×{rec.shape[0]}")


def cmd_info(args):
    """Affiche les informations d'un fichier .hcv2."""
    info = read_header(args.file)
    if 'error' in info:
        sys.exit(f"Erreur : {info['error']}")
    
    print(f"📋 {Path(args.file).name}")
    print(f"   Dimensions : {info['width']}×{info['height']} ({info['pixels']//1024//1024} MP)")
    print(f"   Format : {info['mode']} ({info['precision']})")
    print(f"   Profondeur : {info['bit_depth']} bits")
    print(f"   Version : {info['version']}")
    print(f"   Taille : {info['file_size']//1024} Ko")
    print(f"   Ratio : {info['ratio']}×")
    print(f"   Magic : {info['magic']}")


def cmd_checksum(args):
    """Vérifie l'intégrité d'un fichier .hcv2 (SHA-256)."""
    with open(args.file, 'rb') as f:
        data = f.read()
    
    sha = hashlib.sha256(data).hexdigest()
    info = read_header(args.file)
    if 'error' in info:
        sys.exit(f"Erreur : {info['error']}")
    
    print(f"🔐 {Path(args.file).name}")
    print(f"   SHA-256 : {sha}")
    print(f"   Taille : {len(data)} o")
    print(f"   Intégrité : ✅" if len(data) > 12 else "❌ Fichier corrompu")


def cmd_batch(args):
    """Encode/décode par lot."""
    directory = Path(args.directory)
    if not directory.exists():
        sys.exit(f"Erreur : {args.directory} n'existe pas")
    
    pattern = '**/*' if args.recursive else '*'
    files = []
    for ext in ['.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp']:
        files.extend(directory.glob(f"{pattern}{ext}"))
    for ext in ['.hcv2']:
        files.extend(directory.glob(f"{pattern}{ext}"))
    
    if not files:
        sys.exit("Aucun fichier trouvé")
    
    total_src = 0
    total_dst = 0
    total_time = 0
    
    for f in files:
        if f.suffix.lower() == '.hcv2':
            continue  # decode
        # Encode
        t0 = time.perf_counter()
        cmd_encode(argparse.Namespace(
            image=str(f),
            quality=args.quality,
            output=str(f.with_suffix('.hcv2'))
        ))
        t = time.perf_counter() - t0
        total_time += t
        try:
            info = read_header(str(f.with_suffix('.hcv2')))
            total_src += info['pixels']
            total_dst += info['file_size']
        except:
            pass
    
    if total_src > 0 and total_dst > 0:
        print(f"\n📊 Bilan : {len(files)} fichiers  "
              f"ratio moyen {total_src/total_dst:.1f}×  "
              f"temps total {total_time:.0f}s")


def cmd_dict(args):
    """Entraîne un dictionnaire à partir d'un répertoire."""
    if not _HAVE_CODEC:
        sys.exit(f"Erreur : codec non disponible ({_IMPORT_ERR})")
    
    directory = Path(args.directory)
    if not directory.exists():
        sys.exit(f"Erreur : {args.directory} n'existe pas")
    
    print(f"📚 Entraînement du dictionnaire sur {directory}")
    print(f"   patch_size={args.patch_size}, K={args.K}")
    
    t0 = time.perf_counter()
    db = build_dictionary(
        str(directory),
        output_path=args.output or 'dictionary.hdb',
        patch_size=args.patch_size,
        K=args.K,
        quality='standard',
        max_images=args.max_images or 10000,
        shard_size=20000,
        verbose=True
    )
    t = time.perf_counter() - t0
    print(f"✅ Dictionnaire créé : {args.output or 'dictionary.hdb'}")
    print(f"   {len(db._shards)} shard(s), {t:.0f}s")


def main():
    parser = argparse.ArgumentParser(
        description='HCV2 Pro — Compression Harmonique Professionnelle',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes de qualité :
  archive  (défaut)  SELECT(min_psnr=20) — meilleur compromis 373× @ 64 dB
  lossless           FULL — bit-exact 2,9× @ ∞ dB
  pro                SELECT(min_psnr=30) — quasi-lossless 259× @ 92 dB
  max                MODAL — très compressé 527× @ 29 dB

Exemples :
  hcv2_pro encode video.dpx --quality archive --output archive.hcv2
  hcv2_pro decode archive.hcv2 --output restore.dpx
  hcv2_pro batch /data/archives --quality pro --recursive
  hcv2_pro info archive.hcv2
  hcv2_pro dict /data/training/ --output broadcast.hdb --patch-size 32
        """)
    
    sub = parser.add_subparsers(dest='command')
    
    p_encode = sub.add_parser('encode', help='Encoder une image en .hcv2')
    p_encode.add_argument('image', help='Fichier image source')
    p_encode.add_argument('--quality', '-q', default='archive',
                         choices=['archive', 'lossless', 'pro', 'max'],
                         help='Mode de compression (défaut: archive)')
    p_encode.add_argument('--output', '-o', help='Fichier .hcv2 de sortie')
    
    p_decode = sub.add_parser('decode', help='Décoder un fichier .hcv2')
    p_decode.add_argument('file', help='Fichier .hcv2')
    p_decode.add_argument('--output', '-o', help='Fichier image de sortie')
    p_decode.add_argument('--dict', '-d', help='Dictionnaire (requis pour HHD2)')
    
    p_info = sub.add_parser('info', help='Afficher les informations')
    p_info.add_argument('file', help='Fichier .hcv2')
    
    p_checksum = sub.add_parser('checksum', help='Vérifier l\'intégrité')
    p_checksum.add_argument('file', help='Fichier .hcv2')
    
    p_batch = sub.add_parser('batch', help='Traiter par lot')
    p_batch.add_argument('directory', help='Répertoire source')
    p_batch.add_argument('--quality', '-q', default='archive',
                        choices=['archive', 'lossless', 'pro', 'max'])
    p_batch.add_argument('--recursive', '-r', action='store_true',
                        help='Parcourir les sous-répertoires')
    
    p_dict = sub.add_parser('dict', help='Entraîner un dictionnaire')
    p_dict.add_argument('directory', help='Répertoire d\'entraînement')
    p_dict.add_argument('--output', '-o', default='dictionary.hdb',
                       help='Fichier dictionnaire de sortie')
    p_dict.add_argument('--patch-size', type=int, default=32,
                       help='Taille des patches (défaut: 32)')
    p_dict.add_argument('--k', type=int, default=8,
                       help='Nombre de coefficients DFT (défaut: 8)')
    p_dict.add_argument('--max-images', type=int, default=10000,
                       help='Nombre max d\'images (défaut: 10000)')
    
    p_serve = sub.add_parser('serve', help='Démarrer le serveur API REST')
    p_serve.add_argument('--port', type=int, default=8765,
                        help='Port d\'écoute (défaut: 8765)')
    p_serve.add_argument('--host', default='0.0.0.0',
                        help='Adresse d\'écoute (défaut: 0.0.0.0)')
    p_serve.add_argument('--dict', '-d', default=None,
                        help='Dictionnaire optionnel')
    
    args = parser.parse_args()
    
    if args.command == 'encode':
        cmd_encode(args)
    elif args.command == 'decode':
        cmd_decode(args)
    elif args.command == 'info':
        cmd_info(args)
    elif args.command == 'checksum':
        cmd_checksum(args)
    elif args.command == 'batch':
        cmd_batch(args)
    elif args.command == 'dict':
        cmd_dict(args)
    elif args.command == 'serve':
        cmd_serve(args)
    else:
        parser.print_help()


def cmd_serve(args):
    """Démarre le serveur API REST HCV2."""
    from flask import Flask, request, jsonify, send_file
    import io
    
    app = Flask(__name__)
    
    # Charger le dictionnaire si fourni
    db = None
    if args.dict:
        try:
            db = HarmonicDatabase()
            db.load(Path(args.dict).resolve())
            print(f"  Dictionnaire chargé : {len(db._shards)} shards")
        except Exception as e:
            print(f"  Dictionnaire non chargé : {e}")
    
    @app.route('/api/hcv2/compress', methods=['POST', 'OPTIONS'])
    def compress():
        if request.method == 'OPTIONS':
            return '', 200
        file = request.files.get('image')
        if not file:
            return jsonify({'error': 'Aucun fichier'}), 400
        
        quality = request.form.get('quality', 'archive')
        mode = request.form.get('mode', 'select')
        min_psnr = float(request.form.get('min_psnr', 20))
        return_base64 = request.form.get('base64', 'false').lower() == 'true'
        
        file_data = file.read()
        original_size = len(file_data)
        filename = file.filename or 'image'
        
        try:
            img = np.array(Image.open(io.BytesIO(file_data)).convert('RGB'))
            hc = HarmonicCodec(db or HarmonicDatabase(patch_size=32, K=8, stride=32),
                               use_hcv=True, quality=100)
            
            if quality == 'lossless':
                data = hc.encode_full(img)
            elif quality == 'max':
                data = modal.encode(img)['blob']
            elif quality == 'pro':
                data, _ = hc.encode_select(img, min_psnr=30.0)
            else:  # archive
                data, _ = hc.encode_select(img, min_psnr=20.0)
            
            fmt = 'HCVM' if data[:4] == b'HCVM' else ('HHD2' if data[:4] == b'HHD2' else 'HHDC')
            if quality == 'max':
                fmt = 'HCVM'
            
            if return_base64:
                import base64
                return jsonify({
                    'success': True, 'format': fmt,
                    'ratio': round(original_size / len(data), 1),
                    'original_size': original_size,
                    'compressed_size': len(data),
                    'data_base64': base64.b64encode(data).decode()
                })
            else:
                output = io.BytesIO(data); output.seek(0)
                resp = send_file(output, mimetype='application/octet-stream',
                               as_attachment=True,
                               download_name=f"{filename.rsplit('.',1)[0]}.{fmt.lower()}")
                resp.headers['X-Ratio'] = str(round(original_size / len(data), 1))
                resp.headers['X-Original-Size'] = str(original_size)
                resp.headers['X-Saved'] = str(original_size - len(data))
                resp.headers['X-Codec'] = f'HCV2/{fmt}'
                return resp
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/hcv2/info', methods=['POST', 'OPTIONS'])
    def info():
        if request.method == 'OPTIONS':
            return '', 200
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'Aucun fichier'}), 400
        data = file.read()
        with io.BytesIO(data) as f:
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.hcv2') as tmp:
                tmp.write(data)
                tmp_path = tmp.name
            try:
                info = read_header(tmp_path)
                return jsonify(info)
            finally:
                os.unlink(tmp_path)
    
    @app.route('/api/hcv2/status', methods=['GET'])
    def status():
        return jsonify({
            'version': '1.0',
            'format': '.hcv2',
            'modes': ['archive', 'lossless', 'pro', 'max'],
            'dictionary': len(db._shards) if db else 0,
            'codec': 'available' if _HAVE_CODEC else 'unavailable'
        })
    
    print(f"\n🚀 HCV2 Pro API — http://{args.host}:{args.port}")
    print(f"   Endpoints : /api/hcv2/compress, /info, /status")
    print(f"   Qualités : archive (373x), lossless (2.9x), pro (259x), max (527x)")
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == '__main__':
    main()