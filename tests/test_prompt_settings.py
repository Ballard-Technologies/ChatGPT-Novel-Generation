"""Tests for per-user prompt-settings persistence and override plumbing."""
import json

from models import db
from models.user import User
from utilities import prompt_templates as pt


def _login(client, username='tester', password='password123'):
    return client.post('/login', data={
        'username': username,
        'password': password,
    }, follow_redirects=False)


def test_api_prompt_settings_get_anonymous_returns_defaults_and_empty(client):
    resp = client.get('/api/prompt-settings')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['logged_in'] is False
    assert body['settings'] == {}
    # Defaults include the v2 summary template keyed by name.
    assert 'summary_template_v0030' in body['defaults']
    assert body['defaults']['summary_template_v0030']['create_summary'] \
        == pt.summary_template_v0030['create_summary']


def test_api_prompt_settings_get_logged_in_returns_saved_overrides(
        client, user_factory, flask_app):
    user_factory(username='tester', password='password123')
    _login(client)

    # Seed an override directly on the user row.
    with flask_app.app_context():
        user = User.query.filter_by(username='tester').first()
        user.set_prompt_settings({
            'summary_template_v0030': {'create_summary': 'HELLO {title}'},
        })
        db.session.commit()

    resp = client.get('/api/prompt-settings')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['logged_in'] is True
    assert body['settings']['summary_template_v0030']['create_summary'] \
        == 'HELLO {title}'


def test_api_prompt_settings_save_requires_login(client):
    resp = client.post('/api/prompt-settings',
                       json={'settings': {}},
                       follow_redirects=False)
    assert resp.status_code in (302, 401)


def test_api_prompt_settings_save_persists_only_whitelisted_keys(
        client, user_factory, flask_app):
    user_factory(username='tester', password='password123')
    _login(client)

    resp = client.post('/api/prompt-settings', json={'settings': {
        'summary_template_v0030': {
            'create_summary': 'CUSTOM {title} {user_summary}',
            'not_a_real_key': 'nope',
        },
        'bogus_template_name': {'x': 'y'},
    }})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['ok'] is True
    assert body['settings'] == {
        'summary_template_v0030': {
            'create_summary': 'CUSTOM {title} {user_summary}',
        }
    }

    with flask_app.app_context():
        user = User.query.filter_by(username='tester').first()
        assert user.get_prompt_settings() == {
            'summary_template_v0030': {
                'create_summary': 'CUSTOM {title} {user_summary}',
            }
        }


def test_api_prompt_settings_save_drops_values_matching_default(
        client, user_factory, flask_app):
    user_factory(username='tester', password='password123')
    _login(client)

    default = pt.summary_template_v0030['create_summary']
    resp = client.post('/api/prompt-settings', json={'settings': {
        'summary_template_v0030': {'create_summary': default},
    }})
    assert resp.status_code == 200
    assert resp.get_json()['settings'] == {}
    with flask_app.app_context():
        user = User.query.filter_by(username='tester').first()
        assert user.prompt_settings_json is None


def test_api_prompt_settings_reset_clears_overrides(
        client, user_factory, flask_app):
    user_factory(username='tester', password='password123')
    _login(client)
    with flask_app.app_context():
        user = User.query.filter_by(username='tester').first()
        user.set_prompt_settings({
            'summary_template_v0030': {'create_summary': 'X'},
        })
        db.session.commit()

    resp = client.post('/api/prompt-settings/reset')
    assert resp.status_code == 200
    with flask_app.app_context():
        user = User.query.filter_by(username='tester').first()
        assert user.prompt_settings_json is None


def test_settings_page_redirects_anonymous_to_login(client):
    resp = client.get('/settings', follow_redirects=False)
    assert resp.status_code == 302
    assert '/login' in resp.headers['Location']


def test_settings_page_renders_for_logged_in_user(client, user_factory):
    user_factory(username='tester', password='password123')
    _login(client)
    resp = client.get('/settings')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'summary_template_v0030' in html
    assert 'create_summary' in html


def test_resolve_template_applies_override_for_dict(user_factory, flask_app):
    overrides = {
        'summary_template_v0030': {'create_summary': 'OVERRIDE {title}'},
    }
    merged = pt.resolve_template('summary_template_v0030', overrides)
    assert merged['create_summary'] == 'OVERRIDE {title}'
    # Untouched keys still present with default text.
    assert merged['create_chapters'] \
        == pt.summary_template_v0030['create_chapters']


def test_resolve_template_applies_override_for_list(user_factory):
    overrides = {
        'outline_template_v0010': {'0': 'NEW INTRO {title} {prompt}'},
    }
    merged = pt.resolve_template('outline_template_v0010', overrides)
    assert merged[0] == 'NEW INTRO {title} {prompt}'
    assert merged[1] == pt.outline_template_v0010[1]
