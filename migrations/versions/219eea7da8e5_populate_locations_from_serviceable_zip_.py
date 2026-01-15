"""populate_locations_from_serviceable_zip_codes

Revision ID: 219eea7da8e5
Revises: 8346d84ebd78
Create Date: 2026-01-07 15:46:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '219eea7da8e5'
down_revision: Union[str, None] = '8346d84ebd78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Populate location and servicable_location tables from existing serviceable_zip_codes ARRAY field.
    This migration ensures backward compatibility by migrating existing data.
    """
    # Get database connection
    conn = op.get_bind()
    
    # Get all delivery partners with their serviceable_zip_codes
    partners_result = conn.execute(sa.text("""
        SELECT id, serviceable_zip_codes 
        FROM delivery_partner 
        WHERE serviceable_zip_codes IS NOT NULL 
        AND array_length(serviceable_zip_codes, 1) > 0
    """))
    
    partners = partners_result.fetchall()
    
    # Track unique zip codes to create Location records
    unique_zip_codes = set()
    partner_locations = []  # List of (partner_id, zip_code) tuples
    
    for partner_id, zip_codes in partners:
        if zip_codes:
            for zip_code in zip_codes:
                unique_zip_codes.add(zip_code)
                partner_locations.append((partner_id, zip_code))
    
    # Create Location records for unique zip codes
    for zip_code in unique_zip_codes:
        # Use INSERT ... ON CONFLICT DO NOTHING to handle duplicates
        conn.execute(sa.text("""
            INSERT INTO location (zip_code) 
            VALUES (:zip_code)
            ON CONFLICT (zip_code) DO NOTHING
        """), {"zip_code": zip_code})
    
    # Create ServicableLocation records
    for partner_id, zip_code in partner_locations:
        # Use INSERT ... ON CONFLICT DO NOTHING to handle duplicates
        conn.execute(sa.text("""
            INSERT INTO servicable_location (delivery_partner_id, location_zip_code) 
            VALUES (:partner_id, :zip_code)
            ON CONFLICT (delivery_partner_id, location_zip_code) DO NOTHING
        """), {"partner_id": partner_id, "zip_code": zip_code})
    
    # Commit the transaction
    conn.commit()


def downgrade() -> None:
    """
    Remove all location data (locations will be recreated if needed).
    Note: This does NOT restore serviceable_zip_codes as they were never removed.
    """
    # Clear servicable_location table
    op.execute("DELETE FROM servicable_location")
    
    # Clear location table
    op.execute("DELETE FROM location")
