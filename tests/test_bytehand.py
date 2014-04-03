#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bytehand

import unittest
import urllib
import requests
import urlparse
import json


class TestCaseWithPatchedRequests(unittest.TestCase):
    """Monkey-patch requests.get and requests.post functions for tests
    """

    ok_response = requests.Response()
    ok_response.status_code = 200
    ok_response._content = (
        '[{"status": "0", "description": "4242424242"}]'
    )

    balance_response = requests.Response()
    balance_response.status_code = 200
    balance_response._content = (
        '{"status": "0", "description": "100500.00"}'
    )

    signature_response = requests.Response()
    signature_response.status_code = 200
    signature_response._content = (
        '[{"id": 42, "description": "Test signature",'
        '  "text": "Peter", "created_at": "2042-12-31",'
        '  "state": "ACCEPTED"}]'
    )

    new_signature_response = requests.Response()
    new_signature_response.status_code = 200
    new_signature_response._content = (
        '{"status": "0", "description": "42"}'
    )

    def setUp(self):
        self.requests_request = requests.request

        self.last_url = None
        self.request_method = None
        self.post_data = None
        self.request_urls = []

        def patched_request(method, url, **kwargs):
            self.last_url = url
            self.request_urls.append(url)
            self.post_data = kwargs.get('data')
            self.request_method = method
            if urlparse.urlparse(url).path.endswith('balance'):
                return self.balance_response
            elif urlparse.urlparse(url).path.endswith('signatures'):
                return self.signature_response
            elif urlparse.urlparse(url).path.endswith('signature'):
                return self.new_signature_response
            return self.ok_response
        requests.request = patched_request

    def tearDown(self):
        requests.request = self.requests_request
        del self.requests_request
        del self.last_url
        del self.post_data


class TestBytehandSendSms(TestCaseWithPatchedRequests):

    def test_send_sms(self):
        assert self.last_url == None
        bytehand.send_sms(7771234567, 'Patric', 'Hello, Kate!',
                          1342, 'Password')
        expected_url = urlparse.urljoin(bytehand.API_URL,
                                        'send_multi?id=1342&key=Password')
        self.assertEqual(self.last_url, expected_url)
        self.assertEqual(
            json.dumps([{'to': '7771234567', 'from': 'Patric',
                         'text': 'Hello, Kate!'}]),
            self.post_data
        )

    def test_send_sms_raises(self):
        assert self.last_url == None

        send = lambda: bytehand.send_sms('bad_phone_number',
                                         'Hello, Kate!',
                                         'Patric', 1242, 'Pa$$w0rd')
        self.assertRaises(TypeError, send)
        self.assertEqual(self.last_url, None)

        send = lambda: bytehand.send_sms(7771234567, '', 'Patric',
                                         1242, 'Pa$$w0rd')
        self.assertRaises(TypeError, send)
        self.assertEqual(self.last_url, None)

        send = lambda: bytehand.send_sms(7771234567, 'Hello, Kate',
                                         '', 1342, 'Pa$$w0rd')
        self.assertRaises(TypeError, send)
        self.assertEqual(self.last_url, None)

        send = lambda: bytehand.send_sms(7771234567, 'Hello, Kate',
                                         'Patric', 'id1342', 'Pa$$w0rd')
        self.assertRaises(TypeError, send)
        self.assertEqual(self.last_url, None)


class TestBytehandConnection(TestCaseWithPatchedRequests):

    def test_connection(self):
        conn = bytehand.Connection(userid=1342, key='MYKEY4321')
        msg = {"to": "77712345678",
               "from": "Mom",
               "text": "Don't be late!"}

        status = conn.send(to=msg['to'], signature=msg['from'],
                           text=msg['text'])
        self.assertEqual(
            self.last_url,
            urlparse.urljoin(bytehand.API_URL,
                             'send_multi?id=1342&key=MYKEY4321')
        )
        expected_data = json.dumps([msg])
        self.assertEqual(self.post_data, expected_data)

    def test_send_multi(self):
        conn = bytehand.Connection(userid=1342, key='MYKEY4321')
        msgs = [{"to": "777712345678", "from": "Mom",
                 "text": "Don't be late!"},
                {"to": "749512345678", "from": "Dad",
                 "text": "Don't listen your mother."}]
        status = conn.send_multi(msgs)
        self.assertEqual(
            self.last_url,
            urlparse.urljoin(bytehand.API_URL,
                             'send_multi?id=1342&key=MYKEY4321')
        )
        expected_data = json.dumps(msgs)
        self.assertEqual(self.post_data, expected_data)

    def test_details(self):
        conn = bytehand.Connection(userid=1342, key='MYKEY4321')
        details = conn.details('12345')
        parsed_url = urlparse.urlparse(self.last_url)
        self.assertEqual(
            parsed_url._replace(query='').geturl(),
            urlparse.urljoin(bytehand.API_URL, 'details')
        )
        self.assertEqual(
            dict(kv.split('=') for kv in parsed_url.query.split('&')),
            dict(id='1342', key='MYKEY4321', message='12345')
        )

    def test_balance(self):
        conn = bytehand.Connection(userid=1342, key='MYKEY4321')
        balance = conn.balance()
        self.assertEqual(balance, '100500.00')

        parsed_url = urlparse.urlparse(self.last_url)
        self.assertEqual(
            parsed_url._replace(query='').geturl(),
            urlparse.urljoin(bytehand.API_URL, 'balance')
        )
        self.assertEqual(
            dict(kv.split('=') for kv in parsed_url.query.split('&')),
            dict(id='1342', key='MYKEY4321')
        )

    def test_signatures(self):
        conn = bytehand.Connection(userid=1342, key='MYKEY4321')
        self.assertRaises(
            ValueError,
            lambda: conn.signatures(state='unknown_state')
        )

        def check_signature_url(state=None):
            parsed_url = urlparse.urlparse(self.last_url)
            self.assertEqual(
                parsed_url._replace(query='').geturl(),
                urlparse.urljoin(bytehand.API_URL, 'signatures')
            )
            expect = dict(id='1342', key='MYKEY4321')
            expect.update({'state': state} if state is not None else {})
            self.assertEqual(
                dict(kv.split('=') for kv in parsed_url.query.split('&')),
                expect
            )
        conn.signatures(state='new')
        check_signature_url(state='NEW')

        conn.signatures(state='accepted')
        check_signature_url(state='ACCEPTED')

        conn.signatures(state='REJECTED')
        check_signature_url(state='REJECTED')

        conn.signatures()
        check_signature_url()

    def test_signature(self):
        conn = bytehand.Connection(userid=1342, key='MYKEY4321')
        result = conn.signature('Peter')
        parsed_url = urlparse.urlparse(self.last_url)
        self.assertEqual(
            parsed_url._replace(query='').geturl(),
            urlparse.urljoin(bytehand.API_URL, 'signatures')
        )
        self.assertEqual(
            dict(kv.split('=') for kv in parsed_url.query.split('&')),
            dict(id='1342', key='MYKEY4321')
        )
        self.assertEqual(result, self.signature_response.json()[0])

        self.assertRaises(
            LookupError,
            lambda: conn.signature('NoSuchSignature')
        )

    def test_new_signature(self):
        conn = bytehand.Connection(userid=1342, key='MYKEY4321')
        test_sign = 'test'
        test_description = 'юникод: некоторая тестовая подпись'

        conn.new_signature(test_sign, test_description)

        self.assertEqual(self.request_method, 'post')

        parsed_url = urlparse.urlparse(self.last_url)
        self.assertEqual(
            parsed_url._replace(query='').geturl(),
            urlparse.urljoin(bytehand.API_URL, 'signature')
        )
        self.assertEqual(
            parsed_url.query,
            urllib.urlencode(dict(id='1342', key='MYKEY4321',
                             text=test_sign, description=test_description))
        )

    def test_delete_signature(self):
        conn = bytehand.Connection(userid=1342, key='MYKEY4321')

        conn.delete_signature('Peter')
        self.assertEqual(self.request_method, 'delete')
        parsed_url = urlparse.urlparse(self.last_url)
        self.assertEqual(
            parsed_url._replace(query='').geturl(),
            urlparse.urljoin(bytehand.API_URL, 'signature')
        )
        self.assertEqual(
            dict(kv.split('=') for kv in parsed_url.query.split('&')),
            dict(id='1342', key='MYKEY4321', signature='42')
        )


if __name__ == '__main__':
    unittest.main()
