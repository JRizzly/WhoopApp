"""alter_device_chars_instance_id_nullable

Revision ID: 43b10bbd7d6
Revises: 2b68092d119
Create Date: 2016-04-13 14:09:16.176325

"""

# revision identifiers, used by Alembic.
revision = '43b10bbd7d6'
down_revision = '2b68092d119'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('device_characteristics', 'instance_id', nullable = True)


def downgrade():
    op.alter_column('device_characteristics', 'instance_id', nullable = False)
