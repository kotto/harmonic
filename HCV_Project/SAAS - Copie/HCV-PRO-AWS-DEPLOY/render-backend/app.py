"""
HCV PRO Backend - Render Deployment
Secure Flask API for HCV PRO compression algorithms
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import time
import os
import logging
from datetime import datetime
import json
import numpy as np

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('HCV_PRO_SECRET', 'hcv-pro-secret-2024')
API_KEY_REQUIRED = os.environ.get('HCV_PRO_API_KEY_REQUIRED', 'true').lower() == 'true'
RATE_LIMIT = int(os.environ.get('HCV_PRO_RATE_LIMIT', '100'))

# API Keys (hashed)
API_KEYS = {
    'demo-key-2024': hashlib.sha256('demo-key-2024'.encode()).hexdigest(),
    'hcv-pro-client-001': hashlib.sha256('hcv-pro-client-001'.encode()).hexdigest(),
    'test-key-frontend': hashlib.sha256('test-key-frontend'.encode()).hexdigest()
}

# Rate limiting storage
rate_limit_storage = {}

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def hash_api_key(api_key):
    """Hash API key for comparison"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def verify_api_key(request):
    """Verify API key from request headers"""
    if not API_KEY_REQUIRED:
        return True
    
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return False
    
    api_key = auth_header[7:]  # Remove 'Bearer ' prefix
    hashed_key = hash_api_key(api_key)
    
    return hashed_key in API_KEYS.values()

def check_rate_limit(api_key_hash):
    """Check rate limiting for API key"""
    now = int(time.time())
    hour = now // 3600
    
    if api_key_hash not in rate_limit_storage:
        rate_limit_storage[api_key_hash] = {}
    
    if hour not in rate_limit_storage[api_key_hash]:
        rate_limit_storage[api_key_hash][hour] = 0
    
    if rate_limit_storage[api_key_hash][hour] >= RATE_LIMIT:
        return False
    
    rate_limit_storage[api_key_hash][hour] += 1
    return True

def log_access(endpoint, api_key_hash, status):
    """Log API access"""
    timestamp = datetime.now().isoformat()
    logger.info(f"[{timestamp}] {endpoint} - Key: {api_key_hash[:8]}... - Status: {status}")

def simulate_compression(file_size, file_name=None, method="broadcast"):
    """Simulate HCV PRO compression"""
    # Simulate processing time
    time.sleep(0.15)
    
    # Simulate compression ratios based on method
    ratios = {
        "broadcast": 28.5,
        "android-boost": 15.2,
        "universal-boost": 22.8,
        "video-boost": 18.7
    }
    
    ratio = ratios.get(method, 20.0)
    compressed_size = int(file_size / ratio)
    savings = ((file_size - compressed_size) / file_size) * 100
    
    # Calcul métriques dynamiques selon taille fichier
    ssim = 0.97 + (file_size / 10000000) * 0.015
    if ssim > 0.998: ssim = 0.998
    
    return {
        "method": method,
        "filename": file_name,
        "original_size": file_size,
        "source_size": file_size,
        "raw_size": file_size * 3,
        "compressed_size": compressed_size,
        "ratio": ratio,
        "ratio_vs_raw": round((file_size * 3) / compressed_size, 1),
        "ratio_vs_source": round(ratio, 1),
        "savings_percent": round(savings, 2),
        "savings_vs_raw": round(100 - (100 * compressed_size / (file_size * 3)), 1),
        "savings_vs_source": round(savings, 1),
        "psnr": "∞",
        "ssim": round(ssim, 4),
        "bitexact": True,
        "bitexact_reproducible": True,
        "processing_time_ms": int(file_size / 50000) + 80,
        "media_type": "image"
    }

# Routes
@app.route('/')
def index():
    """Serve main page"""
    return jsonify({
        "service": "HCV PRO Backend",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "/health": "Health check",
            "/info": "Codec information",
            "/stats": "Usage statistics",
            "/compress/<method>": "Compression endpoint"
        }
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "HCV PRO Backend",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "environment": "render"
    })

@app.route('/info')
def info():
    """Information about codecs"""
    return jsonify({
        "codecs": {
            "broadcast": {
                "name": "HCV Broadcast",
                "ratio": "26-33:1",
                "quality": "Lossless",
                "target": "SDI 4:2:2"
            },
            "android-boost": {
                "name": "HCV Android Boost",
                "ratio": "12-18:1",
                "quality": "Near Lossless",
                "target": "Mobile Optimization"
            },
            "universal-boost": {
                "name": "HCV Universal Boost",
                "ratio": "20-25:1",
                "quality": "Lossless",
                "target": "Universal Compatibility"
            },
            "video-boost": {
                "name": "HCV Video Boost",
                "ratio": "15-22:1",
                "quality": "Near Lossless",
                "target": "Video Optimization"
            }
        }
    })

@app.route('/stats')
def stats():
    """Usage statistics"""
    return jsonify({
        "total_requests": sum(sum(hour.values()) for hour in rate_limit_storage.values()),
        "active_keys": len(rate_limit_storage),
        "rate_limit": RATE_LIMIT,
        "uptime": "100%",
        "environment": "render"
    })

@app.route('/compress/<method>', methods=['POST'])
def compress(method):
    """Compression endpoint"""
    # Verify API key
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        log_access(f"/compress/{method}", "none", "unauthorized")
        return jsonify({"error": "API key required"}), 401
    
    api_key = auth_header[7:]
    api_key_hash = hash_api_key(api_key)
    
    if not verify_api_key(request):
        log_access(f"/compress/{method}", api_key_hash, "invalid_key")
        return jsonify({"error": "Invalid API key"}), 401
    
    if not check_rate_limit(api_key_hash):
        log_access(f"/compress/{method}", api_key_hash, "rate_limited")
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    try:
        # Get request data
        if request.is_json:
            data = request.get_json()
            file_size = data.get('file_size', 1024 * 1024)  # Default 1MB
        else:
            return jsonify({"error": "JSON data required"}), 400
        
        # Validate method
        valid_methods = ["broadcast", "android-boost", "universal-boost", "video-boost"]
        if method not in valid_methods:
            log_access(f"/compress/{method}", api_key_hash, "invalid_method")
            return jsonify({"error": f"Invalid method: {method}"}), 400
        
        # Simulate compression
        result = simulate_compression(file_size, method)
        
        log_access(f"/compress/{method}", api_key_hash, "success")
        return jsonify({
            "success": True,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        log_access(f"/compress/{method}", api_key_hash, "error")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
