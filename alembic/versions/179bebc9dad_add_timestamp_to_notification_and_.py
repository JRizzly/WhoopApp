"""Add timestamp to Notification and VerificationCode

Revision ID: 179bebc9dad
Revises: 12c1897643b
Create Date: 2016-04-19 12:03:54.358401

"""

# revision identifiers, used by Alembic.
revision = '179bebc9dad'
down_revision = '12c1897643b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('notifications', sa.Column('timestamp', sa.TIMESTAMP, server_default = sa.func.now()))
    op.add_column('verification_codes', sa.Column('timestamp', sa.TIMESTAMP, server_default = sa.func.now()))


def downgrade():
    op.drop_column('notifications', 'timestamp')
    op.drop_column('verification_codes', 'timestamp')
