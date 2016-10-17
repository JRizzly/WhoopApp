"""create Device and DeviceCharacteristic tables

Revision ID: 492b1853d576
Revises: None
Create Date: 2016-03-21 13:48:15.657935

"""

# revision identifiers, used by Alembic.
revision = '492b1853d576'
down_revision = None

from alembic import op
import sqlalchemy as sa

from sqlalchemy import ForeignKey


def upgrade():
    op.add_column('device_characteristics', sa.Column('device_id', sa.Integer, ForeignKey("devices.id"), nullable = True))
    op.add_column('device_characteristics', sa.Column('type', sa.Unicode, nullable = True, server_default = ''))
    op.add_column('device_characteristics', sa.Column('os', sa.Unicode, nullable = True))
    op.add_column('device_characteristics', sa.Column('device_model', sa.Unicode, nullable = True))
    op.add_column('device_characteristics', sa.Column('carrier', sa.Unicode, nullable = True))
    op.add_column('device_characteristics', sa.Column('instance_id', sa.Unicode, nullable = True))



def downgrade():
    op.drop_column('device_characteristics', 'device_id')
    op.drop_column('device_characteristics', 'type')
    op.drop_column('device_characteristics', 'os')
    op.drop_column('device_characteristics', 'device_model')
    op.drop_column('device_characteristics', 'carrier')
    op.drop_column('device_characteristics', 'instance_id')
