import enum
import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class IngredientCategory(str, enum.Enum):
    PRODUCE = "produce"
    DAIRY = "dairy"
    MEAT = "meat"
    SEAFOOD = "seafood"
    GRAIN = "grain"
    SPICE = "spice"
    CONDIMENT = "condiment"
    CANNED = "canned"
    FROZEN = "frozen"
    BEVERAGE = "beverage"
    BAKING = "baking"
    OTHER = "other"


class UnitType(str, enum.Enum):
    MASS = "mass"        # grams as base
    VOLUME = "volume"    # milliliters as base
    COUNT = "count"      # pieces
    OTHER = "other"


class Ingredient(Base, TimestampMixin):
    __tablename__ = "ingredients"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    category: Mapped[IngredientCategory] = mapped_column(default=IngredientCategory.OTHER)
    default_unit_type: Mapped[UnitType] = mapped_column(default=UnitType.COUNT)

    # Shallow hierarchy: parent is the canonical base ingredient.
    # e.g. "cherry tomato" → parent "tomato"
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ingredients.id"))

    parent: Mapped["Ingredient | None"] = relationship(
        remote_side="Ingredient.id", lazy="selectin"
    )
    aliases: Mapped[list["IngredientAlias"]] = relationship(
        back_populates="ingredient", cascade="all, delete-orphan", lazy="selectin"
    )


class IngredientAlias(Base):
    """Maps variant spellings / names to canonical ingredients.
    e.g. 'tomatos' → tomato, 'aubergine' → eggplant
    """

    __tablename__ = "ingredient_aliases"
    __table_args__ = (UniqueConstraint("alias"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    ingredient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ingredients.id"))
    alias: Mapped[str] = mapped_column(String(200), index=True)

    ingredient: Mapped[Ingredient] = relationship(back_populates="aliases")
