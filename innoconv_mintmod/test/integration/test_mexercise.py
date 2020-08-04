# pylint: disable=missing-docstring

import unittest
import panflute as pf
from innoconv_mintmod.test.utils import get_doc_from_markup
from innoconv_mintmod.constants import DEFAULT_EXERCISE_POINTS


class TestInnoconvIntegrationMExercise(unittest.TestCase):
    def test_mexercise_with_msetpoints(self):
        r"""Test if exercises get points from \MSetPoints."""
        doc = get_doc_from_markup(
            r"""\MSection{Test caption}
        \MLabel{TEST_LABEL}
        \MSetSectionID{VBKM01} % wird fuer tikz-Dateien verwendet

        \begin{MExercise}
            \MDeclareSiteUXID{TEST_EXERCISE}
            Please choose...
            \MLCheckbox{0}{TX1}
            \MSetPoints{1}
            \MLCheckbox{0}{TX2}
            \MLCheckbox{1}{TX3}
        \end{MExercise}
        """
        )
        self.assertIsInstance(doc, pf.Doc)
        header = doc.content[0]
        self.assertIsInstance(header, pf.Header)
        self.assertEqual(header.content[0].text, "Test")
        self.assertEqual(header.content[2].text, "caption")
        self.assertEqual(header.identifier, "TEST_LABEL")
        exercise = doc.content[1]
        self.assertIsInstance(exercise, pf.Div)
        self.assertEqual(exercise.identifier, "TEST_EXERCISE")
        self.assertIn("exercise", exercise.classes)
        checkbox_1 = exercise.content[0].content[4]
        self.assertEqual(checkbox_1.attributes["points"], DEFAULT_EXERCISE_POINTS)
        checkbox_2 = exercise.content[0].content[7]
        self.assertEqual(checkbox_2.attributes["points"], "1")
        checkbox_3 = exercise.content[0].content[9]
        self.assertEqual(checkbox_3.attributes["points"], "1")
