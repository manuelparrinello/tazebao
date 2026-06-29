"""add_editorial_share_links

Revision ID: f48156ee567e
Revises: b33569854077
Create Date: 2026-06-29 16:28:43.130723

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f48156ee567e'
down_revision = 'b33569854077'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('erp_editorial_share_links',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('token', sa.String(length=36), nullable=False),
    sa.Column('cliente_id', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('month', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_by_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['cliente_id'], ['clienti.id'], name=op.f('fk_erp_editorial_share_links_cliente_id_clienti')),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], name=op.f('fk_erp_editorial_share_links_created_by_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_erp_editorial_share_links'))
    )
    with op.batch_alter_table('erp_editorial_share_links', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_erp_editorial_share_links_cliente_id'), ['cliente_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_erp_editorial_share_links_token'), ['token'], unique=True)


def downgrade():
    with op.batch_alter_table('erp_editorial_share_links', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_erp_editorial_share_links_token'))
        batch_op.drop_index(batch_op.f('ix_erp_editorial_share_links_cliente_id'))

    op.drop_table('erp_editorial_share_links')
