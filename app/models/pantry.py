import datetime
import uuid

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid
from app.models.ingredient import Ingredient


class PantryItem(Base, TimestampMixin):
    __tablename__ = "pantry_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingredients.id"), index=True
    )
    quantity: Mapped[float] = mapped_column(Numeric(10, 2))
    unit: Mapped[str] = mapped_column(String(30))  # "g", "ml", "pieces", "cups", ...
    expiry_date: Mapped[datetime.date | None] = mapped_column(Date)
    note: Mapped[str | None] = mapped_column(String(500))

    ingredient: Mapped[Ingredient] = relationship(lazy="selectin")
