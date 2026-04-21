import base64
import json
from anthropic import AsyncAnthropic
from app.core.config import settings
from app.core.exceptions import ExtractionError
from app.schemas.patient import PatientData

client = AsyncAnthropic(api_key=settings.anthropic_api_key)


async def extract_patient_data(pdf_bytes: bytes) -> PatientData:
    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

    try:
        response = await client.messages.create(
            model="claude-3-5-haiku-20241022",
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
                }
            ],
        )
        raw_json = response.content[0].text
    except Exception as e:
        raise ExtractionError(f"Claude API call failed: {e}") from e

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        raise ExtractionError("Claude returned non-JSON response")

    try:
        return PatientData(**data)
    except Exception as e:
        raise ExtractionError(f"Claude response failed schema validation: {e}") from e
