import json
import uuid
from datetime import datetime

from sqlalchemy.dialects.mysql import LONGTEXT

from models import db

# Job lifecycle states. ``queued`` is the initial state written by the web
# worker when the job is created; the RQ worker (or the synchronous dev
# fallback) flips it to ``running`` once it picks the job up and then to
# ``complete``/``failed``. ``cancelled`` is set by the cancel endpoint or by
# the anonymous heartbeat timeout; cooperative cancel in StoryCreator bails
# out on the next should_cancel() check.
STATUS_QUEUED = 'queued'
STATUS_RUNNING = 'running'
STATUS_COMPLETE = 'complete'
STATUS_FAILED = 'failed'
STATUS_CANCELLED = 'cancelled'

TERMINAL_STATUSES = (STATUS_COMPLETE, STATUS_FAILED, STATUS_CANCELLED)
ACTIVE_STATUSES = (STATUS_QUEUED, STATUS_RUNNING)

# Anonymous jobs are cancelled when their owning browser stops polling. The
# client polls every 10s; 30s gives two missed polls of slack before we stop
# spending OpenAI credits on a tab that's already gone.
ANON_HEARTBEAT_TIMEOUT_SECONDS = 30


class Job(db.Model):
    __tablename__ = 'jobs'

    # UUID primary key exposed in URLs so an integer row id can't be guessed
    # or enumerated. Stored as a 32-char hex string for portability between
    # SQLite (no native UUID type) and MariaDB.
    id = db.Column(db.String(32), primary_key=True,
                   default=lambda: uuid.uuid4().hex)
    # Exactly one of user_id / anon_session_id is populated. Logged-in jobs
    # survive tab close; anonymous jobs are cancelled on disconnect.
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=True, index=True,
    )
    anon_session_id = db.Column(db.String(64), nullable=True, index=True)

    status = db.Column(db.String(16), nullable=False, default=STATUS_QUEUED,
                       index=True)
    # Input parameters captured so the worker (running in a separate process)
    # has everything it needs without re-reading the HTTP request.
    version = db.Column(db.String(8), nullable=False)
    model = db.Column(db.String(64), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    summary = db.Column(db.Text().with_variant(LONGTEXT, 'mysql'),
                        nullable=False, default='')
    # OpenAI API key for this run. Not encrypted at rest today; see the
    # follow-up "encrypted api_key column" task.
    api_key = db.Column(db.Text, nullable=False)
    prompt_overrides_json = db.Column(
        db.Text().with_variant(LONGTEXT, 'mysql'), nullable=True,
    )

    # Progress counters mirrored from Redis for durability. Redis is the
    # authoritative source for in-flight updates (hot path); the DB copy is
    # refreshed at terminal transitions so the row is meaningful on its own.
    current = db.Column(db.Integer, nullable=False, default=0)
    total = db.Column(db.Integer, nullable=False, default=0)
    fail_message = db.Column(db.Text, nullable=True)

    # Populated when status transitions to ``complete``.
    chapters_json = db.Column(
        db.Text().with_variant(LONGTEXT, 'mysql'), nullable=True,
    )

    # Only set for anonymous jobs. GET /api/jobs/<id> refreshes this on every
    # poll; the worker reads it to detect abandoned tabs.
    last_heartbeat = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship(
        'User',
        backref=db.backref('jobs', lazy='dynamic',
                           cascade='all, delete-orphan',
                           order_by='Job.created_at.desc()'),
    )

    @property
    def chapters(self):
        if not self.chapters_json:
            return []
        return json.loads(self.chapters_json)

    @chapters.setter
    def chapters(self, value):
        self.chapters_json = json.dumps(value) if value is not None else None

    @property
    def prompt_overrides(self):
        if not self.prompt_overrides_json:
            return {}
        try:
            data = json.loads(self.prompt_overrides_json)
        except (TypeError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    @prompt_overrides.setter
    def prompt_overrides(self, value):
        self.prompt_overrides_json = (json.dumps(value)
                                      if value else None)

    def is_anonymous(self):
        return self.user_id is None

    def is_active(self):
        return self.status in ACTIVE_STATUSES

    def is_terminal(self):
        return self.status in TERMINAL_STATUSES

    def is_owned_by(self, user, anon_session_id):
        """Return True if the given requester identity owns this job."""
        if self.user_id is not None:
            return user is not None and user.is_authenticated \
                and user.id == self.user_id
        return (self.anon_session_id is not None
                and anon_session_id is not None
                and self.anon_session_id == anon_session_id)
