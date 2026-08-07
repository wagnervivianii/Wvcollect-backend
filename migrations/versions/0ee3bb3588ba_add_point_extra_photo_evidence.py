"""add point extra photo evidence

Revision ID: 0ee3bb3588ba
Revises: 96326ce850aa
Create Date: 2026-08-07

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0ee3bb3588ba"
down_revision: Union[str, None] = "96326ce850aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_foto_tipo_evidencia",
        "fto_foto",
        type_="check",
    )

    op.create_check_constraint(
        "ck_foto_tipo_evidencia",
        "fto_foto",
        """
        tipo_evidencia IN (
            'ANTES',
            'DEPOIS',
            'PONTO_EXTRA',
            'GIRO_ESTOQUE'
        )
        """,
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_foto_tipo_evidencia",
        "fto_foto",
        type_="check",
    )

    op.create_check_constraint(
        "ck_foto_tipo_evidencia",
        "fto_foto",
        """
        tipo_evidencia IN (
            'ANTES',
            'DEPOIS',
            'GIRO_ESTOQUE'
        )
        """,
    )