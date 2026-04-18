"""Queue and Redis wiring for asynchronous novel generation.

Two execution modes:

* **Redis-backed** (production) - enabled when ``REDISCLOUD_URL`` or
  ``REDIS_URL`` is set. ``get_queue()`` returns an RQ ``Queue`` that
  enqueues jobs onto Redis; a separate ``rq worker`` process picks them
  up. Progress counters live in Redis hashes keyed by job id.
* **Synchronous in-process** (dev fallback) - used when no Redis URL is
  configured. ``get_queue()`` returns a shim whose ``enqueue`` spawns a
  daemon thread so the web request still returns immediately; progress
  counters live in an in-memory dict guarded by a lock. This mirrors the
  old ``threading.Thread`` behaviour for local development without
  requiring Redis.

The rest of the app only talks to this module via ``get_queue()`` and
``progress_*`` helpers, so swapping backends happens in one place.
"""
import os
import threading
from typing import Any, Callable, Optional

_redis_client = None
_redis_checked = False
_queue = None
_queue_lock = threading.Lock()

# In-memory progress store used only in the synchronous dev fallback. Keyed
# by job id; each value is a dict of string fields. A single lock guards all
# reads/writes because the background worker thread and the /progress poll
# handler touch the same dict.
_memory_progress: dict = {}
_memory_progress_lock = threading.Lock()


def _redis_url() -> Optional[str]:
    # Heroku's "Redis Cloud" add-on publishes REDISCLOUD_URL. Plain REDIS_URL
    # is accepted as a generic override for local dev or other hosts.
    return os.environ.get('REDISCLOUD_URL') or os.environ.get('REDIS_URL')


def get_redis_connection():
    """Return a cached Redis client, or ``None`` if Redis is not configured."""
    global _redis_client, _redis_checked
    if _redis_checked:
        return _redis_client
    url = _redis_url()
    if not url:
        _redis_checked = True
        return None
    import redis  # local import so dev without redis installed still works
    _redis_client = redis.from_url(url, decode_responses=True)
    _redis_checked = True
    return _redis_client


class _SyncQueue:
    """Queue shim that runs jobs in a daemon thread instead of Redis/RQ.

    Only the single ``enqueue`` method is used by the rest of the app, so we
    deliberately do not implement the full RQ interface.
    """

    def enqueue(self, func: Callable[..., Any], *args, **kwargs):
        job_timeout = kwargs.pop('job_timeout', None)  # ignored in dev
        _ = job_timeout
        t = threading.Thread(target=func, args=args, kwargs=kwargs,
                             daemon=True)
        t.start()
        return t


def get_queue():
    """Return the process-wide queue instance (RQ or synchronous shim)."""
    global _queue
    with _queue_lock:
        if _queue is not None:
            return _queue
        conn = get_redis_connection()
        if conn is None:
            _queue = _SyncQueue()
        else:
            from rq import Queue
            _queue = Queue('default', connection=conn)
        return _queue


# ---------------------------------------------------------------------------
# Progress storage
# ---------------------------------------------------------------------------
#
# The worker writes progress fields on every OpenAI call; the web handler
# reads them on every /progress poll. Using Redis hashes keeps this off the
# relational DB hot path. The field set is intentionally small and all
# string-valued so it maps cleanly onto Redis. Terminal transitions also
# copy the final state into the ``jobs`` row so the DB record is
# self-contained.

_PROGRESS_TTL_SECONDS = 60 * 60 * 24  # 24h; jobs_table row is source of truth


def _progress_key(job_id: str) -> str:
    return f'job:{job_id}:progress'


def progress_set(job_id: str, fields: dict) -> None:
    """Merge ``fields`` into the job's progress hash."""
    if not fields:
        return
    payload = {k: ('' if v is None else str(v)) for k, v in fields.items()}
    conn = get_redis_connection()
    if conn is not None:
        conn.hset(_progress_key(job_id), mapping=payload)
        conn.expire(_progress_key(job_id), _PROGRESS_TTL_SECONDS)
        return
    with _memory_progress_lock:
        d = _memory_progress.setdefault(job_id, {})
        d.update(payload)


def progress_get(job_id: str) -> dict:
    """Return the current progress hash (empty dict if unknown)."""
    conn = get_redis_connection()
    if conn is not None:
        return conn.hgetall(_progress_key(job_id)) or {}
    with _memory_progress_lock:
        return dict(_memory_progress.get(job_id, {}))


def progress_increment(job_id: str, field: str, amount: int = 1) -> int:
    """Atomically bump an integer progress counter, returning the new value."""
    conn = get_redis_connection()
    if conn is not None:
        new_val = conn.hincrby(_progress_key(job_id), field, amount)
        conn.expire(_progress_key(job_id), _PROGRESS_TTL_SECONDS)
        return int(new_val)
    with _memory_progress_lock:
        d = _memory_progress.setdefault(job_id, {})
        cur = int(d.get(field, '0') or '0')
        cur += amount
        d[field] = str(cur)
        return cur


def progress_clear(job_id: str) -> None:
    conn = get_redis_connection()
    if conn is not None:
        conn.delete(_progress_key(job_id))
        return
    with _memory_progress_lock:
        _memory_progress.pop(job_id, None)
