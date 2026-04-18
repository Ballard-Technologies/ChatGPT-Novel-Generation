import logging
import os
from functools import wraps

from email_validator import EmailNotValidError, validate_email
from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, url_for)
from flask_login import (current_user, login_required, login_user, logout_user)

from models import db
from models.user import User
from utilities.email import MailgunError, send_email
from utilities.tokens import (generate_reset_token, generate_verify_token,
                              load_reset_token, load_verify_token)

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
        'auth.forgot_password': '5 per minute; 20 per hour',
        'auth.reset_password': '5 per minute; 20 per hour',
        'auth.resend_verification': '3 per minute; 10 per hour',
    }
    for endpoint, limit in limits.items():
        func = app.view_functions[endpoint]
        app.view_functions[endpoint] = limiter.limit(limit)(func)


def _auto_verify_in_dev():
    return os.environ.get('ENV') != 'production'


def verified_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.email_verified:
            if request.accept_mimetypes.best == 'application/json' or request.is_json:
                return jsonify({'error': 'email_not_verified'}), 403
            return redirect(url_for('auth.verify_notice'))
        return view(*args, **kwargs)
    return wrapped


def _send_verification_email(user):
    token = generate_verify_token(user.email)
    verify_url = url_for('auth.verify', token=token, _external=True)
    send_email(
        to=user.email,
        subject='Confirm your email',
        text=(
            f'Welcome to ChatGPT Novel Generation.\n\n'
            f'Confirm your email by opening this link:\n{verify_url}\n\n'
            f'This link expires in 24 hours.'
        ),
    )


def _send_reset_email(user):
    token = generate_reset_token(user.email)
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    send_email(
        to=user.email,
        subject='Reset your password',
        text=(
            f'A password reset was requested for your account.\n\n'
            f'Reset your password by opening this link:\n{reset_url}\n\n'
            f'This link expires in 1 hour. If you did not request this, ignore this email.'
        ),
    )


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        raw_email = request.form.get('email', '')
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        try:
            email = validate_email(raw_email, check_deliverability=False).normalized.lower()
        except EmailNotValidError as exc:
            flash(f'Invalid email: {exc}', 'error')
            return render_template('auth/signup.html', email=raw_email), 400

        if len(password) < MIN_PASSWORD_LENGTH:
            flash(f'Password must be at least {MIN_PASSWORD_LENGTH} characters.', 'error')
            return render_template('auth/signup.html', email=email), 400
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('auth/signup.html', email=email), 400

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('An account with that email already exists. Try logging in.', 'error')
            return render_template('auth/signup.html', email=email), 400

        user = User(email=email)
        user.set_password(password)
        if _auto_verify_in_dev():
            user.email_verified = True
        db.session.add(user)
        db.session.commit()

        if _auto_verify_in_dev():
            logger.info('[dev] Auto-verified %s (ENV!=production)', user.email)
        else:
            try:
                _send_verification_email(user)
            except MailgunError:
                logger.exception('Failed to send verification email on signup')
                flash('Your account was created, but we could not send the verification email. '
                      'Please try resending it.', 'error')

        login_user(user)
        if user.email_verified:
            return redirect(url_for('index'))
        return redirect(url_for('auth.verify_notice'))

    return render_template('auth/signup.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = User.normalize_email(request.form.get('email', ''))
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash('Invalid email or password.', 'error')
            return render_template('auth/login.html', email=email), 401

        login_user(user, remember=bool(request.form.get('remember')))
        next_url = request.args.get('next') or url_for('index')
        return redirect(next_url)

    return render_template('auth/login.html')


@auth_bp.route('/logout', methods=['POST', 'GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/verify-notice')
@login_required
def verify_notice():
    if current_user.email_verified:
        return redirect(url_for('index'))
    return render_template('auth/verify_notice.html', email=current_user.email)


@auth_bp.route('/verify')
def verify():
    token = request.args.get('token', '')
    email = load_verify_token(token)
    if not email:
        return render_template('auth/verified.html', ok=False), 400

    user = User.query.filter_by(email=User.normalize_email(email)).first()
    if not user:
        return render_template('auth/verified.html', ok=False), 400

    if not user.email_verified:
        user.email_verified = True
        db.session.commit()

    return render_template('auth/verified.html', ok=True)


@auth_bp.route('/resend-verification', methods=['POST'])
@login_required
def resend_verification():
    if current_user.email_verified:
        return redirect(url_for('index'))
    try:
        _send_verification_email(current_user)
        flash('Verification email sent. Check your inbox.', 'info')
    except MailgunError:
        logger.exception('Failed to resend verification email')
        flash('Could not send verification email. Try again later.', 'error')
    return redirect(url_for('auth.verify_notice'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = User.normalize_email(request.form.get('email', ''))
        user = User.query.filter_by(email=email).first()
        if user:
            try:
                _send_reset_email(user)
            except MailgunError:
                logger.exception('Failed to send password reset email')
        # Always show the same message to avoid leaking which emails exist.
        flash('If an account exists for that email, a reset link has been sent.', 'info')
        return render_template('auth/forgot_password.html')

    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = load_reset_token(token)
    if not email:
        flash('This reset link is invalid or has expired.', 'error')
        return render_template('auth/reset_password.html', token=None), 400

    user = User.query.filter_by(email=User.normalize_email(email)).first()
    if not user:
        flash('This reset link is invalid or has expired.', 'error')
        return render_template('auth/reset_password.html', token=None), 400

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if len(password) < MIN_PASSWORD_LENGTH:
            flash(f'Password must be at least {MIN_PASSWORD_LENGTH} characters.', 'error')
            return render_template('auth/reset_password.html', token=token), 400
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('auth/reset_password.html', token=token), 400

        user.set_password(password)
        db.session.commit()
        flash('Your password has been reset. You can now log in.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)
