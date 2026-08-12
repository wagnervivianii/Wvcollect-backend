import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CartaModeloRede(Base):
    __tablename__ = "carta_modelo_rede"

    id_modelo_rede: Mapped[uuid.UUID] = mapped_column(
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

    rede: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    rede_normalizada: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "id_modelo",
            "rede_normalizada",
            name="uq_carta_modelo_rede",
        ),
        Index(
            "ix_carta_modelo_rede_normalizada",
            "rede_normalizada",
        ),
    )
