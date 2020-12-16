r"""
Handle mintmod LaTeX environments.

.. note::
    Provide a ``handle_ENVNAME`` function for handling ``ENVNAME`` environment.
    You need to `slugify <https://github.com/un33k/python-slugify>`_ the
    environment name.

    Example: ``handle_mxcontent`` method will receive the
    ``\begin{MXContent}…\end{MXContent}`` environment.
"""

from innoconv_mintmod.constants import ELEMENT_CLASSES, TRANSLATIONS
from innoconv_mintmod.mintmod_filter.elements import (
    create_content_box,
    create_header,
)
from innoconv_mintmod.utils import parse_fragment, extract_identifier


class Environments:

    r"""Handlers for environments are defined here.

    Given the environment:

    .. code-block:: latex

        \begin{MXContent}{Foo title long}{Foo title}{STD}
            Foo content
        \end{MXContent}

    The handler method ``handle_mxcontent`` receives the following arguments:

    .. hlist::
        :columns: 1

        * ``elem_content``: ``'Foo content'``
        * ``cmd_args``: ``['Foo title long', 'Foo title', 'STD']``
        * ``elem``: :class:`panflute.elements.RawBlock`
    """

    # pylint: disable=unused-argument,no-self-use

    def handle_msectionstart(self, elem_content, env_args, elem):
        r"""Handle ``\MSectionStart`` environment."""
        return parse_fragment(elem_content, elem.doc.metadata["lang"].text)

    def handle_mxcontent(self, elem_content, env_args, elem):
        r"""Handle ``\MXContent`` environment."""
        content = parse_fragment(elem_content, elem.doc.metadata["lang"].text)

        # special case: Skip header creation for some weird (meta?) caption in
        # entrance test.
        if env_args[0] != "Restart" and env_args[0] != "Neustart":
            header = create_header(env_args[0], elem.doc, level=3)
            identifier = extract_identifier(content)
            if identifier:
                header.identifier = identifier
            content.insert(0, header)

        return content

    def handle_mcontent(self, elem_content, env_args, elem):
        r"""Handle ``\MContent`` environment."""
        content = parse_fragment(elem_content, elem.doc.metadata["lang"].text)
        lang = elem.doc.metadata["lang"].text
        header = create_header(
            TRANSLATIONS["content"][lang],
            elem.doc,
            level=3,
            identifier="content",
        )
        identifier = extract_identifier(content)
        if identifier:
            header.identifier = identifier
        content.insert(0, header)
        return content

    def handle_mintro(self, elem_content, env_args, elem):
        r"""Handle ``\MIntro`` environment."""
        content = parse_fragment(elem_content, elem.doc.metadata["lang"].text)
        lang = elem.doc.metadata["lang"].text
        header = create_header(
            TRANSLATIONS["introduction"][lang],
            elem.doc,
            level=3,
            identifier="introduction",
        )
        identifier = extract_identifier(content)
        if identifier:
            header.identifier = identifier
        # pylint: disable=no-member
        header.classes.extend(ELEMENT_CLASSES["MINTRO"])
        content.insert(0, header)
        return content

    ###########################################################################
    # Exercises

    def handle_mexercises(self, elem_content, env_args, elem):
        r"""Handle ``\MExercises`` environment."""
        content = parse_fragment(elem_content, elem.doc.metadata["lang"].text)
        lang = elem.doc.metadata["lang"].text
        header = create_header(TRANSLATIONS["exercises"][lang], elem.doc, level=3)
        identifier = extract_identifier(content)
        if identifier:
            header.identifier = identifier
        # pylint: disable=no-member
        header.classes.extend(ELEMENT_CLASSES["MEXERCISES"])
        content.insert(0, header)
        return content

    def handle_mexercisecollection(self, elem_content, env_args, elem):
        r"""Handle ``\MExerciseCollection`` environment."""
        return parse_fragment(elem_content, elem.doc.metadata["lang"].text)

    def handle_mexercise(self, elem_content, env_args, elem):
        r"""Handle ``\MExercise`` environment."""
        return create_content_box(
            elem_content,
            ELEMENT_CLASSES["MEXERCISE"],
            elem.doc.metadata["lang"].text,
        )

    def handle_mexerciseitems(self, elem_content, env_args, elem):
        r"""Handle ``\MExerciseitems`` environments by returning an ordered list
        containing the ``\item`` s defined in the environment. This is needed
        on top of handle_itemize as there are also mexerciseitems environments
        outside itemize environments."""
        return self._replace_mexerciseitems(elem)

    def handle_mquestiongroup(self, elem_content, env_args, elem):
        r"""Handle ``\MQuestionGroup`` environments.

        In mintmod used to group checkboxes together. We just return the
        content as questions are grouped by exercises anyway."""
        return parse_fragment(elem_content, elem.doc.metadata["lang"].text)

    ###########################################################################

    def handle_itemize(self, elem_content, env_args, elem):
        r"""Handle itemize environments, that were not correctly recognized by
        pandoc. This e.g. happens if there are ``\MExerciseItems`` environments
        contained in the items."""
        return self._replace_mexerciseitems(elem)

    def handle_minfo(self, elem_content, env_args, elem):
        r"""Handle ``\MInfo`` environment."""
        return create_content_box(
            elem_content,
            ELEMENT_CLASSES["MINFO"],
            elem.doc.metadata["lang"].text,
        )

    def handle_mxinfo(self, elem_content, env_args, elem):
        r"""Handle ``\MXInfo`` environment."""
        div = create_content_box(
            elem_content,
            ELEMENT_CLASSES["MINFO"],
            elem.doc.metadata["lang"].text,
        )
        header = create_header(env_args[0], elem.doc, level=4, parse_text=True)
        div.content.insert(0, header)
        return div

    def handle_mexperiment(self, elem_content, env_args, elem):
        r"""Handle ``\MExperiment`` environment."""
        return create_content_box(
            elem_content,
            ELEMENT_CLASSES["MEXPERIMENT"],
            elem.doc.metadata["lang"].text,
        )

    def handle_mexample(self, elem_content, env_args, elem):
        r"""Handle ``\MExample`` command."""
        return create_content_box(
            elem_content,
            ELEMENT_CLASSES["MEXAMPLE"],
            elem.doc.metadata["lang"].text,
        )

    def handle_mhint(self, elem_content, env_args, elem):
        r"""Handle ``\MHint`` command."""
        lang = elem.doc.metadata["lang"].text
        div = create_content_box(elem_content, ELEMENT_CLASSES["MHINT"], lang)
        caption = env_args[0]
        # pylint: disable=no-member
        div.attributes["caption"] = caption.replace(
            r"\iSolution", lang == "de" and "Lösung" or "Solution"
        )
        return div

    def handle_mtest(self, elem_content, env_args, elem):
        r"""Handle ``\MTest`` environment."""
        content = parse_fragment(elem_content, elem.doc.metadata["lang"].text)
        title = env_args[0]

        # Normalize various forms of inconsistent titles
        if "Abschlusstest" in title:  # Final test
            title = "Abschlusstest"
        elif "Final Test" in title:
            title = "Final Test"
        elif "Eingangstest" in title:  # Entrance test
            title = "Test 1: Abzugebender Teil"
        elif "Graded Test" in title:
            title = "Test 1: Graded Part To Be Submitted"

        header = create_header(title, elem.doc, level=2)
        identifier = extract_identifier(content)
        if identifier:
            header.identifier = identifier

        # pylint: disable=no-member
        header.classes.extend(ELEMENT_CLASSES["MTEST"])
        content.insert(0, header)
        return content

    def handle_mcoshzusatz(self, elem_content, env_args, elem):
        r"""Handle ``\MCOSHZusatz`` environment."""
        return create_content_box(
            elem_content,
            ELEMENT_CLASSES["MCOSHZUSATZ"],
            elem.doc.metadata["lang"].text,
        )

    def handle_html(self, elem_content, env_args, elem):
        r"""Handle ``\html`` environment."""
        return parse_fragment(
            elem_content, elem.doc.metadata["lang"].text, from_format="html"
        )

    def _replace_mexerciseitems(self, elem):
        r"""Helper function to replace `MExerciseItems` with enumerate in elem
        text and return the pandoc output of the parsed altered element."""
        elem.text = elem.text.replace("\\begin{MExerciseItems}", "\\begin{enumerate}")
        elem.text = elem.text.replace("\\end{MExerciseItems}", "\\end{enumerate}")
        return parse_fragment(elem.text, elem.doc.metadata["lang"].text)
