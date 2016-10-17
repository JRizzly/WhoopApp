"""alter fwd_msg_id to new_msg_id and add fwded_msg_id message_activity

Revision ID: 2b68092d119
Revises: 17861ea39ff
Create Date: 2016-04-08 09:17:47.450635

"""

# revision identifiers, used by Alembic.
revision = '2b68092d119'
down_revision = '17861ea39ff'

from alembic import op
import sqlalchemy as sa

from sqlalchemy import ForeignKey

def upgrade():
    op.alter_column('message_activity', 'fwd_message_id', new_column_name = 'new_message_id')
    op.add_column('message_activity', sa.Column('fwded_message_id', sa.Integer, ForeignKey("messages.id"), nullable = True))


def downgrade():
    op.alter_column('message_activity', 'new_message_id', new_column_name = 'fwd_message_id')
    op.drop_column('message_activity', 'fwded_message_id')
