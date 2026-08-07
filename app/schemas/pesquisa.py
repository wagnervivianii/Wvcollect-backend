import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class IniciarPesquisaRequest(BaseModel):
    id_pesquisa: uuid.UUID

    id_roteiro: uuid.UUID

    iniciada_em_dispositivo: datetime

    latitude_inicio: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude_inicio: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    precisao_inicio_metros: float | None = Field(
        default=None,
        ge=0,
    )

    device_id: str | None = Field(
        default=None,
        max_length=200,
    )

    app_version: str | None = Field(
        default=None,
        max_length=30,
    )

    criada_offline: bool = False

    confirmar_recoleta: bool = False


class PesquisaIniciadaResponse(BaseModel):
    id_pesquisa: uuid.UUID
    id_roteiro: uuid.UUID
    id_pdv: uuid.UUID

    numero_coleta: int

    id_pesquisa_origem: uuid.UUID | None = None

    status: str

    iniciada_em_dispositivo: datetime

    recoleta: bool

    coletas_anteriores: int


class FinalizarPesquisaRequest(BaseModel):
    # Data e hora reais em que o promotor
    # terminou a coleta no aparelho.
    finalizada_em_dispositivo: datetime

    latitude_fim: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude_fim: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    precisao_fim_metros: float | None = Field(
        default=None,
        ge=0,
    )

    # Lista exata do que ficou sem
    # preenchimento no momento do envio.
    #
    # Exemplo conceitual:
    # [
    #     "Nome do responsável",
    #     "Allegra",
    #     "Foto antes"
    # ]
    campos_pendentes: list[str] = Field(
        default_factory=list,
        max_length=100,
    )

    # Só será True quando o aplicativo
    # mostrar o aviso das pendências e
    # o promotor escolher continuar.
    confirmar_envio_com_pendencias: bool = False

    # Horário do aparelho em que o promotor
    # confirmou conscientemente o envio
    # mesmo com campos faltando.
    pendencias_confirmadas_em_dispositivo: datetime | None = None


class PesquisaFinalizadaResponse(BaseModel):
    id_pesquisa: uuid.UUID
    id_roteiro: uuid.UUID
    id_pdv: uuid.UUID

    numero_coleta: int

    status: str

    iniciada_em_dispositivo: datetime
    finalizada_em_dispositivo: datetime

    # Não armazenaremos a duração duplicada.
    # Ela é calculada entre início e fim.
    duracao_segundos: int

    recoleta: bool

    # Auditoria do fechamento.
    envio_com_pendencias: bool = False

    campos_pendentes: list[str] = Field(
        default_factory=list,
    )

    pendencias_confirmadas_em_dispositivo: datetime | None = None