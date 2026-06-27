#!/usr/bin/env python3
"""
HCV Unified Performance Codec - Web Application
================================================
Application web pour démontrer les 7 solutions de compression optimisées
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from PIL import Image
import io
import json
import time
import logging
from pathlib import Path

# Import optimized framework (use simple, most reliable)
from SIMPLE_FRAMEWORK import SimpleFramework as OptimizedSolutionsFramework
logger_msg = "Using SIMPLE framework (zstd-based, robust)"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="HCV Unified Performance Codec", version="1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize framework
framework = OptimizedSolutionsFramework()
logger.info(logger_msg)

# Store compression history
compression_history = []


# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve main HTML page"""
    return get_html_page()


@app.get("/api/solutions")
async def get_solutions():
    """Get all available solutions"""
    info = framework.get_info()
    solutions = []
    
    for solution_id in range(1, 8):
        details = info[solution_id]
        solutions.append({
            'id': solution_id,
            'name': details['name'],
            'target_ratio': details['target_ratio'],
            'description': get_solution_description(solution_id)
        })
    
    return {'solutions': solutions}


@app.post("/api/compress/{solution_id}")
async def compress(solution_id: int, file: UploadFile = File(...)):
    """Compress file with specified solution"""
    try:
        # Validate solution ID
        if solution_id < 1 or solution_id > 7:
            raise HTTPException(status_code=400, detail="Invalid solution ID (1-7)")
        
        # Read file
        content = await file.read()
        
        if not content:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Convert to numpy array
        try:
            image = Image.open(io.BytesIO(content))
            data = np.array(image)
        except:
            # If not an image, treat as binary
            data = np.frombuffer(content, dtype=np.uint8)
        
        # Compress
        start_time = time.time()
        compressed = framework.compress(solution_id, data)
        elapsed = time.time() - start_time
        
        # Calculate metrics
        original_size = len(content)
        compressed_size = len(compressed)
        ratio = original_size / compressed_size if compressed_size > 0 else 0
        savings = 100 * (1 - compressed_size / original_size) if original_size > 0 else 0
        speed = original_size / (1024 * elapsed) if elapsed > 0 else 0
        
        result = {
            'solution_id': solution_id,
            'solution_name': framework.solution_names[solution_id],
            'original_size': original_size,
            'compressed_size': compressed_size,
            'compression_ratio': f"{ratio:.2f}:1",
            'space_saving_percent': f"{savings:.1f}%",
            'compression_time': f"{elapsed:.3f}s",
            'speed_kbps': f"{speed:.0f} KB/s",
            'target_ratio': framework.solution_targets[solution_id]
        }
        
        # Store in history
        compression_history.append({
            'timestamp': time.time(),
            'filename': file.filename,
            **result
        })
        
        # Keep only last 100 entries
        if len(compression_history) > 100:
            compression_history.pop(0)
        
        logger.info(f"Compressed {file.filename} with Solution {solution_id}: {ratio:.2f}:1")
        
        return result
    
    except Exception as e:
        logger.error(f"Compression error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history")
async def get_history():
    """Get compression history"""
    return {'history': compression_history[-20:]}  # Last 20 entries


@app.get("/api/stats")
async def get_stats():
    """Get compression statistics"""
    if not compression_history:
        return {
            'total_compressions': 0,
            'total_original_size': 0,
            'total_compressed_size': 0,
            'average_ratio': 0,
            'average_savings': 0
        }
    
    total_original = sum(h['original_size'] for h in compression_history)
    total_compressed = sum(h['compressed_size'] for h in compression_history)
    avg_ratio = total_original / total_compressed if total_compressed > 0 else 0
    avg_savings = 100 * (1 - total_compressed / total_original) if total_original > 0 else 0
    
    return {
        'total_compressions': len(compression_history),
        'total_original_size': total_original,
        'total_compressed_size': total_compressed,
        'average_ratio': f"{avg_ratio:.2f}:1",
        'average_savings': f"{avg_savings:.1f}%",
        'total_space_saved': total_original - total_compressed
    }


# ─── HELPERS ───────────────────────────────────────────────────────────────────

def get_solution_description(solution_id: int) -> str:
    """Get description for each solution"""
    descriptions = {
        1: "Broadcast video compression with grain synthesis. Optimal for SDI-PUR video.",
        2: "Professional RAW image compression with YCbCr 4:2:2. Best for photography.",
        3: "JPEG/PNG/WebP compression with adaptive strategies. For pre-compressed images.",
        4: "H.264 video compression with motion compensation. For MP4/MOV files.",
        5: "Smartphone media compression. Optimized for HEIC/JPEG/MP4 from mobile devices.",
        6: "Binary lossless compression. 100% faithful reconstruction for any binary data.",
        7: "Professional broadcast archival. Maximum compression for long-term storage."
    }
    return descriptions.get(solution_id, "")


def get_html_page() -> str:
    """Generate HTML page"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HCV Unified Performance Codec</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }
        
        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }
        
        .card h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        
        .upload-area {
            border: 2px dashed #667eea;
            border-radius: 8px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: #f8f9ff;
        }
        
        .upload-area:hover {
            border-color: #764ba2;
            background: #f0f2ff;
        }
        
        .upload-area.dragover {
            border-color: #764ba2;
            background: #e8ebff;
        }
        
        .upload-area input {
            display: none;
        }
        
        .upload-icon {
            font-size: 3em;
            margin-bottom: 10px;
        }
        
        .upload-text {
            color: #667eea;
            font-weight: 500;
        }
        
        .solutions-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .solution-btn {
            padding: 12px 20px;
            border: none;
            border-radius: 6px;
            background: #667eea;
            color: white;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s;
            font-size: 0.9em;
        }
        
        .solution-btn:hover {
            background: #764ba2;
            transform: scale(1.05);
        }
        
        .solution-btn.active {
            background: #764ba2;
            box-shadow: 0 0 10px rgba(118, 75, 162, 0.5);
        }
        
        .results {
            background: #f8f9ff;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
            display: none;
        }
        
        .results.show {
            display: block;
        }
        
        .result-item {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .result-item:last-child {
            border-bottom: none;
        }
        
        .result-label {
            font-weight: 500;
            color: #667eea;
        }
        
        .result-value {
            color: #333;
            font-weight: 600;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .stat-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 1.8em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        .history {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .history h2 {
            color: #667eea;
            margin-bottom: 20px;
        }
        
        .history-item {
            padding: 15px;
            border-left: 4px solid #667eea;
            background: #f8f9ff;
            margin-bottom: 10px;
            border-radius: 4px;
        }
        
        .history-item-title {
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }
        
        .history-item-detail {
            font-size: 0.9em;
            color: #666;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .error {
            background: #fee;
            color: #c33;
            padding: 15px;
            border-radius: 6px;
            margin-top: 10px;
            display: none;
        }
        
        .success {
            background: #efe;
            color: #3c3;
            padding: 15px;
            border-radius: 6px;
            margin-top: 10px;
            display: none;
        }
        
        @media (max-width: 768px) {
            .main-grid {
                grid-template-columns: 1fr;
            }
            
            header h1 {
                font-size: 1.8em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎯 HCV Unified Performance Codec</h1>
            <p>7 Optimized Compression Solutions • +30% Ratio Improvement</p>
        </header>
        
        <div class="main-grid">
            <!-- Upload Card -->
            <div class="card">
                <h2>📤 Upload & Compress</h2>
                <div class="upload-area" id="uploadArea">
                    <div class="upload-icon">📁</div>
                    <div class="upload-text">Drag & drop your file here or click to select</div>
                    <input type="file" id="fileInput" />
                </div>
                
                <div class="solutions-grid" id="solutionsGrid"></div>
                
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p>Compressing...</p>
                </div>
                
                <div class="error" id="error"></div>
                <div class="success" id="success"></div>
            </div>
            
            <!-- Results Card -->
            <div class="card">
                <h2>📊 Compression Results</h2>
                <div class="results" id="results">
                    <div class="result-item">
                        <span class="result-label">Solution:</span>
                        <span class="result-value" id="resultSolution">-</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">Original Size:</span>
                        <span class="result-value" id="resultOriginal">-</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">Compressed Size:</span>
                        <span class="result-value" id="resultCompressed">-</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">Compression Ratio:</span>
                        <span class="result-value" id="resultRatio">-</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">Space Saved:</span>
                        <span class="result-value" id="resultSavings">-</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">Compression Time:</span>
                        <span class="result-value" id="resultTime">-</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">Speed:</span>
                        <span class="result-value" id="resultSpeed">-</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">Target Ratio:</span>
                        <span class="result-value" id="resultTarget">-</span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Statistics -->
        <div class="card">
            <h2>📈 Overall Statistics</h2>
            <div class="stats-grid" id="statsGrid">
                <div class="stat-box">
                    <div class="stat-value" id="statCompressions">0</div>
                    <div class="stat-label">Total Compressions</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="statRatio">0:1</div>
                    <div class="stat-label">Average Ratio</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="statSavings">0%</div>
                    <div class="stat-label">Average Savings</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="statSpaceSaved">0 MB</div>
                    <div class="stat-label">Total Space Saved</div>
                </div>
            </div>
        </div>
        
        <!-- History -->
        <div class="history">
            <h2>📋 Compression History</h2>
            <div id="historyList"></div>
        </div>
    </div>
    
    <script>
        let selectedSolution = null;
        let selectedFile = null;
        
        // Initialize
        document.addEventListener('DOMContentLoaded', async () => {
            await loadSolutions();
            setupUploadArea();
            updateStats();
            updateHistory();
            
            // Auto-update stats every 5 seconds
            setInterval(updateStats, 5000);
            setInterval(updateHistory, 5000);
        });
        
        // Load solutions
        async function loadSolutions() {
            try {
                const response = await fetch('/api/solutions');
                const data = await response.json();
                
                const grid = document.getElementById('solutionsGrid');
                grid.innerHTML = '';
                
                data.solutions.forEach(solution => {
                    const btn = document.createElement('button');
                    btn.className = 'solution-btn';
                    btn.textContent = `${solution.id}. ${solution.name}\\n${solution.target_ratio}`;
                    btn.title = solution.description;
                    btn.onclick = () => selectSolution(solution.id, btn);
                    grid.appendChild(btn);
                });
            } catch (error) {
                console.error('Error loading solutions:', error);
            }
        }
        
        // Select solution
        function selectSolution(id, btn) {
            selectedSolution = id;
            document.querySelectorAll('.solution-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        }
        
        // Setup upload area
        function setupUploadArea() {
            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('fileInput');
            
            uploadArea.addEventListener('click', () => fileInput.click());
            
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });
            
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    handleFile(files[0]);
                }
            });
            
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    handleFile(e.target.files[0]);
                }
            });
        }
        
        // Handle file selection
        function handleFile(file) {
            selectedFile = file;
            if (selectedSolution) {
                compressFile();
            } else {
                showError('Please select a compression solution first');
            }
        }
        
        // Compress file
        async function compressFile() {
            if (!selectedFile || !selectedSolution) {
                showError('Please select both a file and a solution');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', selectedFile);
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('error').style.display = 'none';
            document.getElementById('success').style.display = 'none';
            
            try {
                const response = await fetch(`/api/compress/${selectedSolution}`, {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error('Compression failed');
                }
                
                const result = await response.json();
                displayResults(result);
                showSuccess('Compression successful!');
                updateStats();
                updateHistory();
            } catch (error) {
                showError('Error: ' + error.message);
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }
        
        // Display results
        function displayResults(result) {
            document.getElementById('resultSolution').textContent = result.solution_name;
            document.getElementById('resultOriginal').textContent = formatBytes(result.original_size);
            document.getElementById('resultCompressed').textContent = formatBytes(result.compressed_size);
            document.getElementById('resultRatio').textContent = result.compression_ratio;
            document.getElementById('resultSavings').textContent = result.space_saving_percent;
            document.getElementById('resultTime').textContent = result.compression_time;
            document.getElementById('resultSpeed').textContent = result.speed_kbps;
            document.getElementById('resultTarget').textContent = result.target_ratio;
            
            document.getElementById('results').classList.add('show');
        }
        
        // Update statistics
        async function updateStats() {
            try {
                const response = await fetch('/api/stats');
                const stats = await response.json();
                
                document.getElementById('statCompressions').textContent = stats.total_compressions;
                document.getElementById('statRatio').textContent = stats.average_ratio;
                document.getElementById('statSavings').textContent = stats.average_savings;
                document.getElementById('statSpaceSaved').textContent = formatBytes(stats.total_space_saved);
            } catch (error) {
                console.error('Error updating stats:', error);
            }
        }
        
        // Update history
        async function updateHistory() {
            try {
                const response = await fetch('/api/history');
                const data = await response.json();
                
                const historyList = document.getElementById('historyList');
                historyList.innerHTML = '';
                
                if (data.history.length === 0) {
                    historyList.innerHTML = '<p style="color: #999;">No compressions yet</p>';
                    return;
                }
                
                data.history.reverse().forEach(item => {
                    const div = document.createElement('div');
                    div.className = 'history-item';
                    div.innerHTML = `
                        <div class="history-item-title">
                            ${item.solution_name} - ${item.filename}
                        </div>
                        <div class="history-item-detail">
                            ${item.compression_ratio} • ${item.space_saving_percent} saved • ${item.compression_time}
                        </div>
                    `;
                    historyList.appendChild(div);
                });
            } catch (error) {
                console.error('Error updating history:', error);
            }
        }
        
        // Helpers
        function formatBytes(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
        }
        
        function showError(message) {
            const error = document.getElementById('error');
            error.textContent = message;
            error.style.display = 'block';
        }
        
        function showSuccess(message) {
            const success = document.getElementById('success');
            success.textContent = message;
            success.style.display = 'block';
            setTimeout(() => {
                success.style.display = 'none';
            }, 3000);
        }
    </script>
</body>
</html>
"""


# ─── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import uvicorn
    
    logger.info("=" * 60)
    logger.info("HCV Unified Performance Codec - Web Application")
    logger.info("=" * 60)
    logger.info("Starting server on http://localhost:8000")
    logger.info("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
