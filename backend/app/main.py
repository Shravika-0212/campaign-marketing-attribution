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
    yield

app = FastAPI(
    title="Marketing Attribution and ROI Analytics Platform",
    description="End-to-End Analytics Platform for YottaFlex AI Recruitment Drive",
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
