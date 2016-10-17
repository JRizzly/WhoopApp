"""Add deleted coloumn default value to Groups

Revision ID: 287d5e9328a
Revises: 198b39f0746
Create Date: 2016-07-26 12:55:42.679240

"""

# revision identifiers, used by Alembic.
revision = '287d5e9328a'
down_revision = '198b39f0746'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.alter_column('groups', 'deleted', nullable=False)


def downgrade():
    op.alter_column('groups', 'deleted', nullable=True)
