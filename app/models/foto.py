import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Foto(Base):
    __tablename__ = "fto_foto"

    id_foto: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )

    id_pesquisa: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "fto_pesquisa.id_pesquisa",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # Normalmente NULL.
    # Mantido para futuras evidências
    # ligadas diretamente a produto/SKU.
    id_sku: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dim_sku.id_sku"),
        nullable=True,
    )

    tipo_evidencia: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    nome_arquivo_original: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    storage_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
    )

    arquivo_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    mime_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    tamanho_bytes: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    largura: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    altura: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    hash_sha256: Mapped[str | None] = mapped_column(
        String(64),
        index=True,
        nullable=True,
    )

    latitude: Mapped[float | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
    )

    precisao_metros: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    capturada_em_dispositivo: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    recebida_em_servidor: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    status_upload: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDENTE",
    )

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            """
            tipo_evidencia IN (
                'ANTES',
                'DEPOIS',
                'PONTO_EXTRA',
                'GIRO_ESTOQUE'
            )
            """,
            name="ck_foto_tipo_evidencia",
        ),
        CheckConstraint(
            """
            status_upload IN (
                'PENDENTE',
                'ENVIANDO',
                'ENVIADA',
                'ERRO'
            )
            """,
            name="ck_foto_status_upload",
        ),
        Index(
            "ix_foto_pesquisa_tipo",
            "id_pesquisa",
            "tipo_evidencia",
        ),
    )