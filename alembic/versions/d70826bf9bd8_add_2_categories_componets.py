"""add 2 categories componets

Revision ID: d70826bf9bd8
Revises: 7a601ba63b62
Create Date: 2025-06-23 22:31:12.303671

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd70826bf9bd8'
down_revision: Union[str, None] = '7a601ba63b62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('region_categories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=50), nullable=True),
    sa.Column('creator_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_region_categories_id'), 'region_categories', ['id'], unique=False)
    op.create_table('type_categories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=50), nullable=True),
    sa.Column('creator_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_type_categories_id'), 'type_categories', ['id'], unique=False)
    op.add_column('shipments', sa.Column('type_category_id', sa.Integer(), nullable=True))
    op.add_column('shipments', sa.Column('region_category_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'shipments', 'type_categories', ['type_category_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key(None, 'shipments', 'region_categories', ['region_category_id'], ['id'], ondelete='SET NULL')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'shipments', type_='foreignkey')
    op.drop_constraint(None, 'shipments', type_='foreignkey')
    op.drop_column('shipments', 'region_category_id')
    op.drop_column('shipments', 'type_category_id')
    op.drop_index(op.f('ix_type_categories_id'), table_name='type_categories')
    op.drop_table('type_categories')
    op.drop_index(op.f('ix_region_categories_id'), table_name='region_categories')
    op.drop_table('region_categories')
    # ### end Alembic commands ###
