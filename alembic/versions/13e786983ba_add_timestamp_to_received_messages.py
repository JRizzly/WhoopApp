"""Add Timestamp to received messages

Revision ID: 13e786983ba
Revises: 652377a4fa9e
Create Date: 2016-07-12 12:07:50.670127

"""

# revision identifiers, used by Alembic.
revision = '13e786983ba'
down_revision = '652377a4fa9e'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('received_messages', sa.Column('read_msg_timestamp', sa.TIMESTAMP, server_default = sa.func.now()))


def downgrade():
    op.drop_column('received_messages', 'read_msg_timestamp')
