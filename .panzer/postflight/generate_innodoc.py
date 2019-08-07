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


class CreateMapOfIds:
    """Create a mapping between link IDs and section path."""

    def __init__(self, sections):
        self.sections = sections
        self.id_map = {}

    def create(self):
        """Create map."""
        for section in self.sections:
            self._handle_section(section, "")
        return self.id_map

    def _handle_section(self, section, prefix):
        section_path = "{}/{}".format(prefix, section["id"])
        if "content" in section:
            for node in section["content"]:
                self._handle_node(node, section_path)
        if "children" in section:
            for child in section["children"]:
                self._handle_section(child, section_path)

    def _handle_node(self, node, section_path):
        # TODO: figure, image, what else...?
        handle_node_map = {
            "Span": self._handle_span,
            ("Para", "Plain"): self._handle_para,
            "Div": self._handle_div,
            ("Emph", "Strong"): self._handle_emph_strong,
            "OrderedList": self._handle_orderedlist,
            "BulletList": self._handle_bulletlist,
            (
                "LineBreak",
                "Link",
                "Math",
                "SoftBreak",
                "Space",
                "Str",
            ): lambda *args: None,
        }

        for elem_type in handle_node_map:
            if node["t"] == elem_type or node["t"] in elem_type:
                handle_node_map[elem_type](node, section_path)
                return
        panzertools.log(
            "WARNING", "Encountered unknown element: {}".format(pformat(node))
        )

    def _handle_span(self, node, section_path):
        span_id = node["c"][0][0]
        if span_id:
            self.id_map[span_id] = section_path
        for sub_node in node["c"][1]:
            self._handle_node(sub_node, section_path)

    def _handle_para(self, node, section_path):
        for sub_node in node["c"]:
            self._handle_node(sub_node, section_path)

    def _handle_div(self, node, section_path):
        div_id = node["c"][0][0]
        if div_id:
            self.id_map[div_id] = section_path
        for sub_node in node["c"][1]:
            self._handle_node(sub_node, section_path)

    def _handle_emph_strong(self, node, section_path):
        for sub_node in node["c"]:
            self._handle_node(sub_node, section_path)

    def _handle_orderedlist(self, node, section_path):
        for item in node["c"][1]:
            for sub_node in item:
                self._handle_node(sub_node, section_path)

    def _handle_bulletlist(self, node, section_path):
        for item in node["c"]:
            for sub_node in item:
                self._handle_node(sub_node, section_path)


class PostprocessLinks:
    """Postprocess all links to work with new section structure."""

    def __init__(self, sections, section_map, id_map):
        self.sections = sections
        self.section_map = section_map
        self.id_map = id_map

    def process(self):
        """Rewrite links."""
        for section in self.sections:
            self._handle_section(section)

    def _handle_section(self, section):
        if "content" in section:
            for node in section["content"]:
                self._handle_node(node)
        if "children" in section:
            for child in section["children"]:
                self._handle_section(child)

    def _handle_node(self, node):
        handle_node_map = {
            "Span": self._handle_span,
            "Link": self._handle_ref,
            ("Para", "Plain", "Emph"): self._handle_para,
            "Div": self._handle_div,
            "OrderedList": self._handle_orderedlist,
            "BulletList": self._handle_bulletlist,
            (
                "LineBreak",
                "Math",
                "SoftBreak",
                "Space",
                "Str",
            ): lambda *args: None,
        }

        for elem_type in handle_node_map:
            if node["t"] == elem_type or node["t"] in elem_type:
                handle_node_map[elem_type](node)
                return
        panzertools.log(
            "WARNING", "Encountered unknown element: {}".format(pformat(node))
        )

    def _handle_span(self, node):
        attrs = self._attrs_to_dict(node["c"][0][2])
        if "data-mentry" in attrs.keys():
            pass
        elif "data-mindex" in attrs.keys():
            pass
        elif not attrs.keys():
            for sub_node in node["c"][1]:
                self._handle_node(sub_node)
        elif "question" in node["c"][0][1]:
            pass
        else:
            panzertools.log(
                "WARNING", r"Found unknown span={}".format(pformat(node))
            )

    def _handle_ref(self, node):
        attrs = self._attrs_to_dict(node["c"][0][2])
        if "data-mref" in attrs.keys():
            # \MRef has ID target, caption is (section, example,
            # exercise, ...) number
            self._handle_link("MRef", node)
            node["c"][1] = []
        elif "data-msref" in attrs.keys():
            # \MSRef has ID target and caption
            self._handle_link("MSRef", node)
        elif "data-mnref" in attrs.keys():
            # \MNRef: seems to be the same as \MRef...
            self._handle_link("MNRef", node)
            node["c"][1] = []

    def _handle_para(self, node):
        for sub_node in node["c"]:
            self._handle_node(sub_node)

    def _handle_div(self, node):
        for sub_node in node["c"][1]:
            self._handle_node(sub_node)

    def _handle_orderedlist(self, node):
        for item in node["c"][1]:
            for sub_node in item:
                self._handle_node(sub_node)

    def _handle_bulletlist(self, node):
        for item in node["c"]:
            for sub_node in item:
                self._handle_node(sub_node)

    def _handle_link(self, cmd, node):
        target = node["c"][2][0]
        if target.startswith("#"):
            target = target[1:]
        try:
            # try ID
            section_path = self.id_map[target]
            url = "{}#{}".format(section_path, target)
        except KeyError:
            # try section ID
            try:
                url = self.section_map[target]
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

    @staticmethod
    def _attrs_to_dict(attrs):
        return dict((k, v) for k, v in attrs)


class ExtractSectionTree:
    """Generate section tree from a flat document structure."""

    def __init__(self, nodes, level):
        self.nodes = nodes
        self.level = level
        self.sections = []
        self.section = {}
        self.await_header = True
        self.content = []
        self.children = []

    def get_tree(self):
        """Generate and return tree."""
        section_idx = 0
        for node in self.nodes:
            if node["t"] == "Header" and node["c"][0] == self.level:
                self.await_header = False
                if "title" in self.section:
                    self.create_section()
                    self.children = []
                    self.section = {}
                self.section["title"] = node["c"][2]
                section_id = node["c"][1][0]
                section_num = "{:03}".format(section_idx)
                if section_id:
                    # number sections so they are in consistent order
                    self.section["id"] = "{}-{}".format(
                        section_num, section_id
                    )
                else:
                    # if there's no section id for some reason just use number
                    self.section["id"] = section_num
                section_idx += 1
            else:
                if self.await_header:
                    self.content.append(node)
                else:
                    self.children.append(node)

        if "title" in self.section:
            self.create_section()

        return self.sections, self.content

    def create_section(self):
        """Save a section."""
        if self.level <= MAX_LEVELS:
            subsections, subcontent = ExtractSectionTree(
                self.children, self.level + 1
            ).get_tree()
            if subsections:
                self.section["children"] = subsections
            if subcontent:
                self.section["content"] = subcontent
        elif self.children:
            self.section["content"] = self.children
        self.sections.append(self.section)


class CreateMapOfSectionIds:
    """Create mapping between mintmod section id and section path."""

    def __init__(self, sections):
        self.sections = sections
        self.id_map = {}

    def _handle_section(self, section, prefix):
        mintmod_section_id = self._section_id_to_mintmod_section_id(
            section["id"]
        )
        self.id_map[mintmod_section_id] = "{}/{}".format(prefix, section["id"])
        try:
            for subsection in section["children"]:
                self._handle_section(
                    subsection,
                    prefix="{}".format(self.id_map[mintmod_section_id]),
                )
        except KeyError:
            pass

    @staticmethod
    def _section_id_to_mintmod_section_id(section_id):
        """Remove number prefix from section, e.g. '000-foo' -> 'foo'."""
        if len(section_id) >= 3:
            mm_section_id = section_id[3:]
        if mm_section_id and mm_section_id[0] == "-":
            mm_section_id = mm_section_id[1:]
        return mm_section_id

    def get_map(self):
        """Generate section map."""
        for section in self.sections:
            self._handle_section(section, "")
        return self.id_map


class WriteSections:
    """Write sections to individual files and remove content from TOC tree."""

    #: Timeout for pandoc process
    PANDOC_TIMEOUT = 120

    def __init__(self, sections, outdir_base, output_format):
        self.sections = sections
        self.outdir_base = outdir_base
        self.output_format = output_format

    def write_sections(self):
        """Write all sections."""
        for idx, section in enumerate(self.sections):
            self._write_section(section, self.outdir_base, 1, idx == 0)
        return self.sections

    def _write_section(self, section, outdir, depth, root=False):
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

        filename = "content.{}".format(
            OUTPUT_FORMAT_EXT_MAP[self.output_format]
        )
        filepath = os.path.join(outdir_section, filename)

        if self.output_format == "markdown":
            output = self._convert_section_to_markdown(
                content, section["title"]
            )
            with open(filepath, "w") as sfile:
                sfile.write(output)
        elif self.output_format == "json":
            with open(filepath, "w") as sfile:
                json.dump(content, sfile)
        panzertools.log("INFO", "Wrote section {}".format(section["id"]))

        try:
            for subsection in section["children"]:
                self._write_section(subsection, outdir_section, depth + 1)
        except KeyError:
            pass

    def _convert_section_to_markdown(self, content, title):
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
        out, err = proc.communicate(
            input=section_json, timeout=self.PANDOC_TIMEOUT
        )
        out = out.decode(ENCODING)
        err = err.decode(ENCODING)
        if proc.returncode != 0:
            panzertools.log("ERROR", err)
            raise RuntimeError(
                "pandoc process exited with non-zero return code."
            )
        return out


class GenerateInnodoc:
    """Main class for generate_innodoc postflight filter."""

    #: Languages key in manifest.yml
    LANGKEY = "languages"
    TITLEKEY = "title"

    def __init__(self, debug=False):
        self.debug = debug
        self.options = panzertools.read_options()
        self.filepath = self.options["pandoc"]["output"]
        self.convert_to = "json"
        if os.environ.get("INNOCONV_GENERATE_INNODOC_MARKDOWN"):
            panzertools.log("INFO", "Converting to Markdown.")
            self.convert_to = "markdown"
        if self.options["pandoc"]["write"] != "json":
            panzertools.log("ERROR", "Output is expected to be JSON!")
            sys.exit(0)
        # extract lang
        self.lang = None
        for key in self.options["pandoc"]["options"]["r"]["metadata"]:
            match = re.match(r"^lang:([a-z]{2})$", key[0])
            if match:
                self.lang = match.group(1)
        if not self.lang:
            raise RuntimeError(
                "Error: Unable to extract lang key from metadata!"
            )
        panzertools.log("INFO", "Found lang key={}".format(self.lang))

    def main(self):
        """Post-flight script entry point."""
        # load pandoc output
        with open(self.filepath, "r") as doc_file:
            doc = json.load(doc_file)

        # extract sections from headers
        sections, _ = ExtractSectionTree(doc["blocks"], 1).get_tree()
        panzertools.log("INFO", "Extracted table of contents.")

        # rewrite internal links
        section_map = CreateMapOfSectionIds(sections).get_map()
        panzertools.log("INFO", "Created map of sections from AST.")
        id_map = CreateMapOfIds(sections).create()
        panzertools.log("INFO", "Created ID map from AST.")
        PostprocessLinks(sections, section_map, id_map).process()
        panzertools.log("INFO", "Post-processed links.")

        # output directory
        outdir = os.path.normpath(os.path.dirname(self.filepath))
        if os.path.basename(outdir) != self.lang:  # append lang if necessary
            outdir = os.path.join(outdir, self.lang)
        os.makedirs(outdir, exist_ok=True)

        # write sections to file
        sections = WriteSections(
            sections, outdir, self.convert_to
        ).write_sections()

        if os.environ.get("INNOCONV_GENERATE_INNODOC_MARKDOWN"):
            # write metadata file
            try:
                title = doc["meta"]["title"]["c"]
            except KeyError:
                title = "UNKNOWN COURSE"
            self.update_manifest(title, outdir)
        else:
            # write TOC
            tocpath = os.path.join(outdir, "toc.json")
            with open(tocpath, "w") as toc_file:
                json.dump(sections, toc_file)
            panzertools.log("INFO", "Wrote: {}".format(tocpath))

        # print toc tree
        if self.debug:
            self._print_sections(sections)

        # remove pandoc output file
        os.unlink(self.filepath)
        panzertools.log(
            "INFO", "Removed original pandoc output: {}".format(self.filepath)
        )

    def update_manifest(self, title, outdir):
        """Update ``manifest.yml`` file.

        If it doesn't exist it will be created.
        """
        manifest_path = os.path.abspath(
            os.path.join(outdir, "..", "manifest.yml")
        )
        try:
            with open(manifest_path) as manifest_file:
                manifest = yaml.safe_load(manifest_file)
        except FileNotFoundError:
            manifest = {self.LANGKEY: [], self.TITLEKEY: {}}

        if self.lang not in manifest[self.LANGKEY]:
            manifest[self.LANGKEY].append(self.lang)
        manifest[self.TITLEKEY][self.lang] = title

        with open(manifest_path, "w") as manifest_file:
            yaml.dump(
                manifest,
                manifest_file,
                default_flow_style=False,
                allow_unicode=True,
            )
        panzertools.log("INFO", "Wrote: {}".format(manifest_path))

    @staticmethod
    def _print_sections(sections):
        def _print_section(section, depth):
            if depth > MAX_LEVELS:
                return
            title = GenerateInnodoc._concatenate_strings(section["title"])
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

    @staticmethod
    def _concatenate_strings(elems):
        """Concatenate Str and Space elements into a string."""
        string = ""
        for elem in elems:
            if elem["t"] == "Str":
                string += elem["c"]
            elif elem["t"] == "Space":
                string += " "
        return string


if __name__ == "__main__":
    GenerateInnodoc(debug=bool(os.environ.get("INNOCONV_DEBUG"))).main()
