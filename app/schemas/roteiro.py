import uuid
from datetime import date, datetime

from pydantic import BaseModel


class PDVRoteiroResponse(BaseModel):
    id_roteiro: uuid.UUID
    id_pdv: uuid.UUID

    codigo_origem: str | None = None
    cnpj: str | None = None

    nome_pdv: str

    endereco: str | None = None
    bairro: str | None = None
    cidade: str | None = None
    uf: str | None = None

    latitude: float | None = None
    longitude: float | None = None

    data_inicio: date | None = None
    data_fim: date | None = None

    # Situação da loja para o aplicativo:
    #
    # PENDENTE
    # EM_ANDAMENTO
    # CONCLUIDA
    status_coleta: str = "PENDENTE"

    # Quantas pesquisas concluídas existem
    # para este roteiro/PDV.
    coletas_realizadas: int = 0

    # Data e hora da última coleta concluída.
    ultima_coleta_em: datetime | None = None

    # Se houver uma pesquisa aberta para esta loja,
    # estes campos permitem ao aplicativo retomá-la
    # sem criar uma nova pesquisa.
    id_pesquisa_em_andamento: uuid.UUID | None = None

    numero_coleta_em_andamento: int | None = None

    iniciada_em_dispositivo: datetime | None = None


class RoteiroResponse(BaseModel):
    total: int
    pdvs: list[PDVRoteiroResponse]