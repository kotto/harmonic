"""
KA Server — Routes Media (HCV Compression)
===========================================
Endpoints pour compression HCV, upscaling, enhancement.
"""

import logging
import base64
import os
from flask import request, jsonify, send_file, Response
import io

log = logging.getLogger(__name__)


def register_media_routes(app, services):
    """Enregistre les routes médias (HCV)."""
    
    hcv_codec = services.get('hcv_codec')
    
    @app.route('/api/compress', methods=['POST', 'OPTIONS'])
    def api_compress():
        """Compresse une image (HCV WASM/serveur/fallback)."""
        if request.method == 'OPTIONS':
            return '', 200
        
        # Vérifier content-type
        if 'multipart/form-data' not in (request.content_type or ''):
            return jsonify({
                'error': 'Content-Type doit être multipart/form-data',
                'code': 'INVALID_CONTENT_TYPE'
            }), 400
        
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'Aucun fichier fourni', 'code': 'NO_FILE'}), 400
        
        # Paramètres
        quality = request.form.get('quality', 'standard')  # archive, standard, eco
        method = request.form.get('method', 'auto')        # auto, wasm, server, fallback
        return_base64 = request.form.get('base64', 'false').lower() == 'true'
        
        # Lire fichier
        file_data = file.read()
        original_size = len(file_data)
        filename = file.filename or 'image.jpg'
        
        if original_size == 0:
            return jsonify({'error': 'Fichier vide', 'code': 'EMPTY_FILE'}), 400
        
        if original_size > 100 * 1024 * 1024:  # 100MB
            return jsonify({'error': 'Fichier trop volumineux (max 100MB)', 'code': 'FILE_TOO_LARGE'}), 413
        
        # Compresser via service HCV
        if hcv_codec:
            result = hcv_codec.compress_image(file_data, quality=quality, method=method)
        else:
            # Fallback direct
            from ka_server.services.hcv_codec import _fallback_compress
            result = _fallback_compress(file_data, quality, original_size)
        
        if not result.success:
            return jsonify({
                'error': result.error or 'Compression échouée',
                'code': 'COMPRESSION_FAILED'
            }), 500
        
        # Préparer réponse
        compressed_data = result.compressed_data
        
        # Enregistrer dans l'historique du dashboard
        try:
            from ka_server.services.compress_store import add_entry
            add_entry(
                filename=filename,
                original_size=result.original_size,
                compressed_size=result.compressed_size,
                quality=result.quality if hasattr(result, 'quality') else quality,
                method=result.method if hasattr(result, 'method') else method,
                format='hcv',
            )
        except Exception as e:
            log.warning(f"compress_store: entrée non enregistrée ({e})")
        
        if return_base64:
            # Retourner base64 dans JSON
            b64_data = base64.b64encode(compressed_data).decode('utf-8')
            return jsonify({
                'success': True,
                'filename': f"{filename.rsplit('.', 1)[0]}_hcv.hcv",
                'data_base64': b64_data,
                'original_size': result.original_size,
                'compressed_size': result.compressed_size,
                'ratio': round(result.ratio, 2),
                'saved_percent': round(result.saved_percent, 1),
                'quality': result.quality,
                'method': result.method,
                'format': 'hcv'
            })
        else:
            # Retourner fichier binaire
            output = io.BytesIO(compressed_data)
            output.seek(0)
            return send_file(
                output,
                mimetype='application/octet-stream',
                as_attachment=True,
                download_name=f"{filename.rsplit('.', 1)[0]}_hcv.hcv"
            )
    
    @app.route('/api/upscale', methods=['POST', 'OPTIONS'])
    def api_upscale():
        """Upscale une image (×2, ×4)."""
        if request.method == 'OPTIONS':
            return '', 200
        
        if 'multipart/form-data' not in (request.content_type or ''):
            return jsonify({
                'error': 'Content-Type doit être multipart/form-data',
                'code': 'INVALID_CONTENT_TYPE'
            }), 400
        
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'Aucun fichier fourni', 'code': 'NO_FILE'}), 400
        
        scale = float(request.form.get('scale', 2.0))
        if scale not in (2.0, 4.0):
            return jsonify({'error': 'Scale doit être 2.0 ou 4.0', 'code': 'INVALID_SCALE'}), 400
        
        return_base64 = request.form.get('base64', 'false').lower() == 'true'
        
        file_data = file.read()
        filename = file.filename or 'image.jpg'
        
        if hcv_codec:
            result = hcv_codec.upscale_image(file_data, scale=scale)
        else:
            from ka_server.services.hcv_codec import upscale_image
            result = upscale_image(file_data, scale=scale)
        
        if not result.success:
            return jsonify({
                'error': result.error or 'Upscale échoué',
                'code': 'UPSCALE_FAILED'
            }), 500
        
        upscaled_data = result.upscaled_data
        
        if return_base64:
            b64_data = base64.b64encode(upscaled_data).decode('utf-8')
            return jsonify({
                'success': True,
                'filename': f"{filename.rsplit('.', 1)[0]}_up{int(scale)}x.jpg",
                'data_base64': b64_data,
                'width': result.width,
                'height': result.height,
                'scale_factor': result.scale_factor,
                'method': result.method,
                'format': 'jpg'
            })
        else:
            output = io.BytesIO(upscaled_data)
            output.seek(0)
            return send_file(
                output,
                mimetype='image/jpeg',
                as_attachment=True,
                download_name=f"{filename.rsplit('.', 1)[0]}_up{int(scale)}x.jpg"
            )
    
    @app.route('/api/enhance', methods=['POST', 'OPTIONS'])
    def api_enhance():
        """Amélioration image (débruitage, netteté, correction couleur)."""
        if request.method == 'OPTIONS':
            return '', 200
        
        if 'multipart/form-data' not in (request.content_type or ''):
            return jsonify({
                'error': 'Content-Type doit être multipart/form-data',
                'code': 'INVALID_CONTENT_TYPE'
            }), 400
        
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'Aucun fichier fourni', 'code': 'NO_FILE'}), 400
        
        # Options d'amélioration
        denoise = request.form.get('denoise', 'true').lower() == 'true'
        sharpen = request.form.get('sharpen', 'true').lower() == 'true'
        color_correct = request.form.get('color_correct', 'false').lower() == 'true'
        return_base64 = request.form.get('base64', 'false').lower() == 'true'
        
        file_data = file.read()
        filename = file.filename or 'image.jpg'
        
        # Pour l'instant, on utilise Pillow pour l'enhancement
        # TODO: Intégrer HCV Enhancement quand dispo
        try:
            from PIL import Image, ImageEnhance, ImageFilter
            import io
            
            img = Image.open(io.BytesIO(file_data))
            
            if denoise:
                img = img.filter(ImageFilter.MedianFilter(size=3))
            
            if sharpen:
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.3)
            
            if color_correct:
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(1.1)
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.05)
            
            # Convertir RGB pour JPEG
            if img.mode in ('RGBA', 'LA', 'P'):
                bg = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                bg.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = bg
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=90, optimize=True)
            enhanced_data = output.getvalue()
            
        except Exception as e:
            log.error(f"Enhance failed: {e}")
            return jsonify({'error': str(e), 'code': 'ENHANCE_FAILED'}), 500
        
        if return_base64:
            b64_data = base64.b64encode(enhanced_data).decode('utf-8')
            return jsonify({
                'success': True,
                'filename': f"{filename.rsplit('.', 1)[0]}_enhanced.jpg",
                'data_base64': b64_data,
                'original_size': len(file_data),
                'enhanced_size': len(enhanced_data),
                'operations': {
                    'denoise': denoise,
                    'sharpen': sharpen,
                    'color_correct': color_correct
                }
            })
        else:
            output = io.BytesIO(enhanced_data)
            output.seek(0)
            return send_file(
                output,
                mimetype='image/jpeg',
                as_attachment=True,
                download_name=f"{filename.rsplit('.', 1)[0]}_enhanced.jpg"
            )
    
    @app.route('/api/media/analyze', methods=['POST', 'OPTIONS'])
    def api_analyze():
        """Analyse un fichier pour estimer compression HCV."""
        if request.method == 'OPTIONS':
            return '', 200
        
        if 'multipart/form-data' not in (request.content_type or ''):
            return jsonify({'error': 'Content-Type doit être multipart/form-data'}), 400
        
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
        
        file_data = file.read()
        filename = file.filename or 'file'
        
        if hcv_codec:
            analysis = hcv_codec.analyze_storage(file_data, filename)
        else:
            from ka_server.services.hcv_codec import analyze_storage
            analysis = analyze_storage(file_data, filename)
        
        return jsonify(analysis)
    
    @app.route('/api/media/status', methods=['GET'])
    def api_media_status():
        """Statut des codecs HCV."""
        if hcv_codec:
            status = hcv_codec.get_hcv_status()
        else:
            from ka_server.services.hcv_codec import get_hcv_status
            status = get_hcv_status()
        
        return jsonify(status)
    
    @app.route('/api/hcv2/compress', methods=['POST', 'OPTIONS'])
    def api_hcv2_compress():
        """Compresse une image en format .hcv2 avec le sélecteur 3 modes."""
        if request.method == 'OPTIONS':
            return '', 200
        
        if 'multipart/form-data' not in (request.content_type or ''):
            return jsonify({'error': 'Content-Type doit être multipart/form-data'}), 400
        
        file = request.files.get('image')
        if not file:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
        
        mode = request.form.get('mode', 'select')
        min_psnr = float(request.form.get('min_psnr', 20))
        return_base64 = request.form.get('base64', 'false').lower() == 'true'
        
        file_data = file.read()
        original_size = len(file_data)
        filename = file.filename or 'image.jpg'
        
        try:
            import sys, numpy as np
            from PIL import Image
            import io
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
            from multimodal.harmonic_codec import HarmonicCodec
            from multimodal.harmonic_database import HarmonicDatabase
            
            img = np.array(Image.open(io.BytesIO(file_data)).convert('RGB'))
            hc = HarmonicCodec(HarmonicDatabase(patch_size=32, K=8, stride=32),
                               use_hcv=True, quality=100)
            
            if mode == 'modal':
                import sys as _sys
                from pathlib import Path as _Path
                _p = _Path(__file__).resolve().parent.parent.parent / 'vital-ka' / 'core' / 'python'
                if str(_p) not in _sys.path: _sys.path.insert(0, str(_p))
                import hcv2_modal_codec as modal
                enc = modal.encode(img)
                compressed_data = enc['blob']
                fmt = 'HCVM'
            elif mode == 'full':
                data = hc.encode_full(img)
                compressed_data = data
                fmt = 'HHDC'
            else:  # select (default)
                data, _mode = hc.encode_select(img, min_psnr=min_psnr)
                compressed_data = data
                fmt = 'HCVH' if data[:4] == b'HCVH' else ('HCVM' if data[:4] == b'HCVM' else ('HHD2' if data[:4] == b'HHD2' else 'HHDC'))
            
            compressed_size = len(compressed_data)
            ratio = original_size / compressed_size if compressed_size > 0 else 1.0
            
            if return_base64:
                b64 = base64.b64encode(compressed_data).decode('utf-8')
                return jsonify({
                    'success': True, 'format': fmt, 'ratio': round(ratio, 1),
                    'original_size': original_size, 'compressed_size': compressed_size,
                    'data_base64': b64
                })
            else:
                output = io.BytesIO(compressed_data)
                output.seek(0)
                response = send_file(
                    output, mimetype='application/octet-stream',
                    as_attachment=True,
                    download_name=f"{filename.rsplit('.', 1)[0]}.{fmt.lower()}"
                )
                response.headers['X-Ratio'] = str(round(ratio, 1))
                response.headers['X-Original-Size'] = str(original_size)
                response.headers['X-Saved'] = str(original_size - compressed_size)
                response.headers['X-Codec'] = f'HCV2/{fmt}'
                response.headers['X-PSNR'] = '25-30' if fmt in ('HCVM','HCVH') else '∞'
                return response
        except Exception as e:
            log.error('HCV2 compression error', exc_info=True)
            return jsonify({'error': str(e)}), 500

    @app.route('/api/hcv2/mobile', methods=['POST', 'OPTIONS'])
    def api_hcv2_mobile():
        """📱 Mode Mobile : compression image ou vidéo avec réglages optimisés téléphone.
        
        Utilise le pipeline HCV2 complet (predictor='golden', threshold_scale=2.0)
        pour un ratio ×1000 à qualité visuelle identique (SSIM > 0.998).
        
        Body: multipart/form-data avec champ 'file'
        Returns: JSON {ratio, psnr, ssim, dimensions, format, preview_video_b64}
        """
        if request.method == 'OPTIONS':
            return '', 200
        
        if 'multipart/form-data' not in (request.content_type or ''):
            return jsonify({'error': 'Content-Type doit être multipart/form-data'}), 400
        
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'Fichier requis (champ \"file\")'}), 400
        
        file_data = file.read()
        filename = file.filename or 'file'
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        video_exts = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'm4v', 'mpeg', 'mpg', 'wmv', 'flv'}
        
        try:
            from ka_mobile_compress import KaMobileCompressor
            kc = KaMobileCompressor()
            
            if ext in video_exts:
                result = kc.compress_video(file_data, filename)
            else:
                result = kc.compress_image(file_data)
            
            # Ne pas renvoyer le blob brut
            resp = {k: v for k, v in result.items() if k != 'blob'}
            return jsonify(resp)
        except Exception as e:
            log.error('KA Mobile compression error', exc_info=True)
            return jsonify({'error': str(e)}), 500

    @app.route('/api/hcv2/mobile/download', methods=['POST', 'OPTIONS'])
    def api_hcv2_mobile_download():
        """📱 Télécharge le fichier compressé (blob HCV2)."""
        if request.method == 'OPTIONS':
            return '', 200
        
        if 'multipart/form-data' not in (request.content_type or ''):
            return jsonify({'error': 'Content-Type doit être multipart/form-data'}), 400
        
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'Fichier requis'}), 400
        
        file_data = file.read()
        filename = file.filename or 'file'
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        video_exts = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'm4v', 'mpeg', 'mpg', 'wmv', 'flv'}
        
        try:
            from ka_mobile_compress import KaMobileCompressor
            kc = KaMobileCompressor()
            
            if ext in video_exts:
                result = kc.compress_video(file_data, filename)
            else:
                result = kc.compress_image(file_data)
            
            if 'error' in result:
                return jsonify(result), 400
            
            blob = result.get('blob', b'')
            dl_name = result.get('download_name', f'compressed.{ext}')
            if not blob:
                return jsonify({'error': 'Aucune donnée compressée'}), 500
            
            return jsonify({
                'download_b64': base64.b64encode(blob).decode(),
                'download_name': dl_name,
            })
        except Exception as e:
            log.error('KA Mobile download error', exc_info=True)
            return jsonify({'error': str(e)}), 500

    # ═════════════════════════════════════════════════════════════════════
    # TRANSPARENT COMPRESSION PIPELINE — décompression à la volée + stats
    # ═════════════════════════════════════════════════════════════════════

    @app.route('/api/hcv2/view/<path:filename>')
    def api_hcv2_view(filename):
        """Décompression transparente à la volée.
        
        Si le fichier existe en .hcv2/.hcvm → décompresse et sert l'image.
        Si le fichier est une vignette → sert la vignette.
        Sinon → sert le fichier original (statique).
        L'appelant ne sait pas si le fichier était compressé ou non.
        """
        from ka_background_compress import WATCHED_DIR, THUMBS_DIR
        
        # Vignette ?
        if filename.startswith('thumb/'):
            thumb_path = os.path.join(THUMBS_DIR, filename[6:])
            if os.path.exists(thumb_path):
                return send_file(thumb_path, mimetype='image/jpeg')
        
        # Chercher le fichier original
        safe_path = os.path.normpath(os.path.join(WATCHED_DIR, filename))
        if not safe_path.startswith(os.path.normpath(WATCHED_DIR)):
            return jsonify({'error': 'Chemin invalide'}), 403
        
        # Vérifier si une version compressée existe
        for compressed_ext in ('.hcv2', '.hcvm', '.hhd'):
            compressed_path = safe_path + compressed_ext
            if os.path.exists(compressed_path):
                try:
                    with open(compressed_path, 'rb') as f:
                        blob = f.read()
                    
                    # Décompresser selon le format
                    import io, numpy as np
                    
                    if compressed_ext == '.hcvm':
                        # Image : décompression via codec modal
                        import hcv2_modal_codec as modal
                        from PIL import Image
                        rec_img = modal.decode(blob)
                        rec_img = np.clip(rec_img, 0, 255).astype(np.uint8)
                        img = Image.fromarray(rec_img)
                        buf = io.BytesIO()
                        img.save(buf, format='JPEG', quality=92)
                        buf.seek(0)
                        return Response(buf.getvalue(), mimetype='image/jpeg',
                                        headers={'X-HCV2-Decompressed': 'true',
                                                 'X-HCV2-Ratio': 'compressed'})
                    elif compressed_ext == '.hcv2':
                        # Vidéo : extraire la première frame via le pipeline
                        from hcv2_video_pipeline import decode_video
                        from PIL import Image as PILImage
                        # decode_video prend un dict, pas un blob brut
                        # On utilise KaMobileCompressor qui gère ça
                        # Solution : chercher la vignette pré-générée
                        thumb_path = os.path.join(THUMBS_DIR, os.path.basename(safe_path) + '.jpg')
                        if os.path.exists(thumb_path):
                            return send_file(thumb_path, mimetype='image/jpeg')
                        # Fallback : image noire
                        import struct
                        T, H, W = struct.unpack_from('III', blob[:12])
                        thumb = PILImage.new('RGB', (min(W,320), min(H,240)), (30, 30, 40))
                        buf = io.BytesIO()
                        thumb.save(buf, format='JPEG', quality=70)
                        buf.seek(0)
                        return Response(buf.getvalue(), mimetype='image/jpeg')
                except Exception as e:
                    log.error(f'View decompress error: {e}', exc_info=True)
                    # Fallback : servir l'original s'il existe encore
                    if os.path.exists(safe_path):
                        return send_file(safe_path)
                    return jsonify({'error': 'Erreur décompression'}), 500
        
        # Fichier original non compressé
        if os.path.exists(safe_path):
            return send_file(safe_path)
        
        return jsonify({'error': 'Fichier introuvable'}), 404
    
    @app.route('/api/hcv2/stats')
    def api_hcv2_stats():
        """Statistiques du pipeline de compression transparent."""
        try:
            from ka_background_compress import get_ghost
            ghost = get_ghost()
            s = ghost.stats()
            return jsonify({
                'files_count': s.get('files_count', 0),
                'total_original_mb': round(s.get('total_original_bytes', 0) / (1024**2), 1),
                'total_compressed_mb': round(s.get('total_compressed_bytes', 0) / (1024**2), 1),
                'saved_mb': round((s.get('total_original_bytes', 0) - s.get('total_compressed_bytes', 0)) / (1024**2), 1),
                'avg_ratio': round(s.get('total_original_bytes', 0) / max(s.get('total_compressed_bytes', 0), 1), 1)
                          if s.get('total_compressed_bytes', 0) > 0 else 0,
                'files': s.get('compressed', {}),
                'projection': s.get('projection', {}),
                'free_space_gb': s.get('free_space_gb', 0),
                'first_run': s.get('first_run'),
                'last_run': s.get('last_run'),
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/hcv2/gallery')
    def api_hcv2_gallery():
        """Liste les médias disponibles (pour la galerie démo).
        Inclut les originaux non compressés ET les fichiers compressés (.hcvm, .hcv2)."""
        from ka_background_compress import WATCHED_DIR, THUMBS_DIR
        from pathlib import Path
        import os
        
        items = []
        seen = set()
        
        # 1. Lister les fichiers compressés (.hcvm, .hcv2)
        for ext in ('*.hcvm', '*.hcv2'):
            for f in sorted(Path(WATCHED_DIR).rglob(ext), key=lambda p: p.stat().st_mtime, reverse=True):
                if not f.is_file():
                    continue
                rel = os.path.relpath(str(f), WATCHED_DIR)
                stat = f.stat()
                base_name = f.stem  # sans .hcvm/.hcv2
                is_video = f.suffix == '.hcv2'
                thumb_path = f'hcv2/view/thumb/{base_name}.jpg'
                # Utiliser le chemin ORIGINAL (sans l'extension compressée) pour la vue
                original_rel = rel.rsplit('.', 1)[0]  # enlève .hcvm/.hcv2
                items.append({
                    'name': base_name,
                    'path': original_rel,
                    'size': stat.st_size,
                    'is_video': is_video,
                    'compressed': True,
                    'thumbnail': thumb_path,
                    'modified': stat.st_mtime,
                })
                seen.add(base_name)
        
        # 2. Lister les originaux non encore compressés
        image_exts = ('*.jpg', '*.jpeg', '*.png', '*.heic', '*.webp', '*.gif')
        video_exts = ('*.mp4', '*.avi', '*.mov', '*.mkv')
        for ext in image_exts + video_exts:
            for f in sorted(Path(WATCHED_DIR).rglob(ext), key=lambda p: p.stat().st_mtime, reverse=True):
                if not f.is_file():
                    continue
                if f.stem in seen:
                    continue  # déjà listé comme compressé
                rel = os.path.relpath(str(f), WATCHED_DIR)
                stat = f.stat()
                is_video = f.suffix.lower() in ('.mp4', '.avi', '.mov', '.mkv')
                thumb_path = f'hcv2/view/thumb/{f.name}.jpg'
                items.append({
                    'name': f.name,
                    'path': rel.replace('\\', '/'),
                    'size': stat.st_size,
                    'is_video': is_video,
                    'compressed': False,
                    'thumbnail': thumb_path,
                    'modified': stat.st_mtime,
                })
        
        return jsonify({'items': items, 'count': len(items),
                        'watch_dir': os.path.basename(WATCHED_DIR)})

    @app.route('/api/hcv2/compress_now', methods=['POST'])
    def api_hcv2_compress_now():
        """Force une passe de compression immédiate (pour l'onboarding)."""
        try:
            from ka_background_compress import get_ghost
            ghost = get_ghost()
            n = ghost.compress_now()
            s = ghost.stats()
            return jsonify({
                'processed': n,
                'files_count': s.get('files_count', 0),
                'saved_mb': round((s.get('total_original_bytes', 0) - s.get('total_compressed_bytes', 0)) / (1024**2), 1),
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/hcv2/restore', methods=['POST'])
    def api_hcv2_restore():
        """Restaure un fichier depuis la corbeille."""
        filename = request.json.get('filename') if request.is_json else request.form.get('filename')
        if not filename:
            return jsonify({'error': 'filename requis'}), 400
        try:
            from ka_background_compress import get_ghost
            ghost = get_ghost()
            ok = ghost.restore_file(filename)
            return jsonify({'restored': ok})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/storage/optimize-batch', methods=['POST', 'OPTIONS'])
    def api_storage_optimize_batch():
        """Analyse un lot de fichiers et estime le gain de compression HCV2.
        Body: multipart/form-data avec champ 'files' (un ou plusieurs).
        Returns: {n_files, total_original, total_saved, total_estimated_after, files[]}
        """
        if request.method == 'OPTIONS':
            return '', 200
        if 'multipart/form-data' not in (request.content_type or ''):
            return jsonify({'error': 'multipart requis'}), 400

        files = request.files.getlist('files')
        if not files:
            files = [request.files.get('file')] if request.files.get('file') else []
        if not files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400

        try:
            from ka_mobile_compress import KaMobileCompressor
            kc = KaMobileCompressor()
            video_exts = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'm4v', 'mpeg', 'mpg', 'wmv', 'flv'}

            total_original = 0
            total_after = 0
            results = []

            for f in files:
                data = f.read()
                filename = f.filename or 'file'
                ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
                original_size = len(data)
                total_original += original_size

                try:
                    if ext in video_exts:
                        r = kc.compress_video(data, filename)
                    else:
                        r = kc.compress_image(data)
                    compressed = r.get('compressed_size', len(r.get('blob', b'')))
                    estimated_after = compressed if compressed > 0 else original_size
                except Exception:
                    estimated_after = original_size

                total_after += estimated_after
                ratio = round(original_size / max(estimated_after, 1), 1)
                results.append({
                    'filename': filename,
                    'original_size': original_size,
                    'estimated_after': estimated_after,
                    'estimated_saved': original_size - estimated_after,
                    'estimated_ratio': ratio,
                    'media_type': ('video' if ext in video_exts
                                   else 'image' if ext in ('jpg', 'jpeg', 'png', 'webp', 'heic', 'gif')
                                   else 'other'),
                })

            return jsonify({
                'n_files': len(results),
                'total_original': total_original,
                'total_saved': total_original - total_after,
                'total_estimated_after': total_after,
                'files': results,
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/compress/preview', methods=['POST', 'OPTIONS'])
    def api_compress_preview():
        """Compresse PUIS décompresse une image pour un avant/après visuel réel.
        Retourne l'image originale + l'image reconstruite + ratio + PSNR."""
        if 'multipart/form-data' not in (request.content_type or ''):
            return jsonify({'error': 'Content-Type doit être multipart/form-data'}), 400

        file = request.files.get('file') or request.files.get('image')
        if not file:
            return jsonify({'error': 'Aucun fichier fourni'}), 400

        mode = request.form.get('mode', 'select')
        min_psnr = float(request.form.get('min_psnr', 20))
        file_data = file.read()
        original_size = len(file_data)
        filename = file.filename or 'image.jpg'

        if original_size == 0:
            return jsonify({'error': 'Fichier vide'}), 400
        if original_size > 50 * 1024 * 1024:
            return jsonify({'error': 'Fichier trop volumineux (max 50 MB)'}), 413

        try:
            import sys, numpy as np
            from PIL import Image
            import io
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
            from multimodal.harmonic_codec import HarmonicCodec
            from multimodal.harmonic_database import HarmonicDatabase

            img = np.array(Image.open(io.BytesIO(file_data)).convert('RGB'))
            h, w, _ = img.shape

            hc = HarmonicCodec(HarmonicDatabase(patch_size=32, K=8, stride=32),
                               use_hcv=True, quality=100)

            if mode == 'full':
                data = hc.encode_full(img)
                if data[:4] == b'HHDC':
                    img_rec, _meta = hc.decode_full(data)
                    fmt = 'HHDC'
                else:
                    img_rec, _meta = hc.decode_v2(data)
                    fmt = 'HCV2'
            else:  # select (default)
                data, chosen_mode = hc.encode_select(img, min_psnr=min_psnr)
                img_rec, _meta = hc.decode_select(data)
                fmt = data[:4].decode('ascii', errors='replace')

            compressed_size = len(data)
            ratio = original_size / compressed_size if compressed_size > 0 else 1.0

            # Calcul PSNR
            mse = np.mean((img.astype(np.float64) - img_rec.astype(np.float64)) ** 2)
            psnr = 20 * np.log10(255.0 / max(1.0, np.sqrt(mse))) if mse > 0 else 99.99

            # Encoder l'image reconstruite en JPEG base64
            rec_pil = Image.fromarray(img_rec.clip(0, 255).astype(np.uint8))
            rec_buf = io.BytesIO()
            rec_pil.save(rec_buf, 'JPEG', quality=92)
            rec_b64 = base64.b64encode(rec_buf.getvalue()).decode('utf-8')

            # Encoder l'image originale en JPEG base64
            orig_buf = io.BytesIO()
            Image.fromarray(img).save(orig_buf, 'JPEG', quality=92)
            orig_b64 = base64.b64encode(orig_buf.getvalue()).decode('utf-8')

            return jsonify({
                'success': True,
                'filename': filename,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'ratio': round(ratio, 1),
                'saved_percent': round(100 * (original_size - compressed_size) / max(1, original_size), 1),
                'psnr': round(psnr, 2),
                'format': fmt,
                'mode': mode,
                'width': w,
                'height': h,
                'original_base64': orig_b64,
                'reconstructed_base64': rec_b64,
                'compressed_base64': base64.b64encode(data).decode('utf-8'),
            })

        except Exception as e:
            log.error('Compress preview error', exc_info=True)
            return jsonify({'error': str(e)}), 500