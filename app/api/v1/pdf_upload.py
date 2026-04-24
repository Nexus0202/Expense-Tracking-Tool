import logging
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.deps import DbDep
from app.schemas.expense import ExpenseResponse
from app.services.expense_service import ExpenseService
from app.services.pdf_service import PDFService
from app.utils.exceptions import GeminiAPIError, GeminiParseError, PDFParseError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["PDF Upload"])

_pdf_service = PDFService()


@router.post(
    "/pdf",
    response_model=List[ExpenseResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF and auto-extract expenses via Gemini AI",
)
async def upload_pdf(
    db: DbDep,
    file: UploadFile = File(..., description="Bank statement or receipt PDF"),
) -> List[ExpenseResponse]:
    """
    Pipeline:
    1. Validate the uploaded file is a PDF
    2. Extract plain text with PyMuPDF
    3. Send text to Gemini AI for structured expense extraction
    4. Validate the Gemini response
    5. Persist all parsed expenses with `source = "pdf"`
    6. Return the created expense records

    Returns an empty list if the PDF contains no recognisable transactions.
    """
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only PDF files are accepted (.pdf extension required)",
        )

    try:
        parsed = await _pdf_service.extract_and_parse(file)
    except PDFParseError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except (GeminiAPIError, GeminiParseError) as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    if not parsed:
        logger.info("No expenses detected in PDF '%s'", file.filename)
        return []

    created = ExpenseService.bulk_create(db, parsed)
    logger.info("Saved %d expenses from PDF '%s'", len(created), file.filename)
    return created
