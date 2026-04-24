from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router
from app.config import settings
from app.database.session import engine
from app.models import Expense  # noqa: F401 — registers model with metadata
from app.models.base import Base
from app.utils.exceptions import (
    ExpenseTrackerException,
    expense_tracker_exception_handler,
    generic_exception_handler,
)
from app.utils.logging_config import setup_logging

setup_logging(debug=settings.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="A production-ready Expense Tracking API with PDF parsing and Gemini AI.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(ExpenseTrackerException, expense_tracker_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.include_router(router)


@app.get("/health", tags=["Health"], summary="Health check")
def health_check() -> dict:
    return {"status": "healthy", "app": settings.APP_NAME, "version": "1.0.0"}
