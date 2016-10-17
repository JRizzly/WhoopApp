"""add off-network flag to message_activity

Revision ID: a462e5a9def0
Revises: 492b1853d576
Create Date: 2016-03-28 15:48:12.661977

"""

# revision identifiers, used by Alembic.
revision = 'a462e5a9def0'
down_revision = '492b1853d576'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('message_activity', sa.Column('off_network', sa.Boolean, nullable = True, default = False))


def downgrade():
    op.drop_column('message_activity', 'off_network')
