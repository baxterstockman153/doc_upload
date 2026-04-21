import logging
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.exceptions import ExtractionError
from app.schemas.order import OrderCreate, OrderResponse
from app.services import extraction_service, order_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["uploads"])


@router.post("/upload", response_model=OrderResponse, status_code=201)
async def upload_order(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    logger.info("Upload request: filename=%r content_type=%r", file.filename, file.content_type)

    if file.content_type != "application/pdf":
        logger.warning("Rejected non-PDF upload: content_type=%r", file.content_type)
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    pdf_bytes = await file.read()
    logger.info("Read %d bytes from upload", len(pdf_bytes))

    try:
        patient_data = await extraction_service.extract_patient_data(pdf_bytes)
    except ExtractionError as e:
        logger.error("Extraction failed: %s", e)
        raise HTTPException(
            status_code=422,
            detail="Failed to extract patient data from the uploaded document. Please ensure it is a valid patient record PDF."
        )

    order_create = OrderCreate(
        first_name=patient_data.first_name,
        last_name=patient_data.last_name,
        date_of_birth=patient_data.date_of_birth,
        source_file_name=file.filename,
    )

    order = await order_service.create_order(order_create, db)
    return order
