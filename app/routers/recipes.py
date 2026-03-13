import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.recipe import Recipe, RecipeIngredient, RecipeStep, RecipeTag
from app.schemas.recipe import RecipeCreate, RecipeRead, RecipeSummary, RecipeUpdate

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("/", response_model=list[RecipeSummary])
async def list_recipes(
    q: str | None = None,
    cuisine: str | None = None,
    tag: str | None = None,
    max_time: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Recipe)
    if q:
        stmt = stmt.where(Recipe.title.ilike(f"%{q}%"))
    if cuisine:
        stmt = stmt.where(Recipe.cuisine.ilike(f"%{cuisine}%"))
    if tag:
        stmt = stmt.join(RecipeTag).where(RecipeTag.tag.ilike(f"%{tag}%"))
    if max_time is not None:
        stmt = stmt.where(
            (Recipe.prep_time_minutes + Recipe.cook_time_minutes) <= max_time
        )
    stmt = stmt.order_by(Recipe.title)
    result = await db.execute(stmt)
    recipes = result.scalars().unique().all()
    return [
        RecipeSummary(
            id=r.id,
            title=r.title,
            description=r.description,
            cuisine=r.cuisine,
            prep_time_minutes=r.prep_time_minutes,
            cook_time_minutes=r.cook_time_minutes,
            servings=r.servings,
            tag_list=[t.tag for t in r.tags],
        )
        for r in recipes
    ]


@router.post("/", response_model=RecipeRead, status_code=201)
async def create_recipe(
    body: RecipeCreate, db: AsyncSession = Depends(get_db)
):
    recipe = Recipe(
        title=body.title,
        description=body.description,
        cuisine=body.cuisine,
        prep_time_minutes=body.prep_time_minutes,
        cook_time_minutes=body.cook_time_minutes,
        servings=body.servings,
    )
    for idx, ing in enumerate(body.ingredients):
        recipe.ingredients.append(
            RecipeIngredient(
                ingredient_id=ing.ingredient_id,
                quantity=ing.quantity,
                unit=ing.unit,
                optional=ing.optional,
                group=ing.group,
                position=ing.position or idx,
            )
        )
    for step in body.steps:
        recipe.steps.append(
            RecipeStep(
                step_number=step.step_number,
                instruction=step.instruction,
                duration_minutes=step.duration_minutes,
            )
        )
    for tag_name in body.tags:
        recipe.tags.append(RecipeTag(tag=tag_name))
    db.add(recipe)
    await db.commit()
    await db.refresh(recipe)
    return recipe


@router.get("/{recipe_id}", response_model=RecipeRead)
async def get_recipe(
    recipe_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    recipe = await db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(404, "Recipe not found")
    return recipe


@router.patch("/{recipe_id}", response_model=RecipeRead)
async def update_recipe(
    recipe_id: uuid.UUID,
    body: RecipeUpdate,
    db: AsyncSession = Depends(get_db),
):
    recipe = await db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(404, "Recipe not found")
    data = body.model_dump(exclude_unset=True)

    # Handle nested collections separately
    if "ingredients" in data:
        recipe.ingredients.clear()
        for idx, ing in enumerate(body.ingredients):
            recipe.ingredients.append(
                RecipeIngredient(
                    ingredient_id=ing.ingredient_id,
                    quantity=ing.quantity,
                    unit=ing.unit,
                    optional=ing.optional,
                    group=ing.group,
                    position=ing.position or idx,
                )
            )
        del data["ingredients"]

    if "steps" in data:
        recipe.steps.clear()
        for step in body.steps:
            recipe.steps.append(
                RecipeStep(
                    step_number=step.step_number,
                    instruction=step.instruction,
                    duration_minutes=step.duration_minutes,
                )
            )
        del data["steps"]

    if "tags" in data:
        recipe.tags.clear()
        for tag_name in body.tags:
            recipe.tags.append(RecipeTag(tag=tag_name))
        del data["tags"]

    for field, value in data.items():
        setattr(recipe, field, value)

    await db.commit()
    await db.refresh(recipe)
    return recipe


@router.delete("/{recipe_id}", status_code=204)
async def delete_recipe(
    recipe_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    recipe = await db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(404, "Recipe not found")
    await db.delete(recipe)
    await db.commit()
