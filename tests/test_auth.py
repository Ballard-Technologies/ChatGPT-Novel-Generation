"""End-to-end tests for auth flows (signup, login, logout, verify, reset)."""
import pytest

from models import db
from models.user import User
from utilities.tokens import (
    generate_reset_token,
    generate_verify_token,
)


def test_signup_creates_user_and_logs_in(client, flask_app):
    resp = client.post('/signup', data={
        'email': 'new@example.com',
        'password': 'password123',
        'confirm_password': 'password123',
    }, follow_redirects=False)
    assert resp.status_code == 302

    with flask_app.app_context():
        user = User.query.filter_by(email='new@example.com').first()
        assert user is not None
        assert user.email_verified is True  # dev auto-verify
        assert user.check_password('password123')


def test_signup_rejects_short_password(client):
    resp = client.post('/signup', data={
        'email': 'short@example.com',
        'password': 'abc',
        'confirm_password': 'abc',
    })
    assert resp.status_code == 400


def test_signup_rejects_mismatched_password(client):
    resp = client.post('/signup', data={
        'email': 'mm@example.com',
        'password': 'password123',
        'confirm_password': 'different456',
    })
    assert resp.status_code == 400


def test_signup_rejects_invalid_email(client):
    resp = client.post('/signup', data={
        'email': 'not-an-email',
        'password': 'password123',
        'confirm_password': 'password123',
    })
    assert resp.status_code == 400


def test_signup_rejects_duplicate_email(client, user_factory):
    user_factory(email='dup@example.com', password='password123')
    resp = client.post('/signup', data={
        'email': 'dup@example.com',
        'password': 'password123',
        'confirm_password': 'password123',
    })
    assert resp.status_code == 400


def test_login_success_and_logout(client, user_factory):
    user_factory(email='a@example.com', password='password123')
    resp = client.post('/login', data={
        'email': 'a@example.com',
        'password': 'password123',
    })
    assert resp.status_code == 302

    # Authenticated endpoint should be reachable.
    resp = client.get('/api/me')
    assert resp.status_code == 200
    assert resp.get_json()['email'] == 'a@example.com'

    resp = client.get('/logout')
    assert resp.status_code == 302
    resp = client.get('/api/me', follow_redirects=False)
    assert resp.status_code in (302, 401)


def test_login_wrong_password(client, user_factory):
    user_factory(email='wp@example.com', password='password123')
    resp = client.post('/login', data={
        'email': 'wp@example.com',
        'password': 'WRONG',
    })
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post('/login', data={
        'email': 'nobody@example.com',
        'password': 'password123',
    })
    assert resp.status_code == 401


def test_email_normalization_is_case_insensitive(client, user_factory):
    user_factory(email='mixed@example.com', password='password123')
    resp = client.post('/login', data={
        'email': 'MIXED@Example.com ',
        'password': 'password123',
    })
    assert resp.status_code == 302


def test_verify_flow(client, flask_app, user_factory):
    user_factory(email='v@example.com', password='password123', verified=False)
    with flask_app.app_context():
        token = generate_verify_token('v@example.com')
    resp = client.get(f'/verify?token={token}')
    assert resp.status_code == 200
    with flask_app.app_context():
        user = User.query.filter_by(email='v@example.com').first()
        assert user.email_verified is True


def test_verify_bad_token(client):
    resp = client.get('/verify?token=not-a-real-token')
    assert resp.status_code == 400


def test_reset_password_flow(client, flask_app, user_factory):
    user_factory(email='r@example.com', password='old-password')
    with flask_app.app_context():
        token = generate_reset_token('r@example.com')
    resp = client.post(f'/reset-password/{token}', data={
        'password': 'brand-new-pw',
        'confirm_password': 'brand-new-pw',
    })
    assert resp.status_code == 302
    with flask_app.app_context():
        user = User.query.filter_by(email='r@example.com').first()
        assert user.check_password('brand-new-pw')
        assert not user.check_password('old-password')


def test_forgot_password_does_not_leak_user_existence(client, user_factory):
    user_factory(email='leak@example.com')
    resp_known = client.post('/forgot-password',
                              data={'email': 'leak@example.com'})
    resp_unknown = client.post('/forgot-password',
                                data={'email': 'nobody@example.com'})
    assert resp_known.status_code == resp_unknown.status_code == 200


def test_verified_required_blocks_unverified_user(client, user_factory):
    user_factory(email='u@example.com', password='password123', verified=False)
    client.post('/login', data={'email': 'u@example.com',
                                 'password': 'password123'})
    resp = client.post('/novel-gen',
                        json={'title': 't', 'api_key': 'x', 'bulk_model': 'm',
                              'version': 'v2', 'summary': 's'})
    assert resp.status_code == 403
