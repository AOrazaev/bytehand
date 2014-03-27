# -*- coding: utf-8 -*-
"""FIXME

To open connection just enter:
    >>> conn = Connection(userid=1342, key='5C3D5D3C2B1C4D8B')

Now you can use your connection for sms sending:
    >>> response = conn.send(               # doctest:+SKIP
    ...     to=1234567890,
    ...     text='Hi!',
    ...     signature='bytehand'
    ... )
"""

import json
import urlparse
import urllib
import requests

from definitions import API_URL


class ConnectionError(Exception):
    pass


class Connection(object):
    """Connection to bytehand class.

    :param userid: Your bytehand api id.
    :param key: Your bytehand api key.

    :see: https://www.bytehand.com/secure/settings to get your key and id.
    """
    _API_URL = urlparse.urlparse(API_URL)

    def __init__(self, userid=None, key=None):
        if userid is None or key is None:
            raise ValueError('"userid" and "key" parameters should be set')
        self._userid = userid
        self._key = key

    @property
    def userid(self):
        return self._userid

    @property
    def key(self):
        return self._key

    def send(self, to=None, signature=None, text=None, **kwargs):
        msg = {'to': str(to),
               'from': str(signature),
               'text': text}
        data = json.dumps([msg])

        headers = {'Content-Type': 'application/json;charset=UTF-8'}
        resp = self._post_request('send_multi', data=data, headers=headers,
                                  qargs=dict(id=self.userid, key=self.key),
                                  verify=False)
        resp = resp.json()[0]
        return _SMSResponse(self, resp['status'], resp['description'])

    def _post_request(self, request_type, data=None, qargs={}, **kwargs):
        query = '&'.join('{}={}'.format(arg, urllib.quote(str(val)))
                         for arg, val in qargs.iteritems())
        url = self._API_URL._replace(path=request_type, query=query).geturl()
        resp = requests.post(url, data=data, **kwargs)
        if not resp.ok:
            raise ConnectionError('Http response error. '
                                  'Status = {}. '.format(resp.status_code) +
                                  'Url = "{}". '.format(url) +
                                  'POST data: {}'.format(data))
        return resp


class _SMSResponse(object):

    def __init__(self, conn, status, description):
        self._connection = conn
        self._status = status
        self._description = description

        # cached information
        self._details = None
        self._delivery_status = None

    @property
    def ok(self):
        """Check is sms sending response is ok."""
        return self.status == 0

    @property
    def is_delivered(self):
        """Check is sms delivered to reciever."""
        raise NotImplementedError("FIXME")

    @property
    def details(self):
        """Get detailed information about sended sms."""
        raise NotImplementedError("FIXME")

    @property
    def delivery_status(self):
        """Check sms delivery status."""
        raise NotImplementedError("FIXME")

    @property
    def status(self):
        return self._status

    @property
    def description(self):
        return self._description

