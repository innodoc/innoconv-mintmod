Installation
============

Prerequisites
-------------

innoconv-mintmod is mainly used on Linux machines. It might work on Mac OS,
Windows/Cygwin/WSL. You are invited to share experiences in doing so.

Dependencies
------------

The only dependencies you have to provide yourself is Pandoc and the Python
interpreter.

All others can be installed into a
`Virtual environment <https://docs.python.org/3.7/library/venv.html>`_.

Python interpreter
~~~~~~~~~~~~~~~~~~

While other versions of Python might work fine, innoconv-mintmod was tested
with **Python 3.7**. Make sure you have it installed.

Pandoc
~~~~~~

You need to make sure to have a recent version of the pandoc binary available
in ``PATH`` (**Pandoc 2.9.2.1** at the time of writing). There are `several ways
on installing Pandoc <https://pandoc.org/installing.html>`_.

Virtual environment
~~~~~~~~~~~~~~~~~~~

Setup and activate a virtual environment in a location of your choice.

.. code-block:: console

  $ python3 -m venv venv
  $ source venv/bin/activate

Install innoconv-mintmod in your virtual environment using pip.

.. code-block:: console

  $ pip install --process-dependency-links -e git+https://gitlab.tubit.tu-berlin.de/innodoc/innoconv-mintmod.git#egg=innoconv-mintmod

If everything went fine you should now have access to the ``innoconv-mintmod``
command.

.. code-block:: console

  $ innoconv-mintmod
  usage: innoconv-mintmod [-h] [-o OUTPUT_DIR_BASE]
                          [-f {latex+raw_tex,markdown}]
                          [-t {html5,json,latex,markdown,asciidoc}] [-l {de,en}]
                          [-d] [-i] [-r] [-s]
                          source
  innoconv-mintmod: error: the following arguments are required: source

*Congratulations!*
