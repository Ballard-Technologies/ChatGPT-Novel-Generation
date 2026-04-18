"""End-to-end tests for the username-based auth flow."""
from models import db
from models.novel import Novel
from models.user import User


def _stub_story_pdf(monkeypatch, tmp_path):
    """Replace StoryPDF.create with a stub that writes an empty file.

    The real implementation writes to a hardcoded ``/tmp/transformed_books``
    directory and depends on fpdf; neither is relevant to what these tests
    are asserting about novel persistence.
    """
    import models.story_pdf as story_pdf_mod

    def _fake_create(self, title, chapters):
        p = tmp_path / 'stub.pdf'
        p.write_bytes(b'%PDF-fake')
        return str(p)

    monkeypatch.setattr(story_pdf_mod.StoryPDF, 'create', _fake_create)


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
    # /api/me is public now: returns 200 with username=None when anonymous.
    resp = client.get('/api/me', follow_redirects=False)
    assert resp.status_code == 200
    assert resp.get_json()['username'] is None


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


def test_novel_gen_works_when_logged_in(client, user_factory):
    """Logged-in users can reach /novel-gen."""
    user_factory(username='dave', password='password123')
    client.post('/login', data={'username': 'dave',
                                 'password': 'password123'})
    resp = client.post('/novel-gen', json={
        'title': 't', 'api_key': 'x', 'bulk_model': 'm',
        'version': 'bogus',
    })
    # Handler returns 400 for missing 'summary'; the point is it's NOT 403/401.
    assert resp.status_code == 400
    assert b'format not specified' in resp.data


def test_novel_gen_works_for_anonymous_users(client):
    """Auth is optional: anonymous visitors can also reach /novel-gen."""
    resp = client.post('/novel-gen', json={
        'title': 't', 'api_key': 'x', 'bulk_model': 'm',
        'version': 'bogus',
    })
    assert resp.status_code == 400
    assert b'format not specified' in resp.data


def test_index_is_public(client):
    resp = client.get('/', follow_redirects=False)
    assert resp.status_code == 200


def test_progress_is_public(client):
    resp = client.get('/progress', follow_redirects=False)
    assert resp.status_code == 200


def test_api_me_returns_null_username_when_anonymous(client):
    resp = client.get('/api/me')
    assert resp.status_code == 200
    assert resp.get_json()['username'] is None


def test_create_pdf_persists_novel_for_logged_in_user(
        client, user_factory, flask_app, monkeypatch, tmp_path):
    user_factory(username='saver', password='password123')
    client.post('/login', data={'username': 'saver',
                                 'password': 'password123'})
    _stub_story_pdf(monkeypatch, tmp_path)

    resp = client.post('/create-pdf',
                       json={'title': 'MyBook', 'chapters': ['Ch1', 'Ch2']})
    assert resp.status_code == 200

    with flask_app.app_context():
        novels = Novel.query.all()
        assert len(novels) == 1
        assert novels[0].title == 'MyBook'
        assert novels[0].chapters == ['Ch1', 'Ch2']


def test_create_pdf_does_not_persist_for_anonymous(
        client, flask_app, monkeypatch, tmp_path):
    _stub_story_pdf(monkeypatch, tmp_path)

    resp = client.post('/create-pdf',
                       json={'title': 'MyBook', 'chapters': ['Ch1']})
    assert resp.status_code == 200

    with flask_app.app_context():
        assert Novel.query.count() == 0


def test_my_novels_list_requires_login(client):
    resp = client.get('/api/my-novels', follow_redirects=False)
    assert resp.status_code in (302, 401)


def test_my_novels_list_returns_only_own_novels(flask_app, user_factory):
    uid1 = user_factory(username='alice2', password='password123')
    uid2 = user_factory(username='bob2', password='password123')
    with flask_app.app_context():
        db.session.add(Novel(user_id=uid1, title='A1',
                              chapters_json='["x"]'))
        db.session.add(Novel(user_id=uid2, title='B1',
                              chapters_json='["y"]'))
        db.session.add(Novel(user_id=uid1, title='A2',
                              chapters_json='["z"]'))
        db.session.commit()

    c = flask_app.test_client()
    c.post('/login', data={'username': 'alice2',
                            'password': 'password123'})
    body = c.get('/api/my-novels').get_json()
    assert {n['title'] for n in body} == {'A1', 'A2'}


def test_my_novels_pdf_requires_login(client):
    resp = client.get('/api/my-novels/1/pdf', follow_redirects=False)
    assert resp.status_code in (302, 401)


def test_my_novels_pdf_404_for_other_users_novel(
        flask_app, user_factory, monkeypatch, tmp_path):
    uid_owner = user_factory(username='owner2', password='password123')
    user_factory(username='thief', password='password123')
    with flask_app.app_context():
        n = Novel(user_id=uid_owner, title='Mine',
                  chapters_json='["secret"]')
        db.session.add(n)
        db.session.commit()
        nid = n.id

    _stub_story_pdf(monkeypatch, tmp_path)
    c = flask_app.test_client()
    c.post('/login', data={'username': 'thief',
                            'password': 'password123'})
    resp = c.get(f'/api/my-novels/{nid}/pdf')
    assert resp.status_code == 404


def test_my_novels_pdf_works_for_owner(
        flask_app, user_factory, monkeypatch, tmp_path):
    uid = user_factory(username='owner3', password='password123')
    with flask_app.app_context():
        n = Novel(user_id=uid, title='Mine', chapters_json='["hello"]')
        db.session.add(n)
        db.session.commit()
        nid = n.id

    _stub_story_pdf(monkeypatch, tmp_path)
    c = flask_app.test_client()
    c.post('/login', data={'username': 'owner3',
                            'password': 'password123'})
    resp = c.get(f'/api/my-novels/{nid}/pdf')
    assert resp.status_code == 200
