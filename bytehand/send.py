# -*- coding: utf-8 -*-

import requests
import urlparse
import urllib

from definitions import API_URL
from connection import Connection


def send_sms(to, signature, text, userid, key):
    """Fast function for sending sms.

    Create connection with given (userid, key) pair and
    send sms.

    :note: Your @signature must be verified on bytehand.

    :param to: receiver phone number.
    :param signature: value of "from"-field of sms message.
    :param text: message content.
    :param userid: your bytehand api id.
    :param key: your bytehand api key.

    :see: https://www.bytehand.com/secure/settings to get your key and id.
    """
    to = str(to)
    userid = str(userid)
    if not to.isdigit():
        raise TypeError('Incorrect "to"-field format. '
                        'It must be string of digits, '
                        'but it is: "{}"'.format(to))
    if not text:
        raise TypeError('Can\'t send empty message.')
    if not signature:
        raise TypeError('Signature should be set.')
    if not userid.isdigit():
        raise TypeError('User id must be digit, '
                        'but it is: {}'.format(userid))

    conn = Connection(userid=userid, key=key)
    return conn.send(to=to, signature=signature, text=text)
