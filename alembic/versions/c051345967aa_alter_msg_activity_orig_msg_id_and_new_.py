"""alter msg activity orig msg id and new msg id

Revision ID: c051345967aa
Revises: 53de23d143f
Create Date: 2016-04-04 14:32:45.236271

"""

# revision identifiers, used by Alembic.
revision = 'c051345967aa'
down_revision = '53de23d143f'

from alembic import op
import sqlalchemy as sa

from sqlalchemy import ForeignKey

def upgrade():
    op.alter_column('message_activity', 'message_id', new_column_name = 'orig_message_id')
    op.add_column('message_activity', sa.Column('fwd_message_id', sa.Integer, ForeignKey("messages.id"), nullable = True))


def downgrade():
    op.alter_column('message_activity', 'orig_message_id', new_column_name = 'message_id')
    op.drop_column('message_activity', 'fwd_message_id')
