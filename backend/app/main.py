from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from app.config import settings
from app.api.routes import cv, jobs, tailor
from app.workers.cv_worker import CVWorker

# Initialize worker
cv_worker = CVWorker()

async def start_background_workers():
    """Start background workers for processing jobs"""
    print("✓ Starting CV parser worker...")
    await cv_worker.start()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    Handles startup and shutdown events.
    """
    # Startup
    print("🚀 Starting TailorJob API...")
    
    # Start background workers
    worker_task = asyncio.create_task(start_background_workers())
    
    yield
    
    # Shutdown
    print("👋 Shutting down TailorJob API...")
    worker_task.cancel()

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    redirect_slashes=False
)

# Add CORS middleware - this must be added LAST so it runs FIRST
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",  # Allow any localhost port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight for 1 hour
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.API_VERSION
    }

@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "message": "TailorJob API",
        "version": settings.API_VERSION,
        "docs": "/docs"
    }

# Include routers
app.include_router(cv.router, prefix="/api/cv", tags=["CV"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(tailor.router, prefix="/api/tailor", tags=["Tailor"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )