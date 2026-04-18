"""novels table

Adds the ``novels`` table used by the "My novels" feature to persist
generated novels per logged-in user.

Revision ID: c7e2a9d41f08
Revises: a3f1c2e4d5b7
Create Date: 2026-04-18 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = 'c7e2a9d41f08'
down_revision = 'a3f1c2e4d5b7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'novels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column(
            'chapters_json',
            sa.Text().with_variant(mysql.LONGTEXT(), 'mysql'),
            nullable=False,
        ),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('novels', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_novels_user_id'),
                              ['user_id'], unique=False)


def downgrade():
    with op.batch_alter_table('novels', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_novels_user_id'))
    op.drop_table('novels')
