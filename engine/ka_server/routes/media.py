"""
KA Server — Routes Media (HCV Compression)
===========================================
Endpoints pour compression HCV, upscaling, enhancement.
"""

import logging
import base64
from flask import request, jsonify, send_file
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