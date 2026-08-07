import uuid

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    cpf: str = Field(
        min_length=11,
        max_length=14,
    )
    senha: str = Field(
        min_length=1,
        max_length=128,
    )


class PromotorResponse(BaseModel):
    id_promotor: uuid.UUID
    nome: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    promotor: PromotorResponse