"""remove_serviceable_zip_codes_array_field

Revision ID: e07ee45021e6
Revises: 219eea7da8e5
Create Date: 2026-01-07 15:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e07ee45021e6'
down_revision: Union[str, None] = '219eea7da8e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Phase 3: Remove serviceable_zip_codes ARRAY field.
    All data has been migrated to servicable_locations relationship in Phase 2.
    This is a breaking change - the ARRAY field is no longer available.
    """
    # Drop the serviceable_zip_codes column
    op.drop_column('delivery_partner', 'serviceable_zip_codes')


def downgrade() -> None:
    """
    Restore serviceable_zip_codes ARRAY field.
    Note: This will NOT restore the data - it will be NULL for all partners.
    Data would need to be restored from servicable_locations relationship separately.
    """
    # Add the serviceable_zip_codes column back (nullable, as we can't restore data)
    op.add_column('delivery_partner',
        sa.Column('serviceable_zip_codes', postgresql.ARRAY(sa.INTEGER()), nullable=True)
    )
