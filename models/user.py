import json
import re
from datetime import datetime

from flask_login import UserMixin
from sqlalchemy.dialects.mysql import LONGTEXT
from werkzeug.security import check_password_hash, generate_password_hash

from models import db

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 32
USERNAME_PATTERN = re.compile(r'^[A-Za-z][A-Za-z0-9_\-]*$')


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(USERNAME_MAX_LENGTH), unique=True,
                          nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # User-customised prompt overrides. Stored as a JSON object keyed by
    # template name (e.g. ``summary_template_v0030``) mapping to either a
    # list of strings or a dict of strings, matching the shape of the
    # defaults in utilities/prompt_templates.py. ``NULL`` means "use the
    # defaults for every template".
    prompt_settings_json = db.Column(
        db.Text().with_variant(LONGTEXT, 'mysql'),
        nullable=True,
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_prompt_settings(self):
        """Return the saved prompt-override dict, or ``{}`` if none."""
        if not self.prompt_settings_json:
            return {}
        try:
            data = json.loads(self.prompt_settings_json)
        except (TypeError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def set_prompt_settings(self, data):
        """Persist a prompt-override dict, or ``None`` to clear."""
        if data is None:
            self.prompt_settings_json = None
            return
        self.prompt_settings_json = json.dumps(data)

    @staticmethod
    def normalize_username(username):
        return (username or '').strip().lower()

    @staticmethod
    def validate_username(username):
        """Return None if the username is valid, else an error message."""
        if not username:
            return 'Username is required.'
        if len(username) < USERNAME_MIN_LENGTH:
            return f'Username must be at least {USERNAME_MIN_LENGTH} characters.'
        if len(username) > USERNAME_MAX_LENGTH:
            return f'Username must be at most {USERNAME_MAX_LENGTH} characters.'
        if not USERNAME_PATTERN.match(username):
            return ('Username must start with a letter and contain only '
                    'letters, digits, underscores, and hyphens.')
        return None
