"""add_location_and_servicable_location_models

Revision ID: 8346d84ebd78
Revises: 5bdbd37724da
Create Date: 2026-01-07 15:44:37.272226

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8346d84ebd78'
down_revision: Union[str, None] = '5bdbd37724da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create location table
    op.create_table('location',
        sa.Column('zip_code', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('zip_code')
    )
    
    # Create servicable_location junction table
    op.create_table('servicable_location',
        sa.Column('delivery_partner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_zip_code', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['delivery_partner_id'], ['delivery_partner.id'], ),
        sa.ForeignKeyConstraint(['location_zip_code'], ['location.zip_code'], ),
        sa.PrimaryKeyConstraint('delivery_partner_id', 'location_zip_code')
    )


def downgrade() -> None:
    # Drop tables
    op.drop_table('servicable_location')
    op.drop_table('location')
