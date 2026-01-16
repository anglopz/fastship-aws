"""add_tag_and_shipment_tag_models

Revision ID: 5bdbd37724da
Revises: da0c0995c499
Create Date: 2026-01-07 15:31:01.634542

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5bdbd37724da'
down_revision: Union[str, None] = 'da0c0995c499'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create TagName enum type (only if it doesn't exist)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE tagname AS ENUM ('express', 'standard', 'fragile', 'heavy', 'international', 'domestic', 'temperature_controlled', 'gift', 'return', 'documents');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Check if tables exist before creating
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Create tag table (only if it doesn't exist)
    if 'tag' not in existing_tables:
        op.create_table('tag',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('name', postgresql.ENUM('express', 'standard', 'fragile', 'heavy', 'international', 'domestic', 'temperature_controlled', 'gift', 'return', 'documents', name='tagname', create_type=False), nullable=False),
            sa.Column('instruction', sa.String(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Create shipment_tag junction table (only if it doesn't exist)
    if 'shipment_tag' not in existing_tables:
        op.create_table('shipment_tag',
            sa.Column('shipment_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('tag_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.ForeignKeyConstraint(['shipment_id'], ['shipment.id'], ),
            sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], ),
            sa.PrimaryKeyConstraint('shipment_id', 'tag_id')
        )


def downgrade() -> None:
    # Drop tables
    op.drop_table('shipment_tag')
    op.drop_table('tag')
    
    # Drop enum type
    op.execute("DROP TYPE tagname")
