"""This are unit tests for innoconv.utils"""

# pylint: disable=missing-docstring,invalid-name

import unittest
from mock import patch
import panflute as pf

from innoconv_mintmod.errors import ParseError
from innoconv_mintmod.utils import (
    parse_fragment,
    destringify,
    parse_cmd,
    parse_nested_args,
    remove_empty_paragraphs,
    remember,
    get_remembered,
    to_inline,
    extract_identifier,
    convert_simplification_code,
)
from innoconv_mintmod.test.utils import captured_output
from innoconv_mintmod.constants import INDEX_LABEL_PREFIX, SITE_UXID_PREFIX

CONTENT = r"""
\documentclass[12pt]{article}
\begin{document}

\section{Test heading}

Lorem ipsum dolor sit amet, consectetur adipiscing elit. In luctus
eget lorem ut tincidunt. Duis nunc quam, vehicula et molestie
consectetur, maximus nec sapien. In posuere venenatis fringilla. Sed
ac mi vehicula, blandit elit id, rutrum tellus. Praesent consectetur
lacinia quam, nec molestie neque ultricies eget. Donec eget facilisis
nisi. Suspendisse condimentum facilisis molestie. Donec vehicula dui
vel ligula laoreet porta.

\subsection{Another heading}

Aliquam sit amet lorem nec mauris venenatis volutpat quis et
mauris. Aenean nec ullamcorper orci, at euismod ipsum. Sed ac risus
tortor. Class aptent taciti sociosqu ad litora torquent per conubia
nostra, per inceptos himenaeos. Nullam tincidunt euismod felis, in
varius quam. Mauris lobortis elit mollis nisi imperdiet, at sagittis
libero elementum. Donec hendrerit ex libero, ut condimentum ligula
porttitor at. Pellentesque libero urna, egestas a semper in, auctor
vitae tellus. In quis viverra nibh.

\end{document}
"""


class TestParseFragment(unittest.TestCase):
    def test_parse_fragment(self):
        """parse_fragment() returns valid output if given test document"""
        doc = parse_fragment(CONTENT, "en")
        h_1 = doc[0]
        para_1 = doc[1]
        h_2 = doc[2]
        para_2 = doc[3]

        # test types
        type_tests = (
            (h_1, pf.Header),
            (h_1, pf.Header),
            (h_1.content[0], pf.Str),
            (h_1.content[1], pf.Space),
            (h_1.content[2], pf.Str),
            (para_1, pf.Para),
            (h_2, pf.Header),
            (para_1, pf.Para),
        )
        for elem in type_tests:
            with self.subTest(_type=type(elem[0])):
                self.assertIsInstance(elem[0], elem[1])

        # test content
        content_tests = (
            (h_1.content[0].text, "Test"),
            (h_1.content[2].text, "heading"),
            (len(para_1.content), 121),
            (h_2.content[0].text, "Another"),
            (h_2.content[2].text, "heading"),
            (len(para_2.content), 149),
        )
        for elem in content_tests:
            with self.subTest(value=elem[0]):
                self.assertEqual(elem[0], elem[1])

    def test_parse_fragment_fail(self):
        """if given broken document parse_fragment() raises RuntimeError and
        prints errors"""
        with captured_output() as out:
            with self.assertRaises(RuntimeError):
                parse_fragment(r"\begin{fooenv}bla", "en")
            err_out = out[1].getvalue()
        self.assertTrue("ERROR" in err_out)

    def test_parse_fragment_quiet(self):
        """parse_fragment() prints debug messages"""
        with captured_output() as out:
            parse_fragment(r"\section{foo} \unknownfoobar", "en")
            err_out = out[1].getvalue()
        self.assertTrue("Could not handle command unknownfoobar" in err_out)

    @patch("innoconv_mintmod.utils.log")
    def test_parse_fragment_log_is_called(self, log_mock):
        """parse_fragment() calls log function on warning"""
        parse_fragment(r"\unknowncommandfoobar", "en")
        self.assertTrue(log_mock.called)

    def test_parse_fragment_empty(self):
        """parse_fragment() returns empty list if given empty document"""
        ret = parse_fragment("", "en")
        self.assertEqual(len(ret), 0)

    @patch("innoconv_mintmod.utils.which", return_value=None)
    def test_parse_fragment_not_in_path(self, mock_func):
        # pylint: disable=unused-argument
        """parse_fragment() raises OSError if panzer not in PATH"""
        with self.assertRaises(OSError):
            parse_fragment("foo bar", "en")


class TestDestringify(unittest.TestCase):
    def test_regular(self):
        """Test destringify with a regular string"""
        string = "This is a  really\tnice    string."
        comp = [
            pf.Str("This"),
            pf.Space(),
            pf.Str("is"),
            pf.Space(),
            pf.Str("a"),
            pf.Space(),
            pf.Str("really"),
            pf.Space(),
            pf.Str("nice"),
            pf.Space(),
            pf.Str("string."),
        ]
        ret = destringify(string)
        self._compare_list(ret, comp)

    def test_empty(self):
        """Test destringify with an empty string"""
        string = ""
        ret = destringify(string)
        self.assertListEqual(ret, [])

    def test_empty_whitespace(self):
        """Test destringify with an whitespace string"""
        string = "   "
        ret = destringify(string)
        self.assertListEqual(ret, [])

    def test_one_word(self):
        """Test destringify with one word"""
        string = "foobar"
        ret = destringify(string)
        self._compare_list(ret, [pf.Str("foobar")])

    def test_whitespace(self):
        """Test destringify with leading and trailing whitespace"""
        string = "  foo bar  "
        comp = [pf.Str("foo"), pf.Space(), pf.Str("bar")]
        ret = destringify(string)
        self._compare_list(ret, comp)

    def _compare_list(self, l_1, l_2):
        for i, l_1_elem in enumerate(l_1):
            _type = type(l_2[i])
            with self.subTest(i=i):
                with self.subTest(_type=_type):
                    self.assertIsInstance(l_1_elem, _type)
                if _type == pf.Str:
                    with self.subTest(text=l_1_elem.text):
                        self.assertEqual(l_1_elem.text, l_2[i].text)


class TestParseCmd(unittest.TestCase):
    def test_parse_cmd_with_args(self):
        """Parse ``foobar`` command with arguments"""
        cmd_name, cmd_args = parse_cmd(r"\foobar{foo}{bar}{baz}")
        self.assertEqual(cmd_name, "foobar")
        self.assertEqual(cmd_args, ["foo", "bar", "baz"])

    def test_parse_cmd_without_args(self):
        """Parse ``foobar`` command without arguments"""
        cmd_name, cmd_args = parse_cmd(r"\foobar")
        self.assertEqual(cmd_name, "foobar")
        self.assertEqual(cmd_args, [])

    def test_parse_cmd_colon(self):
        """Parse ``:`` command"""
        cmd_name, cmd_args = parse_cmd(r"\:")
        self.assertEqual(cmd_name, ":")
        self.assertEqual(cmd_args, [])

    def test_parse_cmd_fail(self):
        """It should fail on invalid command"""
        with self.assertRaises(ParseError):
            parse_cmd("not-a-valid-command")

    def test_parse_cmd_nested(self):
        """It should parse nested commands"""
        cmd_name, cmd_args = parse_cmd(r"\foobar{word\bar{two}bbb}{baz}")
        self.assertEqual(cmd_name, "foobar")
        self.assertEqual(cmd_args, [r"word\bar{two}bbb", "baz"])

    def test_parse_cmd_mvector(self):
        r"""It should parse \MVector command"""
        cmd_name, cmd_args = parse_cmd(r"\MVector{2\\-\Mtfrac{5}{2}\\-2}")
        self.assertEqual(cmd_name, "MVector")
        self.assertEqual(cmd_args, [r"2\\-\Mtfrac{5}{2}\\-2"])


class TestParseNestedArgs(unittest.TestCase):
    def test_parse_nested_args_empty(self):
        """It should parse nested arguments: empty"""
        ret = parse_nested_args("")
        self.assertEqual(ret, ([], None))

    def test_parse_nested_args_simple(self):
        """It should parse nested arguments: simple"""
        ret = parse_nested_args("{bbb}{baz}{foo}")
        self.assertEqual(ret, (["bbb", "baz", "foo"], None))

    def test_parse_nested_args_1(self):
        """It should parse nested arguments: nested 1"""
        ret = parse_nested_args(r"{word\bar{two}bbb}{baz}")
        self.assertEqual(ret, ([r"word\bar{two}bbb", "baz"], None))

    def test_parse_nested_args_2(self):
        """It should parse nested arguments: nested 2"""
        ret = parse_nested_args(r"{cont}{}{\foo{\bla{\stop}}}{\baz{}{}{}}")
        self.assertEqual(ret, (["cont", "", r"\foo{\bla{\stop}}", r"\baz{}{}{}"], None))

    def test_parse_nested_args_rest(self):
        """It should parse nested arguments with rest"""
        ret = parse_nested_args(
            r"""{word\bar{two}bbb}{baz}
there is more
stuff here"""
        )
        rest = """
there is more
stuff here"""
        self.assertEqual(ret, ([r"word\bar{two}bbb", "baz"], rest))


class TestRemoveEmptyParagraphs(unittest.TestCase):
    def test_remove_empty_paragraphs(self):
        """It should remove empty paras in document"""
        doc = pf.Doc(
            pf.Para(pf.Str("Foo"), pf.Space(), pf.Str("Bar")),
            pf.Para(),
            pf.Para(pf.Str("Bar"), pf.Space(), pf.Str("Baz")),
        )
        remove_empty_paragraphs(doc)
        self.assertEqual(len(doc.content), 2)
        para1 = doc.content[0]
        self.assertEqual(para1.content[0].text, "Foo")
        self.assertEqual(para1.content[2].text, "Bar")
        para2 = doc.content[1]
        self.assertEqual(para2.content[0].text, "Bar")
        self.assertEqual(para2.content[2].text, "Baz")


class TestRemember(unittest.TestCase):
    def test_remember(self):
        """It should remember and forget."""
        doc = pf.Doc()

        self.assertIsNone(get_remembered(doc, "somekey"))

        header = pf.Header()
        remember(doc, "header", header)
        rememembered_el = get_remembered(doc, "header")
        self.assertEqual(rememembered_el, header)
        self.assertIsNone(get_remembered(doc, "header"))

        img = pf.Image()
        remember(doc, "img", img)
        rememembered_img = get_remembered(doc, "img")
        self.assertEqual(rememembered_img, img)
        self.assertIsNone(get_remembered(doc, "img"))


class TestToInline(unittest.TestCase):
    def test_to_inline(self):
        """It should convert different elements correctly to inline"""

        content1 = pf.Para(pf.Strong(pf.Str("just some text")))
        transformed1 = content1.content[0]

        content2 = pf.Div(
            pf.Para(pf.Strong(pf.Str("again")), pf.Space, pf.Emph(pf.Str("normal")))
        )

        content3 = pf.Div(
            pf.Para(
                pf.Span(pf.Str("foo"), classes=["1st-span-class"]),
                pf.Span(
                    pf.Strong(pf.Str("Unhandled"), pf.Space, pf.Str("command:")),
                    classes=["2nd-span-class"],
                ),
            ),
            pf.CodeBlock(r"\MLFunctionQuestion{10}{sin(x)}{5}{x}{5}{DS2}"),
            classes=["div-class"],
        )

        self.assertEqual(to_inline(content1), transformed1)

        # test if nested inlining works
        il_content2 = to_inline(content2)
        self.assertIsInstance(il_content2.content[0], pf.Strong)
        self.assertEqual(il_content2.content[0].content[0].text, "again")
        self.assertIsInstance(il_content2.content[2], pf.Emph)

        # test if class conservation works and advanced nesting
        il_content3 = to_inline(content3)
        self.assertEqual(len(il_content3.content), 2)
        self.assertEqual(len(il_content3.content[0].content), 2)
        self.assertEqual(il_content3.classes, ["div-class"])
        self.assertEqual(il_content3.content[0].content[0].classes, ["1st-span-class"])
        self.assertEqual(il_content3.content[0].content[1].classes, ["2nd-span-class"])


class TestExtractIdentifier(unittest.TestCase):
    def test_only_uxid(self):
        annot = pf.Div(
            identifier="{}-foo".format(SITE_UXID_PREFIX),
            classes=(SITE_UXID_PREFIX,),
        )
        identifier = extract_identifier([annot])
        self.assertEqual(identifier, "foo")

    def test_uxid_para(self):
        annot = pf.Div(
            identifier="{}-foo".format(SITE_UXID_PREFIX),
            classes=(SITE_UXID_PREFIX,),
        )
        para = pf.Para(pf.Str("bar"))
        identifier = extract_identifier([annot, para])
        self.assertEqual(identifier, "foo")

    def test_uxid_label_para(self):
        mlabel = pf.Div(
            identifier="{}-foo".format(INDEX_LABEL_PREFIX),
            classes=(INDEX_LABEL_PREFIX,),
        )
        uxid = pf.Div(
            identifier="{}-bar".format(SITE_UXID_PREFIX),
            classes=(SITE_UXID_PREFIX,),
        )
        para = pf.Para(pf.Str("bar"))

        tests = (
            ("(mlabel,uxid,para)", "foo", [mlabel, uxid, para]),
            ("(uxid,mlabel,para)", "foo", [uxid, mlabel, para]),
            ("(uxid,para)", "bar", [uxid, para]),
            ("(para)", None, [para]),
        )

        for name, exp_id, test in tests:
            with self.subTest("{} expected: {}".format(name, exp_id)):
                identifier = extract_identifier(test)
                self.assertEqual(identifier, exp_id)


class TestConvertSimplificationCode(unittest.TestCase):
    def test_flags(self):
        cases = (
            (0, ""),
            (1, "no-brackets"),
            (2, "factor-notation"),
            (513, "no-brackets,special-support-points"),
            (528, "only-one-slash,special-support-points"),
            (576, "no-sqrt,special-support-points"),
            (2048, "one-power-no-mult-or-div"),
        )

        for code, exp_code_str in cases:
            with self.subTest("{} expected: {}".format(code, exp_code_str)):
                code_str = convert_simplification_code(code)
                self.assertEqual(exp_code_str, code_str)
