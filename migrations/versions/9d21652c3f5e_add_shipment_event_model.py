"""add shipment event model

Revision ID: 9d21652c3f5e
Revises: 2216e31738cd
Create Date: 2025-01-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '9d21652c3f5e'
down_revision: Union[str, None] = '2216e31738cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add cancelled status to shipment status enum (if using enum type)
    # Note: Since we're using string type, no enum migration needed
    
    # Create shipment_event table
    op.create_table('shipment_event',
        sa.Column('location', sa.Integer(), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.Column('shipment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipment.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_shipment_event_shipment_id', 'shipment_event', ['shipment_id'], unique=False)


def downgrade() -> None:
    # Drop shipment_event table
    op.drop_index('ix_shipment_event_shipment_id', table_name='shipment_event')
    op.drop_table('shipment_event')

