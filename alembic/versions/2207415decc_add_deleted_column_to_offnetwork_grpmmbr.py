"""Add deleted column  to offNetwork GrpMmbr

Revision ID: 2207415decc
Revises: 135cacde446
Create Date: 2016-07-26 14:16:32.437248

"""

# revision identifiers, used by Alembic.
revision = '2207415decc'
down_revision = '135cacde446'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

def upgrade():
    op.add_column('off_network_group_members', sa.Column('deleted', sa.Boolean, nullable=True,default=False))
    off_network_group_members = table('off_network_group_members', column('deleted')) 
    op.execute(off_network_group_members.update().values(deleted=False)) 
    op.alter_column('off_network_group_members', 'deleted', nullable=False)

def downgrade():
    op.drop_column('off_network_group_members', 'deleted') 
