"""Add Timestamp to off network contacts

Revision ID: 43c1daafcc75
Revises: 13e786983ba
Create Date: 2016-07-13 16:54:25.500340

"""

# revision identifiers, used by Alembic.
revision = '43c1daafcc75'
down_revision = '13e786983ba'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('off_network_contacts', sa.Column('timestamp', sa.TIMESTAMP, server_default = sa.func.now()))


def downgrade():
    op.drop_column('off_network_contacts', 'timestamp')


