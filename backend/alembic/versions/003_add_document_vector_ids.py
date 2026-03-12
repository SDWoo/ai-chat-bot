"""Add vector_ids to documents for ChromaDB chunk deletion

Revision ID: 003_vector_ids
Revises: 002_migrate_null
Create Date: 2025-03-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003_vector_ids"
down_revision: Union[str, Sequence[str], None] = "002_migrate_null"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("vector_ids", sa.JSON(), nullable=True, server_default="[]"))


def downgrade() -> None:
    op.drop_column("documents", "vector_ids")
