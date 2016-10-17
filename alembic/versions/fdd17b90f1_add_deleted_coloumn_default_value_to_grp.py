"""Add deleted coloumn default value to Grp

Revision ID: fdd17b90f1
Revises: 287d5e9328a
Create Date: 2016-07-26 13:25:08.473207

"""

# revision identifiers, used by Alembic.
revision = 'fdd17b90f1'
down_revision = '287d5e9328a'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.alter_column('groups', 'deleted', server_default=False)


def downgrade():
    op.alter_column('groups', 'deleted', default=True)
