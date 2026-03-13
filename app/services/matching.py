import uuid
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingredient import Ingredient
from app.models.pantry import PantryItem
from app.models.recipe import Recipe, RecipeIngredient
from app.schemas.matching import IngredientMatch, RecipeMatch


async def _build_pantry_index(db: AsyncSession) -> dict[uuid.UUID, float]:
    """Map ingredient_id → total available quantity."""
    result = await db.execute(select(PantryItem))
    index: dict[uuid.UUID, float] = defaultdict(float)
    for item in result.scalars().all():
        index[item.ingredient_id] += float(item.quantity)
    return index


async def _build_parent_map(db: AsyncSession) -> dict[uuid.UUID, uuid.UUID | None]:
    """Map ingredient_id → parent_id (or None)."""
    result = await db.execute(select(Ingredient))
    return {i.id: i.parent_id for i in result.scalars().all()}


def _check_available(
    ingredient_id: uuid.UUID,
    pantry: dict[uuid.UUID, float],
    parent_map: dict[uuid.UUID, uuid.UUID | None],
) -> float:
    """Return available qty for an ingredient, checking hierarchy."""
    qty = pantry.get(ingredient_id, 0.0)
    if qty > 0:
        return qty
    # Check parent (child → parent: "cherry tomato" covers "tomato")
    parent_id = parent_map.get(ingredient_id)
    if parent_id and pantry.get(parent_id, 0.0) > 0:
        return pantry[parent_id]
    # Check children (parent → child: "tomato" covers if we have "cherry tomato")
    for child_id, pid in parent_map.items():
        if pid == ingredient_id and pantry.get(child_id, 0.0) > 0:
            return pantry[child_id]
    return 0.0


async def match_recipes(
    db: AsyncSession, min_coverage: float = 0.0
) -> list[RecipeMatch]:
    pantry = await _build_pantry_index(db)
    parent_map = await _build_parent_map(db)

    result = await db.execute(select(Recipe))
    recipes = result.scalars().unique().all()

    matches: list[RecipeMatch] = []
    for recipe in recipes:
        required = [ri for ri in recipe.ingredients if not ri.optional]
        if not required:
            continue
        ingredient_matches = []
        matched_count = 0
        for ri in recipe.ingredients:
            avail = _check_available(ri.ingredient_id, pantry, parent_map)
            have = avail >= float(ri.quantity)
            if have and not ri.optional:
                matched_count += 1
            ingredient_matches.append(
                IngredientMatch(
                    ingredient_id=ri.ingredient_id,
                    ingredient_name=ri.ingredient.name if ri.ingredient else "?",
                    required_qty=float(ri.quantity),
                    required_unit=ri.unit,
                    available_qty=avail,
                    have=have,
                    optional=ri.optional,
                )
            )
        coverage = matched_count / len(required) if required else 0.0
        if coverage >= min_coverage:
            matches.append(
                RecipeMatch(
                    recipe_id=recipe.id,
                    recipe_title=recipe.title,
                    coverage=round(coverage, 4),
                    total_required=len(required),
                    total_matched=matched_count,
                    ingredient_matches=ingredient_matches,
                )
            )
    matches.sort(key=lambda m: m.coverage, reverse=True)
    return matches


async def recipe_availability(
    db: AsyncSession, recipe_id: uuid.UUID
) -> RecipeMatch:
    pantry = await _build_pantry_index(db)
    parent_map = await _build_parent_map(db)

    recipe = await db.get(Recipe, recipe_id)
    if not recipe:
        from fastapi import HTTPException
        raise HTTPException(404, "Recipe not found")

    required = [ri for ri in recipe.ingredients if not ri.optional]
    ingredient_matches = []
    matched_count = 0
    for ri in recipe.ingredients:
        avail = _check_available(ri.ingredient_id, pantry, parent_map)
        have = avail >= float(ri.quantity)
        if have and not ri.optional:
            matched_count += 1
        ingredient_matches.append(
            IngredientMatch(
                ingredient_id=ri.ingredient_id,
                ingredient_name=ri.ingredient.name if ri.ingredient else "?",
                required_qty=float(ri.quantity),
                required_unit=ri.unit,
                available_qty=avail,
                have=have,
                optional=ri.optional,
            )
        )
    coverage = matched_count / len(required) if required else 0.0
    return RecipeMatch(
        recipe_id=recipe.id,
        recipe_title=recipe.title,
        coverage=round(coverage, 4),
        total_required=len(required),
        total_matched=matched_count,
        ingredient_matches=ingredient_matches,
    )
