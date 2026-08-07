"""add recollection tracking

Revision ID: d6a3bbfa5e5a
Revises: fecd6c58f685
Create Date: 2026-08-07

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.

revision: str = "d6a3bbfa5e5a"
down_revision: Union[str, Sequence[str], None] = "fecd6c58f685"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "fto_pesquisa",
        sa.Column(
            "numero_coleta",
            sa.Integer(),
            server_default="1",
            nullable=False,
        ),
    )

    op.add_column(
        "fto_pesquisa",
        sa.Column(
            "id_pesquisa_origem",
            sa.UUID(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_pesquisa_origem",
        "fto_pesquisa",
        ["id_pesquisa_origem"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_fto_pesquisa_origem",
        "fto_pesquisa",
        "fto_pesquisa",
        ["id_pesquisa_origem"],
        ["id_pesquisa"],
        ondelete="SET NULL",
    )

    op.create_check_constraint(
        "ck_pesquisa_numero_coleta",
        "fto_pesquisa",
        "numero_coleta >= 1",
    )

    op.create_check_constraint(
        "ck_pesquisa_origem_diferente",
        "fto_pesquisa",
        """
        id_pesquisa_origem IS NULL
        OR id_pesquisa_origem <> id_pesquisa
        """,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "ck_pesquisa_origem_diferente",
        "fto_pesquisa",
        type_="check",
    )

    op.drop_constraint(
        "ck_pesquisa_numero_coleta",
        "fto_pesquisa",
        type_="check",
    )

    op.drop_constraint(
        "fk_fto_pesquisa_origem",
        "fto_pesquisa",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_pesquisa_origem",
        table_name="fto_pesquisa",
    )

    op.drop_column(
        "fto_pesquisa",
        "id_pesquisa_origem",
    )

    op.drop_column(
        "fto_pesquisa",
        "numero_coleta",
    )