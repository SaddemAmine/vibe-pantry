import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.matching import RecipeMatch, ShoppingList
from app.services.matching import match_recipes, recipe_availability
from app.services.shopping import generate_shopping_list

router = APIRouter(tags=["matching"])


@router.get("/recipes/matchable", response_model=list[RecipeMatch])
async def matchable_recipes(
    min_coverage: float = 0.0,
    db: AsyncSession = Depends(get_db),
):
    matches = await match_recipes(db, min_coverage=min_coverage)
    return matches


@router.get("/recipes/{recipe_id}/availability", response_model=RecipeMatch)
async def check_availability(
    recipe_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    return await recipe_availability(db, recipe_id)


@router.post("/shopping-list", response_model=ShoppingList)
async def shopping_list(
    recipe_ids: list[uuid.UUID],
    db: AsyncSession = Depends(get_db),
):
    return await generate_shopping_list(db, recipe_ids)
