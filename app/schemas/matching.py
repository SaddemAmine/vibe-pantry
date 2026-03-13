import uuid

from pydantic import BaseModel


class IngredientMatch(BaseModel):
    ingredient_id: uuid.UUID
    ingredient_name: str
    required_qty: float
    required_unit: str
    available_qty: float
    have: bool
    optional: bool = False


class RecipeMatch(BaseModel):
    recipe_id: uuid.UUID
    recipe_title: str
    coverage: float  # 0.0 – 1.0
    total_required: int
    total_matched: int
    ingredient_matches: list[IngredientMatch] = []


class ShoppingListItem(BaseModel):
    ingredient_id: uuid.UUID
    ingredient_name: str
    needed_qty: float
    unit: str


class ShoppingList(BaseModel):
    recipe_ids: list[uuid.UUID]
    items: list[ShoppingListItem] = []
