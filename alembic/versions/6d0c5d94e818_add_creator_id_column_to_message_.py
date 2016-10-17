"""Add creator_id column to message_activity

Revision ID: 6d0c5d94e818
Revises: 57438524d51
Create Date: 2016-03-31 17:48:30.944797

"""

# revision identifiers, used by Alembic.
revision = '6d0c5d94e818'
down_revision = '57438524d51'

from alembic import op
import sqlalchemy as sa

from sqlalchemy import ForeignKey


def upgrade():
    op.add_column('message_activity', sa.Column('creator_id', sa.Integer, ForeignKey("users.id"), nullable = True))


def downgrade():
    op.drop_column('message_activity', 'creator_id')
