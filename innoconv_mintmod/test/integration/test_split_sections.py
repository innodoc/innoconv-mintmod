# pylint: disable=missing-docstring,too-many-locals

import unittest
import os
import json
import tempfile
from innoconv_mintmod.test.utils import get_doc_from_markup


TEX_CODE = r"""
\MSection{1}
\MLabel{LABEL_1}

\begin{MSectionStart}
Einführungstext-für-header-1.
\end{MSectionStart}

\MSubsection{1-1}
\MLabel{LABEL_1_1}

\begin{MIntro}
\MLabel{LABEL_1_1_1}
MIntro-text-hier.
\end{MIntro}

\MSubsection{1-2}
\MLabel{LABEL_1_2}

subsection-text-hier.

\MSubsubsection{1-2-1}
\MLabel{LABEL_1_2_1}

subsubsection-text-hier.
"""


class TestSplitSections(unittest.TestCase):
    def test_split_sections(self):
        """test postflight split_sections"""
        langs = (("de", "Einführung"), ("en", "Introduction"))
        for lang in langs:
            with self.subTest(lang=lang[0]):
                lang_code, intro_title = lang
                with tempfile.TemporaryDirectory() as tmpdir:
                    pandoc_output = os.path.join(tmpdir, "output.json")
                    get_doc_from_markup(
                        TEX_CODE,
                        style="innoconv-generate-innodoc",
                        output=pandoc_output,
                        lang=lang_code,
                    )

                    toc_output = os.path.join(tmpdir, lang_code, "toc.json")
                    with open(toc_output, "r") as toc_file:
                        toc = json.load(toc_file)

                        sec_1 = toc[0]
                        self.assertEqual(sec_1["id"], "000-LABEL_1")
                        self.assertEqual(sec_1["title"][0]["c"], "1")

                        sec_1_1 = sec_1["children"][0]
                        self.assertEqual(sec_1_1["id"], "000-LABEL_1_1")
                        self.assertEqual(sec_1_1["title"][0]["c"], "1-1")

                        sec_1_1_1 = sec_1_1["children"][0]
                        self.assertEqual(sec_1_1_1["id"], "000-LABEL_1_1_1")
                        self.assertEqual(sec_1_1_1["title"][0]["c"], intro_title)

                        sec_1_2 = sec_1["children"][1]
                        self.assertEqual(sec_1_2["id"], "001-LABEL_1_2")
                        self.assertEqual(sec_1_2["title"][0]["c"], "1-2")

                        # \MSubsubsection (level 4) must not generate section
                        self.assertNotIn("children", sec_1_2)
