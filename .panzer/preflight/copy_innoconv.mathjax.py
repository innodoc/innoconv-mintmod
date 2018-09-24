#!/usr/bin/env python3
"""
Copy innoconv.mathjax.js to build directory.

This script is only needed for the debug HTML build.
"""

import os
import shutil
import sys
sys.path.append(os.path.join(os.environ['PANZER_SHARED'], 'panzerhelper'))
# pylint: disable=import-error,wrong-import-position
import panzertools  # noqa: E402


def main():
    """main function"""
    options = panzertools.read_options()
    output = options['pandoc']['output']
    if output != '-':
        src_file = os.path.join(
            os.environ['PANZER_SHARED'], 'javascript', 'innoconv.mathjax.js')
        build_path = os.path.dirname(output)
        shutil.copy(src_file, build_path)


if __name__ == '__main__':
    main()
