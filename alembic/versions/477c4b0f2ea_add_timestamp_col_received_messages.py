"""add timestamp col received_messages

Revision ID: 477c4b0f2ea
Revises: c051345967aa
Create Date: 2016-04-04 16:50:01.042426

"""

# revision identifiers, used by Alembic.
revision = '477c4b0f2ea'
down_revision = 'c051345967aa'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('received_messages', sa.Column('timestamp', sa.TIMESTAMP, server_default = sa.func.now()))


def downgrade():
    op.drop_column('received_messages', 'timestamp')
