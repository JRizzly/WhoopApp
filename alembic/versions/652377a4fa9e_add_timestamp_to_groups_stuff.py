"""Add Timestamp to Groups Stuff

Revision ID: 652377a4fa9e
Revises: 50ea4b11b29
Create Date: 2016-07-11 17:59:28.748746

"""

# revision identifiers, used by Alembic.
revision = '652377a4fa9e'
down_revision = '50ea4b11b29'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('groups', sa.Column('timestamp', sa.TIMESTAMP, server_default = sa.func.now()))
    op.add_column('group_members', sa.Column('timestamp', sa.TIMESTAMP, server_default = sa.func.now()))
    op.add_column('contacts', sa.Column('timestamp', sa.TIMESTAMP, server_default = sa.func.now()))

def downgrade():
    op.drop_column('groups', 'timestamp')
    op.drop_column('group_members', 'timestamp')
    op.drop_column('contacts', 'timestamp')

