import unittest
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.config import TOMTOM_ACTIVE
from api.tomtom_client import _fetch

class TestTomTomClient(unittest.TestCase):
    def test_tomtom_disabled(self):
        self.assertFalse(TOMTOM_ACTIVE)

    def test_fetch_no_key_returns_none(self):
        if TOMTOM_ACTIVE:
            self.skipTest('TomTom active in environment; skip no-key behavior test')
        result = self._run_async(_fetch('/traffic/services/4/flowSegmentData/absolute/10/json', {'point': '12.97,77.59'}))
        self.assertIsNone(result)

    def _run_async(self, coro):
        import asyncio
        return asyncio.get_event_loop().run_until_complete(coro)

if __name__ == '__main__':
    unittest.main()
