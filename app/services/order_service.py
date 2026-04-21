from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.order import Order
from app.schemas.order import OrderCreate, OrderUpdate


class OrderNotFoundError(Exception):
    pass


async def create_order(data: OrderCreate, db: AsyncSession) -> Order:
    order = Order(**data.model_dump())
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


async def get_order(order_id: int, db: AsyncSession) -> Order:
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if order is None:
        raise OrderNotFoundError(f"Order {order_id} not found")
    return order


async def get_orders(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Order]:
    result = await db.execute(select(Order).offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_order(order_id: int, data: OrderUpdate, db: AsyncSession) -> Order:
    order = await get_order(order_id, db)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    await db.commit()
    await db.refresh(order)
    return order


async def delete_order(order_id: int, db: AsyncSession) -> None:
    order = await get_order(order_id, db)
    await db.delete(order)
    await db.commit()
