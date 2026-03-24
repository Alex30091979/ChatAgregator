"""add chat operator and status

Revision ID: 20260324_0004
Revises: 20260324_0003
Create Date: 2026-03-24 19:05:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260324_0004"
down_revision: str | None = "20260324_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "chats",
        sa.Column("operator_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "chats",
        sa.Column("status", sa.String(length=32), nullable=False, server_default="new"),
    )
    op.create_foreign_key("fk_chats_operator_id_users", "chats", "users", ["operator_id"], ["id"])
    op.create_index("ix_chats_operator_id", "chats", ["operator_id"], unique=False)
    op.create_index("ix_chats_status", "chats", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_chats_status", table_name="chats")
    op.drop_index("ix_chats_operator_id", table_name="chats")
    op.drop_constraint("fk_chats_operator_id_users", "chats", type_="foreignkey")
    op.drop_column("chats", "status")
    op.drop_column("chats", "operator_id")

