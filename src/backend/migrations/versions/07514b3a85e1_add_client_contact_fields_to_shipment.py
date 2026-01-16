"""add_client_contact_fields_to_shipment

Revision ID: 07514b3a85e1
Revises: f7e30f5812f2
Create Date: 2025-12-30 15:27:34.330964

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '07514b3a85e1'
down_revision: Union[str, None] = 'f7e30f5812f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add client contact fields to shipment table (nullable for Phase 1)
    op.add_column('shipment', sa.Column('client_contact_email', sa.String(), nullable=True))
    op.add_column('shipment', sa.Column('client_contact_phone', sa.String(), nullable=True))
    
    # Phase 2: Set placeholder emails for existing shipments (optional - can be done later)
    # op.execute("UPDATE shipment SET client_contact_email = 'placeholder@example.com' WHERE client_contact_email IS NULL")


def downgrade() -> None:
    # Remove client contact fields
    op.drop_column('shipment', 'client_contact_phone')
    op.drop_column('shipment', 'client_contact_email')
