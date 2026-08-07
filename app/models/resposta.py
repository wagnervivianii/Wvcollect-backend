import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Resposta(Base):
    __tablename__ = "fto_resposta"

    id_resposta: Mapped[uuid.UUID] = mapped_column(
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

    id_pergunta: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dim_pergunta.id_pergunta"),
        nullable=False,
    )

    id_sku: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dim_sku.id_sku"),
        nullable=True,
    )

    valor: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    respondida_em_dispositivo: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    recebida_em_servidor: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "id_pesquisa",
            "id_pergunta",
            "id_sku",
            name="uq_resposta_pesquisa_pergunta_sku",
            postgresql_nulls_not_distinct=True,
        ),
        Index("ix_resposta_pesquisa", "id_pesquisa"),
        Index("ix_resposta_sku", "id_sku"),
    )