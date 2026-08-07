import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PDV(Base):
    __tablename__ = "dim_pdv"

    id_pdv: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    codigo_origem: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        index=True,
    )

    cnpj: Mapped[str | None] = mapped_column(
        String(14),
        nullable=True,
        index=True,
    )

    nome_pdv: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
    )

    endereco: Mapped[str | None] = mapped_column(Text)
    bairro: Mapped[str | None] = mapped_column(String(150))
    cidade: Mapped[str | None] = mapped_column(String(150))
    uf: Mapped[str | None] = mapped_column(String(2))

    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7))

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
            "cnpj IS NULL OR cnpj ~ '^[0-9]{14}$'",
            name="ck_dim_pdv_cnpj",
        ),
    )