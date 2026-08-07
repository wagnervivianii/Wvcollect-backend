import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Pergunta(Base):
    __tablename__ = "dim_pergunta"

    id_pergunta: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    codigo: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    texto: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    tipo_resposta: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    aplica_sku: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    obrigatoria: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    ordem: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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
            "tipo_resposta IN ('SIM_NAO', 'TEXTO', 'NUMERO', 'SELECAO')",
            name="ck_dim_pergunta_tipo",
        ),
    )