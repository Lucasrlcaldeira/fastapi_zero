"""add created_at and updated_at to todos

Revision ID: a99cdc5af920
Revises: 99d8f5d0f16c
Create Date: 2026-10-06 18:03:36.809058

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a99cdc5af920'
down_revision: Union[str, Sequence[str], None] = '99d8f5d0f16c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # O SQLite não aceita ADD COLUMN com valor padrão "não constante"
    # (CURRENT_TIMESTAMP muda a cada momento). O batch_alter_table
    # contorna isso: cria uma tabela nova já com as colunas, copia os
    # dados da antiga, apaga a antiga e renomeia a nova para "todos".
    with op.batch_alter_table('todos') as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    # Também em modo batch, para desfazer do mesmo jeito no SQLite.
    with op.batch_alter_table('todos') as batch_op:
        batch_op.drop_column('updated_at')
        batch_op.drop_column('created_at')
