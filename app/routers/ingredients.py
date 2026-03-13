import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.ingredient import Ingredient, IngredientAlias, IngredientCategory
from app.schemas.ingredient import IngredientCreate, IngredientRead, IngredientUpdate

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get("/", response_model=list[IngredientRead])
async def list_ingredients(
    q: str | None = None,
    category: IngredientCategory | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Ingredient)
    if q:
        stmt = stmt.where(Ingredient.name.ilike(f"%{q}%"))
    if category:
        stmt = stmt.where(Ingredient.category == category)
    stmt = stmt.order_by(Ingredient.name)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=IngredientRead, status_code=201)
async def create_ingredient(
    body: IngredientCreate, db: AsyncSession = Depends(get_db)
):
    ingredient = Ingredient(
        name=body.name,
        category=body.category,
        default_unit_type=body.default_unit_type,
        parent_id=body.parent_id,
    )
    for alias_name in body.aliases:
        ingredient.aliases.append(IngredientAlias(alias=alias_name))
    db.add(ingredient)
    await db.commit()
    await db.refresh(ingredient)
    return ingredient


@router.get("/{ingredient_id}", response_model=IngredientRead)
async def get_ingredient(
    ingredient_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    ingredient = await db.get(Ingredient, ingredient_id)
    if not ingredient:
        raise HTTPException(404, "Ingredient not found")
    return ingredient


@router.patch("/{ingredient_id}", response_model=IngredientRead)
async def update_ingredient(
    ingredient_id: uuid.UUID,
    body: IngredientUpdate,
    db: AsyncSession = Depends(get_db),
):
    ingredient = await db.get(Ingredient, ingredient_id)
    if not ingredient:
        raise HTTPException(404, "Ingredient not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(ingredient, field, value)
    await db.commit()
    await db.refresh(ingredient)
    return ingredient
