"""Regression tests: progress state must be isolated per user."""
from controllers import routes


def test_progress_dicts_are_keyed_per_user():
    routes._progress_by_user.clear()
    a = routes._reset_progress_dict(1)
    b = routes._reset_progress_dict(2)
    assert a is not b

    a['current'] = 42
    b['current'] = 7

    assert routes._get_progress_dict(1)['current'] == 42
    assert routes._get_progress_dict(2)['current'] == 7


def test_reset_progress_clears_previous_run():
    routes._progress_by_user.clear()
    d = routes._reset_progress_dict(99)
    d['current'] = 50
    d['text'] = 'stale output'
    d['fail'] = True
    d['fail_message'] = 'boom'

    d2 = routes._reset_progress_dict(99)
    assert d2 is d  # same dict object, cleared in place
    assert 'current' not in d2
    assert 'text' not in d2
    assert d2['fail'] is False
    assert d2['fail_message'] == ''
    assert d2['complete'] is False


def test_progress_endpoint_does_not_leak_full_text(client, user_factory, flask_app):
    user_factory(username='progressp', password='password123')
    client.post('/login', data={'username': 'progressp',
                                 'password': 'password123'})

    from models.user import User
    with flask_app.app_context():
        user = User.query.filter_by(username='progressp').first()
        routes._reset_progress_dict(user.id)['text'] = 'SECRET NOVEL TEXT'

    resp = client.get('/progress')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body.get('text') == ''
    assert b'SECRET NOVEL TEXT' not in resp.data


def test_two_users_have_independent_progress(flask_app, user_factory):
    user_factory(username='progressu1', password='password123')
    user_factory(username='progressu2', password='password123')

    c1 = flask_app.test_client()
    c2 = flask_app.test_client()
    c1.post('/login', data={'username': 'progressu1',
                             'password': 'password123'})
    c2.post('/login', data={'username': 'progressu2',
                             'password': 'password123'})

    from models.user import User
    with flask_app.app_context():
        u1_id = User.query.filter_by(username='progressu1').first().id
        u2_id = User.query.filter_by(username='progressu2').first().id

    routes._reset_progress_dict(u1_id)['current'] = 1
    routes._reset_progress_dict(u2_id)['current'] = 999

    r1 = c1.get('/progress').get_json()
    r2 = c2.get('/progress').get_json()
    assert r1['current'] == 1
    assert r2['current'] == 999
