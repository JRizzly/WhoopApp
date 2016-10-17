"""Add Forwarded Bool col to Message

Revision ID: 2efdb73da754
Revises: 6d0c5d94e818
Create Date: 2016-04-01 13:27:53.155334

"""

# revision identifiers, used by Alembic.
revision = '2efdb73da754'
down_revision = '6d0c5d94e818'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('messages', sa.Column('forwarded', sa.Boolean, nullable = True, default = False))


def downgrade():
    op.drop_column('messages', 'forwarded')
