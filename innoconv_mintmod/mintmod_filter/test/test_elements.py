# pylint: disable=missing-docstring,invalid-name

import unittest
import panflute as pf

from innoconv_mintmod.mintmod_filter.elements import Question


class TestQuestion(unittest.TestCase):
    def test_question(self):
        ex = Question(
            ["correct answer", "ID_000"],
            mintmod_class="MLCheckbox",
            oktypes=pf.Inline,
            points="12",
        )
        self.assertIsInstance(ex, pf.Span)
        self.assertIn("question", ex.classes)
        self.assertIn("checkbox", ex.classes)
        self.assertEqual("correct answer", ex.attributes["solution"])
        self.assertNotIn("uxid", ex.attributes)
        self.assertEqual(ex.identifier, "ID_000")
