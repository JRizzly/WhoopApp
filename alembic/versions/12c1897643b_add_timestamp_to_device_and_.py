"""Add timestamp to Device and DeviceCharacteristic

Revision ID: 12c1897643b
Revises: 43b10bbd7d6
Create Date: 2016-04-18 16:54:39.948921

"""

# revision identifiers, used by Alembic.
revision = '12c1897643b'
down_revision = '43b10bbd7d6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('devices', sa.Column('timestamp', sa.TIMESTAMP, server_default = sa.func.now()))
    op.add_column('device_characteristics', sa.Column('timestamp', sa.TIMESTAMP, server_default = sa.func.now()))


def downgrade():
    op.drop_column('devices', 'timestamp')
    op.drop_column('device_characteristics', 'timestamp')
