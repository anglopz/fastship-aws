"""add_review_model

Revision ID: da0c0995c499
Revises: 97d9ffdac66e
Create Date: 2025-12-30 16:23:38.661227

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'da0c0995c499'
down_revision: Union[str, None] = '97d9ffdac66e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create review table only
    op.create_table(
        'review',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.String(), nullable=True),
        sa.Column('shipment_id', postgresql.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipment.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('shipment_id')  # One-to-one relationship
    )


def downgrade() -> None:
    # Drop review table
    op.drop_table('review')
