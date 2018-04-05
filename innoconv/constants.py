"""Project constants are defined here."""

import re
import os


#: Element class for index labels
INDEX_LABEL_PREFIX = 'index-label'

#: Regular expressions
REGEX_PATTERNS = {
    # latex parsing
    'CMD': re.compile(r'\A\\([^\\\s{]+)(.*)\Z', re.DOTALL),
    'ENV': re.compile(r'\A\\begin{(?P<env_name>[^}]+)}(.+)'
                      r'\\end{(?P=env_name)}\Z', re.DOTALL),
    'ENV_ARGS': re.compile(
        r'\A{(?P<arg>[^\n\r}]+)}(?P<rest>.+)\Z', re.DOTALL),

    'LABEL': re.compile(r'^{}-(.+)$'.format(INDEX_LABEL_PREFIX)),
    'STRIP_HASH_LINE': re.compile(r'^\%(\r\n|\r|\n)'),

    # panzer output parsing
    'PANZER_OUTPUT':
        re.compile(r"----- filter -----.+?json(?:\n|\r\n?)(?P<messages>.+)"
                   "----- pandoc write -----", re.MULTILINE | re.DOTALL)
}

#: Element classes
ELEMENT_CLASSES = {
    'IMAGE': ['img'],
    'FIGURE': ['figure'],
    'DEBUG_UNKNOWN_CMD': ['innoconv-debug-unknown-command'],
    'DEBUG_UNKNOWN_ENV': ['innoconv-debug-unknown-environment'],
    'MINTRO': ['intro'],
    'MEXERCISES': ['exercises'],
    'MEXERCISE': ['exercise'],
    'MINFO': ['info'],
    'MEXPERIMENT': ['experiment'],
    'MEXAMPLE': ['example'],
    'MHINT': ['hint'],
    'MINPUTHINT': ['hint-text'],
    'MTIKZAUTO': ['tikz'],
    'MYOUTUBE_VIDEO': ['video', 'video-youtube'],
}

#: Subjects as used in mintmod command ``\MSetSubject``
MINTMOD_SUBJECTS = {
    r'\MINTMathematics': 'mathematics',
    r'\MINTInformatics': 'informatics',
    r'\MINTChemistry': 'chemistry',
    r'\MINTPhysics': 'physics',
    r'\MINTEngineering': 'engineering',
}

#: Supported language codes
LANGUAGE_CODES = (
    'de',
    'en',
)

#: Default language code
DEFAULT_LANGUAGE_CODE = LANGUAGE_CODES[0]

#: Default innoconv output directory
DEFAULT_OUTPUT_DIR_BASE = os.path.join(os.getcwd(), 'innoconv_output')

#: Default innoconv output format
DEFAULT_OUTPUT_FORMAT = 'json'

#: mapping between output formats and file extensions
OUTPUT_FORMAT_EXT_MAP = {
    'html5': 'html',
    'json': 'json',
    'latex': 'tex',
    'markdown': 'md',
    'asciidoc': 'adoc',
}

#: Output format choices
OUTPUT_FORMAT_CHOICES = list(OUTPUT_FORMAT_EXT_MAP.keys())

#: project root dir
ROOT_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')

#: panzer support directory
PANZER_SUPPORT_DIR = os.path.join(ROOT_DIR, '.panzer')

#: encoding used in this project
ENCODING = 'utf-8'
