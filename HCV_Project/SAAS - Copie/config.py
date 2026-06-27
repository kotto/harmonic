#!/usr/bin/env python3
"""
⚙️ Configuration for Enhanced Harmonic Hybrid AI v2.0 MVP
Centralized configuration management
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

class Environment(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"

@dataclass
class APIConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    workers: int = 1
    log_level: str = "info"
    cors_origins: List[str] = None
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]

@dataclass
class MOEConfig:
    experts_count: int = 4
    routing_threshold: float = 0.7
    max_tokens_per_expert: int = 1000
    confidence_threshold: float = 0.5
    synthesis_method: str = "weighted"
    
    # Expert weights for synthesis
    expert_weights: Dict[str, float] = None
    
    def __post_init__(self):
        if self.expert_weights is None:
            self.expert_weights = {
                "mathematical_reasoning": 0.3,
                "logical_deduction": 0.25,
                "coding_algorithms": 0.25,
                "scientific_knowledge": 0.2
            }

@dataclass
class CompressionConfig:
    target_ratio: float = 5.0
    integrity_threshold: float = 0.95
    preservation_threshold: float = 0.9
    max_compression_time: float = 1.0
    codebook_size: int = 256
    redundancy_threshold: float = 0.85
    similarity_threshold: float = 0.95

@dataclass
class PerformanceConfig:
    max_request_size: int = 10000
    max_response_time: float = 5.0
    max_concurrent_requests: int = 100
    memory_limit_mb: int = 512
    cache_ttl: int = 3600
    
    # Rate limiting
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst: int = 10

@dataclass
class MonitoringConfig:
    health_check_interval: int = 60
    metrics_retention_hours: int = 24
    log_requests: bool = True
    log_responses: bool = False
    enable_prometheus: bool = False
    enable_tracing: bool = False

class Config:
    """Main configuration class"""
    
    def __init__(self, env: Environment = Environment.DEVELOPMENT):
        self.env = env
        self.api = self._load_api_config()
        self.moe = self._load_moe_config()
        self.compression = self._load_compression_config()
        self.performance = self._load_performance_config()
        self.monitoring = self._load_monitoring_config()
    
    def _load_api_config(self) -> APIConfig:
        """Load API configuration from environment variables"""
        return APIConfig(
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", "8000")),
            debug=os.getenv("API_DEBUG", "false").lower() == "true",
            workers=int(os.getenv("API_WORKERS", "1")),
            log_level=os.getenv("API_LOG_LEVEL", "info"),
            cors_origins=os.getenv("API_CORS_ORIGINS", "*").split(",")
        )
    
    def _load_moe_config(self) -> MOEConfig:
        """Load MOE configuration from environment variables"""
        return MOEConfig(
            experts_count=int(os.getenv("MOE_EXPERTS_COUNT", "4")),
            routing_threshold=float(os.getenv("MOE_ROUTING_THRESHOLD", "0.7")),
            max_tokens_per_expert=int(os.getenv("MOE_MAX_TOKENS", "1000")),
            confidence_threshold=float(os.getenv("MOE_CONFIDENCE_THRESHOLD", "0.5")),
            synthesis_method=os.getenv("MOE_SYNTHESIS_METHOD", "weighted")
        )
    
    def _load_compression_config(self) -> CompressionConfig:
        """Load compression configuration from environment variables"""
        return CompressionConfig(
            target_ratio=float(os.getenv("COMPRESSION_TARGET_RATIO", "5.0")),
            integrity_threshold=float(os.getenv("COMPRESSION_INTEGRITY_THRESHOLD", "0.95")),
            preservation_threshold=float(os.getenv("COMPRESSION_PRESERVATION_THRESHOLD", "0.9")),
            max_compression_time=float(os.getenv("COMPRESSION_MAX_TIME", "1.0")),
            codebook_size=int(os.getenv("COMPRESSION_CODEBOOK_SIZE", "256")),
            redundancy_threshold=float(os.getenv("COMPRESSION_REDUNDANCY_THRESHOLD", "0.85")),
            similarity_threshold=float(os.getenv("COMPRESSION_SIMILARITY_THRESHOLD", "0.95"))
        )
    
    def _load_performance_config(self) -> PerformanceConfig:
        """Load performance configuration from environment variables"""
        return PerformanceConfig(
            max_request_size=int(os.getenv("PERF_MAX_REQUEST_SIZE", "10000")),
            max_response_time=float(os.getenv("PERF_MAX_RESPONSE_TIME", "5.0")),
            max_concurrent_requests=int(os.getenv("PERF_MAX_CONCURRENT", "100")),
            memory_limit_mb=int(os.getenv("PERF_MEMORY_LIMIT_MB", "512")),
            cache_ttl=int(os.getenv("PERF_CACHE_TTL", "3600")),
            rate_limit_requests_per_minute=int(os.getenv("PERF_RATE_LIMIT_RPM", "60")),
            rate_limit_burst=int(os.getenv("PERF_RATE_LIMIT_BURST", "10"))
        )
    
    def _load_monitoring_config(self) -> MonitoringConfig:
        """Load monitoring configuration from environment variables"""
        return MonitoringConfig(
            health_check_interval=int(os.getenv("MONITOR_HEALTH_INTERVAL", "60")),
            metrics_retention_hours=int(os.getenv("MONITOR_METRICS_RETENTION", "24")),
            log_requests=os.getenv("MONITOR_LOG_REQUESTS", "true").lower() == "true",
            log_responses=os.getenv("MONITOR_LOG_RESPONSES", "false").lower() == "true",
            enable_prometheus=os.getenv("MONITOR_PROMETHEUS", "false").lower() == "true",
            enable_tracing=os.getenv("MONITOR_TRACING", "false").lower() == "true"
        )
    
    def get_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return {
            "environment": self.env.value,
            "api": {
                "host": self.api.host,
                "port": self.api.port,
                "debug": self.api.debug,
                "workers": self.api.workers,
                "log_level": self.api.log_level
            },
            "moe": {
                "experts_count": self.moe.experts_count,
                "routing_threshold": self.moe.routing_threshold,
                "max_tokens_per_expert": self.moe.max_tokens_per_expert,
                "confidence_threshold": self.moe.confidence_threshold,
                "synthesis_method": self.moe.synthesis_method,
                "expert_weights": self.moe.expert_weights
            },
            "compression": {
                "target_ratio": self.compression.target_ratio,
                "integrity_threshold": self.compression.integrity_threshold,
                "preservation_threshold": self.compression.preservation_threshold,
                "max_compression_time": self.compression.max_compression_time,
                "codebook_size": self.compression.codebook_size
            },
            "performance": {
                "max_request_size": self.performance.max_request_size,
                "max_response_time": self.performance.max_response_time,
                "max_concurrent_requests": self.performance.max_concurrent_requests,
                "memory_limit_mb": self.performance.memory_limit_mb,
                "rate_limit_requests_per_minute": self.performance.rate_limit_requests_per_minute
            },
            "monitoring": {
                "health_check_interval": self.monitoring.health_check_interval,
                "metrics_retention_hours": self.monitoring.metrics_retention_hours,
                "log_requests": self.monitoring.log_requests,
                "enable_prometheus": self.monitoring.enable_prometheus
            }
        }
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # API validation
        if self.api.port < 1 or self.api.port > 65535:
            issues.append("API port must be between 1 and 65535")
        
        # MOE validation
        if self.moe.experts_count < 1 or self.moe.experts_count > 8:
            issues.append("MOE experts count must be between 1 and 8")
        
        if self.moe.routing_threshold < 0 or self.moe.routing_threshold > 1:
            issues.append("MOE routing threshold must be between 0 and 1")
        
        # Compression validation
        if self.compression.target_ratio < 1 or self.compression.target_ratio > 20:
            issues.append("Compression target ratio must be between 1 and 20")
        
        if self.compression.integrity_threshold < 0 or self.compression.integrity_threshold > 1:
            issues.append("Compression integrity threshold must be between 0 and 1")
        
        # Performance validation
        if self.performance.max_request_size < 100 or self.performance.max_request_size > 100000:
            issues.append("Max request size must be between 100 and 100000 characters")
        
        if self.performance.max_response_time < 0.1 or self.performance.max_response_time > 30:
            issues.append("Max response time must be between 0.1 and 30 seconds")
        
        return issues

# Global configuration instance
def get_config(env: Environment = None) -> Config:
    """Get configuration instance"""
    if env is None:
        env_str = os.getenv("ENVIRONMENT", "development").lower()
        env = Environment(env_str) if env_str in [e.value for e in Environment] else Environment.DEVELOPMENT
    
    return Config(env)

# Environment-specific configurations
def get_development_config() -> Config:
    """Get development configuration"""
    return Config(Environment.DEVELOPMENT)

def get_testing_config() -> Config:
    """Get testing configuration"""
    config = Config(Environment.TESTING)
    config.api.debug = True
    config.monitoring.log_requests = True
    config.monitoring.log_responses = True
    return config

def get_production_config() -> Config:
    """Get production configuration"""
    config = Config(Environment.PRODUCTION)
    config.api.debug = False
    config.api.workers = 4
    config.monitoring.enable_prometheus = True
    return config

# Configuration validation
def validate_config(config: Config) -> bool:
    """Validate configuration"""
    issues = config.validate()
    if issues:
        print("Configuration validation issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    return True

if __name__ == "__main__":
    # Test configuration loading
    config = get_config()
    
    print("🔧 Enhanced Harmonic Hybrid AI v2.0 Configuration")
    print("=" * 50)
    
    print(f"Environment: {config.env.value}")
    print(f"API Host:Port: {config.api.host}:{config.api.port}")
    print(f"MOE Experts: {config.moe.experts_count}")
    print(f"Compression Target: {config.compression.target_ratio}x")
    
    # Validate configuration
    if validate_config(config):
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration has issues")
    
    # Print full configuration
    print("\n📋 Full Configuration:")
    import json
    print(json.dumps(config.get_dict(), indent=2))
