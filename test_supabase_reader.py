import unittest
from unittest.mock import patch
from supabase_reader import fetch_workout, validate_uuid

A='11111111-1111-4111-8111-111111111111'
B='22222222-2222-4222-8222-222222222222'

class Tests(unittest.TestCase):
    def test_bad_uuid(self):
        with self.assertRaises(ValueError): validate_uuid('eq.123&limit=999')
    def test_https_required(self):
        with self.assertRaises(ValueError): fetch_workout('http://example.com','key','jwt',A,B)
    def test_missing_credentials(self):
        with self.assertRaises(ValueError): fetch_workout('https://example.com','','',A,B)
    def test_no_write_method(self):
        import inspect
        source=inspect.getsource(fetch_workout)
        self.assertIn("method='GET'",source)
        self.assertNotIn("method='POST'",source)

if __name__=='__main__': unittest.main()
