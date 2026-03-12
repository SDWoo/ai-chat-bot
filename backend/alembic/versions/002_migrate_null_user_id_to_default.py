"""Migrate NULL user_id to default user

기존 user_id가 NULL인 데이터를 default user에 연결합니다.
ChromaDB의 기존 벡터 데이터는 user_id 메타데이터가 없으므로,
해당 데이터는 검색 시 필터링되어 조회되지 않습니다.
필요시 문서/지식을 재업로드하여 user_id가 포함된 벡터로 저장해야 합니다.

Revision ID: 002_migrate_null
Revises: 001_add_user
Create Date: 2025-03-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision: str = "002_migrate_null"
down_revision: Union[str, Sequence[str], None] = "002_add_user_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # default user 생성 (이미 있으면 스킵)
    result = conn.execute(
        text("SELECT id FROM users WHERE ms_oid = 'system-default-user' LIMIT 1")
    )
    row = result.fetchone()
    if row:
        default_user_id = row[0]
    else:
        op.execute(
            text("""
                INSERT INTO users (email, name, ms_oid, ms_tenant_id)
                VALUES ('system@default.local', 'System Default', 'system-default-user', NULL)
            """)
        )
        result = conn.execute(text("SELECT id FROM users WHERE ms_oid = 'system-default-user' LIMIT 1"))
        default_user_id = result.fetchone()[0]

    # user_id가 NULL인 기존 데이터를 default user에 연결
    conn.execute(
        text("UPDATE conversations SET user_id = :uid WHERE user_id IS NULL"),
        {"uid": default_user_id},
    )
    conn.execute(
        text("UPDATE documents SET user_id = :uid WHERE user_id IS NULL"),
        {"uid": default_user_id},
    )
    conn.execute(
        text("UPDATE knowledge_entries SET user_id = :uid WHERE user_id IS NULL"),
        {"uid": default_user_id},
    )


def downgrade() -> None:
    # default user의 데이터를 NULL로 되돌림
    conn = op.get_bind()
    conn.execute(
        text("""
            UPDATE conversations SET user_id = NULL
            WHERE user_id = (SELECT id FROM users WHERE ms_oid = 'system-default-user')
        """)
    )
    conn.execute(
        text("""
            UPDATE documents SET user_id = NULL
            WHERE user_id = (SELECT id FROM users WHERE ms_oid = 'system-default-user')
        """)
    )
    conn.execute(
        text("""
            UPDATE knowledge_entries SET user_id = NULL
            WHERE user_id = (SELECT id FROM users WHERE ms_oid = 'system-default-user')
        """)
    )
    conn.execute(text("DELETE FROM users WHERE ms_oid = 'system-default-user'"))
