"""Convenience functions for creating common elements."""

from slugify import slugify
import panflute as pf
from innoconv.utils import destringify, parse_fragment


def create_header(title_str, doc, level=0, auto_id=False):

    """Create a header element.

    Because headers need to be referenced by other elements, references to the
    found headers are stored in the doc properties.
    """

    title = destringify(title_str)
    header = pf.Header(*title, level=level)
    if auto_id:
        header.identifier = slugify(title_str)
    doc.last_header_elem = header
    return header


def create_content_box(title, div_classes, elem_content, doc, level=4,
                       auto_id=False):

    """Create a content box.

    Convenience function for creating content boxes that only differ
    by having diffent titles and classes.
    """

    div = pf.Div(classes=div_classes)
    content = parse_fragment(elem_content)
    if title:
        header = create_header(title, doc, level=level, auto_id=auto_id)
        content = [header] + content
    div.content.extend(content)
    return div
