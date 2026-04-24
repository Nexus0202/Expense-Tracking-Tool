import json
import logging
from datetime import datetime
from typing import List

import google.generativeai as genai
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings
from app.utils.exceptions import GeminiAPIError, GeminiParseError

logger = logging.getLogger(__name__)

_EXTRACTION_PROMPT = """You are a financial data extractor. Analyze the following text from a bank statement, receipt, or financial document.

Extract ALL expense/transaction entries and return them as a JSON array ONLY.

Rules:
- Return ONLY a valid JSON array — no markdown, no prose, no code fences
- Each entry MUST have exactly these keys: date, amount, category, description
- date: string in "YYYY-MM-DD" format
- amount: positive number (float)
- category: one of ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Healthcare", "Travel", "Education", "Other"]
- description: brief description of the transaction

If no expenses are found, return an empty array: []

Text to analyze:
{text}
"""

_VALID_CATEGORIES = {
    "Food", "Transport", "Shopping", "Bills",
    "Entertainment", "Healthcare", "Travel", "Education", "Other",
}


class GeminiService:
    """Clean service wrapper around the Gemini generative AI API."""

    def __init__(self) -> None:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((GeminiAPIError, GeminiParseError)),
        before_sleep=lambda rs: logger.warning(
            "Gemini retry attempt %d after failure", rs.attempt_number
        ),
    )
    def extract_expenses(self, text: str) -> List[dict]:
        """Send extracted PDF text to Gemini and return validated expense dicts."""
        if not text.strip():
            raise ValueError("Empty text provided — nothing to extract")

        prompt = _EXTRACTION_PROMPT.format(text=text[:12_000])

        try:
            response = self.model.generate_content(prompt)
            raw = response.text.strip()
            logger.debug("Gemini raw response (%d chars)", len(raw))
        except Exception as exc:
            logger.error("Gemini API call failed: %s", exc)
            raise GeminiAPIError(str(exc)) from exc

        return self._parse_response(raw)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _parse_response(self, raw: str) -> List[dict]:
        """Strip optional markdown fences and JSON-decode the response."""
        cleaned = raw

        # Remove ```json ... ``` or ``` ... ``` wrappers if Gemini adds them
        if "```json" in cleaned:
            cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error("JSON decode error: %s\nRaw snippet: %.300s", exc, raw)
            raise GeminiParseError(f"Invalid JSON: {exc}") from exc

        if not isinstance(data, list):
            raise GeminiParseError(
                f"Expected a JSON array but got {type(data).__name__}"
            )

        validated: List[dict] = []
        for idx, item in enumerate(data):
            try:
                validated.append(self._validate_item(item, idx))
            except (KeyError, ValueError, TypeError) as exc:
                logger.warning("Skipping expense item %d — %s", idx, exc)

        logger.info("Gemini returned %d valid expense(s)", len(validated))
        return validated

    @staticmethod
    def _validate_item(item: dict, index: int) -> dict:
        """Validate and normalise a single expense dict from Gemini."""
        if not isinstance(item, dict):
            raise ValueError(f"Item {index} is not a dict")

        # --- date ---
        date_raw = item.get("date")
        if not date_raw:
            raise ValueError("Missing 'date'")
        datetime.strptime(str(date_raw), "%Y-%m-%d")  # strict format check

        # --- amount ---
        amount_raw = item.get("amount")
        if amount_raw is None:
            raise ValueError("Missing 'amount'")
        amount = float(amount_raw)
        if amount <= 0:
            raise ValueError(f"Amount must be positive, got {amount}")

        # --- category ---
        category = str(item.get("category", "Other")).strip()
        if category not in _VALID_CATEGORIES:
            category = "Other"

        # --- description ---
        description = str(item.get("description", "")).strip()

        return {
            "date": str(date_raw),
            "amount": round(amount, 2),
            "category": category,
            "description": description,
        }
