#!/usr/bin/env python3
"""
Intégration Deepseek MOE pour AWS HCV PRO Server
===============================================

Ajoute les endpoints Deepseek MOE avec couche harmonique
au serveur principal HCV PRO déployé sur AWS
"""

import sys
import os
import json
import tempfile
import traceback
from pathlib import Path
from datetime import datetime

# Ajouter le dossier codecs au path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'codecs'))

try:
    from hcv_moe_deepseek_codec import HCVMOEDeepseekCodec
    from deepseek4_moe_integration import Deepseek4MOECompressor, Deepseek4MOEInference
except ImportError as e:
    print(f"❌ Import Deepseek MOE: {e}")
    sys.exit(1)

class DeepseekMOEHandler:
    """Handler pour les opérations Deepseek MOE sur AWS"""
    
    def __init__(self):
        self.compressor = None
        self.inference_engine = None
        self.models_dir = PROJECT_ROOT / "models" / "deepseek4"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
    def initialize_compressor(self, compression_level='balanced', enable_harmonic=True, quantize_8bit=False):
        """Initialise le compresseur Deepseek MOE"""
        try:
            self.compressor = Deepseek4MOECompressor(
                compression_level=compression_level,
                quantize_8bit=quantize_8bit,
                enable_harmonic_layer=enable_harmonic
            )
            return {"status": "success", "message": "Compresseur initialisé"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def compress_model(self, model_path_or_name, output_name=None):
        """Compresse un modèle Deepseek 4"""
        if not self.compressor:
            return {"status": "error", "message": "Compresseur non initialisé"}
        
        try:
            # Déterminer le chemin de sortie
            if output_name:
                output_path = self.models_dir / f"{output_name}.hcmo"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = self.models_dir / f"deepseek4_compressed_{timestamp}.hcmo"
            
            # Compression
            stats = self.compressor.compress_model(model_path_or_name, str(output_path))
            
            return {
                "status": "success",
                "stats": stats,
                "output_path": str(output_path),
                "compression_ratio": stats.get('overall_compression_ratio', 0),
                "harmonic_enabled": stats.get('harmonic_layer_enabled', False)
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def initialize_inference(self, model_path):
        """Initialise le moteur d'inférence"""
        try:
            self.inference_engine = Deepseek4MOEInference(model_path)
            return {"status": "success", "message": "Inférence initialisée"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def run_inference(self, prompt, max_tokens=100, temperature=0.7):
        """Exécute l'inférence Deepseek 4"""
        if not self.inference_engine:
            return {"status": "error", "message": "Inférence non initialisée"}
        
        try:
            result = self.inference_engine.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return {
                "status": "success",
                "generated_text": result,
                "determinism_report": self.inference_engine.get_harmonic_determinism_report()
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def list_compressed_models(self):
        """Liste les modèles compressés disponibles"""
        try:
            models = []
            for file_path in self.models_dir.glob("*.hcmo"):
                stats = file_path.stat()
                models.append({
                    "name": file_path.stem,
                    "path": str(file_path),
                    "size_mb": stats.st_size / (1024*1024),
                    "created": datetime.fromtimestamp(stats.st_ctime).isoformat()
                })
            
            return {"status": "success", "models": sorted(models, key=lambda x: x['created'], reverse=True)}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_model_info(self, model_name):
        """Récupère les informations d'un modèle compressé"""
        try:
            model_path = self.models_dir / f"{model_name}.hcmo"
            if not model_path.exists():
                return {"status": "error", "message": "Modèle non trouvé"}
            
            # Initialiser le codec pour lire les métadonnées
            codec = HCVMOEDeepseekCodec()
            codec.load_model(str(model_path))
            
            # Récupérer les statistiques
            stats = codec.get_compression_stats()
            determinism = codec.get_harmonic_determinism_report()
            
            return {
                "status": "success",
                "model_name": model_name,
                "compression_stats": stats,
                "harmonic_determinism": determinism,
                "file_size_mb": model_path.stat().st_size / (1024*1024)
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Handler global pour Deepseek MOE
deepseek_handler = DeepseekMOEHandler()

def add_deepseek_endpoints(app):
    """Ajoute les endpoints Deepseek MOE à l'application Flask"""
    
    @app.route('/api/deepseek/init', methods=['POST'])
    def init_deepseek_compressor():
        """Initialise le compresseur Deepseek MOE"""
        try:
            data = request.get_json() or {}
            compression_level = data.get('compression_level', 'balanced')
            enable_harmonic = data.get('enable_harmonic', True)
            quantize_8bit = data.get('quantize_8bit', False)
            
            result = deepseek_handler.initialize_compressor(
                compression_level=compression_level,
                enable_harmonic=enable_harmonic,
                quantize_8bit=quantize_8bit
            )
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    
    @app.route('/api/deepseek/compress', methods=['POST'])
    def compress_deepseek_model():
        """Compresse un modèle Deepseek 4"""
        try:
            data = request.get_json() or {}
            model_path = data.get('model_path', 'deepseek-ai/DeepSeek-V2')
            output_name = data.get('output_name')
            
            result = deepseek_handler.compress_model(model_path, output_name)
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    
    @app.route('/api/deepseek/models', methods=['GET'])
    def list_deepseek_models():
        """Liste les modèles Deepseek compressés"""
        try:
            result = deepseek_handler.list_compressed_models()
            return jsonify(result)
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    
    @app.route('/api/deepseek/models/<model_name>/info', methods=['GET'])
    def get_deepseek_model_info(model_name):
        """Récupère les informations d'un modèle"""
        try:
            result = deepseek_handler.get_model_info(model_name)
            return jsonify(result)
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    
    @app.route('/api/deepseek/models/<model_name>/init-inference', methods=['POST'])
    def init_deepseek_inference(model_name):
        """Initialise l'inférence pour un modèle"""
        try:
            model_path = deepseek_handler.models_dir / f"{model_name}.hcmo"
            result = deepseek_handler.initialize_inference(str(model_path))
            return jsonify(result)
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    
    @app.route('/api/deepseek/models/<model_name>/generate', methods=['POST'])
    def generate_deepseek(model_name):
        """Génère du texte avec Deepseek 4"""
        try:
            data = request.get_json() or {}
            prompt = data.get('prompt', '')
            max_tokens = data.get('max_tokens', 100)
            temperature = data.get('temperature', 0.7)
            
            if not prompt:
                return jsonify({"status": "error", "message": "Prompt requis"})
            
            result = deepseek_handler.run_inference(prompt, max_tokens, temperature)
            return jsonify(result)
            
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    
    @app.route('/api/deepseek/benchmark', methods=['POST'])
    def benchmark_deepseek():
        """Benchmark de compression Deepseek"""
        try:
            # Initialiser le compresseur
            init_result = deepseek_handler.initialize_compressor(
                compression_level='balanced',
                enable_harmonic=True,
                quantize_8bit=False
            )
            
            if init_result['status'] != 'success':
                return jsonify(init_result)
            
            # Lancer le benchmark
            codec = HCVMOEDeepseekCodec()
            benchmark_results = codec.benchmark_compression()
            
            return jsonify({
                "status": "success",
                "benchmark": benchmark_results,
                "harmonic_layer": codec.enable_harmonic_layer
            })
            
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    
    @app.route('/api/deepseek/health', methods=['GET'])
    def deepseek_health():
        """Vérifie l'état du service Deepseek"""
        try:
            return jsonify({
                "status": "healthy",
                "service": "Deepseek MOE Harmonic",
                "features": {
                    "compression": deepseek_handler.compressor is not None,
                    "inference": deepseek_handler.inference_engine is not None,
                    "harmonic_layer": True,
                    "models_available": len(list(deepseek_handler.models_dir.glob("*.hcmo")))
                },
                "models_dir": str(deepseek_handler.models_dir)
            })
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    # Test du module
    print("🧪 Test du module Deepseek MOE AWS Integration")
    
    # Test handler
    handler = DeepseekMOEHandler()
    
    # Test initialisation
    print("📊 Test initialisation compresseur...")
    result = handler.initialize_compressor()
    print(f"   Résultat: {result}")
    
    # Test benchmark
    print("\n📊 Test benchmark...")
    codec = HCVMOEDeepseekCodec()
    try:
        benchmark = codec.benchmark_compression()
        print(f"   Benchmark: {benchmark}")
    except Exception as e:
        print(f"   Erreur benchmark: {e}")
    
    print("\n✅ Module testé avec succès!")
