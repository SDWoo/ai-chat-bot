"""Add image_url to messages for vision chat support

Revision ID: 004_image_url
Revises: 003_vector_ids
Create Date: 2026-03-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004_image_url"
down_revision: Union[str, Sequence[str], None] = "003_vector_ids"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("image_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("messages", "image_url")
