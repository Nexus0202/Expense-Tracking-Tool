from fastapi import APIRouter

from app.api.v1 import dashboard, expenses, pdf_upload

router = APIRouter(prefix="/api/v1")

router.include_router(expenses.router)
router.include_router(dashboard.router)
router.include_router(pdf_upload.router)
