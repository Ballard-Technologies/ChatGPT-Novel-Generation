import logging

from flask import (Blueprint, flash, redirect, render_template, request,
                   url_for)
from flask_login import (current_user, login_required, login_user,
                          logout_user)

from models import db
from models.user import User

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

MIN_PASSWORD_LENGTH = 8


def register_rate_limits(app, limiter):
    """Attach per-endpoint rate limits to the auth blueprint's views.

    The Flask-Limiter decorator returns a wrapper function; we also replace
    the entry in ``app.view_functions`` so Flask dispatches through it.
    """
    limits = {
        'auth.login': '10 per minute; 100 per hour',
        'auth.signup': '5 per minute; 20 per hour',
    }
    for endpoint, limit in limits.items():
        func = app.view_functions[endpoint]
        app.view_functions[endpoint] = limiter.limit(limit)(func)


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        raw_username = request.form.get('username', '')
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        username = User.normalize_username(raw_username)
        error = User.validate_username(username)
        if error:
            flash(error, 'error')
            return render_template('auth/signup.html',
                                    username=raw_username), 400

        if len(password) < MIN_PASSWORD_LENGTH:
            flash(f'Password must be at least {MIN_PASSWORD_LENGTH} characters.',
                   'error')
            return render_template('auth/signup.html', username=username), 400
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('auth/signup.html', username=username), 400

        existing = User.query.filter_by(username=username).first()
        if existing:
            flash('That username is already taken.', 'error')
            return render_template('auth/signup.html', username=username), 400

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        return redirect(url_for('index'))

    return render_template('auth/signup.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = User.normalize_username(request.form.get('username', ''))
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash('Invalid username or password.', 'error')
            return render_template('auth/login.html', username=username), 401

        login_user(user, remember=bool(request.form.get('remember')))
        next_url = request.args.get('next') or url_for('index')
        return redirect(next_url)

    return render_template('auth/login.html')


@auth_bp.route('/logout', methods=['POST', 'GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
