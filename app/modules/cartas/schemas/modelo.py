from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CartaModeloCreateResponse(BaseModel):
    id_modelo: UUID
    id_versao: UUID
    storage_key: str
    hash_sha256: str
    tamanho_bytes: int


class CartaModeloRedeResponse(BaseModel):
    rede: str
    rede_normalizada: str


class CartaModeloVersaoResponse(BaseModel):
    id_versao: UUID
    numero_versao: int
    nome_arquivo_original: str
    mime_type: str | None
    criado_em: datetime


class CartaModeloItemResponse(BaseModel):
    id_modelo: UUID
    nome: str
    tipo: str
    granularidade: str
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime
    redes: list[CartaModeloRedeResponse]
    versao_ativa: CartaModeloVersaoResponse | None


class CartaModeloListResponse(BaseModel):
    total: int
    items: list[CartaModeloItemResponse]
