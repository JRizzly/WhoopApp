"""alter send_date message_activity server time

Revision ID: 17861ea39ff
Revises: 4063d64ab51
Create Date: 2016-04-05 11:54:45.644341

"""

# revision identifiers, used by Alembic.
revision = '17861ea39ff'
down_revision = '4063d64ab51'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('message_activity', 'send_date', type_ = sa.TIMESTAMP, server_default = sa.func.now())


def downgrade():
    op.alter_column('message_activity', 'send_date', type_ = sa.TIMESTAMP)
