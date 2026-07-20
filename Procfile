release: flask db upgrade
web: gunicorn app:app
worker: rq worker --url $REDISCLOUD_URL default
