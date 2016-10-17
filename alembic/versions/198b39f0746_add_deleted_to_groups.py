"""Add Deleted to Groups

Revision ID: 198b39f0746
Revises: 539402b60cf
Create Date: 2016-07-21 19:00:24.118539

"""

# revision identifiers, used by Alembic.
revision = '198b39f0746'
down_revision = '539402b60cf'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('groups', sa.Column('deleted', sa.Boolean, nullable = False, default = False))


def downgrade():
    op.drop_column('groups', 'deleted')
