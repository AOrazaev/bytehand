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
        qargs = dict(id=self.userid, key=self.key, message=msgid)
        resp = self._get_request('details', qargs=qargs, verify=False)
        return resp.json()

    def balance(self):
        """:returns: float, how much money in rubles on your account."""
        qargs = dict(id=self.userid, key=self.key)
        resp = self._get_request('balance', qargs=qargs, verify=False)
        self._check_status(resp)
        return resp.json()['description']

    def signatures(self, state=None):
        """Send `signatures` request to bytehand api.

        :param state: str one of ('NEW', 'ACCEPTED', 'REJECTED'),
        case insensative.

        :returns: list of signatures in next format:

            {
                "id": <SIGNATURE_ID>,
                "text": <SIGNATURE_TEXT>,
                "description: <SIGNATURE_DESCRIPTION>,
                "created_at": <DATE_WHEN_CREATED>,
                "state": <SIGNATURE_STATE>
            }

        `<SIGNATURE_ID>`
            internal signature id.
        `<SIGNATURE_TEXT>`
            text of signature
        `<SIGNATURE_DESCRIPTION>`
            description you set when create signature.
        `<DATE_WHEN_CREATED>`
            when you create signature
        `<SIGNATURE_STATE>`
            one of ('NEW', 'ACCEPTED', 'REJECTED'):
            - 'ACCEPTED': You can use this signature to send sms.
            - 'NEW': You can't use this signature. It wasn't
              checked by bytehand moderator.
            - 'REJECTED': You can't use this signature. It was
              checked by bytehand moderator and rejected.
        """
        if state is not None and \
            state.upper() not in ('NEW', 'ACCEPTED', 'REJECTED'):
            raise ValueError('Bad `state` value: "{}"'.format(state))
        qargs = dict(id=self.userid, key=self.key)
        qargs.update(
            {'state': state.upper()} if state is not None else {}
        )
        resp = self._get_request('signatures', qargs=qargs, verify=False)
        return resp.json()

    def signature(self, signature):
        """:returns: dict, detailed information about given signature.

        :param signature: get details for this siganture.

        :raises LookupError: if no given signature in signature list.

        :see: signature dict format in `help(bytehand.signatures)`
        """
        for sign_details in self.signatures():
            if sign_details['text'] == signature:
                return sign_details
        raise LookupError('Can\'t find given signature {}'.format(signature) +
                          ' in signature list.')

    def new_signature(self, signature, description):
        """Send new signature to moderation.

        :param signature: signature text
        :param description: descriptions for moderator
        """
        qargs = dict(id=self.userid, key=self.key, text=signature)
        resp = self._post_request('signature', qargs=qargs,
                                  data={'description': description},
                                  verify=False)
        self._check_status(resp)

    def delete_signature(self, signature):
        """Delete given @signature from your signature list.
        If given @signature is not represented in your signature list,
        when nothing happens.

        :param signature: signature text
        """
        try:
            signature = self.signature(signature)
        except LookupError:
            return
        qargs = dict(id=self.userid, key=self.key, signature=signature['id'])
        resp = self._delete_request('signature', qargs=qargs, verify=False)
        self._check_status(resp)

    def _check_status(self, resp):
        resp = resp.json()
        if int(resp['status']) != 0:
            raise ConnectionError(
                'Nonzero status: {0}\n'.format(resp['status']) +
                'Description: {0}'.format(resp['description'])
            )

    def _request(self, method, request_type, qargs={}, data=None, **kwargs):
        query = urllib.urlencode(qargs)
        url = self._API_URL._replace(path=request_type, query=query).geturl()
        resp = requests.request(method, url, data=data, **kwargs)
        if not resp.ok:
            raise ConnectionError('Http response error. '
                                  'Status = {}. '.format(resp.status_code) +
                                  'Url = "{}". '.format(url) +
                                  'POST data: {}'.format(data))
        return resp

    def _delete_request(self, request_type, qargs, **kwargs):
        return self._request('delete', request_type, qargs, **kwargs)

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
        self._details = None

    @property
    def ok(self):
        """Check is sms sending response is ok."""
        return self.status == 0

    def _get_details(self):
        if self._details is None \
            or self._details['description'] != 'DELIVERED':
            self._details = self._connection.details(self._description)
            if self._details['status'] != 0:
                raise ConnectionError('Can\'t get details. '
                                      'Nonzero status of bytehand response:' +
                                      self._details['description'])

    @property
    def is_delivered(self):
        """Check is sms delivered to reciever."""
        return self.details['description'] == 'DELIVERED'

    @property
    def details(self):
        """Get detailed information about sended sms."""
        if not self.ok:
            raise ConnectionError('Cannot get details of message from '
                                  'response with error')
        self._get_details()
        return self._details

    @property
    def delivery_status(self):
        """Check sms delivery status."""
        return self.details['description']

    @property
    def status(self):
        return self._status

    @property
    def description(self):
        return self._description
