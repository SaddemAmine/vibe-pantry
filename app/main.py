from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import ingredients, matching, pantry, recipes, ui

app = FastAPI(title="Vibe Pantry", version="0.1.0")

# API routers under /api
app.include_router(matching.router, prefix="/api")
app.include_router(ingredients.router, prefix="/api")
app.include_router(pantry.router, prefix="/api")
app.include_router(recipes.router, prefix="/api")

# UI router at root
app.include_router(ui.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
