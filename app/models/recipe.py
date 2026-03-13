import uuid

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid
from app.models.ingredient import Ingredient


class Recipe(Base, TimestampMixin):
    __tablename__ = "recipes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    title: Mapped[str] = mapped_column(String(300), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    cuisine: Mapped[str | None] = mapped_column(String(100))
    prep_time_minutes: Mapped[int | None] = mapped_column(Integer)
    cook_time_minutes: Mapped[int | None] = mapped_column(Integer)
    servings: Mapped[int] = mapped_column(Integer, default=4)

    ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan", lazy="selectin",
        order_by="RecipeIngredient.position",
    )
    steps: Mapped[list["RecipeStep"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan", lazy="selectin",
        order_by="RecipeStep.step_number",
    )
    tags: Mapped[list["RecipeTag"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan", lazy="selectin",
    )


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    recipe_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), index=True
    )
    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingredients.id"), index=True
    )
    quantity: Mapped[float] = mapped_column(Numeric(10, 2))
    unit: Mapped[str] = mapped_column(String(30))
    optional: Mapped[bool] = mapped_column(default=False)
    group: Mapped[str | None] = mapped_column(String(100))  # e.g. "sauce", "marinade"
    position: Mapped[int] = mapped_column(Integer, default=0)

    recipe: Mapped[Recipe] = relationship(back_populates="ingredients")
    ingredient: Mapped[Ingredient] = relationship(lazy="selectin")


class RecipeStep(Base):
    __tablename__ = "recipe_steps"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    recipe_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), index=True
    )
    step_number: Mapped[int] = mapped_column(Integer)
    instruction: Mapped[str] = mapped_column(Text)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)

    recipe: Mapped[Recipe] = relationship(back_populates="steps")


class RecipeTag(Base):
    __tablename__ = "recipe_tags"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    recipe_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), index=True
    )
    tag: Mapped[str] = mapped_column(String(100), index=True)

    recipe: Mapped[Recipe] = relationship(back_populates="tags")
