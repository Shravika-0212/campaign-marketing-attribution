"""Main FastAPI Application Entrypoint.
Configures CORS, database lifecycles, and mounts all API routers.
"""
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.models.database import init_db
from backend.app.api.endpoints import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    
    # Auto-populate if empty or run anomaly detection if needed
    from backend.app.models.database import SessionLocal
    from backend.app.models.entities import Campaign, AnomalyIssue, AttributionResult, Order
    db = SessionLocal()
    try:
        if db.query(Campaign).count() == 0:
            from backend.app.generators.synthetic_data import SyntheticDataGenerator
            from backend.app.generators.config import STARTER_CONFIG
            from backend.app.attribution.engine import AttributionEngine
            from backend.app.analytics.anomaly_detector import AnomalyDetectionEngine
            SyntheticDataGenerator(db, STARTER_CONFIG).generate()
            AttributionEngine(db).run_all_models()
            AnomalyDetectionEngine(db).run_detection()
        else:
            if db.query(AnomalyIssue).count() == 0 and db.query(Order).count() > 0:
                from backend.app.analytics.anomaly_detector import AnomalyDetectionEngine
                AnomalyDetectionEngine(db).run_detection()
            if db.query(AttributionResult).count() == 0 and db.query(Order).count() > 0:
                from backend.app.attribution.engine import AttributionEngine
                AttributionEngine(db).run_all_models()
    finally:
        db.close()
        
    yield

app = FastAPI(
    title="Marketing Attribution and ROI Analytics Platform",
    description="End-to-End Analytics Platform for Marketing Attribution & ROI Analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Enable CORS for local development and frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows localhost:5173, localhost:3000, etc.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router
app.include_router(api_router)

# Mount frontend production build if available
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {
            "platform": "Marketing Attribution and ROI Analytics Platform",
            "docs": "/docs",
            "health": "/api/health",
            "dashboard": "/api/dashboard/summary"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
