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
from base64 import urlsafe_b64encode
import yaml
from slugify import slugify

from innoconv_mintmod.constants import ENCODING, OUTPUT_FORMAT_EXT_MAP
sys.path.append(os.path.join(os.environ['PANZER_SHARED'], 'panzerhelper'))
# pylint: disable=import-error,wrong-import-position
import panzertools  # noqa: E402

#: Max. depth of headers to consider when splitting sections
MAX_LEVELS = 3

#: Timeout for pandoc process
PANDOC_TIMEOUT = 120

#: Languages key in manifest.yml
LANGKEY = 'languages'
TITLEKEY = 'title'


def concatenate_strings(elems):
    """Concatenate Str and Space elements into a string."""
    string = ''
    for elem in elems:
        if elem['t'] == 'Str':
            string += elem['c']
        elif elem['t'] == 'Space':
            string += ' '
    return string


def generate_id(content):
    """Generate ID from content. If there's no content, create random ID."""
    string = concatenate_strings(content)
    if not string:
        string = urlsafe_b64encode(os.urandom(6))
    return slugify(string)


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
                section['children'] = subsections
            if subcontent:
                section['content'] = subcontent
        elif children:
            section['content'] = children
        sections.append(section)

    section_idx = 0
    for node in tree:
        if node['t'] == 'Header' and node['c'][0] == level:
            await_header = False
            if 'title' in section:
                create_section(sections, section, children)
                children = []
                section = {}
            section['title'] = node['c'][2]
            section_id = node['c'][1][0]
            # auto-generate section ID if necessary
            if not section_id:
                section_id = generate_id(section['title'])
            # number sections so they are in consistent order
            section['id'] = '{:03}-{}'.format(section_idx, section_id)
            section_idx += 1
        else:
            if await_header:
                content.append(node)
            else:
                children.append(node)

    if 'title' in section:
        create_section(sections, section, children)

    return sections, content


def write_sections(sections, outdir_base, output_format):
    """Write sections to individual files and remove content from TOC tree."""

    def convert_section_to_markdown(content, title):
        """Convert JSON section to markdown format using pandoc."""
        # TODO: ensure atx-headers are used
        pandoc_cmd = [
            'pandoc',
            '--standalone',
            '--from=json',
            '--to=markdown+yaml_metadata_block',
        ]
        section_json = json.dumps({
            'blocks': content,
            'pandoc-api-version': [1, 17, 5, 1],
            'meta': {'title': {
                't': 'MetaInlines',
                'c': title,
            }},
        }).encode(ENCODING)
        proc = Popen(pandoc_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate(input=section_json, timeout=PANDOC_TIMEOUT)
        out = out.decode(ENCODING)
        err = err.decode(ENCODING)
        if proc.returncode != 0:
            panzertools.log('ERROR', err)
            raise RuntimeError(
                "pandoc process exited with non-zero return code.")
        return out

    def write_section(section, outdir, depth, root=False):
        """Write a single section to a JSON file."""
        if depth > MAX_LEVELS:
            return

        if root:
            outdir_section = outdir
        else:
            outdir_section = os.path.join(outdir, section['id'])
        os.makedirs(outdir_section, exist_ok=True)

        try:
            content = section['content']
            del section['content']
        except KeyError:
            content = []

        filename = 'content.{}'.format(
            OUTPUT_FORMAT_EXT_MAP[output_format])
        filepath = os.path.join(outdir_section, filename)

        if output_format == 'markdown':
            output = convert_section_to_markdown(content, section['title'])
            with open(filepath, 'w') as sfile:
                sfile.write(output)
        elif output_format == 'json':
            with open(filepath, 'w') as sfile:
                json.dump(content, sfile)
        panzertools.log('INFO', 'Wrote section {}'.format(section['id']))

        try:
            for subsection in section['children']:
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
    manifest_path = os.path.abspath(
        os.path.join(outdir, '..', 'manifest.yml'))

    try:
        with open(manifest_path) as manifest_file:
            manifest = yaml.safe_load(manifest_file)
    except FileNotFoundError:
        manifest = {LANGKEY: [], TITLEKEY: {}}

    if lang not in manifest[LANGKEY]:
        manifest[LANGKEY].append(lang)
    manifest[TITLEKEY][lang] = title

    with open(manifest_path, 'w') as manifest_file:
        yaml.dump(manifest, manifest_file, default_flow_style=False,
                  allow_unicode=True)
    panzertools.log('INFO', 'Wrote: {}'.format(manifest_path))


def _print_sections(sections):

    def _print_section(section, depth):
        if depth > MAX_LEVELS:
            return
        title = concatenate_strings(section['title'])
        indent = ' ' * depth
        msg = '{}{} ({})'.format(indent, title, section['id'])
        panzertools.log('INFO', msg)
        try:
            for subsection in section['children']:
                _print_section(subsection, depth + 1)
        except KeyError:
            pass

    panzertools.log('INFO', 'TOC TREE:')
    for section in sections:
        _print_section(section, 1)


def main(debug=False):
    """Post-flight script entry point."""
    options = panzertools.read_options()
    filepath = options['pandoc']['output']
    convert_to = 'json'

    if os.environ.get('INNOCONV_GENERATE_INNODOC_MARKDOWN'):
        panzertools.log('INFO', 'Converting to Markdown.')
        convert_to = 'markdown'

    if options['pandoc']['write'] != 'json':
        panzertools.log('ERROR', 'Output is expected to be JSON!')
        sys.exit(0)

    # extract lang
    lang = None
    for key in options['pandoc']['options']['r']['metadata']:
        match = re.match(r'^lang:([a-z]{2})$', key[0])
        if match:
            lang = match.group(1)
    if not lang:
        raise RuntimeError('Error: Unable to extract lang key from metadata!')
    panzertools.log('INFO', 'Found lang key={}'.format(lang))

    # load pandoc output
    with open(filepath, 'r') as doc_file:
        doc = json.load(doc_file)

    # extract sections from headers
    sections, _ = create_doc_tree(doc['blocks'], level=1)
    panzertools.log('INFO', 'Extracted table of contents.')

    # output directory
    outdir = os.path.normpath(os.path.dirname(filepath))
    if os.path.basename(outdir) != lang:  # append lang if necessary
        outdir = os.path.join(outdir, lang)
    os.makedirs(outdir, exist_ok=True)

    # write sections to file
    sections = write_sections(sections, outdir, convert_to)

    if os.environ.get('INNOCONV_GENERATE_INNODOC_MARKDOWN'):
        # write metadata file
        try:
            title = doc['meta']['title']['c']
        except AttributeError:
            title = 'UNKNOWN COURSE'
        update_manifest(lang, title, outdir)
    else:
        # write TOC
        tocpath = os.path.join(outdir, 'toc.json')
        with open(tocpath, 'w') as toc_file:
            json.dump(sections, toc_file)
        panzertools.log('INFO', 'Wrote: {}'.format(tocpath))

    # print toc tree
    if debug:
        _print_sections(sections)

    # removing pandoc output file
    os.unlink(filepath)
    panzertools.log(
        'INFO', 'Removed original pandoc output: {}'.format(filepath))


if __name__ == '__main__':
    main(debug=bool(os.environ.get('INNOCONV_DEBUG')))
