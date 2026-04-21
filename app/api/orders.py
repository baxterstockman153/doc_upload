from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse
from app.services import order_service
from app.services.order_service import OrderNotFoundError

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(data: OrderCreate, db: AsyncSession = Depends(get_db)):
    return await order_service.create_order(data, db)


@router.get("", response_model=list[OrderResponse])
async def list_orders(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await order_service.get_orders(db, skip=skip, limit=limit)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await order_service.get_order(order_id, db)
    except OrderNotFoundError:
        raise HTTPException(status_code=404, detail="Order not found")


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(order_id: int, data: OrderUpdate, db: AsyncSession = Depends(get_db)):
    try:
        return await order_service.update_order(order_id, data, db)
    except OrderNotFoundError:
        raise HTTPException(status_code=404, detail="Order not found")


@router.delete("/{order_id}", status_code=204)
async def delete_order(order_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await order_service.delete_order(order_id, db)
    except OrderNotFoundError:
        raise HTTPException(status_code=404, detail="Order not found")
    return Response(status_code=204)
