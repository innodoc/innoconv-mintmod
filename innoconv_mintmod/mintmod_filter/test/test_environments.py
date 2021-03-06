# pylint: disable=missing-docstring,invalid-name

import unittest
import panflute as pf
from innoconv_mintmod.constants import ELEMENT_CLASSES
from innoconv_mintmod.mintmod_filter.environments import Environments


class TestMsectionStart(unittest.TestCase):
    def setUp(self):
        self.doc = pf.Doc(metadata={"lang": "en"})
        self.environments = Environments()
        self.elem_content = r"""
        \begin{MSectionStart}
            Lorem ipsum
        \end{MSectionStart}"""
        self.doc.content.extend([pf.RawBlock(self.elem_content, format="latex")])
        self.elem = self.doc.content[0]  # this sets up elem.parent

    def test_msectionstart(self):
        """Should handle MSectionStart"""

        ret = self.environments.handle_msectionstart("Lorem ipsum", [], self.elem)[0]

        self.assertIsInstance(ret, pf.Para)
        self.assertIsInstance(ret.content[0], pf.Str)
        self.assertEqual(ret.content[0].text, "Lorem")
        self.assertIsInstance(ret.content[1], pf.Space)
        self.assertIsInstance(ret.content[2], pf.Str)
        self.assertEqual(ret.content[2].text, "ipsum")


class TestMxContent(unittest.TestCase):
    def setUp(self):
        self.doc = pf.Doc(metadata={"lang": "en"})
        self.environments = Environments()
        self.elem_content = r"""
        \begin{MXContent}{Nice title}{Short title}{STD}
            Lorem ipsum
        \end{MXContent}"""
        self.doc.content.extend([pf.RawBlock(self.elem_content, format="latex")])
        self.elem = self.doc.content[0]  # this sets up elem.parent

    def test_mxcontent(self):
        """Should handle MXContent"""
        ret = self.environments.handle_mxcontent(
            "Lorem ipsum", ["Nice title", "Short title", "STD"], self.elem
        )

        header = ret[0]
        self.assertIsInstance(header, pf.Header)
        self.assertEqual(pf.stringify(header), "Nice title")

        para = ret[1]
        self.assertIsInstance(para.content[0], pf.Str)
        self.assertIsInstance(para.content[1], pf.Space)
        self.assertIsInstance(para.content[2], pf.Str)
        self.assertEqual(para.content[0].text, "Lorem")
        self.assertEqual(para.content[2].text, "ipsum")


class TestBoxesWithoutTitle(unittest.TestCase):
    def setUp(self):
        self.doc = pf.Doc(metadata={"lang": "en"})
        self.environments = Environments()

    def test_handle_mexercise(self):
        """MExercise"""
        self._test_content_box(
            self.environments.handle_mexercise, ELEMENT_CLASSES["MEXERCISE"]
        )

    def test_handle_minfo(self):
        """MInfo"""
        self._test_content_box(self.environments.handle_minfo, ELEMENT_CLASSES["MINFO"])

    def test_handle_mexperiment(self):
        """MExperiment"""
        self._test_content_box(
            self.environments.handle_mexperiment,
            ELEMENT_CLASSES["MEXPERIMENT"],
        )

    def test_handle_mexample(self):
        """MExample"""
        self._test_content_box(
            self.environments.handle_mexample, ELEMENT_CLASSES["MEXAMPLE"]
        )

    def test_handle_mhint(self):
        """MHint"""
        div = self._test_content_box(
            self.environments.handle_mhint,
            ELEMENT_CLASSES["MHINT"],
            [r"\iSolution"],
        )
        self.assertEqual(div.attributes["caption"], "Solution")

    def _test_content_box(self, handler, element_classes, env_args=None):
        # some latex content in the environment
        elem_content = r"""
            \begin{itemize}
                \item{item1}
                \item{item2}
            \end{itemize}
        """

        # should return a div with the given classes
        self.doc.content.extend([pf.RawBlock(elem_content, format="latex")])
        elem = self.doc.content[0]  # this sets up elem.parent
        div = handler(elem_content, env_args, elem)
        self.assertIsInstance(div, pf.Div)
        self.assertEqual(div.classes, element_classes)
        for cls in element_classes:
            with self.subTest(cls=cls):
                self.assertIn(cls, div.classes)

        # and the content of the environment should be parsed correctly
        bullet_list = div.content[0]
        self.assertIsInstance(bullet_list, pf.BulletList)
        self.assertEqual(
            bullet_list.content[0].content[0].content[0].content[0].text,
            "item1",
        )
        return div


class TestMTest(unittest.TestCase):
    def setUp(self):
        self.environments = Environments()

    def test_handle_mtest(self):
        """MTest"""
        doc = pf.Doc(metadata={"lang": "en"})
        elem_content = r"""
        \begin{MTest}{Abschlusstest}
            Foo bar
        \end{MXContent}"""
        doc.content.extend([pf.RawBlock(elem_content, format="latex")])
        elem = doc.content[0]  # this sets up elem.parent

        ret = self.environments.handle_mtest("Foo bar", ["Abschlusstest"], elem)

        self.assertEqual(len(ret), 2)

        header = ret[0]
        self.assertIsInstance(header, pf.Header)
        self.assertEqual(pf.stringify(header), "Abschlusstest")

        para = ret[1]
        self.assertIsInstance(para.content[0], pf.Str)
        self.assertEqual(para.content[0].text, "Foo")
        self.assertIsInstance(para.content[1], pf.Space)
        self.assertIsInstance(para.content[2], pf.Str)
        self.assertEqual(para.content[2].text, "bar")

    def test_handle_mtest_section_title(self):
        """MTest"""
        doc = pf.Doc(metadata={"lang": "en"})
        elem_content = r"""
        \begin{MTest}{Abschlusstest Kapitel \arabic{section}}
            Foo bar
        \end{MXContent}"""
        doc.content.extend([pf.RawBlock(elem_content, format="latex")])
        elem = doc.content[0]  # this sets up elem.parent

        ret = self.environments.handle_mtest(
            "Foo bar", [r"Abschlusstest Kapitel \arabic{section}"], elem
        )

        self.assertEqual(len(ret), 2)

        header = ret[0]
        self.assertIsInstance(header, pf.Header)
        self.assertEqual(pf.stringify(header), "Abschlusstest")

        para = ret[1]
        self.assertIsInstance(para.content[0], pf.Str)
        self.assertEqual(para.content[0].text, "Foo")
        self.assertIsInstance(para.content[1], pf.Space)
        self.assertIsInstance(para.content[2], pf.Str)
        self.assertEqual(para.content[2].text, "bar")


class TestMXInfo(unittest.TestCase):
    def setUp(self):
        self.environments = Environments()

    def test_handle_mxinfo(self):
        """MXInfo"""
        doc = pf.Doc(metadata={"lang": "en"})
        elem_content = r"""
        \begin{MXInfo}{Ableitung}
        Foo bar
        \end{MXInfo}
        """
        doc.content.extend([pf.RawBlock(elem_content, format="latex")])
        elem = doc.content[0]  # this sets up elem.parent
        ret = self.environments.handle_mxinfo("Foo bar", ["Ableitung"], elem)

        self.assertIsInstance(ret, pf.Div)

        header = ret.content[0]
        self.assertIsInstance(header, pf.Header)
        self.assertEqual(pf.stringify(header), "Ableitung")

        para = ret.content[1]
        self.assertIsInstance(para.content[0], pf.Str)
        self.assertEqual(para.content[0].text, "Foo")
        self.assertIsInstance(para.content[1], pf.Space)
        self.assertIsInstance(para.content[2], pf.Str)
        self.assertEqual(para.content[2].text, "bar")

    def test_handle_mxinfo_math_title(self):
        """MXInfo with Math in title"""
        doc = pf.Doc(metadata={"lang": "en"})
        elem_content = r"""
        \begin{MXInfo}{Ableitung $x^n$}
        Foo bar
        \end{MXInfo}
        """
        doc.content.extend([pf.RawBlock(elem_content, format="latex")])
        elem = doc.content[0]  # this sets up elem.parent
        ret = self.environments.handle_mxinfo("Foo bar", ["Ableitung $x^n$"], elem)

        self.assertIsInstance(ret, pf.Div)

        header = ret.content[0]
        self.assertIsInstance(header, pf.Header)
        self.assertIsInstance(header.content[0], pf.Str)
        self.assertEqual(header.content[0].text, "Ableitung")
        self.assertIsInstance(header.content[1], pf.Space)
        self.assertIsInstance(header.content[2], pf.Math)
        self.assertEqual(header.content[2].text, "x^n")
        self.assertEqual(header.content[2].format, "InlineMath")

        para = ret.content[1]
        self.assertIsInstance(para.content[0], pf.Str)
        self.assertEqual(para.content[0].text, "Foo")
        self.assertIsInstance(para.content[1], pf.Space)
        self.assertIsInstance(para.content[2], pf.Str)
        self.assertEqual(para.content[2].text, "bar")


class TestHtml(unittest.TestCase):
    def setUp(self):
        self.environments = Environments()

    def test_handle_html(self):
        """html"""
        doc = pf.Doc(metadata={"lang": "en"})
        html = r"""<p>
        <h3 class="start">Suitable browsers</h3>
        The following browsers can be used for the course: Firefox, Internet
        Explorer, Chrome, Safari, Opera.<br />
        Some other browsers have difficulties rendering our unit pages
        correctly.
        <br />
        We recommend using only the fully updated latest versions of these
        browsers. In particular, the course cannot be completed with obsolete
        browsers such as Internet Explorer 8 or earlier.
        </p>"""
        elem_content = r"\\begin{{html}}\n{}\n\\end{{html}}" "".format(html)
        doc.content.extend([pf.RawBlock(elem_content, format="latex")])
        elem = doc.content[0]  # this sets up elem.parent
        ret = self.environments.handle_html(html, [], elem)
        header = ret[0]
        self.assertIsInstance(header, pf.Header)
        self.assertEqual(header.content[0].text, "Suitable")
        self.assertEqual(header.content[2].text, "browsers")
        para = ret[1]
        self.assertIsInstance(para, pf.Para)
        self.assertEqual(len(para.content), 107)
        self.assertEqual(para.content[106].text, "earlier.")
