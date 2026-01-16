from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
from scalar_fastapi import get_scalar_api_reference

from app.api.api_router import master_router
from app.config import cors_settings
from app.core.exception_handlers import setup_exception_handlers
from app.core.middleware import request_logging_middleware
from app.core.security import oauth2_scheme_seller, oauth2_scheme_partner
from app.database.redis import close_redis, get_redis
from app.database.session import create_db_tables


async def wait_for_database(max_retries: int = 10, delay: float = 2.0):
    """Wait for database to be ready with exponential backoff"""
    import asyncio
    from sqlalchemy import text
    from app.database.session import engine
    
    for attempt in range(max_retries):
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = delay * (2 ** min(attempt, 5))  # Exponential backoff, max 32s
                print(f"⏳ Waiting for database... (attempt {attempt + 1}/{max_retries}) - {e}")
                await asyncio.sleep(wait_time)
            else:
                print(f"❌ Database connection failed after {max_retries} attempts: {e}")
                raise
    return False


async def wait_for_redis(max_retries: int = 5, delay: float = 2.0):
    """Wait for Redis to be ready with exponential backoff"""
    import asyncio
    from app.database.redis import get_redis
    
    for attempt in range(max_retries):
        try:
            await get_redis()
            print("✅ Redis connection successful")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = delay * (2 ** min(attempt, 3))  # Exponential backoff, max 8s
                print(f"⏳ Waiting for Redis... (attempt {attempt + 1}/{max_retries}) - {e}")
                await asyncio.sleep(wait_time)
            else:
                print(f"⚠️  Redis connection failed after {max_retries} attempts: {e}")
                print("⚠️  Application will continue without Redis caching")
                return False
    return False


@asynccontextmanager
async def lifespan_handler(app: FastAPI):
    # Startup - run checks in background to not block port binding
    import os
    import asyncio
    port = os.getenv("PORT", "8000")
    print(f"🚀 Starting application on port {port}...")
    print(f"📡 Server will bind to port {port} immediately")

    # Start database/Redis checks in background task (non-blocking)
    async def startup_checks():
        # Wait for database to be ready (with shorter timeout for Render)
        try:
            await wait_for_database(max_retries=10, delay=2.0)
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("⚠️  Application will start but database operations may fail")
            return
        
        # Crear tablas de la base de datos
        try:
            await create_db_tables()
            print("✅ Database tables created/verified")
        except Exception as e:
            print(f"⚠️  Could not create database tables: {e}")

        # Wait for Redis to be ready (non-blocking, continues if fails)
        await wait_for_redis(max_retries=5, delay=2.0)
        print(f"✅ Application startup checks complete")

    # Start checks in background (don't await - let server bind port first)
    asyncio.create_task(startup_checks())

    yield

    # Shutdown
    print("🛑 Shutting down application...")
    await close_redis()


# Section 28: API Documentation - General Metadata
app = FastAPI(
    title="FastShip API",
    description="""
    FastShip is a comprehensive shipping management API that enables sellers and delivery partners 
    to manage shipments efficiently.
    
    ## Features
    
    * **Seller Management**: Register, authenticate, and manage seller accounts
    * **Delivery Partner Management**: Register and manage delivery partner accounts with serviceable locations
    * **Shipment Management**: Create, track, and manage shipments with real-time status updates
    * **Tagging System**: Add tags to shipments for special handling instructions
    * **Location-Based Routing**: Automatic assignment of delivery partners based on destination
    * **Real-time Notifications**: Email and SMS notifications for shipment status changes
    * **Review System**: Collect customer reviews after delivery
    
    ## Authentication
    
    The API uses OAuth2 with JWT tokens. Two separate authentication schemes are available:
    
    * **Seller Authentication**: For seller endpoints (`/seller/*`)
    * **Delivery Partner Authentication**: For delivery partner endpoints (`/partner/*`)
    
    ## Getting Started
    
    1. Register as a seller or delivery partner
    2. Verify your email address
    3. Login to get an access token
    4. Use the token in the Authorization header: `Bearer <token>`
    """,
    version="1.0.0",
    contact={
        "name": "FastShip API Support",
        "email": "support@fastship.com",
        "url": "https://fastship.com/support",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server",
        },
        {
            "url": "https://api.fastship.com",
            "description": "Production server",
        },
    ],
    terms_of_service="https://fastship.com/terms",
    lifespan=lifespan_handler,
)

# Section 27: Add request logging middleware
app.middleware("http")(request_logging_middleware)

# Section 31-32: Add CORS middleware for frontend integration
# CORS origins are configured via CORS_ORIGINS environment variable
# Default includes common development ports, override in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router with /api/v1 prefix for versioning
app.include_router(master_router, prefix="/api/v1")


# Custom OpenAPI schema to include both OAuth2 schemes
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    # Section 28: Enhanced OpenAPI schema with comprehensive metadata
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        contact=app.contact,
        license_info=app.license_info,
        servers=app.servers,
        terms_of_service=app.terms_of_service,
    )
    
    # Replace the single OAuth2 scheme with both seller and partner schemes
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearerSeller": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/seller/token",
                    "scopes": {}
                }
            }
        },
        "OAuth2PasswordBearerPartner": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/partner/token",
                    "scopes": {}
                }
            }
        }
    }
    
    # Update endpoints to use the correct OAuth2 scheme based on path
    # Seller endpoints use OAuth2PasswordBearerSeller
    # Partner endpoints use OAuth2PasswordBearerPartner
    for path, methods in openapi_schema.get("paths", {}).items():
        for method, operation in methods.items():
            if isinstance(operation, dict) and "security" in operation:
                new_security = []
                for sec_item in operation["security"]:
                    # sec_item is a dict like {"OAuth2PasswordBearer": []}
                    if isinstance(sec_item, dict) and "OAuth2PasswordBearer" in sec_item:
                        # Determine which scheme to use based on path
                        if "/seller" in path or (path.startswith("/shipment") and method.lower() == "post"):
                            # Seller endpoints or shipment creation (requires seller)
                            new_security.append({"OAuth2PasswordBearerSeller": []})
                        elif "/partner" in path or (path.startswith("/shipment") and method.lower() == "patch"):
                            # Partner endpoints or shipment update (requires partner)
                            new_security.append({"OAuth2PasswordBearerPartner": []})
                        else:
                            # Default to seller for other endpoints
                            new_security.append({"OAuth2PasswordBearerSeller": []})
                    else:
                        new_security.append(sec_item)
                operation["security"] = new_security
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


### Root Page
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    """Root page with API information and links to documentation"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FastShip API</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(to bottom, hsl(var(--background)), hsl(var(--muted) / 0.2));
                --background: 0 0% 100%;
                --foreground: 222.2 84% 4.9%;
                --muted: 210 40% 96.1%;
                --muted-foreground: 215.4 16.3% 46.9%;
                --card: 0 0% 100%;
                --card-foreground: 222.2 84% 4.9%;
                --border: 214.3 31.8% 91.4%;
                color: hsl(var(--foreground));
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 48px 16px;
            }
            @media (prefers-color-scheme: dark) {
                body {
                    --background: 222.2 84% 4.9%;
                    --foreground: 210 40% 98%;
                    --muted: 217.2 32.6% 17.5%;
                    --muted-foreground: 215 20.2% 65.1%;
                    --card: 222.2 84% 4.9%;
                    --card-foreground: 210 40% 98%;
                    --border: 217.2 32.6% 17.5%;
                }
            }
            .container {
                max-width: 42rem;
                width: 100%;
                text-align: center;
            }
            .header {
                margin-bottom: 32px;
            }
            h1 {
                font-size: 3.75rem;
                line-height: 1;
                font-weight: 700;
                letter-spacing: -0.025em;
                margin-bottom: 16px;
                background: linear-gradient(to right, hsl(var(--foreground)), hsl(var(--foreground) / 0.7));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .subtitle {
                font-size: 1.5rem;
                line-height: 2rem;
                color: hsl(var(--muted-foreground));
                margin-bottom: 8px;
            }
            .description {
                font-size: 1rem;
                color: hsl(var(--muted-foreground) / 0.8);
                max-width: 36rem;
                margin: 0 auto 32px;
                line-height: 1.6;
            }
            .links {
                display: flex;
                flex-direction: column;
                gap: 16px;
                justify-content: center;
                align-items: center;
                margin: 24px 0 48px;
            }
            @media (min-width: 640px) {
                .links {
                    flex-direction: row;
                }
            }
            .link-button {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                border-radius: 0.5rem;
                font-size: 0.875rem;
                font-weight: 500;
                transition: all 0.2s;
                text-decoration: none;
                padding: 12px 24px;
                min-width: 200px;
            }
            .link-button-primary {
                background: hsl(var(--foreground));
                color: hsl(var(--background));
            }
            .link-button-primary:hover {
                opacity: 0.9;
            }
            .link-button-outline {
                border: 1px solid hsl(var(--border));
                background: transparent;
                color: hsl(var(--foreground));
            }
            .link-button-outline:hover {
                background: hsl(var(--muted));
            }
            .features {
                display: grid;
                grid-template-columns: 1fr;
                gap: 24px;
                margin-top: 48px;
                max-width: 48rem;
            }
            @media (min-width: 768px) {
                .features {
                    grid-template-columns: repeat(3, 1fr);
                }
            }
            .feature-card {
                padding: 24px;
                border-radius: 0.5rem;
                border: 1px solid hsl(var(--border));
                background: hsl(var(--card));
                text-align: left;
            }
            .feature-card h3 {
                font-weight: 600;
                margin-bottom: 8px;
                color: hsl(var(--card-foreground));
            }
            .feature-card p {
                font-size: 0.875rem;
                color: hsl(var(--muted-foreground));
                line-height: 1.5;
            }
            .docs-section {
                margin-top: 48px;
                padding-top: 48px;
                border-top: 1px solid hsl(var(--border));
            }
            .docs-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 16px;
                margin-top: 24px;
            }
            .doc-link {
                padding: 20px;
                border-radius: 0.5rem;
                border: 1px solid hsl(var(--border));
                background: hsl(var(--card));
                text-decoration: none;
                transition: all 0.2s;
                display: block;
            }
            .doc-link:hover {
                border-color: hsl(var(--foreground));
                background: hsl(var(--muted));
            }
            .doc-link h3 {
                font-size: 1.1rem;
                font-weight: 600;
                margin-bottom: 8px;
                color: hsl(var(--card-foreground));
            }
            .doc-link p {
                font-size: 0.875rem;
                color: hsl(var(--muted-foreground));
                line-height: 1.5;
            }
            .footer {
                margin-top: 48px;
                padding-top: 24px;
                border-top: 1px solid hsl(var(--border));
                text-align: center;
            }
            .version {
                color: hsl(var(--muted-foreground));
                font-size: 0.875rem;
            }
            .version a {
                color: hsl(var(--foreground));
                text-decoration: none;
            }
            .version a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to FastShip API</h1>
                <p class="subtitle">Your trusted partner for fast and reliable shipment management</p>
                <p class="description">
                    Start your journey with us right now! Manage your shipments efficiently with our comprehensive platform.
                </p>
            </div>
            
            <div class="links">
                <a href="/docs" class="link-button link-button-primary">Swagger UI</a>
                <a href="/scalar" class="link-button link-button-outline">Scalar Docs</a>
            </div>

            <div class="features">
                <div class="feature-card">
                    <h3>Fast Delivery</h3>
                    <p>Get your packages delivered quickly and safely</p>
                </div>
                <div class="feature-card">
                    <h3>Real-Time Tracking</h3>
                    <p>Track your shipments in real-time from start to finish</p>
                </div>
                <div class="feature-card">
                    <h3>Secure Platform</h3>
                    <p>Your data is protected with enterprise-grade security</p>
                </div>
            </div>

            <div class="docs-section">
                <h2 style="font-size: 1.5rem; font-weight: 600; margin-bottom: 8px; color: hsl(var(--foreground));">API Documentation</h2>
                <p style="color: hsl(var(--muted-foreground)); margin-bottom: 24px;">Explore our comprehensive API documentation</p>
                <div class="docs-grid">
                    <a href="/docs" class="doc-link">
                        <h3>Swagger UI</h3>
                        <p>Interactive API documentation and testing interface</p>
                    </a>
                    <a href="/scalar" class="doc-link">
                        <h3>Scalar Docs</h3>
                        <p>Comprehensive API reference documentation</p>
                    </a>
                    <a href="/api/v1/health" class="doc-link">
                        <h3>Health Check</h3>
                        <p>System health and connectivity status</p>
                    </a>
                    <a href="/redoc" class="doc-link">
                        <h3>ReDoc</h3>
                        <p>Alternative API documentation format</p>
                    </a>
                </div>
            </div>
            
            <div class="footer">
                <div class="version">
                    <p>Version 1.0.0 | <a href="https://fastship.com/support">Support</a></p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content


### Scalar API Documentation
@app.get("/scalar", include_in_schema=False)
def get_scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="Scalar API",
    )


### Health Check Endpoint (available at root for backward compatibility)
# Note: /api/v1/health is provided by the health router
@app.get("/health")
async def health_check():
    """Health check endpoint with Redis status (root level for backward compatibility)"""
    redis_status = "disconnected"
    try:
        redis_client = await get_redis()
        await redis_client.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "disconnected"

    return {"status": "healthy", "redis": redis_status, "service": "FastAPI Backend"}


### Test Redis Endpoint
@app.get("/test-redis")
async def test_redis():
    """Test Redis connection and basic operations"""
    from app.database.redis import get_cache, set_cache

    try:
        # Test básico
        redis_client = await get_redis()
        await redis_client.set("test_key", "Redis is working!")
        value = await redis_client.get("test_key")

        # Test con cache functions
        await set_cache("test_cache", "Cache funciona!", 60)
        cached = await get_cache("test_cache")

        # Limpiar
        await redis_client.delete("test_key")
        await redis_client.delete("fastapi:cache:test_cache")

        return {
            "success": True,
            "message": "Redis is working correctly",
            "basic_test": value,
            "cache_test": cached,
            "timestamp": "test_completed",
        }
    except Exception as e:
        return {"success": False, "error": str(e), "message": "Redis test failed"}


# Setup exception handlers
setup_exception_handlers(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
