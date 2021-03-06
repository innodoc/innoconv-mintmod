"""Utility module"""

import os
import json
from shutil import which
from subprocess import Popen, PIPE
import sys

import panflute as pf
from panflute.elements import from_json

from innoconv_mintmod.constants import (
    REGEX_PATTERNS,
    ENCODING,
    INDEX_LABEL_PREFIX,
    SITE_UXID_PREFIX,
    PANZER_TIMEOUT,
)
from innoconv_mintmod.errors import ParseError


def log(msg_string, level="INFO"):
    """Log messages when running as a panzer filter.

    :param msg_string: Message that is logged
    :type msg_string: str
    :param level: Log level (``INFO``, ``WARNING``, ``ERROR`` OR ``CRITICAL``)
    :type level: str
    """
    outgoing = {"level": level, "message": msg_string}
    outgoing_json = json.dumps(outgoing) + "\n"
    if hasattr(sys.stderr, "buffer"):
        outgoing_bytes = outgoing_json.encode(ENCODING)
        sys.stderr.buffer.write(outgoing_bytes)
    else:
        sys.stderr.write(outgoing_json)
    sys.stderr.flush()


def get_panzer_bin():
    """Get path of panzer binary."""
    panzer_bin = which("panzer")
    if panzer_bin is None or not os.path.exists(panzer_bin):
        raise OSError("panzer executable not found!")
    return panzer_bin


def parse_fragment(parse_string, lang, as_doc=False, from_format="latex+raw_tex"):
    """Parse a source fragment using panzer.

    :param parse_string: Source fragment
    :type parse_string: str
    :param lang: Language code
    :type lang: str
    :param as_doc: Return elements as :class:`panflute.elements.Doc`
    :type as_doc: bool
    :param from_format: Source format
    :type from_format: str

    :rtype: list of :class:`panflute.base.Element` or
        :class:`panflute.elements.Doc`
    :returns: parsed elements

    :raises OSError: if panzer executable is not found
    :raises RuntimeError: if panzer recursion depth is exceeded
    :raises RuntimeError: if panzer output could not be parsed
    """

    root_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
    panzer_cmd = [
        get_panzer_bin(),
        "---panzer-support",
        os.path.join(root_dir, ".panzer"),
        "--from={}".format(from_format),
        "--to=json",
        "--metadata=style:innoconv",
        "--metadata=lang:{}".format(lang),
    ]

    # pass nesting depth as ENV var
    recursion_depth = int(os.getenv("INNOCONV_RECURSION_DEPTH", "0"))
    env = os.environ.copy()
    env["INNOCONV_RECURSION_DEPTH"] = str(recursion_depth + 1)

    if recursion_depth > 10:
        raise RuntimeError("Panzer recursion depth exceeded!")

    proc = Popen(panzer_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, env=env)
    out, err = proc.communicate(
        input=parse_string.encode(ENCODING), timeout=PANZER_TIMEOUT
    )
    out = out.decode(ENCODING)
    err = err.decode(ENCODING)

    if proc.returncode != 0:
        log(err, level="ERROR")
        raise RuntimeError("panzer process exited with non-zero return code.")

    # only print filter messages for better output log
    match = REGEX_PATTERNS["PANZER_OUTPUT"].search(err)
    if match:
        for line in match.group("messages").strip().splitlines():
            log("↳ %s" % line.strip(), level="INFO")
    else:
        raise RuntimeError("Unable to parse panzer output: {}".format(err))

    doc = json.loads(out, object_hook=from_json)

    if as_doc:
        return doc

    if isinstance(doc.content, pf.ListContainer):
        return list(doc.content)

    return doc.content


# pylint: disable=dangerous-default-value
def to_inline(elem, classes=[], attributes={}):
    """Convert any given pandoc element to inline element(s). Some information
    may be lost."""

    if not classes:
        classes = getattr(elem, "classes", [])
    if not attributes:
        attributes = getattr(elem, "attributes", {})

    if isinstance(elem, pf.Inline):
        return elem
    if isinstance(elem, pf.CodeBlock):
        return pf.Code(elem.text, classes=classes, attributes=attributes)
    if isinstance(elem, pf.RawBlock):
        return pf.RawInline(elem.text, format=elem.format)

    elems = []
    if isinstance(elem, pf.Block):
        elems = elem.content
    elif isinstance(elem, list):
        elems = elem

    # dont nest too many spans
    if len(elems) == 1:
        return to_inline(elems[0], classes=classes, attributes=attributes)

    ret = [to_inline(x, classes=classes, attributes=attributes) for x in elems]

    return pf.Span(*ret, classes=classes, attributes=attributes)


def destringify(string):
    """Takes a string and transforms it into list of Str and Space objects.

    This function breaks down strings with whitespace. It could be done by
    calling :func:`parse_fragment` but doesn't have the overhead involed.

    :Example:

        >>> destringify('foo  bar\tbaz')
        [Str(foo), Space, Str(bar), Space, Str(baz)]

    :param string: String to transform
    :type string: str

    :rtype: list
    :returns: list of :class:`panflute.Str` and :class:`panflute.Space`
    """
    ret = []
    split = string.split()
    for word in split:
        ret.append(pf.Str(word))
        if split.index(word) != len(split) - 1:
            ret.append(pf.Space())
    return ret


def parse_cmd(text):
    r"""
    Parse a LaTeX command using regular expressions.

    Parses a command like: ``\foo{bar}{baz}``

    :param text: String to parse
    :type text: str

    :rtype: (str, list)
    :returns: command name and list of command arguments
    """
    match = REGEX_PATTERNS["CMD"].match(text)
    if not match:
        raise ParseError("Could not parse LaTeX command: '%s'" % text)
    groups = match.groups()
    cmd_name = groups[0]
    cmd_args, _ = parse_nested_args(groups[1])
    return cmd_name, cmd_args


def parse_nested_args(to_parse):
    r"""
    Parse LaTeX command arguments that can have nested commands. Returns
    arguments and rest string.

    Parses strings like: ``{bar}{baz{}}rest`` into
    ``[['bar', 'baz{}'], 'rest']``.

    :param to_parse: String to parse
    :type to_parse: str

    :rtype: (list, str)
    :returns: parsed arguments and rest string
    """
    pargs = []
    if to_parse.startswith("{"):
        stack = []
        for i, cha in enumerate(to_parse):
            if not stack and cha != "{":
                break
            if cha == "{":
                stack.append(i)
            elif cha == "}" and stack:
                start = stack.pop()
                if not stack:
                    start_index = start + 1
                    pargs.append(to_parse[start_index:i])
        chars_to_remove = len("".join(pargs)) + 2 * len(pargs)
        to_parse = to_parse[chars_to_remove:]
    if not to_parse:
        to_parse = None
    return (pargs, to_parse)


def extract_identifier(content):
    r"""Extract identifier from content and remove annotation element.

    ``\MLabel``/``MDeclareSiteUXID`` commands that occur within environments
    are parsed in a child process (e.g.
    :py:func:`innoconv_mintmod.mintmod_filter.commands.handle_mlabel`).
    The id attribute can't be set directly as they can't access the whole doc
    tree. As a workaround they create a fake element and add the identifier.

    :param content: List of elements
    :type content: list

    :rtype: str
    :returns: identifier (might be ``None``)
    """
    identifier = None

    def _extract_id(prefix, child):
        if prefix in child.classes:
            match = REGEX_PATTERNS["EXTRACT_ID"](prefix).match(child.identifier)
            if match:
                return match.groups()[0]
        raise ValueError()

    # extract ID (label takes precedence!)
    for prefix in (SITE_UXID_PREFIX, INDEX_LABEL_PREFIX):
        try:
            # check first 3 elements
            for idx in range(3):
                child = content[idx]
                try:
                    identifier = _extract_id(prefix, child)
                except (AttributeError, ValueError):
                    pass
        except IndexError:
            pass

    return identifier


def remove_annotations(doc):
    """Remove left-over annotation elements from document.

    :param doc: Document
    :type doc: :py:class:`panflute.elements.Doc`
    """

    def _rem_para(elem, _):
        try:
            if isinstance(elem, pf.Div) and (
                INDEX_LABEL_PREFIX in elem.classes or SITE_UXID_PREFIX in elem.classes
            ):
                return []  # delete element
        except AttributeError:
            pass
        return None

    doc.walk(_rem_para)


def remove_empty_paragraphs(doc):
    """Remove empty paragraphs from document.

    :param doc: Document
    :type doc: :py:class:`panflute.elements.Doc`
    """

    def _rem_para(elem, _):
        if isinstance(elem, pf.Para) and not elem.content:
            return []  # delete element
        return None

    doc.walk(_rem_para)


def remember(doc, key, elem):
    """Rememember an element in the document for later.

    To retrieve remembered elements use :py:func:`get_remembered`.

    :param doc: Document where to store the memory
    :type doc: :py:class:`panflute.elements.Doc`
    :param key: Key under which element is stored
    :type key: str
    :param elem: Element to remember
    :type elem: :py:class:`panflute.base.Element`
    """
    try:
        doc.remembered_element[key] = elem
    except AttributeError:
        doc.remembered_element = {key: elem}


def get_remembered(doc, key, keep=False):
    """Retrieve rememembered element from the document and forget it.

    To remember elements use :py:func:`remember`.

    :param doc: Document where the element is stored
    :type doc: :py:class:`panflute.elements.Doc`
    :param key: Key under which element is stored
    :type key: str
    :param keep: If value should be kept after retrieving (default=False)
    :type keep: bool

    :rtype: :py:class:`panflute.base.Element`
    :returns: The remembered element or `None`
    """
    try:
        elem = doc.remembered_element[key]
    except (AttributeError, KeyError):
        return None
    if not keep:
        del doc.remembered_element[key]
    return elem


def block_wrap(elem, orig_elem):
    """Wraps an element in a block if necessary.

    If the original element was block panflute expects the return value to be
    also block. In many places we need to detect this and wrap an inline.

    :param elem: Element to be wrapped
    :type elem: :py:class:`panflute.base.Element`
    :param orig_elem: Original element
    :type orig_elem: :py:class:`panflute.base.Element`

    :rtype: :py:class:`panflute.base.Element`
    :returns: ``elem`` or ``elem`` wrapped in
        :py:class:`panflute.elements.Plain`
    """
    if isinstance(orig_elem, pf.Block):
        return pf.Plain(elem)
    return elem


def convert_simplification_code(code):
    """Convert binary flags to string flags."""
    flags = []
    if (code & 15) == 1:
        flags.append("no-brackets")
    if (code & 15) == 2:
        flags.append("factor-notation")
    if (code & 15) == 3:
        # actually never used in tub_mathe
        flags.append("sum-notation")

    code_flags = (
        (16, "only-one-slash"),
        (32, "antiderivative"),
        (64, "no-sqrt"),
        (128, "no-abs"),
        (256, "no-fractions-no-powers"),
        (512, "special-support-points"),
        (1024, "only-natural-number"),
        (2048, "one-power-no-mult-or-div"),
    )
    for code_flag, str_flag in code_flags:
        if (code & code_flag) == code_flag:
            flags.append(str_flag)

    return ",".join(flags)
