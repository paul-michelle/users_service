"""create users table

Revision ID: 876637f0e825
Revises: 
Create Date: 2022-08-26 07:10:54.096111+00:00

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '876637f0e825'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('users',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('username', sa.String(length=20), nullable=False),
    sa.Column('email', sa.String(length=254), nullable=False),
    sa.Column('password', sa.String(length=128), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('admin', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )


def downgrade() -> None:
    op.drop_table('users')
