"""alter messages timestamp server generated

Revision ID: 4063d64ab51
Revises: 477c4b0f2ea
Create Date: 2016-04-05 10:32:56.408139

"""

# revision identifiers, used by Alembic.
revision = '4063d64ab51'
down_revision = '477c4b0f2ea'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('messages', 'send_date', type_ = sa.TIMESTAMP, server_default = sa.func.now())


def downgrade():
    op.alter_column('messages', 'send_date', type_ = sa.TIMESTAMP)
