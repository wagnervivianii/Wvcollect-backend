import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PerguntaColetaResponse(BaseModel):
    id_pergunta: uuid.UUID

    codigo: str
    texto: str
    tipo_resposta: str

    aplica_sku: bool
    obrigatoria: bool

    ordem: int


class ListaPerguntasResponse(BaseModel):
    total: int
    perguntas: list[PerguntaColetaResponse]


class RespostaItemRequest(BaseModel):
    # UUID gerado no aparelho.
    #
    # A resposta só será enviada ao backend
    # quando o promotor confirmar o envio
    # final da coleta.
    id_resposta: uuid.UUID

    id_pergunta: uuid.UUID

    # Esta pesquisa não utiliza SKU,
    # portanto ficará NULL.
    id_sku: uuid.UUID | None = None

    valor: str = Field(
        min_length=1,
        max_length=1000,
    )

    # Momento em que a resposta ficou
    # registrada no aparelho para envio.
    respondida_em_dispositivo: datetime


class SalvarRespostasRequest(BaseModel):
    # Todas as respostas preenchidas são
    # enviadas juntas.
    #
    # Perguntas não respondidas simplesmente
    # não aparecem nesta lista.
    respostas: list[RespostaItemRequest]


class RespostaSalvaResponse(BaseModel):
    id_resposta: uuid.UUID
    id_pergunta: uuid.UUID
    id_sku: uuid.UUID | None

    valor: str

    respondida_em_dispositivo: datetime


class SalvarRespostasResponse(BaseModel):
    id_pesquisa: uuid.UUID

    total_recebidas: int
    total_salvas: int

    respostas: list[RespostaSalvaResponse]