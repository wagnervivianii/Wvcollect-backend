"""add incomplete submission audit

Revision ID: 96326ce850aa
Revises: d6a3bbfa5e5a
Create Date: 2026-08-07

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "96326ce850aa"
down_revision: Union[str, None] = "d6a3bbfa5e5a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "fto_pesquisa",
        sa.Column(
            "envio_com_pendencias",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.add_column(
        "fto_pesquisa",
        sa.Column(
            "campos_pendentes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    op.add_column(
        "fto_pesquisa",
        sa.Column(
            "pendencias_confirmadas_em_dispositivo",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "fto_pesquisa",
        "pendencias_confirmadas_em_dispositivo",
    )

    op.drop_column(
        "fto_pesquisa",
        "campos_pendentes",
    )

    op.drop_column(
        "fto_pesquisa",
        "envio_com_pendencias",
    )