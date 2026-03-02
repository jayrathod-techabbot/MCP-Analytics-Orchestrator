from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.routers import analysis, files
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Directories initialized: %s, %s", settings.UPLOAD_DIR, settings.CHARTS_DIR)
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title="AI Data Analyst",
    version="0.1.0",
    description="AI-powered data analysis assistant using OpenAI tool-calling and MCP pattern",
    docs_url="/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings.CHARTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/charts", StaticFiles(directory=str(settings.CHARTS_DIR)), name="charts")

app.include_router(files.router)
app.include_router(analysis.router)


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}
