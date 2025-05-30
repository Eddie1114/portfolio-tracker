from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import Settings, settings
from app.api.v1.api import api_router
from app.core.database import init_db, engine, Base
from sqlalchemy import text
from datetime import datetime

app = FastAPI(
    title="Portfolio Tracker API",
    description="API for tracking investment portfolios across multiple platforms",
    version="1.0.0"
)

# CORS middleware configuration
origins = [
    "http://localhost:3000",           # Local development
    "http://localhost:5173",           # Vite default port
    "https://portfolio-tracker-eddie1114.vercel.app",  # Vercel deployment
    "https://portfolio-tracker-git-main-eddie1114.vercel.app",  # Vercel preview
    "https://portfolio-tracker-*.vercel.app"  # All Vercel preview deployments
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Initialize database connections
    await init_db()

@app.get("/health")
async def health_check():
    try:
        # Test database connection
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/")
async def root():
    return {
        "message": "Welcome to Portfolio Tracker API",
        "docs": "/docs",
        "redoc": "/redoc"
    }
