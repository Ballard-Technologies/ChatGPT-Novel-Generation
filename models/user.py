import re
from datetime import datetime

from flask_login import UserMixin
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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
