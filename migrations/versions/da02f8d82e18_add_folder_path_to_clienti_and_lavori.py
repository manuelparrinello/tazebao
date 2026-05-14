"""add folder_path to clienti and lavori

Revision ID: da02f8d82e18
Revises: 0006_add_moodboard_tables
Create Date: 2026-05-14 17:22:45.902121

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'da02f8d82e18'
down_revision = '0006_add_moodboard_tables'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('clienti', schema=None) as batch_op:
        batch_op.add_column(sa.Column('folder_path', sa.String(length=255), nullable=True))
        batch_op.create_unique_constraint(batch_op.f('uq_clienti_folder_path'), ['folder_path'])

    with op.batch_alter_table('lavori', schema=None) as batch_op:
        batch_op.add_column(sa.Column('folder_path', sa.String(length=255), nullable=True))
        batch_op.create_unique_constraint(batch_op.f('uq_lavori_folder_path'), ['folder_path'])


def downgrade():
    with op.batch_alter_table('lavori', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('uq_lavori_folder_path'), type_='unique')
        batch_op.drop_column('folder_path')

    with op.batch_alter_table('clienti', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('uq_clienti_folder_path'), type_='unique')
        batch_op.drop_column('folder_path')
