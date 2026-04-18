"""End-to-end tests for the username-based auth flow."""
from models.user import User


def test_signup_creates_user_and_logs_in(client, flask_app):
    resp = client.post('/signup', data={
        'username': 'newuser',
        'password': 'password123',
        'confirm_password': 'password123',
    }, follow_redirects=False)
    assert resp.status_code == 302

    with flask_app.app_context():
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.check_password('password123')


def test_signup_rejects_short_password(client):
    resp = client.post('/signup', data={
        'username': 'shortpw',
        'password': 'abc',
        'confirm_password': 'abc',
    })
    assert resp.status_code == 400


def test_signup_rejects_mismatched_password(client):
    resp = client.post('/signup', data={
        'username': 'mmuser',
        'password': 'password123',
        'confirm_password': 'different456',
    })
    assert resp.status_code == 400


def test_signup_rejects_too_short_username(client):
    resp = client.post('/signup', data={
        'username': 'ab',
        'password': 'password123',
        'confirm_password': 'password123',
    })
    assert resp.status_code == 400


def test_signup_rejects_invalid_chars_in_username(client):
    resp = client.post('/signup', data={
        'username': 'bad user!',
        'password': 'password123',
        'confirm_password': 'password123',
    })
    assert resp.status_code == 400


def test_signup_rejects_username_starting_with_digit(client):
    resp = client.post('/signup', data={
        'username': '1user',
        'password': 'password123',
        'confirm_password': 'password123',
    })
    assert resp.status_code == 400


def test_signup_rejects_duplicate_username(client, user_factory):
    user_factory(username='duplicate', password='password123')
    resp = client.post('/signup', data={
        'username': 'duplicate',
        'password': 'password123',
        'confirm_password': 'password123',
    })
    assert resp.status_code == 400


def test_signup_duplicate_is_case_insensitive(client, user_factory):
    user_factory(username='mixedcase', password='password123')
    resp = client.post('/signup', data={
        'username': 'MixedCase',
        'password': 'password123',
        'confirm_password': 'password123',
    })
    assert resp.status_code == 400


def test_login_success_and_logout(client, user_factory):
    user_factory(username='alice', password='password123')
    resp = client.post('/login', data={
        'username': 'alice',
        'password': 'password123',
    })
    assert resp.status_code == 302

    resp = client.get('/api/me')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['username'] == 'alice'
    assert 'email' not in body
    assert 'email_verified' not in body

    resp = client.get('/logout')
    assert resp.status_code == 302
    resp = client.get('/api/me', follow_redirects=False)
    assert resp.status_code in (302, 401)


def test_login_wrong_password(client, user_factory):
    user_factory(username='bob', password='password123')
    resp = client.post('/login', data={
        'username': 'bob',
        'password': 'WRONG',
    })
    assert resp.status_code == 401


def test_login_unknown_username(client):
    resp = client.post('/login', data={
        'username': 'nobody',
        'password': 'password123',
    })
    assert resp.status_code == 401


def test_username_login_is_case_insensitive(client, user_factory):
    user_factory(username='carol', password='password123')
    resp = client.post('/login', data={
        'username': '  CAROL  ',
        'password': 'password123',
    })
    assert resp.status_code == 302


def test_removed_routes_no_longer_exist(client):
    for path in ['/verify', '/verify-notice', '/resend-verification',
                 '/forgot-password', '/reset-password/sometoken']:
        resp = client.get(path)
        assert resp.status_code == 404, path


def test_novel_gen_requires_only_login(client, user_factory):
    """Previously required email verification; now just login is enough."""
    user_factory(username='dave', password='password123')
    client.post('/login', data={'username': 'dave',
                                 'password': 'password123'})
    resp = client.post('/novel-gen', json={
        'title': 't', 'api_key': 'x', 'bulk_model': 'm',
        'version': 'bogus',
    })
    # Handler returns 400 for missing 'summary'; the point is it's NOT 403.
    assert resp.status_code == 400
    assert b'format not specified' in resp.data
