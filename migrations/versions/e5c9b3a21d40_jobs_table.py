"""jobs table

Adds the ``jobs`` table used to track asynchronous novel-generation
requests. Jobs are created by the web worker, enqueued to Redis/RQ (or a
synchronous dev fallback), and executed by a separate worker process.

Revision ID: e5c9b3a21d40
Revises: d4b1a0f5e219
Create Date: 2026-04-18 00:00:03.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = 'e5c9b3a21d40'
down_revision = 'd4b1a0f5e219'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'jobs',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('anon_session_id', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('version', sa.String(length=8), nullable=False),
        sa.Column('model', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column(
            'summary',
            sa.Text().with_variant(mysql.LONGTEXT(), 'mysql'),
            nullable=False,
        ),
        sa.Column('api_key', sa.Text(), nullable=False),
        sa.Column(
            'prompt_overrides_json',
            sa.Text().with_variant(mysql.LONGTEXT(), 'mysql'),
            nullable=True,
        ),
        sa.Column('current', sa.Integer(), nullable=False),
        sa.Column('total', sa.Integer(), nullable=False),
        sa.Column('fail_message', sa.Text(), nullable=True),
        sa.Column(
            'chapters_json',
            sa.Text().with_variant(mysql.LONGTEXT(), 'mysql'),
            nullable=True,
        ),
        sa.Column('last_heartbeat', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('jobs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_jobs_user_id'),
                              ['user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_jobs_anon_session_id'),
                              ['anon_session_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_jobs_status'),
                              ['status'], unique=False)


def downgrade():
    with op.batch_alter_table('jobs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_jobs_status'))
        batch_op.drop_index(batch_op.f('ix_jobs_anon_session_id'))
        batch_op.drop_index(batch_op.f('ix_jobs_user_id'))
    op.drop_table('jobs')
