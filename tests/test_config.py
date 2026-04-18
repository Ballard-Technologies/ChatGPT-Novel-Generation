"""Tests for app.py configuration and deploy-time invariants.

The config tests spawn a fresh Python subprocess per scenario because
``app.py`` builds a module-level Flask app with side effects on shared
globals (db engine, Limiter storage, blueprint registrations).  Running
them in-process would corrupt state used by the rest of the suite.
"""
import os
import subprocess
import sys
import textwrap


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run_in_subprocess(env_overrides, script):
    env = os.environ.copy()
    env.pop('PYTEST_CURRENT_TEST', None)
    for k, v in env_overrides.items():
        if v is None:
            env.pop(k, None)
        else:
            env[k] = v
    return subprocess.run(
        [sys.executable, '-c', textwrap.dedent(script)],
        cwd=ROOT, env=env, capture_output=True, text=True,
    )


def test_jawsdb_maria_url_is_used_and_driver_is_injected():
    result = _run_in_subprocess(
        {'SECRET_KEY': 'x',
         'JAWSDB_MARIA_URL': 'mysql://user:pass@host:3306/db',
         'DATABASE_URL': None,
         'ENV': None},
        'import app; print(app.app.config["SQLALCHEMY_DATABASE_URI"])',
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'mysql+pymysql://user:pass@host:3306/db'


def test_jawsdb_url_takes_precedence_over_database_url():
    result = _run_in_subprocess(
        {'SECRET_KEY': 'x',
         'JAWSDB_MARIA_URL': 'mysql://jaws:pw@jaws-host/jawsdb',
         'DATABASE_URL': 'sqlite:///should-be-ignored.db',
         'ENV': None},
        'import app; print(app.app.config["SQLALCHEMY_DATABASE_URI"])',
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().startswith('mysql+pymysql://jaws:')


def test_database_url_still_works_as_fallback():
    result = _run_in_subprocess(
        {'SECRET_KEY': 'x',
         'JAWSDB_MARIA_URL': None,
         'DATABASE_URL': 'sqlite:///:memory:',
         'ENV': None},
        'import app; print(app.app.config["SQLALCHEMY_DATABASE_URI"])',
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'sqlite:///:memory:'


def test_engine_options_enable_pool_pre_ping():
    result = _run_in_subprocess(
        {'SECRET_KEY': 'x',
         'JAWSDB_MARIA_URL': 'mysql://u:p@h/d',
         'DATABASE_URL': None,
         'ENV': None},
        '''
        import app
        opts = app.app.config.get("SQLALCHEMY_ENGINE_OPTIONS", {})
        print(opts.get("pool_pre_ping"))
        ''',
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'True'


def test_secret_key_required_in_production():
    result = _run_in_subprocess(
        {'ENV': 'production', 'SECRET_KEY': None,
         'DATABASE_URL': 'sqlite:///:memory:'},
        'import app',
    )
    assert result.returncode != 0
    assert 'SECRET_KEY' in result.stderr


def test_secure_cookies_in_production():
    result = _run_in_subprocess(
        {'ENV': 'production', 'SECRET_KEY': 'x',
         'DATABASE_URL': 'sqlite:///:memory:'},
        '''
        import app
        c = app.app.config
        print(c["SESSION_COOKIE_SECURE"], c["REMEMBER_COOKIE_SECURE"],
              c["SESSION_COOKIE_SAMESITE"])
        ''',
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'True True Lax'


def test_dev_uses_testing_config():
    result = _run_in_subprocess(
        {'ENV': None, 'SECRET_KEY': 'x',
         'DATABASE_URL': 'sqlite:///:memory:'},
        'import app; print(app.app.config["TESTING"])',
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'True'


def test_runtime_txt_pins_python_312():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(here, 'runtime.txt'), 'r') as fh:
        content = fh.read().strip()
    assert content.startswith('python-3.12'), content


def test_procfile_runs_gunicorn():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(here, 'Procfile'), 'r') as fh:
        content = fh.read()
    assert 'gunicorn' in content
    assert 'app:app' in content
