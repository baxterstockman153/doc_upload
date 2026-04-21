import base64
import json
import logging
import re
from anthropic import AsyncAnthropic
from app.core.config import settings
from app.core.exceptions import ExtractionError
from app.schemas.patient import PatientData

logger = logging.getLogger(__name__)

client = AsyncAnthropic(api_key=settings.anthropic_api_key)


async def extract_patient_data(pdf_bytes: bytes) -> PatientData:
    logger.info("Starting extraction, PDF size: %d bytes", len(pdf_bytes))
    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

    try:
        logger.info("Calling Claude API (model: claude-haiku-4-5-20251001)")
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            system=(
                "You are a data extraction assistant. "
                "Extract patient information from the provided text. "
                "Return ONLY a JSON object with keys: first_name, last_name, date_of_birth (YYYY-MM-DD). "
                "Do not include any explanation, markdown, or text outside the JSON object."
            ),
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Extract patient information from this document.",
                        },
                    ],
                },
                {
                    "role": "assistant",
                    "content": "{",
                },
            ],
        )
        raw_json = "{" + response.content[0].text
        raw_json = re.sub(r"^```(?:json)?\s*", "", raw_json.strip())
        raw_json = re.sub(r"\s*```$", "", raw_json)
        logger.info("Claude raw response: %r", raw_json)
    except Exception as e:
        logger.error("Claude API call failed: %s", e, exc_info=True)
        raise ExtractionError(f"Claude API call failed: {e}") from e

    try:
        data = json.loads(raw_json)
        logger.info("Parsed JSON: %s", data)
    except json.JSONDecodeError as e:
        logger.error("Claude returned non-JSON response. raw=%r error=%s", raw_json, e)
        raise ExtractionError("Claude returned non-JSON response")

    try:
        patient = PatientData(**data)
        logger.info("Extraction successful: %s %s dob=%s", patient.first_name, patient.last_name, patient.date_of_birth)
        return patient
    except Exception as e:
        logger.error("Schema validation failed: %s, data=%s", e, data)
        raise ExtractionError(f"Claude response failed schema validation: {e}") from e
