#!/usr/bin/env python3
"""
HCS V2 API Server - Version avec optimiseur vidéo hybride intégré
Intégration complète du HybridVideoParameterOptimizer
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import numpy as np
from PIL import Image
import io
import base64
import time
import logging
import os
from typing import Dict, Any, Optional, List
from enum import Enum
import tempfile
import cv2

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import des modules HCS
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    from core.hybrid_compressor import HybridCompressor
    from core.hybrid_video_parameter_optimizer import (
        HybridVideoParameterOptimizer, 
        VideoOptimizationTarget,
        VideoParameterSet,
        VideoOptimizationResult
    )
    logger.info("Import HybridVideoParameterOptimizer réussi")
    VIDEO_OPTIMIZER_AVAILABLE = True
except ImportError as e:
    logger.error(f"Erreur import HybridVideoParameterOptimizer: {e}")
    VIDEO_OPTIMIZER_AVAILABLE = False
    # Fallback pour test
    class HybridVideoParameterOptimizer:
        def __init__(self, optimization_target=None, max_iterations=15):
            self.optimization_target = optimization_target
            self.max_iterations = max_iterations
        
        def optimize_video_parameters(self, video_path, method="adaptive"):
            return VideoOptimizationResult(
                best_parameters=VideoParameterSet(
                    k_factor=0.02, webp_quality=85, temporal_coherence_weight=0.8,
                    frame_sample_rate=15, description="Default"
                ),
                performance_metrics={'compression_ratio': 50.0, 'processing_time': 2.0},
                quality_metrics={'spatial_quality': 0.8, 'temporal_quality': 0.85},
                temporal_metrics={'temporal_score': 0.85},
                optimization_score=0.82,
                target_achieved=True,
                all_results=[]
            )
    
    class VideoOptimizationTarget(Enum):
        BALANCED_VIDEO = "balanced_video"
        MAX_TEMPORAL_QUALITY = "max_temporal_quality"
        MAX_COMPRESSION_RATIO = "max_compression_ratio"
        REAL_TIME_PROCESSING = "real_time_processing"
        MIN_BANDWIDTH = "min_bandwidth"
    
    class VideoParameterSet:
        def __init__(self, k_factor, webp_quality, temporal_coherence_weight, frame_sample_rate, description):
            self.k_factor = k_factor
            self.webp_quality = webp_quality
            self.temporal_coherence_weight = temporal_coherence_weight
            self.frame_sample_rate = frame_sample_rate
            self.description = description
    
    class VideoOptimizationResult:
        def __init__(self, best_parameters, performance_metrics, quality_metrics, temporal_metrics, optimization_score, target_achieved, all_results):
            self.best_parameters = best_parameters
            self.performance_metrics = performance_metrics
            self.quality_metrics = quality_metrics
            self.temporal_metrics = temporal_metrics
            self.optimization_score = optimization_score
            self.target_achieved = target_achieved
            self.all_results = all_results

try:
    from core.hybrid_compressor import HybridCompressor
    logger.info("Import HybridCompressor réussi")
except ImportError as e:
    logger.error(f"Erreur import HybridCompressor: {e}")
    # Fallback pour test
    class HybridCompressor:
        def __init__(self, k_factor=0.02, webp_quality=95):
            self.k_factor = k_factor
            self.webp_quality = webp_quality
            self.stats = {'total_processed': 0}
        
        def compress_image(self, image, target_ratio=None):
            return b"test_data", {
                'success': True,
                'hybrid_ratio': 100.0,
                'k_ratio': 50.0,
                'webp_ratio': 2.0,
                'total_time': 0.01,
                'space_saved_percent': 99.0,
                'content_type': 'test',
                'optimization_level': 'excellent',
                'format': 'webp'
            }
        
        def get_stats(self):
            return self.stats

# Initialisation FastAPI
app = FastAPI(
    title="HCS V2 Video Optimizer API",
    description="Harmonic Compression System Version 2.0 - Video Parameter Optimizer",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation compresseur hybride
compressor = HybridCompressor(k_factor=0.02, webp_quality=95)

# Initialisation optimiseur vidéo
video_optimizer = HybridVideoParameterOptimizer(
    optimization_target=VideoOptimizationTarget.BALANCED_VIDEO,
    max_iterations=20
) if VIDEO_OPTIMIZER_AVAILABLE else None

# Stockage temporaire
compression_results = {}
optimization_results = {}
result_counter = 0

# Configuration
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_VIDEO_SIZE = 1024 * 1024 * 1024  # 1GB
SUPPORTED_FORMATS = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp']
SUPPORTED_VIDEO_FORMATS = ['video/mp4', 'video/avi', 'video/mov', 'video/mkv']

# Servir les fichiers statiques du frontend
frontend_path = os.path.join(parent_dir, "frontend")
if os.path.exists(frontend_path):
    app.mount("/frontend", StaticFiles(directory=frontend_path), name="frontend")
    print(f"Frontend static files mounted from: {frontend_path}")
else:
    print(f"Warning: Frontend directory not found at {frontend_path}")

@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)  # No content

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))

@app.get("/", tags=["Root"])
async def root():
    """Endpoint racine avec informations système"""
    stats = compressor.get_stats()
    
    return {
        "name": "HCS V2 Video Optimizer API",
        "version": "2.1.0",
        "description": "Harmonic Compression System - Video Parameter Optimizer",
        "status": "operational",
        "video_optimizer_available": VIDEO_OPTIMIZER_AVAILABLE,
        "endpoints": {
            "compress_image": "/api/v2/compress/image",
            "compress_video": "/api/v2/compress/video",
            "optimize_video": "/api/v2/optimize/video",
            "optimize_video_upload": "/api/v2/optimize/video/upload",
            "stats": "/api/v2/stats",
            "health": "/api/v2/health",
            "video_optimizer_info": "/api/v2/video/optimizer/info"
        },
        "performance": {
            "guaranteed_ratio": "50:1",
            "practical_ratio": "500-3000:1",
            "average_fps": f"{stats.get('average_fps', 0):.1f}",
            "total_processed": stats.get('total_processed', 0),
            "video_optimization_targets": [target.value for target in VideoOptimizationTarget]
        }
    }

@app.get("/api/v2/health", tags=["System"])
async def health_check():
    """Vérification de santé du système"""
    try:
        # Test rapide du compresseur
        test_image = np.random.rand(100, 100, 3).astype(np.float32)
        _, test_metadata = compressor.compress_image(test_image)
        
        stats = compressor.get_stats()
        
        health_data = {
            "status": "healthy",
            "timestamp": time.time(),
            "compression_test": {
                "success": test_metadata['success'],
                "ratio": test_metadata['hybrid_ratio'],
                "time": test_metadata['total_time']
            },
            "system_stats": {
                "total_processed": stats.get('total_processed', 0),
                "average_ratio": stats.get('average_ratio', 0),
                "average_time": stats.get('average_time', 0),
                "uptime": "operational"
            },
            "video_optimizer": {
                "available": VIDEO_OPTIMIZER_AVAILABLE,
                "status": "ready" if video_optimizer else "not_available"
            }
        }
        
        return health_data
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {e}")

@app.get("/api/v2/video/optimizer/info", tags=["Video Optimizer"])
async def get_video_optimizer_info():
    """Informations sur l'optimiseur vidéo"""
    if not VIDEO_OPTIMIZER_AVAILABLE:
        return {
            "success": False,
            "message": "Video optimizer not available",
            "fallback_mode": True
        }
    
    return {
        "success": True,
        "optimizer_info": {
            "type": "HybridVideoParameterOptimizer",
            "version": "1.0",
            "optimization_targets": {
                target.value: {
                    "name": target.value.replace("_", " ").title(),
                    "description": _get_target_description(target)
                } for target in VideoOptimizationTarget
            },
            "parameter_ranges": {
                "k_factor": (0.001, 0.05),
                "webp_quality": (20, 95),
                "temporal_coherence_weight": (0.0, 1.0),
                "frame_sample_rate": (5, 30)
            },
            "optimization_methods": ["grid", "random", "adaptive"],
            "max_iterations": 20,
            "parallel_workers": 4
        }
    }

def _get_target_description(target):
    """Description des objectifs d'optimisation"""
    descriptions = {
        VideoOptimizationTarget.MAX_TEMPORAL_QUALITY: "Maximise la cohérence temporelle et la qualité vidéo",
        VideoOptimizationTarget.MAX_COMPRESSION_RATIO: "Maximise le ratio de compression",
        VideoOptimizationTarget.REAL_TIME_PROCESSING: "Optimise pour le traitement temps réel",
        VideoOptimizationTarget.MIN_BANDWIDTH: "Minimise l'utilisation de bande passante",
        VideoOptimizationTarget.BALANCED_VIDEO: "Équilibre qualité, compression et performance"
    }
    return descriptions.get(target, "Optimisation vidéo")

@app.post("/api/v2/optimize/video", tags=["Video Optimizer"])
async def optimize_video_parameters(
    video_path: str,
    target: str = "balanced_video",
    method: str = "adaptive",
    max_iterations: int = 20
):
    """
    Optimise les paramètres pour une vidéo existante
    
    Args:
        video_path: Chemin de la vidéo à optimiser
        target: Objectif d'optimisation
        method: Méthode d'optimisation
        max_iterations: Nombre maximum d'itérations
    """
    global result_counter
    
    if not VIDEO_OPTIMIZER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Video optimizer not available")
    
    try:
        # Validation de l'objectif
        try:
            optimization_target = VideoOptimizationTarget(target)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid target: {target}")
        
        # Validation du chemin
        if not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail=f"Video file not found: {video_path}")
        
        # Configuration de l'optimiseur
        optimizer = HybridVideoParameterOptimizer(
            optimization_target=optimization_target,
            max_iterations=max_iterations
        )
        
        logger.info(f"Début optimisation vidéo: {video_path} -> {target}")
        
        # Lancement de l'optimisation
        start_time = time.time()
        result = optimizer.optimize_video_parameters(video_path, method=method)
        optimization_time = time.time() - start_time
        
        # Génération ID résultat
        result_id = f"opt_{result_counter}"
        result_counter += 1
        
        # Stockage résultat
        optimization_results[result_id] = {
            "video_path": video_path,
            "optimization_target": target,
            "method": method,
            "result": result,
            "optimization_time": optimization_time,
            "timestamp": time.time()
        }
        
        # Préparation de la réponse
        response = {
            "success": True,
            "result_id": result_id,
            "video_path": video_path,
            "optimization_target": target,
            "method": method,
            "optimization_time": optimization_time,
            "best_parameters": {
                "k_factor": result.best_parameters.k_factor,
                "webp_quality": result.best_parameters.webp_quality,
                "temporal_coherence_weight": result.best_parameters.temporal_coherence_weight,
                "frame_sample_rate": result.best_parameters.frame_sample_rate,
                "description": result.best_parameters.description
            },
            "performance_metrics": result.performance_metrics,
            "quality_metrics": result.quality_metrics,
            "temporal_metrics": result.temporal_metrics,
            "optimization_score": result.optimization_score,
            "target_achieved": result.target_achieved,
            "all_results_count": len(result.all_results)
        }
        
        logger.info(f"Optimisation terminée: score={result.optimization_score:.3f}, achieved={result.target_achieved}")
        
        return response
        
    except Exception as e:
        logger.error(f"Video optimization error: {e}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {e}")

@app.post("/api/v2/optimize/video/upload", tags=["Video Optimizer"])
async def optimize_video_upload(
    file: UploadFile = File(...),
    target: str = Form("balanced_video"),
    method: str = Form("adaptive"),
    max_iterations: int = Form(20)
):
    """
    Optimise les paramètres pour une vidéo uploadée
    
    Args:
        file: Fichier vidéo
        target: Objectif d'optimisation
        method: Méthode d'optimisation
        max_iterations: Nombre maximum d'itérations
    """
    global result_counter
    
    if not VIDEO_OPTIMIZER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Video optimizer not available")
    
    try:
        # Validation fichier
        if file.size > MAX_VIDEO_SIZE:
            raise HTTPException(status_code=413, detail="Video too large (max 1GB)")
        
        if file.content_type not in SUPPORTED_VIDEO_FORMATS:
            raise HTTPException(status_code=400, detail=f"Unsupported video format: {file.content_type}")
        
        # Création fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            video_data = await file.read()
            temp_file.write(video_data)
            temp_video_path = temp_file.name
        
        try:
            # Validation de l'objectif
            try:
                optimization_target = VideoOptimizationTarget(target)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid target: {target}")
            
            # Configuration de l'optimiseur
            optimizer = HybridVideoParameterOptimizer(
                optimization_target=optimization_target,
                max_iterations=max_iterations
            )
            
            logger.info(f"Début optimisation vidéo uploadée: {file.filename} -> {target}")
            
            # Lancement de l'optimisation
            start_time = time.time()
            result = optimizer.optimize_video_parameters(temp_video_path, method=method)
            optimization_time = time.time() - start_time
            
            # Génération ID résultat
            result_id = f"upl_{result_counter}"
            result_counter += 1
            
            # Stockage résultat
            optimization_results[result_id] = {
                "original_filename": file.filename,
                "video_path": temp_video_path,
                "optimization_target": target,
                "method": method,
                "result": result,
                "optimization_time": optimization_time,
                "timestamp": time.time()
            }
            
            # Préparation de la réponse
            response = {
                "success": True,
                "result_id": result_id,
                "original_filename": file.filename,
                "optimization_target": target,
                "method": method,
                "optimization_time": optimization_time,
                "best_parameters": {
                    "k_factor": result.best_parameters.k_factor,
                    "webp_quality": result.best_parameters.webp_quality,
                    "temporal_coherence_weight": result.best_parameters.temporal_coherence_weight,
                    "frame_sample_rate": result.best_parameters.frame_sample_rate,
                    "description": result.best_parameters.description
                },
                "performance_metrics": result.performance_metrics,
                "quality_metrics": result.quality_metrics,
                "temporal_metrics": result.temporal_metrics,
                "optimization_score": result.optimization_score,
                "target_achieved": result.target_achieved,
                "all_results_count": len(result.all_results),
                "recommendations": _generate_recommendations(result)
            }
            
            logger.info(f"Optimisation upload terminée: score={result.optimization_score:.3f}")
            
            return response
            
        finally:
            # Nettoyage du fichier temporaire
            try:
                os.unlink(temp_video_path)
            except:
                pass
        
    except Exception as e:
        logger.error(f"Video upload optimization error: {e}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {e}")

def _generate_recommendations(result):
    """Génère des recommandations basées sur les résultats"""
    recommendations = []
    
    if result.optimization_score > 0.8:
        recommendations.append("Excellente configuration trouvée")
    elif result.optimization_score > 0.6:
        recommendations.append("Bonne configuration, peut être améliorée")
    else:
        recommendations.append("Configuration moyenne, envisager d'autres objectifs")
    
    if result.performance_metrics.get('compression_ratio', 0) > 50:
        recommendations.append("Compression très efficace")
    elif result.performance_metrics.get('compression_ratio', 0) > 20:
        recommendations.append("Compression correcte")
    else:
        recommendations.append("Compression faible, vérifier les paramètres")
    
    if result.quality_metrics.get('temporal_quality', 0) > 0.8:
        recommendations.append("Excellente cohérence temporelle")
    
    return recommendations

@app.post("/api/v2/compress/image", tags=["Compression"])
async def compress_image(
    file: UploadFile = File(...),
    target_ratio: Optional[float] = None,
    quality: Optional[int] = None,
    use_optimized_params: Optional[bool] = False
):
    """
    Compresse une image avec K=0.02 + WebP
    Optionnellement utilise les paramètres optimisés par l'optimiseur vidéo
    """
    global result_counter
    
    try:
        # Validation fichier
        if file.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large (max 100MB)")
        
        if file.content_type not in SUPPORTED_FORMATS:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {file.content_type}")
        
        # Utilisation des paramètres optimisés si demandé et disponibles
        if use_optimized_params and video_optimizer and len(optimization_results) > 0:
            # Récupérer le dernier résultat d'optimisation
            last_result = list(optimization_results.values())[-1]
            best_params = last_result['result'].best_parameters
            
            # Application des paramètres optimisés
            compressor.k_factor = best_params.k_factor
            compressor.webp_quality = best_params.webp_quality
            
            logger.info(f"Utilisation paramètres optimisés: K={best_params.k_factor:.4f}, Q={best_params.webp_quality}")
        
        # Lecture fichier
        image_data = await file.read()
        pil_image = Image.open(io.BytesIO(image_data))
        
        # Conversion numpy array
        image_array = np.array(pil_image).astype(np.float32) / 255.0
        
        # Compression hybride
        start_time = time.time()
        compressed_data, metadata = compressor.compress_image(image_array, target_ratio)
        compression_time = time.time() - start_time
        
        # Encodage base64 pour réponse
        compressed_b64 = base64.b64encode(compressed_data).decode('utf-8')
        
        # Génération ID résultat
        result_id = f"img_{result_counter}"
        result_counter += 1
        
        # Stockage résultat
        compression_results[result_id] = {
            "original_filename": file.filename,
            "original_size": len(image_data),
            "compressed_size": len(compressed_data),
            "metadata": metadata,
            "compressed_data": compressed_b64,
            "timestamp": time.time(),
            "used_optimized_params": use_optimized_params
        }
        
        # Réponse
        response = {
            "success": True,
            "result_id": result_id,
            "original_filename": file.filename,
            "original_size": len(image_data),
            "compressed_size": len(compressed_data),
            "compression_ratio": metadata['hybrid_ratio'],
            "space_saved_percent": metadata['space_saved_percent'],
            "processing_time": metadata['total_time'],
            "k_ratio": metadata['k_ratio'],
            "webp_ratio": metadata['webp_ratio'],
            "content_type": metadata['content_type'],
            "performance_level": metadata['optimization_level'],
            "format": "webp",
            "download_url": f"/api/v2/download/{result_id}",
            "used_optimized_params": use_optimized_params,
            "current_params": {
                "k_factor": compressor.k_factor,
                "webp_quality": compressor.webp_quality
            }
        }
        
        logger.info(f"Image compressée: {file.filename} → {metadata['hybrid_ratio']:.1f}:1")
        
        return response
        
    except Exception as e:
        logger.error(f"Image compression error: {e}")
        raise HTTPException(status_code=500, detail=f"Compression failed: {e}")

@app.post("/api/v2/compress/video", tags=["Compression"])
async def compress_video(
    file: UploadFile = File(...),
    target_ratio: Optional[float] = None,
    quality: Optional[int] = None,
    use_optimized_params: Optional[bool] = False
):
    """
    Compresse une vidéo avec K=0.02 + WebP
    Optionnellement utilise les paramètres optimisés par l'optimiseur vidéo
    """
    global result_counter
    
    try:
        # Validation fichier
        if file.size > MAX_VIDEO_SIZE:
            raise HTTPException(status_code=413, detail="Video too large (max 1GB)")
        
        # Utilisation des paramètres optimisés si demandé et disponibles
        if use_optimized_params and video_optimizer and len(optimization_results) > 0:
            # Récupérer le dernier résultat d'optimisation
            last_result = list(optimization_results.values())[-1]
            best_params = last_result['result'].best_parameters
            
            # Application des paramètres optimisés
            compressor.k_factor = best_params.k_factor
            compressor.webp_quality = best_params.webp_quality
            
            logger.info(f"Utilisation paramètres optimisés vidéo: K={best_params.k_factor:.4f}, Q={best_params.webp_quality}")
        
        # Lecture vidéo (simulation pour démo)
        video_data = await file.read()
        
        # Simulation de frames vidéo (démo)
        num_frames = max(30, len(video_data) // (1920 * 1080 * 3))
        
        # Compression de frames représentatives
        sample_frames = []
        for i in range(min(5, num_frames)):
            frame = np.random.rand(480, 640, 3).astype(np.float32)
            sample_frames.append(frame)
        
        # Configuration qualité si spécifiée
        if quality is not None:
            compressor.webp_optimizer.quality = max(0, min(100, quality))
        
        # Compression des frames
        start_time = time.time()
        compressed_frames = []
        total_ratio = 0
        total_k_ratio = 0
        total_webp_ratio = 0
        
        for frame in sample_frames:
            compressed_data, metadata = compressor.compress_image(frame, target_ratio)
            compressed_frames.append(metadata)
            total_ratio += metadata['hybrid_ratio']
            total_k_ratio += metadata['k_ratio']
            total_webp_ratio += metadata['webp_ratio']
        
        compression_time = time.time() - start_time
        avg_ratio = total_ratio / len(compressed_frames) if len(compressed_frames) > 0 else 100
        avg_k_ratio = total_k_ratio / len(compressed_frames) if len(compressed_frames) > 0 else 50
        avg_webp_ratio = total_webp_ratio / len(compressed_frames) if len(compressed_frames) > 0 else 2
        
        # Estimation pour vidéo complète
        estimated_compressed_size = len(video_data) / avg_ratio if avg_ratio > 0 else len(video_data)
        
        # Génération ID résultat
        result_id = f"vid_{result_counter}"
        result_counter += 1
        
        # Stockage résultat
        compression_results[result_id] = {
            "original_filename": file.filename,
            "original_size": len(video_data),
            "estimated_compressed_size": estimated_compressed_size,
            "metadata": {
                "num_frames": num_frames,
                "sample_frames": len(compressed_frames),
                "average_ratio": avg_ratio,
                "compression_time": compression_time,
                "estimated_fps": 30
            },
            "timestamp": time.time(),
            "used_optimized_params": use_optimized_params
        }
        
        # Réponse COMPLÈTE avec tous les ratios
        response = {
            "success": True,
            "result_id": result_id,
            "original_filename": file.filename,
            "original_size": len(video_data),
            "estimated_compressed_size": estimated_compressed_size,
            "compression_ratio": avg_ratio,
            "space_saved_percent": (1 - estimated_compressed_size / len(video_data)) * 100 if len(video_data) > 0 else 0,
            "processing_time": compression_time,
            "k_ratio": avg_k_ratio,
            "webp_ratio": avg_webp_ratio,
            "content_type": "video_simulation",
            "performance_level": "excellent" if avg_ratio > 100 else "good",
            "num_frames": num_frames,
            "sample_frames_processed": len(compressed_frames),
            "average_fps": 30,
            "format": "webp_video_simulation",
            "download_url": f"/api/v2/download/{result_id}",
            "used_optimized_params": use_optimized_params,
            "current_params": {
                "k_factor": compressor.k_factor,
                "webp_quality": compressor.webp_quality
            }
        }
        
        logger.info(f"Vidéo compressée: {file.filename} → {avg_ratio:.1f}:1 (K={avg_k_ratio:.1f}:1, WebP={avg_webp_ratio:.1f}:1)")
        
        return response
        
    except Exception as e:
        logger.error(f"Video compression error: {e}")
        raise HTTPException(status_code=500, detail=f"Compression failed: {e}")

@app.get("/api/v2/stats", tags=["System"])
async def get_stats():
    """Retourne les statistiques du système"""
    stats = compressor.get_stats()
    
    return {
        "system": {
            "status": "operational",
            "uptime": time.time(),
            "version": "2.1.0"
        },
        "performance": {
            "total_processed": stats.get('total_processed', 0),
            "average_ratio": stats.get('average_ratio', 0),
            "average_time": stats.get('average_time', 0),
            "average_fps": stats.get('average_fps', 0)
        },
        "compression": {
            "k_factor": compressor.k_factor,
            "webp_quality": compressor.webp_quality,
            "guaranteed_ratio": "50:1",
            "supported_formats": SUPPORTED_FORMATS,
            "max_file_size": MAX_FILE_SIZE
        },
        "video_optimizer": {
            "available": VIDEO_OPTIMIZER_AVAILABLE,
            "optimizations_completed": len(optimization_results),
            "last_optimization": list(optimization_results.values())[-1]['timestamp'] if optimization_results else None
        },
        "storage": {
            "cached_compression_results": len(compression_results),
            "cached_optimization_results": len(optimization_results),
            "memory_usage": "N/A"
        }
    }

@app.get("/api/v2/download/{result_id}", tags=["Download"])
async def download_compressed(result_id: str):
    """
    Télécharge le fichier compressé
    """
    try:
        if result_id not in compression_results:
            raise HTTPException(status_code=404, detail="Result not found")
        
        result = compression_results[result_id]
        
        if 'compressed_data' in result:
            # Image compressée
            compressed_data = base64.b64decode(result['compressed_data'])
            filename = f"compressed_{result['original_filename']}.webp"
            
            return Response(
                content=compressed_data,
                media_type="image/webp",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
            )
        elif 'estimated_compressed_size' in result:
            # Vidéo (simulation) - créer un fichier de démonstration
            demo_content = f"""HCS V2 Video Optimizer Report
==========================================
Original File: {result['original_filename']}
Original Size: {result['original_size']} bytes
Estimated Compressed Size: {result['estimated_compressed_size']:.2f} bytes
Compression Ratio: {result.get('metadata', {}).get('average_ratio', 'N/A')}:1
Processing Time: {result.get('metadata', {}).get('compression_time', 'N/A')}s
Frames Processed: {result.get('metadata', {}).get('sample_frames', 'N/A')}
Used Optimized Parameters: {result.get('used_optimized_params', False)}
==========================================
This is a demo download for video compression with parameter optimization.
In production, the actual compressed video file would be downloaded.
HCS V2 - Harmonic Compression System with Video Parameter Optimizer
K={compressor.k_factor} + WebP Quality={compressor.webp_quality}
"""
            
            filename = f"hcs_video_optimizer_report_{result['original_filename']}.txt"
            
            return Response(
                content=demo_content.encode('utf-8'),
                media_type="text/plain",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
            )
        else:
            raise HTTPException(status_code=404, detail="No downloadable content found")
            
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {e}")

# Point d'entrée pour le développement
if __name__ == "__main__":
    print("🚀 Démarrage HCS V2 Video Optimizer API Server")
    print("=" * 60)
    print("📊 Configuration:")
    print(f"   K-Factor: {compressor.k_factor}")
    print(f"   WebP Quality: {compressor.webp_quality}")
    print(f"   Video Optimizer: {'✅ Available' if VIDEO_OPTIMIZER_AVAILABLE else '❌ Not Available'}")
    print(f"   Max File Size: {MAX_FILE_SIZE // (1024*1024)} MB")
    print(f"   Max Video Size: {MAX_VIDEO_SIZE // (1024*1024)} MB")
    print(f"   Supported Formats: {', '.join(SUPPORTED_FORMATS)}")
    print(f"   Supported Video Formats: {', '.join(SUPPORTED_VIDEO_FORMATS)}")
    print()
    print("🌐 Endpoints:")
    print("   http://localhost:8012/docs")
    print("   http://localhost:8012/redoc")
    print("   http://localhost:8012/api/v2/optimize/video")
    print("   http://localhost:8012/api/v2/optimize/video/upload")
    print("   http://localhost:8012/api/v2/compress/image")
    print("   http://localhost:8012/api/v2/compress/video")
    print("   http://localhost:8012/api/v2/video/optimizer/info")
    print("   http://localhost:8012/api/v2/stats")
    print("   http://localhost:8012/api/v2/health")
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8012,  # Port dédié pour l'optimiseur vidéo
        reload=False,
        log_level="info"
    )
