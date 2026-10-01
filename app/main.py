"""FitBuddy entry point.  Run:  uvicorn app.main:app --reload"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import config
from app.database import init_db
from app.routes import router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="FitBuddy - AI Fitness Plan Generator", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(config.APP_DIR / "static")), name="static")
app.include_router(router)
