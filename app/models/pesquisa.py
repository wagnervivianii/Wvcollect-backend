import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Pesquisa(Base):
    __tablename__ = "fto_pesquisa"

    id_pesquisa: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )

    id_roteiro: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fto_roteiro.id_roteiro"),
        nullable=False,
    )

    id_promotor: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dim_promotor.id_promotor"),
        nullable=False,
    )

    id_pdv: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dim_pdv.id_pdv"),
        nullable=False,
    )

    # 1 = primeira coleta
    # 2 = primeira recoleta
    # 3 = segunda recoleta...
    numero_coleta: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    # Na primeira coleta fica NULL.
    # Nas recoletas aponta para a pesquisa original.
    id_pesquisa_origem: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "fto_pesquisa.id_pesquisa",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="EM_PREENCHIMENTO",
    )

    latitude_inicio: Mapped[float | None] = mapped_column(
        Numeric(10, 7),
    )

    longitude_inicio: Mapped[float | None] = mapped_column(
        Numeric(10, 7),
    )

    precisao_inicio_metros: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
    )

    latitude_fim: Mapped[float | None] = mapped_column(
        Numeric(10, 7),
    )

    longitude_fim: Mapped[float | None] = mapped_column(
        Numeric(10, 7),
    )

    precisao_fim_metros: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
    )

    # Data e hora reais registradas pelo aparelho.
    # Funciona também quando a coleta é feita offline.
    iniciada_em_dispositivo: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    finalizada_em_dispositivo: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    recebida_em_servidor: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    sincronizada_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    device_id: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    app_version: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    criada_offline: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Indica que o promotor foi avisado sobre campos
    # não preenchidos e decidiu finalizar mesmo assim.
    envio_com_pendencias: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # Lista dos campos que estavam sem preenchimento
    # no momento da confirmação.
    #
    # Exemplo conceitual:
    # [
    #     "Nome do responsável",
    #     "Allegra",
    #     "Foto antes do abastecimento"
    # ]
    campos_pendentes: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Data/hora do aparelho em que o promotor confirmou
    # que queria finalizar mesmo com pendências.
    pendencias_confirmadas_em_dispositivo: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            """
            status IN (
                'EM_PREENCHIMENTO',
                'FINALIZADA_LOCAL',
                'SINCRONIZANDO',
                'SINCRONIZADA',
                'ERRO'
            )
            """,
            name="ck_pesquisa_status",
        ),
        CheckConstraint(
            "numero_coleta >= 1",
            name="ck_pesquisa_numero_coleta",
        ),
        CheckConstraint(
            """
            id_pesquisa_origem IS NULL
            OR id_pesquisa_origem <> id_pesquisa
            """,
            name="ck_pesquisa_origem_diferente",
        ),
        Index(
            "ix_pesquisa_promotor",
            "id_promotor",
        ),
        Index(
            "ix_pesquisa_pdv",
            "id_pdv",
        ),
        Index(
            "ix_pesquisa_status",
            "status",
        ),
        Index(
            "ix_pesquisa_origem",
            "id_pesquisa_origem",
        ),
    )