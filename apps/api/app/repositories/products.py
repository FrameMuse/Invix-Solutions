from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product


async def list_products(session: AsyncSession, limit: int, offset: int) -> list[Product]:
    statement = (
        select(Product)
        .order_by(Product.created_at.desc(), Product.id.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.scalars(statement)
    return list(result)


async def create_product(session: AsyncSession, title: str, image_key: str) -> Product:
    product = Product(title=title, image_key=image_key)
    session.add(product)
    await session.flush()
    await session.refresh(product)
    await session.commit()
    return product
