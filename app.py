from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import router
from database.database import init_db


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):

    init_db()

    yield


app = FastAPI(
    title="Z-Sentinel API",
    version="1.0.0",
    description=(
        "AI-assisted real-time fraud "
        "detection and risk analysis system."
    ),
    lifespan=lifespan,
)


app.include_router(
    router,
    prefix="/api",
)


@app.get("/")
def root():

    return {
        "service": "Z-Sentinel",
        "status": "running",
        "docs": "/docs",
        "health": "/api/health",
    }