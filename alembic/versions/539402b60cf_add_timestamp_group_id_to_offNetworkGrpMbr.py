"""Add Timestamp and group id to OffNetworkGroupMembers

Revision ID: 539402b60cf
Revises: 2dd639d21338
Create Date: 2016-07-16 16:26:20.904624

"""

# revision identifiers, used by Alembic.
revision = '539402b60cf'
down_revision = '2dd639d21338'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import ForeignKey


def upgrade():
    op.add_column('off_network_group_members', sa.Column('group_id', sa.Integer, ForeignKey("groups.id"), nullable = True))
    op.add_column('off_network_group_members', sa.Column('timestamp', sa.TIMESTAMP, server_default = sa.func.now()))

def downgrade():
    op.drop_column('off_network_group_members', 'group_id')
    op.drop_column('off_network_group_members', 'timestamp')

