"""Tests that CSRF protection is enabled on HTML form POSTs and that JSON
API endpoints are explicitly exempted."""
import re


CSRF_INPUT = re.compile(
    r'name="csrf_token"\s+value="([^"]+)"'
)


def _extract_csrf_token(html):
    match = CSRF_INPUT.search(html)
    assert match, 'csrf_token input not found in rendered form'
    return match.group(1)


def test_signup_post_without_csrf_is_rejected(csrf_client):
    resp = csrf_client.post('/signup', data={
        'username': 'csrfuser',
        'password': 'password123',
        'confirm_password': 'password123',
    })
    assert resp.status_code == 400


def test_login_post_without_csrf_is_rejected(csrf_client):
    resp = csrf_client.post('/login', data={
        'username': 'csrfuser',
        'password': 'password123',
    })
    assert resp.status_code == 400


def test_signup_get_renders_csrf_token(csrf_client):
    resp = csrf_client.get('/signup')
    assert resp.status_code == 200
    _extract_csrf_token(resp.get_data(as_text=True))


def test_signup_with_csrf_token_succeeds(csrf_client, flask_app):
    resp = csrf_client.get('/signup')
    token = _extract_csrf_token(resp.get_data(as_text=True))
    resp = csrf_client.post('/signup', data={
        'csrf_token': token,
        'username': 'csrfok',
        'password': 'password123',
        'confirm_password': 'password123',
    })
    assert resp.status_code == 302


def test_novel_gen_json_endpoint_is_csrf_exempt(csrf_client, user_factory):
    """scripts.js posts JSON without a CSRF token; the route exempts itself."""
    user_factory(username='jsonuser', password='password123')
    # Log in using CSRF-protected form by pulling its token.
    resp = csrf_client.get('/login')
    import re as _re
    token = _re.search(r'name="csrf_token"\s+value="([^"]+)"',
                        resp.get_data(as_text=True)).group(1)
    csrf_client.post('/login', data={
        'csrf_token': token,
        'username': 'jsonuser',
        'password': 'password123',
    })

    # The authenticated JSON call should NOT be rejected by CSRF (it may still
    # fail validation inside the handler; we only assert it isn't 400-from-CSRF).
    resp = csrf_client.post('/novel-gen', json={
        'title': 't', 'api_key': 'x', 'bulk_model': 'gpt-4o-mini',
        'version': 'bogus',
    })
    # Without a 'summary' field the route returns 400 with a specific message,
    # which is fine -- the key point is CSRF did not block the request.
    assert resp.status_code in (200, 400)
    if resp.status_code == 400:
        assert b'format not specified' in resp.data
