import logging
import uuid
from datetime import datetime

from flask import (abort, request, jsonify, redirect, render_template,
                   send_from_directory, send_file, session, url_for)
from flask_limiter.util import get_remote_address
from flask_login import current_user, login_required

from controllers.auth import register_rate_limits
from features import job_queue
from features.tasks import run_story_creator
from models import db
from models.job import (ACTIVE_STATUSES, Job, STATUS_CANCELLED,
                        STATUS_COMPLETE, STATUS_QUEUED)
from models.novel import Novel, TITLE_MAX_LENGTH
from models.story_pdf import StoryPDF

from utilities import prompt_templates as pt

logger = logging.getLogger(__name__)


def _get_or_create_anon_id():
    """Return the anonymous session id, minting one if needed."""
    anon_id = session.get('anon_id')
    if not anon_id:
        anon_id = uuid.uuid4().hex
        session['anon_id'] = anon_id
    return anon_id


def _require_job_owner(job_id):
    """Look up a Job and enforce that the current requester owns it.

    Returns the Job on success. Aborts 404 on any mismatch (including
    when the job does not exist) so a stranger cannot probe job ids.
    """
    job = db.session.get(Job, job_id)
    if job is None:
        abort(404)
    anon_id = session.get('anon_id')
    if not job.is_owned_by(current_user, anon_id):
        abort(404)
    return job


def _job_status_payload(job):
    """Shape the public view of a Job for /api/jobs/<id> responses."""
    return {
        'id': job.id,
        'status': job.status,
        'current': job.current,
        'total': job.total,
        'fail_message': job.fail_message or '',
        'created_at': job.created_at.isoformat() + 'Z',
        'completed_at': (job.completed_at.isoformat() + 'Z'
                         if job.completed_at else None),
    }


def configure_routes(app, csrf=None, limiter=None):

    if limiter is not None:
        register_rate_limits(app, limiter)

    @app.route('/', methods=['GET', 'POST'])
    def index():
        return send_from_directory('.', 'index.html')

    @app.route('/api/me')
    def api_me():
        if current_user.is_authenticated:
            return jsonify({'username': current_user.username})
        return jsonify({'username': None})

    @app.route('/api/jobs', methods=['POST'])
    def create_job():
        data = request.get_json(silent=True) or {}
        title = (data.get('title') or '').strip()
        api_key = data.get('api_key') or ''
        chatgpt_model = data.get('bulk_model') or ''
        version = data.get('version') or 'v2'
        summary = data.get('summary')

        if not title:
            return jsonify({'error': 'Title is required.'}), 400
        if summary is None:
            return jsonify({
                'error': 'Type of format not specified. Expected summary.'
            }), 400
        if version not in ('v0', 'v1', 'v2'):
            return jsonify({'error': 'Unknown version.'}), 400

        # Per-user concurrency cap: a single requester can only have one
        # active job at a time. Returning 409 forces the client to cancel
        # (or wait) rather than silently stacking OpenAI spend.
        owner_filter = (Job.user_id == current_user.id
                        if current_user.is_authenticated
                        else Job.anon_session_id == _get_or_create_anon_id())
        active = (Job.query
                  .filter(owner_filter)
                  .filter(Job.status.in_(ACTIVE_STATUSES))
                  .first())
        if active is not None:
            return jsonify({
                'error': 'You already have a job in progress.',
                'job_id': active.id,
            }), 409

        prompt_overrides = (
            current_user.get_prompt_settings()
            if current_user.is_authenticated else {}
        )

        job = Job(
            user_id=(current_user.id if current_user.is_authenticated
                     else None),
            anon_session_id=(None if current_user.is_authenticated
                             else _get_or_create_anon_id()),
            status=STATUS_QUEUED,
            version=version,
            model=chatgpt_model,
            title=title[:TITLE_MAX_LENGTH],
            summary=summary,
            api_key=api_key,
        )
        job.prompt_overrides = prompt_overrides
        # Anonymous jobs are gated on a fresh heartbeat; seed it at
        # creation so the worker doesn't immediately time them out.
        if job.is_anonymous():
            job.last_heartbeat = datetime.utcnow()
        db.session.add(job)
        db.session.commit()

        job_queue.get_queue().enqueue(run_story_creator, job.id,
                                      job_timeout='30m')

        return jsonify({'job_id': job.id, 'status': job.status}), 202

    @app.route('/api/jobs/<job_id>', methods=['GET'])
    def get_job(job_id):
        job = _require_job_owner(job_id)
        # Anonymous heartbeat: every poll from the owner extends the
        # window. Logged-in jobs don't set last_heartbeat and aren't
        # affected by the timeout.
        if job.is_anonymous():
            job.last_heartbeat = datetime.utcnow()
            db.session.commit()
        # Prefer the live Redis counters while the job is running so the
        # bar moves smoothly; fall back to the DB copy once terminal.
        if job.status in (STATUS_QUEUED,) or job.is_active():
            live = job_queue.progress_get(job_id)
            if live:
                try:
                    job.current = int(live.get('current', job.current) or 0)
                    job.total = int(live.get('total', job.total) or 0)
                except (TypeError, ValueError):
                    pass
        return jsonify(_job_status_payload(job))

    @app.route('/api/jobs/<job_id>/cancel', methods=['POST'])
    def cancel_job(job_id):
        job = _require_job_owner(job_id)
        if job.is_terminal():
            return jsonify(_job_status_payload(job))
        job.status = STATUS_CANCELLED
        job.completed_at = datetime.utcnow()
        db.session.commit()
        # Writing Redis last ensures the DB row already says cancelled by
        # the time the worker sees the flag and exits.
        job_queue.progress_set(job_id, {'status': STATUS_CANCELLED})
        return jsonify(_job_status_payload(job))

    @app.route('/api/jobs/<job_id>/pdf', methods=['GET'])
    def get_job_pdf(job_id):
        job = _require_job_owner(job_id)
        if job.status != STATUS_COMPLETE:
            return jsonify({'error': 'Job is not complete.',
                            'status': job.status}), 409
        chapters = job.chapters
        if not chapters:
            return jsonify({'error': 'Job has no chapters.'}), 404
        style = request.args.get('style') or None
        try:
            story_pdf = StoryPDF(style=style)
            pdf_full_path = story_pdf.create(title=job.title,
                                             chapters=chapters)
            if not pdf_full_path:
                raise ValueError('PDF file path is invalid or empty')
            return send_file(pdf_full_path, as_attachment=True)
        except Exception:
            logger.exception('Failed to generate PDF for job %s', job_id)
            return jsonify({'error': 'Failed to generate PDF'}), 500

    @app.route('/api/my-novels')
    @login_required
    def my_novels_list():
        rows = (Novel.query
                .filter_by(user_id=current_user.id)
                .order_by(Novel.created_at.desc())
                .all())
        return jsonify([{
            'id': n.id,
            'title': n.title,
            'created_at': n.created_at.isoformat() + 'Z',
        } for n in rows])

    @app.route('/api/my-novels/<int:novel_id>/pdf')
    @login_required
    def my_novels_pdf(novel_id):
        novel = Novel.query.get(novel_id)
        if novel is None or novel.user_id != current_user.id:
            abort(404)
        try:
            story_pdf = StoryPDF()
            pdf_full_path = story_pdf.create(
                title=novel.title, chapters=novel.chapters,
            )
            return send_file(pdf_full_path, as_attachment=True)
        except Exception:
            logger.exception('Failed to regenerate PDF for saved novel %s',
                             novel_id)
            return jsonify({'error': 'Failed to generate PDF'}), 500

    @app.route('/settings', methods=['GET'])
    def settings_page():
        # Anonymous visitors get bounced to login; the button in the header
        # is still visible so they know the feature exists.
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=url_for('settings_page')))
        return render_template(
            'settings.html',
            registry=pt.PROMPT_TEMPLATE_REGISTRY,
            defaults=pt.get_default_prompts(),
            overrides=current_user.get_prompt_settings(),
        )

    @app.route('/api/prompt-settings', methods=['GET'])
    def api_prompt_settings_get():
        return jsonify({
            'logged_in': current_user.is_authenticated,
            'defaults': pt.get_default_prompts(),
            'settings': (current_user.get_prompt_settings()
                         if current_user.is_authenticated else {}),
            'registry': pt.PROMPT_TEMPLATE_REGISTRY,
        })

    @app.route('/api/prompt-settings', methods=['POST'])
    @login_required
    def api_prompt_settings_save():
        payload = request.get_json(silent=True) or {}
        incoming = payload.get('settings')
        if not isinstance(incoming, dict):
            return jsonify({'error': 'Expected a JSON object under "settings".'}), 400

        # Whitelist the submitted keys against the registry so users cannot
        # smuggle arbitrary blobs into the column. Only strings are kept,
        # and only for keys that exist in the default template.
        cleaned = {}
        for group in pt.PROMPT_TEMPLATE_REGISTRY:
            for tpl in group['templates']:
                name = tpl['name']
                if name not in incoming or not isinstance(incoming[name], dict):
                    continue
                default = pt.get_default_template(name)
                tpl_clean = {}
                for key, value in incoming[name].items():
                    if not isinstance(value, str):
                        continue
                    if isinstance(default, list):
                        try:
                            idx = int(key)
                        except (TypeError, ValueError):
                            continue
                        if 0 <= idx < len(default) and value != default[idx]:
                            tpl_clean[str(idx)] = value
                    else:
                        if key in default and value != default[key]:
                            tpl_clean[key] = value
                if tpl_clean:
                    cleaned[name] = tpl_clean

        current_user.set_prompt_settings(cleaned or None)
        db.session.commit()
        return jsonify({'ok': True, 'settings': cleaned})

    @app.route('/api/prompt-settings/reset', methods=['POST'])
    @login_required
    def api_prompt_settings_reset():
        current_user.set_prompt_settings(None)
        db.session.commit()
        return jsonify({'ok': True})

    # JSON API endpoints used by scripts.js: request payloads contain
    # user-supplied data (OpenAI API key, generated chapters) that an
    # attacker cannot forge, so CSRF exposure is negligible.
    if csrf is not None:
        csrf.exempt(create_job)
        csrf.exempt(cancel_job)
        csrf.exempt(api_me)
        csrf.exempt(api_prompt_settings_get)
        csrf.exempt(api_prompt_settings_save)
        csrf.exempt(api_prompt_settings_reset)

    # Apply a stricter rate limit to the expensive novel generation endpoint.
    # Key by user id for logged-in users and by remote address for anonymous
    # users so concurrent requesters get independent buckets. Replace the
    # entry in app.view_functions so Flask dispatches through the wrapper.
    if limiter is not None:
        def _novel_gen_rate_key():
            if current_user.is_authenticated:
                return f'u:{current_user.get_id()}'
            return f'a:{get_remote_address()}'

        wrapped = limiter.limit(
            '10 per hour',
            key_func=_novel_gen_rate_key,
        )(create_job)
        app.view_functions['create_job'] = wrapped