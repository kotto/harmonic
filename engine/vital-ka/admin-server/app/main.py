# ──────────────────────────────────────────────
# FastAPI Application Entry Point
# ──────────────────────────────────────────────
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import structlog
import time
import uuid

from app.api import api_router
from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.security import pwd_context

# ──────────────────────────────────────────────
# Structured Logging
# ──────────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.log_format == "json" else structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


# ──────────────────────────────────────────────
# Prometheus Metrics
# ──────────────────────────────────────────────
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
)


# ──────────────────────────────────────────────
# Lifespan
# ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("starting_vitalka_admin_server")
    await init_db()
    logger.info("database_initialized")
    yield
    # Shutdown
    logger.info("shutting_down_vitalka_admin_server")
    await close_db()


# ──────────────────────────────────────────────
# FastAPI App
# ──────────────────────────────────────────────
app = FastAPI(
    title="Vital KA Admin Server",
    description="Administration server for Vital KA medical ecosystem - Doctor registry, version management, system admin",
    version="1.0.0",
    docs_url="/docs" if settings.log_level == "DEBUG" else None,
    redoc_url="/redoc" if settings.log_level == "DEBUG" else None,
    openapi_url="/openapi.json" if settings.log_level == "DEBUG" else None,
    lifespan=lifespan,
)

# ──────────────────────────────────────────────
# Middlewares
# ──────────────────────────────────────────────
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Gzip
app.add_middleware(GZipMiddleware, minimum_size=1000)


# ──────────────────────────────────────────────
# Request ID Middleware
# ──────────────────────────────────────────────
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    request.state.request_id = request_id
    
    # Structlog context
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        # Metrics
        duration = time.time() - start_time
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration)
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
        ).inc()
        
        return response
    except Exception as e:
        duration = time.time() - start_time
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=500,
        ).inc()
        logger.exception("request_failed", path=request.url.path, error=str(e))
        raise


# ──────────────────────────────────────────────
# Exception Handlers
# ──────────────────────────────────────────────
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "details": exc.errors(),
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")


# ──────────────────────────────────────────────
# Health & Metrics (public)
# ──────────────────────────────────────────────
@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok", "service": "vitalka-admin"}


@app.get("/metrics", include_in_schema=False)
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ──────────────────────────────────────────────
# Root
# ──────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "Vital KA Admin Server",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.log_level == "DEBUG",
        log_config=None,  # Use structlog
    )