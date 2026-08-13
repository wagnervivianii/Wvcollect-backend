from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPBasic,
    HTTPBasicCredentials,
)

from app.core.config import settings


security = HTTPBasic()


def require_admin(
    credentials: HTTPBasicCredentials = Depends(security),
) -> str:
    """
    Autenticação administrativa compartilhada.

    Configuração carregada pelo Settings:
        WVCOLLECT_ADMIN_USER
        WVCOLLECT_ADMIN_PASSWORD
    """

    expected_user = settings.wvcollect_admin_user.strip()
    expected_password = settings.wvcollect_admin_password

    if not expected_user or not expected_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin web não configurado.",
        )

    user_ok = secrets.compare_digest(
        credentials.username.encode("utf-8"),
        expected_user.encode("utf-8"),
    )

    password_ok = secrets.compare_digest(
        credentials.password.encode("utf-8"),
        expected_password.encode("utf-8"),
    )

    if not (user_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais administrativas inválidas.",
            headers={
                "WWW-Authenticate": "Basic",
            },
        )

    return expected_user
