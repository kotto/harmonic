import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request start
        start_time = time.time()
        
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "client_host": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log request completion
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "status_code": response.status_code,
                    "process_time": round(process_time, 4)
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time, 4))
            
            return response
            
        except Exception as exc:
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log request error
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "error": str(exc),
                    "process_time": round(process_time, 4)
                },
                exc_info=True
            )
            
            raise

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, limit_per_minute: int = 60):
        super().__init__(app)
        self.limit_per_minute = limit_per_minute
        self.requests = {}
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_minute = int(time.time() / 60)
        
        # Initialize request count for this client and minute
        key = f"{client_ip}:{current_minute}"
        if key not in self.requests:
            self.requests[key] = 0
        
        # Check rate limit
        if self.requests[key] >= self.limit_per_minute:
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "client_ip": client_ip,
                    "requests": self.requests[key],
                    "limit": self.limit_per_minute
                }
            )
            
            return Response(
                content="Rate limit exceeded",
                status_code=429,
                headers={"Retry-After": "60"}
            )
        
        # Increment request count
        self.requests[key] += 1
        
        # Clean up old entries (older than 2 minutes)
        old_minute = current_minute - 2
        old_keys = [k for k in self.requests.keys() if int(k.split(":")[1]) < old_minute]
        for old_key in old_keys:
            del self.requests[old_key]
        
        # Process request
        return await call_next(request)