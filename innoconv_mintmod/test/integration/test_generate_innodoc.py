# pylint: disable=missing-docstring

import unittest
import os
import tempfile
from innoconv_mintmod.runner import InnoconvRunner

TEX_CODE = r"""
\MSection{1}
\MLabel{LABEL_1}

\begin{MSectionStart}
Einführungstext-für-header-1.

\MRef{infolabel}
\MSRef{LABEL_1_1_1}{Intro}
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

\begin{MInfo}
  \MLabel{infolabel}
  subsubsection-text-hier .
\end{MInfo}
"""


class TestGenerateInnodoc(unittest.TestCase):
    def test_generate_innodoc(self):
        """Test postflight generate_innodoc.py link processing."""
        lang = "en"
        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = os.path.join(tmpdir, "source", lang)
            source_lang_dir = os.path.join(source_dir, lang)
            output_dir = os.path.join(tmpdir, "output")
            output_dir_lang = os.path.join(output_dir, lang)
            os.makedirs(source_lang_dir)
            with open(
                os.path.join(source_lang_dir, "index.tex"), "w+"
            ) as file:
                file.write(TEX_CODE)
            InnoconvRunner(
                source_dir,
                output_dir,
                lang,
                ignore_exercises=False,
                remove_exercises=False,
                generate_innodoc=True,
                input_format="latex+raw_tex",
                output_format="json",
                generate_innodoc_markdown=True,
            ).run()
            with open(os.path.join(output_dir_lang, "content.md")) as file:
                content = file.read()
                links = (
                    "[](/000-LABEL_1/001-LABEL_1_2/000-LABEL_1_2_1#infolabel)",
                    "[Intro](/000-LABEL_1/000-LABEL_1_1/000-LABEL_1_1_1)",
                )
                for link in links:
                    self.assertIn(link, content)
