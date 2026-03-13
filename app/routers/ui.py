import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.ingredient import Ingredient, IngredientAlias, IngredientCategory, UnitType
from app.models.pantry import PantryItem
from app.models.recipe import Recipe, RecipeIngredient, RecipeStep, RecipeTag
from app.services.matching import match_recipes
from app.services.shopping import generate_shopping_list

router = APIRouter(tags=["ui"])
templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    pantry_count = (await db.execute(select(func.count(PantryItem.id)))).scalar() or 0
    recipe_count = (await db.execute(select(func.count(Recipe.id)))).scalar() or 0
    ingredient_count = (await db.execute(select(func.count(Ingredient.id)))).scalar() or 0
    return templates.TemplateResponse("home.html", {
        "request": request,
        "pantry_count": pantry_count,
        "recipe_count": recipe_count,
        "ingredient_count": ingredient_count,
    })


# ── Ingredients ──────────────────────────────────────────
@router.get("/ingredients", response_class=HTMLResponse)
async def ingredients_page(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ingredient).order_by(Ingredient.name))
    ingredients = result.scalars().all()
    return templates.TemplateResponse("ingredients.html", {
        "request": request,
        "ingredients": ingredients,
        "categories": list(IngredientCategory),
        "unit_types": list(UnitType),
    })


@router.post("/ingredients", response_class=HTMLResponse)
async def create_ingredient_ui(
    request: Request,
    name: str = Form(...),
    category: str = Form("other"),
    default_unit_type: str = Form("count"),
    db: AsyncSession = Depends(get_db),
):
    ingredient = Ingredient(
        name=name,
        category=IngredientCategory(category),
        default_unit_type=UnitType(default_unit_type),
    )
    db.add(ingredient)
    await db.commit()
    return RedirectResponse("/ingredients", status_code=303)


# ── Pantry ───────────────────────────────────────────────
@router.get("/pantry", response_class=HTMLResponse)
async def pantry_page(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PantryItem))
    items = result.scalars().all()
    ing_result = await db.execute(select(Ingredient).order_by(Ingredient.name))
    ingredients = ing_result.scalars().all()
    return templates.TemplateResponse("pantry.html", {
        "request": request,
        "items": items,
        "ingredients": ingredients,
    })


@router.post("/pantry", response_class=HTMLResponse)
async def add_pantry_item_ui(
    request: Request,
    ingredient_id: uuid.UUID = Form(...),
    quantity: float = Form(...),
    unit: str = Form(...),
    expiry_date: str = Form(""),
    note: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    import datetime
    item = PantryItem(
        ingredient_id=ingredient_id,
        quantity=quantity,
        unit=unit,
        expiry_date=datetime.date.fromisoformat(expiry_date) if expiry_date else None,
        note=note or None,
    )
    db.add(item)
    await db.commit()
    return RedirectResponse("/pantry", status_code=303)


@router.post("/pantry/{item_id}/delete", response_class=HTMLResponse)
async def delete_pantry_item_ui(
    item_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    item = await db.get(PantryItem, item_id)
    if item:
        await db.delete(item)
        await db.commit()
    return RedirectResponse("/pantry", status_code=303)


# ── Recipes ──────────────────────────────────────────────
@router.get("/recipes", response_class=HTMLResponse)
async def recipes_page(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Recipe).order_by(Recipe.title))
    recipes = result.scalars().unique().all()
    return templates.TemplateResponse("recipes.html", {
        "request": request,
        "recipes": recipes,
    })


@router.get("/recipes/new", response_class=HTMLResponse)
async def new_recipe_page(request: Request, db: AsyncSession = Depends(get_db)):
    ing_result = await db.execute(select(Ingredient).order_by(Ingredient.name))
    ingredients = ing_result.scalars().all()
    return templates.TemplateResponse("recipe_form.html", {
        "request": request,
        "ingredients": ingredients,
    })


@router.post("/recipes", response_class=HTMLResponse)
async def create_recipe_ui(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    recipe = Recipe(
        title=form["title"],
        description=form.get("description") or None,
        cuisine=form.get("cuisine") or None,
        prep_time_minutes=int(form["prep_time_minutes"]) if form.get("prep_time_minutes") else None,
        cook_time_minutes=int(form["cook_time_minutes"]) if form.get("cook_time_minutes") else None,
        servings=int(form.get("servings", 4)),
    )

    # Collect ingredients from dynamic form rows
    idx = 0
    while f"ing_id_{idx}" in form:
        ing_id = form[f"ing_id_{idx}"]
        qty = form.get(f"ing_qty_{idx}", "1")
        unit = form.get(f"ing_unit_{idx}", "pieces")
        optional = f"ing_optional_{idx}" in form
        if ing_id:
            recipe.ingredients.append(
                RecipeIngredient(
                    ingredient_id=uuid.UUID(ing_id),
                    quantity=float(qty),
                    unit=unit,
                    optional=optional,
                    position=idx,
                )
            )
        idx += 1

    # Collect steps
    idx = 0
    while f"step_{idx}" in form:
        instruction = form[f"step_{idx}"]
        if instruction.strip():
            recipe.steps.append(
                RecipeStep(step_number=idx + 1, instruction=instruction)
            )
        idx += 1

    # Tags
    tags_raw = form.get("tags", "")
    for tag in tags_raw.split(","):
        tag = tag.strip()
        if tag:
            recipe.tags.append(RecipeTag(tag=tag))

    db.add(recipe)
    await db.commit()
    return RedirectResponse("/recipes", status_code=303)


@router.get("/recipes/{recipe_id}", response_class=HTMLResponse)
async def recipe_detail_page(
    recipe_id: uuid.UUID, request: Request, db: AsyncSession = Depends(get_db)
):
    recipe = await db.get(Recipe, recipe_id)
    if not recipe:
        return RedirectResponse("/recipes", status_code=303)
    # Check pantry availability for each ingredient
    from app.services.matching import recipe_availability
    availability = await recipe_availability(db, recipe_id)
    return templates.TemplateResponse("recipe_detail.html", {
        "request": request,
        "recipe": recipe,
        "availability": availability,
    })


@router.post("/recipes/{recipe_id}/cook", response_class=HTMLResponse)
async def cook_recipe_ui(
    recipe_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    recipe = await db.get(Recipe, recipe_id)
    if not recipe:
        return RedirectResponse("/recipes", status_code=303)

    for ri in recipe.ingredients:
        if ri.optional:
            continue
        remaining = float(ri.quantity)
        # Find pantry items for this ingredient, use earliest-expiring first
        result = await db.execute(
            select(PantryItem)
            .where(PantryItem.ingredient_id == ri.ingredient_id)
            .order_by(PantryItem.expiry_date.asc().nulls_last())
        )
        for item in result.scalars().all():
            if remaining <= 0:
                break
            available = float(item.quantity)
            if available <= remaining:
                remaining -= available
                await db.delete(item)
            else:
                item.quantity = available - remaining
                remaining = 0
    await db.commit()
    return RedirectResponse(f"/recipes/{recipe_id}", status_code=303)


@router.post("/recipes/{recipe_id}/delete", response_class=HTMLResponse)
async def delete_recipe_ui(
    recipe_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    recipe = await db.get(Recipe, recipe_id)
    if recipe:
        await db.delete(recipe)
        await db.commit()
    return RedirectResponse("/recipes", status_code=303)


# ── Matching ─────────────────────────────────────────────
@router.get("/match", response_class=HTMLResponse)
async def match_page(request: Request, db: AsyncSession = Depends(get_db)):
    matches = await match_recipes(db, min_coverage=0.0)
    return templates.TemplateResponse("match.html", {
        "request": request,
        "matches": matches,
    })


@router.post("/shopping", response_class=HTMLResponse)
async def shopping_page(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    recipe_ids = [uuid.UUID(rid) for rid in form.getlist("recipe_ids")]
    if not recipe_ids:
        return RedirectResponse("/match", status_code=303)
    shopping = await generate_shopping_list(db, recipe_ids)
    return templates.TemplateResponse("shopping.html", {
        "request": request,
        "shopping": shopping,
    })
