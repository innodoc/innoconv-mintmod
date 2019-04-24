# pylint: disable=missing-docstring,invalid-name

import unittest
import panflute as pf

from innoconv_mintmod.mintmod_filter.elements import Exercise


class TestElement(unittest.TestCase):
    def test_element(self):
        ex = Exercise(
            ["correct answer", "ID_000"],
            mintmod_class="MLCheckbox",
            oktypes=pf.Inline,
            points="12",
        )
        self.assertIsInstance(ex, pf.Span)
        self.assertIn("exercise", ex.classes)
        self.assertIn("checkbox", ex.classes)
        self.assertEqual("correct answer", ex.attributes["solution"])
        self.assertNotIn("uxid", ex.attributes)
        self.assertEqual(ex.identifier, "ID_000")
