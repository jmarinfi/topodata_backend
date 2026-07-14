"""fix_content_hash_unique_per_project

Revision ID: 82cf0182e30e
Revises: b557707b768a
Create Date: 2026-07-14 16:07:40.544381

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82cf0182e30e'
down_revision: Union[str, Sequence[str], None] = 'b557707b768a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('import_sessions') as batch_op:
        batch_op.drop_index('ix_import_sessions_content_hash')
        batch_op.create_index(batch_op.f('ix_import_sessions_content_hash'), ['content_hash'], unique=False)
        batch_op.create_unique_constraint('uq_import_session_project_hash', ['project_id', 'content_hash'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('import_sessions') as batch_op:
        batch_op.drop_constraint('uq_import_session_project_hash', type_='unique')
        batch_op.drop_index(batch_op.f('ix_import_sessions_content_hash'))
        batch_op.create_index(batch_op.f('ix_import_sessions_content_hash'), ['content_hash'], unique=True)
