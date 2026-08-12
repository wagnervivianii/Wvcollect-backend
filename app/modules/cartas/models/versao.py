import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CartaModeloVersao(Base):
    __tablename__ = "carta_modelo_versao"

    id_versao: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    id_modelo: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "carta_modelo.id_modelo",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    numero_versao: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    nome_arquivo_original: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    storage_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
    )

    mime_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    tamanho_bytes: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    hash_sha256: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "id_modelo",
            "numero_versao",
            name="uq_carta_modelo_numero_versao",
        ),
        CheckConstraint(
            "numero_versao >= 1",
            name="ck_carta_modelo_versao_numero",
        ),
        CheckConstraint(
            """
            tamanho_bytes IS NULL
            OR tamanho_bytes >= 0
            """,
            name="ck_carta_modelo_versao_tamanho",
        ),
        Index(
            "ix_carta_modelo_versao_hash",
            "hash_sha256",
        ),
        Index(
            "ux_carta_modelo_versao_ativa",
            "id_modelo",
            unique=True,
            postgresql_where=text("ativo = true"),
        ),
    )
