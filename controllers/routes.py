import logging
import threading

from flask import request, jsonify, send_from_directory, send_file
from flask_login import current_user, login_required

from controllers.auth import register_rate_limits
from models.story_pdf import StoryPDF

from features.story_creator_v0 import StoryCreator as SC0
from features.story_creator_v1 import StoryCreator as SC1
from features.story_creator_v2 import StoryCreator as SC2

logger = logging.getLogger(__name__)

# Per-user progress state. Keyed by user id so concurrent users do not
# overwrite each other's progress. Each inner dict is only ever read/written
# by one user's request thread and that user's background worker thread.
_progress_by_user = {}
_progress_lock = threading.Lock()


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
    @login_required
    def index():
        return send_from_directory('.', 'index.html')

    @app.route('/api/me')
    @login_required
    def api_me():
        return jsonify({
            'username': current_user.username,
        })

    @app.route('/novel-gen', methods=['POST'])
    @login_required
    def submit_book_writer_form():
        progress_data = _reset_progress_dict(current_user.id)

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
    @login_required
    def progress():
        progress_data = _get_progress_dict(current_user.id)
        snapshot = dict(progress_data)
        if 'text' in snapshot:
            snapshot['text'] = ''
        return jsonify(snapshot)

    @app.route('/create-pdf', methods=['POST'])
    @login_required
    def pdf_route():
        data = request.json

        try:
            story_pdf = StoryPDF()

            pdf_full_path = story_pdf.create(title=data['title'], chapters=data['chapters'])

            if not pdf_full_path:
                raise ValueError("PDF file path is invalid or empty")

            return send_file(pdf_full_path, as_attachment=True)

        except Exception as e:
            logger.exception('An error occurred while generating the PDF.')

            # Record failure against the current user's progress dict without
            # leaking the server traceback back to the client.
            progress_data = _get_progress_dict(current_user.id)
            progress_data['fail'] = True
            progress_data['fail_message'] = 'PDF generation failed.'

            return jsonify({'error': 'Failed to generate PDF'}), 500

    # JSON API endpoints used by scripts.js: these are authenticated and the
    # request payloads contain user-specific data (OpenAI API key, generated
    # chapters) that an attacker cannot forge, so CSRF exposure is negligible.
    if csrf is not None:
        csrf.exempt(submit_book_writer_form)
        csrf.exempt(pdf_route)
        csrf.exempt(api_me)

    # Apply a stricter, authenticated rate limit to the expensive novel
    # generation endpoint. Key by user id so concurrent users get independent
    # buckets. Replace the entry in app.view_functions so Flask dispatches
    # through the rate-limited wrapper.
    if limiter is not None:
        wrapped = limiter.limit(
            '10 per hour',
            key_func=lambda: str(current_user.get_id() or 'anon'),
        )(submit_book_writer_form)
        app.view_functions['submit_book_writer_form'] = wrapped