"""Add col deleted to off ntwrk contacts

Revision ID: 3e692fbbf04f
Revises: 11646adf2221
Create Date: 2016-08-08 14:37:54.802144

"""

# revision identifiers, used by Alembic.
revision = '3e692fbbf04f'
down_revision = '11646adf2221'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

def upgrade():
    op.add_column('off_network_contacts', sa.Column('deleted', sa.Boolean, nullable=True,default=False))
    off_network_contacts = table('off_network_contacts', column('deleted')) 
    op.execute(off_network_contacts.update().values(deleted=False)) 
    op.alter_column('off_network_contacts', 'deleted', nullable=False)
    op.alter_column('off_network_contacts', 'deleted', server_default=False)

def downgrade():
    op.drop_column('off_network_contacts', 'deleted') 
