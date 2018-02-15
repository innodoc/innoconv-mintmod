"""The actual filter function."""

import re
import panflute as pf
from slugify import slugify

from mintmod_filter.utils import debug, ParseError
from mintmod_filter.handle_env import handle_environment
from mintmod_filter.handle_substitutions import handle_math_substitutions

PATTERN_SPECIAL = re.compile(r'\\special{html:(.*)}')
PATTERN_MSECTION = re.compile(r'\\MSection{([^}]*)}')


def handle_cmd_special(elem):
    r"""Handle LaTeX command \special{}.

    It's commonly used to embed HTML code. We parse the HTML and insert it.
    """
    match = PATTERN_SPECIAL.match(elem.text)
    if match:
        return pf.RawBlock(match.groups()[0])
    debug(r'Could not find HTML in \special: %s' % elem.text)
    return elem


def handle_cmd_msection(elem, doc):
    """Remember MSection name for later."""
    match = PATTERN_MSECTION.search(elem.text)
    if match is None:
        raise ParseError(r'Could not \MSection: %s' % elem)
    doc.msection_content = match.groups()[0]
    doc.msection_id = slugify(match.groups()[0])
    return []


def filter_action(elem, doc):
    """Walk document AST."""
    if isinstance(elem, pf.Math):
        return handle_math_substitutions(elem, doc)
    elif isinstance(elem, pf.RawBlock) and elem.format == 'latex':
        # handle mintmod commands
        if elem.text.startswith(r'\MSection{'):
            return handle_cmd_msection(elem, doc)
        elif elem.text.startswith(r'\begin{'):
            return handle_environment(elem, doc)
        # handle mintmod environments
        elif elem.text.startswith(r'\special'):
            return handle_cmd_special(elem)
        else:
            debug('Unhandled RawBlock: %s' % elem.text)
    return None
