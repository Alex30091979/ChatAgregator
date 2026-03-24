"""initial schema

Revision ID: 20260324_0001
Revises: 
Create Date: 2026-03-24 17:10:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260324_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "service_nodes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_service_nodes_id", "service_nodes", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_service_nodes_id", table_name="service_nodes")
    op.drop_table("service_nodes")

