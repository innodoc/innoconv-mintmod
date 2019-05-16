#!/usr/bin/env python3
"""
This is the final step to generate innoDoc content from Mintmod input.

 - Loads pandoc output from single JSON file.
 - Extract section tree.
 - Save individual sections to course directory structure.
 - Generate a ``manifest.yml``.
 - Removes single JSON file.
"""

import os
import sys
import json
import re
from subprocess import Popen, PIPE
from pprint import pformat

import yaml

from innoconv_mintmod.constants import ENCODING, OUTPUT_FORMAT_EXT_MAP

sys.path.append(os.path.join(os.environ["PANZER_SHARED"], "panzerhelper"))
# pylint: disable=import-error,wrong-import-position
import panzertools  # noqa: E402

#: Max. depth of headers to consider when splitting sections
MAX_LEVELS = 3

#: Timeout for pandoc process
PANDOC_TIMEOUT = 120

#: Languages key in manifest.yml
LANGKEY = "languages"
TITLEKEY = "title"


def _attrs_to_dict(attrs):
    return dict((k, v) for k, v in attrs)


def section_id_to_mintmod_section_id(section_id):
    """Remove number prefix from section, e.g. '000-foo' -> 'foo'."""
    if len(section_id) >= 3:
        mm_section_id = section_id[3:]
    if mm_section_id and mm_section_id[0] == "-":
        mm_section_id = mm_section_id[1:]
    return mm_section_id


def concatenate_strings(elems):
    """Concatenate Str and Space elements into a string."""
    string = ""
    for elem in elems:
        if elem["t"] == "Str":
            string += elem["c"]
        elif elem["t"] == "Space":
            string += " "
    return string


def create_doc_tree(tree, level):
    """Generate section tree from a flat document structure."""
    sections = []
    section = {}
    await_header = True
    content = []
    children = []

    def create_section(sections, section, children):
        """Save a section."""
        if level <= MAX_LEVELS:
            subsections, subcontent = create_doc_tree(children, level + 1)
            if subsections:
                section["children"] = subsections
            if subcontent:
                section["content"] = subcontent
        elif children:
            section["content"] = children
        sections.append(section)

    section_idx = 0
    for node in tree:
        if node["t"] == "Header" and node["c"][0] == level:
            await_header = False
            if "title" in section:
                create_section(sections, section, children)
                children = []
                section = {}
            section["title"] = node["c"][2]
            section_id = node["c"][1][0]
            section_num = "{:03}".format(section_idx)
            if section_id:
                # number sections so they are in consistent order
                section["id"] = "{}-{}".format(section_num, section_id)
            else:
                # if there's no section id for some reason just use number
                section["id"] = section_num
            section_idx += 1
        else:
            if await_header:
                content.append(node)
            else:
                children.append(node)

    if "title" in section:
        create_section(sections, section, children)

    return sections, content


def create_map_of_section_ids(sections):
    """Create mapping between mintmod section id and section path."""
    id_map = {}

    def handle_section(section, prefix):
        mintmod_section_id = section_id_to_mintmod_section_id(section["id"])
        id_map[mintmod_section_id] = "{}/{}".format(prefix, section["id"])
        try:
            for subsection in section["children"]:
                handle_section(
                    subsection, prefix="{}".format(id_map[mintmod_section_id])
                )
        except KeyError:
            pass

    for section in sections:
        handle_section(section, "")

    return id_map


def create_map_of_ids(sections):
    """Create a mapping between link IDs and section path."""
    id_map = {}

    def handle_node(node, section_path):
        # pylint: disable=too-many-branches
        # TODO: figure, image, what else...?
        if node["t"] == "Span":
            span_id = node["c"][0][0]
            if span_id:
                id_map[span_id] = section_path
            for sub_node in node["c"][1]:
                handle_node(sub_node, section_path)
        elif node["t"] in ("Para", "Plain"):
            for sub_node in node["c"]:
                handle_node(sub_node, section_path)
        elif node["t"] == "Div":
            div_id = node["c"][0][0]
            if div_id:
                id_map[div_id] = section_path
            for sub_node in node["c"][1]:
                handle_node(sub_node, section_path)
        elif node["t"] in ("Emph", "Strong"):
            for sub_node in node["c"]:
                handle_node(sub_node, section_path)
        elif node["t"] == "OrderedList":
            for item in node["c"][1]:
                for sub_node in item:
                    handle_node(sub_node, section_path)
        elif node["t"] == "BulletList":
            for item in node["c"]:
                for sub_node in item:
                    handle_node(sub_node, section_path)
        elif node["t"] in (
            "LineBreak",
            "Link",
            "Math",
            "SoftBreak",
            "Space",
            "Str",
        ):
            pass
        else:
            panzertools.log(
                "WARNING",
                "Encountered unknown element: {}".format(pformat(node)),
            )

    def handle_section(section, prefix):
        section_path = "{}/{}".format(prefix, section["id"])
        if "content" in section:
            for node in section["content"]:
                handle_node(node, section_path)
        if "children" in section:
            for child in section["children"]:
                handle_section(child, section_path)

    for section in sections:
        handle_section(section, "")

    return id_map


def postprocess_links(sections, section_map, id_map):
    """Rewrite links."""
    # pylint: disable=too-many-statements

    def handle_link(cmd, node):
        target = node["c"][2][0]
        if target.startswith("#"):
            target = target[1:]
        try:
            # try ID
            section_path = id_map[target]
            url = "{}#{}".format(section_path, target)
        except KeyError:
            # try section ID
            try:
                url = section_map[target]
            except KeyError:
                panzertools.log(
                    "WARNING",
                    "Found {}: Couldn't map ID={}".format(cmd, target),
                )
                return
        node["c"][0][2] = []  # remove attributes
        node["c"][2][0] = url
        panzertools.log(
            "INFO", "Found {}: '{}' -> '{}'".format(cmd, target, url)
        )

    def handle_node(node):
        # pylint: disable=too-many-branches
        if node["t"] == "Span":
            attrs = _attrs_to_dict(node["c"][0][2])
            if "data-mentry" in attrs.keys():
                pass
            elif "data-mindex" in attrs.keys():
                pass
            elif not attrs.keys():
                for sub_node in node["c"][1]:
                    handle_node(sub_node)
            elif "question" in node["c"][0][1]:
                pass
            else:
                panzertools.log(
                    "WARNING", r"Found unknown span={}".format(pformat(node))
                )
        elif node["t"] == "Link":
            attrs = _attrs_to_dict(node["c"][0][2])
            if "data-mref" in attrs.keys():
                # \MRef has ID target, caption is (section, example,
                # exercise, ...) number
                handle_link("MRef", node)
                node["c"][1] = []
            elif "data-msref" in attrs.keys():
                # \MSRef has ID target and caption
                handle_link("MSRef", node)
            elif "data-mnref" in attrs.keys():
                # \MNRef: seems to be the same as \MRef...
                handle_link("MNRef", node)
                node["c"][1] = []
        elif node["t"] in ("Para", "Plain"):
            for sub_node in node["c"]:
                handle_node(sub_node)
        elif node["t"] == "Div":
            for sub_node in node["c"][1]:
                handle_node(sub_node)
        elif node["t"] == "Emph":
            for sub_node in node["c"]:
                handle_node(sub_node)
        elif node["t"] == "OrderedList":
            for item in node["c"][1]:
                for sub_node in item:
                    handle_node(sub_node)
        elif node["t"] == "BulletList":
            for item in node["c"]:
                for sub_node in item:
                    handle_node(sub_node)
        elif node["t"] in ("LineBreak", "Math", "SoftBreak", "Space", "Str"):
            pass
        else:
            panzertools.log(
                "WARNING",
                "Encountered unknown element: {}".format(pformat(node)),
            )

    def handle_section(section):
        if "content" in section:
            for node in section["content"]:
                handle_node(node)
        if "children" in section:
            for child in section["children"]:
                handle_section(child)

    for section in sections:
        handle_section(section)


def write_sections(sections, outdir_base, output_format):
    """Write sections to individual files and remove content from TOC tree."""

    def convert_section_to_markdown(content, title):
        """Convert JSON section to markdown format using pandoc."""
        # TODO: ensure atx-headers are used
        pandoc_cmd = [
            "pandoc",
            "--wrap=preserve",
            "--columns=999",
            "--standalone",
            "--from=json",
            "--to=markdown+yaml_metadata_block",
        ]
        section_json = json.dumps(
            {
                "blocks": content,
                "pandoc-api-version": [1, 17, 5, 1],
                "meta": {"title": {"t": "MetaInlines", "c": title}},
            }
        ).encode(ENCODING)
        proc = Popen(pandoc_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate(input=section_json, timeout=PANDOC_TIMEOUT)
        out = out.decode(ENCODING)
        err = err.decode(ENCODING)
        if proc.returncode != 0:
            panzertools.log("ERROR", err)
            raise RuntimeError(
                "pandoc process exited with non-zero return code."
            )
        return out

    def write_section(section, outdir, depth, root=False):
        """Write a single section to a JSON file."""
        if depth > MAX_LEVELS:
            return

        if root:
            outdir_section = outdir
        else:
            outdir_section = os.path.join(outdir, section["id"])
        os.makedirs(outdir_section, exist_ok=True)

        try:
            content = section["content"]
            del section["content"]
        except KeyError:
            content = []

        filename = "content.{}".format(OUTPUT_FORMAT_EXT_MAP[output_format])
        filepath = os.path.join(outdir_section, filename)

        if output_format == "markdown":
            output = convert_section_to_markdown(content, section["title"])
            with open(filepath, "w") as sfile:
                sfile.write(output)
        elif output_format == "json":
            with open(filepath, "w") as sfile:
                json.dump(content, sfile)
        panzertools.log("INFO", "Wrote section {}".format(section["id"]))

        try:
            for subsection in section["children"]:
                write_section(subsection, outdir_section, depth + 1)
        except KeyError:
            pass

    for idx, section in enumerate(sections):
        write_section(section, outdir_base, 1, idx == 0)

    return sections


def update_manifest(lang, title, outdir):
    """Update ``manifest.yml`` file.

    If it doesn't exist it will be created.
    """
    manifest_path = os.path.abspath(os.path.join(outdir, "..", "manifest.yml"))

    try:
        with open(manifest_path) as manifest_file:
            manifest = yaml.safe_load(manifest_file)
    except FileNotFoundError:
        manifest = {LANGKEY: [], TITLEKEY: {}}

    if lang not in manifest[LANGKEY]:
        manifest[LANGKEY].append(lang)
    manifest[TITLEKEY][lang] = title

    with open(manifest_path, "w") as manifest_file:
        yaml.dump(
            manifest,
            manifest_file,
            default_flow_style=False,
            allow_unicode=True,
        )
    panzertools.log("INFO", "Wrote: {}".format(manifest_path))


def _print_sections(sections):
    def _print_section(section, depth):
        if depth > MAX_LEVELS:
            return
        title = concatenate_strings(section["title"])
        indent = " " * depth
        msg = "{}{} ({})".format(indent, title, section["id"])
        panzertools.log("INFO", msg)
        try:
            for subsection in section["children"]:
                _print_section(subsection, depth + 1)
        except KeyError:
            pass

    panzertools.log("INFO", "TOC TREE:")
    for section in sections:
        _print_section(section, 1)


def main(debug=False):
    """Post-flight script entry point."""
    # pylint: disable=too-many-locals
    options = panzertools.read_options()
    filepath = options["pandoc"]["output"]
    convert_to = "json"

    if os.environ.get("INNOCONV_GENERATE_INNODOC_MARKDOWN"):
        panzertools.log("INFO", "Converting to Markdown.")
        convert_to = "markdown"

    if options["pandoc"]["write"] != "json":
        panzertools.log("ERROR", "Output is expected to be JSON!")
        sys.exit(0)

    # extract lang
    lang = None
    for key in options["pandoc"]["options"]["r"]["metadata"]:
        match = re.match(r"^lang:([a-z]{2})$", key[0])
        if match:
            lang = match.group(1)
    if not lang:
        raise RuntimeError("Error: Unable to extract lang key from metadata!")
    panzertools.log("INFO", "Found lang key={}".format(lang))

    # load pandoc output
    with open(filepath, "r") as doc_file:
        doc = json.load(doc_file)

    # extract sections from headers
    sections, _ = create_doc_tree(doc["blocks"], level=1)
    panzertools.log("INFO", "Extracted table of contents.")

    # rewrite internal links
    section_map = create_map_of_section_ids(sections)
    panzertools.log("INFO", "Created map of sections from AST.")
    id_map = create_map_of_ids(sections)
    panzertools.log("INFO", "Created ID map from AST.")
    postprocess_links(sections, section_map, id_map)
    panzertools.log("INFO", "Post-processed links.")

    # output directory
    outdir = os.path.normpath(os.path.dirname(filepath))
    if os.path.basename(outdir) != lang:  # append lang if necessary
        outdir = os.path.join(outdir, lang)
    os.makedirs(outdir, exist_ok=True)

    # write sections to file
    sections = write_sections(sections, outdir, convert_to)

    if os.environ.get("INNOCONV_GENERATE_INNODOC_MARKDOWN"):
        # write metadata file
        try:
            title = doc["meta"]["title"]["c"]
        except KeyError:
            title = "UNKNOWN COURSE"
        update_manifest(lang, title, outdir)
    else:
        # write TOC
        tocpath = os.path.join(outdir, "toc.json")
        with open(tocpath, "w") as toc_file:
            json.dump(sections, toc_file)
        panzertools.log("INFO", "Wrote: {}".format(tocpath))

    # print toc tree
    if debug:
        _print_sections(sections)

    # remove pandoc output file
    os.unlink(filepath)
    panzertools.log(
        "INFO", "Removed original pandoc output: {}".format(filepath)
    )


if __name__ == "__main__":
    main(debug=bool(os.environ.get("INNOCONV_DEBUG")))
