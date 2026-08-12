import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CartaModelo(Base):
    __tablename__ = "carta_modelo"

    id_modelo: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    nome: Mapped[str] = mapped_column(
        String(180),
        nullable=False,
    )

    tipo: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    granularidade: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
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

    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            """
            tipo IN (
                'ESTATICO',
                'VARIAVEL'
            )
            """,
            name="ck_carta_modelo_tipo",
        ),
        CheckConstraint(
            """
            granularidade IN (
                'PROMOTOR_REDE',
                'PDV'
            )
            """,
            name="ck_carta_modelo_granularidade",
        ),
        Index(
            "ix_carta_modelo_ativo",
            "ativo",
        ),
    )
