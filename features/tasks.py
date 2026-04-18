"""Top-level task functions invoked by the RQ worker (or the sync
fallback) to run a novel-generation job.

These functions are the entry point for ``features.job_queue.get_queue()``
enqueue calls. They are importable by name so ``rq worker`` can locate
them via ``features.tasks.run_story_creator``.
"""
import logging
import traceback

logger = logging.getLogger(__name__)


def run_story_creator(job_id):
    """Execute a queued novel-generation job.

    Loads the Job row, constructs the appropriate StoryCreator version,
    and runs ``process_summary`` with a ``JobProgressStore``. Top-level
    exceptions are caught and recorded on the job so the web tier can
    report them to the client. ``JobCancelled`` is the expected signal
    that a cooperating cancel has short-circuited the run and is simply
    swallowed - the row is already in the ``cancelled`` state.

    Imports are deferred so the module itself is cheap to import (and
    doesn't trigger the Flask app to be built) until a worker actually
    picks up a job.
    """
    # Deferred imports: importing app.py builds the Flask application,
    # which we want to happen exactly once per worker process. Placing it
    # here also avoids a circular import between controllers.routes and
    # this module.
    from app import app as flask_app
    from features.progress_store import JobCancelled, JobProgressStore
    from features.story_creator_v0 import StoryCreator as SC0
    from features.story_creator_v1 import StoryCreator as SC1
    from features.story_creator_v2 import StoryCreator as SC2
    from models import db
    from models.job import Job, STATUS_RUNNING
    from models.novel import Novel, TITLE_MAX_LENGTH

    with flask_app.app_context():
        job = db.session.get(Job, job_id)
        if job is None:
            logger.warning('run_story_creator: job %s not found', job_id)
            return

        # If the job was cancelled before the worker picked it up, don't
        # charge any OpenAI calls against it.
        if job.status != 'queued':
            logger.info('run_story_creator: job %s not in queued state (%s)',
                        job_id, job.status)
            return

        job.status = STATUS_RUNNING
        db.session.commit()

        progress = JobProgressStore(job_id)
        api_key = job.api_key
        version = job.version
        model = job.model
        title = job.title
        summary = job.summary
        prompt_overrides = job.prompt_overrides
        testing = flask_app.config.get('TESTING', False)
        # Capture the pieces we need to persist a Novel row so we're not
        # holding a reference to the Job object across the long-running
        # process_summary call.
        user_id = job.user_id

        if version == 'v0':
            story_creator = SC0(progress=progress,
                                prompt_overrides=prompt_overrides)
        elif version == 'v1':
            story_creator = SC1(progress=progress, api_key=api_key,
                                testing=testing,
                                prompt_overrides=prompt_overrides)
        else:  # 'v2' and any future default
            story_creator = SC2(progress=progress, api_key=api_key,
                                testing=testing,
                                prompt_overrides=prompt_overrides)

        try:
            story_creator.process_summary(title, summary, model)
        except JobCancelled:
            logger.info('run_story_creator: job %s cancelled', job_id)
            return
        except SystemExit as exc:
            # StoryCreator raises SystemExit on HTTP/network errors after
            # calling progress.fail(); just log and exit the worker.
            logger.warning('run_story_creator: job %s aborted: %s',
                           job_id, exc)
            return
        except Exception as exc:
            logger.exception('run_story_creator: job %s failed', job_id)
            try:
                progress.fail(traceback.format_exception_only(
                    type(exc), exc)[-1].strip())
            except Exception:
                logger.exception(
                    'run_story_creator: failed to record failure on job %s',
                    job_id)
            return

        # Persist a Novel row for logged-in users as soon as the job
        # completes, so "My novels" is populated without requiring the
        # user to download the PDF first.
        if user_id is not None:
            try:
                refreshed = db.session.get(Job, job_id)
                if refreshed is not None and refreshed.chapters:
                    novel_title = (refreshed.title or '')[:TITLE_MAX_LENGTH]
                    if novel_title and refreshed.chapters:
                        novel = Novel(user_id=user_id, title=novel_title)
                        novel.chapters = refreshed.chapters
                        db.session.add(novel)
                        db.session.commit()
            except Exception:
                # Never let a bookkeeping failure mask a successful
                # generation; the chapters remain on the Job row and can
                # still be downloaded via /api/jobs/<id>/pdf.
                logger.exception(
                    'run_story_creator: failed to persist Novel for job %s',
                    job_id)
                db.session.rollback()
