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
        self.userid = userid
        self.key = key

    def send(self, to=None, signature=None, text=None):
        """Send sms message to @to from @signature with given @text.

        :note: Your @signature must be verified on bytehand.

        :param to: receiver phone number.
        :param signature: "from" field of sms message.
        :param text: message content.
        """
        msg = {'to': str(to),
               'from': str(signature),
               'text': text}
        return self.send_multi([msg])[0]

    def send_multi(self, msgs):
        """Send several sms messages from given @msgs list.

        :param msgs: list of dicts (messages) in format
                     {"to": <TO>, "from": <SIGNATURE>, "text": <CONTENT>}

        :note: Your @signature must be verified on bytehand.
        """
        data = json.dumps(msgs)
        headers = {'Content-Type': 'application/json;charset=UTF-8'}
        resp = self._post_request('send_multi', data=data, headers=headers,
                                  qargs=dict(id=self.userid, key=self.key),
                                  verify=False)
        return list(_SMSResponse.from_response(self, resp))

    def details(self, msgid):
        """Get detailed information about message.

        :param msgid: message id. It is specified as `description` of
        sms response status, if `status` of response is 0.

        :returns: next dict

            {
                "status": <STATUS>,
                "description": <DELIVERY>,
                "posted_at": <POSTED_AT>,
                "updated_at": <UPDEATED_AT>,
                "parts": <NUM_PARTS>,
                "cost": <COST>
            }

        where:
            `<STATUS>`
                status of request, always 0.
            `<DELIVERY>`
                one of ("NEW", "DELIVERED", "EXPIRED", "DELETED",
                "UNDELIVERABLE", "ACCEPTED", "UNKNOWN", "REJECTED")
            `<POSTED_AT>`
                sending message time. GMT+0. Format 'yyyy-MM-dd HH:mm:ss'
            `<UPDEATED_AT>`
                last status changed time. GMT+0. Format 'yyyy-MM-dd HH:mm:ss'
            `<NUM_PARTS>`
                number of parts in message.
            `<COST>`
                message cost in rubles.
        """
        headers = {'Content-Type': 'application/json;charset=UTF-8'}
        qargs = dict(id=self.userid, key=self.key, message=msgid)
        resp = self._post_request('details', headers=headers, qargs=qargs,
                                  verify=False)
        return resp.json()

    def _request(self, method, request_type, qargs={}, **kwargs):
        query = '&'.join('{}={}'.format(arg, urllib.quote(str(val)))
                         for arg, val in qargs.iteritems())
        url = self._API_URL._replace(path=request_type, query=query).geturl()
        resp = requests.request(method, url, **kwargs)
        if not resp.ok:
            raise ConnectionError('Http response error. '
                                  'Status = {}. '.format(resp.status_code) +
                                  'Url = "{}". '.format(url) +
                                  'POST data: {}'.format(data))
        return resp

    def _get_request(self, request_type, qargs, **kwargs):
        return self._request('get', request_type, qargs, **kwargs)

    def _post_request(self, request_type, qargs={}, **kwargs):
        return self._request('post', request_type, qargs, **kwargs)


class _SMSResponse(object):

    @staticmethod
    def from_response(conn, response):
        data = response.json()
        for resp in data:
            yield _SMSResponse(conn, resp['status'], resp['description'])

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
