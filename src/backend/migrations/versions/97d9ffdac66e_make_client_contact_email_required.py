"""make_client_contact_email_required

Revision ID: 97d9ffdac66e
Revises: 07514b3a85e1
Create Date: 2025-12-30 15:35:30.663757

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '97d9ffdac66e'
down_revision: Union[str, None] = '07514b3a85e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Phase 2: Set placeholder emails for existing shipments that have NULL
    op.execute(
        "UPDATE shipment SET client_contact_email = 'placeholder@example.com' "
        "WHERE client_contact_email IS NULL"
    )
    
    # Make client_contact_email non-nullable
    op.alter_column(
        'shipment',
        'client_contact_email',
        nullable=False,
        existing_type=sa.String(),
    )


def downgrade() -> None:
    # Make client_contact_email nullable again (Phase 1 state)
    op.alter_column(
        'shipment',
        'client_contact_email',
        nullable=True,
        existing_type=sa.String(),
    )
