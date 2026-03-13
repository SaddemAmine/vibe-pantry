import datetime
import uuid

from pydantic import BaseModel


class PantryItemBase(BaseModel):
    ingredient_id: uuid.UUID
    quantity: float
    unit: str
    expiry_date: datetime.date | None = None
    note: str | None = None


class PantryItemCreate(PantryItemBase):
    pass


class PantryItemUpdate(BaseModel):
    quantity: float | None = None
    unit: str | None = None
    expiry_date: datetime.date | None = None
    note: str | None = None


class PantryItemRead(PantryItemBase):
    id: uuid.UUID
    ingredient_name: str | None = None

    model_config = {"from_attributes": True}
