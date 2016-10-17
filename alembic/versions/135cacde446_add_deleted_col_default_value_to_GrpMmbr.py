"""Add deleted coloumn default value to GrpMmbr

Revision ID: 135cacde446
Revises: fdd17b90f1
Create Date: 2016-07-26 13:48:38.705787

"""

# revision identifiers, used by Alembic.
revision = '135cacde446'
down_revision = 'fdd17b90f1'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

def upgrade():
    op.add_column('group_members', sa.Column('deleted', sa.Boolean, nullable=True,default=False))
    group_members = table('group_members', column('deleted')) 
    op.execute(group_members.update().values(deleted=False)) 
    op.alter_column('group_members', 'deleted', nullable=False)
    op.alter_column('group_members', 'deleted', server_default=False)

def downgrade():
    op.drop_column('group_members', 'deleted')
