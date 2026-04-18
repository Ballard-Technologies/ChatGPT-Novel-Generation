from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

VERIFY_SALT = 'email-verify'
RESET_SALT = 'password-reset'


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


def generate_verify_token(email):
    return _serializer().dumps(email, salt=VERIFY_SALT)


def load_verify_token(token, max_age_seconds=60 * 60 * 24):
    try:
        return _serializer().loads(token, salt=VERIFY_SALT, max_age=max_age_seconds)
    except (BadSignature, SignatureExpired):
        return None


def generate_reset_token(email):
    return _serializer().dumps(email, salt=RESET_SALT)


def load_reset_token(token, max_age_seconds=60 * 60):
    try:
        return _serializer().loads(token, salt=RESET_SALT, max_age=max_age_seconds)
    except (BadSignature, SignatureExpired):
        return None
