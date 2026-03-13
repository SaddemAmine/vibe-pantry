import uuid

from pydantic import BaseModel


class RecipeIngredientBase(BaseModel):
    ingredient_id: uuid.UUID
    quantity: float
    unit: str
    optional: bool = False
    group: str | None = None
    position: int = 0


class RecipeIngredientRead(RecipeIngredientBase):
    id: uuid.UUID
    ingredient_name: str | None = None

    model_config = {"from_attributes": True}


class RecipeStepBase(BaseModel):
    step_number: int
    instruction: str
    duration_minutes: int | None = None


class RecipeStepRead(RecipeStepBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}


class RecipeTagRead(BaseModel):
    id: uuid.UUID
    tag: str

    model_config = {"from_attributes": True}


class RecipeBase(BaseModel):
    title: str
    description: str | None = None
    cuisine: str | None = None
    prep_time_minutes: int | None = None
    cook_time_minutes: int | None = None
    servings: int = 4


class RecipeCreate(RecipeBase):
    ingredients: list[RecipeIngredientBase] = []
    steps: list[RecipeStepBase] = []
    tags: list[str] = []


class RecipeUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    cuisine: str | None = None
    prep_time_minutes: int | None = None
    cook_time_minutes: int | None = None
    servings: int | None = None
    ingredients: list[RecipeIngredientBase] | None = None
    steps: list[RecipeStepBase] | None = None
    tags: list[str] | None = None


class RecipeSummary(RecipeBase):
    id: uuid.UUID
    tag_list: list[str] = []

    model_config = {"from_attributes": True}


class RecipeRead(RecipeBase):
    id: uuid.UUID
    ingredients: list[RecipeIngredientRead] = []
    steps: list[RecipeStepRead] = []
    tags: list[RecipeTagRead] = []

    model_config = {"from_attributes": True}
