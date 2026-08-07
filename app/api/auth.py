from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.dependencies import get_db
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    PromotorResponse,
)
from app.services.auth_service import authenticate_promotor


router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"],
)


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    promotor = authenticate_promotor(
        db=db,
        cpf=payload.cpf,
        senha=payload.senha,
    )

    if promotor is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CPF ou senha inválidos.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    access_token = create_access_token(
        subject=str(promotor.id_promotor),
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        promotor=PromotorResponse(
            id_promotor=promotor.id_promotor,
            nome=promotor.nome,
        ),
    )