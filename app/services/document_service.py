import io
from pypdf import PdfReader
from fastapi import UploadFile


async def extract_text_from_upload(file: UploadFile) -> str:
    file_bytes = await file.read()
    reader = PdfReader(io.BytesIO(file_bytes))
    text = " ".join(page.extract_text() or "" for page in reader.pages)
    return text
