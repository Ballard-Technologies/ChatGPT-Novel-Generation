"""Progress sink used by StoryCreator.

Two implementations:

* ``JobProgressStore`` - production: hot fields (``current``, ``total``,
  ``status``, ``fail_message``) live in Redis; terminal transitions copy
  the final state into the ``jobs`` table so the DB row stands on its
  own. Requires an active Flask app context for DB writes.
* ``DictProgressStore`` - used by tests to exercise StoryCreator without
  Redis or a database.

Cancellation is cooperative: callers invoke ``check_cancel()`` between
OpenAI requests. When the job's status transitions to ``cancelled``
(either by the cancel endpoint or by the anonymous heartbeat timeout),
``check_cancel()`` raises ``JobCancelled``, which StoryCreator lets
propagate up to the task runner.
"""
from datetime import datetime

from features import job_queue
from models import db
from models.job import (ANON_HEARTBEAT_TIMEOUT_SECONDS, Job, STATUS_CANCELLED,
                        STATUS_COMPLETE, STATUS_FAILED, STATUS_RUNNING)


class JobCancelled(Exception):
    """Raised by check_cancel() when the job has been marked cancelled."""


class JobProgressStore:
    """Progress sink backed by Redis plus a Job row."""

    def __init__(self, job_id):
        self.job_id = job_id

    def start(self, *, total):
        job_queue.progress_set(self.job_id, {
            'status': STATUS_RUNNING,
            'current': 0,
            'total': total,
            'fail_message': '',
        })
        self._update_row(status=STATUS_RUNNING, current=0, total=total,
                         fail_message=None)

    def set_total(self, total):
        job_queue.progress_set(self.job_id, {'total': int(total)})

    def get_total(self):
        val = job_queue.progress_get(self.job_id).get('total', '0')
        return int(val or '0')

    def get_current(self):
        val = job_queue.progress_get(self.job_id).get('current', '0')
        return int(val or '0')

    def set_current(self, value):
        job_queue.progress_set(self.job_id, {'current': int(value)})

    def inc_current(self, n=1, *, cap=None):
        """Atomically bump ``current``; optionally clamp to ``cap``."""
        new_val = job_queue.progress_increment(self.job_id, 'current', n)
        if cap is not None and new_val > cap:
            new_val = cap
            job_queue.progress_set(self.job_id, {'current': new_val})
        return new_val

    def complete(self, *, chapters):
        self._update_row(
            status=STATUS_COMPLETE,
            chapters=list(chapters),
            current=self.get_total(),
            completed_at=datetime.utcnow(),
        )
        job_queue.progress_set(self.job_id, {'status': STATUS_COMPLETE})

    def fail(self, message):
        msg = str(message) if message is not None else ''
        self._update_row(status=STATUS_FAILED, fail_message=msg,
                         completed_at=datetime.utcnow())
        job_queue.progress_set(self.job_id, {
            'status': STATUS_FAILED, 'fail_message': msg,
        })

    def check_cancel(self):
        # Fast path: the cancel endpoint writes Redis first, so an explicit
        # cancel always shows up here without a DB round-trip.
        status = job_queue.progress_get(self.job_id).get('status')
        if status == STATUS_CANCELLED:
            raise JobCancelled()

        # DB lookup for the anonymous heartbeat check (and as a fallback if
        # the Redis hash has expired). Expire first so identity-map caching
        # doesn't serve a stale last_heartbeat.
        db.session.expire_all()
        job = db.session.get(Job, self.job_id)
        if job is None:
            # Row disappeared (cascade from user deletion, cleanup job,
            # etc.) - treat as cancelled so the worker exits cleanly.
            raise JobCancelled()
        if job.status == STATUS_CANCELLED:
            raise JobCancelled()
        if job.is_anonymous() and job.last_heartbeat is not None:
            age = (datetime.utcnow() - job.last_heartbeat).total_seconds()
            if age > ANON_HEARTBEAT_TIMEOUT_SECONDS:
                # Tab closed without firing the cancel beacon. Flip the
                # status so /api/jobs/<id> reports cancelled, then abort.
                job.status = STATUS_CANCELLED
                job.completed_at = datetime.utcnow()
                db.session.commit()
                job_queue.progress_set(self.job_id,
                                       {'status': STATUS_CANCELLED})
                raise JobCancelled()

    def _update_row(self, **fields):
        job = db.session.get(Job, self.job_id)
        if job is None:
            return
        for name, value in fields.items():
            if name == 'chapters':
                job.chapters = value
            else:
                setattr(job, name, value)
        db.session.commit()


class DictProgressStore:
    """In-memory store used by tests. Mirrors the JobProgressStore API."""

    def __init__(self):
        self.state = {'status': STATUS_RUNNING, 'current': 0, 'total': 0,
                      'fail_message': '', 'chapters': None}
        self.cancelled = False

    def start(self, *, total):
        self.state.update({'status': STATUS_RUNNING, 'current': 0,
                           'total': total, 'fail_message': ''})

    def set_total(self, total):
        self.state['total'] = int(total)

    def get_total(self):
        return int(self.state.get('total', 0))

    def get_current(self):
        return int(self.state.get('current', 0))

    def set_current(self, value):
        self.state['current'] = int(value)

    def inc_current(self, n=1, *, cap=None):
        new_val = int(self.state.get('current', 0)) + n
        if cap is not None and new_val > cap:
            new_val = cap
        self.state['current'] = new_val
        return new_val

    def complete(self, *, chapters):
        self.state['status'] = STATUS_COMPLETE
        self.state['chapters'] = list(chapters)
        self.state['current'] = self.state.get('total', 0)

    def fail(self, message):
        self.state['status'] = STATUS_FAILED
        self.state['fail_message'] = str(message) if message is not None else ''

    def check_cancel(self):
        if self.cancelled:
            raise JobCancelled()
