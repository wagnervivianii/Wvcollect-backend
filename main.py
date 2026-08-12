from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.fotos import router as fotos_router
from app.api.me import router as me_router
from app.api.perguntas import router as perguntas_router
from app.api.pesquisas import router as pesquisas_router
from app.api.respostas import router as respostas_router
from app.core.config import settings
from app.db.session import engine


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API do WVCollect",
)


app.include_router(auth_router)
app.include_router(me_router)
app.include_router(pesquisas_router)
app.include_router(perguntas_router)
app.include_router(fotos_router)
app.include_router(respostas_router)
app.include_router(admin_router)


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "version": "0.1.0",
        "status": "online",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
    }


@app.get("/health/db")
def health_database():
    try:
        with engine.connect() as connection:
            database, user = connection.execute(
                text(
                    """
                    SELECT
                        current_database(),
                        current_user
                    """
                )
            ).one()

        return {
            "status": "ok",
            "database": database,
            "user": user,
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        )