#!/usr/bin/env python3

"""Main entry for the innoconv document converter."""

import sys
import argparse
from panflute import debug

from innoconv_mintmod.utils import get_panzer_bin
from innoconv_mintmod.constants import (
    DEFAULT_OUTPUT_DIR_BASE,
    DEFAULT_OUTPUT_FORMAT,
    OUTPUT_FORMAT_CHOICES,
    DEFAULT_INPUT_FORMAT,
    INPUT_FORMAT_CHOICES,
    DEFAULT_LANGUAGE_CODE,
    LANGUAGE_CODES,
)
import innoconv_mintmod.metadata as metadata
from innoconv_mintmod.runner import InnoconvRunner

PANZER_BIN = get_panzer_bin()

INNOCONV_DESCRIPTION = """
  Convert mintmod LaTeX content.

  Using panzer executable: "{}"
""".format(
    PANZER_BIN
)

INNOCONV_EPILOG = """
Copyright (C) 2018 innoCampus, TU Berlin
Authors: {}
Web: {}
This is free software; see the source for copying conditions. There is no
warranty, not even for merchantability or fitness for a particular purpose.
""".format(
    metadata.__author__, metadata.__url__
)


def get_arg_parser():
    """Return argument parser."""
    innoconv_argparser = argparse.ArgumentParser(
        description=INNOCONV_DESCRIPTION,
        epilog=INNOCONV_EPILOG,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help=False,
    )

    innoconv_argparser.add_argument(
        "-h", "--help", action="help", help="show this help message and exit"
    )
    innoconv_argparser.add_argument("source", help="content directory or file")

    innoconv_argparser.add_argument(
        "-o",
        "--output-dir-base",
        default=DEFAULT_OUTPUT_DIR_BASE,
        help="output base directory",
    )

    innoconv_argparser.add_argument(
        "-f",
        "--from",
        dest="input_format",
        choices=INPUT_FORMAT_CHOICES,
        default=DEFAULT_INPUT_FORMAT,
        help="input format",
    )

    innoconv_argparser.add_argument(
        "-t",
        "--to",
        dest="output_format",
        choices=OUTPUT_FORMAT_CHOICES,
        default=DEFAULT_OUTPUT_FORMAT,
        help="output format",
    )

    innoconv_argparser.add_argument(
        "-l",
        "--language-code",
        choices=LANGUAGE_CODES,
        default=DEFAULT_LANGUAGE_CODE,
        help="two-letter language code",
    )

    debug_help = "debug mode (output HTML and highlight unknown commands)"
    innoconv_argparser.add_argument(
        "-d", "--debug", action="store_true", help=debug_help
    )

    ign_exercises_help = "don't show logs for unknown exercise commands/envs"
    innoconv_argparser.add_argument(
        "-i",
        "--ignore-exercises",
        action="store_true",
        help=ign_exercises_help,
    )

    rem_exercises_help = "remove all exercise commands/envs"
    innoconv_argparser.add_argument(
        "-r",
        "--remove-exercises",
        action="store_true",
        help=rem_exercises_help,
    )

    generate_innodoc_help = "split sections and generate manifest.yaml"
    innoconv_argparser.add_argument(
        "-g",
        "--generate-innodoc",
        action="store_true",
        default=True,
        help=generate_innodoc_help,
    )

    return innoconv_argparser


def parse_cli_args():
    """Parse command line arguments."""
    return vars(get_arg_parser().parse_args())


def main():
    """innoConv (mintmod) main entry point."""
    args = parse_cli_args()

    generate_innodoc_markdown = False

    if args["remove_exercises"] and not args["ignore_exercises"]:
        debug(
            "Warning: Setting --remove-exercises implies --ignore-exercises."
        )
        args["ignore_exercises"] = True

    if args["generate_innodoc"]:
        if args["output_format"] not in ("json", "markdown"):
            debug(
                "Error: Output format needs to be either 'json' or "
                "'markdown' when splitting."
            )
            sys.exit(-1)
        # in case of markdown with split sections final transform will happen
        # in generate_innodoc.py
        if args["output_format"] == "markdown":
            args["output_format"] = "json"
            generate_innodoc_markdown = True

    runner = InnoconvRunner(
        args["source"],
        args["output_dir_base"],
        args["language_code"],
        ignore_exercises=args["ignore_exercises"],
        remove_exercises=args["remove_exercises"],
        generate_innodoc=args["generate_innodoc"],
        input_format=args["input_format"],
        output_format=args["output_format"],
        generate_innodoc_markdown=generate_innodoc_markdown,
        debug=args["debug"],
    )
    filename_out = runner.run()
    debug("Build finished: {}".format(filename_out))


if __name__ == "__main__":
    main()
