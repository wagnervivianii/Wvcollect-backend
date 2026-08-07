import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.dependencies import get_db
from app.models.promotor import Promotor


bearer_scheme = HTTPBearer(
    auto_error=False,
)


def get_current_promotor(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> Promotor:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não informado.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    token = credentials.credentials

    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    try:
        id_promotor = uuid.UUID(
            payload["sub"]
        )
    except (ValueError, TypeError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    promotor = db.scalar(
        select(Promotor).where(
            Promotor.id_promotor == id_promotor,
            Promotor.ativo.is_(True),
        )
    )

    if promotor is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Promotor não encontrado ou inativo.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    return promotor