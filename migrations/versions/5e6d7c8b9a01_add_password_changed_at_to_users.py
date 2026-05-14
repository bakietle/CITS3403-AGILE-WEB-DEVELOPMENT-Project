"""add password_changed_at to users

Revision ID: 5e6d7c8b9a01
Revises: 116e9e120615
Create Date: 2026-05-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5e6d7c8b9a01'
down_revision = '116e9e120615'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('password_changed_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('password_changed_at')
