import logging
from typing import List

import fitz  # PyMuPDF
from fastapi import UploadFile

from app.services.gemini_service import GeminiService
from app.utils.exceptions import PDFParseError

logger = logging.getLogger(__name__)


class PDFService:
    """Orchestrates PDF text extraction → Gemini parsing → validated expense dicts."""

    def __init__(self) -> None:
        self.gemini = GeminiService()

    async def extract_and_parse(self, file: UploadFile) -> List[dict]:
        """
        Full pipeline:
        1. Read uploaded PDF bytes
        2. Extract plain text with PyMuPDF
        3. Send text to Gemini for structured extraction
        4. Return list of validated expense dicts
        """
        text = await self._extract_text(file)

        if not text.strip():
            raise PDFParseError("No readable text found in the PDF")

        logger.info("Extracted %d characters from PDF '%s'", len(text), file.filename)
        return self.gemini.extract_expenses(text)

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    async def _extract_text(file: UploadFile) -> str:
        """Read PDF bytes and extract page text using PyMuPDF."""
        content = await file.read()

        if not content:
            raise PDFParseError("Uploaded file is empty")

        try:
            pdf = fitz.open(stream=content, filetype="pdf")
        except Exception as exc:
            raise PDFParseError(f"Cannot open PDF: {exc}") from exc

        if pdf.page_count == 0:
            pdf.close()
            raise PDFParseError("PDF has no pages")

        pages: List[str] = []
        for page_num in range(pdf.page_count):
            page_text = pdf[page_num].get_text()
            if page_text.strip():
                pages.append(f"--- Page {page_num + 1} ---\n{page_text}")

        pdf.close()
        return "\n".join(pages)
