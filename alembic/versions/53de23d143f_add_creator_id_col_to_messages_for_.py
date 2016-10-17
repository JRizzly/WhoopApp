"""Add creator_id col to messages for forwarding

Revision ID: 53de23d143f
Revises: 562a677e604
Create Date: 2016-04-04 13:41:16.611913

"""

# revision identifiers, used by Alembic.
revision = '53de23d143f'
down_revision = '562a677e604'

from alembic import op
import sqlalchemy as sa

from sqlalchemy import ForeignKey

def upgrade():
    op.add_column('messages', sa.Column('creator_id', sa.Integer, ForeignKey("users.id"), nullable = True))


def downgrade():
    op.drop_column('messages', 'creator_id')
