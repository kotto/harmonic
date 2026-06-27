#!/usr/bin/env python3
"""
🚀 Enhanced Harmonic Hybrid AI v2.0 - Core API
FastAPI server with /generate and /health endpoints
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import time
import json
import asyncio
import logging
from datetime import datetime
import uvicorn

# Import our modules
from mvp_moe_experts import MOEOrchestrator
from compression_5x import HCVCompression5X

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models
class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="Input prompt for generation", min_length=1, max_length=10000)
    use_compression: bool = Field(False, description="Apply 5x compression to experts")
    max_tokens: Optional[int] = Field(1000, description="Maximum tokens to generate", ge=1, le=4000)
    temperature: Optional[float] = Field(0.7, description="Generation temperature", ge=0.0, le=2.0)
    top_p: Optional[float] = Field(0.9, description="Nucleus sampling parameter", ge=0.1, le=1.0)

class GenerateResponse(BaseModel):
    prompt: str
    response: str
    expert_responses: List[Dict[str, Any]]
    selected_experts: List[str]
    processing_time: float
    confidence_score: float
    tokens_used: int
    model_version: str
    compression_applied: bool
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    experts_status: Dict[str, Dict[str, Any]]
    compression_status: Dict[str, Any]
    system_resources: Dict[str, Any]

class MetricsResponse(BaseModel):
    total_requests: int
    requests_per_minute: float
    average_response_time: float
    success_rate: float
    error_distribution: Dict[str, int]
    expert_usage: Dict[str, int]
    compression_stats: Dict[str, Any]

# Global variables
app = FastAPI(
    title="Enhanced Harmonic Hybrid AI v2.0",
    description="MOE with 4 specialized experts and 5x compression",
    version="2.0.0-MVP",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
moe_orchestrator = MOEOrchestrator()
compression_system = HCVCompression5X()

# Metrics tracking
metrics = {
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'response_times': [],
    'start_time': time.time(),
    'expert_usage': {},
    'errors': {},
    'compression_usage': 0
}

# Health monitoring
health_status = {
    'status': 'healthy',
    'last_check': datetime.now().isoformat(),
    'experts_health': {
        'math': {'status': 'healthy', 'last_used': None},
        'logic': {'status': 'healthy', 'last_used': None},
        'code': {'status': 'healthy', 'last_used': None},
        'science': {'status': 'healthy', 'last_used': None}
    }
}

@app.on_event("startup")
async def startup_event():
    """Initialize the API server"""
    logger.info("🚀 Starting Enhanced Harmonic Hybrid AI v2.0 API")
    logger.info("🧠 MOE System: 4 experts initialized")
    logger.info("🗜️ Compression System: 5x compression ready")
    logger.info("📊 Metrics tracking: Enabled")

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Enhanced Harmonic Hybrid AI v2.0 API",
        "version": "2.0.0-MVP",
        "status": "running",
        "docs": "/docs"
    }

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Generate response using MOE system"""
    start_time = time.time()
    
    try:
        logger.info(f"📝 Processing prompt: {request.prompt[:100]}...")
        
        # Update metrics
        metrics['total_requests'] += 1
        
        # Process with MOE orchestrator
        moe_result = moe_orchestrator.process_request(request.prompt)
        
        # Apply compression if requested
        compression_applied = False
        if request.use_compression:
            try:
                # Compress the expert responses
                for expert_resp in moe_result['expert_responses']:
                    expert_data = {
                        'expert_type': expert_resp['expert'],
                        'content': expert_resp['content'],
                        'confidence': expert_resp['confidence']
                    }
                    compression_result = compression_system.compress_expert(expert_data)
                    expert_resp['compressed'] = compression_result['metrics']['compression_ratio']
                
                compression_applied = True
                metrics['compression_usage'] += 1
                logger.info("🗜️ Compression applied successfully")
                
            except Exception as compression_error:
                logger.warning(f"⚠️ Compression failed: {compression_error}")
        
        # Calculate overall confidence
        confidences = [resp['confidence'] for resp in moe_result['expert_responses']]
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Update expert usage
        for expert in moe_result['selected_experts']:
            metrics['expert_usage'][expert] = metrics['expert_usage'].get(expert, 0) + 1
            health_status['experts_health'].get(expert.split('_')[0], {}).update({
                'last_used': datetime.now().isoformat()
            })
        
        # Calculate processing time
        processing_time = time.time() - start_time
        metrics['response_times'].append(processing_time)
        metrics['successful_requests'] += 1
        
        # Calculate tokens used
        tokens_used = sum(resp.get('tokens_used', 0) for resp in moe_result['expert_responses'])
        
        logger.info(f"✅ Request processed in {processing_time:.3f}s")
        
        return GenerateResponse(
            prompt=request.prompt,
            response=moe_result['synthesized_response'],
            expert_responses=moe_result['expert_responses'],
            selected_experts=moe_result['selected_experts'],
            processing_time=processing_time,
            confidence_score=overall_confidence,
            tokens_used=tokens_used,
            model_version=moe_result['moe_version'],
            compression_applied=compression_applied,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        metrics['failed_requests'] += 1
        error_type = type(e).__name__
        metrics['errors'][error_type] = metrics['errors'].get(error_type, 0) + 1
        
        logger.error(f"❌ Generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check"""
    current_time = time.time()
    uptime = current_time - metrics['start_time']
    
    # Calculate average response time
    avg_response_time = (
        sum(metrics['response_times']) / len(metrics['response_times'])
        if metrics['response_times'] else 0.0
    )
    
    # Calculate success rate
    success_rate = (
        metrics['successful_requests'] / metrics['total_requests']
        if metrics['total_requests'] > 0 else 1.0
    )
    
    # Update health status based on metrics
    if success_rate < 0.9:
        health_status['status'] = 'degraded'
    elif avg_response_time > 5.0:
        health_status['status'] = 'slow'
    else:
        health_status['status'] = 'healthy'
    
    health_status['last_check'] = datetime.now().isoformat()
    
    # Get compression stats
    compression_stats = compression_system.get_compression_stats()
    
    # Mock system resources (in real implementation, use psutil)
    system_resources = {
        'cpu_usage': 45.2,
        'memory_usage': 68.7,
        'disk_usage': 34.1,
        'gpu_usage': 78.3
    }
    
    return HealthResponse(
        status=health_status['status'],
        version="2.0.0-MVP",
        uptime=uptime,
        total_requests=metrics['total_requests'],
        successful_requests=metrics['successful_requests'],
        failed_requests=metrics['failed_requests'],
        average_response_time=avg_response_time,
        experts_status=health_status['experts_health'],
        compression_status=compression_stats,
        system_resources=system_resources
    )

@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get detailed metrics"""
    current_time = time.time()
    uptime_minutes = (current_time - metrics['start_time']) / 60
    
    # Calculate requests per minute
    requests_per_minute = metrics['total_requests'] / uptime_minutes if uptime_minutes > 0 else 0
    
    # Calculate average response time
    avg_response_time = (
        sum(metrics['response_times']) / len(metrics['response_times'])
        if metrics['response_times'] else 0.0
    )
    
    # Calculate success rate
    success_rate = (
        metrics['successful_requests'] / metrics['total_requests']
        if metrics['total_requests'] > 0 else 1.0
    )
    
    # Get compression stats
    compression_stats = compression_system.get_compression_stats()
    
    return MetricsResponse(
        total_requests=metrics['total_requests'],
        requests_per_minute=requests_per_minute,
        average_response_time=avg_response_time,
        success_rate=success_rate,
        error_distribution=metrics['errors'],
        expert_usage=metrics['expert_usage'],
        compression_stats=compression_stats
    )

@app.post("/compress")
async def compress_data(data: Dict[str, Any]):
    """Compress data using 5x compression"""
    try:
        result = compression_system.compress_expert(data)
        return {
            "status": "success",
            "compression_ratio": result['metrics']['compression_ratio'],
            "compressed_size": result['metrics']['compressed_size'],
            "original_size": result['metrics']['original_size'],
            "integrity_score": result['metrics']['integrity_score']
        }
    except Exception as e:
        logger.error(f"❌ Compression failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Compression failed: {str(e)}")

@app.get("/experts")
async def get_experts_info():
    """Get information about available experts"""
    return {
        "experts": [
            {
                "name": "mathematical_reasoning",
                "description": "Specialized in mathematical calculations and reasoning",
                "capabilities": ["algebra", "geometry", "statistics", "calculus"]
            },
            {
                "name": "logical_deduction",
                "description": "Expert in logical reasoning and deduction",
                "capabilities": ["syllogisms", "causal reasoning", "pattern recognition"]
            },
            {
                "name": "coding_algorithms",
                "description": "Programming and algorithm development expert",
                "capabilities": ["python", "javascript", "data structures", "algorithms"]
            },
            {
                "name": "scientific_knowledge",
                "description": "Scientific concepts and principles expert",
                "capabilities": ["physics", "chemistry", "biology", "earth science"]
            }
        ],
        "total_experts": 4,
        "orchestration": "MOE (Mixture of Experts)",
        "version": "2.0-MVP"
    }

@app.delete("/metrics/reset")
async def reset_metrics():
    """Reset all metrics (admin only)"""
    global metrics
    metrics = {
        'total_requests': 0,
        'successful_requests': 0,
        'failed_requests': 0,
        'response_times': [],
        'start_time': time.time(),
        'expert_usage': {},
        'errors': {},
        'compression_usage': 0
    }
    return {"status": "metrics_reset", "timestamp": datetime.now().isoformat()}

# Background task for health monitoring
async def background_health_monitor():
    """Background task to monitor system health"""
    while True:
        try:
            # Perform health checks
            await health_check()
            await asyncio.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Health monitoring error: {e}")
            await asyncio.sleep(60)

# Start background monitoring
@app.on_event("startup")
async def start_background_monitoring():
    asyncio.create_task(background_health_monitor())

if __name__ == "__main__":
    print("🚀 Starting Enhanced Harmonic Hybrid AI v2.0 API Server")
    print("📚 Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("📊 Metrics: http://localhost:8000/metrics")
    
    uvicorn.run(
        "api_core:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
