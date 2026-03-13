import uuid
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pantry import PantryItem
from app.models.recipe import Recipe
from app.schemas.matching import ShoppingList, ShoppingListItem


async def generate_shopping_list(
    db: AsyncSession, recipe_ids: list[uuid.UUID]
) -> ShoppingList:
    # Build pantry stock index
    result = await db.execute(select(PantryItem))
    pantry_stock: dict[uuid.UUID, float] = defaultdict(float)
    for item in result.scalars().all():
        pantry_stock[item.ingredient_id] += float(item.quantity)

    # Aggregate ingredient needs across all requested recipes
    needs: dict[uuid.UUID, dict] = {}
    for recipe_id in recipe_ids:
        recipe = await db.get(Recipe, recipe_id)
        if not recipe:
            continue
        for ri in recipe.ingredients:
            if ri.optional:
                continue
            if ri.ingredient_id not in needs:
                needs[ri.ingredient_id] = {
                    "name": ri.ingredient.name if ri.ingredient else "?",
                    "qty": 0.0,
                    "unit": ri.unit,
                }
            needs[ri.ingredient_id]["qty"] += float(ri.quantity)

    # Subtract pantry stock → shopping list
    items: list[ShoppingListItem] = []
    for ing_id, info in needs.items():
        deficit = info["qty"] - pantry_stock.get(ing_id, 0.0)
        if deficit > 0:
            items.append(
                ShoppingListItem(
                    ingredient_id=ing_id,
                    ingredient_name=info["name"],
                    needed_qty=round(deficit, 2),
                    unit=info["unit"],
                )
            )

    return ShoppingList(recipe_ids=recipe_ids, items=items)
