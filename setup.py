#!/usr/bin/env python3
# pylint: disable=missing-docstring

"""Define project commands."""


import distutils.cmd
from distutils.command.clean import clean
import os
import logging
import re
import subprocess
import sys
from setuptools import setup

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
PANZER_SUPPORT_DIR = os.path.join(ROOT_DIR, ".panzer")
LINT_DIRS = [
    os.path.join(ROOT_DIR, "innoconv_mintmod"),
    os.path.join(ROOT_DIR, "setup.py"),
    os.path.join(PANZER_SUPPORT_DIR, "filter"),
    os.path.join(PANZER_SUPPORT_DIR, "preflight"),
    os.path.join(PANZER_SUPPORT_DIR, "postflight"),
    os.path.join(PANZER_SUPPORT_DIR, "shared", "panzerhelper"),
]

logging.basicConfig(level=logging.INFO, format="%(message)s")

METADATA_PATH = os.path.join(ROOT_DIR, "innoconv_mintmod", "metadata.py")
with open(METADATA_PATH, "r") as metadata_file:
    METADATA = dict(
        re.findall(r"__([a-z_]+)__\s*=\s*['\"]([^'\"]+)['\"]", metadata_file.read())
    )


def get_logger():
    return logging.getLogger("setup.py")


class BaseCommand(distutils.cmd.Command):  # pylint: disable=no-member
    user_options = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = get_logger()

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def _run(self, command, err_msg="Command failed!", cwd=ROOT_DIR):
        self.log.info("Command %s", " ".join(command))

        # make mintmod_filter module available
        env = os.environ.copy()
        env["PYTHONPATH"] = ROOT_DIR

        proc = subprocess.Popen(command, cwd=cwd, env=env, stderr=subprocess.STDOUT)

        return_code = proc.wait(timeout=120)
        if return_code != 0:
            raise RuntimeError(err_msg)


class Flake8Command(BaseCommand):
    description = "Run flake8 on Python source files"

    def run(self):
        self._run(["flake8"] + LINT_DIRS)


class PylintCommand(BaseCommand):
    description = "Run pylint on Python source files"

    def run(self):
        self._run(["pylint", "--output-format=colorized"] + LINT_DIRS)


class TestCommand(BaseCommand):
    description = "Run test suite"

    user_options = [("test-target=", "t", "Test target (module or path)")]

    def initialize_options(self):
        self.test_target = os.path.join(ROOT_DIR, "innoconv_mintmod")

    def run(self):
        self._run(["green", "-r", self.test_target])


class CoverageCommand(BaseCommand):
    description = "Generate HTML coverage report"

    def run(self):
        if not os.path.isfile(os.path.join(ROOT_DIR, ".coverage")):
            self.log.error('Run "./setup.py test" first to generate a ".coverage".')
        self._run(["coverage", "html"])


class CleanCommand(clean, BaseCommand):
    def run(self):
        super().run()
        self._run(["rm", "-rf", os.path.join(ROOT_DIR, "htmlcov")])
        self._run(["rm", "-rf", os.path.join(ROOT_DIR, ".coverage")])


def setup_package():
    setup(
        name="innoconv-mintmod",
        version=METADATA["version"],
        author=METADATA["author"],
        author_email=METADATA["author_email"],
        cmdclass={
            "clean": CleanCommand,
            "coverage": CoverageCommand,
            "flake8": Flake8Command,
            "pylint": PylintCommand,
            "test": TestCommand,
        },
        dependency_links=["git+https://github.com/msprev/panzer#egg=panzer-1.4.1"],
        entry_points={
            "console_scripts": [
                "innoconv-mintmod = innoconv_mintmod.__main__:main",
                "mintmod_ifttm = innoconv_mintmod.mintmod_ifttm:main",
            ]
        },
        include_package_data=True,
        install_requires=["panflute==2.0.5", "panzer", "python-slugify"],
        packages=["innoconv_mintmod"],
        keywords=["pandoc"],
        license=METADATA["license"],
        long_description=open("README.md").read(),
        url=METADATA["url"],
        zip_safe=False,
    )


if __name__ == "__main__":
    try:
        setup_package()
    except RuntimeError as err:
        get_logger().error("%s: %s", type(err).__name__, err)
        sys.exit(-1)
