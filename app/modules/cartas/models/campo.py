import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CartaModeloCampo(Base):
    __tablename__ = "carta_modelo_campo"

    id_campo: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    id_versao: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "carta_modelo_versao.id_versao",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    nome_original: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    chave_normalizada: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    obrigatorio: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    ordem: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "id_versao",
            "chave_normalizada",
            name="uq_carta_modelo_campo_versao_chave",
        ),
        CheckConstraint(
            "ordem >= 1",
            name="ck_carta_modelo_campo_ordem",
        ),
    )
