#!/usr/bin/env python

import bytehand

import unittest
import requests
import urlparse


class TestBytehand(unittest.TestCase):

    def setUp(self):
        self.requests_get = requests.get

        self.last_request = None
        def patched_get(url, **kwargs):
            self.last_request = (url, kwargs)
        requests.get = patched_get

    def tearDown(self):
        requests.get = self.requests_get
        del self.requests_get

    def test_send_sms(self):
        assert self.last_request == None
        bytehand.send_sms(7771234567, 'Hello, Kate!', 'Patric',
                          1342, 'Pa$$w0rd')
        expected_url = urlparse.urljoin(
            bytehand.API_URL,
            'send?id=1342&key=Pa%24%24w0rd&to=7771234567&'
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

    def test_connection(self):
        raise NotImplementedError('FIXME')


if __name__ == '__main__':
    unittest.main()
