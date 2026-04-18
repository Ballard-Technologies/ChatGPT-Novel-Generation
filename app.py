from flask import Flask
import os

# Load variables from a local .env file when not running in production
if os.environ.get('ENV') != 'production':
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from controllers.auth import auth_bp
from controllers.routes import configure_routes
from models import db
from models.user import User
from models.novel import Novel  # noqa: F401  (registers the table with SQLAlchemy)

IS_PRODUCTION = os.environ.get('ENV') == 'production'

app = Flask(__name__, static_folder='.', static_url_path='')

# Secret key is required for sessions and signed tokens.
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    if IS_PRODUCTION:
        raise RuntimeError('SECRET_KEY environment variable must be set in production.')
    secret_key = 'dev-secret-key-change-me'
app.config['SECRET_KEY'] = secret_key

#  Database URL resolution:
#   1. JAWSDB_MARIA_URL  - set by the Heroku JawsDB Maria add-on.
#   2. DATABASE_URL      - generic override for local dev or other hosts.
#   3. sqlite:///local.db - local fallback.
# JawsDB exposes a mysql:// URL; SQLAlchemy needs an explicit driver, so we
# rewrite it to mysql+pymysql://.
database_url = (
    os.environ.get('JAWSDB_MARIA_URL')
    or os.environ.get('DATABASE_URL')
    or 'sqlite:///local.db'
)
if database_url.startswith('mysql://'):
    database_url = database_url.replace('mysql://', 'mysql+pymysql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# MariaDB/MySQL closes idle connections server-side; pool_pre_ping validates
# each checked-out connection so we don't hand a dead one to a request.
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 280,
}

# Determine if the environment is production or development
if IS_PRODUCTION:
    app.config['TESTING'] = False
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['REMEMBER_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
else:
    app.config['TESTING'] = True

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

# CSRF protection for HTML form POSTs. JSON API endpoints used by scripts.js
# (/novel-gen, /create-pdf) are exempted inside controllers/routes.py; those
# endpoints require an authenticated session plus user-supplied data an
# attacker cannot forge, so CSRF exposure there is negligible.
csrf = CSRFProtect(app)

# Rate limiting. In production, set RATELIMIT_STORAGE_URI (e.g. to a Heroku
# Redis URL) so limits are shared across dynos. Without it Flask-Limiter uses
# in-memory storage which is per-process only.
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=['200 per hour'],
    storage_uri=os.environ.get('RATELIMIT_STORAGE_URI', 'memory://'),
    headers_enabled=True,
)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


app.register_blueprint(auth_bp)
configure_routes(app, csrf=csrf, limiter=limiter)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)