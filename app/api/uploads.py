from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.exceptions import ExtractionError
from app.schemas.order import OrderCreate, OrderResponse
from app.services import extraction_service, order_service

router = APIRouter(prefix="/orders", tags=["uploads"])


@router.post("/upload", response_model=OrderResponse, status_code=201)
async def upload_order(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    pdf_bytes = await file.read()

    try:
        patient_data = await extraction_service.extract_patient_data(pdf_bytes)
    except ExtractionError as e:
        raise HTTPException(status_code=422, detail=str(e))

    order_create = OrderCreate(
        first_name=patient_data.first_name,
        last_name=patient_data.last_name,
        date_of_birth=patient_data.date_of_birth,
        source_file_name=file.filename,
    )

    order = await order_service.create_order(order_create, db)
    return order
