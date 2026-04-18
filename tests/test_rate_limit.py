"""Tests for Flask-Limiter integration on sensitive endpoints."""


def test_login_is_rate_limited(client):
    # Limit on /login is 10 per minute. The 11th call should be rejected
    # with 429 Too Many Requests.
    last_status = None
    for _ in range(11):
        resp = client.post('/login', data={
            'email': 'nobody@example.com',
            'password': 'wrong-password',
        })
        last_status = resp.status_code
    assert last_status == 429


def test_signup_is_rate_limited(client):
    # /signup is 5 per minute; 6th attempt should be blocked.
    last_status = None
    for i in range(6):
        resp = client.post('/signup', data={
            'email': f'user{i}@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
        })
        last_status = resp.status_code
    assert last_status == 429


def test_forgot_password_is_rate_limited(client):
    last_status = None
    for i in range(6):
        resp = client.post('/forgot-password',
                            data={'email': f'x{i}@example.com'})
        last_status = resp.status_code
    assert last_status == 429


def test_resend_verification_is_rate_limited(client, user_factory):
    user_factory(email='rv@example.com', password='password123',
                  verified=False)
    client.post('/login', data={'email': 'rv@example.com',
                                 'password': 'password123'})
    last_status = None
    for _ in range(4):
        resp = client.post('/resend-verification')
        last_status = resp.status_code
    assert last_status == 429


def test_novel_gen_is_rate_limited_per_user(client, user_factory):
    user_factory(email='n@example.com', password='password123', verified=True)
    client.post('/login', data={'email': 'n@example.com',
                                 'password': 'password123'})
    # /novel-gen is 10 per hour per authenticated user.
    last_status = None
    for _ in range(11):
        resp = client.post('/novel-gen', json={
            'title': 't', 'api_key': 'x', 'bulk_model': 'gpt-4o-mini',
            'version': 'bogus',  # skips downstream work; returns 400 quickly
        })
        last_status = resp.status_code
    assert last_status == 429
