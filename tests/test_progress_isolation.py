"""Regression tests: job state must be isolated per requester."""
from datetime import datetime, timedelta

from models import db
from models.job import (ANON_HEARTBEAT_TIMEOUT_SECONDS, Job, STATUS_CANCELLED,
                        STATUS_QUEUED, STATUS_RUNNING)


def _seed_job(flask_app, **fields):
    with flask_app.app_context():
        defaults = dict(status=STATUS_QUEUED, version='v2', model='m',
                        title='t', summary='s', api_key='k')
        defaults.update(fields)
        job = Job(**defaults)
        db.session.add(job)
        db.session.commit()
        return job.id


def test_logged_in_users_cannot_read_each_others_jobs(flask_app, user_factory):
    uid1 = user_factory(username='owner1', password='password123')
    uid2 = user_factory(username='owner2', password='password123')
    job_id = _seed_job(flask_app, user_id=uid1)

    c1 = flask_app.test_client()
    c2 = flask_app.test_client()
    c1.post('/login', data={'username': 'owner1', 'password': 'password123'})
    c2.post('/login', data={'username': 'owner2', 'password': 'password123'})

    assert c1.get(f'/api/jobs/{job_id}').status_code == 200
    # The other user must not even learn the job exists.
    assert c2.get(f'/api/jobs/{job_id}').status_code == 404


def test_anonymous_cannot_read_logged_in_job(flask_app, user_factory):
    uid = user_factory(username='owner3', password='password123')
    job_id = _seed_job(flask_app, user_id=uid)
    anon = flask_app.test_client()
    assert anon.get(f'/api/jobs/{job_id}').status_code == 404


def test_two_anonymous_clients_cannot_see_each_others_jobs(flask_app):
    c1 = flask_app.test_client()
    c2 = flask_app.test_client()
    # Pre-seed c1's session directly so the GET below has an anon_id
    # without relying on validation-passing POST side effects.
    with c1.session_transaction() as s:
        s['anon_id'] = 'anon-c1'

    job_id = _seed_job(flask_app, user_id=None, anon_session_id='anon-c1')

    assert c1.get(f'/api/jobs/{job_id}').status_code == 200
    # c2 has no anon_id at all, so the owner check must reject it.
    assert c2.get(f'/api/jobs/{job_id}').status_code == 404


def test_cancel_endpoint_marks_job_cancelled(flask_app, user_factory):
    uid = user_factory(username='canceller', password='password123')
    job_id = _seed_job(flask_app, user_id=uid, status=STATUS_RUNNING)

    c = flask_app.test_client()
    c.post('/login', data={'username': 'canceller',
                           'password': 'password123'})
    resp = c.post(f'/api/jobs/{job_id}/cancel')
    assert resp.status_code == 200
    assert resp.get_json()['status'] == STATUS_CANCELLED

    with flask_app.app_context():
        assert db.session.get(Job, job_id).status == STATUS_CANCELLED


def test_anon_heartbeat_timeout_triggers_cancellation_on_check(flask_app):
    """check_cancel() cancels anon jobs whose last_heartbeat is stale."""
    from features.progress_store import JobCancelled, JobProgressStore

    stale = datetime.utcnow() - timedelta(
        seconds=ANON_HEARTBEAT_TIMEOUT_SECONDS + 5)
    job_id = _seed_job(flask_app, user_id=None, anon_session_id='anon-stale',
                       status=STATUS_RUNNING, last_heartbeat=stale)

    with flask_app.app_context():
        store = JobProgressStore(job_id)
        try:
            store.check_cancel()
        except JobCancelled:
            pass
        else:
            raise AssertionError('expected JobCancelled to be raised')
        assert db.session.get(Job, job_id).status == STATUS_CANCELLED


def test_pdf_endpoint_requires_completed_job(flask_app, user_factory):
    uid = user_factory(username='pdfuser', password='password123')
    job_id = _seed_job(flask_app, user_id=uid, status=STATUS_RUNNING)

    c = flask_app.test_client()
    c.post('/login', data={'username': 'pdfuser', 'password': 'password123'})
    resp = c.get(f'/api/jobs/{job_id}/pdf')
    assert resp.status_code == 409
    assert resp.get_json()['status'] == STATUS_RUNNING


def test_one_active_job_per_user(flask_app, user_factory):
    uid = user_factory(username='onejob', password='password123')
    _seed_job(flask_app, user_id=uid, status=STATUS_RUNNING)

    c = flask_app.test_client()
    c.post('/login', data={'username': 'onejob', 'password': 'password123'})
    resp = c.post('/api/jobs', json={
        'title': 'another', 'api_key': 'x', 'bulk_model': 'm',
        'version': 'v2', 'summary': 'hello',
    })
    assert resp.status_code == 409
