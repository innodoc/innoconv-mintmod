"""Convenience functions and classes for creating common elements."""

from textwrap import shorten
import panflute as pf
from innoconv_mintmod.constants import DEFAULT_EXERCISE_POINTS, ELEMENT_CLASSES
from innoconv_mintmod.utils import (
    destringify,
    parse_fragment,
    extract_identifier,
    remember,
    log,
)


class Question(pf.Element):
    """
    Wrapper/Factory class that inherits from pf.Element and will return pf.Code
    instances, with special classes and attributes, depending on the given
    mintmod class.
    """

    __slots__ = ["identifier", "classes", "attributes"]

    def __new__(cls, *args, **kwargs):
        """The __new__ function expects a keyword argument with the key
        'mintmod_class' that specifies the type of question in the mintmod
        converter.
        """
        mintmod_class = kwargs.get("mintmod_class", None)
        oktypes = kwargs.get("oktypes", None)
        cmd_args = args[0]
        points = kwargs.get("points", None)
        if points is None:
            points = DEFAULT_EXERCISE_POINTS

        class_text_question = ELEMENT_CLASSES["QUESTION"] + ["text"]

        if mintmod_class == "MLQuestion":
            classes = class_text_question
            identifier, attributes = Question.parse_args(
                cmd_args, "length", "solution", "uxid"
            )
            attributes.append(("validation", "exact"))

        elif mintmod_class == "MLParsedQuestion":
            classes = class_text_question
            identifier, attributes = Question.parse_args(
                cmd_args, "length", "solution", "precision", "uxid"
            )
            attributes.append(("validation", "parsed"))

        elif mintmod_class == "MLFunctionQuestion":
            classes = class_text_question
            identifier, attributes = Question.parse_args(
                cmd_args,
                "length",
                "solution",
                "supporting-points",
                "variables",
                "precision",
                "uxid",
            )
            attributes.append(("validation", "function"))

        elif mintmod_class == "MLSpecialQuestion":
            classes = class_text_question
            identifier, attributes = Question.parse_args(
                cmd_args,
                "length",
                "solution",
                "supporting-points",
                "variables",
                "precision",
                "special-type",
                "uxid",
            )
            attributes.append(("validation", "special"))

        elif mintmod_class == "MLSimplifyQuestion":
            classes = class_text_question
            identifier, attributes = Question.parse_args(
                cmd_args,
                "length",
                "solution",
                "supporting-points",
                "variables",
                "precision",
                "simplification-code",
                "uxid",
            )
            attributes.append(("validation", "simplify"))

        elif mintmod_class == "MLCheckbox":
            classes = ELEMENT_CLASSES["QUESTION"] + ["checkbox"]
            identifier, attributes = Question.parse_args(cmd_args, "solution", "uxid")
            attributes.append(("validation", "boolean"))

        elif mintmod_class == "MLIntervalQuestion":
            classes = class_text_question
            identifier, attributes = Question.parse_args(
                cmd_args, "length", "solution", "precision", "uxid"
            )
            attributes.append(("validation", "interval"))
        else:
            raise ValueError(
                "Unknown or missing kwarg mintmod_class: {}".format(mintmod_class)
            )

        attributes.append(("points", points))

        if oktypes == pf.Block:
            return pf.Div(identifier=identifier, classes=classes, attributes=attributes)

        return pf.Span(identifier=identifier, classes=classes, attributes=attributes)

    @staticmethod
    def parse_args(cmd_args, *names):
        """Parse exercise arguments.

        Receive a list of argument names and a list of values and return
        a pandoc conformant argument array containing element's arguments.
        In other words: take a list of arguments and make them named arguments
        for easier referencing.
        """
        if len(names) != len(cmd_args):
            log("Invalid args: {}, args: {}".format(names, cmd_args), "ERROR")
            raise ValueError(
                "Warning: Expected different number of args: {}".format(cmd_args)
            )
        attrs = []
        for idx, name in enumerate(names):
            if name == "uxid":
                identifier = cmd_args[idx]
            else:
                attrs.append((name, cmd_args[idx]))
        return identifier, attrs

    def _slots_to_json(self):
        return [self._ica_to_json()]


def create_content_box(elem_content, elem_classes, lang):
    """
    Create a content box.

    Convenience function for creating content boxes that only differ
    by having diffent content and classes.
    """
    if not elem_classes or elem_classes == []:
        msg = "create_content_box without element classes: {}".format(elem_classes)
        raise ValueError(msg)

    if not elem_content or elem_content == "":
        msg = "create_content_box without element content: {}".format(elem_content)
        raise ValueError(msg)

    div = pf.Div(classes=elem_classes)
    content = parse_fragment(elem_content, lang)

    # Check if environment had an \MLabel/SiteUXID identifier
    identifier = extract_identifier(content)
    if identifier:
        div.identifier = identifier

    div.content.extend(content)
    return div


def create_header(title_str, doc, level=0, parse_text=False, identifier=""):
    """
    Create a header element.

    Because headers need to be referenced by later elements, references to the
    last found header is remembered.
    """
    if not isinstance(doc, pf.Doc):
        raise ValueError("create_header without Doc element")

    if parse_text:
        title = parse_fragment(title_str, doc.metadata["lang"].text)[0].content
    else:
        title = destringify(title_str)
    header = pf.Header(*title, level=level, identifier=identifier)
    remember(doc, "label", header)
    return header


def create_image(filename, descr, elem, add_descr=True, block=True):
    """Create an image element."""

    img = pf.Image(url=filename, classes=ELEMENT_CLASSES["IMAGE"])

    if add_descr:
        descr = parse_fragment(descr, elem.doc.metadata["lang"].text, as_doc=True)
        img.title = shorten(
            pf.stringify(*descr.content).strip(), width=125, placeholder="..."
        )
    else:
        img.title = descr

    if block:
        ret = pf.Div(pf.Plain(img), classes=ELEMENT_CLASSES["FIGURE"])
        remember(elem.doc, "label", ret)
        if add_descr:
            ret.content.append(descr.content[0])
    else:
        remember(elem.doc, "label", img)
        ret = img

    return ret
