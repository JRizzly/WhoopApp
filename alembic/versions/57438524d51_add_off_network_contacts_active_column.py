"""add_off_network_contacts_active_column

Revision ID: 57438524d51
Revises: c8657c13849f
Create Date: 2016-03-31 10:13:32.372774

"""

# revision identifiers, used by Alembic.
revision = '57438524d51'
down_revision = 'c8657c13849f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('off_network_contacts', sa.Column('active', sa.Boolean, nullable = True, default = True))


def downgrade():
    op.drop_column('off_network_contacts', 'active')
    
