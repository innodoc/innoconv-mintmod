"""The actual Pandoc filter."""

import re
import panflute as pf
from slugify import slugify

from mintmod_filter.utils import debug, destringify, ParseError
from mintmod_filter.environments import Environments
from mintmod_filter.commands import Commands
from mintmod_filter.constants import (
    REGEX_PATTERNS, CSS_CLASSES, COLOR_UNKNOWN_CMD, COLOR_UNKNOWN_ENV)
from mintmod_filter.math_substitutions import handle_math_substitutions


class FilterAction:
    def __init__(self):
        self._commands = Commands()
        self._environments = Environments()

    def filter(self, elem, doc):
        """
        Receive document elements.

        This function receives document elements from Pandoc and delegates
        handling of simple subtitutions, mintmod commands and
        environments.

        :param elem: Element to handle
        :type elem: :class:`panflute.base.Element`
        :param doc: Document
        :type doc: :class:`panflute.elements.Doc`
        """
        if isinstance(elem, pf.Math):
            return handle_math_substitutions(elem, doc)
        elif isinstance(elem, pf.RawBlock) and elem.format == 'latex':
            match = REGEX_PATTERNS['CMD'].match(elem.text)
            if match:
                cmd_name = match.groups()[0]
                if cmd_name.startswith('begin'):
                    return self._handle_environment(elem, doc)
                else:
                    args = re.findall(REGEX_PATTERNS['CMD_ARGS'], elem.text)
                    return self._handle_command(cmd_name, args, elem, doc)
            else:
                raise ParseError(
                    'Could not parse LaTeX command: %s...' % elem.text)
        elif isinstance(elem, pf.RawInline) and elem.format == 'latex':
            # no inline environments are allowed
            match = REGEX_PATTERNS['CMD'].match(elem.text)
            if match:
                cmd_name = match.groups()[0]
                args = re.findall(REGEX_PATTERNS['CMD_ARGS'], elem.text)
                return self._handle_command(cmd_name, args, elem, doc)
        return None

    def _handle_command(self, cmd_name, args, elem, doc):
        """Parse and handle mintmod commands."""
        function_name = 'handle_%s' % slugify(cmd_name)
        func = getattr(self._commands, function_name, None)
        if callable(func):
            return func(args, elem, doc)
        return self._handle_unknown_command(cmd_name, args, elem, doc)

    def _handle_unknown_command(self, cmd_name, args, elem, doc):
        """Handle unknown latex commands.

        Output visual feedback about the unknown command.
        """
        debug("Could not handle command %s." % cmd_name)
        classes = CSS_CLASSES['UNKNOWN_CMD'] + [slugify(cmd_name)]
        attrs = {'style': 'background: %s;' % COLOR_UNKNOWN_CMD}

        msg = [
            pf.Strong(*destringify('Unhandled command:')),
            pf.Space(), pf.Code(elem.text),
        ]
        if isinstance(elem, pf.Block):
            div = pf.Div(classes=classes, attributes=attrs)
            div.content.extend([pf.Para(*msg)])
            return div
        elif isinstance(elem, pf.Inline):
            span = pf.Span(classes=classes, attributes=attrs)
            span.content.extend(msg)
            return span

    def _handle_environment(self, elem, doc):
        """Parse and handle mintmod environments."""
        match = REGEX_PATTERNS['ENV'].search(elem.text)
        if match is None:
            raise ParseError(
                'Could not parse LaTeX environment: %s...' % elem.text[:50])

        env_name = match.group('env_name')
        inner_code = match.groups()[1]

        # Parse optional arguments
        env_args = []
        rest = inner_code
        while True:
            match = REGEX_PATTERNS['ENV_ARGS'].search(rest)
            if match is None:
                break
            env_args.append(match.group('arg'))
            rest = match.group('rest')

        function_name = 'handle_%s' % slugify(env_name)
        func = getattr(self._environments, function_name, None)
        if callable(func):
            return func(rest, env_args, doc)
        return self._handle_unknown_environment(
            env_name, env_args, rest, elem, doc)

    def _handle_unknown_environment(self, env_name, args, elem_content, elem,
                                    doc):
        """Handle unknown latex environment.

        Output visual feedback about the unknown environment.
        """
        debug("Could not handle environment %s." % env_name)
        classes = CSS_CLASSES['UNKNOWN_ENV'] + [slugify(env_name)]
        attrs = {'style': 'background: %s;' % COLOR_UNKNOWN_ENV}
        div = pf.Div(classes=classes, attributes=attrs)
        msg = pf.Para(pf.Strong(*destringify('Unhandled environment:')),
                      pf.LineBreak(), pf.Code(elem.text))
        div.content.extend([msg])
        return div
