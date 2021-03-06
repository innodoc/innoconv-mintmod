r"""
Handle mintmod LaTeX commands.

.. note::
    Provide a ``handle_CMDNAME`` function for handling ``CMDNAME`` command.
    You need to `slugify <https://github.com/un33k/python-slugify>`_ the
    command name.

    Example: ``handle_msection`` method will receive the command ``\MSection``.
"""

from os import environ, getcwd, linesep
from os.path import dirname, join
import re
import panflute as pf
from innoconv_mintmod.constants import (
    ELEMENT_CLASSES,
    INDEX_ATTRIBUTE,
    INDEX_LABEL_PREFIX,
    MATH_SUBSTITUTIONS,
    MINTMOD_SUBJECTS,
    REGEX_PATTERNS,
    SITE_UXID_PREFIX,
    TIKZ_SUBSTITUTIONS,
)
from innoconv_mintmod.utils import (
    block_wrap,
    destringify,
    parse_fragment,
    log,
    get_remembered,
    to_inline,
    remember,
)
from innoconv_mintmod.mintmod_filter.elements import (
    Question,
    create_header,
    create_image,
)


class Commands:

    r"""
    Handlers for commands are defined here.

    Given the command:

    .. code-block:: latex

        \MSection{Foo}

    The handler method ``handle_msection`` receives the following arguments:

    .. hlist::
        :columns: 1

        * ``cmd_args``: ``['Foo']``
        * ``elem``: :class:`panflute.base.Element`
    """

    # pylint: disable=unused-argument,no-self-use,too-many-public-methods

    ###########################################################################
    # \input{...}
    # disabled in raw_tex mode since Pandoc 2.8, see pandoc#5673

    def handle_input(self, cmd_args, elem):
        r"""Handle ``\input`` command."""
        filepath = join(getcwd(), cmd_args[0])
        with open(filepath, "r") as input_file:
            input_content = input_file.read()
        environ["INNOCONV_MINTMOD_CURRENT_DIR"] = dirname(filepath)
        return parse_fragment(input_content, elem.doc.metadata["lang"].text)

    ###########################################################################
    # Sections

    def handle_msection(self, cmd_args, elem):
        r"""Handle ``\MSection`` command."""
        return create_header(cmd_args[0], level=1, doc=elem.doc)

    def handle_msubsection(self, cmd_args, elem):
        r"""Handle ``\MSubsection``"""

        # Skip headings in final tests and entrance test -> handled in \MTest env
        if cmd_args[0] in (
            "Abschlusstest",
            "Final Test",
            "Test 1: Abzugebender Teil",
            "Test 1: Graded Part To Be Submitted",
        ):
            return []

        header = create_header(cmd_args[0], level=2, doc=elem.doc)

        # Fix specific identifier
        if cmd_args[0] in ("Test 1: Einführender Teil", "Test 1: Sample Part"):
            header.identifier = "L_TEST01"

        return header

    def handle_msubsubsection(self, cmd_args, elem):
        r"""Handle ``\MSubsubsection``"""
        return create_header(cmd_args[0], level=4, doc=elem.doc)

    def handle_msubsubsectionx(self, cmd_args, elem):
        r"""Handle ``\MSubsubsectionx`` command. Which will generate a level
        4 header."""
        return create_header(cmd_args[0], level=4, doc=elem.doc)

    def handle_mtitle(self, cmd_args, elem):
        r"""Handle ``\MTitle`` command.

        This is an equivalent to ``\subsubsection``
        """
        return create_header(cmd_args[0], level=4, doc=elem.doc)

    def handle_msubsubsubsectionx(self, cmd_args, elem):
        r"""Handle ``\MSubsubsubsectionx`` command. Which will generate a level
        4 header.

        From logical point of view this should be level 5. But from looking at
        the sources, level 4 is correct.
        """
        return create_header(cmd_args[0], level=4, doc=elem.doc)

    ###########################################################################
    # Metadata

    def handle_msubject(self, cmd_args, elem):
        r"""Handle ``\MSubject{title}`` command.

        Command defines the document title.
        """
        if not hasattr(elem.doc.metadata, "title"):
            elem.doc.metadata["title"] = pf.MetaString(cmd_args[0])
        return create_header(cmd_args[0], level=1, doc=elem.doc)

    def handle_msetsubject(self, cmd_args, elem):
        r"""Handle ``\MSetSubject{}`` command.

        Command defines the category.
        """
        elem.doc.metadata["subject"] = pf.MetaString(MINTMOD_SUBJECTS[cmd_args[0]])
        return []

    ###########################################################################
    # ID commands

    def handle_mdeclaresiteuxid(self, cmd_args, elem):
        r"""Handle ``\MDeclareSiteUXID`` command.

        The command can occur in an environment that is parsed by a
        subprocess. In this case there's no last header element. The process
        can't set the ID because it can't access the doc tree. Instead it
        replaces the ``\MDeclareSiteUXID`` by an element that is found by the
        parent process using function
        :py:func:`innoconv.utils.extract_identifier`.
        """
        identifier = cmd_args[0]

        # otherwise return a div/span with ID that is parsed in the parent
        # process
        if isinstance(elem, pf.Block):
            ret = pf.Div()
        else:
            ret = pf.Span()
        ret.identifier = "{}-{}".format(SITE_UXID_PREFIX, identifier)
        ret.classes = [SITE_UXID_PREFIX]
        ret.attributes = {"hidden": "hidden"}
        return ret

    def handle_mlabel(self, cmd_args, elem):
        # pylint: disable=line-too-long
        r"""Handle ``\MLabel`` command.

        Will search for the previous header element and update its ID to the
        ID defined in the command. Otherwise proceed like
        ``\MDeclareSiteUXID``.

        Hides identifier in fake element like
        (:py:func:`innoconv_mintmod.mintmod_filter.commands.Commands.handle_mdeclaresiteuxid`).
        """
        identifier = cmd_args[0]

        # Ignore MLabel in test sections as this would mess up the previous
        # section caption.
        if "Abschlusstest" in identifier or "Ausgangstest" in identifier:
            return []

        # attach identifier to previous element
        try:
            get_remembered(elem.doc, "label").identifier = identifier
            return []
        except AttributeError:
            pass

        # otherwise return a div/span with ID that is parsed in the parent
        # process
        if isinstance(elem, pf.Block):
            ret = pf.Div()
        else:
            ret = pf.Span()
        ret.identifier = "{}-{}".format(INDEX_LABEL_PREFIX, identifier)
        ret.classes = [INDEX_LABEL_PREFIX]
        ret.attributes = {"hidden": "hidden"}
        return ret

    def handle_mcopyrightlabel(self, cmd_args, elem):
        r"""Handle ``\MCopyrightLabel`` command."""
        return self.handle_mlabel(cmd_args, elem)

    def handle_msetsectionid(self, cmd_args, elem):
        r"""Handle ``\MSetSectionID`` command.

        Will search for the previous header element and update its ID to the
        ID defined in the command.
        """
        identifier = cmd_args[0]

        # attach identifier to previous element
        try:
            get_remembered(elem.doc, "label").identifier = identifier
        except AttributeError:
            pass
        return []

    ###########################################################################
    # Links/labels

    def handle_mref(self, cmd_args, elem):
        r"""Handle ``\MRef`` command.

        This command translates to ``\vref``.
        """
        url = "#%s" % cmd_args[0]
        return block_wrap(pf.Link(url=url, attributes={"data-mref": "true"}), elem)

    def handle_msref(self, cmd_args, elem):
        r"""Handle ``\MSRef`` command.

        This command inserts a fragment-style link.
        """
        url = "#%s" % cmd_args[0]
        description = destringify(cmd_args[1])
        return block_wrap(
            pf.Link(*description, url=url, attributes={"data-msref": "true"}),
            elem,
        )

    def handle_mnref(self, cmd_args, elem):
        r"""Handle ``\MNRef`` command.

        This command inserts a section link.
        """
        target = cmd_args[0]
        return block_wrap(pf.Link(url=target, attributes={"data-mnref": "true"}), elem)

    def handle_mextlink(self, cmd_args, elem):
        r"""Handle ``\MExtLink`` command.

        This command inserts an external link.
        """
        url = cmd_args[0]
        text = destringify(cmd_args[1])
        link = pf.Link(*text, url=url)
        return block_wrap(link, elem)

    ###########################################################################
    # Index

    def handle_mentry(self, cmd_args, elem):
        r"""Handle ``\MEntry`` command.

        This command creates an entry for the index.
        """

        if isinstance(elem, pf.Block):
            log("Warning: Expected Inline for MEntry: {}".format(cmd_args))

        text = cmd_args[0]
        concept = cmd_args[1]
        for repl in MATH_SUBSTITUTIONS:  # can contain LaTeX!
            concept = re.sub(repl[0], repl[1], concept)
        strong = pf.Strong()
        strong.content.extend(
            parse_fragment(text, elem.doc.metadata["lang"].text)[0].content
        )
        span = pf.Span()
        span.attributes = {INDEX_ATTRIBUTE: concept}
        span.content = [strong]
        return block_wrap(span, elem)

    def handle_mindex(self, cmd_args, elem):
        r"""Handle ``\MIndex`` command.

        This command creates an invisible entry for the index.
        """

        if isinstance(elem, pf.Block):
            log("Warning: Expected Inline for MIndex: {}".format(cmd_args))

        concept = cmd_args[0]
        for repl in MATH_SUBSTITUTIONS:  # can contain LaTeX!
            concept = re.sub(repl[0], repl[1], concept)
        span = pf.Span()
        span.attributes = {INDEX_ATTRIBUTE: concept, "hidden": "hidden"}
        return block_wrap(span, elem)

    ###########################################################################
    # Media

    def handle_mgraphics(self, cmd_args, elem, add_desc=True):
        r"""Handle ``\MGraphics``.

        Embed an image with title.

        Example: \MGraphics{img.png}{scale=1}{title}
        """
        is_block = isinstance(elem, pf.Block)
        return create_image(cmd_args[0], cmd_args[2], elem, block=is_block)

    def handle_mgraphicssolo(self, cmd_args, elem):
        r"""Handle ``\MGraphicsSolo``.

        Embed an image without title. Uses filename as image title.
        """
        is_block = isinstance(elem, pf.Block)
        return create_image(
            cmd_args[0], cmd_args[0], elem, block=is_block, add_descr=False
        )

    def handle_mugraphics(self, cmd_args, elem):
        r"""Handle ``\MUGraphics``.

        Embed an image with title.
        """
        return self.handle_mgraphics([cmd_args[0], None, cmd_args[2]], elem)

    def handle_mugraphicssolo(self, cmd_args, elem):
        r"""Handle ``\MUGraphicsSolo``.

        Embed an image without title.
        """
        return self.handle_mgraphicssolo(cmd_args, elem)

    def handle_myoutubevideo(self, cmd_args, elem):
        r"""Handle ``\MYoutubeVideo``.

        Just return a Link Element.
        """
        title, _, _, url = cmd_args
        link = pf.Link(
            *destringify(title),
            url=url,
            title=title,
            classes=ELEMENT_CLASSES["MYOUTUBE_VIDEO"],
        )
        return block_wrap(link, elem)

    def handle_mvideo(self, cmd_args, elem):
        r"""Handle ``\MVideo``.

        Just return a Link Element.
        """
        filename = "{}.mp4".format(cmd_args[0])
        title = cmd_args[1]
        link = pf.Link(
            *destringify(title),
            url=filename,
            title=title,
            classes=ELEMENT_CLASSES["MVIDEO"],
        )
        remember(elem.doc, "label", link)
        return block_wrap(link, elem)

    def handle_mtikzauto(self, cmd_args, elem):
        r"""Handle ``\MTikzAuto`` command.

        Create a ``CodeBlock`` with TikZ code.
        """
        if isinstance(elem, pf.Inline):
            raise ValueError(
                r"\MTikzAuto should be block element!: {}".format(cmd_args)
            )
        tikz_code = REGEX_PATTERNS["STRIP_HASH_LINE"].sub("", cmd_args[0])
        for repl in TIKZ_SUBSTITUTIONS:
            tikz_code = re.sub(repl[0], repl[1], tikz_code)
        # remove empty lines
        tikz_code = linesep.join([s for s in tikz_code.splitlines() if s])
        codeblock = pf.CodeBlock(tikz_code)
        codeblock.classes = ELEMENT_CLASSES["MTIKZAUTO"]
        ret = pf.Div(codeblock, classes=["figure"])
        return ret

    ###########################################################################
    # Questions

    def handle_mlquestion(self, cmd_args, elem):
        r"""Handle questions defined by ``\MLQuestion`` command"""
        return Question(
            cmd_args,
            mintmod_class="MLQuestion",
            oktypes=elem.parent.content.oktypes,
            points=get_remembered(elem.doc, "points", keep=True),
        )

    def handle_mlparsedquestion(self, cmd_args, elem):
        r"""Handle questions defined by ``\MLParsedQuestion`` command"""
        return Question(
            cmd_args,
            mintmod_class="MLParsedQuestion",
            oktypes=elem.parent.content.oktypes,
            points=get_remembered(elem.doc, "points", keep=True),
        )

    def handle_mlfunctionquestion(self, cmd_args, elem):
        r"""Handle questions defined by ``\MLFunctionQuestion`` command"""
        return Question(
            cmd_args,
            mintmod_class="MLFunctionQuestion",
            oktypes=elem.parent.content.oktypes,
            points=get_remembered(elem.doc, "points", keep=True),
        )

    def handle_mlspecialquestion(self, cmd_args, elem):
        r"""Handle questions defined by ``\MLSpecialquestion`` command"""
        return Question(
            cmd_args,
            mintmod_class="MLSpecialQuestion",
            oktypes=elem.parent.content.oktypes,
            points=get_remembered(elem.doc, "points", keep=True),
        )

    def handle_mlsimplifyquestion(self, cmd_args, elem):
        r"""Handle questions defined by ``\MLSimplifyQuestion`` command"""
        return Question(
            cmd_args,
            mintmod_class="MLSimplifyQuestion",
            oktypes=elem.parent.content.oktypes,
            points=get_remembered(elem.doc, "points", keep=True),
        )

    def handle_mlcheckbox(self, cmd_args, elem):
        r"""Handle questions defined by ``\MLCheckbox`` command"""
        return Question(
            cmd_args,
            mintmod_class="MLCheckbox",
            oktypes=elem.parent.content.oktypes,
            points=get_remembered(elem.doc, "points", keep=True),
        )

    def handle_mlintervalquestion(self, cmd_args, elem):
        r"""Handle questions defined by ``\MLIntervalQuestion`` command"""
        return Question(
            cmd_args,
            mintmod_class="MLIntervalQuestion",
            oktypes=elem.parent.content.oktypes,
            points=get_remembered(elem.doc, "points", keep=True),
        )

    def handle_mgroupbutton(self, cmd_args, elem):
        r"""Handle ``\MGroupButton`` command.

        Render empty as this button is displayed automatically in clients.
        """
        return []

    def handle_msetpoints(self, cmd_args, elem):
        r"""Handle ``\MSetPoints`` command.

        Remember points for next question.
        """
        points_value = cmd_args[0]
        remember(elem.doc, "points", points_value)
        return []

    def handle_mdirectrouletteexercises(self, cmd_args, elem):
        r"""Handle ``\MDirectRouletteExercises`` command.

        Remember points for next question.
        """
        filepath = join(environ["INNOCONV_MINTMOD_CURRENT_DIR"], cmd_args[0])
        with open(filepath, "r") as input_file:
            input_content = input_file.read()
        content = parse_fragment(input_content, elem.doc.metadata["lang"].text)
        div = pf.Div(classes=ELEMENT_CLASSES["MDIRECTROULETTEEXERCISES"])
        div.content.extend(content)
        return div

    ###########################################################################
    # Misc elements

    def handle_special(self, cmd_args, elem):
        r"""Handle ``\special`` command.

        This command is used to embed HTML in LaTeX source.
        """
        if cmd_args[0].startswith("html:"):
            return pf.RawBlock(cmd_args[0][5:], format="html")
        return None

    def handle_minputhint(self, cmd_args, elem):
        r"""Handle ``\MInputHint`` command."""
        content = parse_fragment(cmd_args[0], elem.doc.metadata["lang"].text)
        if isinstance(elem, pf.Block):
            div = pf.Div(classes=ELEMENT_CLASSES["MINPUTHINT"])
            div.content.extend(content)
            return div
        span = pf.Span(classes=ELEMENT_CLASSES["MINPUTHINT"])
        if content and isinstance(content[0], pf.Para):
            span.content.extend(content[0].content)
        return span

    def handle_mequationitem(self, cmd_args, elem):
        r"""Handle ``\MEquationItem`` command."""

        if len(cmd_args) != 2:
            raise ValueError(
                r"\MEquationItem needs 2 arguments. Received: {}".format(cmd_args)
            )

        content_left = parse_fragment(cmd_args[0], elem.doc.metadata["lang"].text)
        content_right = parse_fragment(cmd_args[1], elem.doc.metadata["lang"].text)

        content = to_inline(
            [content_left, pf.Math(r"\;\;=\;", format="InlineMath"), content_right]
        )

        if isinstance(elem, pf.Block):
            return pf.Plain(content)

        return content

    ###########################################################################
    # Command pass-thru

    def handle_mzxyzhltrennzeichen(self, cmd_args, elem):
        r"""Handle ``\MZXYZhltrennzeichen`` command.

        It is transformed to a ``\decmarker`` command and later substituted
        by MathJax. This is already in math substitions but as it occurs
        outside of math environments it's defined here too.
        """
        if isinstance(elem, pf.Block):
            raise ValueError(r"Encountered \MZXYZhltrennzeichen as block element!")
        return pf.Math(r"\decmarker", format="InlineMath")

    def handle_mzahl(self, cmd_args, elem):
        r"""Handle ``\MZahl`` command.

        This is a math command but in fact occurs also in text.
        """
        if isinstance(elem, pf.Block):
            raise ValueError(r"Encountered \MZahl as block element!")
        return pf.Math(
            r"\num{{{}.{}}}".format(cmd_args[0], cmd_args[1]),
            format="InlineMath",
        )

    ###########################################################################
    # Simple substitutions

    def handle_glqq(self, cmd_args, elem):
        r"""Handle ``\glqq`` command."""
        return pf.Str("„")

    def handle_grqq(self, cmd_args, elem):
        r"""Handle ``\grqq`` command."""
        return pf.Str("“")

    def handle_quad(self, cmd_args, elem):
        r"""Handle ``\quad`` command."""
        return pf.Space()

    def handle_mblank(self, cmd_args, elem):
        r"""Handle ``\MBlank`` command."""
        return pf.Space()

    ###########################################################################
    # Formatting

    def handle_modstextbf(self, cmd_args, elem):
        r"""Handle \modstextbf command."""
        return pf.Strong(
            *parse_fragment(cmd_args[0], elem.doc.metadata["lang"].text)[0].content
        )

    def handle_modsemph(self, cmd_args, elem):
        r"""Handle \modsemph command."""
        return pf.Emph(
            *parse_fragment(cmd_args[0], elem.doc.metadata["lang"].text)[0].content
        )

    def handle_highlight(self, cmd_args, elem):
        r"""Handle \highlight command.

        This seems to be some sort of formatting command. There's no
        documentation and it does nothing in the mintmod code. We just keep
        the information here.
        """
        return pf.Span(
            *parse_fragment(cmd_args[0], elem.doc.metadata["lang"].text)[0].content,
            classes=ELEMENT_CLASSES["HIGHLIGHT"],
        )

    def handle_newline(self, cmd_args, elem):
        r"""Handle \newline command."""
        return pf.LineBreak()

    ###########################################################################
    # No-ops

    def handle_mmodstartbox(self, cmd_args, elem):
        r"""Handle ``\MModStartBox`` command.

        This command displays a table of content for the current chapter. This
        is handled elswhere and becomes a no-op.
        """
        return self._noop()

    def handle_mpragma(self, cmd_args, elem):
        r"""Handle ``\MPragma`` command.

        This command was used to embed build time flags for mintmod. It becomes
        a no-op.
        """
        return self._noop()

    def handle_vspace(self, cmd_args, elem):
        r"""Handle ``\vspace`` command.

        A display related command. It becomes a no-op.
        """
        return self._noop()

    def handle_newpage(self, cmd_args, elem):
        r"""Handle ``\newpage`` command.

        A display related command. It becomes a no-op.
        """
        return self._noop()

    def handle_mprintindex(self, cmd_args, elem):
        r"""Handle ``\MPrintIndex`` command.

        Index will be printed automatically. It becomes a no-op.
        """
        return self._noop()

    def handle_mcontenttable(self, cmd_args, elem):
        r"""Handle ``\MContentTable`` command."""
        return self._noop()

    def handle_mglobalstart(self, cmd_args, elem):
        r"""Handle ``\MGlobalStart`` command."""
        return self._noop()

    def handle_mpullsite(self, cmd_args, elem):
        r"""Handle ``\MPullSite`` command."""
        return self._noop()

    def handle_mglobalchaptertag(self, cmd_args, elem):
        r"""Handle ``\MGlobalChapterTag`` command."""
        return self._noop()

    def handle_mglobalconftag(self, cmd_args, elem):
        r"""Handle ``\MGlobalConfTag`` command."""
        return self._noop()

    def handle_mgloballogouttag(self, cmd_args, elem):
        r"""handle ``\MGlobalLogoutTag`` command."""
        return self._noop()

    def handle_mgloballogintag(self, cmd_args, elem):
        r"""Handle ``\MGlobalLoginTag`` command."""
        return self._noop()

    def handle_mgloballocationtag(self, cmd_args, elem):
        r"""Handle ``\MGlobalLocationTag`` command."""
        return self._noop()

    def handle_mglobaldatatag(self, cmd_args, elem):
        r"""Handle ``\MGlobalDataTag`` command."""
        return self._noop()

    def handle_mglobalsearchtag(self, cmd_args, elem):
        r"""Handle ``\MGlobalSearchTag`` command."""
        return self._noop()

    def handle_mglobalfavotag(self, cmd_args, elem):
        r"""Handle ``\MGlobalFavoTag`` command."""
        return self._noop()

    def handle_mglobalstesttag(self, cmd_args, elem):
        r"""Handle ``\MGlobalSTestTag`` command."""
        return self._noop()

    def handle_mwatermarksettings(self, cmd_args, elem):
        r"""Handle ``\MWatermarkSettings`` command."""
        return self._noop()

    def handle_smallskip(self, cmd_args, elem):
        r"""Handle ``\smallskip`` command."""
        return self._noop()

    def handle_medskip(self, cmd_args, elem):
        r"""Handle ``\medskip`` command."""
        return self._noop()

    def handle_bigskip(self, cmd_args, elem):
        r"""Handle ``\bigskip`` command."""
        return self._noop()

    def handle_hspace(self, cmd_args, elem):
        r"""Handle ``\hspace`` and ``\hspace*`` command."""
        return self._noop()

    def handle_clearpage(self, cmd_args, elem):
        r"""Handle ``\clearpage`` command."""
        return self._noop()

    def handle_noindent(self, cmd_args, elem):
        r"""Handle ``\noindent`` command."""
        return self._noop()

    def handle_mcopyrightcollection(self, cmd_args, elem):
        r"""Handle ``\MCopyrightCollection`` command."""
        return self._noop()

    def handle_mformelzoomhint(self, cmd_args, elem):
        r"""Handle ``\MFormelZoomHint`` command."""
        return self._noop()

    def handle_jhtmlhinweiseingabefunktionen(self, cmd_args, elem):
        # pylint: disable=invalid-name
        r"""Handle ``\jHTMLHinweisEingabeFunktionen`` command."""
        return self._noop()

    def handle_jhtmlhinweiseingabefunktionenexp(self, cmd_args, elem):
        # pylint: disable=invalid-name
        r"""Handle ``\jHTMLHinweisEingabeFunktionenExp`` command."""
        return self._noop()

    @staticmethod
    def _noop():
        """Return no elements."""
        return []
