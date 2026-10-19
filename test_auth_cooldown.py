import unittest
from unittest.mock import patch
from fastapi import HTTPException
import api
from garmin_auth_errors import classify_login_error

class AuthCooldownTests(unittest.TestCase):
    def setUp(self):
        api._garmin_cooldown_until = 0.0
    def tearDown(self):
        api._garmin_cooldown_until = 0.0
    def test_429_classification(self):
        self.assertEqual(classify_login_error(Exception("Mobile login returned 429")), "rate_limited")
    def test_cloudflare_classification(self):
        self.assertEqual(classify_login_error(Exception("HTTP 403 (Cloudflare bot challenge)")), "rate_limited")
    def test_no_false_credential_failure(self):
        self.assertEqual(classify_login_error(Exception("Connection timed out")), "uncertain")
    def test_cooldown_after_rejection(self):
        with self.assertRaises(HTTPException) as caught:
            api._garmin_login_failure(Exception("HTTP 403 Cloudflare bot challenge"))
        self.assertEqual(caught.exception.status_code, 429)
        with self.assertRaises(HTTPException) as second:
            api._guard_garmin_login()
        self.assertEqual(second.exception.status_code, 429)
        self.assertGreater(int(second.exception.headers["Retry-After"]), 0)

if __name__ == "__main__": unittest.main()
