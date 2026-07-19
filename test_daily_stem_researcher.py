#!/usr/bin/env python3
import unittest
from daily_stem_researcher import clean_text, match_keywords


class TestDailyStemResearcher(unittest.TestCase):

    def test_clean_text(self):
        self.assertEqual(clean_text("  Hello   World  "), "Hello World")
        self.assertEqual(clean_text("\nHello\nWorld\t"), "Hello World")
        self.assertEqual(clean_text(""), "")
        self.assertEqual(clean_text(None), "")

    def test_match_keywords(self):
        # Match title
        matched, kw = match_keywords("A study of Quantum Mechanics", "Abstract text here", ["quantum"])
        self.assertTrue(matched)
        self.assertEqual(kw, "quantum")

        # Match summary
        matched, kw = match_keywords("Regular title", "This paper covers differential equations.", ["differential"])
        self.assertTrue(matched)
        self.assertEqual(kw, "differential")

        # No match
        matched, kw = match_keywords("Regular title", "Abstract text here", ["quantum", "differential"])
        self.assertFalse(matched)
        self.assertIsNone(kw)


if __name__ == "__main__":
    unittest.main()
