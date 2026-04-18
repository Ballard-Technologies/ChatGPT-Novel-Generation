"""user prompt settings column

Adds a nullable ``prompt_settings_json`` column to the ``users`` table used
to persist per-user overrides for the story-generation prompt templates.

Revision ID: d4b1a0f5e219
Revises: c7e2a9d41f08
Create Date: 2026-04-18 00:00:02.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = 'd4b1a0f5e219'
down_revision = 'c7e2a9d41f08'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'prompt_settings_json',
                sa.Text().with_variant(mysql.LONGTEXT(), 'mysql'),
                nullable=True,
            )
        )


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('prompt_settings_json')
