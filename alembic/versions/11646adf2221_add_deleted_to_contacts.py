"""Add deleted to contacts

Revision ID: 11646adf2221
Revises: 2207415decc
Create Date: 2016-08-01 15:31:38.666246

"""

# revision identifiers, used by Alembic.
revision = '11646adf2221'
down_revision = '2207415decc'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column 


def upgrade():
    op.add_column('contacts', sa.Column('deleted', sa.Boolean, nullable=True,default=False))
    contacts = table('contacts', column('deleted')) 
    op.execute(contacts.update().values(deleted=False)) 
    op.alter_column('contacts', 'deleted', nullable=False)
    op.alter_column('contacts', 'deleted', server_default=False)

def downgrade():
    op.drop_column('contacts', 'deleted')  

