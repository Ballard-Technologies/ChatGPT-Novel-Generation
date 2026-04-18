import json
from datetime import datetime

from sqlalchemy.dialects.mysql import LONGTEXT

from models import db

TITLE_MAX_LENGTH = 255


class Novel(db.Model):
    __tablename__ = 'novels'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False, index=True,
    )
    title = db.Column(db.String(TITLE_MAX_LENGTH), nullable=False)
    # Chapters are stored as a JSON-encoded list of strings. MariaDB's default
    # TEXT column tops out at 64 KiB which is not enough for a full novel, so
    # prefer LONGTEXT on MySQL/MariaDB; SQLite's TEXT is already unbounded.
    chapters_json = db.Column(
        db.Text().with_variant(LONGTEXT, 'mysql'),
        nullable=False,
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship(
        'User',
        backref=db.backref('novels', lazy='dynamic',
                            cascade='all, delete-orphan',
                            order_by='Novel.created_at.desc()'),
    )

    @property
    def chapters(self):
        return json.loads(self.chapters_json)

    @chapters.setter
    def chapters(self, value):
        self.chapters_json = json.dumps(value)
