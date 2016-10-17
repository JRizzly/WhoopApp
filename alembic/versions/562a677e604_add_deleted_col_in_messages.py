"""Add deleted col in messages

Revision ID: 562a677e604
Revises: 2efdb73da754
Create Date: 2016-04-01 16:19:20.470834

"""

# revision identifiers, used by Alembic.
revision = '562a677e604'
down_revision = '2efdb73da754'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('messages', sa.Column('deleted', sa.Boolean, nullable = True, default = False))


def downgrade():
    op.drop_column('messages', 'deleted')
