"""
Global exception handlers for FastAPI
Section 26: Error Handling Integration
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .exceptions import FastShipError


def _get_handler(exception_class):
    """Create exception handler for a specific exception class"""
    async def handler(request: Request, exc: FastShipError) -> JSONResponse:
        # Optional: Debug printing with rich (if available)
        try:
            from rich import print as rich_print, panel
            rich_print(
                panel.Panel(
                    f"{exc.__class__.__name__}: {exc.message}",
                    title="Handled Exception",
                    border_style="red",
                ),
            )
        except ImportError:
            # Rich not available, use standard print
            import builtins
            builtins.print(f"[Exception] {exc.__class__.__name__}: {exc.message}")
        
        # Return JSONResponse with consistent format
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.__class__.__name__,
                "message": exc.message,
                "status_code": exc.status_code
            }
        )
    return handler


def setup_exception_handlers(app: FastAPI):
    """
    Configure global exception handlers
    Section 26: Uses automatic registration via __subclasses__()
    """
    
    # Section 26: Automatically register all FastShipError subclasses
    exception_classes = FastShipError.__subclasses__()
    for exception_class in exception_classes:
        app.add_exception_handler(
            exception_class,
            _get_handler(exception_class)
        )
    
    # Request validation errors (Pydantic)
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors"""
        return JSONResponse(
            status_code=422,
            content={
                "error": "ValidationError",
                "message": "Validation error",
                "details": exc.errors()
            }
        )
    
    # Starlette HTTP exceptions
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle Starlette HTTP exceptions"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTPException",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        )
    
    # Section 26: Enhanced 500 Internal Server Error handler
    @app.exception_handler(status.HTTP_500_INTERNAL_SERVER_ERROR)
    async def internal_server_error_handler(request: Request, exc: Exception):
        """Handle 500 Internal Server Errors"""
        # Log the error (in production, use proper logging)
        print(f"Internal Server Error: {type(exc).__name__}: {exc}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": "Internal server error",
                "status_code": 500
            },
            headers={
                "X-Error": f"{type(exc).__name__}",
            }
        )
    
    # General exception handler (catch-all)
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle any other unhandled exceptions"""
        # Log the error (in production, use proper logging)
        print(f"Unhandled exception: {type(exc).__name__}: {exc}")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "Internal server error",
                "status_code": 500
            }
        )
    
    return app
