"""Add User model and user_id to Conversation, Document, KnowledgeEntry

Revision ID: 001_add_user
Revises:
Create Date: 2025-03-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_add_user"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("ms_oid", sa.String(), nullable=False),
        sa.Column("ms_tenant_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_ms_oid"), "users", ["ms_oid"], unique=True)

    # Add user_id to conversations (nullable for migration)
    op.add_column("conversations", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_conversations_user_id",
        "conversations",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_conversations_user_id"), "conversations", ["user_id"], unique=False)

    # Add user_id to documents
    op.add_column("documents", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_documents_user_id",
        "documents",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_documents_user_id"), "documents", ["user_id"], unique=False)

    # Add user_id to knowledge_entries
    op.add_column("knowledge_entries", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_knowledge_entries_user_id",
        "knowledge_entries",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_knowledge_entries_user_id"), "knowledge_entries", ["user_id"], unique=False)


def downgrade() -> None:
    # Remove user_id from knowledge_entries
    op.drop_index(op.f("ix_knowledge_entries_user_id"), table_name="knowledge_entries")
    op.drop_constraint("fk_knowledge_entries_user_id", "knowledge_entries", type_="foreignkey")
    op.drop_column("knowledge_entries", "user_id")

    # Remove user_id from documents
    op.drop_index(op.f("ix_documents_user_id"), table_name="documents")
    op.drop_constraint("fk_documents_user_id", "documents", type_="foreignkey")
    op.drop_column("documents", "user_id")

    # Remove user_id from conversations
    op.drop_index(op.f("ix_conversations_user_id"), table_name="conversations")
    op.drop_constraint("fk_conversations_user_id", "conversations", type_="foreignkey")
    op.drop_column("conversations", "user_id")

    # Drop users table
    op.drop_index(op.f("ix_users_ms_oid"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
