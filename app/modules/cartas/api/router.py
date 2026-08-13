from fastapi import APIRouter

from app.modules.cartas.api.modelos import (
    router as modelos_router,
)


router = APIRouter(
    prefix="/cartas",
)

router.include_router(modelos_router)
