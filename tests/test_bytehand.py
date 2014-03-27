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
        self.requests_get = requests.get
        self.requests_post = requests.post
        ok_response = requests.Response()
        ok_response.status_code = 200
        ok_response._content = '[{"status": "0", "description": "4242424242"}]'

        self.last_request = None
        def patched_get(url, **kwargs):
            self.last_request = (url, kwargs)
            return ok_response
        requests.get = patched_get

        self.post_url = None
        self.post_data = None
        def patched_post(url, data=None, **kwargs):
            self.post_url = url
            self.post_data = data
            return ok_response
        requests.post = patched_post


    def tearDown(self):
        requests.get = self.requests_get
        requests.post = self.requests_post
        del self.requests_get
        del self.last_request
        del self.requests_post
        del self.post_url
        del self.post_data


class TestBytehandSendSms(TestCaseWithPatchedRequests):

    def test_send_sms(self):
        assert self.last_request == None
        bytehand.send_sms(7771234567, 'Hello, Kate!', 'Patric',
                          1342, 'Password')
        expected_url = urlparse.urljoin(
            bytehand.API_URL,
            'send?id=1342&key=Password&to=7771234567&'
            'from=Patric&text=Hello%2C%20Kate%21')
        self.assertEqual(self.last_request, (expected_url, {}))

    def test_send_sms_raises(self):
        assert self.last_request == None

        send = lambda: bytehand.send_sms('bad_phone_number',
                                         'Hello, Kate!',
                                         'Patric', 1242, 'Pa$$w0rd')
        self.assertRaises(TypeError, send)
        self.assertEqual(self.last_request, None)

        send = lambda: bytehand.send_sms(7771234567, '', 'Patric',
                                         1242, 'Pa$$w0rd')
        self.assertRaises(TypeError, send)
        self.assertEqual(self.last_request, None)

        send = lambda: bytehand.send_sms(7771234567, 'Hello, Kate',
                                         '', 1342, 'Pa$$w0rd')
        self.assertRaises(TypeError, send)
        self.assertEqual(self.last_request, None)

        send = lambda: bytehand.send_sms(7771234567, 'Hello, Kate',
                                         'Patric', 'id1342', 'Pa$$w0rd')
        self.assertRaises(TypeError, send)
        self.assertEqual(self.last_request, None)


class TestBytehandConnection(TestCaseWithPatchedRequests):

    def test_connection(self):
        conn = bytehand.Connection(userid=1342, key='MYKEY4321')
        msg = {"to": "77712345678",
               "from": "Mom",
               "text": "Don't be late!"}

        status = conn.send(signature=msg['from'], **msg)
        self.assertEqual(
            self.post_url,
            urlparse.urljoin(bytehand.API_URL,
                             'send_multi?id=1342&key=MYKEY4321')
        )
        expected_data = json.dumps([msg])
        self.assertEqual(self.post_data, expected_data)


if __name__ == '__main__':
    unittest.main()
