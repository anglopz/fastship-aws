"""add_email_verified_field

Revision ID: f7e30f5812f2
Revises: 9d21652c3f5e
Create Date: 2025-12-30 14:00:04.563722

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7e30f5812f2'
down_revision: Union[str, None] = '9d21652c3f5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add email_verified column to seller table
    op.add_column('seller', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    
    # Add email_verified column to delivery_partner table
    op.add_column('delivery_partner', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    
    # Set all existing users to email_verified=True (Phase 2: migration for existing data)
    op.execute("UPDATE seller SET email_verified = true WHERE email_verified = false")
    op.execute("UPDATE delivery_partner SET email_verified = true WHERE email_verified = false")


def downgrade() -> None:
    # Remove email_verified column from both tables
    op.drop_column('delivery_partner', 'email_verified')
    op.drop_column('seller', 'email_verified')
