#!/usr/bin/env python3

"""Main entry for Pandoc filter ``mintmod_filter``."""

import os
from panflute import run_filter
from innoconv_mintmod.mintmod_filter.filter_action import MintmodFilterAction
from innoconv_mintmod.utils import remove_annotations, remove_empty_paragraphs


def main():
    """Execute filter and remove empty paragraphs."""
    debug = bool(os.environ.get('INNOCONV_DEBUG'))
    filter_action = MintmodFilterAction(debug=debug)

    def _finalize(doc):
        remove_empty_paragraphs(doc)
        if not os.getenv('INNOCONV_RECURSION_DEPTH'):
            # remove_annotations must not happen in subprocesses
            remove_annotations(doc)
    run_filter(filter_action.filter, finalize=_finalize)


if __name__ == '__main__':
    main()
