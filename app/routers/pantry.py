import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.pantry import PantryItem
from app.schemas.pantry import PantryItemCreate, PantryItemRead, PantryItemUpdate

router = APIRouter(prefix="/pantry", tags=["pantry"])


@router.get("/items", response_model=list[PantryItemRead])
async def list_pantry_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PantryItem))
    items = result.scalars().all()
    return [
        PantryItemRead(
            id=item.id,
            ingredient_id=item.ingredient_id,
            quantity=float(item.quantity),
            unit=item.unit,
            expiry_date=item.expiry_date,
            note=item.note,
            ingredient_name=item.ingredient.name if item.ingredient else None,
        )
        for item in items
    ]


@router.post("/items", response_model=PantryItemRead, status_code=201)
async def add_pantry_item(
    body: PantryItemCreate, db: AsyncSession = Depends(get_db)
):
    item = PantryItem(**body.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return PantryItemRead(
        id=item.id,
        ingredient_id=item.ingredient_id,
        quantity=float(item.quantity),
        unit=item.unit,
        expiry_date=item.expiry_date,
        note=item.note,
        ingredient_name=item.ingredient.name if item.ingredient else None,
    )


@router.get("/items/{item_id}", response_model=PantryItemRead)
async def get_pantry_item(
    item_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    item = await db.get(PantryItem, item_id)
    if not item:
        raise HTTPException(404, "Pantry item not found")
    return PantryItemRead(
        id=item.id,
        ingredient_id=item.ingredient_id,
        quantity=float(item.quantity),
        unit=item.unit,
        expiry_date=item.expiry_date,
        note=item.note,
        ingredient_name=item.ingredient.name if item.ingredient else None,
    )


@router.patch("/items/{item_id}", response_model=PantryItemRead)
async def update_pantry_item(
    item_id: uuid.UUID,
    body: PantryItemUpdate,
    db: AsyncSession = Depends(get_db),
):
    item = await db.get(PantryItem, item_id)
    if not item:
        raise HTTPException(404, "Pantry item not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)
    return PantryItemRead(
        id=item.id,
        ingredient_id=item.ingredient_id,
        quantity=float(item.quantity),
        unit=item.unit,
        expiry_date=item.expiry_date,
        note=item.note,
        ingredient_name=item.ingredient.name if item.ingredient else None,
    )


@router.delete("/items/{item_id}", status_code=204)
async def delete_pantry_item(
    item_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    item = await db.get(PantryItem, item_id)
    if not item:
        raise HTTPException(404, "Pantry item not found")
    await db.delete(item)
    await db.commit()


@router.get("/expiring", response_model=list[PantryItemRead])
async def expiring_items(
    days: int = 7, db: AsyncSession = Depends(get_db)
):
    cutoff = datetime.date.today() + datetime.timedelta(days=days)
    result = await db.execute(
        select(PantryItem).where(PantryItem.expiry_date <= cutoff)
    )
    items = result.scalars().all()
    return [
        PantryItemRead(
            id=item.id,
            ingredient_id=item.ingredient_id,
            quantity=float(item.quantity),
            unit=item.unit,
            expiry_date=item.expiry_date,
            note=item.note,
            ingredient_name=item.ingredient.name if item.ingredient else None,
        )
        for item in items
    ]
