"""initial migration with delivery partner

Revision ID: 2216e31738cd
Revises: 
Create Date: 2025-12-22 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '2216e31738cd'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create seller table with UUID
    op.create_table('seller',
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('password_hash', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_seller_email', 'seller', ['email'], unique=True)
    
    # Create delivery_partner table
    op.create_table('delivery_partner',
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('password_hash', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.Column('serviceable_zip_codes', sa.ARRAY(sa.INTEGER()), nullable=False),
        sa.Column('max_handling_capacity', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create shipment table with UUID and relationships
    op.create_table('shipment',
        sa.Column('content', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('destination', sa.Integer(), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('estimated_delivery', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.Column('seller_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('delivery_partner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['seller_id'], ['seller.id'], ),
        sa.ForeignKeyConstraint(['delivery_partner_id'], ['delivery_partner.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('shipment')
    op.drop_table('delivery_partner')
    op.drop_index('ix_seller_email', table_name='seller')
    op.drop_table('seller')
