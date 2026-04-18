"""Ensures requirements.txt is valid and fully pinned for reproducible Heroku
builds."""
import os
import re


REQ_LINE = re.compile(r'^([A-Za-z0-9_.\-]+)==([A-Za-z0-9_.\-+]+)\s*$')


def _read_requirements(name):
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(here, name), 'r') as fh:
        return [line.strip() for line in fh.readlines()
                if line.strip() and not line.lstrip().startswith('#')
                and not line.lstrip().startswith('-')]


def test_all_requirements_are_pinned():
    unpinned = []
    for line in _read_requirements('requirements.txt'):
        if not REQ_LINE.match(line):
            unpinned.append(line)
    assert not unpinned, (
        f'requirements.txt entries must be pinned with ==: {unpinned}'
    )


def test_required_packages_present():
    pkgs = {REQ_LINE.match(line).group(1).lower()
            for line in _read_requirements('requirements.txt')
            if REQ_LINE.match(line)}
    for required in [
        'flask', 'flask-sqlalchemy', 'flask-migrate', 'flask-login',
        'flask-wtf', 'flask-limiter', 'gunicorn', 'pymysql',
        'itsdangerous', 'werkzeug',
    ]:
        assert required in pkgs, f'missing required package: {required}'


def test_postgres_driver_is_not_declared():
    """JawsDB Maria uses MySQL/MariaDB; psycopg2 must not sneak back in."""
    joined = '\n'.join(_read_requirements('requirements.txt')).lower()
    assert 'psycopg2' not in joined


def test_dev_requirements_include_pytest():
    lines = _read_requirements('requirements-dev.txt')
    joined = '\n'.join(lines).lower()
    assert 'pytest' in joined
