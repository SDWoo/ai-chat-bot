"""Add user_id columns to existing tables (users table already exists)

users 테이블은 이미 init_db 등으로 생성되어 있음.
conversations, documents, knowledge_entries에 user_id 컬럼만 추가.

Revision ID: 002_add_user_id
Revises: 001_add_user
Create Date: 2025-03-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_add_user_id"
down_revision: Union[str, Sequence[str], None] = "001_add_user"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(conn, table: str, column: str) -> bool:
    result = conn.execute(
        sa.text(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = :t AND column_name = :c
            """
        ),
        {"t": table, "c": column},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    conn = op.get_bind()

    for table in ["conversations", "documents", "knowledge_entries"]:
        if not column_exists(conn, table, "user_id"):
            op.add_column(table, sa.Column("user_id", sa.Integer(), nullable=True))
            op.create_foreign_key(
                f"fk_{table}_user_id",
                table,
                "users",
                ["user_id"],
                ["id"],
                ondelete="SET NULL",
            )
            op.create_index(op.f(f"ix_{table}_user_id"), table, ["user_id"], unique=False)


def downgrade() -> None:
    for table in ["conversations", "documents", "knowledge_entries"]:
        op.drop_index(op.f(f"ix_{table}_user_id"), table_name=table)
        op.drop_constraint(f"fk_{table}_user_id", table, type_="foreignkey")
        op.drop_column(table, "user_id")
