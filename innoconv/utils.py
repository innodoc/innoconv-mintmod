"""Utility Module."""

import os
import json
import re
from subprocess import Popen, PIPE
from shutil import which

import panflute as pf
from panflute.elements import from_json

from innoconv.constants import REGEX_PATTERNS
from innoconv.errors import ParseError


def log(msg_string, level='INFO'):
    """Log messages for panzer."""
    msg = {
        'level': level,
        'message': msg_string,
    }
    pf.debug(json.dumps(msg))


def parse_fragment(parse_string, quiet=True):
    """Parse a source fragment using panzer.

    :param parse_string: Source fragment
    :type parse_string: str
    :param quiet: Pass ``---quiet``` arg to panzer
    :type quiet: boolean

    :returns: list of :class:`panflute.Element`
    """

    panzer_bin = which('panzer')
    if panzer_bin is None or not os.path.exists(panzer_bin):
        log('panzer executable not found!', level='CRITICAL')
        return []

    root_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
    panzer_support_dir = os.path.join(root_dir, '.panzer')
    panzer_cmd = [
        panzer_bin,
        '---panzer-support', panzer_support_dir,
        '--from=latex+raw_tex',
        '--to=json',
        '--metadata=style:innoconv',
    ]

    if quiet:
        panzer_cmd.append('---quiet')

    proc = Popen(panzer_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate(input=parse_string.encode('utf-8'))

    # TODO: pass nesting level to subprocesses and indent output

    if err:
        for line in err.decode('utf-8').splitlines():
            log(line.strip(), level='INFO')

    if proc.returncode != 0:
        log('panzer process exited with non-zero return code.', level='ERROR')
        return []

    doc = json.loads(out.decode('utf-8'), object_pairs_hook=from_json)
    return doc.content.list


def destringify(string):
    """Takes a string and transforms it into list of Str and Space objects.

    This function breaks down strings with whitespace. It could be done by
    calling :func:`parse_fragment` but doesn't have the overhead involed.

    :Example:

        >>> destringify('foo  bar\tbaz')
        [Str(foo), Space, Str(bar), Space, Str(baz)]

    :param string: String to transform
    :type string: str

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

    :param string: String to parse
    :type string: str

    :returns: `str` cmd_name, list of `str` cmd_args
    """
    match = REGEX_PATTERNS['CMD'].match(text)
    if not match:
        raise ParseError("Could not parse LaTeX command: '%s'" % text)
    cmd_name = match.groups()[0]
    cmd_args = re.findall(REGEX_PATTERNS['CMD_ARGS'], text)
    return cmd_name, cmd_args
