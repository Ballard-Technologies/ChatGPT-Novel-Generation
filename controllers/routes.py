import logging
import threading
import uuid

from flask import abort, request, jsonify, send_from_directory, send_file, session
from flask_limiter.util import get_remote_address
from flask_login import current_user, login_required

from controllers.auth import register_rate_limits
from models import db
from models.novel import Novel, TITLE_MAX_LENGTH
from models.story_pdf import StoryPDF

from features.story_creator_v0 import StoryCreator as SC0
from features.story_creator_v1 import StoryCreator as SC1
from features.story_creator_v2 import StoryCreator as SC2

logger = logging.getLogger(__name__)

# Per-requester progress state. Keyed by a string that is either
# ``u:<user_id>`` for logged-in users or ``a:<anon_session_id>`` for anonymous
# browser sessions, so concurrent requesters do not overwrite each other's
# progress. Each inner dict is only ever read/written by one requester's
# request thread and that requester's background worker thread.
_progress_by_user = {}
_progress_lock = threading.Lock()


def _current_requester_key():
    """Return a stable key identifying the current requester.

    Authenticated users get ``u:<id>``. Anonymous users get ``a:<uuid>``
    stored in the Flask session so the same browser keeps the same key
    across requests.
    """
    if current_user.is_authenticated:
        return f'u:{current_user.id}'
    anon_id = session.get('anon_id')
    if not anon_id:
        anon_id = uuid.uuid4().hex
        session['anon_id'] = anon_id
    return f'a:{anon_id}'


def _get_progress_dict(user_id):
    with _progress_lock:
        d = _progress_by_user.get(user_id)
        if d is None:
            d = {}
            _progress_by_user[user_id] = d
        return d


def _reset_progress_dict(user_id):
    with _progress_lock:
        d = _progress_by_user.get(user_id)
        if d is None:
            d = {}
            _progress_by_user[user_id] = d
        else:
            d.clear()
        d['complete'] = False
        d['fail'] = False
        d['fail_message'] = ''
        d['meta_text'] = ''
        return d


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

    @app.route('/novel-gen', methods=['POST'])
    def submit_book_writer_form():
        progress_data = _reset_progress_dict(_current_requester_key())

        data = request.json
        title = data['title']
        api_key = data['api_key']
        chatgpt_model = data['bulk_model']
        version = data['version']

        if version == 'v0':
            story_creator = SC0(progress_data=progress_data)
        elif version == 'v1':
            story_creator = SC1(progress_data=progress_data, api_key=api_key, testing=app.config.get('TESTING'))
        elif version == 'v2':
            story_creator = SC2(progress_data=progress_data, api_key=api_key, testing=app.config.get('TESTING'))
        else:
            story_creator = SC2(progress_data=progress_data, api_key=api_key, testing=app.config.get('TESTING'))

        if 'summary' in data:
            summary_data = data['summary']
            threading.Thread(target=story_creator.process_summary, args=(title, summary_data, chatgpt_model)).start()
        else:
            return jsonify({'message': 'Type of format not specified. Expected outline or summary.'}), 400

        return jsonify({'message': 'Processing started successfully'}), 200

    @app.route('/progress')
    def progress():
        progress_data = _get_progress_dict(_current_requester_key())
        snapshot = dict(progress_data)
        if 'text' in snapshot:
            snapshot['text'] = ''
        return jsonify(snapshot)

    @app.route('/create-pdf', methods=['POST'])
    def pdf_route():
        data = request.json

        try:
            story_pdf = StoryPDF(style=data.get('style'))

            pdf_full_path = story_pdf.create(title=data['title'], chapters=data['chapters'])

            if not pdf_full_path:
                raise ValueError("PDF file path is invalid or empty")

            # Persist the novel for logged-in users so it shows up in their
            # "My novels" list. Anonymous users get the PDF without saving.
            if current_user.is_authenticated:
                title = (data.get('title') or '')[:TITLE_MAX_LENGTH]
                chapters = data.get('chapters') or []
                if title and chapters:
                    novel = Novel(user_id=current_user.id, title=title)
                    novel.chapters = chapters
                    db.session.add(novel)
                    db.session.commit()

            return send_file(pdf_full_path, as_attachment=True)

        except Exception as e:
            logger.exception('An error occurred while generating the PDF.')

            # Record failure against the current requester's progress dict
            # without leaking the server traceback back to the client.
            progress_data = _get_progress_dict(_current_requester_key())
            progress_data['fail'] = True
            progress_data['fail_message'] = 'PDF generation failed.'

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

    # JSON API endpoints used by scripts.js: request payloads contain
    # user-supplied data (OpenAI API key, generated chapters) that an
    # attacker cannot forge, so CSRF exposure is negligible.
    if csrf is not None:
        csrf.exempt(submit_book_writer_form)
        csrf.exempt(pdf_route)
        csrf.exempt(api_me)

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
        )(submit_book_writer_form)
        app.view_functions['submit_book_writer_form'] = wrapped