"""Add Timestamp to messages

Revision ID: 2dd639d21338
Revises: 43c1daafcc75
Create Date: 2016-07-13 16:59:52.548098

"""

# revision identifiers, used by Alembic.
revision = '2dd639d21338'
down_revision = '43c1daafcc75'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('messages', sa.Column('timestamp', sa.TIMESTAMP, server_default = sa.func.now()))


def downgrade():
    op.drop_column('messages', 'timestamp')
