#!/usr/bin/env python

import bytehand

import unittest
import requests
import urlparse
import json


class TestCaseWithPatchedRequests(unittest.TestCase):
    """Monkey-patch requests.get and requests.post functions for tests
    """
    def setUp(self):
        self.requests_request = requests.request
        ok_response = requests.Response()
        ok_response.status_code = 200
        ok_response._content = '[{"status": "0", "description": "4242424242"}]'

        self.last_url = None
        self.post_data = None

        def patched_request(mehtod, url, **kwargs):
            self.last_url = url
            self.post_data = kwargs.get('data')
            return ok_response
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


if __name__ == '__main__':
    unittest.main()
