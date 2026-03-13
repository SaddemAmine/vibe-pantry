import uuid

from pydantic import BaseModel

from app.models.ingredient import IngredientCategory, UnitType


class AliasRead(BaseModel):
    id: uuid.UUID
    alias: str

    model_config = {"from_attributes": True}


class IngredientBase(BaseModel):
    name: str
    category: IngredientCategory = IngredientCategory.OTHER
    default_unit_type: UnitType = UnitType.COUNT
    parent_id: uuid.UUID | None = None


class IngredientCreate(IngredientBase):
    aliases: list[str] = []


class IngredientUpdate(BaseModel):
    name: str | None = None
    category: IngredientCategory | None = None
    default_unit_type: UnitType | None = None
    parent_id: uuid.UUID | None = None


class IngredientRead(IngredientBase):
    id: uuid.UUID
    aliases: list[AliasRead] = []

    model_config = {"from_attributes": True}
