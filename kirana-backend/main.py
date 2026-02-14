"""
KiranaGPT Backend - FastAPI Entry Point
WhatsApp-native AI business copilot for India's kirana stores
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from loguru import logger

# Load environment variables
load_dotenv()

# Configure logger
logger.add(
    "logs/kiranagpt_{time}.log",
    rotation="500 MB",
    retention="10 days",
    level=os.getenv("LOG_LEVEL", "INFO"),
)

# Initialize FastAPI app
app = FastAPI(
    title="KiranaGPT Backend",
    description="AI Operating System for Kirana Stores - Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "KiranaGPT Backend",
        "version": "1.0.0",
        "message": "WhatsApp-native AI business copilot for kirana stores",
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "gemini_api_configured": bool(os.getenv("GEMINI_API_KEY")),
        "weather_api_configured": bool(os.getenv("WEATHER_API_KEY")),
        "demo_mode": os.getenv("DEMO_MODE", "false").lower() == "true",
    }


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("🚀 KiranaGPT Backend starting up...")
    logger.info(f"📊 Debug mode: {os.getenv('DEBUG', 'false')}")
    logger.info(f"🎭 Demo mode: {os.getenv('DEMO_MODE', 'false')}")
    logger.info(f"🌐 CORS origins: {allowed_origins}")

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    logger.success("✅ KiranaGPT Backend started successfully!")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("👋 KiranaGPT Backend shutting down...")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"

    logger.info(f"🚀 Starting server on port {port}")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=debug,
        log_level="info",
    )
