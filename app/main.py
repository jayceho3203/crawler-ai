# app/main.py
"""
Main FastAPI application with memory optimization for Render free tier
Requests-only mode (no Playwright) for compatibility
"""

import os
import gc
import logging
import psutil
import asyncio
import subprocess
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from .api.routes import router
from .api.debug_routes import router as debug_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Memory monitoring
def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def log_memory_usage():
    """Log current memory usage"""
    memory_mb = get_memory_usage()
    logger.info(f"💾 Current memory usage: {memory_mb:.1f} MB")

async def ensure_playwright_browsers():
    """Ensure Playwright browsers are installed"""
    try:
        # Try to import and launch browser
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
            await browser.close()
        logger.info("✅ Playwright browsers already installed")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Playwright browsers not found: {e}")
        try:
            # Install browsers
            logger.info("🔧 Installing Playwright browsers...")
            result = subprocess.run([
                sys.executable, "-m", "playwright", "install", "chromium"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info("✅ Playwright browsers installed successfully")
                return True
            else:
                logger.error(f"❌ Failed to install Playwright browsers: {result.stderr}")
                return False
        except Exception as install_error:
            logger.error(f"❌ Error installing Playwright browsers: {install_error}")
            return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with memory optimization"""
    # Startup
    logger.info("🚀 Starting crawler-ai service...")
    log_memory_usage()
    
    # Ensure Playwright browsers are installed
    await ensure_playwright_browsers()
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down crawler-ai service...")
    # Force garbage collection
    gc.collect()
    log_memory_usage()

# Create FastAPI app with memory optimization
app = FastAPI(
    title="Crawler AI Service",
    description="AI-powered web crawler for career pages and contact information (requests-only mode)",
    version="1.0.0",
    lifespan=lifespan,
    # Enable Swagger UI for testing (even in production)
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Gzip compression to reduce memory usage
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Memory monitoring middleware
@app.middleware("http")
async def memory_monitoring_middleware(request: Request, call_next):
    """Monitor memory usage for each request"""
    start_memory = get_memory_usage()
    
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"❌ Request failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(e)}
        )
    finally:
        end_memory = get_memory_usage()
        memory_diff = end_memory - start_memory
        
        if memory_diff > 50:  # Log if memory increased by more than 50MB
            logger.warning(f"⚠️ Memory increased by {memory_diff:.1f} MB during request")
        
        # Force garbage collection if memory usage is high
        if end_memory > 400:  # 400MB threshold for Render free tier
            logger.warning(f"⚠️ High memory usage ({end_memory:.1f} MB), forcing cleanup")
            gc.collect()
            log_memory_usage()

# Include routers
app.include_router(router, prefix="/api/v1")
app.include_router(debug_router)  # Debug routes không cần prefix

# No alias endpoint needed - all endpoints use /api/v1 prefix

# Health check endpoint with memory info
@app.get("/health")
async def health_check():
    """Health check with memory usage information"""
    memory_mb = get_memory_usage()
    
    return {
        "status": "healthy",
        "mode": "requests-only",
        "memory_usage_mb": round(memory_mb, 1),
        "memory_limit_mb": 512,  # Render free tier limit
        "memory_percentage": round((memory_mb / 512) * 100, 1)
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Crawler AI Service",
        "version": "1.0.0",
        "mode": "requests-only",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "career_pages": "/api/v1/detect_career_pages_scrapy",
            "job_urls": "/api/v1/extract_job_urls",
            "job_details": "/api/v1/extract_job_details",
            "ai_analysis": "/api/v1/ai_agent_analysis"
        }
    }

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with memory cleanup"""
    logger.error(f"❌ Unhandled exception: {exc}")
    
    # Force cleanup on errors
    gc.collect()
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "memory_usage_mb": round(get_memory_usage(), 1)
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    # Memory-optimized uvicorn settings
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        workers=1,  # Single worker to reduce memory usage
        loop="asyncio",
        access_log=False,  # Disable access logs to save memory
        log_level="warning"
    ) 