"""Helper for panzer processing scripts."""
import json
import sys

ENCODING = "utf8"


def log(level, message):
    """Log message to console"""
    outgoing = {"level": level, "message": message}
    outgoing_json = json.dumps(outgoing) + "\n"
    outgoing_bytes = outgoing_json.encode(ENCODING)
    sys.stderr.buffer.write(outgoing_bytes)
    sys.stderr.flush()


def read_options():
    """Read pandoc options from stdin"""
    stdin_bytes = sys.stdin.buffer.read()
    stdin = stdin_bytes.decode(ENCODING)
    message_in = json.loads(stdin)
    options = message_in[0]["options"]
    return options


def destringify(string):
    """Takes a string and transforms it into list of Str and Space objects."""
    ret = []
    split = string.split()
    for word in split:
        ret.append({"t": "Str", "c": word})
        if split.index(word) != len(split) - 1:
            ret.append({"t": "Space"})
    return ret
