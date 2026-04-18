import logging
import os

import requests

logger = logging.getLogger(__name__)


class MailgunError(RuntimeError):
    pass


def _config():
    api_key = os.environ.get('MAILGUN_API_KEY')
    domain = os.environ.get('MAILGUN_DOMAIN')
    sender = os.environ.get('MAILGUN_FROM') or (
        f'no-reply@{domain}' if domain else None
    )
    api_base = os.environ.get('MAILGUN_API_BASE', 'https://api.mailgun.net/v3')
    return api_key, domain, sender, api_base


def send_email(to, subject, text, html=None):
    api_key, domain, sender, api_base = _config()
    if not api_key or not domain or not sender:
        if os.environ.get('ENV') != 'production':
            logger.warning(
                '[dev] Mailgun not configured; logging email instead.\n'
                'To: %s\nSubject: %s\n\n%s', to, subject, text,
            )
            return {'dev_logged': True}
        raise MailgunError(
            'Mailgun is not configured. Set MAILGUN_API_KEY, MAILGUN_DOMAIN and '
            'optionally MAILGUN_FROM.'
        )

    data = {'from': sender, 'to': [to], 'subject': subject, 'text': text}
    if html:
        data['html'] = html

    url = f'{api_base}/{domain}/messages'
    try:
        response = requests.post(url, auth=('api', api_key), data=data, timeout=15)
    except requests.RequestException as exc:
        logger.exception('Mailgun request failed')
        raise MailgunError(f'Mailgun request failed: {exc}') from exc

    if response.status_code >= 400:
        logger.error('Mailgun returned %s: %s', response.status_code, response.text)
        raise MailgunError(
            f'Mailgun returned {response.status_code}: {response.text}'
        )

    return response.json() if response.content else {}
