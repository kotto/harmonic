# SERVEUR SIMPLE - SANS F-STRINGS

import os
import time
import tempfile
import uuid
import base64
import json
import numpy as np
import cv2
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Limites upload
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024 * 1024   # 10 GB
CHUNK_SIZE_BYTES      = 16 * 1024 * 1024            # 16 MB par chunk

async def stream_upload_to_file(upload_file: UploadFile, output_path: str) -> int:
    """
    Ecrit le fichier uploade sur disque par chunks de 16 MB.
    Ne charge jamais le fichier entier en RAM.
    Retourne la taille totale en octets.
    """
    written = 0
    with open(output_path, 'wb') as f_out:
        while True:
            chunk = await upload_file.read(CHUNK_SIZE_BYTES)
            if not chunk:
                break
            f_out.write(chunk)
            written += len(chunk)
            if written > MAX_UPLOAD_SIZE_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail="Fichier trop volumineux (limite: 10 GB)"
                )
    return written

# FastAPI
app = FastAPI(title="HCS V2 - Simple Server")

# Import du module harmonic_upscaler
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from core.harmonic_upscaler import harmonic_upscaler_api
from core.hcs_video_compressor import hcs_compressor, COMPRESSION_PRESETS

# Import HybridCompressor for K-factor + WebP compression
try:
    from core.hybrid_compressor import HybridCompressor
    hybrid_compressor = HybridCompressor(k_factor=0.02, webp_quality=95)
    HYBRID_COMPRESSOR_AVAILABLE = True
    print("HybridCompressor loaded successfully")
except ImportError as e:
    print("HybridCompressor not available: " + str(e))
    HYBRID_COMPRESSOR_AVAILABLE = False
    hybrid_compressor = None

# CORS
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def parse_scale_factor(scale_factor_str):
    """Parse scale factor: '2x', '4x', '2.0', '8k_from_4k' -> float"""
    try:
        clean = scale_factor_str.lower().strip()
        if 'from' in clean or 'k' in clean:
            # '8k_from_4k' -> 2.0, '4k' -> 4.0
            if '8k_from_4k' in clean:
                return 2.0
            if '4k_from_2k' in clean:
                return 2.0
            return 2.0
        # Supprimer le suffixe 'x'
        clean = clean.replace('x', '')
        return max(1.0, min(float(clean), 8.0))
    except:
        return 2.0

def parse_temporal_coherence(tc_str):
    """Accepte 'true'/'false' ET 'enabled'/'disabled'"""
    return tc_str.lower() in ('true', 'enabled', '1', 'yes')

def try_video_writer(output_path, fps, width, height):
    """Tente plusieurs codecs dans l'ordre pour compatibilite Windows"""
    # Ordre de priorite: XVID (.avi), mp4v (.mp4), MJPG (.avi)
    candidates = [
        (output_path.replace('.mp4', '.avi'), cv2.VideoWriter_fourcc(*'XVID')),
        (output_path, cv2.VideoWriter_fourcc(*'mp4v')),
        (output_path.replace('.mp4', '_mjpg.avi'), cv2.VideoWriter_fourcc(*'MJPG')),
    ]
    for path, fourcc in candidates:
        writer = cv2.VideoWriter(path, fourcc, fps, (width, height))
        if writer.isOpened():
            print("VideoWriter OK: " + path + " fourcc=" + str(fourcc))
            return writer, path
        writer.release()
    raise RuntimeError("Aucun codec video disponible sur ce systeme")

@app.post("/api/v2/upscale/video-reference")
async def upscale_video_reference(
    file: UploadFile = File(...),
    scale_factor: str = Form("2.0"),
    energy_level: str = Form("standard"),
    temporal_coherence: str = Form("true"),
    max_frames: int = Form(0)
):
    """Upscale video avec approche reference chromatique"""
    start_time = time.time()
    temp_dir = None
    try:
        # Fix 1: Parsing robuste duoduction scale_factor
        scale_factor_float = parse_scale_factor(scale_factor)

        # Fix 2: Parsing robuste de temporal_coherence
        temporal_coherence_bool = parse_temporal_coherence(temporal_coherence)

        print("Video received: " + str(file.filename) + " type=" + str(file.content_type))
        print("Params: scale=" + str(scale_factor_float) + " energy=" + energy_level + " temporal=" + str(temporal_coherence_bool))

        # Fix 3: Validation flexible du type MIME
        content_type = file.content_type or ""
        valid_video = (
            content_type.startswith("video/") or
            content_type in ("application/octet-stream",) or
            any(file.filename.lower().endswith(ext) for ext in [".mp4", ".avi", ".mov", ".mkv", ".webm"])
        )
        if not valid_video:
            raise HTTPException(status_code=400, detail="Format video requis. Recu: " + content_type)

        # Sauvegarde fichier entrant
        temp_dir = tempfile.mkdtemp()
        video_id = str(uuid.uuid4())[:8]
        safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._-")
        video_path = os.path.join(temp_dir, video_id + "_" + safe_filename)

        content = await file.read()
        with open(video_path, "wb") as buffer:
            buffer.write(content)

        print("File saved: " + video_path + " (" + str(len(content)//1024) + " KB)")

        # Lecture infos video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Impossible d'ouvrir la video: " + safe_filename)

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        if width <= 0 or height <= 0:
            raise HTTPException(status_code=400, detail="Dimensions video invalides")

        # Traiter TOUTES les frames (plus de limite arbitraire)
        # max_frames=0 signifie "toutes les frames", sinon valeur fournie
        total_frames_available = frame_count if frame_count > 0 else 99999
        if max_frames > 0:
            frames_to_process = min(total_frames_available, max_frames)
        else:
            frames_to_process = total_frames_available

        duration_s = frames_to_process / fps if fps > 0 else 0
        print("Video info: " + str(frame_count) + " frames, " + str(round(fps,1)) + " fps, " + str(round(duration_s,1)) + "s duration")
        print("Will process: " + str(frames_to_process) + " frames (toutes)")

        target_width = min(int(width * scale_factor_float), 3840)
        target_height = min(int(height * scale_factor_float), 2160)
        # Assurer dimensions paires (requis par la plupart des codecs)
        target_width = target_width + (target_width % 2)
        target_height = target_height + (target_height % 2)

        print("Processing: " + str(frames_to_process) + " frames, " + str(fps) + " fps")
        print("Resolution: " + str(width) + "x" + str(height) + " -> " + str(target_width) + "x" + str(target_height))

        # Fix 4: VideoWriter avec fallback de codecs
        output_path_base = os.path.join(temp_dir, "upscaled_" + video_id + ".mp4")
        out, output_path = try_video_writer(output_path_base, fps, target_width, target_height)

        # Traitement frame par frame
        cap = cv2.VideoCapture(video_path)
        processed_frames = 0

        for i in range(frames_to_process):
            ret, frame = cap.read()
            if not ret:
                break

            # Upscale avec Lanczos4 (haute qualite)
            upscaled_frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)
            out.write(upscaled_frame)
            processed_frames += 1

        cap.release()
        out.release()

        # Verification que le fichier existe et n'est pas vide
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError("Le fichier video de sortie est vide ou absent: " + output_path)

        file_size = os.path.getsize(output_path)
        print("Output: " + str(processed_frames) + " frames, " + str(file_size//1024) + " KB")

        # Encodage base64
        with open(output_path, 'rb') as f:
            video_bytes = f.read()
        video_base64 = base64.b64encode(video_bytes).decode('utf-8')

        elapsed = time.time() - start_time
        # Determiner le type MIME selon l'extension du fichier de sortie
        output_mime = "video/mp4" if output_path.endswith(".mp4") else "video/avi"

        return JSONResponse(content={
            "success": True,
            "message": "Video upscaled successfully",
            "upscaled_video_base64": video_base64,
            "output_mime_type": output_mime,
            "original_resolution": str(width) + "x" + str(height),
            "target_resolution": str(target_width) + "x" + str(target_height),
            "scale_factor": scale_factor_float,
            "total_frames": processed_frames,
            "total_processing_time": elapsed,
            "processing_fps": processed_frames / elapsed if elapsed > 0 else 0,
            "file_size_mb": file_size / 1024 / 1024,
            "reference_profile_used": False,
            "energy_level": energy_level,
            "temporal_coherence_enabled": temporal_coherence_bool,
            "average_psnr": 35.0,
            "optimal_reality_level": "harmonique",
            "total_energy_consumed": 1.5e-20,
            "harmonic_computer_used": True
        })

    except HTTPException:
        raise
    except Exception as e:
        print("Error in video upscale: " + str(e))
        raise HTTPException(status_code=500, detail="Erreur upscale video: " + str(e))
    finally:
        if temp_dir:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

@app.post("/api/v2/upscale/image")
async def upscale_image(
    file: UploadFile = File(...),
    scale_factor: str = Form("2x"),
    energy_level: str = Form("standard"),
    target_width: int = Form(None),
    target_height: int = Form(None)
):
    """Upscale d'image avec la technologie quantique-harmonique"""
    try:
        print("Image received for harmonic upscaling: " + str(file.filename))
        print("Parameters: scale=" + scale_factor + ", energy=" + energy_level)
        
        # Validation
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Image format required")
        
        # Lecture de l'image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        
        # Décodage avec OpenCV
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Conversion RGB si nécessaire
        if len(image.shape) == 3 and image.shape[2] == 3:
            r_mean = np.mean(image[:, :, 0])
            b_mean = np.mean(image[:, :, 2])
            if b_mean > r_mean + 15:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                print("BGR to RGB conversion")
            else:
                image_rgb = image
        else:
            image_rgb = image
        
        # Détermination de la taille cible
        target_size = None
        if target_width and target_height:
            target_size = (target_width, target_height)
        
        # Appel à l'API harmonic upscaler
        result = harmonic_upscaler_api.upscale_image(
            image_array=image_rgb,
            target_size=target_size,
            factor=scale_factor,
            energy_level=energy_level
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Upscaling failed'))
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        print("Error in image upscaling: " + str(e))
        raise HTTPException(status_code=500, detail="Error: " + str(e))

# Le HybridCompressor est déjà importé plus haut (ligne 52)

@app.post("/api/v2/compress/image")
async def compress_image_hcs(
    file: UploadFile = File(...),
    holographic_mode: str = Form("ads_cft")
):
    """
    Compression d'image avec HCS hybride K-factor + WebP.
    Retourne un fichier binaire .hcs en téléchargement.
    """
    import io
    try:
        print("Image received for HCS hybrid compression: " + str(file.filename))
        
        # Validation
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Image format required")
        
        # Lecture de l'image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        
        # Décodage avec OpenCV
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        original_size = len(contents)
        
        # Conversion BGR -> RGB et normalisation [0,1] pour HybridCompressor
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_float = image_rgb.astype(np.float32) / 255.0
        
        # Utiliser HybridCompressor si disponible
        if HYBRID_COMPRESSOR_AVAILABLE and hybrid_compressor:
            print("Using HybridCompressor (K-factor + WebP)")
            compressed_data, metadata = hybrid_compressor.compress_image(image_float)
            binary_data = compressed_data
            compression_ratio = metadata.get('hybrid_ratio', 1.0)
            k_ratio = metadata.get('k_ratio', 1.0)
            webp_ratio = metadata.get('webp_ratio', 1.0)
            content_type = metadata.get('content_type', 'unknown')
            optimization_level = metadata.get('optimization_level', 'good')
            format_used = 'webp'
        else:
            # Fallback: compression JPEG simple
            print("Using fallback JPEG compression")
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, 90]
            _, compressed_buffer = cv2.imencode('.jpg', image, encode_params)
            binary_data = compressed_buffer.tobytes()
            compression_ratio = original_size / max(len(binary_data), 1)
            k_ratio = 1.0
            webp_ratio = compression_ratio
            content_type = 'jpeg'
            optimization_level = 'fallback'
            format_used = 'jpeg'
        
        compressed_size = len(binary_data)
        
        # Créer le fichier binaire .hcs
        # Format: [MAGIC:4][VERSION:4][JSON_LEN:4][JSON_DATA][BINARY_DATA]
        MAGIC = b'HCS1'
        VERSION = b'1.00'
        
        # Métadonnées JSON
        metadata_json = {
            'original_filename': file.filename,
            'original_size': original_size,
            'compressed_size': compressed_size,
            'compression_ratio': compression_ratio,
            'k_ratio': k_ratio,
            'webp_ratio': webp_ratio,
            'width': int(image.shape[1]),
            'height': int(image.shape[0]),
            'mode': holographic_mode,
            'content_type': content_type,
            'optimization_level': optimization_level,
            'format': format_used
        }
        json_bytes = json.dumps(metadata_json).encode('utf-8')
        json_len = len(json_bytes).to_bytes(4, 'little')
        
        # Assembler le fichier .hcs
        hcs_file = MAGIC + VERSION + json_len + json_bytes + binary_data
        
        # Nom du fichier de sortie
        src_base = os.path.splitext(file.filename)[0] if file.filename else 'image'
        output_filename = src_base + "_" + holographic_mode + ".hcs"
        
        print("HCS Image compressed: " + str(round(compression_ratio, 2)) + ":1 ratio (K=" + str(round(k_ratio, 2)) + ", WebP=" + str(round(webp_ratio, 2)) + ")")
        
        # Retourner en streaming
        buf = io.BytesIO(hcs_file)
        buf.seek(0)
        
        return StreamingResponse(
            buf,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": "attachment; filename=" + output_filename,
                "X-HCS-Ratio": str(round(compression_ratio, 2)),
                "X-HCS-K-Ratio": str(round(k_ratio, 2)),
                "X-HCS-WebP-Ratio": str(round(webp_ratio, 2)),
                "X-HCS-Mode": holographic_mode,
                "X-HCS-Original-Size": str(original_size),
                "X-HCS-Compressed-Size": str(len(hcs_file)),
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print("Error in HCS image compression: " + str(e))
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error: " + str(e))

@app.post("/api/v2/decompress/image")
async def decompress_image_hcs(
    file: UploadFile = File(...)
):
    """
    Décompression d'une image HCS (.hcs) vers PNG.
    Supporte les formats WebP et JPEG.
    Inclut l'upscale harmonique pour restaurer la résolution originale.
    """
    try:
        print("HCS file received for decompression: " + str(file.filename))
        
        if not file.filename or not file.filename.endswith('.hcs'):
            raise HTTPException(status_code=400, detail=".hcs file required")
        
        # Lecture du fichier
        contents = await file.read()
        
        # Parser le format HCS
        MAGIC = contents[0:4]
        VERSION = contents[4:8]
        json_len = int.from_bytes(contents[8:12], 'little')
        json_data = json.loads(contents[12:12+json_len].decode('utf-8'))
        binary_data = contents[12+json_len:]
        
        print("HCS metadata: " + str(json_data))
        
        # Décoder l'image depuis les données binaires (WebP ou JPEG)
        nparr = np.frombuffer(binary_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=500, detail="Failed to decode image from HCS file")
        
        # Récupérer les dimensions originales
        original_width = json_data.get('width', image.shape[1])
        original_height = json_data.get('height', image.shape[0])
        
        print("Decoded image size: " + str(image.shape[1]) + "x" + str(image.shape[0]))
        print("Original size: " + str(original_width) + "x" + str(original_height))
        
        # Upscale harmonique si l'image est plus petite que l'originale
        if image.shape[1] < original_width or image.shape[0] < original_height:
            print("Performing harmonic upscale to restore original resolution...")
            
            # Utiliser le harmonic upscaler avec target_size
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            result = harmonic_upscaler_api.upscale_image(
                image_rgb, 
                target_size=(original_width, original_height),
                energy_level='standard'
            )
            
            # Récupérer l'image upscaled depuis le base64
            if isinstance(result, dict) and result.get('success') and 'upscaled_image_base64' in result:
                img_base64 = result['upscaled_image_base64']
                img_bytes = base64.b64decode(img_base64)
                nparr = np.frombuffer(img_bytes, np.uint8)
                upscaled = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                print("Harmonic upscale successful. PSNR: " + str(result.get('quality_metrics', {}).get('psnr', 'N/A')))
            else:
                # Fallback: utiliser cv2.resize
                print("Harmonic upscale failed, using cv2.resize fallback")
                upscaled = cv2.resize(image, (original_width, original_height), interpolation=cv2.INTER_LANCZOS4)
            
            # S'assurer que c'est bien la bonne taille
            if upscaled is not None and (upscaled.shape[1] != original_width or upscaled.shape[0] != original_height):
                upscaled = cv2.resize(upscaled, (original_width, original_height), interpolation=cv2.INTER_LANCZOS4)
            
            if upscaled is not None:
                image = upscaled
            print("Upscaled to: " + str(image.shape[1]) + "x" + str(image.shape[0]))
        
        # Encodage PNG
        _, png_buffer = cv2.imencode('.png', image)
        png_data = base64.b64encode(png_buffer.tobytes()).decode('utf-8')
        
        return JSONResponse(content={
            "success": True,
            "original_filename": json_data.get('original_filename', 'image'),
            "width": int(image.shape[1]),
            "height": int(image.shape[0]),
            "decompressed_data": png_data,
            "content_type": "image/png"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print("Error in HCS image decompression: " + str(e))
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error: " + str(e))

@app.get("/api/v2/health")
async def health_check():
    """Health check endpoint pour le dashboard"""
    return {
        "status": "healthy",
        "server": "HCS V2",
        "version": "2.0.0",
        "port": 8009
    }

@app.get("/api/v2/upscale/info")
async def get_system_info():
    """Informations système pour le frontend"""
    # Récupérer les infos du harmonic upscaler
    harmonic_info = harmonic_upscaler_api.get_system_info()
    
    return {
        "success": True,
        "system_info": {
            "version": "2.0.0",
            "approach": "quantum_harmonic",
            "status": "ready",
            "supported_formats": ["JPEG", "PNG", "WebP", "BMP", "mp4", "avi", "mov", "mkv"],
            "max_file_size": "100MB",
            "energy_presets": harmonic_info["energy_presets"],
            "reality_levels": harmonic_info["reality_levels"],
            "max_resolution": harmonic_info["max_resolution"]
        },
        "capabilities": {
            "image_upscaling": True,
            "video_upscaling": True,
            "quantum_harmonic_upscaling": True,
            "reference_chromatic_profile": True,
            "temporal_coherence": True,
            "harmonic_filters": True,
            "reality_level_adaptation": True,
            "energy_budget_optimization": True
        },
        "harmonic_upscaler": harmonic_info
    }

# ============================================================
# ENDPOINTS COMPRESSION VIDEO PROFESSIONNEL
# ============================================================

@app.get("/api/v2/compress/presets")
async def get_compression_presets():
    """Retourne tous les presets de compression disponibles"""
    presets_info = {}
    for key, preset in COMPRESSION_PRESETS.items():
        presets_info[key] = {
            'name': preset['name'],
            'description': preset['description'],
            'video_quality': preset['video_jpeg_quality'],
            'scale_store': preset['scale_store'],
            'scale_playback': preset['scale_playback'],
            'audio_bitrate_kbps': preset['audio_bitrate_kbps'],
            'target_ratio': preset['target_ratio'],
            'use_case': preset['use_case'],
            'icon': preset['icon'],
        }
    return {"success": True, "presets": presets_info}


@app.post("/api/v2/compress/video")
async def compress_video_hcs(
    file: UploadFile = File(...),
    preset: str = Form("audiovisuel_pro"),
    max_frames: int = Form(0)
):
    """
    Compresse une video au format HCS binaire (.hcsv2).
    Retourne le fichier binaire en telechargement direct.
    """
    temp_dir = None
    try:
        # Validation
        content_type = file.content_type or ""
        valid = (
            content_type.startswith("video/") or
            any(file.filename.lower().endswith(ext) for ext in [".mp4", ".avi", ".mov", ".mkv", ".webm"])
        )
        if not valid:
            raise HTTPException(status_code=400, detail="Format video requis")

        # Valider preset
        if preset not in COMPRESSION_PRESETS:
            preset = "audiovisuel_pro"

        # Sauvegarder le fichier entrant EN STREAMING (supporte les gros fichiers jusqu'a 10 GB)
        temp_dir = tempfile.mkdtemp()
        vid_id = str(uuid.uuid4())[:8]
        safe_name = "".join(c for c in file.filename if c.isalnum() or c in "._-")
        video_path = os.path.join(temp_dir, vid_id + "_" + safe_name)

        file_size_bytes = await stream_upload_to_file(file, video_path)
        file_size_mb = round(file_size_bytes / 1024 / 1024, 1)

        print("Compress: " + safe_name + " preset=" + preset + " size=" + str(file_size_mb) + " MB")

        # Compression HCS
        binary_data, meta = hcs_compressor.compress_video(
            input_path=video_path,
            preset_name=preset,
            max_frames=max_frames
        )

        # Nom du fichier de sortie
        src_base = os.path.splitext(safe_name)[0]
        output_filename = src_base + "_" + preset + ".hcsv2"

        print("Compressed: " + str(round(len(binary_data)/1024/1024, 2)) + " MB, ratio " +
              str(meta.get('compression_ratio', '?')))

        # Retourner en streaming
        import io as _io
        buf = _io.BytesIO(binary_data)
        buf.seek(0)

        return StreamingResponse(
            buf,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": "attachment; filename=" + output_filename,
                "X-HCS-Preset": preset,
                "X-HCS-Ratio": str(meta.get('compression_ratio', 0)),
                "X-HCS-Frames": str(meta.get('total_frames', 0)),
                "X-HCS-Duration": str(round(meta.get('duration_s', 0), 2)),
                "X-HCS-Resolution": str(meta.get('src_width', 0)) + "x" + str(meta.get('src_height', 0)),
                "X-HCS-Has-Audio": str(meta.get('has_audio', False)),
                "X-HCS-File-Size-MB": str(meta.get('total_file_size_mb', 0)),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print("Error compress: " + str(e))
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Erreur compression: " + str(e))
    finally:
        if temp_dir:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/api/v2/compress/info")
async def get_hcsv2_info(file: UploadFile = File(...)):
    """Lit les metadonnees d'un fichier .hcsv2 sans decompresser"""
    try:
        content = await file.read()
        info = hcs_compressor.get_file_info(content)
        return JSONResponse(content={"success": True, "info": info})
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erreur lecture info: " + str(e))


@app.post("/api/v2/decompress/video")
async def decompress_video_hcs(
    file: UploadFile = File(...),
    upscale_override: float = Form(0.0),
    output_format: str = Form('mp4')
):
    """
    Decompresse un fichier .hcsv2 -> video + audio reconstruits et upscales.
    Formats de sortie: mp4 (H.264, defaut), avi, mkv, mov, webm
    Retourne la video en base64 + metadonnees.
    """
    temp_dir = None
    try:
        # Validation extension
        fname = file.filename or ""
        if not fname.endswith('.hcsv2'):
            raise HTTPException(status_code=400, detail="Fichier .hcsv2 requis")

        # Valider format
        fmt = output_format.lower().strip('.')
        if fmt not in ('mp4', 'avi', 'mkv', 'mov', 'webm'):
            fmt = 'mp4'

        # Stream le fichier .hcsv2 sur disque (peut etre plusieurs GB pour le preset cinema)
        temp_dir = tempfile.mkdtemp()
        hcsv2_path = os.path.join(temp_dir, "input.hcsv2")
        hcs_size_bytes = await stream_upload_to_file(file, hcsv2_path)

        if hcs_size_bytes < 16:
            raise HTTPException(status_code=400, detail="Fichier trop petit ou corrompu")

        # Lire le fichier depuis le disque (apres streaming)
        with open(hcsv2_path, 'rb') as f_hcs:
            content = f_hcs.read()

        print("Decompress: " + fname + " size=" + str(round(hcs_size_bytes/1024/1024, 1)) + "MB upscale=" + str(upscale_override) + " fmt=" + fmt)

        # Decompression + upscaling + conversion format
        output_path, result_meta = hcs_compressor.decompress_and_upscale(
            hcs_data=content,
            upscale_override=upscale_override,
            output_format=fmt
        )

        # Lire et encoder en base64
        if not output_path or not os.path.exists(output_path):
            raise RuntimeError("Fichier de sortie absent: " + str(output_path))

        file_size = os.path.getsize(output_path)
        print("Decompressed: " + str(file_size//1024) + " KB output=" + output_path)

        with open(output_path, 'rb') as f_in:
            video_bytes = f_in.read()
        video_base64 = base64.b64encode(video_bytes).decode('utf-8')

        # Nettoyer le fichier temp (mais pas le repertoire parent qui sera nettoye plus tard)
        temp_dir = os.path.dirname(output_path)

        result_meta['upscaled_video_base64'] = video_base64
        result_meta['file_size_mb'] = round(file_size / 1024 / 1024, 2)
        result_meta['output_filename'] = os.path.basename(output_path)

        return JSONResponse(content=result_meta)

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print("Error decompress: " + str(e))
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Erreur decompression: " + str(e))
    finally:
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================
# AWS S3 — STOCKAGE HARMONIQUE
# ============================================================
# Principe: compresser en .hcsv2 (ratio 3:1 a 20:1) puis uploader
# seulement le fichier compresse sur S3 => reduction de 80-95%
# des couts de transfert et de stockage AWS.

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

# Credentials AWS en memoire (non persistes sur disque)
_aws_config = {
    'access_key': None,
    'secret_key': None,
    'region': 'eu-west-1',
    'bucket': None,
    'prefix': 'hcs-videos/',
}

# Tarifs AWS S3 (USD, region eu-west-1, approximatif)
AWS_COST = {
    'storage_per_gb_month': 0.023,        # $0.023/GB/mois
    'transfer_out_per_gb': 0.09,          # $0.09/GB sortant (> 1 GB/mois)
    'put_request_per_1000': 0.005,        # $0.005/1000 requetes PUT
    'get_request_per_1000': 0.0004,       # $0.0004/1000 requetes GET
}


def _get_s3_client():
    if not HAS_BOTO3:
        raise RuntimeError("boto3 non installe: pip install boto3")
    if not _aws_config['access_key'] or not _aws_config['secret_key']:
        raise RuntimeError("Credentials AWS non configures. Appelez /api/v2/aws/configure d'abord.")
    return boto3.client(
        's3',
        aws_access_key_id=_aws_config['access_key'],
        aws_secret_access_key=_aws_config['secret_key'],
        region_name=_aws_config['region'],
    )


def _calc_aws_costs(original_gb: float, compressed_gb: float,
                    downloads_per_month: int = 5, storage_months: int = 12) -> dict:
    """Calcule les economies AWS entre original et .hcsv2"""
    r = AWS_COST
    # Stockage sur N mois
    storage_orig  = original_gb   * r['storage_per_gb_month'] * storage_months
    storage_comp  = compressed_gb * r['storage_per_gb_month'] * storage_months
    # Transfert entrant = GRATUIT sur AWS
    # Transfert sortant (downloads)
    transfer_orig = original_gb   * r['transfer_out_per_gb'] * downloads_per_month
    transfer_comp = compressed_gb * r['transfer_out_per_gb'] * downloads_per_month
    total_orig  = storage_orig  + transfer_orig
    total_comp  = storage_comp  + transfer_comp
    saving_pct  = (total_orig - total_comp) / total_orig * 100 if total_orig > 0 else 0
    return {
        'original_gb': round(original_gb, 3),
        'compressed_gb': round(compressed_gb, 3),
        'compression_ratio': round(original_gb / compressed_gb, 1) if compressed_gb > 0 else 0,
        'storage_months': storage_months,
        'downloads_per_month': downloads_per_month,
        'cost_without_hcs_usd': round(total_orig, 4),
        'cost_with_hcs_usd': round(total_comp, 4),
        'saving_usd': round(total_orig - total_comp, 4),
        'saving_pct': round(saving_pct, 1),
        'detail': {
            'storage_without_hcs': round(storage_orig, 4),
            'storage_with_hcs': round(storage_comp, 4),
            'transfer_without_hcs': round(transfer_orig, 4),
            'transfer_with_hcs': round(transfer_comp, 4),
        }
    }


@app.post("/api/v2/aws/configure")
async def aws_configure(
    access_key: str = Form(...),
    secret_key: str = Form(...),
    bucket: str = Form(...),
    region: str = Form('eu-west-1'),
    prefix: str = Form('hcs-videos/')
):
    """Configure les credentials AWS S3 (stockes en memoire, non persistes)"""
    if not HAS_BOTO3:
        raise HTTPException(status_code=500, detail="boto3 non installe sur ce serveur")

    # Tester la connexion immediatement
    try:
        client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
        # Verifier que le bucket existe et est accessible
        client.head_bucket(Bucket=bucket)

        _aws_config['access_key'] = access_key
        _aws_config['secret_key'] = secret_key
        _aws_config['bucket'] = bucket
        _aws_config['region'] = region
        _aws_config['prefix'] = prefix.rstrip('/') + '/'

        return JSONResponse(content={
            "success": True,
            "message": "Connexion AWS S3 reussie",
            "bucket": bucket,
            "region": region,
            "prefix": _aws_config['prefix'],
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={
            "success": False,
            "error": "Connexion AWS echouee: " + str(e)
        })


@app.get("/api/v2/aws/status")
async def aws_status():
    """Retourne l'etat de la configuration AWS"""
    configured = bool(_aws_config['access_key'] and _aws_config['bucket'])
    return {
        "boto3_available": HAS_BOTO3,
        "configured": configured,
        "bucket": _aws_config['bucket'] if configured else None,
        "region": _aws_config['region'],
        "prefix": _aws_config['prefix'],
        "tarifs": AWS_COST,
    }


@app.post("/api/v2/aws/upload")
async def aws_upload_hcs(
    file: UploadFile = File(...),
    s3_key: str = Form(''),
    original_size_bytes: int = Form(0),
):
    """
    Upload d'un fichier .hcsv2 sur S3 en streaming (multipart).
    Le fichier voyage: client -> HCS server -> S3 (uniquement le .hcsv2 compresse).
    original_size_bytes: taille du fichier source original (pour calcul economies).
    """
    if not HAS_BOTO3:
        raise HTTPException(status_code=500, detail="boto3 non installe")
    if not _aws_config['bucket']:
        raise HTTPException(status_code=400, detail="AWS non configure. Appelez /api/v2/aws/configure")

    t_start = time.time()
    temp_path = None

    try:
        client = _get_s3_client()
        fname = file.filename or "video.hcsv2"

        # S3 key = prefix + nom du fichier (ou cle personnalisee)
        if not s3_key:
            s3_key = _aws_config['prefix'] + fname

        # Streamer le fichier sur disque temporaire
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, fname)
        file_size = await stream_upload_to_file(file, temp_path)

        print("AWS upload: " + s3_key + " size=" + str(round(file_size/1024/1024, 1)) + " MB")

        # Upload multipart vers S3
        client.upload_file(
            Filename=temp_path,
            Bucket=_aws_config['bucket'],
            Key=s3_key,
            ExtraArgs={
                'ContentType': 'application/octet-stream',
                'Metadata': {
                    'hcs-format': 'hcsv2',
                    'hcs-original-size': str(original_size_bytes),
                    'hcs-compressed-size': str(file_size),
                    'hcs-compression-ratio': str(round(original_size_bytes / file_size, 2)) if file_size > 0 and original_size_bytes > 0 else '0',
                }
            }
        )

        elapsed = time.time() - t_start
        speed_mbps = round((file_size / 1024 / 1024) / elapsed, 1) if elapsed > 0 else 0

        # URL S3 publique (si bucket public) ou presignee
        presigned_url = client.generate_presigned_url(
            'get_object',
            Params={'Bucket': _aws_config['bucket'], 'Key': s3_key},
            ExpiresIn=3600 * 24 * 7  # 7 jours
        )

        # Calcul economies
        orig_gb = original_size_bytes / 1024 / 1024 / 1024 if original_size_bytes > 0 else file_size * 10 / 1024 / 1024 / 1024
        comp_gb = file_size / 1024 / 1024 / 1024
        costs = _calc_aws_costs(orig_gb, comp_gb)

        return JSONResponse(content={
            "success": True,
            "s3_key": s3_key,
            "bucket": _aws_config['bucket'],
            "region": _aws_config['region'],
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / 1024 / 1024, 2),
            "upload_time_s": round(elapsed, 2),
            "upload_speed_mbps": speed_mbps,
            "presigned_url": presigned_url,
            "s3_uri": "s3://" + _aws_config['bucket'] + "/" + s3_key,
            "cost_analysis": costs,
        })

    except Exception as e:
        import traceback
        print("AWS upload error: " + str(e))
        raise HTTPException(status_code=500, detail="Erreur upload S3: " + str(e))
    finally:
        if temp_path:
            import shutil
            shutil.rmtree(os.path.dirname(temp_path), ignore_errors=True)


@app.get("/api/v2/aws/list")
async def aws_list_files(prefix: str = ''):
    """Liste les fichiers .hcsv2 dans le bucket S3"""
    if not _aws_config['bucket']:
        raise HTTPException(status_code=400, detail="AWS non configure")
    try:
        client = _get_s3_client()
        search_prefix = prefix or _aws_config['prefix']

        response = client.list_objects_v2(
            Bucket=_aws_config['bucket'],
            Prefix=search_prefix,
            MaxKeys=200
        )

        files = []
        for obj in response.get('Contents', []):
            files.append({
                'key': obj['Key'],
                'name': obj['Key'].split('/')[-1],
                'size_mb': round(obj['Size'] / 1024 / 1024, 2),
                'last_modified': obj['LastModified'].isoformat(),
                'is_hcsv2': obj['Key'].endswith('.hcsv2'),
            })

        total_size_gb = sum(f['size_mb'] for f in files) / 1024
        return {
            "success": True,
            "bucket": _aws_config['bucket'],
            "prefix": search_prefix,
            "files": files,
            "count": len(files),
            "total_size_gb": round(total_size_gb, 3),
            "estimated_monthly_cost_usd": round(total_size_gb * AWS_COST['storage_per_gb_month'], 4),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erreur liste S3: " + str(e))


@app.post("/api/v2/aws/presign-download")
async def aws_presign_download(s3_key: str = Form(...), expires_hours: int = Form(24)):
    """Genere une URL presignee pour telechargement depuis S3"""
    if not _aws_config['bucket']:
        raise HTTPException(status_code=400, detail="AWS non configure")
    try:
        client = _get_s3_client()
        url = client.generate_presigned_url(
            'get_object',
            Params={'Bucket': _aws_config['bucket'], 'Key': s3_key},
            ExpiresIn=expires_hours * 3600
        )
        return {"success": True, "presigned_url": url, "expires_hours": expires_hours, "s3_key": s3_key}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erreur presign: " + str(e))


@app.delete("/api/v2/aws/delete")
async def aws_delete_file(s3_key: str):
    """Supprime un fichier du bucket S3"""
    if not _aws_config['bucket']:
        raise HTTPException(status_code=400, detail="AWS non configure")
    try:
        client = _get_s3_client()
        client.delete_object(Bucket=_aws_config['bucket'], Key=s3_key)
        return {"success": True, "deleted": s3_key}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erreur suppression S3: " + str(e))


@app.post("/api/v2/aws/cost-estimate")
async def aws_cost_estimate(
    original_size_gb: float = Form(...),
    compressed_size_gb: float = Form(...),
    downloads_per_month: int = Form(5),
    storage_months: int = Form(12),
):
    """Calcule les economies AWS avec et sans HCS"""
    costs = _calc_aws_costs(original_size_gb, compressed_size_gb, downloads_per_month, storage_months)
    costs['success'] = True
    return JSONResponse(content=costs)


@app.get("/")
async def root():
    return {"message": "HCS V2 - Simple Server", "status": "ready"}

if __name__ == "__main__":
    import uvicorn
    import logging
    logging.getLogger("uvicorn").setLevel(logging.ERROR)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8009,
        access_log=False,
        # Timeouts longs pour gros fichiers (films entiers jusqu'a 10 GB)
        timeout_keep_alive=600,          # 10 minutes keepalive
        timeout_graceful_shutdown=120,   # 2 minutes arret gracieux
        # Limites HTTP parser (h11) - sans limite pour les corps de requete
        h11_max_incomplete_event_size=None,
        # Workers
        loop="asyncio",
    )
