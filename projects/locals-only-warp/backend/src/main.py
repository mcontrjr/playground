"""
Main FastAPI application for Google Places API backend.
"""
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .config import get_settings
from .routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting up Google Places API backend...")
    settings = get_settings()
    
    # Log configuration (without sensitive data)
    logger.info(f"API Title: {settings.api_title}")
    logger.info(f"API Version: {settings.api_version}")
    logger.info(f"Debug Mode: {settings.debug}")
    logger.info(f"Google Maps Base URL: {settings.google_maps_base_url}")
    
    # Verify API key is present (but don't log it)
    if settings.google_maps_api_key:
        logger.info("Google Maps API key loaded successfully")
    else:
        logger.error("Google Maps API key not found! Check your .env file.")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Google Places API backend...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware (configure for production)
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["*"]
    )
    
    # Include routes
    app.include_router(router, prefix="/api/v1")
    
    return app


# Create the app instance
app = create_app()


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint that redirects to documentation."""
    return {
        "message": "Google Places API Backend",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/v1/health",
        "version": get_settings().api_version
    }


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
    )
