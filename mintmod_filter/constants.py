import re

# regex patterns
REGEX_PATTERNS = {
    'CMD': re.compile(r'\\([A-Za-z0-9_]+)', re.DOTALL),
    'CMD_ARGS': re.compile(r'{([^}]+)}'),
    'ENV': re.compile(r'\A\\begin{(?P<env_name>[^}]+)}(.+)'
                      r'\\end{(?P=env_name)}\Z', re.DOTALL),
    'ENV_ARGS': re.compile(
        r'\A{(?P<arg>[^\n\r}]+)}(?P<rest>.+)\Z', re.DOTALL),
}

# CSS classes
CSS_CLASSES = {
    'MXCONTENT': ['content'],
    'MEXERCISES': ['content', 'exercises'],
    'MEXERCISE': ['exercise'],
    'MINFO': ['info'],
    'MEXPERIMENT': ['experiment'],
    'MEXAMPLE': ['example'],
    'MHINT': ['hint'],
    'MHINT_TEXT': ['hint-text'],
    'UNKNOWN_CMD': ['unknown-command'],
    'UNKNOWN_ENV': ['unknown-environment'],
}

# colors
COLOR_UNKNOWN_CMD = '#ffa500'
COLOR_UNKNOWN_ENV = '#ff4d00'
