from uuid import UUID

from pydantic import BaseModel


class CartaModeloCreateResponse(BaseModel):
    id_modelo: UUID
    id_versao: UUID
    storage_key: str
    hash_sha256: str
    tamanho_bytes: int
