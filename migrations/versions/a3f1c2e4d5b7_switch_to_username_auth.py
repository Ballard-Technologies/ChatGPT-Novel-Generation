"""switch to username auth

Drops email / email_verified and adds username.

NOTE: This is a destructive migration.  Any existing users rows are deleted
because there is no sensible automatic mapping from email addresses to
usernames, and on MariaDB/Postgres you cannot add a NOT NULL UNIQUE column
to a table that already has rows without a default.  If you need to
preserve accounts, back them up before running ``flask db upgrade`` and
re-create them manually afterwards.

Revision ID: a3f1c2e4d5b7
Revises: b8d9f850bbd5
Create Date: 2026-04-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a3f1c2e4d5b7'
down_revision = 'b8d9f850bbd5'
branch_labels = None
depends_on = None


def upgrade():
    # Wipe any existing rows so we can add a NOT NULL column cleanly.
    op.execute('DELETE FROM users')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_email'))
        batch_op.drop_column('email_verified')
        batch_op.drop_column('email')
        batch_op.add_column(
            sa.Column('username', sa.String(length=32), nullable=False)
        )
        batch_op.create_index(
            batch_op.f('ix_users_username'), ['username'], unique=True
        )


def downgrade():
    op.execute('DELETE FROM users')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_username'))
        batch_op.drop_column('username')
        batch_op.add_column(
            sa.Column('email', sa.String(length=254), nullable=False)
        )
        batch_op.add_column(
            sa.Column('email_verified', sa.Boolean(), nullable=False)
        )
        batch_op.create_index(
            batch_op.f('ix_users_email'), ['email'], unique=True
        )
