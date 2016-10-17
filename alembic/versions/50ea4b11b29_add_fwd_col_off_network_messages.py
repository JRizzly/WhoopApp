"""add fwd col off_network_messages

Revision ID: 50ea4b11b29
Revises: 179bebc9dad
Create Date: 2016-05-09 12:42:30.641106

"""

# revision identifiers, used by Alembic.
revision = '50ea4b11b29'
down_revision = '179bebc9dad'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('off_network_messages', sa.Column('forwarded', sa.Boolean, nullable = True, default = False))


def downgrade():
    op.drop_column('off_network_messages', 'forwarded')
