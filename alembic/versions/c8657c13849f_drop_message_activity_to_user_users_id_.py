"""Drop message_activity.to_user - users.id FK

Revision ID: c8657c13849f
Revises: a462e5a9def0
Create Date: 2016-03-31 09:50:35.458115

"""

# revision identifiers, used by Alembic.
revision = 'c8657c13849f'
down_revision = 'a462e5a9def0'

from alembic import op
import sqlalchemy as sa


def upgrade():
#    op.drop_constraint("message_activity_to_user_id_fkey", "message_activity", type_ = "foreignkey")
    pass


def downgrade():
#    op.create_foreign_key(
#            "message_activity_to_user_id_fkey", "message_activity",
#            "users", ["to_user_id"], ["id"])
    pass
