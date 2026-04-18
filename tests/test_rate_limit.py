"""Tests for Flask-Limiter integration on sensitive endpoints."""


def test_login_is_rate_limited(client):
    # Limit on /login is 10 per minute. The 11th call should be rejected
    # with 429 Too Many Requests.
    last_status = None
    for _ in range(11):
        resp = client.post('/login', data={
            'username': 'nobody',
            'password': 'wrong-password',
        })
        last_status = resp.status_code
    assert last_status == 429


def test_signup_is_rate_limited(client):
    # /signup is 5 per minute; 6th attempt should be blocked.
    last_status = None
    for i in range(6):
        resp = client.post('/signup', data={
            'username': f'user{i}',
            'password': 'password123',
            'confirm_password': 'password123',
        })
        last_status = resp.status_code
    assert last_status == 429


def test_novel_gen_is_rate_limited_per_user(client, user_factory):
    user_factory(username='ratelimit', password='password123')
    client.post('/login', data={'username': 'ratelimit',
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
