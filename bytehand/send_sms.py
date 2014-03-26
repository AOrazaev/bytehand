# -*- coding: utf-8 -*-

import requests
import urlparse
import urllib

from definitions import API_URL


def _generate_url_path(to, text, sign, user_id, key):
    path = 'send?id={user}&key={key}&to={to}&from={sign}&text={text}'
    return path.format(
        user=urllib.quote(user_id),
        key=urllib.quote(key),
        to=to,
        sign=urllib.quote(sign),
        text=urllib.quote(text)
    )

def send_sms(to, text, signature, user_id, key):
    to = str(to)
    user_id = str(user_id)
    if not to.isdigit():
        raise TypeError('Incorrect "to"-field format. '
                        'It must be string of digits, '
                        'but it is: "{}"'.format(to))
    if not text:
        raise TypeError('Can\'t send empty message.')
    if not signature:
        raise TypeError('Signature should be set.')
    if not user_id.isdigit():
        raise TypeError('User id must be digit, '
                        'but it is: {}'.format(user_id))

    path = _generate_url_path(to, text, signature, user_id, key)
    response = requests.get(urlparse.urljoin(API_URL, path))


