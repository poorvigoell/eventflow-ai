import unittest
import sys, os
import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.nlp_parser import parse_event_text

class TestNLPParser(unittest.TestCase):
    def test_parse_protest(self):
        text = "There is a massive political rally at Freedom Park tomorrow at 5pm for 4 hours"
        result = parse_event_text(text)
        self.assertEqual(result["event_type"], "protest")
        self.assertEqual(result["venue_name"], "Freedom Park")
        self.assertEqual(result["duration_hours"], 4.0)
        self.assertEqual(result["time"], "17:00")
        expected_date = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        self.assertEqual(result["date"], expected_date)

    def test_parse_construction(self):
        text = "Construction work on MG Road at 10am for 2.5 hours"
        result = parse_event_text(text)
        self.assertEqual(result["event_type"], "construction")
        self.assertEqual(result["venue_name"], "MG Road")
        self.assertEqual(result["duration_hours"], 2.5)
        self.assertEqual(result["time"], "10:00")
        self.assertEqual(result["date"], datetime.date.today().strftime("%Y-%m-%d"))

if __name__ == '__main__':
    unittest.main()
