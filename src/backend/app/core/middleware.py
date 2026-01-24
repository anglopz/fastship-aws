"""
HTTP Middleware for request logging and performance monitoring
Section 27: API Middleware Integration
"""
import logging
import os
import uuid
from pathlib import Path
from time import perf_counter
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import logging_settings

# Try to import Celery task (optional - fallback to sync logging if not available)
# Use lazy import to prevent blocking if Celery/Redis is unavailable at startup
CELERY_AVAILABLE = False
_log_request_task = None

def _get_log_request_task():
    """Lazy import of Celery task to prevent blocking at module load time"""
    global CELERY_AVAILABLE, _log_request_task
    if _log_request_task is None:
        try:
            from app.celery_app import log_request_task
            _log_request_task = log_request_task
            CELERY_AVAILABLE = True
        except (ImportError, Exception) as e:
            CELERY_AVAILABLE = False
            logging.warning(f"Celery not available for async logging: {e}, using sync logging")
    return _log_request_task

logger = logging.getLogger(__name__)

# Ensure logs directory exists
_log_dir = Path(logging_settings.LOG_DIR)
_log_dir.mkdir(exist_ok=True)


async def request_logging_middleware(request: Request, call_next) -> Response:
    """
    Middleware to log requests and measure processing time.
    
    Section 27: API Middleware
    - Measures request processing time
    - Logs request details (method, URL, status code, duration)
    - Uses Celery for async logging (if available)
    - Phase 3: Adds request ID tracking for better traceability
    
    Args:
        request: FastAPI Request object
        call_next: Next middleware/endpoint in the chain
        
    Returns:
        Response: HTTP response with X-Request-ID header
    """
    # Phase 3: Generate unique request ID for traceability
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    
    # Start timing
    start = perf_counter()
    
    # Process request
    response: Response = await call_next(request)
    
    # Phase 3: Add request ID to response header
    response.headers["X-Request-ID"] = request_id
    
    # Calculate duration
    end = perf_counter()
    time_taken = round(end - start, 2)
    
    # Extract request details
    method = request.method
    url = str(request.url)
    status_code = response.status_code
    client_ip = request.client.host if request.client else "unknown"
    
    # Phase 3: Enhanced log message with request ID and IP
    # Section 27 format: {method} {url} ({status_code}) {time_taken} s
    # Enhanced format: {method} {url} ({status_code}) {time_taken} s [request_id={id}] [ip={ip}]
    log_message = f"{method} {url} ({status_code}) {time_taken} s [request_id={request_id}] [ip={client_ip}]"
    
    # Log asynchronously via Celery (if available)
    # Use fire-and-forget pattern to prevent blocking if Celery/Redis is unavailable
    log_task = _get_log_request_task()
    if log_task and CELERY_AVAILABLE:
        try:
            # Use apply_async with ignore_result=True for true fire-and-forget
            # This prevents blocking if Redis connection is slow or unavailable
            log_task.apply_async(
                args=[log_message],
                ignore_result=True,
                expires=300  # Expire task after 5 minutes if not processed
            )
        except Exception as e:
            # Fallback to sync logging if Celery fails
            # Don't let logging failures block the response
            try:
                logger.warning(f"Failed to queue log via Celery: {e}, using sync logging")
            except Exception:
                pass  # Even sync logging can fail, don't block
            try:
                _log_request_sync(log_message)
            except Exception:
                pass  # Don't block response if logging fails
    else:
        # Fallback to sync logging
        try:
            _log_request_sync(log_message)
        except Exception:
            pass  # Don't block response if logging fails
    
    return response


def _log_request_sync(log_message: str) -> None:
    """
    Synchronous logging fallback.
    
    Args:
        log_message: Log message to write
    """
    try:
        # Use Python logging module for better structure
        logger.info(log_message)
        
        # Also write to file (Section 27 style)
        log_file_path = _log_dir / logging_settings.LOG_FILE
        with open(log_file_path, "a") as file:
            file.write(f"{log_message}\n")
    except Exception as e:
        # Don't fail the request if logging fails
        logger.error(f"Failed to write log: {e}", exc_info=True)


def get_request_id(request: Request) -> Optional[str]:
    """
    Get request ID from request state (Phase 3 enhancement).
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Request ID string or None if not set
    """
    return getattr(request.state, "request_id", None)

